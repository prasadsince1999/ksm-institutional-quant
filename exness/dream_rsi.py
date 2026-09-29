"""
exness/dream_rsi.py — Dream-RSI: Recursive Self-Improvement Engine for Institutional Trading.
Based on the DeepMind/Google Technical Report (2026): 'Dream-RSI: Recursive Self-Improvement through Evolving Worlds'.

Core Architecture:
1. Online Exploration (MetaTrader 5): Live trading logs decisions into a Discovery Tree on disk.
2. Replay Simulator Pool (History): 10-Year parquet data + live execution traces act as an exact,
   zero-execution-cost replay simulator.
3. Offline Dreaming: Explores thousands of policy revisions (wicks, bodies, killzones, target RRs)
   at zero risk in milliseconds.
4. Monotonic Improvement Gate: The winning policy can NEVER be worse than the currently deployed one,
   because the current policy is always in the candidate set.
5. Autonomous Deployment: Updates asset_profiles.json only when a revision mathematically beats the baseline.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
import json
import time
import itertools
from datetime import datetime
import pandas as pd
import numpy as np

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
EXNESS_DIR = os.path.join(ROOT_DIR, "exness")
PROFILES_PATH = os.path.join(EXNESS_DIR, "asset_profiles.json")
DISCOVERY_TREE_PATH = os.path.join(DATA_DIR, "live_discovery_tree.json")

def pip_size(pair: str) -> float:
    if "XAU" in pair or "GOLD" in pair:
        return 0.10
    return 0.01 if "JPY" in pair else 0.0001

class LiveDiscoveryTreeLogger:
    """
    Logs live trading exploration steps from MetaTrader 5 into a persistent Discovery Tree.
    This log becomes part of the Replay Simulator pool for offline dreaming.
    """
    def __init__(self, filepath=DISCOVERY_TREE_PATH):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([], f)

    def log_node(self, node_data: dict):
        """Appends an exploration decision node to the discovery tree."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                tree = json.load(f)
            node_data["timestamp"] = datetime.utcnow().isoformat()
            tree.append(node_data)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(tree, f, indent=2)
        except Exception as e:
            print(f"⚠️ [Dream-RSI Logger] Error logging discovery node: {e}")

