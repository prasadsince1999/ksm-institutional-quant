# Class 1 (Part 1) — Market Structure & Liquidity Mapping

**Course**: Indian Binary Trading (IBT) / The IBT Trader  
**Topic**: Smart Money Concepts (SMC) Market Structure Foundation  
**Timeframe**: 1-Minute (1m) chart (with 5-minute higher timeframe bias context)  
**Platforms**: TradingView (EURUSD 1m FXCM) & Exness WebTerminal (Bar Replay)  

---

## 1. TOPIC & CONTEXT

- **Core Concepts Taught**:
  - Smart Money Concepts (SMC) Market Structure & Liquidity Mapping (Class 1 / Day 1).
  - Market structure foundation: Inducement (IDM), Break of Structure (BOS), and Change of Character (CHOCH) / Market Structure Shift (MSS).
  - Candlestick Mechanics: Major Candles vs. Internal (Inside) Candles.
  - Valid Pullback vs. Fake Pullback (mechanics of liquidity sweeps, wick travel, and the Equal Highs/Lows exception).
  - Mechanical confirmation of Higher High (HH), BOS, CHOCH, and trend identification vs. retail price action traps.
- **Timeframes & Currency Pairs Displayed**:
  - Currency Pair: `EUR/USD` (Telegram student charts also display `AUD/USD`; broker terminal shows watchlist tabs for `BTC`, `XAU/USD`, and `ETH`).
  - Timeframe: 1-Minute (1m) chart.
  - Platforms Used:
    - TradingView (`EURUSD · 1 · FXCM`) during the first half for theoretical candle drawings and structure mapping.
    - Exness WebTerminal (`my.exness.com/webterminal`, `EUR/USD 1m`) using the built-in Bar Replay tool for step-by-step market replay.
  - Contextual Note: The mentor explains that while 1-minute liquidity sweeps work for day trading/binary scalping, the exact same structural theory works with even higher reliability on higher timeframes such as the 4-Hour (4H) chart.

---

## 2. VISUAL CANDLESTICK & STRUCTURE RULES

### A. Major vs. Minor / Inside Candles (Filtering Noise)
- **Definition of a Major Candle**: A candle whose high and low have not yet been breached by subsequent price action (both ends are protected).
- **The Inside Candle Rule**: Any candle that remains strictly within the high and low range of the preceding major candle (neither breaking its high nor its low) is an Internal / Inside Candle.
- **Filtering Directive**: Completely ignore inside candles. They are minor noise and are never used to determine market structure or swing points (*"Hum structure mein nahi lenge usko, koi bhi use nahi hota"*).
- **Transfer to New Major Candle**:
  - In an uptrend, as soon as a subsequent candle breaks the high of the current major candle (whether by wick or body), that new candle becomes the new Major Candle.
  - In a downtrend, as soon as a candle breaks the low of the current major candle, it becomes the new Major Candle.

### B. Valid Pullback / Sweep (Wick-to-Body & Mechanics)
- **Uptrend Valid Pullback**:
  1. Identify the current bullish Major Candle.
  2. The low of this Major Candle must be swept or broken by price (can be done with a wick or candle body, by a single candle or across multiple candles).
  3. Price must then form the trend-continuation candle (a green candle in bullish momentum). The lowest point of this sweep leg becomes the Valid Pullback.
- **Downtrend Valid Pullback**:
  1. Identify the bearish Major Candle.
  2. The high of this Major Candle must be swept/broken (by wick or body).
  3. A red candle follows, resuming downward momentum. The highest point of this sweep is the Valid Pullback.
- **Equal Highs (EQH) / Equal Lows (EQL) Liquidity Rule (Special Exception)**:
  - If a candle forms with an Equal High to the preceding green candle (highs match exactly), both candles become Major Candles because equal highs hold concentrated buy-side liquidity.
  - Even if a third candle remains inside the absolute low of the first candle, if it sweeps the low of the equal-high candle, it is confirmed as a Valid Pullback.
  - In a downtrend, equal lows (EQL) function identically: sweeping the high of an equal-low candle constitutes a valid pullback.
- **Valid Sweep vs. Fake Sweep**:
  - **Valid Sweep**: Price takes liquidity from the extreme (high/low) of a confirmed Major Candle or Equal High/Low.
  - **Fake Sweep**: Candlestick wicks/bodies crossing high/lows of internal candles. Because internal candles hold no major swing liquidity, internal crossing is invalid.

### C. Swing High / Swing Low Rules (Lookback & Confirmation)
- The mentor does not use an arbitrary candle count lookback (e.g., 3-bar or 5-bar fractal counts). Identification is purely structural and conditional:
  - **Higher High (HH) Confirmation**: Price must break the previous high with a **Candle Body Close**. If it only pierces with a wick, the HH is not confirmed; the level shifts to the highest point of that wick until a candle closes above it with a full body.
  - **Major Swing High (BOS Level)**: Only confirmed after price pulls back and touches/mitigates the Inducement (IDM). Once IDM is mitigated, the highest peak reached between the initial breakout and the IDM mitigation is marked as the Major Swing High (BOS level).
  - **Major Swing Low (CHOCH Level)**: Located at the absolute lowest point below the inducement that originated the BOS move. It is confirmed as the structural swing low only after the BOS line is broken with a full candle body.

---

## 3. ENTRY & EXECUTION HABITS

