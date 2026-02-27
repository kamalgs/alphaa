"""Tests for CachingProvider."""

from __future__ import annotations

from datetime import date

import pandas as pd

from alphaa.core.types import DateRange
from alphaa.data.cache import CachingProvider


class FakeProvider:
    """A trivial provider for testing — no mocks needed."""

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df
        self.call_count = 0

    def fetch_ohlcv(self, symbol: str, date_range: DateRange) -> pd.DataFrame:
        self.call_count += 1
        return self._df

    def fetch_symbols(self, index: str | None = None) -> list[str]:
        return ["TEST.NS"]


class TestCachingProvider:
    def test_cache_miss_calls_inner(self, tmp_path: object) -> None:
        df = pd.DataFrame(
            {"open": [100.0], "high": [105.0], "low": [95.0], "close": [102.0], "volume": [1000]},
            index=pd.DatetimeIndex([date(2024, 1, 1)]),
        )
        inner = FakeProvider(df)
        cache = CachingProvider(inner, cache_dir=str(tmp_path))

        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 2))
        result = cache.fetch_ohlcv("TEST.NS", date_range)

        assert inner.call_count == 1
        assert result.iloc[0]["close"] == 102.0

    def test_cache_hit_avoids_inner(self, tmp_path: object) -> None:
        df = pd.DataFrame(
            {"open": [100.0], "high": [105.0], "low": [95.0], "close": [102.0], "volume": [1000]},
            index=pd.DatetimeIndex([date(2024, 1, 1)]),
        )
        inner = FakeProvider(df)
        cache = CachingProvider(inner, cache_dir=str(tmp_path))

        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 2))

        # First call — cache miss
        cache.fetch_ohlcv("TEST.NS", date_range)
        assert inner.call_count == 1

        # Second call — cache hit
        result = cache.fetch_ohlcv("TEST.NS", date_range)
        assert inner.call_count == 1  # NOT called again
        assert result.iloc[0]["close"] == 102.0

    def test_cache_writes_parquet_file(self, tmp_path: object) -> None:
        df = pd.DataFrame(
            {"open": [100.0], "high": [105.0], "low": [95.0], "close": [102.0], "volume": [1000]},
            index=pd.DatetimeIndex([date(2024, 1, 1)]),
        )
        inner = FakeProvider(df)
        cache = CachingProvider(inner, cache_dir=str(tmp_path))

        date_range = DateRange(date(2024, 1, 1), date(2024, 1, 2))
        cache.fetch_ohlcv("TEST.NS", date_range)

        from pathlib import Path

        files = list(Path(str(tmp_path)).glob("*.csv"))
        assert len(files) == 1

    def test_fetch_symbols_delegates(self, tmp_path: object) -> None:
        inner = FakeProvider(pd.DataFrame())
        cache = CachingProvider(inner, cache_dir=str(tmp_path))
        assert cache.fetch_symbols() == ["TEST.NS"]
