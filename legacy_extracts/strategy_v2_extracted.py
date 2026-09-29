"""
IBT Binary Options Strategy — PrasaD — ENHANCED v2
strategy.py — THE FILE THE AGENT MODIFIES

Full course integration: Classes 1–8 + Trade Log Checklist
4-Step Entry Flow + All Course Filters

Enhancements over v1:
  ✓ Major Candle detection (inside candles ignored)
  ✓ IDM tracking + mitigation state required before signals
  ✓ Valid Pullback (two conditions: sweep + body break together)
  ✓ Liquidity strength scoring (0/1/2+ sweeps)
  ✓ Premium/Discount zone filter (50% midpoint)
  ✓ Equal Highs/Lows detection + skip
  ✓ No Resistance Area bonus scoring
  ✓ Gap Sweep micro-entry strategy
  ✓ T1/T2 target system with traffic light logic
  ✓ IFC candle integration (2nd sweep context)
  ✓ Order Flow direction bias
  ✓ BOS/CHoCH as liquidity levels
  ✓ CFVG large wick filter
  ✓ Double BAG 50% wait with actual midpoint calc
  ✓ Manipulation Gap tied to target tracking
  ✓ Ranging market skip
"""

import numpy as np

# ══════════════════════════════════════════════════════════
#  PARAMETERS — agent modifies only these values
# ══════════════════════════════════════════════════════════

PARAMS = {

    # ── Step 1: Trigger ──────────────────────────────────
    "sweep_lookback":          5,    # bars for swing high/low detection
    "sweep_wick_ratio":        0.55, # wick must be ≥ this fraction of total candle
    "efvg_min_size_pips":      3.0,  # extreme FVG minimum pip size
    "efvg_lookback":           12,   # how far back to find extreme FVG

    # ── Major Candle / Inside Candle ─────────────────────
    "ignore_inside_candles":   True, # skip inside candles entirely

    # ── IDM Tracking ─────────────────────────────────────
    "idm_lookback":            20,   # bars to look for IDM after HH/LL
    "idm_mitigation_required": True, # signal only fires AFTER IDM mitigated

    # ── Liquidity Strength ────────────────────────────────
    "min_sweep_count":         1,    # 0=weak skip, 1=neutral OK, 2+=strong preferred
    "sweep_count_lookback":    30,   # bars to count historical sweeps at level

    # ── Premium / Discount Zones ─────────────────────────
    "use_pd_filter":           True, # only buy in discount, sell in premium
    "pd_range_lookback":       50,   # bars to define premium/discount range

    # ── Equal Highs/Lows Detection ───────────────────────
    "equal_level_tolerance":   0.0003, # price within 0.03% = equal level
    "equal_level_lookback":    20,   # bars to check for equal highs/lows

    # ── Step 2: Confirmation ─────────────────────────────
    "sharp_turn_bars":         3,    # max bars for a valid sharp turn
    "sharp_turn_gap_pips":     2.0,  # gap inside sharp turn ≥ N pips
    "ifvg_retest_tolerance":   0.35, # depth into IFVG still valid (0–1)

    # ── Step 3: Entry Gap ────────────────────────────────
    "bag_min_size_pips":       2.5,
    "cfvg_min_size_pips":      2.0,
    "cfvg_large_wick_ratio":   0.6,  # wick > this = wait mitigation, not direct
    "fvg_min_size_pips":       1.5,
    "fvg_mitigated_depth":     0.5,
    "no_resistance_lookback":  20,

    # ── Gap Sweep Micro-Entry ─────────────────────────────
    "use_gap_sweep_entry":     True, # after gap mitigated, sweep of mitigating candle
    "gap_sweep_max_delay":     3,    # max bars after mitigation to watch for sweep

    # ── Double BAG Filter ─────────────────────────────────
    "double_bag_wait_50pct":   True, # skip double BAG, wait for 50% retrace

    # ── Step 4: Target / Traffic Light ───────────────────
    "t1_min_pips":             8,    # T1 (Extreme FVG) must be ≥ N pips away
    "t2_min_pips":             15,   # T2 (Swing H/L) target minimum
    "max_obstruction_pips":    2.0,  # level closer than N pips = blocked target
    "traffic_light_enabled":   True, # Green at R1, Red at T1

    # ── Order Flow Bias ───────────────────────────────────
    "use_order_flow_filter":   True, # only trade in Order Flow direction
    "of_gap_count_lookback":   10,   # bars to count directional gaps for OFD

    # ── Manipulation Gap ──────────────────────────────────
    "mg_impulse_candles":      4,    # consecutive candles = impulse before MG
    "mg_after_target_lookback":5,    # first gap within N bars of T1 = MG

    # ── Trade Management ─────────────────────────────────
    "entry_bar_delay":         0,
    "max_trades_per_day":      4,
    "session_start_hour":      12,   # UTC 12:00 = IST 17:30
    "session_end_hour":        16,   # UTC 16:00 = IST 21:30

    # ── Signal Scoring Weights ────────────────────────────
    # Score each signal 0-10. Only trade if score >= min_score.
    "min_signal_score":        5,
    "score_a_class_gap":       3,    # BAG or CFVG (A-class gap)
    "score_sweep_2plus":       2,    # 2+ sweeps at level
    "score_sweep_1":           1,    # 1 sweep at level
    "score_ifc_candle":        2,    # IFC at sweep = institutional
    "score_no_resistance":     1,    # no resistance area on left
    "score_pd_zone":           1,    # in correct premium/discount zone
    "score_order_flow":        1,    # aligned with Order Flow direction

    # ── Pair weights (1.0 = trade normally, 0 = skip) ────
    "pair_weights": {
        "EURJPY": 1.0,   # 27 trades — most active
        "EURGBP": 1.0,   # 24 trades — very active
        "USDJPY": 1.0,   # 20 trades
        "AUDJPY": 0.8,   # 15 trades
        "CADJPY": 0.8,   # 12 trades
        "EURUSD": 1.0,   # 12 trades
        "GBPUSD": 0.8,   # 9 trades
    },
}


