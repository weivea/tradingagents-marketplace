# HK Stock Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add basic Hong Kong stock (HKEX) support so the multi-agent trading analysis pipeline correctly detects, routes, and analyzes HK stocks.

**Architecture:** Extend the existing `cn` MCP server with 3 new HK-specific Python modules + TypeScript tool wrappers (following the A-share pattern exactly). Update the SKILL.md orchestrator with HK market detection, tool routing, and agent rules. Update each analyst agent definition with HK-specific sections.

**Tech Stack:** Python (AKShare), TypeScript (MCP SDK + Zod), Markdown (agent definitions)

---

## File Structure

### New Files (6)
| File | Responsibility |
|------|---------------|
| `plugins/cn_mcp/python/hk_stock_info.py` | Fetch HK company profile + security info + financial indicators from AKShare |
| `plugins/cn_mcp/python/hk_stock_connect.py` | Fetch Stock Connect (港股通) holding data for a specific HK stock from AKShare |
| `plugins/cn_mcp/python/hk_hot_rank.py` | Fetch HK stock popularity/hot rank data from AKShare |
| `plugins/cn_mcp/src/tools/hk-stock-info.ts` | TypeScript MCP tool wrapper for `get_hk_stock_info` |
| `plugins/cn_mcp/src/tools/hk-stock-connect.ts` | TypeScript MCP tool wrapper for `get_hk_stock_connect` |
| `plugins/cn_mcp/src/tools/hk-hot-rank.ts` | TypeScript MCP tool wrapper for `get_hk_hot_rank` |

### Modified Files (5)
| File | Change |
|------|--------|
| `plugins/cn_mcp/python/__main__.py` | Add 3 CLI subcommands for HK tools |
| `plugins/cn_mcp/src/index.ts` | Register 3 new HK MCP tools |
| `skills/trading-analysis/SKILL.md` | Add HK market detection + tool routing + agent prompt rules |
| `agents/market-analyst.md` | Add HK stock section (following A-share pattern) |
| `agents/fundamentals-analyst.md` | Add HK stock section (following A-share pattern) |
| `agents/sentiment-analyst.md` | Add HK stock section (following A-share pattern) |
| `agents/news-analyst.md` | Add HK stock section (following A-share pattern) |

---

### Task 1: Python module — `hk_stock_info.py`

**Files:**
- Create: `plugins/cn_mcp/python/hk_stock_info.py`

- [ ] **Step 1: Create the Python module**

Create `plugins/cn_mcp/python/hk_stock_info.py` with this content:

```python
"""HK stock info (港股信息) via AKShare."""

from __future__ import annotations

import traceback
from typing import Any

import akshare as ak
import pandas as pd


def _normalize_hk_code(symbol: str) -> str:
    """Normalize HK stock code to 5-digit format (e.g. '700' -> '00700')."""
    code = symbol.split(".")[0].lstrip("0") or "0"
    return code.zfill(5)


def get_hk_stock_info(symbol: str) -> dict[str, Any]:
    """Get basic information for a Hong Kong stock.

    Combines three AKShare endpoints:
      - stock_hk_company_profile_em: company profile
      - stock_hk_security_profile_em: security/listing info
      - stock_hk_financial_indicator_em: key financial metrics

    Args:
        symbol: HK stock code (e.g. '00700', '0700.HK', '700').

    Returns:
        Dict with "text" (Markdown) and "data".
    """
    code = _normalize_hk_code(symbol)
    data: dict[str, Any] = {}
    lines: list[str] = [f"## 港股信息 — {code}\n"]

    # --- Company profile ---
    try:
        df_profile: pd.DataFrame = ak.stock_hk_company_profile_em(symbol=code)
        if df_profile is not None and not df_profile.empty:
            row = df_profile.iloc[0]
            profile: dict[str, str] = {}
            for col in df_profile.columns:
                val = str(row[col]) if pd.notna(row[col]) else ""
                if val and val != "nan":
                    profile[col] = val
            data["profile"] = profile

            lines.append("### 公司概况\n")
            for k, v in profile.items():
                if k == "公司介绍":
                    lines.append(f"- **{k}**: {v[:300]}{'...' if len(v) > 300 else ''}")
                else:
                    lines.append(f"- **{k}**: {v}")
            lines.append("")
    except Exception as exc:
        lines.append(f"*获取公司概况失败: {exc}*\n")

    # --- Security profile ---
    try:
        df_sec: pd.DataFrame = ak.stock_hk_security_profile_em(symbol=code)
        if df_sec is not None and not df_sec.empty:
            row = df_sec.iloc[0]
            sec_info: dict[str, str] = {}
            for col in df_sec.columns:
                val = str(row[col]) if pd.notna(row[col]) else ""
                if val and val != "nan":
                    sec_info[col] = val
            data["security"] = sec_info

            lines.append("### 证券资料\n")
            for k, v in sec_info.items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")
    except Exception as exc:
        lines.append(f"*获取证券资料失败: {exc}*\n")

    # --- Financial indicators ---
    try:
        df_fin: pd.DataFrame = ak.stock_hk_financial_indicator_em(symbol=code)
        if df_fin is not None and not df_fin.empty:
            row = df_fin.iloc[0]
            fin_data: dict[str, str] = {}
            for col in df_fin.columns:
                val = str(row[col]) if pd.notna(row[col]) else ""
                if val and val != "nan":
                    fin_data[col] = val
            data["financial"] = fin_data

            lines.append("### 关键财务指标\n")
            for k, v in fin_data.items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")
    except Exception as exc:
        lines.append(f"*获取财务指标失败: {exc}*\n")

    if not data:
        return {
            "text": f"No info found for HK stock {code}.",
            "data": {},
        }

    return {"text": "\n".join(lines), "data": data}
```

