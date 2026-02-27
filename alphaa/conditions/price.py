"""Price-based conditions."""

from __future__ import annotations

from alphaa.core.conditions import condition
from alphaa.core.types import Context


@condition
def price_near_52w_low(ctx: Context, within_pct: float = 5.0) -> bool:
    """True when close is within `within_pct`% of 52-week low."""
    low_52w = ctx.indicators["low_252"].iloc[-1]
    return bool(ctx.close <= low_52w * (1 + within_pct / 100))


@condition
def price_near_52w_high(ctx: Context, within_pct: float = 5.0) -> bool:
    """True when close is within `within_pct`% of 52-week high."""
    high_52w = ctx.indicators["high_252"].iloc[-1]
    return bool(ctx.close >= high_52w * (1 - within_pct / 100))
