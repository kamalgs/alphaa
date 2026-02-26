"""Shared test fixtures and helpers."""

from __future__ import annotations

from datetime import date

import pandas as pd

from alphaa.core.types import Bar, Context, Fill, PortfolioState, Position, Side


def make_bar(
    symbol: str = "TEST.NS",
    bar_date: date | None = None,
    open: float = 100.0,
    high: float = 105.0,
    low: float = 95.0,
    close: float = 100.0,
    volume: int = 1000,
    adj_close: float | None = None,
) -> Bar:
    """Create a Bar with sensible defaults."""
    return Bar(
        symbol=symbol,
        date=bar_date or date(2024, 1, 1),
        open=open,
        high=high,
        low=low,
        close=close,
        volume=volume,
        adj_close=adj_close,
    )


def make_context(
    close: float = 100.0,
    indicators: dict[str, pd.Series] | None = None,
    positions: dict[str, Position] | None = None,
    cash: float = 100_000.0,
    symbol: str = "TEST.NS",
    bar_date: date | None = None,
    params: dict[str, object] | None = None,
) -> Context:
    """Create a Context with sensible defaults for testing conditions."""
    bar_date = bar_date or date(2024, 1, 1)
    bar = make_bar(symbol=symbol, bar_date=bar_date, close=close)

    history = pd.DataFrame(
        {"open": [close], "high": [close], "low": [close], "close": [close], "volume": [1000]},
        index=pd.DatetimeIndex([bar_date]),
    )

    portfolio = PortfolioState(
        cash=cash,
        positions=positions or {},
    )

    return Context(
        current_bar=bar,
        history=history,
        portfolio=portfolio,
        indicators=indicators or {},
        params=params or {},
    )


def make_ohlcv_df(
    prices: list[float],
    start_date: date | None = None,
) -> pd.DataFrame:
    """Build a proper OHLCV DataFrame from a list of close prices.

    For simplicity, open=high=low=close and volume=1000.
    """
    start = start_date or date(2024, 1, 1)
    dates = pd.bdate_range(start=start, periods=len(prices))
    return pd.DataFrame(
        {
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices,
            "volume": [1000] * len(prices),
        },
        index=dates,
    )


def make_position(
    symbol: str = "TEST.NS",
    quantity: int = 10,
    avg_cost: float = 100.0,
) -> Position:
    """Create a Position with sensible defaults."""
    entry_fill = Fill(
        symbol=symbol,
        side=Side.BUY,
        quantity=quantity,
        price=avg_cost,
        date=date(2024, 1, 1),
    )
    return Position(
        symbol=symbol,
        quantity=quantity,
        avg_cost=avg_cost,
        lots=[entry_fill],
    )
