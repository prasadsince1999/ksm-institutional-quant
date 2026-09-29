"""
scripts/camber_26y_runner.py — Camber Cloud Autonomous 26-Year Simulation Harness.

Orchestrates distributed high-throughput simulation on Camber Cloud HPC:
  - Target Hardware : Camber Cloud (8 vCPU / 32GB RAM / 1x Cloud GPU)
  - Quota Accounting: Automatically updates C:\Projects\KSM x Tech - Projects\otto-lab\discovery\camber_budget.json
  - Execution Burst : Runs parallel 26-year live-mirror backtest across all pairs in ~6-8 minutes.
"""

import os
import sys
import time
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

OTTO_LAB_DIR = Path(r"C:\Projects\KSM x Tech - Projects\otto-lab")
if (OTTO_LAB_DIR / "brain").exists():
    sys.path.insert(0, str(OTTO_LAB_DIR / "brain"))
    try:
        from camber_bridge import CamberBridge
    except ImportError:
        CamberBridge = None
else:
    CamberBridge = None

from scripts.simulate_26y_live_mirror import run_all_26y

def run_camber_burst():
    print("=" * 80)
    print("⚡ CAMBER CLOUD 26-YEAR HIGH-FIDELITY SIMULATION DISPATCH")
    print("=" * 80)
    
    bridge = CamberBridge() if CamberBridge else None
    if bridge:
        print(bridge.get_budget_status())
    else:
        print("Running in Standalone Compute Mode (Local / Cloud Worker)")
        
    start_time = time.time()
    
    # Run the full 26-year live-mirror simulation
    results = run_all_26y()
    
    duration_sec = time.time() - start_time
    duration_min = duration_sec / 60.0
    
    print("\n" + "=" * 80)
    print(f"✅ CAMBER CLOUD EXECUTION BURST COMPLETE in {duration_sec:.1f}s ({duration_min:.2f} mins)")
    print("=" * 80)
    
    if bridge:
        run_id = f"camber_26y_{int(time.time())}"
        metrics = {
            "total_bars_audited": results.get("total_bars_audited", 0),
            "total_trades": results.get("portfolio_summary", {}).get("total_trades", 0),
            "win_rate_pct": results.get("portfolio_summary", {}).get("win_rate_pct", 0),
            "net_return_r": results.get("portfolio_summary", {}).get("net_return_r", 0),
            "max_drawdown_pct": results.get("portfolio_summary", {}).get("max_drawdown_pct", 0),
            "simulated_ending_balance": results.get("portfolio_summary", {}).get("simulated_ending_balance", 0)
        }
        bridge.log_run(
            run_id=run_id,
            duration_minutes=duration_min,
            task_name="26-Year High-Fidelity Live-Mirror Institutional Simulation",
            metrics=metrics
        )
        print("\nUpdated Camber Cloud Compute Budget:")
        print(bridge.get_budget_status())

if __name__ == "__main__":
    run_camber_burst()
