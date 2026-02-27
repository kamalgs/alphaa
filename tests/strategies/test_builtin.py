"""Tests for the built-in strategy factory."""

from __future__ import annotations

from alphaa.core.strategy import Strategy
from alphaa.strategies.builtin import build_default_strategy


class TestBuildDefaultStrategy:
    def test_returns_strategy(self) -> None:
        strategy = build_default_strategy()
        assert isinstance(strategy, Strategy)
        assert strategy.name == "buy-low-sell-high"

    def test_has_indicators(self) -> None:
        strategy = build_default_strategy()
        assert len(strategy.indicators) == 2

    def test_custom_params(self) -> None:
        strategy = build_default_strategy(entry_pct=10.0, exit_pct=3.0, stop_loss_pct=15.0)
        assert isinstance(strategy, Strategy)

    def test_ignores_extra_kwargs(self) -> None:
        strategy = build_default_strategy(extra="ignored")
        assert isinstance(strategy, Strategy)
