import datetime as dt
import pytest
from python.accounts import ensure_account
from python.orders import place_order
from python.settlement import tick_pending_orders


def test_cn_buy_locked_same_day(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="600519", market="CN",
                side="buy", qty=100, order_type="market", ref_price=1800.0)
    res = place_order(conn, account_id="aggressive", symbol="600519", market="CN",
                     side="sell", qty=100, order_type="market", ref_price=1810.0)
    assert res["ok"] is False
    assert res["error_code"] == "INSUFFICIENT_POSITION"


def test_tick_releases_t1_positions(conn):
    ensure_account(conn, "aggressive")
    buy_res = place_order(conn, account_id="aggressive", symbol="600519", market="CN",
                         side="buy", qty=100, order_type="market", ref_price=1800.0)
    conn.execute("UPDATE orders SET settle_date=? WHERE id=?",
                 ((dt.date.today() - dt.timedelta(days=1)).isoformat(), buy_res["order_id"]))
    conn.commit()
    tick_pending_orders(conn, account_id="aggressive", price_map={})
    res = place_order(conn, account_id="aggressive", symbol="600519", market="CN",
                     side="sell", qty=100, order_type="market", ref_price=1810.0)
    assert res["ok"] is True


def test_tick_triggers_limit_order(conn):
    ensure_account(conn, "neutral")
    lim_res = place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                         side="buy", qty=10, order_type="limit",
                         price=140.0, ref_price=150.0)
    assert lim_res["status"] == "pending"
    result = tick_pending_orders(conn, account_id="neutral",
                                price_map={"AAPL": 138.0})
    assert result["triggered"] == 1
    row = conn.execute("SELECT status, filled_price FROM orders WHERE id=?",
                       (lim_res["order_id"],)).fetchone()
    assert row["status"] == "filled"
    assert row["filled_price"] == 140.0


def test_tick_triggers_stop_sell(conn):
    ensure_account(conn, "aggressive")
    place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                side="buy", qty=10, order_type="market", ref_price=150.0)
    stop_res = place_order(conn, account_id="aggressive", symbol="AAPL", market="US",
                          side="sell", qty=10, order_type="stop",
                          price=145.0, ref_price=150.0)
    assert stop_res["status"] == "pending"
    result = tick_pending_orders(conn, account_id="aggressive",
                                price_map={"AAPL": 144.0})
    assert result["triggered"] == 1


def test_tick_leaves_untriggered_pending(conn):
    ensure_account(conn, "neutral")
    lim = place_order(conn, account_id="neutral", symbol="AAPL", market="US",
                     side="buy", qty=10, order_type="limit",
                     price=140.0, ref_price=150.0)
    result = tick_pending_orders(conn, account_id="neutral",
                                price_map={"AAPL": 145.0})
    assert result["triggered"] == 0
    row = conn.execute("SELECT status FROM orders WHERE id=?",
                       (lim["order_id"],)).fetchone()
    assert row["status"] == "pending"
