# Code Review — `--show-history` feature (HEAD~2..HEAD)

**Scope:** commits `25d028e` (add terminal rich) and `ee0f25f` (add progress)  
**Files changed:** `main.py`, `session_repository.py`, `ui.py`, `__init__.py` (ui), `test_session_repository.py`, `test_main.py`, `test_ui.py`

---

## Analysis Framework Findings

### 1. Duplication

| # | Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|---|
| D1 | `ui.py:64-65` and `ui.py:148` | Duplication | `filled = round(pct * _BAR_WIDTH)` / `"█" * filled + "░" * (...)` verbatim in both `TerminalUI.show_history` and `TerminalRichUI.show_history` | Extract `_make_bar(pct: float) -> str` module-level helper; rich variant wraps in markup | Single change point if bar formula or width changes | LOW |
| D2 | `ui.py:61` and `ui.py:138` | Duplication | `label = "attempt" if n == 1 else "attempts"` in both renderers | Extract `_attempt_label(n: int) -> str` helper or fold into a shared `_history_title` helper | Reduces drift risk | LOW |
| D3 | `ui.py:42` and `ui.py:106` | Duplication | `ratio = result.correct / result.total if result.total else 0` copied to both `show_summary` implementations | Add `score: float` property to `SessionResult` and use it here and in `get_history` | Formula defined once; all callers stay in sync | LOW |

---

### 2. Magic Values

| # | Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|---|
| M1 | `ui.py:108, 119` | Magic values | `"\U0001f4ca"`, `"\U0001f4cc"` unicode escapes mixed with literal emojis elsewhere in the same file | Replace with `"📊"` and `"📌"` to match surrounding style | Consistent, readable | LOW |

---

### 3. Type Safety

| # | Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|---|
| T1 | `session_repository.py:83` | Missing type args | `data: dict = json.loads(...)` | `data: dict[str, object] = json.loads(...)` — or fully `dict[str, int \| list[str]]` | Eliminates mypy `[type-arg]` error; `data.get()` calls become typed | LOW |
| T2 | `tests/ui/test_ui.py:12` | Incomplete annotation | `return request.param()` returns `TerminalUI \| TerminalRichUI` (both `Any` from `params`) typed as `-> UI` | Use `cast(UI, request.param())` or change the return type to `TerminalUI \| TerminalRichUI` | Eliminates mypy `[no-any-return]` error | LOW |
| T3 | `session_repository.py:84-85` | False type annotation | `total: int = data.get("total", 0)` — `data` is untyped (`dict`), so the `: int` annotation is not enforced by mypy and gives false safety | Fix T1 first; annotations then flow naturally | Avoids silent type error if JSON has wrong shape | LOW |

---

### 4. Complexity

No methods exceeding 30 lines were introduced. Logic is straightforward.

---

### 5. Code Smells

| # | Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|---|
| CS1 | `session_repository.py:83` | Poor separation of concerns | `get_history` manually parses JSON keys `"total"` and `"correct"` — bypasses `SessionResult` model | Add `SessionResult.from_json(s: str) -> SessionResult` (or `from_dict`) and call `result.correct / result.total` via the model | `SessionResult` owns its own serialization contract; field renames are caught by the compiler, not silently zeroed | MEDIUM |
| CS2 | `ui.py:150-157` | Unnecessarily fragmented string | Bar built via 4–5 `+` concatenations | `f"[{color}]{'█' * filled}[/][dim]{'░' * (_BAR_WIDTH - filled)}[/]"` | Single expression, easier to read | LOW |
| CS3 | `session_repository.py:83` | Redundant cast | `str(row["result"])` — `result` column is TEXT; `sqlite3` already returns it as `str` | Remove `str()` cast; add `assert isinstance(row["result"], str)` if narrowing is needed | Removes misleading code that implies the column could return a non-string | LOW |

---

## AI-Specific Checks

### 1. Context Gaps
- None identified. The `--show-history` feature matches the architectural intent described in `ARCHITECTURE.md`.

### 2. Phantom Dependencies
- None. `rich` is a declared dependency in `pyproject.toml`.

### 3. Over-Engineering
- None. The implementation is appropriately simple.

### 4. Test Theatre

