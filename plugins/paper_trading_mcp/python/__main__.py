"""CLI dispatcher: python -m python <subcommand> [args].

All subcommands return JSON on stdout.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def _dump(result: object) -> None:
    def default(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        raise TypeError(f"not serializable: {type(o).__name__}")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=default))


def _parse_json(s: str | None):
    return json.loads(s) if s else None


def cmd_place_order(args):
    from .db import connect
    from .orders import place_order
    conn = connect()
    res = place_order(
        conn,
        account_id=args.account_id, symbol=args.symbol, market=args.market,
        side=args.side, qty=args.qty, order_type=args.order_type,
        price=args.price, ref_price=args.ref_price,
    )
    _dump(res)


def cmd_cancel_order(args):
    from .db import connect
    from .orders import cancel_order
    conn = connect()
    _dump(cancel_order(conn, account_id=args.account_id, order_id=args.order_id))


def cmd_tick(args):
    from .db import connect
    from .settlement import tick_pending_orders
    conn = connect()
    pm = _parse_json(args.price_map) or {}
    _dump(tick_pending_orders(conn, account_id=args.account_id, price_map=pm))


def cmd_get_portfolio(args):
    from .db import connect
    from .portfolio import get_portfolio
    conn = connect()
    pm = _parse_json(args.price_map)
    _dump(get_portfolio(conn, args.account_id, price_map=pm))


def cmd_get_positions(args):
    from .db import connect
    from .portfolio import get_positions
    conn = connect()
    _dump(get_positions(conn, args.account_id))


def cmd_get_cash(args):
    from .db import connect
    from .accounts import get_cash
    conn = connect()
    _dump(get_cash(conn, args.account_id))


def cmd_get_pending(args):
    from .db import connect
    from .portfolio import get_pending_orders
    conn = connect()
    _dump(get_pending_orders(conn, args.account_id))


def cmd_get_history(args):
    from .db import connect
    from .portfolio import get_order_history
    conn = connect()
    _dump(get_order_history(conn, args.account_id,
                            start_date=args.start_date, end_date=args.end_date))


def cmd_get_pnl(args):
    from .db import connect
    from .portfolio import get_pnl
    conn = connect()
    pm = _parse_json(args.price_map)
    _dump(get_pnl(conn, args.account_id, date=args.date, price_map=pm))


def cmd_append_journal(args):
    from .journal import append_journal
    _dump(append_journal(args.account_id, args.date, args.markdown))


def cmd_read_journal(args):
    from .journal import read_journal
    _dump({"content": read_journal(args.account_id, args.date)})


def cmd_init_discussion(args):
    from .discussion import init_discussion
    pnl = _parse_json(args.pnl_summary) or {}
    _dump(init_discussion(args.date, pnl_summary=pnl, force=args.force))


def cmd_read_discussion(args):
    from .discussion import read_discussion
    _dump({"content": read_discussion(args.date)})


def cmd_append_discussion(args):
    from .discussion import append_discussion
    _dump(append_discussion(
        args.date, speaker=args.speaker, markdown=args.markdown,
        next_speaker=args.next_speaker, reason=args.reason or "",
    ))


def main():
    p = argparse.ArgumentParser(prog="paper_trading_mcp")
    sub = p.add_subparsers(dest="command", required=True)

    po = sub.add_parser("place-order")
    po.add_argument("--account-id", required=True)
    po.add_argument("--symbol", required=True)
    po.add_argument("--market", required=True, choices=["CN", "HK", "US"])
    po.add_argument("--side", required=True, choices=["buy", "sell"])
    po.add_argument("--qty", type=float, required=True)
    po.add_argument("--order-type", required=True, choices=["market", "limit", "stop"])
    po.add_argument("--price", type=float)
    po.add_argument("--ref-price", type=float)
    po.set_defaults(func=cmd_place_order)

    co = sub.add_parser("cancel-order")
    co.add_argument("--account-id", required=True)
    co.add_argument("--order-id", type=int, required=True)
    co.set_defaults(func=cmd_cancel_order)

    tk = sub.add_parser("tick-pending-orders")
    tk.add_argument("--account-id", required=True)
    tk.add_argument("--price-map", help="JSON object like {\"AAPL\": 150.0}")
    tk.set_defaults(func=cmd_tick)

    gp = sub.add_parser("get-portfolio")
    gp.add_argument("--account-id", required=True)
    gp.add_argument("--price-map")
    gp.set_defaults(func=cmd_get_portfolio)

    gpos = sub.add_parser("get-positions")
    gpos.add_argument("--account-id", required=True)
    gpos.set_defaults(func=cmd_get_positions)

    gc = sub.add_parser("get-cash")
    gc.add_argument("--account-id", required=True)
    gc.set_defaults(func=cmd_get_cash)

    gpe = sub.add_parser("get-pending-orders")
    gpe.add_argument("--account-id", required=True)
    gpe.set_defaults(func=cmd_get_pending)

    gh = sub.add_parser("get-order-history")
    gh.add_argument("--account-id", required=True)
    gh.add_argument("--start-date")
    gh.add_argument("--end-date")
    gh.set_defaults(func=cmd_get_history)

    gpnl = sub.add_parser("get-pnl")
    gpnl.add_argument("--account-id", required=True)
    gpnl.add_argument("--date")
    gpnl.add_argument("--price-map")
    gpnl.set_defaults(func=cmd_get_pnl)

    aj = sub.add_parser("append-journal")
    aj.add_argument("--account-id", required=True)
    aj.add_argument("--date", required=True)
    aj.add_argument("--markdown", required=True)
    aj.set_defaults(func=cmd_append_journal)

    rj = sub.add_parser("read-journal")
    rj.add_argument("--account-id", required=True)
    rj.add_argument("--date", required=True)
    rj.set_defaults(func=cmd_read_journal)

    idd = sub.add_parser("init-discussion")
    idd.add_argument("--date", required=True)
    idd.add_argument("--pnl-summary", help="JSON dict")
    idd.add_argument("--force", action="store_true")
    idd.set_defaults(func=cmd_init_discussion)

    rd = sub.add_parser("read-discussion")
    rd.add_argument("--date", required=True)
    rd.set_defaults(func=cmd_read_discussion)

    ad = sub.add_parser("append-discussion")
    ad.add_argument("--date", required=True)
    ad.add_argument("--speaker", required=True,
                    choices=["aggressive", "neutral", "conservative"])
    ad.add_argument("--markdown", required=True)
    ad.add_argument("--next-speaker", required=True,
                    choices=["aggressive", "neutral", "conservative", "end"])
    ad.add_argument("--reason", default="")
    ad.set_defaults(func=cmd_append_discussion)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
