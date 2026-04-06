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
