"""Shareholder (股东) data via AKShare.

Uses stock_main_stock_holder (top-10 holders per stock) and
stock_shareholder_change_ths (historical shareholder changes).
"""

from __future__ import annotations

import traceback
from typing import Any

import akshare as ak
import pandas as pd


def _yahoo_to_akshare(ticker: str) -> str:
    """Convert Yahoo-format ticker (600519.SS) to 6-digit code (600519)."""
    return ticker.split(".")[0]


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame to list of dicts, converting dates to strings."""
    # Convert datetime columns to strings to avoid serialisation issues
    for col in df.select_dtypes(include=["datetime64", "datetimetz"]).columns:
        df[col] = df[col].astype(str)
    return df.to_dict(orient="records")


def get_cn_shareholder_changes(symbol: str, date: str) -> dict[str, Any]:
    """Get top-10 shareholders and recent shareholder changes for a stock.

    Uses two AKShare endpoints:
      - stock_main_stock_holder(stock=code): top-10 holders with dates
      - stock_shareholder_change_ths(symbol=code): historical changes

    The *date* parameter is used to filter holder records closest to the given
    report period.  Format: YYYYMMDD.

    Args:
        symbol: Ticker in Yahoo format or raw 6-digit code.
        date: Report date in YYYYMMDD format (used for filtering).

    Returns:
        Dict with "text" (Markdown), "holders" and "changes" data.
    """
    code = _yahoo_to_akshare(symbol)
    holders_data: list[dict[str, Any]] = []
    changes_data: list[dict[str, Any]] = []
    lines: list[str] = [f"## 股东信息 — {code}\n"]

    # --- Top-10 holders ---
    try:
        df_holders: pd.DataFrame = ak.stock_main_stock_holder(stock=code)
        if df_holders is not None and not df_holders.empty:
            # Filter by date if possible (截至日期 column)
            if "截至日期" in df_holders.columns:
                # Convert date param YYYYMMDD -> YYYY-MM-DD for comparison
                target = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
                # Find the closest reporting date
                dates_available = df_holders["截至日期"].astype(str).unique()
                # Try exact match first, then pick the latest available
                if target in dates_available:
                    df_holders = df_holders[df_holders["截至日期"].astype(str) == target]
                else:
                    # Just use the latest available date group
                    latest = sorted(dates_available)[-1]
                    df_holders = df_holders[df_holders["截至日期"].astype(str) == latest]
                    lines.append(f"*注: 未找到 {target} 数据，展示最新 {latest} 数据*\n")

            holders_data = _df_to_records(df_holders)

            lines.append("### 前十大股东\n")
            for rec in holders_data[:10]:
                name = str(rec.get("股东名称", ""))
                ratio = rec.get("持股比例", None)
                shares = rec.get("持股数量", None)
                nature = str(rec.get("股本性质", ""))
                ratio_str = f"{ratio}%" if ratio is not None else ""
                shares_str = f" ({shares}股)" if shares is not None else ""
                lines.append(f"- {name} — {ratio_str}{shares_str} [{nature}]")
            lines.append("")
    except Exception as exc:
        lines.append(f"*获取股东列表失败: {exc}*\n")

    # --- Shareholder changes ---
    try:
        df_changes: pd.DataFrame = ak.stock_shareholder_change_ths(symbol=code)
        if df_changes is not None and not df_changes.empty:
            # Show latest 10 changes
            changes_data = _df_to_records(df_changes.head(10))

            lines.append("### 近期股东变动\n")
            for rec in changes_data:
                ann_date = rec.get("公告日期", "")
                holder = rec.get("变动股东", "")
                qty = rec.get("变动数量", "")
                method = rec.get("变动途径", "")
                lines.append(f"- {ann_date} | {holder} | {qty} | {method}")
            lines.append("")
    except Exception as exc:
        lines.append(f"*获取股东变动失败: {exc}*\n")

    if not holders_data and not changes_data:
        return {
            "text": f"No shareholder data found for {code} (date={date}).",
            "holders": [],
            "changes": [],
        }

    return {
        "text": "\n".join(lines),
        "holders": holders_data,
        "changes": changes_data,
    }
