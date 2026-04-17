import pytest
from python.accounts import ensure_account, get_cash, adjust_cash, INITIAL_CNY, INITIAL_HKD, INITIAL_USD


def test_ensure_account_creates_with_initial_capital(conn):
    ensure_account(conn, "aggressive")
    cash = get_cash(conn, "aggressive")
    assert cash == {"CNY": INITIAL_CNY, "HKD": INITIAL_HKD, "USD": INITIAL_USD}


def test_ensure_account_is_idempotent(conn):
    ensure_account(conn, "neutral")
    ensure_account(conn, "neutral")  # must not reset cash
    adjust_cash(conn, "neutral", "CNY", -1000)
    ensure_account(conn, "neutral")
    assert get_cash(conn, "neutral")["CNY"] == INITIAL_CNY - 1000


def test_adjust_cash_debit(conn):
    ensure_account(conn, "conservative")
    adjust_cash(conn, "conservative", "USD", -500)
    assert get_cash(conn, "conservative")["USD"] == INITIAL_USD - 500


def test_adjust_cash_credit(conn):
    ensure_account(conn, "aggressive")
    adjust_cash(conn, "aggressive", "HKD", 1000)
    assert get_cash(conn, "aggressive")["HKD"] == INITIAL_HKD + 1000


def test_adjust_cash_invalid_currency(conn):
    ensure_account(conn, "aggressive")
    with pytest.raises(ValueError):
        adjust_cash(conn, "aggressive", "JPY", 100)


def test_get_cash_missing_account_auto_creates(conn):
    cash = get_cash(conn, "aggressive")
    assert cash["CNY"] == INITIAL_CNY
