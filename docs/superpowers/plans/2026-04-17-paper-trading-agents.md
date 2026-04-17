# Paper Trading Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build 4 new plugins under `/plugins` — `paper_trading_mcp` (multi-account SQLite-backed simulated trading MCP) plus three trader agent plugins (`trader_aggressive`, `trader_neutral`, `trader_conservative`) that trade daily via existing `cn_mcp`/`t_mcp` and gather at 17:00 for a free-form self-directed discussion.

**Architecture:** `paper_trading_mcp` mirrors the structure of the existing `cn_mcp` plugin: a Node/TypeScript MCP server (stdio transport) delegating business logic to a Python (uv-managed) CLI, with SQLite persistence at `~/.paper_trading/paper.db`. Three trader plugins are pure Claude Code plugins (agent markdown + slash commands, no server). Discussion is orchestrated as a self-directed turn-taking loop driven by `next_speaker` HTML comments embedded in a shared markdown file.

**Tech Stack:** TypeScript (`@modelcontextprotocol/sdk`, `zod`), Python 3.10+ (stdlib + `pytest`), SQLite (stdlib `sqlite3`), uv for Python env management, Claude Code plugin manifest format.

**Spec:** `docs/superpowers/specs/2026-04-17-paper-trading-agents-design.md`

---

## File Structure

**New plugins:**

```
plugins/paper_trading_mcp/
├── .claude-plugin/plugin.json
├── .mcp.json
├── .gitignore
├── package.json
├── pyproject.toml
├── tsconfig.json
├── src/
│   ├── index.ts                     # MCP server wiring, tool registrations
│   └── tools/
│       └── call-python.ts           # Python CLI invocation helper
├── python/
│   ├── __init__.py
│   ├── __main__.py                  # CLI dispatcher
│   ├── db.py                        # SQLite schema + connection
│   ├── accounts.py                  # account init, cash ops
│   ├── fees.py                      # market-specific fee rules
│   ├── orders.py                    # place_order, cancel_order, matching
│   ├── portfolio.py                 # positions, pnl, portfolio queries
│   ├── settlement.py                # T+1 settlement + pending order sweep
│   ├── journal.py                   # daily journal read/append
│   └── discussion.py                # discussion file init/read/append
├── commands/
│   └── run-discussion.md            # /paper-trading:run-discussion
├── tests/
│   ├── conftest.py                  # pytest fixtures (in-memory db)
│   ├── test_accounts.py
│   ├── test_fees.py
│   ├── test_orders.py
│   ├── test_settlement.py
│   ├── test_portfolio.py
│   ├── test_journal.py
│   └── test_discussion.py
└── README.md

plugins/trader_aggressive/           # same structure for _neutral and _conservative
├── .claude-plugin/plugin.json
├── agents/trader-aggressive.md
├── commands/
│   ├── trade-day.md
│   └── join-discussion.md
└── README.md
```

**Responsibilities:**

- `db.py` owns schema + connection. One concern only.
- `fees.py` is a pure function module — fee rules per market, no IO.
- `orders.py` owns order lifecycle (submit/cancel/match). Reads from `db`, delegates fees to `fees`.
- `settlement.py` owns T+1 date math + pending-order sweep. Reads from `db`.
- `portfolio.py` is read-only aggregations.
- `journal.py` and `discussion.py` are file IO only (markdown append/read).
- `call-python.ts` is the only TS ↔ Python bridge; all MCP tool handlers in `index.ts` call it.
- Three trader plugins share structure but diverge only in agent prompt content (the persona spec).

---

## Task 1 — `paper_trading_mcp` Plugin Skeleton

**Files:**
- Create: `plugins/paper_trading_mcp/.gitignore`
- Create: `plugins/paper_trading_mcp/.claude-plugin/plugin.json`
- Create: `plugins/paper_trading_mcp/.mcp.json`
- Create: `plugins/paper_trading_mcp/package.json`
- Create: `plugins/paper_trading_mcp/pyproject.toml`
- Create: `plugins/paper_trading_mcp/tsconfig.json`
- Create: `plugins/paper_trading_mcp/README.md`
- Create: `plugins/paper_trading_mcp/python/__init__.py`

- [ ] **Step 1: Create `.gitignore`**

Create `plugins/paper_trading_mcp/.gitignore`:

```
node_modules/
dist/
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 2: Create plugin manifest**

Create `plugins/paper_trading_mcp/.claude-plugin/plugin.json`:

```json
{
  "name": "paper_trading_mcp",
  "description": "MCP server providing multi-account simulated trading (CN/HK/US markets, T+1, limit/stop orders) for the TradingAgents paper-trading workflow",
  "version": "0.1.0",
  "author": {
    "name": "TauricResearch"
  }
}
```

- [ ] **Step 3: Create MCP server registration**

Create `plugins/paper_trading_mcp/.mcp.json`:

```json
{
  "mcpServers": {
    "paper_trading": {
      "type": "stdio",
      "command": "node",
      "args": ["./plugins/paper_trading_mcp/dist/index.js"],
      "env": {}
    }
  }
}
```

- [ ] **Step 4: Create package.json**

Create `plugins/paper_trading_mcp/package.json`:

```json
{
  "name": "paper_trading_mcp",
  "version": "0.1.0",
  "description": "MCP server providing multi-account simulated trading",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "setup:python": "uv sync --project .",
    "setup": "npm install && npm run build && npm run setup:python",
    "test:python": "uv run --project . pytest -v"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.12.1",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "typescript": "^5.8.0"
  }
}
```

- [ ] **Step 5: Create pyproject.toml**

Create `plugins/paper_trading_mcp/pyproject.toml`:

```toml
[project]
name = "paper-trading-mcp"
version = "0.1.0"
description = "Multi-account simulated trading engine"
requires-python = ">=3.10"
dependencies = []

[dependency-groups]
dev = [
    "pytest>=8.0.0",
]
```

- [ ] **Step 6: Create tsconfig.json**

Create `plugins/paper_trading_mcp/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "node",
    "esModuleInterop": true,
    "strict": true,
    "outDir": "dist",
    "rootDir": "src",
    "declaration": false,
    "skipLibCheck": true
  },
  "include": ["src/**/*.ts"]
}
```

- [ ] **Step 7: Create Python package marker**

Create `plugins/paper_trading_mcp/python/__init__.py`:

```python
"""paper_trading_mcp business logic (CLI-invoked by the Node MCP server)."""
```

- [ ] **Step 8: Create minimal README**

Create `plugins/paper_trading_mcp/README.md`:

```markdown
# paper_trading_mcp

MCP server providing multi-account simulated trading for three trader agents (`trader_aggressive`, `trader_neutral`, `trader_conservative`).

**Markets:** CN (A-shares, T+1), HK, US (both T+0).
**Initial capital per account:** ¥1,000,000 + HK$1,000,000 + $100,000.
**Persistence:** `~/.paper_trading/paper.db` (SQLite).

## Setup

```
cd plugins/paper_trading_mcp
npm run setup
```

## Tools

See `docs/superpowers/specs/2026-04-17-paper-trading-agents-design.md` §Component 1.

## Slash Commands

- `/paper-trading:run-discussion` — orchestrate the daily 17:00 free-form discussion among the three trader agents.
```

- [ ] **Step 9: Verify skeleton installs**

Run:
```bash
cd plugins/paper_trading_mcp && npm install
```
Expected: `node_modules/` populated, no errors.

- [ ] **Step 10: Commit**

```bash
git add plugins/paper_trading_mcp
git commit -m "feat(paper_trading_mcp): scaffold plugin (manifests, package.json, pyproject)"
```

---

## Task 2 — SQLite Schema & Connection (`db.py`)

**Files:**
- Create: `plugins/paper_trading_mcp/python/db.py`
- Create: `plugins/paper_trading_mcp/tests/__init__.py`
- Create: `plugins/paper_trading_mcp/tests/conftest.py`
- Create: `plugins/paper_trading_mcp/tests/test_db.py`

- [ ] **Step 1: Create tests/__init__.py**

Create empty file `plugins/paper_trading_mcp/tests/__init__.py`.

- [ ] **Step 2: Write failing test for schema creation**

Create `plugins/paper_trading_mcp/tests/test_db.py`:

```python
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
    init_schema(conn)  # second call must not raise
    cur = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    assert cur.fetchone()[0] == 4
```

- [ ] **Step 3: Create pytest conftest**

Create `plugins/paper_trading_mcp/tests/conftest.py`:

```python
import sqlite3
import pytest
from python.db import init_schema


@pytest.fixture
def conn():
    """Fresh in-memory SQLite with schema initialized."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    init_schema(c)
    yield c
    c.close()
```

- [ ] **Step 4: Run test — verify it fails**

Run:
```bash
cd plugins/paper_trading_mcp && uv run pytest tests/test_db.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'python.db'`

- [ ] **Step 5: Implement `db.py`**

Create `plugins/paper_trading_mcp/python/db.py`:

```python
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
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
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
    settle_date  TEXT
);

CREATE TABLE IF NOT EXISTS trade_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    account_id   TEXT NOT NULL,
    event        TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    """Create tables if missing. Idempotent."""
    conn.executescript(SCHEMA)
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
```

- [ ] **Step 6: Run tests — verify they pass**

Run:
```bash
cd plugins/paper_trading_mcp && uv sync && uv run pytest tests/test_db.py -v
```
Expected: 2 passed.

- [ ] **Step 7: Commit**

```bash
git add plugins/paper_trading_mcp/python/db.py plugins/paper_trading_mcp/tests plugins/paper_trading_mcp/uv.lock
git commit -m "feat(paper_trading_mcp): add sqlite schema (accounts, positions, orders, trade_log)"
```

---

## Task 3 — Fee Rules (`fees.py`)

**Files:**
- Create: `plugins/paper_trading_mcp/python/fees.py`
- Create: `plugins/paper_trading_mcp/tests/test_fees.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/paper_trading_mcp/tests/test_fees.py`:

```python
import pytest
from python.fees import calc_fee


def test_cn_buy_commission_only_min5():
    # 100 shares * 10 CNY = 1000; 0.025% = 0.25 → minimum 5
    assert calc_fee(market="CN", side="buy", qty=100, price=10.0) == pytest.approx(5.0)


def test_cn_buy_commission_over_min():
    # 1M CNY notional → 0.025% = 250
    assert calc_fee(market="CN", side="buy", qty=10000, price=100.0) == pytest.approx(250.0)


def test_cn_sell_adds_stamp_duty():
    # 1M notional → commission 250 + stamp 0.05% = 500 → total 750
    assert calc_fee(market="CN", side="sell", qty=10000, price=100.0) == pytest.approx(750.0)


def test_hk_buy_commission_and_stamp():
    # 1M HKD notional → commission 0.08% = 800 + stamp 0.1% = 1000 → 1800
    assert calc_fee(market="HK", side="buy", qty=10000, price=100.0) == pytest.approx(1800.0)


def test_hk_sell_commission_and_stamp():
    assert calc_fee(market="HK", side="sell", qty=10000, price=100.0) == pytest.approx(1800.0)


def test_hk_min_commission():
    # small order: commission would be tiny → floored at HK$5 + stamp 0.1%
    # 10 shares * 10 HKD = 100 notional; commission 0.08 → min 5; stamp 0.1% = 0.1 → total 5.1
    assert calc_fee(market="HK", side="buy", qty=10, price=10.0) == pytest.approx(5.1)


def test_us_per_share_min1():
    # 100 shares * $0.005 = $0.5 → min $1
    assert calc_fee(market="US", side="buy", qty=100, price=50.0) == pytest.approx(1.0)


def test_us_per_share_over_min():
    # 1000 shares * $0.005 = $5
    assert calc_fee(market="US", side="sell", qty=1000, price=50.0) == pytest.approx(5.0)


def test_unknown_market_raises():
    with pytest.raises(ValueError):
        calc_fee(market="JP", side="buy", qty=100, price=10.0)
```

- [ ] **Step 2: Run test — verify it fails**

Run:
```bash
cd plugins/paper_trading_mcp && uv run pytest tests/test_fees.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'python.fees'`

- [ ] **Step 3: Implement `fees.py`**

Create `plugins/paper_trading_mcp/python/fees.py`:

```python
"""Market-specific fee rules for paper trading.

