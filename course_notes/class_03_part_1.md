# Class 3 (Part 1) — Order Block (OB) Mechanics, POIs & Trading Zones

**Course**: Indian Binary Trading (IBT) / The IBT Trader  
**Topic**: Order Block Mechanics, POI Hierarchy, SMT Traps & Trading Zones (Targets)  
**Timeframe**: 1-Minute (1m) chart  
**Platforms**: TradingView (`EURUSD · 1 · FXCM`), Student charts: Gold (`XAU/USD` 1m), Tesla (`TSLA` 1m NASDAQ)  
**Session Type**: Core Theory, Mechanical Criteria & Live Chart Demonstrations  

---

## 1. TOPIC & CONTEXT

- **Specific Concepts Taught**:
  - **Order Block (OB) Mechanics & Criteria**: Core definition, the 3 mandatory conditions for an Order Block, candle color selection (buy before sell / sell before buy), and zone refinement.
  - **No-Gap Wick Order Blocks**: Identifying Order Blocks via wick sweeps when no imbalance/gap exists.
  - **Order Block Classification & Traps**: Decisional Order Block vs. Extreme Order Block vs. SMT (Smart Money Trap).
  - **Points of Interest (POI) & Reversal Points**: Hierarchy of POIs (IDM, OB, Gaps, BOS, CHOCH, Swings).
  - **External vs. Internal Structure**: Macro POIs (External/U-turns) vs. internal trade execution legs (Internal/Road). Minor BOS validation vs. regular swings.
  - **Market Targets & Trading Zones**: Internal structure mapping using Starting Points (Reversal Points 1 & 2) and Stopping Points (Targets 1 & 2), 50% equilibrium filter, and the "look-left" rule for target progression.
- **Timeframe(s) & Assets Displayed**:
  - Primary Active Chart: `EUR/USD`, 1-Minute (1m) timeframe (FXCM feed on TradingView).
  - Student Homework Charts Displayed: Gold vs. US Dollar (`XAU/USD`) on the 1-minute timeframe, and Tesla, Inc. (`TSLA`) on the 1-minute timeframe (NASDAQ).

---

## 2. VISUAL CANDLESTICK & STRUCTURE RULES

### A. Major vs. Minor / Inside Candles

- **Rule to Ignore Inside (Minor) Candles [02:40–03:35]**:
  - A candle is strictly classified as an Inside / Minor candle if both its high and low are completely contained within the high-to-low range of the preceding candle.
  - Because there is no price range expansion or structural breakout (*"iske andar tha, there is no gap"*), inside candles are completely ignored for determining Order Blocks, valid pullbacks, and swing structure.
- **Major Candle Rule [02:45–03:05, 07:55–08:05, 11:25–11:35]**:
  - A candle becomes a Major Candle only when it breaks or sweeps the high or low of the previous candle.
  - Order Blocks must be constructed on a Major candle.

### B. Valid Pullback / Sweep & Wick-to-Body Relationship

- **Visual Wick-to-Body Threshold [13:40–14:15]**:
  - **Fake / Weak Sweep ("Low Probability")**: A candle that merely has a minuscule/tiny wick poking past the previous candle's extreme (*"chhota sa wick"*). Even though it technically pierces the level, it does not demonstrate institutional rejection and has a high failure rate.
  - **Valid Sweep ("High Probability")**: Requires a prominent, large rejection wick (*"wick thoda bada hai... jyada reaction dikh raha hai"*). The large wick visually proves institutional absorption/liquidity sweep and establishes a high-probability wick Order Block.
- **Equal Lows / Pullback Sweep [38:50]**:
  - If equal lows or a level sweep occurs, the candle creating the sweep/equal reaction is marked as the major candle, and a sweep of its high/low validates the pullback.

### C. Swing High / Swing Low Lookback Rule

- **Immediate Preceding Pullback (1-Leg Lookback) [27:10–27:50, 31:30–32:45]**:
  - The mentor identifies internal swing points by looking back to the immediate preceding pullback:
    - **Internal Low**: Established by the reversal candle immediately upon mitigating an Order Block / POI.
    - **Internal High (Target 2)**: Established by identifying the highest point of the immediate preceding pullback leg directly above the reaction zone.
- **Progression Lookback ("Look Left")**:
  - If the immediate pullback high is broken, the algorithm looks back to the next distinct prior pullback swing to the left to define the next target.

