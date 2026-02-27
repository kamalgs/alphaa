"""Tests for core value types."""

from datetime import date

import pytest

from alphaa.core.types import (
    Bar,
    DateRange,
    Fill,
    Order,
    OrderType,
    PortfolioSnapshot,
    PortfolioState,
    Position,
    Side,
    Signal,
    Trade,
)


class TestBar:
    def test_creation(self) -> None:
        bar = Bar(
            symbol="RELIANCE.NS",
            date=date(2024, 1, 15),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=50000,
        )
        assert bar.symbol == "RELIANCE.NS"
        assert bar.close == 102.0
        assert bar.adj_close is None

    def test_frozen(self) -> None:
        bar = Bar("TEST.NS", date(2024, 1, 1), 100, 105, 95, 100, 1000)
        with pytest.raises(AttributeError):
            bar.close = 200.0  # type: ignore[misc]


class TestSignal:
    def test_creation(self) -> None:
        sig = Signal(symbol="TEST.NS", side=Side.BUY, date=date(2024, 1, 1))
        assert sig.side == Side.BUY
        assert sig.reason == ""

    def test_frozen(self) -> None:
        sig = Signal(symbol="TEST.NS", side=Side.BUY, date=date(2024, 1, 1))
        with pytest.raises(AttributeError):
            sig.side = Side.SELL  # type: ignore[misc]


class TestOrder:
    def test_defaults(self) -> None:
        order = Order(symbol="TEST.NS", side=Side.BUY, quantity=10)
        assert order.order_type == OrderType.MARKET
        assert order.limit_price is None

    def test_frozen(self) -> None:
        order = Order(symbol="TEST.NS", side=Side.BUY, quantity=10)
        with pytest.raises(AttributeError):
            order.quantity = 20  # type: ignore[misc]


class TestFill:
    def test_creation(self) -> None:
        fill = Fill(
            symbol="TEST.NS",
            side=Side.BUY,
            quantity=10,
            price=100.0,
            date=date(2024, 1, 1),
        )
        assert fill.fees == 0.0

    def test_frozen(self) -> None:
        fill = Fill("TEST.NS", Side.BUY, 10, 100.0, date(2024, 1, 1))
        with pytest.raises(AttributeError):
            fill.price = 200.0  # type: ignore[misc]


class TestTrade:
    def test_pnl_profit(self) -> None:
        entry = Fill("TEST.NS", Side.BUY, 10, 100.0, date(2024, 1, 1))
        exit_ = Fill("TEST.NS", Side.SELL, 10, 120.0, date(2024, 3, 1))
        trade = Trade(symbol="TEST.NS", entry=entry, exit=exit_)

        assert trade.pnl == 200.0  # (120-100)*10

    def test_pnl_loss(self) -> None:
        entry = Fill("TEST.NS", Side.BUY, 10, 100.0, date(2024, 1, 1))
        exit_ = Fill("TEST.NS", Side.SELL, 10, 80.0, date(2024, 2, 1))
        trade = Trade(symbol="TEST.NS", entry=entry, exit=exit_)

        assert trade.pnl == -200.0  # (80-100)*10

    def test_pnl_with_fees(self) -> None:
        entry = Fill("TEST.NS", Side.BUY, 10, 100.0, date(2024, 1, 1), fees=5.0)
        exit_ = Fill("TEST.NS", Side.SELL, 10, 120.0, date(2024, 3, 1), fees=5.0)
        trade = Trade(symbol="TEST.NS", entry=entry, exit=exit_)

        assert trade.pnl == 190.0  # (120-100)*10 - 5 - 5

    def test_holding_days(self) -> None:
        entry = Fill("TEST.NS", Side.BUY, 10, 100.0, date(2024, 1, 1))
        exit_ = Fill("TEST.NS", Side.SELL, 10, 120.0, date(2024, 3, 1))
        trade = Trade(symbol="TEST.NS", entry=entry, exit=exit_)

        assert trade.holding_days == 60

    def test_return_pct(self) -> None:
        entry = Fill("TEST.NS", Side.BUY, 10, 100.0, date(2024, 1, 1))
        exit_ = Fill("TEST.NS", Side.SELL, 10, 120.0, date(2024, 3, 1))
        trade = Trade(symbol="TEST.NS", entry=entry, exit=exit_)

        assert trade.return_pct == pytest.approx(0.20)


class TestPortfolioState:
    def test_snapshot_no_positions(self) -> None:
        state = PortfolioState(cash=100_000.0)
        snap = state.snapshot(date(2024, 1, 1), {})

        assert snap.cash == 100_000.0
        assert snap.holdings_value == 0.0
        assert snap.total_value == 100_000.0

    def test_snapshot_with_position(self) -> None:
        pos = Position(symbol="TEST.NS", quantity=10, avg_cost=100.0)
        state = PortfolioState(cash=90_000.0, positions={"TEST.NS": pos})
        snap = state.snapshot(date(2024, 1, 1), {"TEST.NS": 120.0})

        assert snap.cash == 90_000.0
        assert snap.holdings_value == 1200.0  # 10 * 120
        assert snap.total_value == 91_200.0

    def test_snapshot_missing_price_uses_avg_cost(self) -> None:
        pos = Position(symbol="TEST.NS", quantity=10, avg_cost=100.0)
        state = PortfolioState(cash=90_000.0, positions={"TEST.NS": pos})
        snap = state.snapshot(date(2024, 1, 1), {})

        assert snap.holdings_value == 1000.0  # falls back to avg_cost


class TestPortfolioSnapshot:
    def test_frozen(self) -> None:
        snap = PortfolioSnapshot(date(2024, 1, 1), 100_000.0, 0.0, 100_000.0)
        with pytest.raises(AttributeError):
            snap.cash = 0.0  # type: ignore[misc]


class TestDateRange:
    def test_unpacking(self) -> None:
        dr = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        start, end = dr
        assert start == date(2024, 1, 1)
        assert end == date(2024, 12, 31)

    def test_named_access(self) -> None:
        dr = DateRange(date(2024, 1, 1), date(2024, 12, 31))
        assert dr.start == date(2024, 1, 1)
        assert dr.end == date(2024, 12, 31)
