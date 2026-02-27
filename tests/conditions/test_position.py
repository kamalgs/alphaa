"""Tests for position conditions."""

from __future__ import annotations

from alphaa.conditions.position import has_no_position, has_position, stop_loss
from tests.conftest import make_context, make_position


class TestHasPosition:
    def test_with_position(self) -> None:
        pos = make_position(symbol="TEST.NS")
        ctx = make_context(positions={"TEST.NS": pos})
        assert has_position()(ctx) is True

    def test_without_position(self) -> None:
        ctx = make_context()
        assert has_position()(ctx) is False


class TestHasNoPosition:
    def test_with_position(self) -> None:
        pos = make_position(symbol="TEST.NS")
        ctx = make_context(positions={"TEST.NS": pos})
        assert has_no_position()(ctx) is False

    def test_without_position(self) -> None:
        ctx = make_context()
        assert has_no_position()(ctx) is True


class TestStopLoss:
    def test_triggered(self) -> None:
        pos = make_position(symbol="TEST.NS", avg_cost=100.0)
        ctx = make_context(close=85.0, positions={"TEST.NS": pos})
        # 85 <= 100 * 0.90 = 90 → True
        assert stop_loss(pct=10.0)(ctx) is True

    def test_not_triggered(self) -> None:
        pos = make_position(symbol="TEST.NS", avg_cost=100.0)
        ctx = make_context(close=95.0, positions={"TEST.NS": pos})
        # 95 <= 100 * 0.90 = 90 → False
        assert stop_loss(pct=10.0)(ctx) is False

    def test_no_position(self) -> None:
        ctx = make_context(close=50.0)
        assert stop_loss(pct=10.0)(ctx) is False