All fees returned in the market's native currency.
"""
from __future__ import annotations


def calc_fee(*, market: str, side: str, qty: float, price: float) -> float:
    notional = qty * price
    if market == "CN":
        commission = max(notional * 0.00025, 5.0)
        stamp = notional * 0.0005 if side == "sell" else 0.0
        return commission + stamp
    if market == "HK":
        commission = max(notional * 0.0008, 5.0)
        stamp = notional * 0.001  # both sides
        return commission + stamp
    if market == "US":
        per_share = qty * 0.005
        return max(per_share, 1.0)
    raise ValueError(f"Unknown market: {market}")


CURRENCY_BY_MARKET = {"CN": "CNY", "HK": "HKD", "US": "USD"}
```

- [ ] **Step 4: Run tests — verify pass**

Run:
```bash
cd plugins/paper_trading_mcp && uv run pytest tests/test_fees.py -v
```
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/python/fees.py plugins/paper_trading_mcp/tests/test_fees.py
git commit -m "feat(paper_trading_mcp): add per-market fee rules (CN/HK/US)"
```

---

## Task 4 — Account Init & Cash Operations (`accounts.py`)

**Files:**
- Create: `plugins/paper_trading_mcp/python/accounts.py`
- Create: `plugins/paper_trading_mcp/tests/test_accounts.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/paper_trading_mcp/tests/test_accounts.py`:

```python
import pytest
from python.accounts import ensure_account, get_cash, adjust_cash, INITIAL_CNY, INITIAL_HKD, INITIAL_USD


def test_ensure_account_creates_with_initial_capital(conn):
    ensure_account(conn, "aggressive")
    cash = get_cash(conn, "aggressive")
    assert cash == {"CNY": INITIAL_CNY, "HKD": INITIAL_HKD, "USD": INITIAL_USD}


def test_ensure_account_is_idempotent(conn):
    ensure_account(conn, "neutral")
    ensure_account(conn, "neutral")  # must not reset cash
    adjust_cash(conn, "neutral", "CNY", -1000)
    ensure_account(conn, "neutral")
    assert get_cash(conn, "neutral")["CNY"] == INITIAL_CNY - 1000


def test_adjust_cash_debit(conn):
    ensure_account(conn, "conservative")
    adjust_cash(conn, "conservative", "USD", -500)
    assert get_cash(conn, "conservative")["USD"] == INITIAL_USD - 500


def test_adjust_cash_credit(conn):
    ensure_account(conn, "aggressive")
    adjust_cash(conn, "aggressive", "HKD", 1000)
    assert get_cash(conn, "aggressive")["HKD"] == INITIAL_HKD + 1000


def test_adjust_cash_invalid_currency(conn):
    ensure_account(conn, "aggressive")
    with pytest.raises(ValueError):
        adjust_cash(conn, "aggressive", "JPY", 100)


def test_get_cash_missing_account_auto_creates(conn):
    cash = get_cash(conn, "aggressive")
    assert cash["CNY"] == INITIAL_CNY
```

- [ ] **Step 2: Run test — verify fails**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_accounts.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `accounts.py`**

Create `plugins/paper_trading_mcp/python/accounts.py`:

```python
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
```

- [ ] **Step 4: Run tests — pass**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_accounts.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/python/accounts.py plugins/paper_trading_mcp/tests/test_accounts.py
git commit -m "feat(paper_trading_mcp): add account init + multi-currency cash ledger"
```

---

## Task 5 — Market Orders & Matching (`orders.py`)

**Files:**
- Create: `plugins/paper_trading_mcp/python/orders.py`
- Create: `plugins/paper_trading_mcp/tests/test_orders.py`

- [ ] **Step 1: Write failing tests for market buy/sell**

Create `plugins/paper_trading_mcp/tests/test_orders.py`:

```python
import pytest
from python.accounts import ensure_account, get_cash, INITIAL_CNY, INITIAL_USD
from python.orders import place_order, cancel_order


def test_market_buy_us_fills_immediately(conn):
    ensure_account(conn, "aggressive")
    res = place_order(
        conn,
        account_id="aggressive",
        symbol="AAPL",
        market="US",
        side="buy",
        qty=100,
        order_type="market",
        ref_price=150.0,
    )
    assert res["ok"] is True
    assert res["status"] == "filled"
    assert res["filled_price"] == 150.0
    assert res["filled_qty"] == 100
    # Cash debited: 100*150 + $1 min fee = 15001
    assert get_cash(conn, "aggressive")["USD"] == pytest.approx(INITIAL_USD - 15001.0)


def test_market_buy_cn_sets_settle_date(conn):
    ensure_account(conn, "aggressive")
    res = place_order(
        conn,
        account_id="aggressive",
        symbol="600519",
        market="CN",
        side="buy",
        qty=100,
        order_type="market",
        ref_price=1800.0,
    )
    assert res["ok"] is True
    # T+1 so settle_date is set to a future business day
    assert res["settle_date"] is not None
    assert res["settle_date"] != res["submitted_at"][:10]


def test_market_buy_insufficient_cash(conn):
    ensure_account(conn, "conservative")
    res = place_order(
        conn,
        account_id="conservative",
        symbol="AAPL",
        market="US",
        side="buy",
        qty=10000,
        order_type="market",
        ref_price=500.0,  # 5M > 100k cash
    )
    assert res["ok"] is False
    assert res["error_code"] == "INSUFFICIENT_CASH"


def test_market_buy_requires_ref_price(conn):
    ensure_account(conn, "aggressive")
    res = place_order(
        conn,
        account_id="aggressive",
        symbol="AAPL",
        market="US",
        side="buy",
        qty=10,
        order_type="market",
        ref_price=None,
    )
    assert res["ok"] is False
    assert res["error_code"] == "MISSING_REF_PRICE"


def test_market_sell_without_position(conn):
    ensure_account(conn, "aggressive")
    res = place_order(
        conn,
        account_id="aggressive",
        symbol="AAPL",
        market="US",
        side="sell",
        qty=100,
        order_type="market",
        ref_price=150.0,
    )
    assert res["ok"] is False
    assert res["error_code"] == "INSUFFICIENT_POSITION"


def test_market_sell_us_after_buy(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    # US is T+0, so available immediately
    res = place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                     side="sell", qty=100, order_type="market", ref_price=160.0)
    assert res["ok"] is True
    assert res["status"] == "filled"


def test_limit_buy_stays_pending(conn):
    ensure_account(conn, "neutral")
    res = place_order(
        conn,
        account_id="neutral",
        symbol="AAPL",
        market="US",
        side="buy",
        qty=10,
        order_type="limit",
        price=140.0,
        ref_price=150.0,  # current price above limit → not triggered
    )
    assert res["ok"] is True
    assert res["status"] == "pending"


def test_cancel_pending_order(conn):
    ensure_account(conn, "neutral")
    res = place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                     side="buy", qty=10, order_type="limit",
                     price=140.0, ref_price=150.0)
    order_id = res["order_id"]
    cancel_res = cancel_order(conn, account_id="neutral", order_id=order_id)
    assert cancel_res["ok"] is True
    assert cancel_res["status"] == "cancelled"


def test_cancel_nonexistent_order(conn):
    ensure_account(conn, "neutral")
    res = cancel_order(conn, account_id="neutral", order_id=99999)
    assert res["ok"] is False
    assert res["error_code"] == "ORDER_NOT_FOUND"


def test_cancel_already_filled_order(conn):
    ensure_account(conn, "aggressive")
    res = place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                     side="buy", qty=10, order_type="market", ref_price=150.0)
    cancel_res = cancel_order(conn, account_id="aggressive", order_id=res["order_id"])
    assert cancel_res["ok"] is False
    assert cancel_res["error_code"] == "ORDER_NOT_CANCELLABLE"
```

- [ ] **Step 2: Run test — verify fails**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_orders.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `orders.py`**

Create `plugins/paper_trading_mcp/python/orders.py`:

```python
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
    """Skip Sat/Sun. Does not handle public holidays (acceptable for simulation)."""
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
    conn: sqlite3.Connection,
    account_id: str,
    symbol: str,
    market: str,
    qty: float,
    price: float,
    currency: str,
    settle_date: str | None,
) -> None:
    """Increase qty; if CN, buy-qty goes to total qty but NOT available_qty (T+1)."""
    row = _get_position(conn, account_id, symbol, market)
    available_delta = 0.0 if market == "CN" else qty
    if row is None:
        conn.execute(
            """INSERT INTO positions
               (account_id, symbol, market, qty, available_qty, avg_cost, currency)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (account_id, symbol, market, qty, available_delta, price, currency),
        )
    else:
        new_qty = row["qty"] + qty
        new_avail = row["available_qty"] + available_delta
        new_cost = (row["qty"] * row["avg_cost"] + qty * price) / new_qty
        conn.execute(
            """UPDATE positions SET qty=?, available_qty=?, avg_cost=?
               WHERE id=?""",
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
    # buy-stop triggers when market rises to/above stop; sell-stop when falls to/below
    return ref_price >= stop_price if side == "buy" else ref_price <= stop_price


def place_order(
    conn: sqlite3.Connection,
    *,
    account_id: str,
    symbol: str,
    market: str,
    side: str,
    qty: float,
    order_type: str,
    price: float | None = None,
    ref_price: float | None = None,
) -> dict:
    """Place an order. Returns structured result."""
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

    # Determine whether to fill immediately
    should_fill = order_type == "market"
    fill_price = ref_price
    if order_type == "limit" and ref_price is not None and _limit_triggers(side, price, ref_price):
        should_fill = True
        fill_price = price  # limits fill at limit (not ref)
    elif order_type == "stop" and ref_price is not None and _stop_triggers(side, price, ref_price):
        should_fill = True
        fill_price = ref_price  # stops convert to market

    currency = CURRENCY_BY_MARKET[market]

    if should_fill:
        # Pre-flight checks
        fee = calc_fee(market=market, side=side, qty=qty, price=fill_price)
        if side == "buy":
            cost = qty * fill_price + fee
            if get_cash(conn, account_id)[currency] < cost:
                return {"ok": False, "error_code": "INSUFFICIENT_CASH",
                        "message": f"need {cost} {currency}"}
        else:  # sell
            row = _get_position(conn, account_id, symbol, market)
            if row is None or row["available_qty"] < qty:
                avail = 0 if row is None else row["available_qty"]
                return {"ok": False, "error_code": "INSUFFICIENT_POSITION",
                        "message": f"available={avail}, wanted={qty}"}

        # Insert filled order
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

        # Settle cash & position
        if side == "buy":
            adjust_cash(conn, account_id, currency, -(qty * fill_price + fee))
            _upsert_position_buy(conn, account_id, symbol, market, qty, fill_price,
                                 currency, settle_date)
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

    # Pending order (limit/stop that did not trigger)
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
```

- [ ] **Step 4: Run tests — pass**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_orders.py -v`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/python/orders.py plugins/paper_trading_mcp/tests/test_orders.py
git commit -m "feat(paper_trading_mcp): market/limit/stop orders with cash+position settlement"
```

---

## Task 6 — T+1 Settlement & Pending Order Sweep (`settlement.py`)

**Files:**
- Create: `plugins/paper_trading_mcp/python/settlement.py`
- Create: `plugins/paper_trading_mcp/tests/test_settlement.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/paper_trading_mcp/tests/test_settlement.py`:

```python
import datetime as dt
import pytest
from python.accounts import ensure_account
from python.orders import place_order
from python.settlement import tick_pending_orders


def test_cn_buy_locked_same_day(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1800.0)
    # Try to sell same day → should fail (INSUFFICIENT_POSITION, available=0)
    res = place_order(conn, account_id="aggressive", symbol="600519", market="CN",
                     side="sell", qty=100, order_type="market", ref_price=1810.0)
    assert res["ok"] is False
    assert res["error_code"] == "INSUFFICIENT_POSITION"


def test_tick_releases_t1_positions(conn):
    ensure_account(conn, "aggressive")
    buy_res = place_order(conn, account_id="aggressive", symbol="600519", market="CN",
                         side="buy", qty=100, order_type="market", ref_price=1800.0)
    # Force settle_date to yesterday so sweep releases it
    conn.execute("UPDATE orders SET settle_date=? WHERE id=?",
                 ((dt.date.today() - dt.timedelta(days=1)).isoformat(), buy_res["order_id"]))
    conn.commit()
    tick_pending_orders(conn, account_id="aggressive", price_map={})
    # Now sell should succeed
    res = place_order(conn, account_id="aggressive", symbol="600519", market="CN",
                     side="sell", qty=100, order_type="market", ref_price=1810.0)
    assert res["ok"] is True


def test_tick_triggers_limit_order(conn):
    ensure_account(conn, "neutral")
    # Place limit buy at $140 when ref=150 → pending
    lim_res = place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                         side="buy", qty=10, order_type="limit",
                         price=140.0, ref_price=150.0)
    assert lim_res["status"] == "pending"
    # Price drops to 138 → should trigger
    result = tick_pending_orders(conn, account_id="neutral",
                                price_map={"AAPL": 138.0})
    assert result["triggered"] == 1
    # Verify order is now filled
    row = conn.execute("SELECT status, filled_price FROM orders WHERE id=?",
                       (lim_res["order_id"],)).fetchone()
    assert row["status"] == "filled"
    assert row["filled_price"] == 140.0


