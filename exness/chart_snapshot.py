"""
exness/chart_snapshot.py — Autonomous Institutional Chart Snapshot Engine.
Renders high-resolution, TradingView dark-mode candlestick chart photos for every live trade event:
1. Pending Limit Order Placed
2. Preempted Order Cancelled (Target Preempted)
3. Order Filled into Active Market Position
4. In-Flight Break-Even Lock / Trailing Stop Update
5. Trade Closed (Take Profit / Stop Loss Autopsy)

Saves clean PNG images in reports/trade_snapshots/ and catalogs metadata in snapshot_index.json.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import matplotlib
matplotlib.use('Agg')
import json
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SNAPSHOT_DIR = os.path.join(ROOT_DIR, "reports", "trade_snapshots")
INDEX_FILE = os.path.join(SNAPSHOT_DIR, "snapshot_index.json")

class ChartSnapshotEngine:
    """
    Asynchronous, non-blocking chart rendering engine for Exness MT5 trades.
    Uses mplfinance and matplotlib to generate institutional-grade dark charts.
    """
    def __init__(self, output_dir: str = SNAPSHOT_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self._init_index()

    def _init_index(self):
        if not os.path.exists(INDEX_FILE):
            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    def _record_index(self, entry: Dict[str, Any]):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                index = json.load(f)
            index.append(entry)
            with open(INDEX_FILE, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ChartSnapshot] Failed to update index: {e}")

    def capture_async(self, symbol: str, event_type: str, ticket: int,
                      entry_price: float = 0.0, sl_price: Optional[float] = None,
                      tp_price: Optional[float] = None, exit_price: Optional[float] = None,
                      extra_info: Optional[Dict[str, Any]] = None,
                      callback: Optional[Any] = None, **kwargs):
        """Dispatches chart generation to a background thread to never block MT5 execution."""
        def worker():
            path = self.capture_sync(symbol, event_type, ticket, entry_price, sl_price, tp_price, exit_price, extra_info)
            if callback and path:
                try:
                    callback(path)
                except Exception as e:
                    print(f"[ChartSnapshot] Callback error: {e}")

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def capture_sync(self, symbol: str, event_type: str, ticket: int,
                     entry_price: float = 0.0, sl_price: Optional[float] = None,
                     tp_price: Optional[float] = None, exit_price: Optional[float] = None,
                     extra_info: Optional[Dict[str, Any]] = None, **kwargs) -> Optional[str]:
        """Synchronously renders and saves a trade event chart snapshot."""
        try:
            import MetaTrader5 as mt5
            import pandas as pd
            import mplfinance as mpf

            # Ensure MT5 is initialized in this thread
            if not mt5.initialize():
                return None

            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
            if rates is None or len(rates) == 0:
                return None

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'tick_volume': 'Volume'}, inplace=True)

            timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp_str}_{symbol}_{event_type}_T{ticket}.png"
            file_path = os.path.join(self.output_dir, filename)

            # Institutional Dark Theme (#131722)
            mc = mpf.make_marketcolors(
                up='#26a69a', down='#ef5350',
                edge={'up': '#26a69a', 'down': '#ef5350'},
                wick={'up': '#26a69a', 'down': '#ef5350'},
                volume='inherit'
            )
            s = mpf.make_mpf_style(
                base_mpf_style='nightclouds',
                marketcolors=mc,
                gridcolor='#2b2b36',
                gridstyle='--',
                facecolor='#131722',
                figcolor='#131722'
            )

            hlines_vals = []
            hlines_colors = []
            if entry_price and entry_price > 0:
                hlines_vals.append(entry_price)
                hlines_colors.append('#00e5ff')  # Cyan = Entry
            if sl_price and sl_price > 0:
                hlines_vals.append(sl_price)
                hlines_colors.append('#ff1744')  # Red = Stop Loss
            if tp_price and tp_price > 0:
                hlines_vals.append(tp_price)
                hlines_colors.append('#00e676')  # Green = Take Profit
            if exit_price and exit_price > 0:
                hlines_vals.append(exit_price)
                hlines_colors.append('#ffd600')  # Gold = Closed/Exit Deal

            hlines = dict(
                hlines=hlines_vals,
                colors=hlines_colors,
                linestyle=['--', '--', '--', '--'][:len(hlines_vals)],
                linewidths=[1.8, 1.8, 2.0, 2.0][:len(hlines_vals)]
            ) if hlines_vals else None

            extra = extra_info or {}
            lots = extra.get("lots", 0.0)
            archetype = extra.get("archetype", "SMC_STRUCTURE")
            result_str = extra.get("result", "")
            title_text = f"\n{symbol} M5 | {event_type} | TICKET #{ticket} {result_str}\nArchetype: {archetype} | Lots: {lots}"

            fig, axlist = mpf.plot(
                df,
                type='candle',
                style=s,
                hlines=hlines,
                title=title_text,
                volume=False,
                figsize=(12, 6),
                returnfig=True
            )

            ax = axlist[0]
            n = len(df)

            if entry_price and entry_price > 0:
                ax.text(n - 1, entry_price, f"  ENTRY: {entry_price}", color='#00e5ff', fontsize=10, verticalalignment='center', fontweight='bold')
            if sl_price and sl_price > 0:
                ax.text(n - 1, sl_price, f"  SL: {sl_price}", color='#ff1744', fontsize=10, verticalalignment='center', fontweight='bold')
            if tp_price and tp_price > 0:
                ax.text(n - 1, tp_price, f"  TP: {tp_price}", color='#00e676', fontsize=10, verticalalignment='center', fontweight='bold')
            if exit_price and exit_price > 0:
                ax.text(n - 1, exit_price, f"  EXIT: {exit_price}", color='#ffd600', fontsize=10, verticalalignment='center', fontweight='bold')

            if entry_price and tp_price and entry_price > 0 and tp_price > 0:
                ax.axhspan(min(entry_price, tp_price), max(entry_price, tp_price), color='#00e676', alpha=0.10)
            if entry_price and sl_price and entry_price > 0 and sl_price > 0:
                ax.axhspan(min(entry_price, sl_price), max(entry_price, sl_price), color='#ff1744', alpha=0.08)

            fig.savefig(file_path, dpi=120, bbox_inches='tight')

            # Record in index
            self._record_index({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "event_type": event_type,
                "ticket": ticket,
                "entry": entry_price,
                "sl": sl_price,
                "tp": tp_price,
                "filename": filename,
                "path": file_path,
                "extra": extra
            })

            print(f"📸 [ChartSnapshot] Generated trade photo: {filename}")
            return file_path
        except Exception as e:
            print(f"[ChartSnapshot] Error rendering chart: {e}")
            return None
