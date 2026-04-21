"""SQLite schema and connection helpers for paper_trading_mcp."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".paper_trading" / "paper.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    cash_cny   REAL NOT NULL,
    cash_hkd   REAL NOT NULL,
    cash_usd   REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id            INTEGER PRIMARY KEY,
    account_id    TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    market        TEXT NOT NULL CHECK(market IN ('CN','HK','US')),
    qty           REAL NOT NULL,
    available_qty REAL NOT NULL,
    avg_cost      REAL NOT NULL,
    currency      TEXT NOT NULL,
    UNIQUE(account_id, symbol, market)
);

CREATE TABLE IF NOT EXISTS orders (
    id           INTEGER PRIMARY KEY,
    account_id   TEXT NOT NULL,
    symbol       TEXT NOT NULL,
    market       TEXT NOT NULL CHECK(market IN ('CN','HK','US')),
    side         TEXT NOT NULL CHECK(side IN ('buy','sell')),
    order_type   TEXT NOT NULL CHECK(order_type IN ('market','limit','stop')),
    qty          REAL NOT NULL,
    price        REAL,
    ref_price    REAL,
    status       TEXT NOT NULL CHECK(status IN ('pending','filled','cancelled','rejected')),
    filled_price REAL,
    filled_qty   REAL,
    fee          REAL,
    submitted_at TEXT NOT NULL,
    filled_at    TEXT,
    settle_date  TEXT,
    realized_pnl REAL
);

CREATE TABLE IF NOT EXISTS trade_log (
    id           INTEGER PRIMARY KEY,
    ts           TEXT NOT NULL,
    account_id   TEXT NOT NULL,
    event        TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if missing, then run idempotent column migrations."""
    conn.executescript(SCHEMA)
    # Idempotent migration: add realized_pnl to existing orders tables
    cols = {r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()}
    if "realized_pnl" not in cols:
        conn.execute("ALTER TABLE orders ADD COLUMN realized_pnl REAL")
    conn.commit()


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection, ensuring parent dir + schema exist."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    init_schema(conn)
    return conn
