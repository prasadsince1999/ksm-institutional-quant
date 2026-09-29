"""
exness/market_awareness.py — Institutional Timing, Economic News, and Session Guardian.
Provides full real-time awareness for the Exness MT5 SMC Trading Engine:
  ✓ Live Economic Calendar (Forex Factory High-Impact Red-Folder News API)
  ✓ Pre-News 30-Minute Blackout Shield (Prevents spread-spike whipsaws)
  ✓ Post-News 15-to-45 Minute Judas Opportunity Window
  ✓ Institutional Session Kill Zones (London Open, NY Overlap)
  ✓ Broker Rollover Spread Freeze (21:00 to 23:00 UTC swap settlement)
  ✓ Friday Weekend Risk Shutdown (Auto-cancels pending orders before market close)
  ✓ Live Dynamic Spread Filter (Blocks entries if broker spread > 2.0 pips)
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import json
import time
import urllib.request
from datetime import datetime, timezone, timedelta

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CALENDAR_CACHE_FILE = os.path.join(ROOT_DIR, "data", "economic_calendar.json")

class EconomicCalendar:
    """
    Fetches, parses, and monitors live high-impact economic news events
    via the public Forex Factory economic calendar feed.
    """
    FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

    def __init__(self, cache_ttl_seconds: int = 3600):
        self.cache_ttl = cache_ttl_seconds
        self.last_fetch_time = 0
        self.events = []
        self._load_or_fetch()

    def _load_or_fetch(self):
        """Loads cached calendar if fresh, otherwise fetches live feed."""
        now = time.time()
        if os.path.exists(CALENDAR_CACHE_FILE):
            try:
                mtime = os.path.getmtime(CALENDAR_CACHE_FILE)
                if now - mtime < self.cache_ttl:
                    with open(CALENDAR_CACHE_FILE, "r", encoding="utf-8") as f:
                        self.events = json.load(f)
                    self.last_fetch_time = mtime
                    return
            except Exception:
                pass

        self._fetch_live()

    def _fetch_live(self):
        """Fetches the latest weekly calendar feed from Forex Factory."""
        try:
            req = urllib.request.Request(
                self.FEED_URL,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            
            # Filter and normalize High & Medium impact events
            normalized = []
            for ev in raw:
                impact = ev.get("impact", "")
                if impact in ["High", "Medium"]:
                    normalized.append({
                        "title": ev.get("title", ""),
                        "country": ev.get("country", ""),
                        "date": ev.get("date", ""),
                        "impact": impact,
                        "forecast": ev.get("forecast", ""),
                        "previous": ev.get("previous", ""),
                    })
            
            self.events = normalized
            self.last_fetch_time = time.time()

            # Save cache
            os.makedirs(os.path.dirname(CALENDAR_CACHE_FILE), exist_ok=True)
            with open(CALENDAR_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.events, f, indent=2)

        except Exception as e:
            # Fallback to existing cache if offline
            if os.path.exists(CALENDAR_CACHE_FILE):
                with open(CALENDAR_CACHE_FILE, "r", encoding="utf-8") as f:
                    self.events = json.load(f)

    def check_news_status(self, symbol: str, now_utc: datetime = None) -> dict:
        """
        Evaluates whether a symbol is currently affected by High-Impact economic news.
        Returns:
          - is_blackout: True if within 30m before or 15m after High-Impact news
          - is_post_news_window: True if 15m to 45m after High-Impact news (Judas window)
          - nearest_event: details of the imminent or recent event
        """
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        # Extract currencies from symbol (e.g., USDJPY -> USD, JPY)
        curr1 = symbol[:3].upper()
        curr2 = symbol[3:6].upper() if len(symbol) >= 6 else ""
        relevant_currencies = {curr1, curr2, "ALL"}

        nearest_imminent = None
        min_time_diff = float("inf")
        is_blackout = False
        is_post_news = False

        for ev in self.events:
            ev_curr = ev.get("country", "").upper()
            if ev_curr not in relevant_currencies and ev_curr != "ALL":
                continue

            # Only High impact triggers strict blackout; Medium is informational
            if ev.get("impact") != "High":
                continue

            try:
                # Format: 2026-09-14T08:30:00-04:00
                ev_time_str = ev.get("date", "")
                ev_time = datetime.fromisoformat(ev_time_str).astimezone(timezone.utc)
            except Exception:
                continue

            diff_seconds = (ev_time - now_utc).total_seconds()
            diff_minutes = diff_seconds / 60.0

            # Pre-news blackout: 30 minutes before release
            # Post-news freeze: 15 minutes after release (0-second spread widening)
            if -15.0 <= diff_minutes <= 30.0:
                is_blackout = True
                nearest_imminent = {
                    **ev,
                    "minutes_to_release": round(diff_minutes, 1),
                    "event_utc": ev_time.strftime("%Y-%m-%d %H:%M UTC")
                }
                break

            # Post-news Judas opportunity window: 15m to 45m after release
            elif -45.0 <= diff_minutes < -15.0:
                is_post_news = True
                nearest_imminent = {
                    **ev,
                    "minutes_since_release": round(abs(diff_minutes), 1),
                    "event_utc": ev_time.strftime("%Y-%m-%d %H:%M UTC")
                }

            # Track nearest future event
            if 0 < diff_minutes < min_time_diff:
                min_time_diff = diff_minutes
                nearest_imminent = {
                    **ev,
                    "minutes_to_release": round(diff_minutes, 1),
                    "event_utc": ev_time.strftime("%Y-%m-%d %H:%M UTC")
                }

        return {
            "symbol": symbol,
            "is_blackout": is_blackout,
            "is_post_news_window": is_post_news,
            "nearest_event": nearest_imminent,
        }


class SessionGuardian:
    """
    Monitors global market session hours, rollover freeze, and weekend risk rules.
    """
    @staticmethod
    def get_market_state(now_utc: datetime = None) -> dict:
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)

        weekday = now_utc.weekday() # 0 = Monday, 4 = Friday, 5 = Saturday, 6 = Sunday
        hour = now_utc.hour
        minute = now_utc.minute

        # ── 1. Weekend Shutdown Check ──
        # Forex closes Friday ~22:00 UTC and reopens Sunday ~21:00 UTC.
        # Strict Risk Rule: Close pending orders and stop new trades Friday after 19:00 UTC.
        if weekday == 4 and hour >= 19:
            return {
                "can_trade": False,
                "session": "FRIDAY_WEEKEND_SHUTDOWN",
                "reason": "Weekend risk defense active (Friday >19:00 UTC). Pending orders must be canceled to avoid Sunday opening gaps.",
                "action": "CANCEL_PENDINGS_HOLD_OFF"
            }
        if weekday in [5, 6]:
            return {
                "can_trade": False,
                "session": "WEEKEND_MARKET_CLOSED",
                "reason": "Interbank Forex market is closed on weekends.",
                "action": "HALT"
            }

        # ── 2. Daily Broker Rollover Freeze (21:00 to 23:00 UTC) ──
        # Exness & interbank brokers settle daily swap contracts at 5:00 PM New York (21:00/22:00 UTC).
        # Liquidity dries up; spreads explode up to 10x (1.0 pip -> 15 pips).
        if hour >= 21 and hour < 23:
            return {
                "can_trade": False,
                "session": "BROKER_ROLLOVER_FREEZE",
                "reason": f"Daily swap rollover active ({hour:02d}:{minute:02d} UTC). Spreads widen dramatically. Trading frozen.",
                "action": "FREEZE_NEW_ENTRIES"
            }

        # ── 3. Asian Session (00:00 to 06:00 UTC) ──
        # Accumulation phase: Used exclusively to record the Asian Range High/Low.
        if hour >= 0 and hour < 7:
            return {
                "can_trade": False,
                "session": "ASIAN_CONSOLIDATION",
                "reason": f"Asian Range Accumulation ({hour:02d}:{minute:02d} UTC). Recording Asian High/Low for London Judas Swings.",
                "action": "MONITOR_ACCUMULATION_ONLY"
            }

        # ── 4. London Open Kill Zone (07:00 to 10:00 UTC) ──
        # Peak manipulation & Judas swing window: Tier-1 Alpha opportunity.
        if hour >= 7 and hour < 11:
            return {
                "can_trade": True,
                "session": "LONDON_OPEN_KILLZONE",
                "reason": f"Prime London Open Kill Zone ({hour:02d}:{minute:02d} UTC). Maximum institutional liquidity & Judas sweeps.",
                "action": "EXECUTE_NORMAL"
            }

        # ── 5. London / New York Overlap (11:00 to 16:00 UTC) ──
        # Maximum daily trading volume, US economic news, macro trend continuation.
        if hour >= 11 and hour < 16:
            return {
                "can_trade": True,
                "session": "LONDON_NY_OVERLAP_KILLZONE",
                "reason": f"Prime London/NY Overlap ({hour:02d}:{minute:02d} UTC). Highest volume expansion window.",
                "action": "EXECUTE_NORMAL"
            }

        # ── 6. Late New York Session (16:00 to 19:00 UTC) ──
        # Trend winding down: Manage open trades, allow high-conviction entries only.
        if hour >= 16 and hour < 19:
            return {
                "can_trade": True,
                "session": "NY_WINDDOWN",
                "reason": f"Late New York Session ({hour:02d}:{minute:02d} UTC). Monitor and manage open positions.",
                "action": "SELECTIVE_ENTRIES"
            }

        # ── 7. Evening Dead Zone (19:00 to 21:00 UTC) ──
        return {
            "can_trade": False,
            "session": "EVENING_DEAD_ZONE",
            "reason": f"Trading day concluded ({hour:02d}:{minute:02d} UTC). Low volume.",
            "action": "HALT_NEW_ENTRIES"
        }


class MarketAwarenessGuardian:
    """
    Unified Master Awareness Controller.
    Combines session timing, economic news calendar, and real-time spread filters.
    """
    def __init__(self, max_spread_pips: float = 2.0):
        self.calendar = EconomicCalendar()
        self.session_guardian = SessionGuardian()
        self.max_spread_pips = max_spread_pips

    def evaluate_trading_permission(self, symbol: str, current_spread_pips: float = None) -> dict:
        """
        Master decision check before placing or holding any limit order.
        Returns whether the agent is permitted to trade, with clear rationale.
        """
        now_utc = datetime.now(timezone.utc)

        # 1. Timing & Session Check
        sess_state = self.session_guardian.get_market_state(now_utc)
        if not sess_state["can_trade"]:
            return {
                "permitted": False,
                "status": "TIMING_BLOCKED",
                "reason": sess_state["reason"],
                "session": sess_state["session"],
                "action": sess_state["action"]
            }

        # 2. Economic News Check
        news_state = self.calendar.check_news_status(symbol, now_utc)
        if news_state["is_blackout"]:
            ev = news_state["nearest_event"]
            ev_title = ev.get("title", "High-Impact News")
            mins = ev.get("minutes_to_release", 0)
            status_desc = f"releasing in {mins} minutes" if mins > 0 else f"released {abs(mins)} minutes ago"
            return {
                "permitted": False,
                "status": "NEWS_BLACKOUT",
                "reason": f"🛑 Pre-News Shield Active: '{ev_title}' ({ev.get('country')}) is {status_desc}. Pending orders halted to protect capital.",
                "session": sess_state["session"],
                "news_event": ev,
                "action": "PAUSE_AND_PROTECT"
            }

        # 3. Spread Check (if live spread provided from broker)
        # Gold has higher natural spread (~2.0 - 4.0 pips = 20-40 cents) than FX pairs (~0.8 - 1.8 pips)
        limit_spread = 5.0 if ("XAU" in symbol.upper() or "GOLD" in symbol.upper()) else self.max_spread_pips
        if current_spread_pips is not None and current_spread_pips > limit_spread:
            return {
                "permitted": False,
                "status": "SPREAD_BLOWOUT",
                "reason": f"⚠️ Broker spread blowout ({current_spread_pips:.1f} pips > max {limit_spread:.1f} pips). Waiting for liquidity.",
                "session": sess_state["session"],
                "action": "WITHHOLD_ORDER"
            }

        # 4. Post-News Judas Opportunity Detection
        is_post_news_opp = news_state["is_post_news_window"]

        return {
            "permitted": True,
            "status": "APPROVED",
            "session": sess_state["session"],
            "is_post_news_window": is_post_news_opp,
            "reason": f"Market timing and liquidity cleared ({sess_state['session']}). No imminent high-impact news."
        }


if __name__ == "__main__":
    print("=" * 75)
    print("   MARKET AWARENESS & TIMING GUARDIAN DIAGNOSTIC TEST")
    print("=" * 75)

    guardian = MarketAwarenessGuardian(max_spread_pips=2.0)
    now = datetime.now(timezone.utc)
    print(f"Current UTC Time : {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Total Cached News: {len(guardian.calendar.events)} events this week")

    for sym in ["USDJPY", "EURJPY"]:
        res = guardian.evaluate_trading_permission(sym, current_spread_pips=1.1)
        print(f"\n[{sym}] Status: {res['status']} | Permitted: {res['permitted']}")
        print(f"       Session: {res['session']}")
        print(f"       Reason : {res['reason']}")
        if "news_event" in res:
            print(f"       News   : {res['news_event']['title']} ({res['news_event']['country']})")
    print("=" * 75)
