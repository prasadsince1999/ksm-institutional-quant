"""
tests/test_execution_sentinel.py — Comprehensive Invariant Test Suite.
Verifies that all institutional safety invariants and anomaly traps catch bugs
before real capital is ever risked.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import unittest
import time

ROOT_DIR = r"c:\Projects\Other\ibt-engine"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from exness.execution_sentinel import ExecutionSentinel

class TestExecutionSentinel(unittest.TestCase):
    def setUp(self):
        self.test_incidents_file = os.path.join(ROOT_DIR, "data", "test_incidents.json")
        if os.path.exists(self.test_incidents_file):
            try:
                os.remove(self.test_incidents_file)
            except Exception:
                pass
        self.sentinel = ExecutionSentinel(incidents_file=self.test_incidents_file)

    def tearDown(self):
        if os.path.exists(self.test_incidents_file):
            try:
                os.remove(self.test_incidents_file)
            except Exception:
                pass

    def test_1_gold_volatility_floor_rejection(self):
        """Test 1: Gold Stop Loss tighter than $5.00 / 1.0x ATR MUST be rejected."""
        res = self.sentinel.validate_pre_trade_invariants(
            symbol="XAUUSDm",
            order_type="BUY_LIMIT",
            entry_price=4388.948,
            sl_price=4386.412, # Only $2.53 SL! (The exact bug from earlier)
            tp_price=4390.470,
            risk_pips=25.3,
            rr_ratio=0.6,
            current_bid=4391.0,
            current_ask=4391.3,
            current_spread_pips=3.0,
            atr=4.50,
            pip=0.10
        )
        self.assertFalse(res["passed"])
        self.assertEqual(res["rule"], "INVARIANT_VOLATILITY_FLOOR")
        print("[PASS] Test 1: Gold micro-stop ($2.53) correctly rejected by Sentinel!")

    def test_2_spread_safety_ratio_rejection(self):
        """Test 2: Stop loss smaller than 4x spread MUST be rejected."""
        res = self.sentinel.validate_pre_trade_invariants(
            symbol="EURUSDm",
            order_type="BUY_LIMIT",
            entry_price=1.1500,
            sl_price=1.1494, # 6.0 pips SL (passes 5.0p vol floor)
            tp_price=1.1504,
            risk_pips=6.0,
            rr_ratio=0.6,
            current_bid=1.1510,
            current_ask=1.1512,
            current_spread_pips=2.0, # 2.0p spread -> 4x is 8.0p -> 6.0p is rejected!
            atr=0.0004, # 4.0 pips ATR
            pip=0.0001
        )
        self.assertFalse(res["passed"])
        self.assertEqual(res["rule"], "INVARIANT_SPREAD_SAFETY")
        print("[PASS] Test 2: High spread ratio trade correctly rejected by Sentinel!")

    def test_3_price_geometry_rejection(self):
        """Test 3: Buy Limit entry above market Ask MUST be rejected."""
        res = self.sentinel.validate_pre_trade_invariants(
            symbol="EURUSDm",
            order_type="BUY_LIMIT",
            entry_price=1.1520, # Entry above ask!
            sl_price=1.1510,
            tp_price=1.1526,
            risk_pips=10.0,
            rr_ratio=0.6,
            current_bid=1.1510,
            current_ask=1.1511,
            current_spread_pips=0.8,
            atr=0.0010,
            pip=0.0001
        )
        self.assertFalse(res["passed"])
        self.assertEqual(res["rule"], "INVARIANT_PRICE_GEOMETRY")
        print("[PASS] Test 3: Inverted price geometry correctly rejected by Sentinel!")

    def test_4_target_preemption_cancels_pending_order(self):
        """Test 4: Pending limit order whose TP has been reached MUST be cancelled."""
        should_cancel, reason = self.sentinel.audit_in_flight_pending_order(
            ticket=5123414404,
            symbol="XAUUSDm",
            order_type=2, # Buy Limit
            price_open=4388.948,
            sl=4386.412,
            tp=4390.470,
            time_setup=time.time() - 300, # 5m ago
            current_bid=4395.0, # Price reached 4395 (well past TP 4390.47)!
            current_ask=4395.3,
            timeframe_m=5,
            max_bars=8
        )
        self.assertTrue(should_cancel)
        self.assertTrue("TARGET_PREEMPTED" in reason)
        print("[PASS] Test 4: Target Pre-Emption watchdog correctly triggered cancellation!")

    def test_5_adverse_drop_cancels_order(self):
        """Test 5: Price gapping through SL while pending triggers instant cancel."""
        should_cancel, reason = self.sentinel.audit_in_flight_pending_order(
            ticket=77777,
            symbol="EURUSDm",
            order_type=2, # Buy Limit
            price_open=1.1500,
            sl=1.1490, # 10 pips risk
            tp=1.1506,
            time_setup=time.time() - 300,
            current_bid=1.1488, # Price gapped below SL (1.1490)!
            current_ask=1.1489,
            timeframe_m=5,
            max_bars=8
        )
        self.assertTrue(should_cancel)
        self.assertTrue("ADVERSE_DROP" in reason)
        print("[PASS] Test 5: Adverse drop below SL correctly cancelled before bad fill!")

    def test_6_time_decay_cancels_order(self):
        """Test 6: Order older than 8 bars (40 min) MUST be cancelled."""
        should_cancel, reason = self.sentinel.audit_in_flight_pending_order(
            ticket=88888,
            symbol="USDJPYm",
            order_type=2,
            price_open=155.00,
            sl=154.90,
            tp=155.06,
            time_setup=time.time() - 2500, # 41.6 minutes ago (> 40 min)
            current_bid=155.02,
            current_ask=155.03,
            timeframe_m=5,
            max_bars=8
        )
        self.assertTrue(should_cancel)
        self.assertTrue("TIME_DECAY" in reason)
        print("[PASS] Test 6: 8-bar time decay correctly purged stale order!")

    def test_7_flash_stop_out_quarantines_symbol(self):
        """Test 7: Trade closing in 26 seconds triggers FLASH_STOP_OUT and auto-quarantines asset."""
        now = time.time()
        audit = self.sentinel.audit_closed_deal(
            ticket=4420052491,
            symbol="XAUUSDm",
            order_ticket=5123414404,
            entry_time=now - 26, # 26 seconds ago!
            exit_time=now,
            entry_price=4387.738,
            exit_price=4386.412,
            profit_usd=-1.33,
            planned_risk_usd=1.33
        )
        self.assertTrue(audit["anomaly_detected"])
        self.assertEqual(audit["anomaly_type"], "FLASH_STOP_OUT")

        # Verify that subsequent trade attempts on XAUUSD are blocked by quarantine!
        is_quar, q_reason = self.sentinel.is_symbol_quarantined("XAUUSDm")
        self.assertTrue(is_quar)
        print("[PASS] Test 7: Flash stop-out instantly detected and asset quarantined for 60m!")

if __name__ == "__main__":
    unittest.main()
