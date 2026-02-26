# AlphaA — Architecture Design

## Design Philosophy

AlphaA is a **composition framework**. Each component is deliberately trivial
in isolation. The power emerges when pieces snap together — like UNIX pipes,
where `cat | grep | sort | uniq` accomplishes what no single program could.

### Three Axioms

1. **Protocols, not inheritance.** Structural typing via `typing.Protocol` means
   any object that quacks right *is* right. No forced base classes. Trivial to
   mock, trivial to test, trivial to swap.

2. **Data as immutable values.** Market bars, trades, signals — all frozen
   dataclasses. No mutable state leaking between components. The engine owns
   the clock; everything else is pure computation.

3. **Composition via code, not configuration.** A strategy is Python code that
   reads like a sentence. No YAML schemas to learn. The user's IDE gives
   autocompletion and type checking for free.

---

## Core Abstractions (`core/`)

`core/` depends on nothing. It defines the vocabulary every other module speaks.

### Value Types (`core/types.py`)

All domain objects are frozen dataclasses. Immutability prevents an entire class
of bugs where components accidentally share and mutate state.

```python
class Side(Enum):
    BUY = auto()
    SELL = auto()

class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()

class OrderStatus(Enum):
    PENDING = auto()
    FILLED = auto()
    CANCELLED = auto()
    REJECTED = auto()
```

```python
@dataclass(frozen=True)
class Bar:
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: float | None = None

@dataclass(frozen=True)
class Signal:
    symbol: str
    side: Side
    date: date
    reason: str = ""

@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None

@dataclass(frozen=True)
class Fill:
    symbol: str
    side: Side
    quantity: int
    price: float
    date: date
    fees: float = 0.0

@dataclass(frozen=True)
class Trade:
    symbol: str
    entry: Fill
    exit: Fill

    @property
    def pnl(self) -> float:
        return (self.exit.price - self.entry.price) * self.entry.quantity - self.entry.fees - self.exit.fees

    @property
    def holding_days(self) -> int:
        return (self.exit.date - self.entry.date).days

    @property
    def return_pct(self) -> float:
        return (self.exit.price - self.entry.price) / self.entry.price
```

```python
@dataclass(frozen=True)
class PortfolioSnapshot:
    date: date
    cash: float
    holdings_value: float
    total_value: float

class DateRange(NamedTuple):
    start: date
    end: date
```

**Portfolio state** is the one deliberately mutable type. It is owned exclusively
by the engine and updated only through fills:

```python
@dataclass
class Position:
    symbol: str
    quantity: int
    avg_cost: float
    lots: list[Fill]    # FIFO lot tracking for tax purposes

@dataclass
class PortfolioState:
    cash: float
    positions: dict[str, Position]    # symbol -> Position

    def snapshot(self, date: date, prices: dict[str, float]) -> PortfolioSnapshot:
        holdings = sum(
            pos.quantity * prices.get(pos.symbol, pos.avg_cost)
            for pos in self.positions.values()
        )
        return PortfolioSnapshot(
            date=date, cash=self.cash,
            holdings_value=holdings, total_value=self.cash + holdings,
        )
```

**Design decisions on types:**

| Decision | Rationale |
|----------|-----------|
| `float` not `Decimal` for prices | Backtesting is analytical, not accounting. Convert at broker boundary if needed. |
| `Signal` is strategy output, not order | Says *what* to do, not *how*. The engine decides quantity and order type. |
| `Trade` has computed properties only | Value object. No methods that mutate state. |
| `PortfolioState` is mutable | Portfolio state *must* change as fills arrive. Contained exclusively within the engine. |

### Context — The Key Insight (`core/types.py`)

Every condition in AlphaA receives one argument: a `Context`. This uniformity
is what makes `&`, `|`, `~` composition work.

