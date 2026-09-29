"""
exness/evaluator_forex.py — Institutional Forex Backtest Evaluator for AutoResearch.
Evaluates candidate SMC parameter sets on 32.5 months of multi-year M15 data (USDJPY & EURJPY).
Pre-caches resampled M15 data in memory for sub-second evaluation turns.
"""

import os
import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import pandas as pd
import numpy as np

DATA_DIR = os.path.abspath(os.path.join(ROOT_DIR, "data"))
PRIMARY_PAIRS = ["USDJPY", "EURJPY"]

def pip_size(pair: str) -> float:
    return 0.01 if "JPY" in pair else 0.0001

class ForexDatasetCache:
    _instance = None

    @classmethod
    def get_data(cls):
        if cls._instance is None:
            cls._instance = cls._load_all()
        return cls._instance

    @classmethod
    def _load_all(cls):
        cache = {}
        for pair in PRIMARY_PAIRS:
            csv_path = os.path.join(DATA_DIR, f"{pair}_multiyear.csv")
            if not os.path.exists(csv_path):
                continue
            df_m1 = pd.read_csv(csv_path, parse_dates=["datetime"], index_col="datetime")
            df_m1.columns = [c.lower() for c in df_m1.columns]
            df_m15 = df_m1.resample("15min").agg({
                "open": "first", "high": "max", "low": "min", "close": "last"
            }).dropna()
            cache[pair] = df_m15
        
        # Align index across pairs for SMT cross-checks
        if "USDJPY" in cache and "EURJPY" in cache:
            common = cache["USDJPY"].index.intersection(cache["EURJPY"].index)
            cache["USDJPY"] = cache["USDJPY"].loc[common].copy()
            cache["EURJPY"] = cache["EURJPY"].loc[common].copy()
            
            # Precompute Asian Session Range (00:00 to 06:00 UTC) for both
            for p in PRIMARY_PAIRS:
                df = cache[p]
                hours = df.index.hour
                asian_mask = (hours >= 0) & (hours < 6)
                asian_df = df[asian_mask]
                a_hi = asian_df.groupby(asian_df.index.date)["high"].max()
                a_lo = asian_df.groupby(asian_df.index.date)["low"].min()
                dates = df.index.date
                df["asian_hi"] = [a_hi.get(d, np.nan) for d in dates]
                df["asian_lo"] = [a_lo.get(d, np.nan) for d in dates]
                
        return cache

