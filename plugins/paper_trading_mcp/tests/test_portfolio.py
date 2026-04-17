import pytest
from python.accounts import ensure_account, INITIAL_USD
from python.orders import place_order
from python.portfolio import (
    get_positions, get_portfolio, get_pending_orders,
    get_order_history, get_pnl,
)


def test_positions_empty_for_new_account(conn):
    ensure_account(conn, "neutral")
    assert get_positions(conn, "neutral") == []


def test_positions_after_buy(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    pos = get_positions(conn, "aggressive")
    assert len(pos) == 1
    assert pos[0]["symbol"] == "AAPL"
    assert pos[0]["qty"] == 100
    assert pos[0]["avg_cost"] == 150.0


def test_portfolio_with_price_map(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    pf = get_portfolio(conn, "aggressive", price_map={"AAPL": 160.0})
    assert pf["cash"]["USD"] == pytest.approx(INITIAL_USD - 15001.0)
    assert len(pf["positions"]) == 1
    assert pf["positions"][0]["market_value"] == pytest.approx(16000.0)


def test_pending_orders(conn):
    ensure_account(conn, "neutral")
    place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                side="buy", qty=10, order_type="limit",
                price=140.0, ref_price=150.0)
    pending = get_pending_orders(conn, "neutral")
    assert len(pending) == 1
    assert pending[0]["order_type"] == "limit"


def test_order_history(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=10, order_type="market", ref_price=150.0)
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="sell", qty=10, order_type="market", ref_price=160.0)
    hist = get_order_history(conn, "aggressive")
    assert len(hist) == 2


def test_pnl_realized_after_round_trip(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="sell", qty=100, order_type="market", ref_price=160.0)
    pnl = get_pnl(conn, "aggressive")
    assert pnl["realized_usd"] == pytest.approx(998.0)


def test_pnl_unrealized_from_price_map(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    pnl = get_pnl(conn, "aggressive", price_map={"AAPL": 160.0})
    assert pnl["unrealized_usd"] == pytest.approx(1000.0)
