---
name: sentiment-analysis
description: Analyze social media sentiment and public opinion for a stock. Requires the ta MCP server.
---

# Sentiment Analysis

Run a social media and sentiment analysis for a specific stock.

## When to Use

When the user asks about sentiment, social media buzz, or public opinion for a stock.

## Inputs

1. **Ticker symbol** (required)
2. **Analysis date** (defaults to today)

## Execution

Dispatch a **general-purpose** sub-agent with the `ta:sentiment-analyst` agent prompt. The sub-agent should:

1. Call `get_news(ticker=TICKER, start_date=7_DAYS_BEFORE, end_date=DATE)` for company news
2. Analyze sentiment signals from the articles
3. Write a comprehensive sentiment report ending with a Markdown summary table

## Output

A sentiment report covering overall mood (bullish/neutral/bearish), key narratives, and actionable insights.

## A-Share Mode

When the ticker is detected as a **Chinese A-share stock** (ends with `.SS`/`.SZ` or is a 6-digit numeric code), use the **cn** MCP server tools instead of **ta** server tools for sentiment data:

**Tool routing for A-share tickers:**

| Step | US Stock Tool (ta server) | A-Share Tool (cn server) |
|------|--------------------------|--------------------------|
| Company news | `get_news(ticker, start_date, end_date)` | `get_cn_news(symbol, limit)` |
| Company info | N/A | `get_cn_stock_info(symbol)` |

**A-share execution steps:**

1. Call `get_cn_news(symbol=TICKER, limit=50)` from **cn** server for company news from 东方财富
2. Call `get_cn_stock_info(symbol=TICKER)` from **cn** server for basic company information
3. Analyze sentiment from the news articles — identify positive/negative/neutral signals
4. Consider 东方财富股吧 and 雪球 sentiment characteristics when assessing social buzz
5. Note northbound capital (北向资金) flows as a key sentiment indicator
6. Write a comprehensive sentiment report ending with a Markdown summary table
