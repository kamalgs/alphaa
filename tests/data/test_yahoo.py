"""Tests for YahooFinanceProvider."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest

from alphaa.core.types import DateRange
from alphaa.data.yahoo import YahooFinanceProvider


class TestYahooFinanceProvider:
    def test_resolve_symbol_adds_suffix(self) -> None:
        provider = YahooFinanceProvider(exchange_suffix=".NS")
        assert provider._resolve_symbol("RELIANCE") == "RELIANCE.NS"

    def test_resolve_symbol_preserves_explicit_suffix(self) -> None:
        provider = YahooFinanceProvider(exchange_suffix=".NS")
        assert provider._resolve_symbol("RELIANCE.NS") == "RELIANCE.NS"

    def test_fetch_ohlcv_normalizes_columns(self) -> None:
        mock_df = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [95.0],
                "Close": [102.0],
                "Volume": [1000],
            },
            index=pd.DatetimeIndex([date(2024, 1, 1)]),
        )

        provider = YahooFinanceProvider()
        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 2))

        with patch("alphaa.data.yahoo.yf.download", return_value=mock_df):
            df = provider.fetch_ohlcv("RELIANCE", date_range)

        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.iloc[0]["close"] == 102.0

    def test_fetch_ohlcv_handles_multiindex_columns(self) -> None:
        """yfinance >= 0.2.31 returns MultiIndex columns."""
        arrays = [
            ["Open", "High", "Low", "Close", "Volume"],
            ["RELIANCE.NS"] * 5,
        ]
        tuples = list(zip(*arrays))
        index = pd.MultiIndex.from_tuples(tuples)
        mock_df = pd.DataFrame(
            [[100.0, 105.0, 95.0, 102.0, 1000]],
            columns=index,
            index=pd.DatetimeIndex([date(2024, 1, 1)]),
        )

        provider = YahooFinanceProvider()
        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 2))

        with patch("alphaa.data.yahoo.yf.download", return_value=mock_df):
            df = provider.fetch_ohlcv("RELIANCE", date_range)

        assert list(df.columns) == ["open", "high", "low", "close", "volume"]

    def test_fetch_symbols_returns_empty(self) -> None:
        provider = YahooFinanceProvider()
        assert provider.fetch_symbols() == []

    @pytest.mark.slow
    def test_fetch_real_data(self) -> None:
        """Integration test that hits the real Yahoo Finance API."""
        provider = YahooFinanceProvider()
        date_range = DateRange(date(2024, 1, 1), date(2024, 2, 1))
        df = provider.fetch_ohlcv("RELIANCE.NS", date_range)

        assert len(df) > 0
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
