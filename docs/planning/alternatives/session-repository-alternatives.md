# Alternatives: SessionRepository Handling between GamePlanner and Strategy

## Context

`GamePlanner` is the Strategy-pattern context class. It holds a `QuizMode` strategy and delegates card ordering to it. `GamePlanner` must also own the session lifecycle: create a session, store its result, retrieve missed cards, and close it.

The problem is `AdaptiveStrategy`: it needs the missed cards from the most recent session (via `SessionRepository.get_missed_cards`) to do its work. Giving the strategy direct access to the repository creates tight coupling between the ordering algorithm and the persistence layer.

Three alternatives are presented below, each reflecting a different coupling trade-off.

---

## Alternative 1: `configure()` Hook on `QuizMode` (Template Method variant)

### Idea

Add an optional `configure(missed_cards: list[str]) -> None` hook to the `QuizMode` ABC with a no-op default. `GamePlanner` holds `SessionRepository`, fetches missed cards before calling `order()`, and passes them via `configure()`. Only `AdaptiveStrategy` overrides the hook; all other strategies inherit the no-op.

### Code sketch

```python
# utils/strategies/base.py
class QuizMode(ABC):
    def configure(self, missed_cards: list[str]) -> None:
        """Pre-order hook for strategies that need historical data. No-op by default."""

    @abstractmethod
    def order(self, cards: list[Flashcard]) -> list[Flashcard]: ...


# utils/strategies/adaptive.py
class AdaptiveStrategy(QuizMode):
    def __init__(self) -> None:
        self._missed: list[str] = []

    def configure(self, missed_cards: list[str]) -> None:
        self._missed = missed_cards

    def order(self, cards: list[Flashcard]) -> list[Flashcard]:
        missed_set = set(self._missed)
        missed = [c for c in cards if c.front in missed_set]
        rest   = [c for c in cards if c.front not in missed_set]
        return missed + rest


# utils/strategies/game_planner.py
class GamePlanner:
    def __init__(self, strategy: QuizMode, repo: SessionRepository) -> None:
        self._strategy = strategy
        self._repo = repo
        self._session_id: str | None = None

    def start_session(self, dataset: str) -> None:
        self._dataset = dataset
        missed = self._repo.get_missed_cards(dataset)
        self._strategy.configure(missed)
        self._session_id = self._repo.create_session(dataset)

    def plan(self, cards: list[Flashcard]) -> list[Flashcard]:
        return self._strategy.order(cards)

    def finish_session(self, result: SessionResult) -> None:
        self._repo.save_session_result(self._session_id, result)

    def close(self) -> None:
        self._session_id = None
```

### Trade-offs

| | |
|---|---|
| **Pro** | Strategies stay unaware of `SessionRepository`. `AdaptiveStrategy` holds plain data (`list[str]`), not a repo reference. |
| **Pro** | The hook is opt-in: simple strategies get a free no-op, no interface bloat. |
| **Con** | `QuizMode` grows a method (`configure`) that most implementations never use. This can feel like interface pollution if the strategy hierarchy grows. |
| **Con** | The protocol between `GamePlanner` and strategy is implicit: callers must remember to call `start_session()` before `plan()`. |

---

## Alternative 2: Callable Provider Injection into `AdaptiveStrategy`

### Idea

`AdaptiveStrategy.__init__` accepts a `Callable[[str], list[str]]` — a function that takes a dataset name and returns missed cards. `GamePlanner` owns `SessionRepository` and wires `repo.get_missed_cards` as the provider when constructing the strategy. The strategy calls the provider lazily at `order()` time. `GamePlanner` never interrogates the strategy's type.

### Code sketch

```python
# utils/strategies/adaptive.py
from collections.abc import Callable

class AdaptiveStrategy(QuizMode):
    def __init__(self, missed_provider: Callable[[str], list[str]]) -> None:
        self._missed_provider = missed_provider

    def order(self, cards: list[Flashcard], dataset: str = "") -> list[Flashcard]:
        missed_set = set(self._missed_provider(dataset))
        missed = [c for c in cards if c.front in missed_set]
        rest   = [c for c in cards if c.front not in missed_set]
        return missed + rest


# utils/strategies/game_planner.py
class GamePlanner:
    def __init__(self, strategy: QuizMode, repo: SessionRepository) -> None:
        self._strategy = strategy
        self._repo = repo
        self._session_id: str | None = None

    def start_session(self, dataset: str) -> None:
        self._dataset = dataset
        self._session_id = self._repo.create_session(dataset)

    def plan(self, cards: list[Flashcard]) -> list[Flashcard]:
        return self._strategy.order(cards, self._dataset)

    def finish_session(self, result: SessionResult) -> None:
        self._repo.save_session_result(self._session_id, result)

    def close(self) -> None:
        self._session_id = None


# Wiring in main.py
repo = SessionRepository(db)
strategy = AdaptiveStrategy(missed_provider=repo.get_missed_cards)
planner  = GamePlanner(strategy, repo)
```

