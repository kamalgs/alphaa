"""Shared backtest composition logic.

Used by both the CLI and web layer to run a backtest end-to-end.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from alphaa.broker.paper import PaperBroker
from alphaa.conditions.position import has_no_position, has_position, stop_loss
from alphaa.conditions.price import price_near_52w_high, price_near_52w_low
from alphaa.core.strategy import Strategy
from alphaa.core.types import BacktestConfig, BacktestMetrics, BacktestResult, DateRange
from alphaa.data.cache import CachingProvider
from alphaa.data.yahoo import YahooFinanceProvider
from alphaa.engine.backtest import BacktestEngine
from alphaa.engine.cost_models import ZeroCostModel
from alphaa.indicators.price import rolling_high, rolling_low
from alphaa.reporting.metrics import compute_metrics

if TYPE_CHECKING:
    from alphaa.core.protocols import DataProvider


@dataclass(frozen=True)
class BacktestRequest:
    """Parameters for a backtest run."""

    symbol: str
    start_date: date
    end_date: date
    capital: float = 100_000.0
    entry_pct: float = 5.0
    exit_pct: float = 5.0
    stop_loss_pct: float = 10.0
    use_cache: bool = True


@dataclass(frozen=True)
class BacktestResponse:
    """Result of a backtest run."""

    result: BacktestResult
    metrics: BacktestMetrics
    ohlcv: pd.DataFrame


def run_backtest(
    request: BacktestRequest,
    data_provider: DataProvider | None = None,
) -> BacktestResponse:
    """Run a full backtest and return result + metrics.

    If *data_provider* is ``None``, a Yahoo Finance provider (optionally
    wrapped with caching) is created automatically.
    """
    if data_provider is None:
        yahoo: DataProvider = YahooFinanceProvider()
        provider: DataProvider = (
            CachingProvider(yahoo) if request.use_cache else yahoo
        )
    else:
        provider = data_provider

    date_range = DateRange(request.start_date, request.end_date)

    strategy = Strategy(
        name="buy-low-sell-high",
        entry=price_near_52w_low(within_pct=request.entry_pct) & has_no_position(),
        exit=(
            price_near_52w_high(within_pct=request.exit_pct)
            | stop_loss(pct=request.stop_loss_pct)
        )
        & has_position(),
        indicators=[rolling_high(252), rolling_low(252)],
    )

    config = BacktestConfig(
        strategy=strategy,
        symbol=request.symbol,
        date_range=date_range,
        starting_capital=request.capital,
        data_provider=provider,
        broker=PaperBroker(),
        cost_model=ZeroCostModel(),
    )

    engine = BacktestEngine()
    result = engine.run(config)
    metrics = compute_metrics(result)
    ohlcv = provider.fetch_ohlcv(request.symbol, date_range)

    return BacktestResponse(result=result, metrics=metrics, ohlcv=ohlcv)
