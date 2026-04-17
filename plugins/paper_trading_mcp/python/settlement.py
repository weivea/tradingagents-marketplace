"""T+1 settlement and pending-order sweep."""
from __future__ import annotations

import datetime as dt
import sqlite3

from .accounts import adjust_cash
from .fees import calc_fee, CURRENCY_BY_MARKET
from .orders import (
    _limit_triggers, _stop_triggers, _upsert_position_buy,
    _update_position_sell, _get_position, _log,
)


def _settle_t1(conn: sqlite3.Connection, account_id: str) -> int:
    today = dt.date.today().isoformat()
    rows = conn.execute(
        """SELECT id, symbol, market, qty FROM orders
           WHERE account_id=? AND status='filled' AND side='buy'
             AND market='CN' AND settle_date IS NOT NULL AND settle_date<=?""",
        (account_id, today),
    ).fetchall()
    count = 0
    for r in rows:
        conn.execute(
            """UPDATE positions SET available_qty = available_qty + ?
               WHERE account_id=? AND symbol=? AND market=?""",
            (r["qty"], account_id, r["symbol"], r["market"]),
        )
        conn.execute("UPDATE orders SET settle_date=NULL WHERE id=?", (r["id"],))
        _log(conn, account_id, "settle", {"order_id": r["id"]})
        count += 1
    conn.commit()
    return count


def _sweep_pending(conn: sqlite3.Connection, account_id: str,
                   price_map: dict[str, float]) -> int:
    rows = conn.execute(
        "SELECT * FROM orders WHERE account_id=? AND status='pending'",
        (account_id,),
    ).fetchall()
    triggered = 0
    now_iso = dt.datetime.utcnow().isoformat()
    for r in rows:
        px = price_map.get(r["symbol"])
        if px is None:
            continue
        fires = False
        fill_price = None
        if r["order_type"] == "limit" and _limit_triggers(r["side"], r["price"], px):
            fires = True
            fill_price = r["price"]
        elif r["order_type"] == "stop" and _stop_triggers(r["side"], r["price"], px):
            fires = True
            fill_price = px
        if not fires:
            continue

        fee = calc_fee(market=r["market"], side=r["side"], qty=r["qty"], price=fill_price)
        currency = CURRENCY_BY_MARKET[r["market"]]

        if r["side"] == "buy":
            cost = r["qty"] * fill_price + fee
            cash_row = conn.execute(
                "SELECT cash_cny, cash_hkd, cash_usd FROM accounts WHERE account_id=?",
                (account_id,),
            ).fetchone()
            cur_cash = {"CNY": cash_row["cash_cny"], "HKD": cash_row["cash_hkd"],
                       "USD": cash_row["cash_usd"]}[currency]
            if cur_cash < cost:
                conn.execute(
                    "UPDATE orders SET status='rejected' WHERE id=?", (r["id"],)
                )
                _log(conn, account_id, "reject",
                     {"order_id": r["id"], "reason": "INSUFFICIENT_CASH"})
                continue
        else:
            pos = _get_position(conn, account_id, r["symbol"], r["market"])
            if pos is None or pos["available_qty"] < r["qty"]:
                conn.execute(
                    "UPDATE orders SET status='rejected' WHERE id=?", (r["id"],)
                )
                _log(conn, account_id, "reject",
                     {"order_id": r["id"], "reason": "INSUFFICIENT_POSITION"})
                continue

        settle_date = None
        if r["market"] == "CN" and r["side"] == "buy":
            from .orders import _next_business_day
            settle_date = _next_business_day(dt.date.today()).isoformat()

        conn.execute(
            """UPDATE orders SET status='filled', filled_price=?, filled_qty=?,
                   fee=?, filled_at=?, settle_date=? WHERE id=?""",
            (fill_price, r["qty"], fee, now_iso, settle_date, r["id"]),
        )
        if r["side"] == "buy":
            adjust_cash(conn, account_id, currency, -(r["qty"] * fill_price + fee))
            _upsert_position_buy(conn, account_id, r["symbol"], r["market"],
                                 r["qty"], fill_price, currency, settle_date)
        else:
            adjust_cash(conn, account_id, currency, r["qty"] * fill_price - fee)
            _update_position_sell(conn, account_id, r["symbol"], r["market"], r["qty"])

        _log(conn, account_id, "fill",
             {"order_id": r["id"], "symbol": r["symbol"],
              "price": fill_price, "via": "sweep"})
        triggered += 1
    conn.commit()
    return triggered


def tick_pending_orders(
    conn: sqlite3.Connection, *, account_id: str, price_map: dict[str, float]
) -> dict:
    settled = _settle_t1(conn, account_id)
    triggered = _sweep_pending(conn, account_id, price_map or {})
    return {"ok": True, "settled": settled, "triggered": triggered}
