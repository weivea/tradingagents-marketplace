# A-Share Trading Analysis Support — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Chinese A-share stock analysis support to the TradingAgents framework by building a new `cn_mcp` Python MCP server (AKShare data) and updating orchestration skills/agent prompts for market-aware routing.

**Architecture:** New `plugins/cn_mcp/` Python MCP plugin provides 6 A-share data tools (news, dragon-tiger, shareholders, stock info) via AKShare. Existing `t_mcp` continues to serve price/indicators/fundamentals for all markets (Yahoo Finance works for A-shares). Orchestration skills detect `.SS`/`.SZ` tickers and route news/insider calls to cn_mcp. Agent prompts gain conditional A-share market rules.

**Tech Stack:** Python 3.10+, uv, AKShare, MCP Python SDK, TypeScript MCP wrapper (Node.js)

---

## Task 1: Scaffold cn_mcp plugin directory structure

**Files:**
- Create: `plugins/cn_mcp/.claude-plugin/plugin.json`
- Create: `plugins/cn_mcp/.mcp.json`
- Create: `plugins/cn_mcp/pyproject.toml`
- Create: `plugins/cn_mcp/.gitignore`
- Create: `plugins/cn_mcp/python/__init__.py`
- Create: `plugins/cn_mcp/python/__main__.py`

**Step 1: Create plugin.json**

```json
// plugins/cn_mcp/.claude-plugin/plugin.json
{
  "name": "cn_mcp",
  "description": "MCP server providing 6 Chinese A-share data tools (news, dragon tiger list, shareholder changes, stock info) via AKShare for the TradingAgents framework",
  "version": "0.1.0",
  "author": {
    "name": "TauricResearch"
  }
}
```

**Step 2: Create .mcp.json**

This tells the plugin harness how to start the MCP server. Follow the same pattern as `plugins/t_mcp/.mcp.json` and `plugins/gv/.mcp.json` — a TS Node.js process that delegates to Python via `callPython`.

```json
// plugins/cn_mcp/.mcp.json
{
  "mcpServers": {
    "cn": {
      "type": "stdio",
      "command": "node",
      "args": ["./plugins/cn_mcp/dist/index.js"],
      "env": {}
    }
  }
}
```

**Step 3: Create pyproject.toml**

```toml
# plugins/cn_mcp/pyproject.toml
[project]
name = "cn-mcp"
version = "0.1.0"
description = "Chinese A-share market data tools via AKShare"
requires-python = ">=3.10"
dependencies = [
    "akshare>=1.14.0",
]
```

**Step 4: Create .gitignore**

```
# plugins/cn_mcp/.gitignore
.venv/
__pycache__/
*.pyc
node_modules/
dist/
```

**Step 5: Create Python package files**

```python
# plugins/cn_mcp/python/__init__.py
```

```python
# plugins/cn_mcp/python/__main__.py
"""CLI entry point: python -m python <command> [args]"""

import argparse
import json
import sys
import io

# Force UTF-8 stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def cmd_cn_news(args: argparse.Namespace) -> None:
    from .news import get_cn_news
    result = get_cn_news(args.symbol, limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_cn_global_news(args: argparse.Namespace) -> None:
    from .news import get_cn_global_news
    result = get_cn_global_news(limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_cn_dragon_tiger(args: argparse.Namespace) -> None:
    from .dragon_tiger import get_cn_dragon_tiger
    result = get_cn_dragon_tiger(args.symbol, args.start_date, args.end_date)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_cn_dragon_tiger_stats(args: argparse.Namespace) -> None:
    from .dragon_tiger import get_cn_dragon_tiger_stats
    result = get_cn_dragon_tiger_stats(args.period)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_cn_shareholder(args: argparse.Namespace) -> None:
    from .shareholder import get_cn_shareholder_changes
    result = get_cn_shareholder_changes(args.symbol, args.date)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_cn_stock_info(args: argparse.Namespace) -> None:
    from .stock_info import get_cn_stock_info
    result = get_cn_stock_info(args.symbol)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="cn-mcp", description="CN A-Share Data CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # cn-news
    p = sub.add_parser("cn-news", help="Get A-share company news")
    p.add_argument("symbol", help="6-digit A-share code e.g. 600519")
    p.add_argument("--limit", type=int, default=20, help="Max articles")
    p.set_defaults(func=cmd_cn_news)

    # cn-global-news
    p = sub.add_parser("cn-global-news", help="Get Chinese macro/market news")
    p.add_argument("--limit", type=int, default=20, help="Max articles")
    p.set_defaults(func=cmd_cn_global_news)

    # cn-dragon-tiger
    p = sub.add_parser("cn-dragon-tiger", help="Get dragon tiger list detail")
    p.add_argument("symbol", help="6-digit A-share code e.g. 600519")
    p.add_argument("--start-date", required=True, help="Start date YYYYMMDD")
    p.add_argument("--end-date", required=True, help="End date YYYYMMDD")
    p.set_defaults(func=cmd_cn_dragon_tiger)

    # cn-dragon-tiger-stats
    p = sub.add_parser("cn-dragon-tiger-stats", help="Get dragon tiger statistics")
    p.add_argument("--period", default="近一月", help="近一月/近三月/近六月/近一年")
    p.set_defaults(func=cmd_cn_dragon_tiger_stats)

    # cn-shareholder
    p = sub.add_parser("cn-shareholder", help="Get shareholder changes")
    p.add_argument("symbol", help="6-digit A-share code e.g. 600519")
    p.add_argument("--date", required=True, help="Report date YYYYMMDD")
    p.set_defaults(func=cmd_cn_shareholder)

    # cn-stock-info
    p = sub.add_parser("cn-stock-info", help="Get A-share stock info")
    p.add_argument("symbol", help="6-digit A-share code e.g. 600519")
    p.set_defaults(func=cmd_cn_stock_info)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

**Step 6: Run `uv sync` to create venv and install akshare**

```bash
cd plugins/cn_mcp && uv sync
```

Expected: `.venv/` created, akshare installed successfully.

**Step 7: Commit**

```bash
git add plugins/cn_mcp/
git commit -m "feat(cn_mcp): scaffold plugin directory structure with pyproject.toml and CLI entry point"
```

---

## Task 2: Implement Python data tools — news.py

**Files:**
- Create: `plugins/cn_mcp/python/news.py`

**Step 1: Implement get_cn_news and get_cn_global_news**

```python
# plugins/cn_mcp/python/news.py
"""A-share news data via AKShare (东方财富 source)."""

