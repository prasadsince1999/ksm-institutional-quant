# Class 7 (Part 2) — Practical Replay, 30-Second Rule, Manipulation Gaps & Live Quotex Execution

**Course**: Indian Binary Trading (IBT) / The IBT Trader  
**Topic**: Live Chart SMC/ICT Application, Manipulation Gaps, Strict 30s Execution Rule, 3+ Sweep Degradation & Live Broker Nuances  
**Timeframe**: Exclusively 1-Minute (1m / M1)  
**Platforms**: Quotex (live trading web platform), TradingView (OANDA / FXCM feeds for symbol search and candle comparison)  
**Assets**: `EUR/USD`, `EUR/GBP`, `USD/JPY`, `EUR/JPY`, `CAD/JPY`, `GBP/USD`, `GBP/JPY`, `AUD/USD` (1m)  
**Session Type**: Live Trading, Market Replay & Student Doubt Clearing  

---

## 1. TOPIC & CONTEXT

- **Specific Concepts Taught**:
  - **Live Chart SMC/ICT Application on 1-Minute Binary Options**: Practical identification and live mapping of Inducement (IDM), Order Blocks (OB), Extreme Fair Value Gaps (EFVG), Break of Structure (BOS), and Liquidity Sweeps.
  - **Manipulation Gap vs. Genuine Reaction Gap**: Recognizing why the first gap following a structural pivot or target is a manipulation trap and how to wait for its breakout before trading reversals.
  - **Overlapping Extreme Gap Strategy for Strong Trends**: How to trade aggressive runaway trends that refuse to retrace to Inducement by utilizing prior resistance/support levels aligned with overlapping extreme gaps.
  - **Technical Trend vs. Practical/Price Action Trend**: Distinguishing between macro structural bias (technically uptrend) and real-time order flow (practically downtrend).
  - **Candle Anatomy Rules for Gap Validity**: Major vs. minor/inside candle distinctions, 3rd candle upper/lower wick rejection rules, and gap separation distance.
  - **Macro & Market Quality Filters**:
    - Economic news filtering via Investing.com (identifying volatility shocks and post-news volume drops).
    - Optimal trading sessions and hours schedule.
    - Real market vs. OTC broker behavior, including broker-specific wick manipulation (Quotex vs. IQ Option).
  - **Ranging Market Identification**: Defining a ranging market mechanically when price fails to respect both bullish and bearish gaps.
  - **Execution Habits**: The 30-second rule, safety margin pullbacks into Inverse Fair Value Gaps (IFVG), and session trade limits.

- **Timeframe(s) and Currency Pairs Displayed**:
  - Timeframe: Exclusively the 1-minute (1m / M1) timeframe.
  - Platforms Used: Quotex (live trading web platform) and TradingView (OANDA / FXCM feeds).
  - Currency Pairs Analyzed:
    - `EUR/USD` (1m) – Analyzed extensively; live trade taken.
    - `EUR/GBP` (1m) – Analyzed extensively; live trade taken.
    - `USD/JPY` (1m) – Levels mapped and analyzed.
    - `EUR/JPY` (1m) – Mapped and analyzed for inside candle / trap failure.
    - `CAD/JPY`, `GBP/USD`, `GBP/JPY`, `AUD/USD` (1m) – Monitored.

---

## 2. VISUAL CANDLESTICK & STRUCTURE RULES

### A. Major vs. Minor / Inside Candles

- **Rule for Inside / Minor Candles [33:30–33:45]**:
  - Gaps created between a major candle and an inside/minor candle (a candle whose range is contained within or fails to meaningfully expand past the preceding candle) are **strictly invalid**.
  - Mentor demonstrations on `EUR/JPY`: Price formed an apparent gap and touched resistance, but the trade failed because the middle candle was not a true structural candle (*"This is a major candle, this is not a major candle. There is no gap actually, isliye market fail ho gayi"*).
  - **Mechanical Rule**: Do not mark an FVG/BAG unless all three candles are major, standalone expansion candles with clear high/low separation.

### B. Valid Pullback / Sweep (Wick-to-Body Relationship)

