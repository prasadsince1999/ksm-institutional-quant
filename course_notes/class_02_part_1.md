# Class 2 (Part 1) — Fair Value Gaps (FVG), Imbalances & Advanced Structure

**Course**: Indian Binary Trading (IBT) / The IBT Trader  
**Topic**: Fair Value Gaps (FVG), The 4 Imbalance Types & Mechanical Qualification Rules  
**Timeframe**: 1-Minute (1m) chart (with higher timeframe 5m, 10m, 15m context)  
**Platforms**: TradingView (`EURUSD · 1 · FXCM`), Quotex Mobile Web (`market-qx.trade` 1m)  
**Student Homework Reviewed**: Sourabh (EUR/USD Quotex), Prasad (XAU/USD TradingView), Mayur (USD/JPY TradingView), Vikas  

---

## 1. TOPIC & CONTEXT

- **Specific Concepts Taught**:
  - **SMC Mentorship Class 2 (Day 2)**: Fair Value Gaps (FVG) / Imbalance & Advanced Market Structure Review.
  - **Homework Analysis**: Reviewing student chart submissions on market structure mapping, single-pullback IDM vs. CHOCH rules, and shifting levels.
  - **Institutional Imbalance Theory**: Why Fair Value Gaps form (institutional footprint, banks/hedge funds entering the market, buyers/sellers imbalance, the *"Shark vs. Small Fish"* concept, and the *"iPhone Discount / Fair Price"* analogy).
  - **The 4 Specific Types of Fair Value Gaps**:
    1. **Normal Fair Value Gap (FVG)**: Classic 3-candle imbalance.
    2. **Breakaway Gap (BAG)**: High-momentum continuation gap.
    3. **Overlapping Gap (OG)**: Support/Resistance body breakout gap used as a reversal/refinement point.
    4. **Manipulation Gap (MG)**: Partially mitigated gap trap and the formation of a critical Liquidity Level.
  - **Mechanical Qualification Rules**: Major candle requirement for Candle 1, the 50% equilibrium level (Consequent Encroachment), visible rejection wick requirements, and direct entry vs. mitigation rules.
- **Timeframe(s) and Currency Pairs Displayed**:
  - Mentor’s Main Platform: TradingView — `EUR/USD` (Euro / U.S. Dollar), 1-Minute (1m) timeframe, FXCM feed (`EURUSD · 1 · FXCM`).
  - Student Homework Charts Reviewed On-Screen:
    - `EUR/USD` (1m): Quotex mobile binary trading platform (`market-qx.trade`) submitted by student Sourabh Ray [01:30 - 02:35].
    - Gold / US Dollar (`XAU/USD`, 1m): TradingView chart submitted by student Prasad [02:36 - 03:45].
    - `USD/JPY` (1m): TradingView FXCM feed submitted by student Mayur [03:50 - 04:46].

---

## 2. VISUAL CANDLESTICK & STRUCTURE RULES

### A. Major vs. Minor / Inside Candles