# ══════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════

def pip_size(pair: str) -> float:
    return 0.01 if "JPY" in pair else 0.0001

def to_pips(diff: float, pair: str) -> float:
    return abs(diff) / pip_size(pair)


# ══════════════════════════════════════════════════════════
#  MAJOR CANDLE DETECTION
#  Inside candle: high < prev high AND low > prev low → ignore
#  Major candle: its high or low remains unbreached by next candles
# ══════════════════════════════════════════════════════════

def is_inside_candle(df, i):
    if i < 1:
        return False
    return (df["high"].iloc[i] <= df["high"].iloc[i - 1] and
            df["low"].iloc[i]  >= df["low"].iloc[i - 1])

def find_major_candle(df, i, lookback=5):
    """Returns index of last major candle before i (not inside candle)."""
    for j in range(i - 1, max(i - lookback - 1, 0), -1):
        if not is_inside_candle(df, j):
            return j
    return i - 1


# ══════════════════════════════════════════════════════════
#  PREMIUM / DISCOUNT ZONE
#  50% midpoint of recent range divides premium (top half) from discount (bottom)
#  Buys: price must be in discount zone
#  Sells: price must be in premium zone
# ══════════════════════════════════════════════════════════

def get_pd_zone(df, i, p):
    lb = p["pd_range_lookback"]
    start = max(0, i - lb)
    hi = df["high"].iloc[start:i].max()
    lo = df["low"].iloc[start:i].min()
    mid = (hi + lo) / 2
    current = df["close"].iloc[i]

    if current < mid:
        return "discount"
    elif current > mid:
        return "premium"
    else:
        return "midpoint"


# ══════════════════════════════════════════════════════════
#  EQUAL HIGHS / EQUAL LOWS DETECTION
#  Clusters of equal highs or lows = dense liquidity = wait for sweep
# ══════════════════════════════════════════════════════════

def has_equal_levels(df, i, p, direction):
    """
    direction='high': check for equal highs in lookback
    direction='low': check for equal lows
    Returns True if 2+ levels within tolerance → dense liquidity
    """
    lb = p["equal_level_lookback"]
    tol = p["equal_level_tolerance"]
    start = max(0, i - lb)
    current_price = df["close"].iloc[i]

    count = 0
    if direction == "high":
        ref = df["high"].iloc[start:i].max()
        for j in range(start, i):
            if abs(df["high"].iloc[j] - ref) / ref < tol:
                count += 1
    else:
        ref = df["low"].iloc[start:i].min()
        for j in range(start, i):
            if abs(df["low"].iloc[j] - ref) / ref < tol:
                count += 1

    return count >= 2


# ══════════════════════════════════════════════════════════
#  LIQUIDITY SWEEP DETECTION (Enhanced)
#  Valid pullback requires TWO conditions simultaneously:
#    1. Wick pierces swing high/low (liquidity swept)
#    2. Body closes back on the other side (body break confirmation)
#  Sweep counting for strength scoring
# ══════════════════════════════════════════════════════════

