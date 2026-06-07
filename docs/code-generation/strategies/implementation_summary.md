# Implementation Summary — Quiz Strategies

## Changes Made

### `utils/strategies/sequential.py`
- Implemented `SequentialStrategy.order()`: returns `list(cards)`, a shallow copy that preserves the original order without mutating the input.

### `utils/strategies/random_strategy.py`
- Implemented `RandomStrategy.order()`: copies the input with `list(cards)`, shuffles the copy in-place via `random.shuffle`, and returns it. The original deck is never mutated.

### `utils/strategies/__init__.py`
- Removed `AdaptiveStrategy` from the public API and `__all__`.
- Added a `_REGISTRY` dict mapping mode names (`"sequential"`, `"random"`) to their classes.
- Added `get_strategy(mode: str) -> QuizMode`, a factory function that instantiates the requested strategy or raises `ValueError` for unsupported modes.

### `main.py`
- Replaced the inline `_STRATEGIES` dict and direct class imports with a single call to `get_strategy` from the strategies package.
- Removed the `AdaptiveStrategy` import and mode reference from the help text.

### `tests/strategies/test_strategies.py`
- Removed all `AdaptiveStrategy` test cases.
- Added three `get_strategy` factory tests:
  - `test_factory_returns_sequential` — verifies correct type is returned.
  - `test_factory_returns_random` — verifies correct type is returned.
  - `test_factory_raises_for_unknown_mode` — verifies `ValueError` is raised for an unrecognised mode string.

## Design Decisions

| Decision | Rationale |
|---|---|
| Return a copy in both strategies | Strategies must not mutate caller data; returning `list(cards)` is explicit and cheap. |
| Factory in `__init__.py` | Keeps the public surface of the package self-contained; callers import one function instead of multiple classes plus their own dispatch logic. |
| `ValueError` in factory | Standard Python convention for invalid argument values; no custom exception needed. |
| `AdaptiveStrategy` left on disk but unexported | The file is not deleted because it is a planned extension point (see `ARCHITECTURE.md`); it is simply not part of the current public API. |
