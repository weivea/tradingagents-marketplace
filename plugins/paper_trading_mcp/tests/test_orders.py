import pytest
from python.accounts import ensure_account, get_cash, INITIAL_CNY, INITIAL_USD
from python.orders import place_order, cancel_order


def test_market_buy_us_fills_immediately(conn):
    ensure_account(conn, "aggressive")
    res = place_order(
        conn,
        account_id="aggressive",
        symbol="AAPL",
        market="US",
        side="buy",
        qty=100,
        order_type="market",
        ref_price=150.0,
    )
    assert res["ok"] is True
    assert res["status"] == "filled"
    assert res["filled_price"] == 150.0
    assert res["filled_qty"] == 100
    # Cash debited: 100*150 + $1 min fee = 15001
    assert get_cash(conn, "aggressive")["USD"] == pytest.approx(INITIAL_USD - 15001.0)


def test_market_buy_cn_sets_settle_date(conn):
    ensure_account(conn, "aggressive")
    res = place_order(
        conn,
        account_id="aggressive",
        symbol="600519",
        market="CN",
        side="buy",
        qty=100,
        order_type="market",
        ref_price=1800.0,
    )
    assert res["ok"] is True
    assert res["settle_date"] is not None
    assert res["settle_date"] != res["submitted_at"][:10]


def test_market_buy_insufficient_cash(conn):
    ensure_account(conn, "conservative")
    res = place_order(
        conn,
        account_id="conservative",
        symbol="AAPL",
        market="US",
        side="buy",
        qty=10000,
        order_type="market",
        ref_price=500.0,
    )
    assert res["ok"] is False
    assert res["error_code"] == "INSUFFICIENT_CASH"


def test_market_buy_requires_ref_price(conn):
    ensure_account(conn, "aggressive")
    res = place_order(
        conn,
        account_id="aggressive",
        symbol="AAPL",
        market="US",
        side="buy",
        qty=10,
        order_type="market",
        ref_price=None,
    )
    assert res["ok"] is False
    assert res["error_code"] == "MISSING_REF_PRICE"


def test_market_sell_without_position(conn):
    ensure_account(conn, "aggressive")
    res = place_order(
        conn,
        account_id="aggressive",
        symbol="AAPL",
        market="US",
        side="sell",
        qty=100,
        order_type="market",
        ref_price=150.0,
    )
    assert res["ok"] is False
    assert res["error_code"] == "INSUFFICIENT_POSITION"


def test_market_sell_us_after_buy(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=100, order_type="market", ref_price=150.0)
    res = place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                     side="sell", qty=100, order_type="market", ref_price=160.0)
    assert res["ok"] is True
    assert res["status"] == "filled"


def test_limit_buy_stays_pending(conn):
    ensure_account(conn, "neutral")
    res = place_order(
        conn,
        account_id="neutral",
        symbol="AAPL",
        market="US",
        side="buy",
        qty=10,
        order_type="limit",
        price=140.0,
        ref_price=150.0,
    )
    assert res["ok"] is True
    assert res["status"] == "pending"


def test_cancel_pending_order(conn):
    ensure_account(conn, "neutral")
    res = place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                     side="buy", qty=10, order_type="limit",
                     price=140.0, ref_price=150.0)
    order_id = res["order_id"]
    cancel_res = cancel_order(conn, account_id="neutral", order_id=order_id)
    assert cancel_res["ok"] is True
    assert cancel_res["status"] == "cancelled"


def test_cancel_nonexistent_order(conn):
    ensure_account(conn, "neutral")
    res = cancel_order(conn, account_id="neutral", order_id=99999)
    assert res["ok"] is False
    assert res["error_code"] == "ORDER_NOT_FOUND"


def test_cancel_already_filled_order(conn):
    ensure_account(conn, "aggressive")
    res = place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                     side="buy", qty=10, order_type="market", ref_price=150.0)
    cancel_res = cancel_order(conn, account_id="aggressive", order_id=res["order_id"])
    assert cancel_res["ok"] is False
    assert cancel_res["error_code"] == "ORDER_NOT_CANCELLABLE"