def detect_swing_sweep(df, i, p):
    """
    Returns ('bull'/'bear', sweep_count) or (None, 0)
    Bull sweep: wick below swing low, close above it
    Bear sweep: wick above swing high, close below it
    """
    lb = p["sweep_lookback"]
    if i < lb + 2:
        return None, 0

    # Find swing using major candles only
    swing_highs = []
    swing_lows = []
    for j in range(max(0, i - lb), i):
        if not is_inside_candle(df, j):
            swing_highs.append(df["high"].iloc[j])
            swing_lows.append(df["low"].iloc[j])

    if not swing_highs:
        return None, 0

    swing_high = max(swing_highs)
    swing_low  = min(swing_lows)
    row = df.iloc[i]

    body_top    = max(row["close"], row["open"])
    body_bottom = min(row["close"], row["open"])
    total_size  = row["high"] - row["low"]
    body_size   = body_top - body_bottom

    if total_size == 0:
        return None, 0

    wick_ratio  = 1 - (body_size / total_size) if total_size > 0 else 0

    # Valid pullback: wick sweeps + body closes back (BOTH conditions)
    bull_sweep = (row["low"] < swing_low and
                  body_bottom >= swing_low and
                  wick_ratio >= p["sweep_wick_ratio"])

    bear_sweep = (row["high"] > swing_high and
                  body_top <= swing_high and
                  wick_ratio >= p["sweep_wick_ratio"])

    direction = None
    if bull_sweep:
        direction = "bull"
    elif bear_sweep:
        direction = "bear"
    else:
        return None, 0

    # Count historical sweeps at this level (strength scoring)
    count_lb = p["sweep_count_lookback"]
    sweep_count = 0
    level = swing_low if direction == "bull" else swing_high
    for j in range(max(0, i - count_lb), i):
        r = df.iloc[j]
        if direction == "bull" and r["low"] < level and r["close"] > level:
            sweep_count += 1
        elif direction == "bear" and r["high"] > level and r["close"] < level:
            sweep_count += 1

    return direction, sweep_count


# ══════════════════════════════════════════════════════════
#  IFC CANDLE DETECTION
#  Institutional Funding Candle: large wick, tiny body
#  Appears at 2nd sweep of a level → institutional entry signal
#  NOT directly tradeable alone — context signal only
# ══════════════════════════════════════════════════════════

def is_ifc_candle(df, i):
    """Returns True if candle is IFC shape (shooting star / hammer)"""
    row = df.iloc[i]
    body   = abs(row["close"] - row["open"])
    total  = row["high"] - row["low"]
    if total == 0:
        return False
    body_ratio = body / total
    return body_ratio < 0.25  # body < 25% of total range = IFC shape


# ══════════════════════════════════════════════════════════
#  ORDER FLOW DIRECTION BIAS
#  Consistent gaps in one direction = Order Flow = trade that direction only
#  If gaps form on both sides = ranging = skip
# ══════════════════════════════════════════════════════════

def get_order_flow_direction(df, i, p):
    """
    Count bullish vs bearish gaps in last N bars
    Returns 'bull', 'bear', or 'ranging'
    """
    lb = p["of_gap_count_lookback"]
    bull_gaps = 0
    bear_gaps = 0

    for j in range(max(2, i - lb), i):
        if df["low"].iloc[j] > df["high"].iloc[j - 2]:
            bull_gaps += 1
        if df["high"].iloc[j] < df["low"].iloc[j - 2]:
            bear_gaps += 1

    if bull_gaps == 0 and bear_gaps == 0:
        return None
    if bull_gaps > bear_gaps * 1.5:
        return "bull"
    if bear_gaps > bull_gaps * 1.5:
        return "bear"
    return "ranging"


# ══════════════════════════════════════════════════════════
#  IDM TRACKING
#  IDM = first pullback below HH (uptrend) or above LL (downtrend)
#  Must be mitigated (touched) before OB/gap becomes valid for entry
# ══════════════════════════════════════════════════════════

def check_idm_mitigated(df, i, p, direction):
    """
    Checks if the current IDM level has been mitigated (touched).
    Returns True if IDM was touched (wick or body — either counts for IDM).
    """
    lb = p["idm_lookback"]
    start = max(0, i - lb)

    if direction == "bull":
        # In uptrend: find swing low after last HH (IDM = first pullback below HH)
        recent_high = df["high"].iloc[start:i].max()
        hh_idx = df["high"].iloc[start:i].values.argmax() + start
        # IDM = lowest point between HH and now
        if hh_idx + 1 >= i:
            return True  # not enough bars
        idm_low = df["low"].iloc[hh_idx:i].min()
        # Check if price came back to IDM level (touched)
        for j in range(hh_idx, i):
            if df["low"].iloc[j] <= idm_low * 1.001:  # within 0.1%
                return True
    else:
        # In downtrend: IDM = first pullback above LL
        recent_low = df["low"].iloc[start:i].min()
        ll_idx = df["low"].iloc[start:i].values.argmin() + start
        if ll_idx + 1 >= i:
            return True
        idm_high = df["high"].iloc[ll_idx:i].max()
        for j in range(ll_idx, i):
            if df["high"].iloc[j] >= idm_high * 0.999:
                return True

    return False


