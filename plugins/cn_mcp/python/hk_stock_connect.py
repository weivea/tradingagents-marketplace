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
