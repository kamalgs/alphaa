"""CLI entry point for AlphaA."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from alphaa.core.types import DateRange
from alphaa.data.cache import CachingProvider
from alphaa.data.yahoo import YahooFinanceProvider
from alphaa.reporting.charts import plot_equity_curve, plot_trades_on_price
from alphaa.reporting.cli_output import print_summary
from alphaa.reporting.csv_export import export_trade_log
from alphaa.service.backtest_service import BacktestRequest, run_backtest


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="alphaa",
        description="AlphaA — Backtest trading strategies on Indian equities",
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Stock symbol (e.g., RELIANCE.NS)",
    )
    parser.add_argument(
        "--start",
        default="2019-01-01",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        default="2024-01-01",
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=100_000.0,
        help="Starting capital (default: 100000)",
    )
    parser.add_argument(
        "--entry-pct",
        type=float,
        default=5.0,
        help="Entry threshold: %% within 52-week low (default: 5)",
    )
    parser.add_argument(
        "--exit-pct",
        type=float,
        default=5.0,
        help="Exit threshold: %% within 52-week high (default: 5)",
    )
    parser.add_argument(
        "--stop-loss",
        type=float,
        default=10.0,
        help="Stop loss %% below entry (default: 10)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for CSV and chart output",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable data caching",
    )
    return parser.parse_args(args)


def main(args: list[str] | None = None) -> None:
    parsed = parse_args(args)

    request = BacktestRequest(
        symbol=parsed.symbol,
        start_date=date.fromisoformat(parsed.start),
        end_date=date.fromisoformat(parsed.end),
        capital=parsed.capital,
        entry_pct=parsed.entry_pct,
        exit_pct=parsed.exit_pct,
        stop_loss_pct=parsed.stop_loss,
        use_cache=not parsed.no_cache,
    )

    response = run_backtest(request)
    result = response.result
    metrics = response.metrics

    print_summary(metrics, result)

    # --- Output files ---
    if parsed.output_dir:
        output_dir = Path(parsed.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_path = output_dir / f"{parsed.symbol}_trades.csv"
        export_trade_log(result.trade_log, csv_path)
        print(f"  Trade log: {csv_path}")

        equity_path = output_dir / f"{parsed.symbol}_equity.png"
        plot_equity_curve(result, output_path=equity_path)
        print(f"  Equity curve: {equity_path}")

        yahoo: YahooFinanceProvider | CachingProvider = YahooFinanceProvider()
        provider = CachingProvider(yahoo) if request.use_cache else yahoo
        date_range = DateRange(request.start_date, request.end_date)
        ohlcv = provider.fetch_ohlcv(parsed.symbol, date_range)
        trades_path = output_dir / f"{parsed.symbol}_trades.png"
        plot_trades_on_price(result, ohlcv, output_path=trades_path)
        print(f"  Trade chart: {trades_path}")


if __name__ == "__main__":
    main()
