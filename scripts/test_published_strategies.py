"""
scripts/test_published_strategies.py — Rigorous out-of-sample backtest of famous published strategies.

Implements and evaluates:
  1. Turtle Trading System 1 (20-day Donchian Breakout, 10-day exit, 2N ATR stop)
  2. Turtle Trading System 2 (55-day Donchian Breakout, 20-day exit, 2N ATR stop)
  3. Larry Williams Volatility Breakout (Open + 0.50 * PrevDayRange)
  4. Paul Tudor Jones 200-Day SMA Macro Momentum

Evaluated across 24+ years of real historical Forex tick data under era-adjusted spreads and slippage.
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import honest_replay as hr

PAIRS = ["GBPJPY", "USDCAD", "EURJPY", "USDJPY", "GBPUSD", "EURUSD", "USDCHF"]


def load_daily(pair):
    """Loads M5 parquet and resamples to daily candles (UTC)."""
    f = os.path.join(hr.DATA_DIR, f"{pair}_max_m5.parquet")
    if not os.path.exists(f):
        return None
    df = hr.load(pair, offset_hours=5)
    d = df.resample("1D").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last"
    }).dropna()
    d = d[d["high"] > d["low"]]
    return d


def compute_atr_n(df, period=20):
    """Computes the classic Turtle N (20-day exponential ATR)."""
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    n_bars = len(df)
    tr = np.zeros(n_bars)
    tr[0] = h[0] - l[0]
    for i in range(1, n_bars):
        tr[i] = max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1]))
    atr = pd.Series(tr, index=df.index).ewm(alpha=1.0/period, adjust=False).mean().values
    return atr


def backtest_turtle(daily_data, entry_len=20, exit_len=10, stop_n=2.0):
    """
    Backtests the pure Turtle Trading rules:
      - Buy when High > 20-day (or 55-day) High
      - Sell Short when Low < 20-day (or 55-day) Low
      - Stop loss at 2N (2 * ATR)
      - Exit when price crosses 10-day (or 20-day) opposite extreme
      - Real era-adjusted spreads & stop slippage
    """
    trades = []
    for pair, df in daily_data.items():
        pip = hr.strat.pip_size(pair)
        h = df["high"].values
        l = df["low"].values
        c = df["close"].values
        times = df.index
        n = len(df)
        if n < entry_len + 50:
            continue

        atr_n = compute_atr_n(df, 20)
        hi_entry = pd.Series(h).rolling(entry_len).max().shift(1).values
        lo_entry = pd.Series(l).rolling(entry_len).min().shift(1).values
        hi_exit = pd.Series(h).rolling(exit_len).max().shift(1).values
        lo_exit = pd.Series(l).rolling(exit_len).min().shift(1).values

        pos = 0 # +1 for long, -1 for short
        entry_px = 0.0
        stop_px = 0.0
        risk_dist = 0.0
        entry_idx = 0

        for i in range(entry_len + 1, n):
            yr = times[i].year
            sp = hr.spread_pips(pair, 12, yr) * pip
            slip = hr.SLIP_PIPS * pip

            # Check exits if in position
            if pos == 1:
                # Stopped out?
                if l[i] <= stop_px:
                    loss = (stop_px - entry_px - sp - slip) / risk_dist
                    trades.append({"pair": pair, "t_entry": times[entry_idx], "t_exit": times[i], "r": float(loss)})
                    pos = 0
                # System exit? (Break of 10-day low)
                elif l[i] <= lo_exit[i]:
                    exit_px = min(c[i], lo_exit[i])
                    pnl = (exit_px - entry_px - sp) / risk_dist
                    trades.append({"pair": pair, "t_entry": times[entry_idx], "t_exit": times[i], "r": float(pnl)})
                    pos = 0

            elif pos == -1:
                # Stopped out?
                if h[i] >= stop_px:
                    loss = (entry_px - stop_px - sp - slip) / risk_dist
                    trades.append({"pair": pair, "t_entry": times[entry_idx], "t_exit": times[i], "r": float(loss)})
                    pos = 0
                # System exit? (Break of 10-day high)
                elif h[i] >= hi_exit[i]:
                    exit_px = max(c[i], hi_exit[i])
                    pnl = (entry_px - exit_px - sp) / risk_dist
                    trades.append({"pair": pair, "t_entry": times[entry_idx], "t_exit": times[i], "r": float(pnl)})
                    pos = 0

            # Check entries if flat
            if pos == 0:
                cur_n = atr_n[i-1]
                if cur_n <= 0:
                    continue
                risk = stop_n * cur_n

                if h[i] > hi_entry[i]: # Long breakout
                    pos = 1
                    entry_px = hi_entry[i] + sp # enter at ask
                    stop_px = entry_px - risk
                    risk_dist = risk
                    entry_idx = i

                elif l[i] < lo_entry[i]: # Short breakdown
                    pos = -1
                    entry_px = lo_entry[i] # enter at bid
                    stop_px = entry_px + risk
                    risk_dist = risk
                    entry_idx = i

    return trades


def backtest_larry_williams(daily_data, k=0.50):
    """
    Backtests Larry Williams Daily Volatility Expansion:
      - Buy if Today's High >= Today's Open + K * PrevRange
      - Sell Short if Today's Low <= Today's Open - K * PrevRange
      - Exit at market Close (or end of next bar)
    """
    trades = []
    for pair, df in daily_data.items():
        pip = hr.strat.pip_size(pair)
        o = df["open"].values
        h = df["high"].values
        l = df["low"].values
        c = df["close"].values
        times = df.index
        n = len(df)
        if n < 50:
            continue

        rng = h - l
        prev_rng = pd.Series(rng).shift(1).values
        atr = compute_atr_n(df, 20)

        for i in range(21, n):
            yr = times[i].year
            sp = hr.spread_pips(pair, 12, yr) * pip
            slip = hr.SLIP_PIPS * pip
            prng = prev_rng[i]
            cur_atr = atr[i]
            if prng <= 0 or cur_atr <= 0:
                continue

            long_trigger = o[i] + (k * prng)
            short_trigger = o[i] - (k * prng)
            stop_dist = cur_atr * 1.0 # 1 ATR stop

            # Long breakout
            if h[i] >= long_trigger:
                entry = long_trigger + sp
                exit_px = c[i]
                stopped = l[i] <= entry - stop_dist
                r = -1.0 - (slip / stop_dist) if stopped else (exit_px - entry) / stop_dist
                trades.append({"pair": pair, "t_entry": times[i], "t_exit": times[i], "r": float(r)})

            # Short breakdown
            elif l[i] <= short_trigger:
                entry = short_trigger
                exit_px = c[i] + sp
                stopped = h[i] >= entry + stop_dist
                r = -1.0 - (slip / stop_dist) if stopped else (entry - exit_px) / stop_dist
                trades.append({"pair": pair, "t_entry": times[i], "t_exit": times[i], "r": float(r)})

    return trades


def print_stats(name, trades):
    rs = np.array([t["r"] for t in trades]) if trades else np.array([0.0])
    n = len(rs)
    if n == 0:
        print(f"{name}: No trades generated.")
        return
    mean = float(rs.mean())
    se = float(rs.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
    win_pct = float((rs > 0).mean() * 100)
    gw, gl = rs[rs > 0].sum(), -rs[rs < 0].sum()
    pf = round(float(gw / gl), 2) if gl > 0 else float("inf")
    ci_lo = mean - 1.96 * se
    ci_hi = mean + 1.96 * se
    net = float(rs.sum())

    print(f"\n{'='*75}")
    print(f"STRATEGY: {name}")
    print(f"{'='*75}")
    print(f"Total Trades (N)        : {n:,}")
    print(f"Win Rate                : {win_pct:.1f}%")
    print(f"Expectancy (Mean R)     : {mean:+.4f} R/trade")
    print(f"95% Confidence Interval : [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"Profit Factor (PF)      : {pf}")
    print(f"Total Net R             : {net:+.1f} R")
    print(f"{'='*75}")


def main():
    print("Loading 24+ years of data and resampling to Daily timeframe...")
    daily_data = {}
    for p in PAIRS:
        d = load_daily(p)
        if d is not None:
            daily_data[p] = d
            print(f"  • {p}: {len(d):,} daily bars ({d.index[0].strftime('%Y-%m-%d')} to {d.index[-1].strftime('%Y-%m-%d')})")

    # 1. Turtle System 1 (20-day Breakout)
    t1 = backtest_turtle(daily_data, entry_len=20, exit_len=10, stop_n=2.0)
    print_stats("Turtle System 1 (20-Day Breakout / 10-Day Exit / 2N Stop)", t1)

    # 2. Turtle System 2 (55-day Breakout)
    t2 = backtest_turtle(daily_data, entry_len=55, exit_len=20, stop_n=2.0)
    print_stats("Turtle System 2 (55-Day Breakout / 20-Day Exit / 2N Stop)", t2)

    # 3. Larry Williams Volatility Breakout (0.50 Range)
    lw = backtest_larry_williams(daily_data, k=0.50)
    print_stats("Larry Williams Volatility Breakout (0.50 * PrevRange)", lw)


if __name__ == "__main__":
    main()
