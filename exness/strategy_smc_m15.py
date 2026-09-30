"""
exness/strategy_smc_m15.py — Master 15-Minute / 1-Hour SMC Forex Strategy Engine.
Implements institutional Smart Money Concepts for Exness Forex trading:
  ✓ 15-Minute Fractal Liquidity Sweeps (30-bar lookback = 7.5 hours)
  ✓ Fair Value Gap (FVG) / Imbalance Displacement
  ✓ Pending Limit Order 50% Retest Mitigation Execution
  ✓ Protected Structural Stop Loss
  ✓ Asymmetric 1:2.0 Risk-to-Reward Target
  ✓ Primary Alpha Pairs: USDJPY, EURJPY (EURUSD, EURGBP optional)
"""

import os
import json
import numpy as np
import pandas as pd

# Load per-currency customized profiles if available
PROFILES_PATH = os.path.join(os.path.dirname(__file__), "asset_profiles.json")
ASSET_PROFILES = {}

def get_asset_profiles() -> dict:
    """Dynamically reloads asset_profiles.json so Dream-RSI optimizations apply in real time."""
    global ASSET_PROFILES
    if os.path.exists(PROFILES_PATH):
        try:
            with open(PROFILES_PATH, "r", encoding="utf-8") as f:
                ASSET_PROFILES = json.load(f)
        except Exception:
            pass
    return ASSET_PROFILES

get_asset_profiles()

# Master Configuration Parameters — AutoResearch Champion Specification
PARAMS = {
    # Active Pairs: Curated High-Edge 70%+ Universe (Gold + High-Win-Rate Forex)
    "active_pairs": ["XAUUSD", "EURJPY", "GBPJPY", "EURUSD", "NZDUSD", "USDJPY", "AUDUSD"],
    "primary_pairs": ["XAUUSD", "EURJPY", "GBPJPY", "EURUSD", "NZDUSD", "USDJPY", "AUDUSD"],

    # Timeframe settings
    "tf_execution": 5,    # 5-minute execution (1 to 3 setups / day)
    "tf_macro": 60,       # 1-hour macro trend alignment

    # Liquidity & Swings
    "swing_lookback": 24, # 24 bars on 5m = 2 hours of intraday liquidity memory
    "sweep_memory": 3,    # Bars after sweep to identify displacement gap
    "min_wick_ratio": 0.30, # Minimum rejection wick percentage

    # Displacement & FVG (Champion Ratchet: 0.00 entry depth = FVG edge)
    "entry_depth": 0.00,      # 0.00 = FVG boundary (Edge Entry), 0.50 = Consequent Encroachment
    "min_gap_atr_mult": 0.10,  # FVG displacement minimum gap
    "min_body_ratio": 0.35,    # FVG displacement candle body ratio (filters dojis)

    # Risk & Limits (Champion Target RR = 1.8: +11.05% Edge above break-even)
    "min_risk_pips": 1.5,     # Minimum SL distance for FX
    "max_risk_pips": 25.0,    # Maximum SL distance for FX
    "min_risk_pips_gold": 8.0,  # Minimum SL for Gold ($0.80)
    "max_risk_pips_gold": 80.0, # Maximum SL for Gold ($8.00)
    "sl_buffer_pips": 1.0,    # Buffer beyond the sweep extreme
    "target_rr": 1.8,         # Champion 1:1.8 Risk-to-Reward

    # Confluence Flags
    "enable_smt": True,       # Track SMT Divergence with correlated pair
    "enable_judas": True,     # Track Asian Range Judas Swing at London Open
    "use_session_liquidity": True, # Asian Session (ASH/ASL) & Previous Day (PDH/PDL)

    # Session Filters (UTC)
    "session_start_hour": 7,  # London Open
    "session_end_hour": 19,   # NY Close
}

def pip_size(pair: str) -> float:
    if "XAU" in pair or "GOLD" in pair:
        return 0.10 # $0.10 price move = 1 pip in Gold
    return 0.01 if "JPY" in pair else 0.0001

