"""
backtest.py — Fixed Evaluator (NEVER modified by agent)
Scores strategy.py on historical 1-min forex data.

Score = win_rate * profit_factor * (1 - max_drawdown)
Binary options payout = 1.80x (configurable)
"""

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from strategy import generate_signals, PARAMS

# ── Config ──────────────────────────────────────────────
PAYOUT      = 1.80     # binary options payout multiplier
BET_PCT     = 0.02     # 2% of capital per trade (flat betting)
INIT_CAP    = 100_000  # starting capital ₹
DATA_DIR    = "./data"  # folder with CSV files per pair

PAIRS = ["EURJPY", "EURGBP", "USDJPY", "AUDJPY", "CADJPY", "EURUSD", "GBPUSD"]

# ── Load Data ────────────────────────────────────────────
def load_pair(pair):
    """
    Expects CSV with columns: datetime, open, high, low, close
    Can be exported from TradingView or downloaded via yfinance/Kite.
    """
    path = os.path.join(DATA_DIR, f"{pair}_1min.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["datetime"], index_col="datetime")
    df.columns = [c.lower() for c in df.columns]
    return df.sort_index()

# ── Simulate trade outcomes ───────────────────────────────
def simulate_trade(df, signal, payout=PAYOUT):
    """
    Binary option: enter at close of signal bar.
    Win if price moves favorably in next 5 bars.
    """
    i   = signal["bar"]
    dir = signal["direction"]
    if i + 5 >= len(df):
        return None

    entry = df["close"].iloc[i]
    future_bars = df.iloc[i + 1 : i + 6]

    if dir == "bull":
        won = future_bars["close"].max() > entry
    else:
        won = future_bars["close"].min() < entry

    return won

# ── Main scoring function ─────────────────────────────────
def score(params=None):
    if params is None:
        params = PARAMS

    all_results = []
    capital = INIT_CAP
    peak    = INIT_CAP
    max_dd  = 0.0
    daily_counts = {}

    for pair in PAIRS:
        df = load_pair(pair)
        if df is None:
            continue

        signals = generate_signals(df, pair, params)

        for sig in signals:
            # daily trade cap
            bar_date = str(df.index[sig["bar"]].date())
            daily_counts[bar_date] = daily_counts.get(bar_date, 0) + 1
            if daily_counts[bar_date] > params.get("max_trades_per_day", 4):
                continue

            result = simulate_trade(df, sig)
            if result is None:
                continue

            bet = capital * BET_PCT
            if result:
                capital += bet * (payout - 1)
                all_results.append(1)
            else:
                capital -= bet
                all_results.append(0)

            if capital > peak:
                peak = capital
            dd = (peak - capital) / peak
            if dd > max_dd:
                max_dd = dd

    if len(all_results) < 20:
        return {"score": 0.0, "reason": "too_few_trades", "trades": len(all_results)}

    wins       = sum(all_results)
    total      = len(all_results)
    win_rate   = wins / total
    losses     = total - wins
    gross_wins = wins * BET_PCT * (PAYOUT - 1)
    gross_loss = losses * BET_PCT
    profit_factor = gross_wins / gross_loss if gross_loss > 0 else 99.0

    # THE SCORE — higher is better
    # Binary breakeven is 55.6% at 1.80x payout
    # Penalty if below breakeven
    breakeven_wr = 1 / PAYOUT  # ~0.556
    edge_bonus   = max(0, win_rate - breakeven_wr) * 2

    final_score = (win_rate * profit_factor * (1 - max_dd)) + edge_bonus

    return {
        "score":         round(final_score, 4),
        "win_rate":      round(win_rate, 4),
        "profit_factor": round(profit_factor, 4),
        "max_drawdown":  round(max_dd, 4),
        "total_trades":  total,
        "capital_final": round(capital, 2),
    }


if __name__ == "__main__":
    result = score()
    print(json.dumps(result, indent=2))
