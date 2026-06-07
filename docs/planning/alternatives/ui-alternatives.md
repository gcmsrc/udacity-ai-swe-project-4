# UI Module Alternatives

Current state: `utils/ui/ui.py` defines a `UI` class with stub methods that raise `NotImplementedError`.
The `QuizEngine` receives a `UI` instance and calls three methods on it:
- `prompt_answer(card)` → `str`
- `show_feedback(correct, expected)` → `None`
- `show_summary(result)` → `None`

---

## Alternative 1 — Abstract Base Class (ABC)

**Design.** `UI` becomes a proper ABC using `abc.ABC` and `@abstractmethod`. A concrete
`TerminalUI` subclass provides the implementation. `QuizEngine` is typed against the abstract
`UI`, so any subclass is accepted.

```python
# utils/ui/ui.py
from abc import ABC, abstractmethod
from utils.models import Flashcard, SessionResult


class UI(ABC):
    """Contract for all terminal I/O implementations."""

    @abstractmethod
    def prompt_answer(self, card: Flashcard) -> str: ...

    @abstractmethod
    def show_feedback(self, correct: bool, expected: str) -> None: ...

    @abstractmethod
    def show_summary(self, result: SessionResult) -> None: ...


class TerminalUI(UI):
    """Plain print/input implementation."""

    def prompt_answer(self, card: Flashcard) -> str:
        return input(f"{card.front}: ").strip()

    def show_feedback(self, correct: bool, expected: str) -> None:
        if correct:
            print("Correct!")
        else:
            print(f"Wrong. Answer: {expected}")

    def show_summary(self, result: SessionResult) -> None:
        ratio = result.correct / result.total if result.total else 0
        print(f"\nResult: {result.correct}/{result.total} ({ratio:.0%})")
        if result.missed:
            print("Missed:", ", ".join(result.missed))
```

**Trade-offs.**

| + | - |
|---|---|
| Enforces the contract at instantiation time (can't forget a method) | Requires explicit inheritance — coupling concrete classes to this module |
| Works well with `isinstance` checks and type narrowing | Slightly more boilerplate than needed for a single implementation |
| Familiar OOP pattern, easy to extend | Harder to compose or wrap without subclassing |

---

## Alternative 2 — Protocol (structural subtyping)

**Design.** `UI` is a `typing.Protocol`. `QuizEngine` is typed against it. Any class that
exposes the three methods satisfies the protocol — no inheritance required. This follows the
Dependency Inversion Principle strictly: the engine depends on a structural interface, not a
class hierarchy.

```python
# utils/ui/ui.py
from typing import Protocol
from utils.models import Flashcard, SessionResult


class UI(Protocol):
    """Structural interface — any object with these three methods qualifies."""

    def prompt_answer(self, card: Flashcard) -> str: ...
    def show_feedback(self, correct: bool, expected: str) -> None: ...
    def show_summary(self, result: SessionResult) -> None: ...


# Concrete implementation — no inheritance needed
class TerminalUI:
    def prompt_answer(self, card: Flashcard) -> str:
        return input(f"{card.front}: ").strip()

    def show_feedback(self, correct: bool, expected: str) -> None:
        if correct:
            print("Correct!")
        else:
            print(f"Wrong. Answer: {expected}")

    def show_summary(self, result: SessionResult) -> None:
        ratio = result.correct / result.total if result.total else 0
        print(f"\nResult: {result.correct}/{result.total} ({ratio:.0%})")
        if result.missed:
            print("Missed:", ", ".join(result.missed))
```

**Trade-offs.**

| + | - |
|---|---|
| Zero coupling between `TerminalUI` and the `UI` protocol | Missing methods are only caught by `mypy`, not at runtime |
| Test doubles (`unittest.mock.Mock`) satisfy the protocol automatically | Less discoverable — new developers may not find the protocol |
| Aligns with modern Python typing (PEP 544) | `isinstance(obj, UI)` always returns `False` unless `runtime_checkable` is added |

---

## Alternative 3 — Dataclass of callables (functional composition)

**Design.** `UI` is a `dataclass` with three callable fields. A factory function
`terminal_ui()` returns a pre-wired instance. `QuizEngine` calls the fields as regular
callables. Behaviour is swapped by passing different functions — no subclassing at all.

```python
# utils/ui/ui.py
from dataclasses import dataclass
from typing import Callable
from utils.models import Flashcard, SessionResult


@dataclass
class UI:
    """Bundle of I/O callables injected into QuizEngine."""

    prompt_answer: Callable[[Flashcard], str]
    show_feedback: Callable[[bool, str], None]
    show_summary: Callable[[SessionResult], None]


def _prompt(card: Flashcard) -> str:
    return input(f"{card.front}: ").strip()


def _feedback(correct: bool, expected: str) -> None:
    print("Correct!" if correct else f"Wrong. Answer: {expected}")


def _summary(result: SessionResult) -> None:
    ratio = result.correct / result.total if result.total else 0
    print(f"\nResult: {result.correct}/{result.total} ({ratio:.0%})")
    if result.missed:
        print("Missed:", ", ".join(result.missed))


def terminal_ui() -> UI:
    """Return a UI wired to standard terminal I/O."""
    return UI(prompt_answer=_prompt, show_feedback=_feedback, show_summary=_summary)
```

**Usage in tests — no mocking framework needed:**

```python
ui = UI(
    prompt_answer=lambda card: "test answer",
    show_feedback=lambda correct, expected: None,
    show_summary=lambda result: None,
)
```

**Trade-offs.**

| + | - |
|---|---|
| Trivially testable — swap any callable with a lambda | No enforcement of signatures; wrong callables fail only at call time |
| No class hierarchy to maintain | Less intuitive for developers expecting OOP patterns |
| Easy to compose (e.g. logging wrapper = replace one callable) | `mypy` inference on callable fields is less precise than method signatures |

---

## Recommendation

**Alternative 2 (Protocol)** is the best fit for this codebase because:

1. `QuizEngine` already uses dependency injection — the Protocol documents the exact contract
   without creating inheritance coupling.
2. `unittest.mock.Mock()` satisfies it out of the box, matching the existing test style in
   `tests/ui/test_ui.py`.
3. `mypy` (already in the toolchain) will catch missing methods at type-check time, making the
   runtime behaviour of Alternative 1 redundant.

Alternative 1 (ABC) is a safe fallback if explicit runtime enforcement is required.
Alternative 3 suits a more functional style or scenarios where individual behaviours need to
be composed at runtime (e.g. a logging decorator on just `show_feedback`).
