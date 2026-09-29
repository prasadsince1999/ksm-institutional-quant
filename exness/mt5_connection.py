"""
exness/mt5_connection.py — Secure MetaTrader 5 Connection & Market Data Layer.
Connects directly to Exness MT5 Demo/Real trading servers.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# Path to environment file
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

def load_env_credentials():
    """Loads MT5 credentials from .env without exposing secrets."""
    creds = {
        "login": None,
        "password": None,
        "server": None,
        "path": None
    }
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "EXNESS_MT5_LOGIN":
                    try: creds["login"] = int(v)
                    except: creds["login"] = v
                elif k == "EXNESS_MT5_PASSWORD":
                    creds["password"] = v
                elif k == "EXNESS_MT5_SERVER":
                    creds["server"] = v
                elif k == "EXNESS_MT5_PATH":
                    creds["path"] = v
    # Fallback to os.environ
    if not creds["login"] and "EXNESS_MT5_LOGIN" in os.environ:
        try: creds["login"] = int(os.environ["EXNESS_MT5_LOGIN"])
        except: creds["login"] = os.environ["EXNESS_MT5_LOGIN"]
    if not creds["password"] and "EXNESS_MT5_PASSWORD" in os.environ:
        creds["password"] = os.environ["EXNESS_MT5_PASSWORD"]
    if not creds["server"] and "EXNESS_MT5_SERVER" in os.environ:
        creds["server"] = os.environ["EXNESS_MT5_SERVER"]
    if not creds["path"] and "EXNESS_MT5_PATH" in os.environ:
        creds["path"] = os.environ["EXNESS_MT5_PATH"]

    return creds

class ExnessMT5:
    def __init__(self):
        self.creds = load_env_credentials()
        self.connected = False
        self.account_info = None

    def connect(self) -> bool:
        """Initializes MT5 and logs into the Exness account."""
        init_kwargs = {}
        if self.creds.get("path"):
            init_kwargs["path"] = self.creds["path"]

        if not mt5.initialize(**init_kwargs):
            err = mt5.last_error()
            print(f"❌ MT5 Initialize Failed: {err}")
            return False

        # If credentials provided, login explicitly
        if self.creds.get("login") and self.creds.get("password") and self.creds.get("server"):
            authorized = mt5.login(
                login=self.creds["login"],
                password=self.creds["password"],
                server=self.creds["server"]
            )
            if not authorized:
                err = mt5.last_error()
                print(f"❌ Exness MT5 Login Failed for account {self.creds['login']}: {err}")
                mt5.shutdown()
                return False
            print(f"✅ Successfully logged into Exness MT5 Server: {self.creds['server']} (Account: {self.creds['login']})")
        else:
            # Connect to currently active terminal account
            info = mt5.account_info()
            if info is not None:
                print(f"✅ Connected to active MT5 Terminal (Account: {info.login}, Server: {info.server})")
            else:
                print("ℹ️ MT5 initialized. No credentials provided in .env yet.")

        self.account_info = mt5.account_info()
        self.connected = True
        return True

    def get_account_summary(self) -> dict:
        """Returns key financial metrics of the Exness account."""
        if not self.connected:
            return None
        info = mt5.account_info()
        if info is None:
            return None
        return {
            "login": info.login,
            "server": info.server,
            "currency": info.currency,
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "leverage": info.leverage,
        }

    def resolve_symbol(self, symbol: str) -> str:
        """Finds the actual symbol name on this broker account (e.g. USDJPY -> USDJPYm)."""
        self.ensure_connection()
        candidates = [symbol, symbol + "m", symbol + ".r", symbol + "z", symbol + "_z"]
        for cand in candidates:
            info = mt5.symbol_info(cand)
            if info is not None:
                mt5.symbol_select(cand, True)
                return cand
        return symbol

    def is_healthy(self) -> bool:
        """Verifies if MT5 IPC connection is actually alive."""
        try:
            t = mt5.terminal_info()
            return t is not None and t.connected
        except:
            return False

    def ensure_connection(self) -> bool:
        if not self.connected or not self.is_healthy():
            self.connected = False
            return self.connect()
        return True

    def fetch_rates(self, symbol: str, timeframe: int = mt5.TIMEFRAME_M15, count: int = 500) -> pd.DataFrame:
        """Fetches historical OHLCV bars from Exness MT5."""
        if not self.ensure_connection():
            return None

        actual_symbol = self.resolve_symbol(symbol)

        # Ensure symbol is selected in MarketWatch
        if not mt5.symbol_select(actual_symbol, True):
            print(f"⚠️ Symbol {actual_symbol} not found or cannot be selected.")
            return None

        rates = mt5.copy_rates_from_pos(actual_symbol, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            err = mt5.last_error()
            print(f"⚠️ Failed to copy rates for {actual_symbol}: {err}")
            return None

        df = pd.DataFrame(rates)
        df["datetime"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("datetime", inplace=True)
        df.rename(columns={"tick_volume": "volume"}, inplace=True)
        return df[["open", "high", "low", "close", "volume"]]

    def get_symbol_details(self, symbol: str) -> dict:
        """Retrieves trading specification for dynamic lot calculation."""
        if not self.connected:
            return None
        actual_symbol = self.resolve_symbol(symbol)
        info = mt5.symbol_info(actual_symbol)
        if info is None:
            return None
        return {
            "symbol": info.name,
            "point": info.point,
            "digits": info.digits,
            "spread": info.spread,
            "trade_contract_size": info.trade_contract_size,
            "volume_min": info.volume_min,
            "volume_max": info.volume_max,
            "volume_step": info.volume_step,
            "ask": info.ask,
            "bid": info.bid,
        }

    def disconnect(self):
        """Clean shutdown of MT5 connection."""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("🔌 MT5 Connection closed.")

if __name__ == "__main__":
    print("Testing Exness MT5 Connection Module...")
    client = ExnessMT5()
    if client.connect():
        summary = client.get_account_summary()
        if summary:
            print(f"Account Balance : ${summary['balance']:,.2f} {summary['currency']}")
            print(f"Account Equity  : ${summary['equity']:,.2f}")
            print(f"Leverage        : 1:{summary['leverage']}")
        client.disconnect()
