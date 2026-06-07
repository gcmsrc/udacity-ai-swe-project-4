# Overall Code Review

**Scope**: `src/` and `tests/`
**Date**: 2026-06-07
**Tools run**: `black`, `isort`, `flake8`, `mypy`, `pytest --cov=src`

---

## 1. Analysis Framework Findings

### 1.1 Duplication

---

**Issue D1 — SQL constant duplicated in test**

- **File**: `tests/db/test_session_repository.py:122–123`
- **Category**: Duplication
- **Current code**:
  ```python
  _INSERT_SESSION = (
      "INSERT INTO sessions (id, dataset, created_at, result) VALUES (?, ?, ?, NULL)"
  )
  ```
  This is identical to `_SQL_INSERT_SESSION` in `src/.../db/session_repository.py:11–13`.
- **Suggested improvement**: Import the constant from the production module, or use `repo.create_session()` (the public API) to insert rows instead of raw SQL.
- **Benefit**: Schema changes are reflected in tests automatically; no silent drift.
- **Refactoring risk**: LOW

---

### 1.2 Magic Values

---

**Issue M1 — `_DB_PATH` hardcoded relative to `cwd()` at import time**

- **File**: `src/flashcard_quiz/main.py:24`
- **Category**: Magic Values
- **Current code**:
  ```python
  _DB_PATH = Path.cwd() / "data" / "db" / "flashcards.db"
  ```
- **Suggested improvement**: Accept an optional `--db-path` CLI option (with a sensible default), or at minimum resolve the path inside `main()` rather than at module import time.
- **Benefit**: Avoids silently writing the DB to a different directory when the CLI is invoked from an unexpected working directory; makes the path visible to users.
- **Refactoring risk**: LOW

---

### 1.3 Type Safety

---

**Issue T1 — Wrong return type annotation causes 6 mypy errors**

- **File**: `tests/main/test_main.py:77`
- **Category**: Type Safety
- **Current code**:
  ```python
  def _run_with_mocked_db_and_engine(
      runner: CliRunner,
      deck_file: Path,
      mode: str,
      fake_result: SessionResult,
  ) -> "CliRunner":   # wrong: returns Result, not CliRunner
  ```
  mypy reports 6 errors: `Incompatible return value type (got "Result", expected "CliRunner")` and five `"CliRunner" has no attribute 'exit_code'/'output'` errors on callers (lines 92, 98, 104, 110, 116).
- **Suggested improvement**:
  ```python
  from typer.testing import CliRunner, Result
  ) -> Result:
  ```
- **Benefit**: Eliminates all 6 mypy errors; IDEs autocomplete `Result` attributes correctly.
- **Refactoring risk**: LOW

---

### 1.4 Complexity

No methods exceeded 30 lines. No issues found in this category.

---

### 1.5 Code Smells

---

**Issue S1 — No try/finally around DB lifecycle in `main()`; connection leaked on error**

- **File**: `src/flashcard_quiz/main.py:51–65`
- **Category**: Code Smell (poor resource management)
- **Current code**:
  ```python
  db.connect(_DB_PATH)
  repo = SessionRepository(db)
  session_id = repo.create_session(str(deck))
  ...
  result = engine.run(cards)
  repo.save_session_result(session_id, result)
  ui.show_summary(result)
  db.disconnect()   # never reached if engine.run() raises
  ```
- **Suggested improvement**:
  ```python
  db.connect(_DB_PATH)
  try:
      repo = SessionRepository(db)
      session_id = repo.create_session(str(deck))
      ...
      result = engine.run(cards)
      repo.save_session_result(session_id, result)
      ui.show_summary(result)
  finally:
      db.disconnect()
  ```
- **Benefit**: The SQLite file handle is released cleanly even when the quiz loop raises (e.g. `KeyboardInterrupt`, unhandled exception in a strategy).
- **Refactoring risk**: LOW

---

**Issue S2 — Dead assignment in adaptive weight test**

- **File**: `tests/strategies/test_strategies.py:179–181`
- **Category**: Code Smell (dead code)
- **Current code**:
  ```python
  s.record_result(card, correct=False)
  current_weight = s._weights[0]    # line 179: captures weight after 1st miss
  current_weight = s._weights[0]    # line 181: immediately overwrites with same value
  s.record_result(card, correct=False)
  assert s._weights[0] > current_weight
  ```
  Line 179 is overwritten before any mutation occurs. The assertion compares weight after 2 misses (4.0) against weight after 2 misses read again (4.0) — but actually compares against line 181's value, which is still 2.0. The test passes correctly by accident: the assertion is `4.0 > 2.0`. However, line 179 is dead code.