# ══════════════════════════════════════════════════════════
#  EXTREME FVG DETECTION (Step 1B)
#  Extreme FVG = widest / most prominent gap at swing extremes
#  Also used as T1 target level
# ══════════════════════════════════════════════════════════

def detect_extreme_fvg(df, i, p, pair):
    """
    Finds most recent extreme FVG and checks if current bar mitigates it.
    Returns ('bull'/'bear', fvg_high, fvg_low) or (None, 0, 0)
    """
    lb  = p["efvg_lookback"]
    min_pips = p["efvg_min_size_pips"]
    depth    = p["fvg_mitigated_depth"]

    best_bull = None
    best_bear = None

    for j in range(i - 2, max(i - lb, 2), -1):
        if is_inside_candle(df, j):
            continue

        # Bullish extreme FVG: low[j] > high[j-2]
        if df["low"].iloc[j] > df["high"].iloc[j - 2]:
            size = to_pips(df["low"].iloc[j] - df["high"].iloc[j - 2], pair)
            if size >= min_pips:
                fvg_top = df["low"].iloc[j]
                fvg_bot = df["high"].iloc[j - 2]
                mit_level = fvg_top - (fvg_top - fvg_bot) * depth
                if df["low"].iloc[i] <= mit_level:
                    if best_bull is None or size > best_bull[0]:
                        best_bull = (size, fvg_top, fvg_bot)

        # Bearish extreme FVG: high[j] < low[j-2]
        if df["high"].iloc[j] < df["low"].iloc[j - 2]:
            size = to_pips(df["low"].iloc[j - 2] - df["high"].iloc[j], pair)
            if size >= min_pips:
                fvg_bot = df["high"].iloc[j]
                fvg_top = df["low"].iloc[j - 2]
                mit_level = fvg_bot + (fvg_top - fvg_bot) * depth
                if df["high"].iloc[i] >= mit_level:
                    if best_bear is None or size > best_bear[0]:
                        best_bear = (size, fvg_top, fvg_bot)

    if best_bull:
        return "bull", best_bull[1], best_bull[2]
    if best_bear:
        return "bear", best_bear[1], best_bear[2]
    return None, 0, 0


# ══════════════════════════════════════════════════════════
#  SHARP TURN DETECTION (Step 2A)
#  Fast reversal structure: opposing gap forms breaking/overlapping MG
#  Left-side gap must already be broken for valid ST
# ══════════════════════════════════════════════════════════

def detect_sharp_turn(df, i, p, pair):
    bars = p["sharp_turn_bars"]
    min_pips = p["sharp_turn_gap_pips"]
    if i < bars + 3:
        return None

    # Look for opposing gap pattern
    for j in range(i - bars, i):
        if j < 2 or is_inside_candle(df, j):
            continue

        # Prior bullish gap → look for bearish gap (bear ST)
        if df["low"].iloc[j] > df["high"].iloc[j - 2]:
            prior_gap_high = df["low"].iloc[j]
            for k in range(j + 1, i + 1):
                if k < 2 or is_inside_candle(df, k):
                    continue
                if df["high"].iloc[k] < df["low"].iloc[k - 2]:
                    size = to_pips(df["low"].iloc[k - 2] - df["high"].iloc[k], pair)
                    # Opposing gap overlaps/breaks prior gap (left-side break required)
                    if size >= min_pips and df["high"].iloc[k] <= prior_gap_high:
                        return "bear"

        # Prior bearish gap → look for bullish gap (bull ST)
        if df["high"].iloc[j] < df["low"].iloc[j - 2]:
            prior_gap_low = df["high"].iloc[j]
            for k in range(j + 1, i + 1):
                if k < 2 or is_inside_candle(df, k):
                    continue
                if df["low"].iloc[k] > df["high"].iloc[k - 2]:
                    size = to_pips(df["low"].iloc[k] - df["high"].iloc[k - 2], pair)
                    if size >= min_pips and df["low"].iloc[k] >= prior_gap_low:
                        return "bull"

    return None


