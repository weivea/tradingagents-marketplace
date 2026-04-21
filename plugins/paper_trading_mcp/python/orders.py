"""Order placement, matching, cancellation."""
from __future__ import annotations

import datetime as dt
import json
import sqlite3

from .accounts import ensure_account, adjust_cash, get_cash
from .fees import calc_fee, CURRENCY_BY_MARKET


def _log(conn: sqlite3.Connection, account_id: str, event: str, payload: dict) -> None:
    conn.execute(
        "INSERT INTO trade_log (ts, account_id, event, payload_json) VALUES (?, ?, ?, ?)",
        (dt.datetime.utcnow().isoformat(), account_id, event, json.dumps(payload)),
    )


def _next_business_day(from_dt: dt.date) -> dt.date:
    d = from_dt + dt.timedelta(days=1)
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d


def _get_position(conn: sqlite3.Connection, account_id: str, symbol: str, market: str):
    return conn.execute(
        "SELECT * FROM positions WHERE account_id=? AND symbol=? AND market=?",
        (account_id, symbol, market),
    ).fetchone()


def _upsert_position_buy(
    conn: sqlite3.Connection, account_id: str, symbol: str, market: str,
    qty: float, price: float, currency: str, settle_date: str | None,
    fee: float = 0.0,
) -> None:
    row = _get_position(conn, account_id, symbol, market)
    available_delta = 0.0 if market == "CN" else qty
    # Fee-capitalized avg_cost: cost basis includes commission/stamp.
    if row is None:
        new_cost = (qty * price + fee) / qty
        conn.execute(
            """INSERT INTO positions
               (account_id, symbol, market, qty, available_qty, avg_cost, currency)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (account_id, symbol, market, qty, available_delta, new_cost, currency),
        )
    else:
        new_qty = row["qty"] + qty
        new_avail = row["available_qty"] + available_delta
        new_cost = (row["qty"] * row["avg_cost"] + qty * price + fee) / new_qty
        conn.execute(
            "UPDATE positions SET qty=?, available_qty=?, avg_cost=? WHERE id=?",
            (new_qty, new_avail, new_cost, row["id"]),
        )


def _update_position_sell(
    conn: sqlite3.Connection, account_id: str, symbol: str, market: str, qty: float
) -> None:
    row = _get_position(conn, account_id, symbol, market)
    new_qty = row["qty"] - qty
    new_avail = row["available_qty"] - qty
    if new_qty <= 0:
        conn.execute("DELETE FROM positions WHERE id=?", (row["id"],))
    else:
        conn.execute(
            "UPDATE positions SET qty=?, available_qty=? WHERE id=?",
            (new_qty, new_avail, row["id"]),
        )


def _limit_triggers(side: str, limit_price: float, ref_price: float) -> bool:
    return ref_price <= limit_price if side == "buy" else ref_price >= limit_price


def _stop_triggers(side: str, stop_price: float, ref_price: float) -> bool:
    return ref_price >= stop_price if side == "buy" else ref_price <= stop_price


def place_order(
    conn: sqlite3.Connection, *, account_id: str, symbol: str, market: str,
    side: str, qty: float, order_type: str,
    price: float | None = None, ref_price: float | None = None,
) -> dict:
    ensure_account(conn, account_id)
    now = dt.datetime.utcnow()
    now_iso = now.isoformat()

    if market not in ("CN", "HK", "US"):
        return {"ok": False, "error_code": "INVALID_MARKET", "message": f"bad market {market}"}
    if side not in ("buy", "sell"):
        return {"ok": False, "error_code": "INVALID_SIDE", "message": f"bad side {side}"}
    if order_type not in ("market", "limit", "stop"):
        return {"ok": False, "error_code": "INVALID_ORDER_TYPE", "message": order_type}
    if order_type == "market" and ref_price is None:
        return {"ok": False, "error_code": "MISSING_REF_PRICE",
                "message": "market orders require ref_price"}
    if order_type in ("limit", "stop") and price is None:
        return {"ok": False, "error_code": "MISSING_PRICE",
                "message": f"{order_type} requires price"}
    if qty <= 0:
        return {"ok": False, "error_code": "INVALID_QTY", "message": "qty must be > 0"}

    should_fill = order_type == "market"
    fill_price = ref_price
    if order_type == "limit" and ref_price is not None and _limit_triggers(side, price, ref_price):
        should_fill = True
        fill_price = price
    elif order_type == "stop" and ref_price is not None and _stop_triggers(side, price, ref_price):
        should_fill = True
        fill_price = ref_price

    currency = CURRENCY_BY_MARKET[market]

    if should_fill:
        fee = calc_fee(market=market, side=side, qty=qty, price=fill_price)
        if side == "buy":
            cost = qty * fill_price + fee
            if get_cash(conn, account_id)[currency] < cost:
                return {"ok": False, "error_code": "INSUFFICIENT_CASH",
                        "message": f"need {cost} {currency}"}
        else:
            row = _get_position(conn, account_id, symbol, market)
            if row is None or row["available_qty"] < qty:
                avail = 0 if row is None else row["available_qty"]
                return {"ok": False, "error_code": "INSUFFICIENT_POSITION",
                        "message": f"available={avail}, wanted={qty}"}

        settle_date = None
        if market == "CN" and side == "buy":
            settle_date = _next_business_day(now.date()).isoformat()
        cur = conn.execute(
            """INSERT INTO orders (account_id, symbol, market, side, order_type,
                qty, price, ref_price, status, filled_price, filled_qty, fee,
                submitted_at, filled_at, settle_date)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (account_id, symbol, market, side, order_type, qty, price, ref_price,
             "filled", fill_price, qty, fee, now_iso, now_iso, settle_date),
        )
        order_id = cur.lastrowid

        if side == "buy":
            adjust_cash(conn, account_id, currency, -(qty * fill_price + fee))
            _upsert_position_buy(conn, account_id, symbol, market, qty, fill_price,
                                 currency, settle_date, fee=fee)
        else:
            adjust_cash(conn, account_id, currency, qty * fill_price - fee)
            _update_position_sell(conn, account_id, symbol, market, qty)

        _log(conn, account_id, "fill", {
            "order_id": order_id, "symbol": symbol, "market": market,
            "side": side, "qty": qty, "price": fill_price, "fee": fee,
        })
        conn.commit()
        return {"ok": True, "order_id": order_id, "status": "filled",
                "filled_price": fill_price, "filled_qty": qty, "fee": fee,
                "settle_date": settle_date, "submitted_at": now_iso}

    cur = conn.execute(
        """INSERT INTO orders (account_id, symbol, market, side, order_type,
            qty, price, ref_price, status, submitted_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (account_id, symbol, market, side, order_type, qty, price, ref_price,
         "pending", now_iso),
    )
    order_id = cur.lastrowid
    _log(conn, account_id, "submit", {"order_id": order_id, "order_type": order_type})
    conn.commit()
    return {"ok": True, "order_id": order_id, "status": "pending",
            "submitted_at": now_iso}


def cancel_order(conn: sqlite3.Connection, *, account_id: str, order_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM orders WHERE id=? AND account_id=?", (order_id, account_id),
    ).fetchone()
    if row is None:
        return {"ok": False, "error_code": "ORDER_NOT_FOUND",
                "message": f"no order {order_id} for {account_id}"}
    if row["status"] != "pending":
        return {"ok": False, "error_code": "ORDER_NOT_CANCELLABLE",
                "message": f"status={row['status']}"}
    conn.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
    _log(conn, account_id, "cancel", {"order_id": order_id})
    conn.commit()
    return {"ok": True, "order_id": order_id, "status": "cancelled"}