| # | Location | Issue | Scenario |
|---|---|---|---|
| TT1 | `test_main.py` | **`--show-history` path completely untested** | Lines 84–86 and 92 of `main.py` have 0% coverage (confirmed by `pytest --cov`). No integration test invokes the app with `--show-history`. The wiring `repo.get_history → ui.show_history` is exercised only in unit tests, never end-to-end. |
| TT2 | `test_session_repository.py:113-120` | **Timestamp ordering non-determinism** | `create_session` uses `datetime.now(timezone.utc).isoformat()`. Three sessions created in a tight loop can receive the same timestamp on a slow or GC-pausing interpreter, making `ORDER BY created_at ASC` non-deterministic and the assertion `[0.5, 0.75, 1.0]` potentially flaky. |
| TT3 | `test_main.py:66-80` | **Real `TerminalRichUI` exercised in non-TTY tests** | `_run_with_mocked_db_and_engine` patches DB and engine but not `TerminalRichUI`. The real rich renderer runs inside the `CliRunner`. Tests asserting on `"50%"` and `"CPU"` currently pass because rich strips markup in non-TTY mode, but this is fragile to rich version changes. |

### 5. Architectural Mismatches
- None. The `UI` Protocol extension, `SessionRepository.get_history`, and the `--show-history` flag are consistent with the documented architecture.

---

## Correctness Bugs

| # | File | Line | Summary | Failure Scenario | Severity |
|---|---|---|---|---|---|
| **B1** | `session_repository.py` | 83 | `json.JSONDecodeError` propagates uncaught from `get_history` | A corrupt `result` row in the database (hand-edited, or written by a future bug) causes `json.loads()` to raise. The `try/finally` in `main.py` only guarantees `db.disconnect()` — there is no `except` clause. The exception reaches the user as a raw Python traceback instead of a clean error message. | HIGH |
| **B2** | `main.py` | 75, 85 | Path string used as dataset key without normalisation | `create_session(str(deck))` and `get_history(str(deck))` use `str()` on the same variable within one run (consistent), but across runs the raw CLI path is stored. Running `flashcard ./decks/basics.json` stores `"./decks/basics.json"`; running later from a different CWD or with `flashcard decks/basics.json --show-history` queries `"decks/basics.json"` — no rows match, history is silently empty. | MEDIUM |

---

## Format Checks

### black
```
would reformat tests/db/test_session_repository.py
would reformat tests/main/test_main.py
```
**Action:** run `uv run black tests/db/test_session_repository.py tests/main/test_main.py`

### isort
Clean — no issues.

### flake8
```
tests/db/test_session_repository.py:118:89: E501 line too long (93 > 88 characters)
```
Line 118:
```python
        repo.save_session_result(sid, SessionResult(total=total, correct=correct, missed=[]))
```
**Action:** split the line or run `black` (which will also fix this).

### mypy
```
src/flashcard_quiz/utils/db/session_repository.py:83: error: Missing type arguments for generic type "dict"  [type-arg]
tests/ui/test_ui.py:12: error: Returning Any from function declared to return "UI"  [no-any-return]
```
See T1 and T2 in the Type Safety section above.

---

## Test Coverage

**Overall: 99% (344 statements, 5 missed)**

| File | Coverage | Missing lines |
|---|---|---|
| `main.py` | 91% | 85–86, 92 |
| `connection.py` | 94% | 83, 94 |

### Uncovered lines in `main.py`

```python
84    if show_history:
85        history = repo.get_history(str(deck))   # NOT COVERED
86        ui.show_history(history)                 # NOT COVERED
...
92    app()                                        # NOT COVERED (guard __main__)
```

Lines 85–86 represent the entire `--show-history` branch. No test in `test_main.py` passes `--show-history`. This is a meaningful gap: the integration between `get_history`, its return value, and `show_history` is exercised only by unit tests with no orchestration coverage.

**Recommended fix:** add a test to `test_main.py` using `_run_and_capture_ui` with `["--show-history"]`, configuring `mock_repo_cls.return_value.get_history.return_value = [0.5, 1.0]`, and asserting the history output appears in `result.output`.

---

## Summary of Prioritised Actions

| Priority | Item | File(s) |
|---|---|---|
| P1 — Fix | B1: catch `json.JSONDecodeError` in `get_history` / `main.py` | `session_repository.py`, `main.py` |
| P1 — Fix | TT1: add `--show-history` integration test | `test_main.py` |
| P2 — Fix | Format: run `black` on two test files | `test_session_repository.py`, `test_main.py` |
| P2 — Fix | T1/T2: fix two mypy errors | `session_repository.py`, `test_ui.py` |
| P3 — Improve | B2: normalise path via `Path.resolve()` or `str(deck.resolve())` | `main.py` |
| P3 — Improve | TT2: mock `datetime.now` or use fixed timestamps in ordering test | `test_session_repository.py` |
| P3 — Improve | CS1: add `SessionResult.from_json` to centralise deserialisation | `models.py`, `session_repository.py` |
| P4 — Cleanup | D1–D3, CS2–CS3, M1: extract bar helper, deduplicate ratio, fix escapes | `ui.py` |
