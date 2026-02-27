"""Yahoo Finance data provider."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from alphaa.core.types import DateRange


class YahooFinanceProvider:
    """Fetches OHLCV data from Yahoo Finance.

    Satisfies the DataProvider protocol.
    """

    def __init__(self, exchange_suffix: str = ".NS") -> None:
        self._suffix = exchange_suffix

    def _resolve_symbol(self, symbol: str) -> str:
        if "." in symbol:
            return symbol
        return f"{symbol}{self._suffix}"

    def fetch_ohlcv(self, symbol: str, date_range: DateRange) -> pd.DataFrame:
        ticker = self._resolve_symbol(symbol)
        df: pd.DataFrame = yf.download(
            ticker,
            start=str(date_range.start),
            end=str(date_range.end),
            progress=False,
            auto_adjust=True,
        )

        # Flatten MultiIndex columns if present (yfinance >= 0.2.31)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Normalize column names to lowercase
        df.columns = [c.lower() for c in df.columns]

        # Ensure expected columns exist
        expected = {"open", "high", "low", "close", "volume"}
        missing = expected - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns from Yahoo Finance: {missing}")

        return df[["open", "high", "low", "close", "volume"]]

    def fetch_symbols(self, index: str | None = None) -> list[str]:
        return []
