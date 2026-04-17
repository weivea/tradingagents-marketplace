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