- [ ] **Step 2: Test the module manually**

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -c "from python.hk_stock_info import get_hk_stock_info; import json; r = get_hk_stock_info('00700'); print(r['text'][:500])"
```
Expected: Markdown output starting with `## 港股信息 — 00700` with company profile data for Tencent.

- [ ] **Step 3: Commit**

```bash
git add plugins/cn_mcp/python/hk_stock_info.py
git commit -m "feat(cn_mcp): add HK stock info Python module

Fetches company profile, security info, and financial indicators
for Hong Kong stocks via AKShare."
```

---

### Task 2: Python module — `hk_stock_connect.py`

**Files:**
- Create: `plugins/cn_mcp/python/hk_stock_connect.py`

- [ ] **Step 1: Create the Python module**

Create `plugins/cn_mcp/python/hk_stock_connect.py` with this content:

```python
"""HK Stock Connect (港股通) holding data via AKShare."""

from __future__ import annotations

import traceback
from typing import Any

import akshare as ak
import pandas as pd


def _normalize_hk_code(symbol: str) -> str:
    """Normalize HK stock code to 5-digit format (e.g. '700' -> '00700')."""
    code = symbol.split(".")[0].lstrip("0") or "0"
    return code.zfill(5)


def get_hk_stock_connect(symbol: str) -> dict[str, Any]:
    """Get Stock Connect (港股通) southbound holding data for an HK stock.

    Uses stock_hsgt_individual_em to get the holding history for a specific
    HK stock, then summarises the last 30 trading days.

    Args:
        symbol: HK stock code (e.g. '00700', '0700.HK', '700').

    Returns:
        Dict with "text" (Markdown) and "data".
    """
    code = _normalize_hk_code(symbol)
    try:
        df: pd.DataFrame = ak.stock_hsgt_individual_em(symbol=code)
        if df is None or df.empty:
            return {
                "text": f"No Stock Connect data found for {code}.",
                "data": {},
            }

        # Sort by date descending, take last 30 rows
        date_col = None
        for col_name in ["持股日期", "日期", "date"]:
            if col_name in df.columns:
                date_col = col_name
                break

        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.sort_values(date_col, ascending=False)

        recent = df.head(30).copy()

        # Build summary
        lines: list[str] = [f"## 港股通持仓 — {code}\n"]
        lines.append(f"最近 {len(recent)} 个交易日数据\n")

        # Key columns we care about
        pct_col = None
        for col_name in ["持股占比", "持股占已发行股份百分比"]:
            if col_name in recent.columns:
                pct_col = col_name
                break

        qty_col = None
        for col_name in ["持股数量", "持股股数"]:
            if col_name in recent.columns:
                qty_col = col_name
                break

        val_col = None
        for col_name in ["持股市值", "持股市值(元)"]:
            if col_name in recent.columns:
                val_col = col_name
                break

        close_col = None
        for col_name in ["收盘价", "当日收盘价"]:
            if col_name in recent.columns:
                close_col = col_name
                break

        # Trend analysis
        if pct_col and len(recent) >= 2:
            try:
                latest_pct = float(recent.iloc[0][pct_col])
                oldest_pct = float(recent.iloc[-1][pct_col])
                pct_change = latest_pct - oldest_pct
                if pct_change > 0.05:
                    trend = "增持"
                    trend_desc = f"南向资金持续增持，持股占比从 {oldest_pct:.2f}% 升至 {latest_pct:.2f}%（+{pct_change:.2f}%）"
                elif pct_change < -0.05:
                    trend = "减持"
                    trend_desc = f"南向资金持续减持，持股占比从 {oldest_pct:.2f}% 降至 {latest_pct:.2f}%（{pct_change:.2f}%）"
                else:
                    trend = "持平"
                    trend_desc = f"南向资金持仓基本持平，持股占比约 {latest_pct:.2f}%"
                lines.append(f"### 趋势: {trend}\n")
                lines.append(f"{trend_desc}\n")
            except (ValueError, TypeError):
                pass

        # Recent data table
        lines.append("### 近期持仓明细\n")
        lines.append("| 日期 | 收盘价 | 持股数量 | 持股市值 | 持股占比 |")
        lines.append("|------|--------|----------|----------|----------|")
        for _, row in recent.head(10).iterrows():
            d = str(row[date_col])[:10] if date_col else ""
            c = str(row[close_col]) if close_col and pd.notna(row[close_col]) else ""
            q = str(row[qty_col]) if qty_col and pd.notna(row[qty_col]) else ""
            v = str(row[val_col]) if val_col and pd.notna(row[val_col]) else ""
            p = str(row[pct_col]) if pct_col and pd.notna(row[pct_col]) else ""
            lines.append(f"| {d} | {c} | {q} | {v} | {p} |")

        # Serialise data
        for col in recent.select_dtypes(include=["datetime64", "datetimetz"]).columns:
            recent[col] = recent[col].astype(str)
        records = recent.head(30).to_dict(orient="records")

        return {"text": "\n".join(lines), "data": records}

    except Exception as exc:
        return {
            "text": f"Error fetching Stock Connect data for {code}: {exc}",
            "data": {},
            "error": traceback.format_exc(),
        }
```

