"""Protocols for AlphaA components.

Structural typing — any object with the right shape satisfies the protocol.
No inheritance required.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import pandas as pd

from alphaa.core.types import DateRange, Fill, Order, Position

Indicator = Callable[[pd.DataFrame], pd.Series]


class DataProvider(Protocol):
    def fetch_ohlcv(self, symbol: str, date_range: DateRange) -> pd.DataFrame: ...
    def fetch_symbols(self, index: str | None = None) -> list[str]: ...


class Broker(Protocol):
    def place_order(self, order: Order) -> Fill: ...
    def cancel_order(self, order_id: str) -> bool: ...
    def get_positions(self) -> dict[str, Position]: ...
    def get_portfolio_value(self) -> float: ...


class CostModel(Protocol):
    def compute_fees(self, order: Order, fill_price: float) -> float: ...