---

## 3. ENTRY & EXECUTION HABITS

- **Order Type & Zone Execution**:
  - **No Blind Market Orders**: The mentor explicitly notes that traders place Limit Orders at Order Block zones, but stresses that one must not blindly execute trades just because price touches an Order Block or Extreme FVG.
  - **Confirmation Requirement [30:30–30:50, 33:15–33:30]**: Price must enter the POI / Reversal Zone and show confirmation (a reversal candle / change in internal flow) before taking a trade towards the next target.
  - **Execution Space (Safety Margin)**: Trades are taken inside the Trading Zone after reversal confirmation, targeting the Extreme FVG (Target 1) or the Pullback High (Target 2). Once the target is hit, entries are prohibited.
- **Live Execution & Expiration Timer**:
  - **No Live Orders Placed**: This lecture is a structured theoretical and live chart analysis webinar; the mentor does not execute live market orders on TradingView.
  - **Expiration Time**: No binary options expiration clock is utilized (analysis is conducted entirely on 1-minute SMC forex price action).

---

## 4. "DO NOT TRADE" / AVOIDANCE RULES

1. **Do NOT Pick the 2nd or 3rd Candle for an Order Block [12:20–12:35]**:
   - Only the 1st candle at the gap/reversal point can be selected (or refined to the major candle that broke the range). Selecting the 2nd or 3rd subsequent candle is an error and invalid.
2. **Do NOT Trade Mitigated Wicks for Wick Order Blocks [13:05–13:15, 15:40–15:45]**:
   - If any subsequent candle's wick has already touched or overlapped the sweep wick, that level is mitigated and invalidated.
3. **Avoid Order Blocks with Tiny / Negligible Wicks [13:45–14:05]**:
   - Small wicks that lack visual rejection size represent low probability; skip them in favor of wicks showing strong rejection.
4. **Avoid Smart Money Traps (SMT) Before Inducement [17:45–18:25]**:
   - Any Order Block located before the Inducement (IDM) or sitting directly on the IDM is a trap. Price must take Inducement first before any valid Order Block can be traded.
5. **Avoid Random Intermediate Order Blocks (50/50 OBs) [18:55–19:15]**:
   - Only trade the **Decisional OB** (the first valid pullback past IDM) and the **Extreme OB** (the absolute origin/extreme of the leg). Order blocks in between Decisional and Extreme have only ~50% probability and should be skipped.
6. **Do NOT Trade Before Inducement is Taken [20:25–20:35]**:
   - Never initiate buy or sell trades before price has swept/mitigated the Inducement level.
7. **Do NOT Mark Minor BOS Without Prior OB Mitigation [23:50–24:15]**:
   - If the market breaks a pullback high without first mitigating the Order Block, it is not a minor Break of Structure; it is simply a standard swing. Marking internal IDM/OB from an unmitigated swing will fail.
8. **Avoid Gaps/FVGs Located Below 50% Equilibrium [29:20–29:35]**:
   - In an internal upward move, gaps sitting below the 50% discount/premium equilibrium have low probability. Only prioritize gaps above the 50% level.
9. **STOP TRADING at Target / Stopping Points [30:25–30:50]**:
   - When price reaches Target 1 (Extreme FVG) or Target 2 (Pullback High), all trades in that direction must stop (*"Red Signal / Traffic Light"*). Do not buy or counter-sell blindly at the target; wait for price to break out or establish a new reversal structure.
10. **Avoid Order Blocks Invalidated by Prior Wick Sweeps [36:20–36:50]**:
   - When analyzing EUR/USD, the mentor rejects an Order Block candidate because a prior wick had already swept through it, downgrading it to low probability.
11. **Do NOT Trade Old Order Blocks After a CHoCH [37:15–37:35]**:
   - Order Blocks must only be traded within the existing structure. Once a Change of Character (CHOCH) occurs, the prior trend is invalidated; old Order Blocks will produce weak reactions and fail.
12. **Do NOT Mark Order Blocks with Zero Imbalance Remaining [38:15–38:25]**:
   - If previous candle movements have completely filled/mitigated the gap, the Order Block is dead. There must be an open, unmitigated gap (or unmitigated reaction wick).

---

## 5. TIMESTAMPED RULE SUMMARY

