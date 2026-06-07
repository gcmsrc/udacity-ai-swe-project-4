# Code Review: `utils/strategies/` and `utils/quiz_engine/`

**Date:** 2026-06-07  
**Reviewer role:** Senior software engineer  
**Files reviewed:**
- `utils/quiz_engine/quiz_engine.py`
- `utils/strategies/base.py`, `sequential.py`, `random_strategy.py`, `adaptive.py`, `__init__.py`, `game_planner.py`
- `tests/strategies/test_strategies.py`

---

## Analysis Framework

### 1. Duplication

No significant duplication found across the reviewed files.

---

### 2. Magic Values

**Issue 1 — Strategy name strings duplicated across registry and docstring**

- **Location:** `utils/strategies/__init__.py:35-36`
- **Category:** Magic values
- **Current code:**
  ```python
  def get_strategy(mode: str) -> QuizMode:
      """
      Args:
          mode: one of ``"sequential"`` or ``"random"``.
      ...
      """
      if mode not in _REGISTRY:
          supported = ", ".join(sorted(_REGISTRY))
  ```
- **Suggested improvement:** The docstring already lists the modes by hand. Since `_REGISTRY` is the source of truth and `get_strategy` already builds the error message dynamically from `_REGISTRY`, the docstring enum is redundant and will drift. Drop the explicit list from the docstring, or generate it programmatically.
- **Benefit:** Single source of truth; docstring never falls out of sync when a new mode is added.
- **Refactoring risk:** LOW

---

### 3. Type Safety

No type issues found. `mypy` passes clean on all 9 source files.

---

### 4. Complexity

**Issue 2 — `QuizEngine.__init__` and `QuizEngine.run` are unimplemented stubs**

- **Location:** `utils/quiz_engine/quiz_engine.py:14, 25`
- **Category:** Complexity / incompleteness
- **Current code:**
  ```python
  def __init__(self, strategy: QuizMode, ui: UI) -> None:
      raise NotImplementedError

  def run(self, cards: list[Flashcard]) -> SessionResult:
      raise NotImplementedError
  ```
- **Suggested improvement:** Implement both methods. `__init__` should store `strategy` and `ui` as instance attributes; `run` should iterate over `strategy.order(cards)`, call `ui.prompt_answer(card)`, compare to `card.back`, track correct/missed, call `ui.show_feedback`, and return a `SessionResult`.
- **Benefit:** The class is currently non-functional; every test in `test_quiz_engine.py` fails at the `engine` fixture step.
- **Refactoring risk:** LOW (the contract is fully specified in the docstrings and tests)

**Issue 3 — `AdaptiveStrategy.order` is an unimplemented stub**

- **Location:** `utils/strategies/adaptive.py:16`
- **Category:** Complexity / incompleteness
- **Current code:**
  ```python
  def order(self, cards: list[Flashcard]) -> list[Flashcard]:
      raise NotImplementedError
  ```
- **Suggested improvement:** Implement the algorithm described in `ARCHITECTURE.md`: missed cards first (preserving their original relative order), then remaining cards.
  ```python
  def order(self, cards: list[Flashcard]) -> list[Flashcard]:
      missed = [c for c in cards if c.front in self.missed]
      rest = [c for c in cards if c.front not in self.missed]
      return missed + rest
  ```
- **Benefit:** Without this, `AdaptiveStrategy` cannot be used and has 0% test coverage.
- **Refactoring risk:** LOW

---

### 5. Code Smells

**Issue 4 — `AdaptiveStrategy` not exported from the package**

- **Location:** `utils/strategies/__init__.py:3-14`
- **Category:** Code smell — architectural mismatch
- **Current code:**
  ```python
  from .base import QuizMode
  from .game_planner import GamePlanner
  from .random_strategy import RandomStrategy
  from .sequential import SequentialStrategy

  __all__ = ["QuizMode", "SequentialStrategy", "RandomStrategy", "GamePlanner", "get_strategy"]
  ```
- **Suggested improvement:** Add `from .adaptive import AdaptiveStrategy` and include it in `__all__`. `ARCHITECTURE.md` section 4 explicitly lists `AdaptiveStrategy` as a public export.
- **Benefit:** Aligns the package surface with the architecture document; callers can import `AdaptiveStrategy` without reaching into the internal module.
- **Refactoring risk:** LOW

---

## AI-Specific Checks

### 1. Context Gaps

