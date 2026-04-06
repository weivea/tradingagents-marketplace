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
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│     PHASE 6: SAVE ANALYSIS REPORTS      │
│                                         │
│  Write English report → analysis/       │
│  Write Chinese report → analysis/       │
└─────────────────────────────────────────┘
```

## Execution Steps

### A-Share Market Detection

Before dispatching any sub-agents, determine whether the ticker is a **Chinese A-share stock**.

**Detection rules — a ticker is A-share if ANY of these match:**
1. It ends with `.SS` (Shanghai) or `.SZ` (Shenzhen) — e.g. `600519.SS`, `000858.SZ`
2. It is a 6-digit numeric string (e.g. `600519`, `000858`, `300750`) — automatically append `.SS` for codes starting with `6` and `.SZ` for codes starting with `0` or `3`

**When the ticker IS an A-share stock**, inject the following rules block into every sub-agent prompt (analysts, researchers, trader, risk team, portfolio manager):

```
**A-Share Market Rules:**
- Price limit: Main board ±10%, STAR/ChiNext ±20%, ST ±5%
- T+1 trading (cannot sell shares bought on the same day)
- Trading hours: 9:15-9:25 call auction, 9:30-11:30 / 13:00-15:00 continuous
- Currency: CNY (Chinese Yuan)
- Dragon tiger list (龙虎榜) replaces insider transactions as a fund flow indicator
- Policy-driven: CSRC, PBOC, and State Council policies heavily impact A-shares
- Northbound capital (北向资金 via Stock Connect) is a key sentiment indicator
```

**Data source routing table:**

| Data Need | US Stocks (MCP server) | A-Share Stocks (MCP server) |
|-----------|----------------------|---------------------------|
| Stock price (OHLCV) | `get_stock_data` (ta) | `get_stock_data` (ta) — works for `.SS`/`.SZ` tickers |
| Technical indicators | `get_indicators` (ta) | `get_indicators` (ta) — works for `.SS`/`.SZ` tickers |
| Company news | `get_news` (ta) | `get_cn_news` (**cn**) |
| Global/macro news | `get_global_news` (ta) | `get_cn_global_news` (**cn**) |
| Insider / fund flow | `get_insider_transactions` (ta) | `get_cn_dragon_tiger` (**cn**) + `get_cn_dragon_tiger_stats` (**cn**) |
| Shareholder changes | N/A | `get_cn_shareholder_changes` (**cn**) |
| Company fundamentals | `get_fundamentals` (ta) | `get_fundamentals` (ta) — works for `.SS`/`.SZ` tickers |
| Financial statements | `get_balance_sheet` / `get_cashflow` / `get_income_statement` (ta) | Same tools (ta) — work for `.SS`/`.SZ` tickers |
| Company info | N/A | `get_cn_stock_info` (**cn**) |

---

### HK Stock Market Detection

Before dispatching any sub-agents, also determine whether the ticker is a **Hong Kong stock**.

**Detection rules — a ticker is HK stock if ANY of these match:**
1. It ends with `.HK` — e.g. `0700.HK`, `9988.HK`, `1810.HK`
2. The user explicitly mentions it is a Hong Kong / 港股 stock

**Ticker format conversion:**
- For `ta` server tools (Yahoo Finance): use `XXXX.HK` format (4-digit code + `.HK`), e.g. `0700.HK`
- For `cn` server HK tools (AKShare): use 5-digit code, e.g. `00700`

**When the ticker IS an HK stock**, inject the following rules block into every sub-agent prompt:

```
**HK Stock Market Rules:**
- Trading hours: Morning 9:30-12:00, Afternoon 13:00-16:00 (HKT, UTC+8)
- Closing auction: 16:00-16:10
- No daily price limit (unlike A-share ±10%, HK stocks have no circuit breaker on individual stocks)
- T+2 settlement
- Currency: HKD (Hong Kong Dollar)
- Lot size varies by stock (not uniform 100 shares like A-shares)
- Short selling is permitted for designated securities
- Many large HK-listed stocks also trade as ADRs in the US (e.g. BABA / 9988.HK)
- Stock Connect southbound holdings (港股通) are a key sentiment indicator
```

**Data source routing table — HK stocks:**

| Data Need | MCP Server | Tool |
|-----------|-----------|------|
| Stock price (OHLCV) | ta | `get_stock_data(XXXX.HK, ...)` |
| Technical indicators | ta | `get_indicators(XXXX.HK, indicator, date)` |
| Company news | ta | `get_news(XXXX.HK, start, end)` — English news, limited precision |
| Global/macro news | ta | `get_global_news(date)` |
| Company fundamentals | ta | `get_fundamentals(XXXX.HK)` |
| Financial statements | ta | `get_balance_sheet` / `get_cashflow` / `get_income_statement(XXXX.HK)` |
| Company info (HK-specific) | **cn** | `get_hk_stock_info(XXXXX)` |
| Stock Connect holdings | **cn** | `get_hk_stock_connect(XXXXX)` |
| Hot rank / popularity | **cn** | `get_hk_hot_rank(XXXXX)` |

**Important:** Do NOT use A-share-specific tools for HK stocks: `get_cn_news`, `get_cn_dragon_tiger`, `get_cn_shareholder_changes`, `get_cn_stock_info`.

---

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
>
> **If the ticker is an A-share stock**, also include:
> {A-Share Market Rules block}
> Note price limit bands when discussing support/resistance. Account for T+1 restrictions in trading recommendations. Mention trading session context (call auction vs continuous).
>
> **If the ticker is an HK stock**, also include:
> {HK Stock Market Rules block}
> Note that HK stocks have NO daily price limit — support/resistance analysis should not reference limit-up/limit-down. Account for T+2 settlement. Consider HK trading session timing when discussing entry/exit.

**Sub-agent 2 — Sentiment Analyst:**
Prompt the sub-agent with:
> You are a Social Media & Sentiment Analyst. Analyze sentiment for {TICKER} as of {DATE}.
>
> **If the ticker is a US stock**, use MCP tools from ta:
> 1. Call `get_news(ticker="{TICKER}", start_date="{7_DAYS_BEFORE}", end_date="{DATE}")` for company news
> 2. Analyze sentiment from the articles — identify positive/negative/neutral signals
> 3. Write a comprehensive sentiment report with overall assessment and a Markdown summary table
>
> **If the ticker is an A-share stock**, use MCP tools from cn:
> {A-Share Market Rules block}
> 1. Call `get_cn_news(symbol="{TICKER}", limit=50)` from **cn** server for company news from 东方财富
> 2. Call `get_cn_stock_info(symbol="{TICKER}")` from **cn** server for basic company info
> 3. Analyze sentiment from the news — identify positive/negative/neutral signals
> 4. Consider 东方财富股吧 and 雪球 sentiment characteristics when assessing social buzz
> 5. Note northbound capital (北向资金) flows as a key sentiment indicator
> 6. Write a comprehensive sentiment report with overall assessment and a Markdown summary table
>
> **If the ticker is an HK stock**, use a mix of ta and cn MCP tools:
> {HK Stock Market Rules block}
> 1. Call `get_news(ticker="{TICKER}", start_date="{7_DAYS_BEFORE}", end_date="{DATE}")` from **ta** server for English news (note: precision is limited for HK stocks)
> 2. Call `get_hk_stock_info(symbol="{HK_CODE}")` from **cn** server for company info
> 3. Call `get_hk_stock_connect(symbol="{HK_CODE}")` from **cn** server for Stock Connect holding trends — southbound capital flows are a key sentiment indicator
> 4. Call `get_hk_hot_rank(symbol="{HK_CODE}")` from **cn** server for popularity ranking trend
> 5. HK market sentiment is influenced by both US and A-share markets — note cross-market dynamics
> 6. Write a comprehensive sentiment report with overall assessment and a Markdown summary table
>
> Use the exact ticker "{TICKER}" in every tool call.

**Sub-agent 3 — News Analyst:**
Prompt the sub-agent with:
> You are a News Analyst. Analyze news for {TICKER} as of {DATE}.
>
> **If the ticker is a US stock**, use MCP tools from ta:
> 1. Call `get_news(ticker="{TICKER}", start_date="{7_DAYS_BEFORE}", end_date="{DATE}")` for company news
> 2. Call `get_global_news(curr_date="{DATE}", look_back_days=7, limit=10)` for macroeconomic news
> 3. Call `get_insider_transactions(ticker="{TICKER}")` for insider activity
> 4. Write a comprehensive news analysis report with a Markdown summary table
>
> **If the ticker is an A-share stock**, use MCP tools from cn:
> {A-Share Market Rules block}
> 1. Call `get_cn_news(symbol="{TICKER}", limit=50)` from **cn** server for company news from 东方财富
> 2. Call `get_cn_global_news(limit=20)` from **cn** server for Chinese macro/market news
> 3. Call `get_cn_dragon_tiger(symbol="{TICKER}", start_date="{30_DAYS_BEFORE}", end_date="{DATE}")` from **cn** server for 龙虎榜 data (replaces insider transactions)
> 4. Call `get_cn_shareholder_changes(symbol="{TICKER}")` from **cn** server for top-10 shareholder changes
> 5. Focus on policy impact (CSRC, PBOC, State Council), northbound capital flows, and sector rotation
> 6. Write a comprehensive news analysis report with a Markdown summary table
>
> **If the ticker is an HK stock**, use a mix of ta and cn MCP tools:
> {HK Stock Market Rules block}
> 1. Call `get_news(ticker="{TICKER}", start_date="{7_DAYS_BEFORE}", end_date="{DATE}")` from **ta** server for English news (limited precision for HK stocks)
> 2. Call `get_global_news(curr_date="{DATE}", look_back_days=7, limit=10)` from **ta** server for macro news
> 3. Call `get_hk_stock_connect(symbol="{HK_CODE}")` from **cn** server for Stock Connect flows (replaces insider transactions / 龙虎榜 for HK)
> 4. Call `get_hk_stock_info(symbol="{HK_CODE}")` from **cn** server for company info including Stock Connect eligibility
> 5. Focus on HK-specific risks: US-China relations, regulatory changes, cross-listing dynamics
> 6. Write a comprehensive news analysis report with a Markdown summary table
> Note: Do NOT use A-share tools (get_cn_news, get_cn_dragon_tiger, get_cn_shareholder_changes) for HK stocks.
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
>
> **If the ticker is an A-share stock**, also include:
> {A-Share Market Rules block}
> Additionally call `get_cn_stock_info(symbol="{TICKER}")` from **cn** server for A-share basic info (industry classification, market cap, float shares).
> Note: Financial statements are reported under Chinese GAAP. Currency is CNY. Consider state ownership structure and any government-related entity among major shareholders.
>
> **If the ticker is an HK stock**, also include:
> {HK Stock Market Rules block}
> Additionally call `get_hk_stock_info(symbol="{HK_CODE}")` from **cn** server for HK-specific info (listing date, lot size, Stock Connect eligibility, financial snapshot).
> Note: HK-listed companies report under IFRS (not US GAAP or Chinese GAAP). Currency is typically HKD or USD. Identify if the company has weighted voting rights (WVR, marked with -W). Distinguish H-shares (mainland-incorporated) from red-chips (offshore-incorporated, mainland operations) from local HK companies.

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

---

### Phase 6: Save Analysis Reports (English + Chinese)

After presenting the final output to the user, **automatically** generate and save two comprehensive report files to the `analysis/` directory in the project root.

**File naming convention:**
- English: `analysis/{TICKER}_{DATE}_en.md`
- Chinese: `analysis/{TICKER}_{DATE}_zh.md`

Example: `analysis/NVDA_2026-04-04_en.md` and `analysis/NVDA_2026-04-04_zh.md`

**Both reports must follow this structure:**

```markdown
# {TICKER} Trading Analysis Report — {DATE}
# {TICKER} 交易分析报告 — {DATE}  (Chinese version)

