"""Tests for CSV trade log export."""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from alphaa.core.types import Fill, Side, Trade
from alphaa.reporting.csv_export import export_trade_log


class TestExportTradeLog:
    def test_writes_csv(self, tmp_path: Path) -> None:
        trades = [
            Trade(
                symbol="TEST.NS",
                entry=Fill("TEST.NS", Side.BUY, 100, 100.0, date(2023, 3, 1)),
                exit=Fill("TEST.NS", Side.SELL, 100, 120.0, date(2023, 6, 1)),
            ),
        ]
        output = tmp_path / "trades.csv"
        export_trade_log(trades, output)

        assert output.exists()

        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["symbol"] == "TEST.NS"
        assert rows[0]["entry_price"] == "100.00"
        assert rows[0]["exit_price"] == "120.00"
        assert rows[0]["quantity"] == "100"
        assert rows[0]["pnl"] == "2000.00"
        assert rows[0]["holding_days"] == "92"

    def test_empty_trade_log(self, tmp_path: Path) -> None:
        output = tmp_path / "trades.csv"
        export_trade_log([], output)

        assert output.exists()
        with open(output) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 0

    def test_multiple_trades(self, tmp_path: Path) -> None:
        trades = [
            Trade(
                symbol="A.NS",
                entry=Fill("A.NS", Side.BUY, 50, 100.0, date(2023, 1, 1)),
                exit=Fill("A.NS", Side.SELL, 50, 110.0, date(2023, 2, 1)),
            ),
            Trade(
                symbol="B.NS",
                entry=Fill("B.NS", Side.BUY, 30, 200.0, date(2023, 3, 1)),
                exit=Fill("B.NS", Side.SELL, 30, 190.0, date(2023, 4, 1)),
            ),
        ]
        output = tmp_path / "trades.csv"
        export_trade_log(trades, output)

        with open(output) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["symbol"] == "A.NS"
        assert rows[1]["symbol"] == "B.NS"
