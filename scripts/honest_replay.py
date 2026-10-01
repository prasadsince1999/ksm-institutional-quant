"""
scripts/honest_replay.py — Honest replay + walk-forward harness for KSM-Institutional-Quant.

What it fixes versus dream_rsi.py / chamber_rr_stress_test.py:
  1. Uses the SAME analyze_m15_setup() the live trader uses (no re-implemented copy that can drift).
  2. Ignores asset_profiles.json on purpose (those numbers are stale/in-sample). Params come from the grid.
  3. Converts HistData timestamps EST(UTC-5, no DST) -> UTC so "07:00 UTC killzone" means 07:00 UTC.
  4. Real costs: spread on entry/exit, limit must trade THROUGH the price, stop slippage.
  5. Portfolio limits like live: 1 trade per pair, max 3 concurrent, max 5 fills/day, chronological equity.
  6. Walk-forward: choose params on the TRAIN years only, report only on the next unseen year.
  7. --verify-causal: proves the strategy never peeks ahead by re-running on truncated data.
  8. --replay: prints bars one by one like a live chart, showing each setup, fill and exit.

Usage:
  python scripts/honest_replay.py --pairs EURUSD GBPUSD --walkforward --src-offset-hours 5
  python scripts/honest_replay.py --pairs EURUSD --verify-causal 40
  python scripts/honest_replay.py --pairs EURUSD --replay --from 2025-03-10 --to 2025-03-12
  python scripts/honest_replay.py --synthetic      # smoke test with fake data
"""
import argparse, os, sys, itertools, random
import numpy as np
import pandas as pd

if os.path.exists(os.path.join(os.path.dirname(__file__), "data")):
    ROOT = os.path.abspath(os.path.dirname(__file__))
else:
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
import exness.strategy_smc_m15 as strat

strat.get_asset_profiles = lambda: {}          # ignore stale per-pair profiles

DATA_DIR = os.path.join(ROOT, "data")
BASE_SPREAD = {"JPY": 1.0, "XAU": 2.0, "DEFAULT": 0.8}   # pips, prime hours (matches your stress test)
SLIP_PIPS = 0.3                                            # extra loss on stop-outs
PENETRATION_PIPS = 0.2                                     # price must trade through the limit
FILL_WINDOW = 8                                            # bars, same as live purge_expired_pending_orders
MAX_HOLD = 48                                              # bars (4h on M5) then close at market
MAX_CONCURRENT, MAX_DAILY = 3, 5

ERA_SPREADS = True      # --flat-spreads turns this off
BE_AT = None            # --be-at 1.0 mirrors the live copilot's break-even shield
MIN_STOP_SPREAD_RATIO = None # --min-stop-spread-ratio 8.0 skips trades where stop < 8x spread
MIN_ATR_PIPS = None          # --min-atr-pips 8.0 skips low-volatility regimes
SPREAD_MULT = 1.0            # --spread-mult 1.3 widens spreads by 30% for friction stress testing


def era_mult(year):
    if not ERA_SPREADS: return 1.0
    return 2.5 if year < 2008 else 1.6 if year < 2012 else 1.25 if year < 2016 else 1.0


def spread_pips(pair, hour, year=2025):
    base = BASE_SPREAD["XAU"] if "XAU" in pair else BASE_SPREAD["JPY"] if "JPY" in pair else BASE_SPREAD["DEFAULT"]
    base = base * era_mult(year) * SPREAD_MULT
    if 21 <= hour < 22: return base * 6
    if 0 <= hour < 6:   return base * 2
    if 7 <= hour <= 16: return base
    return base * 1.3


def load(pair, offset_hours, synthetic=False):
    if synthetic:
        rng = np.random.default_rng(abs(hash(pair)) % 2**32)
        idx = pd.date_range("2022-01-03", "2025-12-31", freq="5min")
        idx = idx[idx.dayofweek < 5]
        ret = rng.normal(0, 0.00018, len(idx)).cumsum()
        close = 1.10 + ret
        open_ = np.r_[close[0], close[:-1]]
        wick = np.abs(rng.normal(0, 0.00012, len(idx)))
        df = pd.DataFrame({"open": open_, "close": close,
                           "high": np.maximum(open_, close) + wick,
                           "low": np.minimum(open_, close) - wick}, index=idx)
        return df
    f = os.path.join(DATA_DIR, f"{pair}_max_m5.parquet")
    df = pd.read_parquet(f)
    df.columns = [c.lower() for c in df.columns]
    df.index = pd.to_datetime(df.index) + pd.Timedelta(hours=offset_hours)   # EST -> UTC
    return df[["open", "high", "low", "close"]]


