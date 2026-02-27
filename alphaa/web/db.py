"""SQLite persistence for backtest runs."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS backtest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    symbol TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    capital REAL NOT NULL,
    entry_pct REAL NOT NULL,
    exit_pct REAL NOT NULL,
    stop_loss_pct REAL NOT NULL,
    strategy_name TEXT NOT NULL,
    total_return_pct REAL NOT NULL,
    cagr_pct REAL NOT NULL,
    max_drawdown_pct REAL NOT NULL,
    sharpe_ratio REAL NOT NULL,
    win_rate_pct REAL NOT NULL,
    total_trades INTEGER NOT NULL,
    avg_holding_days REAL NOT NULL,
    profit_factor REAL NOT NULL,
    benchmark_return_pct REAL,
    equity_chart_path TEXT,
    trades_chart_path TEXT
);
"""

DEFAULT_DB_PATH = Path("~/.alphaa/web.db").expanduser()


@dataclass(frozen=True)
class LeaderboardRow:
    """Typed row for leaderboard queries."""

    id: int
    created_at: str
    symbol: str
    start_date: str
    end_date: str
    capital: float
    entry_pct: float
    exit_pct: float
    stop_loss_pct: float
    strategy_name: str
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate_pct: float
    total_trades: int
    avg_holding_days: float
    profit_factor: float
    benchmark_return_pct: float | None
    equity_chart_path: str | None
    trades_chart_path: str | None


def get_db(path: Path | None = None) -> sqlite3.Connection:
    """Open (or create) the SQLite database and return a connection."""
    db_path = path or DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def save_run(
    conn: sqlite3.Connection,
    *,
    symbol: str,
    start_date: str,
    end_date: str,
    capital: float,
    entry_pct: float,
    exit_pct: float,
    stop_loss_pct: float,
    strategy_name: str,
    total_return_pct: float,
    cagr_pct: float,
    max_drawdown_pct: float,
    sharpe_ratio: float,
    win_rate_pct: float,
    total_trades: int,
    avg_holding_days: float,
    profit_factor: float,
    benchmark_return_pct: float | None = None,
    equity_chart_path: str | None = None,
    trades_chart_path: str | None = None,
) -> int:
    """Insert a backtest run and return its row id."""
    cursor = conn.execute(
        """\
        INSERT INTO backtest_runs (
            symbol, start_date, end_date, capital,
            entry_pct, exit_pct, stop_loss_pct, strategy_name,
            total_return_pct, cagr_pct, max_drawdown_pct, sharpe_ratio,
            win_rate_pct, total_trades, avg_holding_days, profit_factor,
            benchmark_return_pct, equity_chart_path, trades_chart_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            symbol, start_date, end_date, capital,
            entry_pct, exit_pct, stop_loss_pct, strategy_name,
            total_return_pct, cagr_pct, max_drawdown_pct, sharpe_ratio,
            win_rate_pct, total_trades, avg_holding_days, profit_factor,
            benchmark_return_pct, equity_chart_path, trades_chart_path,
        ),
    )
    conn.commit()
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def get_leaderboard(conn: sqlite3.Connection, limit: int = 50) -> list[LeaderboardRow]:
    """Return runs ranked by CAGR (descending)."""
    cursor = conn.execute(
        "SELECT * FROM backtest_runs ORDER BY cagr_pct DESC LIMIT ?",
        (limit,),
    )
    return [LeaderboardRow(*row) for row in cursor.fetchall()]


def get_run(conn: sqlite3.Connection, run_id: int) -> LeaderboardRow | None:
    """Return a single run by id, or None if not found."""
    cursor = conn.execute(
        "SELECT * FROM backtest_runs WHERE id = ?",
        (run_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return LeaderboardRow(*row)