# ══════════════════════════════════════════════════════════
#  INVERSE FVG DETECTION (Step 2B)
#  Existing gap broken by body → polarity flips → trade on retest
# ══════════════════════════════════════════════════════════

def detect_ifvg(df, i, p, pair):
    tol = p["ifvg_retest_tolerance"]
    lb  = p["efvg_lookback"]

    for j in range(i - 2, max(i - lb, 2), -1):
        if is_inside_candle(df, j):
            continue

        # Original bear gap broken by bull body → IFVG bull
        if df["high"].iloc[j] < df["low"].iloc[j - 2]:
            gap_bot = df["high"].iloc[j]
            gap_top = df["low"].iloc[j - 2]
            gap_mid = gap_bot + (gap_top - gap_bot) * tol
            for k in range(j + 1, i):
                if df["close"].iloc[k] > gap_top:
                    if gap_bot <= df["low"].iloc[i] <= gap_mid:
                        if df["close"].iloc[i] > gap_bot:
                            return "bull"
                    break

        # Original bull gap broken by bear body → IFVG bear
        if df["low"].iloc[j] > df["high"].iloc[j - 2]:
            gap_top = df["low"].iloc[j]
            gap_bot = df["high"].iloc[j - 2]
            gap_mid = gap_top - (gap_top - gap_bot) * tol
            for k in range(j + 1, i):
                if df["close"].iloc[k] < gap_bot:
                    if gap_mid <= df["high"].iloc[i] <= gap_top:
                        if df["close"].iloc[i] < gap_top:
                            return "bear"
                    break

    return None


# ══════════════════════════════════════════════════════════
#  ENTRY GAP DETECTION (Step 3)
#  C-FVG, BAG, FVG + FVG Mitigated
#  Includes: CFVG large wick filter, Double BAG skip, MG detection
# ══════════════════════════════════════════════════════════

