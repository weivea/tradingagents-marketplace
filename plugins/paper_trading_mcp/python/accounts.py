"""Account initialization and cash ledger."""
from __future__ import annotations

import datetime as dt
import sqlite3

INITIAL_CNY = 1_000_000.0
INITIAL_HKD = 1_000_000.0
INITIAL_USD = 100_000.0

VALID_CURRENCIES = {"CNY", "HKD", "USD"}


def ensure_account(conn: sqlite3.Connection, account_id: str) -> None:
    """Create account row with initial capital if it doesn't exist."""
    conn.execute(
        """
        INSERT OR IGNORE INTO accounts
            (account_id, cash_cny, cash_hkd, cash_usd, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (account_id, INITIAL_CNY, INITIAL_HKD, INITIAL_USD, dt.datetime.utcnow().isoformat()),
    )
    conn.commit()


def get_cash(conn: sqlite3.Connection, account_id: str) -> dict[str, float]:
    """Return current cash balances {CNY, HKD, USD}. Auto-creates account."""
    ensure_account(conn, account_id)
    row = conn.execute(
        "SELECT cash_cny, cash_hkd, cash_usd FROM accounts WHERE account_id=?",
        (account_id,),
    ).fetchone()
    return {"CNY": row["cash_cny"], "HKD": row["cash_hkd"], "USD": row["cash_usd"]}


def adjust_cash(
    conn: sqlite3.Connection, account_id: str, currency: str, delta: float
) -> None:
    """Add delta (can be negative) to the specified cash column."""
    if currency not in VALID_CURRENCIES:
        raise ValueError(f"Invalid currency: {currency}")
    ensure_account(conn, account_id)
    col = {"CNY": "cash_cny", "HKD": "cash_hkd", "USD": "cash_usd"}[currency]
    conn.execute(
        f"UPDATE accounts SET {col} = {col} + ? WHERE account_id=?",
        (delta, account_id),
    )
    conn.commit()
