# AlphaA - Algo Trading Platform for Indian Markets

## Vision

A fundamentals-driven, delivery-based algo trading platform for Indian equities (NSE/BSE).
Enables systematic strategies that combine fundamental screening with technical timing
for entry/exit, with rigorous backtesting before live deployment.

---

## Core Principles

- **Delivery only** - No intraday; all positions are held overnight or longer
- **Fundamentals first** - Stock selection driven by financial ratios and quality metrics
- **Technical timing** - Technical indicators used only for entry/exit timing, not stock picking
- **Backtest before deploy** - Every strategy must be validated through historical simulation
- **Broker-agnostic** - Clean abstraction layer; broker implementations are pluggable
- **Data-source agnostic** - Start with free sources, swap in paid APIs without code changes

---

## High-Level Requirements

### 1. Data Layer

| Category | Data Points | Frequency |
|---|---|---|
| **Price (OHLCV)** | Open, High, Low, Close, Volume, Adj Close | Daily |
| **Fundamental Ratios** | PE, PEG, PB, EV/EBITDA, Dividend Yield | Quarterly / Annual |
| **Profitability** | ROE, ROCE, Operating Margin, Net Margin, EPS growth | Quarterly / Annual |
| **Balance Sheet** | Debt/Equity, Current Ratio, Interest Coverage | Quarterly / Annual |
| **Technical (derived)** | 52-week High/Low, Moving Averages (SMA/EMA), RSI, MACD | Computed from OHLCV |
| **Corporate Actions** | Splits, Bonuses, Dividends (for adjusted price calc) | As-reported |
| **Market Metadata** | Sector, Industry, Market Cap category, Index membership | Periodic |

**Data source strategy:** Free sources initially (Yahoo Finance, NSE/BSE feeds, screener.in).
Abstract behind a `DataProvider` interface so paid sources (CMOTS, Capitaline, broker APIs)
can be plugged in later.

**Stock universe:** Full NSE/BSE listed equities. Filterable by index membership, market cap,
sector, liquidity.

### 2. Strategy Framework

- Declarative strategy definition - define entry/exit rules as composable conditions
- Support both **screening** (which stocks) and **timing** (when to buy/sell) as separate concerns
- Strategy receives market data snapshot and current portfolio state, emits signals (BUY/SELL/HOLD)
- Strategies are plain Python classes implementing a `Strategy` interface
- Built-in library of common conditions (price near 52w low/high, PE below threshold, etc.)

### 3. Backtesting Engine

- Event-driven or vectorized engine that replays historical data day-by-day
- Tracks simulated portfolio: positions, cash, P&L
- **MVP:** Close-price execution, no slippage/commission modeling
- **Later:** Pluggable execution models (slippage, brokerage charges - STT, stamp duty, GST, SEBI fees)
- Supports single-stock strategies (MVP) with portfolio-level planned for later
- Configurable initial capital, date range, and strategy parameters

**Output metrics:**
- Total return, CAGR, max drawdown, Sharpe ratio, win rate
- Trade log with entry/exit dates, prices, holding period, per-trade P&L
- Benchmark comparison (Nifty 50 / Sensex)

### 4. Reporting & Visualization

- **CLI output:** Summary stats, trade log table printed to terminal
- **CSV export:** Full trade log and daily portfolio value for external analysis
- **Charts (Matplotlib/Plotly):**
  - Equity curve vs benchmark
  - Drawdown chart
  - Entry/exit markers on price chart
  - Monthly/yearly returns heatmap

### 5. Broker Abstraction (Interface Only in MVP)

```
BrokerAdapter (interface):
  - place_order(symbol, qty, order_type, price) -> OrderID
  - cancel_order(order_id)
  - get_order_status(order_id) -> OrderStatus
  - get_positions() -> List[Position]
  - get_holdings() -> List[Holding]
  - get_portfolio_value() -> float
```

- First real implementation target: **Groww**
- Paper trading adapter that simulates execution against live prices (pre-live validation)

### 6. Position & P&L Tracking

- Track cost basis (supports averaging on multiple buys)
- Realized vs unrealized P&L
- Holding period tracking (for LTCG/STCG tax classification - 1yr threshold for equity)
- FIFO-based lot tracking for partial exits
- Daily portfolio value snapshots

### 7. Scenario Simulation

- "What-if" analysis: replay strategy with modified parameters
- Parameter sweep: run strategy across a grid of parameter values
- Walk-forward analysis: train on one period, validate on next
- Monte Carlo simulation of trade sequences (planned, not MVP)

---

## MVP Scope

**Goal:** Backtest a simple "buy near 52-week low, sell near 52-week high" strategy
on any single NSE/BSE stock, and see whether it would have made money.

### MVP Deliverables

1. **Data module**
   - Fetch daily OHLCV for any NSE/BSE stock from a free source (Yahoo Finance)
   - Compute 52-week high/low (rolling)
   - Local caching (SQLite or Parquet files) to avoid re-fetching

2. **Strategy interface + sample strategy**
   - `Strategy` base class with `on_data(date, ohlcv, indicators, portfolio) -> Signal`
   - `NearFiftyTwoWeekLowHigh` strategy:
     - BUY when price is within X% of 52-week low
     - SELL when price is within Y% of 52-week high
     - X, Y are configurable parameters

3. **Backtest engine (simple)**
   - Iterate over daily bars, feed to strategy, execute signals at next-day close
   - Track: cash, shares held, portfolio value per day
   - Calculate: total return, CAGR, max drawdown, number of trades, win rate

4. **Output**
   - CLI summary table (printed to terminal)
   - CSV trade log export
   - Equity curve chart (Matplotlib)
   - Price chart with buy/sell markers

5. **Broker abstraction (interface only)**
   - Define `BrokerAdapter` abstract class
   - `BacktestBroker` implementation used by the engine

### MVP Non-Goals (Deferred)

- Live broker integration (Groww)
- Fundamental data ingestion
- Portfolio-level strategies (multi-stock)
- Realistic execution modeling (slippage, commissions)
- Web UI
- Real-time data streaming
- Monte Carlo / advanced scenario analysis

---

## Project Structure (Planned)

```
alphaa/
  core/
    strategy.py         # Strategy base class, Signal enum
    engine.py           # Backtest engine
    portfolio.py        # Position, P&L, lot tracking
    broker.py           # BrokerAdapter interface + BacktestBroker
  data/
    provider.py         # DataProvider interface
    yahoo.py            # Yahoo Finance implementation
    cache.py            # Local data caching
    indicators.py       # Technical indicator computations
  strategies/
    fifty_two_week.py   # MVP sample strategy
  reporting/
    metrics.py          # Performance metrics calculation
    charts.py           # Matplotlib/Plotly visualizations
    export.py           # CSV export
  cli/
    main.py             # CLI entry point
  tests/
```

---

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.11+ |
| Data manipulation | pandas |
| Market data (free) | yfinance |
| Technical indicators | pandas-ta or ta-lib |
| Visualization | matplotlib + plotly |
| Data caching | SQLite / Parquet |
| CLI | click or typer |
| Testing | pytest |

---

## Success Criteria for MVP

1. Can fetch 5 years of daily data for any NSE stock (e.g., `RELIANCE.NS`)
2. Can run the 52-week low/high strategy with configurable thresholds
3. Produces a clear trade log showing every buy/sell with dates, prices, and P&L
4. Generates an equity curve chart showing strategy vs buy-and-hold
5. Backtest runs in under 10 seconds for a single stock over 5 years
6. Code is structured so adding a new strategy requires only implementing one class
