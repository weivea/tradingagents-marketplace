"""Chinese A-share news data via AKShare."""

from __future__ import annotations

import traceback
from typing import Any

import akshare as ak
import pandas as pd


def _yahoo_to_akshare(ticker: str) -> str:
    """Convert Yahoo-format ticker (600519.SS) to 6-digit code (600519)."""
    return ticker.split(".")[0]


def get_cn_news(symbol: str, limit: int = 20) -> dict[str, Any]:
    """Get company-specific news for a Chinese A-share stock.

    Args:
        symbol: Ticker in Yahoo format (e.g. 600519.SS) or raw 6-digit code.
        limit: Maximum number of articles to return.

    Returns:
        Dict with "text" (Markdown) and "count".
    """
    code = _yahoo_to_akshare(symbol)
    try:
        df: pd.DataFrame = ak.stock_news_em(symbol=code)
        if df is None or df.empty:
            return {"text": f"No news found for {code}.", "count": 0, "articles": []}

        df = df.head(limit)

        articles: list[dict[str, str]] = []
        lines: list[str] = [f"## 个股新闻 — {code}\n"]

        for _, row in df.iterrows():
            title = str(row.get("新闻标题", row.get("title", "")))
            content = str(row.get("新闻内容", row.get("content", "")))
            pub_time = str(row.get("发布时间", row.get("datetime", "")))
            source = str(row.get("文章来源", row.get("source", "")))

            articles.append(
                {"title": title, "content": content, "time": pub_time, "source": source}
            )
            lines.append(f"### {title}")
            lines.append(f"*{pub_time}* — {source}\n")
            snippet = content[:200] + "..." if len(content) > 200 else content
            lines.append(snippet + "\n")

        return {"text": "\n".join(lines), "count": len(articles), "articles": articles}

    except Exception as exc:
        return {
            "text": f"Error fetching news for {code}: {exc}",
            "count": 0,
            "articles": [],
            "error": traceback.format_exc(),
        }


def get_cn_global_news(limit: int = 20) -> dict[str, Any]:
    """Get macro / A-share global news by searching multiple keywords.

    Searches keywords ["A股", "央行", "证监会", "宏观经济", "GDP"] and
    deduplicates by title.

    Args:
        limit: Maximum total articles to return.

    Returns:
        Dict with "text" (Markdown) and "count".
    """
    keywords = ["A股", "央行", "证监会", "宏观经济", "GDP"]
    seen_titles: set[str] = set()
    all_articles: list[dict[str, str]] = []

    for kw in keywords:
        try:
            df: pd.DataFrame = ak.stock_news_em(symbol=kw)
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                title = str(row.get("新闻标题", row.get("title", "")))
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                content = str(row.get("新闻内容", row.get("content", "")))
                pub_time = str(row.get("发布时间", row.get("datetime", "")))
                source = str(row.get("文章来源", row.get("source", "")))

                all_articles.append(
                    {"title": title, "content": content, "time": pub_time, "source": source}
                )
                if len(all_articles) >= limit:
                    break
        except Exception:
            continue  # skip keywords that fail

        if len(all_articles) >= limit:
            break

    all_articles = all_articles[:limit]

    lines: list[str] = ["## A股宏观新闻\n"]
    for art in all_articles:
        lines.append(f"### {art['title']}")
        lines.append(f"*{art['time']}* — {art['source']}\n")
        snippet = art["content"][:200] + "..." if len(art["content"]) > 200 else art["content"]
        lines.append(snippet + "\n")

    return {"text": "\n".join(lines), "count": len(all_articles), "articles": all_articles}
