import pytest
from python.fees import calc_fee


def test_cn_buy_commission_only_min5():
    assert calc_fee(market="CN", side="buy", qty=100, price=10.0) == pytest.approx(5.0)


def test_cn_buy_commission_over_min():
    assert calc_fee(market="CN", side="buy", qty=10000, price=100.0) == pytest.approx(250.0)


def test_cn_sell_adds_stamp_duty():
    assert calc_fee(market="CN", side="sell", qty=10000, price=100.0) == pytest.approx(750.0)


def test_hk_buy_commission_and_stamp():
    assert calc_fee(market="HK", side="buy", qty=10000, price=100.0) == pytest.approx(1800.0)


def test_hk_sell_commission_and_stamp():
    assert calc_fee(market="HK", side="sell", qty=10000, price=100.0) == pytest.approx(1800.0)


def test_hk_min_commission():
    assert calc_fee(market="HK", side="buy", qty=10, price=10.0) == pytest.approx(5.1)


def test_us_per_share_min1():
    assert calc_fee(market="US", side="buy", qty=100, price=50.0) == pytest.approx(1.0)


def test_us_per_share_over_min():
    assert calc_fee(market="US", side="sell", qty=1000, price=50.0) == pytest.approx(5.0)


def test_unknown_market_raises():
    with pytest.raises(ValueError):
        calc_fee(market="JP", side="buy", qty=100, price=10.0)