- [ ] **Step 2: Test the module manually**

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -c "from python.hk_stock_connect import get_hk_stock_connect; r = get_hk_stock_connect('00700'); print(r['text'][:500])"
```
Expected: Markdown output with `## 港股通持仓 — 00700`, trend summary, and recent holding data table.

- [ ] **Step 3: Commit**

```bash
git add plugins/cn_mcp/python/hk_stock_connect.py
git commit -m "feat(cn_mcp): add HK Stock Connect holding Python module

Fetches southbound (港股通) holding data for HK stocks via AKShare,
with 30-day trend analysis."
```

---

### Task 3: Python module — `hk_hot_rank.py`

**Files:**
- Create: `plugins/cn_mcp/python/hk_hot_rank.py`

- [ ] **Step 1: Create the Python module**

Create `plugins/cn_mcp/python/hk_hot_rank.py` with this content:

```python
"""HK stock hot rank (港股人气排名) via AKShare."""

from __future__ import annotations

import traceback
from typing import Any

import akshare as ak
import pandas as pd


def _normalize_hk_code(symbol: str) -> str:
    """Normalize HK stock code to 5-digit format (e.g. '700' -> '00700')."""
    code = symbol.split(".")[0].lstrip("0") or "0"
    return code.zfill(5)


def get_hk_hot_rank(symbol: str | None = None) -> dict[str, Any]:
    """Get HK stock popularity / hot rank data.

    Without symbol: returns top-20 hottest HK stocks from stock_hk_hot_rank_em.
    With symbol: returns historical rank trend from stock_hk_hot_rank_detail_em.

    Args:
        symbol: Optional HK stock code. If omitted, returns the overall ranking.

    Returns:
        Dict with "text" (Markdown) and "data".
    """
    if symbol:
        return _get_individual_rank(symbol)
    return _get_overall_rank()


def _get_overall_rank() -> dict[str, Any]:
    """Get top-20 hottest HK stocks."""
    try:
        df: pd.DataFrame = ak.stock_hk_hot_rank_em()
        if df is None or df.empty:
            return {"text": "No HK hot rank data available.", "data": []}

        df = df.head(20)

        lines: list[str] = ["## 港股人气排名 Top 20\n"]
        lines.append("| 排名 | 代码 | 名称 | 最新价 | 涨跌幅 |")
        lines.append("|------|------|------|--------|--------|")

        for _, row in df.iterrows():
            rank = str(row.get("当前排名", row.get("排名", "")))
            code = str(row.get("代码", row.get("证券代码", "")))
            name = str(row.get("股票名称", row.get("名称", "")))
            price = str(row.get("最新价", ""))
            change = str(row.get("涨跌幅", ""))
            lines.append(f"| {rank} | {code} | {name} | {price} | {change} |")

        for col in df.select_dtypes(include=["datetime64", "datetimetz"]).columns:
            df[col] = df[col].astype(str)
        records = df.to_dict(orient="records")

        return {"text": "\n".join(lines), "data": records}

    except Exception as exc:
        return {
            "text": f"Error fetching HK hot rank: {exc}",
            "data": [],
            "error": traceback.format_exc(),
        }


def _get_individual_rank(symbol: str) -> dict[str, Any]:
    """Get historical rank trend for a specific HK stock."""
    code = _normalize_hk_code(symbol)
    try:
        df: pd.DataFrame = ak.stock_hk_hot_rank_detail_em(symbol=code)
        if df is None or df.empty:
            return {
                "text": f"No hot rank history found for {code}.",
                "data": [],
            }

        # Sort by time descending
        time_col = None
        for col_name in ["时间", "日期", "date"]:
            if col_name in df.columns:
                time_col = col_name
                break

        if time_col:
            df = df.sort_values(time_col, ascending=False)

        recent = df.head(30)

        rank_col = None
        for col_name in ["排名", "当前排名"]:
            if col_name in df.columns:
                rank_col = col_name
                break

        lines: list[str] = [f"## 港股人气排名趋势 — {code}\n"]

        if rank_col and time_col and len(recent) >= 2:
            try:
                latest_rank = int(recent.iloc[0][rank_col])
                oldest_rank = int(recent.iloc[-1][rank_col])
                rank_change = oldest_rank - latest_rank  # positive = improving
                if rank_change > 5:
                    lines.append(f"排名上升趋势: 从第 {oldest_rank} 名升至第 {latest_rank} 名（上升 {rank_change} 位）\n")
                elif rank_change < -5:
                    lines.append(f"排名下降趋势: 从第 {oldest_rank} 名降至第 {latest_rank} 名（下降 {abs(rank_change)} 位）\n")
                else:
                    lines.append(f"排名基本稳定: 当前第 {latest_rank} 名\n")
            except (ValueError, TypeError):
                pass

        lines.append("| 日期 | 排名 |")
        lines.append("|------|------|")
        for _, row in recent.head(15).iterrows():
            t = str(row[time_col])[:10] if time_col else ""
            r = str(row[rank_col]) if rank_col else ""
            lines.append(f"| {t} | {r} |")

        for col in df.select_dtypes(include=["datetime64", "datetimetz"]).columns:
            df[col] = df[col].astype(str)
        records = recent.head(30).astype(str).to_dict(orient="records")

        return {"text": "\n".join(lines), "data": records}

    except Exception as exc:
        return {
            "text": f"Error fetching hot rank for {code}: {exc}",
            "data": [],
            "error": traceback.format_exc(),
        }
```

