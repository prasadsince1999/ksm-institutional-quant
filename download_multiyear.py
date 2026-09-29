"""
download_multiyear.py — Automated downloader for 2024, 2025, and 2026 (Jan–Sep) data.
Downloads full year 2025 and all 2026 months for EURUSD, GBPUSD, USDJPY, EURGBP, EURJPY.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import time
import histdata

DATA_DIR = r"c:\Projects\Other\ibt-engine\data"
os.makedirs(DATA_DIR, exist_ok=True)

PAIRS = ["eurusd", "gbpusd", "usdjpy", "eurgbp", "eurjpy"]
MONTHS_2026 = [str(m) for m in range(1, 10)] # Jan to Sep 2026

print("=" * 65)
print("   DOWNLOADING MULTI-YEAR DATA (2025 + 2026)")
print("=" * 65)

# 1. Download 2025 Full Year for all pairs
print("\n--- PHASE 1: Full Year 2025 ---")
for pair in PAIRS:
    target_zip = os.path.join(DATA_DIR, f"DAT_ASCII_{pair.upper()}_M1_2025.zip")
    if os.path.exists(target_zip):
        print(f"  ✓ 2025 {pair.upper()} already exists on disk.")
        continue
    
    # Check if in root dir
    root_zip = f"DAT_ASCII_{pair.upper()}_M1_2025.zip"
    if os.path.exists(root_zip):
        os.rename(root_zip, target_zip)
        print(f"  ✓ Moved {root_zip} to data directory.")
        continue

    print(f"  Downloading 2025 {pair.upper()}...")
    try:
        res = histdata.download_hist_data(year='2025', pair=pair, output_directory=DATA_DIR, verbose=False)
        print(f"  ✅ Saved: {res}")
    except Exception as e:
        print(f"  ❌ Error downloading 2025 {pair.upper()}: {e}")
    time.sleep(0.5)

# 2. Download 2026 Monthly Data (Jan to Sep 2026)
print("\n--- PHASE 2: Year 2026 (Months 1–9) ---")
for pair in PAIRS:
    print(f"\nProcessing 2026 for {pair.upper()}...")
    for m in MONTHS_2026:
        m_str = m.zfill(2)
        target_zip = os.path.join(DATA_DIR, f"DAT_ASCII_{pair.upper()}_M1_2026{m_str}.zip")
        if os.path.exists(target_zip):
            continue

        root_zip = f"DAT_ASCII_{pair.upper()}_M1_2026{m_str}.zip"
        if os.path.exists(root_zip):
            os.rename(root_zip, target_zip)
            continue

        try:
            res = histdata.download_hist_data(year='2026', month=m, pair=pair, output_directory=DATA_DIR, verbose=False)
            print(f"  ✅ {pair.upper()} 2026-{m_str}: {res}")
        except Exception as e:
            print(f"  ⚠️ {pair.upper()} 2026-{m_str} download note: {e}")
        time.sleep(0.3)

print("\n" + "=" * 65)
print("Multi-year download completed! Ready for dataset compilation.")
print("=" * 65)
