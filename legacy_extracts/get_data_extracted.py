"""
get_data.py — Download 1-minute forex data for all pairs
Run once before starting agent_loop.py

Uses yfinance (free, no API key needed).
For higher quality data, export directly from TradingView.
"""

import os
import yfinance as yf
import pandas as pd

PAIRS = {
    "EURJPY": "EURJPY=X",
    "EURGBP": "EURGBP=X",
    "USDJPY": "USDJPY=X",
    "AUDJPY": "AUDJPY=X",
    "CADJPY": "CADJPY=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
}

os.makedirs("./data", exist_ok=True)

for pair, ticker in PAIRS.items():
    print(f"Downloading {pair}...")
    try:
        # 1-minute data, last 7 days (yfinance limit for 1min)
        df = yf.download(ticker, period="7d", interval="1m", auto_adjust=True)
        df = df[["Open", "High", "Low", "Close"]].copy()
        df.columns = ["open", "high", "low", "close"]
        df.index.name = "datetime"
        df.to_csv(f"./data/{pair}_1min.csv")
        print(f"  Saved {len(df)} rows")
    except Exception as e:
        print(f"  Error: {e}")

print("\nDone. For 30-day 1-min data, export from TradingView:")
print("  Chart → Export → CSV → 1 minute timeframe")
print("  Save as: ./data/EURJPY_1min.csv (etc.)")
