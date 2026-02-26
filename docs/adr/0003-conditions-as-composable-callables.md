# ADR-0003: Conditions as composable callables

## Status
Accepted

## Context
Strategy rules like "buy when price is near 52-week low AND we have no position" need to be expressed, composed, and parameterized. Common approaches include DSLs (YAML/JSON rule engines), class hierarchies, or raw functions.

## Decision
Use a `@condition` decorator that transforms `(Context, *args) -> bool` functions into composable `ConditionBase` objects supporting `&` (AND), `|` (OR), `~` (NOT) operators. Every condition receives a single `Context` argument, enabling uniform composition. `ParamSpec` preserves type safety for parameterized conditions.

## Consequences
- Strategies read like sentences: `price_near_52w_low(5) & has_no_position()`
- Boolean composition is built-in — no need for explicit `AndCondition` wiring
- `repr()` shows readable condition trees for debugging
- IDE autocompletion works for condition parameters
- Adding a new condition is just writing a function with the `@condition` decorator
- No YAML/JSON to learn — conditions are Python code
