"""Chart generation for backtest results."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from alphaa.core.types import BacktestResult

# Use non-interactive backend for server/CI environments
matplotlib.use("Agg")


def plot_equity_curve(
    result: BacktestResult,
    output_path: str | Path | None = None,
) -> None:
    """Plot equity curve vs benchmark."""
    fig, ax = plt.subplots(figsize=(12, 6))

    dates = [snap.date for snap in result.equity_curve]
    values = [snap.total_value for snap in result.equity_curve]
    ax.plot(dates, values, label=result.strategy_name, linewidth=1.5)  # type: ignore[arg-type]

    if result.benchmark_curve:
        bm_dates = [snap.date for snap in result.benchmark_curve]
        bm_values = [snap.total_value for snap in result.benchmark_curve]
        ax.plot(bm_dates, bm_values, label="Buy & Hold", linewidth=1.5, linestyle="--")  # type: ignore[arg-type]

    ax.set_title(f"{result.strategy_name} — {result.symbol}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_trades_on_price(
    result: BacktestResult,
    ohlcv_df: pd.DataFrame,
    output_path: str | Path | None = None,
) -> None:
    """Plot price chart with buy/sell markers."""
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(ohlcv_df.index, ohlcv_df["close"], label="Close", linewidth=1, color="gray")

    for trade in result.trade_log:
        ax.plot(
            trade.entry.date,  # type: ignore[arg-type]
            trade.entry.price,
            "^",
            color="green",
            markersize=8,
        )
        ax.plot(
            trade.exit.date,  # type: ignore[arg-type]
            trade.exit.price,
            "v",
            color="red",
            markersize=8,
        )

    ax.set_title(f"{result.strategy_name} — {result.symbol} Trades")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150)
    plt.close(fig)
