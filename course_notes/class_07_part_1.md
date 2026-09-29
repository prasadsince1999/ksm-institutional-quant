# Class 7 (Part 1) — Advanced Gap Taxonomy, CFVG & Gap Sweep Strategy

**Course**: Indian Binary Trading (IBT) / The IBT Trader  
**Topic**: Advanced Gap Taxonomy (BAG, CFVG, IFVG, MG), 3rd Candle Anatomy & Gap Sweep Strategy  
**Timeframe**: Exclusively 1-Minute (1m / M1) timeframe  
**Platforms**: TradingView (`EURUSD` 1m FXCM, `BTCUSD` 1m Bitstamp), Quotex (`EURUSD`, `USDJPY`, `EURGBP`, `CADJPY`, `EURAU`, `AUDCHF`, `CHFJPY` 1m)  
**Session Type**: Advanced Execution Masterclass & Student Homework Review  

---

## 1. TOPIC & CONTEXT

- **Specific Concepts Taught**:
  - **Smart Money Concepts (SMC) & ICT for High-Frequency / Binary Trading**: Inducement (IDM), Order Blocks (OB), Break of Structure (BOS), Change of Character (CHOCH), Liquidity Sweeps, and Traps.
  - **Weak vs. Strong Levels**: Weak Inducement (unmitigated structural levels) vs. Strong Inducement (levels backed by prior gap mitigations).
  - **Gap Classification & Behavior**:
    - FVG (Fair Value Gap) vs. BAG (Breakaway Gap / Balanced Alignment Gap).
    - 3rd Candle Anatomy Rule for BAG and CFVG.
    - Two Consecutive BAGs Rule (retracement dynamics).
    - Manipulation Gap vs. Extreme Gap (identifying false reaction gaps before major targets).
    - Premium (above 50%) vs. Discount (below 50%) gap filtering using 0.5 equilibrium.
    - CFVG (Color Change Fair Value Gap) rules and execution.
    - IFVG (Inverse Fair Value Gap) rules, limits of retest, and invalidation.
  - **Confluence Strategy**: BAG + CFVG = Direct Trade (DT).
  - **Gap Sweep Strategy**: Single-candle sweep of prior candle's high/low inside a mitigated zone.
  - **Internal vs. External Confirmation Rules**: When a candle sweep suffices vs. when a full gap is mandatory.
  - **Target Space Rule**: Minimum space required before an opposing barrier.
  - **Doji Handling Rules**: Execution protocols when an indecision candle forms.
- **Timeframe(s) and Currency Pairs Displayed**:
  - Timeframe: Exclusively the 1-minute timeframe (1m / M1).
  - Mentor's Chart: `EUR/USD` (1-minute, FXCM on TradingView).
  - Student Charts Reviewed:
    - `BTC/USD` (1m, TradingView Bitstamp)
    - `CAD/JPY` (1m, Forex.com & binary broker)
    - `EUR/USD` (1m, Quotex platform)
    - `USD/JPY` (1m, Quotex platform)
    - `AUD/CHF` (1m, Quotex platform)
    - `EUR/AUD` (1m, Quotex platform)
    - `EUR/GBP` (1m, Quotex mobile platform)
    - `CHF/JPY` (Quotex platform)

---

## 2. VISUAL CANDLESTICK & STRUCTURE RULES

### A. Major vs. Minor / Inside Candles

- **Inside Candle Invalidation**: Inside candles (candles whose entire range from high to low is contained within the preceding mother candle) are strictly ignored when defining market structure or sweep events. They do not constitute a new swing high/low or an inducement level.
- **3–4 Candle Consolidation Rule [13:55]**: If price spends 3 to 4 candles consolidating inside a zone after a gap mitigation without creating a new directional gap (FVG or BAG), buying/selling strength is considered exhausted, signaling an imminent reversal.

### B. Valid Pullback / Sweep (Wick-to-Body Relationship)

- **Wick Directionality**:
  - **Bullish Sweep / Buy**: The signal candle must sweep below the previous candle’s low via a lower wick, but the close must be a solid **GREEN body** [32:50]. A lower rejection wick (hammer-style) is required. If the upper wick is larger than the lower wick, the sweep is deemed rejected and will reverse downward [13:05].
  - **Bearish Sweep / Sell**: The signal candle must sweep above the previous candle’s high via an upper wick, but the close must be a solid **RED body**.
  - **Fake Sweep Rejection**: If a candle sweeps liquidity but closes as an opposite-colored candle (e.g., a red candle sweeping a low in a buy setup), the sweep is **FAKE / INVALID** [32:55].
- **3rd Candle Rule for Gaps (BAG / CFVG) [11:30–12:35]**:
  - *Invalid for 00s direct open*: If the 3rd candle is an oversized marubozu/expansion candle with no wick, or has long wicks on both sides, or exhibits a large opposing rejection wick, it is considered prone to retracement.
  - *Valid for 00s direct open*: A candle with a healthy body and a rejection wick pointing towards the origin (e.g., bottom wick for a buy, top wick for a sell).

