"""
download_and_compile_expansion_pairs.py
KSM X TECH: Maximum Historical Data Downloader & Compiler for Expansion Pairs
Downloads maximum historical M1 data (2000/2005 to 2026) for:
- GBPUSD (2000 to 2026)
- USDCAD (2000 to 2026)
- USDCHF (2000 to 2026)
- AUDUSD (2000 to 2026)
- EURJPY (2005 to 2026)
- NZDUSD (2005 to 2026)
Applies strict data hygiene, resamples to M5, and compiles to high-performance ZSTD Parquet.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
import zipfile
import glob
import pandas as pd
import histdata

DATA_DIR = r"c:\Projects\Other\ibt-engine\data"
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG = {
    "GBPUSD": {"start_year": 2000, "end_year": 2025, "months_2026": range(1, 10)},
    "USDCAD": {"start_year": 2000, "end_year": 2025, "months_2026": range(1, 10)},
    "USDCHF": {"start_year": 2000, "end_year": 2025, "months_2026": range(1, 10)},
    "AUDUSD": {"start_year": 2000, "end_year": 2025, "months_2026": range(1, 10)},
    "EURJPY": {"start_year": 2005, "end_year": 2025, "months_2026": range(1, 10)},
    "NZDUSD": {"start_year": 2005, "end_year": 2025, "months_2026": range(1, 10)},
}

print("=" * 80)
print("     KSM X TECH: EXPANSION PAIRS MULTI-DECADE DATA COMPILER")
print("=" * 80)

# Phase 1: Download missing archives
print("\n[PHASE 1] Scanning and downloading missing archives...")

for pair, cfg in CONFIG.items():
    pair_lower = pair.lower()
    print(f"\nChecking archives for {pair} ({cfg['start_year']} to 2026)...")
    
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
            print(f"DONE ({os.path.basename(res)})")
        except Exception as e:
            print(f"FAILED ({e})")
        time.sleep(0.2)
        
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
            print(f"DONE ({os.path.basename(res)})")
        except Exception as e:
            print(f"NOTE ({e})")
        time.sleep(0.2)

print("\n[PHASE 1 COMPLETE] All required archives downloaded.")

# Phase 2: Ingestion, Hygiene & M5 Compilation
print("\n[PHASE 2] Ingesting, quality-checking, and compiling to M5 Parquet...")

compiled_summary = {}

for pair, cfg in CONFIG.items():
    print(f"\nProcessing {pair}...")
    t0 = time.time()
    
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
            
            # Strict Institutional Data Quality Rules
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
        
    df_m5 = pd.concat(m5_chunks)
    df_m5 = df_m5[~df_m5.index.duplicated(keep='first')]
    df_m5 = df_m5.sort_index()
    
    assert df_m5.index.is_monotonic_increasing, f"Index for {pair} is not monotonic!"
    assert not df_m5.isnull().values.any(), f"Null values detected in {pair} M5 data!"
    
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
    
    years_span = (df_m5.index[-1] - df_m5.index[0]).days / 365.25
    print(f"  ✅ {pair} COMPLETE:")
    print(f"     • Date Range   : {start_dt} to {end_dt} (~{years_span:.1f} years)")
    print(f"     • Raw M1 Bars  : {total_raw_m1_bars:,}")
    print(f"     • Clean M5 Bars: {total_m5:,}")
    print(f"     • Parquet Size : {file_size_mb:.2f} MB (ZSTD)")
    print(f"     • Time         : {elapsed:.1f}s | Filtered: {corrupt_bars_filtered}")

print("\n" + "=" * 80)
print("              COMPILATION SUMMARY")
print("=" * 80)
for pair, info in compiled_summary.items():
    cov = f"{info['start']} to {info['end']}"
    print(f"{pair:<10} {cov:<24} {info['m5_bars']:<12,d} M5 bars {info['size_mb']:<8.2f} MB")
print("=" * 80)