import akshare as ak


def _yahoo_to_akshare(ticker: str) -> str:
    """Convert Yahoo-format ticker to AKShare format: 600519.SS → 600519"""
    return ticker.split(".")[0]


def get_cn_news(symbol: str, limit: int = 20) -> dict:
    """Get company-specific news for an A-share stock.

    Args:
        symbol: Ticker in Yahoo format (600519.SS) or raw (600519)
        limit: Max articles to return
    """
    code = _yahoo_to_akshare(symbol)
    try:
        df = ak.stock_news_em(symbol=code)
        if df is None or df.empty:
            return {"text": f"No news found for {symbol}.", "count": 0}

        articles = []
        for _, row in df.head(limit).iterrows():
            articles.append(
                f"- [{row.get('发布时间', 'N/A')}] **{row.get('新闻标题', 'N/A')}**\n"
                f"  来源: {row.get('文章来源', 'N/A')}\n"
                f"  摘要: {str(row.get('新闻内容', ''))[:200]}"
            )

        header = f"# A股新闻 — {symbol}\n\n共 {len(articles)} 条\n\n"
        return {"text": header + "\n\n".join(articles), "count": len(articles)}

    except Exception as e:
        return {"text": f"Error fetching news for {symbol}: {e}", "count": 0}


def get_cn_global_news(limit: int = 20) -> dict:
    """Get Chinese macro/market news.

    Uses AKShare to search for macro-economic and market-wide news
    from Chinese sources (东方财富).
    """
    keywords = ["A股", "央行", "证监会", "宏观经济", "GDP"]
    all_articles: list[str] = []
    seen_titles: set[str] = set()

    for keyword in keywords:
        try:
            df = ak.stock_news_em(symbol=keyword)
            if df is None or df.empty:
                continue
            for _, row in df.head(5).iterrows():
                title = row.get("新闻标题", "")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_articles.append(
                        f"- [{row.get('发布时间', 'N/A')}] **{title}**\n"
                        f"  来源: {row.get('文章来源', 'N/A')}\n"
                        f"  摘要: {str(row.get('新闻内容', ''))[:200]}"
                    )
        except Exception:
            continue

    if not all_articles:
        return {"text": "No Chinese macro news found.", "count": 0}

    articles = all_articles[:limit]
    header = f"# 中国宏观/市场新闻\n\n共 {len(articles)} 条\n\n"
    return {"text": header + "\n\n".join(articles), "count": len(articles)}
```

**Step 2: Smoke test the news tool manually**

```bash
cd plugins/cn_mcp && uv run python -m python cn-news 600519 --limit 5
```

Expected: JSON output with `text` containing Chinese news articles about 贵州茅台, `count` > 0.

```bash
cd plugins/cn_mcp && uv run python -m python cn-global-news --limit 5
```

Expected: JSON output with macro/market news from Chinese sources.

**Step 3: Commit**

```bash
git add plugins/cn_mcp/python/news.py
git commit -m "feat(cn_mcp): implement get_cn_news and get_cn_global_news via AKShare"
```

---

## Task 3: Implement Python data tools — dragon_tiger.py

**Files:**
- Create: `plugins/cn_mcp/python/dragon_tiger.py`

**Step 1: Implement dragon tiger tools**

```python
# plugins/cn_mcp/python/dragon_tiger.py
"""Dragon tiger list (龙虎榜) data via AKShare."""

import akshare as ak


def _yahoo_to_akshare(ticker: str) -> str:
    return ticker.split(".")[0]