### C. Swing High / Swing Low Lookback

- **Structure & Inducement Lookback**: Inducement (IDM) is defined as the first valid minor pullback that took liquidity against the primary impulse leg before creating the higher high / lower low.
- **Gap Sweep Lookback Limit [34:50]**: When trading the Gap Sweep pattern, the sweep must happen within 1 candle (highest probability) or at most 2 candles. If price takes 3 or more candles to sweep the low/high, the setup is invalidated.

---

## 3. ENTRY & EXECUTION HABITS

- **Direct Open (00s) vs. Pullback into Zone (Safety Margin)**:
  - **Direct Trade (DT) at Candle Open (00s)**: Executed immediately at the open of the candle (00s) only when high-probability confluence is present:
    1. Clean BAG + CFVG alignment [30:10].
    2. The 3rd candle has a clear directional rejection wick and a healthy body [24:10].
  - **Pullback Entry (Safety Margin)**: Mandatory under the following conditions:
    1. When the 3rd candle has large wicks or indecisive body [12:30].
    2. After two consecutive BAGs: price will retrace; enter only on a 50% pullback into the gap [15:30].
    3. On Doji formations: never enter at 00s; wait for price to retrace deep into the candle wick/lower half before firing [39:30].
    4. At mitigated levels where price wicks into the zone before closing [06:55].
- **Exact Expiration Time**:
  - **Fixed 1-Minute Expiration**: All broker trades displayed on Quotex are set to 1 minute (60 seconds), aligning with the duration of the current 1-minute candle (e.g., entry taken during candle duration expiring precisely at the close: 19:09:00, 19:12:00, 20:22:00, etc.).

---

## 4. "DO NOT TRADE" / AVOIDANCE RULES

1. **Ranging / Choppy Market [04:55]**: Skip all setups when candles are caught in a horizontal consolidation range without clear structural order flow.
2. **Trapped Between Support & Resistance [07:35]**: Do not enter when price is trapped between horizontal S/R levels with no gaps and liquidity has already been swept.
3. **Gap from an Unmitigated / Weak Inducement [09:10]**: Avoid gaps created directly off an unmitigated inducement level. Without a higher-timeframe or extreme gap mitigation backing it, it has a 50/50 failure rate.
4. **Third Candle with Bearish Rejection in Bullish Gap [11:35–12:20]**: If the 3rd candle of a bullish gap has an oversized upper wick or dual-sided wicks, avoid buying at the open.
5. **No Gap Formation after 3–4 Candles [13:55]**: If price reacts to a mitigation zone but fails to print a fresh FVG or BAG within 3 to 4 candles, buyer/seller strength has dried up; do not take trend-continuation trades.
6. **Double Consecutive BAG Open [15:10]**: Never enter directly at the open of a candle following two consecutive BAGs; wait for a 50% retracement.
7. **Manipulation Gap (First Gap Prior to Major Barrier) [16:20–17:35]**: The very first gap located immediately in front of an external target, reversal point, or inducement is a Manipulation Gap. Do not buy/sell on reactions inside this gap.
8. **Buying in Premium Zone (Above 50%) [18:55–19:25]**: Do not take buy trades from gaps located above the 50% equilibrium level (Premium); valid buy gaps must sit below 50% in the Discount zone (Extreme Gap).
9. **Conflicting Gaps (Gaps Above and Below) [20:30]**: When price sits between an unfilled gap above and another below at a reversal point, do not trade; wait for one side to break.
10. **Trading Prior to Manipulation Gap Breakout [22:15]**: Do not attempt to trade a reversal until the preceding manipulation gap has been broken by a candle body close.
11. **Over-using Inverse Fair Value Gaps (IFVG) [25:20]**: IFVGs cannot be used repeatedly like support/resistance lines. Maximum 2 interactions are permitted (original creation retest + one flip retest); any further touches must be skipped.
12. **Gaps Without Prior Liquidity Sweeps [29:10]**: Any momentum gap that appears without first sweeping a swing point or mitigating an OB/gap is fake momentum; do not trade.
13. **Opposite-Color Candle on Sweep [32:55]**: On a Gap Sweep setup, if the candle sweeping the low closes red, buying is canceled.
14. **Break of Sweep Candle Extremes [33:55]**: If a subsequent retracement candle breaks below the low of the green sweep candle, the setup is dead.
15. **Gap Sweep Taking > 2 Candles [34:50]**: If a sweep does not occur within 1 to 2 candles inside the zone, abort the trade.
16. **Candle Sweep at External Structure Levels [36:40–38:10]**: A single-candle sweep is strictly an internal continuation confirmation. At external turning points (IDM, OB, Target/BOS), entry requires a full structural gap (FVG/BAG).
17. **Lack of Space to Target [37:25]**: If there is not enough distance between the entry price and the target level to accommodate at least one full 1-minute candle body, skip the trade.
18. **Signal Candle Closing as a Doji [39:15]**: If the setup candle closes as a flat doji with no real body, skip direct open execution.

