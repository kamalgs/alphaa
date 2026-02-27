"""Caching decorator for data providers."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from alphaa.core.types import DateRange

if TYPE_CHECKING:
    from alphaa.core.protocols import DataProvider


class CachingProvider:
    """Wraps any DataProvider with local CSV file caching.

    Satisfies the DataProvider protocol.
    """

    def __init__(
        self,
        inner: DataProvider,
        cache_dir: str = "~/.alphaa/cache",
    ) -> None:
        self._inner = inner
        self._cache_dir = Path(cache_dir).expanduser()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, symbol: str, date_range: DateRange) -> Path:
        key = f"{symbol}_{date_range.start}_{date_range.end}.csv"
        return self._cache_dir / key

    def fetch_ohlcv(self, symbol: str, date_range: DateRange) -> pd.DataFrame:
        path = self._cache_path(symbol, date_range)

        if path.exists():
            return pd.read_csv(path, index_col=0, parse_dates=True)

        df = self._inner.fetch_ohlcv(symbol, date_range)
        df.to_csv(path)
        return df

    def fetch_symbols(self, index: str | None = None) -> list[str]:
        return self._inner.fetch_symbols(index)