### Trade-offs

| | |
|---|---|
| **Pro** | `AdaptiveStrategy` depends on a callable, not on `SessionRepository` — the dependency is inverted at its narrowest point. Trivial to test: pass `lambda _: ["card_front"]`. |
| **Pro** | `GamePlanner` is unaware of strategy internals; no `isinstance` check, no type-specific branching. |
| **Con** | `QuizMode.order()` signature must change to accept `dataset: str`, or `AdaptiveStrategy` must capture the dataset at construction time (tying it to a single deck). |
| **Con** | The callable is called once per `order()` invocation, which triggers a DB read every time `plan()` is called. May need caching if `plan()` is called in a tight loop. |

---

## Alternative 3: `OrderingContext` Passed Through `plan()`

### Idea

Define a lightweight `OrderingContext` dataclass that carries per-plan metadata (including `missed_cards`). Change `QuizMode.order()` to accept it. `GamePlanner.plan()` fetches missed cards from `SessionRepository`, builds the context, and passes it to the strategy. Strategies that don't need historical data simply ignore `context.missed_cards`.

### Code sketch

```python
# utils/models/models.py  (or utils/strategies/context.py)
@dataclass
class OrderingContext:
    dataset: str
    missed_cards: list[str] = field(default_factory=list)


# utils/strategies/base.py
class QuizMode(ABC):
    @abstractmethod
    def order(self, cards: list[Flashcard], context: OrderingContext) -> list[Flashcard]: ...


# utils/strategies/sequential.py
class SequentialStrategy(QuizMode):
    def order(self, cards: list[Flashcard], context: OrderingContext) -> list[Flashcard]:
        return list(cards)


# utils/strategies/adaptive.py
class AdaptiveStrategy(QuizMode):
    def order(self, cards: list[Flashcard], context: OrderingContext) -> list[Flashcard]:
        missed_set = set(context.missed_cards)
        missed = [c for c in cards if c.front in missed_set]
        rest   = [c for c in cards if c.front not in missed_set]
        return missed + rest


# utils/strategies/game_planner.py
class GamePlanner:
    def __init__(self, strategy: QuizMode, repo: SessionRepository) -> None:
        self._strategy = strategy
        self._repo = repo
        self._session_id: str | None = None
        self._dataset: str = ""

    def start_session(self, dataset: str) -> None:
        self._dataset = dataset
        self._session_id = self._repo.create_session(dataset)

    def plan(self, cards: list[Flashcard]) -> list[Flashcard]:
        missed = self._repo.get_missed_cards(self._dataset)
        context = OrderingContext(dataset=self._dataset, missed_cards=missed)
        return self._strategy.order(cards, context)

    def finish_session(self, result: SessionResult) -> None:
        self._repo.save_session_result(self._session_id, result)

    def close(self) -> None:
        self._session_id = None
```

### Trade-offs

| | |
|---|---|
| **Pro** | Strategies are pure functions of `(cards, context)` — no hidden state, no callbacks, trivially testable by constructing an `OrderingContext` inline. |
| **Pro** | `OrderingContext` is a natural extension point: future strategies (e.g. spaced repetition) can add fields without changing the `order()` signature. |
| **Con** | The `QuizMode` interface changes: all existing strategies must be updated to accept `context`, even though most ignore it. This is a breaking change for any external strategy implementations. |
| **Con** | `GamePlanner.plan()` always fetches missed cards from the DB, regardless of strategy type. For non-adaptive strategies this is an unnecessary read. |

---

## Summary Comparison

| Criterion | Alt 1: configure() hook | Alt 2: Callable provider | Alt 3: OrderingContext |
|---|---|---|---|
| Strategy awareness of repo | None | None | None |
| Interface change to `QuizMode` | Adds `configure()` | Changes `order()` signature | Changes `order()` signature |
| Testability of strategy | Inject list directly | Inject lambda | Construct context inline |
| DB read timing | At `start_session()` | Lazily at `order()` | At every `plan()` call |
| OCP for new strategy fields | No — needs new hook | No — needs new provider arg | Yes — extend `OrderingContext` |
| Coupling surface | `GamePlanner` ↔ strategy via hook contract | `AdaptiveStrategy` ↔ callable | `GamePlanner` ↔ repo (centralised) |

**Recommendation:** Alternative 3 (`OrderingContext`) is the most extensible and keeps the clearest data-flow: all historical data passes through a single, typed object that `GamePlanner` owns and strategies consume as plain input. The one-time breaking change to `QuizMode.order()` is acceptable given the small number of existing strategies and the long-term benefit of a stable, enrichable context object.
