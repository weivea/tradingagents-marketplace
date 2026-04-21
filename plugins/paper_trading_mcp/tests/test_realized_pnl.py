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


def test_sell_fill_writes_realized_pnl_immediate_path(conn):
    """Buy 100@150 (US, fee=1.0) → avg_cost=150.01.
    Sell 100@160 (US, fee=1.0) → realized=(160-150.01)*100 - 1.0 = 998.0."""
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="sell", qty=100, order_type="market", ref_price=160.0)
    sell_row = conn.execute(
        "SELECT realized_pnl, side FROM orders WHERE side='sell' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert sell_row["realized_pnl"] == pytest.approx(998.0)


def test_buy_orders_have_null_realized_pnl(conn):
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=10, order_type="market", ref_price=150.0)
    row = conn.execute(
        "SELECT realized_pnl FROM orders WHERE side='buy' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert row["realized_pnl"] is None


from python.portfolio import get_pnl


def test_get_pnl_realized_zero_when_only_buys(conn):
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1500.0)
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1400.0)
    pnl = get_pnl(conn, "neutral")
    assert pnl["realized_cny"] == 0.0
    assert pnl["realized_hkd"] == 0.0
    assert pnl["realized_usd"] == 0.0


def test_get_pnl_unrealized_uses_fee_capitalized_avg_cost(conn):
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1500.0)
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1400.0)
    # avg_cost = 1450.3625; price 1500 → unrealized = (1500-1450.3625)*200 = 9927.5
    pnl = get_pnl(conn, "neutral", price_map={"600519": 1500.0})
    assert pnl["unrealized_cny"] == pytest.approx(9927.5)


def test_get_pnl_old_sell_rows_excluded(conn):
    """Sell rows with realized_pnl IS NULL (e.g. pre-migration data) must NOT be summed."""
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    # Manually insert an OLD-style sell row with NULL realized_pnl
    conn.execute(
        """INSERT INTO orders (account_id, symbol, market, side, order_type,
            qty, price, ref_price, status, filled_price, filled_qty, fee,
            submitted_at, filled_at, settle_date, realized_pnl)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("neutral", "AAPL", "US", "sell", "market", 50, None, 160.0,
         "filled", 160.0, 50, 1.0, "2026-01-01T00:00:00", "2026-01-01T00:00:00",
         None, None),
    )
    conn.commit()
    pnl = get_pnl(conn, "neutral")
    assert pnl["realized_usd"] == 0.0  # the NULL row was skipped


from python.settlement import tick_pending_orders


def test_sweep_sell_path_writes_realized_pnl(conn):
    """Limit-sell triggered by tick_pending_orders must populate realized_pnl."""
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    # avg_cost = 150.01
    sell = place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                       side="sell", qty=100, order_type="limit",
                       price=160.0, ref_price=150.0)
    assert sell["status"] == "pending"
    tick_pending_orders(conn, account_id="neutral", price_map={"AAPL": 161.0})
    row = conn.execute(
        "SELECT status, realized_pnl FROM orders WHERE id=?", (sell["order_id"],)
    ).fetchone()
    assert row["status"] == "filled"
    # filled at limit_price=160; realized = (160-150.01)*100 - 1.0 = 998.0
    assert row["realized_pnl"] == pytest.approx(998.0)


from python.accounts import INITIAL_USD


def test_equity_identity_after_mixed_sequence(conn):
    """For any series of fills, realized + unrealized must equal change in total equity."""
    ensure_account(conn, "neutral")
    initial_usd = INITIAL_USD

    # Five-step sequence in US market (no T+1 complication):
    # 1) Buy 100 @ 150
    # 2) Buy  50 @ 160
    # 3) Sell 80 @ 170
    # 4) Buy  30 @ 155
    # 5) Sell 50 @ 175
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=50, order_type="market", ref_price=160.0)
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="sell", qty=80, order_type="market", ref_price=170.0)
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=30, order_type="market", ref_price=155.0)
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="sell", qty=50, order_type="market", ref_price=175.0)

    latest_price = 180.0
    price_map = {"AAPL": latest_price}

    from python.accounts import get_cash
    from python.portfolio import get_positions, get_pnl

    cash_now = get_cash(conn, "neutral")["USD"]
    market_value = sum(p["qty"] * latest_price for p in get_positions(conn, "neutral"))
    equity_change = (cash_now + market_value) - initial_usd

    pnl = get_pnl(conn, "neutral", price_map=price_map)
    accounted = pnl["realized_usd"] + pnl["unrealized_usd"]

    assert accounted == pytest.approx(equity_change, abs=1e-6), (
        f"identity broken: equity_change={equity_change}, "
        f"realized={pnl['realized_usd']}, unrealized={pnl['unrealized_usd']}"
    )