- **[02:40–03:35] Inside Candle Exclusion Rule**: Ignore all candles contained inside the previous candle's high/low range; only range-breaking candles qualify as Major Candles.
- **[06:10–06:30] Core Order Block Definition**: Sell before the last buying candle (bearish); buy before the last selling candle (bullish).
- **[06:35–07:15] Three Mandatory Rules for an Order Block**: Must have (1) a valid pullback, (2) an open gap (Mitigation, Manipulation, or FVG), and (3) a Major candle.
- **[07:50–08:15] Order Block Boundary Marking**: Extend the zone across the entire body and wicks of the identified Major candle.
- **[10:00–10:55] OB Refinement & First Candle Rule**: Always take the 1st candle forming the gap; refine to the major candle that broke the previous low/high.
- **[11:30–12:10] Unmitigated Level Priority**: If the initial candle's wick is already touched, shift refinement to the unmitigated major candle.
- **[12:20–12:35] Second/Third Candle Exclusion Rule**: Never pick the 2nd or 3rd candle of a leg as an Order Block.
- **[12:45–13:30] No-Gap Wick Order Block Rule**: If no gap exists, the Order Block is strictly the reaction candle's wick (green candle wick in uptrend / red candle wick in downtrend).
- **[13:05–13:20] Wick Unmitigated Condition**: The reaction wick must remain completely untouched by subsequent candle wicks.
- **[13:40–14:15] Large Rejection Wick Requirement**: Tiny sweep wicks are low-probability/fake; a valid sweep requires a visually prominent rejection wick.
- **[15:25–16:00] Wick Sweep Mandatory Requirement**: The reaction wick must sweep the previous candle’s low (bullish) or high (bearish).
- **[16:35–17:35] Order Block Location Rule**: Valid OBs must reside strictly below Inducement (uptrend) or strictly above Inducement (downtrend).
- **[17:45–18:25] SMT Avoidance Rule**: Order blocks forming before or right at Inducement are Smart Money Traps—do not trade them.
- **[18:40–19:15] Decisional vs. Extreme Rule**: Trade only Decisional OBs (first pullback after IDM) and Extreme OBs (deepest swing origin); ignore intermediate 50/50 OBs.
- **[19:40–20:45] Point of Interest (POI) Taxonomy**: Hierarchy: (1) IDM, (2) OB, (3) Gaps, (4) BOS, (5) CHOCH, (6) Swings.
- **[20:25–20:35] IDM Prerequisite Rule**: No trades are permitted until Inducement has been swept/mitigated.
- **[21:35–22:50] External vs. Internal Execution Rule**: External levels mark macro POI reversal boundaries; internal levels supply the trading zones and trade continuation legs.
- **[23:15–24:15] Minor BOS Condition**: A breakout only qualifies as a Minor BOS if price has first mitigated the Order Block.
- **[25:10–26:40] Market Targets Definition**: Price operates between Starting Points (Reversal Points) and Stopping Points (Targets).
- **[27:10–28:40] Trading Zone Construction**: Zone is defined between the reaction low at the POI and the immediate preceding pullback high.
- **[28:45–29:35] Target 1 & 50% Equilibrium Filter**: Target 1 is the Extreme FVG of the trading zone; FVGs located above the 50% level carry high probability.
- **[30:00–30:50] Stopping Point ("Red Light") Rule**: Cease trading upon reaching Target 1 or Target 2; never trade at the stopping point itself.
- **[31:00–31:25] Target 2 Definition**: Target 2 is the swing/pullback high.
- **[31:30–32:00] Left-Look Target Progression**: If Target 2 breaks, look left to the next prior pullback to establish the next Target 1 and Target 2.
- **[32:00–33:45] Reversal Points Mapping**: Reversal Point 1 is the Extreme FVG inside the pullback leg; Reversal Point 2 is the swing low.
- **[36:20–36:55] Practical Disqualification of OB**: Eliminating invalid OBs on EUR/USD due to prior sweep/mitigation.
- **[37:10–37:35] CHoCH Invalidation Rule**: Do not look for Order Blocks inside a leg once a CHOCH has broken the trend structure.
- **[38:15–38:35] Fully Mitigated Gap Rejection**: If no open gap remains after candle mitigation, the Order Block is disqualified.
- **[38:50–39:25] Live Market Identification**: Locating equal-low candle sweeps, marking Inducement, and establishing the Decisional Order Block above Inducement on EUR/USD 1m.
