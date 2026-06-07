# Architecture: CLI Flashcard Application

## 1. Module Overview

| Package | Responsibility |
|---|---|
| `utils/models/` | Data classes: `Flashcard`, `SessionResult` |
| `utils/data_loader/` | Load and validate JSON; raise user-friendly errors |
| `utils/strategies/` | `QuizMode` ABC + Sequential / Random / Adaptive implementations |
| `utils/quiz_engine/` | Runs the quiz loop; owns answer-checking and score tracking |
| `utils/ui/` | All terminal I/O: prompts, feedback, summary table |
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

## 5. Key Interfaces

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

### `QuizEngine` (`utils/quiz_engine/`)
```python
class QuizEngine:
    def __init__(self, strategy: QuizMode, ui: UI) -> None: ...
    def run(self, cards: list[Flashcard]) -> SessionResult: ...
```

### `DatabaseConnection` (`utils/db/connection.py`)
```python
class DatabaseConnection:
    """Singleton managing the SQLite connection for the process lifetime."""

    def connect(self, db_path: Path) -> None:
        """Open the connection; create schema if the file is new."""

    def disconnect(self) -> None:
        """Commit and close the connection."""

    def execute(self, query: str, params: tuple = ()) -> list[dict]:
        """Execute a query and return rows as dicts."""
```

Only one instance is ever created (see Singleton pattern in §2). Call `connect()` once at application startup (in `main.py`) and `disconnect()` at shutdown.

### `SessionRepository` (`utils/db/session_repository.py`)
```python
class SessionRepository:
    def __init__(self, db: DatabaseConnection) -> None: ...

    def create_session(self, dataset: str) -> str:
        """Create a new session row and return its UUID."""

    def save_result(self, session_id: str, card_front: str, correct: bool) -> None:
        """Persist a single card result for the given session."""

    def get_missed_cards(self, dataset: str) -> list[str]:
        """Return card fronts the user got wrong in any prior session for this dataset."""
```

`SessionRepository` takes a `DatabaseConnection` via constructor injection, which keeps it testable: tests pass an in-memory connection without touching the singleton.

#### Database Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id        TEXT PRIMARY KEY,   -- UUID4
    dataset   TEXT NOT NULL,      -- path or name of the JSON deck
    created_at TEXT NOT NULL      -- ISO-8601 timestamp
);

CREATE TABLE IF NOT EXISTS card_results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    card_front TEXT NOT NULL,
    correct    INTEGER NOT NULL   -- 1 = correct, 0 = incorrect
);
```

---

## 6. Extension Points

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

1. Add a column to `card_results` in the schema (migration or recreation).
2. Update `SessionRepository.save_result()` to accept and store the new field.
3. Update `QuizEngine` to capture and pass the new data.

No strategy or UI code needs to change.

### Swapping the database backend

Replace `DatabaseConnection` with a subclass that wraps a different backend (e.g. PostgreSQL via `psycopg2`). Because `SessionRepository` depends only on the `DatabaseConnection` interface, all repository code works without modification.
