"""
exness/model_watcher.py — Zero-Downtime Model Checkpoint Watcher.
Monitors the neural weights on disk. When a newly certified model checkpoint
is committed by the Sunday training pipeline, it triggers an in-memory hot-swap
without requiring MT5 disconnection or process restart.
"""

import os
import sys
import time
from typing import Callable, Optional

class ModelWatcher:
    """
    Watches a target model weights file for filesystem updates (mtime/size).
    When modified, invokes the registered hot-reload callback.
    """
    def __init__(self, weights_path: str, reload_callback: Optional[Callable] = None):
        self.weights_path = weights_path
        self.reload_callback = reload_callback
        self.last_mtime = self._get_mtime()
        self.last_size = self._get_size()
        self.reloads_count = 0

    def _get_mtime(self) -> float:
        if os.path.exists(self.weights_path):
            try:
                return os.path.getmtime(self.weights_path)
            except OSError:
                return 0.0
        return 0.0

    def _get_size(self) -> int:
        if os.path.exists(self.weights_path):
            try:
                return os.path.getsize(self.weights_path)
            except OSError:
                return 0
        return 0

    def check_for_updates(self) -> bool:
        """
        Polls file status. If modified and non-empty, calls reload_callback.
        Returns True if a hot-reload occurred.
        """
        current_mtime = self._get_mtime()
        current_size = self._get_size()

        # Check if file was modified and has finished writing (size > 0 and stable)
        if current_mtime > self.last_mtime and current_size > 0:
            # Short sleep to prevent reading partial writes
            time.sleep(0.1)
            new_size = self._get_size()
            if new_size == current_size:
                print(f"\n⚡ [ModelWatcher] Detected new model weights on disk ({self.weights_path})!")
                print(f"   Timestamp: {current_mtime} (delta: +{current_mtime - self.last_mtime:.1f}s)")
                self.last_mtime = current_mtime
                self.last_size = current_size
                self.reloads_count += 1

                if self.reload_callback:
                    try:
                        t0 = time.perf_counter()
                        success = self.reload_callback(self.weights_path)
                        dt = (time.perf_counter() - t0) * 1000.0
                        if success:
                            print(f"✅ [ModelWatcher] Zero-downtime hot-reload completed in {dt:.1f}ms! (Total reloads: {self.reloads_count})")
                            return True
                        else:
                            print(f"⚠️ [ModelWatcher] Hot-reload callback returned failure.")
                    except Exception as e:
                        print(f"❌ [ModelWatcher] Error during hot-reload callback: {e}")
                return True

        return False
