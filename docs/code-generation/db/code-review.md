# Code Review: `utils/db`

**Files reviewed:**
- `utils/db/connection.py`
- `utils/db/session_repository.py`
- `utils/db/__init__.py`
- `tests/db/test_session_repository.py`

---

## Analysis Framework

### 1. Duplication

**No significant duplication found.**

The `execute()` method is the single point for all query execution. Error handling is propagated uniformly by letting `sqlite3` exceptions bubble up, so there is no repeated try/except boilerplate.

---

### 2. Magic Values

| Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|
| `session_repository.py:42` | Magic value — SQL literal | `"INSERT INTO sessions (id, dataset, created_at, result) VALUES (?, ?, ?, NULL)"` | Extract the SQL strings to named constants or a dedicated SQL module | Easier to find and update schema-related strings in one place | LOW |
| `session_repository.py:57–59` | Repeated field names | `{"total": result.total, "correct": result.correct, "missed": result.missed}` | Use `dataclasses.asdict(result)` | Removes the need to manually mirror every field; auto-adapts when the dataclass gains new fields | LOW |

---

### 3. Type Safety

| Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|
| `connection.py:27` | Type declared in `__new__` — not a class-level annotation | `cls._instance._conn: sqlite3.Connection \| None = None` | Declare `_conn: sqlite3.Connection \| None = None` as a class-level attribute | Fixes mypy `misc` and `assignment` errors; makes the attribute visible to static analysis without running `__new__` | LOW |
| `connection.py:58` | Missing generic type args | `params: tuple = ()` / `-> list[dict]` | `params: tuple[()] = ()` → better: `params: tuple[object, ...] = ()` and `-> list[dict[str, object]]` | Resolves mypy `type-arg` errors | LOW |
| `session_repository.py:89` | `Any` return | `json.loads(rows[0]["result"]).get("missed", [])` | Cast or type-guard: `result_data: dict[str, object] = json.loads(...)` then return `list(result_data.get("missed", []))` | Resolves mypy `no-any-return` error; makes the return type explicit | LOW |
| `tests/db/test_session_repository.py:13` | Generator fixture type | `def db(tmp_path: Path) -> DatabaseConnection` | `-> Generator[DatabaseConnection, None, None]` | Resolves mypy `misc` generator return type error | LOW |

---

### 4. Complexity

**No complexity issues found.** All methods are well under 30 lines, have a single clear purpose, and contain no deep nesting.

---

### 5. Code Smells

| Location | Category | Current code | Suggested improvement | Benefit | Risk |
|---|---|---|---|---|---|
| `connection.py:75` | `assert` for runtime guard | `assert self._conn is not None, "call connect() before execute()"` | Raise `RuntimeError("call connect() before execute()")` | `assert` is silently stripped with `python -O`; a `RuntimeError` is always raised | LOW |
| `connection.py:85` | Same `assert` pattern | `assert self._conn is not None` | Same: raise `RuntimeError` | Same as above | LOW |
| `session_repository.py:91–93` | Unclear ownership of `close()` | `def close(self) -> None: self.db.disconnect()` | Remove `close()` or document why `SessionRepository` owns the connection lifecycle | The ARCHITECTURE doc states `disconnect()` is called by `main.py`, not the repository. This method creates ambiguity about who is responsible for closing the connection. | MEDIUM |

---

## AI-Specific Checks

### 1. Context gaps

**Architectural mismatch — schema deviation from `ARCHITECTURE.md`.**

The architecture document specifies a two-table schema:

```sql
CREATE TABLE sessions (id, dataset, created_at);
CREATE TABLE card_results (id, session_id, card_front, correct);
```

The implementation instead uses a **single `sessions` table** with a `result TEXT` column that stores a JSON blob. The `card_results` table is never created.

- `SessionRepository` exposes `save_session_result()` (not `save_result()` as documented).
- The `card_results` table and the `save_result(session_id, card_front, correct)` method from the architecture are entirely absent.

This is the highest-severity finding. Querying individual card-level results (e.g. "how many times was card X missed across all sessions?") is not possible with the current schema without deserialising every JSON blob.

