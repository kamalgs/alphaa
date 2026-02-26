"""Smoke tests for chart generation."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from alphaa.core.types import (
    BacktestResult,
    DateRange,
    Fill,
    PortfolioSnapshot,
    Side,
    Trade,
)
from alphaa.reporting.charts import plot_equity_curve, plot_trades_on_price


def _make_result_with_trades() -> BacktestResult:
    trade = Trade(
        symbol="TEST.NS",
        entry=Fill("TEST.NS", Side.BUY, 100, 100.0, date(2023, 3, 1)),
        exit=Fill("TEST.NS", Side.SELL, 100, 120.0, date(2023, 6, 1)),
    )
    equity = [
        PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
        PortfolioSnapshot(date(2023, 6, 1), 100_000.0, 2000.0, 102_000.0),
        PortfolioSnapshot(date(2024, 1, 1), 102_000.0, 0.0, 102_000.0),
    ]
    benchmark = [
        PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
        PortfolioSnapshot(date(2023, 6, 1), 105_000.0, 0.0, 105_000.0),
        PortfolioSnapshot(date(2024, 1, 1), 110_000.0, 0.0, 110_000.0),
    ]
    return BacktestResult(
        strategy_name="test",
        symbol="TEST.NS",
        date_range=DateRange(date(2023, 1, 1), date(2024, 1, 1)),
        starting_capital=100_000.0,
        trade_log=[trade],
        equity_curve=equity,
        benchmark_curve=benchmark,
    )


class TestPlotEquityCurve:
    def test_saves_file(self, tmp_path: Path) -> None:
        result = _make_result_with_trades()
        output = tmp_path / "equity.png"
        plot_equity_curve(result, output_path=output)

        assert output.exists()
        assert output.stat().st_size > 0


class TestPlotTradesOnPrice:
    def test_saves_file(self, tmp_path: Path) -> None:
        result = _make_result_with_trades()
        ohlcv = pd.DataFrame(
            {
                "open": [100.0, 110.0, 120.0],
                "high": [105.0, 115.0, 125.0],
                "low": [95.0, 105.0, 115.0],
                "close": [100.0, 110.0, 120.0],
                "volume": [1000, 1000, 1000],
            },
            index=pd.DatetimeIndex(
                [date(2023, 1, 1), date(2023, 6, 1), date(2024, 1, 1)]
            ),
        )
        output = tmp_path / "trades.png"
        plot_trades_on_price(result, ohlcv, output_path=output)

        assert output.exists()
        assert output.stat().st_size > 0
