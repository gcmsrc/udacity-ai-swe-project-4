# Code Review: Adaptive Strategy & Quiz Engine (`d78ec67`)

**Commit:** `add adaptive strategy`

**Files reviewed:**
- `utils/strategies/base.py`
- `utils/strategies/sequential.py`
- `utils/strategies/random_strategy.py`
- `utils/strategies/adaptive.py`
- `utils/strategies/game_planner.py`
- `utils/strategies/__init__.py`
- `utils/quiz_engine/quiz_engine.py`
- `utils/models/models.py`
- `utils/db/connection.py`
- `utils/db/session_repository.py`
- `tests/strategies/test_strategies.py`
- `tests/db/test_session_repository.py`

---

## Analysis Framework

### 1. Duplication

| Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|
| `sequential.py:8–11` / `random_strategy.py:11–14` | Duplication — identical `__init__` and index state | Both declare `_cards: list[Flashcard] = []` and `_index: int = 0` in `__init__`; `get_next_card()` is line-for-line identical in both | Extract a `_BaseIndexedStrategy` mixin with shared `__init__`, `_cards`, `_index`, and `get_next_card()`; each subclass only needs to override `setup()` | Removes ~12 lines of duplicated logic; exhaustion semantics are in one place | MEDIUM |

---

### 2. Magic Values

| Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|
| `adaptive.py:38` | Magic number | `self._weights[idx] *= 2.0` | `_MISSED_WEIGHT_MULTIPLIER: float = 2.0` as a module-level constant | Single change point if the multiplier is tuned; documents intent | LOW |

---

### 3. Type Safety

| Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|
| `session_repository.py:83` | `arg-type` — `object` passed to `json.loads` | `result_data: dict[str, object] = json.loads(rows[0]["result"])` | `json.loads(str(rows[0]["result"]))` | `execute()` returns `list[dict[str, object]]`; indexing yields `object`, but `json.loads` requires `str \| bytes \| bytearray`. Cast resolves the mypy error | LOW |
| `session_repository.py:84` | `call-overload` / `no-any-return` | `return list(result_data.get("missed", []))` | `return [str(m) for m in result_data.get("missed", [])]` | Resolves mypy overload-mismatch and `no-any-return`; also makes the per-element cast explicit | LOW |
| `test_session_repository.py:71` | Same `arg-type` | `data = json.loads(rows[0]["result"])` | `data = json.loads(str(rows[0]["result"]))` | Same root cause as above; test mirrors production code's issue | LOW |
| `base.py:25` | Phantom `noqa` comment | `def record_result(...) -> None:  # noqa: ARG002` | Remove the comment | `ARG002` is a **ruff** rule; this project uses **flake8**, which does not recognise it. The suppression is a no-op and gives a false impression that a linter check is being managed | LOW |

---

### 4. Complexity

| Method | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|
| `quiz_engine.run()` line 37 | Method doing too much — I/O side-effect inside a data-returning method | `self._ui.show_summary(result)` called inside `run()` before `return result` | Move `show_summary()` to `main.py`, after persistence completes | `run()` should return data; the caller decides when and whether to display it. See AI-specific §1 for full impact | MEDIUM |

---

### 5. Code Smells

| Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|
| `connection.py:82,92` | `assert` used as runtime guard | `assert self._conn is not None, "call connect() before execute()"` and `assert self._conn is not None` in `_create_schema` | `raise RuntimeError("call connect() before execute()")` | `assert` is stripped by `python -O`. This was flagged in the previous review (old lines 75, 85) and was not fixed | LOW |
| `adaptive.py:37` | Silent `StopIteration` on missing card | `idx = next(i for i, c in enumerate(self._cards) if c.front == card.front)` | Build a `{card.front: index}` dict in `setup()` and use a direct lookup; raise `ValueError` if not found | `next()` on an exhausted generator raises `StopIteration` — an opaque error if `record_result` is ever called with an unexpected card. A pre-built dict is also O(1) vs O(n) | LOW |
| `game_planner.py` | Near-empty class with no behavior | `GamePlanner` is now `_strategy` + `set_strategy()` + `strategy` property — a mutable reference to a strategy | Consider eliminating `GamePlanner` and having `main.py` hold the strategy directly, or restore meaningful behavior | The Strategy pattern's Context class is supposed to *use* the strategy, not just hold it. As written it adds a layer with no purpose | MEDIUM |

---

## AI-Specific Checks

### 1. Context gaps — `QuizEngine.run()` violates the data-flow contract

`quiz_engine.run()` (line 37) calls `self._ui.show_summary(result)` before returning. The `ARCHITECTURE.md` (§3) specifies:

```
→ quiz_engine.run()         → SessionResult
→ db.save_results()         → persisted to SQLite
→ ui.show_summary()         → terminal output
```

