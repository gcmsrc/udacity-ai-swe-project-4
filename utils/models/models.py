from dataclasses import dataclass, field


@dataclass
class Flashcard:
    """A single flashcard with a question (front) and answer (back)."""

    front: str
    back: str


@dataclass
class SessionResult:
    """Aggregate outcome of a completed quiz session."""

    total: int
    correct: int
    missed: list[str] = field(default_factory=list)
