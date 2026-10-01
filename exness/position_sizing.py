"""
exness/position_sizing.py — pure, unit-testable position sizing.

Fixes three bugs in the old trader.calculate_lot_size():
  1. JPY crosses (EURJPY, GBPJPY) divided by the CROSS price (~180) instead of USDJPY (~150),
     so lots were ~20% too large.
  2. USDCAD / USDCHF used a flat $10 pip value (real: ~$7.3 and ~$12.5 per lot).
  3. max(vol_min, ...) silently forced the minimum lot even when that exceeded the risk budget,
     contradicting the docstring "guarantees risk does not exceed the specified percentage".

Preferred method: MT5's own trade_tick_value / trade_tick_size (broker-correct for every symbol).
Fallback: quote-currency conversion using supplied rates.
"""
import math
import re
from typing import Dict, Optional, Tuple

MAX_OVERRISK_FACTOR = 1.25   # if the minimum lot would risk > 1.25x the budget, REFUSE the trade


def base_symbol(symbol: str) -> str:
    """'EURUSDm' / 'EURUSD.r' / 'XAUUSDz' -> 'EURUSD'."""
    m = re.match(r"[A-Z]{6}", symbol.upper())
    return m.group(0) if m else symbol.upper()


def pip_value_per_lot_usd(symbol: str, contract_size: float, pip: float,
                          rates: Optional[Dict[str, float]] = None,
                          tick_value: Optional[float] = None,
                          tick_size: Optional[float] = None) -> float:
    """USD value of a 1-pip move for 1.0 lot."""
    if tick_value and tick_size and tick_value > 0 and tick_size > 0:
        return tick_value * (pip / tick_size)            # broker-correct, any symbol
    rates = rates or {}
    sym = base_symbol(symbol)
    quote = sym[3:6]
    native = contract_size * pip                        # pip value in QUOTE currency per lot
    if quote == "USD":
        return native
    # quote currency is the first leg of a USDxxx pair: divide by that rate
    if quote in ("JPY", "CAD", "CHF"):
        r = rates.get("USD" + quote)
        if not r or r <= 0:
            raise ValueError(f"need USD{quote} rate to size {symbol}")
        return native / r
    # quote currency is the second leg of xxxUSD: multiply by that rate
    if quote in ("GBP", "EUR", "AUD", "NZD"):
        r = rates.get(quote + "USD")
        if not r or r <= 0:
            raise ValueError(f"need {quote}USD rate to size {symbol}")
        return native * r
    raise ValueError(f"unsupported quote currency for {symbol}")


def lots_for_risk(equity: float, risk_pct: float, risk_pips: float, pip_value_lot: float,
                  vol_min: float, vol_max: float, vol_step: float) -> Tuple[float, Dict]:
    """
    Returns (lots, info). lots == 0.0 means REFUSE (caller must skip the trade).
    Rounds DOWN to the volume step. Never rounds up past budget * MAX_OVERRISK_FACTOR.
    """
    budget = equity * risk_pct
    info = {"budget_usd": round(budget, 4), "status": "OK"}
    if risk_pips <= 0 or pip_value_lot <= 0 or budget <= 0:
        info["status"] = "REJECT_BAD_INPUT"
        return 0.0, info
    raw = budget / (risk_pips * pip_value_lot)
    lots = math.floor(raw / vol_step + 1e-9) * vol_step
    if lots < vol_min:
        min_risk = vol_min * risk_pips * pip_value_lot
        info["min_lot_risk_usd"] = round(min_risk, 4)
        if min_risk > budget * MAX_OVERRISK_FACTOR:
            info["status"] = "REJECT_MIN_LOT_EXCEEDS_BUDGET"
            return 0.0, info
        lots = vol_min
        info["status"] = "MIN_LOT_SLIGHT_OVERRISK"
    lots = min(lots, vol_max)
    lots = round(lots, 8)
    actual = lots * risk_pips * pip_value_lot
    info["actual_risk_usd"] = round(actual, 4)
    info["actual_risk_pct"] = round(actual / equity, 6)
    return lots, info


def calculate_turtle_drawdown_equity(current_equity: float, peak_equity: float) -> float:
    """
    Implements the Turtle Trading Account Shrinkage Rule:
    For every 10% drawdown in equity from the peak, the sizing equity is reduced by 20%.
    Prevents account ruin during extended drawdown periods.
    """
    if peak_equity <= 0 or current_equity <= 0:
        return current_equity
    dd_pct = (peak_equity - current_equity) / peak_equity
    if dd_pct <= 0:
        return current_equity
    # Number of full 10% drawdown steps
    steps = math.floor(dd_pct / 0.10)
    reduction_factor = (0.80) ** steps
    return current_equity * reduction_factor

