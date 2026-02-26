"""Tests for backtest metrics computation."""

from __future__ import annotations

from datetime import date

import pytest

from alphaa.core.types import (
    BacktestResult,
    DateRange,
    Fill,
    PortfolioSnapshot,
    Side,
    Trade,
)
from alphaa.reporting.metrics import compute_metrics


def _make_result(
    trades: list[Trade] | None = None,
    equity: list[PortfolioSnapshot] | None = None,
    benchmark: list[PortfolioSnapshot] | None = None,
    starting_capital: float = 100_000.0,
    start: date = date(2023, 1, 1),
    end: date = date(2024, 1, 1),
) -> BacktestResult:
    return BacktestResult(
        strategy_name="test",
        symbol="TEST.NS",
        date_range=DateRange(start, end),
        starting_capital=starting_capital,
        trade_log=trades or [],
        equity_curve=equity or [],
        benchmark_curve=benchmark or [],
    )


def _make_trade(
    entry_price: float,
    exit_price: float,
    quantity: int = 100,
    entry_date: date = date(2023, 3, 1),
    exit_date: date = date(2023, 6, 1),
) -> Trade:
    return Trade(
        symbol="TEST.NS",
        entry=Fill("TEST.NS", Side.BUY, quantity, entry_price, entry_date),
        exit=Fill("TEST.NS", Side.SELL, quantity, exit_price, exit_date),
    )


class TestComputeMetrics:
    def test_zero_trades(self) -> None:
        equity = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2024, 1, 1), 100_000.0, 0.0, 100_000.0),
        ]
        result = _make_result(equity=equity)
        metrics = compute_metrics(result)

        assert metrics.total_trades == 0
        assert metrics.total_return_pct == pytest.approx(0.0)
        assert metrics.win_rate_pct == 0.0
        assert metrics.avg_holding_days == 0.0
        assert metrics.profit_factor == 0.0

    def test_single_winning_trade(self) -> None:
        trade = _make_trade(100.0, 120.0, quantity=100)
        equity = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2024, 1, 1), 102_000.0, 0.0, 102_000.0),
        ]
        result = _make_result(trades=[trade], equity=equity)
        metrics = compute_metrics(result)

        assert metrics.total_trades == 1
        assert metrics.win_rate_pct == 100.0
        assert metrics.total_return_pct == pytest.approx(2.0)
        assert metrics.avg_holding_days == 92  # Mar 1 to Jun 1

    def test_single_losing_trade(self) -> None:
        trade = _make_trade(100.0, 80.0, quantity=100)
        equity = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2024, 1, 1), 98_000.0, 0.0, 98_000.0),
        ]
        result = _make_result(trades=[trade], equity=equity)
        metrics = compute_metrics(result)

        assert metrics.win_rate_pct == 0.0
        assert metrics.total_return_pct == pytest.approx(-2.0)

    def test_mixed_trades(self) -> None:
        trades = [
            _make_trade(100.0, 120.0, quantity=100),  # +2000
            _make_trade(100.0, 90.0, quantity=100),   # -1000
        ]
        equity = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2024, 1, 1), 101_000.0, 0.0, 101_000.0),
        ]
        result = _make_result(trades=trades, equity=equity)
        metrics = compute_metrics(result)

        assert metrics.total_trades == 2
        assert metrics.win_rate_pct == pytest.approx(50.0)
        assert metrics.profit_factor == pytest.approx(2.0)  # 2000/1000

    def test_max_drawdown(self) -> None:
        equity = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2023, 4, 1), 120_000.0, 0.0, 120_000.0),  # peak
            PortfolioSnapshot(date(2023, 7, 1), 96_000.0, 0.0, 96_000.0),   # trough
            PortfolioSnapshot(date(2024, 1, 1), 110_000.0, 0.0, 110_000.0),
        ]
        result = _make_result(equity=equity)
        metrics = compute_metrics(result)

        # Drawdown from 120k to 96k = 20%
        assert metrics.max_drawdown_pct == pytest.approx(20.0)

    def test_benchmark_return(self) -> None:
        equity = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2024, 1, 1), 110_000.0, 0.0, 110_000.0),
        ]
        benchmark = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2024, 1, 1), 115_000.0, 0.0, 115_000.0),
        ]
        result = _make_result(equity=equity, benchmark=benchmark)
        metrics = compute_metrics(result)

        assert metrics.benchmark_return_pct == pytest.approx(15.0)

    def test_all_wins_profit_factor(self) -> None:
        trades = [
            _make_trade(100.0, 110.0),
            _make_trade(100.0, 120.0),
        ]
        equity = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2024, 1, 1), 103_000.0, 0.0, 103_000.0),
        ]
        result = _make_result(trades=trades, equity=equity)
        metrics = compute_metrics(result)

        assert metrics.profit_factor == float("inf")

    def test_cagr(self) -> None:
        equity = [
            PortfolioSnapshot(date(2023, 1, 1), 100_000.0, 0.0, 100_000.0),
            PortfolioSnapshot(date(2025, 1, 1), 121_000.0, 0.0, 121_000.0),
        ]
        result = _make_result(
            equity=equity,
            start=date(2023, 1, 1),
            end=date(2025, 1, 1),
        )
        metrics = compute_metrics(result)

        # 21% over 2 years → CAGR ≈ 10%
        assert metrics.cagr_pct == pytest.approx(10.0, abs=0.5)
