import json
from dataclasses import asdict, dataclass, field


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

    @property
    def score(self) -> float:
        """Fraction of correct answers; 0.0 when total is zero."""
        return self.correct / self.total if self.total else 0.0

    def to_json(self) -> str:
        """Serialise the result to a JSON string."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, s: str) -> "SessionResult":
        """Deserialise a SessionResult from a JSON string."""
        data = json.loads(s)
        return cls(total=data["total"], correct=data["correct"], missed=data.get("missed", []))
