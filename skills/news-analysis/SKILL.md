---
name: news-analysis
description: Analyze recent news, global events, and insider activity for a stock. Requires the tradingagents-data MCP server.
---

# News Analysis

Run a news and macroeconomic analysis for a specific stock.

## When to Use

When the user asks about news impact, macro environment, or insider activity for a stock.

## Inputs

1. **Ticker symbol** (required)
2. **Analysis date** (defaults to today)

## Execution

Dispatch a **general-purpose** sub-agent with the `tradingagents:news-analyst` agent prompt. The sub-agent should:

1. Call `get_news(ticker=TICKER, start_date=7_DAYS_BEFORE, end_date=DATE)` for company news
2. Call `get_global_news(curr_date=DATE, look_back_days=7, limit=10)` for macro news
3. Call `get_insider_transactions(ticker=TICKER)` for insider activity
4. Write a comprehensive news report ending with a Markdown summary table

## Output

A news report covering company developments, macro context, insider activity, and impact assessment.
