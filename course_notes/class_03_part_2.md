# Class 3 (Part 2) — Practical Targets, Reversal Points & Traffic Light Rules

**Course**: Indian Binary Trading (IBT) / The IBT Trader  
**Topic**: Live Market Targets, Starting vs. Stopping Points & Structural Resets  
**Timeframe**: 1-Minute (1m) chart  
**Platform**: TradingView (`EURUSD · 1 · FXCM`)  
**Session Type**: Practical Replay, Internal Structure Mapping & Target Progression  

---

## 1. TOPIC & CONTEXT

- **Specific Concepts Taught**:
  - **Live Chart Application of Market Targets & Reversal Points**: Practical mapping of internal structure using Stopping Points (Targets 1 & 2) and Starting Points (Reversal Points 1 & 2).
  - **Trend Polarity Dynamics**:
    - *Downtrend*: Targets are located below current price (liquidity to be broken); Reversal Points are located above current price (pullback ceilings).
    - *Uptrend*: Targets are located above current price; Reversal Points are located below current price.
  - **Break of Structure (BOS) Liquidity Rule**: Why trading must stop completely once price reaches a Major Break of Structure.
  - **Structural Reset After BOS**: Locating the new Inducement (IDM), scanning pullbacks for valid Order Blocks, and marking the Change of Character (CHOCH) level.
  - **CHoCH Boundary Rule**: Disqualification of Order Blocks located beyond the CHOCH boundary.
  - **Mitigated Target Disqualification**: Eliminating Target 1 when an FVG is already mitigated.
  - **Sequential "Look-Left" Target Extraction**: Algorithmic lookback to preceding swing pullbacks when targets are broken.
  - **"Speed Breakers vs. U-Turns" Philosophy**: Why Targets are meant to be broken while Reversal Points act as structural pivots.
- **Timeframe(s) & Currency Pair Displayed**:
  - Asset / Pair: `EUR/USD` (Euro / U.S. Dollar, FXCM feed on TradingView).
  - Timeframe: 1-Minute ("1m" / "1") chart throughout the entire session.

---

## 2. VISUAL CANDLESTICK & STRUCTURE RULES

### A. Major vs. Minor / Inside Candles

- **Opposite-Color Candle Trigger [02:20–02:35, 02:55–03:05, 04:00–04:15]**:
  - Minor/inside candles inside an uninterrupted momentum leg are ignored.
  - A new internal swing high or low is mechanically established only when an opposite-color candle closes:
    - *During a downward leg*: The low is confirmed only when the first green candle prints. That lowest point is marked as the swing low, and the origin of the drop is marked as the swing high.
    - *During an upward leg*: The high is confirmed only when the first red candle prints. That highest point is marked as the swing high, and the origin of the rally is marked as the swing low.
  - Uninterrupted candles of the same color are treated as a single momentum block (visually measured with rectangular projection boxes).

### B. Valid Pullback / Sweep & Wick-to-Body Mechanics

- **Sweep + Opposite-Color Candle Reversal [06:45–07:15]**:
  - A valid sweep requires price to pierce beyond the previous candle’s extreme with a wick, reject, and immediately print an opposite-color expansion candle (*"market low sweep karne ke baad green candle laya"*).
  - This validates the candle as an Order Block and establishes the boundaries of the new Trading Zone.
- **Clear Gap vs. Tiny Inconsequential Gap [04:15–04:25]**:
  - When selecting Reversal Point 1, the mentor ignores tiny, negligible gaps (*"chhota sa gap hai, gap hi nahi tha"*); Reversal Point 1 strictly requires a clear, prominent Fair Value Gap (FVG/BAG).
- **Mitigated Gap Elimination [07:30–07:45]**:
  - If a wick from a subsequent candle has already tagged or overlapped the FVG zone, that FVG is mitigated. It loses its status as a valid target.

### C. Swing High / Swing Low Lookback Rule

- **1-Pullback Immediate Lookback [02:20–02:35, 07:05–07:20]**:
  - Once an opposite-color candle forms a low/high, the opposite boundary is the immediate preceding pullback directly adjacent to that move.
