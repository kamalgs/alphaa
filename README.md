# AlphaA

Algo trading platform for Indian equities (NSE/BSE) with backtesting. Define rule-based strategies, validate them against historical data, and evaluate performance before deploying capital.

## Installation

```bash
git clone <repo-url>
cd alphaa
pip install -e ".[dev]"
```

## Quick Start

```bash
python -m alphaa --symbol RELIANCE.NS --start 2019-01-01 --end 2024-01-01
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy alphaa/
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

## License

See [LICENSE](LICENSE).
