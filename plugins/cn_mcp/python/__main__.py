"""CLI entry point: python -m python <command> [args]"""

import argparse
import datetime
import io
import json
import sys

# Force UTF-8 stdout (system default may be GBK/cp936 on Windows)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def _default_serializer(obj: object) -> object:
    """JSON serializer for types not handled by default."""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    if hasattr(obj, "item"):  # numpy scalar
        return obj.item()
    # Handle pandas NaT / NaN
    try:
        import math
        if isinstance(obj, float) and math.isnan(obj):
            return None
    except (TypeError, ValueError):
        pass
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _sanitize(obj: object) -> object:
    """Recursively replace float NaN with None for JSON safety."""
    import math

    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


def _dump(result: dict) -> None:
    """Print result dict as JSON with safe serialization."""
    clean = _sanitize(result)
    print(json.dumps(clean, ensure_ascii=False, indent=2, default=_default_serializer))


def cmd_cn_news(args: argparse.Namespace) -> None:
    from .news import get_cn_news

    result = get_cn_news(args.symbol, limit=args.limit)
    _dump(result)


def cmd_cn_global_news(args: argparse.Namespace) -> None:
    from .news import get_cn_global_news

    result = get_cn_global_news(limit=args.limit)
    _dump(result)


def cmd_cn_dragon_tiger(args: argparse.Namespace) -> None:
    from .dragon_tiger import get_cn_dragon_tiger

    result = get_cn_dragon_tiger(
        args.symbol, start_date=args.start_date, end_date=args.end_date
    )
    _dump(result)


def cmd_cn_dragon_tiger_stats(args: argparse.Namespace) -> None:
    from .dragon_tiger import get_cn_dragon_tiger_stats

    result = get_cn_dragon_tiger_stats(period=args.period)
    _dump(result)


def cmd_cn_shareholder(args: argparse.Namespace) -> None:
    from .shareholder import get_cn_shareholder_changes

    result = get_cn_shareholder_changes(args.symbol, date=args.date)
    _dump(result)


def cmd_cn_stock_info(args: argparse.Namespace) -> None:
    from .stock_info import get_cn_stock_info

    result = get_cn_stock_info(args.symbol)
    _dump(result)


def cmd_hk_stock_info(args: argparse.Namespace) -> None:
    from .hk_stock_info import get_hk_stock_info

    result = get_hk_stock_info(args.symbol)
    _dump(result)


def cmd_hk_stock_connect(args: argparse.Namespace) -> None:
    from .hk_stock_connect import get_hk_stock_connect

    result = get_hk_stock_connect(args.symbol)
    _dump(result)


def cmd_cn_stock_quote(args: argparse.Namespace) -> None:
    from .quote import get_cn_stock_quote

    result = get_cn_stock_quote(args.symbol)
    _dump(result)


def cmd_hk_stock_quote(args: argparse.Namespace) -> None:
    from .quote import get_hk_stock_quote

    result = get_hk_stock_quote(args.symbol)
    _dump(result)


def cmd_hk_hot_rank(args: argparse.Namespace) -> None:
    from .hk_hot_rank import get_hk_hot_rank

    symbol = getattr(args, "symbol", None)
    result = get_hk_hot_rank(symbol=symbol)
    _dump(result)


def main() -> None:
    parser = argparse.ArgumentParser(prog="cn_mcp", description="Chinese A-share data CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # cn-news
    p_news = sub.add_parser("cn-news", help="Get news for a Chinese stock")
    p_news.add_argument("symbol", help="Ticker symbol (e.g. 600519.SS or 600519)")
    p_news.add_argument("--limit", type=int, default=20, help="Max articles to return")
    p_news.set_defaults(func=cmd_cn_news)

    # cn-global-news
    p_gnews = sub.add_parser("cn-global-news", help="Get macro / A-share global news")
    p_gnews.add_argument("--limit", type=int, default=20, help="Max articles to return")
    p_gnews.set_defaults(func=cmd_cn_global_news)

    # cn-dragon-tiger
    p_dt = sub.add_parser("cn-dragon-tiger", help="Dragon tiger list for a stock")
    p_dt.add_argument("symbol", help="Ticker symbol")
    p_dt.add_argument("--start-date", required=True, help="Start date YYYYMMDD")
    p_dt.add_argument("--end-date", required=True, help="End date YYYYMMDD")
    p_dt.set_defaults(func=cmd_cn_dragon_tiger)

    # cn-dragon-tiger-stats
    p_dts = sub.add_parser("cn-dragon-tiger-stats", help="Dragon tiger statistics")
    p_dts.add_argument("--period", default="近一月", help="Period: 近一月 / 近三月 / 近六月 / 近一年")
    p_dts.set_defaults(func=cmd_cn_dragon_tiger_stats)

    # cn-shareholder
    p_sh = sub.add_parser("cn-shareholder", help="Shareholder changes for a stock")
    p_sh.add_argument("symbol", help="Ticker symbol")
    p_sh.add_argument("--date", required=True, help="Report date YYYYMMDD")
    p_sh.set_defaults(func=cmd_cn_shareholder)

    # cn-stock-info
    p_info = sub.add_parser("cn-stock-info", help="Basic stock information")
    p_info.add_argument("symbol", help="Ticker symbol (e.g. 600519.SS or 600519)")
    p_info.set_defaults(func=cmd_cn_stock_info)

    # hk-stock-info
    p_hk_info = sub.add_parser("hk-stock-info", help="HK stock basic information")
    p_hk_info.add_argument("symbol", help="HK stock code (e.g. 00700)")
    p_hk_info.set_defaults(func=cmd_hk_stock_info)

    # hk-stock-connect
    p_hk_connect = sub.add_parser("hk-stock-connect", help="HK Stock Connect holding data")
    p_hk_connect.add_argument("symbol", help="HK stock code (e.g. 00700)")
    p_hk_connect.set_defaults(func=cmd_hk_stock_connect)

    # cn-stock-quote
    p_cn_q = sub.add_parser("cn-stock-quote", help="A-share realtime quote + 5档")
    p_cn_q.add_argument("symbol", help="Ticker symbol (e.g. 600519.SS or 600519)")
    p_cn_q.set_defaults(func=cmd_cn_stock_quote)

    # hk-stock-quote
    p_hk_q = sub.add_parser("hk-stock-quote", help="HK near-realtime quote (1-min bar)")
    p_hk_q.add_argument("symbol", help="HK stock code (e.g. 00700)")
    p_hk_q.set_defaults(func=cmd_hk_stock_quote)

    # hk-hot-rank
    p_hk_rank = sub.add_parser("hk-hot-rank", help="HK stock hot rank")
    p_hk_rank.add_argument("symbol", nargs="?", default=None, help="HK stock code (optional)")
    p_hk_rank.set_defaults(func=cmd_hk_hot_rank)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
