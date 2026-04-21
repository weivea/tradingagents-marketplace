# Paper Trading — Realized PnL Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `get_pnl.realized_*` so it reports true realized profit-and-loss instead of net cash flow from fills.

**Architecture:** Capitalize buy fees into `positions.avg_cost`; on every sell fill write `realized_pnl = (fill_price - avg_cost_at_sell) * qty - sell_fee` onto the order row; change `get_pnl` to `SUM(realized_pnl)` over filled sells. Schema migration adds one nullable column idempotently.

**Tech Stack:** Python 3.10+, sqlite3, pytest (run via `uv`). Spec: `docs/superpowers/specs/2026-04-21-paper-trading-realized-pnl-fix-design.md`.

## File Map

- `plugins/paper_trading_mcp/python/db.py` — add column to SCHEMA + idempotent ALTER in `init_schema`
- `plugins/paper_trading_mcp/python/orders.py` — `_upsert_position_buy` takes `fee`; sell fill path writes `realized_pnl`; `place_order` INSERT includes `realized_pnl`
- `plugins/paper_trading_mcp/python/settlement.py` — sweep sell path writes `realized_pnl`; sweep buy path passes `fee` to upsert
- `plugins/paper_trading_mcp/python/portfolio.py` — rewrite `get_pnl` to use `SUM(realized_pnl)`
- `plugins/paper_trading_mcp/tests/test_realized_pnl.py` — **new**, 7 tests
- `plugins/paper_trading_mcp/tests/test_portfolio.py` — adjust 2 existing assertions to match fee-capitalized avg_cost
- `plugins/paper_trading_mcp/tests/test_orders.py` — no change expected; covered by regression run

All commands assume cwd = `plugins/paper_trading_mcp/`.

---

## Task 1: Add `realized_pnl` column with idempotent migration

**Files:**
- Modify: `python/db.py`
- Test: `tests/test_realized_pnl.py` (new)

- [ ] **Step 1: Create test file with the migration test**