def test_tick_triggers_stop_sell(conn):
    ensure_account(conn, "aggressive")
    # Buy then place stop-sell at 145
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=10, order_type="market", ref_price=150.0)
    stop_res = place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                          side="sell", qty=10, order_type="stop",
                          price=145.0, ref_price=150.0)
    assert stop_res["status"] == "pending"
    # Price drops to 144 → stop triggers
    result = tick_pending_orders(conn, account_id="aggressive",
                                price_map={"AAPL": 144.0})
    assert result["triggered"] == 1


def test_tick_leaves_untriggered_pending(conn):
    ensure_account(conn, "neutral")
    lim = place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                     side="buy", qty=10, order_type="limit",
                     price=140.0, ref_price=150.0)
    result = tick_pending_orders(conn, account_id="neutral",
                                price_map={"AAPL": 145.0})  # still above limit
    assert result["triggered"] == 0
    row = conn.execute("SELECT status FROM orders WHERE id=?",
                       (lim["order_id"],)).fetchone()
    assert row["status"] == "pending"
```

- [ ] **Step 2: Run test — fails**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_settlement.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `settlement.py`**

Create `plugins/paper_trading_mcp/python/settlement.py`:

```python
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
    """Release CN buys whose settle_date <= today into available_qty. Returns count."""
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
        # Null out settle_date so we don't re-settle
        conn.execute("UPDATE orders SET settle_date=NULL WHERE id=?", (r["id"],))
        _log(conn, account_id, "settle", {"order_id": r["id"]})
        count += 1
    conn.commit()
    return count


def _sweep_pending(conn: sqlite3.Connection, account_id: str,
                   price_map: dict[str, float]) -> int:
    """Trigger any pending limit/stop orders whose conditions are met. Returns count."""
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

        # Post-trigger affordability check
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
    """Per spec: settle T+1 releases, then sweep pending limit/stop orders."""
    settled = _settle_t1(conn, account_id)
    triggered = _sweep_pending(conn, account_id, price_map or {})
    return {"ok": True, "settled": settled, "triggered": triggered}
```

- [ ] **Step 4: Run tests — pass**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_settlement.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/python/settlement.py plugins/paper_trading_mcp/tests/test_settlement.py
git commit -m "feat(paper_trading_mcp): add T+1 settlement + pending order sweep"
```

---

## Task 7 — Portfolio, Positions, PnL Queries (`portfolio.py`)

**Files:**
- Create: `plugins/paper_trading_mcp/python/portfolio.py`
- Create: `plugins/paper_trading_mcp/tests/test_portfolio.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/paper_trading_mcp/tests/test_portfolio.py`:

```python
import pytest
from python.accounts import ensure_account, INITIAL_USD
from python.orders import place_order
from python.portfolio import (
    get_positions, get_portfolio, get_pending_orders,
    get_order_history, get_pnl,
)


def test_positions_empty_for_new_account(conn):
    ensure_account(conn, "neutral")
    assert get_positions(conn, "neutral") == []


def test_positions_after_buy(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    pos = get_positions(conn, "aggressive")
    assert len(pos) == 1
    assert pos[0]["symbol"] == "AAPL"
    assert pos[0]["qty"] == 100
    assert pos[0]["avg_cost"] == 150.0


def test_portfolio_with_price_map(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    pf = get_portfolio(conn, "aggressive", price_map={"AAPL": 160.0})
    assert pf["cash"]["USD"] == pytest.approx(INITIAL_USD - 15001.0)
    assert len(pf["positions"]) == 1
    # market_value uses latest price
    assert pf["positions"][0]["market_value"] == pytest.approx(16000.0)


def test_pending_orders(conn):
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=10, order_type="limit",
                price=140.0, ref_price=150.0)
    pending = get_pending_orders(conn, "neutral")
    assert len(pending) == 1
    assert pending[0]["order_type"] == "limit"


def test_order_history(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=10, order_type="market", ref_price=150.0)
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="sell", qty=10, order_type="market", ref_price=160.0)
    hist = get_order_history(conn, "aggressive")
    assert len(hist) == 2


def test_pnl_realized_after_round_trip(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="sell", qty=100, order_type="market", ref_price=160.0)
    pnl = get_pnl(conn, "aggressive")
    # Gross: 100*(160-150)=1000; fees: $1 buy + $1 sell = $2; realized ~= 998
    assert pnl["realized_usd"] == pytest.approx(998.0)


def test_pnl_unrealized_from_price_map(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    pnl = get_pnl(conn, "aggressive", price_map={"AAPL": 160.0})
    # Unrealized = 100*(160-150) = 1000 (fees already paid)
    assert pnl["unrealized_usd"] == pytest.approx(1000.0)
```

- [ ] **Step 2: Run test — fails**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_portfolio.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `portfolio.py`**

Create `plugins/paper_trading_mcp/python/portfolio.py`:

```python
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
    """Realized PnL = sum over all filled sells: (sell_price - sym_avg_cost_at_sale) * qty - fee,
    tracked per-currency.

    Simplification: we compute realized as (proceeds - fees) for sells, minus
    (cost + fees) for buys, summed per currency. This equals cash flow.

    Unrealized = sum over current positions of (latest - avg_cost) * qty per currency.
    """
    # Realized: cash flow from all filled orders on given date (or all-time)
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

    # Unrealized
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

- [ ] **Step 4: Run tests — pass**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_portfolio.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/python/portfolio.py plugins/paper_trading_mcp/tests/test_portfolio.py
git commit -m "feat(paper_trading_mcp): add portfolio/positions/history/pnl queries"
```

---

## Task 8 — Journal File I/O (`journal.py`)

**Files:**
- Create: `plugins/paper_trading_mcp/python/journal.py`
- Create: `plugins/paper_trading_mcp/tests/test_journal.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/paper_trading_mcp/tests/test_journal.py`:

