#!/usr/bin/env python
"""
scripts/fill_audit.py — does reality match the simulation?

Joins what the bot INTENDED (data/live_execution_telemetry.jsonl, written by ExecutionRecorder)
with what MT5 ACTUALLY did (deal history), and measures:
  - adverse entry slippage (pips)               [limit orders should never fill worse than the limit]
  - adverse stop-loss slippage (pips)           [simulation assumes 0.3]
  - take-profit shortfall (pips)
  - spread at proposal vs the simulation's spread model
Writes reports/verification/measured_friction.json, which scripts/verify_system.py automatically
re-runs the frozen config under (scenario MEASURED_LIVE). Edge claims need that scenario to stay positive.

    python scripts/fill_audit.py --days 30         # needs MetaTrader5 + a running terminal
    python scripts/fill_audit.py --selftest        # pure-logic test, no MT5 needed
"""
import argparse, json, os, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
from exness.strategy_smc_m15 import pip_size
from exness.position_sizing import base_symbol

OUT = os.path.join(ROOT, "reports", "verification", "measured_friction.json")
TELEMETRY = os.path.join(ROOT, "data", "live_execution_telemetry.jsonl")
MODEL = {"slip_pips": 0.3, "penetration_pips": 0.2}


def model_spread_pips(symbol, hour):
    base = base_symbol(symbol)
    b = 2.0 if "XAU" in base else 1.0 if "JPY" in base else 0.8
    if 21 <= hour < 22: return b * 6
    if 0 <= hour < 6: return b * 2
    if 7 <= hour <= 16: return b
    return b * 1.3


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def compute_friction(intents, deals):
    """
    intents: dicts with order_ticket, symbol, order_type, entry_price, sl_price, tp_price, current_spread_pips, timestamp_utc
    deals:   dicts with order, position_id, symbol, entry ('IN'/'OUT'), price, time (epoch), reason ('SL','TP','CLIENT','EXPERT',...)
    """
    by_order = {d["order"]: d for d in deals if d["entry"] == "IN"}
    exits = {}
    for d in deals:
        if d["entry"] == "OUT":
            exits[d["position_id"]] = d
    rows = []
    for it in intents:
        tk = it.get("order_ticket")
        if not tk or tk not in by_order:
            continue
        din = by_order[tk]
        dout = exits.get(din["position_id"])
        if not dout:
            continue                                            # still open
        sym = it["symbol"]
        pip = pip_size(sym)
        buy = it["order_type"].upper().startswith("BUY")
        sgn = 1.0 if buy else -1.0
        entry, sl, tp = it["entry_price"], it["sl_price"], it["tp_price"]
        entry_adverse = sgn * (din["price"] - entry) / pip      # >0 = filled WORSE than the limit
        risk = abs(entry - sl)
        r_price = sgn * (dout["price"] - din["price"]) / risk if risk > 0 else None
        sl_slip = tp_short = None
        if dout["reason"] == "SL":
            sl_slip = sgn * (sl - dout["price"]) / pip          # >0 = stopped WORSE than the stop price
        elif dout["reason"] == "TP":
            tp_short = sgn * (tp - dout["price"]) / pip         # >0 = got LESS than the target
        hour = datetime.fromtimestamp(din["time"], tz=timezone.utc).hour
        ms = model_spread_pips(sym, hour)
        spread_ratio = (it.get("current_spread_pips") / ms) if it.get("current_spread_pips") and ms else None
        rows.append({"symbol": sym, "reason": dout["reason"], "entry_adverse_pips": entry_adverse, "sl_slip_pips": sl_slip,
                     "tp_shortfall_pips": tp_short, "spread_ratio": spread_ratio, "r_price": r_price})
    n = len(rows)
    sl_n = sum(1 for r in rows if r["sl_slip_pips"] is not None)
    out = {"n_closed": n, "n_sl_exits": sl_n,
           "mean_entry_adverse_pips": mean([r["entry_adverse_pips"] for r in rows]),
           "mean_sl_slip_pips": mean([r["sl_slip_pips"] for r in rows]),
           "mean_tp_shortfall_pips": mean([r["tp_shortfall_pips"] for r in rows]),
           "mean_spread_ratio": mean([r["spread_ratio"] for r in rows]),
           "mean_r_price": mean([r["r_price"] for r in rows]),
           "model": MODEL, "rows": rows}
    if n < 30 or sl_n < 10:
        out["status"] = "INSUFFICIENT_DATA"
        out["note"] = f"need >= 30 closed trades and >= 10 stop-outs; have {n} and {sl_n}. Do not draw conclusions."
        return out
    slip = max(0.0, out["mean_sl_slip_pips"] or 0.0)
    ratio = max(0.5, out["mean_spread_ratio"] or 1.0)
    out.update({"status": "OK", "slip_pips": round(slip, 3), "spread_mult": round(ratio, 3),
                "penetration_pips": MODEL["penetration_pips"]})
    out["verdict"] = ("FRICTION_WITHIN_MODEL" if slip <= MODEL["slip_pips"] and ratio <= 1.0
                      else "FRICTION_WORSE_THAN_MODEL")
    return out


