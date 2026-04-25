"""Realtime / near-realtime quote tools via AKShare.

- get_cn_stock_quote: A-share spot + 5档盘口 (stock_bid_ask_em, ~3s delay)
- get_hk_stock_quote: HK near-realtime via stock_hk_hist_min_em (last 1-min bar, ~0-60s delay)
"""

from __future__ import annotations

import traceback
from typing import Any

import time
import urllib.request

import akshare as ak
import pandas as pd


TENCENT_HK_URL = "https://qt.gtimg.cn/q=hk{code}"
TENCENT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://stockapp.finance.qq.com/",
}


def _retry(fn, attempts: int = 3, sleep: float = 1.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(sleep * (i + 1))
    raise last  # type: ignore[misc]


def _tencent_hk_quote(code: str) -> dict[str, Any] | None:
    """Fallback: parse Tencent HK quote string.

    Field index reference (key ones):
      1=name, 2=code, 3=last, 4=prev_close, 5=open, 6=volume(shares),
      30=time, 31=change, 32=change_pct, 33=high, 34=low, 36=amount,
      39=PE, 45=turnover_rate, 46=PB
    """
    url = TENCENT_HK_URL.format(code=code)
    req = urllib.request.Request(url, headers=TENCENT_HEADERS)
    raw = urllib.request.urlopen(req, timeout=8).read().decode("gb18030", errors="ignore")
    if "=" not in raw:
        return None
    payload = raw.split('="', 1)[1].rstrip('";\n')
    parts = payload.split("~")
    if len(parts) < 50:
        return None

    def f(idx: int) -> float | None:
        try:
            return float(parts[idx])
        except (ValueError, IndexError):
            return None

    return {
        "name": parts[1] if len(parts) > 1 else None,
        "code": code,
        "time": parts[30] if len(parts) > 30 else None,
        "last": f(3),
        "prev_close": f(4),
        "open": f(5),
        "high": f(33),
        "low": f(34),
        "change": f(31),
        "change_pct": f(32),
        "volume": f(6),
        "amount": f(37),
        "pe_ttm": f(39),
        "pb": f(46),
        "turnover_rate": f(38),
        "_source": "tencent",
    }


def _strip(symbol: str) -> str:
    return symbol.split(".")[0]


def _norm_hk(symbol: str) -> str:
    code = _strip(symbol).lstrip("0") or "0"
    return code.zfill(5)


def get_cn_stock_quote(symbol: str) -> dict[str, Any]:
    """A-share realtime quote with 5-level order book.

    Source: ak.stock_bid_ask_em (东财 push2, ~3s delay).
    """
    code = _strip(symbol)
    try:
        df: pd.DataFrame = ak.stock_bid_ask_em(symbol=code)
        if df is None or df.empty:
            return {"text": f"No quote data for {code}.", "data": {}}

        # Two-column item/value table -> dict
        kv: dict[str, Any] = {}
        for _, row in df.iterrows():
            k = str(row.iloc[0])
            v = row.iloc[1]
            try:
                v = float(v)
                if v.is_integer():
                    v = int(v)
            except (TypeError, ValueError):
                pass
            kv[k] = v

        last = kv.get("最新")
        prev = kv.get("昨收")
        chg = kv.get("涨跌")
        chg_pct = kv.get("涨幅")
        lines = [
            f"## A股实时报价 — {code}\n",
            f"- **最新价**: {last}  (昨收 {prev}, 涨跌 {chg}, 涨幅 {chg_pct}%)",
            f"- **今开/最高/最低**: {kv.get('今开')} / {kv.get('最高')} / {kv.get('最低')}",
            f"- **成交量(手)/金额(元)**: {kv.get('总手')} / {kv.get('金额')}",
            f"- **换手率/量比**: {kv.get('换手')}% / {kv.get('量比')}",
            f"- **涨停/跌停**: {kv.get('涨停')} / {kv.get('跌停')}",
            f"- **外盘/内盘**: {kv.get('外盘')} / {kv.get('内盘')}",
            "",
            "### 五档盘口",
            "| 档 | 买价 | 买量(手) | 卖价 | 卖量(手) |",
            "|---|---|---|---|---|",
        ]
        for i in range(1, 6):
            lines.append(
                f"| {i} | {kv.get(f'buy_{i}')} | {kv.get(f'buy_{i}_vol')} | "
                f"{kv.get(f'sell_{i}')} | {kv.get(f'sell_{i}_vol')} |"
            )

        return {"text": "\n".join(lines), "data": kv}
    except Exception as exc:
        return {
            "text": f"Error fetching CN quote for {code}: {exc}",
            "data": {},
            "error": traceback.format_exc(),
        }


def get_hk_stock_quote(symbol: str) -> dict[str, Any]:
    """HK near-realtime quote via 1-min K-line last bar.

    Source: ak.stock_hk_hist_min_em (东财, ~0-60s delay).
    Note: HK五档需要付费 LV1 行情, akshare 拿不到.
    """
    code = _norm_hk(symbol)
    # Try akshare first
    try:
        df_min: pd.DataFrame = _retry(
            lambda: ak.stock_hk_hist_min_em(symbol=code, period="1", adjust="")
        )
        if df_min is None or df_min.empty:
            return {"text": f"No HK quote data for {code}.", "data": {}}
        last = df_min.iloc[-1]

        # 当日日K拿涨跌幅
        df_day: pd.DataFrame = _retry(
            lambda: ak.stock_hk_hist(symbol=code, period="daily", adjust="")
        ).tail(2)
        today = df_day.iloc[-1] if not df_day.empty else None
        prev_close = df_day.iloc[-2]["收盘"] if len(df_day) >= 2 else None

        latest_price = last.get("最新价") or last.get("收盘")
        chg = (
            round(float(latest_price) - float(prev_close), 4)
            if prev_close is not None and latest_price is not None
            else None
        )
        chg_pct = (
            round(chg / float(prev_close) * 100, 3)
            if chg is not None and prev_close
            else None
        )

        kv: dict[str, Any] = {
            "code": code,
            "time": str(last.get("时间")),
            "last": float(latest_price) if latest_price is not None else None,
            "prev_close": float(prev_close) if prev_close is not None else None,
            "change": chg,
            "change_pct": chg_pct,
            "open": float(today["开盘"]) if today is not None else None,
            "high": float(today["最高"]) if today is not None else None,
            "low": float(today["最低"]) if today is not None else None,
            "volume": int(today["成交量"]) if today is not None else None,
            "amount": float(today["成交额"]) if today is not None else None,
            "turnover_rate": float(today["换手率"]) if today is not None else None,
        }
        lines = [
            f"## 港股准实时报价 — {code}",
            f"_数据时间: {kv['time']} (akshare 1-min bar, 延迟约 0-60s)_\n",
            f"- **最新价**: {kv['last']}  (昨收 {kv['prev_close']}, 涨跌 {kv['change']}, 涨幅 {kv['change_pct']}%)",
            f"- **今开/最高/最低**: {kv['open']} / {kv['high']} / {kv['low']}",
            f"- **成交量(股)/金额(港元)**: {kv['volume']} / {kv['amount']}",
            f"- **换手率**: {kv['turnover_rate']}%",
            "",
            "_注: 港股五档盘口需付费 LV1 行情, akshare 不提供._",
        ]
        return {"text": "\n".join(lines), "data": kv}
    except Exception as exc_ak:
        # Fallback to Tencent
        try:
            kv = _tencent_hk_quote(code)
            if not kv:
                raise RuntimeError("tencent empty")
            lines = [
                f"## 港股准实时报价 — {kv.get('name') or code} ({code})",
                f"_数据时间: {kv['time']} (Tencent fallback, akshare unreachable)_\n",
                f"- **最新价**: {kv['last']}  (昨收 {kv['prev_close']}, 涨跌 {kv['change']}, 涨幅 {kv['change_pct']}%)",
                f"- **今开/最高/最低**: {kv['open']} / {kv['high']} / {kv['low']}",
                f"- **成交量(股)/金额(港元)**: {kv['volume']} / {kv['amount']}",
                f"- **换手率/PE(TTM)/PB**: {kv['turnover_rate']}% / {kv['pe_ttm']} / {kv['pb']}",
            ]
            return {"text": "\n".join(lines), "data": kv}
        except Exception as exc_tc:
            return {
                "text": f"Error fetching HK quote for {code}: akshare={exc_ak} | tencent={exc_tc}",
                "data": {},
                "error": traceback.format_exc(),
            }
