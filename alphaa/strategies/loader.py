"""Sandboxed strategy loader using RestrictedPython.

Uploaded user strategy files are compiled and executed in a restricted
sandbox — only whitelisted alphaa building blocks are available, and
import/open/exec/eval are all blocked.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from RestrictedPython import compile_restricted_exec, safe_builtins
from RestrictedPython.Guards import guarded_iter_unpack_sequence, safer_getattr

from alphaa.conditions.position import has_no_position, has_position, stop_loss
from alphaa.conditions.price import price_near_52w_high, price_near_52w_low
from alphaa.core.conditions import ConditionBase, condition
from alphaa.core.strategy import Strategy
from alphaa.indicators.price import rolling_high, rolling_low, sma

STRATEGIES_DIR = Path("~/.alphaa/strategies").expanduser()


class StrategyLoadError(Exception):
    """Raised when a strategy file cannot be loaded or executed."""


def _build_allowed_globals() -> dict[str, Any]:
    """Build the dict of globals available inside the sandbox."""
    return {
        "__builtins__": safe_builtins,
        "__name__": "user_strategy",
        # Guard functions for safe attribute/iteration access
        "_getattr_": safer_getattr,
        "_getiter_": iter,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        # Core
        "Strategy": Strategy,
        "ConditionBase": ConditionBase,
        "condition": condition,
        # Conditions — price
        "price_near_52w_low": price_near_52w_low,
        "price_near_52w_high": price_near_52w_high,
        # Conditions — position
        "has_position": has_position,
        "has_no_position": has_no_position,
        "stop_loss": stop_loss,
        # Indicators
        "sma": sma,
        "rolling_high": rolling_high,
        "rolling_low": rolling_low,
    }


def save_strategy_file(filename: str, content: str) -> Path:
    """Save strategy source to ~/.alphaa/strategies/ and return the path."""
    STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
    path = STRATEGIES_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path


def validate_strategy_source(source: str) -> list[str]:
    """Compile source with RestrictedPython and return a list of errors.

    An empty list means the source is valid. Checks:
    1. RestrictedPython compilation succeeds
    2. A ``build_strategy`` callable is defined
    """
    errors: list[str] = []

    result = compile_restricted_exec(source)

    if result.errors:
        errors.extend(result.errors)
        return errors

    if result.code is None:
        errors.append("Compilation produced no code.")
        return errors

    # Execute in sandbox to check that build_strategy is defined
    sandbox_globals = _build_allowed_globals()
    sandbox_locals: dict[str, Any] = {}
    try:
        exec(result.code, sandbox_globals, sandbox_locals)  # noqa: S102
    except Exception as exc:
        errors.append(f"Execution error: {exc}")
        return errors

    if "build_strategy" not in sandbox_locals:
        errors.append("Strategy file must define a 'build_strategy' function.")
    elif not callable(sandbox_locals["build_strategy"]):
        errors.append("'build_strategy' must be callable.")

    return errors


def load_strategy(filepath: Path, params: dict[str, Any] | None = None) -> Strategy:
    """Load a strategy from a .py file, execute in sandbox, and return a Strategy.

    Raises ``StrategyLoadError`` on any failure.
    """
    if not filepath.exists():
        msg = f"Strategy file not found: {filepath}"
        raise StrategyLoadError(msg)

    source = filepath.read_text(encoding="utf-8")
    validation_errors = validate_strategy_source(source)
    if validation_errors:
        msg = f"Invalid strategy: {'; '.join(validation_errors)}"
        raise StrategyLoadError(msg)

    result = compile_restricted_exec(source)
    assert result.code is not None  # validated above

    sandbox_globals = _build_allowed_globals()
    sandbox_locals: dict[str, Any] = {}
    exec(result.code, sandbox_globals, sandbox_locals)  # noqa: S102

    build_fn = sandbox_locals["build_strategy"]
    effective_params = params or {}

    try:
        strategy = build_fn(**effective_params)
    except Exception as exc:
        msg = f"build_strategy() failed: {exc}"
        raise StrategyLoadError(msg) from exc

    if not isinstance(strategy, Strategy):
        msg = f"build_strategy() must return a Strategy, got {type(strategy).__name__}"
        raise StrategyLoadError(msg)

    return strategy


def list_strategy_files() -> list[Path]:
    """Return all .py files in the strategies directory."""
    if not STRATEGIES_DIR.exists():
        return []
    return sorted(STRATEGIES_DIR.glob("*.py"))


def delete_strategy_file(filename: str) -> None:
    """Delete a strategy file by name."""
    path = STRATEGIES_DIR / filename
    if path.exists():
        path.unlink()
