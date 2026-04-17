# trader_aggressive

Aggressive paper-trading persona. Account ID: `aggressive`. Uses `paper_trading_mcp` for execution and `cn_mcp` / `t_mcp` for data.

## Commands

- `/trader-aggressive:trade-day` — daily trading cycle
- `/trader-aggressive:join-discussion` — append one turn to today's discussion (usually invoked by `/paper-trading:run-discussion`)

## Persona

- Single-symbol cap: 40%, total up to 100% invested
- Stop-loss: -8%
- Style: momentum, dragon-tiger, HK hot-rank, US momentum indicators
