# TradingAgents — Claude Code Plugin

A Claude Code / Copilot CLI plugin that brings the [TradingAgents](https://github.com/TauricResearch/TradingAgents) multi-agent trading framework to your terminal. Specialized AI agents — analysts, researchers, traders, and risk managers — collaborate to evaluate stocks and produce trading decisions.

> ⚠️ **Disclaimer**: This plugin is for research purposes only. It is not financial, investment, or trading advice.

## Setup

### 1. Build the MCP Servers

```bash
# Financial data MCP server
cd ta/plugins/t_mcp
npm install
npm run build

# Video generation MCP server (requires uv — https://docs.astral.sh/uv/)
cd ../gv
npm run setup    # one-click: npm install + tsc + uv venv + playwright
```

### 2. Configure — Claude Code

The project includes `.claude/settings.json` with everything preconfigured:

```json
{
  "extraKnownMarketplaces": {
    "ta": {
      "source": {
        "source": "directory",
        "path": "./ta"
      }
    }
  },
  "enabledPlugins": {
    "ta@ta": true,
    "t_mcp@ta": true
  }
}
```

### 2. Configure — Copilot CLI

Option A — **启动参数 `--plugin-dir`**（推荐，无需全局安装）:

```bash
copilot --plugin-dir ./ta --plugin-dir ./ta/plugins/t_mcp
```

Option B — **全局安装**:

```bash
# Register the local marketplace
copilot plugin marketplace add ./ta

# Install both plugins
copilot plugin install ta@ta
copilot plugin install t_mcp@ta
```

### Plugin Components

- **`ta`** — 10 skills + 13 agents for the analysis pipeline
- **`t_mcp`** — MCP server with 9 financial data tools
- **`gv`** — MCP server with 5 video generation tools + Python CLI

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

### MCP Server — t_mcp (9 tools)

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

### Custom Agents (13)

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
| `video-scriptwriter` | Extracts short-video narration scripts |

### Skills (10)

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
| `gen-video` | Convert analysis reports to narrated videos |

### MCP Server — gv (5 tools)

| Tool | Description |
|------|-------------|
| `parse_report` | Parse Chinese Markdown report into structured sections |
| `generate_tts` | Chinese TTS audio + timestamps + SRT subtitles |
| `render_frames` | Render text as scroll image or per-slide images |
| `compose_video` | Compose MP4 from frames + audio |
| `generate_video` | One-click report → video |

## Gen-Video — Report to Video

Convert Chinese analysis reports (`analysis/*_zh.md`) into narrated vertical videos for social media (抖音/B站/小红书).

```
为 NIO 报告生成视频
```

This produces two versions:

- **Full version** (`*_full.mp4`) — 8-15 min, full-text narration with scrolling text
- **Short version** (`*_short.mp4`) — 60-90s, AI-extracted key points with slide transitions

Or use the CLI directly:

```bash
cd plugins/gv
uv run python -m python generate "../../analysis/NIO_2026-04-04_zh.md" --version both
```

Output lands in `gen-video/output/`. See [`plugins/gv/README.md`](plugins/gv/README.md) for full documentation.

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