```python
@dataclass(frozen=True)
class Context:
    current_bar: Bar
    history: pd.DataFrame           # OHLCV up to and including today (no lookahead)
    portfolio: PortfolioState       # Current cash, positions
    indicators: dict[str, pd.Series]  # Pre-computed, keyed by name
    params: dict[str, object]       # Strategy-level parameters

    @property
    def date(self) -> date:
        return self.current_bar.date

    @property
    def close(self) -> float:
        return self.current_bar.close

    @property
    def symbol(self) -> str:
        return self.current_bar.symbol
```

**Why a single Context?**

- **Uniform signature** — every Condition is `(Context) -> bool`. This is what
  enables boolean composition.
- **No lookahead by construction** — `history` is sliced by the engine to only
  include data up to and including the current bar's date.
- **Indicator pre-computation** — indicators are computed once over the full
  DataFrame, then sliced per bar. Conditions access values via
  `ctx.indicators["sma_50"]` rather than recomputing every bar.
- **Extensible without changing signatures** — when fundamental data is added,
  it goes into Context. No condition signatures change.

### Protocols (`core/protocols.py`)

Structural typing — any object with the right shape satisfies the protocol.

```python
class DataProvider(Protocol):
    def fetch_ohlcv(self, symbol: str, date_range: DateRange) -> pd.DataFrame: ...
    def fetch_symbols(self, index: str | None = None) -> list[str]: ...

class Broker(Protocol):
    def place_order(self, order: Order) -> Fill: ...
    def cancel_order(self, order_id: str) -> bool: ...
    def get_positions(self) -> dict[str, Position]: ...
    def get_portfolio_value(self) -> float: ...

class CostModel(Protocol):
    def compute_fees(self, order: Order, fill_price: float) -> float: ...
```

### Indicator Type

No class hierarchy. Just a callable:

```python
Indicator = Callable[[pd.DataFrame], pd.Series]
```

---

## Composable Conditions — The Design Centerpiece

The condition system is where AlphaA's composability comes alive.

### The `@condition` Decorator (`core/conditions.py`)

A decorator that transforms a plain function into a composable `Condition`
object with `&`, `|`, `~` operators:

```python
class ConditionBase:
    def __and__(self, other):   return _And(self, other)
    def __or__(self, other):    return _Or(self, other)
    def __invert__(self):       return _Not(self)

class _And(ConditionBase):
    def __init__(self, left, right):
        self._left, self._right = left, right
    def __call__(self, ctx: Context) -> bool:
        return self._left(ctx) and self._right(ctx)
    def __repr__(self):
        return f"({self._left!r} & {self._right!r})"

class _Or(ConditionBase):
    def __init__(self, left, right):
        self._left, self._right = left, right
    def __call__(self, ctx: Context) -> bool:
        return self._left(ctx) or self._right(ctx)

class _Not(ConditionBase):
    def __init__(self, inner):
        self._inner = inner
    def __call__(self, ctx: Context) -> bool:
        return not self._inner(ctx)
```

The decorator itself uses `ParamSpec` to preserve parameter types:

```python
P = ParamSpec("P")

def condition(fn: Callable[Concatenate[Context, P], bool]) -> Callable[P, ConditionBase]:
    @wraps(fn)
    def factory(*args: P.args, **kwargs: P.kwargs) -> ConditionBase:
        class _Cond(ConditionBase):
            def __call__(self, ctx: Context) -> bool:
                return fn(ctx, *args, **kwargs)
            def __repr__(self) -> str:
                params = ", ".join(
                    [repr(a) for a in args] +
                    [f"{k}={v!r}" for k, v in kwargs.items()]
                )
                return f"{fn.__name__}({params})"
        return _Cond()
    return factory
```

**What `@condition` achieves:**

- **Parameterization** — `price_near_52w_low(within_pct=5)` captures the
  parameter and returns a `Condition` object.
- **Composition** — the returned object has `__and__`, `__or__`, `__invert__`.
- **Introspection** — `repr()` shows readable condition trees for debugging.
- **Type safety** — `ParamSpec` preserves IDE autocompletion.

### Built-in Condition Library (`conditions/`)

