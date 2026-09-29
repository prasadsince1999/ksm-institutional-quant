"""
tests/test_execution_recorder.py — Unit test suite for ExecutionRecorder.
"""

import os
import sys
import json
import unittest
import tempfile
import time

ROOT_DIR = r"c:\Projects\Other\ibt-engine"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from exness.execution_recorder import ExecutionRecorder

class TestExecutionRecorder(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.temp_file.close()
        self.recorder = ExecutionRecorder(log_path=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_log_proposal_and_physics(self):
        """Verify that pre-trade physics (R_ss, R_sa) are computed and logged correctly."""
        rec_id = self.recorder.log_proposal(
            symbol="EURUSD",
            timeframe="M5",
            order_type="BUY_LIMIT",
            archetype="TREND_FVG_PULLBACK",
            session="LONDON_OPEN",
            entry_price=1.08500,
            sl_price=1.08400,
            tp_price=1.08700,
            risk_pips=10.0,
            rr_ratio=2.0,
            current_spread_pips=1.0,
            atr_pips=12.5,
            lot_size=0.10,
            sentinel_passed=True,
            hybrid_verdict={"approved": True, "risk_rating": "PRIME_SETUP"},
            order_ticket=12345678
        )
        self.assertTrue(os.path.exists(self.temp_file.name))

        with open(self.temp_file.name, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        self.assertEqual(len(lines), 1)
        record = lines[0]
        self.assertEqual(record["symbol"], "EURUSD")
        self.assertEqual(record["spread_to_stop_ratio"], 0.10) # 1.0 / 10.0
        self.assertEqual(record["stop_to_atr_ratio"], 0.80)   # 10.0 / 12.5
        self.assertEqual(record["terminal_state"], "PLACED")
        self.assertEqual(record["order_ticket"], 12345678)

    def test_record_closed_deal_linking(self):
        """Verify that closed deal matches order ticket and classifies flash stop out."""
        # Step 1: Log proposal
        self.recorder.log_proposal(
            symbol="XAUUSD",
            timeframe="M5",
            order_type="BUY_LIMIT",
            archetype="LIQUIDITY_SWEEP",
            session="NY_OVERLAP",
            entry_price=2400.00,
            sl_price=2398.68,
            tp_price=2404.00,
            risk_pips=13.2,
            rr_ratio=3.0,
            current_spread_pips=3.5,
            atr_pips=65.0,
            lot_size=0.05,
            order_ticket=999888
        )

        now = time.time()
        # Step 2: Record flash stop-out (duration 26 seconds, loss)
        self.recorder.record_closed_deal(
            order_ticket=999888,
            deal_ticket=111222,
            symbol="XAUUSD",
            entry_time_ts=now,
            exit_time_ts=now + 26.0,
            entry_price=2400.00,
            exit_price=2398.68,
            profit_usd=-6.60,
            planned_risk_usd=6.60
        )

        with open(self.temp_file.name, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]

        self.assertEqual(len(lines), 1)
        record = lines[0]
        self.assertIsNotNone(record["closed_deal"])
        self.assertEqual(record["terminal_state"], "FLASH_STOP_OUT")
        self.assertEqual(record["closed_deal"]["duration_seconds"], 26.0)

if __name__ == "__main__":
    unittest.main()
