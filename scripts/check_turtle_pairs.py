import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import test_published_strategies as tps
import numpy as np, pandas as pd

daily_data = {}
for p in tps.PAIRS:
    d = tps.load_daily(p)
    if d is not None:
        daily_data[p] = d

t2 = tps.backtest_turtle(daily_data, entry_len=55, exit_len=20, stop_n=2.0)
df_t = pd.DataFrame(t2)
for p, g in df_t.groupby("pair"):
    rs = g["r"].values
    gw, gl = rs[rs > 0].sum(), -rs[rs < 0].sum()
    pf = round(gw / gl, 2) if gl > 0 else float("inf")
    w_pct = (rs > 0).mean() * 100
    print(f"{p:<8} N={len(rs):<5} Win%={w_pct:4.1f}% Mean={rs.mean():+.4f}R Net={rs.sum():+6.1f}R PF={pf}")
