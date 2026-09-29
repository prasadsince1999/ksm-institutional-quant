"""
convert_histdata.py — Convert downloaded HistData ZIP files to clean 1-minute CSVs.
Extracts the last 30 trading days of real institutional 1m candles for each pair.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import zipfile
import pandas as pd
from datetime import datetime

DATA_DIR = r"c:\Projects\Other\ibt-engine\data"
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "EURGBP", "EURJPY"]

# We want 30 trading days (approx 30,000 to 35,000 1-minute bars per pair)
BARS_30_DAYS = 35_000

print("=" * 65)
print("   CONVERTING HISTDATA TO CLEAN 30-DAY 1-MINUTE DATASETS")
print("=" * 65)

total_bars = 0

for pair in PAIRS:
    zip_path = os.path.join(DATA_DIR, f"DAT_ASCII_{pair}_M1_2024.zip")
    if not os.path.exists(zip_path):
        print(f"  ⚠️ Zip not found: {zip_path}")
        continue

    with zipfile.ZipFile(zip_path) as z:
        csv_name = [name for name in z.namelist() if name.endswith(".csv")][0]
        with z.open(csv_name) as f:
            # Format: 20240101 170000;1.10427;1.10429;1.10425;1.10429;0
            df = pd.read_csv(f, sep=';', header=None, names=["datetime_str", "open", "high", "low", "close", "vol"])
            
            # Take the last 30 trading days (approx 35,000 bars)
            df_30d = df.tail(BARS_30_DAYS).copy()
            
            # Parse datetime: '20241231 165900' -> datetime object
            df_30d["datetime"] = pd.to_datetime(df_30d["datetime_str"], format="%Y%m%d %H%M%S")
            df_30d = df_30d[["datetime", "open", "high", "low", "close"]].set_index("datetime")
            df_30d = df_30d.sort_index()

            out_csv = os.path.join(DATA_DIR, f"{pair}_1min.csv")
            df_30d.to_csv(out_csv)
            
            non_zero = (df_30d["high"] > df_30d["low"]).sum()
            total_bars += len(df_30d)
            start_dt = df_30d.index[0].strftime("%Y-%m-%d")
            end_dt = df_30d.index[-1].strftime("%Y-%m-%d")
            print(f"  ✅ {pair:6s}: {len(df_30d):,} bars ({start_dt} to {end_dt}) | Real Wick Bars: {non_zero:,} | Saved to {pair}_1min.csv")

print("─" * 65)
print(f"  TOTAL 30-DAY BARS CONVERTED: {total_bars:,} candles across 5 pairs")
print("=" * 65)
