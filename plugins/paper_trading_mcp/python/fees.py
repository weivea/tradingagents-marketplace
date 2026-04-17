"""Market-specific fee rules for paper trading.

All fees returned in the market's native currency.
"""
from __future__ import annotations


def calc_fee(*, market: str, side: str, qty: float, price: float) -> float:
    notional = qty * price
    if market == "CN":
        commission = max(notional * 0.00025, 5.0)
        stamp = notional * 0.0005 if side == "sell" else 0.0
        return commission + stamp
    if market == "HK":
        commission = max(notional * 0.0008, 5.0)
        stamp = notional * 0.001  # both sides
        return commission + stamp
    if market == "US":
        per_share = qty * 0.005
        return max(per_share, 1.0)
    raise ValueError(f"Unknown market: {market}")


CURRENCY_BY_MARKET = {"CN": "CNY", "HK": "HKD", "US": "USD"}
