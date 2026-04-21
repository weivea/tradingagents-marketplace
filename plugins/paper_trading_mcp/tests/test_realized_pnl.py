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


from python.accounts import ensure_account
from python.orders import place_order
from python.portfolio import get_positions


def test_buy_fee_capitalized_into_avg_cost(conn):
    """Single buy 100 @ 1500 with fee 37.5 → avg_cost = 1500.375."""
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1500.0)
    pos = get_positions(conn, "neutral")
    assert len(pos) == 1
    assert pos[0]["avg_cost"] == pytest.approx(1500.375)


def test_buy_fee_capitalized_weighted_average(conn):
    """100@1500 fee=37.5, then 100@1400 fee=35.0 → avg_cost = 1450.3625."""
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1500.0)
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1400.0)
    pos = get_positions(conn, "neutral")
    assert pos[0]["avg_cost"] == pytest.approx(1450.3625)