---

## 5. TIMESTAMPED RULE SUMMARY

- **[04:55] Ranging Invalidation Rule**: Avoid taking setups inside tight horizontal ranges; edge is lost without structural momentum.
- **[07:35] Support/Resistance Trap Rule**: Do not buy/sell between major S/R lines without fresh gap confirmation and untaken liquidity.
- **[08:35] Weak Inducement Rule**: Inducements touched without prior HTF gap mitigation represent weak levels; resulting gaps have a 50% failure rate.
- **[09:45] Strong Inducement Rule**: A level becomes strong only when its origin stems from a prior gap/liquidity mitigation.
- **[10:30] Mitigation-to-Gap Strength Rule**: When a zone is mitigated and immediately produces a new gap, the new gap is considered high-probability.
- **[11:35] BAG 3rd Candle Marubozu Rule**: An oversized expansion candle without wicks signals impending retracement; skip direct open entry.
- **[12:00] BAG 3rd Candle Opposing Wick Rule**: Long upper wicks on bullish gaps (or long lower wicks on bearish gaps) invalidate direct open entry.
- **[12:15] BAG 3rd Candle Dual Wick Rule**: Long wicks on both sides of the 3rd candle signal indecision and require waiting for a pullback.
- **[12:45] Perfect 3rd Candle Geometry**: A solid body with a rejection wick pointing towards entry origin allows direct trade on the next candle open.
- **[13:55] 3–4 Candle Exhaustion Limit**: Failure to print a new gap within 3–4 candles after mitigation indicates buyer/seller exhaustion.
- **[15:10] Two Consecutive BAGs Rule**: Two back-to-back BAGs cause immediate retracement; wait for a 50% pullback or 1 candle rest before entering.
- **[16:20] Manipulation Gap Identification**: The first gap immediately preceding a target or reversal level is a manipulation gap; do not trade bounces from it.
- **[18:05] Premium vs. Discount (50% Equilibrium)**: Measure swing low to swing high; execute buys only in Discount (< 50%) and sells in Premium (> 50%).
- **[18:45] Extreme Gap Rule**: In a multi-gap impulse leg, the first is manipulation, intermediate ones are low probability, and the final (Extreme Gap) in Discount is the prime zone.
- **[20:30] Dual Conflicting Gap Rule**: Skip trading when price is trapped between opposing unfilled gaps at a key pivot.
- **[22:15] Manipulation Gap Breakout Rule**: Reversals require waiting for a full candle body breakout through the opposing manipulation gap.
- **[23:05] Color Change FVG (CFVG) Rule**: An opposite-color candle within a trend creating an FVG acts as a BAG, qualifying for Direct Trade (DT).
- **[24:10] CFVG 3rd Candle Condition**: CFVG entries require a healthy body and supporting wick; dual long wicks mandate waiting for mitigation.
- **[24:35] Inverse Fair Value Gap (IFVG) Rule**: Broken FVGs become IFVGs on retest; valid as confluence only, with a strict maximum of 2 uses.
- **[29:10] Liquidity Sweep Prerequisite**: Gaps formed without sweeping a swing extreme or mitigating a block are fake momentum and must not be traded.
- **[30:10] Confluence Strategy (BAG + CFVG)**: Merging a BAG with a CFVG and IFVG retest constitutes a high-conviction Direct Trade (DT).
- **[32:30] Gap Sweep Strategy (Internal Reversal)**: Price dipping into a mitigated gap and sweeping the prior candle's low offers a 1-candle continuation setup.
- **[33:00] Gap Sweep Color Requirement**: Bullish sweep candles must close GREEN; bearish sweep candles must close RED. Opposite closes invalidate the trade.
- **[33:45] Gap Sweep Invalidation Level**: If price breaks below the low of the green sweep candle, the trade setup is canceled.
- **[34:50] Gap Sweep Lookback Rule**: The sweep event must take place within 1 candle (optimal) or 2 candles maximum.
- **[36:40] Internal vs. External Confirmation Mandate**: Single-candle sweeps are valid only inside the leg towards target. Major structural levels (OB, IDM, Target/BOS) strictly require full gap creation.
- **[37:25] Minimum Target Space Rule**: Ensure at least one full 1-minute candle body of empty space exists before the target; otherwise, reject the trade.
- **[39:15] Doji Execution Protocol**: Never enter at 00s open after a flat doji; either skip or enter only after price pulls back deep into the wick for a safety margin.