Create `tests/test_realized_pnl.py` with:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project . pytest tests/test_realized_pnl.py -v`
Expected: FAIL — `realized_pnl` not in columns.

- [ ] **Step 3: Update SCHEMA constant in `python/db.py`**

In the `orders` `CREATE TABLE` block (lines 31–48), add `realized_pnl REAL` as the last column before the closing `);`. The full new orders block:

```python
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
```

- [ ] **Step 4: Add idempotent ALTER in `init_schema`**

Replace the body of `init_schema` in `python/db.py` with:

```python
def init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if missing, then run idempotent column migrations."""
    conn.executescript(SCHEMA)
    # Idempotent migration: add realized_pnl to existing orders tables
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(orders)").fetchall()}
    if "realized_pnl" not in cols:
        conn.execute("ALTER TABLE orders ADD COLUMN realized_pnl REAL")
    conn.commit()
```

- [ ] **Step 5: Run the migration tests, expect PASS**

Run: `uv run --project . pytest tests/test_realized_pnl.py -v`
Expected: both tests PASS.

- [ ] **Step 6: Run the full suite to confirm no regressions**

Run: `uv run --project . pytest -v`
Expected: all existing tests still PASS (`test_pnl_realized_after_round_trip` may keep passing because the buggy formula coincidentally hits 998.0; that gets fixed in Task 2/3).

- [ ] **Step 7: Commit**

```bash
git add plugins/paper_trading_mcp/python/db.py plugins/paper_trading_mcp/tests/test_realized_pnl.py
git commit -m "feat(paper_trading_mcp): add orders.realized_pnl column with idempotent migration"
```

---

## Task 2: Capitalize buy fee into `avg_cost`

**Files:**
- Modify: `python/orders.py` (`_upsert_position_buy`, two call sites)
- Modify: `python/settlement.py` (sweep buy call site)
- Test: `tests/test_realized_pnl.py` (append)

- [ ] **Step 1: Append failing test for fee capitalization**

Append to `tests/test_realized_pnl.py`:

```python
from python.accounts import ensure_account
from python.orders import place_order
from python.portfolio import get_positions


def test_buy_fee_capitalized_into_avg_cost(conn):
    """Single buy 100 @ 1500 with fee 37.5 → avg_cost = 1500.375 (CN A-share fee = 0.025% commission, min 5)."""
    ensure_account(conn, "neutral")
    # 100 * 1500 * 0.00025 = 37.5  (above 5.0 min)
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1500.0)
    pos = get_positions(conn, "neutral")
    assert len(pos) == 1
    assert pos[0]["avg_cost"] == pytest.approx(1500.375)


def test_buy_fee_capitalized_weighted_average(conn):
    """Two buys: 100@1500 fee=37.5, then 100@1400 fee=35.0 → avg_cost = 1450.3625."""
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1500.0)
    place_order(conn, account_id="neutral", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1400.0)
    pos = get_positions(conn, "neutral")
    assert pos[0]["avg_cost"] == pytest.approx(1450.3625)
```

The `conn` fixture is already provided by `tests/conftest.py`.

- [ ] **Step 2: Run new tests, expect FAIL**

Run: `uv run --project . pytest tests/test_realized_pnl.py::test_buy_fee_capitalized_into_avg_cost tests/test_realized_pnl.py::test_buy_fee_capitalized_weighted_average -v`
Expected: FAIL — current `avg_cost` will be `1500.0` and `1450.0` (no fee).

- [ ] **Step 3: Add `fee` parameter to `_upsert_position_buy` in `python/orders.py`**

Replace the function definition (lines 33–53) with:

```python
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
```

- [ ] **Step 4: Pass `fee` from `place_order` buy fill site**

In `python/orders.py`, find the buy branch in `place_order` (currently line 143):

```python
        if side == "buy":
            adjust_cash(conn, account_id, currency, -(qty * fill_price + fee))
            _upsert_position_buy(conn, account_id, symbol, market, qty, fill_price,
                                 currency, settle_date)
```

Change the `_upsert_position_buy` call to pass `fee`:

```python
        if side == "buy":
            adjust_cash(conn, account_id, currency, -(qty * fill_price + fee))
            _upsert_position_buy(conn, account_id, symbol, market, qty, fill_price,
                                 currency, settle_date, fee=fee)
```

- [ ] **Step 5: Pass `fee` from sweep buy fill site in `python/settlement.py`**

Around line 100 in `python/settlement.py`, find:

```python
        if r["side"] == "buy":
            adjust_cash(conn, account_id, currency, -(r["qty"] * fill_price + fee))
            _upsert_position_buy(conn, account_id, r["symbol"], r["market"],
                                 r["qty"], fill_price, currency, settle_date)
```

Change the `_upsert_position_buy` call to pass `fee`:

```python
        if r["side"] == "buy":
            adjust_cash(conn, account_id, currency, -(r["qty"] * fill_price + fee))
            _upsert_position_buy(conn, account_id, r["symbol"], r["market"],
                                 r["qty"], fill_price, currency, settle_date, fee=fee)
```

- [ ] **Step 6: Run new tests, expect PASS**

Run: `uv run --project . pytest tests/test_realized_pnl.py::test_buy_fee_capitalized_into_avg_cost tests/test_realized_pnl.py::test_buy_fee_capitalized_weighted_average -v`
Expected: both PASS.

- [ ] **Step 7: Update existing assertions that no longer match**

Two existing tests assume fee is NOT in `avg_cost`. Update them:

In `tests/test_portfolio.py`, line 23 (`test_positions_after_buy`):

```python
    assert pos[0]["avg_cost"] == pytest.approx(150.01)  # was 150.0; now fee-capitalized: (100*150 + 1)/100
```

(US fee for 100 @ 150 = `max(100*0.005, 1.0) = 1.0`.)

In `tests/test_portfolio.py`, line 71 (`test_pnl_unrealized_from_price_map`):

```python
    assert pnl["unrealized_usd"] == pytest.approx(999.0)  # was 1000.0; (160-150.01)*100
```

In `tests/test_portfolio.py`, line 33 (`test_portfolio_with_price_map`):
This one expects `market_value == 16000.0` (just `qty × price`), which is unchanged. Leave it.

- [ ] **Step 8: Run full suite**

Run: `uv run --project . pytest -v`
Expected: all PASS. Note `test_pnl_realized_after_round_trip` may now FAIL with a small delta (was 998.0 by coincidence; now off by the buy fee being in avg_cost). That's expected — Task 3 fixes the realized formula and Task 4 will update that assertion.

If only `test_pnl_realized_after_round_trip` fails, proceed. If anything else fails, stop and investigate.

- [ ] **Step 9: Commit**

```bash
git add plugins/paper_trading_mcp/python/orders.py plugins/paper_trading_mcp/python/settlement.py plugins/paper_trading_mcp/tests/test_realized_pnl.py plugins/paper_trading_mcp/tests/test_portfolio.py
git commit -m "feat(paper_trading_mcp): capitalize buy fees into avg_cost"
```

---

## Task 3: Write `realized_pnl` on sell fills (immediate path)

**Files:**
- Modify: `python/orders.py` (`place_order` sell branch)
- Test: `tests/test_realized_pnl.py` (append)

- [ ] **Step 1: Append failing test**

Append to `tests/test_realized_pnl.py`:

```python
def test_sell_fill_writes_realized_pnl_immediate_path(conn):
    """Buy 100@1500 (fee 37.5), buy 100@1400 (fee 35) → avg_cost 1450.3625.
    Sell 100@1600 → realized = (1600-1450.3625)*100 - sell_fee.
    CN sell fee = 100*1600*0.00025 + 100*1600*0.0005 = 40 + 80 = 120
    realized = 14963.75 - 120 = 14843.75
    But CN T+1 blocks selling same-day buys, so we use US to keep it simple.
    """
    ensure_account(conn, "neutral")
    # US fee: max(qty*0.005, 1.0). 100*150*0.005 = 75 → fee = 75.0? No: per_share=100*0.005=0.5, max(0.5, 1.0)=1.0
    # avg_cost after buy 100@150 fee=1.0: (100*150 + 1)/100 = 150.01
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    # Sell 100 @ 160; sell_fee = max(100*0.005, 1.0) = 1.0
    # realized = (160 - 150.01) * 100 - 1.0 = 999.0 - 1.0 = 998.0
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
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run --project . pytest tests/test_realized_pnl.py::test_sell_fill_writes_realized_pnl_immediate_path -v`
Expected: FAIL — `realized_pnl` is currently NULL on all sells.

- [ ] **Step 3: Modify `place_order` sell-fill branch in `python/orders.py`**

Replace the immediate-fill block in `place_order` (currently lines 114–156) so that:
1. For sells, it reads `avg_cost` BEFORE updating positions.
2. Computes `realized_pnl` and includes it in the INSERT.

Replace the entire `if should_fill:` block (lines 114–156) with:

```python
    if should_fill:
        fee = calc_fee(market=market, side=side, qty=qty, price=fill_price)
        realized_pnl = None
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
            # Capture avg_cost BEFORE the position is mutated.
            realized_pnl = (fill_price - row["avg_cost"]) * qty - fee

        settle_date = None
        if market == "CN" and side == "buy":
            settle_date = _next_business_day(now.date()).isoformat()
        cur = conn.execute(
            """INSERT INTO orders (account_id, symbol, market, side, order_type,
                qty, price, ref_price, status, filled_price, filled_qty, fee,
                submitted_at, filled_at, settle_date, realized_pnl)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (account_id, symbol, market, side, order_type, qty, price, ref_price,
             "filled", fill_price, qty, fee, now_iso, now_iso, settle_date, realized_pnl),
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
```

Key changes from the original:
- Added `realized_pnl = None` default.
- For sells, capture `realized_pnl` BEFORE mutating the position.
- INSERT statement now has 16 columns (added `realized_pnl`).

- [ ] **Step 4: Run new tests, expect PASS**

Run: `uv run --project . pytest tests/test_realized_pnl.py -v`
Expected: all `tests/test_realized_pnl.py` tests PASS so far.

- [ ] **Step 5: Run full suite**

Run: `uv run --project . pytest -v`
Expected: only `test_pnl_realized_after_round_trip` may still fail (next task fixes it).

- [ ] **Step 6: Commit**

```bash
git add plugins/paper_trading_mcp/python/orders.py plugins/paper_trading_mcp/tests/test_realized_pnl.py
git commit -m "feat(paper_trading_mcp): write realized_pnl on immediate sell fills"
```

---

## Task 4: Rewrite `get_pnl` to SUM realized_pnl + update existing test

**Files:**
- Modify: `python/portfolio.py` (`get_pnl`)
- Modify: `tests/test_portfolio.py` (`test_pnl_realized_after_round_trip`)
- Test: `tests/test_realized_pnl.py` (append)

- [ ] **Step 1: Append failing tests for new SUM behavior**

Append to `tests/test_realized_pnl.py`:

```python
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
    # Buy first to satisfy schema constraints / position invariants
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
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run --project . pytest tests/test_realized_pnl.py::test_get_pnl_realized_zero_when_only_buys tests/test_realized_pnl.py::test_get_pnl_unrealized_uses_fee_capitalized_avg_cost tests/test_realized_pnl.py::test_get_pnl_old_sell_rows_excluded -v`
Expected: at least the first two FAIL with the buggy formula.

- [ ] **Step 3: Rewrite `get_pnl` in `python/portfolio.py`**

Replace the entire `get_pnl` function (lines 58–87) with:

```python
def get_pnl(
    conn: sqlite3.Connection, account_id: str,
    date: str | None = None, price_map: dict[str, float] | None = None,
) -> dict:
    q = """SELECT market, realized_pnl
           FROM orders
           WHERE account_id=?
             AND status='filled'
             AND side='sell'
             AND realized_pnl IS NOT NULL"""
    args: list = [account_id]
    if date:
        q += " AND substr(filled_at,1,10)=?"
        args.append(date)
    rows = conn.execute(q, args).fetchall()
    realized = {"CNY": 0.0, "HKD": 0.0, "USD": 0.0}
    for r in rows:
        cur = CURRENCY_BY_MARKET[r["market"]]
        realized[cur] += r["realized_pnl"]

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
```

- [ ] **Step 4: Update existing realized assertion in `tests/test_portfolio.py`**

`test_pnl_realized_after_round_trip` (line 56) buys 100 @ 150 then sells 100 @ 160 (US).

Recompute:
- buy fee = 1.0; avg_cost = (100*150 + 1)/100 = 150.01
- sell fee = 1.0
- realized = (160 - 150.01) * 100 - 1.0 = 999 - 1 = **998.0**

Coincidence: same number as before. Leave the assertion at `998.0` — but add a comment so it's clear why it still works:

Replace line 63 with:

```python
    # avg_cost = 150.01 (fee-capitalized); realized = (160-150.01)*100 - 1.0 = 998.0
    assert pnl["realized_usd"] == pytest.approx(998.0)
