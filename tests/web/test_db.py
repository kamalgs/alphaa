"""Tests for the SQLite persistence layer."""

from __future__ import annotations

from pathlib import Path

from alphaa.web.db import (
    delete_strategy,
    get_db,
    get_leaderboard,
    get_run,
    get_strategy,
    list_strategies,
    save_run,
    save_strategy,
)


def _sample_run_kwargs(symbol: str = "RELIANCE.NS", cagr: float = 12.5) -> dict:  # type: ignore[type-arg]
    return dict(
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


class TestDatabase:
    def test_insert_and_query(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        run_id = save_run(conn, **_sample_run_kwargs())

        row = get_run(conn, run_id)
        assert row is not None
        assert row.symbol == "RELIANCE.NS"
        assert row.cagr_pct == 12.5
        assert row.total_trades == 5
        assert row.strategy_source == "builtin"
        assert row.strategy_params_json == "{}"
        conn.close()

    def test_leaderboard_sorted_by_cagr(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        save_run(conn, **_sample_run_kwargs("AAAA.NS", cagr=5.0))
        save_run(conn, **_sample_run_kwargs("BBBB.NS", cagr=20.0))
        save_run(conn, **_sample_run_kwargs("CCCC.NS", cagr=10.0))

        rows = get_leaderboard(conn)
        assert len(rows) == 3
        assert rows[0].symbol == "BBBB.NS"
        assert rows[1].symbol == "CCCC.NS"
        assert rows[2].symbol == "AAAA.NS"
        conn.close()

    def test_get_run_not_found(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        assert get_run(conn, 999) is None
        conn.close()

    def test_leaderboard_limit(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        for i in range(5):
            save_run(conn, **_sample_run_kwargs(f"SYM{i}.NS", cagr=float(i)))

        rows = get_leaderboard(conn, limit=3)
        assert len(rows) == 3
        conn.close()

    def test_chart_paths_stored(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        run_id = save_run(
            conn,
            **_sample_run_kwargs(),
            equity_chart_path="/tmp/eq.png",
            trades_chart_path="/tmp/tr.png",
        )

        row = get_run(conn, run_id)
        assert row is not None
        assert row.equity_chart_path == "/tmp/eq.png"
        assert row.trades_chart_path == "/tmp/tr.png"
        conn.close()

    def test_strategy_source_stored(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        run_id = save_run(
            conn,
            **_sample_run_kwargs(),
            strategy_source="custom:my_strat.py",
            strategy_params_json='{"pct": 10}',
        )

        row = get_run(conn, run_id)
        assert row is not None
        assert row.strategy_source == "custom:my_strat.py"
        assert row.strategy_params_json == '{"pct": 10}'
        conn.close()


class TestStrategyCRUD:
    def test_save_and_get(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        sid = save_strategy(conn, name="My Strategy", filename="my_strat.py")

        row = get_strategy(conn, sid)
        assert row is not None
        assert row.name == "My Strategy"
        assert row.filename == "my_strat.py"
        assert row.description == ""
        conn.close()

    def test_save_with_description(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        sid = save_strategy(
            conn,
            name="Described",
            filename="desc.py",
            description="A test strategy",
        )
        row = get_strategy(conn, sid)
        assert row is not None
        assert row.description == "A test strategy"
        conn.close()

    def test_list_strategies(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        save_strategy(conn, name="First", filename="first.py")
        save_strategy(conn, name="Second", filename="second.py")

        rows = list_strategies(conn)
        assert len(rows) == 2
        conn.close()

    def test_get_strategy_not_found(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        assert get_strategy(conn, 999) is None
        conn.close()

    def test_delete_strategy(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        sid = save_strategy(conn, name="To Delete", filename="del.py")
        assert delete_strategy(conn, sid)
        assert get_strategy(conn, sid) is None
        conn.close()

    def test_delete_nonexistent(self, tmp_path: Path) -> None:
        conn = get_db(tmp_path / "test.db")
        assert not delete_strategy(conn, 999)
        conn.close()
