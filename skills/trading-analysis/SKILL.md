---
name: trading-analysis
description: Run the full TradingAgents multi-agent trading analysis pipeline. Orchestrates analysts, researchers, trader, risk team, and portfolio manager to produce a final trading decision. Requires the ta MCP server.
---

# TradingAgents — Full Analysis Pipeline

Orchestrate the complete multi-agent trading analysis for a stock, mirroring the dynamics of a real-world trading firm.

## When to Use

When the user asks to analyze a stock for trading decisions. Trigger phrases include:
- "analyze NVDA for trading"
- "should I buy AAPL?"
- "trading analysis for TSLA"
- "run TradingAgents on MSFT"
- "what's your trading recommendation for GOOGL?"

## Inputs

1. **Ticker symbol** (required) — e.g. NVDA, AAPL, TSLA
2. **Analysis date** (defaults to today)
3. **Debate rounds** (defaults to 1) — number of bull/bear and risk debate rounds

## Pipeline Architecture

```
┌─────────────────────────────────────────┐
│         PHASE 1: ANALYST TEAM           │
│  (4 sub-agents dispatched in PARALLEL)  │
├──────────┬──────────┬──────┬────────────┤
│ Market   │Sentiment │ News │Fundamentals│
│ Analyst  │ Analyst  │Analyst│  Analyst   │
└────┬─────┴────┬─────┴──┬───┴─────┬──────┘
     │          │        │         │
     ▼          ▼        ▼         ▼
  4 Reports collected
     │
     ▼
┌─────────────────────────────────────────┐
│      PHASE 2: INVESTMENT RESEARCH       │
│    (sequential bull/bear debate)        │
│                                         │
│  Bull Researcher ←→ Bear Researcher     │
│           ↓                             │
│     Research Manager → Investment Plan  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│        PHASE 3: TRADING DECISION        │
│                                         │
│  Trader → FINAL TRANSACTION PROPOSAL    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       PHASE 4: RISK ASSESSMENT          │
│    (sequential 3-way debate)            │
│                                         │
│  Aggressive ←→ Conservative ←→ Neutral  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│     PHASE 5: PORTFOLIO DECISION         │
│                                         │
│  Portfolio Manager → FINAL RATING       │
│  (Buy/Overweight/Hold/Underweight/Sell) │
└─────────────────────────────────────────┘
```

## Execution Steps

### Phase 1: Analyst Reports (PARALLEL)

Dispatch **4 sub-agents in parallel** using the Task tool with `mode="background"`:

**Sub-agent 1 — Market Analyst:**
Prompt the sub-agent with:
> You are a Market/Technical Analyst. Analyze {TICKER} as of {DATE}.
>
> Use MCP tools from ta:
> 1. Call `get_stock_data(symbol="{TICKER}", start_date="{30_DAYS_BEFORE}", end_date="{DATE}")` to get OHLCV data
> 2. Select up to 8 complementary technical indicators from: close_50_sma, close_200_sma, close_10_ema, macd, macds, macdh, rsi, boll, boll_ub, boll_lb, atr, vwma
> 3. Call `get_indicators` for each selected indicator
> 4. Write a detailed technical analysis report with specific price levels and a Markdown summary table
>
> Use the exact ticker "{TICKER}" in every tool call, preserving any exchange suffix.

**Sub-agent 2 — Sentiment Analyst:**
Prompt the sub-agent with:
> You are a Social Media & Sentiment Analyst. Analyze sentiment for {TICKER} as of {DATE}.
>
> Use MCP tools from ta:
> 1. Call `get_news(ticker="{TICKER}", start_date="{7_DAYS_BEFORE}", end_date="{DATE}")` for company news
> 2. Analyze sentiment from the articles — identify positive/negative/neutral signals
> 3. Write a comprehensive sentiment report with overall assessment and a Markdown summary table
>
> Use the exact ticker "{TICKER}" in every tool call.

