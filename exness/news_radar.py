"""
exness/news_radar.py — Sub-Second Breaking News & Geopolitical Shock Radar.
Powered by Local Laya (421M ModernBERT-large + RLCD) running 100% locally on device.

Monitors real-time financial headlines and macroeconomic events, triaging shock volatility
in <120ms to execute an automated Flash Kill-Switch before spread blowouts wipe out capital.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

class NewsRadar:
    """
    Sub-Second Macroeconomic & Geopolitical Shock Sentinel.
    Runs asynchronous headline ingestion and evaluates threat level via Local Laya.
    """
    def __init__(self, guardian=None, quarantine_minutes: int = 30):
        self.guardian = guardian
        self.quarantine_minutes = quarantine_minutes
        self.seen_headlines = set()
        self.is_quarantined = False
        self.quarantine_until = 0.0
        self.last_shock_event = None

        if self.guardian is None:
            try:
                from exness.laya_guardian import LayaGuardian
                self.guardian = LayaGuardian(lazy_load=True)
            except Exception as e:
                print(f"[NewsRadar] Failed to load LayaGuardian: {e}")
                self.guardian = None

    def _hash_headline(self, headline: str) -> str:
        return hashlib.sha256(headline.strip().lower().encode("utf-8")).hexdigest()

    def is_in_quarantine(self) -> bool:
        """Returns True if the trading engine is currently under shock quarantine."""
        if not self.is_quarantined:
            return False
        if time.time() > self.quarantine_until:
            print(f"🛡️ [NewsRadar] Shock quarantine expired. Resuming normal institutional scanning.")
            self.is_quarantined = False
            self.quarantine_until = 0.0
            return False
        return True

    def audit_market_safety(self) -> Dict[str, Any]:
        """
        Quick check on whether current market environment is under shock quarantine.
        Returns dict with 'kill_switch_active': bool, and 'reason': str.
        """
        if self.is_in_quarantine():
            return {
                "kill_switch_active": True,
                "reason": f"Shock quarantine active until {datetime.fromtimestamp(self.quarantine_until, tz=timezone.utc).strftime('%H:%M:%S UTC')} (Event: {self.last_shock_event.get('reason') if self.last_shock_event else 'Unknown'})"
            }
        return {
            "kill_switch_active": False,
            "reason": "Normal market conditions"
        }

    def trigger_quarantine(self, reason: str, duration_minutes: Optional[int] = None):
        """Enforces a trading freeze following a confirmed shock headline."""
        duration = duration_minutes or self.quarantine_minutes
        self.is_quarantined = True
        self.quarantine_until = time.time() + (duration * 60)
        self.last_shock_event = {
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "quarantine_until": datetime.fromtimestamp(self.quarantine_until, tz=timezone.utc).isoformat()
        }
        print(f"🚨 [NewsRadar FLASH KILL-SWITCH] Trading frozen for {duration} minutes! Reason: {reason}")

    def triage_headline(self, headline: str) -> Dict[str, Any]:
        """
        Classifies a single breaking headline using Local Laya in sub-second time.
        """
        h_hash = self._hash_headline(headline)
        is_new = h_hash not in self.seen_headlines
        self.seen_headlines.add(h_hash)

        if not self.guardian:
            return {
                "halt_trading": False,
                "impact": "ROUTINE_COMMENTARY",
                "confidence": 0.50,
                "latency_ms": 0.0,
                "is_new": is_new,
                "fallback": True
            }

        t0 = time.perf_counter()
        eval_res = self.guardian.evaluate_news_headline(headline)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        eval_res["is_new"] = is_new
        eval_res["latency_ms"] = round(latency_ms, 1)

        if eval_res.get("halt_trading") or eval_res.get("impact") == "VOLATILITY_SPIKE":
            self.trigger_quarantine(reason=headline)

        return eval_res

    def execute_kill_switch_protocol(self, mt5_client=None) -> Dict[str, Any]:
        """
        Emergency action: Purges all active pending limit orders on the broker
        to eliminate toxic slippage hazard during sudden market turbulence.
        """
        print("🚨 [NewsRadar] Executing Flash Kill-Switch Protocol across Exness MT5...")
        cancelled_tickets = []
        try:
            import MetaTrader5 as mt5
            orders = mt5.orders_get()
            if orders:
                for o in orders:
                    # Cancel pending limit orders
                    if o.type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_BUY_STOP, mt5.ORDER_TYPE_SELL_STOP]:
                        req = {
                            "action": mt5.TRADE_ACTION_REMOVE,
                            "order": o.ticket
                        }
                        res = mt5.order_send(req)
                        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                            cancelled_tickets.append(o.ticket)
                            print(f"  🛑 Purged pending order #{o.ticket} on {o.symbol} before volatility hit.")
            
            return {
                "success": True,
                "cancelled_orders_count": len(cancelled_tickets),
                "tickets": cancelled_tickets,
                "quarantine_active": True
            }
        except Exception as e:
            print(f"[NewsRadar] Kill-Switch broker error: {e}")
            return {
                "success": False,
                "error": str(e),
                "cancelled_orders_count": len(cancelled_tickets),
                "tickets": cancelled_tickets
            }

def run_test_suite():
    print("=" * 70)
    print("TESTING SUB-SECOND BREAKING NEWS RADAR (LOCAL LAYA)")
    print("=" * 70)

    radar = NewsRadar()
    test_headlines = [
        ("🚨 EMERGENCY: Federal Reserve announces unscheduled 75 bps emergency rate hike amid inflation spike", True),
        ("Middle East Conflict Escalates: Missile strikes hit key oil refineries; crude surges 9%", True),
        ("European Central Bank leaves benchmark rates unchanged at 3.75%, matching forecasts", False),
        ("Apple reports Q3 earnings per share of $1.40 vs $1.38 consensus, services revenue up 12%", False),
        ("🚨 FLASH CRASH WARNING: Major liquidity provider freezes interbank forex FX pricing", True)
    ]

    for h, expected_halt in test_headlines:
        print(f"\nEvaluating: \"{h}\"")
        res = radar.triage_headline(h)
        print(f"  • Impact: {res.get('impact')} | Halt Trading: {res.get('halt_trading')} | Conf: {res.get('confidence')} | Latency: {res.get('latency_ms')}ms")
        is_match = (res.get('halt_trading') == expected_halt) or (res.get('impact') == 'VOLATILITY_SPIKE' and expected_halt)
        print(f"  • Ground Truth Concordance: {'✅ PASS' if is_match else '⚠️ DEVIATION'}")

    print("\n" + "=" * 70)
    print("NEWS RADAR TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    run_test_suite()
