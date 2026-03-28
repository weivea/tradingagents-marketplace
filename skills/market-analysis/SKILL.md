---
name: market-analysis
description: Run technical/market analysis on a stock using price data and indicators. Requires the tradingagents-data MCP server.
---

# Market Analysis

Run a technical/market analysis for a specific stock ticker and date.

## When to Use

When the user asks for market analysis, technical analysis, or chart analysis of a stock.

## Inputs

1. **Ticker symbol** (required, e.g. NVDA, AAPL, TSLA)
2. **Analysis date** (defaults to today if not specified)

## Execution

Dispatch a **general-purpose** sub-agent with the `tradingagents:market-analyst` agent prompt. The sub-agent should:

1. Call `get_stock_data(symbol=TICKER, start_date=30_DAYS_BEFORE, end_date=DATE)` to get OHLCV data
2. Select up to 8 complementary indicators from: `close_50_sma`, `close_200_sma`, `close_10_ema`, `macd`, `macds`, `macdh`, `rsi`, `boll`, `boll_ub`, `boll_lb`, `atr`, `vwma`
3. Call `get_indicators` for each selected indicator
4. Write a detailed technical analysis report ending with a Markdown summary table

## Output

A comprehensive technical analysis report with trend analysis, support/resistance levels, momentum assessment, and actionable insights.
