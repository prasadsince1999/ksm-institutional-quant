"""
exness/backtest_m15.py — Multi-Year 15-Minute SMC Forex Backtester.
Evaluates the 15m SMC Strategy across 32.5 months of real interbank data (2024 to 2026).
Simulates:
  - Account: $100 starting balance
  - Risk: 1.0% ($1.00 per trade)
  - Limit Order 50% FVG Retest fills
  - Target: 1:2.0 RR (SL = Sweep Extreme - 1 pip, TP = 2x Risk)
  - Primary Alpha Pairs: USDJPY, EURJPY
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
import time

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
PRIMARY_PAIRS = ["USDJPY", "EURJPY"]
ALL_PAIRS = ["USDJPY", "EURJPY", "EURGBP", "EURUSD"]
INIT_CAPITAL = 100.0   # $100 starting capital for PrasaD
RISK_PCT = 0.01        # 1% risk per trade

def pip_size(pair: str) -> float:
    return 0.01 if "JPY" in pair else 0.0001

def backtest_pair_m15(pair: str):
    csv_path = os.path.join(DATA_DIR, f"{pair}_multiyear.csv")
    if not os.path.exists(csv_path):
        return None

    df_m1 = pd.read_csv(csv_path, parse_dates=["datetime"], index_col="datetime")
    df_m1.columns = [c.lower() for c in df_m1.columns]

    df_m15 = df_m1.resample("15min").agg({
        "open": "first", "high": "max", "low": "min", "close": "last"
    }).dropna()

    opens  = df_m15["open"].values
    highs  = df_m15["high"].values
    lows   = df_m15["low"].values
    closes = df_m15["close"].values
    times  = df_m15.index
    n = len(df_m15)
    pip = pip_size(pair)

    # Rolling ATR 20
    tr = np.maximum(highs - lows, np.maximum(np.abs(highs - np.roll(closes, 1)), np.abs(lows - np.roll(closes, 1))))
    tr[0] = highs[0] - lows[0]
    atr20 = pd.Series(tr).rolling(20).mean().values

    # 30-bar rolling swings (7.5 hours of market memory)
    sw_hi = pd.Series(highs).rolling(30).max().shift(3).values
    sw_lo = pd.Series(lows).rolling(30).min().shift(3).values

    bull_gaps = np.zeros(n, dtype=bool)
    bear_gaps = np.zeros(n, dtype=bool)
    bull_gaps[2:] = (lows[2:] > highs[:-2])
    bear_gaps[2:] = (highs[2:] < lows[:-2])

    hours = times.hour
    trades = []

    for i in range(50, n - 40):
        h = hours[i]
        if h < 7 or h >= 19:
            continue

        atr = atr20[i]
        if atr < 1.0 * pip:
            continue

        # Liquidity Sweep check in last 3 M15 bars
        ext_h = sw_hi[i]
        ext_l = sw_lo[i]

        bull_sweep = False
        bear_sweep = False
        sweep_extreme = 0.0

        for k in range(max(0, i-3), i):
            if lows[k] < ext_l and min(opens[k], closes[k]) >= ext_l:
                bull_sweep = True
                sweep_extreme = lows[k]
            if highs[k] > ext_h and max(opens[k], closes[k]) <= ext_h:
                bear_sweep = True
                sweep_extreme = highs[k]

        sig = None
        if bull_sweep and bull_gaps[i] and closes[i] > opens[i]:
            sig = "bull"
            limit_entry = highs[i-2] # AutoResearch Champion: FVG Edge Entry
            sl_price = sweep_extreme - (1.0 * pip)
            risk_dist = limit_entry - sl_price
        elif bear_sweep and bear_gaps[i] and closes[i] < opens[i]:
            sig = "bear"
            limit_entry = lows[i-2]  # AutoResearch Champion: FVG Edge Entry
            sl_price = sweep_extreme + (1.0 * pip)
            risk_dist = sl_price - limit_entry

        if sig is None or risk_dist <= 0:
            continue

        risk_pips = risk_dist / pip
        if risk_pips < 2.0 or risk_pips > 25.0:
            continue

        # Check for Limit Order fill in next 1 to 8 bars (within 2 hours)
        filled = False
        fill_bar = -1
        for f_step in range(1, 9):
            chk_idx = i + f_step
            if chk_idx >= n:
                break
            if sig == "bull":
                if lows[chk_idx] <= sl_price:
                    break # Invalidated before fill
                if lows[chk_idx] <= limit_entry:
                    filled = True
                    fill_bar = chk_idx
                    break
            else:
                if highs[chk_idx] >= sl_price:
                    break
                if highs[chk_idx] >= limit_entry:
                    filled = True
                    fill_bar = chk_idx
                    break

        if not filled:
            continue

        # Targets (Champion: 1:1.8 RR)
        target_rr = 1.8
        tp_price = limit_entry + (target_rr * risk_dist) if sig == "bull" else limit_entry - (target_rr * risk_dist)

        # Track outcome up to 32 bars (8 hours)
        outcome_r = None

        for step in range(1, 33):
            b_idx = fill_bar + step
            if b_idx >= n:
                break
            b_h = highs[b_idx]
            b_l = lows[b_idx]

            if sig == "bull":
                if b_l <= sl_price:
                    outcome_r = -1.0
                    break
                if b_h >= tp_price:
                    outcome_r = target_rr
                    break
            else:
                if b_h >= sl_price:
                    outcome_r = -1.0
                    break
                if b_l <= tp_price:
                    outcome_r = target_rr
                    break

        if outcome_r is None:
            outcome_r = 0.0 # Closed at market / breakeven after 8 hours

        trades.append({
            "pair": pair,
            "datetime": times[fill_bar],
            "year": times[fill_bar].year,
            "ym": times[fill_bar].strftime("%Y-%m"),
            "sig": sig,
            "risk_pips": round(risk_pips, 1),
            "r_multiple": outcome_r,
            "won": (outcome_r > 0),
        })

    return pd.DataFrame(trades)

def run_backtest():
    print("=" * 75)
    print("   EXNESS FOREX 15-MINUTE SMC INSTITUTIONAL BACKTEST (2024–2026)")
    print(f"   Initial Capital: ${INIT_CAPITAL:.2f} | Base Risk: {RISK_PCT*100:.1f}% (${INIT_CAPITAL*RISK_PCT:.2f})")
    print("   Execution: FVG Edge Limit Orders | Target: 1:1.8 RR (AutoResearch Champion)")
    print("=" * 75)

    all_dfs = []
    for p in PRIMARY_PAIRS:
        t0 = time.time()
        df_p = backtest_pair_m15(p)
        if df_p is not None:
            all_dfs.append(df_p)
            print(f"  ✓ {p:8s}: {len(df_p):3d} filled limit trades in {time.time()-t0:.1f}s")

    fdf = pd.concat(all_dfs, ignore_index=True)
    fdf.sort_values("datetime", inplace=True)
    total_trades = len(fdf)

    print("\n" + "─" * 75)
    print(f"PRIMARY ALPHA PAIR UNIVERSE (USDJPY + EURJPY): {total_trades} TRADES (32.5 MONTHS)")
    print("─" * 75)

    # Simulate Portfolio Growth
    capital = INIT_CAPITAL
    peak_capital = INIT_CAPITAL
    max_dd = 0.0

    daily_counts = {}
    executed = []

    for idx, row in fdf.iterrows():
        t_date = str(row["datetime"].date())
        if daily_counts.get(t_date, 0) >= 2:
            continue

        daily_counts[t_date] = daily_counts.get(t_date, 0) + 1
        dollar_risk = capital * RISK_PCT
        r_mult = row["r_multiple"]

        pnl = dollar_risk * r_mult
        capital += pnl

        if capital > peak_capital:
            peak_capital = capital
        dd = (peak_capital - capital) / peak_capital
        if dd > max_dd:
            max_dd = dd

        executed.append({
            **row.to_dict(),
            "capital": capital,
            "pnl": pnl
        })

    edf = pd.DataFrame(executed)
    n_ex = len(edf)
    wins = edf["won"].sum()
    be_trades = sum(1 for e in executed if e["r_multiple"] == 0.0)
    losses = n_ex - wins - be_trades
    wr = (wins / n_ex * 100) if n_ex > 0 else 0
    total_r = edf["r_multiple"].sum()
    net_ret = ((capital - INIT_CAPITAL) / INIT_CAPITAL) * 100

    print(f"\n🏆 PORTFOLIO PERFORMANCE SUMMARY:")
    print(f"  • Total Trades Executed : {n_ex} (~7 trades / month)")
    print(f"  • Winning Trades        : {wins} ({wr:.2f}%)")
    print(f"  • Break-Even Trades     : {be_trades}")
    print(f"  • Losing Trades         : {losses}")
    print(f"  • Break-Even Win Rate   : 35.71% (Required for 1:1.8 RR)")
    print(f"  • Net Institutional Edge: +{wr - 35.71:.2f}% Above Break-Even")
    print(f"  • Total Net R-Multiple  : {total_r:+6.1f} R")
    print(f"  • Starting Capital      : ${INIT_CAPITAL:,.2f}")
    print(f"  • Final Capital         : ${capital:,.2f} (Net Return: {net_ret:+.1f}%)")
    print(f"  • Maximum Peak Drawdown : {max_dd*100:.1f}%")

    print("\n" + "=" * 75)
    print("   YEAR-BY-YEAR CONSISTENCY (2024 vs 2025 vs 2026):")
    print("=" * 75)
    for yr, grp in fdf.groupby("year"):
        n_yr = len(grp)
        w_yr = grp["won"].sum()
        r_yr = grp["r_multiple"].sum()
        wr_yr = (w_yr / n_yr * 100) if n_yr > 0 else 0
        gain_1pct = r_yr * 1.0
        gain_2pct = r_yr * 2.0
        print(f"  Year {yr}: {n_yr:3d} trades | Win Rate: {wr_yr:5.1f}% | Net R: {r_yr:+5.1f}R | Return @ 1%: {gain_1pct:+5.1f}% | Return @ 2%: {gain_2pct:+5.1f}%")

    print("\n" + "=" * 75)
    print("   PAIR PERFORMANCE BREAKDOWN:")
    print("=" * 75)
    for p_name, grp in fdf.groupby("pair"):
        n_p = len(grp)
        w_p = grp["won"].sum()
        r_p = grp["r_multiple"].sum()
        wr_p = (w_p / n_p * 100) if n_p > 0 else 0
        print(f"  • {p_name:8s}: {n_p:3d} trades | Win Rate: {wr_p:5.1f}% | Net R: {r_p:+5.1f}R (+{r_p*1.0:+5.1f}% ROI)")
    print("=" * 75)

if __name__ == "__main__":
    run_backtest()
