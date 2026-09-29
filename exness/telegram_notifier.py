"""
exness/telegram_notifier.py — Autonomous Institutional Telegram Dispatcher.
Dispatches real-time trade alerts with attached high-resolution chart snapshots to Telegram.

Features:
1. Asynchronous & Non-Blocking: Dispatches in background daemon threads without blocking MT5 loop.
2. Photo & Document Support: Attaches TradingView dark-mode candlestick charts for every trade.
3. Complete Lifecycle Coverage:
   - Pending Limit Order Placed
   - Order Filled into Position
   - In-Flight Break-Even & Trailing Stop Updates
   - Trade Closed Autopsy (Take Profit / Stop Loss)
"""

import os
import sys
import threading
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, ".env"))

class TelegramNotifier:
    """
    Non-blocking Telegram Bot Dispatcher for Exness MT5 Trading Engine.
    """
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

        if self.enabled:
            print(f"[Telegram] Bot notifier initialized (Chat ID: {self.chat_id}).")
        else:
            print("[Telegram] Bot notifier disabled (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing).")

    def _send_request_async(self, endpoint: str, data: dict, files: Optional[dict] = None):
        """Dispatches an HTTP request to Telegram in a background thread."""
        if not self.enabled or not self.api_url:
            return

        def worker():
            try:
                url = f"{self.api_url}/{endpoint}"
                resp = requests.post(url, data=data, files=files, timeout=15)
                if not resp.json().get("ok"):
                    print(f"[Telegram] Warning: API returned {resp.status_code}: {resp.text}")
            except Exception as e:
                print(f"[Telegram] Error dispatching to Telegram: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def send_message(self, text: str, parse_mode: str = "Markdown"):
        """Sends a text message asynchronously."""
        if not self.enabled:
            return
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        self._send_request_async("sendMessage", payload)

    def send_photo(self, photo_path: str, caption: str, parse_mode: str = "Markdown"):
        """Sends a chart snapshot photo with formatted caption asynchronously."""
        if not self.enabled:
            return

        if not os.path.exists(photo_path):
            # Fall back to text message if photo file missing
            self.send_message(caption, parse_mode=parse_mode)
            return

        def worker():
            try:
                url = f"{self.api_url}/sendPhoto"
                with open(photo_path, "rb") as f:
                    files = {"photo": f}
                    payload = {
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": parse_mode
                    }
                    resp = requests.post(url, data=payload, files=files, timeout=20)
                    if not resp.json().get("ok"):
                        print(f"[Telegram] Photo send warning: {resp.text}")
            except Exception as e:
                print(f"[Telegram] Error sending photo to Telegram: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def notify_order_placed(
        self,
        symbol: str,
        order_type: str,
        ticket: int,
        entry_price: float,
        sl_price: float,
        tp_price: float,
        risk_pips: float,
        rr_ratio: float,
        lot_size: float,
        archetype: str,
        guardian_info: Optional[Dict[str, Any]] = None,
        account_summary: Optional[Dict[str, Any]] = None,
        image_path: Optional[str] = None
    ):
        """Notifies Telegram when a pending limit order is placed on MT5."""
        if not self.enabled:
            return

        direction_emoji = "🟢 BUY" if "BUY" in order_type.upper() else "🔴 SELL"
        time_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        # Guardian info formatting
        g_text = ""
        if guardian_info:
            engine = guardian_info.get("engine", "GUARDIAN")
            risk = guardian_info.get("risk_rating", "NORMAL")
            allow_p = guardian_info.get("allow_probability", 0.5)
            g_text = f"\n🧠 *Guardian*: `{engine}` ({risk}, allow={allow_p:.2f})"

        # Balance info formatting
        bal_text = ""
        if account_summary:
            bal = account_summary.get("balance", 0.0)
            equity = account_summary.get("equity", 0.0)
            bal_text = f"\n💼 *Account*: Balance `${bal:,.2f}` | Equity `${equity:,.2f}`"

        caption = (
            f"🎯 *NEW PENDING ORDER PLACED*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Asset*: `{symbol}` ({order_type})\n"
            f"🎫 *Ticket*: `#{ticket}`\n"
            f"⏰ *Time*: `{time_str}`\n"
            f"🔹 *Entry*: `{entry_price:.5f}`\n"
            f"🛑 *Stop Loss*: `{sl_price:.5f}` ({risk_pips:.1f} pips)\n"
            f"🎯 *Take Profit*: `{tp_price:.5f}` (Target {rr_ratio:.1f}R)\n"
            f"📦 *Volume*: `{lot_size:.2f} Lots`\n"
            f"🏛 *Archetype*: `{archetype}`"
            f"{g_text}"
            f"{bal_text}"
        )

        if image_path and os.path.exists(image_path):
            self.send_photo(image_path, caption)
        else:
            self.send_message(caption)

    def notify_trade_closed(
        self,
        symbol: str,
        deal_ticket: int,
        position_ticket: int,
        outcome: str,
        profit_usd: float,
        entry_price: float,
        exit_price: float,
        comment: str = "",
        account_summary: Optional[Dict[str, Any]] = None,
        image_path: Optional[str] = None
    ):
        """Notifies Telegram when a trade is closed (Take Profit or Stop Loss hit)."""
        if not self.enabled:
            return

        won = outcome.upper() == "WIN" or profit_usd > 0
        status_emoji = "🏆 TAKE PROFIT HIT" if won else "🛑 STOP LOSS HIT"
        pnl_emoji = "🟢" if won else "🔴"
        time_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        bal_text = ""
        if account_summary:
            bal = account_summary.get("balance", 0.0)
            equity = account_summary.get("equity", 0.0)
            bal_text = f"\n💼 *New Balance*: `${bal:,.2f}` | Equity `${equity:,.2f}`"

        caption = (
            f"{status_emoji}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Asset*: `{symbol}`\n"
            f"🎫 *Deal*: `#{deal_ticket}` (Pos `#{position_ticket}`)\n"
            f"⏰ *Time*: `{time_str}`\n"
            f"{pnl_emoji} *Realized PnL*: `${profit_usd:+.2f}`\n"
            f"🔹 *Entry*: `{entry_price:.5f}` ➔ *Exit*: `{exit_price:.5f}`\n"
            f"📝 *Exit Reason*: `{comment}`"
            f"{bal_text}"
        )

        if image_path and os.path.exists(image_path):
            self.send_photo(image_path, caption)
        else:
            self.send_message(caption)

    def notify_break_even_lock(
        self,
        symbol: str,
        ticket: int,
        entry_price: float,
        new_sl: float,
        gain_r: float,
        image_path: Optional[str] = None
    ):
        """Notifies Telegram when In-Flight Co-Pilot locks in Break-Even protection."""
        if not self.enabled:
            return

        time_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        caption = (
            f"🛡 *BREAK-EVEN LOCKED (RISK-FREE)*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Asset*: `{symbol}` (Pos `#{ticket}`)\n"
            f"⏰ *Time*: `{time_str}`\n"
            f"🚀 *Gain*: `+{gain_r:.2f}R` reached\n"
            f"🔒 *New SL*: `{new_sl:.5f}` (Entry: `{entry_price:.5f}`)\n"
            f"✨ Trade is now 100% risk-free."
        )

        if image_path and os.path.exists(image_path):
            self.send_photo(image_path, caption)
        else:
            self.send_message(caption)
