---
name: fundamentals-analysis
description: Perform fundamental analysis on a company — financials, valuation, balance sheet. Requires the ta MCP server.
---

# Fundamentals Analysis

Run a fundamental analysis for a specific company.

## When to Use

When the user asks about company financials, valuation, balance sheet health, or fundamental analysis.

## Inputs

1. **Ticker symbol** (required)
2. **Analysis date** (optional)

## Execution

Dispatch a **general-purpose** sub-agent with the `ta:fundamentals-analyst` agent prompt. The sub-agent should:

1. Call `get_fundamentals(ticker=TICKER)` for company overview
2. Call `get_balance_sheet(ticker=TICKER)` for balance sheet
3. Call `get_cashflow(ticker=TICKER)` for cash flow
4. Call `get_income_statement(ticker=TICKER)` for income statement
5. Write a comprehensive fundamentals report ending with a Markdown summary table

## Output

A fundamentals report covering financials, valuation metrics, balance sheet health, and key risks.