### 2. Phantom dependencies

None found. All imports (`sqlite3`, `json`, `uuid`, `datetime`) are standard library.

### 3. Over-engineering

**Singleton resets between tests are not handled.** The `DatabaseConnection` singleton holds its `_instance` for the lifetime of the process. In the test suite, each `db` fixture calls `DatabaseConnection()` and `connect()` on the same singleton instance. Because `disconnect()` sets `_conn = None` but does **not** reset `_instance`, a subsequent `DatabaseConnection()` call returns the same object. This works only because the fixture always reconnects before yielding — but it means tests are sharing state through the singleton, not truly isolated. A test that forgot to call `connect()` would silently use any leftover connection.

Suggested fix: add a `_reset()` class method (test-only) that sets `_instance = None`, or document clearly in the fixture why reconnecting the same instance is safe.

### 4. Test theatre

The SQL injection tests (`test_sql_injection_*`) verify that parameterised queries work as designed by `sqlite3` — not application logic. These are testing the Python standard library, not the `SessionRepository`. They can be removed without reducing coverage of the application code.

### 5. Architectural mismatches

See **Context gaps** above. The schema mismatch is the only architectural issue.

---

## Formatting Checks

### `black`

Two files would be reformatted:

- `utils/db/connection.py`
- `tests/db/test_session_repository.py`

Note: the black warning (`Python 3.12 cannot parse code formatted for Python 3.15`) is a tooling version mismatch, not a code issue.

### `isort`

No issues found. All imports are correctly ordered.

### `flake8`

12 E501 (line too long) violations, all in `tests/db/test_session_repository.py`, plus one in `utils/db/session_repository.py`:

| File | Line | Issue |
|---|---|---|
| `session_repository.py` | 42 | E501 line too long (92 > 88) |
| `test_session_repository.py` | 39 | E501 line too long (96 > 88) |
| `test_session_repository.py` | 79 | E501 line too long (92 > 88) |
| `test_session_repository.py` | 84 | E501 line too long (92 > 88) |
| `test_session_repository.py` | 86 | E501 line too long (91 > 88) |
| `test_session_repository.py` | 102 | E501 line too long (91 > 88) |
| `test_session_repository.py` | 111 | E501 line too long (90 > 88) |
| `test_session_repository.py` | 114 | E501 line too long (91 > 88) |
| `test_session_repository.py` | 127 | E501 line too long (92 > 88) |
| `test_session_repository.py` | 128 | E501 line too long (96 > 88) |
| `test_session_repository.py` | 130 | E501 line too long (91 > 88) |
| `test_session_repository.py` | 144 | E501 line too long (92 > 88) |

### `mypy`

7 errors across 3 files (see Type Safety section for details):

| File | Line | Error |
|---|---|---|
| `connection.py` | 27 | `[misc]` Type cannot be declared in assignment to non-self attribute |
| `connection.py` | 27 | `[assignment]` Incompatible types in assignment |
| `connection.py` | 52 | `[assignment]` Incompatible types in assignment |
| `connection.py` | 58 | `[type-arg]` Missing type arguments for generic `tuple` |
| `connection.py` | 58 | `[type-arg]` Missing type arguments for generic `dict` |
| `session_repository.py` | 89 | `[no-any-return]` Returning `Any` from function declared to return `list[str]` |
| `test_session_repository.py` | 13 | `[misc]` Generator function return type should be `Generator` |

---

## Test Coverage

**Overall: 98%** — above the 80% threshold.

| File | Statements | Missed | Cover |
|---|---|---|---|
| `utils/db/__init__.py` | 3 | 0 | 100% |
| `utils/db/connection.py` | 27 | 0 | 100% |
| `utils/db/session_repository.py` | 23 | 1 | 96% |

**Uncovered line:**

- `session_repository.py:93` — the body of `SessionRepository.close()` (`self.db.disconnect()`).

This is the `close()` method flagged as a code smell above. Since `main.py` is expected to call `db.disconnect()` directly (per the architecture), this method is neither called by tests nor by the application — which is further evidence it should be removed or its ownership clarified.
