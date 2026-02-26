"""Position-based conditions."""

from __future__ import annotations

from alphaa.core.conditions import condition
from alphaa.core.types import Context


@condition
def has_position(ctx: Context) -> bool:
    """True when there is an open position for the current symbol."""
    return ctx.symbol in ctx.portfolio.positions


@condition
def has_no_position(ctx: Context) -> bool:
    """True when there is no open position for the current symbol."""
    return ctx.symbol not in ctx.portfolio.positions


@condition
def stop_loss(ctx: Context, pct: float = 10.0) -> bool:
    """True when current price has fallen `pct`% below average cost."""
    pos = ctx.portfolio.positions.get(ctx.symbol)
    if pos is None:
        return False
    return ctx.close <= pos.avg_cost * (1 - pct / 100)