- [ ] **Step 2: Test the module manually — overall ranking**

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -c "from python.hk_hot_rank import get_hk_hot_rank; r = get_hk_hot_rank(); print(r['text'][:500])"
```
Expected: Markdown table with `## 港股人气排名 Top 20` and 20 rows of HK stocks.

- [ ] **Step 3: Test the module manually — individual stock**

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -c "from python.hk_hot_rank import get_hk_hot_rank; r = get_hk_hot_rank('00700'); print(r['text'][:500])"
```
Expected: Markdown with `## 港股人气排名趋势 — 00700` and rank history table.

- [ ] **Step 4: Commit**

```bash
git add plugins/cn_mcp/python/hk_hot_rank.py
git commit -m "feat(cn_mcp): add HK hot rank Python module

Fetches HK stock popularity rankings (overall top-20 or individual
stock trend) via AKShare."
```

---

### Task 4: Register HK commands in Python CLI (`__main__.py`)

**Files:**
- Modify: `plugins/cn_mcp/python/__main__.py`

- [ ] **Step 1: Add 3 command handler functions**

Add these functions after the existing `cmd_cn_stock_info` function (after line 90):

```python
def cmd_hk_stock_info(args: argparse.Namespace) -> None:
    from .hk_stock_info import get_hk_stock_info

    result = get_hk_stock_info(args.symbol)
    _dump(result)


def cmd_hk_stock_connect(args: argparse.Namespace) -> None:
    from .hk_stock_connect import get_hk_stock_connect

    result = get_hk_stock_connect(args.symbol)
    _dump(result)


def cmd_hk_hot_rank(args: argparse.Namespace) -> None:
    from .hk_hot_rank import get_hk_hot_rank

    symbol = getattr(args, "symbol", None)
    result = get_hk_hot_rank(symbol=symbol)
    _dump(result)
```

- [ ] **Step 2: Add 3 subparser registrations**

Add these after the existing `p_info` subparser (after line 129), before `args = parser.parse_args()`:

```python
    # hk-stock-info
    p_hk_info = sub.add_parser("hk-stock-info", help="HK stock basic information")
    p_hk_info.add_argument("symbol", help="HK stock code (e.g. 00700)")
    p_hk_info.set_defaults(func=cmd_hk_stock_info)

    # hk-stock-connect
    p_hk_connect = sub.add_parser("hk-stock-connect", help="HK Stock Connect holding data")
    p_hk_connect.add_argument("symbol", help="HK stock code (e.g. 00700)")
    p_hk_connect.set_defaults(func=cmd_hk_stock_connect)

    # hk-hot-rank
    p_hk_rank = sub.add_parser("hk-hot-rank", help="HK stock hot rank")
    p_hk_rank.add_argument("symbol", nargs="?", default=None, help="HK stock code (optional)")
    p_hk_rank.set_defaults(func=cmd_hk_hot_rank)
```

- [ ] **Step 3: Test CLI integration**

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -m python hk-stock-info 00700 | head -20
```
Expected: JSON output with `"text"` key containing markdown about Tencent.

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -m python hk-stock-connect 00700 | head -20
```
Expected: JSON output with Stock Connect holding data.

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -m python hk-hot-rank | head -20
```
Expected: JSON output with top-20 HK hot rank.

- [ ] **Step 4: Commit**

```bash
git add plugins/cn_mcp/python/__main__.py
git commit -m "feat(cn_mcp): register HK stock CLI subcommands

