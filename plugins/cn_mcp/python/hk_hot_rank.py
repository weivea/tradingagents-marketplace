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
