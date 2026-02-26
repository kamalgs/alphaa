"""Tests for the condition composition system."""

from __future__ import annotations

from tests.conftest import make_context

from alphaa.core.conditions import ConditionBase, _And, _Not, _Or, condition
from alphaa.core.types import Context


@condition
def always_true(ctx: Context) -> bool:
    return True


@condition
def always_false(ctx: Context) -> bool:
    return False


@condition
def price_above(ctx: Context, threshold: float) -> bool:
    return ctx.close > threshold


class TestConditionDecorator:
    def test_creates_callable(self) -> None:
        cond = always_true()
        assert isinstance(cond, ConditionBase)

    def test_returns_bool(self) -> None:
        ctx = make_context()
        assert always_true()(ctx) is True
        assert always_false()(ctx) is False

    def test_parameterized_condition(self) -> None:
        ctx = make_context(close=150.0)
        assert price_above(100.0)(ctx) is True
        assert price_above(200.0)(ctx) is False

    def test_repr_no_params(self) -> None:
        cond = always_true()
        assert repr(cond) == "always_true()"

    def test_repr_with_params(self) -> None:
        cond = price_above(100.0)
        assert repr(cond) == "price_above(100.0)"

    def test_repr_with_kwargs(self) -> None:
        cond = price_above(threshold=100.0)
        assert repr(cond) == "price_above(threshold=100.0)"


class TestAnd:
    def test_both_true(self) -> None:
        ctx = make_context()
        cond = always_true() & always_true()
        assert isinstance(cond, _And)
        assert cond(ctx) is True

    def test_one_false(self) -> None:
        ctx = make_context()
        assert (always_true() & always_false())(ctx) is False
        assert (always_false() & always_true())(ctx) is False

    def test_both_false(self) -> None:
        ctx = make_context()
        assert (always_false() & always_false())(ctx) is False

    def test_repr(self) -> None:
        cond = always_true() & always_false()
        assert repr(cond) == "(always_true() & always_false())"


class TestOr:
    def test_both_true(self) -> None:
        ctx = make_context()
        cond = always_true() | always_true()
        assert isinstance(cond, _Or)
        assert cond(ctx) is True

    def test_one_true(self) -> None:
        ctx = make_context()
        assert (always_true() | always_false())(ctx) is True
        assert (always_false() | always_true())(ctx) is True

    def test_both_false(self) -> None:
        ctx = make_context()
        assert (always_false() | always_false())(ctx) is False

    def test_repr(self) -> None:
        cond = always_true() | always_false()
        assert repr(cond) == "(always_true() | always_false())"


class TestNot:
    def test_inverts_true(self) -> None:
        ctx = make_context()
        cond = ~always_true()
        assert isinstance(cond, _Not)
        assert cond(ctx) is False

    def test_inverts_false(self) -> None:
        ctx = make_context()
        assert (~always_false())(ctx) is True

    def test_repr(self) -> None:
        cond = ~always_true()
        assert repr(cond) == "~always_true()"


class TestNestedComposition:
    def test_and_or_not(self) -> None:
        ctx = make_context(close=150.0)
        # (true & true) | ~false => True | True => True
        cond = (always_true() & price_above(100.0)) | ~always_false()
        assert cond(ctx) is True

    def test_complex_tree(self) -> None:
        ctx = make_context(close=150.0)
        # (price_above(100) & ~always_false()) should be True
        cond = price_above(100.0) & ~always_false()
        assert cond(ctx) is True

        # (price_above(200) & ~always_false()) should be False
        cond2 = price_above(200.0) & ~always_false()
        assert cond2(ctx) is False