- **Algorithmic "Look-Left" Sequential Lookback [07:50–08:15, 09:00–09:35, 17:35–17:50]**:
  - When price breaks Target 2 (the immediate pullback high/low), the system looks back to the immediate preceding pullback leg to the left.
  - From that prior swing leg, it extracts:
    1. **Next Target 1 (T1)**: The Extreme FVG of that left-side leg.
    2. **Next Target 2 (T2)**: The structural high/low of that left-side leg.
  - If those are broken, the system scans left again to the next prior swing leg.

---

## 3. ENTRY & EXECUTION HABITS

- **No Live Orders Placed on Screen**:
  - Similar to Video 1, this session is a live mentoring analysis on TradingView. The mentor does not click the live Buy/Sell order buttons (the TradingView order panel remains idle at 0.01 lot).
- **Execution Space & Safety Margin [03:00–03:40, 10:55–11:05, 13:10–13:25]**:
  - **Never Enter at Stopping Points**: Do not place trades when price reaches Target 1 or Target 2 (*"Red Light"*).
  - **Execute Between Starting Point & Stopping Point**: After price mitigates a Reversal Point (Starting Point / Green Signal) and confirms reversal via an opposite-color candle, the entry is taken inside that Trading Zone targeting the next Target 1 (Extreme FVG) and Target 2 (Swing extreme).
- **Expiration Time**:
  - Not applicable. The webinar focuses purely on 1-minute SMC spot forex price action without binary option timers.

---

## 4. "DO NOT TRADE" / AVOIDANCE RULES

1. **STOP ALL TRADING When Major BOS is Reached [04:30–04:48]**:
   - *Visual Cue*: Price touches or breaks the external Break of Structure line.
   - *Mentor Rule*: *"Ek baar hamara breakout structure touch kar diya market, hum koi bhi trade execute nahi karna. Neeche nahi karna, upar nahi karna. Kyun? Breakout structure is big big liquidity level."* All trading must halt until the structural reset (IDM sweep) completes.
2. **Do NOT Trade Order Blocks Located Beyond CHoCH [05:20–05:38]**:
   - *Visual Cue*: An Order Block sitting above the Change of Character level in a downtrend (or below in an uptrend).
   - *Mentor Rule*: Disqualify it. If price reaches and breaks CHOCH, the trend reverses to an uptrend, invalidating bearish OBs. OBs must only be sought inside the existing CHOCH boundary.
3. **Avoid Pullbacks Lacking an Open Gap or Major Candle [04:55–05:10, 06:45–06:55]**:
   - *Visual Cue*: Intermediate pullbacks after BOS that do not contain a valid FVG and a major candle.
   - *Mentor Rule*: Skip them and scan higher up the leg until a valid unmitigated OB is found.
4. **Delete Target 1 if the FVG is Already Mitigated [07:30–07:45]**:
   - *Visual Cue*: An FVG inside the target zone that has already been pierced by a candle wick.
   - *Mentor Rule*: *"Yeh gap toh already mitigation ho gaya... isme toh koi bhi target nahi tha."* Do not map it as Target 1; Target 2 becomes the sole target.
5. **No Intermediate Reversal Entries in Gapless Momentum [08:15–08:40]**:
   - *Visual Cue*: A strong momentum leg containing zero gaps (*"koi bhi gap nahi tha"*).
   - *Mentor Rule*: Reversal Point 1 does not exist. Do not attempt to catch reversals in the middle of the leg; wait until price reaches Reversal Point 2 (the absolute swing extreme).
6. **Ignore External Inducement When Trading Internal Legs [10:00–10:15]**:
   - *Visual Cue*: Price trading between internal Target and Reversal zones.
   - *Mentor Rule*: Do not look at external Inducement levels to take internal trades. Internal legs trade exclusively from Target to Reversal.