Conditions are organized by domain:

```python
# conditions/price.py
@condition
def price_near_52w_low(ctx: Context, within_pct: float = 5.0) -> bool:
    low_52w = ctx.indicators["low_252"].iloc[-1]
    return ctx.close <= low_52w * (1 + within_pct / 100)

@condition
def price_near_52w_high(ctx: Context, within_pct: float = 5.0) -> bool:
    high_52w = ctx.indicators["high_252"].iloc[-1]
    return ctx.close >= high_52w * (1 - within_pct / 100)

@condition
def price_above_sma(ctx: Context, period: int = 50) -> bool:
    return ctx.close > ctx.indicators[f"sma_{period}"].iloc[-1]

# conditions/position.py
@condition
def has_no_position(ctx: Context) -> bool:
    return ctx.symbol not in ctx.portfolio.positions

@condition
def has_position(ctx: Context) -> bool:
    return ctx.symbol in ctx.portfolio.positions

@condition
def stop_loss(ctx: Context, pct: float = 10.0) -> bool:
    pos = ctx.portfolio.positions.get(ctx.symbol)
    if pos is None:
        return False
    return ctx.close <= pos.avg_cost * (1 - pct / 100)

# conditions/volume.py
@condition
def volume_above_avg(ctx: Context, periods: int = 20, multiplier: float = 1.0) -> bool:
    avg_vol = ctx.history["volume"].tail(periods).mean()
    return ctx.current_bar.volume > avg_vol * multiplier
```

### Strategy = Entry + Exit + Indicators (`core/strategy.py`)

```python
@dataclass(frozen=True)
class Strategy:
    name: str
    entry: Condition
    exit: Condition
    indicators: list[Indicator] = field(default_factory=list)
    params: dict[str, object] = field(default_factory=dict)
```

Usage reads like a sentence:

```python
strategy = Strategy(
    name="buy-low-sell-high",
    entry=price_near_52w_low(within_pct=5) & has_no_position(),
    exit=price_near_52w_high(within_pct=5) & has_position() | stop_loss(pct=10),
    indicators=[rolling_high(252), rolling_low(252)],
)
```

---

## Indicators (`indicators/`)

Indicators are factory functions that return `Callable[[DataFrame], Series]`.
No class hierarchy. Depend on `pandas` only.

```python
# indicators/price.py
def sma(period: int) -> Indicator:
    def compute(df: pd.DataFrame) -> pd.Series:
        return df["close"].rolling(window=period).mean()
    compute.__name__ = f"sma_{period}"
    return compute

def ema(period: int) -> Indicator:
    def compute(df: pd.DataFrame) -> pd.Series:
        return df["close"].ewm(span=period, adjust=False).mean()
    compute.__name__ = f"ema_{period}"
    return compute

def rolling_high(period: int) -> Indicator:
    def compute(df: pd.DataFrame) -> pd.Series:
        return df["high"].rolling(window=period).max()
    compute.__name__ = f"high_{period}"
    return compute

def rolling_low(period: int) -> Indicator:
    def compute(df: pd.DataFrame) -> pd.Series:
        return df["low"].rolling(window=period).min()
    compute.__name__ = f"low_{period}"
    return compute
```

Composite indicators return lists:

```python
# indicators/price.py
def bollinger_bands(period: int = 20, std_dev: float = 2.0) -> list[Indicator]:
    def upper(df): ...
    def lower(df): ...
    return [sma(period), upper, lower]
```

---

## Module Structure & Dependencies

