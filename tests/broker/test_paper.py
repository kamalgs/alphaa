"""Tests for PaperBroker."""

from __future__ import annotations

from datetime import date

from alphaa.broker.paper import PaperBroker
from alphaa.core.types import Order, Side


class TestPaperBroker:
    def test_fill_at_current_price(self) -> None:
        broker = PaperBroker()
        broker.set_current_bar(date(2024, 1, 15), 150.0)

        order = Order(symbol="TEST.NS", side=Side.BUY, quantity=10)
        fill = broker.place_order(order)

        assert fill.symbol == "TEST.NS"
        assert fill.side == Side.BUY
        assert fill.quantity == 10
        assert fill.price == 150.0
        assert fill.date == date(2024, 1, 15)
        assert fill.fees == 0.0

    def test_fill_with_fees(self) -> None:
        broker = PaperBroker()
        broker.set_current_bar(date(2024, 1, 15), 100.0)
        broker.set_fees(5.50)

        order = Order(symbol="TEST.NS", side=Side.SELL, quantity=5)
        fill = broker.place_order(order)

        assert fill.fees == 5.50
        assert fill.price == 100.0

    def test_sell_order(self) -> None:
        broker = PaperBroker()
        broker.set_current_bar(date(2024, 6, 1), 200.0)

        order = Order(symbol="TEST.NS", side=Side.SELL, quantity=20)
        fill = broker.place_order(order)

        assert fill.side == Side.SELL
        assert fill.quantity == 20