7. **STOP TRADING at Target / Stopping Points ("Red Light Rule") [13:10–13:25]**:
   - *Visual Cue*: Price reaches Target 1 (Extreme FVG) or Target 2 (Swing high/low).
   - *Mentor Rule*: Targets are stopping points (red traffic light). Cease trading immediately; do not chase price further and do not take blind counter-trend trades.
8. **Do NOT Expect Targets to Hold as Reversal Support [17:35–18:15]**:
   - *Visual Cue*: Downtrend targets (support lows) being approached.
   - *Mentor Rule*: Targets are "speed breakers" that the market is actively trying to break. Never trade reversals off targets; true reversals only happen at designated Reversal Points (*"U-turns"*).

---

## 5. TIMESTAMPED RULE SUMMARY

- **[01:20–01:55] Downtrend Target Architecture**: In a downtrend, Target 1 is the Extreme FVG below, and Target 2 is the Break of Structure level / Swing Low.
- **[02:00–02:15] Polarity Inversion Rule**: Uptrends place Targets above and Reversal Points below; downtrends place Targets below and Reversal Points above.
- **[02:20–02:45] Opposite-Color Reversal Candle Rule**: The low of a leg is established only when the first green candle closes; the high is the origin of that move.
- **[02:45–03:00] Reversal Point 1 Definition**: Reversal Point 1 is strictly the Extreme FVG within the newly formed pullback leg.
- **[03:00–03:40] Internal Leg Resumption**: When price mitigates Reversal Point 1 and prints an opposite red candle, a new internal trading zone forms towards Target 1 (internal FVG) and Target 2 (swing low).
- **[04:15–04:28] Gap Filtering Rule**: Ignore tiny, negligible gaps; Reversal Point 1 must be anchored to a clear, visually obvious FVG/BAG.
- **[04:30–04:48] BOS Cease-Trade Mandate**: The moment price hits the external BOS level, immediately stop all trade execution in both directions due to massive liquidity.
- **[04:50–05:15] Post-BOS Structural Reset Sequence**: Mark IDM at the first valid pullback above BOS; scan deeper pullbacks to find the first valid unmitigated Order Block.
- **[05:20–05:38] CHoCH Boundary Limit Rule**: Order Blocks above the CHOCH line are disqualified; valid OBs must reside inside the CHOCH boundary.
- **[06:45–07:15] Sweep + Opposite Candle OB Validation**: A valid OB forms when price sweeps a low/high with a wick and prints an immediate opposite-color expansion candle.
- **[07:30–07:45] Mitigated Gap Elimination**: Disqualify any Target 1 FVG that has already been touched by price; advance directly to Target 2.
- **[07:50–08:15] Left-Side Target Lookback**: When Target 2 is broken, look left to the immediate prior pullback leg to establish the next Target 1 (Extreme FVG) and Target 2 (Swing high).
- **[08:15–08:40] Zero-Gap Momentum Rule**: When an impulse leg contains no gaps, Reversal Point 1 is absent; price will retrace directly to Reversal Point 2 (the swing origin).
- **[09:10–09:35] Sequential Expansion Rule**: Each successive breakout triggers a scan to the next prior pullback to the left to extract the next Target/Reversal zone.
- **[10:00–10:15] Internal Autonomy Principle**: Inside internal legs, external Inducements are obsolete; execution relies purely on Target-to-Reversal cycles.
- **[10:20–10:55] Live Market Zone Mapping**: Defining the active Trading Zone on EUR/USD 1m between the reaction low and the pullback high, setting Target 1 at the Extreme FVG.
- **[13:10–13:25] Traffic Signal Execution Model**: Red Signal = Stopping Point (Target 1 / Target 2; stop trading). Green Signal = Starting Point (Reversal Point 1 / Reversal Point 2; enter trade upon confirmation).
- **[15:40–16:15] Trend-Agnostic System Execution**: Using internal Target-to-Reversal flow allows high-probability entries in both directions regardless of the macro trend.
- **[17:35–18:15] Speed Breaker vs. U-Turn Rule**: Targets are speed breakers meant to be broken by momentum; Reversal Points are institutional U-turns that pivot the entire leg.
