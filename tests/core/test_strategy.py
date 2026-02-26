"""Tests for Strategy dataclass."""

from __future__ import annotations

from alphaa.core.conditions import condition
from alphaa.core.strategy import Strategy
from alphaa.core.types import Context
from tests.conftest import make_context


@condition
def mock_entry(ctx: Context) -> bool:
    return True


@condition
def mock_exit(ctx: Context) -> bool:
    return False


class TestStrategy:
    def test_construction(self) -> None:
        strategy = Strategy(
            name="test-strategy",
            entry=mock_entry(),
            exit=mock_exit(),
        )
        assert strategy.name == "test-strategy"
        assert strategy.indicators == []
        assert strategy.params == {}

    def test_frozen(self) -> None:
        import pytest

        strategy = Strategy(name="test", entry=mock_entry(), exit=mock_exit())
        with pytest.raises(AttributeError):
            strategy.name = "changed"  # type: ignore[misc]

    def test_entry_exit_are_callable(self) -> None:
        strategy = Strategy(name="test", entry=mock_entry(), exit=mock_exit())
        ctx = make_context()
        assert strategy.entry(ctx) is True
        assert strategy.exit(ctx) is False

    def test_with_params(self) -> None:
        strategy = Strategy(
            name="test",
            entry=mock_entry(),
            exit=mock_exit(),
            params={"threshold": 5.0},
        )
        assert strategy.params["threshold"] == 5.0
