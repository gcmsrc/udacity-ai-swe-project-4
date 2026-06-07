# Architecture: CLI Flashcard Application

## 1. Module Overview

| Package | Responsibility |
|---|---|
| `utils/models/` | Data classes: `Flashcard`, `SessionResult` |
| `utils/data_loader/` | Load and validate JSON; raise user-friendly errors |
| `utils/strategies/` | `QuizMode` ABC + Sequential / Random / Adaptive implementations |
| `utils/quiz_engine/` | Runs the quiz loop; owns answer-checking and score tracking |
| `utils/ui/` | All terminal I/O via the `UI` Protocol; `TerminalUI` (plain) and `TerminalRichUI` (`rich`-styled) implementations |
| `utils/db/` | Singleton DB connection; session creation and result persistence |
| `main.py` | Typer app; wires CLI args → data loader → strategy → engine → ui |

---

## 2. Design Patterns

### Strategy Pattern — Quiz Modes

`QuizMode` is an **Abstract Base Class** (ABC) with one abstract method. The ABC enforces the contract at class-definition time: any concrete subclass that omits `order()` raises `TypeError` on instantiation, which catches mistakes early rather than at runtime.

```python
from abc import ABC, abstractmethod

class QuizMode(ABC):
    @abstractmethod
    def order(self, cards: list[Flashcard]) -> list[Flashcard]: ...
```

Three concrete strategies subclass it:

| Strategy | Class | Algorithm |
|---|---|---|
| Sequential | `SequentialStrategy` | Return cards as-is |
| Random | `RandomStrategy` | `random.shuffle` then return |
| Adaptive | `AdaptiveStrategy` | Missed cards first, remaining cards appended |

**Why ABC over Protocol?**  
`Protocol` gives structural (duck-typed) compatibility — anything with a matching signature qualifies. `ABC` gives nominal enforcement — only explicit subclasses are valid strategies, and forgetting to implement `order()` is a hard error at instantiation. For an internal tool where all strategies live in the same repo, this stricter contract is preferable: mistakes are caught immediately rather than silently passing type-checkers.

**Why Strategy here?**  
Each mode is a different algorithm for *ordering* the same deck. Swapping modes at runtime (from a CLI flag) maps directly to choosing a strategy object. Adding "Spaced Repetition" later means subclassing `QuizMode` — nothing else changes.

### Singleton Pattern — Database Connection

`DatabaseConnection` is a **Singleton** that manages the single SQLite connection for the process lifetime. The class-level `_instance` guard ensures only one connection is ever opened, regardless of how many modules import the class.

```python
class DatabaseConnection:
    _instance: "DatabaseConnection | None" = None

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self, db_path: Path) -> None: ...
    def disconnect(self) -> None: ...
    def execute(self, query: str, params: tuple = ()) -> list[dict]: ...
```

**Why Singleton here?**  
Opening a new database connection per module or per call would waste resources and risk connection-state inconsistencies. A singleton keeps connection lifecycle explicit and testable: tests can call `connect()` with an in-memory path, exercise the full stack, then `disconnect()`.

**Why not a module-level global?**  
A singleton class exposes a clear interface (`connect`, `disconnect`, `execute`), can be sub-classed for testing (e.g. an in-memory variant), and signals intent better than an undeclared module-level variable.

### Data Classes — Models

Plain `dataclass` objects carry data between layers. No business logic lives in models.

### UI Protocol — Pluggable Renderers

All terminal I/O sits behind a `UI` **Protocol** (structural subtyping, PEP 544). `QuizEngine` is typed against `UI` and calls three methods — `prompt_answer`, `show_feedback`, `show_summary` — without knowing the concrete renderer. Two implementations satisfy it:

| Class | Backend | Use |
|---|---|---|
| `TerminalUI` | built-in `print` / `input` | Minimal, dependency-free fallback |
| `TerminalRichUI` | [`rich`](https://github.com/textualize/rich) | Default: styled prompts, colored feedback, bordered summary table |

**Why a second renderer instead of editing the first?**
The two classes are interchangeable because they share the same Protocol. `TerminalRichUI` is a **pure aesthetic** layer — it reproduces the exact same control flow and outcomes as `TerminalUI` (same prompts, same correct/wrong decisions, same summary content) and only changes *presentation*. Keeping `TerminalUI` intact preserves a zero-dependency fallback and makes the visual upgrade a drop-in swap in `main.py`, with no change to `QuizEngine`, strategies, or any business logic.

`TerminalRichUI` owns a single `rich.console.Console` instance and renders:

- **Prompt** — the card front styled with `Console.input` (bold cyan question, dim prompt arrow).
- **Feedback** — a green `Correct!` panel, or a red panel showing the expected answer on a miss.
- **Summary** — a `rich.table.Table` with the score and pass-ratio, plus a panel listing any missed cards.

Because `rich` writes to a `Console`, output is fully testable: tests construct the console with `Console(file=io.StringIO(), force_terminal=False)` and assert on the captured text, mirroring how `TerminalUI` is tested against `capsys`.

---

## 3. Module Dependency Diagram

```
main.py
  │
  ├── utils/data_loader/   (loads JSON → list[Flashcard])
  │       └── utils/models/
  │
  ├── utils/strategies/    (orders list[Flashcard])
  │       └── utils/models/
  │
  ├── utils/quiz_engine/   (runs loop → SessionResult)
  │       ├── utils/models/
  │       └── utils/strategies/
  │
  ├── utils/ui/            (I/O only, no business logic)
  │       └── utils/models/
  │
  └── utils/db/            (session creation and result persistence)
          ├── utils/models/
          └── DatabaseConnection (singleton)
```

Data flow:

```
JSON file
  → data_loader.load()        → list[Flashcard]
  → db.create_session()       → session_id (UUID)
  → strategy.order()          → list[Flashcard] (ordered)
  → quiz_engine.run()         → SessionResult
  → db.save_results()         → persisted to SQLite
  → ui.show_summary()         → terminal output
```

The `AdaptiveStrategy` additionally reads prior-session results from the database at ordering time:

```
db.get_missed_cards(dataset)  → list[str]   (fronts the user got wrong before)
  → adaptive.order()          → missed cards first, rest appended
```

---

## 4. File / Folder Structure

```
submission/
├── main.py                          # Typer entry point
├── data/
│   └── sample_cards.json            # Sample flashcard deck
├── utils/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py              # exports: Flashcard, SessionResult
│   │   └── models.py
│   ├── data_loader/
│   │   ├── __init__.py              # exports: load_flashcards
│   │   └── data_loader.py
│   ├── strategies/
│   │   ├── __init__.py              # exports: QuizMode, SequentialStrategy, RandomStrategy, AdaptiveStrategy
│   │   ├── base.py                  # QuizMode ABC
│   │   ├── sequential.py
│   │   ├── random_strategy.py
│   │   └── adaptive.py
│   ├── quiz_engine/
│   │   ├── __init__.py              # exports: QuizEngine
│   │   └── quiz_engine.py
│   ├── ui/
│   │   ├── __init__.py              # exports: UI
│   │   └── ui.py
│   └── db/
│       ├── __init__.py              # exports: DatabaseConnection, SessionRepository
│       ├── connection.py            # DatabaseConnection singleton
│       └── session_repository.py   # session creation and result persistence
├── tests/
│   ├── __init__.py
│   ├── data_loader/
│   │   ├── __init__.py
│   │   └── test_data_loader.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   └── test_strategies.py
│   ├── quiz_engine/
│   │   ├── __init__.py
│   │   └── test_quiz_engine.py
│   ├── ui/
│   │   ├── __init__.py
│   │   └── test_ui.py
│   └── db/
│       ├── __init__.py
│       └── test_session_repository.py
├── docs/
│   └── ARCHITECTURE.md              # this file
└── requirements.txt
```

Each package's `__init__.py` re-exports the public surface so callers import from the package, not from internal modules:

```python
# utils/strategies/__init__.py
from .base import QuizMode
from .sequential import SequentialStrategy
from .random_strategy import RandomStrategy
from .adaptive import AdaptiveStrategy
```

---

## 5. CLI Entry Point (`main.py`)

`main.py` hosts a **Typer** application that is the single entry point for the flashcard quiz. It wires CLI arguments to the internal modules and handles errors before they reach the user as raw tracebacks.

### Invocation

```bash
# via Python
python main.py DECK_FILE [--mode sequential|random|adaptive]

# via installed script (registered in pyproject.toml)
flashcard DECK_FILE [--mode sequential|random|adaptive]
```

### Arguments and Options

| Parameter | CLI form | Type | Default | Description |
|---|---|---|---|---|
| `deck_file` | positional argument | `Path` | required | Path to the JSON flashcard deck |
| `mode` | `--mode` | `str` | `sequential` | Quiz mode: `sequential`, `random`, or `adaptive` |

### `pyproject.toml` Script Entry

```toml
[project.scripts]
flashcard = "main:app"
```

This registers the `flashcard` command so the app can be called without `python`.

### Application Flow

```
main(deck_file, mode)
  ├── validate mode  ──────────────────────────────► typer.Exit(1) + message on unknown mode
  ├── load_flashcards(deck_file) → list[Flashcard]  ► typer.Exit(1) + message on file/parse error
  ├── DatabaseConnection().connect(db_path)
  ├── SessionRepository.create_session(deck_file)   → session_id
  ├── strategy.order(cards)                         → ordered list[Flashcard]
  ├── ui = TerminalRichUI()                         → default rich renderer
  ├── QuizEngine(strategy, ui).run(cards)           → SessionResult
  ├── SessionRepository.save_session_result(session_id, result)
  ├── ui.show_summary(result)
  └── DatabaseConnection().disconnect()
```

### Error Handling

All user-facing errors use `typer.Exit(code=1)` paired with a plain `typer.echo` message. No raw tracebacks are shown. Two categories of error are handled:

| Source | Error | User message |
|---|---|---|
| `load_flashcards` | File not found | `"Deck file not found: <path>"` |
| `load_flashcards` | Invalid JSON / schema | `"Could not read deck: <reason>"` |
| `main` | Unknown `--mode` value | `"Unknown mode '<value>'. Choose: sequential, random, adaptive."` |

### Mode → Strategy Mapping

```python
STRATEGIES: dict[str, type[QuizMode]] = {
    "sequential": SequentialStrategy,
    "random": RandomStrategy,
    "adaptive": AdaptiveStrategy,
}
```

`main` looks up the mode string in this dict; an unknown key prints the error message and exits before any I/O occurs.

---

## 6. Key Interfaces

### `Flashcard` (`utils/models/`)
```python
@dataclass
class Flashcard:
    front: str   # the question / term shown to the user
    back: str    # the expected answer
```

### `SessionResult` (`utils/models/`)
```python
@dataclass
class SessionResult:
    total: int
    correct: int
    missed: list[str]   # list of `front` values the user got wrong
```

### `QuizMode` ABC (`utils/strategies/base.py`)
```python
class QuizMode(ABC):
    @abstractmethod
    def order(self, cards: list[Flashcard]) -> list[Flashcard]: ...
```

### `CardsDataLoader` (`utils/data_loader/`)
```python
class CardsDataLoader:
    def load(self, path: Path | str) -> list[Flashcard]:
        """Load and validate a JSON deck. Raises on any error."""
```

`CardsDataLoader` is the internal implementation class. It is testable in isolation and accepts both `Path` and `str` arguments.

### `load_flashcards` (`utils/data_loader/`)
```python
def load_flashcards(path: Path) -> list[Flashcard]:
    """Load and validate a JSON deck. Raises typer.Exit on any error."""
```

`load_flashcards` is the public CLI-facing wrapper that delegates to `CardsDataLoader` and converts exceptions into user-friendly `typer.Exit` calls.

Supported JSON schemas:

```json
[
  {"front": "CPU", "back": "Central Processing Unit"},
  {"front": "RAM", "back": "Random Access Memory"}
]
```

```json
{
  "cards": [
    {"front": "CPU", "back": "Central Processing Unit"},
    {"front": "RAM", "back": "Random Access Memory"}
  ]
}
```

Both formats are equivalent. The wrapped format (`{"cards": [...]}`) exists to accommodate deck files that carry additional top-level metadata alongside the card list.

### `UI` Protocol (`utils/ui/`)
```python
class UI(Protocol):
    """Terminal I/O contract — any object with these methods qualifies."""

    def prompt_answer(self, card: Flashcard) -> str: ...
    def show_feedback(self, correct: bool, expected: str) -> None: ...
    def show_summary(self, result: SessionResult) -> None: ...
```

### `TerminalRichUI` (`utils/ui/`)
```python
class TerminalRichUI:
    """`rich`-styled implementation of the UI Protocol.

    Aesthetic-only: identical I/O behaviour to TerminalUI, richer rendering.
    """

    def __init__(self, console: Console | None = None) -> None:
        """Use the given Console, or create a default one."""

    def prompt_answer(self, card: Flashcard) -> str:
        """Show the styled card front; return the user's answer (stripped)."""

    def show_feedback(self, correct: bool, expected: str) -> None:
        """Render a green 'Correct!' panel, or a red panel with the answer."""

    def show_summary(self, result: SessionResult) -> None:
        """Render a score table and a panel listing any missed cards."""
```

`TerminalRichUI` is injected into `QuizEngine` exactly where `TerminalUI` was. `main.py` constructs it as the default renderer; swapping back to `TerminalUI` requires no other change. The optional `console` parameter exists for testing — pass a `Console(file=StringIO())` to capture output.

### `QuizEngine` (`utils/quiz_engine/`)
```python
class QuizEngine:
    def __init__(self, strategy: QuizMode, ui: UI) -> None: ...
    def run(self, cards: list[Flashcard]) -> SessionResult: ...
```

`QuizEngine` accepts any `UI` — `TerminalUI` or `TerminalRichUI` — via constructor injection.

### `DatabaseConnection` (`utils/db/connection.py`)
```python
class DatabaseConnection:
    """Singleton managing the SQLite connection for the process lifetime."""

    def connect(self, db_path: Path) -> None:
        """Open the connection; create schema if the file is new."""

    def disconnect(self) -> None:
        """Commit and close the connection."""

    def execute(self, query: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
        """Execute a query and return rows as dicts."""

    @classmethod
    def _reset(cls) -> None:
        """Reset the singleton — for use in tests only."""
```

Only one instance is ever created (see Singleton pattern in §2). Call `connect()` once at application startup (in `main.py`) and `disconnect()` at shutdown. `disconnect()` is called exclusively by `main.py`; `SessionRepository` does not own the connection lifecycle.

### `SessionRepository` (`utils/db/session_repository.py`)
```python
class SessionRepository:
    def __init__(self, db: DatabaseConnection) -> None: ...

    def create_session(self, dataset: str) -> str:
        """Create a new session row and return its UUID."""

    def save_session_result(self, session_id: str, result: SessionResult) -> None:
        """Persist the completed session result as a JSON blob."""

    def get_missed_cards(self, dataset: str) -> list[str]:
        """Return card fronts the user got wrong in the most recent session for this dataset."""
```

`SessionRepository` takes a `DatabaseConnection` via constructor injection, which keeps it testable: tests pass a tmp-path connection without touching the singleton.

#### Database Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,   -- UUID4
    dataset    TEXT NOT NULL,      -- path or name of the JSON deck
    created_at TEXT NOT NULL,      -- ISO-8601 timestamp
    result     TEXT                -- JSON blob, NULL until the session completes
);
```

The completed `SessionResult` (total, correct, missed) is stored as a JSON blob in the `result` column. This keeps the schema simple and avoids a separate `card_results` table.

---

## 7. Extension Points

### Adding a new quiz mode

1. Create a new file in `utils/strategies/` subclassing `QuizMode` and implementing `order()`.
2. Re-export the new class from `utils/strategies/__init__.py`.
3. Add the mode name → class mapping in `main.py`.
4. Add tests in `tests/strategies/test_strategies.py`.

No other files need to change.

### Example: Spaced Repetition
```python
# utils/strategies/spaced_repetition.py
class SpacedRepetitionStrategy(QuizMode):
    def __init__(self, due_dates: dict[str, date]) -> None:
        self.due_dates = due_dates

    def order(self, cards: list[Flashcard]) -> list[Flashcard]:
        today = date.today()
        return sorted(cards, key=lambda c: self.due_dates.get(c.front, today))
```

### Adding session persistence

Session tracking is already wired in via `utils/db/`. To extend persistence (e.g. track response time per card):

1. Add a field to `SessionResult` in `utils/models/`.
2. Update `SessionResult.to_json()` (via `dataclasses.asdict`) to include the new field automatically.
3. Update `QuizEngine` to capture and pass the new data.

No strategy or UI code needs to change.

### Swapping the database backend

Replace `DatabaseConnection` with a subclass that wraps a different backend (e.g. PostgreSQL via `psycopg2`). Because `SessionRepository` depends only on the `DatabaseConnection` interface, all repository code works without modification.
