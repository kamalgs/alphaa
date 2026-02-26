"""Paper broker — simulated order execution for backtesting."""

from __future__ import annotations

from datetime import date

from alphaa.core.types import Fill, Order, Position


class PaperBroker:
    """Fills orders at a given price (typically current bar's close).

    Satisfies the Broker protocol.
    """

    def __init__(self) -> None:
        self._current_date: date = date(2000, 1, 1)
        self._current_price: float = 0.0
        self._positions: dict[str, Position] = {}
        self._fees: float = 0.0

    def set_current_bar(self, bar_date: date, price: float) -> None:
        """Called by the engine before placing orders."""
        self._current_date = bar_date
        self._current_price = price

    def set_fees(self, fees: float) -> None:
        """Set the fees to apply to the next fill."""
        self._fees = fees

    def place_order(self, order: Order) -> Fill:
        return Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=self._current_price,
            date=self._current_date,
            fees=self._fees,
        )

    def cancel_order(self, order_id: str) -> bool:
        return False

    def get_positions(self) -> dict[str, Position]:
        return self._positions

    def get_portfolio_value(self) -> float:
        return 0.0