```

- [ ] **Step 5: Run new tests, expect PASS**

Run: `uv run --project . pytest tests/test_realized_pnl.py -v`
Expected: all PASS.

- [ ] **Step 6: Run full suite**

Run: `uv run --project . pytest -v`
Expected: ALL tests PASS.

- [ ] **Step 7: Commit**

```bash
git add plugins/paper_trading_mcp/python/portfolio.py plugins/paper_trading_mcp/tests/test_portfolio.py plugins/paper_trading_mcp/tests/test_realized_pnl.py
git commit -m "fix(paper_trading_mcp): get_pnl returns true realized P&L instead of cash flow"
```

---

## Task 5: Cover sweep sell path (`_sweep_pending`)

**Files:**
- Modify: `python/settlement.py` (sweep sell branch)
- Test: `tests/test_realized_pnl.py` (append)

- [ ] **Step 1: Append failing test**

Append to `tests/test_realized_pnl.py`:

```python
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
```

- [ ] **Step 2: Run, expect FAIL**

Run: `uv run --project . pytest tests/test_realized_pnl.py::test_sweep_sell_path_writes_realized_pnl -v`
Expected: FAIL — `realized_pnl` is NULL on the sweep-filled sell row.

- [ ] **Step 3: Modify `_sweep_pending` in `python/settlement.py`**

Find the sell branch and the UPDATE statement that fills the order (currently lines 78–104). Replace the section starting from the `else:` (sell-side validation) through the position update with:

```python
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

        # Compute realized_pnl for sells using avg_cost BEFORE position mutation.
        realized_pnl = None
        if r["side"] == "sell":
            realized_pnl = (fill_price - pos["avg_cost"]) * r["qty"] - fee

        conn.execute(
            """UPDATE orders SET status='filled', filled_price=?, filled_qty=?,
                   fee=?, filled_at=?, settle_date=?, realized_pnl=? WHERE id=?""",
            (fill_price, r["qty"], fee, now_iso, settle_date, realized_pnl, r["id"]),
        )
        if r["side"] == "buy":
            adjust_cash(conn, account_id, currency, -(r["qty"] * fill_price + fee))
            _upsert_position_buy(conn, account_id, r["symbol"], r["market"],
                                 r["qty"], fill_price, currency, settle_date, fee=fee)
        else:
            adjust_cash(conn, account_id, currency, r["qty"] * fill_price - fee)
            _update_position_sell(conn, account_id, r["symbol"], r["market"], r["qty"])
