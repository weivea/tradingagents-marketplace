# Paper Trading — Realized PnL Fix (Design)

**Date:** 2026-04-21
**Plugin:** `plugins/paper_trading_mcp`
**Status:** Approved for planning

## Problem

`portfolio.get_pnl()` returns `realized_*` values that are actually **net cash flow from fills**, not realized profit-and-loss. The current loop signs every filled order by side (buy = −1, sell = +1) and sums `qty * price − fee` — so a pure-buy account shows a large negative "realized" number equal to its cash outflow.

Observed on smoke test: 200 shares bought (no sells) → `realized_cny = −290,072.5` (= 100×1500 + 37.5 + 100×1400 + 35). True realized should be 0.

This misleads any consumer of the PnL API, including the three trader agents' discussion / trade-day flows.

## Decisions

Three choices fixed in brainstorming:

1. **Cost-basis method:** weighted-average cost (matches existing `positions.avg_cost`).
2. **Fee treatment:** capitalize buy fees into `avg_cost`; deduct sell fees from realized at sell time.
3. **Persistence:** add `orders.realized_pnl REAL` column; write once on sell fill; aggregate via `SUM`.

Rejected alternatives (and why):

- **FIFO batches** — needs a new "lots" concept; overkill for this simulator.
- **`positions.realized_pnl` accumulator** — positions are DELETED on full close, so the running total is fragile.
- **Query-time replay without persistence** — O(N) every query; reconstructing avg_cost at each historical sell is awkward.

## Scope

**In scope:**
- `portfolio.get_pnl` semantics.
- `orders._upsert_position_buy` fee capitalization.
- Sell fill paths in `orders.place_order` and `settlement._sweep_pending` writing `realized_pnl`.
- Idempotent schema migration adding `orders.realized_pnl`.

**Out of scope:**
- `init_discussion.pnl_summary` key-name confusion (separate concern; tracked as a docs issue).
- Concurrency / locking (single-connection sqlite today; YAGNI).
- Backfilling `realized_pnl` for historical sell rows (ambiguous; left NULL → excluded from SUM).
- FX normalization of realized PnL (stays per-currency, matching existing API shape).

## Architecture

### Schema change

Add one column:

```sql
ALTER TABLE orders ADD COLUMN realized_pnl REAL;  -- NULL for buys and pre-migration rows
```

Migration hook: `db.init_schema()` checks `PRAGMA table_info(orders)`; runs the `ALTER` if the column is missing. Idempotent. Failure throws (fail-fast on startup).

### Invariants

- `avg_cost` reflects **fee-capitalized** per-share cost at all times.
- `realized_pnl` on an order row is non-NULL **iff** `side='sell' AND status='filled'` and that order was filled **after** the migration ran.
- Currency of `realized_pnl` = `CURRENCY_BY_MARKET[market]`.
- Equity identity:
  `final_cash_per_currency + Σ(qty × latest_price) − initial_cash_per_currency == realized + unrealized` (within float tolerance).

### Buy fill path

Single entry point: `orders._upsert_position_buy`. Change `new_cost` formula to capitalize fee:

- New position: `avg_cost = (qty * fill_price + fee) / qty`
- Existing position: `avg_cost = (old_qty * old_avg_cost + qty * fill_price + fee) / (old_qty + qty)`

Caller must pass `fee` into `_upsert_position_buy` (signature changes). Both call sites (`orders.place_order`, `settlement._sweep_pending`) already compute `fee` before the upsert.

Order row: `realized_pnl = NULL`.

### Sell fill path

Two sites to patch:

1. `orders.place_order` — immediate-fill branch.
2. `settlement._sweep_pending` — limit/stop trigger branch.

Both already call `_get_position(...)` (or can) and already compute `sell_fee`. Add:

```python
pos = _get_position(conn, account_id, symbol, market)
if pos is None:
    raise RuntimeError("position disappeared before sell fill")
avg_cost_at_sell = pos["avg_cost"]
realized = (fill_price - avg_cost_at_sell) * qty - sell_fee
# include realized in the UPDATE/INSERT of the sell order row
```

`_update_position_sell` is unchanged (standard weighted-average: selling does not touch `avg_cost`). Full close still DELETEs the position row — the realized number is already captured in `orders`.

### Query path

`portfolio.get_pnl`:

```sql
SELECT market, SUM(realized_pnl) AS r
FROM orders
WHERE account_id = ?
  AND status = 'filled'
  AND side = 'sell'
  AND realized_pnl IS NOT NULL
  [AND substr(filled_at, 1, 10) = ?]    -- when date provided
GROUP BY market;
```

Bucket by `CURRENCY_BY_MARKET[market]` into `realized_cny / realized_hkd / realized_usd`.

`unrealized_*` logic unchanged (already uses `price_map − avg_cost`; now benefits from fee-capitalized `avg_cost`).

Return shape is unchanged — consumers keep working.

## Data-flow walk-through (the smoke-test scenario)

Initial: 1,000,000 CNY cash, no positions.

| Step | Action | Formula | Result |
|---|---|---|---|
| 1 | Buy 100 @ 1500, fee 37.5 | `avg_cost = (100*1500 + 37.5)/100` | `avg_cost = 1500.375`, cash = 849,962.5, realized_pnl row = NULL |
| 2 | Buy 100 @ 1400, fee 35   | `avg_cost = (100*1500.375 + 100*1400 + 35)/200` | `avg_cost = 1450.3625`, cash = 709,927.5, realized_pnl row = NULL |
| 3 | Query `get_pnl`, price_map={1500} | realized = 0 (no sells), unrealized = (1500−1450.3625)*200 | **realized 0, unrealized 9,927.5** |
| 4 | Sell 100 @ 1600, fee 40  | `realized = (1600−1450.3625)*100 − 40` | realized_pnl row = 14,923.75, cash = 869,887.5, position 100 @ 1450.3625 |
| 5 | Query `get_pnl`, price_map={1600} | realized = 14,923.75, unrealized = (1600−1450.3625)*100 | **realized 14,923.75, unrealized 14,963.75, total 29,887.5** |

Equity check step 5: 869,887.5 + 100×1600 − 1,000,000 = 29,887.5 ✓.

## Error handling

| Failure | Response |
|---|---|
| ALTER TABLE fails on startup | Raise; surface early (bad DB = bad data). |
| Sell fill reaches `_get_position → None` | `RuntimeError` — indicates invariant broken upstream; do not silently write garbage. |
| Old sell row with `realized_pnl IS NULL` | Filtered out of SUM. Not retroactively computed (ambiguous cost basis historically). |
| Concurrent writers | Not addressed (out of scope; same as today). |

## Testing plan

New file: `plugins/paper_trading_mcp/python/tests/test_realized_pnl.py`

Written **TDD**: each test is written and run red first, then made green.

| # | Test | Assertion |
|---|---|---|
| 1 | `test_buy_does_not_produce_realized` | After buys only: `get_pnl.realized_cny == 0`; all order rows have `realized_pnl IS NULL`. |
| 2 | `test_fee_capitalized_into_avg_cost` | Single buy 100 @ 1500 fee=37.5 → `position.avg_cost == 1500.375`. |
| 3 | `test_sell_realized_with_weighted_cost` | Replay smoke-test scenario + sell 100 @ 1600 fee=40 → `realized_cny == 14923.75`, `unrealized_cny == 14963.75` at price 1600. |
| 4 | `test_equity_identity` (**golden**) | Random 5-step buy/sell sequence → `(final_cash + market_value) − initial_cash == realized + unrealized` within 1e-6. |
| 5 | `test_sweep_sell_path_also_writes_realized` | Pending limit-sell triggered by `tick_pending_orders` → that order row has correct `realized_pnl`. |
| 6 | `test_migration_idempotent` | Open an in-memory DB without the column, call `init_schema` twice, verify column added and no error. |
| 7 | `test_old_orders_excluded_from_sum` | Manually INSERT a sell row with `realized_pnl=NULL`; `get_pnl` does not include it. |

### Acceptance

- All 7 new tests pass.
- All existing tests pass: `uv run --project . pytest -v` (inside `plugins/paper_trading_mcp`).
- Manual re-run of the smoke-test MCP calls returns `realized_cny == 0`, `unrealized_cny ≈ 9927.5` at price 1500 (instead of `−290072.5 / +10000`).

## Files touched

- `python/db.py` — schema string + idempotent migration helper
- `python/orders.py` — `_upsert_position_buy` fee capitalization; sell paths write `realized_pnl`
- `python/settlement.py` — sweep sell path writes `realized_pnl`
- `python/portfolio.py` — `get_pnl` query switched to `SUM(realized_pnl)` over sells
- `python/tests/test_realized_pnl.py` — new