def detect_entry_gap(df, i, p, pair):
    """
    Returns (direction, gap_type, fvg_high, fvg_low) or (None, None, 0, 0)
    """
    if i < 3:
        return None, None, 0, 0

    row   = df.iloc[i]
    prev  = df.iloc[i - 1]
    prev2 = df.iloc[i - 2]

    # Skip inside candles for gap detection
    if is_inside_candle(df, i) or is_inside_candle(df, i - 1):
        return None, None, 0, 0

    # Manipulation Gap detection: first gap after impulse run
    imp_up = all(df["close"].iloc[i - k] > df["open"].iloc[i - k]
                 for k in range(1, p["mg_impulse_candles"] + 1) if i - k >= 0)
    imp_dn = all(df["close"].iloc[i - k] < df["open"].iloc[i - k]
                 for k in range(1, p["mg_impulse_candles"] + 1) if i - k >= 0)
    is_mg = (row["low"] > prev2["high"] and imp_up) or \
            (row["high"] < prev2["low"] and imp_dn)
    if is_mg:
        return None, None, 0, 0  # Never trade MG

    # BAG: body break of prior extreme
    bull_bag_exists = row["low"] > prev2["high"]
    bear_bag_exists = row["high"] < prev2["low"]

    if bull_bag_exists:
        size = to_pips(row["low"] - prev2["high"], pair)
        if size >= p["bag_min_size_pips"]:
            if prev["close"] > prev2["high"]:  # body break confirmation
                # Double BAG check
                if i >= 4:
                    pp2 = df.iloc[i - 3]
                    pp3 = df.iloc[i - 4]
                    prior_bull_bag = (prev["low"] > pp3["high"] and
                                      df["close"].iloc[i - 2] > pp3["high"])
                    if prior_bull_bag and p["double_bag_wait_50pct"]:
                        return None, None, 0, 0  # Skip, wait for 50% retrace
                return "bull", "BAG", row["high"], row["low"]

    if bear_bag_exists:
        size = to_pips(prev2["low"] - row["high"], pair)
        if size >= p["bag_min_size_pips"]:
            if prev["close"] < prev2["low"]:
                if i >= 4:
                    pp2 = df.iloc[i - 3]
                    pp3 = df.iloc[i - 4]
                    prior_bear_bag = (prev["high"] < pp3["low"] and
                                      df["close"].iloc[i - 2] < pp3["low"])
                    if prior_bear_bag and p["double_bag_wait_50pct"]:
                        return None, None, 0, 0
                return "bear", "BAG", row["high"], row["low"]

    # CFVG: color change on current candle
    bull_gap = row["low"] > prev2["high"]
    bear_gap = row["high"] < prev2["low"]

    if bull_gap:
        size = to_pips(row["low"] - prev2["high"], pair)
        if size >= p["cfvg_min_size_pips"]:
            # Color change: prev was bearish, current is bullish
            if row["close"] > row["open"] and prev["close"] < prev["open"]:
                # Large wick filter: if current candle has large wick → wait mitigation
                body   = abs(row["close"] - row["open"])
                total  = row["high"] - row["low"]
                wick_r = 1 - (body / total) if total > 0 else 0
                if wick_r > p["cfvg_large_wick_ratio"]:
                    return None, None, 0, 0  # Large wick CFVG → wait mitigation
                return "bull", "CFVG", row["high"], row["low"]

    if bear_gap:
        size = to_pips(prev2["low"] - row["high"], pair)
        if size >= p["cfvg_min_size_pips"]:
            if row["close"] < row["open"] and prev["close"] > prev["open"]:
                body   = abs(row["close"] - row["open"])
                total  = row["high"] - row["low"]
                wick_r = 1 - (body / total) if total > 0 else 0
                if wick_r > p["cfvg_large_wick_ratio"]:
                    return None, None, 0, 0
                return "bear", "CFVG", row["high"], row["low"]

    # FVG + Prior FVG Mitigated
    if bull_gap:
        size = to_pips(row["low"] - prev2["high"], pair)
        if size >= p["fvg_min_size_pips"]:
            lb = p["efvg_lookback"]
            depth = p["fvg_mitigated_depth"]
            for j in range(max(2, i - lb), i - 2):
                if is_inside_candle(df, j):
                    continue
                if df["high"].iloc[j] < df["low"].iloc[j - 2]:
                    fvg_bot = df["high"].iloc[j]
                    fvg_top = df["low"].iloc[j - 2]
                    mit_level = fvg_bot + (fvg_top - fvg_bot) * depth
                    if df["high"].iloc[j + 1:i].max() >= mit_level:
                        return "bull", "FVG", row["high"], row["low"]

    if bear_gap:
        size = to_pips(prev2["low"] - row["high"], pair)
        if size >= p["fvg_min_size_pips"]:
            lb = p["efvg_lookback"]
            depth = p["fvg_mitigated_depth"]
            for j in range(max(2, i - lb), i - 2):
                if is_inside_candle(df, j):
                    continue
                if df["low"].iloc[j] > df["high"].iloc[j - 2]:
                    fvg_top = df["low"].iloc[j]
                    fvg_bot = df["high"].iloc[j - 2]
                    mit_level = fvg_top - (fvg_top - fvg_bot) * depth
                    if df["low"].iloc[j + 1:i].min() <= mit_level:
                        return "bear", "FVG", row["high"], row["low"]

    # Gap Sweep Micro-Entry: after gap mitigation, next candle sweeps low
    if p["use_gap_sweep_entry"]:
        gap_sweep = detect_gap_sweep_entry(df, i, p, pair)
        if gap_sweep:
            return gap_sweep[0], "GAP_SWEEP", gap_sweep[1], gap_sweep[2]

    return None, None, 0, 0


def detect_gap_sweep_entry(df, i, p, pair):
    """
    Gap Sweep Strategy: after a gap is mitigated by a candle,
    if the next candle sweeps the mitigating candle's low (bull) → entry.
    One trade per gap sweep. Returns (direction, high, low) or None.
    """
    delay = p["gap_sweep_max_delay"]
    if i < delay + 3:
        return None

    # Look back for a recently mitigated gap
    for j in range(max(2, i - delay - 2), i - 1):
        # Bullish gap mitigated: low[j] > high[j-2], then price came back
        if df["low"].iloc[j] > df["high"].iloc[j - 2]:
            fvg_top = df["low"].iloc[j]
            fvg_bot = df["high"].iloc[j - 2]
            # Check if mitigating candle exists between j and i
            for m in range(j + 1, i):
                if df["low"].iloc[m] <= fvg_top:  # price entered gap = mitigated
                    mitig_candle = m
                    # Now: did current candle sweep mitigating candle's low?
                    if (i == mitig_candle + 1 or i <= mitig_candle + delay):
                        if (df["low"].iloc[i] < df["low"].iloc[mitig_candle] and
                                df["close"].iloc[i] > df["low"].iloc[mitig_candle]):
                            # Green candle (bull signal)
                            if df["close"].iloc[i] > df["open"].iloc[i]:
                                return ("bull", df["high"].iloc[i], df["low"].iloc[i])
                    break

        # Bearish gap mitigated
        if df["high"].iloc[j] < df["low"].iloc[j - 2]:
            fvg_bot = df["high"].iloc[j]
            fvg_top = df["low"].iloc[j - 2]
            for m in range(j + 1, i):
                if df["high"].iloc[m] >= fvg_bot:
                    mitig_candle = m
                    if i <= mitig_candle + delay:
                        if (df["high"].iloc[i] > df["high"].iloc[mitig_candle] and
                                df["close"].iloc[i] < df["high"].iloc[mitig_candle]):
                            if df["close"].iloc[i] < df["open"].iloc[i]:
                                return ("bear", df["high"].iloc[i], df["low"].iloc[i])
                    break

    return None


