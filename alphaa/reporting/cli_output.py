"""Terminal summary output."""

from __future__ import annotations

from alphaa.core.types import BacktestMetrics, BacktestResult


def print_summary(metrics: BacktestMetrics, result: BacktestResult) -> str:
    """Format and print a terminal summary of backtest results.

    Returns the formatted string (useful for testing).
    """
    lines = [
        "",
        f"  Strategy: {result.strategy_name}",
        f"  Symbol:   {result.symbol}",
        f"  Period:   {result.date_range.start} to {result.date_range.end}",
        f"  Capital:  {result.starting_capital:,.0f}",
        "",
        "  Performance",
        "  -----------",
        f"  Total Return:    {metrics.total_return_pct:+.2f}%",
        f"  CAGR:            {metrics.cagr_pct:+.2f}%",
        f"  Max Drawdown:    {metrics.max_drawdown_pct:.2f}%",
        f"  Sharpe Ratio:    {metrics.sharpe_ratio:.2f}",
        "",
        "  Trades",
        "  ------",
        f"  Total Trades:    {metrics.total_trades}",
        f"  Win Rate:        {metrics.win_rate_pct:.1f}%",
        f"  Avg Holding:     {metrics.avg_holding_days:.0f} days",
        f"  Profit Factor:   {metrics.profit_factor:.2f}",
    ]

    if metrics.benchmark_return_pct is not None:
        lines.append("")
        lines.append(f"  Benchmark:       {metrics.benchmark_return_pct:+.2f}%")

    lines.append("")
    output = "\n".join(lines)
    print(output)
    return output