def get_cn_dragon_tiger(symbol: str, start_date: str, end_date: str) -> dict:
    """Get dragon tiger list detail for a specific stock.

    The dragon tiger list (龙虎榜) shows institutional and large trader activity
    on stocks that had unusual price/volume movements.

    Args:
        symbol: Ticker in Yahoo format (600519.SS) or raw (600519)
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
    """
    code = _yahoo_to_akshare(symbol)
    try:
        df = ak.stock_lhb_detail_em(
            start_date=start_date,
            end_date=end_date,
        )
        if df is None or df.empty:
            return {"text": f"No dragon tiger data found for period {start_date}-{end_date}.", "count": 0}

        # Filter for our specific stock
        code_col = "代码" if "代码" in df.columns else df.columns[0]
        stock_df = df[df[code_col].astype(str).str.contains(code)]

        if stock_df.empty:
            return {
                "text": f"No dragon tiger entries for {symbol} in period {start_date}-{end_date}.",
                "count": 0,
            }

        entries = []
        for _, row in stock_df.iterrows():
            entry_parts = []
            for col in stock_df.columns:
                val = row.get(col)
                if val is not None and str(val) != "nan":
                    entry_parts.append(f"  - **{col}**: {val}")
            entries.append("\n".join(entry_parts))

        header = f"# 龙虎榜 — {symbol} ({start_date} 至 {end_date})\n\n共 {len(entries)} 条记录\n\n"
        return {"text": header + "\n\n---\n\n".join(entries), "count": len(entries)}

    except Exception as e:
        return {"text": f"Error fetching dragon tiger data: {e}", "count": 0}


def get_cn_dragon_tiger_stats(period: str = "近一月") -> dict:
    """Get dragon tiger list statistics for a period.

    Args:
        period: One of "近一月", "近三月", "近六月", "近一年"
    """
    try:
        df = ak.stock_lhb_stock_statistic_em(symbol=period)
        if df is None or df.empty:
            return {"text": f"No dragon tiger statistics for {period}.", "count": 0}

        entries = []
        for _, row in df.head(30).iterrows():
            entry_parts = []
            for col in df.columns:
                val = row.get(col)
                if val is not None and str(val) != "nan":
                    entry_parts.append(f"  - **{col}**: {val}")
            entries.append("\n".join(entry_parts))

        header = f"# 龙虎榜统计 — {period}\n\n前 {len(entries)} 只股票\n\n"
        return {"text": header + "\n\n---\n\n".join(entries), "count": len(entries)}

    except Exception as e:
        return {"text": f"Error fetching dragon tiger stats: {e}", "count": 0}
```

**Step 2: Smoke test**

```bash
cd plugins/cn_mcp && uv run python -m python cn-dragon-tiger 600519 --start-date 20260301 --end-date 20260406
```

Expected: JSON with dragon tiger data (or "no entries" if Moutai wasn't on the list in that period — that's fine).

```bash
cd plugins/cn_mcp && uv run python -m python cn-dragon-tiger-stats --period 近一月
```

Expected: JSON with top 30 stocks by dragon tiger activity.

**Step 3: Commit**

```bash
git add plugins/cn_mcp/python/dragon_tiger.py
git commit -m "feat(cn_mcp): implement dragon tiger list tools via AKShare"
```

---

## Task 4: Implement Python data tools — shareholder.py and stock_info.py

**Files:**
- Create: `plugins/cn_mcp/python/shareholder.py`
- Create: `plugins/cn_mcp/python/stock_info.py`

**Step 1: Implement shareholder changes**

```python
# plugins/cn_mcp/python/shareholder.py
"""Top 10 shareholder changes via AKShare."""

import akshare as ak


def _yahoo_to_akshare(ticker: str) -> str:
    return ticker.split(".")[0]


def get_cn_shareholder_changes(symbol: str, date: str) -> dict:
    """Get top-10 tradable shareholder changes for a stock.

    Args:
        symbol: Ticker in Yahoo format (600519.SS) or raw (600519)
        date: Report date in YYYYMMDD format (e.g. 20250930 for Q3 2025)
    """
    code = _yahoo_to_akshare(symbol)
    try:
        df = ak.stock_gdfx_free_holding_change_em(date=date)
        if df is None or df.empty:
            return {"text": f"No shareholder data for date {date}.", "count": 0}

        # Filter for our stock
        code_col = None
        for col in df.columns:
            if "代码" in str(col):
                code_col = col
                break
        if code_col is None:
            code_col = df.columns[0]

        stock_df = df[df[code_col].astype(str).str.contains(code)]

        if stock_df.empty:
            return {"text": f"No shareholder change data for {symbol} on {date}.", "count": 0}

        entries = []
        for _, row in stock_df.iterrows():
            entry_parts = []
            for col in stock_df.columns:
                val = row.get(col)
                if val is not None and str(val) != "nan":
                    entry_parts.append(f"  - **{col}**: {val}")
            entries.append("\n".join(entry_parts))

        header = f"# 十大流通股东变动 — {symbol} (报告期: {date})\n\n共 {len(entries)} 条\n\n"
        return {"text": header + "\n\n---\n\n".join(entries), "count": len(entries)}

    except Exception as e:
        return {"text": f"Error fetching shareholder data: {e}", "count": 0}
```

**Step 2: Implement stock info**

```python
# plugins/cn_mcp/python/stock_info.py
"""A-share stock basic info via AKShare."""

import akshare as ak


