# Verification report — FAILED
commit `14436f0` · generated 2026-10-01T06:16:28.245690+00:00 · runtime 173.1s · report hash `a4a9e4dc8389c48d`

| check | status | detail |
|---|---|---|
| sizing_unit_and_property | **PASS** | pip values match closed-form for 10 symbols; 3000 random cases never exceeded 1.25x budget; min-lot refusal works |
| selftest_timezone_detector | **PASS** | aligned clock ratio 4.74 (>=1.4), 5h-shifted ratio 0.99 (<1.4) |
| selftest_fill_audit_math | **PASS** | synthetic fills with a known 0.5 pip stop slippage measured as 0.5000000000010552 pips; verdict FRICTION_WORSE_THAN_MODEL |
| causality_synthetic | **PASS** | 20 random cut points; setups changed when future bars were added in 0 cases |
| selftest_causality_detector_catches_leak | **PASS** | deliberately leaky strategy flagged in 3/60 cuts (must be > 0) |
| null_edge_random_walk | **PASS** | zero-cost martingale random walk, 1655 trades: mean -0.0337R, 95% interval [-0.082, +0.014]. PASS needs upper bound <= +0.05R (engine may not manufacture edge). Lower bound -0.082 shows how conservative the engine is. |
| selftest_null_detector_catches_leak | **PASS** | leaky strategy on random data: t=24.89 over 422 trades (must exceed 3.0) |
| cost_monotonicity | **PASS** | mean R at cost levels 0/1x/2x = -0.100 / -0.241 / -0.355 (must not rise as costs rise) |
| timezone_alignment_real_data | **PASS** | volatility at 07-08 UTC vs 02-03 UTC: EURUSD x1.90, GBPUSD x2.00 (must be >= 1.4; if ~1 the clock is mislabelled and killzones are misaligned) |
| causality_real_GBPJPY | **PASS** | 40 random cut points; setups changed when future bars were added in 0 cases |
| causality_real_USDCAD | **PASS** | 40 random cut points; setups changed when future bars were added in 0 cases |
| claim_gate_RESEARCH | **FAIL** | [RESEARCH] 2000-01-01..2023-12-31 config 4a0143b9c7a40a80: verdict NO_EDGE. base 95% CI [-0.0726, -0.0414] includes <= 0 |

## Allowed claims (copy only from here)
- Frozen config `4a0143b9c7a40a80` (claim_gate_RESEARCH): n=17278, mean -0.0572R, 95% CI [-0.0726, -0.0414], t=-7.47; mild stress -0.0744R; severe stress -0.1023R; 15 variants counted; verdict **NO_EDGE**.
- Net R by pair: {"EURJPY": {"n": 2295, "mean_r": -0.0763, "net_r": -175.1}, "EURUSD": {"n": 2287, "mean_r": -0.1015, "net_r": -232.1}, "GBPJPY": {"n": 3882, "mean_r": -0.0143, "net_r": -55.7}, "GBPUSD": {"n": 4268, "mean_r": -0.0502, "net_r": -214.1}, "USDCAD": {"n": 1975, "mean_r": -0.0698, "net_r": -137.9}, "USDCHF": {"n": 1639, "mean_r": -0.0823, "net_r": -134.8}, "USDJPY": {"n": 932, "mean_r": -0.0415, "net_r": -38.7}}
- Net R by archetype: {"NY_PM_REVERSAL": {"n": 208, "mean_r": 0.0322, "net_r": 6.7}, "SESSION_JUDAS_BREAKOUT": {"n": 3517, "mean_r": -0.0528, "net_r": -185.6}, "SWEEP_REVERSAL": {"n": 2114, "mean_r": -0.0562, "net_r": -118.9}, "TREND_FVG_PULLBACK": {"n": 11439, "mean_r": -0.0604, "net_r": -690.7}}

## NOT verified in this run
- (nothing skipped)

Anything not listed above is unverified. Do not state it as fact.