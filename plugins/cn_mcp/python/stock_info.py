"""Stock info (个股信息) via AKShare."""

from __future__ import annotations

import traceback
from typing import Any

import akshare as ak
import pandas as pd


def _yahoo_to_akshare(ticker: str) -> str:
    """Convert Yahoo-format ticker (600519.SS) to 6-digit code (600519)."""
    return ticker.split(".")[0]


def get_cn_stock_info(symbol: str) -> dict[str, Any]:
    """Get basic information for a Chinese A-share stock.

    Args:
        symbol: Ticker in Yahoo format (e.g. 600519.SS) or raw 6-digit code.

    Returns:
        Dict with "text" (Markdown) and "data".
    """
    code = _yahoo_to_akshare(symbol)
    try:
        df: pd.DataFrame = ak.stock_individual_info_em(symbol=code)
        if df is None or df.empty:
            return {
                "text": f"No info found for {code}.",
                "data": {},
            }

        # The result is typically a two-column table: item / value
        data: dict[str, str] = {}
        for _, row in df.iterrows():
            key = str(row.iloc[0])
            val = str(row.iloc[1])
            data[key] = val

        lines: list[str] = [f"## 个股信息 — {code}\n"]
        for k, v in data.items():
            lines.append(f"- **{k}**: {v}")

        return {"text": "\n".join(lines), "data": data}

    except Exception as exc:
        return {
            "text": f"Error fetching stock info for {code}: {exc}",
            "data": {},
            "error": traceback.format_exc(),
        }
