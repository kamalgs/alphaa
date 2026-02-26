"""Cost models for backtesting."""

from __future__ import annotations

from alphaa.core.types import Order


class ZeroCostModel:
    """Zero-fee cost model. Satisfies the CostModel protocol."""

    def compute_fees(self, order: Order, fill_price: float) -> float:
        return 0.0