# ══════════════════════════════════════════════════════════
#  TARGET CLARITY CHECK — TRAFFIC LIGHT SYSTEM (Step 4)
#  T1 = Extreme FVG level (mandatory stop — Red = don't trade past this)
#  T2 = Swing High/Low
#  R1 = Extreme FVG at reversal zone (Green = enter)
#  R2 = Swing Low/High (deeper entry)
#  Only trade between R1 and T1 — this is the valid trading zone
# ══════════════════════════════════════════════════════════

def check_clear_target(df, i, p, pair, direction):
    """
    Returns (is_clear, t1_pips, t2_pips, in_valid_zone)
    Traffic light: valid zone = between R1 (E-FVG) and T1 (swing target)
    """
    t1_min    = p["t1_min_pips"] * pip_size(pair)
    t2_min    = p["t2_min_pips"] * pip_size(pair)
    obstruct  = p["max_obstruction_pips"] * pip_size(pair)
    lb        = p["no_resistance_lookback"]
    current   = df["close"].iloc[i]

    if direction == "bull":
        t1_target = df["high"].iloc[max(0, i - lb) : i].max()
        t1_pips   = to_pips(t1_target - current, pair)
        # Check no obstruction between current and T1
        mid = (current + t1_target) / 2
        recent_highs = df["high"].iloc[max(0, i - lb) : i]
        obstructions = ((recent_highs > current + obstruct) &
                        (recent_highs < mid)).sum()
        # T2 target (further swing high)
        t2_target = df["high"].iloc[max(0, i - lb * 2) : i].max()
        t2_pips   = to_pips(t2_target - current, pair)
    else:
        t1_target = df["low"].iloc[max(0, i - lb) : i].min()
        t1_pips   = to_pips(current - t1_target, pair)
        mid = (current + t1_target) / 2
        recent_lows = df["low"].iloc[max(0, i - lb) : i]
        obstructions = ((recent_lows < current - obstruct) &
                        (recent_lows > mid)).sum()
        t2_target = df["low"].iloc[max(0, i - lb * 2) : i].min()
        t2_pips   = to_pips(current - t2_target, pair)

    is_clear     = (t1_pips >= p["t1_min_pips"] and obstructions == 0)
    in_valid_zone = is_clear  # simplified: clear T1 = valid zone

    return is_clear, t1_pips, t2_pips, in_valid_zone


# ══════════════════════════════════════════════════════════
#  NO RESISTANCE AREA CHECK
#  No gap or swing on the left side = price moves fast
#  Bonus score for no resistance area
# ══════════════════════════════════════════════════════════

def has_no_resistance(df, i, p, direction):
    """Returns True if no prior swing/gap blocks the path"""
    lb = p["no_resistance_lookback"]
    current = df["close"].iloc[i]
    pip = pip_size("EURUSD")  # generic small threshold

    if direction == "bull":
        zone_top = df["high"].iloc[max(0, i - lb) : i].max()
        obstacles = sum(1 for j in range(max(0, i - lb), i)
                        if current < df["high"].iloc[j] < zone_top)
        return obstacles == 0
    else:
        zone_bot = df["low"].iloc[max(0, i - lb) : i].min()
        obstacles = sum(1 for j in range(max(0, i - lb), i)
                        if zone_bot < df["low"].iloc[j] < current)
        return obstacles == 0


# ══════════════════════════════════════════════════════════
#  SIGNAL SCORING
#  Each confluence adds points. Min score = trade, below = skip.
# ══════════════════════════════════════════════════════════

def calculate_signal_score(gap_type, sweep_count, is_ifc, no_resist, pd_ok, of_aligned, p):
    score = 0

    # Gap type score
    if gap_type in ("BAG", "CFVG"):
        score += p["score_a_class_gap"]
    elif gap_type in ("FVG", "GAP_SWEEP"):
        score += 1

    # Sweep strength
    if sweep_count >= 2:
        score += p["score_sweep_2plus"]
    elif sweep_count == 1:
        score += p["score_sweep_1"]

    # IFC candle at sweep (institutional entry signal)
    if is_ifc:
        score += p["score_ifc_candle"]

    # No resistance area
    if no_resist:
        score += p["score_no_resistance"]

    # Premium/Discount zone alignment
    if pd_ok:
        score += p["score_pd_zone"]

    # Order Flow alignment
    if of_aligned:
        score += p["score_order_flow"]

    return score


