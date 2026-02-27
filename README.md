# AlphaA

Algo trading platform for Indian equities (NSE/BSE) with backtesting. Define rule-based strategies combining fundamental stock selection with technical entry/exit timing, validate them against historical data, and evaluate performance.

## Installation

```bash
git clone <repo-url>
cd alphaa
pip install -e ".[dev]"
```

## Quick Start

Backtest the default "buy near 52-week low, sell near 52-week high" strategy on Reliance:

```bash
python -m alphaa --symbol RELIANCE.NS --start 2019-01-01 --end 2024-01-01
```

With output files (CSV trade log + charts):

```bash
python -m alphaa --symbol RELIANCE.NS --start 2019-01-01 --end 2024-01-01 --output-dir ./output
```

Customize thresholds:

```bash
python -m alphaa --symbol TCS.NS --entry-pct 3 --exit-pct 7 --stop-loss 15 --capital 500000
```

## Writing a Custom Strategy

```python
from alphaa.core import Strategy, condition, Context
from alphaa.conditions import has_no_position, has_position
from alphaa.indicators import sma, rolling_high, rolling_low

@condition
def price_below_sma(ctx: Context, period: int = 50) -> bool:
    return ctx.close < ctx.indicators[f"sma_{period}"].iloc[-1]

strategy = Strategy(
    name="my-strategy",
    entry=price_below_sma(period=50) & has_no_position(),
    exit=has_position(),  # exit on any bar when in position
    indicators=[sma(50), rolling_high(252), rolling_low(252)],
)
```

## Project Structure

| Module | Responsibility |
|--------|---------------|
| `alphaa/core/` | Types, protocols, condition composition |
| `alphaa/conditions/` | Reusable condition library |
| `alphaa/indicators/` | Indicator functions (DataFrame -> Series) |
| `alphaa/data/` | Data providers and caching |
| `alphaa/engine/` | Backtesting engine |
| `alphaa/broker/` | Order execution (paper/live) |
| `alphaa/reporting/` | Metrics, CSV export, charts |
| `alphaa/cli/` | CLI entry point |

## Development

```bash
pip install -e ".[dev]"

# Run tests
pytest

# Run tests without network
pytest -m "not slow"

# Lint
ruff check .

# Type check
mypy alphaa/
```

## License

See [LICENSE](LICENSE).
