"""
tests/test_laya_guardian.py — Comprehensive Unit Test Suite for LayaGuardian.
Verifies that Laya System 1 Decision Engine produces calibrated decisions
across news triage, tape confluence gating, and forensic incident triage.
"""

import os
import sys
import unittest
import time

ROOT_DIR = r"c:\Projects\Other\ibt-engine"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from exness.laya_guardian import LayaGuardian

class TestLayaGuardian(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.guardian = LayaGuardian(lazy_load=False)

    def test_1_device_and_readiness(self):
        """Test 1: Verify model is loaded and running on available device."""
        self.assertTrue(self.guardian.is_loaded)
        self.assertIsNotNone(self.guardian.agent)
        print(f"\n[PASS] Test 1: Laya Guardian online on device '{self.guardian.device.upper()}'")

    def test_2_emergency_news_headline_halts_trading(self):
        """Test 2: Emergency breaking news headline MUST trigger halt_trading=True."""
        headline = "EMERGENCY BREAKING: Federal Reserve calls unscheduled press conference; interbank overnight lending frozen amid liquidity crisis."
        t0 = time.perf_counter()
        res = self.guardian.evaluate_news_headline(headline)
        dt = (time.perf_counter() - t0) * 1000

        self.assertFalse(res["fallback"])
        self.assertTrue(res["halt_trading"])
        self.assertEqual(res["impact"], "VOLATILITY_SPIKE")
        print(f"[PASS] Test 2: Emergency headline triggered HALT ({res['impact']}, conf={res['confidence']:.2f}) in {dt:.1f}ms")

    def test_3_routine_news_does_not_halt(self):
        """Test 3: Routine benign news MUST NOT halt trading."""
        headline = "Retail footwear company reports quarterly in-store sales increased by 2.1 percent year over year."
        t0 = time.perf_counter()
        res = self.guardian.evaluate_news_headline(headline)
        dt = (time.perf_counter() - t0) * 1000

        self.assertFalse(res["fallback"])
        self.assertFalse(res["halt_trading"])
        self.assertIn(res["impact"], ["NO_IMPACT", "ROUTINE_COMMENTARY"])
        print(f"[PASS] Test 3: Routine news allowed normal trading ({res['impact']}, conf={res['confidence']:.2f}) in {dt:.1f}ms")

    def test_4_tape_confluence_clean_setup(self):
        """Test 4: Clean London Open SMC trend setup evaluates with high conviction."""
        setup = {
            "pair": "EURUSD",
            "order_type": "BUY_LIMIT",
            "archetype": "TREND_FVG_PULLBACK",
            "risk_pips": 8.0,
            "rr_ratio": 0.6
        }
        macro = {
            "spread_pips": 0.8,
            "session": "London_Open (08:30 UTC)",
            "liquidity_state": "EXPANDING_TREND"
        }
        t0 = time.perf_counter()
        res = self.guardian.evaluate_tape_confluence(setup, macro)
        dt = (time.perf_counter() - t0) * 1000

        self.assertFalse(res["fallback"])
        self.assertTrue(res["approved"])
        print(f"[PASS] Test 4: Clean setup approved ({res['conviction']}, conf={res['confidence']:.2f}) in {dt:.1f}ms")

    def test_5_forensic_incident_triage(self):
        """Test 5: Flash stop-out telemetry receives intelligent forensic quarantine rating."""
        telemetry = {
            "symbol": "XAUUSDm",
            "duration_seconds": 26,
            "profit_usd": -1.33,
            "planned_risk_usd": 5.0,
            "entry_price": 4387.738,
            "exit_price": 4386.412
        }
        t0 = time.perf_counter()
        res = self.guardian.triage_execution_incident(telemetry)
        dt = (time.perf_counter() - t0) * 1000

        self.assertFalse(res["fallback"])
        self.assertIn("quarantine_minutes", res)
        self.assertGreaterEqual(res["quarantine_minutes"], 15)
        print(f"[PASS] Test 5: Incident triaged (cause={res['root_cause']}, quar={res['quarantine_minutes']}m, conf={res['confidence']:.2f}) in {dt:.1f}ms")

    def test_6_failsafe_fallback_on_disabled(self):
        """Test 6: Disabled or unavailable guardian returns safe fallback defaults without error."""
        fallback_guardian = LayaGuardian(enabled=False)
        res = fallback_guardian.evaluate_news_headline("Any headline")
        self.assertTrue(res["fallback"])
        self.assertFalse(res["halt_trading"])
        print("[PASS] Test 6: Disabled guardian fails open safely to deterministic fallback.")

    def test_7_hot_reload_weights(self):
        """Test 7: Verify reload_lora_weights hot-swaps active model in RAM."""
        res = self.guardian.reload_lora_weights()
        self.assertTrue(res)
        self.assertTrue(self.guardian.is_distilled)
        print("[PASS] Test 7: LoRA weights hot-reloaded successfully into memory.")

if __name__ == "__main__":
    unittest.main()
