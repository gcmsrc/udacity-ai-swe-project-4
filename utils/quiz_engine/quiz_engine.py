from utils.models import Flashcard, SessionResult
from utils.strategies.base import QuizMode
from utils.ui import UI


class QuizEngine:
    """Drives the quiz loop: present cards, collect answers, track score."""

    def __init__(self, strategy: QuizMode, ui: UI) -> None:
        """Args:
        strategy: determines card ordering.
        ui: handles all terminal I/O.
        """
        raise NotImplementedError

    def run(self, cards: list[Flashcard]) -> SessionResult:
        """Run a full quiz session and return the result.

        Args:
            cards: the deck to quiz on.

        Returns:
            A SessionResult with totals and missed card fronts.
        """
        raise NotImplementedError
