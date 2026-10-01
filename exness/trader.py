"""
exness/trader.py — Automated Execution & Risk Management Engine for Exness MT5.
Calibrated for PrasaD (KSM X Tech):
  - Active Capital: $500.00 USD (~₹41,750 INR)
  - Base Risk: 1.0% ($5.00 risk per trade) to 1.5% ($7.50 risk per trade)
  - Micro-lot auto-sizing (down to 0.01 lots)
  - Pending Limit Order dispatch with embedded SL/TP
  - Automated Break-Even Shield at +1.0R
  - Max 3 concurrent trades, 5 trades/day cap, 3-loss circuit breaker
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import time
import math
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone

from exness.mt5_connection import ExnessMT5
from exness.strategy_smc_m15 import analyze_m15_setup, pip_size, to_pips
from exness.market_awareness import MarketAwarenessGuardian
from exness.dream_rsi import LiveDiscoveryTreeLogger
from exness.execution_sentinel import ExecutionSentinel
from exness.laya_guardian import LayaGuardian
from exness.hybrid_decision_guardian import HybridDecisionGuardian
from exness.execution_recorder import ExecutionRecorder
from exness.model_watcher import ModelWatcher
from exness.chart_snapshot import ChartSnapshotEngine
from exness.inflight_copilot import InFlightCoPilot
from exness.news_radar import NewsRadar
from exness.agent_committee import InstitutionalCommittee
from exness.telegram_notifier import TelegramNotifier
from exness.position_sizing import pip_value_per_lot_usd, lots_for_risk, calculate_turtle_drawdown_equity

MAGIC_NUMBER = 987654
DEFAULT_RISK_PCT = 0.005  # 0.5% risk per trade ($2.50 on $500 balance, conservative risk posture)
MAX_CONCURRENT_TRADES = 3
MAX_DAILY_TRADES = 5
CIRCUIT_BREAKER_LOSSES = 3

class ExnessTrader:
    def __init__(
        self,
        risk_pct: float = DEFAULT_RISK_PCT,
        mm_mode: str = "fixed_fractional", # "fixed_fractional", "anti_martingale", or "news_reserve"
        starting_balance: float = 500.0,
        max_spread_pips: float = 2.0,
        dry_run: bool = False,
        enable_laya: bool = True,
        use_jev: bool = True
    ):
        self.mt5_client = ExnessMT5()
        self.guardian = MarketAwarenessGuardian(max_spread_pips=max_spread_pips)
        self.sentinel = ExecutionSentinel()
        self.laya = LayaGuardian(lazy_load=True, enabled=enable_laya)
        self.hybrid_guardian = HybridDecisionGuardian(use_jev=use_jev, use_decider_backup=True, use_laya_backup=enable_laya)
        self.recorder = ExecutionRecorder()
        lora_weights_path = os.path.join(ROOT_DIR, "exness", "models", "laya_lora_distilled", "laya_lora_weights.pt")
        self.chart_snapshots = ChartSnapshotEngine()
        self.telegram = TelegramNotifier()
        self.inflight_copilot = InFlightCoPilot(guardian=self.laya, snapshot_engine=self.chart_snapshots)
        self.news_radar = NewsRadar(guardian=self.laya)
        self.committee = InstitutionalCommittee(guardian=self.laya)
        self.model_watcher = ModelWatcher(
            weights_path=lora_weights_path,
            reload_callback=self.laya.reload_lora_weights if hasattr(self.laya, 'reload_lora_weights') else None
        )
        self.base_risk_pct = risk_pct
        self.risk_pct = risk_pct
        self.mm_mode = mm_mode
        self.starting_balance = starting_balance
        self.news_vault = 0.0 # 20% profit siphoned into News Vault
        self.dry_run = dry_run
        self.daily_trade_count = 0
        self.daily_consecutive_losses = 0
        self.last_trade_date = None
        self.last_trade_won = False
        self.last_placed_setup = set()
        self.tree_logger = LiveDiscoveryTreeLogger()
        self.audited_deals = set()
        self.last_overnight_run = None
        self.peak_equity = starting_balance if (starting_balance and starting_balance > 0) else 500.0

    def initialize(self) -> bool:
        """Connects to MT5 and checks account state."""
        if not self.mt5_client.connect():
            return False
        summary = self.mt5_client.get_account_summary()
        if summary:
            # Dynamically lock starting balance to current broker balance if not set or default
            if self.starting_balance is None or self.starting_balance <= 0:
                self.starting_balance = summary['balance']
            print(f"\n{'='*65}\n  EXNESS MT5 TRADING ENGINE INITIALIZED\n{'='*65}")
            print(f"Account Login  : {summary['login']} ({summary['server']})")
            print(f"Balance        : ${summary['balance']:,.2f} {summary['currency']}")
            print(f"Equity         : ${summary['equity']:,.2f}")
            print(f"Capital Base   : ${self.starting_balance:,.2f}")
            print(f"Leverage       : 1:{summary['leverage']}")
            print(f"MM Mode        : {self.mm_mode.upper()} (Base Risk: {self.base_risk_pct * 100:.1f}%)")
            print(f"Mode           : {'DRY RUN (MONITOR ONLY)' if self.dry_run else 'LIVE AUTOMATED EXECUTION'}")
            print(f"{'='*65}\n")
        return True

    def get_effective_risk_pct(self, is_news_trade: bool = False) -> float:
        """Determines active trade risk % based on chosen Money Management model."""
        summary = self.mt5_client.get_account_summary()
        if not summary:
            return self.base_risk_pct

        equity = summary["equity"]

        if is_news_trade:
            # Sourced exclusively from accumulated News Vault
            if self.news_vault >= 2.0:
                return min(0.05, self.news_vault / equity) # Max 5% or vault amount
            return 0.0 # No news trade if vault empty

        if self.mm_mode == "anti_martingale":
            # If last trade won and equity > starting capital, risk 2.5% using house money
            if self.last_trade_won and equity > self.starting_balance:
                return 0.025
            return self.base_risk_pct

        return self.base_risk_pct

    def calculate_lot_size(self, symbol: str, risk_pips: float, is_news_trade: bool = False) -> float:
        """
        Calculates exact volume in lots using broker tick value or live quote conversion.
        Refuses trades (returns 0.0) if minimum lot risks > 1.25x the budget (MAX_OVERRISK_FACTOR).
        """
        summary = self.mt5_client.get_account_summary()
        if not summary:
            return 0.0

        equity = summary["equity"]
        self.peak_equity = max(getattr(self, 'peak_equity', equity), equity)
        effective_equity = calculate_turtle_drawdown_equity(equity, self.peak_equity)
        active_risk_pct = self.get_effective_risk_pct(is_news_trade=is_news_trade)

        details = self.mt5_client.get_symbol_details(symbol)
        if not details:
            return 0.0

        contract_size = details.get("trade_contract_size", 100000.0)
        vol_min = details.get("volume_min", 0.01)
        vol_max = details.get("volume_max", 100.0)
        vol_step = details.get("volume_step", 0.01)
        pip = pip_size(symbol)

        tick_val = details.get("trade_tick_value", 0.0)
        tick_sz = details.get("trade_tick_size", 0.0)

        rates = {}
        for p in ["USDJPY", "USDCAD", "USDCHF", "GBPUSD", "EURUSD", "AUDUSD", "NZDUSD"]:
            det = self.mt5_client.get_symbol_details(p)
            if det and det.get("ask", 0.0) > 0:
                rates[p] = det["ask"]

        try:
            pv = pip_value_per_lot_usd(symbol, contract_size, pip, rates=rates,
                                       tick_value=tick_val, tick_size=tick_sz)
        except Exception as e:
            print(f"⚠️ Sizing conversion error for {symbol}: {e}")
            return 0.0

        lots, info = lots_for_risk(effective_equity, active_risk_pct, risk_pips, pv,
                                   vol_min, vol_max, vol_step)
        if lots <= 0.0:
            print(f"🛑 [Sizing Refusal] {symbol}: {info.get('status')} - budget ${info.get('budget_usd')} exceeded by min lot risk (${info.get('min_lot_risk_usd')})")
            return 0.0

        return lots

    def check_daily_discipline(self) -> bool:
        """Enforces daily trade cap and circuit breaker rules based on actual MT5 filled deals."""
        now_utc = datetime.now(timezone.utc)
        start_of_day = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
        deals = mt5.history_deals_get(start_of_day, now_utc)
        filled_today = 0
        if deals:
            filled_today = sum(1 for d in deals if d.magic == MAGIC_NUMBER and d.entry == mt5.DEAL_ENTRY_IN)

        self.daily_trade_count = filled_today

        if self.daily_trade_count >= MAX_DAILY_TRADES:
            print(f"🛑 Daily trade cap reached ({self.daily_trade_count}/{MAX_DAILY_TRADES} filled trades). Stopping for today.")
            return False

        if self.daily_consecutive_losses >= CIRCUIT_BREAKER_LOSSES:
            print(f"🚨 Circuit breaker triggered ({CIRCUIT_BREAKER_LOSSES} losses). Trading locked until tomorrow.")
            return False

        return True

    def count_open_positions(self, symbol: str = None) -> int:
        """Returns number of active positions with our magic number."""
        positions = mt5.positions_get()
        if positions is None:
            return 0
        if symbol:
            clean_sym = symbol.replace("m", "").replace(".r", "").replace("z", "").upper()
            return sum(1 for p in positions if p.magic == MAGIC_NUMBER and clean_sym in p.symbol.upper())
        return sum(1 for p in positions if p.magic == MAGIC_NUMBER)

    def count_active_orders(self, symbol: str = None) -> int:
        """Returns number of active pending limit orders with our magic number."""
        orders = mt5.orders_get()
        if orders is None:
            return 0
        if symbol:
            clean_sym = symbol.replace("m", "").replace(".r", "").replace("z", "").upper()
            return sum(1 for o in orders if o.magic == MAGIC_NUMBER and clean_sym in o.symbol.upper())
        return sum(1 for o in orders if o.magic == MAGIC_NUMBER)

    def get_portfolio_context(self) -> dict:
        """
        Retrieves real-time portfolio metrics from MT5:
          - open_trades: active positions with our magic number
          - usd_exposure: active positions involving USD
          - daily_pnl_pct: realized + floating PnL today relative to account balance
        """
        positions = mt5.positions_get()
        our_positions = [p for p in positions if p.magic == MAGIC_NUMBER] if positions else []
        open_trades = len(our_positions)
        usd_exposure = sum(1 for p in our_positions if "USD" in p.symbol.upper())

        now_utc = datetime.now(timezone.utc)
        start_of_day = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
        deals = mt5.history_deals_get(start_of_day, now_utc) or []
        realized_pnl = sum(
            d.profit + d.swap + d.commission
            for d in deals
            if d.magic == MAGIC_NUMBER and d.entry == mt5.DEAL_ENTRY_OUT
        )
        floating_pnl = sum(p.profit for p in our_positions)
        total_pnl = realized_pnl + floating_pnl

        summary = self.mt5_client.get_account_summary()
        balance = summary["balance"] if summary and summary.get("balance", 0) > 0 else self.starting_balance
        daily_pnl_pct = (total_pnl / balance) * 100.0 if balance > 0 else 0.0

        return {
            "open_trades": open_trades,
            "usd_exposure": usd_exposure,
            "daily_pnl_pct": round(daily_pnl_pct, 2)
        }

    def place_limit_order(self, setup: dict, is_news_trade: bool = False) -> bool:
        """Places a native pending limit order on Exness MT5."""
        if not self.check_daily_discipline():
            return False

        symbol = self.mt5_client.resolve_symbol(setup["pair"])
        setup_time = setup.get("datetime") or setup.get("timestamp") or setup.get("bar", 0)
        setup_key = f"{symbol}_{setup_time}_{setup['order_type']}"
        if setup_key in self.last_placed_setup:
            return False

        # Guard: Ensure we do not already have an active pending order on this symbol
        if self.count_active_orders(symbol) > 0:
            return False

        # Guard: Ensure we do not already have an active position open on this symbol
        if self.count_open_positions(symbol) > 0:
            return False

        # Guard: Check total portfolio exposure (active positions + active pending limit orders)
        total_exposure = self.count_open_positions() + self.count_active_orders()
        if total_exposure >= MAX_CONCURRENT_TRADES:
            print(f"⚠️ Max concurrent portfolio exposure reached ({MAX_CONCURRENT_TRADES}). Skipping order.")
            return False

        # Turtle Portfolio Correlation Guard: Max 2 concurrent positions in closely correlated assets
        open_pos = self.mt5_client.get_open_positions() or []
        open_symbols = [p["symbol"].upper() for p in open_pos]
        if "JPY" in symbol.upper():
            jpy_count = sum(1 for s in open_symbols if "JPY" in s)
            if jpy_count >= 2:
                print(f"🛑 [Turtle Correlation Guard] Max 2 JPY-correlated positions reached ({jpy_count} active). Skipping {symbol}.")
                return False
        if symbol.upper().endswith("USD"):
            usd_count = sum(1 for s in open_symbols if s.endswith("USD"))
            if usd_count >= 2:
                print(f"🛑 [Turtle Correlation Guard] Max 2 USD-quote positions reached ({usd_count} active). Skipping {symbol}.")
                return False

        order_type_str = setup["order_type"]
        entry_price = setup["limit_entry"]
        sl_price = setup["stop_loss"]
        tp_price = setup["take_profit"]
        risk_pips = setup["risk_pips"]
        rr = setup.get("rr_ratio", 1.8)

        # Calculate lot size
        lot_size = self.calculate_lot_size(symbol, risk_pips, is_news_trade=is_news_trade)
        if lot_size <= 0.0:
            print(f"🛑 [Sizing Refusal] Order rejected for {symbol}: risk exceeds budget or bad input. Skipping.")
            return False

        order_type = mt5.ORDER_TYPE_BUY_LIMIT if order_type_str == "BUY_LIMIT" else mt5.ORDER_TYPE_SELL_LIMIT

        # Autonomous Invariant Verification via ExecutionSentinel
        tick = mt5.symbol_info_tick(symbol)
        details = self.mt5_client.get_symbol_details(symbol)
        cur_bid = tick.bid if tick else (details["bid"] if details else 0.0)
        cur_ask = tick.ask if tick else (details["ask"] if details else 0.0)
        pip = pip_size(symbol)
        current_spread_pips = (cur_ask - cur_bid) / pip if pip > 0 else 0.0
        atr = setup.get("atr_pips", 10.0) * pip

        # Guard: Stop-to-Spread Ratio Floor (Skip setups where risk < 8x live spread)
        if current_spread_pips and risk_pips < 8.0 * current_spread_pips:
            print(f"🛑 [Execution Guard] Stop size too tight relative to live spread ({risk_pips:.1f}p < 8x {current_spread_pips:.1f}p spread). Skipping.")
            return False

        inv = self.sentinel.validate_pre_trade_invariants(
            symbol=symbol,
            order_type=order_type_str,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            risk_pips=risk_pips,
            rr_ratio=rr,
            current_bid=cur_bid,
            current_ask=cur_ask,
            current_spread_pips=current_spread_pips,
            atr=atr,
            pip=pip
        )
        current_session = self.guardian.session_guardian.get_market_state(datetime.now(timezone.utc))["session"]
        archetype = setup.get("archetype", "CORE_SMC_M5")
        atr_pips = round(atr / pip, 2) if pip > 0 else round(atr, 2)

        if not inv["passed"]:
            print(f"🛑 [EXECUTION SENTINEL] Order rejected by invariant gatekeeper! Rule: {inv['rule']} | Detail: {inv['detail']}")
            self.recorder.log_proposal(
                symbol=symbol,
                timeframe=f"M{setup.get('timeframe_m', 5)}",
                order_type=order_type_str,
                archetype=archetype,
                session=current_session,
                entry_price=entry_price,
                sl_price=sl_price,
                tp_price=tp_price,
                risk_pips=risk_pips,
                rr_ratio=rr,
                current_spread_pips=current_spread_pips,
                atr_pips=atr_pips,
                lot_size=lot_size,
                sentinel_passed=False,
                sentinel_rule=inv['rule']
            )
            return False

        # System 1 Pre-Trade Confluence Gating via Hybrid Decision Guardian (Jev Primary + Laya Backup)
        gate = None
        if hasattr(self, 'hybrid_guardian') and self.hybrid_guardian:
            macro_ctx = {
                "spread_pips": round(current_spread_pips, 2),
                "session": current_session,
                "liquidity_state": "EXPANDING_TREND" if "TREND" in archetype else "LIQUIDITY_SWEEP"
            }
            gate = self.hybrid_guardian.evaluate_pre_trade_setup(setup, macro_ctx)
            engine_name = gate.get("engine", "SYSTEM_1")
            rating = gate.get("risk_rating") or gate.get("conviction", "NORMAL")
            allow_p = gate.get("allow_probability", 0.5)
            lat_ms = gate.get("latency_ms", 0.0)
            print(f"🧠 [{engine_name}] Pre-Trade Gate: {rating} (allow_prob={allow_p:.2f}) in {lat_ms:.1f}ms")
            if not gate.get("approved", True):
                print(f"🛑 [{engine_name}] Order vetoed! Risk: {rating}")
                self.recorder.log_proposal(
                    symbol=symbol,
                    timeframe=f"M{setup.get('timeframe_m', 5)}",
                    order_type=order_type_str,
                    archetype=archetype,
                    session=current_session,
                    entry_price=entry_price,
                    sl_price=sl_price,
                    tp_price=tp_price,
                    risk_pips=risk_pips,
                    rr_ratio=rr,
                    current_spread_pips=current_spread_pips,
                    atr_pips=atr_pips,
                    lot_size=lot_size,
                    sentinel_passed=True,
                    hybrid_verdict=gate
                )
                return False

        # System 3: Institutional 3-Agent Committee Arbitration
        if hasattr(self, 'committee') and self.committee:
            portfolio_ctx = self.get_portfolio_context()
            is_news_quarantine = (
                self.news_radar.is_in_quarantine()
                if hasattr(self, 'news_radar') and self.news_radar
                else False
            )
            macro_comm_ctx = {
                "spread_pips": round(current_spread_pips, 2),
                "session": current_session,
                "liquidity_state": "EXPANDING_TREND" if "TREND" in archetype else "LIQUIDITY_SWEEP",
                "news_threat": is_news_quarantine
            }
            comm_res = self.committee.evaluate_setup(setup, macro_comm_ctx, portfolio_ctx)
            print(f"🏛️ [Institutional Committee] Decision: {comm_res.get('decision')} (Multiplier: {comm_res.get('lot_multiplier')}x)")
            if not comm_res.get("approved", True):
                print(f"🛑 [Institutional Committee] Order vetoed by {comm_res.get('veto_agent')}: {comm_res.get('reasoning')}")
                self.recorder.log_proposal(
                    symbol=symbol,
                    timeframe=f"M{setup.get('timeframe_m', 5)}",
                    order_type=order_type_str,
                    archetype=archetype,
                    session=current_session,
                    entry_price=entry_price,
                    sl_price=sl_price,
                    tp_price=tp_price,
                    risk_pips=risk_pips,
                    rr_ratio=rr,
                    current_spread_pips=current_spread_pips,
                    atr_pips=atr_pips,
                    lot_size=lot_size,
                    sentinel_passed=True,
                    hybrid_verdict=gate
                )
                return False
            lot_multiplier = comm_res.get("lot_multiplier", 1.0)
            if lot_multiplier < 1.0:
                lot_size = max(0.01, round(lot_size * lot_multiplier, 2))
                print(f"  ⚖️ Committee adjusted lot size to {lot_size} lots ({lot_multiplier}x conviction)")

        print(f"\n🚀 PREPARING SMC ORDER: {symbol} {order_type_str}")
        print(f"  • Trade Classification : {'⚡ POST-NEWS JUDAS (HOUSE MONEY)' if is_news_trade else archetype}")
        print(f"  • Entry Limit Price    : {entry_price}")
        print(f"  • Stop Loss            : {sl_price} ({risk_pips} pips)")
        print(f"  • Take Profit (1:{rr}R): {tp_price}")
        print(f"  • Calculated Lots      : {lot_size} lots")

        if self.dry_run:
            print("  ℹ️ [DRY RUN ACTIVE] Order logged but not sent to broker.")
            return True

        # Send order to Exness
        arch_tag = "TRN" if "TREND" in archetype else "SWP"
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 10,
            "magic": MAGIC_NUMBER,
            "comment": f"IBT_{arch_tag}_RR{setup['rr_ratio']}",
            "type_time": mt5.ORDER_TIME_DAY, # Auto-cancels at end of day if unfilled
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err = result.comment if result else mt5.last_error()
            print(f"❌ Order Placement Failed: {err}")
            return False

        print(f"✅ Pending Order Successfully Placed on Exness! Ticket: {result.order}")
        self.last_placed_setup.add(setup_key)
        # Note: Filled executions are tracked dynamically via MT5 history deals in check_daily_discipline()
        self.recorder.log_proposal(
            symbol=symbol,
            timeframe=f"M{setup.get('timeframe_m', 5)}",
            order_type=order_type_str,
            archetype=archetype,
            session=current_session,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            risk_pips=risk_pips,
            rr_ratio=rr,
            current_spread_pips=current_spread_pips,
            atr_pips=atr_pips,
            lot_size=lot_size,
            sentinel_passed=True,
            hybrid_verdict=gate,
            order_ticket=result.order
        )
        self.tree_logger.log_node({
            "event": "LIMIT_ORDER_PLACED",
            "symbol": symbol,
            "archetype": archetype,
            "order_ticket": result.order,
            "order_type": order_type_str,
            "entry": entry_price,
            "sl": sl_price,
            "tp": tp_price,
            "risk_pips": risk_pips,
            "rr": rr,
            "lot_size": lot_size,
            "is_news_trade": is_news_trade
        })
        # Dispatch Telegram notification with rendered chart photo
        summary = self.mt5_client.get_account_summary()
        guardian_info = gate if 'gate' in locals() else None

        def on_order_snapshot_rendered(img_path):
            if hasattr(self, 'telegram') and self.telegram:
                self.telegram.notify_order_placed(
                    symbol=symbol,
                    order_type=order_type_str,
                    ticket=result.order,
                    entry_price=entry_price,
                    sl_price=sl_price,
                    tp_price=tp_price,
                    risk_pips=risk_pips,
                    rr_ratio=rr,
                    lot_size=lot_size,
                    archetype=archetype,
                    guardian_info=guardian_info,
                    account_summary=summary,
                    image_path=img_path
                )

        if hasattr(self, 'chart_snapshots') and self.chart_snapshots:
            self.chart_snapshots.capture_async(
                symbol=symbol,
                event_type="LIMIT_ORDER_PLACED",
                ticket=result.order,
                entry_price=entry_price,
                sl_price=sl_price,
                tp_price=tp_price,
                extra_info={"lots": lot_size, "archetype": archetype},
                callback=on_order_snapshot_rendered
            )
        elif hasattr(self, 'telegram') and self.telegram:
            self.telegram.notify_order_placed(
                symbol=symbol,
                order_type=order_type_str,
                ticket=result.order,
                entry_price=entry_price,
                sl_price=sl_price,
                tp_price=tp_price,
                risk_pips=risk_pips,
                rr_ratio=rr,
                lot_size=lot_size,
                archetype=archetype,
                guardian_info=guardian_info,
                account_summary=summary,
                image_path=None
            )
        return True

    def manage_active_positions(self):
        """
        Audits active positions exclusively via Autonomous In-Flight Co-Pilot.
        Includes a native deterministic fail-safe in case the copilot encounters an error.
        """
        if hasattr(self, 'inflight_copilot') and self.inflight_copilot:
            try:
                self.inflight_copilot.audit_active_positions(magic_number=MAGIC_NUMBER)
                return
            except Exception as e:
                print(f"⚠️ [InFlight Co-Pilot] Audit failed: {e}. Executing native fail-safe break-even.")

        # Fail-safe break-even fallback
        self.native_failsafe_breakeven()

    def native_failsafe_breakeven(self):
        """Deterministic fail-safe break-even check (+0.7R -> open + 0.3 pips)."""
        positions = mt5.positions_get()
        if not positions:
            return
        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue
            symbol = pos.symbol
            pip = pip_size(symbol)
            is_buy = (pos.type == mt5.ORDER_TYPE_BUY)
            open_p = pos.price_open
            cur_p = pos.price_current
            sl = pos.sl
            tp = pos.tp
            risk_dist = abs(open_p - sl)
            if risk_dist <= 0:
                continue
            current_gain = (cur_p - open_p) if is_buy else (open_p - cur_p)
            current_r = current_gain / risk_dist
            be_level = open_p + (0.3 * pip) if is_buy else open_p - (0.3 * pip)
            sl_needs_update = (sl < open_p) if is_buy else (sl > open_p)
            if current_r >= 0.7 and sl_needs_update:
                req = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "symbol": symbol,
                    "sl": round(be_level, 3 if "JPY" in symbol else 5),
                    "tp": tp,
                }
                res = mt5.order_send(req)
                if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"🛡️ [Fail-Safe Break-Even] Position #{pos.ticket} secured at {be_level}")

    def cancel_all_pending_orders(self, reason: str = ""):
        """Cancels all active pending limit orders placed by this EA."""
        orders = mt5.orders_get()
        if not orders:
            return

        for o in orders:
            if o.magic == MAGIC_NUMBER:
                print(f"🛑 CANCELLING PENDING ORDER #{o.ticket} on {o.symbol} | Reason: {reason}")
                req = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": o.ticket
                }
                res = mt5.order_send(req)
                if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"✅ Order #{o.ticket} successfully removed.")
                else:
                    err = res.comment if res else mt5.last_error()
                    print(f"⚠️ Failed to remove order #{o.ticket}: {err}")

    def purge_expired_pending_orders(self, max_bars: int = 8, timeframe_m: int = 5):
        """
        In-Flight Order Watchdog enforcing:
        1. Target Pre-Emption Invalidation: If price reached TP before fill, cancel order.
        2. Adverse Price Runaway: If price expanded > 1.8x target distance in profit direction.
        3. Adverse Drop: If price already crossed SL before fill.
        4. 8-Bar Limit Timeout (40 minutes on M5): Purges unfilled limit orders after 8 bars.
        """
        orders = mt5.orders_get()
        if not orders:
            return

        for o in orders:
            if o.magic != MAGIC_NUMBER:
                continue

            tick = mt5.symbol_info_tick(o.symbol)
            cur_bid = tick.bid if tick else 0.0
            cur_ask = tick.ask if tick else 0.0

            should_cancel, cancel_reason = self.sentinel.audit_in_flight_pending_order(
                ticket=o.ticket,
                symbol=o.symbol,
                order_type=o.type,
                price_open=o.price_open,
                sl=o.sl,
                tp=o.tp,
                time_setup=o.time_setup,
                current_bid=cur_bid,
                current_ask=cur_ask,
                timeframe_m=timeframe_m,
                max_bars=max_bars
            )

            if should_cancel:
                print(f"🛑 [SENTINEL IN-FLIGHT WATCHDOG] Order #{o.ticket} on {o.symbol} CANCELLED: {cancel_reason}")
                req = {
                    "action": mt5.TRADE_ACTION_REMOVE,
                    "order": o.ticket
                }
                res = mt5.order_send(req)
                if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"✅ Order #{o.ticket} successfully removed from broker.")
                else:
                    err = res.comment if res else mt5.last_error()
                    print(f"⚠️ Failed to remove order #{o.ticket}: {err}")

    def audit_closed_deals(self):
        """
        Polls closed deals from MT5 history, runs ExecutionSentinel forensic audit
        (detecting flash stop-outs < 180s and excessive slippage blowout),
        and logs them to the Dream-RSI Discovery Tree.
        """
        now = datetime.utcnow()
        start = datetime(now.year, now.month, now.day)
        deals = mt5.history_deals_get(start, datetime.now())
        if deals is None:
            return

        for d in deals:
            if d.magic != MAGIC_NUMBER or d.entry != mt5.DEAL_ENTRY_OUT:
                continue
            if d.ticket in self.audited_deals:
                continue

            self.audited_deals.add(d.ticket)
            won = d.profit > 0
            self.last_trade_won = won
            if won:
                self.daily_consecutive_losses = 0
            else:
                self.daily_consecutive_losses += 1

            # Lookup entry deal to calculate exact trade lifetime and entry price
            pos_deals = mt5.history_deals_get(position=d.position_id)
            entry_time = d.time
            entry_price = d.price
            if pos_deals:
                entry_deal = next((p for p in pos_deals if p.entry == mt5.DEAL_ENTRY_IN), None)
                if entry_deal:
                    entry_time = entry_deal.time
                    entry_price = entry_deal.price

            planned_risk_usd = self.starting_balance * self.base_risk_pct
            sentinel_res = self.sentinel.audit_closed_deal(
                ticket=d.ticket,
                symbol=d.symbol,
                order_ticket=d.order,
                entry_time=entry_time,
                exit_time=d.time,
                entry_price=entry_price,
                exit_price=d.price,
                profit_usd=d.profit,
                planned_risk_usd=planned_risk_usd
            )

            # System 1 Forensic Triage via Laya Guardian
            if sentinel_res and sentinel_res.get("anomaly_detected") and hasattr(self, 'laya') and self.laya and self.laya.enabled:
                duration_sec = d.time - entry_time
                telemetry = {
                    "symbol": d.symbol,
                    "duration_seconds": duration_sec,
                    "profit_usd": d.profit,
                    "planned_risk_usd": planned_risk_usd,
                    "entry_price": entry_price,
                    "exit_price": d.price
                }
                triage = self.laya.triage_execution_incident(telemetry)
                if not triage.get("fallback", False):
                    print(f"🧠 [LAYA GUARDIAN] Incident Forensic Triage: Cause = {triage['root_cause']} | Quarantine = {triage['quarantine_minutes']}m (conf={triage['confidence']:.2f}) in {triage['latency_ms']:.1f}ms")
                    if triage["quarantine_minutes"] > 60:
                        self.sentinel.quarantine_symbol(d.symbol, duration_minutes=triage["quarantine_minutes"], reason=f"Laya Triage: {triage['root_cause']}")

            # High-Fidelity Microstructure Telemetry recording
            self.recorder.record_closed_deal(
                order_ticket=d.order,
                deal_ticket=d.ticket,
                symbol=d.symbol,
                entry_time_ts=entry_time,
                exit_time_ts=d.time,
                entry_price=entry_price,
                exit_price=d.price,
                profit_usd=d.profit,
                planned_risk_usd=planned_risk_usd
            )

            self.tree_logger.log_node({
                "event": "DEAL_CLOSED",
                "symbol": d.symbol,
                "deal_ticket": d.ticket,
                "order_ticket": d.order,
                "position_ticket": d.position_id,
                "profit_usd": round(d.profit, 2),
                "volume": d.volume,
                "price": d.price,
                "comment": d.comment,
                "outcome": "WIN" if won else "LOSS"
            })
            print(f"📊 [Dream-RSI Node] Logged closed deal #{d.ticket} ({d.symbol}): Profit ${d.profit:+.2f} ({'WIN' if won else 'LOSS'})")
            # Dispatch Telegram notification with autopsy chart photo
            summary = self.mt5_client.get_account_summary()
            deal_profit = round(d.profit, 2)
            deal_won = won
            deal_comment = d.comment

            def on_close_snapshot_rendered(img_path):
                if hasattr(self, 'telegram') and self.telegram:
                    self.telegram.notify_trade_closed(
                        symbol=d.symbol,
                        deal_ticket=d.ticket,
                        position_ticket=d.position_id,
                        outcome="WIN" if deal_won else "LOSS",
                        profit_usd=deal_profit,
                        entry_price=entry_price,
                        exit_price=d.price,
                        comment=deal_comment,
                        account_summary=summary,
                        image_path=img_path
                    )

            if hasattr(self, 'chart_snapshots') and self.chart_snapshots:
                self.chart_snapshots.capture_async(
                    symbol=d.symbol,
                    event_type="TRADE_CLOSED",
                    ticket=d.ticket,
                    entry_price=entry_price,
                    exit_price=d.price,
                    extra_info={"profit_usd": deal_profit, "outcome": "WIN" if deal_won else "LOSS"},
                    callback=on_close_snapshot_rendered
                )
            elif hasattr(self, 'telegram') and self.telegram:
                self.telegram.notify_trade_closed(
                    symbol=d.symbol,
                    deal_ticket=d.ticket,
                    position_ticket=d.position_id,
                    outcome="WIN" if deal_won else "LOSS",
                    profit_usd=deal_profit,
                    entry_price=entry_price,
                    exit_price=d.price,
                    comment=deal_comment,
                    account_summary=summary,
                    image_path=None
                )

    def run_scan_cycle(self, pairs: list = None, timeframe_m: int = 5):
        """
        Fetches live candles from Exness, audits timing and economic news,
        and evaluates SMC setups only when market conditions are safe.
        """
        if pairs is None:
            pairs = ["GBPJPY", "USDCAD", "EURJPY", "USDJPY", "GBPUSD", "EURUSD", "USDCHF"]

        mt5_tf = mt5.TIMEFRAME_M5 if timeframe_m == 5 else mt5.TIMEFRAME_M15
        tf_label = f"M{timeframe_m}"

        print(f"\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}] Scanning {len(pairs)} assets on {tf_label} with Institutional Awareness...")

        # Zero-downtime hot-reload check
        if hasattr(self, 'model_watcher') and self.model_watcher:
            self.model_watcher.check_for_updates()

        # Pillar 1: Sub-Second Breaking News & Geopolitical Shock Radar
        if hasattr(self, 'news_radar') and self.news_radar:
            radar_res = self.news_radar.audit_market_safety()
            if radar_res.get("kill_switch_active"):
                print(f"🚨 [NEWS RADAR KILL-SWITCH] {radar_res.get('reason')}. Cancelling pending orders.")
                self.cancel_all_pending_orders(reason="NEWS_RADAR_KILL_SWITCH")
                return

        self.manage_active_positions()
        self.purge_expired_pending_orders(max_bars=8, timeframe_m=timeframe_m)
        self.audit_closed_deals()

        # Daily Rollover Autonomous Overnight Learner Trigger (21:00 UTC)
        now_utc = datetime.utcnow()
        if now_utc.hour >= 21 and self.last_overnight_run != now_utc.date():
            self.last_overnight_run = now_utc.date()
            print("\n🌙 [Daily Rollover Gate] Market swap settlement active. Launching Autonomous Overnight Learner...")
            try:
                from exness.overnight_learner import OvernightLearner
                learner = OvernightLearner()
                learner.run_nightly_learning_cycle()
            except Exception as e:
                print(f"⚠️ [Overnight Learner] Exception: {e}")

        for pair in pairs:
            # Check live spread if connected
            details = self.mt5_client.get_symbol_details(pair)
            current_spread_pips = None
            if details:
                pip = pip_size(pair)
                current_spread_pips = (details["ask"] - details["bid"]) / pip

            # 1. Market Awareness Guardian Audit
            perm = self.guardian.evaluate_trading_permission(pair, current_spread_pips=current_spread_pips)

            if not perm["permitted"]:
                print(f"  🛑 [{pair:7s}] BLOCKED: {perm['reason']}")
                if perm.get("action") == "CANCEL_PENDINGS_HOLD_OFF":
                    self.cancel_all_pending_orders(reason=perm["reason"])
                continue

            # 2. News Opportunity Tagging
            is_news_trade = perm.get("is_post_news_window", False)
            if is_news_trade:
                print(f"  ⚡ [{pair:7s}] POST-NEWS OPPORTUNITY WINDOW ACTIVE (Funded by News Vault: ${self.news_vault:.2f})")

            # 3. Technical SMC Scanning
            df = self.mt5_client.fetch_rates(pair, mt5_tf, 300)
            if df is None or len(df) < 50:
                print(f"  ⚠️ [{pair:7s}] Insufficient data received from broker.")
                continue

            setups = analyze_m15_setup(df, pair)
            if setups:
                latest_setup = setups[-1]
                # Check if setup is on the current bar
                if latest_setup["bar"] >= len(df) - 2:
                    self.place_limit_order(latest_setup, is_news_trade=is_news_trade)
                else:
                    bars_ago = len(df) - 1 - latest_setup["bar"]
                    spread_str = f"{current_spread_pips:4.1f}p" if current_spread_pips is not None else " N/A"
                    print(f"  ✓ [{pair:7s}] Spread: {spread_str} | Status: ACTIVE | Last: {latest_setup['order_type']} ({bars_ago} bars ago)")
            else:
                spread_str = f"{current_spread_pips:4.1f}p" if current_spread_pips is not None else " N/A"
                print(f"  ✓ [{pair:7s}] Spread: {spread_str} | Status: ACTIVE | Consolidating (Awaiting FVG)")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Exness MT5 Automated SMC Trading System [PrasaD]")
    parser.add_argument("--live", action="store_true", help="Enable Live Demo Order Execution (Default: Dry Run / Monitor)")
    parser.add_argument("--loop", action="store_true", help="Run in continuous 60s background scanning loop")
    parser.add_argument("--timeframe", type=int, default=5, choices=[5, 15], help="Execution timeframe in minutes (default: 5 for M5 intraday)")
    parser.add_argument("--risk", type=float, default=0.005, help="Risk percentage per trade (default: 0.005 = 0.5% conservative institutional posture)")
    parser.add_argument("--capital", type=float, default=500.0, help="Starting balance for risk calculations in USD (default: 500.0, matches ~₹41,750 live capital base)")
    parser.add_argument("--mm", type=str, default="fixed_fractional", choices=["anti_martingale", "fixed_fractional", "news_reserve"], help="Money management mode")
    parser.add_argument("--pairs", type=str, default="GBPJPY,USDCAD,EURJPY,USDJPY,GBPUSD,EURUSD,USDCHF", help="Validated positive-expectancy pairs to trade (NZDUSD and AUDUSD excluded)")
    parser.add_argument("--no-laya", action="store_true", help="Disable Local Laya Backup")
    parser.add_argument("--no-jev", action="store_true", help="Disable TypeSafe Jev Primary Engine")

    args = parser.parse_args()
    pair_list = [p.strip().upper() for p in args.pairs.split(",") if p.strip()]

    dry_run = not args.live

    print("=" * 70)
    print("   EXNESS MT5 MULTI-ASSET SMC ENGINE — PRASAD / KSM X TECH")
    print(f"   Execution Mode : {'🟢 LIVE DEMO EXECUTION' if not dry_run else '🟡 DRY RUN (MONITOR ONLY)'}")
    print(f"   Timeframe      : M{args.timeframe} Intraday (High Frequency)")
    print(f"   Money Mgmt     : {args.mm.upper()} (Base Risk: {args.risk*100:.1f}%)")
    print(f"   Capital Base   : ${args.capital:,.2f} USD (~₹{args.capital*83.5:,.0f})")
    print(f"   Active Assets  : {', '.join(pair_list)}")
    print(f"   Primary AI     : {'DISABLED (--no-jev)' if args.no_jev else 'TypeSafe Jev System One (Cloud API, ~350ms)'}")
    print(f"   Backup AI      : {'DISABLED (--no-laya)' if args.no_laya else 'Local Laya 421M (ModernBERT-RLCD on CUDA)'}")
    print("=" * 70)

    trader = ExnessTrader(
        risk_pct=args.risk,
        mm_mode=args.mm,
        starting_balance=args.capital,
        dry_run=dry_run,
        enable_laya=not args.no_laya,
        use_jev=not args.no_jev
    )

    if not trader.initialize():
        sys.exit(1)

    try:
        if args.loop:
            print(f"🔄 Starting continuous M{args.timeframe} market scan loop (Polling every 60 seconds)...")
            print("   Press Ctrl+C at any time to halt.\n")
            while True:
                trader.run_scan_cycle(pair_list, timeframe_m=args.timeframe)
                time.sleep(60)
        else:
            # Single immediate scan
            trader.run_scan_cycle(pair_list, timeframe_m=args.timeframe)
            print("\n✅ Single scan complete. Use '--loop' for continuous real-time trading.")
    except KeyboardInterrupt:
        print("\n🛑 Manual stop detected by user.")
    finally:
        trader.mt5_client.disconnect()
