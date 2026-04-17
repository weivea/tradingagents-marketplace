"""Read-only portfolio, position, PnL aggregations."""
from __future__ import annotations

import datetime as dt
import sqlite3

from .accounts import get_cash
from .fees import CURRENCY_BY_MARKET


def get_positions(conn: sqlite3.Connection, account_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM positions WHERE account_id=? ORDER BY market, symbol",
        (account_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_portfolio(
    conn: sqlite3.Connection, account_id: str,
    price_map: dict[str, float] | None = None,
) -> dict:
    cash = get_cash(conn, account_id)
    positions = get_positions(conn, account_id)
    pm = price_map or {}
    for p in positions:
        px = pm.get(p["symbol"], p["avg_cost"])
        p["latest_price"] = px
        p["market_value"] = p["qty"] * px
    return {"account_id": account_id, "cash": cash, "positions": positions}


def get_pending_orders(conn: sqlite3.Connection, account_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM orders WHERE account_id=? AND status='pending' ORDER BY id",
        (account_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_order_history(
    conn: sqlite3.Connection, account_id: str,
    start_date: str | None = None, end_date: str | None = None,
) -> list[dict]:
    q = "SELECT * FROM orders WHERE account_id=?"
    args: list = [account_id]
    if start_date:
        q += " AND submitted_at>=?"
        args.append(start_date)
    if end_date:
        q += " AND submitted_at<=? || 'T23:59:59'"
        args.append(end_date)
    q += " ORDER BY id"
    rows = conn.execute(q, args).fetchall()
    return [dict(r) for r in rows]


def get_pnl(
    conn: sqlite3.Connection, account_id: str,
    date: str | None = None, price_map: dict[str, float] | None = None,
) -> dict:
    q = """SELECT market, side, filled_qty, filled_price, fee
           FROM orders WHERE account_id=? AND status='filled'"""
    args: list = [account_id]
    if date:
        q += " AND substr(filled_at,1,10)=?"
        args.append(date)
    rows = conn.execute(q, args).fetchall()
    realized = {"CNY": 0.0, "HKD": 0.0, "USD": 0.0}
    for r in rows:
        cur = CURRENCY_BY_MARKET[r["market"]]
        sign = 1 if r["side"] == "sell" else -1
        realized[cur] += sign * r["filled_qty"] * r["filled_price"] - r["fee"]

    pm = price_map or {}
    unrealized = {"CNY": 0.0, "HKD": 0.0, "USD": 0.0}
    for p in get_positions(conn, account_id):
        px = pm.get(p["symbol"], p["avg_cost"])
        cur = CURRENCY_BY_MARKET[p["market"]]
        unrealized[cur] += (px - p["avg_cost"]) * p["qty"]

    return {
        "realized_cny": realized["CNY"], "realized_hkd": realized["HKD"],
        "realized_usd": realized["USD"],
        "unrealized_cny": unrealized["CNY"], "unrealized_hkd": unrealized["HKD"],
        "unrealized_usd": unrealized["USD"],
    }