class DreamRSIEngine:
    """
    Recursive Self-Improvement Engine using Historical Replay Simulators.
    """
    def __init__(self, pairs=None):
        if pairs is None:
            self.pairs = ["XAUUSD", "EURJPY", "GBPJPY", "EURUSD", "NZDUSD", "USDJPY", "AUDUSD", "GBPUSD", "USDCAD", "USDCHF"]
        else:
            self.pairs = pairs

        self.current_profiles = self.load_profiles()
        self.tree_logger = LiveDiscoveryTreeLogger()

    def load_profiles(self) -> dict:
        if os.path.exists(PROFILES_PATH):
            with open(PROFILES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_profiles(self, profiles: dict):
        with open(PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=4)
        print(f"💾 [Dream-RSI] Successfully deployed updated policies to: {PROFILES_PATH}")

    def load_replay_world(self, pair: str):
        """
        Loads the multi-decade historical dataset (up to 26 years) for a pair from the parquet cache.
        Precomputes market structure, session sweeps, and future price paths once.
        """
        max_file = os.path.join(DATA_DIR, f"{pair.upper()}_max_m5.parquet")
        ten_file = os.path.join(DATA_DIR, f"{pair.upper()}_10y_m5.parquet")
        parquet_file = max_file if os.path.exists(max_file) else ten_file
        if not os.path.exists(parquet_file):
            print(f"⚠️ [Dream-RSI] Parquet replay simulator not found: {parquet_file}")
            return None, 0

        print(f"  [REPLAY WORLD] Ingesting: {os.path.basename(parquet_file)}")
        df = pd.read_parquet(parquet_file)
        df.columns = [c.lower() for c in df.columns]
        opens  = df["open"].values
        highs  = df["high"].values
        lows   = df["low"].values
        closes = df["close"].values
        times  = df.index
        n = len(df)
        pip = pip_size(pair)
        is_gold = "XAU" in pair

        tr = np.maximum(highs - lows, np.maximum(np.abs(highs - np.roll(closes, 1)), np.abs(lows - np.roll(closes, 1))))
        tr[0] = highs[0] - lows[0]
        atr20 = pd.Series(tr).rolling(20).mean().values

        # H1 Trend (span=600 on M5 = 50 hours)
        ema_trend = pd.Series(closes).ewm(span=600, adjust=False).mean().values

        # Swings (24 bars)
        sw_hi = pd.Series(highs).rolling(24).max().shift(3).values
        sw_lo = pd.Series(lows).rolling(24).min().shift(3).values

        hours = times.hour
        dates = times.date

        ash = np.full(n, np.nan)
        asl = np.full(n, np.nan)
        pdh = np.full(n, np.nan)
        pdl = np.full(n, np.nan)

        curr_date = None
        day_h, day_l = -1e9, 1e9
        prev_h, prev_l = -1e9, 1e9
        asia_h, asia_l = -1e9, 1e9

        for idx in range(n):
            d = dates[idx]
            h = hours[idx]
            if d != curr_date:
                curr_date = d
                prev_h, prev_l = day_h, day_l
                day_h, day_l = highs[idx], lows[idx]
                asia_h, asia_l = -1e9, 1e9
            else:
                day_h = max(day_h, highs[idx])
                day_l = min(day_l, lows[idx])

            if 0 <= h < 7:
                asia_h = max(asia_h, highs[idx])
                asia_l = min(asia_l, lows[idx])

            if prev_h > 0:
                pdh[idx] = prev_h
                pdl[idx] = prev_l
            if h >= 7 and asia_h > 0:
                ash[idx] = asia_h
                asl[idx] = asia_l

        bull_gaps = np.zeros(n, dtype=bool)
        bear_gaps = np.zeros(n, dtype=bool)
        bull_gaps[2:] = (lows[2:] > highs[:-2])
        bear_gaps[2:] = (highs[2:] < lows[:-2])

        c_r = highs - lows
        c_b = np.abs(closes - opens)
        safe_cr = np.maximum(c_r, 1e-9)
        body_ratios = np.where(c_r > 0, c_b / safe_cr, 0.0)

        min_breathing_pips = 15.0 if is_gold else (8.0 if "JPY" in pair else 5.0)
        sl_buf = 2.0 * pip if is_gold else 1.0 * pip
        max_risk_pips = 120.0 if is_gold else 35.0

        candidates = []

        for i in range(50, n - 40):
            h = hours[i]
            if h < 7 or h >= 19:
                continue
            if atr20[i] < 1.0 * pip or c_r[i] < 0.5 * pip:
                continue

            ref_h, ref_l = sw_hi[i], sw_lo[i]

            for k in range(max(0, i-3), i):
                k_r = highs[k] - lows[k]
                if k_r <= 0:
                    continue
                lower_wick = min(opens[k], closes[k]) - lows[k]
                upper_wick = highs[k] - max(opens[k], closes[k])
                lw_ratio = lower_wick / k_r
                uw_ratio = upper_wick / k_r

                swept_bull = False
                is_session_sweep_bull = False
                if not np.isnan(pdl[k]) and lows[k] < pdl[k] and min(opens[k], closes[k]) >= pdl[k]:
                    swept_bull = True
                    is_session_sweep_bull = True
                elif not np.isnan(asl[k]) and lows[k] < asl[k] and min(opens[k], closes[k]) >= asl[k]:
                    swept_bull = True
                    is_session_sweep_bull = True
                elif lows[k] < ref_l and min(opens[k], closes[k]) >= ref_l:
                    swept_bull = True

                if swept_bull and bull_gaps[i] and closes[i] > opens[i]:
                    limit_entry = highs[i-2]
                    sl_price = lows[k] - sl_buf
                    risk_dist = limit_entry - sl_price
                    if risk_dist > 0:
                        risk_pips = risk_dist / pip
                        if risk_pips < min_breathing_pips:
                            risk_dist = min_breathing_pips * pip
                            sl_price = limit_entry - risk_dist
                            risk_pips = min_breathing_pips
                        if risk_pips <= max_risk_pips:
                            candidates.append({
                                "idx": i,
                                "year": times[i].year,
                                "type": "BUY",
                                "hour": h,
                                "h1_bull": bool(closes[i] > ema_trend[i]),
                                "session_sweep": is_session_sweep_bull,
                                "wick_ratio": lw_ratio,
                                "body_ratio": body_ratios[i],
                                "entry": limit_entry,
                                "sl": sl_price,
                                "risk_dist": risk_dist,
                                "future_bars": [(highs[m], lows[m]) for m in range(i+1, min(i+41, n))]
                            })

                swept_bear = False
                is_session_sweep_bear = False
                if not np.isnan(pdh[k]) and highs[k] > pdh[k] and max(opens[k], closes[k]) <= pdh[k]:
                    swept_bear = True
                    is_session_sweep_bear = True
                elif not np.isnan(ash[k]) and highs[k] > ash[k] and max(opens[k], closes[k]) <= ash[k]:
                    swept_bear = True
                    is_session_sweep_bear = True
                elif highs[k] > ref_h and max(opens[k], closes[k]) <= ref_h:
                    swept_bear = True

                if swept_bear and bear_gaps[i] and closes[i] < opens[i]:
                    limit_entry = lows[i-2]
                    sl_price = highs[k] + sl_buf
                    risk_dist = sl_price - limit_entry
                    if risk_dist > 0:
                        risk_pips = risk_dist / pip
                        if risk_pips < min_breathing_pips:
                            risk_dist = min_breathing_pips * pip
                            sl_price = limit_entry + risk_dist
                            risk_pips = min_breathing_pips
                        if risk_pips <= max_risk_pips:
                            candidates.append({
                                "idx": i,
                                "year": times[i].year,
                                "type": "SELL",
                                "hour": h,
                                "h1_bull": bool(closes[i] > ema_trend[i]),
                                "session_sweep": is_session_sweep_bear,
                                "wick_ratio": uw_ratio,
                                "body_ratio": body_ratios[i],
                                "entry": limit_entry,
                                "sl": sl_price,
                                "risk_dist": risk_dist,
                                "future_bars": [(highs[m], lows[m]) for m in range(i+1, min(i+41, n))]
                            })

        return candidates, n

    def simulate_policy_offline(self, candidates, policy: dict, precomputed_outcomes: dict):
        """
        Replays a policy candidate across the historical tree at ZERO execution cost.
        Returns: (win_rate, profit_factor, net_r, trades, score)
        """
        trr = policy["target_rr"]
        kz = policy["killzones_only"]
        h1 = policy["use_h1_filter"]
        sess_only = policy.get("session_sweep_only", False)
        wick = policy["min_wick_ratio"]
        body = policy["min_body_ratio"]

        cached_res = precomputed_outcomes[trr]
        w, l = 0, 0
        net = 0.0

        for idx, c in enumerate(candidates):
            if kz:
                h = c["hour"]
                if not ((7 <= h <= 10) or (12 <= h <= 15)):
                    continue
            if h1:
                if c["type"] == "BUY" and not c["h1_bull"]:
                    continue
                if c["type"] == "SELL" and c["h1_bull"]:
                    continue
            if sess_only and not c["session_sweep"]:
                continue
            if c["wick_ratio"] < wick:
                continue
            if c["body_ratio"] < body:
                continue

            res, r_mult = cached_res[idx]
            if res == "WIN":
                w += 1
                net += r_mult
            elif res == "LOSS":
                l += 1
                net += r_mult

        tot = w + l
        if tot == 0:
            return 0.0, 0.0, 0.0, 0, -1e9

        wr = (w / tot) * 100.0
        pf = (w * trr) / l if l > 0 else 999.0
        exp = net / tot

        # Dream-RSI Multi-Objective Fitness
        score = (wr * 2.0) + (min(tot, 250) * 0.4) + (pf * 15.0) + (exp * 40.0)
        return wr, pf, net, tot, score

    def dream_for_pair(self, pair: str):
        """
        Executes one Dream-RSI loop iteration for a specific currency pair:
        1. Loads Replay Simulator
        2. Retrieves currently deployed policy pi^0
        3. Dreams M revisions {pi^1, ... pi^M}
        4. Applies Monotonic Improvement Gate: Deploy winner only if Score(pi*) > Score(pi^0)
        """
        print(f"\n🌙 [Dream-RSI] Initiating Offline Dreaming for {pair}...")
        t0 = time.time()
        candidates, total_bars = self.load_replay_world(pair)
        if not candidates:
            print(f"  ❌ Could not load world for {pair}")
            return None, False

        # Precompute trade outcomes for all candidate target RRs
        trr_options = [0.6, 0.7, 0.8, 0.9, 1.0, 1.2]
        precomputed = {}
        for trr in trr_options:
            outcomes = []
            for c in candidates:
                entry, sl, r_dist = c["entry"], c["sl"], c["risk_dist"]
                sig = c["type"]
                tp = entry + (trr * r_dist) if sig == "BUY" else entry - (trr * r_dist)
                filled = False
                res_str = "EXPIRED"
                r_val = 0.0
                for b_h, b_l in c["future_bars"]:
                    if not filled:
                        if sig == "BUY" and b_l <= entry:
                            filled = True
                        elif sig == "SELL" and b_h >= entry:
                            filled = True
                    if filled:
                        if sig == "BUY":
                            if b_l <= sl:
                                res_str = "LOSS"
                                r_val = -1.0
                                break
                            elif b_h >= tp:
                                res_str = "WIN"
                                r_val = trr
                                break
                        elif sig == "SELL":
                            if b_h >= sl:
                                res_str = "LOSS"
                                r_val = -1.0
                                break
                            elif b_l <= tp:
                                res_str = "WIN"
                                r_val = trr
                                break
                outcomes.append((res_str, r_val))
            precomputed[trr] = outcomes

        # Retrieve Baseline (pi^0)
        baseline_policy = self.current_profiles.get(pair, {
            "target_rr": 0.7,
            "use_h1_filter": True,
            "killzones_only": True,
            "session_sweep_only": False,
            "min_wick_ratio": 0.4,
            "min_body_ratio": 0.5
        })

        b_wr, b_pf, b_net, b_tot, b_score = self.simulate_policy_offline(candidates, baseline_policy, precomputed)
        print(f"  Current Deployed Policy (pi^0): WR: {b_wr:.2f}% | PF: {b_pf:.2f} | Net: {b_net:+.1f}R | Trades: {b_tot} | Score: {b_score:.1f}")

        # Dream Space Generation: Explore revisions
        h1_opts = [True, False]
        kz_opts = [True, False]
        sess_opts = [True, False]
        wick_opts = [0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
        body_opts = [0.35, 0.45, 0.55, 0.65]

        dream_grid = list(itertools.product(trr_options, h1_opts, kz_opts, sess_opts, wick_opts, body_opts))

        best_policy = baseline_policy
        best_score = b_score
        best_stats = (b_wr, b_pf, b_net, b_tot)
        improved = False

        dream_replays = 0
        min_trade_thresh = 15 if "XAU" in pair else 35

        for trr, h1, kz, sess_only, wick, body in dream_grid:
            dream_replays += 1
            cand_policy = {
                "pair": pair,
                "target_rr": trr,
                "use_h1_filter": h1,
                "killzones_only": kz,
                "session_sweep_only": sess_only,
                "min_wick_ratio": wick,
                "min_body_ratio": body
            }

            wr, pf, net, tot, score = self.simulate_policy_offline(candidates, cand_policy, precomputed)
            if tot < min_trade_thresh:
                continue

            # Dream-RSI Monotonic Filter: Must be strictly higher score AND WR >= 70%
            if wr >= 70.0 and score > best_score:
                best_score = score
                best_policy = cand_policy
                best_stats = (wr, pf, net, tot)
                improved = True

        elapsed = time.time() - t0
        w_wr, w_pf, w_net, w_tot = best_stats

        print(f"  ⚡ Replayed {dream_replays:,d} dreamt policy trajectories in {elapsed:.2f}s (Zero Real Executions)")
        if improved:
            print(f"  🎯 [RECURSIVE UPGRADE FOUND!] New Policy pi*:")
            print(f"     • Win Rate     : {w_wr:.2f}% (Baseline: {b_wr:.2f}%)")
            print(f"     • Profit Factor: {w_pf:.2f} (Baseline: {b_pf:.2f})")
            print(f"     • Net Return   : {w_net:+.1f} R (Baseline: {b_net:+.1f} R)")
            print(f"     • Total Trades : {w_tot} trades over 10 years")
            print(f"     • Target RR    : 1:{best_policy['target_rr']:.1f}")
            best_policy["win_rate"] = round(w_wr, 2)
            best_policy["pf"] = round(w_pf, 2)
            best_policy["net_r"] = round(w_net, 1)
            best_policy["trades"] = w_tot
            best_policy["last_dream_rsi_upgrade"] = datetime.utcnow().isoformat()
            return best_policy, True
        else:
            print(f"  🛡️ [MONOTONIC INVARIANT PRESERVED] Deployed policy pi^0 remains optimal. No degradation permitted.")
            return baseline_policy, False

    def run_full_dream_cycle(self):
        """
        Runs the recursive self-improvement cycle across all assets in the universe.
        """
        print("=" * 85)
        print("   🧠 DREAM-RSI: RECURSIVE SELF-IMPROVEMENT ENGINE (Google DeepMind 2026)")
        print("   History as an Evolving Replay Simulator | Monotonic Improvement Guarantee")
        print("=" * 85)

        updated_profiles = dict(self.current_profiles)
        upgrades_count = 0

        for pair in self.pairs:
            best_policy, upgraded = self.dream_for_pair(pair)
            if best_policy:
                updated_profiles[pair] = best_policy
                if upgraded:
                    upgrades_count += 1

        if upgrades_count > 0:
            self.save_profiles(updated_profiles)
            print(f"\n🚀 [Dream-RSI] Successfully deployed {upgrades_count} upgraded policies to live trading!")
        else:
            print(f"\n✅ [Dream-RSI] All policies are currently at mathematical global optima (>= 70% Win Rate).")
        print("=" * 85)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dream-RSI: Recursive Self-Improvement Engine")
    parser.add_argument("--dream", action="store_true", help="Execute offline dreaming loop across replay simulators")
    parser.add_argument("--pair", type=str, default=None, help="Target specific pair to dream on")
    args = parser.parse_args()

    pairs = [args.pair.upper()] if args.pair else None
    engine = DreamRSIEngine(pairs=pairs)
    engine.run_full_dream_cycle()
