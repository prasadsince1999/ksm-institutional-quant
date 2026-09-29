"""
exness/execution_recorder.py — High-Fidelity Microstructure Telemetry Recorder.
Institutional ledger capturing complete market state physics, hybrid AI verdicts,
and closed deal physics for continuous experience replay and neural distillation.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TELEMETRY_LOG_FILE = os.path.join(ROOT_DIR, "data", "live_execution_telemetry.jsonl")

class ExecutionRecorder:
    """
    High-Fidelity Telemetry Recorder.
    Captures pre-trade physical invariants, model triage probabilities,
    and post-trade terminal states in an append-only JSONL format.
    """
    def __init__(self, log_path: str = TELEMETRY_LOG_FILE):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_proposal(
        self,
        symbol: str,
        timeframe: str,
        order_type: str,
        archetype: str,
        session: str,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        risk_pips: float,
        rr_ratio: float,
        current_spread_pips: float,
        atr_pips: float,
        lot_size: float,
        preceding_candles: Optional[list] = None,
        news_proximity_minutes: Optional[float] = None,
        sentinel_passed: bool = True,
        sentinel_rule: str = "ALL_INVARIANTS_PASSED",
        hybrid_verdict: Optional[Dict[str, Any]] = None,
        order_ticket: Optional[int] = None
    ) -> str:
        """
        Logs a candidate trade setup evaluated by the engine.
        Returns the unique record ID.
        """
        now_utc = datetime.now(timezone.utc)
        record_id = f"{symbol}_{int(now_utc.timestamp())}_{order_ticket or 'PENDING'}"

        # Calculate institutional physics
        spread_to_stop_ratio = round((current_spread_pips / risk_pips), 4) if risk_pips > 0 else 1.0
        stop_to_atr_ratio = round((risk_pips / atr_pips), 4) if atr_pips > 0 else 1.0

        record = {
            "record_id": record_id,
            "timestamp_utc": now_utc.isoformat(),
            "timestamp_epoch": now_utc.timestamp(),
            "symbol": symbol,
            "timeframe": timeframe,
            "order_type": order_type,
            "archetype": archetype,
            "session": session,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "risk_pips": risk_pips,
            "rr_ratio": rr_ratio,
            "lot_size": lot_size,
            "current_spread_pips": current_spread_pips,
            "atr_pips": atr_pips,
            "spread_to_stop_ratio": spread_to_stop_ratio,
            "stop_to_atr_ratio": stop_to_atr_ratio,
            "preceding_candles": preceding_candles or [],
            "news_proximity_minutes": news_proximity_minutes,
            "sentinel": {
                "passed": sentinel_passed,
                "rule": sentinel_rule
            },
            "hybrid_guardian": hybrid_verdict or {},
            "order_ticket": order_ticket,
            "terminal_state": "PLACED" if order_ticket else ("VETOED_SENTINEL" if not sentinel_passed else "VETOED_AI"),
            "closed_deal": None
        }

        self._append_record(record)
        return record_id

    def record_closed_deal(
        self,
        order_ticket: int,
        deal_ticket: int,
        symbol: str,
        entry_time_ts: float,
        exit_time_ts: float,
        entry_price: float,
        exit_price: float,
        profit_usd: float,
        planned_risk_usd: float,
        max_favorable_r: float = 0.0,
        max_adverse_r: float = 0.0
    ):
        """
        Updates an existing record or appends a post-trade closed deal record.
        Identifies execution anomalies (micro-stop flash < 180s, zombie decay > 4h).
        """
        duration_seconds = max(0.0, exit_time_ts - entry_time_ts)
        won = profit_usd > 0
        realized_r = round((profit_usd / planned_risk_usd), 2) if planned_risk_usd > 0 else (1.0 if won else -1.0)

        # Classify terminal state
        if duration_seconds < 180 and not won:
            terminal_state = "FLASH_STOP_OUT"
        elif duration_seconds > 14400 and not won: # > 4 hours
            terminal_state = "ZOMBIE_DRIFT_LOSS"
        elif won:
            terminal_state = "WIN_TAKE_PROFIT"
        else:
            terminal_state = "NORMAL_LOSS"

        closed_deal_data = {
            "order_ticket": order_ticket,
            "deal_ticket": deal_ticket,
            "symbol": symbol,
            "entry_time_iso": datetime.fromtimestamp(entry_time_ts, tz=timezone.utc).isoformat(),
            "exit_time_iso": datetime.fromtimestamp(exit_time_ts, tz=timezone.utc).isoformat(),
            "duration_seconds": round(duration_seconds, 1),
            "entry_price": entry_price,
            "exit_price": exit_price,
            "profit_usd": round(profit_usd, 2),
            "planned_risk_usd": round(planned_risk_usd, 2),
            "realized_r": realized_r,
            "max_favorable_r": round(max_favorable_r, 2),
            "max_adverse_r": round(max_adverse_r, 2),
            "terminal_state": terminal_state
        }

        # Attempt in-place update if file is small, otherwise append a CLOSED_DEAL event
        updated = self._update_record_with_deal(order_ticket, closed_deal_data)
        if not updated:
            now_utc = datetime.now(timezone.utc)
            event = {
                "record_id": f"DEAL_{deal_ticket}_{int(now_utc.timestamp())}",
                "timestamp_utc": now_utc.isoformat(),
                "event_type": "CLOSED_DEAL_AUTONOMOUS",
                "symbol": symbol,
                "order_ticket": order_ticket,
                "terminal_state": terminal_state,
                "closed_deal": closed_deal_data
            }
            self._append_record(event)

    def _append_record(self, record: dict):
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[ExecutionRecorder Warning] Failed to write log: {e}")

    def _update_record_with_deal(self, order_ticket: int, closed_deal_data: dict) -> bool:
        """Finds matching order_ticket in JSONL and updates its closed_deal field."""
        if not os.path.exists(self.log_path):
            return False
        try:
            lines = []
            matched = False
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    try:
                        rec = json.loads(line_str)
                        if rec.get("order_ticket") == order_ticket and not matched:
                            rec["closed_deal"] = closed_deal_data
                            rec["terminal_state"] = closed_deal_data["terminal_state"]
                            matched = True
                        lines.append(rec)
                    except Exception:
                        pass
            if matched:
                with open(self.log_path, "w", encoding="utf-8") as f:
                    for rec in lines:
                        f.write(json.dumps(rec) + "\n")
                return True
        except Exception as e:
            print(f"[ExecutionRecorder Warning] Could not update in-place: {e}")
        return False
