# Class 6 (Part 1) — The Price Action Trap Setup & Live Quotex Execution

**Course**: Indian Binary Trading (IBT) / The IBT Trader  
**Topic**: The Price Action Trap Setup, Retail Traps vs. Institutional Reality & Live Quotex Execution  
**Timeframe**: Exclusively 1-Minute (1m) candles across all charts  
**Platforms**: Quotex (`market-qx.trade` 1m binary), TradingView (`EURUSD`, `USDJPY`, `EURGBP`, `CADJPY`, `BTCUSD`, `ETHUSD`, `AUDJPY`, `GBPUSD` 1m FXCM/Bitstamp)  
**Session Type**: Core Strategy Execution, Retail Trap Engineering & Live Trading  

---

## 1. TOPIC & CONTEXT

- **Specific Concepts Taught**:
  - **Smart Money Concepts (SMC) Core Review**: Break of Structure (BOS), Change of Character (CHOCH), Inducement (IDM), Order Blocks (OB), Order Flow (OF), and Fair Value Gaps (FVG / BAG / BAGI / IFVG / Overlapping Gaps).
  - **The "Price Action Trap" Setup**: How conventional retail price action patterns (Support & Resistance bounces, Bullish Engulfing, Morning Star, Spinning Tops, Retests, and Martingale doubling) are engineered by the market/brokers as liquidity traps.
  - **Institutional vs. Binary/OTC Mechanics**: Real Forex market liquidity (stop-loss orders, hedge funds, banks) versus Binary Options / OTC market (broker algorithmic counter-trading against retail sentiment volume).
  - **Setup Filtering & News Protocol**: Reading economic calendar events, avoiding entry during high-impact news spikes, and checking market conditions before execution.
- **Timeframes & Assets Displayed**:
  - Timeframe: Exclusively 1-minute (1m) candles across all platforms.
  - Trading Platforms & Pairs:
    - Quotex (Binary Options Platform, 1m candles): `EUR/GBP`, `USD/JPY`, `CAD/JPY`, `EUR/USD`, `EUR/JPY`, `GBP/USD`, `GBP/JPY`, `AUD/USD`.
    - TradingView (1m charts): `ETH/USD` (Bitstamp), `BTC/USD` (Bitstamp), `EUR/USD` (OANDA / FXCM), `AUD/JPY` (FXCM), `GBP/USD` (FXCM).

---

## 2. VISUAL CANDLESTICK & STRUCTURE RULES

### A. Major vs. Minor / Inside Candles

- **The Inside Candle Rule [04:15–04:35, 08:15–09:15]**:
  - If a candle's entire range (high and low wicks) remains strictly within the high-to-low range of the preceding candle, it is an Internal / Inside Candle (Minor Candle). The candle that sets the boundary is the Major Candle.
  - **Structure / Pullback Rule**: All candles inside the major candle's range are completely ignored for swing and pullback structure. The mentor boxes 3 internal candles at [08:25] and states: *"High, low, ye teen candle iske andar thi. There is no pullback. Market seedha niche aaya hai."* (Price moved in a straight leg; no valid pullback exists).
  - **Order Block Selection Rule [04:15–04:35]**: If a candidate Order Block candle has subsequent inside candles (e.g., a green candle followed by an inside red candle), you do not isolate the inside candle; you must encompass the entire Major Candle as the valid Order Block zone.
  - **FVG Exception [08:55–09:10]**: Inside candles do not count for structural pullbacks, but they can still be used to define valid Fair Value Gaps (FVG / BAG).

### B. Valid Pullback / Sweep (Wick-to-Body & Valid vs. Fake)

- **Valid Pullback Definition [03:45–04:05, 08:15–09:15]**:
  - A pullback is only valid if a candle's wick explicitly sweeps / takes out the extreme wick high (in a downtrend) or extreme wick low (in an uptrend) of the previous major candle.
  - The extreme point of this first valid pullback constitutes the Inducement (IDM) level.