def get_setups(df, pair, params):
    p = {**strat.PARAMS, **params, "active_pairs": [pair.upper()]}
    return strat.analyze_m15_setup(df, pair, p)


def simulate(df, pair, setups, rr):
    """Return list of trades with entry/exit bar indices and net R after costs."""
    pip = strat.pip_size(pair)
    hi, lo, cl = df["high"].values, df["low"].values, df["close"].values
    hours, n = df.index.hour, len(df)
    trades = []
    for s in setups:
        i = s["bar"]; buy = s["order_type"] == "BUY_LIMIT"
        entry, sl = s["limit_entry"], s["stop_loss"]
        risk = abs(entry - sl)
        if risk <= 0: continue
        sp = spread_pips(pair, hours[i], df.index[i].year) * pip
        if MIN_STOP_SPREAD_RATIO and (risk / sp) < MIN_STOP_SPREAD_RATIO:
            continue
        if MIN_ATR_PIPS and s.get("atr_pips", 0.0) < MIN_ATR_PIPS:
            continue
        tp = entry + rr * risk if buy else entry - rr * risk
        pen = PENETRATION_PIPS * pip
        fill = None
        for j in range(i + 1, min(i + 1 + FILL_WINDOW, n)):
            if buy:
                if lo[j] <= sl: break                       # invalidated before fill
                if lo[j] <= entry - sp - pen: fill = j; break   # ask must trade through
            else:
                if hi[j] >= sl: break
                if hi[j] >= entry + pen: fill = j; break
        if fill is None: continue
        r = None; exit_j = None
        cur_sl = sl; be_done = False
        for j in range(fill, min(fill + MAX_HOLD, n)):
            if buy:
                stop_hit = lo[j] <= cur_sl
                tp_hit = (hi[j] >= tp) if j > fill else False
            else:
                stop_hit = hi[j] >= cur_sl - sp    # ask-based stop for shorts
                tp_hit = (lo[j] <= tp - sp) if j > fill else False
            if stop_hit:                            # SL first if both touched (conservative)
                if be_done:
                    r = (0.3 * pip - 0.5 * SLIP_PIPS * pip) / risk          # stopped at break-even (+0.3 pip lock, half slip)
                else:
                    r = -1.0 - (SLIP_PIPS_R(pip, risk))
                exit_j = j; break
            if tp_hit:
                r = rr; exit_j = j; break           # spread already paid via bid/ask trigger levels
            if BE_AT and not be_done and j > fill:  # arm break-even for the NEXT bar (no same-bar peeking)
                reached = (hi[j] >= entry + BE_AT * risk) if buy else (lo[j] <= entry - BE_AT * risk - sp)
                if reached:
                    be_done = True
                    cur_sl = entry + 0.3 * pip if buy else entry - 0.3 * pip
        if r is None:
            exit_j = min(fill + MAX_HOLD, n) - 1
            move = (cl[exit_j] - entry) if buy else (entry - (cl[exit_j] + sp))   # shorts buy back at ask
            r = move / risk
        trades.append({"pair": pair, "t_entry": df.index[fill], "t_exit": df.index[exit_j],
                       "r": float(r), "arch": s["archetype"]})
    return trades


def SLIP_PIPS_R(pip, risk):
    return (SLIP_PIPS * pip) / risk