**Sub-agent 3 — News Analyst:**
Prompt the sub-agent with:
> You are a News Analyst. Analyze news for {TICKER} as of {DATE}.
>
> Use MCP tools from ta:
> 1. Call `get_news(ticker="{TICKER}", start_date="{7_DAYS_BEFORE}", end_date="{DATE}")` for company news
> 2. Call `get_global_news(curr_date="{DATE}", look_back_days=7, limit=10)` for macroeconomic news
> 3. Call `get_insider_transactions(ticker="{TICKER}")` for insider activity
> 4. Write a comprehensive news analysis report with a Markdown summary table
>
> Use the exact ticker "{TICKER}" in every tool call.

**Sub-agent 4 — Fundamentals Analyst:**
Prompt the sub-agent with:
> You are a Fundamentals Analyst. Analyze {TICKER}.
>
> Use MCP tools from ta:
> 1. Call `get_fundamentals(ticker="{TICKER}")` for company overview and key statistics
> 2. Call `get_balance_sheet(ticker="{TICKER}")` for balance sheet data
> 3. Call `get_cashflow(ticker="{TICKER}")` for cash flow statement
> 4. Call `get_income_statement(ticker="{TICKER}")` for income statement
> 5. Write a comprehensive fundamental analysis report with a Markdown summary table
>
> Use the exact ticker "{TICKER}" in every tool call.

**After all 4 complete**, collect their reports as:
- `market_report` — from Market Analyst
- `sentiment_report` — from Sentiment Analyst
- `news_report` — from News Analyst
- `fundamentals_report` — from Fundamentals Analyst

Present a brief status update to the user: "✅ Analyst reports complete. Starting investment debate..."

---

### Phase 2: Investment Research (SEQUENTIAL)

Run `{DEBATE_ROUNDS}` rounds of bull/bear debate:

**For each round:**

1. **Dispatch Bull Researcher sub-agent:**
> You are a Bull Analyst advocating for investing in {TICKER}.
>
> **Analyst Reports:**
> - Market: {market_report}
> - Sentiment: {sentiment_report}
> - News: {news_report}
> - Fundamentals: {fundamentals_report}
>
> **Debate history so far:** {debate_history}
> **Last bear argument:** {last_bear_argument}
>
> Build a compelling case FOR investing. Counter the bear's arguments with specific evidence. Focus on growth potential, competitive advantages, and positive indicators. Write conversationally, engaging directly with the bear's points.
>
> Start your response with: **Bull Analyst:**

2. **Dispatch Bear Researcher sub-agent:**
> You are a Bear Analyst arguing against investing in {TICKER}.
>
> **Analyst Reports:**
> - Market: {market_report}
> - Sentiment: {sentiment_report}
> - News: {news_report}
> - Fundamentals: {fundamentals_report}
>
> **Debate history so far:** {debate_history}
> **Last bull argument:** {last_bull_argument}
>
> Build a compelling case AGAINST investing. Counter the bull's arguments with specific evidence. Focus on risks, challenges, and negative indicators. Write conversationally.
>
> Start your response with: **Bear Analyst:**

Accumulate the debate history after each turn.

3. **After all rounds, dispatch Research Manager sub-agent:**
> You are the Research Manager. Evaluate the bull/bear debate and make a definitive investment decision for {TICKER}.
>
> **Full debate history:** {full_debate_history}
> **Analyst reports:** {all 4 reports}
>
> Summarize key points, then commit to Buy, Sell, or Hold. Do NOT default to Hold simply because both sides have valid points. Include:
> 1. Your Recommendation (Buy/Sell/Hold)
> 2. Rationale
> 3. Strategic Actions for the trader

Save the result as `investment_plan`.

Present status: "✅ Investment research complete. Trader making decision..."

---

### Phase 3: Trading Decision

