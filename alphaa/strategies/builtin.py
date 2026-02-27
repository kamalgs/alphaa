"""Built-in buy-low-sell-high strategy."""

from __future__ import annotations

from alphaa.conditions.position import has_no_position, has_position, stop_loss
from alphaa.conditions.price import price_near_52w_high, price_near_52w_low
from alphaa.core.strategy import Strategy
from alphaa.indicators.price import rolling_high, rolling_low


def build_default_strategy(
    entry_pct: float = 5.0,
    exit_pct: float = 5.0,
    stop_loss_pct: float = 10.0,
    **_kwargs: object,
) -> Strategy:
    """Build the default buy-low-sell-high strategy.

    This is the original hardcoded strategy extracted into a factory function.
    """
    return Strategy(
        name="buy-low-sell-high",
        entry=price_near_52w_low(within_pct=entry_pct) & has_no_position(),
        exit=(
            price_near_52w_high(within_pct=exit_pct)
            | stop_loss(pct=stop_loss_pct)
        )
        & has_position(),
        indicators=[rolling_high(252), rolling_low(252)],
    )