```

Key changes:
- The sell branch now keeps `pos` in a variable (was previously fetched only for validation, then dropped).
- `realized_pnl` computed before position mutation.
- UPDATE adds `realized_pnl=?` and a corresponding parameter.

- [ ] **Step 4: Run new test, expect PASS**

Run: `uv run --project . pytest tests/test_realized_pnl.py::test_sweep_sell_path_writes_realized_pnl -v`
Expected: PASS.

- [ ] **Step 5: Run full suite**

Run: `uv run --project . pytest -v`
Expected: ALL PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/paper_trading_mcp/python/settlement.py plugins/paper_trading_mcp/tests/test_realized_pnl.py
git commit -m "fix(paper_trading_mcp): sweep sell path also writes realized_pnl"
```

---

## Task 6: Equity-identity golden test

**Files:**
- Test: `tests/test_realized_pnl.py` (append)

- [ ] **Step 1: Append golden test**

This test asserts the fundamental invariant: `(final_cash + market_value) - initial_cash == realized + unrealized` after an arbitrary sequence of buys and sells. If this ever fails, the realized/unrealized accounting is broken.

Append to `tests/test_realized_pnl.py`:

```python
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

    # Use a price_map that reflects "current market" for unrealized.
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
```

- [ ] **Step 2: Run test, expect PASS**