def _yahoo_to_akshare(ticker: str) -> str:
    return ticker.split(".")[0]


def get_cn_stock_info(symbol: str) -> dict:
    """Get basic info for an A-share stock (sector, market cap, shares, etc).

    Args:
        symbol: Ticker in Yahoo format (600519.SS) or raw (600519)
    """
    code = _yahoo_to_akshare(symbol)
    try:
        df = ak.stock_individual_info_em(symbol=code)
        if df is None or df.empty:
            return {"text": f"No stock info for {symbol}.", "data": {}}

        info_dict = {}
        for _, row in df.iterrows():
            key = str(row.iloc[0]) if len(row) > 0 else ""
            val = str(row.iloc[1]) if len(row) > 1 else ""
            if key:
                info_dict[key] = val

        lines = [f"# A 股基础信息 — {symbol}\n"]
        for k, v in info_dict.items():
            lines.append(f"- **{k}**: {v}")

        return {"text": "\n".join(lines), "data": info_dict}

    except Exception as e:
        return {"text": f"Error fetching stock info: {e}", "data": {}}
```

**Step 3: Smoke test both**

```bash
cd plugins/cn_mcp && uv run python -m python cn-stock-info 600519
```

Expected: JSON with stock info (总市值, 流通市值, 行业, etc.)

```bash
cd plugins/cn_mcp && uv run python -m python cn-shareholder 600519 --date 20250930
```

Expected: JSON with shareholder data or empty result if date not available.

**Step 4: Commit**

```bash
git add plugins/cn_mcp/python/shareholder.py plugins/cn_mcp/python/stock_info.py
git commit -m "feat(cn_mcp): implement shareholder changes and stock info tools"
```

---

## Task 5: Create TypeScript MCP wrapper for cn_mcp

**Files:**
- Create: `plugins/cn_mcp/package.json`
- Create: `plugins/cn_mcp/tsconfig.json`
- Create: `plugins/cn_mcp/src/index.ts`
- Create: `plugins/cn_mcp/src/tools/call-python.ts`
- Create: `plugins/cn_mcp/src/tools/news.ts`
- Create: `plugins/cn_mcp/src/tools/dragon-tiger.ts`
- Create: `plugins/cn_mcp/src/tools/shareholder.ts`
- Create: `plugins/cn_mcp/src/tools/stock-info.ts`

This follows the exact same pattern as `plugins/gv/` — a TypeScript MCP server that delegates each tool to a Python subprocess via `callPython`.

**Step 1: Create package.json**

```json
{
  "name": "cn_mcp",
  "version": "0.1.0",
  "description": "MCP server providing Chinese A-share data tools via AKShare",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "setup:python": "uv sync --project .",
    "setup": "npm install && npm run build && npm run setup:python"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.12.1",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "typescript": "^5.8.0"
  }
}
```

**Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true
  },
  "include": ["src/**/*"]
}
```

**Step 3: Create call-python.ts**

```typescript
// plugins/cn_mcp/src/tools/call-python.ts
import { execFile } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PLUGIN_DIR = path.resolve(__dirname, "../..");  // plugins/cn_mcp/

export function callPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      "uv",
      ["run", "--project", PLUGIN_DIR, "python", "-m", "python", ...args],
      {
        cwd: PLUGIN_DIR,
        timeout: 120_000,  // 2 min — AKShare network calls can be slow
        maxBuffer: 10 * 1024 * 1024,  // 10MB
        encoding: "utf-8",
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      },
      (err, stdout, stderr) => {
        if (err) {
          reject(new Error(`Python error: ${stderr || err.message}`));
        } else {
          resolve(stdout);
        }
      }
    );
  });
}
```

**Step 4: Create tool wrapper files**

```typescript
// plugins/cn_mcp/src/tools/news.ts
import { callPython } from "./call-python.js";

export interface CnNewsParams {
  symbol: string;
  limit?: number;
}

export interface CnGlobalNewsParams {
  limit?: number;
}

export async function getCnNews(params: CnNewsParams): Promise<string> {
  const { symbol, limit = 20 } = params;
  // Strip .SS/.SZ suffix for AKShare
  const code = symbol.split(".")[0];
  try {
    const raw = await callPython(["cn-news", code, "--limit", String(limit)]);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching A-share news for ${symbol}: ${error.message}`;
  }
}

export async function getCnGlobalNews(params: CnGlobalNewsParams): Promise<string> {
  const { limit = 20 } = params;
  try {
    const raw = await callPython(["cn-global-news", "--limit", String(limit)]);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching Chinese macro news: ${error.message}`;
  }
}
```

```typescript
// plugins/cn_mcp/src/tools/dragon-tiger.ts
import { callPython } from "./call-python.js";

export interface CnDragonTigerParams {
  symbol: string;
  start_date: string;
  end_date: string;
}

export interface CnDragonTigerStatsParams {
  period?: string;
}

export async function getCnDragonTiger(params: CnDragonTigerParams): Promise<string> {
  const { symbol, start_date, end_date } = params;
  const code = symbol.split(".")[0];
  try {
    const raw = await callPython([
      "cn-dragon-tiger", code,
      "--start-date", start_date,
      "--end-date", end_date,
    ]);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching dragon tiger data for ${symbol}: ${error.message}`;
  }
}

