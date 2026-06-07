# Architecture: CLI Flashcard Application

## 1. Module Overview

| Package | Responsibility |
|---|---|
| `utils/models/` | Data classes: `Flashcard`, `SessionResult` |
| `utils/data_loader/` | Load and validate JSON; raise user-friendly errors |
| `utils/strategies/` | `QuizMode` ABC + Sequential / Random / Adaptive implementations |
| `utils/quiz_engine/` | Runs the quiz loop; owns answer-checking and score tracking |
| `utils/ui/` | All terminal I/O: prompts, feedback, summary table |
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
  └── utils/ui/            (I/O only, no business logic)
          └── utils/models/
```

Data flow:

```
JSON file
  → data_loader.load()  → list[Flashcard]
  → strategy.order()    → list[Flashcard] (ordered)
  → quiz_engine.run()   → SessionResult
  → ui.show_summary()   → terminal output
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
│   └── ui/
│       ├── __init__.py              # exports: UI
│       └── ui.py
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
│   └── ui/
│       ├── __init__.py
│       └── test_ui.py
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

Adding persistence (e.g. saving missed cards across sessions) only requires a new module inside `utils/` — the engine and strategies remain untouched.
