"""Tests for price indicators."""

from __future__ import annotations

import pandas as pd
import pytest

from alphaa.indicators.price import rolling_high, rolling_low, sma


def _make_df(closes: list[float]) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=len(closes))
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [1000] * len(closes),
        },
        index=dates,
    )


class TestSma:
    def test_known_values(self) -> None:
        df = _make_df([10.0, 20.0, 30.0, 40.0, 50.0])
        result = sma(3)(df)
        # SMA(3) of [10,20,30,40,50] = [NaN, NaN, 20, 30, 40]
        assert result.iloc[2] == pytest.approx(20.0)
        assert result.iloc[3] == pytest.approx(30.0)
        assert result.iloc[4] == pytest.approx(40.0)

    def test_nan_for_insufficient_data(self) -> None:
        df = _make_df([10.0, 20.0, 30.0])
        result = sma(3)(df)
        assert pd.isna(result.iloc[0])
        assert pd.isna(result.iloc[1])

    def test_name(self) -> None:
        ind = sma(50)
        assert ind.__name__ == "sma_50"


class TestRollingHigh:
    def test_known_values(self) -> None:
        df = _make_df([10.0, 20.0, 15.0, 25.0, 5.0])
        result = rolling_high(3)(df)
        # Rolling max of high over 3: [NaN, NaN, 20, 25, 25]
        assert result.iloc[2] == pytest.approx(20.0)
        assert result.iloc[3] == pytest.approx(25.0)
        assert result.iloc[4] == pytest.approx(25.0)

    def test_name(self) -> None:
        assert rolling_high(252).__name__ == "high_252"


class TestRollingLow:
    def test_known_values(self) -> None:
        df = _make_df([30.0, 10.0, 20.0, 5.0, 15.0])
        result = rolling_low(3)(df)
        # Rolling min of low over 3: [NaN, NaN, 10, 5, 5]
        assert result.iloc[2] == pytest.approx(10.0)
        assert result.iloc[3] == pytest.approx(5.0)
        assert result.iloc[4] == pytest.approx(5.0)

    def test_name(self) -> None:
        assert rolling_low(252).__name__ == "low_252"
