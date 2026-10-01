# Institutional Quant Rules of Engagement (AGENTS.md)

This document establishes the binding, non-negotiable rules for all AI agents (Gemini, Claude, Jev, Laya, Decider) and human developers working on this codebase.

---

## 1. Zero-Bullshit & Machine-Evidence Mandate
1. **No Simulated or Hallucinated Claims**:
   - You may **NEVER** state an expectancy ($R/\text{trade}$), win rate, profit factor, annual return, or drawdown unless that exact number appears verbatim in `reports/verification/latest.md` or is output by `python scripts/verify_system.py` in the current session.
   - Banned language without statistical proof: *"mathematically proven"*, *"guaranteed"*, *"unbreakable"*, *"zero look-ahead proven"*, *"pure alpha"*.
2. **Every Edge Claim Requires a Machine Gate Receipt**:
   - An edge is only considered supported if `python scripts/verify_system.py --full` outputs:
     - Verdict: `EDGE_SUPPORTED` or `EDGE_SUPPORTED_IN_SIMULATION_ONLY`.
     - $N \ge 1,000$ trades.
     - 95% Bootstrap Confidence Interval strictly above 0 ($CI_{\text{lo}} > 0$).
     - $t$-statistic exceeding the Bonferroni-corrected multiple testing threshold $z$.
     - Positive expectancy under **MILD_STRESS** friction ($\times 1.15$ spread, $0.45\text{p}$ slip, $0.3\text{p}$ penetration).
     - No single pair contributing $> 50\%$ of total net $R$.

---

## 2. The Holdout Lock Protocol
1. **Strict Temporal Partitioning**:
   - `config/frozen_config.json` sets `research_end` (e.g., `2023-12-31`).
   - All exploratory research, hyperparameter tuning, and model fitting must occur strictly on data $\le \text{research\_end}$.
2. **Single-Shot Final Exam**:
   - The holdout period ($> \text{research\_end}$) may be evaluated **exactly once** per configuration hash via:
     ```bash
     python scripts/verify_system.py --final-exam
     ```
   - The result is cryptographically hashed and locked in `reports/verification/holdout_lock.json`.
   - Modifying parameters and re-running on the holdout is treated as catastrophic data contamination.

---

## 3. Position Sizing Invariants
All live and simulation order sizing must execute via [`exness/position_sizing.py`](exness/position_sizing.py):
1. **JPY Cross Sizing**: JPY pairs (e.g., `EURJPY`, `GBPJPY`) must convert pip value to USD using `USDJPY`, not the cross's own price.
2. **USD-Base Pairs**: `USDCAD` and `USDCHF` must convert using their live quote rates (never a flat $10).
3. **Hard Budget Enforcement**: If the minimum lot ($0.01$) risks $> 1.25\times$ the calculated dollar risk budget, the trade **must be refused** (`lots = 0.0`). No silent clipping to $0.01$ is permitted.

---

## 4. Reality Calibration (Fill Audit)
1. **Simulation is Only a Hypothesis**:
   - A positive backtest is not proof of real-world profit.
   - Live demo execution must log all intended orders into `data/live_execution_telemetry.jsonl`.
2. **Continuous Friction Measurement**:
   - After $\ge 30$ closed demo trades, run:
     ```bash
     python scripts/fill_audit.py --days 30
     ```
   - This records real slippage and spread into `reports/verification/measured_friction.json`.
   - `verify_system.py` will automatically test the strategy against `MEASURED_LIVE` friction. If the edge turns negative under measured friction, live trading is halted immediately.

---

## 5. Standard Verification Commands
- **Quick self-test (15s)**:
  ```bash
  python scripts/verify_system.py --quick
  ```
- **Full real-data claim gate**:
  ```bash
  python scripts/verify_system.py --full
  ```
- **Fill audit from live MT5**:
  ```bash
  python scripts/fill_audit.py --days 30
  ```