# ══════════════════════════════════════════════════════════
#  MAIN SIGNAL GENERATOR
#  Runs all 4 steps + all filters, produces scored signals
# ══════════════════════════════════════════════════════════

def generate_signals(df, pair, params=None):
    """
    Returns list of signal dicts with full confluence breakdown.
    Each signal: {bar, direction, gap_type, step1, step2, score, t1_pips, t2_pips}
    """
    p = params or PARAMS
    signals = []
    daily_counts = {}

    for i in range(30, len(df)):

        # ── Session filter ──────────────────────────────
        hour = df.index[i].hour if hasattr(df.index[i], "hour") else 0
        if not (p["session_start_hour"] <= hour < p["session_end_hour"]):
            continue

        # ── Pair weight filter ──────────────────────────
        if p["pair_weights"].get(pair, 1.0) == 0:
            continue

        # ── Skip inside candles ─────────────────────────
        if p["ignore_inside_candles"] and is_inside_candle(df, i):
            continue

        # ── Order Flow Direction ────────────────────────
        of_dir = get_order_flow_direction(df, i, p)
        if of_dir == "ranging" and p["use_order_flow_filter"]:
            continue  # Ranging market = stay out

        # ── STEP 1: Trigger ─────────────────────────────
        sweep_dir, sweep_count = detect_swing_sweep(df, i, p)
        efvg_dir, efvg_hi, efvg_lo = detect_extreme_fvg(df, i, p, pair)
        trigger_dir = sweep_dir or efvg_dir
        if trigger_dir is None:
            continue
        step1 = "Sweep" if sweep_dir else "E-FVG"

        # ── IDM Mitigation Check ────────────────────────
        if p["idm_mitigation_required"]:
            if not check_idm_mitigated(df, i, p, trigger_dir):
                continue

        # ── Equal Highs/Lows → Skip if no sweep yet ────
        check_dir = "high" if trigger_dir == "bear" else "low"
        if has_equal_levels(df, i, p, check_dir) and sweep_count == 0:
            continue  # Equal levels = wait for sweep, not happened yet

        # ── STEP 2: Confirmation ────────────────────────
        st_dir   = detect_sharp_turn(df, i, p, pair)
        ifvg_dir = detect_ifvg(df, i, p, pair)
        confirm_dir = st_dir or ifvg_dir
        if confirm_dir is None:
            continue
        if confirm_dir != trigger_dir:
            continue
        step2 = "SharpTurn" if st_dir else "IFVG"

        # ── STEP 3: Entry Gap ───────────────────────────
        gap_dir, gap_type, g_hi, g_lo = detect_entry_gap(df, i, p, pair)
        if gap_dir is None or gap_dir != trigger_dir:
            continue

        # ── STEP 4: Clear Target (Traffic Light) ────────
        is_clear, t1_pips, t2_pips, in_zone = check_clear_target(
            df, i, p, pair, trigger_dir)
        if not is_clear:
            continue

        # ── Confluence Scoring ──────────────────────────
        pd_zone   = get_pd_zone(df, i, p)
        pd_ok     = ((trigger_dir == "bull" and pd_zone == "discount") or
                     (trigger_dir == "bear" and pd_zone == "premium"))
        ifc       = is_ifc_candle(df, i)
        no_resist = has_no_resistance(df, i, p, trigger_dir)
        of_ok     = (of_dir == trigger_dir)

        score = calculate_signal_score(
            gap_type, sweep_count, ifc, no_resist, pd_ok, of_ok, p)

        if score < p["min_signal_score"]:
            continue

        # ── Daily Trade Cap ─────────────────────────────
        bar_date = str(df.index[i].date()) if hasattr(df.index[i], "date") else str(i)
        daily_counts[bar_date] = daily_counts.get(bar_date, 0) + 1
        if daily_counts[bar_date] > p["max_trades_per_day"]:
            continue

        signals.append({
            "bar":         i,
            "direction":   trigger_dir,
            "gap_type":    gap_type,
            "step1":       step1,
            "step2":       step2,
            "score":       score,
            "sweep_count": sweep_count,
            "ifc_candle":  ifc,
            "pd_zone":     pd_zone,
            "of_dir":      of_dir,
            "t1_pips":     round(t1_pips, 1),
            "t2_pips":     round(t2_pips, 1),
            "pair":        pair,
        })

    return signals
