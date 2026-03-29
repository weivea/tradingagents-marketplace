# TradingAgents — Claude Code Plugin

A Claude Code / Copilot CLI plugin that brings the [TradingAgents](https://github.com/TauricResearch/TradingAgents) multi-agent trading framework to your terminal. Specialized AI agents — analysts, researchers, traders, and risk managers — collaborate to evaluate stocks and produce trading decisions.

> ⚠️ **Disclaimer**: This plugin is for research purposes only. It is not financial, investment, or trading advice.

## Setup

### 1. Build the MCP Server

```bash
cd tradingagents/plugins/t_mcp
npm install
npm run build
```

### 2. Configure — Claude Code

The project includes `.claude/settings.json` with everything preconfigured:

```json
{
  "extraKnownMarketplaces": {
    "tradingagents": {
      "source": {
        "source": "directory",
        "path": "./tradingagents"
      }
    }
  },
  "enabledPlugins": {
    "tradingagents@tradingagents": true,
    "t_mcp@tradingagents": true
  }
}
```

### 2. Configure — Copilot CLI

Option A — **启动参数 `--plugin-dir`**（推荐，无需全局安装）:

```bash
copilot --plugin-dir ./tradingagents --plugin-dir ./tradingagents/plugins/t_mcp
```

Option B — **全局安装**:

```bash
# Register the local marketplace
copilot plugin marketplace add ./tradingagents

# Install both plugins
copilot plugin install tradingagents@tradingagents
copilot plugin install t_mcp@tradingagents
```

### Plugin Components

- **`tradingagents`** — 9 skills + 12 agents for the analysis pipeline
- **`t_mcp`** — MCP server with 9 financial data tools

The MCP server declares itself via `.mcp.json` inside the plugin directory — no manual `mcpServers` configuration needed.

## Usage

### Full Analysis Pipeline

Ask Claude to analyze a stock:

```
Analyze NVDA for trading
```

This triggers the `trading-analysis` skill which runs 5 phases:

1. **Analyst Team** (parallel) — Market, sentiment, news, and fundamentals analysis
2. **Research Team** — Bull vs. bear debate → investment plan
3. **Trader** — Trading decision proposal
4. **Risk Team** — Aggressive/conservative/neutral risk debate
5. **Portfolio Manager** — Final rating (Buy/Overweight/Hold/Underweight/Sell)

### Individual Analysis

You can also run individual phases:

- `"Run market analysis on AAPL"` — Technical indicators and price trends
- `"Analyze sentiment for TSLA"` — Social media and public opinion
- `"Get fundamentals for MSFT"` — Financial statements and valuation
- `"Run news analysis for GOOGL"` — News, macro events, insider activity

## Architecture

```
User: "Analyze NVDA"
    │
    ▼
Trading Analysis Skill (Master Orchestrator)
    │
    ├── [parallel] 4 Analyst Sub-Agents → 4 Reports
    │   ├── Market Analyst (technical indicators, price action)
    │   ├── Sentiment Analyst (social media, public opinion)
    │   ├── News Analyst (company news, macro events, insider activity)
    │   └── Fundamentals Analyst (financials, valuation, balance sheet)
    │
    ├── [sequential] Bull ↔ Bear Debate (N rounds)
    │   └── Research Manager → Investment Plan
    │
    ├── Trader → Transaction Proposal (BUY/HOLD/SELL)
    │
    ├── [sequential] Risk Debate (N rounds)
    │   ├── Aggressive Analyst
    │   ├── Conservative Analyst
    │   └── Neutral Analyst
    │
    └── Portfolio Manager → Final Rating
        (Buy / Overweight / Hold / Underweight / Sell)
```

## Components

### MCP Server (9 tools)

| Tool | Description |
|------|-------------|
| `get_stock_data` | OHLCV stock price data |
| `get_indicators` | Technical indicators (SMA, EMA, MACD, RSI, Bollinger, ATR, VWMA) |
| `get_fundamentals` | Company profile, financial data, key statistics |
| `get_balance_sheet` | Balance sheet (quarterly/annual) |
| `get_cashflow` | Cash flow statement |
| `get_income_statement` | Income statement |
| `get_news` | Company-specific news |
| `get_global_news` | Global macroeconomic news |
| `get_insider_transactions` | Insider trading activity |

### Custom Agents (12)

| Agent | Role |
|-------|------|
| `market-analyst` | Technical/price analysis |
| `sentiment-analyst` | Social media & sentiment |
| `news-analyst` | News & macro analysis |
| `fundamentals-analyst` | Financial fundamentals |
| `bull-researcher` | Advocates FOR investing |
| `bear-researcher` | Advocates AGAINST investing |
| `research-manager` | Judges debate, creates investment plan |
| `trader` | Makes trading decision |
| `risk-aggressive` | Champions high-reward opportunities |
| `risk-conservative` | Prioritizes asset protection |
| `risk-neutral` | Balanced risk perspective |
| `portfolio-manager` | Final decision maker |

### Skills (9)

| Skill | Description |
|-------|-------------|
| `trading-analysis` | **Master orchestrator** — full pipeline |
| `market-analysis` | Technical analysis phase |
| `sentiment-analysis` | Sentiment analysis phase |
| `news-analysis` | News analysis phase |
| `fundamentals-analysis` | Fundamental analysis phase |
| `investment-research` | Bull/bear debate + research manager |
| `trading-decision` | Trader decision phase |
| `risk-assessment` | 3-way risk debate |
| `portfolio-decision` | Portfolio manager final decision |

## Credits

Based on the [TradingAgents](https://github.com/TauricResearch/TradingAgents) framework by [Tauric Research](https://tauric.ai/).

## Citation

```bibtex
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={TradingAgents: Multi-Agents LLM Financial Trading Framework},
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138},
}
```
