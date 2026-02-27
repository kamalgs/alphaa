"""Integration tests for the web app using FastAPI TestClient."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from alphaa.core.types import DateRange
from alphaa.service.backtest_service import BacktestRequest, BacktestResponse, run_backtest
from alphaa.web.app import create_app
from alphaa.web.db import get_db, save_run

FIXTURE_PATH = Path(__file__).parent.parent / "data" / "fixtures" / "RELIANCE_NS_2019_2024.csv"


class FixtureProvider:
    """DataProvider that reads from a pre-recorded CSV file."""

    def __init__(self, csv_path: Path) -> None:
        self._df = pd.read_csv(csv_path, index_col=0, parse_dates=True)

    def fetch_ohlcv(self, symbol: str, date_range: DateRange) -> pd.DataFrame:
        return self._df

    def fetch_symbols(self, index: str | None = None) -> list[str]:
        return []


def _make_client(tmp_path: Path) -> TestClient:
    """Create a TestClient with a tmp_path DB and fixture data provider."""
    db_path = tmp_path / "test.db"
    static_dir = tmp_path / "static"
    static_dir.mkdir()

    app = create_app()

    # Override DB dependency
    def _override_db() -> sqlite3.Connection:
        return get_db(db_path)

    from alphaa.web.routes import _get_db
    app.dependency_overrides[_get_db] = _override_db

    # Override static directory
    from fastapi.staticfiles import StaticFiles
    for route in app.routes:
        if hasattr(route, "name") and route.name == "static":
            app.routes.remove(route)
            break
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return TestClient(app)


def _seed_run(tmp_path: Path, symbol: str = "RELIANCE.NS", cagr: float = 12.5) -> int:
    """Insert a test run into the DB and return its id."""
    conn = get_db(tmp_path / "test.db")
    run_id = save_run(
        conn,
        symbol=symbol,
        start_date="2019-01-01",
        end_date="2024-01-01",
        capital=100_000.0,
        entry_pct=5.0,
        exit_pct=5.0,
        stop_loss_pct=10.0,
        strategy_name="buy-low-sell-high",
        total_return_pct=80.0,
        cagr_pct=cagr,
        max_drawdown_pct=15.0,
        sharpe_ratio=1.2,
        win_rate_pct=60.0,
        total_trades=5,
        avg_holding_days=90.0,
        profit_factor=2.5,
    )
    conn.close()
    return run_id


class TestGetIndex:
    def test_returns_200(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Run a Backtest" in resp.text


class TestPostRun:
    def test_redirects_on_success(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        provider = FixtureProvider(FIXTURE_PATH)

        original_run = run_backtest

        def patched_run(
            request: BacktestRequest,
            data_provider: object = None,
        ) -> BacktestResponse:
            return original_run(request, data_provider=provider)

        with patch("alphaa.web.routes.run_backtest", side_effect=patched_run), \
             patch("alphaa.web.routes.STATIC_DIR", tmp_path / "static"):
            resp = client.post(
                "/run",
                data={
                    "symbol": "RELIANCE.NS",
                    "start": "2019-01-01",
                    "end": "2024-01-01",
                    "capital": "100000",
                    "entry_pct": "5",
                    "exit_pct": "5",
                    "stop_loss": "10",
                },
                follow_redirects=False,
            )

        assert resp.status_code == 303
        assert resp.headers["location"].startswith("/result/")


class TestGetResult:
    def test_returns_200_for_existing_run(self, tmp_path: Path) -> None:
        run_id = _seed_run(tmp_path)
        client = _make_client(tmp_path)
        resp = client.get(f"/result/{run_id}")
        assert resp.status_code == 200
        assert "RELIANCE.NS" in resp.text

    def test_returns_404_for_missing_run(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        resp = client.get("/result/999")
        assert resp.status_code == 404


class TestGetLeaderboard:
    def test_returns_200(self, tmp_path: Path) -> None:
        client = _make_client(tmp_path)
        resp = client.get("/leaderboard")
        assert resp.status_code == 200
        assert "Leaderboard" in resp.text

    def test_shows_runs_sorted_by_cagr(self, tmp_path: Path) -> None:
        _seed_run(tmp_path, "AAAA.NS", cagr=5.0)
        _seed_run(tmp_path, "BBBB.NS", cagr=20.0)
        client = _make_client(tmp_path)
        resp = client.get("/leaderboard")
        assert resp.status_code == 200
        # BBBB should appear before AAAA (higher CAGR)
        assert resp.text.index("BBBB.NS") < resp.text.index("AAAA.NS")