```
alphaa/
    __init__.py
    core/                       # The "language" — types, protocols, composition
        __init__.py
        types.py                # Bar, Signal, Order, Fill, Trade, Context, PortfolioState, ...
        protocols.py            # DataProvider, Broker, CostModel, Indicator type alias
        conditions.py           # Condition protocol, ConditionBase, @condition, _And/_Or/_Not
        strategy.py             # Strategy dataclass

    conditions/                 # Built-in condition library
        __init__.py
        price.py                # price_near_52w_low, price_near_52w_high, price_above_sma
        volume.py               # volume_above_avg, volume_spike
        position.py             # has_position, has_no_position, stop_loss, take_profit
        fundamental.py          # (post-MVP) pe_below, roe_above, debt_equity_below

    indicators/                 # Indicator functions (DataFrame -> Series)
        __init__.py
        price.py                # sma, ema, rolling_high, rolling_low, bollinger_bands
        momentum.py             # rsi, macd, rate_of_change
        volume.py               # volume_sma, obv, vwap

    data/                       # DataProvider implementations
        __init__.py
        yahoo.py                # YahooFinanceProvider (MVP)
        cache.py                # CachingProvider (decorator around any provider)

    engine/                     # The backtesting engine
        __init__.py
        backtest.py             # BacktestEngine: bar loop, context construction, signal handling
        cost_models.py          # ZeroCostModel, IndianEquityCostModel (post-MVP)

    broker/                     # Broker implementations
        __init__.py
        paper.py                # PaperBroker (simulated fills for backtesting)
        groww.py                # (post-MVP) GrowwBroker

    reporting/                  # Output and visualization
        __init__.py
        metrics.py              # Compute return, CAGR, drawdown, Sharpe, win rate
        cli.py                  # Terminal summary output
        csv_export.py           # Trade log CSV export
        charts.py               # Equity curve, drawdown, entry/exit markers (matplotlib)

    cli/                        # Command-line interface
        __init__.py
        main.py                 # Entry point, argument parsing, wiring
```

### Dependency Rules

| Module | Depends On | Responsibility |
|--------|------------|----------------|
| `core/` | Nothing | Define vocabulary: types, protocols, condition composition |
| `conditions/` | `core/` only | Library of reusable `@condition` functions |
| `indicators/` | `pandas` only | Library of indicator functions `(DataFrame -> Series)` |
| `data/` | `core/` | Fetch and cache market data |
| `engine/` | `core/` | Bar-by-bar simulation loop |
| `broker/` | `core/` | Order execution (simulated or live) |
| `reporting/` | `core/` | Compute metrics, format output, render charts |
| `cli/` | Everything | Composition root — wires all modules together |

The dependency graph is strictly layered: `core/` depends on nothing, domain
modules depend only on `core/`, and `cli/` is the composition root. No circular
dependencies. No module reaches into another module's internals.

---

## Data Flow

```
1. CLI parses arguments
        │
        ▼
2. DataProvider.fetch_ohlcv(symbol, date_range)
        │
        ▼
3. Raw OHLCV DataFrame
        │
        ▼
4. Engine pre-computes indicators:
        for indicator in strategy.indicators:
            indicators[indicator.__name__] = indicator(ohlcv_df)
        │
        ▼
5. Bar-by-bar loop:
        for each bar:
            history  = ohlcv_df up to current date
            sliced   = {k: v[:current_date] for k, v in indicators}
            ctx      = Context(bar, history, portfolio, sliced)

            if not in position and strategy.entry(ctx):
                → Signal(BUY) → Order → broker.place_order() → Fill → update portfolio
            if in position and strategy.exit(ctx):
                → Signal(SELL) → Order → broker.place_order() → Fill → record Trade

            equity_curve.append(portfolio.snapshot())
        │
        ▼
6. BacktestResult(trade_log, equity_curve, benchmark_curve)
        │
        ▼
7. Reporting:
        metrics = compute_metrics(result)
        print_summary(metrics)
        export_csv(result.trade_log)
        plot_equity_curve(result)
```

### Result Types

