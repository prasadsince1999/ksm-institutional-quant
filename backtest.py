"""
backtest.py — Fixed Evaluator for IBT Binary Options Strategy
Scores strategy.py on historical 1-min forex data.

Binary Options Settlement Rules:
- Entry at close of signal candle i (which is the exact open of candle i+1).
- Expiration at close of candle i+1 (true 1-minute binary expiry).
- Bull (CALL): Win if close[i+1] > close[i].
- Bear (PUT):  Win if close[i+1] < close[i].
- Tie (ATM):   Refund (no gain, no loss).

Money Management Rules:
- 2% Base Stake (e.g. ₹200 on ₹10,000 capital).
- Two Win Streak (Lambo Binary):
    - Trade 1: Base Stake.
    - If Win -> Trade 2: Base Stake + Profit.
    - If Win -> Streak complete! Bank profit, reset to Base.
    - If Loss at any step -> Reset to Base Stake.
- Daily Risk Discipline:
    - Max 4 trades per day.
    - 3 consecutive losses = STOP for the day (Circuit Breaker).
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
import pandas as pd
from datetime import datetime
from strategy import generate_signals, PARAMS

PAYOUT_RATE = 0.85     # 85% net payout on Quotex (1.85x return)
BASE_STAKE_PCT = 0.02  # 2% base risk
INIT_CAPITAL = 10_000  # Starting capital in ₹ (e.g., ₹10,000)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

PAIRS = ["EURJPY", "EURGBP", "USDJPY", "EURUSD", "GBPUSD"]

def load_pair_data(pair):
    path = os.path.join(DATA_DIR, f"{pair}_1min.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["datetime"], index_col="datetime")
    df.columns = [c.lower() for c in df.columns]
    if df.index.tz is not None:
        df.index = df.index.tz_convert("UTC")
    return df.sort_index()

def simulate_1m_binary_trade(df, signal_bar, direction):
    """
    Simulates a 1-minute binary trade entered at signal_bar close.
    Settles exactly at signal_bar + 1 close.
    Returns: 1 (Win), 0 (Loss), None (Tie / Out of bounds)
    """
    if signal_bar + 1 >= len(df):
        return None

    entry_price = df["close"].iloc[signal_bar]
    exit_price = df["close"].iloc[signal_bar + 1]

    if direction == "bull":
        if exit_price > entry_price:
            return 1
        elif exit_price < entry_price:
            return 0
        else:
            return None  # Tie / Refund
    elif direction == "bear":
        if exit_price < entry_price:
            return 1
        elif exit_price > entry_price:
            return 0
        else:
            return None  # Tie / Refund
    return None

def run_backtest(params=None):
    if params is None:
        params = PARAMS

    print("\n" + "=" * 65)
    print("   IBT BINARY OPTIONS STRATEGY — RIGOROUS 1-MIN BACKTEST")
    print("=" * 65)

    all_signals = []
    
    # 1. Collect signals across all pairs
    for pair in PAIRS:
        df = load_pair_data(pair)
        if df is None:
            print(f"  ⚠️ Missing data for {pair}. Run get_data.py first.")
            continue

        signals = generate_signals(df, pair, params)
        for s in signals:
            all_signals.append({
                "pair": pair,
                "datetime": df.index[s["bar"]],
                "bar": s["bar"],
                "direction": s["direction"],
                "score": s.get("score", 0),
                "gap_type": s.get("gap_type", ""),
                "df": df,
            })

    if not all_signals:
        print("\n❌ No signals generated. Check data or relax parameters.")
        return None

    # Sort all signals chronologically
    all_signals.sort(key=lambda x: x["datetime"])
    print(f"\nTotal raw setups identified across {len(PAIRS)} pairs: {len(all_signals)}")

    # 2. Execute trade simulation with Two-Win Streak Money Management
    capital = INIT_CAPITAL
    peak_capital = INIT_CAPITAL
    max_drawdown = 0.0

    daily_trade_counts = {}
    daily_consecutive_losses = {}
    
    executed_trades = []
    streak_step = 1  # 1 = Base trade, 2 = Compounded trade
    current_consecutive_losses = 0
    max_consecutive_losses = 0

    for sig in all_signals:
        trade_date = str(sig["datetime"].date())

        # Daily trade cap (Max 4 per day)
        trades_today = daily_trade_counts.get(trade_date, 0)
        if trades_today >= params.get("max_trades_per_day", 4):
            continue

        # Circuit breaker: 3 consecutive losses in a day = Stop trading today
        day_losses = daily_consecutive_losses.get(trade_date, 0)
        if day_losses >= 3:
            continue

        # Simulate true 1-min binary outcome
        result = simulate_1m_binary_trade(sig["df"], sig["bar"], sig["direction"])
        if result is None:
            continue  # Tie / end of data

        daily_trade_counts[trade_date] = trades_today + 1

        # Two-Win Streak Stake calculation
        base_stake = capital * BASE_STAKE_PCT
        if streak_step == 1:
            stake = base_stake
        else:
            stake = base_stake + (base_stake * PAYOUT_RATE)

        # Apply outcome
        if result == 1:  # WIN
            net_gain = stake * PAYOUT_RATE
            capital += net_gain
            current_consecutive_losses = 0
            daily_consecutive_losses[trade_date] = 0

            if streak_step == 1:
                streak_step = 2  # Move to step 2 of streak
            else:
                streak_step = 1  # Streak successfully completed! Reset to base
        else:  # LOSS
            capital -= stake
            current_consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
            daily_consecutive_losses[trade_date] = day_losses + 1
            streak_step = 1  # Reset to base stake on loss

        # Track Drawdown
        if capital > peak_capital:
            peak_capital = capital
        dd = (peak_capital - capital) / peak_capital
        if dd > max_drawdown:
            max_drawdown = dd

        executed_trades.append({
            "datetime": sig["datetime"],
            "pair": sig["pair"],
            "direction": sig["direction"],
            "score": sig["score"],
            "gap_type": sig["gap_type"],
            "result": "WIN" if result == 1 else "LOSS",
            "stake": round(stake, 2),
            "capital": round(capital, 2),
        })

    total_executed = len(executed_trades)
    if total_executed == 0:
        print("\n❌ Zero trades passed daily and session filters.")
        return None

    wins = sum(1 for t in executed_trades if t["result"] == "WIN")
    losses = total_executed - wins
    win_rate = (wins / total_executed) * 100

    gross_profit = sum(t["stake"] * PAYOUT_RATE for t in executed_trades if t["result"] == "WIN")
    gross_loss = sum(t["stake"] for t in executed_trades if t["result"] == "LOSS")
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 99.0
    net_return_pct = ((capital - INIT_CAPITAL) / INIT_CAPITAL) * 100

    # 3. Print Results
    print("\n" + "─" * 65)
    print("                    BACKTEST RESULTS SUMMARY")
    print("─" * 65)
    print(f"Total Trades Executed:    {total_executed}")
    print(f"Winning Trades:           {wins}")
    print(f"Losing Trades:            {losses}")
    print(f"Win Rate:                 {win_rate:.2f}% (Breakeven at 85% payout is 54.05%)")
    print(f"Profit Factor:            {profit_factor:.2f}")
    print(f"Starting Capital:         ₹{INIT_CAPITAL:,.2f}")
    print(f"Final Capital:            ₹{capital:,.2f}")
    print(f"Net Profit / Loss:        ₹{capital - INIT_CAPITAL:,.2f} ({net_return_pct:+.2f}%)")
    print(f"Max Peak Drawdown:        {max_drawdown * 100:.2f}%")
    print(f"Max Consecutive Losses:   {max_consecutive_losses}")
    print("─" * 65)

    # Breakdown by Pair
    print("\nPair Performance Breakdown:")
    for pair in PAIRS:
        pair_trades = [t for t in executed_trades if t["pair"] == pair]
        if pair_trades:
            p_wins = sum(1 for t in pair_trades if t["result"] == "WIN")
            p_total = len(pair_trades)
            p_wr = (p_wins / p_total) * 100
            print(f"  • {pair:8s}: {p_total:3d} trades | {p_wins:2d} wins | Win Rate: {p_wr:5.1f}%")

    print("=" * 65)

    return {
        "total_trades": total_executed,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "net_profit": capital - INIT_CAPITAL,
        "max_drawdown": max_drawdown,
        "trades": executed_trades,
    }

if __name__ == "__main__":
    run_backtest()
