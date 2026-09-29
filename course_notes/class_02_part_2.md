# Class 2 (Part 2) — Live Chart Application & Practical Gap Execution Models

**Course**: Indian Binary Trading (IBT) / The IBT Trader  
**Topic**: Live Chart Application, The 4 FVG Types & Execution Models  
**Timeframe**: 1-Minute (1m) & 5-Minute (5m) (with multi-timeframe validation up to 1-Month)  
**Platforms**: TradingView (EUR/USD FXCM, BTC/USD Binance, NIFTY 50 NSE, Gold XAU/USD, Apple AAPL)  
**Session Type**: Practical Replay, Student Chart Review & Doubt Clearing  

---

## 1. TOPIC & CONTEXT

- **Specific Concepts Taught**:
  - **SMC Mentorship Class 2 (Day 2 Part 2)**: Live Chart Application & Practical Identification of the 4 Fair Value Gap (FVG) Types.
  - **Dual-Sweep (Outside Bar) Mechanics**: Clarifying how to read internal price movement when a single candle sweeps both the high and low of a preceding Major Candle.
  - **Practical Gap Execution Models**:
    1. **Breakaway Gap (BAG)**: Live chart identification (Candle 3 body break of Candle 2) and direct 4th-candle execution.
    2. **Normal Fair Value Gap (FVG)**: Candle 3 wick-only break of Candle 2, requiring mitigation before execution.
    3. **Liquidity Level (LQ Level)**: Identifying the extreme wick/point formed when an FVG or BAG is mitigated, and trading the subsequent reaction from that level.
    4. **Manipulation Gap (MG)**: Recognizing residual unmitigated gap traps.
    5. **Overlapping Gap (OG)**: Slicing through Support/Resistance body levels with a gap, and refining the zone beneath resistance or above support.
    6. **Inside Candle Error Identification**: Demonstrating how drawing an FVG from an inside candle is an invalid trap, and showing how anchoring to the true Major Candle eliminates the gap.
  - **Fractal Multi-Timeframe & Multi-Asset Proof**: Demonstrating that mechanical gap rules apply identically from 1-Minute scalping up to the 1-Month macro timeframe across Forex, Crypto, Indices, Stocks, and Commodities.
  - **Trading Psychology & Win-Rate Expectations**: Accepting losses, setting realistic 80%–90% win-rate expectations, and previewing Class 3 (Order Blocks).
- **Timeframe(s) and Currency Pairs Displayed**:
  - TradingView Platform:
    - `EUR/USD`: 1-Minute (1m) and 5-Minute (5m) charts (FXCM feed).
    - `BTC/USD` (Bitcoin): 1-Month (1M), 1-Hour (1h), and 1-Minute (1m) charts (Bitstamp / Binance feed).
    - `NIFTY 50 INDEX`: 1-Month (1M) and 1-Hour (1h) charts (NSE feed).
    - Gold (`XAU/USD`): 1-Minute (1m) and 15-Minute (15m) charts (Forex.com feed).
    - Apple Inc. (`AAPL`): 15-Minute (15m) chart (Nasdaq feed).
    - (Search windows also show TSLA, EUR/GBP, and USD/JPY).

---

## 2. VISUAL CANDLESTICK & STRUCTURE RULES

### A. Major vs. Minor / Inside Candles

- **Major Candle Rule for Candle 1 [08:00 - 08:35]**:
  - The mentor draws an FVG on EUR/USD 1m and asks students to evaluate it.
  - **The Rule**: Candle 1 of any gap must be a Major Candle. If a candidate Candle 1 is trapped inside the high and low range of the candle before it, it is an Internal / Inside Candle and cannot be used.
  - **Zone Recalculation**: You must step back to the true preceding Major Candle. If measuring from that Major Candle's high/low overlaps with Candle 3's wick, there is NO GAP (*"Ye overlap kar diya, there is no gap. Idhar koi bhi gap nahi!"*).
- **Bearish Major Candle Identification [08:50 - 09:15]**:
  - In a downtrend, a candle that sweeps the high of the prior candle becomes the Major Candle. Gaps cannot be initiated from minor inside candles underneath it; the zone must be anchored strictly to the confirmed Major Candle.

### B. Valid Pullback / Sweep (Wick-to-Body Relationships)

