"""
compile_multiyear_dataset.py — Compiles 2024, 2025, and 2026 (Jan–Sep) into unified CSVs.
Produces continuous 32.5-month datasets (~1,000,000 candles per pair) in data/{PAIR}_multiyear.csv.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import zipfile
import glob
import pandas as pd
from datetime import datetime

DATA_DIR = r"c:\Projects\Other\ibt-engine\data"
PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "EURGBP", "EURJPY"]

print("=" * 65)
print("   COMPILING MULTI-YEAR CONTINUOUS DATASETS (2024 - 2026)")
print("=" * 65)

total_all_pairs = 0

for pair in PAIRS:
    print(f"\nProcessing {pair}...")
    pair_dfs = []

    # 1. Look for 2024 zip
    zip_2024 = os.path.join(DATA_DIR, f"DAT_ASCII_{pair}_M1_2024.zip")
    if os.path.exists(zip_2024):
        with zipfile.ZipFile(zip_2024) as z:
            csv_name = [n for n in z.namelist() if n.endswith(".csv")][0]
            with z.open(csv_name) as f:
                df24 = pd.read_csv(f, sep=';', header=None, names=["dt_str", "open", "high", "low", "close", "vol"])
                df24["datetime"] = pd.to_datetime(df24["dt_str"], format="%Y%m%d %H%M%S")
                df24 = df24[["datetime", "open", "high", "low", "close"]]
                pair_dfs.append(df24)
                print(f"  ✓ Added 2024: {len(df24):,} bars")

    # 2. Look for 2025 zip
    zip_2025 = os.path.join(DATA_DIR, f"DAT_ASCII_{pair}_M1_2025.zip")
    if os.path.exists(zip_2025):
        with zipfile.ZipFile(zip_2025) as z:
            csv_name = [n for n in z.namelist() if n.endswith(".csv")][0]
            with z.open(csv_name) as f:
                df25 = pd.read_csv(f, sep=';', header=None, names=["dt_str", "open", "high", "low", "close", "vol"])
                df25["datetime"] = pd.to_datetime(df25["dt_str"], format="%Y%m%d %H%M%S")
                df25 = df25[["datetime", "open", "high", "low", "close"]]
                pair_dfs.append(df25)
                print(f"  ✓ Added 2025: {len(df25):,} bars")

    # 3. Look for 2026 monthly zips
    zips_2026 = sorted(glob.glob(os.path.join(DATA_DIR, f"DAT_ASCII_{pair}_M1_2026*.zip")))
    for z_path in zips_2026:
        with zipfile.ZipFile(z_path) as z:
            csv_name = [n for n in z.namelist() if n.endswith(".csv")][0]
            with z.open(csv_name) as f:
                df26m = pd.read_csv(f, sep=';', header=None, names=["dt_str", "open", "high", "low", "close", "vol"])
                df26m["datetime"] = pd.to_datetime(df26m["dt_str"], format="%Y%m%d %H%M%S")
                df26m = df26m[["datetime", "open", "high", "low", "close"]]
                pair_dfs.append(df26m)
                print(f"  ✓ Added {os.path.basename(z_path)}: {len(df26m):,} bars")

    if not pair_dfs:
        print(f"  ⚠️ No data found for {pair}")
        continue

    combined = pd.concat(pair_dfs).drop_duplicates(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)
    combined.set_index("datetime", inplace=True)
    
    out_file = os.path.join(DATA_DIR, f"{pair}_multiyear.csv")
    combined.to_csv(out_file)
    
    total_all_pairs += len(combined)
    s_date = combined.index[0].strftime("%Y-%m-%d")
    e_date = combined.index[-1].strftime("%Y-%m-%d")
    print(f"  🎯 {pair} COMPILED: {len(combined):,} bars ({s_date} to {e_date}) -> {out_file}")

print("\n" + "=" * 65)
print(f"  MULTI-YEAR COMPILATION COMPLETE: {total_all_pairs:,} total candles across 5 pairs")
print("=" * 65)
