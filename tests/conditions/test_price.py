"""Tests for price conditions."""

from __future__ import annotations

import pandas as pd

from alphaa.conditions.price import price_near_52w_high, price_near_52w_low
from tests.conftest import make_context


class TestPriceNear52wLow:
    def test_at_low(self) -> None:
        ctx = make_context(
            close=100.0,
            indicators={"low_252": pd.Series([100.0])},
        )
        assert price_near_52w_low(within_pct=5.0)(ctx) is True

    def test_within_range(self) -> None:
        ctx = make_context(
            close=104.0,
            indicators={"low_252": pd.Series([100.0])},
        )
        # 104 <= 100 * 1.05 = 105 → True
        assert price_near_52w_low(within_pct=5.0)(ctx) is True

    def test_above_range(self) -> None:
        ctx = make_context(
            close=110.0,
            indicators={"low_252": pd.Series([100.0])},
        )
        # 110 <= 100 * 1.05 = 105 → False
        assert price_near_52w_low(within_pct=5.0)(ctx) is False


class TestPriceNear52wHigh:
    def test_at_high(self) -> None:
        ctx = make_context(
            close=200.0,
            indicators={"high_252": pd.Series([200.0])},
        )
        assert price_near_52w_high(within_pct=5.0)(ctx) is True

    def test_within_range(self) -> None:
        ctx = make_context(
            close=192.0,
            indicators={"high_252": pd.Series([200.0])},
        )
        # 192 >= 200 * 0.95 = 190 → True
        assert price_near_52w_high(within_pct=5.0)(ctx) is True

    def test_below_range(self) -> None:
        ctx = make_context(
            close=180.0,
            indicators={"high_252": pd.Series([200.0])},
        )
        # 180 >= 200 * 0.95 = 190 → False
        assert price_near_52w_high(within_pct=5.0)(ctx) is False