```python
@dataclass(frozen=True)
class BacktestResult:
    strategy_name: str
    symbol: str
    date_range: DateRange
    starting_capital: float
    trade_log: list[Trade]
    equity_curve: list[PortfolioSnapshot]
    benchmark_curve: list[PortfolioSnapshot]

@dataclass(frozen=True)
class BacktestMetrics:
    total_return_pct: float
    cagr_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    win_rate_pct: float
    total_trades: int
    avg_holding_days: float
    profit_factor: float
    benchmark_return_pct: float | None

@dataclass
class BacktestConfig:
    strategy: Strategy
    symbol: str
    date_range: DateRange
    starting_capital: float = 100_000.0
    data_provider: DataProvider = ...
    broker: Broker = ...
    cost_model: CostModel = ...
    benchmark_symbol: str | None = None
```

---

## Extension Points

The MVP design is deliberately minimal, but every extension follows the same
pattern: implement a protocol, pass it in.

### Multi-Stock Strategies

- `BacktestConfig.symbols: list[str]` instead of single symbol
- Engine fetches data for all symbols, runs conditions per-symbol
- `Context` gains `universe: dict[str, DataFrame]` for cross-stock conditions
- No existing code changes — just new code paths

### Screening + Timing Separation

```python
@dataclass(frozen=True)
class Strategy:
    name: str
    screen: Condition | None    # "Which stocks?" — evaluated across universe
    entry: Condition             # "When to buy?" — evaluated per-stock
    exit: Condition              # "When to sell?" — evaluated per-stock
    indicators: list[Indicator] = field(default_factory=list)
    params: dict[str, object] = field(default_factory=dict)
```

### Parameter Sweeps

Because strategies are built from code with explicit parameters, sweeps are
just loops:

```python
for entry_pct in [3, 5, 7, 10]:
    for exit_pct in [3, 5, 7, 10]:
        strategy = Strategy(
            entry=price_near_52w_low(within_pct=entry_pct) & has_no_position(),
            exit=price_near_52w_high(within_pct=exit_pct) & has_position(),
            ...
        )
        result = BacktestEngine().run(BacktestConfig(strategy=strategy, ...))
```

### Plugin Registry (Future)

```python
_conditions: dict[str, Callable] = {}
_indicators: dict[str, Callable] = {}

def register_condition(name: str):
    def decorator(fn):
        _conditions[name] = fn
        return fn
    return decorator
```

Deferred — MVP does not need dynamic discovery. Direct imports are clearer and
more type-safe.

---

## Implementation Order

17 files in dependency order. Each is independently testable.

| # | File | What to Test |
|---|------|-------------|
| 1 | `core/types.py` | Instantiation, frozen enforcement, computed properties |
| 2 | `core/conditions.py` | Composition, `&`/`|`/`~` operators, `@condition` decorator |
| 3 | `core/protocols.py` | Type declarations only — no tests needed |
| 4 | `core/strategy.py` | Dataclass construction |
| 5 | `indicators/price.py` | Known-input/known-output on small DataFrames |
| 6 | `conditions/price.py` | With mock Context |
| 7 | `conditions/position.py` | With mock Context |
| 8 | `data/yahoo.py` | Integration test (real API or recorded fixture) |
| 9 | `data/cache.py` | Cache miss delegates, cache hit reads file |
| 10 | `broker/paper.py` | Order → Fill at expected price |
| 11 | `engine/backtest.py` | Known OHLCV data → expected trades |
| 12 | `engine/cost_models.py` | Zero fees, fee calculation |
| 13 | `reporting/metrics.py` | Known trade log → expected metrics |
| 14 | `reporting/cli.py` | Snapshot or visual verification |
| 15 | `reporting/csv_export.py` | Write and read back |
| 16 | `reporting/charts.py` | Smoke tests (no exceptions on valid data) |
| 17 | `cli/main.py` | End-to-end integration with cached data |

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pandas` | DataFrame for OHLCV data, indicator computation |
| `yfinance` | Yahoo Finance data fetching (MVP data source) |
| `matplotlib` | Charts (equity curve, drawdown, trade markers) |
| `click` or `argparse` | CLI argument parsing |

No heavy frameworks. No ORMs. No async (backtesting is batch computation).
The dependency footprint is deliberately minimal.