Run: `uv run --project . pytest tests/test_realized_pnl.py::test_equity_identity_after_mixed_sequence -v`
Expected: PASS. If it fails, **stop and investigate** — the accounting is fundamentally broken somewhere.

- [ ] **Step 3: Run full suite**

Run: `uv run --project . pytest -v`
Expected: ALL PASS.

- [ ] **Step 4: Commit**

```bash
git add plugins/paper_trading_mcp/tests/test_realized_pnl.py
git commit -m "test(paper_trading_mcp): equity-identity golden test for realized PnL"
```

---

## Task 7: Manual smoke verification via MCP tools

This task is purely manual — no code changes. It verifies the user-facing fix matches the spec's acceptance criterion.

- [ ] **Step 1: Reset the user's paper-trading database**

The dev DB lives at `~/.paper_trading/paper.db`. To get a clean baseline, back it up:

```bash
mv ~/.paper_trading/paper.db ~/.paper_trading/paper.db.bak.$(date +%s) 2>/dev/null || true
```

- [ ] **Step 2: Replay the smoke-test scenario via MCP tools**

In Claude Code (with the paper_trading MCP server connected), run these tool calls in order:

1. `mcp__plugin_paper_trading_mcp_paper_trading__place_order` with `{account_id: "neutral", symbol: "600519", market: "CN", side: "buy", qty: 100, order_type: "market", ref_price: 1500}`
2. `mcp__plugin_paper_trading_mcp_paper_trading__place_order` with `{account_id: "neutral", symbol: "600519", market: "CN", side: "buy", qty: 100, order_type: "market", ref_price: 1400}`
3. `mcp__plugin_paper_trading_mcp_paper_trading__get_pnl` with `{account_id: "neutral", price_map: {"600519": 1500}}`

- [ ] **Step 3: Verify acceptance criterion**

Step 3 above must return:

```json
{
  "realized_cny": 0.0,
  "realized_hkd": 0.0,
  "realized_usd": 0.0,
  "unrealized_cny": 9927.5,    // was buggy +10000.0
  "unrealized_hkd": 0.0,
  "unrealized_usd": 0.0
}
```

Tolerance: `realized_cny == 0.0` exactly; `unrealized_cny ≈ 9927.5` (within 0.01).

If the numbers match, the fix is verified end-to-end. If `realized_cny` is anything other than `0.0` or `unrealized_cny` differs from 9927.5 by more than 0.01, the implementation is wrong — go back to systematic-debugging.

- [ ] **Step 4: Restore previous DB if desired**

```bash
ls ~/.paper_trading/paper.db.bak.* 2>/dev/null && \
  echo "Backups exist; restore manually if you want to keep prior state"
```

- [ ] **Step 5: No commit needed** (verification only).

---

## Self-review summary

- Spec coverage: §Architecture (Tasks 1–5), §Data-flow walk-through (Tasks 2–4 cover the buy steps, Task 3+5 cover sells), §Error handling migration (Task 1), §Testing plan tests #1–7 (covered by Tasks 2–6 plus the migration tests in Task 1; #4 golden = Task 6; #6 migration = Task 1; #7 old-orders excluded = Task 4 step 1 third test). §Acceptance manual replay = Task 7.
- All file paths absolute under `plugins/paper_trading_mcp/`.
- Method signatures consistent: `_upsert_position_buy(..., fee=0.0)` defined in Task 2 and called with `fee=fee` in Tasks 2 & 5.
- INSERT/UPDATE column counts verified to match new 16-column INSERT in Task 3 and 7-bind UPDATE in Task 5.
- No "TBD"; all code blocks present.

---

## Plan complete

Saved to `docs/superpowers/plans/2026-04-21-paper-trading-realized-pnl-fix.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?