export async function getCnDragonTigerStats(params: CnDragonTigerStatsParams): Promise<string> {
  const { period = "近一月" } = params;
  try {
    const raw = await callPython(["cn-dragon-tiger-stats", "--period", period]);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching dragon tiger stats: ${error.message}`;
  }
}
```

```typescript
// plugins/cn_mcp/src/tools/shareholder.ts
import { callPython } from "./call-python.js";

export interface CnShareholderParams {
  symbol: string;
  date: string;
}

export async function getCnShareholderChanges(params: CnShareholderParams): Promise<string> {
  const { symbol, date } = params;
  const code = symbol.split(".")[0];
  try {
    const raw = await callPython(["cn-shareholder", code, "--date", date]);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching shareholder data for ${symbol}: ${error.message}`;
  }
}
```

```typescript
// plugins/cn_mcp/src/tools/stock-info.ts
import { callPython } from "./call-python.js";

export interface CnStockInfoParams {
  symbol: string;
}

export async function getCnStockInfo(params: CnStockInfoParams): Promise<string> {
  const { symbol } = params;
  const code = symbol.split(".")[0];
  try {
    const raw = await callPython(["cn-stock-info", code]);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching stock info for ${symbol}: ${error.message}`;
  }
}
```

**Step 5: Create index.ts — MCP server with all 6 tools registered**

```typescript
// plugins/cn_mcp/src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { getCnNews, getCnGlobalNews } from "./tools/news.js";
import { getCnDragonTiger, getCnDragonTigerStats } from "./tools/dragon-tiger.js";
import { getCnShareholderChanges } from "./tools/shareholder.js";
import { getCnStockInfo } from "./tools/stock-info.js";

const server = new McpServer({
  name: "cn",
  version: "0.1.0",
});

// --- A-Share News ---
server.registerTool(
  "get_cn_news",
  {
    description: "Get company-specific news for a Chinese A-share stock (东方财富 source)",
    inputSchema: {
      symbol: z.string().describe("A-share ticker (e.g. 600519.SS, 000001.SZ, or raw 600519)"),
      limit: z.number().optional().default(20).describe("Max articles to return"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnNews(params) }],
  })
);

server.registerTool(
  "get_cn_global_news",
  {
    description: "Get Chinese macroeconomic and market news (央行, 证监会, GDP, A股 from 东方财富)",
    inputSchema: {
      limit: z.number().optional().default(20).describe("Max articles to return"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnGlobalNews(params) }],
  })
);

// --- Dragon Tiger List (龙虎榜) ---
server.registerTool(
  "get_cn_dragon_tiger",
  {
    description: "Get dragon tiger list (龙虎榜) detail for an A-share stock — shows institutional/large trader activity on unusual price movements",
    inputSchema: {
      symbol: z.string().describe("A-share ticker (e.g. 600519.SS or 600519)"),
      start_date: z.string().describe("Start date in YYYYMMDD format"),
      end_date: z.string().describe("End date in YYYYMMDD format"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnDragonTiger(params) }],
  })
);

server.registerTool(
  "get_cn_dragon_tiger_stats",
  {
    description: "Get dragon tiger list (龙虎榜) statistics — top stocks by institutional trading activity over a period",
    inputSchema: {
      period: z.string().optional().default("近一月").describe("Period: 近一月/近三月/近六月/近一年"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnDragonTigerStats(params) }],
  })
);

// --- Shareholder Changes ---
server.registerTool(
  "get_cn_shareholder_changes",
  {
    description: "Get top-10 tradable shareholder changes for an A-share stock (十大流通股东变动)",
    inputSchema: {
      symbol: z.string().describe("A-share ticker (e.g. 600519.SS or 600519)"),
      date: z.string().describe("Reporting period date in YYYYMMDD format (e.g. 20250930)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnShareholderChanges(params) }],
  })
);

// --- Stock Info ---
server.registerTool(
  "get_cn_stock_info",
  {
    description: "Get basic info for a Chinese A-share stock — sector, market cap, shares outstanding, listing date",
    inputSchema: {
      symbol: z.string().describe("A-share ticker (e.g. 600519.SS or 600519)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnStockInfo(params) }],
  })
);

// --- Start server ---
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
```

**Step 6: Install npm deps and build**

```bash
cd plugins/cn_mcp && npm install && npm run build
```

Expected: `dist/` directory created with compiled JS.

**Step 7: Commit**

```bash
git add plugins/cn_mcp/package.json plugins/cn_mcp/tsconfig.json plugins/cn_mcp/src/
git commit -m "feat(cn_mcp): add TypeScript MCP server wrapper with 6 registered tools"
```

---

## Task 6: Register cn_mcp plugin in project configuration

**Files:**
- Modify: `plugins/cn_mcp/.mcp.json` (already created in Task 1)
- Modify: `.claude/settings.local.json`

**Step 1: Verify .mcp.json is correct**

The file created in Task 1 should already be:
```json
{
  "mcpServers": {
    "cn": {
      "type": "stdio",
      "command": "node",
      "args": ["./plugins/cn_mcp/dist/index.js"],
      "env": {}
    }
  }
}
```

**Step 2: Add cn_mcp to settings.local.json enabled plugins**

In `.claude/settings.local.json`, add `"cn_mcp@ta": true` to `enabledPlugins`:

```json
"enabledPlugins": {
    "ta@ta": true,
    "t_mcp@ta": true,
    "gv@ta": true,
    "cn_mcp@ta": true
}
```

Also add MCP tool permissions to the `allow` list:

```json
"permissions": {
    "allow": [
      ...existing entries...,
      "mcp__plugin_cn_mcp_cn__get_cn_news",
      "mcp__plugin_cn_mcp_cn__get_cn_global_news",
      "mcp__plugin_cn_mcp_cn__get_cn_dragon_tiger",
      "mcp__plugin_cn_mcp_cn__get_cn_dragon_tiger_stats",
      "mcp__plugin_cn_mcp_cn__get_cn_shareholder_changes",
      "mcp__plugin_cn_mcp_cn__get_cn_stock_info"
    ]
}
```

> **Note:** The tool permission names follow the pattern `mcp__plugin_{plugin_dir}_{server_name}__{tool_name}`. The plugin directory name is `cn_mcp` and the MCP server name is `cn` (from `.mcp.json`), so the prefix is `mcp__plugin_cn_mcp_cn__`. If this naming convention doesn't match at runtime, check what names appear in the permission prompt and adjust accordingly.

**Step 3: Commit**

```bash
git add .claude/settings.local.json plugins/cn_mcp/.mcp.json
git commit -m "feat(cn_mcp): register cn_mcp plugin in settings and enable MCP tool permissions"
```

**Step 4: Reload plugins to verify**

Restart Claude Code or run `/reload-plugins` to verify the cn_mcp server starts and all 6 tools are available.

---

## Task 7: Update trading-analysis orchestration skill for A-share routing

**Files:**
- Modify: `skills/trading-analysis/SKILL.md`

**Step 1: Add A-share market detection and routing to the SKILL.md**

At the top of the `## Execution Steps` section (after line 81), insert a new section:

```markdown
### A-Share Market Detection

Before starting Phase 1, detect whether the ticker is a Chinese A-share:

**A-share indicators:**
- Ticker ends with `.SS` (Shanghai) or `.SZ` (Shenzhen)
- Ticker is a 6-digit number (600xxx = Shanghai, 000xxx/002xxx/300xxx/688xxx = Shenzhen)

**If A-share detected, apply these modifications to ALL phases:**

1. **Market context injection:** Add this context block to every sub-agent prompt:

> **A-Share Market Rules:**
> - Price limit: Main board ±10%, STAR/ChiNext ±20%, ST ±5%
> - T+1 trading (cannot sell shares bought on the same day)
> - Trading hours: 9:15-9:25 call auction, 9:30-11:30 / 13:00-15:00 continuous
> - Currency: CNY (Chinese Yuan)
> - Dragon tiger list (龙虎榜) replaces insider transactions as a fund flow indicator
> - Policy-driven: CSRC, PBOC, and State Council policies heavily impact A-shares
> - Northbound capital (北向资金 via Stock Connect) is a key sentiment indicator
> - This is a China A-share stock. Analyze it with China-specific market context.

2. **Data source routing for analyst sub-agents:**

| Sub-agent | US stocks (default) | A-shares (modified) |
|-----------|-------------------|-------------------|
| Market Analyst | `get_stock_data` + `get_indicators` from ta | Same — no change |
| Sentiment Analyst | `get_news` from ta | `get_cn_news` from cn + `get_cn_stock_info` from cn |
| News Analyst | `get_news` + `get_global_news` + `get_insider_transactions` from ta | `get_cn_news` + `get_cn_global_news` + `get_cn_dragon_tiger` + `get_cn_shareholder_changes` from cn |
| Fundamentals Analyst | `get_fundamentals` + financials from ta | Same — no change (Yahoo works for A-shares) |
```

**Step 2: Update the Sub-agent 2 (Sentiment) prompt in Phase 1**

Replace the existing Sentiment Analyst prompt (around lines 99-108) with a version that branches on market type:

```markdown
**Sub-agent 2 — Sentiment Analyst:**

*If A-share:*
> You are a Social Media & Sentiment Analyst. Analyze sentiment for {TICKER} as of {DATE}.
>
> {A-Share Market Rules block from above}
>
> Use MCP tools from cn:
> 1. Call `get_cn_news(symbol="{TICKER}", limit=20)` for Chinese-language company news
> 2. Call `get_cn_stock_info(symbol="{TICKER}")` for stock metadata and sector context
> 3. Analyze sentiment from the articles — identify positive/negative/neutral signals
> 4. Consider Chinese social media platforms (东方财富股吧, 雪球) sentiment characteristics
> 5. Write a comprehensive sentiment report with overall assessment and a Markdown summary table
>
> Use the exact ticker "{TICKER}" in every tool call.

*If NOT A-share (default):*
> (existing prompt unchanged)
```

**Step 3: Update the Sub-agent 3 (News) prompt in Phase 1**

Replace the existing News Analyst prompt (around lines 110-120) with:

```markdown
**Sub-agent 3 — News Analyst:**

*If A-share:*
> You are a News Analyst. Analyze news for {TICKER} as of {DATE}.
>
> {A-Share Market Rules block from above}
>
> Use MCP tools from cn:
> 1. Call `get_cn_news(symbol="{TICKER}", limit=20)` for Chinese-language company news
> 2. Call `get_cn_global_news(limit=15)` for Chinese macroeconomic/policy news
> 3. Call `get_cn_dragon_tiger(symbol="{TICKER}", start_date="{30_DAYS_BEFORE_YYYYMMDD}", end_date="{DATE_YYYYMMDD}")` for institutional activity (replaces insider transactions)
> 4. Call `get_cn_shareholder_changes(symbol="{TICKER}", date="{LATEST_QUARTER_YYYYMMDD}")` for shareholder changes
> 5. Write a comprehensive news analysis report with a Markdown summary table
>
> Note: For A-shares, dragon tiger list (龙虎榜) data replaces US-style insider transactions. The latest quarter date for shareholder data should be the most recent quarter-end (e.g. 20250930, 20251231, 20260331).
>
> Use the exact ticker "{TICKER}" in every tool call.

*If NOT A-share (default):*
> (existing prompt unchanged)
```

**Step 4: Verify the skill reads correctly**

Read through the full updated skill to verify it's coherent and no syntax errors.

**Step 5: Commit**

```bash
git add skills/trading-analysis/SKILL.md
git commit -m "feat: add A-share market detection and data routing to trading-analysis skill"
```

---

## Task 8: Update individual analyst skills for A-share support

**Files:**
- Modify: `skills/news-analysis/SKILL.md`
- Modify: `skills/sentiment-analysis/SKILL.md`

These standalone skills (used when invoking `ta:news-analysis` or `ta:sentiment-analysis` individually outside the full pipeline) also need A-share awareness.

**Step 1: Update news-analysis SKILL.md**

After the existing `## Execution` section, add:

```markdown
## A-Share Mode

If the ticker ends with `.SS` or `.SZ` (or is a 6-digit number), this is a Chinese A-share stock. Modify the execution:

1. Call `get_cn_news(symbol=TICKER, limit=20)` from cn instead of `get_news` from ta
2. Call `get_cn_global_news(limit=15)` from cn instead of `get_global_news` from ta
3. Call `get_cn_dragon_tiger(symbol=TICKER, start_date=30_DAYS_BEFORE_YYYYMMDD, end_date=DATE_YYYYMMDD)` from cn instead of `get_insider_transactions` from ta
4. Optionally call `get_cn_shareholder_changes(symbol=TICKER, date=LATEST_QUARTER_YYYYMMDD)` from cn
5. Apply A-share market rules (±10% price limits, T+1 trading, policy-driven market)

The report should be written with Chinese market context in mind.
```

**Step 2: Update sentiment-analysis SKILL.md**

After the existing `## Execution` section, add:

```markdown
## A-Share Mode

If the ticker ends with `.SS` or `.SZ` (or is a 6-digit number), this is a Chinese A-share stock. Modify the execution:

1. Call `get_cn_news(symbol=TICKER, limit=20)` from cn instead of `get_news` from ta
2. Call `get_cn_stock_info(symbol=TICKER)` from cn for additional context
3. Analyze sentiment considering Chinese social media characteristics (东方财富股吧, 雪球)
4. Apply A-share market rules (±10% price limits, T+1 trading, policy-driven market)

The report should consider China-specific sentiment drivers (policy announcements, northbound capital flows, sector rotation).
```

**Step 3: Commit**

```bash
git add skills/news-analysis/SKILL.md skills/sentiment-analysis/SKILL.md
git commit -m "feat: add A-share mode to news-analysis and sentiment-analysis skills"
```

---

## Task 9: Update agent prompts with A-share awareness

**Files:**
- Modify: `agents/news-analyst.md`
- Modify: `agents/sentiment-analyst.md`
- Modify: `agents/market-analyst.md`
- Modify: `agents/fundamentals-analyst.md`

The agent prompts need a note about A-share ticker handling. The orchestrator injects the full market context, but the agents should know to adapt their language when they see A-share tickers.

**Step 1: Add A-share note to news-analyst.md**

After the `## Output Format` section, add:

```markdown
## A-Share Stocks

If the ticker ends with `.SS` (Shanghai) or `.SZ` (Shenzhen), this is a Chinese A-share stock. When analyzing A-shares:
- Use `get_cn_news` and `get_cn_global_news` from the **cn** MCP server instead of `get_news` and `get_global_news`
- Use `get_cn_dragon_tiger` instead of `get_insider_transactions` (龙虎榜 replaces US insider data)
- Optionally use `get_cn_shareholder_changes` for top-10 shareholder movement
- Focus on policy impact (CSRC, PBOC, State Council), sector rotation, and northbound capital flows
- Apply A-share rules: ±10% price limits (±20% for STAR/ChiNext), T+1 trading, CNY currency
```

**Step 2: Add A-share note to sentiment-analyst.md**

After the `## Output Format` section, add:

```markdown
## A-Share Stocks

If the ticker ends with `.SS` or `.SZ`, this is a Chinese A-share stock. When analyzing A-shares:
- Use `get_cn_news` from the **cn** MCP server instead of `get_news`
- Consider Chinese social media characteristics: 东方财富股吧 (retail investor forum), 雪球 (Snowball)
- Northbound capital (北向资金) flow is a key institutional sentiment indicator
- Policy announcements from CSRC/PBOC often cause sharp sentiment shifts
- A-share retail investor dominance means sentiment can be more volatile than US markets
```

**Step 3: Add A-share note to market-analyst.md**

After the last line ("Use the exact ticker..."), add:

```markdown
## A-Share Stocks

If the ticker ends with `.SS` or `.SZ`, this is a Chinese A-share stock. Keep in mind:
- Price limit bands: Main board ±10%, STAR Market (688xxx) / ChiNext (300xxx) ±20%, ST stocks ±5%
- T+1 rule: shares bought today cannot be sold until tomorrow
- Trading sessions: 9:15-9:25 call auction, 9:30-11:30 morning, 13:00-15:00 afternoon (no after-hours)
- Volume patterns differ from US markets — A-share volume concentrates in morning session
- The same `get_stock_data` and `get_indicators` tools work for A-shares (use the full ticker with .SS/.SZ suffix)
```

**Step 4: Add A-share note to fundamentals-analyst.md**

After the last line, add:

```markdown
## A-Share Stocks

If the ticker ends with `.SS` or `.SZ`, this is a Chinese A-share stock. Keep in mind:
- Financial data is in **CNY** (Chinese Yuan), not USD
- Accounting standards follow Chinese GAAP (CAS), which differs from US GAAP/IFRS in some areas
- State ownership is common — check for government/SOE shareholders
- The same `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement` tools work for A-shares
- Optionally use `get_cn_stock_info` from the **cn** MCP server for additional A-share-specific metadata
```

**Step 5: Commit**

```bash
git add agents/news-analyst.md agents/sentiment-analyst.md agents/market-analyst.md agents/fundamentals-analyst.md
git commit -m "feat: add A-share awareness notes to analyst agent prompts"
```

---

## Task 10: Integration test — run full pipeline on Moutai (600519.SS)

**Files:** None (testing only)

**Step 1: Reload plugins**

Run `/reload-plugins` in Claude Code to pick up the new cn_mcp server.

**Step 2: Verify cn_mcp tools are available**

Try calling each cn_mcp tool manually to verify they work:

```
get_cn_news(symbol="600519.SS", limit=5)
get_cn_global_news(limit=5)
get_cn_stock_info(symbol="600519.SS")
get_cn_dragon_tiger(symbol="600519", start_date="20260301", end_date="20260406")
get_cn_dragon_tiger_stats(period="近一月")
```

Expected: Each tool returns Chinese-language data. If any fail, debug the Python layer (AKShare API changes are common — check function signatures against latest AKShare docs).

**Step 3: Run individual analyst skills on A-share**

Test each standalone skill:
```
/ta:market-analysis 600519.SS
/ta:news-analysis 600519.SS
/ta:sentiment-analysis 600519.SS
/ta:fundamentals-analysis 600519.SS
```

Expected: Each should produce a report. News and sentiment should use cn_mcp tools (Chinese news). Market and fundamentals should use t_mcp tools (Yahoo Finance).

**Step 4: Run full trading-analysis pipeline**

```
/ta:trading-analysis 600519.SS
```

Expected: Full 6-phase pipeline runs, producing:
- 4 analyst reports (with Chinese news/sentiment data)
- Bull/bear debate with A-share context
- Trader decision
- Risk debate
- Portfolio manager final rating
- Reports saved to `analysis/600519.SS_2026-04-06_en.md` and `analysis/600519.SS_2026-04-06_zh.md`

**Step 5: Verify report quality**

Check the generated reports for:
- Chinese news coverage (not random English news)
- Dragon tiger data (if 600519 was on the list)
- A-share market rule awareness in analysis
- Correct currency (CNY, not USD)

**Step 6: Test with a Shenzhen stock**

Run a second test with a Shenzhen ticker:
```
/ta:trading-analysis 000001.SZ
```

Expected: Same quality analysis for Ping An Bank.

**Step 7: Regression test with a US stock**

Verify US stocks still work:
```
/ta:trading-analysis AAPL
```

Expected: Identical behavior to before — uses t_mcp tools only, no A-share rules injected.

---

## Task 11: Final cleanup and commit

**Files:**
- Verify all files committed
- Update: `plugins/cn_mcp/.gitignore` (ensure node_modules, dist, .venv excluded)

**Step 1: Add lock files to gitignore if needed**

Verify `plugins/cn_mcp/.gitignore` includes:
```
.venv/
__pycache__/
*.pyc
node_modules/
dist/
package-lock.json
uv.lock
```

**Step 2: Run git status**

```bash
git status
```

Expected: Clean working tree, or only generated analysis reports.

**Step 3: Final commit if needed**

```bash
git add -A && git commit -m "feat(cn_mcp): complete A-share trading analysis support"
```
