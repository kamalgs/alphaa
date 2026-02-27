"""Route handlers for the AlphaA web app."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from alphaa.reporting.charts import plot_equity_curve, plot_trades_on_price
from alphaa.service.backtest_service import BacktestRequest, run_backtest
from alphaa.web.db import DEFAULT_DB_PATH, get_db, get_leaderboard, get_run, save_run

router = APIRouter()

STATIC_DIR = Path("~/.alphaa/web/static").expanduser()


def _get_db() -> sqlite3.Connection:
    """Dependency that provides a DB connection."""
    return get_db(DEFAULT_DB_PATH)


def _render(request: Request, template: str, context: dict[str, Any]) -> HTMLResponse:
    """Render a Jinja2 template, returning HTMLResponse."""
    templates = request.app.state.templates
    resp: Any = templates.TemplateResponse(template, context)
    return resp  # type: ignore[no-any-return]


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """Render the backtest form."""
    return _render(request, "index.html", {"request": request, "active_page": "index"})


@router.post("/run", response_model=None)
def run(
    request: Request,
    symbol: Annotated[str, Form()],
    start: Annotated[str, Form()],
    end: Annotated[str, Form()],
    capital: Annotated[float, Form()],
    entry_pct: Annotated[float, Form()],
    exit_pct: Annotated[float, Form()],
    stop_loss: Annotated[float, Form()],
    conn: Annotated[sqlite3.Connection, Depends(_get_db)],
) -> RedirectResponse | HTMLResponse:
    """Execute a backtest, save to DB, redirect to result page."""
    try:
        bt_request = BacktestRequest(
            symbol=symbol,
            start_date=date.fromisoformat(start),
            end_date=date.fromisoformat(end),
            capital=capital,
            entry_pct=entry_pct,
            exit_pct=exit_pct,
            stop_loss_pct=stop_loss,
        )
        response = run_backtest(bt_request)
    except Exception as exc:
        return _render(
            request,
            "index.html",
            {
                "request": request,
                "active_page": "index",
                "error": str(exc),
                "symbol": symbol,
                "start": start,
                "end": end,
                "capital": capital,
                "entry_pct": entry_pct,
                "exit_pct": exit_pct,
                "stop_loss": stop_loss,
            },
        )

    result = response.result
    metrics = response.metrics

    # Save to DB first to get the run id
    run_id = save_run(
        conn,
        symbol=symbol,
        start_date=start,
        end_date=end,
        capital=capital,
        entry_pct=entry_pct,
        exit_pct=exit_pct,
        stop_loss_pct=stop_loss,
        strategy_name=result.strategy_name,
        total_return_pct=metrics.total_return_pct,
        cagr_pct=metrics.cagr_pct,
        max_drawdown_pct=metrics.max_drawdown_pct,
        sharpe_ratio=metrics.sharpe_ratio,
        win_rate_pct=metrics.win_rate_pct,
        total_trades=metrics.total_trades,
        avg_holding_days=metrics.avg_holding_days,
        profit_factor=metrics.profit_factor,
        benchmark_return_pct=metrics.benchmark_return_pct,
    )

    # Generate charts
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    equity_filename = f"run_{run_id}_equity.png"
    equity_path = STATIC_DIR / equity_filename
    plot_equity_curve(result, output_path=equity_path)

    trades_filename = f"run_{run_id}_trades.png"
    trades_path = STATIC_DIR / trades_filename
    plot_trades_on_price(result, response.ohlcv, output_path=trades_path)

    # Update DB with chart paths
    conn.execute(
        "UPDATE backtest_runs SET equity_chart_path = ?, trades_chart_path = ? WHERE id = ?",
        (str(equity_path), str(trades_path), run_id),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(url=f"/result/{run_id}", status_code=303)


@router.get("/result/{run_id}", response_class=HTMLResponse)
def result_page(
    request: Request,
    run_id: int,
    conn: Annotated[sqlite3.Connection, Depends(_get_db)],
) -> HTMLResponse:
    """Show metrics and charts for a single run."""
    row = get_run(conn, run_id)
    conn.close()

    if row is None:
        return HTMLResponse(content="Run not found", status_code=404)

    equity_filename = None
    if row.equity_chart_path and Path(row.equity_chart_path).exists():
        equity_filename = Path(row.equity_chart_path).name

    trades_filename = None
    if row.trades_chart_path and Path(row.trades_chart_path).exists():
        trades_filename = Path(row.trades_chart_path).name

    return _render(
        request,
        "result.html",
        {
            "request": request,
            "active_page": "",
            "run": row,
            "equity_chart_filename": equity_filename,
            "trades_chart_filename": trades_filename,
        },
    )


@router.get("/leaderboard", response_class=HTMLResponse)
def leaderboard(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(_get_db)],
) -> HTMLResponse:
    """Table of all runs ranked by CAGR."""
    runs = get_leaderboard(conn)
    conn.close()

    return _render(
        request,
        "leaderboard.html",
        {"request": request, "active_page": "leaderboard", "runs": runs},
    )
