# MetaTrader 5 Real-Time Infrastructure & Operational Runbook
## Volume IV: Autonomous Execution Daemon, News Protection, and Recursive Self-Improvement

**Author:** PrasaD (Chief Architect, KSM X Tech)  
**Quantitative Verification:** Antigravity AI  
**Series:** Institutional SMC Quantitative Engine Whitepaper Series (Volume IV)  
**Parent Paper:** Autonomous Institutional SMC Quantitative Engine (26-Year Empirical Study)  
**Date:** September 18, 2026  

---

## 1. System Architecture Overview

The **KSM X Tech Engine** is engineered for zero-latency, local execution. Unlike cloud-dependent trading bots that introduce API rate-limits, monthly subscription overhead, and webhook disconnect risks, our architecture runs natively on the operator's Windows machine, interfacing directly with MetaTrader 5 via high-speed Inter-Process Communication (IPC).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        REAL-TIME SYSTEM EXECUTION TOPOLOGY                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ Forex Factory Economic Feed ]                                                      │
│                 │                                                                      │
│                 ▼ (Scraped JSON every 4 hours)                                         │
│   [ exness/economic_calendar.json ] ──> NEWS EMBARGO FILTER (Blocks High Impact +-30m) │
│                                                   │                                    │
│                                                   ▼                                    │
│   [ MetaTrader 5 Terminal ] <── IPC ──> [ exness/trader.py (Live Daemon Task-4152) ]   │
│         ▲                                         │                                    │
│         │ (Pending Limits / Stops / TPs)          ▼ (M5 Bar Analysis Every 60s)        │
│         │                               [ exness/strategy_smc_m15.py ]                 │
│         │                                         │                                    │
│   [ Exness Broker Bridge ]                        ▼ (Dynamic Per-Asset Rules)          │
│   Account: 414328XXX ($500.00)          [ exness/asset_profiles.json ]                 │
│                                                   ▲                                    │
│                                                   │ (Nightly Roll Optimization)        │
│                                         [ exness/overnight_learner.py ]                │
│                                                   ▲                                    │
│                                                   │ (Decadal Calibration)              │
│                                         [ data/*_max_m5.parquet (26.3 Yrs) ]           │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Order Lifecycle State Machine

To prevent slippage and market chasing, orders move through a strict deterministic state machine:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                          ORDER LIFECYCLE STATE MACHINE                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ 1. SCANNING ]        ──> M5 bar closes. Confluence check (Strategy 1, 2, 3, or 4). │
│          │                                                                             │
│          ▼                                                                             │
│   [ 2. PENDING LIMIT ]   ──> Order submitted at exact FVG boundary.                    │
│          │                   Active mitigation timer = 8 bars (40 minutes).            │
│          ├──────────────────────────────┬──────────────────────────────┐               │
│          ▼                              ▼                              ▼               │
│   [ 3A. FILLED ]               [ 3B. TIMEOUT ]                [ 3C. EMBARGO ]          │
│   Price mitigates limit price. Price leaves zone without fill. High-impact news event. │
│   Position active on broker.   ORDER CANCELLED. Zero risk.    ORDER CANCELLED.         │
│          │                                                                             │
│          ├──────────────────────────────┐                                              │
│          ▼                              ▼                                              │
│   [ 4A. TAKE PROFIT (0.6R) ]    [ 4B. STOP LOSS ]                                      │
│   Target reached (+0.6R).       Structural stop hit (-1.0R).                           │
│   Trade logged to ledger.       Daily drawdown counter incremented.                    │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. High-Impact News Embargo Architecture

High-impact macroeconomic announcements (Non-Farm Payrolls [NFP], Consumer Price Index [CPI], Federal Reserve FOMC, Interest Rate Decisions) cause severe retail spread widening up to 10–20 pips and unpredictable slippage.

### 3.1 News Protection Parameters
* **Embargo Window:** $\pm 30\text{ minutes}$ around any "Red Folder" high-impact event.
* **Pre-News Action:** 15 minutes before the release, all resting pending limit orders are automatically purged.
* **Open Position Rule:** Open trades have their stop losses maintained at breakeven if in profit $\ge 0.3\text{ R}$.
* **Post-News Cooldown:** The engine resumes scanning only 30 minutes after the release once spreads normalize.

---

## 4. The 21:00 UTC Overnight Recursive Learner

Every trading day at **21:00 UTC (New York Close / Asian Rollover)**, the engine initiates an autonomous self-improvement routine (`exness/overnight_learner.py`):
1. **Trade Reconciliation:** Pulls closed trades from MetaTrader 5 and reconciles executed fills against predicted setups.
2. **Spread Calibration:** Samples current live broker spreads during the rollover window to update spread friction models.
3. **Parameter Ratchet:** Backtests recent market structures against the 26.3-year master Parquet store (`data/*_max_m5.parquet`). If subtle shifts in volatility are detected, it updates rejection wick thresholds ($\pm 0.05$) and ATR filters in `exness/asset_profiles.json`.
4. **Hot-Reload:** Changes take effect immediately on the running live daemon without restarting the process.

---

## 5. Operational Maintenance & Failure Recovery Runbook

| Incident | Root Cause | Automated Daemon Defense | Manual Operator Recovery Action |
|---|---|---|---|
| **Terminal Crash** | Windows OS update or memory leak | Daemon retries connection every 15s | Restart MT5 terminal; daemon reconnects automatically |
| **Network Outage** | ISP disconnection | Hard broker SL/TP protect open positions | Verify router connection; daemon resumes upon link restore |
| **High Spread Surge** | Rollover / Illiquid bank holiday | Institutional breathing room floor (5–15p) | Daemon logs warning and skips new limit entries |
| **Max Loss Trigger** | 3 consecutive losses (-4.5% equity) | **HARD LOCKDOWN** circuit breaker engages | Review trade logs; daemon resumes at 07:00 UTC next day |

---
*Volume IV Certified by Antigravity Quantitative Verification Engine for PrasaD (KSM X Tech).*
