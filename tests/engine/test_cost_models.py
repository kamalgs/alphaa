"""Tests for cost models."""

from __future__ import annotations

from alphaa.core.types import Order, Side
from alphaa.engine.cost_models import ZeroCostModel


class TestZeroCostModel:
    def test_returns_zero(self) -> None:
        model = ZeroCostModel()
        order = Order(symbol="TEST.NS", side=Side.BUY, quantity=10)
        assert model.compute_fees(order, 100.0) == 0.0

    def test_returns_zero_for_sell(self) -> None:
        model = ZeroCostModel()
        order = Order(symbol="TEST.NS", side=Side.SELL, quantity=5)
        assert model.compute_fees(order, 200.0) == 0.0
