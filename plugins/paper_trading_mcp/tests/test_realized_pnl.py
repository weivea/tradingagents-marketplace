import sqlite3
import pytest
from python.db import init_schema


def test_migration_adds_realized_pnl_column_idempotently():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    # Simulate an OLD database: create orders table without realized_pnl
    c.executescript("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            account_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            market TEXT NOT NULL,
            side TEXT NOT NULL,
            order_type TEXT NOT NULL,
            qty REAL NOT NULL,
            price REAL,
            ref_price REAL,
            status TEXT NOT NULL,
            filled_price REAL,
            filled_qty REAL,
            fee REAL,
            submitted_at TEXT NOT NULL,
            filled_at TEXT,
            settle_date TEXT
        );
    """)
    # First call should add the column
    init_schema(c)
    cols = {r["name"] for r in c.execute("PRAGMA table_info(orders)").fetchall()}
    assert "realized_pnl" in cols
    # Second call must be idempotent (no error)
    init_schema(c)
    c.close()


def test_fresh_schema_has_realized_pnl():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    init_schema(c)
    cols = {r["name"] for r in c.execute("PRAGMA table_info(orders)").fetchall()}
    assert "realized_pnl" in cols
    c.close()