- **Suggested improvement**: Remove line 179; keep only line 181 (which serves as the baseline just before the second miss):
  ```python
  s.record_result(card, correct=False)
  current_weight = s._weights[0]   # weight after 1st miss
  s.record_result(card, correct=False)
  assert s._weights[0] > current_weight
  ```
- **Benefit**: Intent of the test is immediately clear; no reader confusion about which assignment counts.
- **Refactoring risk**: LOW

---

**Issue S3 — `GamePlanner` tests access private attribute `_strategy`**

- **File**: `tests/strategies/test_strategies.py:228–235`
- **Category**: Code Smell (test coupling to internals)
- **Current code**:
  ```python
  def test_game_planner_exposes_strategy() -> None:
      planner = GamePlanner(strategy)
      assert planner._strategy is strategy    # private attr

  def test_game_planner_set_strategy_replaces_strategy() -> None:
      planner.set_strategy(new_strategy)
      assert planner._strategy is new_strategy  # private attr
  ```
- **Suggested improvement**: `GamePlanner` should expose a `strategy` property; tests should use that.
- **Benefit**: Tests survive internal refactors of the storage attribute name.
- **Refactoring risk**: LOW

---

## 2. AI-Specific Findings

### 2.1 Context Gap / Architectural Mismatch

---

**Issue A1 — `AdaptiveStrategy` draws with replacement; some cards may never appear**

- **File**: `src/flashcard_quiz/utils/strategies/adaptive.py:33–39`
- **Category**: Context Gap (logic error in strategy design)
- **Current code**:
  ```python
  def get_next_card(self) -> Flashcard | None:
      ...
      self._drawn += 1
      return random.choices(self._cards, weights=self._weights, k=1)[0]
  ```
  `random.choices` samples **with replacement**. `_total` is fixed at `len(cards)`. A card with a high weight can consume multiple draw slots, leaving other cards unseen.
- **Concrete failure scenario**: Deck of 5 cards; user misses card A three times in a row. A's weight is `1.0 × 2^3 = 8.0`; B–E have weight `1.0` each. Total weight = 12. On each remaining draw, A is drawn with ~67% probability. Across the 5 total draws, cards B–E may never be presented at all.
- **Suggested improvement**: Sample without replacement by tracking which cards have been drawn and adjusting the pool, or use a priority queue ordered by weight while ensuring every card appears at least once before repeating.
- **Benefit**: All cards are guaranteed to be seen at least once per session, which is the expected flashcard experience.
- **Refactoring risk**: MEDIUM

---

**Issue A2 — `AdaptiveStrategy` never uses cross-session data; `get_missed_cards()` is unreachable dead code**

- **File**: `src/flashcard_quiz/utils/db/session_repository.py:68` and `src/flashcard_quiz/main.py`
- **Category**: Architectural Mismatch (`ARCHITECTURE.md` §2 and §3 describe DB-backed adaptive seeding)
- **Current situation**: `SessionRepository.get_missed_cards()` is defined and tested in isolation, but is never called from `main.py` or from `AdaptiveStrategy`. The architecture doc states:
  > `db.get_missed_cards(dataset) → list[str]` → `adaptive.order()` → missed cards first
  
  Neither `main.py` nor `AdaptiveStrategy` contains any reference to `get_missed_cards`.
- **Impact**: Users in adaptive mode get no benefit from previous sessions. The method is effectively dead code in production.
- **Suggested improvement**: Wire `get_missed_cards` in `main.py` before constructing the strategy, and either pass the missed fronts to `AdaptiveStrategy.setup()` or extend the interface.
- **Benefit**: Adaptive mode actually works as documented; cross-session learning is enabled.
- **Refactoring risk**: MEDIUM

---

### 2.2 Over-Engineering

---

**Issue O1 — `GamePlanner` is dead production code**

- **File**: `src/flashcard_quiz/utils/strategies/game_planner.py`
- **Category**: Over-Engineering
- **Current situation**: `GamePlanner` implements the GoF Strategy *context* — it stores a strategy and allows swapping it via `set_strategy()`. It is exported from `utils/strategies/__init__.py` and covered by two tests. However, `main.py` never imports or references it; `QuizEngine` accepts a `QuizMode` directly.
- **Impact**: The class adds indirection with no production use case; the `set_strategy` capability (runtime strategy swapping) is never triggered. Future developers may waste time wondering why it exists.
- **Suggested improvement**: Remove `GamePlanner` entirely until there is an actual use case (e.g. mid-session strategy switching), or at minimum document clearly why it is present and how it is intended to be used.
- **Benefit**: Codebase becomes smaller and the strategy module is easier to understand.
- **Refactoring risk**: LOW

---

### 2.3 Test Theatre

---

