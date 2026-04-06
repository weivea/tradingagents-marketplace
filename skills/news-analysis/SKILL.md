---
name: news-analysis
description: Analyze recent news, global events, and insider activity for a stock. Requires the ta MCP server.
---

# News Analysis

Run a news and macroeconomic analysis for a specific stock.

## When to Use

When the user asks about news impact, macro environment, or insider activity for a stock.

## Inputs

1. **Ticker symbol** (required)
2. **Analysis date** (defaults to today)

## Execution

Dispatch a **general-purpose** sub-agent with the `ta:news-analyst` agent prompt. The sub-agent should:

1. Call `get_news(ticker=TICKER, start_date=7_DAYS_BEFORE, end_date=DATE)` for company news
2. Call `get_global_news(curr_date=DATE, look_back_days=7, limit=10)` for macro news
3. Call `get_insider_transactions(ticker=TICKER)` for insider activity
4. Write a comprehensive news report ending with a Markdown summary table

## Output

A news report covering company developments, macro context, insider activity, and impact assessment.

## A-Share Mode

When the ticker is detected as a **Chinese A-share stock** (ends with `.SS`/`.SZ` or is a 6-digit numeric code), use the **cn** MCP server tools instead of **ta** server tools for news-specific data:

**Tool routing for A-share tickers:**

| Step | US Stock Tool (ta server) | A-Share Tool (cn server) |
|------|--------------------------|--------------------------|
| Company news | `get_news(ticker, start_date, end_date)` | `get_cn_news(symbol, limit)` |
| Global/macro news | `get_global_news(curr_date, look_back_days, limit)` | `get_cn_global_news(limit)` |
| Insider / fund flow | `get_insider_transactions(ticker)` | `get_cn_dragon_tiger(symbol, start_date, end_date)` |
| Shareholder activity | N/A | `get_cn_shareholder_changes(symbol, date)` |

**A-share execution steps:**

1. Call `get_cn_news(symbol=TICKER, limit=50)` from **cn** server for company news from 东方财富
2. Call `get_cn_global_news(limit=20)` from **cn** server for Chinese macro/market news
3. Call `get_cn_dragon_tiger(symbol=TICKER, start_date=30_DAYS_BEFORE, end_date=DATE)` from **cn** server for 龙虎榜 data (replaces insider transactions as fund flow signal)
4. Call `get_cn_shareholder_changes(symbol=TICKER)` from **cn** server for top-10 shareholder changes
5. Focus the report on policy impact (CSRC, PBOC, State Council), northbound capital (北向资金), and sector rotation themes
6. Write a comprehensive news report ending with a Markdown summary table