def portfolio(trades, risk_pct=0.01, start=500.0):
    """Chronological portfolio with live-style limits. Returns (equity curve stats, executed trades)."""
    trades = sorted(trades, key=lambda t: t["t_entry"])
    open_, per_day, done = [], {}, []
    for t in trades:
        open_ = [o for o in open_ if o["t_exit"] > t["t_entry"]]
        d = t["t_entry"].date()
        if len(open_) >= MAX_CONCURRENT or per_day.get(d, 0) >= MAX_DAILY: continue
        if any(o["pair"] == t["pair"] for o in open_): continue
        open_.append(t); per_day[d] = per_day.get(d, 0) + 1; done.append(t)
    eq, peak, mdd = start, start, 0.0
    for t in sorted(done, key=lambda x: x["t_exit"]):
        eq += eq * risk_pct * t["r"]
        peak = max(peak, eq); mdd = max(mdd, (peak - eq) / peak)
    rs = np.array([t["r"] for t in done]) if done else np.array([0.0])
    gw, gl = rs[rs > 0].sum(), -rs[rs < 0].sum()
    return {"n": len(done), "win%": round((rs > 0).mean() * 100, 1), "expR": round(rs.mean(), 3),
            "netR": round(rs.sum(), 1), "PF": round(gw / gl, 2) if gl > 0 else float("inf"),
            "maxDD%": round(mdd * 100, 1), "end$": round(eq, 2)}, done


GRID = [{"rr": rr, "min_body_ratio": b, "killzones_only": kz}
        for rr, b, kz in itertools.product([1.0, 1.5, 2.0], [0.35, 0.55], [True, False])]


_SETUPS_CACHE = {}

def eval_combo(data, pairs, combo, lo_dt, hi_dt):
    allt = []
    for pair in pairs:
        df = data[pair]
        sub = df[(df.index >= lo_dt) & (df.index < hi_dt)]
        if len(sub) < 500: continue
        p = {k: v for k, v in combo.items() if k != "rr"}
        cache_key = (pair, lo_dt, hi_dt, p.get("min_body_ratio"), p.get("killzones_only"))
        if cache_key not in _SETUPS_CACHE:
            _SETUPS_CACHE[cache_key] = get_setups(sub, pair, p)
        setups = _SETUPS_CACHE[cache_key]
        allt += simulate(sub, pair, setups, combo["rr"])
    return portfolio(allt)[0]


def walkforward(data, pairs, train_years=3, min_trades=150, start_year=None):
    years = sorted({y for df in data.values() for y in df.index.year.unique()})
    test_years = [y for y in years[train_years:] if (start_year is None or y >= start_year)]
    print(f"\nWALK-FORWARD (train {train_years}y -> test next 1y, params chosen on TRAIN only, costs on)")
    print(f"{'test yr':<8}{'chosen params':<48}{'train expR':<11}{'TEST n':<8}{'win%':<7}{'expR':<8}{'PF':<6}{'maxDD%':<7}")
    oos_r = []
    for y in test_years:
        t0, t1 = pd.Timestamp(f"{y - train_years}-01-01"), pd.Timestamp(f"{y}-01-01")
        best, best_score = None, -9
        for c in GRID:
            st = eval_combo(data, pairs, c, t0, t1)
            if st["n"] >= min_trades and st["expR"] > best_score:
                best, best_score = c, st["expR"]
        if best is None:
            print(f"{y:<8}no combo reached {min_trades} trades on train"); continue
        te = eval_combo(data, pairs, best, t1, pd.Timestamp(f"{y + 1}-01-01"))
        oos_r.append(te)
        print(f"{y:<8}{str(best):<48}{best_score:<11}{te['n']:<8}{te['win%']:<7}{te['expR']:<8}{te['PF']:<6}{te['maxDD%']:<7}")
    if oos_r:
        tot = sum(x["n"] for x in oos_r)
        wexp = sum(x["expR"] * x["n"] for x in oos_r) / max(tot, 1)
        print(f"\nOUT-OF-SAMPLE TOTAL: {tot} trades | weighted expectancy {wexp:+.3f} R/trade")
        print("Trust this number, not the in-sample one. If it is <= 0 after costs, there is no edge yet.")