By calling `show_summary()` internally, the engine forces the summary to appear **before** persistence. `main.py` cannot suppress the summary (for headless use), reorder it, or skip it on a save error.

**Suggested fix:** remove `self._ui.show_summary(result)` from `run()`. Move the call to `main.py`:

```python
result = engine.run(cards)
db.save_session_result(session_id, result)
ui.show_summary(result)
```

---

### 2. Phantom dependencies

None found. All imports are standard library or internal modules.

---

### 3. Over-engineering

No over-engineering found in the new code.

---

### 4. Test theatre

| Test | Issue | Suggested improvement |
|---|---|---|
| `test_strategies.py:253` — `test_adaptive_doubles_weight_on_miss` | Accesses private `s._weights[0]` — tests internal implementation state, not observable behaviour | Replace with a statistical assertion: set up a two-card deck, mark card 0 as missed N times, drain the strategy, assert card 0 appears more than card 1 |
| `test_strategies.py:260` — `test_adaptive_correct_answer_does_not_change_weight` | Same — `s._weights[0] == 1.0` tests the private array after a trivial no-op | Remove or fold into the behavioural test above; the "no change on correct" path is already implicitly covered by the initial-weight test |

**Missing edge cases:**

- `AdaptiveStrategy.record_result()` with a card not in `_cards` — currently raises `StopIteration` (opaque); no test covers this.
- Any strategy's `get_next_card()` called before `setup()` — returns `None` silently; no test documents or verifies this contract.

---

### 5. Architectural mismatches

| Location | Mismatch |
|---|---|
| `ARCHITECTURE.md` §2 — Strategy Pattern | Still documents `QuizMode.order(cards)` as the single abstract method. The new interface (`setup()`, `get_next_card()`, `record_result()`) is not reflected. The design rationale ("Each mode is a different algorithm for *ordering* the same deck") is now stale. |
| `ARCHITECTURE.md` §2 — Strategy table | Adaptive row still reads "Missed cards first, remaining cards appended" — the old upfront-sort behaviour, replaced by in-session weighted draws. |
| `ARCHITECTURE.md` §5 — Key Interfaces | `QuizMode` code block shows `order()` only; entirely replaced in the implementation. |
| `quiz_engine.run()` line 37 | Calls `show_summary()` before returning — violates the data-flow sequence documented in §3 (see §1 above). |

---

## Formatting Checks

### black

All 17 files would be left unchanged. ✓

### isort

No issues found. ✓

### flake8

No issues found. ✓

### mypy

4 errors in 2 files:

| File | Line | Error | Rule |
|---|---|---|---|
| `utils/db/session_repository.py` | 83 | Argument 1 to "loads" has incompatible type "object"; expected "str \| bytes \| bytearray" | `arg-type` |
| `utils/db/session_repository.py` | 84 | No overload variant of "list" matches argument type "object" | `call-overload` |
| `utils/db/session_repository.py` | 84 | Returning Any from function declared to return "list[str]" | `no-any-return` |
| `tests/db/test_session_repository.py` | 71 | Argument 1 to "loads" has incompatible type "object"; expected "str \| bytes \| bytearray" | `arg-type` |

**Root cause:** `execute()` returns `list[dict[str, object]]`. Indexing a `dict[str, object]` yields `object`, not `str`. `json.loads` requires `str | bytes | bytearray`. Fix: cast before calling `json.loads`:

```python
# session_repository.py
result_data: dict[str, object] = json.loads(str(rows[0]["result"]))
return [str(m) for m in result_data.get("missed", [])]

# test_session_repository.py
data = json.loads(str(rows[0]["result"]))
```

---

## Test Coverage

**Overall: 96%** — above the 80% threshold.

**7 tests failing** in `tests/ui/test_ui.py` — `UI` is an unimplemented stub (`raise NotImplementedError`). This is intentional at this stage of the Red-Green-Refactor cycle.

| File | Stmts | Miss | Cover | Missing |
|---|---|---|---|---|
| `main.py` | 11 | 11 | 0% | 1–22 (not yet implemented) |
| `utils/data_loader/data_loader.py` | 40 | 1 | 98% | line 132 |
| `tests/ui/test_ui.py` | 41 | 12 | 71% | 27, 33, 40–41, 48–49, 56–57, 64–65, 72–73 |
| All other changed files | — | — | 100% | — |

The 12 missed lines in `tests/ui/test_ui.py` are assertion lines inside the 7 failing tests — they are unimplemented code, not untested paths.

**Missing test cases in the strategies suite:**

- `AdaptiveStrategy.record_result()` called with a card absent from `_cards` — raises `StopIteration` with no test coverage.
- Any strategy's `get_next_card()` invoked before `setup()` — currently returns `None` silently; no test documents this contract.
