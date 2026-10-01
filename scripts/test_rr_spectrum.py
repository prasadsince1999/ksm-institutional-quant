"""
scripts/test_rr_spectrum.py — Empirical comparison of Risk-to-Reward ratios.
Evaluates RR in [0.6, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0] on modern research data (2015–2023)
with all friction hurdles active (era spreads, 0.3p slip, 0.2p penetration, j > fill TP).
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import honest_replay as hr

data = {}
pairs = ["GBPJPY", "USDCAD", "EURJPY", "USDJPY", "GBPUSD", "EURUSD", "USDCHF"]
for p in pairs:
    f = os.path.join(hr.DATA_DIR, f"{p}_max_m5.parquet")
    if os.path.exists(f):
        data[p] = hr.load(p, 5)

sub_data = {}
for p, df in data.items():
    sub = df[(df.index >= pd.Timestamp("2015-01-01")) & (df.index <= pd.Timestamp("2023-12-31"))]
    if len(sub) > 1000:
        sub_data[p] = sub

setups_by_pair = {}
for p, df in sub_data.items():
    setups_by_pair[p] = hr.get_setups(df, p, {"min_body_ratio": 0.35, "killzones_only": True})

rr_values = [0.6, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0]
results = []

hr.MIN_STOP_SPREAD_RATIO = 8.0
hr.MIN_ATR_PIPS = 5.0
hr.BE_AT = 1.0

for rr in rr_values:
    trades = []
    for p, df in sub_data.items():
        trades += hr.simulate(df, p, setups_by_pair[p], rr)
    stats, done = hr.portfolio(trades)
    rs = np.array([t["r"] for t in done]) if done else np.array([0.0])
    mean_r = float(rs.mean()) if len(rs) else 0.0
    se = float(rs.std(ddof=1) / np.sqrt(len(rs))) if len(rs) > 1 else 0.0
    win_pct = float((rs > 0).mean() * 100) if len(rs) else 0.0
    ci_lo = mean_r - 1.96 * se
    ci_hi = mean_r + 1.96 * se
    results.append({
        "rr": rr,
        "n": len(done),
        "win_pct": round(win_pct, 1),
        "mean_r": round(mean_r, 4),
        "se": round(se, 4),
        "ci_lo": round(ci_lo, 4),
        "ci_hi": round(ci_hi, 4),
        "pf": stats.get("PF"),
        "net_r": round(float(rs.sum()), 1)
    })

print("-" * 75)
print(f"{'RR':<6}{'N':<8}{'Win%':<8}{'Mean R':<10}{'95% CI':<24}{'PF':<6}{'Net R':<8}")
print("-" * 75)
for r in results:
    ci = f"[{r['ci_lo']:+.4f}, {r['ci_hi']:+.4f}]"
    print(f"{r['rr']:<6}{r['n']:<8}{r['win_pct']:<8}{r['mean_r']:<+10.4f}{ci:<24}{r['pf']:<6}{r['net_r']:<+8.1f}")
print("-" * 75)
