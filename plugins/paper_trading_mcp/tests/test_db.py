import sqlite3
from python.db import init_schema


def test_init_schema_creates_all_tables():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [r[0] for r in cur.fetchall()]
    assert tables == ["accounts", "orders", "positions", "trade_log"]


def test_init_schema_is_idempotent():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    init_schema(conn)
    cur = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    assert cur.fetchone()[0] == 4