- **Dual-Sweep (Outside Bar) Mechanics [03:00 - 04:15]**:
  - When a single candle sweeps both the high and low of the major candle:
    - **Bullish Candle Flow**: Opens low, dips to sweep the low, drives up to sweep the high, and closes high.
    - **Bearish Candle Flow**: Opens high, pushes up to sweep the high, drops down to sweep the low, and closes low.
    - The internal price delivery must be mapped based on the candle's open-to-close trajectory to determine which liquidity was taken first.
- **Breakaway Gap (BAG) Body Break Rule [04:55 - 05:40, 07:10 - 07:25]**:
  - Candle 3 must break and close beyond Candle 2's extreme with a full candle body close.
  - A body break indicates aggressive institutional continuation, validating direct entry on the 4th candle without waiting for a pullback.
- **Normal FVG Wick Break Rule [07:15 - 07:45, 09:50 - 10:05]**:
  - If Candle 3 breaks Candle 2's high/low with a wick only (or remains inside Candle 2), it is classified as a standard FVG.
  - Standard FVGs strictly require a price pullback to mitigate the zone before any entry can be taken.
- **Liquidity Level (LQ Level) Rule [06:05 - 06:20, 07:45 - 08:00]**:
  - When an FVG or BAG is mitigated, the absolute extreme wick/tail formed by the mitigating candle inside the gap zone is marked as the **Liquidity Level**.
  - Future sweeps of this liquidity level generate high-probability reaction/reversal moves.

### C. Swing High / Swing Low Lookback Logic

- No Arbitrary Candle Count Lookback: The mentor does not count 3, 5, or 10 bars.
- **Structural Reference Points [06:40 - 07:05, 16:15 - 17:10]**:
  - Support and Resistance lines are anchored to historical candle body closes (recent swing highs/lows).
  - In Overlapping Gaps, the zone is refined to the portion of the gap sitting directly below the resistance body line (in an uptrend) or directly above the support body line (in a downtrend).

---

## 3. ENTRY & EXECUTION HABITS

### Execution Habits Taught on Chart:

1. **Breakaway Gap (BAG) Direct Entry Habit [05:15 - 05:45, 09:40 - 09:55, 14:20 - 14:40]**:
   - **Timing**: The mentor demonstrates entering directly on the exact open of the 4th candle (00s) in the direction of the impulse.
   - Traders do not wait for a pullback or safety margin because BAG represents explosive continuation (*"Fourth candle mein hum kya karna? Directly buy karna. Win ho gaya"*).
   - **Secondary BAG Entry [06:00 - 06:10]**: If price later returns to mitigate the BAG, traders can execute a secondary entry in the trend direction off the mitigation touch.
2. **Normal FVG Entry Habit (Safety Margin / Mitigation Required) [07:30 - 07:45, 09:55 - 10:05]**:
   - Direct entry on the candle open is strictly forbidden.
   - Traders must wait for price to pull back into the gap zone (mitigation) and show rejection before executing.
3. **Overlapping Gap (OG) Entry Habit [06:40 - 07:05, 16:35 - 16:55]**:
   - Traders wait for price to retest the refined gap zone beneath the resistance body line (or above the support body line) before entering in the trend direction.

### Timeframe & Expiry Context:
- The mentor demonstrates that the rules are completely timeframe-independent:
  - On the 1-Minute (1m) chart, each candle is 60 seconds (standard binary/scalping expiration).
  - On the 1-Month (1M) chart, each candle is 30 days.
  - The 4th-candle continuation and mitigation rules work identically across both time horizons.

---

## 4. "DO NOT TRADE" / AVOIDANCE RULES

1. **Avoid Gaps Drawn from Inside Candles [08:00 - 08:35]**:
   - Do not anchor Candle 1 to an inside candle. If tracing back to the preceding Major Candle causes wicks to overlap, skip the setup—there is no valid gap.
2. **Do Not Enter Directly on Normal FVGs Without Mitigation [07:30 - 07:45, 11:55 - 12:05]**:
   - If Candle 3 only broke Candle 2 by a wick, avoid entering at the candle open. If price runs away without mitigating the gap, skip the move (*"Mitigation nahi hua to there is no opportunity"*).
3. **Avoid Trading the Residual Zone of a Manipulation Gap [06:20 - 06:35]**:
   - If an FVG has already been partially tapped, do not treat the remaining unmitigated sliver as a fresh support/resistance zone. In SMC, a retested level is weakened and prone to manipulation. Only monitor the Liquidity Level left by the initial tap.