**Issue 5 — `QuizEngine` is entirely non-functional (see Issue 2)**

The AI generated a well-documented stub but left both methods raising `NotImplementedError`. This is the most critical gap: the entire test suite for `QuizEngine` (`test_quiz_engine.py`, 8 tests) fails at instantiation, making the 69% coverage number misleading — it reflects missing implementation, not tested code.

**Issue 6 — `AdaptiveStrategy` is a stub with no tests (see Issue 3)**

Zero lines of `adaptive.py` are exercised. Combined with Issue 5, 15 of 55 total statements are unreachable dead code.

---

### 2. Phantom Dependencies

None found. All imports resolve to the standard library or local modules.

---

### 3. Over-Engineering

**Issue 7 — `GamePlanner` is an unnecessary indirection layer**

- **Location:** `utils/strategies/game_planner.py`
- **Category:** Over-engineering / architectural mismatch
- **Current code:**
  ```python
  class GamePlanner:
      def __init__(self, strategy: QuizMode) -> None: ...
      def set_strategy(self, strategy: QuizMode) -> None: ...
      def plan(self, cards: list[Flashcard]) -> list[Flashcard]: ...
  ```
- **Issue:** `GamePlanner` is a textbook GoF "Context" class. `ARCHITECTURE.md` does not mention it; `QuizEngine` already fills the Context role (it holds a strategy and calls `strategy.order()`). Adding a second Context class with a different vocabulary (`plan` vs `order`, `GamePlanner` vs `QuizEngine`) splits the strategy pattern across two unrelated abstractions.
- **Suggested improvement:** Remove `GamePlanner`. If strategy swapping at runtime is needed, add `set_strategy` directly to `QuizEngine`.
- **Benefit:** Removes an undocumented abstraction; reduces the surface callers must learn.
- **Refactoring risk:** LOW (not used by `main.py` or `QuizEngine`)

---

### 4. Test Theatre

**Issue 8 — Trivial length assertions add noise without value**

- **Location:** `tests/strategies/test_strategies.py:43-45, 64-66`
- **Category:** Test theatre
- **Current code:**
  ```python
  def test_sequential_returns_all_cards(deck):
      result = SequentialStrategy().order(deck)
      assert len(result) == len(deck)

  def test_random_returns_all_cards(deck):
      result = RandomStrategy().order(deck)
      assert len(result) == len(deck)
  ```
- **Issue:** These tests verify that `len(list(...))` equals `len(deck)` — they test Python's `list()` constructor, not strategy behaviour. The content assertions in `test_sequential_preserves_order` and `test_random_returns_same_cards` already subsume length correctness.
- **Suggested improvement:** Remove both tests. Content equality implies cardinality equality.
- **Benefit:** Leaner test file; no false confidence from tautological assertions.
- **Refactoring risk:** LOW

**Issue 9 — No test verifies `RandomStrategy` actually changes order**

- **Location:** `tests/strategies/test_strategies.py:59-61`
- **Category:** Test theatre — happy-path focus
- **Current code:**
  ```python
  def test_random_returns_same_cards(deck):
      result = RandomStrategy().order(deck)
      assert sorted(result, key=lambda c: c.front) == sorted(deck, key=lambda c: c.front)
  ```
- **Issue:** This only checks content, not that shuffling ever produces a different order. With a 1-card deck the test would still pass and shuffling would be meaningless. Seed-based tests or a probabilistic check over many runs would give confidence that the strategy actually randomises.
- **Suggested improvement:**
  ```python
  def test_random_changes_order_statistically(deck):
      orders = [tuple(c.front for c in RandomStrategy().order(deck)) for _ in range(50)]
      assert len(set(orders)) > 1, "RandomStrategy never produced a different order"
  ```
- **Benefit:** Catches a strategy that silently returns cards in the original order.
- **Refactoring risk:** LOW

**Issue 10 — No tests for `AdaptiveStrategy`**

- **Location:** `tests/strategies/test_strategies.py`
- **Category:** Test theatre — missing coverage
- **Issue:** `AdaptiveStrategy` is the most complex strategy (state-dependent ordering) and has zero tests. Critical cases to add:
  - Empty `missed` list → same order as sequential.
  - All cards missed → all returned in original order (or whichever is specified).
  - Subset missed → missed cards appear first; rest appended.
  - `missed` contains a front not in the current deck → does not error, ignored gracefully.