```python
import pytest
from pathlib import Path
from python.journal import append_journal, read_journal


def test_append_creates_file(tmp_path):
    append_journal("aggressive", "2026-04-17", "Bought AAPL.", base_dir=tmp_path)
    f = tmp_path / "journals" / "aggressive-2026-04-17.md"
    assert f.exists()
    assert "Bought AAPL." in f.read_text()


def test_append_appends_not_overwrites(tmp_path):
    append_journal("aggressive", "2026-04-17", "Entry 1", base_dir=tmp_path)
    append_journal("aggressive", "2026-04-17", "Entry 2", base_dir=tmp_path)
    content = read_journal("aggressive", "2026-04-17", base_dir=tmp_path)
    assert "Entry 1" in content
    assert "Entry 2" in content


def test_read_missing_returns_empty(tmp_path):
    content = read_journal("neutral", "2026-04-17", base_dir=tmp_path)
    assert content == ""
```

- [ ] **Step 2: Run test — fails**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_journal.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `journal.py`**

Create `plugins/paper_trading_mcp/python/journal.py`:

```python
"""Markdown journal file storage per account per day."""
from __future__ import annotations

from pathlib import Path

DEFAULT_BASE = Path.home() / ".paper_trading"


def _journal_path(base_dir: Path, account_id: str, date: str) -> Path:
    return base_dir / "journals" / f"{account_id}-{date}.md"


def append_journal(
    account_id: str, date: str, markdown: str, *, base_dir: Path | None = None,
) -> dict:
    base = base_dir or DEFAULT_BASE
    path = _journal_path(base, account_id, date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(markdown.rstrip() + "\n\n")
    return {"ok": True, "path": str(path)}


def read_journal(
    account_id: str, date: str, *, base_dir: Path | None = None,
) -> str:
    base = base_dir or DEFAULT_BASE
    path = _journal_path(base, account_id, date)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
```

- [ ] **Step 4: Run tests — pass**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_journal.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/python/journal.py plugins/paper_trading_mcp/tests/test_journal.py
git commit -m "feat(paper_trading_mcp): add per-account daily journal files"
```

---

## Task 9 — Discussion File I/O (`discussion.py`)

**Files:**
- Create: `plugins/paper_trading_mcp/python/discussion.py`
- Create: `plugins/paper_trading_mcp/tests/test_discussion.py`

- [ ] **Step 1: Write failing tests**

Create `plugins/paper_trading_mcp/tests/test_discussion.py`:

```python
import pytest
from python.discussion import (
    init_discussion, read_discussion, append_discussion,
    parse_last_next_speaker,
)


def test_init_creates_file_with_header(tmp_path):
    pnl = {"aggressive": 2.3, "neutral": 0.5, "conservative": -0.1}
    res = init_discussion("2026-04-17", pnl_summary=pnl, base_dir=tmp_path)
    assert res["ok"] is True
    content = read_discussion("2026-04-17", base_dir=tmp_path)
    assert "2026-04-17" in content
    assert "激进" in content
    assert "+2.3" in content


