#!/usr/bin/env python
"""
scripts/verify_system.py — ONE command that produces machine-generated evidence.

    python scripts/verify_system.py --quick        # ~minutes, synthetic data, tests the tests
    python scripts/verify_system.py --full         # + real data: timezone, causality, frozen-config claim gate
    python scripts/verify_system.py --final-exam   # touches the locked holdout (after research_end). ONCE per config hash.

Output: reports/verification/latest.json + latest.md (+ timestamped copies) and an append-only ledger.jsonl.
Exit code is non-zero if any check FAILS. SKIPPED is never reported as PASSED.

Rule for humans and AI agents: a number may only be quoted if it is in latest.md / latest.json
(or in a command output from this session). See AGENTS.md.
"""
import argparse, hashlib, json, math, os, subprocess, sys, time
from datetime import datetime, timezone
from statistics import NormalDist
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import honest_replay as hr                      # the execution/walk-forward engine
from exness.position_sizing import pip_value_per_lot_usd, lots_for_risk

OUT_DIR = os.path.join(ROOT, "reports", "verification")
LEDGER = os.path.join(OUT_DIR, "ledger.jsonl")
LOCK = os.path.join(OUT_DIR, "holdout_lock.json")
MEASURED = os.path.join(OUT_DIR, "measured_friction.json")      # written by scripts/fill_audit.py
os.makedirs(OUT_DIR, exist_ok=True)

DEFAULTS = dict(SPREAD_MULT=1.0, SLIP_PIPS=0.3, PENETRATION_PIPS=0.2, MIN_STOP_SPREAD_RATIO=None,
                MIN_ATR_PIPS=None, BE_AT=None, MAX_DAILY=5, ERA_SPREADS=True)


# ----------------------------------------------------------------------------- utilities
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def git_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


def set_friction(**kw):
    """Set harness globals; anything not given resets to DEFAULTS so scenarios never leak into each other."""
    cfg = {**DEFAULTS, **kw}
    for k, v in cfg.items():
        setattr(hr, k, v)


def result(name, status, detail, **numbers):
    return {"name": name, "status": status, "detail": detail, "numbers": numbers}