- **Touch-and-Go Candle Sweep [06:40–07:05]**:
  - When a candle spikes directly into an extreme level and bounces immediately within the same candle, do **not** buy at the open of the next candle.
  - You must wait for the low of that touch candle to be swept by a subsequent candle before entering long.
- **Wick Rejection Directionality on CFVG [05:35–05:45]**:
  - On a bullish Color Change Fair Value Gap (CFVG), if the 3rd candle has an oversized upper wick (bearish rejection), direct open entry is **prohibited**.
  - Entry is only permitted after price retraces and mitigates the gap.
- **Valid vs. Fake Sweeps**:
  - **Valid Sweep [09:15]**: Price sweeps the high/low of a key structural point and immediately closes back within the zone with a confirming body color (green body with lower wick for buy; red body with upper wick for sell).
  - **Fake / Weak Sweep [25:40–25:55]**: If a support or resistance level has been swept **3 or more times ($3\times+$)**, the level is considered drained of liquidity and fragile. Further sweeps are breakout traps rather than reversal points.
- **Gap Distance / Candle Separation [27:35–28:05]**:
  - If the candle preceding the entry closes with empty space (a visual void) between its body and the gap boundary, **do not enter**.
  - Price will often print an extra candle to fill that visual void before reversing.

### C. Swing High / Swing Low Lookback

- **Impulse Leg Lookback [02:50–03:20, 20:30]**:
  - When mapping a swing high and swing low to apply the 50% equilibrium (Fibonacci), measure the immediate structural impulse wave, which typically consists of **7 to 15 candles** on the 1-minute timeframe (visually tracked using the Date Range tool: 7 bars, 11 bars, 13 bars, 15 bars).
- **Consolidation Lookback [15:35]**:
  - If an attempted move spends **3 to 4 candles** failing to generate an FVG or BAG, directional institutional strength is judged to be zero.

---

## 3. ENTRY & EXECUTION HABITS

### A. Direct Open (00s) vs. Safety Margin Pullback

- **No Blind Open Entries (00s)**:
  - Across the live trades demonstrated, the mentor does **not** click blindly at the 00s open.
  - **Pullback Entry (Safety Margin)**: Entry is taken only after the candle opens, moves against the intended trade direction, and tests an Inverse Fair Value Gap (IFVG) or the 50% equilibrium of the gap [26:08, 26:40].
- **The Strict 30-Second Rule [29:35–29:45, 36:40]**:
  - A pullback entry into the zone is valid **only if price reaches the entry level within the first 29 to 30 seconds of the 1-minute candle**.
  - If the candle takes longer than 30 seconds to reach the zone, the trade must be **strictly skipped/cancelled**:  
    *"29-30 seconds ke andar aaye toh lena, iske baad hum kuchh bhi trade nahi lena."*

### B. Live Trades Executed (Quotex ₹10,000 Real Capital)

- **Trade 1 [26:08–27:15]: `EUR/USD` – SELL (Down)**
  - **Setup**: Upward pullback into an IFVG zone during the initial seconds of the 1-minute candle.
  - **Stake**: ₹10,000 INR.
  - **Execution**: Safety margin entry taken inside the first 20 seconds as price spiked into the IFVG.
  - **Result**: **WIN (+₹18,700 payout)**. The candle closed as a small doji/red body, winning precisely because of the safety margin entry.
- **Trade 2 [26:38–27:20]: `EUR/GBP` – SELL (Down)**
  - **Setup**: Push upward into the gap at price 0.87233.
  - **Stake**: ₹10,000 INR.
  - **Result**: **LOSS (₹0 payout)**.
  - **Post-Mortem Analysis [27:00–27:30]**: The mentor breaks down the exact algorithmic reason for the loss:
    1. The low had already been swept multiple times (**$3\times+$ times**), draining liquidity.
    2. The candle closed **above the 50% level** of the gap, invalidating the bearish structure.

### C. Exact Expiration Time

- **Fixed 1-Minute Expiration**:
  - All trades are executed on Quotex set to expire at the close of the current 1-minute candle (e.g., set to 21:26:00, 21:30:00, 21:40:00).

