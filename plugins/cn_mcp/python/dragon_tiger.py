"""Dragon Tiger (龙虎榜) list data via AKShare."""

from __future__ import annotations

import traceback
from typing import Any

import akshare as ak
import pandas as pd


def _yahoo_to_akshare(ticker: str) -> str:
    """Convert Yahoo-format ticker (600519.SS) to 6-digit code (600519)."""
    return ticker.split(".")[0]


def _df_to_records(df: pd.DataFrame, limit: int | None = None) -> list[dict[str, Any]]:
    """Convert a DataFrame to a list of JSON-safe dicts."""
    if df is None or df.empty:
        return []
    if limit:
        df = df.head(limit)
    # Convert all values to JSON-serialisable types
    records = df.astype(str).to_dict(orient="records")
    return records


def get_cn_dragon_tiger(
    symbol: str, start_date: str, end_date: str
) -> dict[str, Any]:
    """Get Dragon Tiger list details for a specific stock.

    Args:
        symbol: Ticker in Yahoo format or raw 6-digit code.
        start_date: Start date in YYYYMMDD format.
        end_date: End date in YYYYMMDD format.

    Returns:
        Dict with "text" (Markdown) and "data".
    """
    code = _yahoo_to_akshare(symbol)
    try:
        df: pd.DataFrame = ak.stock_lhb_detail_em(
            start_date=start_date, end_date=end_date
        )
        if df is None or df.empty:
            return {
                "text": f"No dragon tiger data found for period {start_date}-{end_date}.",
                "data": [],
            }

        # Filter for the specific stock code
        # The column name may vary; try common names
        code_col = None
        for col_name in ["代码", "证券代码", "股票代码", "code"]:
            if col_name in df.columns:
                code_col = col_name
                break

        if code_col:
            filtered = df[df[code_col].astype(str).str.contains(code)]
        else:
            # If no known code column, return all and let caller filter
            filtered = df

        if filtered.empty:
            return {
                "text": f"No dragon tiger records found for {code} in {start_date}-{end_date}.",
                "data": [],
            }

        records = _df_to_records(filtered)

        lines: list[str] = [f"## 龙虎榜 — {code} ({start_date} ~ {end_date})\n"]
        lines.append(f"共 {len(records)} 条记录\n")
        for rec in records[:20]:  # cap display
            name = rec.get("名称", rec.get("证券名称", rec.get("股票名称", code)))
            date_val = rec.get("上榜日期", rec.get("日期", ""))
            reason = rec.get("解读", rec.get("上榜原因", ""))
            lines.append(f"- **{name}** {date_val} — {reason}")

        return {"text": "\n".join(lines), "data": records}

    except Exception as exc:
        return {
            "text": f"Error fetching dragon tiger data for {code}: {exc}",
            "data": [],
            "error": traceback.format_exc(),
        }


def get_cn_dragon_tiger_stats(period: str = "近一月") -> dict[str, Any]:
    """Get aggregated dragon tiger statistics.

    Args:
        period: One of "近一月", "近三月", "近六月", "近一年".

    Returns:
        Dict with "text" (Markdown) and "data".
    """
    try:
        df: pd.DataFrame = ak.stock_lhb_stock_statistic_em(symbol=period)
        if df is None or df.empty:
            return {
                "text": f"No dragon tiger statistics for period '{period}'.",
                "data": [],
            }

        records = _df_to_records(df, limit=50)

        lines: list[str] = [f"## 龙虎榜统计 — {period}\n"]
        lines.append(f"共 {len(records)} 只股票\n")
        for rec in records[:30]:
            name = rec.get("名称", rec.get("证券名称", ""))
            code_val = rec.get("代码", rec.get("证券代码", ""))
            count = rec.get("上榜次数", "")
            lines.append(f"- {code_val} {name} — 上榜 {count} 次")

        return {"text": "\n".join(lines), "data": records}

    except Exception as exc:
        return {
            "text": f"Error fetching dragon tiger stats: {exc}",
            "data": [],
            "error": traceback.format_exc(),
        }