4. **Avoid Overlapping Gaps Detached from S/R Levels [17:00 - 17:15]**:
   - If a gap is not directly intersecting or tightly hugging the Support/Resistance body level, reject it as a low-probability setup.
5. **The 100% Win-Rate Trap [17:35 - 18:10]**:
   - Avoid emotional trading and unrealistic expectations of perfection. No strategy achieves a 100% win rate. A disciplined implementation of SMC structure and gaps yields a realistic 80%–90% win rate; losses must be accepted as normal business expenses.

---

## 5. TIMESTAMPED RULE SUMMARY

- **[03:00 - 04:15] Dual-Sweep Candle Formation Rule**: How to map internal liquidity flow when an outside candle sweeps both the high and low of a preceding Major Candle based on open-to-close trajectory.
- **[04:55 - 05:25] Live BAG Confirmation Rule**: When Candle 3 closes beyond Candle 2's high with a full body, it is a confirmed Breakaway Gap. Enter directly at the open of Candle 4.
- **[05:30 - 05:50] Consecutive BAG Continuations**: Demonstrating back-to-back BAGs on EUR/USD 1m, each producing immediate single-candle continuation wins.
- **[06:00 - 06:20] BAG Secondary Mitigation & Liquidity Level**: When price eventually returns to tap an earlier BAG, the lowest point of that tap is marked as an institutional Liquidity Level.
- **[06:20 - 06:35] Manipulation Gap Identification**: Marking the residual unmitigated gap left after a partial mitigation as an untradeable Manipulation Gap.
- **[06:40 - 07:05] Overlapping Gap (OG) Live Identification**: Marking a gap that slices through a resistance body line and refining the zone strictly to the space beneath the resistance line.
- **[07:15 - 07:45] Normal FVG Live Identification & Mitigation**: When Candle 3 breaks Candle 2 by wick only, it is a standard FVG; entry is only valid after price pulls back and mitigates the zone.
- **[07:45 - 08:00] FVG Liquidity Level Marking**: The extreme low formed during an FVG mitigation is marked as a Liquidity Level for future sweep entries.
- **[08:00 - 08:35] Inside Candle Invalidation Trap**: Proving why an FVG drawn from an inside candle is invalid because anchoring to the true Major Candle creates wick overlap.
- **[08:50 - 09:15] Bearish Major Candle & Gap Alignment**: Anchoring gaps in a downtrend strictly to the Major Candle whose high was swept.
- **[09:30 - 09:55] Bearish BAG Live Entry**: Demonstrating a bearish BAG where Candle 3 closes below Candle 2 with a body, leading to an immediate 4th-candle downward sell win.
- **[09:55 - 10:15] Bearish FVG Live Mitigation**: Demonstrating a bearish FVG (wick break of Candle 2) requiring price to retrace upward into the gap before resuming downward momentum.
- **[10:20 - 11:40] Macro Timeframe Proof (BTC/USD 1-Month)**: Proving that 30-day candles on Bitcoin respect BAG continuation and FVG mitigation with the exact same precision as 1-minute candles.
- **[11:45 - 12:30] Stock Index Proof (Nifty 50 1-Month & 1-Hour)**: Demonstrating BAG and FVG behavior on Indian equity markets across 1M and 1h charts.
- **[12:35 - 13:35] Scalping Proof (Nifty 50 1-Minute)**: Showing rapid 1-minute scalping setups using BAG and FVG continuations.
- **[14:15 - 15:40] Cross-Asset Demonstration (Gold & Apple 15m)**: Validating FVG mitigation and BAG expansion on XAU/USD and NASDAQ stocks (AAPL).
- **[16:10 - 17:15] Overlapping Gap Confirmation & Proximity Filter**: Demonstrating that an Overlapping Gap must be positioned directly at or very close to an S/R body level to be valid.
- **[17:35 - 18:10] Quantitative Win-Rate Framework**: Establishing the statistical reality of trading (80%–90% realistic win rate; 100% win rate does not exist; accept losses).
- **[18:45 - 19:20] Preparation for Class 3**: Homework assignment directing students to combine Class 1 (Market Structure) with Class 2 (Gaps) in preparation for Order Block integration.