def synth(seed, start="2022-01-03", end="2023-03-31", profile=True, sub=12, bar_sigma=0.00042):
    """
    Deterministic M5 bars built from a genuine intra-bar random-walk path (martingale by construction),
    so touching a level has zero expected drift afterwards. (Attaching random wicks to bars would create
    fake mean-reversion and bias every null test.)
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end, freq="5min")
    idx = idx[idx.dayofweek < 5]
    prof = np.ones(24)
    if profile:
        prof[[7, 8, 12, 13, 14, 15]] = 2.4
        prof[0:6] = 0.5
    sig = bar_sigma * prof[idx.hour] / math.sqrt(sub)
    steps = rng.normal(0, 1, (len(idx), sub)) * sig[:, None]
    path = 1.10 + np.cumsum(steps.reshape(-1)).reshape(len(idx), sub)
    open_ = np.r_[1.10, path[:-1, -1]]
    high = np.maximum(open_, path.max(axis=1))
    low = np.minimum(open_, path.min(axis=1))
    return pd.DataFrame({"open": open_, "close": path[:, -1], "high": high, "low": low}, index=idx)


def block_stats(rs, days, seed=0, boots=2000):
    """Mean R with day-block bootstrap CI (trades within a day are not independent)."""
    rs = np.asarray(rs, float)
    n = len(rs)
    if n < 30:
        return {"n": n, "mean": float(rs.mean()) if n else 0.0, "se": None, "t": None,
                "ci_lo": None, "ci_hi": None, "win_pct": None, "pf": None, "n_for_80pct_power": None}
    mean = rs.mean()
    sd = rs.std(ddof=1)
    se = sd / math.sqrt(n)
    g = pd.DataFrame({"d": list(days), "r": rs}).groupby("d")["r"].agg(["sum", "count"])
    sums, cnts = g["sum"].values, g["count"].values
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(sums), size=(boots, len(sums)))
    boot = sums[idx].sum(1) / cnts[idx].sum(1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    gw, gl = rs[rs > 0].sum(), -rs[rs < 0].sum()
    need = int((2.8 * sd / abs(mean)) ** 2) if abs(mean) > 1e-9 else None
    return {"n": n, "mean": round(float(mean), 4), "se": round(float(se), 4), "t": round(float(mean / se), 2),
            "ci_lo": round(float(lo), 4), "ci_hi": round(float(hi), 4),
            "win_pct": round(float((rs > 0).mean() * 100), 1), "pf": round(float(gw / gl), 2) if gl > 0 else None,
            "n_for_80pct_power": need}


# ----------------------------------------------------------------------------- checks
def check_sizing():
    fails = []
    rates = {"USDJPY": 150.0, "USDCAD": 1.36, "USDCHF": 0.88, "GBPUSD": 1.27, "EURUSD": 1.08,
             "AUDUSD": 0.66, "NZDUSD": 0.60}
    cases = [("EURUSD", 100000, 0.0001, 10.0), ("GBPUSDm", 100000, 0.0001, 10.0),
             ("AUDUSD", 100000, 0.0001, 10.0), ("USDJPY", 100000, 0.01, 1000 / 150.0),
             ("EURJPY", 100000, 0.01, 1000 / 150.0), ("GBPJPYm", 100000, 0.01, 1000 / 150.0),
             ("USDCAD", 100000, 0.0001, 10 / 1.36), ("USDCHF", 100000, 0.0001, 10 / 0.88),
             ("EURGBP", 100000, 0.0001, 10 * 1.27), ("XAUUSD", 100, 0.1, 10.0)]
    for sym, cs, pip, expect in cases:
        got = pip_value_per_lot_usd(sym, cs, pip, rates)
        if abs(got - expect) > 1e-6:
            fails.append(f"{sym}: got {got:.4f} expected {expect:.4f}")
    tv = pip_value_per_lot_usd("EURJPY", 100000, 0.01, rates, tick_value=0.6667, tick_size=0.001)
    if abs(tv - 6.667) > 0.01:
        fails.append(f"tick_value path wrong: {tv}")
    # property test: lots>0 must never exceed 1.25x the budget, and never be below vol_min
    rng = np.random.default_rng(7)
    worst = 0.0
    for _ in range(3000):
        eq = float(rng.uniform(100, 20000)); rp = float(rng.uniform(0.001, 0.02))
        pips = float(rng.uniform(2, 120)); pv = float(rng.uniform(4, 14))
        lots, info = lots_for_risk(eq, rp, pips, pv, 0.01, 100.0, 0.01)
        if lots > 0:
            ratio = lots * pips * pv / (eq * rp)
            worst = max(worst, ratio)
            if ratio > 1.25 + 1e-9 or lots < 0.01 - 1e-12:
                fails.append(f"risk ratio {ratio:.3f} lots {lots}")
                break
    lots, info = lots_for_risk(500, 0.005, 100, 10.0, 0.01, 100, 0.01)       # gold-like wide stop on $500
    if lots != 0.0 or info["status"] != "REJECT_MIN_LOT_EXCEEDS_BUDGET":
        fails.append(f"wide-stop min-lot refusal not triggered: {lots} {info}")
    return result("sizing_unit_and_property", "FAIL" if fails else "PASS",
                  "; ".join(fails[:4]) or "pip values match closed-form for 10 symbols; 3000 random cases never exceeded 1.25x budget; min-lot refusal works",
                  worst_risk_ratio=round(worst, 3))


def causality_mismatches(get_setups_fn, df, pair, k, params, seed=0, ctx=3000, fut=3000):
    """Adding FUTURE bars must not change any setup at or before the cut. Compare windows with/without future."""
    rng = np.random.default_rng(seed)
    n = len(df)
    hi_ok = n - fut - 1
    if hi_ok <= ctx + 10:
        return None, 0
    cuts = rng.integers(ctx, hi_ok, size=k)
    bad = 0
    for pos in cuts:
        a = df.iloc[pos - ctx: pos + 1]
        b = df.iloc[pos - ctx: pos + 1 + fut]
        A = {(s["datetime"], s["order_type"], round(s["limit_entry"], 8), round(s["stop_loss"], 8))
             for s in get_setups_fn(a, pair, params)}
        B = {(s["datetime"], s["order_type"], round(s["limit_entry"], 8), round(s["stop_loss"], 8))
             for s in get_setups_fn(b, pair, params) if s["datetime"] <= a.index[-1]}
        if A != B:
            bad += 1
    return bad, len(cuts)


def leaky_get_setups(df, pair, params):
    """DELIBERATELY BROKEN strategy (peeks 10 bars ahead). Used to prove the detectors detect."""
    out = []
    cl = df["close"].values
    for s in hr.get_setups(df, pair, params):
        i = s["bar"]
        if i + 10 >= len(df):
            continue
        up = cl[i + 10] > cl[i]
        if (s["order_type"] == "BUY_LIMIT") == up:
            out.append(s)
    return out


def check_causality(df, pair, label, k):
    p = {"min_body_ratio": 0.35, "killzones_only": True}
    bad, checked = causality_mismatches(hr.get_setups, df, pair, k, p)
    if bad is None:
        return result(f"causality_{label}", "FAIL" if label == "synthetic" else "SKIP", "not enough bars")
    return result(f"causality_{label}", "PASS" if bad == 0 else "FAIL",
                  f"{checked} random cut points; setups changed when future bars were added in {bad} cases",
                  checked=checked, mismatches=bad)


def check_causality_detector(df):
    p = {"min_body_ratio": 0.35, "killzones_only": True}
    bad, checked = causality_mismatches(leaky_get_setups, df, "EURUSD", 60, p)
    ok = bad is not None and bad > 0
    return result("selftest_causality_detector_catches_leak", "PASS" if ok else "FAIL",
                  f"deliberately leaky strategy flagged in {bad}/{checked} cuts (must be > 0)", flagged=bad, checked=checked)


def null_edge(get_setups_fn, seeds=(1, 2, 3), rr=1.0):
    """Random-walk data has no edge. With ZERO costs the mean R must not be significantly positive."""
    set_friction(SPREAD_MULT=0.0, SLIP_PIPS=0.0, PENETRATION_PIPS=0.0)
    rs = []
    for sd in seeds:
        df = synth(sd, end="2022-12-31", profile=False)
        setups = get_setups_fn(df, "EURUSD", {"min_body_ratio": 0.35, "killzones_only": True})
        rs += [t["r"] for t in hr.simulate(df, "EURUSD", setups, rr)]
    set_friction()
    rs = np.array(rs)
    if len(rs) < 200:
        return None, len(rs), 0.0
    t = rs.mean() / (rs.std(ddof=1) / math.sqrt(len(rs)))
    return float(t), len(rs), float(rs.mean())


def check_null_edge():
    t, n, m = null_edge(hr.get_setups)
    if t is None:
        return result("null_edge_random_walk", "FAIL", f"VACUOUS: engine produced only {n} trades on synthetic data, test is meaningless")
    se = abs(m / t) if t else float("nan")
    upper, lower = m + 1.96 * se, m - 1.96 * se
    ok = upper <= 0.05
    return result("null_edge_random_walk", "PASS" if ok else "FAIL",
                  f"zero-cost martingale random walk, {n} trades: mean {m:+.4f}R, 95% interval [{lower:+.3f}, {upper:+.3f}]. "
                  f"PASS needs upper bound <= +0.05R (engine may not manufacture edge). "
                  f"Lower bound {lower:+.3f} shows how conservative the engine is.",
                  n=n, mean_r=round(m, 4), ci_lo=round(lower, 4), ci_hi=round(upper, 4))


def check_null_detector():
    t, n, m = null_edge(leaky_get_setups)
    ok = t is not None and t > 3.0
    return result("selftest_null_detector_catches_leak", "PASS" if ok else "FAIL",
                  f"leaky strategy on random data: t={t if t is None else round(t, 2)} over {n} trades (must exceed 3.0)",
                  t=None if t is None else round(t, 2), n=n)


def check_cost_monotonic():
    df = synth(11, end="2022-12-31", profile=False)
    setups = hr.get_setups(df, "EURUSD", {"min_body_ratio": 0.35, "killzones_only": True})
    levels = [dict(SPREAD_MULT=0.0, SLIP_PIPS=0.0, PENETRATION_PIPS=0.0),
              dict(SPREAD_MULT=1.0, SLIP_PIPS=0.3, PENETRATION_PIPS=0.2),
              dict(SPREAD_MULT=2.0, SLIP_PIPS=0.6, PENETRATION_PIPS=0.4)]
    means = []
    for lv in levels:
        set_friction(**lv)
        rs = [t["r"] for t in hr.simulate(df, "EURUSD", setups, 1.0)]
        means.append(float(np.mean(rs)) if rs else 0.0)
    set_friction()
    ok = means[0] >= means[1] - 0.02 and means[1] >= means[2] - 0.02
    if len(setups) < 100:
        return result("cost_monotonicity", "FAIL", f"VACUOUS: only {len(setups)} setups generated")
    return result("cost_monotonicity", "PASS" if ok else "FAIL",
                  f"mean R at cost levels 0/1x/2x = {means[0]:+.3f} / {means[1]:+.3f} / {means[2]:+.3f} (must not rise as costs rise)",
                  zero=round(means[0], 4), base=round(means[1], 4), double=round(means[2], 4))


def tz_ratio(df):
    d = df[df.index.year >= 2015] if (df.index.year >= 2015).any() else df
    rng = (d["high"] - d["low"]).groupby(d.index.hour).mean()
    return float(rng.loc[[7, 8]].mean() / rng.loc[[2, 3]].mean())


def check_timezone_real(data):
    out = {}
    for p in ("EURUSD", "GBPUSD"):
        if p in data:
            out[p] = tz_ratio(data[p])
    if not out:
        return result("timezone_alignment_real_data", "SKIP", "no EURUSD/GBPUSD data loaded")
    ok = all(v >= 1.4 for v in out.values())
    return result("timezone_alignment_real_data", "PASS" if ok else "FAIL",
                  "volatility at 07-08 UTC vs 02-03 UTC: " + ", ".join(f"{k} x{v:.2f}" for k, v in out.items())
                  + " (must be >= 1.4; if ~1 the clock is mislabelled and killzones are misaligned)",
                  **{k: round(v, 2) for k, v in out.items()})


def check_fill_audit_selftest():
    import fill_audit
    ok, res = fill_audit.selftest()
    return result("selftest_fill_audit_math", "PASS" if ok else "FAIL",
                  f"synthetic fills with a known 0.5 pip stop slippage measured as {res.get('mean_sl_slip_pips')} pips; verdict {res.get('verdict')}",
                  measured_sl_slip=res.get("mean_sl_slip_pips"))


def check_timezone_detector():
    good = synth(5, end="2022-06-30", profile=True)
    bad = good.copy()
    bad.index = bad.index - pd.Timedelta(hours=5)         # mislabel clock by 5h
    rg, rb = tz_ratio(good), tz_ratio(bad)
    ok = rg >= 1.4 and rb < 1.4
    return result("selftest_timezone_detector", "PASS" if ok else "FAIL",
                  f"aligned clock ratio {rg:.2f} (>=1.4), 5h-shifted ratio {rb:.2f} (<1.4)",
                  aligned=round(rg, 2), shifted=round(rb, 2))


# ----------------------------------------------------------------------------- claim gate (real data)
def load_cfg(path):
    with open(path) as f:
        return json.load(f)


def config_hash(cfg):
    core = {k: v for k, v in cfg.items() if not k.startswith("_")}
    blob = json.dumps(core, sort_keys=True) + sha256_file(os.path.join(ROOT, "exness", "strategy_smc_m15.py")) \
        + sha256_file(os.path.join(HERE, "honest_replay.py"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def ledger_variants(cur_hash, cfg):
    seen = {cur_hash}
    if os.path.exists(LEDGER):
        with open(LEDGER) as f:
            for line in f:
                try:
                    seen.add(json.loads(line)["config_hash"])
                except Exception:
                    pass
    return len(seen) + int(cfg.get("prior_variants_tried", 0))


def run_scenario(data, setups_by_pair, cfg, lo, hi, scenario):
    set_friction(MIN_STOP_SPREAD_RATIO=cfg.get("min_stop_spread_ratio"), MIN_ATR_PIPS=cfg.get("min_atr_pips"),
                 BE_AT=cfg.get("be_at"), **scenario)
    trades = []
    for pair, (df, setups) in setups_by_pair.items():
        trades += hr.simulate(df, pair, setups, cfg["rr"])
    _, done = hr.portfolio(trades)
    set_friction()
    return done


def claim_gate(cfg, data, window_lo, window_hi, tag):
    cfg_hash = config_hash(cfg)
    setups_by_pair = {}
    for pair in cfg["pairs"]:
        if pair not in data:
            continue
        df = data[pair]
        df = df[(df.index >= pd.Timestamp(window_lo)) & (df.index <= pd.Timestamp(window_hi))]
        if len(df) < 5000:
            continue
        set_friction()
        setups_by_pair[pair] = (df, hr.get_setups(df, pair, {"min_body_ratio": cfg["min_body_ratio"],
                                                               "killzones_only": cfg["killzones_only"]}))
    if not setups_by_pair:
        return result(f"claim_gate_{tag}", "SKIP", "no real data in window"), None
    scenarios = {"BASE": dict(),
                 "MILD_STRESS": dict(SPREAD_MULT=1.15, SLIP_PIPS=0.45, PENETRATION_PIPS=0.3),
                 "SEVERE_STRESS": dict(SPREAD_MULT=1.3, SLIP_PIPS=0.6, PENETRATION_PIPS=0.5)}
    if os.path.exists(MEASURED):
        m = json.load(open(MEASURED))
        if m.get("status") == "OK":
            scenarios["MEASURED_LIVE"] = dict(SPREAD_MULT=m["spread_mult"], SLIP_PIPS=m["slip_pips"],
                                              PENETRATION_PIPS=m.get("penetration_pips", 0.2))
    blocks, base_done = {}, None
    for name, sc in scenarios.items():
        done = run_scenario(data, setups_by_pair, cfg, window_lo, window_hi, sc)
        if name == "BASE":
            base_done = done
        blocks[name] = block_stats([t["r"] for t in done], [t["t_entry"].date() for t in done])
    b = blocks["BASE"]
    if b["se"] is None:
        return result(f"claim_gate_{tag}", "SKIP", f"only {b['n']} trades"), None

    rows = pd.DataFrame([{"pair": t["pair"], "arch": t["arch"], "year": t["t_entry"].year, "r": t["r"]} for t in base_done])
    by = lambda col: {str(k): {"n": int(len(g)), "mean_r": round(float(g["r"].mean()), 4), "net_r": round(float(g["r"].sum()), 1)}
                      for k, g in rows.groupby(col)}
    net = rows["r"].sum()
    top_pair_share = float(rows.groupby("pair")["r"].sum().max() / net) if net > 0 else None
    k = ledger_variants(cfg_hash, cfg)
    bonf_z = NormalDist().inv_cdf(1 - 0.025 / k)

    # verdict
    reasons, verdict = [], "EDGE_SUPPORTED"
    if b["n"] < cfg.get("min_trades_for_claim", 1000):
        verdict = "INSUFFICIENT_TRADES"; reasons.append(f"n={b['n']} < {cfg.get('min_trades_for_claim', 1000)}")
    elif not (b["ci_lo"] > 0):
        verdict = "NO_EDGE"; reasons.append(f"base 95% CI [{b['ci_lo']}, {b['ci_hi']}] includes <= 0")
    elif b["t"] < bonf_z:
        verdict = "NOT_SIGNIFICANT_AFTER_MULTIPLE_TESTING"; reasons.append(f"t={b['t']} < Bonferroni z={bonf_z:.2f} for {k} variants tried")
    elif blocks["MILD_STRESS"]["mean"] <= 0:
        verdict = "EDGE_FRAGILE"; reasons.append(f"mild-stress mean {blocks['MILD_STRESS']['mean']:+.4f}R <= 0")
    elif "MEASURED_LIVE" in blocks and blocks["MEASURED_LIVE"]["mean"] <= 0:
        verdict = "EDGE_FAILS_MEASURED_LIVE_FRICTION"; reasons.append(f"measured-live mean {blocks['MEASURED_LIVE']['mean']:+.4f}R <= 0")
    elif top_pair_share is not None and top_pair_share > 0.5:
        verdict = "EDGE_CONCENTRATED"; reasons.append(f"one pair supplies {top_pair_share:.0%} of net R")
    if verdict == "EDGE_SUPPORTED" and "MEASURED_LIVE" not in blocks:
        verdict = "EDGE_SUPPORTED_IN_SIMULATION_ONLY"; reasons.append("no measured live friction yet (run scripts/fill_audit.py after >= 30 closed demo trades)")

    detail = f"[{tag}] {window_lo}..{window_hi} config {cfg_hash}: verdict {verdict}. " + "; ".join(reasons)
    res = result(f"claim_gate_{tag}", "PASS" if verdict.startswith("EDGE_SUPPORTED") else "FAIL", detail,
                 verdict=verdict, config_hash=cfg_hash, variants_counted=k, bonferroni_z=round(bonf_z, 2),
                 scenarios=blocks, by_pair=by("pair"), by_year=by("year"), by_archetype=by("arch"),
                 top_pair_share=None if top_pair_share is None else round(top_pair_share, 3))
    with open(LEDGER, "a") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "commit": git_commit(), "config_hash": cfg_hash,
                            "tag": tag, "window": [window_lo, window_hi], "verdict": verdict,
                            "n": b["n"], "mean": b["mean"], "t": b["t"]}) + "\n")
    return res, cfg_hash


def final_exam(cfg, data):
    cfg_hash = config_hash(cfg)
    lock = json.load(open(LOCK)) if os.path.exists(LOCK) else {}
    if cfg_hash in lock:
        r = lock[cfg_hash]
        return result("final_exam_holdout", "FAIL" if not str(r["verdict"]).startswith("EDGE_SUPPORTED") else "PASS",
                      f"HOLDOUT ALREADY USED for config {cfg_hash}; stored result reused (re-running would be peeking). verdict {r['verdict']}",
                      stored=r)
    start = (pd.Timestamp(cfg["research_end"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    res, _ = claim_gate(cfg, data, start, "2100-01-01", "HOLDOUT")
    if res["status"] != "SKIP":
        lock[cfg_hash] = {"ts": datetime.now(timezone.utc).isoformat(), "verdict": res["numbers"]["verdict"],
                          "scenarios": res["numbers"]["scenarios"]}
        json.dump(lock, open(LOCK, "w"), indent=2)
    return res


# ----------------------------------------------------------------------------- report
def write_report(results, args, cfg, started):
    status = "ALL_CHECKS_PASSED" if all(r["status"] in ("PASS", "SKIP") for r in results) and \
        not any(r["name"].startswith("claim_gate") and r["status"] == "FAIL" for r in results) else "FAILED"
    meta = {"generated_utc": datetime.now(timezone.utc).isoformat(), "commit": git_commit(),
            "args": vars(args), "runtime_s": round(time.time() - started, 1), "overall": status,
            "strategy_sha": sha256_file(os.path.join(ROOT, "exness", "strategy_smc_m15.py"))[:12],
            "harness_sha": sha256_file(os.path.join(HERE, "honest_replay.py"))[:12]}
    body = {"meta": meta, "results": results}
    meta["report_sha256"] = hashlib.sha256(json.dumps(results, sort_keys=True, default=str).encode()).hexdigest()[:16]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    for name in (f"{stamp}_{meta['commit']}.json", "latest.json"):
        json.dump(body, open(os.path.join(OUT_DIR, name), "w"), indent=2, default=str)

    L = [f"# Verification report — {meta['overall']}",
         f"commit `{meta['commit']}` · generated {meta['generated_utc']} · runtime {meta['runtime_s']}s · report hash `{meta['report_sha256']}`", "",
         "| check | status | detail |", "|---|---|---|"]
    for r in results:
        L.append(f"| {r['name']} | **{r['status']}** | {r['detail']} |")
    allowed = []
    for r in results:
        n = r["numbers"]
        if r["name"].startswith("claim_gate") and "scenarios" in n:
            b, m, s = n["scenarios"]["BASE"], n["scenarios"]["MILD_STRESS"], n["scenarios"]["SEVERE_STRESS"]
            allowed.append(f"Frozen config `{n['config_hash']}` ({r['name']}): n={b['n']}, mean {b['mean']:+.4f}R, 95% CI [{b['ci_lo']:+.4f}, {b['ci_hi']:+.4f}], t={b['t']}; "
                           f"mild stress {m['mean']:+.4f}R; severe stress {s['mean']:+.4f}R; {n['variants_counted']} variants counted; verdict **{n['verdict']}**.")
            if "MEASURED_LIVE" in n["scenarios"]:
                ml = n["scenarios"]["MEASURED_LIVE"]
                allowed.append(f"Under friction measured from real demo fills: mean {ml['mean']:+.4f}R (n={ml['n']}).")
            allowed.append(f"Net R by pair: {json.dumps(n['by_pair'])}")
            allowed.append(f"Net R by archetype: {json.dumps(n['by_archetype'])}")
    L += ["", "## Allowed claims (copy only from here)"] + [f"- {a}" for a in allowed] if allowed else \
        ["", "## Allowed claims", "- None about real-data edge: no claim gate ran. Say so."]
    skipped = [r["name"] for r in results if r["status"] == "SKIP"]
    L += ["", "## NOT verified in this run"] + ([f"- {s}" for s in skipped] or ["- (nothing skipped)"])
    L += ["", "Anything not listed above is unverified. Do not state it as fact."]
    text = "\n".join(L)
    for name in (f"{stamp}_{meta['commit']}.md", "latest.md"):
        open(os.path.join(OUT_DIR, name), "w", encoding="utf-8").write(text)
    return status, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--final-exam", action="store_true")
    ap.add_argument("--config", default=os.path.join(ROOT, "config", "frozen_config.json"))
    ap.add_argument("--pairs", nargs="*", default=None)
    a = ap.parse_args()
    if not (a.quick or a.full or a.final_exam):
        a.quick = True
    started = time.time()
    cfg = load_cfg(a.config)
    if a.pairs:
        cfg["pairs"] = [p.upper() for p in a.pairs]
    results = []

    # ---- always: tests of the tests
    results.append(check_sizing())
    results.append(check_timezone_detector())
    results.append(check_fill_audit_selftest())
    sdf = synth(21, end="2022-12-31", profile=False)
    results.append(check_causality(sdf, "EURUSD", "synthetic", 20))
    results.append(check_causality_detector(sdf))
    results.append(check_null_edge())
    results.append(check_null_detector())
    results.append(check_cost_monotonic())

    # ---- real data checks
    if a.full or a.final_exam:
        data = {}
        for p in cfg["pairs"]:
            f = os.path.join(hr.DATA_DIR, f"{p}_max_m5.parquet")
            if os.path.exists(f):
                data[p] = hr.load(p, cfg["src_offset_hours"])
        if not data:
            results.append(result("real_data_loaded", "SKIP", f"no parquet files in {hr.DATA_DIR}"))
        else:
            results.append(check_timezone_real(data))
            for p in list(data)[:2]:
                results.append(check_causality(data[p], p, f"real_{p}", 40))
            if a.full:
                res, _ = claim_gate(cfg, data, "2000-01-01", cfg["research_end"], "RESEARCH")
                results.append(res)
            if a.final_exam:
                results.append(final_exam(cfg, data))

    status, text = write_report(results, a, cfg, started)
    print(text)
    sys.exit(0 if status == "ALL_CHECKS_PASSED" else 1)


if __name__ == "__main__":
    main()