---

## 4. "DO NOT TRADE" / AVOIDANCE RULES

1. **Manipulation Gap (First Gap after Reversal) [04:05–04:45]**: The first gap formed immediately after a price reversal or target point is a Manipulation Gap. Never trade a reaction or bounce off this gap; wait for it to be broken.
2. **CFVG with Upper Wick Rejection [05:35]**: Avoid buying at the open of a CFVG setup if the 3rd candle has a prominent upper wick.
3. **Trading Directly into Resistance [07:30–08:10]**: Do not buy from a bullish gap if the immediate close is directly against an unmitigated extreme resistance zone.
4. **Two Consecutive BAGs Open [08:10–08:25]**: When two Breakaway Gaps print sequentially, do not enter at the open. Expect a mandatory retracement into the IFVG or 50% zone.
5. **Conflicting Dual Setups (Trap on Both Sides) [09:10–09:40]**: If technical indicators show a sell setup at the highs (e.g., BAG + CFVG) and a buy setup at the lows (e.g., sweep + green candle) simultaneously, avoid entering. Price is trapped between opposing algorithmic orders.
6. **Aggressive Trend Inducement Skipping [11:55–12:20]**: In runaway momentum moves where price refuses to pull back to Inducement, do not place blind limit/reversal trades expecting an IDM touch.
7. **Economic News / Friday Market Close [14:15–14:35, 32:45]**: Avoid trading around high-impact news (e.g., 9:00 PM USD news on Investing.com) and during late Friday sessions (after 9:30 PM). Spreads widen, volume thins, and broker price feeds exhibit erratic behavior.
8. **No Gap Formed after 3–4 Pushes [15:35]**: If buyers or sellers push multiple times but cannot print a clean gap, strength is absent; do not trade trend continuation.
9. **Wick-Heavy Price Action [16:45]**: When candles consistently print long upper and lower wicks with miniature bodies, market structure is degraded; cease trading.
10. **Order Block Manipulation Trap [22:05–22:35]**: Do not buy into an Order Block upon the first apparent gap; wait until price breaks through the manipulation gap.
11. **Level Swept 3+ Times [25:40–25:55]**: If a support or resistance line has been wicked/swept 3 or more times, reject further sweep setups at that line.
12. **Gap Separation / Void [27:35–28:05]**: If a candle closes far from the zone boundary leaving an unfilled visual gap, do not enter; expect a fill candle first.
13. **Absence of Reaction [28:15]**: If price approaches a zone and fails to show an immediate wick rejection, do not enter.
14. **Entry after 30 Seconds [29:35, 36:40]**: If the candle has been open for more than 30 seconds before reaching the level, cancel the trade immediately.
15. **Insufficient Target Space (< 1 Candle Body) [30:00–30:25]**: If the distance between the entry price and the next extreme gap/barrier is smaller than a single average 1-minute candle body, do not enter.
16. **Violent Momentum Spikes into Support [31:45–32:10]**: If price crashes into a support level or gap via an abnormally large, fast momentum bar, do not trade the bounce; high velocity typically blows through the level.
17. **Fake Gaps from Inside Candles [33:30–33:45]**: Gaps generated by inside or minor candles are structural illusions; reject any setup based on them.
18. **Dual-Sided Gap Invalidation (Mechanical Definition of Chop) [39:00–39:40]**: If the market prints bullish gaps that fail to produce upward moves, and bearish gaps that fail to produce downward moves, the market is in a chop/ranging regime. Stop trading completely.

---

## 5. TIMESTAMPTED RULE SUMMARY