> Disclaimer: This report is generated by AI for research purposes only. It does not constitute financial advice.
> 免责声明：本报告由AI生成，仅供研究参考，不构成任何投资建议。 (Chinese version)

## Final Rating / 最终评级
**{RATING}** (Buy / Overweight / Hold / Underweight / Sell)

## Executive Summary / 执行摘要
{Portfolio Manager's executive summary}

## Investment Thesis / 投资论点
{Portfolio Manager's investment thesis}

---

## Phase Details / 分析过程

### 1. Market Analysis / 市场分析
{Key highlights from market_report: trend, support/resistance levels, technical signals}

### 2. Sentiment Analysis / 舆情分析
{Key highlights from sentiment_report: overall sentiment, key signals}

### 3. News Analysis / 新闻分析
{Key highlights from news_report: major news, macro context, insider activity}

### 4. Fundamental Analysis / 基本面分析
{Key highlights from fundamentals_report: valuations, balance sheet, cash flow}

### 5. Investment Debate / 投资辩论
**Bull Case / 看多观点:** {Summary of bull arguments}
**Bear Case / 看空观点:** {Summary of bear arguments}
**Research Manager Decision / 研究经理决策:** {investment_plan summary}

### 6. Trading Decision / 交易决策
{trader_decision summary}

### 7. Risk Assessment / 风险评估
**Aggressive View / 激进观点:** {Summary}
**Conservative View / 保守观点:** {Summary}
**Neutral View / 中立观点:** {Summary}

---

*Generated by TradingAgents on {DATE}*
*由 TradingAgents 生成于 {DATE}*  (Chinese version)
```

**Execution instructions:**

1. **Write the English report first** using the Write tool to `analysis/{TICKER}_{DATE}_en.md` — compile all phase outputs into a coherent, professional English report following the structure above.

2. **Write the Chinese report** using the Write tool to `analysis/{TICKER}_{DATE}_zh.md` — translate the full report into professional Simplified Chinese. This is NOT a machine-style literal translation; produce a naturally fluent Chinese financial research report. Translate all section headers, body text, and the disclaimer. Keep ticker symbols, numerical data, and technical indicator names in English.

3. **Confirm to the user** that both reports have been saved:
   > 📄 Analysis reports saved:
   > - English: `analysis/{TICKER}_{DATE}_en.md`
   > - 中文: `analysis/{TICKER}_{DATE}_zh.md`

**Important:**
- Always create the `analysis/` directory if it doesn't exist (use `mkdir -p analysis`)
- If a report file for the same ticker and date already exists, overwrite it
- The Chinese report should read like a professional analyst wrote it natively in Chinese — not a translated document
- Include specific numbers, price levels, and data points from the analyst reports

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