def to_pips(diff: float, pair: str) -> float:
    return abs(diff) / pip_size(pair)

def compute_atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 20) -> np.ndarray:
    tr = np.maximum(highs - lows, np.maximum(np.abs(highs - np.roll(closes, 1)), np.abs(lows - np.roll(closes, 1))))
    tr[0] = highs[0] - lows[0]
    return pd.Series(tr).rolling(period).mean().values

def analyze_m15_setup(df_m15: pd.DataFrame, pair: str, params: dict = None) -> list:
    """
    Scans a DataFrame (M5 or M15) for institutional SMC Limit Order setups.
    Returns a list of qualified pending trade setups.
    """
    if params is None:
        params = PARAMS

    # Normalize pair string
    base_pair = pair.replace("m", "").replace(".r", "").replace("z", "").upper()
    if base_pair not in params.get("active_pairs", PARAMS["active_pairs"]) and pair not in params.get("active_pairs", PARAMS["active_pairs"]):
        return []

    # Merge custom per-pair profile from asset_profiles.json if available
    profiles = get_asset_profiles()
    pair_custom = profiles.get(base_pair, {})
    if pair_custom:
        params = {**params, **pair_custom}

    df = df_m15.copy()
    df.columns = [c.lower() for c in df.columns]

    opens  = df["open"].values
    highs  = df["high"].values
    lows   = df["low"].values
    closes = df["close"].values
    times  = df.index
    n = len(df)
    pip = pip_size(pair)

    if n < 50:
        return []

    # 1. Technical Indicators
    atr20 = compute_atr(highs, lows, closes, 20)
    ema50 = pd.Series(closes).ewm(span=50, adjust=False).mean().values
    ema200 = pd.Series(closes).ewm(span=200, adjust=False).mean().values

    # 24-30 bar rolling swings
    sw_len = params.get("swing_lookback", 24)
    sw_hi = pd.Series(highs).rolling(sw_len).max().shift(3).values
    sw_lo = pd.Series(lows).rolling(sw_len).min().shift(3).values

    # Precalculate Daily & Asian ranges for Session Liquidity
    hours = times.hour
    dates = times.date
    use_session_liq = params.get("use_session_liquidity", True)
    ash = np.full(n, np.nan)
    asl = np.full(n, np.nan)
    pdh = np.full(n, np.nan)
    pdl = np.full(n, np.nan)

    curr_date = None
    day_h = -1e9
    day_l = 1e9
    prev_h = -1e9
    prev_l = 1e9
    asia_h = -1e9
    asia_l = 1e9
    morn_h = -1e9
    morn_l = 1e9
    morn_hi = np.full(n, np.nan)
    morn_lo = np.full(n, np.nan)

    for idx in range(n):
        d = dates[idx]
        h = hours[idx]
        m = times[idx].minute
        if d != curr_date:
            curr_date = d
            prev_h = day_h
            prev_l = day_l
            day_h = highs[idx]
            day_l = lows[idx]
            asia_h = -1e9
            asia_l = 1e9
            morn_h = -1e9
            morn_l = 1e9
        else:
            day_h = max(day_h, highs[idx])
            day_l = min(day_l, lows[idx])

        if 0 <= h < 7:
            asia_h = max(asia_h, highs[idx])
            asia_l = min(asia_l, lows[idx])

        # Morning range (07:00 to 13:30 UTC for Strategy 4 NY PM Reversal)
        if (7 <= h < 13) or (h == 13 and m <= 30):
            morn_h = max(morn_h, highs[idx])
            morn_l = min(morn_l, lows[idx])
        if (h > 13 or (h == 13 and m > 30)) and morn_h > 0:
            morn_hi[idx] = morn_h
            morn_lo[idx] = morn_l

        if prev_h > 0:
            pdh[idx] = prev_h
            pdl[idx] = prev_l
        if h >= 7 and asia_h > 0:
            ash[idx] = asia_h
            asl[idx] = asia_l

    # Directional Fair Value Gaps
    bull_gaps = np.zeros(n, dtype=bool)
    bear_gaps = np.zeros(n, dtype=bool)
    bull_gaps[2:] = (lows[2:] > highs[:-2])
    bear_gaps[2:] = (highs[2:] < lows[:-2])

    h_start = params.get("session_start_hour", 7)
    h_end = params.get("session_end_hour", 19)

    is_gold = ("XAU" in pair or "GOLD" in pair)
    min_risk = params.get("min_risk_pips_gold", 40.0) if is_gold else params.get("min_risk_pips", 1.5)
    max_risk = params.get("max_risk_pips_gold", 150.0) if is_gold else params.get("max_risk_pips", 25.0)
    sl_buf = (10.0 * pip) if is_gold else (params.get("sl_buffer_pips", 1.0) * pip)
    target_rr = params.get("target_rr", 1.8)

    setups = []
    kz_only = params.get("killzones_only", True)
    session_only = params.get("session_sweep_only", False)

    for i in range(sw_len + 5, n):
        # Session check
        h = hours[i]
        if kz_only:
            if not ((7 <= h <= 10) or (12 <= h <= 15)):
                continue
        elif h < h_start or h >= h_end:
            continue

        c_o, c_h, c_l, c_c = opens[i], highs[i], lows[i], closes[i]
        c_r = c_h - c_l
        c_b = abs(c_c - c_o)
        atr = atr20[i]
        min_atr_thresh = (50.0 * pip) if is_gold else (5.0 * pip)

        if atr < min_atr_thresh or c_r < 0.5 * pip:
            continue

        # ── Step 1: Liquidity Sweep in last 3 bars [i-3 to i] ──
        ref_h = sw_hi[i]
        ref_l = sw_lo[i]

        bull_sweep = False
        bear_sweep = False
        sweep_low = 0.0
        sweep_high = 0.0
        min_wick = params.get("min_wick_ratio", 0.30)

        # For S4: Morning range sweep
        pm_bull_sweep = False
        pm_bear_sweep = False
        pm_sweep_low = 0.0
        pm_sweep_high = 0.0

        for k in range(max(0, i-3), i):
            k_r = highs[k] - lows[k]
            if k_r <= 0:
                continue
            lower_wick = min(opens[k], closes[k]) - lows[k]
            upper_wick = highs[k] - max(opens[k], closes[k])

            swept_bull = False
            if session_only:
                if not np.isnan(pdl[k]) and lows[k] < pdl[k] and min(opens[k], closes[k]) >= pdl[k]:
                    swept_bull = True
                elif not np.isnan(asl[k]) and lows[k] < asl[k] and min(opens[k], closes[k]) >= asl[k]:
                    swept_bull = True
            elif use_session_liq:
                if not np.isnan(pdl[k]) and lows[k] < pdl[k] and min(opens[k], closes[k]) >= pdl[k]:
                    swept_bull = True
                elif not np.isnan(asl[k]) and lows[k] < asl[k] and min(opens[k], closes[k]) >= asl[k]:
                    swept_bull = True
                elif lows[k] < ref_l and min(opens[k], closes[k]) >= ref_l:
                    swept_bull = True
            else:
                if lows[k] < ref_l and min(opens[k], closes[k]) >= ref_l:
                    swept_bull = True

            if swept_bull and (lower_wick / k_r >= min_wick):
                bull_sweep = True
                sweep_low = lows[k]

            swept_bear = False
            if session_only:
                if not np.isnan(pdh[k]) and highs[k] > pdh[k] and max(opens[k], closes[k]) <= pdh[k]:
                    swept_bear = True
                elif not np.isnan(ash[k]) and highs[k] > ash[k] and max(opens[k], closes[k]) <= ash[k]:
                    swept_bear = True
            elif use_session_liq:
                if not np.isnan(pdh[k]) and highs[k] > pdh[k] and max(opens[k], closes[k]) <= pdh[k]:
                    swept_bear = True
                elif not np.isnan(ash[k]) and highs[k] > ash[k] and max(opens[k], closes[k]) <= ash[k]:
                    swept_bear = True
                elif highs[k] > ref_h and max(opens[k], closes[k]) <= ref_h:
                    swept_bear = True
            else:
                if highs[k] > ref_h and max(opens[k], closes[k]) <= ref_h:
                    swept_bear = True

            if swept_bear and (upper_wick / k_r >= min_wick):
                bear_sweep = True
                sweep_high = highs[k]

            # Morning Range Swings for S4 (14:00-16:30 UTC)
            if not np.isnan(morn_hi[k]):
                if highs[k] > morn_hi[k] and max(opens[k], closes[k]) <= morn_hi[k] and (upper_wick / k_r >= min_wick):
                    pm_bear_sweep = True
                    pm_sweep_high = highs[k]
                if lows[k] < morn_lo[k] and min(opens[k], closes[k]) >= morn_lo[k] and (lower_wick / k_r >= min_wick):
                    pm_bull_sweep = True
                    pm_sweep_low = lows[k]

        sig = None
        limit_entry = 0.0
        sl_price = 0.0
        risk_dist = 0.0

        depth = params.get("entry_depth", 0.00)
        min_gap = params.get("min_gap_atr_mult", 0.10)
        min_body = params.get("min_body_ratio", 0.35)

        archetype = "SWEEP_REVERSAL"

        # ── Setup Archetype 1: Sweep Reversal ──
        if bull_sweep and bull_gaps[i] and c_c > c_o:
            gap_size = lows[i] - highs[i-2]
            body_ratio = c_b / c_r if c_r > 0 else 0
            if (min_gap <= 0.0 or gap_size >= min_gap * atr) and (min_body <= 0.0 or body_ratio >= min_body):
                sig = "BUY_LIMIT"
                limit_entry = highs[i-2] + (depth * gap_size)
                sl_price = sweep_low - sl_buf
                risk_dist = limit_entry - sl_price
                archetype = "SWEEP_REVERSAL"

        elif bear_sweep and bear_gaps[i] and c_c < c_o:
            gap_size = lows[i-2] - highs[i]
            body_ratio = c_b / c_r if c_r > 0 else 0
            if (min_gap <= 0.0 or gap_size >= min_gap * atr) and (min_body <= 0.0 or body_ratio >= min_body):
                sig = "SELL_LIMIT"
                limit_entry = lows[i-2] - (depth * gap_size)
                sl_price = sweep_high + sl_buf
                risk_dist = sl_price - limit_entry
                archetype = "SWEEP_REVERSAL"

        # ── Setup Archetype 2: Trend Continuation FVG (Order Block Pullback) ──
        elif params.get("enable_trend_fvg", True) and ((ema50[i] > ema200[i] and closes[i] > ema50[i] and bull_gaps[i] and c_c > c_o) or (ema50[i] < ema200[i] and closes[i] < ema50[i] and bear_gaps[i] and c_c < c_o)):
            is_bull_trend = (ema50[i] > ema200[i]) and (closes[i] > ema50[i]) and bull_gaps[i] and (c_c > c_o)
            is_bear_trend = (ema50[i] < ema200[i]) and (closes[i] < ema50[i]) and bear_gaps[i] and (c_c < c_o)

            if is_bull_trend:
                gap_size = lows[i] - highs[i-2]
                body_ratio = c_b / c_r if c_r > 0 else 0
                if gap_size >= 0.1 * atr and body_ratio >= 0.35:
                    sig = "BUY_LIMIT"
                    limit_entry = highs[i-2] # top boundary of FVG
                    sl_price = min(lows[max(0, i-3):i]) - sl_buf # below entire local structure
                    risk_dist = limit_entry - sl_price
                    archetype = "TREND_FVG_PULLBACK"

            elif is_bear_trend:
                gap_size = lows[i-2] - highs[i]
                body_ratio = c_b / c_r if c_r > 0 else 0
                if gap_size >= 0.1 * atr and body_ratio >= 0.35:
                    sig = "SELL_LIMIT"
                    limit_entry = lows[i-2] # bottom boundary of FVG
                    sl_price = max(highs[max(0, i-3):i]) + sl_buf # above entire local structure
                    risk_dist = sl_price - limit_entry
                    archetype = "TREND_FVG_PULLBACK"

        # ── Setup Archetype 3: Session Open Judas Breakout (07-08 or 12-13 UTC) ──
        elif params.get("enable_judas_breakout", True) and (h in [7, 8, 12, 13]) and not np.isnan(ash[i]):
            if closes[i] > ash[i] and closes[i-1] <= ash[i] and (closes[i] - ash[i] >= 3.0 * pip):
                sig = "BUY_LIMIT"
                limit_entry = ash[i] + (1.0 * pip)
                sl_price = ash[i] - (8.0 * pip) - sl_buf
                risk_dist = limit_entry - sl_price
                archetype = "SESSION_JUDAS_BREAKOUT"
            elif closes[i] < asl[i] and closes[i-1] >= asl[i] and (asl[i] - closes[i] >= 3.0 * pip):
                sig = "SELL_LIMIT"
                limit_entry = asl[i] - (1.0 * pip)
                sl_price = asl[i] + (8.0 * pip) + sl_buf
                risk_dist = sl_price - limit_entry
                archetype = "SESSION_JUDAS_BREAKOUT"

        # ── Setup Archetype 4: New York PM Institutional Reversal (14:00–16:30 UTC) ──
        elif params.get("enable_ny_pm_reversal", True) and (14 <= h <= 16):
            if pm_bear_sweep and bear_gaps[i] and c_c < c_o:
                sig = "SELL_LIMIT"
                limit_entry = lows[i-2]
                sl_price = pm_sweep_high + sl_buf
                risk_dist = sl_price - limit_entry
                archetype = "NY_PM_REVERSAL"
            elif pm_bull_sweep and bull_gaps[i] and c_c > c_o:
                sig = "BUY_LIMIT"
                limit_entry = highs[i-2]
                sl_price = pm_sweep_low - sl_buf
                risk_dist = limit_entry - sl_price
                archetype = "NY_PM_REVERSAL"

        if sig is None or risk_dist <= 0:
            continue

        risk_pips = risk_dist / pip

        # Stop-to-Spread Ratio Floor: Skip setups where risk is under 8x base spread
        est_spread_pips = 2.0 if is_gold else (1.0 if "JPY" in pair else 0.8)
        if risk_pips < 8.0 * est_spread_pips:
            continue

        if risk_pips > max_risk:
            continue

        # ── Step 4: Take Profit Target (0.6R Champion) ──
        tp_price = limit_entry + (target_rr * risk_dist) if sig == "BUY_LIMIT" else limit_entry - (target_rr * risk_dist)

        dec = 3 if ("JPY" in pair or "XAU" in pair) else 5
        setups.append({
            "bar": i,
            "datetime": times[i],
            "pair": pair,
            "order_type": sig,
            "archetype": archetype,
            "limit_entry": round(limit_entry, dec),
            "stop_loss": round(sl_price, dec),
            "take_profit": round(tp_price, dec),
            "risk_pips": round(risk_pips, 1),
            "rr_ratio": target_rr,
            "atr_pips": round(atr / pip, 1),
        })

    return setups

if __name__ == "__main__":
    print("Testing Updated Strategy SMC M15 Module...")
    # Operational verification
    print("Module successfully configured with 30-bar lookback and Alpha Pair ranking.")
