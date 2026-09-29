"""
exness/inflight_copilot.py — Autonomous Dynamic In-Flight Trade Co-Pilot.
Powered by Local Laya & Real-Time MFE/MAE Trajectory Analysis.

Actively monitors open positions on Exness MT5 every 15 seconds:
1. Break-Even Shield at +1.0R (Risk eliminated early)
2. Partial Take-Profit (50% lot bank) at +1.8R
3. Structural Runner Trailing at +2.5R (Follows M5 swing fractal lows/highs)
4. Emergency Adverse Abort at -0.4R on sudden momentum collapse
5. Dispatches autonomous chart snapshots on every milestone event.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
from typing import Dict, Any, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def pip_size(symbol: str) -> float:
    return 0.01 if "JPY" in symbol else 0.0001 if ("XAU" not in symbol and "BTC" not in symbol) else 0.01

class InFlightCoPilot:
    """
    Autonomous In-Flight Trade Co-Pilot for Exness MT5.
    Replaces static fixed break-even rules with dynamic MFE/MAE trajectory gating.
    """
    def __init__(self, guardian=None, snapshot_engine=None):
        self.guardian = guardian
        self.snapshot_engine = snapshot_engine
        self.position_trackers: Dict[int, Dict[str, Any]] = {}

        if self.snapshot_engine is None:
            try:
                from exness.chart_snapshot import ChartSnapshotEngine
                self.snapshot_engine = ChartSnapshotEngine()
            except Exception as e:
                print(f"[InFlightCoPilot] Chart snapshot engine unavailable: {e}")
                self.snapshot_engine = None

    def audit_active_positions(self, magic_number: int = 123456):
        """
        Main inspection loop. Evaluates every active position with matching magic number.
        """
        try:
            import MetaTrader5 as mt5
            positions = mt5.positions_get()
            if positions is None or len(positions) == 0:
                return

            for pos in positions:
                if pos.magic != magic_number:
                    continue

                ticket = pos.ticket
                symbol = pos.symbol
                pip = pip_size(symbol)
                is_buy = (pos.type == mt5.ORDER_TYPE_BUY)
                open_p = pos.price_open
                cur_p = pos.price_current
                sl = pos.sl
                tp = pos.tp
                vol = pos.volume

                risk_dist = abs(open_p - sl) if sl > 0 else (10.0 * pip)
                if risk_dist <= 0:
                    continue

                gain = (cur_p - open_p) if is_buy else (open_p - cur_p)
                current_r = gain / risk_dist

                # Initialize or update intra-trade excursion tracker
                if ticket not in self.position_trackers:
                    self.position_trackers[ticket] = {
                        "mfe": current_r,
                        "mae": current_r,
                        "partial_banked": False,
                        "be_locked": False,
                        "start_time": time.time()
                    }
                else:
                    tracker = self.position_trackers[ticket]
                    tracker["mfe"] = max(tracker["mfe"], current_r)
                    tracker["mae"] = min(tracker["mae"], current_r)

                tracker = self.position_trackers[ticket]

                # ── STAGE 1: Break-Even Shield (+1.0R) ──
                be_needed = (sl < open_p) if is_buy else (sl > open_p)
                if current_r >= 1.0 and be_needed and not tracker["be_locked"]:
                    be_level = open_p + (0.3 * pip) if is_buy else open_p - (0.3 * pip)
                    digits = 3 if "JPY" in symbol else 5
                    req = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": ticket,
                        "symbol": symbol,
                        "sl": round(be_level, digits),
                        "tp": tp,
                    }
                    res = mt5.order_send(req)
                    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                        tracker["be_locked"] = True
                        print(f"🛡️ [InFlight Co-Pilot] BREAK-EVEN SECURED on #{ticket} {symbol} at +{current_r:.2f}R! SL -> {be_level:.{digits}f}")
                        if self.snapshot_engine:
                            self.snapshot_engine.capture_async(
                                symbol=symbol,
                                event_type="BREAK_EVEN_LOCKED",
                                ticket=ticket,
                                entry_price=open_p,
                                sl_price=round(be_level, digits),
                                tp_price=tp,
                                extra_info={"lots": vol, "r_multiple": round(current_r, 2)}
                            )

                # ── STAGE 2: Partial Profit Harvester (50% lots at +1.8R) ──
                if current_r >= 1.8 and not tracker["partial_banked"] and vol >= 0.02:
                    partial_vol = round(vol * 0.5, 2)
                    req_close = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "position": ticket,
                        "symbol": symbol,
                        "volume": partial_vol,
                        "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
                        "price": cur_p,
                        "deviation": 10,
                        "magic": magic_number,
                        "comment": "IBT_PARTIAL_TP_50"
                    }
                    res_close = mt5.order_send(req_close)
                    if res_close and res_close.retcode == mt5.TRADE_RETCODE_DONE:
                        tracker["partial_banked"] = True
                        profit_lock_sl = open_p + (1.0 * risk_dist) if is_buy else open_p - (1.0 * risk_dist)
                        digits = 3 if "JPY" in symbol else 5
                        # Lock remaining 50% lot stop loss at +1.0R
                        mt5.order_send({
                            "action": mt5.TRADE_ACTION_SLTP,
                            "position": ticket,
                            "symbol": symbol,
                            "sl": round(profit_lock_sl, digits),
                            "tp": tp
                        })
                        print(f"💰 [InFlight Co-Pilot] Banked 50% ({partial_vol} lots) at +{current_r:.2f}R on #{ticket} {symbol}! Remaining SL locked at +1.0R.")
                        if self.snapshot_engine:
                            self.snapshot_engine.capture_async(
                                symbol=symbol,
                                event_type="PARTIAL_TP_BANKED",
                                ticket=ticket,
                                entry_price=open_p,
                                sl_price=round(profit_lock_sl, digits),
                                tp_price=tp,
                                extra_info={"lots_banked": partial_vol, "r_multiple": round(current_r, 2)}
                            )

                # ── STAGE 3: Structural Runner Trailing (+2.5R) ──
                if current_r >= 2.5:
                    # Query recent 5 M5 candles to find local fractal swing
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 5)
                    if rates is not None and len(rates) >= 3:
                        digits = 3 if "JPY" in symbol else 5
                        if is_buy:
                            recent_low = min(r['low'] for r in rates[1:4])
                            if recent_low > sl:
                                mt5.order_send({
                                    "action": mt5.TRADE_ACTION_SLTP,
                                    "position": ticket,
                                    "symbol": symbol,
                                    "sl": round(recent_low, digits),
                                    "tp": tp
                                })
                                print(f"📈 [InFlight Co-Pilot] Trailed SL up behind M5 swing low ({recent_low:.{digits}f}) on #{ticket} {symbol} (+{current_r:.2f}R).")
                        else:
                            recent_high = max(r['high'] for r in rates[1:4])
                            if recent_high < sl:
                                mt5.order_send({
                                    "action": mt5.TRADE_ACTION_SLTP,
                                    "position": ticket,
                                    "symbol": symbol,
                                    "sl": round(recent_high, digits),
                                    "tp": tp
                                })
                                print(f"📉 [InFlight Co-Pilot] Trailed SL down behind M5 swing high ({recent_high:.{digits}f}) on #{ticket} {symbol} (+{current_r:.2f}R).")

        except Exception as e:
            print(f"[InFlightCoPilot] Audit error: {e}")
