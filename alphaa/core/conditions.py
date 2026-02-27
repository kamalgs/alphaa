"""Composable condition system for AlphaA.

The @condition decorator transforms plain functions into composable objects
with &, |, ~ operators. Every condition receives a single Context argument.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Concatenate, ParamSpec

if TYPE_CHECKING:
    from alphaa.core.types import Context

P = ParamSpec("P")


class ConditionBase:
    """Base class providing boolean composition operators."""

    def __call__(self, ctx: Context) -> bool:
        raise NotImplementedError

    def __and__(self, other: ConditionBase) -> _And:
        return _And(self, other)

    def __or__(self, other: ConditionBase) -> _Or:
        return _Or(self, other)

    def __invert__(self) -> _Not:
        return _Not(self)


class _And(ConditionBase):
    def __init__(self, left: ConditionBase, right: ConditionBase) -> None:
        self._left = left
        self._right = right

    def __call__(self, ctx: Context) -> bool:
        return self._left(ctx) and self._right(ctx)

    def __repr__(self) -> str:
        return f"({self._left!r} & {self._right!r})"


class _Or(ConditionBase):
    def __init__(self, left: ConditionBase, right: ConditionBase) -> None:
        self._left = left
        self._right = right

    def __call__(self, ctx: Context) -> bool:
        return self._left(ctx) or self._right(ctx)

    def __repr__(self) -> str:
        return f"({self._left!r} | {self._right!r})"


class _Not(ConditionBase):
    def __init__(self, inner: ConditionBase) -> None:
        self._inner = inner

    def __call__(self, ctx: Context) -> bool:
        return not self._inner(ctx)

    def __repr__(self) -> str:
        return f"~{self._inner!r}"


def condition(
    fn: Callable[Concatenate[Context, P], bool],
) -> Callable[P, ConditionBase]:
    """Decorator that transforms a function into a composable condition factory.

    The decorated function must have Context as its first parameter.
    Additional parameters become the factory's arguments.

    Usage:
        @condition
        def price_above(ctx: Context, threshold: float) -> bool:
            return ctx.close > threshold

        # Creates a composable condition object:
        cond = price_above(100.0)
        result = cond(ctx)  # evaluates the condition

        # Compose with boolean operators:
        combined = price_above(100.0) & price_above(50.0)
    """

    @wraps(fn)
    def factory(*args: P.args, **kwargs: P.kwargs) -> ConditionBase:
        class _Cond(ConditionBase):
            def __call__(self, ctx: Context) -> bool:
                return fn(ctx, *args, **kwargs)

            def __repr__(self) -> str:
                params = ", ".join(
                    [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
                )
                return f"{fn.__name__}({params})"

        return _Cond()

    return factory