- **Candle 1 MUST Be a Major Candle [19:55 - 21:05]**:
  - When identifying any 3-candle Fair Value Gap (Candle 1, Candle 2, Candle 3), Candle 1 must strictly be a confirmed Major Candle (*"First candle must and should be need major candle"*).
  - **Ignoring Inside Candles**: If the candle immediately preceding the impulse candle (Candle 2) is an inside/internal candle (i.e., its range is trapped inside the prior candle's high and low), do not draw the gap from it. You must look back to the preceding Major Candle.
  - If drawing the zone from the true Major Candle's high/low overlaps with Candle 3's wick, there is NO gap, and the setup is completely invalidated.
- **Candle 3 Inside Candle Status [24:20 - 24:50]**:
  - While Candle 1 must be a Major Candle, Candle 3 does not need to break Candle 2. Even if Candle 3 is an inside candle relative to Candle 2, a normal FVG remains valid as long as open space exists between Candle 1's high and Candle 3's low.

### B. Valid Pullback / Sweep (Wick-to-Body Relationships)

- **Single-Pullback Structure Rule [02:15 - 02:35]**:
  - When price advances out of an origin with only one pullback, that pullback is always Inducement (IDM), never a Change of Character (CHOCH).
- **Normal FVG vs. Breakaway Gap (BAG) Wick vs. Body Rule [23:20 - 24:15 & 27:25 - 27:55]**:
  - **Normal FVG**: Candle 3 breaks the extreme (high in an uptrend, low in a downtrend) of Candle 2 with a **WICK ONLY**, or remains an inside candle. It does not close beyond Candle 2 with a body.
  - **Breakaway Gap (BAG)**: Candle 3 breaks and closes beyond the extreme of Candle 2 with a **FULL CANDLE BODY CLOSE**.
- **Visible Rejection Wick Confirmation Rule [22:30 - 23:15]**:
  - When price mitigates an FVG, the reaction candle must produce an unambiguous, clearly visible rejection wick.
  - A microscopic wick that is only visible when zooming in heavily is strictly rejected as confirmation (*"Zoom karu toh dikhegi... this is not a perfect confirmation. Humko chahiye bada rejection, visible reaction"*).
- **Support / Resistance Body Anchoring in Overlapping Gaps [31:20 - 31:35]**:
  - When identifying an Overlapping Gap at a support or resistance line, the S/R reference line is drawn strictly at the candle body close, NOT the wick extreme.

### C. Swing High / Swing Low Lookback Logic

- No Arbitrary Bar Lookback: The mentor does not count 3 or 5 candles.
- During the review of Gold (XAU/USD) and USD/JPY [02:40 - 04:45], swing points are verified strictly via the mechanical SMC process:
  - A Swing High (BOS) is only confirmed after price mitigates IDM; it is anchored to the highest candle peak formed between the initial breakout and the IDM mitigation.
  - A Swing Low (CHOCH) is anchored to the absolute lowest structural point below IDM that originated the impulsive BOS move.

---

## 3. ENTRY & EXECUTION HABITS

- **Execution Habits in this Lecture**:
  - No live or demo orders are clicked on-screen by the mentor; this session is dedicated to homework validation and FVG categorization.
- **Mechanical Execution Rules Established by Gap Type**:
  1. **Normal Fair Value Gap (FVG) Execution [25:00 - 26:15]**:
     - Never enter directly. An FVG strictly requires Mitigation (price returning to touch the gap) plus a visible rejection wick before entering in the trend direction.
  2. **Breakaway Gap (BAG) Execution [28:10 - 29:30]**:
     - BAG signals strong momentum/continuation.
     - **Direct Entry**: In ~90% of setups, traders enter directly on the open of the 4th candle in the trend direction without waiting for mitigation or pullback.
     - Even if a minor retracement candle appears, traders do not wait for gap mitigation; direct entry is executed in the impulse direction.
     - **The Target Exception (Safety Margin Required) [29:30 - 30:50]**: If the 3rd candle of the BAG closes directly into an existing swing high, resistance, or pullback level (target reached), do not enter directly. In this specific scenario, you must wait for a pullback to mitigate the BAG before taking the trade.
  3. **Overlapping Gap Execution [33:20 - 34:15, 35:50 - 36:25]**:
     - Not a direct entry gap. Acts as a structural reversal zone. Traders must wait for price to enter the zone and show lower-timeframe/internal confirmation before executing.
- **Timeframe & Expiry Context**:
  - Analysis is executed on the 1-Minute (1m) chart. The mobile execution shown by the student on Quotex operates on 1-minute expiration scalps.

---

## 4. "DO NOT TRADE" / AVOIDANCE RULES

1. **Avoid Labeling Single-Pullback Moves as CHOCH [02:15 - 02:35]**:
   - Do not mark a lone pullback as a trend reversal line; it is strictly an IDM level.
2. **Skip Microscopic / Invisible Gaps [19:15 - 19:35]**:
   - Avoid trading gaps that are barely perceptible or require extreme zoom to see. They carry no institutional backing and fail frequently.
3. **Avoid Gaps from Giant News / Exhaustion Candles [19:35 - 19:55]**:
   - Skip massive, erratic gaps created by high-impact news events or exhaustion candles. They do not respect technical SMC rules.
4. **Do Not Anchor Gaps to Inside Candles [19:55 - 21:05]**:
   - Never draw an FVG from Candle 1 if Candle 1 is an inside candle. Always trace back to the preceding Major Candle. If overlapping wicks eliminate the open space, reject the setup.
5. **Skip FVG Entries Lacking a Visible Rejection Wick [22:40 - 23:15]**:
   - Do not enter merely because price touched an FVG. If the candle closing inside the gap lacks a clear, visible rejection wick, reject the trade.
6. **Avoid Direct BAG Entries into Major Pullbacks/Targets [29:35 - 30:50]**:
   - Skip direct candle-open entries on Breakaway Gaps if the breakout candle terminates right into a major swing high or resistance level. Wait for mitigation.
7. **Do Not Trade Directly on Overlapping Gaps [33:20 - 33:45]**:
   - Avoid placing blind limit or market orders at Overlapping Gaps. They require secondary confirmation.
8. **The Retested "Remaining Gap" Trap (Manipulation Gap) [37:45 - 39:20]**:
   - *The Visual Trap*: An FVG was previously partially mitigated by a candle wick. Later, price returns to test the "remaining" unmitigated portion of the gap, hits the 50% level, and forms a bullish reaction candle.
   - *The SMC Mechanical Reality*: **DO NOT BUY THIS GAP**. In SMC, unlike retail support/resistance where multiple touches make a level "stronger", a gap or order block that has been touched once becomes WEAK (*"SMC me koi bhi level ek baar touch hua, ye weak hota... remaining gap weak hai, ye manipulate karega"*).
   - It has a 50-50 failure rate and will frequently get smashed through.
   - *The Correct Rule*: Locate the lowest wick/body point reached during the initial mitigation inside the gap. Mark this line as the **Liquidity Level**. Only trade when price sweeps this liquidity level.

---

## 5. TIMESTAMPED RULE SUMMARY

- **[02:15 - 02:35] Single Pullback IDM Rule**: If price rallies out of an origin with a single pullback, that level is strictly IDM, not CHOCH.
- **[06:30 - 07:45] Mechanical FVG 3-Candle Definition**:
  - Bullish FVG = Open gap between Candle 1 High and Candle 3 Low.
  - Bearish FVG = Open gap between Candle 1 Low and Candle 3 High.
- **[07:45 - 08:05] Wick Overlap Invalidation**: If wicks of Candle 1 and Candle 3 touch or overlap, there is no imbalance; the gap is completely invalid.
- **[08:50 - 10:05] Imbalance Theory**: A gap indicates that one side of the market (buyers or sellers) overpowered the other with aggressive institutional orders, creating an inefficiency.
- **[12:15 - 12:45] Footprint Rule**: Fair Value Gaps represent institutional footprints; they mark where banks and hedge funds entered the market.
- **[18:40 - 19:05] Candle Color Neutrality Rule**: The colors of Candle 1 and Candle 3 do not matter. The gap type is dictated entirely by Candle 2 (Green = Bullish Imbalance; Red = Bearish Imbalance).
- **[19:15 - 19:35] Gap Size Filter**: Ignore tiny, invisible gaps; they lack institutional backing.
- **[19:35 - 19:55] News / Exhaustion Filter**: Exclude giant gaps caused by high-impact news releases or exhaustion moves.
- **[19:55 - 21:05] Major Candle 1 Rule**: Candle 1 must always be a Major Candle. If Candle 1 is an inside candle, trace back to the preceding Major Candle to measure the gap.
- **[21:05 - 22:25] 50% Equilibrium (Consequent Encroachment) Rule**:
  - Measure 50% of the full gap zone.
  - A candle body closing above the 50% level confirms the gap is holding for a reversal.
  - A candle body closing below the 50% level on higher timeframes (5m, 10m, 15m) indicates the gap has failed and price is likely to continue lower.
- **[22:30 - 23:15] Rejection Wick Rule**: Entering an FVG requires a prominent, visually obvious rejection wick inside the gap zone.
- **[23:20 - 24:50] Normal FVG Structural Signature**: In a standard FVG, Candle 3 breaks Candle 2 by wick only, or stays inside Candle 2. It requires mitigation before trading.
- **[25:00 - 26:15] FVG Mitigation Rule**: Normal FVGs are never traded blindly; you must wait for price to tap the zone and reject.
- **[27:20 - 28:05] Breakaway Gap (BAG) Structural Signature**: Candle 3 breaks and closes beyond Candle 2 with a full candle body.
- **[28:10 - 29:30] BAG Direct Entry Rule**: BAG is a high-momentum continuation signal. Traders can enter directly on the open of Candle 4 without waiting for mitigation.
- **[29:30 - 30:50] BAG Target Mitigation Exception**: If Candle 3 closes directly into a swing high, resistance, or pullback target, direct entry is prohibited; traders must wait for mitigation.
- **[31:15 - 32:30] Overlapping Gap (OG) Definition**: An FVG or BAG that slices through a prior Support or Resistance level.
- **[32:45 - 33:15] OG Zone Refinement Rule**:
  - For Resistance: The OG zone is refined to the portion below the resistance body line.
  - For Support: The OG zone is refined to the portion above the support body line.
- **[33:20 - 34:15] OG Non-Direct Trading Rule**: Do not enter blindly at an OG. It is an institutional reversal POI that requires lower-timeframe internal confirmation.
- **[34:50 - 35:30] OG Proximity Rule**: A gap must intersect or sit directly adjacent to the S/R line to qualify as an Overlapping Gap.
- **[37:30 - 38:55] Manipulation Gap (MG) Trap Rule**: If an FVG has already been partially mitigated, the remaining unmitigated gap is weak and prone to manipulation. Do not trade the remaining gap.
- **[39:10 - 39:52] Liquidity Level Rule inside MG**: The extreme wick/body point reached during the initial mitigation inside a gap is designated as a Liquidity Level. Trade opportunities only occur when this specific level is swept.
