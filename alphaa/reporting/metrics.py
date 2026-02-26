"""Compute backtest performance metrics."""

from __future__ import annotations

import math

from alphaa.core.types import BacktestMetrics, BacktestResult


def compute_metrics(result: BacktestResult) -> BacktestMetrics:
    """Compute all performance metrics from a BacktestResult."""
    trades = result.trade_log
    equity = result.equity_curve
    benchmark = result.benchmark_curve

    total_trades = len(trades)

    # --- Total return ---
    if not equity:
        return _empty_metrics(total_trades, benchmark)

    start_value = result.starting_capital
    end_value = equity[-1].total_value
    total_return_pct = ((end_value - start_value) / start_value) * 100

    # --- CAGR ---
    date_range = result.date_range
    years = (date_range.end - date_range.start).days / 365.25
    if years > 0 and end_value > 0 and start_value > 0:
        cagr_pct = ((end_value / start_value) ** (1 / years) - 1) * 100
    else:
        cagr_pct = 0.0

    # --- Max drawdown ---
    max_drawdown_pct = _compute_max_drawdown(equity)

    # --- Sharpe ratio (daily returns, annualized) ---
    sharpe_ratio = _compute_sharpe(equity)

    # --- Win rate ---
    if total_trades > 0:
        wins = sum(1 for t in trades if t.pnl > 0)
        win_rate_pct = (wins / total_trades) * 100
    else:
        win_rate_pct = 0.0

    # --- Average holding days ---
    if total_trades > 0:
        avg_holding_days = sum(t.holding_days for t in trades) / total_trades
    else:
        avg_holding_days = 0.0

    # --- Profit factor ---
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        profit_factor = float("inf")
    else:
        profit_factor = 0.0

    # --- Benchmark return ---
    benchmark_return_pct: float | None = None
    if benchmark:
        bm_start = benchmark[0].total_value
        bm_end = benchmark[-1].total_value
        if bm_start > 0:
            benchmark_return_pct = ((bm_end - bm_start) / bm_start) * 100

    return BacktestMetrics(
        total_return_pct=total_return_pct,
        cagr_pct=cagr_pct,
        max_drawdown_pct=max_drawdown_pct,
        sharpe_ratio=sharpe_ratio,
        win_rate_pct=win_rate_pct,
        total_trades=total_trades,
        avg_holding_days=avg_holding_days,
        profit_factor=profit_factor,
        benchmark_return_pct=benchmark_return_pct,
    )


def _compute_max_drawdown(equity: list) -> float:  # type: ignore[type-arg]
    """Maximum peak-to-trough percentage decline."""
    if len(equity) < 2:
        return 0.0

    peak = equity[0].total_value
    max_dd = 0.0

    for snap in equity:
        if snap.total_value > peak:
            peak = snap.total_value
        if peak > 0:
            dd = (peak - snap.total_value) / peak * 100
            max_dd = max(max_dd, dd)

    return max_dd


def _compute_sharpe(equity: list, risk_free_rate: float = 0.0) -> float:  # type: ignore[type-arg]
    """Annualized Sharpe ratio from daily returns."""
    if len(equity) < 2:
        return 0.0

    values = [snap.total_value for snap in equity]
    returns = []
    for i in range(1, len(values)):
        if values[i - 1] > 0:
            returns.append(values[i] / values[i - 1] - 1)

    if not returns:
        return 0.0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_return = math.sqrt(variance)

    if std_return == 0:
        return 0.0

    daily_sharpe = (mean_return - risk_free_rate / 252) / std_return
    return daily_sharpe * math.sqrt(252)


def _empty_metrics(total_trades: int, benchmark: list) -> BacktestMetrics:  # type: ignore[type-arg]
    benchmark_return_pct: float | None = None
    if benchmark:
        bm_start = benchmark[0].total_value
        bm_end = benchmark[-1].total_value
        if bm_start > 0:
            benchmark_return_pct = ((bm_end - bm_start) / bm_start) * 100

    return BacktestMetrics(
        total_return_pct=0.0,
        cagr_pct=0.0,
        max_drawdown_pct=0.0,
        sharpe_ratio=0.0,
        win_rate_pct=0.0,
        total_trades=total_trades,
        avg_holding_days=0.0,
        profit_factor=0.0,
        benchmark_return_pct=benchmark_return_pct,
    )
