"""Core value types for AlphaA.

All domain objects are frozen dataclasses (immutable) except PortfolioState,
which is the sole deliberately mutable type owned exclusively by the engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum, auto
from typing import TYPE_CHECKING, NamedTuple

import pandas as pd

if TYPE_CHECKING:
    from alphaa.core.strategy import Strategy


# --- Enums ---


class Side(Enum):
    BUY = auto()
    SELL = auto()


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()


class OrderStatus(Enum):
    PENDING = auto()
    FILLED = auto()
    CANCELLED = auto()
    REJECTED = auto()


# --- Market Data ---


@dataclass(frozen=True)
class Bar:
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: float | None = None


# --- Signals & Orders ---


@dataclass(frozen=True)
class Signal:
    symbol: str
    side: Side
    date: date
    reason: str = ""


@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None


@dataclass(frozen=True)
class Fill:
    symbol: str
    side: Side
    quantity: int
    price: float
    date: date
    fees: float = 0.0


# --- Trades ---


@dataclass(frozen=True)
class Trade:
    symbol: str
    entry: Fill
    exit: Fill

    @property
    def pnl(self) -> float:
        return (
            (self.exit.price - self.entry.price) * self.entry.quantity
            - self.entry.fees
            - self.exit.fees
        )

    @property
    def holding_days(self) -> int:
        return (self.exit.date - self.entry.date).days

    @property
    def return_pct(self) -> float:
        return (self.exit.price - self.entry.price) / self.entry.price


# --- Portfolio ---


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_cost: float
    lots: list[Fill] = field(default_factory=list)


@dataclass
class PortfolioState:
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)

    def snapshot(self, date: date, prices: dict[str, float]) -> PortfolioSnapshot:
        holdings = sum(
            pos.quantity * prices.get(pos.symbol, pos.avg_cost)
            for pos in self.positions.values()
        )
        return PortfolioSnapshot(
            date=date,
            cash=self.cash,
            holdings_value=holdings,
            total_value=self.cash + holdings,
        )


@dataclass(frozen=True)
class PortfolioSnapshot:
    date: date
    cash: float
    holdings_value: float
    total_value: float


class DateRange(NamedTuple):
    start: date
    end: date


# --- Context ---


@dataclass(frozen=True)
class Context:
    current_bar: Bar
    history: pd.DataFrame
    portfolio: PortfolioState
    indicators: dict[str, pd.Series]
    params: dict[str, object] = field(default_factory=dict)

    @property
    def date(self) -> date:
        return self.current_bar.date

    @property
    def close(self) -> float:
        return self.current_bar.close

    @property
    def symbol(self) -> str:
        return self.current_bar.symbol


# --- Backtest ---


@dataclass(frozen=True)
class BacktestResult:
    strategy_name: str
    symbol: str
    date_range: DateRange
    starting_capital: float
    trade_log: list[Trade]
    equity_curve: list[PortfolioSnapshot]
    benchmark_curve: list[PortfolioSnapshot]


@dataclass(frozen=True)
class BacktestMetrics:
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate_pct: float
    total_trades: int
    avg_holding_days: float
    profit_factor: float
    benchmark_return_pct: float | None


@dataclass
class BacktestConfig:
    strategy: Strategy
    symbol: str
    date_range: DateRange
    starting_capital: float = 100_000.0
    data_provider: object | None = None  # DataProvider protocol
    broker: object | None = None  # Broker protocol
    cost_model: object | None = None  # CostModel protocol
    benchmark_symbol: str | None = None


__all__ = [
    "Side",
    "OrderType",
    "OrderStatus",
    "Bar",
    "Signal",
    "Order",
    "Fill",
    "Trade",
    "Position",
    "PortfolioState",
    "PortfolioSnapshot",
    "DateRange",
    "Context",
    "BacktestResult",
    "BacktestMetrics",
    "BacktestConfig",
]
