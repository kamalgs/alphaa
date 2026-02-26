"""Integration test — the tracer bullet.

Proves the entire architecture works end-to-end using synthetic data.
Zero external dependencies.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from alphaa.broker.paper import PaperBroker
from alphaa.conditions.position import has_no_position, has_position, stop_loss
from alphaa.conditions.price import price_near_52w_high, price_near_52w_low
from alphaa.core.strategy import Strategy
from alphaa.core.types import BacktestConfig, DateRange
from alphaa.engine.backtest import BacktestEngine
from alphaa.engine.cost_models import ZeroCostModel
from alphaa.indicators.price import rolling_high, rolling_low
from tests.conftest import make_ohlcv_df


class SyntheticProvider:
    """A DataProvider that returns a pre-built DataFrame."""

    def __init__(self, df):  # type: ignore[no-untyped-def]
        self._df = df

    def fetch_ohlcv(self, symbol, date_range):  # type: ignore[no-untyped-def]
        return self._df

    def fetch_symbols(self, index=None):  # type: ignore[no-untyped-def]
        return []


def _make_price_pattern() -> list[float]:
    """Create a price pattern that triggers buy-low/sell-high strategy.

    The key insight: make_ohlcv_df sets open=high=low=close, so we need
    to establish a range where the 52w high and low are distinct from the
    current price.

    Pattern:
    - 10 days at 120 (establish 52w high)
    - 10 days at 80 (establish 52w low)
    - 232 days at 100 (stable middle — neither near high nor low)
    - 5 days at 82 (near 52w low of 80 → triggers buy)
    - 50 days rising from 82 toward 118
    - 5 days at 118 (near 52w high → triggers sell)
    - 10 days at 100 (back to middle)
    """
    prices: list[float] = []

    # Phase 1: Establish 52-week range
    prices.extend([120.0] * 10)
    prices.extend([80.0] * 10)
    prices.extend([100.0] * 232)

    # Phase 2: Drop near 52w low → triggers entry
    # 82 <= 80 * 1.05 = 84 → True
    prices.extend([82.0] * 5)

    # Phase 3: Rise toward high
    for i in range(50):
        prices.append(82.0 + (36.0 * (i + 1) / 50))

    # Phase 4: Near 52w high → triggers exit
    prices.extend([118.0] * 5)

    # Phase 5: Back to middle
    prices.extend([100.0] * 10)

    return prices


class TestBacktestEngineIntegration:
    """End-to-end integration test with synthetic data."""

    def test_full_backtest_produces_result(self) -> None:
        prices = _make_price_pattern()
        df = make_ohlcv_df(prices, start_date=date(2023, 1, 2))
        provider = SyntheticProvider(df)

        strategy = Strategy(
            name="buy-low-sell-high",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=price_near_52w_high(within_pct=5) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="TEST.NS",
            date_range=DateRange(date(2023, 1, 2), date(2025, 6, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        engine = BacktestEngine()
        result = engine.run(config)

        # Basic structure checks
        assert result.strategy_name == "buy-low-sell-high"
        assert result.symbol == "TEST.NS"
        assert result.starting_capital == 100_000.0
        assert len(result.equity_curve) == len(prices)
        assert len(result.benchmark_curve) == len(prices)

    def test_trades_are_generated(self) -> None:
        prices = _make_price_pattern()
        df = make_ohlcv_df(prices, start_date=date(2023, 1, 2))
        provider = SyntheticProvider(df)

        strategy = Strategy(
            name="buy-low-sell-high",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=price_near_52w_high(within_pct=5) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="TEST.NS",
            date_range=DateRange(date(2023, 1, 2), date(2025, 6, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        result = BacktestEngine().run(config)

        # Should have at least one trade
        assert len(result.trade_log) >= 1

        # First trade should be profitable (bought near low, sold near high)
        trade = result.trade_log[0]
        assert trade.pnl > 0
        assert trade.entry.price < trade.exit.price
        assert trade.holding_days > 0

    def test_equity_curve_starts_at_initial_capital(self) -> None:
        # Close is always 100, but high=200 and low=50 to establish a wide range.
        # This ensures 100 is never within 5% of 52w low (50) or high (200).
        dates = pd.bdate_range("2023-01-02", periods=300)
        df = pd.DataFrame(
            {
                "open": [100.0] * 300,
                "high": [200.0] * 300,
                "low": [50.0] * 300,
                "close": [100.0] * 300,
                "volume": [1000] * 300,
            },
            index=dates,
        )
        provider = SyntheticProvider(df)

        strategy = Strategy(
            name="never-trades",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=price_near_52w_high(within_pct=5) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="TEST.NS",
            date_range=DateRange(date(2023, 1, 2), date(2024, 6, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        result = BacktestEngine().run(config)

        # No trades — price stays in the middle, never near 52w low or high
        assert len(result.trade_log) == 0
        # Equity stays at initial capital
        assert result.equity_curve[0].total_value == pytest.approx(100_000.0)
        assert result.equity_curve[-1].total_value == pytest.approx(100_000.0)

    def test_benchmark_curve_tracks_buy_and_hold(self) -> None:
        prices = [100.0] * 100 + [200.0] * 100
        df = make_ohlcv_df(prices, start_date=date(2023, 1, 2))
        provider = SyntheticProvider(df)

        strategy = Strategy(
            name="test",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=price_near_52w_high(within_pct=5) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="TEST.NS",
            date_range=DateRange(date(2023, 1, 2), date(2024, 1, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        result = BacktestEngine().run(config)

        # Benchmark buys 1000 shares at 100, holds
        # At price 200: value = 1000*200 = 200_000
        assert result.benchmark_curve[-1].total_value == pytest.approx(200_000.0)

    def test_stop_loss_exits_position(self) -> None:
        """Verify stop loss triggers exit when price drops sharply."""
        prices: list[float] = []
        # Establish range with distinct high and low
        prices.extend([120.0] * 10)
        prices.extend([80.0] * 10)
        prices.extend([100.0] * 232)
        # Drop near 52w low → triggers entry at 82
        prices.extend([82.0] * 5)
        # Sharp drop to 70 (triggers 10% stop loss from 82 entry: 82*0.9=73.8)
        prices.extend([70.0] * 10)
        # Recovery
        prices.extend([100.0] * 10)

        df = make_ohlcv_df(prices, start_date=date(2023, 1, 2))
        provider = SyntheticProvider(df)

        strategy = Strategy(
            name="with-stop-loss",
            entry=price_near_52w_low(within_pct=5) & has_no_position(),
            exit=(price_near_52w_high(within_pct=5) | stop_loss(pct=10)) & has_position(),
            indicators=[rolling_high(252), rolling_low(252)],
        )

        config = BacktestConfig(
            strategy=strategy,
            symbol="TEST.NS",
            date_range=DateRange(date(2023, 1, 2), date(2025, 6, 1)),
            starting_capital=100_000.0,
            data_provider=provider,
            broker=PaperBroker(),
            cost_model=ZeroCostModel(),
        )

        result = BacktestEngine().run(config)

        # Should have a trade that exited at a loss (stop loss)
        assert len(result.trade_log) >= 1
        trade = result.trade_log[0]
        assert trade.pnl < 0  # Stop loss = loss