def evaluate_forex_params(params: dict) -> dict:
    """
    Evaluates a specific set of parameters against the cached multi-year M15 data.
    Returns quantitative performance metrics and Karpathy objective fitness.
    """
    cache = ForexDatasetCache.get_data()
    all_trades = []

    sw_len = params.get("swing_lookback", 30)
    sw_mem = params.get("sweep_memory", 3)
    min_gap_mult = params.get("min_gap_atr_mult", 0.0)
    min_body_ratio = params.get("min_body_ratio", 0.0)
    target_rr = params.get("target_rr", 2.0)
    entry_depth = params.get("entry_depth", 0.50) # 0.50 = midpoint, 0.382 = shallow, 0.618 = deep
    filter_smt = params.get("filter_smt", False)
    filter_judas = params.get("filter_judas", False)
    h_start = params.get("session_start_hour", 7)
    h_end = params.get("session_end_hour", 19)
    min_risk_pips = params.get("min_risk_pips", 2.0)
    max_risk_pips = params.get("max_risk_pips", 25.0)
    sl_buf_pips = params.get("sl_buffer_pips", 1.0)
    max_hold_bars = params.get("max_hold_bars", 32) # 8 hours

    uj_df = cache.get("USDJPY")
    ej_df = cache.get("EURJPY")

    if uj_df is None or ej_df is None:
        return {"fitness": 0.0, "net_r": 0.0, "win_rate": 0.0}

    # Pre-extract rolling swings for SMT comparison
    uj_highs = uj_df["high"].values
    uj_lows  = uj_df["low"].values
    ej_highs = ej_df["high"].values
    ej_lows  = ej_df["low"].values

    uj_sw_hi = pd.Series(uj_highs).rolling(sw_len).max().shift(3).values
    uj_sw_lo = pd.Series(uj_lows).rolling(sw_len).min().shift(3).values
    ej_sw_hi = pd.Series(ej_highs).rolling(sw_len).max().shift(3).values
    ej_sw_lo = pd.Series(ej_lows).rolling(sw_len).min().shift(3).values

    for pair in PRIMARY_PAIRS:
        df = cache[pair]
        opens  = df["open"].values
        highs  = df["high"].values
        lows   = df["low"].values
        closes = df["close"].values
        times  = df.index
        n = len(df)
        pip = pip_size(pair)

        # Swings for this pair
        sw_hi = uj_sw_hi if pair == "USDJPY" else ej_sw_hi
        sw_lo = uj_sw_lo if pair == "USDJPY" else ej_sw_lo
        other_sw_hi = ej_sw_hi if pair == "USDJPY" else uj_sw_hi
        other_sw_lo = ej_sw_lo if pair == "USDJPY" else uj_sw_lo
        other_highs = ej_highs if pair == "USDJPY" else uj_highs
        other_lows  = ej_lows  if pair == "USDJPY" else uj_lows

        asian_hi = df["asian_hi"].values
        asian_lo = df["asian_lo"].values

        # ATR 20
        tr = np.maximum(highs - lows, np.maximum(np.abs(highs - np.roll(closes, 1)), np.abs(lows - np.roll(closes, 1))))
        tr[0] = highs[0] - lows[0]
        atr20 = pd.Series(tr).rolling(20).mean().values

        bull_gaps = np.zeros(n, dtype=bool)
        bear_gaps = np.zeros(n, dtype=bool)
        bull_gaps[2:] = (lows[2:] > highs[:-2])
        bear_gaps[2:] = (highs[2:] < lows[:-2])

        hours = times.hour

        for i in range(sw_len + 5, n - max_hold_bars - 8):
            h = hours[i]
            if h < h_start or h >= h_end:
                continue

            atr = atr20[i]
            if atr < 1.0 * pip:
                continue

            c_o, c_h, c_l, c_c = opens[i], highs[i], lows[i], closes[i]
            c_r = c_h - c_l
            c_b = abs(c_c - c_o)
            if c_r < 0.5 * pip:
                continue

            # Check Liquidity Sweeps
            ext_h = sw_hi[i]
            ext_l = sw_lo[i]

            bull_sweep = False
            bear_sweep = False
            sweep_extreme = 0.0

            for k in range(max(0, i - sw_mem), i):
                if lows[k] < ext_l and min(opens[k], closes[k]) >= ext_l:
                    bull_sweep = True
                    sweep_extreme = lows[k]
                if highs[k] > ext_h and max(opens[k], closes[k]) <= ext_h:
                    bear_sweep = True
                    sweep_extreme = highs[k]

            # ── SMT Divergence Filter ──
            if filter_smt:
                # Other pair must have failed to sweep (correlated crack)
                other_ext_h = other_sw_hi[i]
                other_ext_l = other_sw_lo[i]
                other_swept_low = any(other_lows[k] < other_ext_l for k in range(max(0, i - sw_mem), i))
                other_swept_high = any(other_highs[k] > other_ext_h for k in range(max(0, i - sw_mem), i))

                if bull_sweep and other_swept_low:
                    # Both swept -> no divergence
                    bull_sweep = False
                if bear_sweep and other_swept_high:
                    # Both swept -> no divergence
                    bear_sweep = False

            # ── Asian Judas Swing Filter ──
            if filter_judas:
                # Must be London Open (07:00 - 09:00 UTC) and must sweep Asian range
                is_london = (h >= 7 and h <= 9)
                a_h = asian_hi[i]
                a_l = asian_lo[i]
                if not is_london or np.isnan(a_h) or np.isnan(a_l):
                    continue
                # For bull setup, sweep low must have penetrated below asian_lo
                if bull_sweep and sweep_extreme >= a_l:
                    bull_sweep = False
                # For bear setup, sweep high must have penetrated above asian_hi
                if bear_sweep and sweep_extreme <= a_h:
                    bear_sweep = False

            sig = None
            limit_entry = 0.0
            sl_price = 0.0
            risk_dist = 0.0

            # Bullish Setup
            if bull_sweep and bull_gaps[i] and c_c > c_o:
                if min_body_ratio <= 0.0 or c_b >= min_body_ratio * c_r:
                    gap_size = lows[i] - highs[i-2]
                    if min_gap_mult <= 0.0 or gap_size >= min_gap_mult * atr:
                        sig = "bull"
                        limit_entry = highs[i-2] + (entry_depth * gap_size)
                        sl_price = sweep_extreme - (sl_buf_pips * pip)
                        risk_dist = limit_entry - sl_price

            # Bearish Setup
            elif bear_sweep and bear_gaps[i] and c_c < c_o:
                if min_body_ratio <= 0.0 or c_b >= min_body_ratio * c_r:
                    gap_size = lows[i-2] - highs[i]
                    if min_gap_mult <= 0.0 or gap_size >= min_gap_mult * atr:
                        sig = "bear"
                        limit_entry = lows[i-2] - (entry_depth * gap_size)
                        sl_price = sweep_extreme + (sl_buf_pips * pip)
                        risk_dist = sl_price - limit_entry

            if sig is None or risk_dist <= 0:
                continue

            risk_pips = risk_dist / pip
            if risk_pips < min_risk_pips or risk_pips > max_risk_pips:
                continue

            # Limit order fill check in next 1 to 8 bars
            filled = False
            fill_bar = -1
            for f_step in range(1, 9):
                chk_idx = i + f_step
                if chk_idx >= n:
                    break
                if sig == "bull":
                    if lows[chk_idx] <= sl_price:
                        break
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

            tp_price = limit_entry + (target_rr * risk_dist) if sig == "bull" else limit_entry - (target_rr * risk_dist)

            # Outcome tracking up to max_hold_bars
            outcome_r = None
            for step in range(1, max_hold_bars + 1):
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
                outcome_r = 0.0

            all_trades.append({
                "pair": pair,
                "datetime": times[fill_bar],
                "year": times[fill_bar].year,
                "sig": sig,
                "risk_pips": risk_pips,
                "r_multiple": outcome_r,
                "target_rr": target_rr,
                "won": (outcome_r > 0),
            })

    if len(all_trades) == 0:
        return {
            "total_trades": 0, "win_rate": 0.0, "net_r": 0.0,
            "max_drawdown": 100.0, "final_capital": 100.0, "fitness": 0.0
        }

    fdf = pd.DataFrame(all_trades)
    fdf.sort_values("datetime", inplace=True)

    # Apply Portfolio Simulation (Max 2 trades/day)
    capital = 100.0
    peak_capital = 100.0
    max_dd = 0.0
    daily_counts = {}
    executed = []

    for idx, row in fdf.iterrows():
        t_date = str(row["datetime"].date())
        if daily_counts.get(t_date, 0) >= params.get("max_daily_trades", 2):
            continue
        daily_counts[t_date] = daily_counts.get(t_date, 0) + 1

        dollar_risk = capital * params.get("risk_pct", 0.01)
        r_mult = row["r_multiple"]
        pnl = dollar_risk * r_mult
        capital += pnl

        if capital > peak_capital:
            peak_capital = capital
        dd = (peak_capital - capital) / peak_capital
        if dd > max_dd:
            max_dd = dd

        executed.append({**row.to_dict(), "capital": capital, "pnl": pnl})

    edf = pd.DataFrame(executed)
    n_ex = len(edf)
    if n_ex == 0:
        return {
            "total_trades": 0, "win_rate": 0.0, "net_r": 0.0,
            "max_drawdown": 100.0, "final_capital": 100.0, "fitness": 0.0
        }

    wins = edf["won"].sum()
    be_trades = sum(1 for e in executed if e["r_multiple"] == 0.0)
    losses = n_ex - wins - be_trades
    wr = (wins / n_ex * 100) if n_ex > 0 else 0
    total_r = edf["r_multiple"].sum()

    gross_profit = sum(e["pnl"] for e in executed if e["pnl"] > 0)
    gross_loss = abs(sum(e["pnl"] for e in executed if e["pnl"] < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 9.99

    # Required break-even win rate for given target_rr
    be_wr = 100.0 / (1.0 + target_rr)

    # Karpathy Objective Fitness Function
    # Balances: Net R, Drawdown safety, edge over break-even, trade statistical sample size
    size_factor = min(1.0, n_ex / 100.0) # penalty if fewer than 100 trades over 32 months
    dd_penalty = max(0.0, 1.0 - (max_dd * 1.5))
    edge_ratio = (wr / be_wr) if be_wr > 0 else 1.0
    fitness = round(total_r * dd_penalty * edge_ratio * size_factor, 2)

    return {
        "total_trades": n_ex,
        "wins": int(wins),
        "losses": int(losses),
        "be_trades": int(be_trades),
        "win_rate": round(wr, 2),
        "be_win_rate": round(be_wr, 2),
        "edge": round(wr - be_wr, 2),
        "net_r": round(total_r, 1),
        "profit_factor": round(profit_factor, 2),
        "final_capital": round(capital, 2),
        "net_roi_pct": round(((capital - 100.0) / 100.0) * 100, 2),
        "max_drawdown": round(max_dd * 100, 2),
        "fitness": fitness
    }

if __name__ == "__main__":
    from exness.strategy_smc_m15 import PARAMS
    print("Pre-caching dataset and running baseline evaluation...")
    import time
    t0 = time.time()
    res = evaluate_forex_params(PARAMS)
    print(f"Evaluated in {time.time()-t0:.2f}s:")
    for k, v in res.items():
        print(f"  {k}: {v}")