- **Refactoring risk:** LOW

---

### 5. Architectural Mismatches

**Issue 11 — `__init__.py` exports diverge from `ARCHITECTURE.md`**

- **Location:** `utils/strategies/__init__.py:8-14`
- **Category:** Architectural mismatch
- **ARCHITECTURE.md section 4 specifies:**
  ```
  __init__.py  # exports: QuizMode, SequentialStrategy, RandomStrategy, AdaptiveStrategy
  ```
- **Actual exports:** `QuizMode`, `SequentialStrategy`, `RandomStrategy`, `GamePlanner`, `get_strategy` — `AdaptiveStrategy` is absent; `GamePlanner` and `get_strategy` are undocumented additions.
- **Suggested improvement:** Export `AdaptiveStrategy`; either document `GamePlanner`/`get_strategy` in the architecture doc or remove them if not needed.
- **Refactoring risk:** LOW

---

## Coverage Report

**Overall coverage: 69% — below the 80% threshold.**

| Module | Stmts | Miss | Cover | Uncovered lines |
|---|---|---|---|---|
| `utils/quiz_engine/__init__.py` | 2 | 2 | 0% | 1–3 |
| `utils/quiz_engine/quiz_engine.py` | 8 | 8 | 0% | 1–25 |
| `utils/strategies/adaptive.py` | 7 | 7 | 0% | 1–16 |
| `utils/strategies/__init__.py` | 11 | 0 | 100% | — |
| `utils/strategies/base.py` | 5 | 0 | 100% | — |
| `utils/strategies/game_planner.py` | 9 | 0 | 100% | — |
| `utils/strategies/random_strategy.py` | 8 | 0 | 100% | — |
| `utils/strategies/sequential.py` | 5 | 0 | 100% | — |

### Uncovered code details

- **`utils/quiz_engine/quiz_engine.py` (lines 1–25):** The entire file is uncovered because `QuizEngine.__init__` raises `NotImplementedError`, so the `engine` fixture in `test_quiz_engine.py` fails immediately. Fixing Issue 2 unblocks all 8 engine tests.
- **`utils/strategies/adaptive.py` (lines 1–16):** No tests exist for `AdaptiveStrategy`. Fixing Issues 3 and 10 (implementation + tests) will bring this to 100%.
- **`utils/quiz_engine/__init__.py` (lines 1–3):** Covered once `QuizEngine` is instantiable (fixing Issue 2 is sufficient).

---

## Formatting Checks

### `black`
`tests/strategies/test_strategies.py` would be reformatted (caused by the long import line on line 4 which `black` would split into a parenthesised multi-line form). All other files pass.

### `isort`
`tests/strategies/test_strategies.py` has an incorrectly sorted/formatted import block (same root cause as the `black` finding on line 4).

### `flake8`
```
tests/strategies/test_strategies.py:4:89: E501 line too long (90 > 88 characters)
```
**Current line 4:**
```python
from utils.strategies import GamePlanner, RandomStrategy, SequentialStrategy, get_strategy
```
**Fix:** wrap in parentheses (which `black` would produce automatically):
```python
from utils.strategies import (
    GamePlanner,
    RandomStrategy,
    SequentialStrategy,
    get_strategy,
)
```

### `mypy`
Clean — no issues found in any of the 9 source files.

---

## Summary of Issues

| # | File | Category | Severity | Risk |
|---|---|---|---|---|
| 1 | `strategies/__init__.py:35` | Magic values | Low | LOW |
| 2 | `quiz_engine/quiz_engine.py:14,25` | Incompleteness | **Critical** | LOW |
| 3 | `strategies/adaptive.py:16` | Incompleteness | **Critical** | LOW |
| 4 | `strategies/__init__.py` | Architectural mismatch | High | LOW |
| 5 | `quiz_engine/quiz_engine.py` | Context gap (AI) | **Critical** | LOW |
| 6 | `strategies/adaptive.py` | Context gap (AI) | High | LOW |
| 7 | `strategies/game_planner.py` | Over-engineering | Medium | LOW |
| 8 | `test_strategies.py:43-45,64-66` | Test theatre | Low | LOW |
| 9 | `test_strategies.py:59-61` | Test theatre | Medium | LOW |
| 10 | `test_strategies.py` | Missing tests | High | LOW |
| 11 | `strategies/__init__.py` | Architectural mismatch | High | LOW |
