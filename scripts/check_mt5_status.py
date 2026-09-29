import MetaTrader5 as mt5
from datetime import datetime, timezone

if not mt5.initialize():
    print("MT5 initialize failed:", mt5.last_error())
    exit(1)

info = mt5.account_info()
if info is not None:
    print(f"Account: {info.login}")
    print(f"Balance: {info.balance:.2f}")
    print(f"Equity: {info.equity:.2f}")
    print(f"Margin: {info.margin:.2f}")
    print(f"Free Margin: {info.margin_free:.2f}")
else:
    print("Failed to get account info")

positions = mt5.positions_get()
print(f"\nOpen positions count: {len(positions) if positions else 0}")
if positions:
    for p in positions:
        pos_type = "BUY" if p.type == 0 else "SELL"
        print(f"  Pos #{p.ticket} | {p.symbol} {pos_type} | Vol: {p.volume} | Open: {p.price_open} | Cur: {p.price_current} | SL: {p.sl} | TP: {p.tp} | Profit: ${p.profit:.2f}")

now = datetime.now(timezone.utc)
today_start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
deals = mt5.history_deals_get(today_start, now)
print(f"\nDeals today ({today_start.date()}): {len(deals) if deals else 0}")
if deals:
    for d in deals:
        print(f"  Deal #{d.ticket} | Order: {d.order} | Symbol: {d.symbol} | Type: {d.type} | Entry: {d.entry} | Vol: {d.volume} | Price: {d.price} | Profit: ${d.profit:.2f} | Comment: {d.comment}")

orders = mt5.orders_get()
print(f"\nPending orders count: {len(orders) if orders else 0}")
if orders:
    for o in orders:
        print(f"  Order #{o.ticket} | Symbol: {o.symbol} | Type: {o.type} | Vol: {o.volume_current} | Price: {o.price_open} | SL: {o.sl} | TP: {o.tp}")

mt5.shutdown()