def load_intents(path=TELEMETRY):
    items = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("order_ticket"):
                    items.append(r)
    return items


def load_deals_from_mt5(days):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit("MT5 not initialised: start the terminal and log in first")
    reasons = {getattr(mt5, n): n.replace("DEAL_REASON_", "") for n in dir(mt5) if n.startswith("DEAL_REASON_")}
    raw = mt5.history_deals_get(datetime.now(timezone.utc) - timedelta(days=days), datetime.now(timezone.utc) + timedelta(days=1))
    mt5.shutdown()
    deals = []
    for d in raw or []:
        if d.type not in (0, 1):                                  # buy / sell only
            continue
        deals.append({"order": d.order, "position_id": d.position_id, "symbol": d.symbol,
                      "entry": "IN" if d.entry == 0 else "OUT" if d.entry in (1, 3) else "OTHER",
                      "price": d.price, "time": d.time, "reason": reasons.get(d.reason, str(d.reason))})
    return deals


def selftest():
    now = datetime(2026, 9, 22, 14, 0, tzinfo=timezone.utc).timestamp()
    intents, deals = [], []
    for k in range(40):
        tk = 1000 + k
        buy = k % 2 == 0
        entry, sl, tp = (1.1000, 1.0990, 1.1010) if buy else (1.1000, 1.1010, 1.0990)
        intents.append({"order_ticket": tk, "symbol": "EURUSDm", "order_type": "BUY_LIMIT" if buy else "SELL_LIMIT",
                        "entry_price": entry, "sl_price": sl, "tp_price": tp, "current_spread_pips": 1.0})
        stop_out = k % 3 == 0
        deals.append({"order": tk, "position_id": tk, "symbol": "EURUSDm", "entry": "IN", "price": entry, "time": now, "reason": "EXPERT"})
        if stop_out:   # 0.5 pip worse than stop
            px = sl - 0.00005 if buy else sl + 0.00005
            deals.append({"order": tk + 9000, "position_id": tk, "symbol": "EURUSDm", "entry": "OUT", "price": px, "time": now + 60, "reason": "SL"})
        else:
            deals.append({"order": tk + 9000, "position_id": tk, "symbol": "EURUSDm", "entry": "OUT", "price": tp, "time": now + 60, "reason": "TP"})
    res = compute_friction(intents, deals)
    ok = (res["status"] == "OK" and abs(res["mean_sl_slip_pips"] - 0.5) < 1e-6 and abs(res["mean_tp_shortfall_pips"]) < 1e-9
          and res["verdict"] == "FRICTION_WORSE_THAN_MODEL" and abs(res["mean_spread_ratio"] - 1.25) < 1e-9)
    return ok, res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        ok, res = selftest()
        print("SELFTEST", "PASS" if ok else "FAIL", {k: v for k, v in res.items() if k != "rows"})
        sys.exit(0 if ok else 1)
    res = compute_friction(load_intents(), load_deals_from_mt5(a.days))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    slim = {k: v for k, v in res.items() if k != "rows"}
    slim["generated_utc"] = datetime.now(timezone.utc).isoformat()
    json.dump(slim, open(OUT, "w"), indent=2)
    print(json.dumps(slim, indent=2))
    if res["status"] == "OK":
        print("\nNext: python scripts/verify_system.py --full   (re-runs the frozen config under MEASURED_LIVE friction)")
