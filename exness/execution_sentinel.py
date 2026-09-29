"""
exness/execution_sentinel.py — Autonomous Execution Sentinel & Invariant Guardian.
Institutional-grade pre-flight verification, in-flight order monitoring,
and post-trade forensic anomaly detection.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import json
import time
from datetime import datetime
import MetaTrader5 as mt5

class ExecutionSentinel:
    """
    Autonomous Pre-Trade, In-Flight, and Post-Trade Immune System.
    Prevents execution errors, catches runaway targets, enforces volatility floors,
    and detects execution anomalies without requiring human monitoring.
    """
    def __init__(self, incidents_file: str = None):
        if incidents_file is None:
            self.incidents_file = os.path.join(os.path.dirname(__file__), "..", "data", "execution_incidents.json")
        else:
            self.incidents_file = incidents_file
        self.quarantined_symbols = {} # symbol -> unquarantine_timestamp
        self.load_incidents()

    def load_incidents(self):
        self.incidents = []
        if os.path.exists(self.incidents_file):
            try:
                with open(self.incidents_file, "r", encoding="utf-8") as f:
                    self.incidents = json.load(f)
            except Exception:
                self.incidents = []

    def record_incident(self, incident: dict):
        incident["timestamp"] = datetime.utcnow().isoformat()
        self.incidents.append(incident)
        try:
            os.makedirs(os.path.dirname(self.incidents_file), exist_ok=True)
            with open(self.incidents_file, "w", encoding="utf-8") as f:
                json.dump(self.incidents, f, indent=2)
        except Exception as e:
            print(f"[Sentinel Warning] Failed to write incident file: {e}")

    def is_symbol_quarantined(self, symbol: str) -> tuple[bool, str]:
        """Checks if an asset is temporarily locked due to an execution anomaly."""
        clean = symbol.replace("m", "").replace(".r", "").upper()
        now = time.time()
        if clean in self.quarantined_symbols:
            unquar_time = self.quarantined_symbols[clean]
            if now < unquar_time:
                remaining_m = (unquar_time - now) / 60.0
                return True, f"Quarantined due to prior anomaly ({remaining_m:.1f}m remaining)"
            else:
                del self.quarantined_symbols[clean]
        return False, ""

    def quarantine_symbol(self, symbol: str, duration_minutes: int = 60, reason: str = ""):
        clean = symbol.replace("m", "").replace(".r", "").upper()
        self.quarantined_symbols[clean] = time.time() + (duration_minutes * 60)
        print(f"[SENTINEL QUARANTINE] {clean} quarantined for {duration_minutes}m! Reason: {reason}")
        self.record_incident({
            "type": "SYMBOL_QUARANTINE",
            "symbol": clean,
            "duration_minutes": duration_minutes,
            "reason": reason
        })

    def validate_pre_trade_invariants(
        self,
        symbol: str,
        order_type: str,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        risk_pips: float,
        rr_ratio: float,
        current_bid: float,
        current_ask: float,
        current_spread_pips: float,
        atr: float,
        pip: float
    ) -> dict:
        """
        Pre-Flight Invariant Gatekeeper.
        Evaluates institutional invariants BEFORE sending an order to the broker.
        If any invariant is violated, the order is rejected.
        """
        # Check Quarantine
        quar, q_reason = self.is_symbol_quarantined(symbol)
        if quar:
            return {"passed": False, "rule": "QUARANTINE_ACTIVE", "detail": q_reason}

        is_gold = ("XAU" in symbol.upper() or "GOLD" in symbol.upper())
        is_buy = ("BUY" in order_type.upper())

        # 1. Price Geometry Invariant (Must be a true discount/premium pending order, not immediate market chase)
        if is_buy:
            if entry_price >= current_ask:
                return {
                    "passed": False,
                    "rule": "INVARIANT_PRICE_GEOMETRY",
                    "detail": f"Buy Limit entry ({entry_price}) >= current Ask ({current_ask}). Would fill immediately as market order!"
                }
            if sl_price >= entry_price:
                return {"passed": False, "rule": "INVARIANT_SL_LOGIC", "detail": f"Buy SL ({sl_price}) >= Entry ({entry_price})"}
            if tp_price <= entry_price:
                return {"passed": False, "rule": "INVARIANT_TP_LOGIC", "detail": f"Buy TP ({tp_price}) <= Entry ({entry_price})"}
        else:
            if entry_price <= current_bid:
                return {
                    "passed": False,
                    "rule": "INVARIANT_PRICE_GEOMETRY",
                    "detail": f"Sell Limit entry ({entry_price}) <= current Bid ({current_bid}). Would fill immediately as market order!"
                }
            if sl_price <= entry_price:
                return {"passed": False, "rule": "INVARIANT_SL_LOGIC", "detail": f"Sell SL ({sl_price}) <= Entry ({entry_price})"}
            if tp_price >= entry_price:
                return {"passed": False, "rule": "INVARIANT_TP_LOGIC", "detail": f"Sell TP ({tp_price}) >= Entry ({entry_price})"}

        # 2. Minimum Volatility Floor Invariant (Gold: min $5.00 / 50 pips, FX: min 5 pips or 0.8x ATR)
        sl_distance = abs(entry_price - sl_price)
        min_vol_dist = (5.0 if is_gold else max(5.0 * pip, 0.8 * atr))
        if sl_distance < min_vol_dist:
            return {
                "passed": False,
                "rule": "INVARIANT_VOLATILITY_FLOOR",
                "detail": f"SL distance ({sl_distance:.3f}) < required volatility floor ({min_vol_dist:.3f}). Stop loss too tight for normal candle wicks!"
            }

        # 3. Spread Safety Ratio Invariant (Stop distance must be >= 4x broker spread)
        if current_spread_pips and current_spread_pips > 0:
            spread_dist = current_spread_pips * pip
            if sl_distance < 4.0 * spread_dist:
                return {
                    "passed": False,
                    "rule": "INVARIANT_SPREAD_SAFETY",
                    "detail": f"SL distance ({sl_distance/pip:.1f}p) < 4x spread ({current_spread_pips:.1f}p * 4 = {4*current_spread_pips:.1f}p). Trade vulnerable to spread noise!"
                }

        # 4. Reward-to-Risk Sanity
        if rr_ratio < 0.4 or rr_ratio > 3.0:
            return {
                "passed": False,
                "rule": "INVARIANT_RR_BOUNDS",
                "detail": f"Target RR ({rr_ratio}) outside safe institutional envelope [0.4, 3.0]"
            }

        return {"passed": True, "rule": "ALL_INVARIANTS_PASSED", "detail": "Pre-trade parameters certified"}

    def audit_in_flight_pending_order(
        self,
        ticket: int,
        symbol: str,
        order_type: int, # mt5.ORDER_TYPE_BUY_LIMIT or SELL_LIMIT
        price_open: float,
        sl: float,
        tp: float,
        time_setup: float,
        current_bid: float,
        current_ask: float,
        timeframe_m: int = 5,
        max_bars: int = 8
    ) -> tuple[bool, str]:
        """
        In-Flight Order Watchdog.
        Inspects pending limits on every scan cycle.
        Returns: (should_cancel: bool, reason: str)
        """
        now_ts = time.time()
        is_buy = (order_type == 2) or (order_type == getattr(mt5, 'ORDER_TYPE_BUY_LIMIT', 2)) or ("BUY" in str(order_type).upper())

        # Check 1: Target Pre-Emption Invalidation
        if tp > 0:
            if is_buy and current_bid >= tp:
                return True, f"TARGET_PREEMPTED: Market reached TP ({tp}) before fill. Subsequent pullback is counter-trend exhaustion."
            elif not is_buy and current_ask <= tp:
                return True, f"TARGET_PREEMPTED: Market reached TP ({tp}) before fill. Subsequent pullback is counter-trend exhaustion."

        # Check 2: Adverse Price Runaway (Price moved > 1.8x target distance in the profit direction)
        target_dist = abs(tp - price_open)
        if target_dist > 0:
            profit_runaway = (current_bid - price_open) if is_buy else (price_open - current_ask)
            if profit_runaway >= 1.8 * target_dist:
                return True, f"ADVERSE_EXPANSION: Price ran away {profit_runaway:.4f} (>1.8x target distance). Setup structure decayed."

        # Check 3: Adverse Drop Through SL (Price gapped through SL while pending)
        adverse_drop = (price_open - current_ask) if is_buy else (current_bid - price_open)
        risk_dist = abs(price_open - sl)
        if risk_dist > 0 and adverse_drop >= risk_dist:
            return True, f"ADVERSE_DROP: Price already crossed SL level ({sl}) before limit fill! Cancel to prevent instant loss."

        # Check 4: 8-Bar Time Decay (40 minutes on M5)
        max_age_sec = max_bars * timeframe_m * 60
        age_sec = now_ts - time_setup
        if age_sec >= max_age_sec:
            age_bars = age_sec / (timeframe_m * 60)
            return True, f"TIME_DECAY: Order elapsed {age_bars:.1f} bars (> {max_bars} bars / {max_age_sec/60:.0f}m limit)."

        return False, ""

    def audit_closed_deal(
        self,
        ticket: int,
        symbol: str,
        order_ticket: int,
        entry_time: float,
        exit_time: float,
        entry_price: float,
        exit_price: float,
        profit_usd: float,
        planned_risk_usd: float
    ) -> dict:
        """
        Post-Trade Forensic Auditor.
        Scans closed deals immediately upon execution exit.
        Detects Flash Stop-Outs (<3 min) and Extreme Slippage.
        """
        duration_sec = exit_time - entry_time
        duration_min = duration_sec / 60.0
        is_loss = (profit_usd < 0)

        result = {"anomaly_detected": False, "anomaly_type": None, "action": None}

        # Anomaly 1: Flash Stop-Out (<180 seconds on an M5 setup!)
        if is_loss and duration_sec < 180.0:
            print(f"[SENTINEL ANOMALY] Flash Stop-Out on {symbol} #{ticket}! Closed in only {duration_sec:.0f}s with loss ${profit_usd:.2f}!")
            self.quarantine_symbol(symbol, duration_minutes=60, reason=f"Flash stop-out ({duration_sec:.0f}s). Volatility / slippage check required.")
            result = {
                "anomaly_detected": True,
                "anomaly_type": "FLASH_STOP_OUT",
                "detail": f"Trade closed in {duration_sec:.0f} seconds (Expected >= 300s on M5)",
                "action": "QUARANTINE_60_MIN"
            }
            self.record_incident({
                "type": "FLASH_STOP_OUT",
                "deal_ticket": ticket,
                "order_ticket": order_ticket,
                "symbol": symbol,
                "duration_seconds": round(duration_sec, 1),
                "entry_price": entry_price,
                "exit_price": exit_price,
                "profit_usd": profit_usd,
                "planned_risk_usd": planned_risk_usd
            })
            return result

        # Anomaly 2: Extreme Slippage / Loss Blowout (>1.35x planned risk)
        if is_loss and planned_risk_usd > 0:
            actual_loss = abs(profit_usd)
            if actual_loss > 1.35 * planned_risk_usd:
                print(f"[SENTINEL ANOMALY] Extreme Slippage on {symbol} #{ticket}! Actual loss ${actual_loss:.2f} > 1.35x planned ${planned_risk_usd:.2f}!")
                result = {
                    "anomaly_detected": True,
                    "anomaly_type": "EXCESSIVE_SLIPPAGE_BLOWOUT",
                    "detail": f"Actual loss ${actual_loss:.2f} exceeded planned risk ${planned_risk_usd:.2f} by {actual_loss/planned_risk_usd:.2f}x",
                    "action": "RECORD_INCIDENT"
                }
                self.record_incident({
                    "type": "EXCESSIVE_SLIPPAGE",
                    "deal_ticket": ticket,
                    "symbol": symbol,
                    "actual_loss": actual_loss,
                    "planned_risk": planned_risk_usd
                })
                return result

        return result