- **Execution in this Lecture**:
  - No live or simulated trade entries were clicked in this video. The mentor explicitly instructs students that this is an introductory session dedicated to macro market structure reading:  
    *"Right now, do not trade directly. From here to here we will trade, but how to execute entries we will learn in upcoming classes. Today we are understanding the big picture."* [09:05, 38:15]
- **System Execution Rules (from Pinned Course Framework [03:06])**:
  - **Higher Timeframe Bias**: 5-minute timeframe determines directional bias.
  - **Entry Timeframe**: 1-minute timeframe for precision entry.
  - **Entry Criteria**: Look for internal confirmation (chart flip or gap / manipulation breakout of the first candle).
  - **Safety Margin / Activation**: After activation, the entry candle must sweep the previous candle's high or low before driving toward the target (targeting recent swing high/low).
- **Expiration / Trade Style**: Binary options / scalping context referenced by students; the structural framework operates on 1-minute candles.

---

## 4. "DO NOT TRADE" / AVOIDANCE RULES

1. **Avoid Indicator & Retail Candlestick Patterns [05:00 - 06:15]**:
   - Do not trade blind engulfing patterns, Bollinger Bands, or basic support/resistance lines without understanding whether liquidity has been swept.
2. **Do Not Trade Real Capital Immediately [08:50 - 09:15]**:
   - Students must practice mapping structure on demo/replay for at least 1 month before executing real-money trades.
3. **Skip Internal Candle Swings [14:10 - 14:40 & 19:40 - 19:50]**:
   - Never mark IDM, BOS, or swing points inside an unresolved major candle. If a candle doesn't break the major candle's high or low, completely ignore it.
4. **Avoid Calling Wick Crosses a Breakout (The Shifting Level Rule) [21:10 - 22:35 & 27:30 - 28:00]**:
   - If price pushes past a Higher High or BOS line with only a wick and closes back inside, skip/reject the breakout. This is a sweep, not a break. Shift the level to the wick tip.
5. **The "Aggressive Downtrend" Retail Trap [32:40 - 33:15 & 38:00 - 39:25]**:
   - *The Visual Trap*: Price violently dumps downward with long, consecutive red candles, creating lower lows that look like a massive downtrend to price action traders.
   - *The SMC Mechanical Reality*: Look at the confirmed CHOCH line. Unless price breaks and closes below the CHOCH level with a full candle body, the market is still 100% in an uptrend. Retail sellers entering here get trapped, and price violently reverses upward into a BOS.

---

## 5. TIMESTAMPED RULE SUMMARY

- **[06:15 - 07:10] Rule of Liquidity as Market Fuel**: Market only moves in two ways—to sweep liquidity and then reverse/expand.
- **[11:00 - 11:50] The 3 Essential Elements of Market Structure**: 1. Inducement (IDM), 2. Break of Structure (BOS), 3. Change of Character (CHOCH) / Market Structure Shift (MSS).
- **[12:35 - 14:45] Major vs. Inside Candle Rule**: A major candle's high and low are protected. Subsequent candles within this range are inside candles and must be ignored. Breaking the extreme transfers the major candle designation to the breakout candle.
- **[14:50 - 16:40] Mechanical Valid Pullback Rule**: In an uptrend, price must sweep/break the low of the major candle, followed by continuation candle flow. In a downtrend, it must sweep the high of the major candle.
- **[18:10 - 19:50] Equal Highs/Lows Exception Rule**: Equal highs contain equal liquidity; both candles become major candles. Sweeping the low of the second candle validates the pullback even if inside the first candle's lowest low.
- **[21:10 - 22:45] Higher High (HH) Confirmation Rule**: An uptrend HH is only confirmed when a candle breaks above the swing high with a full candle body.
- **[21:45 - 22:35] Shifting High Rule**: If a candle only wicks above the HH, it is a liquidity sweep. Shift the HH line to the new wick high; repeat until a candle body closes above.
- **[23:15 - 24:30] Inducement (IDM) Creation Rule**: Once HH is broken with a body, the first valid pullback below that HH is marked as the IDM level.
- **[24:35 - 25:15] Shifting IDM Rule**: If price creates a new HH without touching the previously drawn IDM, the old IDM is invalidated and IDM shifts to the first pullback below the newest HH.
- **[25:15 - 25:50] IDM Mitigation Rule**: IDM can be mitigated by either a wick sweep OR a body close—both are valid to confirm mitigation.
- **[26:15 - 27:20] Break of Structure (BOS) Line Rule**: Once IDM is mitigated, draw a horizontal line at the highest candle peak formed between the HH breakout and the IDM touch. This is marked as the BOS level.
- **[27:20 - 28:05] BOS Breakout Rule**: BOS is only confirmed when a candle breaks and closes above the BOS line with a full candle body. A wick cross shifts the BOS line to the wick tip.
- **[28:10 - 29:20] Change of Character (CHOCH) Level Rule**: The absolute lowest point below the IDM leg is designated as the Major Swing Low (CHOCH level). It is locked in once BOS breaks with a candle body.
- **[30:00 - 32:40] Trend Reversal Rule (Bullish to Bearish)**: When price breaks below the confirmed CHOCH line with a candle body close, the trend officially shifts from uptrend to downtrend. The rules invert: IDM forms at the first pullback above the new lower low, BOS marks the swing low, and CHOCH shifts to the highest swing high.
- **[36:00 - 39:48] Practical Chart Walkthrough (EUR/USD 1m Replay)**: Step-by-step application demonstrating how internal swings are bypassed, how IDM is tracked and mitigated, how BOS confirms the swing high, and how the CHOCH level protects traders from fake bearish momentum dumps.
