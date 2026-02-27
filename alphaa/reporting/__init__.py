"""Reporting — metrics, CLI output, CSV export, charts."""

from alphaa.reporting.charts import plot_equity_curve, plot_trades_on_price
from alphaa.reporting.cli_output import print_summary
from alphaa.reporting.csv_export import export_trade_log
from alphaa.reporting.metrics import compute_metrics

__all__ = [
    "compute_metrics",
    "export_trade_log",
    "plot_equity_curve",
    "plot_trades_on_price",
    "print_summary",
]
