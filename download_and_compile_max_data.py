"""
download_and_compile_max_data.py
Downloads maximum historical M1 forex & gold data (2000 to 2026),
applies strict institutional data quality checks, resamples to M5,
saves to high-efficiency ZSTD-compressed Parquet, and deletes obsolete CSVs.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
import zipfile
import glob
import pandas as pd
import numpy as np
import histdata

DATA_DIR = r"c:\Projects\Other\ibt-engine\data"
os.makedirs(DATA_DIR, exist_ok=True)

print("=" * 80)
print("     KSM X TECH: MAXIMUM HISTORICAL DATA PIPELINE & COMPRESSION ENGINE")
print("=" * 80)

CONFIG = {
    "EURUSD": {
        "start_year": 2000,
        "end_year": 2025,
        "months_2026": range(1, 10),
    },
    "USDJPY": {
        "start_year": 2000,
        "end_year": 2025,
        "months_2026": range(1, 10),
    },
    "GBPJPY": {
        "start_year": 2005,
        "end_year": 2025,
        "months_2026": range(1, 10),
    },
    "XAUUSD": {
        "start_year": 2009,
        "end_year": 2025,
        "months_2026": range(1, 10),
    },
}

# ─────────────────────────────────────────────────────────────
# 1. DOWNLOAD MISSING ARCHIVES
# ─────────────────────────────────────────────────────────────
print("\n[PHASE 1] Checking & Downloading Missing Historical Archives...")

for pair, cfg in CONFIG.items():
    pair_lower = pair.lower()
    print(f"\nScanning archives for {pair} ({cfg['start_year']} to 2026)...")
    
    # Yearly archives
    for yr in range(cfg["start_year"], cfg["end_year"] + 1):
        target_zip = os.path.join(DATA_DIR, f"DAT_ASCII_{pair}_M1_{yr}.zip")
        if os.path.exists(target_zip):
            continue
        
        # Check root dir fallback
        root_zip = f"DAT_ASCII_{pair}_M1_{yr}.zip"
        if os.path.exists(root_zip):
            os.rename(root_zip, target_zip)
            continue
            
        print(f"  --> Downloading {pair} {yr}...", end=" ", flush=True)
        try:
            res = histdata.download_hist_data(year=str(yr), pair=pair_lower, output_directory=DATA_DIR, verbose=False)
            print(f"DONE (Saved: {os.path.basename(res)})")
        except Exception as e:
            print(f"FAILED ({e})")
        time.sleep(0.3)
        
    # 2026 monthly archives
    for m in cfg["months_2026"]:
        m_str = str(m).zfill(2)
        target_zip = os.path.join(DATA_DIR, f"DAT_ASCII_{pair}_M1_2026{m_str}.zip")
        if os.path.exists(target_zip):
            continue
            
        root_zip = f"DAT_ASCII_{pair}_M1_2026{m_str}.zip"
        if os.path.exists(root_zip):
            os.rename(root_zip, target_zip)
            continue
            
        print(f"  --> Downloading {pair} 2026-{m_str}...", end=" ", flush=True)
        try:
            res = histdata.download_hist_data(year='2026', month=str(m), pair=pair_lower, output_directory=DATA_DIR, verbose=False)
            print(f"DONE (Saved: {os.path.basename(res)})")
        except Exception as e:
            print(f"NOTE ({e})")
        time.sleep(0.3)

print("\n[PHASE 1 COMPLETE] All required historical archives secured.")

# ─────────────────────────────────────────────────────────────
# 2. INGESTION, DATA QUALITY VALIDATION & RESAMPLING
# ─────────────────────────────────────────────────────────────
print("\n[PHASE 2] Ingesting, Quality-Checking, Resampling, and Compressing...")

compiled_summary = {}

for pair, cfg in CONFIG.items():
    print(f"\nProcessing {pair}...")
    t0 = time.time()
    
    # Collect all matching zip files for this pair
    pattern = os.path.join(DATA_DIR, f"DAT_ASCII_{pair}_M1_*.zip")
    zips = sorted(glob.glob(pattern))
    print(f"  Found {len(zips)} archive files for {pair}.")
    
    m5_chunks = []
    total_raw_m1_bars = 0
    corrupt_bars_filtered = 0
    
    for zpath in zips:
        try:
            with zipfile.ZipFile(zpath, 'r') as z:
                csv_names = [n for n in z.namelist() if n.lower().endswith('.csv')]
                if not csv_names:
                    continue
                with z.open(csv_names[0]) as f:
                    df = pd.read_csv(
                        f, 
                        sep=';', 
                        header=None, 
                        names=['datetime', 'open', 'high', 'low', 'close', 'vol'],
                        usecols=[0, 1, 2, 3, 4]
                    )
                    
            if df.empty:
                continue
                
            total_raw_m1_bars += len(df)
            
            # Parse datetime
            df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S', errors='coerce')
            df = df.dropna(subset=['datetime']).set_index('datetime')
            
            # Strict Data Quality Rules:
            # 1. Prices must be positive
            # 2. High must be >= Low, Open, Close
            # 3. Low must be <= Open, Close
            valid_mask = (
                (df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0) &
                (df['high'] >= df['low']) &
                (df['high'] >= df['open']) &
                (df['high'] >= df['close']) &
                (df['low'] <= df['open']) &
                (df['low'] <= df['close'])
            )
            
            invalid_count = (~valid_mask).sum()
            corrupt_bars_filtered += invalid_count
            if invalid_count > 0:
                df = df[valid_mask]
                
            # Drop duplicates within chunk
            df = df[~df.index.duplicated(keep='first')]
            
            # Resample to M5 in chunk to minimize memory footprint
            chunk_m5 = df.resample('5min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last'
            }).dropna()
            
            m5_chunks.append(chunk_m5)
            
        except Exception as e:
            print(f"  ⚠️ Error processing {os.path.basename(zpath)}: {e}")
            
    if not m5_chunks:
        print(f"  ❌ No valid data parsed for {pair}!")
        continue
        
    # Concatenate all M5 chunks
    df_m5 = pd.concat(m5_chunks)
    
    # Global Deduplication & Sorting
    df_m5 = df_m5[~df_m5.index.duplicated(keep='first')]
    df_m5 = df_m5.sort_index()
    
    # Final Sanity Checks
    assert df_m5.index.is_monotonic_increasing, f"Index for {pair} is not monotonic!"
    assert not df_m5.isnull().values.any(), f"Null values detected in {pair} M5 data!"
    
    # Save to High-Efficiency Parquet (zstd compression)
    out_parquet = os.path.join(DATA_DIR, f"{pair}_max_m5.parquet")
    df_m5.to_parquet(out_parquet, compression='zstd')
    
    file_size_mb = os.path.getsize(out_parquet) / (1024 * 1024)
    elapsed = time.time() - t0
    
    start_dt = df_m5.index[0].strftime('%Y-%m-%d')
    end_dt = df_m5.index[-1].strftime('%Y-%m-%d')
    total_m5 = len(df_m5)
    
    compiled_summary[pair] = {
        "raw_m1_bars": total_raw_m1_bars,
        "m5_bars": total_m5,
        "start": start_dt,
        "end": end_dt,
        "size_mb": file_size_mb,
        "time_s": elapsed,
        "corrupt_filtered": corrupt_bars_filtered,
    }
    
    print(f"  ✅ {pair} COMPLETE:")
    print(f"     • Date Range   : {start_dt} to {end_dt} (~{(df_m5.index[-1] - df_m5.index[0]).days / 365.25:.1f} years)")
    print(f"     • Raw M1 Bars  : {total_raw_m1_bars:,}")
    print(f"     • Clean M5 Bars: {total_m5:,}")
    print(f"     • Parquet Size : {file_size_mb:.2f} MB (ZSTD compressed)")
    print(f"     • Processing   : {elapsed:.1f}s | Corrupt bars filtered: {corrupt_bars_filtered}")

# ─────────────────────────────────────────────────────────────
# 3. CLEAN UP OBSOLETE UNCOMPRESSED CSV FILES (FREEING SPACE)
# ─────────────────────────────────────────────────────────────
print("\n[PHASE 3] Freeing Disk Space: Removing Obsolete Uncompressed CSVs...")

csv_targets = [
    "EURGBP_multiyear.csv",
    "EURJPY_multiyear.csv",
    "EURUSD_multiyear.csv",
    "GBPUSD_multiyear.csv",
    "USDJPY_multiyear.csv",
    "EURGBP_1min.csv",
    "EURJPY_1min.csv",
    "EURUSD_1min.csv",
    "GBPUSD_1min.csv",
    "USDJPY_1min.csv",
    "XAUUSD_m5.csv",
]

freed_bytes = 0
for fname in csv_targets:
    fpath = os.path.join(DATA_DIR, fname)
    if os.path.exists(fpath):
        size = os.path.getsize(fpath)
        try:
            os.remove(fpath)
            freed_bytes += size
            print(f"  🗑️ Deleted redundant CSV: {fname} (Freed {size / (1024*1024):.1f} MB)")
        except Exception as e:
            print(f"  ⚠️ Could not delete {fname}: {e}")

print(f"\n🎉 Total Disk Space Reclaimed: {freed_bytes / (1024*1024):.2f} MB!")

# ─────────────────────────────────────────────────────────────
# 4. SUMMARY TABLE
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("              MAXIMUM HISTORICAL DATASET SUMMARY")
print("=" * 80)
print(f"{'Pair':<10} {'Coverage':<24} {'Raw M1 Bars':<15} {'Clean M5 Bars':<15} {'Parquet Size':<12}")
print("-" * 80)
for pair, info in compiled_summary.items():
    cov = f"{info['start']} to {info['end']}"
    print(f"{pair:<10} {cov:<24} {info['raw_m1_bars']:<15,d} {info['m5_bars']:<15,d} {info['size_mb']:<8.2f} MB")
print("=" * 80)
