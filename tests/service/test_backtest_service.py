"""Tests for the backtest service layer."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from alphaa.core.types import DateRange
from alphaa.service.backtest_service import BacktestRequest, BacktestResponse, run_backtest

FIXTURE_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "RELIANCE_NS_2019_2024.csv"


class FixtureProvider:
    """DataProvider that reads from a pre-recorded CSV file."""

    def __init__(self, csv_path: Path) -> None:
        self._df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

    def fetch_ohlcv(self, symbol: str, date_range: DateRange) -> pd.DataFrame:
        return self._df

    def fetch_symbols(self, index: str | None = None) -> list[str]:
        return []


class TestRunBacktest:
    def test_returns_valid_response(self) -> None:
        request = BacktestRequest(
            symbol="RELIANCE.NS",
            start_date=date(2019, 1, 1),
            end_date=date(2024, 1, 1),
        )
        provider = FixtureProvider(FIXTURE_PATH)

        response = run_backtest(request, data_provider=provider)

        assert isinstance(response, BacktestResponse)
        assert response.result.strategy_name == "buy-low-sell-high"
        assert response.result.symbol == "RELIANCE.NS"
        assert len(response.result.trade_log) >= 1
        assert len(response.result.equity_curve) > 0

    def test_metrics_are_populated(self) -> None:
        request = BacktestRequest(
            symbol="RELIANCE.NS",
            start_date=date(2019, 1, 1),
            end_date=date(2024, 1, 1),
        )
        provider = FixtureProvider(FIXTURE_PATH)

        response = run_backtest(request, data_provider=provider)

        assert response.metrics.total_trades >= 1
        assert -100 <= response.metrics.total_return_pct <= 10000
        assert 0 <= response.metrics.win_rate_pct <= 100

    def test_custom_parameters(self) -> None:
        request = BacktestRequest(
            symbol="RELIANCE.NS",
            start_date=date(2019, 1, 1),
            end_date=date(2024, 1, 1),
            capital=200_000.0,
            entry_pct=3.0,
            exit_pct=3.0,
            stop_loss_pct=15.0,
        )
        provider = FixtureProvider(FIXTURE_PATH)

        response = run_backtest(request, data_provider=provider)

        assert response.result.starting_capital == 200_000.0
