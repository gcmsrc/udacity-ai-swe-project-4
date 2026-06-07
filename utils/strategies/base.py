from abc import ABC, abstractmethod

from utils.models import Flashcard


class QuizMode(ABC):
    """Contract for all quiz-ordering strategies."""

    @abstractmethod
    def setup(self, cards: list[Flashcard]) -> None:
        """Initialise the strategy with the full deck before the session starts.

        Args:
            cards: the deck to present during this session.
        """

    @abstractmethod
    def get_next_card(self) -> Flashcard | None:
        """Return the next card to present, or None when the session is complete.

        Returns:
            The next :class:`Flashcard`, or ``None`` if all draws are exhausted.
        """

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Feed back the result of the last answer.

        No-op for strategies that do not adapt to user performance.

        Args:
            card: the card that was just answered.
            correct: whether the user's answer was correct.
        """


class _BaseIndexedStrategy(QuizMode):
    """Shared index-walk implementation for non-adaptive strategies.

    Subclasses only need to implement ``setup()``.
    ``get_next_card()`` raises ``RuntimeError`` if called before ``setup()``.
    """

    def __init__(self) -> None:
        self._cards: list[Flashcard] | None = None
        self._index: int = 0

    def get_next_card(self) -> Flashcard | None:
        if self._cards is None:
            raise RuntimeError("call setup() before get_next_card()")
        if self._index >= len(self._cards):
            return None
        card = self._cards[self._index]
        self._index += 1
        return card