**Issue TT1 — `record_result()` called before `setup()` gives a misleading error**

- **File**: `src/flashcard_quiz/utils/strategies/adaptive.py:41–61`
- **Category**: Test Theatre (missing edge-case guard)
- **Current situation**: `get_next_card()` checks `if self._cards is None: raise RuntimeError("call setup() before get_next_card()")`. `record_result()` has no equivalent guard. If called before `setup()`, `_card_index` is `{}`, so it raises `ValueError("Card '...' not found in the current deck")` — a misleading message since the real problem is that `setup()` was never called.
- **Suggested improvement**: Add the same guard to `record_result()`:
  ```python
  def record_result(self, card: Flashcard, correct: bool) -> None:
      if self._cards is None:
          raise RuntimeError("call setup() before record_result()")
      ...
  ```
  Add a test `test_adaptive_record_result_before_setup_raises`.
- **Benefit**: Consistent, actionable errors across all pre-setup misuses of the strategy.
- **Refactoring risk**: LOW

---

## 3. Format Checks

### 3.1 black

Three files would be reformatted:

| File | Note |
|---|---|
| `src/flashcard_quiz/utils/strategies/game_planner.py` | Trailing blank line / spacing |
| `tests/main/test_main.py` | Long helper lines |
| `tests/quiz_engine/test_quiz_engine.py` | Import spacing |

Run `uv run black src/ tests/` to apply.

### 3.2 isort

No issues in `src/` or `tests/` (4 `.venv` files skipped).

### 3.3 flake8

| File | Line | Code | Message |
|---|---|---|---|
| `src/.../strategies/game_planner.py` | 23 | W391 | Blank line at end of file |
| `src/.../ui/ui.py` | 7 | E501 | Line too long (90 > 88 chars) |
| `tests/main/test_main.py` | 5 | F401 | `unittest.mock.MagicMock` imported but unused |
| `tests/main/test_main.py` | 91, 109, 115 | E501 | Lines too long (89 > 88 chars) |
| `tests/quiz_engine/test_quiz_engine.py` | 1 | F401 | `unittest.mock.call` imported but unused |

### 3.4 mypy

All 6 errors are in `tests/main/test_main.py` and stem from the wrong return type annotation on `_run_with_mocked_db_and_engine` (see Issue T1):

| Line | Error |
|---|---|
| 86 | `Incompatible return value type (got "Result", expected "CliRunner")` |
| 92 | `"CliRunner" has no attribute "exit_code"` |
| 98 | `"CliRunner" has no attribute "exit_code"` |
| 104 | `"CliRunner" has no attribute "exit_code"` |
| 110 | `"CliRunner" has no attribute "output"` |
| 116 | `"CliRunner" has no attribute "output"` |

---

## 4. Test Coverage

Overall coverage: **99%** (280 statements, 3 missed). This exceeds the 80% threshold.

### Uncovered lines

| File | Line | Statement | Why uncovered |
|---|---|---|---|
| `src/flashcard_quiz/main.py` | 69 | `app()` in `if __name__ == "__main__"` | Never executed under pytest — expected. |
| `src/flashcard_quiz/utils/db/connection.py` | 83 | `raise RuntimeError("call connect() before execute()")` in `execute()` | No test calls `execute()` on an unconnected instance. |
| `src/flashcard_quiz/utils/db/connection.py` | 94 | `raise RuntimeError(...)` in `_create_schema()` | Defensive guard unreachable via `connect()` (which always sets `_conn` first). |

**Recommendation**: Add a test that calls `db.execute()` before `db.connect()` to cover line 83. Line 94 and the `__main__` guard are acceptable to leave uncovered.

---

## 5. Summary Table

| ID | File | Category | Severity |
|---|---|---|---|
| A1 | `strategies/adaptive.py:38` | Context gap — draws with replacement | HIGH |
| A2 | `db/session_repository.py:68` + `main.py` | Architectural mismatch — `get_missed_cards` unused | HIGH |
| S1 | `main.py:51–65` | DB connection leaked on exception | MEDIUM |
| T1 | `tests/main/test_main.py:77` | Wrong return type → 6 mypy errors | MEDIUM |
| O1 | `strategies/game_planner.py` | Dead production code | LOW |
| M1 | `main.py:24` | `_DB_PATH` magic path at import time | LOW |
| TT1 | `strategies/adaptive.py:41` | Missing pre-setup guard on `record_result()` | LOW |
| D1 | `tests/db/test_session_repository.py:122` | Duplicated SQL constant | LOW |
| S2 | `tests/strategies/test_strategies.py:179` | Dead assignment | LOW |
| S3 | `tests/strategies/test_strategies.py:228` | Tests access private `_strategy` attr | LOW |
