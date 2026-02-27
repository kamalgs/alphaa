# ADR-0002: Immutable value types

## Status
Accepted

## Context
Mutable state shared between components is a primary source of bugs in trading systems. When a Bar or Trade object is passed to multiple functions, any of them could modify it, causing subtle data corruption.

## Decision
All domain value types (Bar, Signal, Order, Fill, Trade, PortfolioSnapshot, Context) are frozen dataclasses. `PortfolioState` is the sole deliberate exception — it must mutate as fills arrive, and is owned exclusively by the engine.

## Consequences
- No accidental mutation of market data, signals, or trades
- Thread safety for free on value types
- Slightly more verbose updates (must create new instances instead of mutating)
- PortfolioState mutation is contained to a single owner (the engine), making it easy to audit
