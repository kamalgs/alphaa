"""Route handlers for the AlphaA web app."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from alphaa.reporting.charts import plot_equity_curve, plot_trades_on_price
from alphaa.service.backtest_service import BacktestRequest, run_backtest
from alphaa.strategies.loader import (
    StrategyLoadError,
    load_strategy,
    save_strategy_file,
    validate_strategy_source,
)
from alphaa.web.db import (
    DEFAULT_DB_PATH,
    get_db,
    get_leaderboard,
    get_run,
    get_strategy,
    list_strategies,
    save_run,
    save_strategy,
)

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
def index(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(_get_db)],
) -> HTMLResponse:
    """Render the backtest form with strategy dropdown."""
    strategies = list_strategies(conn)
    conn.close()
    return _render(
        request,
        "index.html",
        {"request": request, "active_page": "index", "strategies": strategies},
    )


@router.post("/run", response_model=None)
def run(
    request: Request,
    symbol: Annotated[str, Form()],
    start: Annotated[str, Form()],
    end: Annotated[str, Form()],
    capital: Annotated[float, Form()],
    strategy_id: Annotated[str, Form()],
    strategy_params: Annotated[str, Form()],
    conn: Annotated[sqlite3.Connection, Depends(_get_db)],
) -> RedirectResponse | HTMLResponse:
    """Execute a backtest, save to DB, redirect to result page."""
    strategies = list_strategies(conn)

    # Parse strategy params JSON
    try:
        params: dict[str, Any] = json.loads(strategy_params) if strategy_params.strip() else {}
    except json.JSONDecodeError as exc:
        return _render(
            request,
            "index.html",
            {
                "request": request,
                "active_page": "index",
                "strategies": strategies,
                "error": f"Invalid strategy params JSON: {exc}",
                "symbol": symbol,
                "start": start,
                "end": end,
                "capital": capital,
                "strategy_id": strategy_id,
                "strategy_params": strategy_params,
            },
        )

    try:
        bt_request = BacktestRequest(
            symbol=symbol,
            start_date=date.fromisoformat(start),
            end_date=date.fromisoformat(end),
            capital=capital,
            entry_pct=float(params.get("entry_pct", 5.0)),
            exit_pct=float(params.get("exit_pct", 5.0)),
            stop_loss_pct=float(params.get("stop_loss_pct", 10.0)),
        )

        strategy_source = "builtin"
        custom_strategy = None

        if strategy_id != "builtin":
            db_strategy = get_strategy(conn, int(strategy_id))
            if db_strategy is None:
                raise ValueError(f"Strategy #{strategy_id} not found")  # noqa: TRY301
            from alphaa.strategies.loader import STRATEGIES_DIR

            filepath = STRATEGIES_DIR / db_strategy.filename
            custom_strategy = load_strategy(filepath, params=params)
            strategy_source = f"custom:{db_strategy.filename}"

        response = run_backtest(bt_request, strategy=custom_strategy)
    except (ValueError, StrategyLoadError) as exc:
        return _render(
            request,
            "index.html",
            {
                "request": request,
                "active_page": "index",
                "strategies": strategies,
                "error": str(exc),
                "symbol": symbol,
                "start": start,
                "end": end,
                "capital": capital,
                "strategy_id": strategy_id,
                "strategy_params": strategy_params,
            },
        )
    except Exception as exc:
        return _render(
            request,
            "index.html",
            {
                "request": request,
                "active_page": "index",
                "strategies": strategies,
                "error": str(exc),
                "symbol": symbol,
                "start": start,
                "end": end,
                "capital": capital,
                "strategy_id": strategy_id,
                "strategy_params": strategy_params,
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
        entry_pct=bt_request.entry_pct,
        exit_pct=bt_request.exit_pct,
        stop_loss_pct=bt_request.stop_loss_pct,
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
        strategy_source=strategy_source,
        strategy_params_json=json.dumps(params),
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


# --- Strategy management routes ---


@router.get("/strategies", response_class=HTMLResponse)
def strategies_page(
    request: Request,
    conn: Annotated[sqlite3.Connection, Depends(_get_db)],
) -> HTMLResponse:
    """List uploaded strategies."""
    strategies = list_strategies(conn)
    conn.close()
    return _render(
        request,
        "strategies.html",
        {"request": request, "active_page": "strategies", "strategies": strategies},
    )


@router.post("/strategies/upload", response_model=None)
def upload_strategy(
    request: Request,
    name: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    conn: Annotated[sqlite3.Connection, Depends(_get_db)],
    description: Annotated[str, Form()] = "",
) -> RedirectResponse | HTMLResponse:
    """Upload a .py strategy file, validate it, and save to disk + DB."""
    strategies = list_strategies(conn)

    if not file.filename or not file.filename.endswith(".py"):
        return _render(
            request,
            "strategies.html",
            {
                "request": request,
                "active_page": "strategies",
                "strategies": strategies,
                "error": "File must be a .py file.",
                "name": name,
                "description": description,
            },
        )

    content = file.file.read().decode("utf-8")

    errors = validate_strategy_source(content)
    if errors:
        return _render(
            request,
            "strategies.html",
            {
                "request": request,
                "active_page": "strategies",
                "strategies": strategies,
                "error": "; ".join(errors),
                "name": name,
                "description": description,
            },
        )

    filename = file.filename
    save_strategy_file(filename, content)
    save_strategy(conn, name=name, filename=filename, description=description)
    conn.close()

    return RedirectResponse(url="/strategies", status_code=303)
