"""Core vocabulary — types, protocols, conditions, strategy."""

from alphaa.core.conditions import ConditionBase, condition
from alphaa.core.protocols import Broker, CostModel, DataProvider, Indicator
from alphaa.core.strategy import Strategy
from alphaa.core.types import (
    BacktestConfig,
    BacktestMetrics,
    BacktestResult,
    Bar,
    Context,
    DateRange,
    Fill,
    Order,
    OrderStatus,
    OrderType,
    PortfolioSnapshot,
    PortfolioState,
    Position,
    Side,
    Signal,
    Trade,
)

__all__ = [
    "BacktestConfig",
    "BacktestMetrics",
    "BacktestResult",
    "Bar",
    "Broker",
    "ConditionBase",
    "Context",
    "CostModel",
    "DataProvider",
    "DateRange",
    "Fill",
    "Indicator",
    "Order",
    "OrderStatus",
    "OrderType",
    "PortfolioSnapshot",
    "PortfolioState",
    "Position",
    "Side",
    "Signal",
    "Strategy",
    "Trade",
    "condition",
]
