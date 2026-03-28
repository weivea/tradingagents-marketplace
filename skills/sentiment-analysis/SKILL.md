---
name: sentiment-analysis
description: Analyze social media sentiment and public opinion for a stock. Requires the tradingagents-data MCP server.
---

# Sentiment Analysis

Run a social media and sentiment analysis for a specific stock.

## When to Use

When the user asks about sentiment, social media buzz, or public opinion for a stock.

## Inputs

1. **Ticker symbol** (required)
2. **Analysis date** (defaults to today)

## Execution

Dispatch a **general-purpose** sub-agent with the `tradingagents:sentiment-analyst` agent prompt. The sub-agent should:

1. Call `get_news(ticker=TICKER, start_date=7_DAYS_BEFORE, end_date=DATE)` for company news
2. Analyze sentiment signals from the articles
3. Write a comprehensive sentiment report ending with a Markdown summary table

## Output

A sentiment report covering overall mood (bullish/neutral/bearish), key narratives, and actionable insights.
