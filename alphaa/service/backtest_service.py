"""Shared backtest composition logic.

Used by both the CLI and web layer to run a backtest end-to-end.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from alphaa.broker.paper import PaperBroker
from alphaa.core.strategy import Strategy
from alphaa.core.types import BacktestConfig, BacktestMetrics, BacktestResult, DateRange
from alphaa.data.cache import CachingProvider
from alphaa.data.yahoo import YahooFinanceProvider
from alphaa.engine.backtest import BacktestEngine
from alphaa.engine.cost_models import ZeroCostModel
from alphaa.reporting.metrics import compute_metrics
from alphaa.strategies.builtin import build_default_strategy

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
    strategy: Strategy | None = None,
) -> BacktestResponse:
    """Run a full backtest and return result + metrics.

    If *data_provider* is ``None``, a Yahoo Finance provider (optionally
    wrapped with caching) is created automatically.

    If *strategy* is ``None``, the default buy-low-sell-high strategy is used.
    """
    if data_provider is None:
        yahoo: DataProvider = YahooFinanceProvider()
        provider: DataProvider = (
            CachingProvider(yahoo) if request.use_cache else yahoo
        )
    else:
        provider = data_provider

    date_range = DateRange(request.start_date, request.end_date)

    if strategy is None:
        strategy = build_default_strategy(
            entry_pct=request.entry_pct,
            exit_pct=request.exit_pct,
            stop_loss_pct=request.stop_loss_pct,
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
