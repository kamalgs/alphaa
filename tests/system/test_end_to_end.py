"""System test — full pipeline with fixture data.

Uses the recorded RELIANCE.NS CSV fixture, not the Yahoo API.
Tests the entire composition: provider -> indicators -> strategy -> engine -> reporting.
"""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import pandas as pd

from alphaa.broker.paper import PaperBroker
from alphaa.conditions.position import has_no_position, has_position, stop_loss
from alphaa.conditions.price import price_near_52w_high, price_near_52w_low
from alphaa.core.strategy import Strategy
from alphaa.core.types import BacktestConfig, DateRange
from alphaa.engine.backtest import BacktestEngine
from alphaa.engine.cost_models import ZeroCostModel
from alphaa.indicators.price import rolling_high, rolling_low
from alphaa.reporting.charts import plot_equity_curve, plot_trades_on_price
from alphaa.reporting.csv_export import export_trade_log
from alphaa.reporting.metrics import compute_metrics

FIXTURE_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "RELIANCE_NS_2019_2024.csv"


class FixtureProvider:
    """DataProvider that reads from a pre-recorded CSV file."""

    def __init__(self, csv_path: Path) -> None:
        self._df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

    def fetch_ohlcv(self, symbol: str, date_range: DateRange) -> pd.DataFrame:
        return self._df

    def fetch_symbols(self, index: str | None = None) -> list[str]:
        return []


class TestEndToEnd:
    def test_full_pipeline_produces_results(self) -> None:
        provider = FixtureProvider(FIXTURE_PATH)

        strategy = Strategy(
            name="buy-low-sell-high",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=(price_near_52w_high(within_pct=5) | stop_loss(pct=10)) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="RELIANCE.NS",
            date_range=DateRange(date(2019, 1, 1), date(2024, 1, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        result = BacktestEngine().run(config)

        # Result structure is valid
        assert result.strategy_name == "buy-low-sell-high"
        assert result.symbol == "RELIANCE.NS"
        assert len(result.equity_curve) > 0
        assert len(result.benchmark_curve) > 0

        # Has trades (RELIANCE.NS has enough price movement)
        assert len(result.trade_log) >= 1

    def test_metrics_are_reasonable(self) -> None:
        provider = FixtureProvider(FIXTURE_PATH)

        strategy = Strategy(
            name="buy-low-sell-high",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=(price_near_52w_high(within_pct=5) | stop_loss(pct=10)) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="RELIANCE.NS",
            date_range=DateRange(date(2019, 1, 1), date(2024, 1, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        result = BacktestEngine().run(config)
        metrics = compute_metrics(result)

        # Metrics are not NaN or inf (except profit_factor which can be inf)
        assert not math.isnan(metrics.total_return_pct)
        assert not math.isnan(metrics.cagr_pct)
        assert not math.isnan(metrics.max_drawdown_pct)
        assert not math.isnan(metrics.sharpe_ratio)
        assert not math.isnan(metrics.win_rate_pct)
        assert not math.isinf(metrics.total_return_pct)
        assert not math.isinf(metrics.cagr_pct)

        # Sanity ranges
        assert -100 <= metrics.total_return_pct <= 10000
        assert 0 <= metrics.max_drawdown_pct <= 100
        assert 0 <= metrics.win_rate_pct <= 100

    def test_csv_export_works(self, tmp_path: Path) -> None:
        provider = FixtureProvider(FIXTURE_PATH)

        strategy = Strategy(
            name="buy-low-sell-high",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=(price_near_52w_high(within_pct=5) | stop_loss(pct=10)) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="RELIANCE.NS",
            date_range=DateRange(date(2019, 1, 1), date(2024, 1, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        result = BacktestEngine().run(config)

        csv_path = tmp_path / "trades.csv"
        export_trade_log(result.trade_log, csv_path)
        assert csv_path.exists()
        assert csv_path.stat().st_size > 0

    def test_charts_are_generated(self, tmp_path: Path) -> None:
        provider = FixtureProvider(FIXTURE_PATH)

        strategy = Strategy(
            name="buy-low-sell-high",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=(price_near_52w_high(within_pct=5) | stop_loss(pct=10)) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="RELIANCE.NS",
            date_range=DateRange(date(2019, 1, 1), date(2024, 1, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        result = BacktestEngine().run(config)
        ohlcv = provider.fetch_ohlcv("RELIANCE.NS", config.date_range)

        equity_path = tmp_path / "equity.png"
        plot_equity_curve(result, output_path=equity_path)
        assert equity_path.exists()
        assert equity_path.stat().st_size > 0

        trades_path = tmp_path / "trades.png"
        plot_trades_on_price(result, ohlcv, output_path=trades_path)
        assert trades_path.exists()
        assert trades_path.stat().st_size > 0
