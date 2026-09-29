# 🏛️ KSM-Institutional-Quant: Autonomous Smart Money Concepts (SMC) Quantitative Trading System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![MetaTrader 5](https://img.shields.io/badge/Broker-MetaTrader%205%20(Exness)-green.svg)](https://www.metatrader5.com/)
[![CUDA Accelerated](https://img.shields.io/badge/Hardware-PyTorch%20CUDA-orange.svg)](https://pytorch.org/)
[![Execution Timeframe](https://img.shields.io/badge/Timeframe-M5%20Intraday-purple.svg)]()
[![License](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

An institutional-grade, multi-asset quantitative algorithmic trading engine built for automated execution on **MetaTrader 5** via **Exness**. 

The system programmatically deconstructs discretionary **Smart Money Concepts (SMC)** and **Inner Circle Trader (ICT)** price delivery algorithms into deterministic mathematical invariants, vetted by a **Triple-Tier Hybrid AI Decision Committee** (TypeSafe Jev + Decider 2B + Laya 421M) and safeguarded by an in-flight **Execution Sentinel**.

---

## 📑 Table of Contents

1. [Executive Summary & Core Principles](#-executive-summary--core-principles)
2. [Multi-Decade Microstructure Foundation (26 Years, 17.2M Bars)](#-multi-decade-microstructure-foundation)
3. [The Three Pillars of the Execution Architecture](#-the-three-pillars-of-the-execution-architecture)
   - [Pillar I: Institutional Liquidity Engine](#pillar-i-institutional-liquidity-engine)
   - [Pillar II: Multi-Tier System 1 Decision Committee](#pillar-ii-multi-tier-system-1-decision-committee)
   - [Pillar III: Pre-Flight Execution Sentinel](#pillar-iii-pre-flight-execution-sentinel)
4. [Quantitative Risk Geometry & Money Management](#-quantitative-risk-geometry--money-management)
5. [Real-Time Telemetry & Dark-Mode Chart Dispatcher](#-real-time-telemetry--dark-mode-chart-dispatcher)
6. [Repository Structure & File Catalog](#-repository-structure--file-catalog)
7. [Research Papers & Formal Documentation](#-research-papers--formal-documentation)
8. [Installation & Deployment Guide](#-installation--deployment-guide)
9. [CLI Usage & Operating Modes](#-cli-usage--operating-modes)
10. [Institutional Standards & Risk Disclaimer](#-institutional-standards--risk-disclaimer)

---

## 🏛️ Executive Summary & Core Principles

Most retail trading bots fail because they optimize over-fitted indicators on tiny sample sizes, run toxic martingale grids, or chase sub-1:1 risk-to-reward ratios where broker spread friction guarantees long-term ruin.

**KSM-Institutional-Quant** enforces four non-negotiable institutional invariants:
1. **Mathematical Expectancy First**: Strictly targets **1:1.5 to 1:2.0 Risk-to-Reward**, ensuring that a 45% win rate generates substantial positive mathematical expectancy ($E > +0.09R$ per trade).
2. **Symmetrical Fixed Fractional Risk**: Flat 1.0% equity allocation per trade. Winning trades never escalate risk, protecting capital against negative asymmetry.
3. **Session Liquidity Alignment**: Entries occur exclusively following sweeps of Asian Session Highs/Lows (ASH/ASL) or Previous Day Highs/Lows (PDH/PDL) during London Open (07:00–11:30 UTC) and New York Open (12:00–16:30 UTC) killzones.
4. **Deterministic Invariant Gatekeeping**: Every order is checked against hard microstructure invariants (spread safety, volatility floor, price geometry) in 3ms before broker submission.

---

## 📊 Multi-Decade Microstructure Foundation

The core algorithmic models were backtested and calibrated across **10 institutional assets** utilizing over **17.2 Million 5-minute bars (2000–2026)**:

| Asset Class | Symbols | Primary Liquidity Killzone | Base Spread Floor |
| :--- | :--- | :--- | :--- |
| **Commodities** | `XAUUSD` (Spot Gold) | London Open / NY AM Reversal | 2.0 pips ($0.20) |
| **Forex Majors** | `EURUSD`, `GBPUSD`, `USDJPY`, `AUDUSD`, `NZDUSD`, `USDCAD`, `USDCHF` | London Open / NY Overlap | 0.7 – 1.0 pips |
| **Forex Crosses** | `EURJPY`, `GBPJPY` | London Open (High Beta Momentum) | 1.4 – 2.0 pips |

### 50,000-Path Monte Carlo Simulation & R:R Stress Test

Simulating 10,353,840 real M5 bars on PyTorch CUDA with dynamic Exness spreads and limit-order queue penetration physics:

| Target R:R | Historical Trades | Realized Win Rate | Required Break-Even Win Rate | Net Return | Profit Factor | Expected Value (EV) per Trade |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1 : 0.6** | 5,767 | **78.13%** | 62.50% | +925.1 R | 1.73 | +0.160 R |
| **1 : 1.0** | 5,525 | **61.38%** | 50.00% | +865.3 R | 1.41 | +0.157 R |
| **1 : 1.5** *(Active Baseline)* | 5,225 | **45.84%** | **40.00%** | **+485.6 R** | **1.17** | **+0.093 R** |
| **1 : 2.0** | 4,921 | **36.46%** | 33.33% | +253.4 R | 1.08 | +0.052 R |

*Under the 1:1.5 baseline with flat 1.0% Fixed Fractional risk, starting capital of $500.00 compounded to $44,387.79 with a peak drawdown of 27.7%.*

---

## ⚡ The Three Pillars of the Execution Architecture

```
                                  [ M5 Live Tick Stream ]
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    PILLAR I: INSTITUTIONAL LIQUIDITY ENGINE  │
                      │  • Session Accumulation Gate (00-06 UTC)     │
                      │  • Judas Liquidity Sweeps (ASH/ASL/PDH/PDL)  │
                      │  • Displacement Candle & FVG Detection       │
                      └──────────────────────┬───────────────────────┘
                                             │ Qualified Candidate Setup
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    PILLAR II: HYBRID DECISION COMMITTEE      │
                      │  • Tier 1: TypeSafe Jev (Cloud API, ~350ms)  │
                      │  • Tier 2: Decider 2B (Local GPU, ~1.7s)     │
                      │  • Tier 3: Laya 421M (ModernBERT, ~12ms)     │
                      └──────────────────────┬───────────────────────┘
                                             │ Consensus Approval
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    PILLAR III: EXECUTION SENTINEL            │
                      │  • Spread Safety Ratio (SL >= 4x Spread)     │
                      │  • Volatility Floor (SL >= 5p / 0.8x ATR)    │
                      │  • Price Geometry (Discount/Premium Limit)   │
                      │  • Dynamic Quarantine Gate                   │
                      └──────────────────────┬───────────────────────┘
                                             │ Passed All Invariants
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │    BROKER EXECUTION & TELEMETRY              │
                      │  • MetaTrader 5 Limit Order Dispatch         │
                      │  • Telegram Dark-Mode Chart Snapshot Bot     │
                      │  • In-Flight Co-Pilot (BE Lock & Trail)      │
                      └──────────────────────────────────────────────┘
```

### Pillar I: Institutional Liquidity Engine
Located in [`exness/strategy_smc_m15.py`](exness/strategy_smc_m15.py), the setup detection engine tracks four archetypes:
1. **Session Judas Sweep Reversal**: Price sweeps Asian High/Low during London Open (07:00–09:00 UTC) by 3–15 pips, followed by Market Structure Shift (MSS) displacement creating a Fair Value Gap (FVG).
2. **New York PM Institutional Reversal**: Sweeps morning London highs/lows during the NY PM window (14:00–16:30 UTC).
3. **Trend Continuation FVG Pullback**: Pullbacks to high-displacement order blocks aligned with the 1-hour macro trend.
4. **Session Breakout Extension**: Sustained expansion moves out of multi-hour compressions.

### Pillar II: Multi-Tier System 1 Decision Committee
Located in [`exness/hybrid_decision_guardian.py`](exness/hybrid_decision_guardian.py), incoming candidate setups are evaluated by three independent models:
* **Primary (Cloud)**: **TypeSafe Jev System One** (Decision Index Score: **59.5**, ~350ms latency). Evaluates order flow context and rejects structural traps (`TOXIC_TRAP`).
* **Secondary (Local GPU)**: **Decider 2B** (Decision Index Score: **44.0**, Qwen3.5-2B backbone, ~1.7s latency on CUDA). Operates fully offline with zero internet dependency.
* **Tertiary (Local CPU)**: **Laya 421M** (Decision Index Score: **16.4**, ModernBERT-RLCD architecture, ~12ms latency).

### Pillar III: Pre-Flight Execution Sentinel
Located in [`exness/execution_sentinel.py`](exness/execution_sentinel.py), this deterministic mathematics layer acts as a fail-safe firewall before any order is transmitted to MetaTrader 5:
* **`INVARIANT_SPREAD_SAFETY`**: Stop-loss distance must be at least $4.0\times$ current broker spread.
* **`INVARIANT_VOLATILITY_FLOOR`**: Prevents micro-stops that get swept by normal candle noise (minimum 5 pips on FX, $5.00 on Gold, or $0.8\times$ 20-period ATR).
* **`INVARIANT_PRICE_GEOMETRY`**: Enforces strict limit pricing (Buy Limit must be below current Ask; Sell Limit must be above current Bid).
* **`INVARIANT_RR_SANITY`**: Rejects any trade with an effective reward-to-risk ratio below 1:1.5.

---

## 📈 Quantitative Risk Geometry & Money Management

A common retail misconception is that a 70%+ win rate is required to be profitable. In reality:

$$\text{Expectancy } (E) = (P_{\text{win}} \times R_{\text{win}}) - (P_{\text{loss}} \times R_{\text{loss}})$$

$$\text{Break-Even Win Rate } (WR_{\text{BE}}) = \frac{1}{1 + RR}$$

* At **1 : 0.6 R:R**, required break-even win rate is **62.5%** (over 68% after retail spread friction). One loss erases 1.67 wins.
* At **1 : 1.5 R:R**, required break-even win rate is only **40.0%**. A 48% win rate generates substantial risk-adjusted compounding.

### Symmetrical Fixed Fractional Sizing
The engine uses strict **1.0% equity risk per trade**:
$$\text{Lot Size} = \frac{\text{Account Equity} \times 0.01}{\text{SL Distance (pips)} \times \text{Pip Value}}$$

Anti-martingale risk escalation (scaling up to 2.5% on wins) is explicitly disabled by default to prevent a single adverse stop-out from wiping out multiple consecutive winning sessions.

---

## 📱 Real-Time Telemetry & Dark-Mode Chart Dispatcher

The engine features an asynchronous Telegram notification pipeline in [`exness/telegram_notifier.py`](exness/telegram_notifier.py) and [`exness/chart_snapshot.py`](exness/chart_snapshot.py):

* **Event Triggers**:
  1. *Pending Order Dispatched*: Notifies symbol, limit price, stop loss, and target.
  2. *Order Filled*: Alerts live position open with fill slippage audit.
  3. *In-Flight Milestones*: Break-even lock at $+1.0R$, partial profit bank at $+1.5R$.
  4. *Trade Closed*: Complete forensic autopsy (PnL in USD and $R$, hold duration).
* **Dark-Mode TradingView Chart Snapshots**: Generates clean, high-contrast candlestick charts with plotted Entry, Stop Loss, and Take Profit lines rendered directly from actual MT5 price buffers.

---

## 📂 Repository Structure & File Catalog

```
ksm-institutional-quant/
├── exness/                                 # Production MT5 Live Execution Engine
│   ├── asset_profiles.json                 # Per-pair calibrated parameters (1.5R baseline)
│   ├── chart_snapshot.py                   # Dark-mode chart image renderer
│   ├── decider_guardian.py                 # Local Decider 2B inference bridge (CUDA)
│   ├── execution_sentinel.py               # Deterministic pre-flight invariant gatekeeper
│   ├── hybrid_decision_guardian.py         # Triad decision committee (Jev + Decider + Laya)
│   ├── inflight_copilot.py                 # In-flight trailing and break-even manager
│   ├── market_awareness.py                 # Session accumulation & spread monitor
│   ├── mt5_connection.py                   # Low-latency Exness MT5 bridge
│   ├── telegram_notifier.py                # Asynchronous Telegram trade dispatcher
│   └── trader.py                           # Master continuous trading daemon
│
├── decider/                                # System 1 Reasoning & Probe Architecture
│   ├── engine.py                           # Decider model execution core
│   ├── infer.py                            # Optimized FP16 / FP8 inference pipelines
│   └── systemone.py                        # System One policy wrappers
│
├── scripts/                                # Quantitative Verification & Tools
│   ├── camber_real_gpu_backtest.py         # 26-year multi-pair GPU backtest harness
│   ├── chamber_rr_stress_test.py           # Multi-decade R:R & money management stress test
│   ├── regression_benchmark.py             # 45-scenario institutional certification gate
│   └── security_audit.py                   # Automated secret and credential scanner
│
├── course_notes/                           # Algorithmic SMC/ICT lecture deconstructions
│   ├── class_01_part_1.md to class_08.md   # Systematic mechanics extractions
│   └── README.md                           # Syllabus and foundational overview
│
├── .env.example                            # Configuration template with placeholders
├── .gitignore                              # Prevents credential, data, and weight leaks
├── IBT_Clean.pine                          # Pine Script TradingView reference indicator
├── requirements.txt                        # Python dependencies
└── README.md                               # System documentation
```

---

## 📚 Research Papers & Formal Documentation

The repository includes a comprehensive 6-volume quantitative research series:

* **[Volume 1: All-Weather Quantitative Architecture](RESEARCH_PAPER_ALL_WEATHER_QUANT.md)**  
  *Macro regime shifts, structural edge, and 26-year historical cross-validation.*
* **[Volume 2: High-Frequency Microstructure & Spread Dynamics](RESEARCH_PAPER_VOL_2_MICROSTRUCTURE.md)**  
  *Exness empirical spread surface, rollover liquidity air-pockets, and fill physics.*
* **[Volume 3: Risk, Ruin, and the Mathematics of Convex Asymmetry](RESEARCH_PAPER_VOL_3_RISK_AND_RUIN.md)**  
  *Kelly criterion, drawdowns, anti-martingale hazards, and the 1:1.5R sweet spot.*
* **[Volume 4: Execution Infrastructure & MT5 Daemon Architecture](RESEARCH_PAPER_VOL_4_EXECUTION_INFRASTRUCTURE.md)**  
  *Asynchronous multiprocessing, tick buffers, daemon thread stability, and low-latency RPC.*
* **[Volume 5: Execution Sentinel & Invariant Gatekeeping](RESEARCH_PAPER_VOL_5_EXECUTION_SENTINEL.md)**  
  *Deterministic pre-flight invariants, volatility floors, and dynamic quarantine mechanics.*
* **[Volume 6: Neural Distillation: Jev to Decider 2B & Laya](RESEARCH_PAPER_VOL_6_NEURAL_DISTILLATION_JEV_LAYA.md)**  
  *Teacher-student policy distillation, LoRA fine-tuning, and on-device inference on consumer GPUs.*

---

## 🚀 Installation & Deployment Guide

### Prerequisites
* **Operating System**: Windows 10/11 or Windows Server (required for MetaTrader 5 Python API).
* **Python**: Version `3.10` or higher.
* **Broker Account**: Exness MT5 Standard, Pro, or Raw Spread account (Demo or Real).
* **GPU (Optional)**: NVIDIA GPU with CUDA support for local Decider 2B inference.

### Step 1: Clone the Repository
```bash
git clone https://github.com/prasadsince1999/ksm-institutional-quant.git
cd ksm-institutional-quant
```

### Step 2: Create a Virtual Environment & Install Dependencies
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Credentials
Copy the `.env.example` template to `.env` and fill in your details:
```bash
cp .env.example .env
```
Edit `.env` with your preferred text editor:
```ini
EXNESS_MT5_LOGIN=your_mt5_account_number
EXNESS_MT5_PASSWORD=your_mt5_password
EXNESS_MT5_SERVER=Exness-MT5Real  # or Exness-MT5Trial6 for demo
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 💻 CLI Usage & Operating Modes

### 1. Dry-Run Monitoring Mode (Safe Verification)
Scans active pairs, checks session liquidity, runs AI committee gates, and logs setups **without sending live orders**:
```bash
python exness/trader.py --timeframe 5 --risk 0.01 --capital 500.0
```

### 2. Live Automated Execution Mode
Runs the continuous background loop, placing pending limit orders and managing in-flight trades with flat 1.0% fixed fractional risk:
```bash
python exness/trader.py --live --loop --timeframe 5 --risk 0.01 --capital 500.0 --mm fixed_fractional
```

### 3. Run the Quantitative Stress Test
Execute the PyTorch CUDA simulation engine across historical data to evaluate R:R curves and money management:
```bash
python scripts/chamber_rr_stress_test.py
```

### 4. Run the 45-Scenario Certification Gate
Run the institutional regression test suite to verify model concordance:
```bash
python scripts/regression_benchmark.py
```

---

## ⚠️ Institutional Standards & Risk Disclaimer

1. **Not Financial Advice**: The software, algorithmic strategies, and research papers contained in this repository are for educational, research, and quantitative engineering purposes only.
2. **Capital Risk**: Foreign exchange and commodity trading carries substantial risk of loss. Past backtested performance is no guarantee of future live execution results.
3. **Execution Responsibility**: Users deploying this engine on real capital are solely responsible for ensuring adequate margin, VPS connectivity, broker spread conditions, and risk management parameters.

---

**Chief Architect**: PrasaD (KSM X Tech)  
**Engineering Discipline**: Advanced Agentic Coding & Institutional Quant Systems  
**License**: [MIT](LICENSE)