def test_init_refuses_if_exists(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    res = init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    assert res["ok"] is False
    assert res["error_code"] == "DISCUSSION_EXISTS"


def test_init_force_overwrites(tmp_path):
    init_discussion("2026-04-17", pnl_summary={"aggressive": 1.0}, base_dir=tmp_path)
    res = init_discussion("2026-04-17", pnl_summary={"aggressive": 2.0},
                         base_dir=tmp_path, force=True)
    assert res["ok"] is True
    content = read_discussion("2026-04-17", base_dir=tmp_path)
    assert "+2.0" in content


def test_append_with_next_speaker_comment(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    append_discussion(
        "2026-04-17", speaker="aggressive",
        markdown="I crushed it today.",
        next_speaker="conservative",
        reason="want to provoke the coward",
        base_dir=tmp_path,
    )
    content = read_discussion("2026-04-17", base_dir=tmp_path)
    assert "**激进选手：**" in content
    assert "crushed it" in content
    assert "next_speaker: conservative" in content
    assert "want to provoke" in content


def test_parse_last_next_speaker(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    append_discussion("2026-04-17", speaker="aggressive", markdown="line 1",
                     next_speaker="neutral", reason="r", base_dir=tmp_path)
    append_discussion("2026-04-17", speaker="neutral", markdown="line 2",
                     next_speaker="conservative", reason="r", base_dir=tmp_path)
    content = read_discussion("2026-04-17", base_dir=tmp_path)
    assert parse_last_next_speaker(content) == "conservative"


def test_parse_returns_none_when_missing(tmp_path):
    assert parse_last_next_speaker("no comments here") is None


def test_append_rejects_invalid_next_speaker(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    with pytest.raises(ValueError):
        append_discussion("2026-04-17", speaker="aggressive", markdown="x",
                         next_speaker="random_user", reason="r", base_dir=tmp_path)


def test_append_rejects_invalid_speaker(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    with pytest.raises(ValueError):
        append_discussion("2026-04-17", speaker="ghost", markdown="x",
                         next_speaker="neutral", reason="r", base_dir=tmp_path)
```

- [ ] **Step 2: Run test — fails**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_discussion.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement `discussion.py`**

Create `plugins/paper_trading_mcp/python/discussion.py`:

```python
"""Shared markdown discussion file + next_speaker directive parsing."""
from __future__ import annotations

import re
from pathlib import Path

DEFAULT_BASE = Path.home() / ".paper_trading"

VALID_SPEAKERS = {"aggressive", "neutral", "conservative"}
VALID_NEXT = {"aggressive", "neutral", "conservative", "end"}

CHINESE_LABEL = {
    "aggressive": "激进选手",
    "neutral": "中性选手",
    "conservative": "保守选手",
}

NEXT_SPEAKER_RE = re.compile(
    r"<!--\s*next_speaker:\s*(aggressive|neutral|conservative|end)\s*(?:/\s*reason:\s*[^>]*)?-->",
    re.IGNORECASE,
)


def _discussion_path(base_dir: Path, date: str) -> Path:
    return base_dir / "discussions" / f"{date}.md"


def init_discussion(
    date: str, *, pnl_summary: dict[str, float],
    base_dir: Path | None = None, force: bool = False,
) -> dict:
    base = base_dir or DEFAULT_BASE
    path = _discussion_path(base, date)
    if path.exists() and not force:
        return {"ok": False, "error_code": "DISCUSSION_EXISTS",
                "message": f"{path} already exists; use force=True to overwrite"}
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [f"# {date} 交易心得讨论", ""]
    if pnl_summary:
        bits = []
        for key in ("aggressive", "neutral", "conservative"):
            if key in pnl_summary:
                sign = "+" if pnl_summary[key] >= 0 else ""
                bits.append(f"{CHINESE_LABEL[key][:2]} {sign}{pnl_summary[key]:.1f}%")
        parts.append("**今日战绩** · " + " · ".join(bits))
        parts.append("")
    parts.append("---")
    parts.append("")
    path.write_text("\n".join(parts), encoding="utf-8")
    return {"ok": True, "path": str(path)}


def read_discussion(date: str, *, base_dir: Path | None = None) -> str:
    base = base_dir or DEFAULT_BASE
    path = _discussion_path(base, date)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def append_discussion(
    date: str, *, speaker: str, markdown: str, next_speaker: str,
    reason: str = "", base_dir: Path | None = None,
) -> dict:
    if speaker not in VALID_SPEAKERS:
        raise ValueError(f"Invalid speaker: {speaker}")
    if next_speaker not in VALID_NEXT:
        raise ValueError(f"Invalid next_speaker: {next_speaker}")
    base = base_dir or DEFAULT_BASE
    path = _discussion_path(base, date)
    if not path.exists():
        return {"ok": False, "error_code": "DISCUSSION_NOT_INITIALIZED",
                "message": f"call init_discussion first for {date}"}
    label = CHINESE_LABEL[speaker]
    block = (
        f"**{label}：** {markdown.strip()}\n"
        f"<!-- next_speaker: {next_speaker} / reason: {reason.strip()} -->\n\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(block)
    return {"ok": True, "path": str(path)}


def parse_last_next_speaker(content: str) -> str | None:
    """Return the last next_speaker directive, or None if absent."""
    matches = NEXT_SPEAKER_RE.findall(content)
    if not matches:
        return None
    return matches[-1].lower()
```

- [ ] **Step 4: Run tests — pass**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_discussion.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/python/discussion.py plugins/paper_trading_mcp/tests/test_discussion.py
git commit -m "feat(paper_trading_mcp): add shared discussion file + next_speaker parsing"
```

---

## Task 10 — Python CLI (`__main__.py`)

The Node MCP server invokes Python as a CLI subprocess. One subcommand per MCP tool.

**Files:**
- Create: `plugins/paper_trading_mcp/python/__main__.py`

- [ ] **Step 1: Implement `__main__.py`**

Create `plugins/paper_trading_mcp/python/__main__.py`:

```python
"""CLI dispatcher: python -m python <subcommand> [args].

All subcommands return JSON on stdout.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def _dump(result: object) -> None:
    def default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        raise TypeError(f"not serializable: {type(o).__name__}")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=default))


def _parse_json(s: str | None):
    return json.loads(s) if s else None


# --- Trading commands ---

def cmd_place_order(args):
    from .db import connect
    from .orders import place_order
    conn = connect()
    res = place_order(
        conn,
        account_id=args.account_id, symbol=args.symbol, market=args.market,
        side=args.side, qty=args.qty, order_type=args.order_type,
        price=args.price, ref_price=args.ref_price,
    )
    _dump(res)


def cmd_cancel_order(args):
    from .db import connect
    from .orders import cancel_order
    conn = connect()
    _dump(cancel_order(conn, account_id=args.account_id, order_id=args.order_id))


def cmd_tick(args):
    from .db import connect
    from .settlement import tick_pending_orders
    conn = connect()
    pm = _parse_json(args.price_map) or {}
    _dump(tick_pending_orders(conn, account_id=args.account_id, price_map=pm))


def cmd_get_portfolio(args):
    from .db import connect
    from .portfolio import get_portfolio
    conn = connect()
    pm = _parse_json(args.price_map)
    _dump(get_portfolio(conn, args.account_id, price_map=pm))


def cmd_get_positions(args):
    from .db import connect
    from .portfolio import get_positions
    conn = connect()
    _dump(get_positions(conn, args.account_id))


def cmd_get_cash(args):
    from .db import connect
    from .accounts import get_cash
    conn = connect()
    _dump(get_cash(conn, args.account_id))


def cmd_get_pending(args):
    from .db import connect
    from .portfolio import get_pending_orders
    conn = connect()
    _dump(get_pending_orders(conn, args.account_id))


def cmd_get_history(args):
    from .db import connect
    from .portfolio import get_order_history
    conn = connect()
    _dump(get_order_history(conn, args.account_id,
                            start_date=args.start_date, end_date=args.end_date))


def cmd_get_pnl(args):
    from .db import connect
    from .portfolio import get_pnl
    conn = connect()
    pm = _parse_json(args.price_map)
    _dump(get_pnl(conn, args.account_id, date=args.date, price_map=pm))


# --- Journal / discussion ---

def cmd_append_journal(args):
    from .journal import append_journal
    _dump(append_journal(args.account_id, args.date, args.markdown))


def cmd_read_journal(args):
    from .journal import read_journal
    _dump({"content": read_journal(args.account_id, args.date)})


def cmd_init_discussion(args):
    from .discussion import init_discussion
    pnl = _parse_json(args.pnl_summary) or {}
    _dump(init_discussion(args.date, pnl_summary=pnl, force=args.force))


def cmd_read_discussion(args):
    from .discussion import read_discussion
    _dump({"content": read_discussion(args.date)})


def cmd_append_discussion(args):
    from .discussion import append_discussion
    _dump(append_discussion(
        args.date, speaker=args.speaker, markdown=args.markdown,
        next_speaker=args.next_speaker, reason=args.reason or "",
    ))


def main():
    p = argparse.ArgumentParser(prog="paper_trading_mcp")
    sub = p.add_subparsers(dest="command", required=True)

    # place-order
    po = sub.add_parser("place-order")
    po.add_argument("--account-id", required=True)
    po.add_argument("--symbol", required=True)
    po.add_argument("--market", required=True, choices=["CN", "HK", "US"])
    po.add_argument("--side", required=True, choices=["buy", "sell"])
    po.add_argument("--qty", type=float, required=True)
    po.add_argument("--order-type", required=True, choices=["market", "limit", "stop"])
    po.add_argument("--price", type=float)
    po.add_argument("--ref-price", type=float)
    po.set_defaults(func=cmd_place_order)

    co = sub.add_parser("cancel-order")
    co.add_argument("--account-id", required=True)
    co.add_argument("--order-id", type=int, required=True)
    co.set_defaults(func=cmd_cancel_order)

    tk = sub.add_parser("tick-pending-orders")
    tk.add_argument("--account-id", required=True)
    tk.add_argument("--price-map", help="JSON object like {\"AAPL\": 150.0}")
    tk.set_defaults(func=cmd_tick)

    gp = sub.add_parser("get-portfolio")
    gp.add_argument("--account-id", required=True)
    gp.add_argument("--price-map")
    gp.set_defaults(func=cmd_get_portfolio)

    gpos = sub.add_parser("get-positions")
    gpos.add_argument("--account-id", required=True)
    gpos.set_defaults(func=cmd_get_positions)

    gc = sub.add_parser("get-cash")
    gc.add_argument("--account-id", required=True)
    gc.set_defaults(func=cmd_get_cash)

    gpe = sub.add_parser("get-pending-orders")
    gpe.add_argument("--account-id", required=True)
    gpe.set_defaults(func=cmd_get_pending)

    gh = sub.add_parser("get-order-history")
    gh.add_argument("--account-id", required=True)
    gh.add_argument("--start-date")
    gh.add_argument("--end-date")
    gh.set_defaults(func=cmd_get_history)

    gpnl = sub.add_parser("get-pnl")
    gpnl.add_argument("--account-id", required=True)
    gpnl.add_argument("--date")
    gpnl.add_argument("--price-map")
    gpnl.set_defaults(func=cmd_get_pnl)

    aj = sub.add_parser("append-journal")
    aj.add_argument("--account-id", required=True)
    aj.add_argument("--date", required=True)
    aj.add_argument("--markdown", required=True)
    aj.set_defaults(func=cmd_append_journal)

    rj = sub.add_parser("read-journal")
    rj.add_argument("--account-id", required=True)
    rj.add_argument("--date", required=True)
    rj.set_defaults(func=cmd_read_journal)

    idd = sub.add_parser("init-discussion")
    idd.add_argument("--date", required=True)
    idd.add_argument("--pnl-summary", help="JSON dict")
    idd.add_argument("--force", action="store_true")
    idd.set_defaults(func=cmd_init_discussion)

    rd = sub.add_parser("read-discussion")
    rd.add_argument("--date", required=True)
    rd.set_defaults(func=cmd_read_discussion)

    ad = sub.add_parser("append-discussion")
    ad.add_argument("--date", required=True)
    ad.add_argument("--speaker", required=True,
                    choices=["aggressive", "neutral", "conservative"])
    ad.add_argument("--markdown", required=True)
    ad.add_argument("--next-speaker", required=True,
                    choices=["aggressive", "neutral", "conservative", "end"])
    ad.add_argument("--reason", default="")
    ad.set_defaults(func=cmd_append_discussion)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test the CLI end-to-end**

Run these from `plugins/paper_trading_mcp`:
```bash
# Clean any pre-existing test DB
rm -f ~/.paper_trading_test.db

# Get cash (auto-creates account)
TMPDB=/tmp/pt_smoke.db uv run python -c "
from python.db import connect
from python.accounts import get_cash
conn = connect('/tmp/pt_smoke.db')
print(get_cash(conn, 'aggressive'))
"
```
Expected: prints `{'CNY': 1000000.0, 'HKD': 1000000.0, 'USD': 100000.0}`.

Run:
```bash
uv run python -m python place-order --account-id aggressive --symbol AAPL \
  --market US --side buy --qty 10 --order-type market --ref-price 150.0
```
Expected: JSON with `"ok": true, "status": "filled"`.

- [ ] **Step 3: Run full test suite**

Run: `cd plugins/paper_trading_mcp && uv run pytest -v`
Expected: all tests (db + fees + accounts + orders + settlement + portfolio + journal + discussion) pass.

- [ ] **Step 4: Commit**

```bash
git add plugins/paper_trading_mcp/python/__main__.py
git commit -m "feat(paper_trading_mcp): add python CLI dispatcher (all 14 subcommands)"
```

---

## Task 11 — TypeScript MCP Wrapper (`src/`)

**Files:**
- Create: `plugins/paper_trading_mcp/src/tools/call-python.ts`
- Create: `plugins/paper_trading_mcp/src/index.ts`

- [ ] **Step 1: Create Python invocation helper**

Create `plugins/paper_trading_mcp/src/tools/call-python.ts`:

```typescript
import { execFile } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PLUGIN_DIR = path.resolve(__dirname, "../..");

export function callPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      "uv",
      ["run", "--project", PLUGIN_DIR, "python", "-m", "python", ...args],
      {
        cwd: PLUGIN_DIR,
        timeout: 60_000,
        maxBuffer: 10 * 1024 * 1024,
        encoding: "utf-8",
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      },
      (err, stdout, stderr) => {
        if (err) reject(new Error(`Python error: ${stderr || err.message}`));
        else resolve(stdout);
      }
    );
  });
}
```

- [ ] **Step 2: Create MCP server entry point**

Create `plugins/paper_trading_mcp/src/index.ts`:

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { callPython } from "./tools/call-python.js";

const server = new McpServer({ name: "paper_trading", version: "0.1.0" });

const ACCOUNT = z.enum(["aggressive", "neutral", "conservative"]);
const MARKET = z.enum(["CN", "HK", "US"]);
const SIDE = z.enum(["buy", "sell"]);
const ORDER_TYPE = z.enum(["market", "limit", "stop"]);
const NEXT_SPEAKER = z.enum(["aggressive", "neutral", "conservative", "end"]);

function textResult(text: string) {
  return { content: [{ type: "text" as const, text }] };
}

// place_order
server.registerTool(
  "place_order",
  {
    description: "Place a paper-trading order (market/limit/stop). Market orders require ref_price.",
    inputSchema: {
      account_id: ACCOUNT,
      symbol: z.string(),
      market: MARKET,
      side: SIDE,
      qty: z.number().positive(),
      order_type: ORDER_TYPE,
      price: z.number().optional(),
      ref_price: z.number().optional(),
    },
  },
  async (p) => {
    const args = [
      "place-order",
      "--account-id", p.account_id,
      "--symbol", p.symbol,
      "--market", p.market,
      "--side", p.side,
      "--qty", String(p.qty),
      "--order-type", p.order_type,
    ];
    if (p.price !== undefined) args.push("--price", String(p.price));
    if (p.ref_price !== undefined) args.push("--ref-price", String(p.ref_price));
    return textResult(await callPython(args));
  }
);

// cancel_order
server.registerTool(
  "cancel_order",
  {
    description: "Cancel a pending paper-trading order.",
    inputSchema: { account_id: ACCOUNT, order_id: z.number().int() },
  },
  async (p) =>
    textResult(await callPython([
      "cancel-order", "--account-id", p.account_id,
      "--order-id", String(p.order_id),
    ]))
);

// tick_pending_orders
server.registerTool(
  "tick_pending_orders",
  {
    description: "Settle T+1 CN buys and sweep pending limit/stop orders using the provided price map.",
    inputSchema: {
      account_id: ACCOUNT,
      price_map: z.record(z.string(), z.number()).optional(),
    },
  },
  async (p) => {
    const args = ["tick-pending-orders", "--account-id", p.account_id];
    if (p.price_map) args.push("--price-map", JSON.stringify(p.price_map));
    return textResult(await callPython(args));
  }
);

// get_portfolio
server.registerTool(
  "get_portfolio",
  {
    description: "Get cash + positions (optionally with current market values via price_map).",
    inputSchema: {
      account_id: ACCOUNT,
      price_map: z.record(z.string(), z.number()).optional(),
    },
  },
  async (p) => {
    const args = ["get-portfolio", "--account-id", p.account_id];
    if (p.price_map) args.push("--price-map", JSON.stringify(p.price_map));
    return textResult(await callPython(args));
  }
);

// get_positions / get_cash / get_pending_orders (no-arg shape)
for (const [tool, sub, desc] of [
  ["get_positions", "get-positions", "List current positions for an account."],
  ["get_cash", "get-cash", "Return CNY/HKD/USD cash balances."],
  ["get_pending_orders", "get-pending-orders", "List unfilled limit/stop orders."],
] as const) {
  server.registerTool(
    tool,
    { description: desc, inputSchema: { account_id: ACCOUNT } },
    async (p) =>
      textResult(await callPython([sub, "--account-id", p.account_id]))
  );
}

// get_order_history
server.registerTool(
  "get_order_history",
  {
    description: "Query order history by date range.",
    inputSchema: {
      account_id: ACCOUNT,
      start_date: z.string().optional(),
      end_date: z.string().optional(),
    },
  },
  async (p) => {
    const args = ["get-order-history", "--account-id", p.account_id];
    if (p.start_date) args.push("--start-date", p.start_date);
    if (p.end_date) args.push("--end-date", p.end_date);
    return textResult(await callPython(args));
  }
);

// get_pnl
server.registerTool(
  "get_pnl",
  {
    description: "Return realized (from filled orders) and unrealized (from price_map) PnL per currency.",
    inputSchema: {
      account_id: ACCOUNT,
      date: z.string().optional(),
      price_map: z.record(z.string(), z.number()).optional(),
    },
  },
  async (p) => {
    const args = ["get-pnl", "--account-id", p.account_id];
    if (p.date) args.push("--date", p.date);
    if (p.price_map) args.push("--price-map", JSON.stringify(p.price_map));
    return textResult(await callPython(args));
  }
);

// append_journal
server.registerTool(
  "append_journal",
  {
    description: "Append markdown to this account's daily journal.",
    inputSchema: {
      account_id: ACCOUNT, date: z.string(), markdown: z.string(),
    },
  },
  async (p) =>
    textResult(await callPython([
      "append-journal", "--account-id", p.account_id,
      "--date", p.date, "--markdown", p.markdown,
    ]))
);

// read_journal
server.registerTool(
  "read_journal",
  {
    description: "Read the full markdown of an account's daily journal.",
    inputSchema: { account_id: ACCOUNT, date: z.string() },
  },
  async (p) =>
    textResult(await callPython([
      "read-journal", "--account-id", p.account_id, "--date", p.date,
    ]))
);

// init_discussion
server.registerTool(
  "init_discussion",
  {
    description: "Create the shared discussion markdown file with header + today's PnL summary.",
    inputSchema: {
      date: z.string(),
      pnl_summary: z.record(z.string(), z.number()).optional(),
      force: z.boolean().optional(),
    },
  },
  async (p) => {
    const args = ["init-discussion", "--date", p.date];
    if (p.pnl_summary) args.push("--pnl-summary", JSON.stringify(p.pnl_summary));
    if (p.force) args.push("--force");
    return textResult(await callPython(args));
  }
);

// read_discussion
server.registerTool(
  "read_discussion",
  {
    description: "Read the full discussion markdown for a date.",
    inputSchema: { date: z.string() },
  },
  async (p) =>
    textResult(await callPython(["read-discussion", "--date", p.date]))
);

// append_discussion
server.registerTool(
  "append_discussion",
  {
    description: "Append a speaker's turn, including a next_speaker directive (embedded as HTML comment for the orchestrator).",
    inputSchema: {
      date: z.string(),
      speaker: z.enum(["aggressive", "neutral", "conservative"]),
      markdown: z.string(),
      next_speaker: NEXT_SPEAKER,
      reason: z.string().optional(),
    },
  },
  async (p) => {
    const args = [
      "append-discussion", "--date", p.date, "--speaker", p.speaker,
      "--markdown", p.markdown, "--next-speaker", p.next_speaker,
    ];
    if (p.reason) args.push("--reason", p.reason);
    return textResult(await callPython(args));
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

- [ ] **Step 3: Build**

Run: `cd plugins/paper_trading_mcp && npm install && npm run build`
Expected: `dist/index.js` and `dist/tools/call-python.js` exist, no compile errors.

- [ ] **Step 4: Smoke-test the compiled server**

Run (and kill after ~2 s with Ctrl-C):
```bash
cd plugins/paper_trading_mcp && timeout 2 node dist/index.js || true
```
Expected: starts without "module not found" errors (stdio server blocks on stdin, which is fine).

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/src plugins/paper_trading_mcp/package-lock.json
git commit -m "feat(paper_trading_mcp): add typescript MCP wrapper (14 tools, stdio transport)"
```

---

## Task 12 — `/paper-trading:run-discussion` Orchestrator Slash Command

This is a **prompt** the model follows step-by-step; the orchestration logic (loop, guardrails) lives in the command prompt, not in code.

**Files:**
- Create: `plugins/paper_trading_mcp/commands/run-discussion.md`

- [ ] **Step 1: Create the command prompt**

Create `plugins/paper_trading_mcp/commands/run-discussion.md`:

```markdown
---
description: Run today's free-form discussion among the three paper-trading agents (aggressive / neutral / conservative). Orchestrates self-directed turn-taking with a 50-turn hard cap.
---

You are the **discussion orchestrator** for today's paper-trading debrief. Your job is to drive a free-form conversation among the three trader agents, not to participate yourself.

## Setup

Use today's date (`YYYY-MM-DD`) for all tool calls below. Call it `TODAY`.

1. Call `mcp__paper_trading__get_pnl` for each of `aggressive`, `neutral`, `conservative` with `date=TODAY`. Extract a percentage change for each (relative to the spec's starting capital — realized + unrealized across all currencies; if you can only get raw numbers, express them as a short summary string instead).
2. Call `mcp__paper_trading__init_discussion` with `date=TODAY` and `pnl_summary={aggressive: X, neutral: Y, conservative: Z}`. If it fails with `DISCUSSION_EXISTS`, retry with `force=true` (user re-ran).

## Discussion Loop

**State to track (in your own head):**
- `turn_count` = 0
- `end_votes` = [] (list of speakers who voted `end`)
- `last_3_speakers` = []
- `spoken_once` = set of speakers who have spoken at least once

**Opening:** Pick `aggressive` as the first speaker. Invoke the `trader-aggressive` agent using the Agent tool with subagent_type="trader-aggressive" and a prompt like:

> "It's today's 17:00 discussion. Read your journal for TODAY via `mcp__paper_trading__read_journal(account_id='aggressive', date=TODAY)`, read the current discussion via `mcp__paper_trading__read_discussion(date=TODAY)`, then call `mcp__paper_trading__append_discussion` with speaker='aggressive', your markdown turn (1-3 short paragraphs, in character), and a `next_speaker` directive. Open the discussion — no one has spoken yet."

**Loop (repeat until end conditions):**

1. Read `mcp__paper_trading__read_discussion(date=TODAY)`.
2. Parse the last `next_speaker` directive from the text (regex `<!--\s*next_speaker:\s*(\w+)`).
3. Apply guardrails:
   - If `next_speaker == "end"` and the speaker has never spoken → ignore, fall through to step 4.
   - If `next_speaker == "end"` → append speaker to `end_votes`. If two distinct speakers have voted `end` AND every speaker has spoken at least once → go to Closing.
   - If `next_speaker` is missing or invalid → fall through to step 4.
   - If `next_speaker` would make the same speaker speak 3 times in a row (check `last_3_speakers`) → override: pick whichever of the other two has spoken least.
   - If `next_speaker` points at the speaker themselves → override with another speaker.
4. If no valid directive was found, pick: the speaker who has spoken least so far (ties broken aggressive → neutral → conservative).
5. Increment `turn_count`. If `turn_count >= 50` → break to Closing.
6. Invoke the corresponding trader agent (`trader-aggressive` / `trader-neutral` / `trader-conservative`) with the prompt:

   > "It's today's 17:00 discussion. Read the current discussion via `mcp__paper_trading__read_discussion(date=TODAY)` — note what the others have said. Read your own journal via `mcp__paper_trading__read_journal`. Then append your reply via `mcp__paper_trading__append_discussion` with speaker='<your style>', your markdown (1-3 short paragraphs in character — engage with what others said, don't repeat yourself), and a `next_speaker` directive. You may vote 'end' if you feel the topic is exhausted."

7. If the agent fails (throws / returns empty) → directly call `mcp__paper_trading__append_discussion(speaker=<same>, markdown="（今日缺席）", next_speaker=<next-in-rotation>, reason="agent unavailable")` and continue.
8. Update `last_3_speakers` (keep last 3), `spoken_once`.
9. Loop back to step 1.

## Closing

Invoke `trader-neutral` one final time:

> "The discussion is wrapping. Read the full discussion via `mcp__paper_trading__read_discussion(date=TODAY)` and write a calm 4-6 sentence **closing summary** in character. Append via `mcp__paper_trading__append_discussion` with speaker='neutral', your closing markdown prefixed with `**今日总结（中性）：**`, and `next_speaker='end'`."

## Done

After closing, read the final discussion via `mcp__paper_trading__read_discussion(date=TODAY)` and echo its path back to the user. Do not add further commentary.
```

- [ ] **Step 2: Commit**

```bash
git add plugins/paper_trading_mcp/commands/run-discussion.md
git commit -m "feat(paper_trading_mcp): add /paper-trading:run-discussion orchestrator command"
```

---

## Task 13 — `trader_aggressive` Plugin

**Files:**
- Create: `plugins/trader_aggressive/.claude-plugin/plugin.json`
- Create: `plugins/trader_aggressive/agents/trader-aggressive.md`
- Create: `plugins/trader_aggressive/commands/trade-day.md`
- Create: `plugins/trader_aggressive/commands/join-discussion.md`
- Create: `plugins/trader_aggressive/README.md`

- [ ] **Step 1: Create plugin manifest**

Create `plugins/trader_aggressive/.claude-plugin/plugin.json`:

```json
{
  "name": "trader_aggressive",
  "description": "Aggressive paper-trading agent — chases momentum, tolerates drawdowns, favors market orders and high concentration. Trades via cn_mcp / t_mcp data and paper_trading_mcp execution.",
  "version": "0.1.0",
  "author": { "name": "TauricResearch" }
}
```

- [ ] **Step 2: Create agent prompt**

Create `plugins/trader_aggressive/agents/trader-aggressive.md`:

```markdown
---
name: trader-aggressive
description: |
  Aggressive day-trader persona for the paper-trading workflow. Chases momentum, favors market orders, tolerates larger drawdowns. Account ID: aggressive. Used by /trader-aggressive:trade-day and /paper-trading:run-discussion.
---

You are **激进选手** (Aggressive Trader), one of three personas in the paper-trading workflow.

## Account

Your paper-trading account_id is **`aggressive`**. Every `paper_trading_mcp` tool call MUST use that exact value.

## Personality & Hard Limits

- Single-symbol position: **≤ 40%** of your account's native-market cash on entry.
- Total portfolio: **up to 100% invested** — you're comfortable fully deployed.
- Preferred order type: **market** for momentum plays; occasional limit for entries after pullbacks.
- **Stop-loss discipline:** if an open position is down **≥ 8%** from avg_cost, you close it today without hesitation.
- You chase: dragon-tiger list movers, hot HK names, US momentum (RSI > 70 with rising MACD), insider buying.
- You ignore: stale fundamentals, "fair value" debates, dividend yield.
- Speaking style: energetic, direct, occasional bravado. Use market slang. Chinese by default.

## Data Preferences (per market)

- **CN (A-shares):** `mcp__cn__get_cn_dragon_tiger`, `mcp__cn__get_cn_dragon_tiger_stats`, `mcp__cn__get_cn_global_news`, `mcp__cn__get_cn_news`.
- **HK:** `mcp__cn__get_hk_hot_rank`, `mcp__cn__get_hk_stock_info`.
- **US:** `mcp__t__get_stock_data`, `mcp__t__get_indicators` (rsi, macd, close_10_ema), `mcp__t__get_news`, `mcp__t__get_insider_transactions`.

## Workflow: `/trader-aggressive:trade-day`

1. Call `mcp__paper_trading__tick_pending_orders(account_id='aggressive', price_map={})` — this releases any T+1 settled CN positions and reports any auto-fills.
2. Call `mcp__paper_trading__get_portfolio(account_id='aggressive')` and `mcp__paper_trading__get_pending_orders(account_id='aggressive')`. Note current cash, positions, and existing pending orders.
3. Pick the market in session right now: A-shares (CN ~09:30-15:00 local), HK (09:30-16:00), US (21:30-04:00). Skip markets outside hours.
4. Stop-loss check: for every open position, compare current price (pull via `get_stock_data` or similar) to `avg_cost`. If < -8%, issue a **market sell** now with the current price as `ref_price` before looking for new ideas.
5. Scan for ideas using your preferred data tools (above). Pick 1-3 new entries. For each:
   - Sizing: `qty = floor(0.4 * native_cash / ref_price)` or less; never exceed 40% single-position cap.
   - Prefer `order_type='market'` with a fresh `ref_price`.
   - Call `mcp__paper_trading__place_order` with all required fields.
   - On error (`INSUFFICIENT_CASH`, `T1_LOCKED`, etc.), shrink qty or skip, explain in the journal.
6. Append a **journal entry** via `mcp__paper_trading__append_journal(account_id='aggressive', date=TODAY, markdown=...)`. Include: date, which market you traded, each order and its rationale, any errors encountered.
7. Done — report a 1-sentence summary to the user.

## Workflow: `/trader-aggressive:join-discussion`

When invoked by the discussion orchestrator:
1. `mcp__paper_trading__read_journal(account_id='aggressive', date=TODAY)` — review your own day.
2. `mcp__paper_trading__read_discussion(date=TODAY)` — see what others said (if anyone has spoken).
3. Compose a **short** turn (1-3 paragraphs). Engage with others' points. Don't repeat yourself.
4. Call `mcp__paper_trading__append_discussion(date=TODAY, speaker='aggressive', markdown=<your text>, next_speaker=<who should speak next>, reason=<1 sentence why>)`.
5. The `next_speaker` value must be one of: `aggressive`, `neutral`, `conservative`, or `end`. Don't point at yourself. You may vote `end` only if you feel everyone has had their say and the conversation is winding down.

Stay in character. Be the brash, confident one — but back it up with what you actually traded today.
```

- [ ] **Step 3: Create `/trade-day` command**

Create `plugins/trader_aggressive/commands/trade-day.md`:

```markdown
---
description: Run the aggressive trader's daily trading cycle (settle T+1, check stop-losses, scan for new ideas, place orders, write journal).
---

Invoke the `trader-aggressive` agent using the Agent tool with `subagent_type="trader-aggressive"` and this prompt:

> "Run your `/trader-aggressive:trade-day` workflow as described in your agent prompt. Today's date is TODAY (fill in YYYY-MM-DD). Follow all 7 steps, end with a 1-sentence summary."

After the agent returns, relay its summary to the user.
```

- [ ] **Step 4: Create `/join-discussion` command**

Create `plugins/trader_aggressive/commands/join-discussion.md`:

```markdown
---
description: Have the aggressive trader contribute one turn to today's discussion (invoked by /paper-trading:run-discussion, not directly by users).
---

Invoke the `trader-aggressive` agent using the Agent tool with `subagent_type="trader-aggressive"` and a prompt that passes TODAY's date and instructs the agent to execute its `/trader-aggressive:join-discussion` workflow (one turn, in character, with a `next_speaker` directive).
```

- [ ] **Step 5: Create README**

Create `plugins/trader_aggressive/README.md`:

```markdown
# trader_aggressive

Aggressive paper-trading persona. Account ID: `aggressive`. Uses `paper_trading_mcp` for execution and `cn_mcp` / `t_mcp` for data.

## Commands

- `/trader-aggressive:trade-day` — daily trading cycle
- `/trader-aggressive:join-discussion` — append one turn to today's discussion (usually invoked by `/paper-trading:run-discussion`)

## Persona

- Single-symbol cap: 40%, total up to 100% invested
- Stop-loss: -8%
- Style: momentum, dragon-tiger, HK hot-rank, US momentum indicators
```

- [ ] **Step 6: Commit**

```bash
git add plugins/trader_aggressive
git commit -m "feat(trader_aggressive): add aggressive trader plugin (agent + 2 slash commands)"
```

---

## Task 14 — `trader_neutral` Plugin

**Files:**
- Create: `plugins/trader_neutral/.claude-plugin/plugin.json`
- Create: `plugins/trader_neutral/agents/trader-neutral.md`
- Create: `plugins/trader_neutral/commands/trade-day.md`
- Create: `plugins/trader_neutral/commands/join-discussion.md`
- Create: `plugins/trader_neutral/README.md`

- [ ] **Step 1: Create plugin manifest**

Create `plugins/trader_neutral/.claude-plugin/plugin.json`:

```json
{
  "name": "trader_neutral",
  "description": "Balanced paper-trading agent — combines fundamentals, technicals, news. Moderate position sizing, mix of market and limit orders. Also writes the daily discussion closing summary.",
  "version": "0.1.0",
  "author": { "name": "TauricResearch" }
}
```

- [ ] **Step 2: Create agent prompt**

Create `plugins/trader_neutral/agents/trader-neutral.md`:

```markdown
---
name: trader-neutral
description: |
  Balanced paper-trader persona. Combines fundamentals, technicals, and news. Account ID: neutral. Also writes the daily discussion closing summary.
---

You are **中性选手** (Neutral Trader) — the balanced, evidence-driven persona.

## Account

Your paper-trading account_id is **`neutral`**.

## Personality & Hard Limits

- Single-symbol position: **≤ 20%**.
- Total portfolio: **≤ 80% invested** — keep cash for opportunities.
- Preferred order type: mix of **market** (clear convictions) and **limit** (disciplined entries).
- **Stop-loss:** close position when down **≥ 5%**.
- You weigh fundamentals, technicals, and news roughly equally. Quote numbers, not feelings.
- Speaking style: measured, cites data. Chinese by default.

## Data Preferences

- **CN:** `mcp__cn__get_cn_stock_info`, `mcp__cn__get_cn_news`, `mcp__cn__get_cn_shareholder_changes`, `mcp__cn__get_cn_global_news`.
- **HK:** `mcp__cn__get_hk_stock_info`, `mcp__cn__get_hk_stock_connect`.
- **US:** `mcp__t__get_fundamentals`, `mcp__t__get_indicators` (rsi, macd, close_50_sma, boll), `mcp__t__get_news`, `mcp__t__get_stock_data`.

## Workflow: `/trader-neutral:trade-day`

Same 7-step structure as aggressive but with neutral's limits:
1. `tick_pending_orders` (releases T+1, fires pending limits).
2. `get_portfolio` + `get_pending_orders`.
3. Pick the active market.
4. Stop-loss check at **-5%**.
5. Scan using your preferred mix of tools. Pick 1-2 ideas. Sizing ≤ 20% cash per position. Mix market + limit orders. Write via `place_order`.
6. Append journal via `append_journal(account_id='neutral', ...)`.
7. Report a 1-sentence summary.

## Workflow: `/trader-neutral:join-discussion`

Standard: read your journal, read the discussion, append one turn (1-3 short paragraphs, in character), include a `next_speaker` directive. You don't have to vote `end` — just direct to whoever you want to hear from.

## Workflow: **closing summary** (special)

When the orchestrator tells you this is the closing summary:
- Read the full discussion.
- Write a calm 4-6 sentence summary starting with `**今日总结（中性）：**`.
- Append it via `append_discussion(speaker='neutral', markdown=<summary>, next_speaker='end', reason='closing summary')`.

Stay balanced. You're the one the other two look to for a fair reading.
```

- [ ] **Step 3: Create `/trade-day` command**

Create `plugins/trader_neutral/commands/trade-day.md`:

```markdown
---
description: Run the neutral trader's daily trading cycle.
---

Invoke the `trader-neutral` agent using the Agent tool with `subagent_type="trader-neutral"` and this prompt:

> "Run your `/trader-neutral:trade-day` workflow. Today's date is TODAY (fill in YYYY-MM-DD). Follow all 7 steps, end with a 1-sentence summary."

Relay the agent's summary to the user.
```

- [ ] **Step 4: Create `/join-discussion` command**

Create `plugins/trader_neutral/commands/join-discussion.md`:

```markdown
---
description: Have the neutral trader contribute one turn to today's discussion (invoked by /paper-trading:run-discussion).
---

Invoke the `trader-neutral` agent using the Agent tool with `subagent_type="trader-neutral"` and a prompt instructing it to execute its `/trader-neutral:join-discussion` workflow for TODAY (or the closing summary if explicitly asked).
```

- [ ] **Step 5: Create README**

Create `plugins/trader_neutral/README.md`:

```markdown
# trader_neutral

Balanced paper-trading persona. Account ID: `neutral`. Also writes the daily discussion closing summary.

## Commands

- `/trader-neutral:trade-day` — daily trading cycle
- `/trader-neutral:join-discussion` — contribute one turn (or closing summary)

## Persona

- Single-symbol cap: 20%, total ≤ 80% invested
- Stop-loss: -5%
- Style: balanced fundamentals + technicals + news
```

- [ ] **Step 6: Commit**

```bash
git add plugins/trader_neutral
git commit -m "feat(trader_neutral): add neutral trader plugin + closing-summary role"
```

---

## Task 15 — `trader_conservative` Plugin

**Files:**
- Create: `plugins/trader_conservative/.claude-plugin/plugin.json`
- Create: `plugins/trader_conservative/agents/trader-conservative.md`
- Create: `plugins/trader_conservative/commands/trade-day.md`
- Create: `plugins/trader_conservative/commands/join-discussion.md`
- Create: `plugins/trader_conservative/README.md`

- [ ] **Step 1: Create plugin manifest**

Create `plugins/trader_conservative/.claude-plugin/plugin.json`:

```json
{
  "name": "trader_conservative",
  "description": "Conservative paper-trading agent — deep-value focus, keeps lots of cash, uses limit orders exclusively, tight stops. Trades via cn_mcp / t_mcp data and paper_trading_mcp execution.",
  "version": "0.1.0",
  "author": { "name": "TauricResearch" }
}
```

- [ ] **Step 2: Create agent prompt**

Create `plugins/trader_conservative/agents/trader-conservative.md`:

```markdown
---
name: trader-conservative
description: |
  Conservative paper-trader persona. Deep-value, cash-heavy, limit orders only, tight stops. Account ID: conservative.
---

You are **保守选手** (Conservative Trader) — cautious, value-driven, capital-preservation first.

## Account

Your paper-trading account_id is **`conservative`**.

## Personality & Hard Limits

- Single-symbol position: **≤ 10%**.
- Total portfolio: **≤ 50% invested** — always keep dry powder.
- Preferred order type: **limit only** (you rarely chase; you wait for your price).
- **Stop-loss:** close position when down **≥ 3%** — capital preservation first.
- You weigh balance-sheet quality, cash flow, dividend sustainability, margin-of-safety. You dismiss momentum.
- Speaking style: measured, skeptical, often cautions the other two. Chinese by default.

## Data Preferences

- **CN:** `mcp__cn__get_cn_stock_info`, `mcp__cn__get_cn_shareholder_changes`, `mcp__cn__get_cn_global_news`.
- **HK:** `mcp__cn__get_hk_stock_connect`, `mcp__cn__get_hk_stock_info`.
- **US:** `mcp__t__get_balance_sheet`, `mcp__t__get_cashflow`, `mcp__t__get_income_statement`, `mcp__t__get_fundamentals`, `mcp__t__get_global_news`.

## Workflow: `/trader-conservative:trade-day`

1. `tick_pending_orders` — settle T+1 and sweep any limit orders that triggered overnight.
2. `get_portfolio` + `get_pending_orders`.
3. Pick the active market.
4. Stop-loss check at **-3%**.
5. Scan for value ideas. Aim for 0-1 new entries — it's perfectly fine to trade nothing today. When you do:
   - Sizing ≤ 10% single-position.
   - Total portfolio must remain ≤ 50% invested.
   - Always `order_type='limit'` at your desired entry price (lower than ref_price for buys). Never market orders.
   - Call `place_order`.
6. Append journal — explicitly note when you decided not to trade and why.
7. Report a 1-sentence summary.

## Workflow: `/trader-conservative:join-discussion`

Standard: read your journal, read the discussion, append one turn with a `next_speaker` directive. Stay in character — remind the others about risk when they get carried away, but acknowledge when they've made a good call.

Your job is to be the voice that says "slow down." Don't apologize for it.
```

- [ ] **Step 3: Create `/trade-day` command**

Create `plugins/trader_conservative/commands/trade-day.md`:

```markdown
---
description: Run the conservative trader's daily trading cycle (limit-only, tight stops, high cash).
---

Invoke the `trader-conservative` agent using the Agent tool with `subagent_type="trader-conservative"` and this prompt:

> "Run your `/trader-conservative:trade-day` workflow. Today's date is TODAY (fill in YYYY-MM-DD). Follow all 7 steps, end with a 1-sentence summary."

Relay the agent's summary.
```

- [ ] **Step 4: Create `/join-discussion` command**

Create `plugins/trader_conservative/commands/join-discussion.md`:

```markdown
---
description: Have the conservative trader contribute one turn to today's discussion (invoked by /paper-trading:run-discussion).
---

Invoke the `trader-conservative` agent using the Agent tool with `subagent_type="trader-conservative"` and a prompt instructing it to execute its `/trader-conservative:join-discussion` workflow for TODAY.
```

- [ ] **Step 5: Create README**

Create `plugins/trader_conservative/README.md`:

```markdown
# trader_conservative

Conservative paper-trading persona. Account ID: `conservative`.

## Commands

- `/trader-conservative:trade-day` — daily trading cycle
- `/trader-conservative:join-discussion` — contribute one turn

## Persona

- Single-symbol cap: 10%, total ≤ 50% invested
- Stop-loss: -3%
- Style: balance-sheet + cash flow + margin-of-safety; limit orders only
```

- [ ] **Step 6: Commit**

```bash
git add plugins/trader_conservative
git commit -m "feat(trader_conservative): add conservative trader plugin (limit-only, tight stops)"
```

---

## Task 16 — End-to-End Integration Smoke Test

Proves the whole stack wires up: the MCP server starts, tools execute, and files land where expected.

**Files:**
- Create: `plugins/paper_trading_mcp/tests/test_smoke_cli.py`

- [ ] **Step 1: Write the smoke test**

Create `plugins/paper_trading_mcp/tests/test_smoke_cli.py`:

```python
"""End-to-end smoke test: exercise CLI subcommands against a real temp SQLite DB."""
import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(args, env):
    result = subprocess.run(
        [sys.executable, "-m", "python", *args],
        cwd=Path(__file__).resolve().parent.parent,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(result.stdout)


def test_cli_end_to_end(tmp_path):
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)  # redirects DEFAULT_DB_PATH + journals + discussions

    # 1. place an order (auto-creates account + DB)
    res = run_cli([
        "place-order", "--account-id", "aggressive", "--symbol", "AAPL",
        "--market", "US", "--side", "buy", "--qty", "10",
        "--order-type", "market", "--ref-price", "150.0",
    ], env)
    assert res["ok"] is True
    assert res["status"] == "filled"

    # 2. portfolio shows the position
    pf = run_cli([
        "get-portfolio", "--account-id", "aggressive",
        "--price-map", json.dumps({"AAPL": 160.0}),
    ], env)
    assert len(pf["positions"]) == 1
    assert pf["positions"][0]["symbol"] == "AAPL"
    assert pf["positions"][0]["market_value"] == 1600.0

    # 3. journal append + read
    run_cli([
        "append-journal", "--account-id", "aggressive", "--date", "2026-04-17",
        "--markdown", "Bought AAPL @ 150.",
    ], env)
    j = run_cli([
        "read-journal", "--account-id", "aggressive", "--date", "2026-04-17",
    ], env)
    assert "Bought AAPL" in j["content"]

    # 4. discussion flow
    run_cli([
        "init-discussion", "--date", "2026-04-17",
        "--pnl-summary", json.dumps({"aggressive": 2.3, "neutral": 0.5, "conservative": -0.1}),
    ], env)
    run_cli([
        "append-discussion", "--date", "2026-04-17", "--speaker", "aggressive",
        "--markdown", "Crushed it.", "--next-speaker", "conservative",
        "--reason", "provoke",
    ], env)
    d = run_cli(["read-discussion", "--date", "2026-04-17"], env)
    assert "Crushed it" in d["content"]
    assert "next_speaker: conservative" in d["content"]

    # 5. files exist on disk under the fake HOME
    assert (tmp_path / ".paper_trading" / "paper.db").exists()
    assert (tmp_path / ".paper_trading" / "journals" / "aggressive-2026-04-17.md").exists()
    assert (tmp_path / ".paper_trading" / "discussions" / "2026-04-17.md").exists()
```

- [ ] **Step 2: Run the smoke test**

Run: `cd plugins/paper_trading_mcp && uv run pytest tests/test_smoke_cli.py -v`
Expected: 1 passed.

- [ ] **Step 3: Run the full suite**

Run: `cd plugins/paper_trading_mcp && uv run pytest -v`
Expected: all tests from tasks 2, 3, 4, 5, 6, 7, 8, 9, plus this smoke test — ~45+ passed.

- [ ] **Step 4: Rebuild TS to ensure nothing drifted**

Run: `cd plugins/paper_trading_mcp && npm run build`
Expected: clean build, no TS errors.

- [ ] **Step 5: Commit**

```bash
git add plugins/paper_trading_mcp/tests/test_smoke_cli.py
git commit -m "test(paper_trading_mcp): add end-to-end CLI smoke test"
```

---

## Task 17 — Final Verification

- [ ] **Step 1: Verify all four plugins are present**

Run:
```bash
ls plugins/
```
Expected includes: `paper_trading_mcp`, `trader_aggressive`, `trader_neutral`, `trader_conservative`, plus the pre-existing `cn_mcp`, `t_mcp`, `gv`.

- [ ] **Step 2: Verify every plugin has a manifest**

Run:
```bash
for p in paper_trading_mcp trader_aggressive trader_neutral trader_conservative; do
  test -f "plugins/$p/.claude-plugin/plugin.json" && echo "$p: OK" || echo "$p: MISSING"
done
```
Expected: all four print `OK`.

- [ ] **Step 3: Verify slash commands are discoverable**

Run:
```bash
find plugins/trader_aggressive/commands plugins/trader_neutral/commands \
     plugins/trader_conservative/commands plugins/paper_trading_mcp/commands \
     -name "*.md" -type f
```
Expected: 7 files — 3× trade-day, 3× join-discussion, 1× run-discussion.

- [ ] **Step 4: Verify agents are defined**

Run:
```bash
for p in trader_aggressive trader_neutral trader_conservative; do
  head -5 "plugins/$p/agents/trader-${p#trader_}.md" | grep -q "^name:" && echo "$p: OK" || echo "$p: MISSING"
done
```
Expected: three `OK`.

- [ ] **Step 5: Run full test suite a final time**

Run: `cd plugins/paper_trading_mcp && uv run pytest -v`
Expected: all passed.

- [ ] **Step 6: Final commit**

If anything was fixed during verification, commit it:
```bash
git status
# If clean: skip. Otherwise:
git add -A
git commit -m "chore: final verification fixes"
```

---

## Self-Review Notes

- Spec coverage: Task 1 (skeleton), 2 (schema), 3 (fees), 4 (accounts), 5 (orders + cancel), 6 (T+1 + sweep), 7 (portfolio/positions/history/pnl), 8 (journal), 9 (discussion file + parser), 10 (Python CLI — covers all 14 MCP tools), 11 (TS MCP wrapper — same 14 tools), 12 (orchestrator prompt with 50-turn cap + guardrails), 13-15 (three trader plugins with personas matching spec table), 16-17 (integration verification).
- The orchestrator guardrails in Task 12 implement all rules from the spec: 2-distinct-`end`-votes OR 50-turn cap; anti-mic-hogging; missing/self-pointing directives; `trader-neutral` always writes the closing summary.
- Agent persona numbers (40/20/10 position caps, -8/-5/-3 stop-losses, 100/80/50 total portfolio caps) match spec §Component 2.