**Dispatch Trader sub-agent:**
> You are a Trading Agent for {TICKER}.
>
> **Investment Plan:** {investment_plan}
> **Analyst Reports:** {all 4 reports}
>
> Evaluate the investment plan against all available data. Consider timing, risk/reward, and market conditions. Make a firm trading decision.
>
> End your response with: FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**

Save the result as `trader_decision`.

Present status: "✅ Trading decision made. Starting risk assessment..."

---

### Phase 4: Risk Assessment (SEQUENTIAL)

Run `{DEBATE_ROUNDS}` rounds of 3-way risk debate:

**For each round, cycle through:**

1. **Dispatch Aggressive Analyst sub-agent:**
> You are the Aggressive Risk Analyst. Champion high-reward opportunities for {TICKER}.
>
> **Trader's decision:** {trader_decision}
> **Analyst reports:** {all 4 reports}
> **Debate history:** {risk_debate_history}
> **Last conservative response:** {last_conservative}
> **Last neutral response:** {last_neutral}
>
> Counter conservative/neutral arguments. Show why bold action is optimal. Write conversationally.
> Start with: **Aggressive Analyst:**

2. **Dispatch Conservative Analyst sub-agent:**
> You are the Conservative Risk Analyst. Prioritize asset protection for {TICKER}.
>
> **Trader's decision:** {trader_decision}
> **Analyst reports:** {all 4 reports}
> **Debate history:** {risk_debate_history}
> **Last aggressive response:** {last_aggressive}
> **Last neutral response:** {last_neutral}
>
> Counter aggressive/neutral arguments. Emphasize risks and stability. Write conversationally.
> Start with: **Conservative Analyst:**

3. **Dispatch Neutral Analyst sub-agent:**
> You are the Neutral Risk Analyst. Provide a balanced perspective on {TICKER}.
>
> **Trader's decision:** {trader_decision}
> **Analyst reports:** {all 4 reports}
> **Debate history:** {risk_debate_history}
> **Last aggressive response:** {last_aggressive}
> **Last conservative response:** {last_conservative}
>
> Challenge both sides. Advocate for balanced risk management. Write conversationally.
> Start with: **Neutral Analyst:**

Save the full risk debate as `risk_debate_history`.

Present status: "✅ Risk assessment complete. Portfolio Manager making final decision..."

---

### Phase 5: Portfolio Decision

**Dispatch Portfolio Manager sub-agent:**
> You are the Portfolio Manager. Deliver the final trading decision for {TICKER}.
>
> **Rating Scale** (use exactly one):
> - **Buy**: Strong conviction to enter or add to position
> - **Overweight**: Favorable outlook, gradually increase exposure
> - **Hold**: Maintain current position, no action needed
> - **Underweight**: Reduce exposure, take partial profits
> - **Sell**: Exit position or avoid entry
>
> **Trader's plan:** {trader_decision}
> **Risk debate history:** {risk_debate_history}
> **Analyst reports:** {all 4 reports}
>
> Required output:
> 1. **Rating**: exactly one of Buy / Overweight / Hold / Underweight / Sell
> 2. **Executive Summary**: entry strategy, position sizing, risk levels, time horizon
> 3. **Investment Thesis**: detailed reasoning anchored in evidence

---

### Final Output

Present the complete result to the user:

1. **The Final Rating** (prominently displayed): BUY / OVERWEIGHT / HOLD / UNDERWEIGHT / SELL
2. **Executive Summary** from the Portfolio Manager
3. **Investment Thesis** with key evidence
4. A collapsible summary of each phase's findings (analyst highlights, debate outcomes, trader decision)

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| Ticker | (required) | Stock ticker symbol (e.g. NVDA, AAPL) |
| Date | today | Analysis date in yyyy-mm-dd format |
| Debate rounds | 1 | Number of bull/bear and risk debate rounds |

## Important Notes

- All sub-agents should use the MCP tools from the `ta` MCP server
- The 4 analyst sub-agents run in **parallel** for speed
- All debate phases run **sequentially** (each response depends on the previous)
- This is for research purposes only — not financial advice
