# ADR-0001: Composition over inheritance

## Status
Accepted

## Context
Trading platforms often use deep class hierarchies (BaseStrategy -> TechnicalStrategy -> MovingAverageStrategy). This makes testing hard, extension painful, and creates coupling between unrelated components.

## Decision
Use `typing.Protocol` for structural typing instead of ABC base classes. Any object that implements the right methods satisfies a protocol — no explicit inheritance required. Components are composed at the call site, not via class hierarchies.

## Consequences
- Any object with matching methods works as a DataProvider, Broker, or CostModel
- Testing is trivial — no need to subclass or mock complex base classes
- Swapping implementations (e.g., Yahoo -> paid data source) requires zero code changes elsewhere
- No `super().__init__()` chains to manage
- IDE autocompletion still works via Protocol type hints