Add hk-stock-info, hk-stock-connect, hk-hot-rank subcommands
to the Python CLI entry point."
```

---

### Task 5: TypeScript MCP tool — `hk-stock-info.ts`

**Files:**
- Create: `plugins/cn_mcp/src/tools/hk-stock-info.ts`

- [ ] **Step 1: Create the TypeScript tool wrapper**

Create `plugins/cn_mcp/src/tools/hk-stock-info.ts` with this content:

```typescript
import { callPython } from "./call-python.js";

export interface GetHkStockInfoParams {
  symbol: string;
}

export async function getHkStockInfo(params: GetHkStockInfoParams): Promise<string> {
  const { symbol } = params;
  const args = ["hk-stock-info", symbol];
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching HK stock info: ${error.message}`;
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/cn_mcp/src/tools/hk-stock-info.ts
git commit -m "feat(cn_mcp): add HK stock info TypeScript MCP tool wrapper"
```

---

### Task 6: TypeScript MCP tool — `hk-stock-connect.ts`

**Files:**
- Create: `plugins/cn_mcp/src/tools/hk-stock-connect.ts`

- [ ] **Step 1: Create the TypeScript tool wrapper**

Create `plugins/cn_mcp/src/tools/hk-stock-connect.ts` with this content:

```typescript
import { callPython } from "./call-python.js";

export interface GetHkStockConnectParams {
  symbol: string;
}

export async function getHkStockConnect(params: GetHkStockConnectParams): Promise<string> {
  const { symbol } = params;
  const args = ["hk-stock-connect", symbol];
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching HK Stock Connect data: ${error.message}`;
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/cn_mcp/src/tools/hk-stock-connect.ts
git commit -m "feat(cn_mcp): add HK Stock Connect TypeScript MCP tool wrapper"
```

---

### Task 7: TypeScript MCP tool — `hk-hot-rank.ts`

**Files:**
- Create: `plugins/cn_mcp/src/tools/hk-hot-rank.ts`

- [ ] **Step 1: Create the TypeScript tool wrapper**

Create `plugins/cn_mcp/src/tools/hk-hot-rank.ts` with this content:

```typescript
import { callPython } from "./call-python.js";

export interface GetHkHotRankParams {
  symbol?: string;
}

export async function getHkHotRank(params: GetHkHotRankParams): Promise<string> {
  const { symbol } = params;
  const args = ["hk-hot-rank"];
  if (symbol) args.push(symbol);
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching HK hot rank: ${error.message}`;
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add plugins/cn_mcp/src/tools/hk-hot-rank.ts
git commit -m "feat(cn_mcp): add HK hot rank TypeScript MCP tool wrapper"
```

---

### Task 8: Register HK tools in MCP server (`index.ts`)

**Files:**
- Modify: `plugins/cn_mcp/src/index.ts`

- [ ] **Step 1: Add imports for the 3 new tools**

Add these imports after the existing `getCnStockInfo` import (line 8):

```typescript
import { getHkStockInfo } from "./tools/hk-stock-info.js";
import { getHkStockConnect } from "./tools/hk-stock-connect.js";
import { getHkHotRank } from "./tools/hk-hot-rank.js";
```

- [ ] **Step 2: Add 3 MCP tool registrations**

Add these registrations before the `// --- Start server ---` comment (before line 103):

```typescript
// --- HK Stock Info ---
server.registerTool(
  "get_hk_stock_info",
  {
    description: "Get basic information for a Hong Kong stock (company profile, listing info, financial indicators)",
    inputSchema: {
      symbol: z.string().describe("HK stock code (e.g. 00700, 0700.HK, or 700)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getHkStockInfo(params) }],
  })
);

// --- HK Stock Connect ---
server.registerTool(
  "get_hk_stock_connect",
  {
    description: "Get Stock Connect (港股通) southbound holding data and trend for a Hong Kong stock",
    inputSchema: {
      symbol: z.string().describe("HK stock code (e.g. 00700, 0700.HK, or 700)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getHkStockConnect(params) }],
  })
);

// --- HK Hot Rank ---
server.registerTool(
  "get_hk_hot_rank",
  {
    description: "Get Hong Kong stock popularity / hot rank. Without symbol: top-20 hottest HK stocks. With symbol: historical rank trend for that stock.",
    inputSchema: {
      symbol: z.string().optional().describe("HK stock code (optional — omit for overall top-20 ranking)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getHkHotRank(params) }],
  })
);
```

- [ ] **Step 3: Build the TypeScript project to verify compilation**

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && npm run build
```
Expected: Clean build with no errors.

- [ ] **Step 4: Commit**

```bash
git add plugins/cn_mcp/src/index.ts
git commit -m "feat(cn_mcp): register 3 HK stock MCP tools in server

Register get_hk_stock_info, get_hk_stock_connect, get_hk_hot_rank
tools in the cn MCP server."
```

---

### Task 9: Add HK market detection and tool routing to SKILL.md

**Files:**
- Modify: `skills/trading-analysis/SKILL.md`

- [ ] **Step 1: Add HK market detection section**

After the existing "A-Share Market Detection" section (after line 102 — the closing of the A-Share Market Rules code block), add this new section:

```markdown
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
```

- [ ] **Step 2: Add HK-specific instructions to the 4 analyst sub-agent prompts in SKILL.md**

For **Sub-agent 1 — Market Analyst** (around line 136), after the A-share block, add:

```markdown
>
> **If the ticker is an HK stock**, also include:
> {HK Stock Market Rules block}
> Note that HK stocks have NO daily price limit — support/resistance analysis should not reference limit-up/limit-down. Account for T+2 settlement. Consider HK trading session timing when discussing entry/exit.
```

For **Sub-agent 2 — Sentiment Analyst** (around line 156), add a new HK block after the A-share block:

```markdown
>
> **If the ticker is an HK stock**, use a mix of ta and cn MCP tools:
> {HK Stock Market Rules block}
> 1. Call `get_news(ticker="{TICKER}", start_date="{7_DAYS_BEFORE}", end_date="{DATE}")` from **ta** server for English news (note: precision is limited for HK stocks)
> 2. Call `get_hk_stock_info(symbol="{HK_CODE}")` from **cn** server for company info
> 3. Call `get_hk_stock_connect(symbol="{HK_CODE}")` from **cn** server for Stock Connect holding trends — southbound capital flows are a key sentiment indicator
> 4. Call `get_hk_hot_rank(symbol="{HK_CODE}")` from **cn** server for popularity ranking trend
> 5. HK market sentiment is influenced by both US and A-share markets — note cross-market dynamics
> 6. Write a comprehensive sentiment report with overall assessment and a Markdown summary table
```

For **Sub-agent 3 — News Analyst** (around line 178), add a new HK block after the A-share block:

```markdown
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
```

For **Sub-agent 4 — Fundamentals Analyst** (around line 197), add after the A-share block:

```markdown
>
> **If the ticker is an HK stock**, also include:
> {HK Stock Market Rules block}
> Additionally call `get_hk_stock_info(symbol="{HK_CODE}")` from **cn** server for HK-specific info (listing date, lot size, Stock Connect eligibility, financial snapshot).
> Note: HK-listed companies report under IFRS (not US GAAP or Chinese GAAP). Currency is typically HKD or USD. Identify if the company has weighted voting rights (WVR, marked with -W). Distinguish H-shares (mainland-incorporated) from red-chips (offshore-incorporated, mainland operations) from local HK companies.
```

- [ ] **Step 3: Verify the SKILL.md edits are internally consistent**

Read through the modified SKILL.md and verify:
- HK detection rules don't conflict with A-share detection rules
- Tool names match exactly: `get_hk_stock_info`, `get_hk_stock_connect`, `get_hk_hot_rank`
- `{HK_CODE}` placeholder is used for cn tools, `{TICKER}` for ta tools
- No A-share tools are referenced in HK blocks

- [ ] **Step 4: Commit**

```bash
git add skills/trading-analysis/SKILL.md
git commit -m "feat(skill): add HK stock market detection and tool routing

Add HK market detection rules, tool routing table, and HK-specific
instructions for all 4 analyst sub-agents in the trading-analysis
orchestrator."
```

---

### Task 10: Add HK stock section to `market-analyst.md`

**Files:**
- Modify: `agents/market-analyst.md`

- [ ] **Step 1: Add HK Stocks section**

After the existing "## A-Share Stocks" section (after line 78 — end of file), add:

```markdown
## HK Stocks

When analyzing a **Hong Kong stock** (ticker ends with `.HK`), the same `get_stock_data` and `get_indicators` tools from the **ta** server work — no tool substitution needed. However, apply these HK-specific rules:

**No daily price limit:**
- Unlike A-shares (±10%) or STAR/ChiNext (±20%), HK stocks have **no individual stock circuit breaker**
- Do NOT reference limit-up/limit-down (涨停/跌停) in support/resistance analysis
- Extreme intraday moves are possible — consider wider stop-loss levels

**T+2 settlement:**
- Shares settle on T+2 (compared to A-share T+1)
- This affects short-term trading strategies and margin considerations

**Trading sessions:**
- 9:00-9:30 — Pre-opening session
- 9:30-12:00 — Morning continuous trading
- 13:00-16:00 — Afternoon continuous trading
- 16:00-16:10 — Closing auction session
- No midday break as short as US markets, but a 1-hour lunch break (12:00-13:00)

**Short selling:**
- HK permits short selling for designated securities — factor this into momentum and sentiment analysis
- High short interest can signal bearish conviction or set up short squeezes

**Additional considerations:**
- Currency is **HKD** — all price levels and indicators are in Hong Kong dollars
- Index context: reference 恒生指数 (HSI) and 恒生科技指数 (HSTECH) for broad market context
- Many HK stocks have dual listings (e.g. Alibaba 9988.HK / BABA) — note arbitrage dynamics
- Lot sizes vary by stock — not uniform like A-shares (100 shares/lot)
```

- [ ] **Step 2: Commit**

```bash
git add agents/market-analyst.md
git commit -m "feat(agents): add HK stock rules to market-analyst

Add HK-specific market rules: no price limit, T+2 settlement,
trading sessions, short selling, and HSI/HSTECH index context."
```

---

### Task 11: Add HK stock section to `fundamentals-analyst.md`

**Files:**
- Modify: `agents/fundamentals-analyst.md`

- [ ] **Step 1: Add HK Stocks section**

After the existing "## A-Share Stocks" section (after line 51 — end of file), add:

```markdown
## HK Stocks

When analyzing a **Hong Kong stock** (ticker ends with `.HK`), the same `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, and `get_income_statement` tools from the **ta** server work. Apply these additional considerations:

**Additional cn server tool:**
- Call `get_hk_stock_info(symbol)` from **cn** server for HK-specific info including company profile, listing details, lot size, Stock Connect eligibility, and key financial indicators (EPS, PE, PB, ROE, ROA)

**HK fundamental analysis adjustments:**

- **Currency**: Financial data may be reported in **HKD, USD, or CNY** depending on the company. Always note the reporting currency and consider exchange rate impacts for companies with mainland China revenue.
- **Accounting standards**: HK-listed companies report under **IFRS (International Financial Reporting Standards)**, which differs from US GAAP and Chinese GAAP in areas like goodwill impairment, lease accounting, and revenue recognition.
- **Weighted Voting Rights (WVR)**: Companies marked with **-W** (e.g. Tencent, Meituan, Xiaomi) have dual-class share structures. This affects governance and control — the founder/management may control voting power disproportionate to economic ownership.
- **Company categories**: Distinguish between:
  - **H-shares**: Mainland China-incorporated, listed in HK (e.g. ICBC, China Mobile) — subject to both mainland and HK regulations
  - **Red-chips**: Offshore-incorporated (Cayman/BVI), mainland operations (e.g. Tencent, Alibaba) — primarily HK-regulated
  - **Local HK companies**: Incorporated and operating in HK (e.g. CK Hutchison, HK Exchanges)
- **Stock Connect eligibility**: Check via `get_hk_stock_info` whether the stock is a Stock Connect constituent — this affects liquidity from mainland investors.
- **Valuation context**: HK valuations often sit between A-share (premium) and US (discount) levels for dual-listed companies. Compare against HK sector averages and consider the HK market's institutional-investor-dominated nature.
```

- [ ] **Step 2: Commit**

```bash
git add agents/fundamentals-analyst.md
git commit -m "feat(agents): add HK stock rules to fundamentals-analyst

Add HK-specific fundamental analysis rules: IFRS standards, WVR,
H-share/red-chip/local categories, and valuation context."
```

---

### Task 12: Add HK stock section to `sentiment-analyst.md`

**Files:**
- Modify: `agents/sentiment-analyst.md`

- [ ] **Step 1: Add HK Stocks section**

After the existing "## A-Share Stocks" section (after line 50 — end of file), add:

```markdown
## HK Stocks

When analyzing a **Hong Kong stock** (ticker ends with `.HK`), apply the following adjustments:

**Tool usage — mix of ta and cn servers:**

| Data Need | Tool | Server |
|-----------|------|--------|
| Company news | `get_news(ticker, start, end)` | ta — English news, limited precision for HK stocks |
| Company info | `get_hk_stock_info(symbol)` | cn |
| Stock Connect holdings | `get_hk_stock_connect(symbol)` | cn |
| Hot rank / popularity | `get_hk_hot_rank(symbol)` | cn |

**HK sentiment analysis focus areas:**
- **Stock Connect southbound flows (港股通南向资金)**: The single most important HK-specific sentiment indicator. Sustained net inflows from mainland investors signal institutional confidence. Use `get_hk_stock_connect` to track holding trends — increasing holdings = bullish signal, decreasing = bearish.
- **Hot rank / popularity (人气排名)**: Use `get_hk_hot_rank` to gauge retail attention. A rapidly rising rank suggests growing interest; falling rank suggests fading momentum.
- **Cross-market dynamics**: HK market sentiment is heavily influenced by both US and A-share markets. US tech selloffs impact HK tech stocks; A-share rallies can boost HK-listed Chinese companies via Stock Connect flows.
- **News precision caveat**: HK stock news from Yahoo Finance (`get_news`) tends to return general Asian/global news rather than company-specific articles. Weight this data source lower than for US stocks. Focus more on Stock Connect data and hot rank for sentiment signals.
- **Institutional dominance**: Unlike A-shares (60-70% retail), HK is more institutional. Sentiment shifts tend to be more measured but more sustained.
```

- [ ] **Step 2: Commit**

```bash
git add agents/sentiment-analyst.md
git commit -m "feat(agents): add HK stock rules to sentiment-analyst

Add HK-specific sentiment rules: Stock Connect flows, hot rank,
cross-market dynamics, and news precision caveats."
```

---

### Task 13: Add HK stock section to `news-analyst.md`

**Files:**
- Modify: `agents/news-analyst.md`

- [ ] **Step 1: Add HK Stocks section**

After the existing "## A-Share Stocks" section (after line 54 — end of file), add:

```markdown
## HK Stocks

When analyzing a **Hong Kong stock** (ticker ends with `.HK`), apply the following adjustments:

**Tool usage — mix of ta and cn servers:**

| Standard Tool (ta) | HK Replacement | Server |
|--------------------|----------------|--------|
| `get_news` | `get_news` (same tool, limited precision) | ta |
| `get_global_news` | `get_global_news` (same tool) | ta |
| `get_insider_transactions` | `get_hk_stock_connect(symbol)` — Stock Connect flows replace insider data | cn |

**Additional cn server tools to call:**
- `get_hk_stock_info(symbol)` — company info including Stock Connect eligibility
- `get_hk_hot_rank(symbol)` — popularity trend (optional, for context)

**Important:** Do NOT use A-share-specific tools for HK stocks:
- ❌ `get_cn_news` — A-share news only
- ❌ `get_cn_dragon_tiger` — A-share 龙虎榜 only
- ❌ `get_cn_shareholder_changes` — A-share shareholders only
- ❌ `get_cn_global_news` — A-share macro news only

**HK news analysis focus areas:**
- **Stock Connect flows (港股通)**: Replaces insider transactions and 龙虎榜 as the primary fund flow indicator. Use `get_hk_stock_connect` to see whether southbound capital is accumulating or divesting.
- **US-China relations**: A dominant risk factor for HK-listed Chinese companies — trade tensions, sanctions, delisting threats, and regulatory actions can move stocks significantly.
- **Regulatory changes**: HKEX listing rule changes, SFC enforcement actions, and mainland regulatory changes (e.g. gaming, education, fintech crackdowns) all impact HK stocks.
- **Cross-listing dynamics**: For stocks with dual US/HK listings (e.g. BABA/9988.HK, JD/9618.HK), monitor both markets for news that may create arbitrage or contagion.
- **News data limitation**: Yahoo Finance news for HK tickers returns mostly general Asian/global articles. This is a known limitation — compensate by weighting Stock Connect data and macro news more heavily.
```

- [ ] **Step 2: Commit**

```bash
git add agents/news-analyst.md
git commit -m "feat(agents): add HK stock rules to news-analyst

Add HK-specific news analysis rules: Stock Connect as fund flow
indicator, US-China risks, and news data limitations."
```

---

### Task 14: Build, verify, and end-to-end test

**Files:**
- No new files — verification only

- [ ] **Step 1: Build the cn MCP server**

Run:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && npm run build
```
Expected: Clean build with no TypeScript errors.

- [ ] **Step 2: Test each new MCP tool via the Python CLI**

Run all 3 HK tools:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -m python hk-stock-info 00700 | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('data') else 'FAIL')"
```
Expected: `OK`

```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -m python hk-stock-connect 00700 | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('data') else 'FAIL')"
```
Expected: `OK`

```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -m python hk-hot-rank | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('data') else 'FAIL')"
```
Expected: `OK`

- [ ] **Step 3: Verify ta server tools work with .HK tickers**

Use the MCP tools directly to confirm Yahoo Finance handles `.HK`:
- Call `get_stock_data(symbol="0700.HK", start_date="2026-03-01", end_date="2026-04-06")` — should return price data
- Call `get_indicators(symbol="0700.HK", indicator="rsi", curr_date="2026-04-06")` — should return RSI values
- Call `get_fundamentals(ticker="0700.HK")` — should return company data

- [ ] **Step 4: Confirm no regression on existing tools**

Quick check that existing A-share tools still work:
```bash
cd /Users/jianliwei/personal-repos/tradingagents-marketplace/plugins/cn_mcp && uv run python -m python cn-stock-info 600519 | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('data') else 'FAIL')"
```
Expected: `OK`

- [ ] **Step 5: Run a full end-to-end analysis on a HK stock**

Run the full trading-analysis pipeline on Tencent (0700.HK) to verify the complete flow works:
- Use the `ta:trading-analysis` skill with ticker `0700.HK`
- Verify all 4 analyst sub-agents complete successfully
- Verify reports are generated in `analysis/` directory
- Verify no A-share tools are called during the analysis