- **Valid Sweep vs. Fake Sweep / Trap [19:40–20:30, 30:40–31:10, 33:35–33:55]**:
  - **Valid Sweep**: Price extends beyond an established swing point or equal highs/lows solely with a wick (taking out liquidity), reacts immediately, and leaves wick rejection without closing body beyond the level. At [05:00], multiple wick sweeps of a level confirm liquidity absorption and validate a reversal.
  - **Fake Sweep / Trap**:
    1. *Reversal without a sweep*: If price bounces off a nominal support/resistance level without first sweeping a swing high/low, without mitigating an unmitigated Order Block, and without tapping an extreme FVG, the bounce is fake momentum designed to lure retail traders into buying/selling [20:15–20:40, 30:45–31:00].
    2. *Sweep of an invalidated / weak zone*: At [33:35–33:55], price makes a minor wick sweep of a low, but the mentor rejects it because the underlying gap had already been broken out. When the gap structure is compromised, the support level becomes "weak" and will be broken.

### C. Swing High / Swing Low Lookback

- **Candle Lookback Rule [03:45–04:05, 08:20–08:35]**:
  - Swing highs and swing lows are identified dynamically candle-by-candle (1-candle lookback to the immediate preceding major candle's high/low boundary).
  - There is no requirement for fixed multi-candle fractal indicators (e.g., 5-bar Bill Williams fractals). A single candle that breaches the previous candle's wick extreme constitutes the beginning of a pullback swing.

---

## 3. ENTRY & EXECUTION HABITS

- **Entry Timing & Safety Margin [34:48–35:50]**:
  - **Execution on Open**: In the live execution shown at [34:48–34:52] on EUR/GBP (1m chart, **₹50,000 INR position**), the mentor executes a Down (Sell) trade at 00:58 on the Quotex candle countdown—**entering immediately at the candle's open (00s)** without waiting for a price retrace / safety margin.
  - **Trade Outcome [35:48]**: The trade finishes at the exact entry price (0.87451), closing as an ATM (At-The-Money) refund doji (RESULT: +50,000.00 ₹).
  - **Discretionary Rule for Reversal Traps [39:15–39:35]**: When waiting for a rejection entry inside an overhead FVG, the candle must visually show an upper wick reaction/rejection from the gap. If it closes flat inside the gap with zero upper wick reaction, do not enter.
- **Exact Expiration Time**:
  - **Fixed 1-minute expiration** matching the close of the current 1m candle (e.g., entering at 20:42:01 with expiry set to 20:43:00).

---

## 4. "DO NOT TRADE" / AVOIDANCE RULES

1. **Old Order Blocks Post-CHoCH [04:50–05:05]**:
   - *Avoid*: Do not trade an Order Block belonging to the prior trend once a Change of Character (CHOCH) has occurred. Trend bias has flipped; old OBs have a high probability of failing.
2. **S/R Bounces Lacking Liquidity Sweeps [20:15–20:45]**:
   - *Avoid*: Do not take a classical price action bounce (e.g., Hammer/Spinning Top at Support). If the move into support did not sweep a previous swing or tap an OB/FVG, it is an engineered trap; prepare to counter-trade (sell) once price reaches the overhead gap.
3. **Martingale (MTG) Averaging [22:05–22:45]**:
   - *Avoid*: Strictly avoid Martingale / MTG doubling (e.g., $1 \rightarrow \$2 \rightarrow \$4) on supposed pattern retests. Retailers blow accounts doubling down when "strong support" holds for 1 candle before plummeting.
4. **Un-Backtested OTC Assets [26:00–26:45]**:
   - *Avoid*: Never trade OTC pairs blindly. OTC algorithms can alter hourly or daily. Skip any OTC pair unless you have verified on the current session chart that it is actively respecting BAG/FVG mitigation rules.
5. **Mid-Range Between Support & Resistance [32:00–32:35]**:
   - *Avoid*: When price closes at a support level but has immediate overhead resistance with no clear liquidity target or clear indication of who the broker is trapping, skip the trade completely.
6. **Trap Counter-Trading When Liquidity Is Already Swept [32:40–33:05]**:
   - *Avoid*: Do not sell as a "trap" if the swing low / equal lows have already been cleanly swept into a demand FVG. A genuine sweep causes a real rally, not a trap breakdown.
7. **Post-News Extreme Trendy Conditions & Spike Wicks [34:15–34:40]**:
   - *Avoid*: Do not trade right after high-impact news (e.g., 7:30 Economic Calendar news) when charts display erratic multi-candle trends with long erratic wicks/spikes. Slippage and wick volatility cause trade failure regardless of directional accuracy.
8. **Equal Highs / Equal Lows Compression [37:10–38:15]**:
   - *Avoid (USD/JPY)*: Skip when price forms equal highs above and equal lows below without taking out liquidity on either side. Even if price closes in an FVG, the setup is reduced to 50/50 chop.
9. **Zero-Rejection Gap Closes [37:45, 39:15–39:35]**:
   - *Avoid (EUR/JPY)*: Even when the trap direction succeeds, skip entries where the candle closes directly inside the gap without displaying an upper wick reaction/rejection.

---

## 5. TIMESTAMPED RULE SUMMARY

- **[02:00] Break of Structure (BOS) vs. Inducement (IDM)**: A valid structural break requires prior inducement mitigation.
- **[03:50] Inducement Identification**: The extreme of the first valid pullback after creating a new high/low must be marked as the Inducement level.
- **[04:20] Major Candle vs. Inside Candle (OB Rule)**: When selecting an Order Block, if internal candles exist within the primary candle's range, enclose the entire major candle as the OB zone.
- **[04:55] CHoCH Invalidation of OBs**: An Order Block must not be traded after a structural Change of Character has flipped the trend bias.
- **[05:40] Mitigation & Liquidity Sweep Requirement**: An FVG or OB must have remaining unmitigated imbalance; sweeps of previous swing wicks provide high-probability liquidity.
- **[08:25] Mechanical Inside Candle Rule**: Three internal candles bounded within the high and low of a preceding candle do not form a pullback; structure is treated as a single continuous impulse leg.
- **[08:55] FVG vs. Inside Candle Independence**: Inside candles do not count for pullbacks, but the space between candle 1 and candle 3 across inside bars remains a valid Fair Value Gap.
- **[10:10] Forex Data Feed Selection**: FXCM and Forex.com data feeds are preferred over OANDA on TradingView due to minimal gap-up/gap-down broker server anomalies.
- **[17:45] The Price Action Trap Anatomy**: Novice traders (50%) buy at support on a spinning top/hammer; intermediate traders (20%) buy on the subsequent bullish engulfing confirmation.
- **[19:40] The Trap Entry Trigger**: Sell against retail buyers when price enters an unmitigated FVG/BAG above the support bounce, provided the bounce occurred without a prior liquidity sweep.
- **[21:40] Martingale Liquidation Cycle**: Retail MTG buyers doubling at the 50% engulfing retest are trapped as price stalls at support and subsequently breaks cleanly downward.
- **[26:30] OTC Asset Qualification Rule**: Backtest the last few swings on any OTC chart to verify algorithmic compliance with BAG/FVG mitigation before taking trades.
- **[27:25] The Golden Rule**: *"Without liquidity sweep karke aaye toh TRAP."* (Any price action pattern arriving at S/R without a liquidity sweep is an automatic retail trap).
- **[32:15] S/R Pinch Filter**: Discard setups where candle closes at support while squeezed directly under overhead resistance without directional clarity.
- **[33:45] Weak Level Filter**: A level that has broken through an underlying gap is compromised ("weak level"); do not rely on minor wick sweeps at compromised levels.
- **[34:30] News Volatility Filter**: Avoid trading when 1m charts exhibit extreme trends with oversized wicks/spikes following scheduled economic data releases.
- **[34:49] Live Mechanical Execution (EUR/GBP)**: Execution occurs at 00:58 (exact candle open) for a fixed 1-minute expiration down-trade into support liquidity.
- **[37:35] Equal Highs/Lows Rejection**: Do not trade inside an FVG if price leaves unswept equal highs and equal lows (ranging liquidity buildup).
- **[39:20] Gap Rejection Verification**: Reversal entries from an FVG require clear visual wick rejection from the zone; flat closes inside the gap without rejection wicks must be skipped.
