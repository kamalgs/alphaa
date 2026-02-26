"""CSV export for trade logs."""

from __future__ import annotations

import csv
from pathlib import Path

from alphaa.core.types import Trade


def export_trade_log(trades: list[Trade], path: str | Path) -> None:
    """Write trade log to CSV file."""
    fieldnames = [
        "symbol",
        "entry_date",
        "entry_price",
        "exit_date",
        "exit_price",
        "quantity",
        "pnl",
        "return_pct",
        "holding_days",
    ]

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for trade in trades:
            writer.writerow(
                {
                    "symbol": trade.symbol,
                    "entry_date": trade.entry.date,
                    "entry_price": f"{trade.entry.price:.2f}",
                    "exit_date": trade.exit.date,
                    "exit_price": f"{trade.exit.price:.2f}",
                    "quantity": trade.entry.quantity,
                    "pnl": f"{trade.pnl:.2f}",
                    "return_pct": f"{trade.return_pct:.4f}",
                    "holding_days": trade.holding_days,
                }
            )
