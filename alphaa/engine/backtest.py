"""Backtesting engine — the bar-by-bar simulation loop."""

from __future__ import annotations

import pandas as pd

from alphaa.broker.paper import PaperBroker
from alphaa.core.types import (
    BacktestConfig,
    BacktestResult,
    Bar,
    Context,
    Fill,
    Order,
    PortfolioSnapshot,
    PortfolioState,
    Position,
    Side,
    Trade,
)
from alphaa.engine.cost_models import ZeroCostModel


class BacktestEngine:
    """Run a strategy over historical data and produce a BacktestResult."""

    def run(self, config: BacktestConfig) -> BacktestResult:
        # --- Resolve defaults ---
        provider = config.data_provider
        if provider is None:
            raise ValueError("data_provider is required")

        broker = config.broker
        if broker is None:
            broker = PaperBroker()

        cost_model = config.cost_model
        if cost_model is None:
            cost_model = ZeroCostModel()

        strategy = config.strategy

        # --- Fetch data ---
        ohlcv = provider.fetch_ohlcv(config.symbol, config.date_range)

        # --- Pre-compute indicators ---
        indicators: dict[str, pd.Series] = {}
        for ind in strategy.indicators:
            series = ind(ohlcv)
            indicators[ind.__name__] = series

        # --- Initialize portfolio ---
        portfolio = PortfolioState(cash=config.starting_capital)
        trade_log: list[Trade] = []
        equity_curve: list[PortfolioSnapshot] = []
        pending_entry: Fill | None = None

        # --- Bar-by-bar loop ---
        for i in range(len(ohlcv)):
            row = ohlcv.iloc[i]
            bar_date = ohlcv.index[i]
            if isinstance(bar_date, pd.Timestamp):
                bar_date = bar_date.date()

            bar = Bar(
                symbol=config.symbol,
                date=bar_date,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]),
            )

            # Slice history and indicators up to current bar (no lookahead)
            history = ohlcv.iloc[: i + 1]
            sliced_indicators = {
                k: v.iloc[: i + 1] for k, v in indicators.items()
            }

            ctx = Context(
                current_bar=bar,
                history=history,
                portfolio=portfolio,
                indicators=sliced_indicators,
                params=strategy.params,
            )

            # Set broker state
            if isinstance(broker, PaperBroker):
                broker.set_current_bar(bar_date, bar.close)

            # --- Entry logic ---
            symbol = config.symbol
            if symbol not in portfolio.positions and strategy.entry(ctx):
                # Determine quantity: invest all available cash
                quantity = int(portfolio.cash // bar.close)
                if quantity > 0:
                    order = Order(symbol=symbol, side=Side.BUY, quantity=quantity)
                    fees = cost_model.compute_fees(order, bar.close)
                    if isinstance(broker, PaperBroker):
                        broker.set_fees(fees)
                    fill = broker.place_order(order)

                    # Update portfolio
                    portfolio.cash -= fill.price * fill.quantity + fill.fees
                    portfolio.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=fill.quantity,
                        avg_cost=fill.price,
                        lots=[fill],
                    )
                    pending_entry = fill

            # --- Exit logic ---
            elif symbol in portfolio.positions and strategy.exit(ctx):
                pos = portfolio.positions[symbol]
                order = Order(symbol=symbol, side=Side.SELL, quantity=pos.quantity)
                fees = cost_model.compute_fees(order, bar.close)
                if isinstance(broker, PaperBroker):
                    broker.set_fees(fees)
                fill = broker.place_order(order)

                # Record trade
                if pending_entry is not None:
                    trade = Trade(symbol=symbol, entry=pending_entry, exit=fill)
                    trade_log.append(trade)
                    pending_entry = None

                # Update portfolio
                portfolio.cash += fill.price * fill.quantity - fill.fees
                del portfolio.positions[symbol]

            # Record equity
            prices = {symbol: bar.close}
            equity_curve.append(portfolio.snapshot(bar_date, prices))

        # --- Compute benchmark (buy-and-hold) ---
        benchmark_curve = self._compute_benchmark(
            ohlcv, config.starting_capital, config.symbol
        )

        return BacktestResult(
            strategy_name=strategy.name,
            symbol=config.symbol,
            date_range=config.date_range,
            starting_capital=config.starting_capital,
            trade_log=trade_log,
            equity_curve=equity_curve,
            benchmark_curve=benchmark_curve,
        )

    def _compute_benchmark(
        self,
        ohlcv: pd.DataFrame,
        starting_capital: float,
        symbol: str,
    ) -> list[PortfolioSnapshot]:
        """Buy-and-hold benchmark: buy on day 1, hold until the end."""
        first_close = float(ohlcv.iloc[0]["close"])
        quantity = int(starting_capital // first_close)
        remaining_cash = starting_capital - quantity * first_close

        curve: list[PortfolioSnapshot] = []
        for i in range(len(ohlcv)):
            bar_date = ohlcv.index[i]
            if isinstance(bar_date, pd.Timestamp):
                bar_date = bar_date.date()
            close = float(ohlcv.iloc[i]["close"])
            holdings = quantity * close
            curve.append(
                PortfolioSnapshot(
                    date=bar_date,
                    cash=remaining_cash,
                    holdings_value=holdings,
                    total_value=remaining_cash + holdings,
                )
            )
        return curve
