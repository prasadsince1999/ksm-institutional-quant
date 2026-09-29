"""
get_data.py — Download 30 days of 1-minute historical Forex data for IBT Strategy
Downloads maximum available 1-minute candles (30 days rolling) for EURJPY, EURGBP, USDJPY, EURUSD, GBPUSD.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "EURGBP": "EURGBP=X",
    "EURJPY": "EURJPY=X",
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

print("=" * 60)
print("   DOWNLOADING FULL 30 DAYS OF 1-MINUTE FOREX CANDLES")
print("=" * 60)

now = datetime.now()
NUM_CHUNKS = 6
CHUNK_DAYS = 4.8

for pair, ticker in PAIRS.items():
    print(f"\nFetching 30-day 1m data for {pair} ({ticker})...")
    chunks = []
    for i in range(NUM_CHUNKS, -1, -1):
        start = now - timedelta(days=(i + 1) * CHUNK_DAYS)
        end = now - timedelta(days=i * CHUNK_DAYS)
        s_str = start.strftime('%Y-%m-%d')
        e_str = end.strftime('%Y-%m-%d')
        try:
            d = yf.download(ticker, start=s_str, end=e_str, interval="1m", progress=False)
            if not d.empty:
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.get_level_values(0)
                d = d[["Open", "High", "Low", "Close"]].copy()
                d.columns = ["open", "high", "low", "close"]
                chunks.append(d)
        except Exception as e:
            print(f"  ⚠️ Chunk error {s_str} to {e_str}: {e}")

    if not chunks:
        print(f"  ❌ No data retrieved for {pair}")
        continue

    df = pd.concat(chunks)
    df = df[~df.index.duplicated(keep="first")].sort_index()
    df.index.name = "datetime"
    df = df.dropna()

    out_path = os.path.join(DATA_DIR, f"{pair}_1min.csv")
    df.to_csv(out_path)
    print(f"  ✅ Saved {len(df):,} 1-minute candles for {pair} ({df.index[0]} to {df.index[-1]}) to {out_path}")

print("\n" + "=" * 60)
print("30-Day Data download completed! Ready for rigorous backtest.")
print("=" * 60)
