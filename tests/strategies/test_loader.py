"""Tests for the sandboxed strategy loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from alphaa.core.strategy import Strategy
from alphaa.strategies.loader import (
    StrategyLoadError,
    delete_strategy_file,
    list_strategy_files,
    load_strategy,
    save_strategy_file,
    validate_strategy_source,
)

VALID_STRATEGY = """\
def build_strategy(**params):
    return Strategy(
        name="test-strategy",
        entry=price_near_52w_low(within_pct=params.get("pct", 5.0)) & has_no_position(),
        exit=has_position(),
        indicators=[rolling_high(252), rolling_low(252)],
    )
"""

VALID_STRATEGY_WITH_SMA = """\
def build_strategy(**params):
    return Strategy(
        name="sma-strategy",
        entry=price_near_52w_low() & has_no_position(),
        exit=has_position(),
        indicators=[sma(20), rolling_high(252), rolling_low(252)],
    )
"""

MISSING_BUILD_STRATEGY = """\
def some_other_function():
    pass
"""

RETURNS_WRONG_TYPE = """\
def build_strategy(**params):
    return "not a strategy"
"""

IMPORT_OS = """\
import os

def build_strategy(**params):
    return Strategy(
        name="bad",
        entry=has_no_position(),
        exit=has_position(),
        indicators=[],
    )
"""

USES_OPEN = """\
def build_strategy(**params):
    data = open("/etc/passwd").read()
    return Strategy(
        name="bad",
        entry=has_no_position(),
        exit=has_position(),
        indicators=[],
    )
"""

USES_EXEC = """\
def build_strategy(**params):
    exec("print('hacked')")
    return Strategy(
        name="bad",
        entry=has_no_position(),
        exit=has_position(),
        indicators=[],
    )
"""

USES_DUNDER_ATTR = """\
def build_strategy(**params):
    x = Strategy.__class__
    return Strategy(
        name="bad",
        entry=has_no_position(),
        exit=has_position(),
        indicators=[],
    )
"""


class TestValidateStrategySource:
    def test_valid_strategy(self) -> None:
        errors = validate_strategy_source(VALID_STRATEGY)
        assert errors == []

    def test_valid_with_sma(self) -> None:
        errors = validate_strategy_source(VALID_STRATEGY_WITH_SMA)
        assert errors == []

    def test_missing_build_strategy(self) -> None:
        errors = validate_strategy_source(MISSING_BUILD_STRATEGY)
        assert any("build_strategy" in e for e in errors)

    def test_import_blocked(self) -> None:
        errors = validate_strategy_source(IMPORT_OS)
        assert len(errors) > 0

    def test_syntax_error(self) -> None:
        errors = validate_strategy_source("def build_strategy(:\n  pass")
        assert len(errors) > 0


class TestLoadStrategy:
    def test_load_valid(self, tmp_path: Path) -> None:
        path = tmp_path / "valid.py"
        path.write_text(VALID_STRATEGY)
        strategy = load_strategy(path)
        assert isinstance(strategy, Strategy)
        assert strategy.name == "test-strategy"

    def test_load_with_params(self, tmp_path: Path) -> None:
        path = tmp_path / "valid.py"
        path.write_text(VALID_STRATEGY)
        strategy = load_strategy(path, params={"pct": 10.0})
        assert isinstance(strategy, Strategy)

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(StrategyLoadError, match="not found"):
            load_strategy(tmp_path / "nope.py")

    def test_returns_wrong_type(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.py"
        path.write_text(RETURNS_WRONG_TYPE)
        with pytest.raises(StrategyLoadError, match="must return a Strategy"):
            load_strategy(path)

    def test_import_blocked(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.py"
        path.write_text(IMPORT_OS)
        with pytest.raises(StrategyLoadError, match="Invalid strategy"):
            load_strategy(path)

    def test_open_blocked(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.py"
        path.write_text(USES_OPEN)
        with pytest.raises(StrategyLoadError):
            load_strategy(path)

    def test_dunder_attr_blocked(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.py"
        path.write_text(USES_DUNDER_ATTR)
        with pytest.raises(StrategyLoadError):
            load_strategy(path)


class TestSaveAndListStrategies:
    def test_save_and_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("alphaa.strategies.loader.STRATEGIES_DIR", tmp_path)
        save_strategy_file("my_strat.py", VALID_STRATEGY)
        files = list_strategy_files()
        assert len(files) == 1
        assert files[0].name == "my_strat.py"

    def test_delete(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("alphaa.strategies.loader.STRATEGIES_DIR", tmp_path)
        save_strategy_file("to_delete.py", VALID_STRATEGY)
        assert (tmp_path / "to_delete.py").exists()
        delete_strategy_file("to_delete.py")
        assert not (tmp_path / "to_delete.py").exists()

    def test_list_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("alphaa.strategies.loader.STRATEGIES_DIR", tmp_path / "empty")
        files = list_strategy_files()
        assert files == []
