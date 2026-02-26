# AlphaA - Product Requirements Document

## Vision

A trading platform for Indian equities (NSE/BSE) that enables systematic,
fundamentals-driven delivery-based investing with rigorous backtesting
before real capital deployment.

## Target User

Individual investors who want to define rule-based strategies combining
fundamental stock selection with technical entry/exit timing, validate them
against historical data, and eventually execute them through a broker.

---

## Core Requirements

### R1. Market Data Access

The platform must provide access to the following data for all NSE/BSE listed equities:

| Category | Data Points | Frequency |
|---|---|---|
| **Price** | Open, High, Low, Close, Volume, Adjusted Close | Daily |
| **Fundamental Ratios** | PE, PEG, PB, EV/EBITDA, Dividend Yield | Quarterly / Annual |
| **Profitability Metrics** | ROE, ROCE, Operating Margin, Net Margin, EPS Growth | Quarterly / Annual |
| **Balance Sheet Health** | Debt/Equity, Current Ratio, Interest Coverage | Quarterly / Annual |
| **Technical Indicators** | 52-week High/Low, Moving Averages, RSI, MACD | Derived from price |
| **Corporate Actions** | Splits, Bonuses, Dividends | As-reported |
| **Market Metadata** | Sector, Industry, Market Cap category, Index membership | Periodic |

Users must be able to filter the stock universe by index membership, market cap,
sector, and liquidity.

Data sources must be swappable — the platform should not be locked to any single vendor.

### R2. Strategy Definition

Users must be able to define trading strategies as rules that specify:

- **What to buy** — screening criteria based on fundamental and technical data
- **When to buy/sell** — entry and exit conditions based on price and indicator thresholds
- Strategies must be parameterizable (e.g., "buy within X% of 52-week low" where X is configurable)
- Screening (stock selection) and timing (entry/exit) should be separable concerns
- The platform should ship with a library of common reusable conditions

### R3. Backtesting

Users must be able to test any strategy against historical data to evaluate performance.

**Inputs:**
- Strategy with parameters
- Stock(s) to test on
- Date range
- Starting capital

**Outputs:**
- Performance metrics: total return, CAGR, max drawdown, Sharpe ratio, win rate
- Trade log: every buy/sell with dates, prices, holding period, and per-trade P&L
- Benchmark comparison against Nifty 50 / Sensex

The backtesting engine must support progressively realistic execution modeling —
starting simple and adding slippage, brokerage charges (STT, stamp duty, GST, SEBI fees),
and partial fills over time.

### R4. Reporting & Visualization

Users must be able to review strategy results through:

- **Summary reports** — key metrics displayed in terminal
- **Exportable trade logs** — full trade history in CSV for external analysis
- **Visual charts:**
  - Equity curve vs benchmark
  - Drawdown over time
  - Entry/exit markers on price chart
  - Monthly/yearly returns heatmap

### R5. Trade Execution

The platform must provide a broker-agnostic way to:

- Place and cancel orders (market/limit)
- View order status
- View current positions and holdings
- View portfolio value

First broker target: **Groww**. The platform must also support paper trading
(simulated execution against live/historical prices) for pre-deployment validation.

### R6. Position & P&L Tracking

The platform must track:

- Cost basis with support for averaging across multiple buys
- Realized and unrealized P&L
- Holding period per lot (relevant for LTCG vs STCG — 1 year threshold for Indian equities)
- FIFO-based lot tracking for partial exits
- Daily portfolio value history

### R7. Scenario Simulation

Users must be able to:

- Replay a strategy with modified parameters ("what-if" analysis)
- Run parameter sweeps across a grid of values to find optimal settings
- Perform walk-forward analysis (train on one period, validate on the next)
- Run Monte Carlo simulations of trade sequences (future)

---

## MVP Scope

**Goal:** Enable a user to backtest a simple strategy — "buy near 52-week low,
sell near 52-week high" — on any single NSE/BSE stock and evaluate whether
it would have been profitable.

### MVP Capabilities

1. **Data:** Fetch daily OHLCV for any NSE/BSE stock with local caching
2. **Indicators:** Compute rolling 52-week high and low
3. **Strategy:** Configure a buy-near-low / sell-near-high strategy with adjustable thresholds
4. **Backtest:** Run the strategy over a historical period with a given starting capital
5. **Results:** View performance summary, trade log (terminal + CSV), and equity curve chart with buy/sell markers

### Deferred to Post-MVP

- Live broker integration (Groww)
- Fundamental data ingestion and screening
- Multi-stock / portfolio-level strategies
- Realistic execution modeling (slippage, commissions)
- Web-based UI
- Real-time data streaming
- Monte Carlo and advanced scenario analysis

---

## Success Criteria (MVP)

1. User can backtest on any NSE/BSE stock using at least 5 years of historical data
2. Strategy thresholds (buy/sell proximity to 52-week low/high) are configurable
3. Trade log clearly shows every transaction with dates, prices, and P&L
4. Equity curve chart compares strategy performance against buy-and-hold
5. Adding a new strategy requires minimal effort — just defining the rules