| Timestamp | Direct Mechanical Rule |
|---|---|
| **[01:21]** | **Doji inside FVG Rule**: A Doji candle inside an FVG counts as a mitigation touch; wait for post-mitigation confirmation. |
| **[02:05]** | **Level Drawing Tool Rule**: The Date Range tool is preferred over standard rectangles because it automatically marks the 50% equilibrium level. |
| **[02:50]** | **4-Point Structural Mapping**: Mark the Lower Low breakout, Inducement, Extreme FVG, and Order Block before considering entries. |
| **[04:05]** | **Manipulation Gap Rule**: The first gap created following a reversal or target reach is a Manipulation Gap; do not trade bounces from it. |
| **[05:35]** | **CFVG 3rd Candle Wick Filter**: If the 3rd candle of a bullish CFVG has a large upper rejection wick, open entry is banned; wait for mitigation. |
| **[06:40]** | **Touch-and-Go Sweep Rule**: A single candle that touches a level and bounces must have its low swept by a subsequent candle before entering long. |
| **[08:15]** | **Double BAG Retracement Rule**: Two consecutive BAGs require a retracement into the IFVG or 50% level before taking continuation trades. |
| **[09:15]** | **Dual Trap Invalidation**: When sell setups at resistance and buy setups at support form concurrently, stand aside. |
| **[11:55]** | **Overlapping Extreme Gap Rule**: In runaway trends where Inducement is bypassed, enter only at Overlapping Gaps aligned with prior resistance. |
| **[14:15]** | **High-Impact News Filter**: Use Investing.com; stop trading during red-folder events (e.g., 9:00 PM USD) and after 9:30 PM on Fridays. |
| **[15:35]** | **3–4 Candle Exhaustion Rule**: A move that takes 3–4 candles without creating an FVG indicates zero institutional momentum. |
| **[16:45]** | **Wick Noise Filter**: When charts become dominated by dual-sided wicks without clean bodies, cease trading. |
| **[18:40]** | **Resistance Trap with CFVG**: Sweeping a resistance high is insufficient for a sell if an opposing CFVG and trap sit directly below. |
| **[20:30]** | **50% Equilibrium Target Rule**: Measure the swing high to swing low of the impulse leg; price targets the 50% level before reversing. |
| **[22:15]** | **Manipulation Gap Breakout Prerequisite**: Reversals off an Order Block require a confirmed candle close through the manipulation gap. |
| **[25:40]** | **3+ Sweep Degradation Rule**: A level swept 3 or more times is liquidity-drained and prone to failure. |
| **[26:08]** | **Live Trade 1 Entry (EUR/USD Win)**: Sell entry taken on an upward pullback into an IFVG level; won as a doji due to margin of safety. |
| **[26:40]** | **Live Trade 2 Entry (EUR/GBP Loss)**: Sell entry taken on EUR/GBP; lost due to 3+ prior sweeps and breakout above 50% of the gap. |
| **[27:35]** | **Gap Separation Void Rule**: If a candle closes separated from the gap boundary, do not enter; wait for a fill candle. |
| **[28:15]** | **Mandatory Visual Reaction**: Price must display a live rejection wick at the level before an entry is triggered. |
| **[29:35]** | **The 30-Second Execution Cutoff**: Pullback entries into a zone must execute within the first 29–30 seconds of the 1m candle; cancel entries after 30s. |
| **[30:00]** | **Minimum Target Space Rule**: Ensure at least one full 1-minute candle body of empty space exists before the next EFVG barrier. |
| **[31:45]** | **Fast Momentum Rejection**: Abnormally large expansion spikes directly into a level invalidate bounce trades. |
| **[32:45]** | **Optimal Trading Schedule**:  <br>• Best Windows: 5:30 PM – 9:00/9:30 PM, 3:30 PM – 4:30 PM, and after 12:30 PM / 1:00 PM. <br>• Avoid: Morning sessions before 12:30 PM (insufficient volume). |
| **[33:35]** | **Major vs. Minor Candle FVG Filter**: Gaps formed with an inside/minor candle are fake; FVG/BAG calculations require three major candles. |
| **[35:15]** | **Broker Feed Integrity**: Quotex is preferred over IQ Option because it preserves true market gaps and does not artificially distort candle wicks. |
| **[37:55]** | **Session Trade Quota**: Limit execution to 3 to 5 (or 4 to 6) high-probability trades per session to prevent psychological tilt. |
| **[39:10]** | **Mechanical Definition of Ranging Markets**: If market fails to hold both bullish and bearish gaps, market is in chop; shut down trading. |