def verify_causal(data, pairs, k):
    """Truncate history at random bars: setups seen at bar i must be identical with and without future data."""
    bad = 0
    for pair in pairs:
        df = data[pair].iloc[-60000:]
        full = {s["datetime"]: s for s in get_setups(df, pair, {})}
        cand = random.sample(list(full.keys()), min(k, len(full))) if full else []
        for ts in cand:
            pos = df.index.get_loc(ts)
            trunc = get_setups(df.iloc[:pos + 1], pair, {})
            m = [s for s in trunc if s["datetime"] == ts]
            same = m and abs(m[0]["limit_entry"] - full[ts]["limit_entry"]) < 1e-9 \
                     and abs(m[0]["stop_loss"] - full[ts]["stop_loss"]) < 1e-9
            if not same: bad += 1
        print(f"{pair}: checked {len(cand)} setups, look-ahead mismatches: {bad}")
    print("CAUSAL OK" if bad == 0 else "LOOK-AHEAD DETECTED — do not trust any backtest built on this function")


def replay(data, pair, d0, d1, combo):
    """Walk the chart bar by bar like a live feed, narrating setups, fills and exits."""
    df = data[pair]; df = df[(df.index >= d0) & (df.index < d1)]
    p = {k: v for k, v in combo.items() if k != "rr"}
    by_bar = {s["datetime"]: s for s in get_setups(df, pair, p)}
    trades = {t["t_entry"]: t for t in simulate(df, pair, list(by_bar.values()), combo["rr"])}
    for ts, row in df.iterrows():
        line = f"{ts:%Y-%m-%d %H:%M}  O{row.open:.5f} H{row.high:.5f} L{row.low:.5f} C{row.close:.5f}"
        if ts in by_bar:
            s = by_bar[ts]; line += f"   << SETUP {s['order_type']} {s['archetype']} @ {s['limit_entry']} SL {s['stop_loss']}"
        if ts in trades:
            line += f"   >> FILLED, will end {trades[ts]['r']:+.2f}R at {trades[ts]['t_exit']:%H:%M}"
        if ts in by_bar or ts in trades or ts.minute == 0:
            print(line)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="+", default=["EURUSD"])
    ap.add_argument("--src-offset-hours", type=int, default=5, help="HistData is EST (UTC-5): add 5h")
    ap.add_argument("--walkforward", action="store_true")
    ap.add_argument("--verify-causal", type=int, default=0)
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--from", dest="d0"); ap.add_argument("--to", dest="d1")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--flat-spreads", action="store_true", help="use modern spreads for every year (optimistic)")
    ap.add_argument("--be-at", type=float, default=None, help="break-even shield trigger in R, e.g. 1.0")
    ap.add_argument("--min-stop-spread-ratio", type=float, default=None, help="skip setups where risk / spread < N")
    ap.add_argument("--min-atr-pips", type=float, default=None, help="skip setups where 20-bar ATR < N pips")
    ap.add_argument("--max-daily", type=int, default=5, help="max fills per day")
    ap.add_argument("--start-year", type=int, default=None, help="first test year in walkforward")
    ap.add_argument("--slip-pips", type=float, default=None, help="extra loss on stop-outs")
    ap.add_argument("--penetration-pips", type=float, default=None, help="limit must trade through by N pips")
    ap.add_argument("--spread-mult", type=float, default=None, help="multiplier on all spreads")
    a = ap.parse_args()
    if a.flat_spreads: ERA_SPREADS = False
    BE_AT = a.be_at
    if a.min_stop_spread_ratio is not None: MIN_STOP_SPREAD_RATIO = a.min_stop_spread_ratio
    if a.min_atr_pips is not None: MIN_ATR_PIPS = a.min_atr_pips
    if a.max_daily is not None: MAX_DAILY = a.max_daily
    if a.slip_pips is not None: SLIP_PIPS = a.slip_pips
    if a.penetration_pips is not None: PENETRATION_PIPS = a.penetration_pips
    if a.spread_mult is not None: SPREAD_MULT = a.spread_mult
    pairs = [p.upper() for p in a.pairs]
    data = {p: load(p, a.src_offset_hours, a.synthetic) for p in pairs}
    if a.verify_causal: verify_causal(data, pairs, a.verify_causal)
    if a.walkforward or a.synthetic: walkforward(data, pairs, start_year=a.start_year)
    if a.replay:
        replay(data, pairs[0], pd.Timestamp(a.d0), pd.Timestamp(a.d1), {"rr": 1.5, "min_body_ratio": 0.35, "killzones_only": True})
