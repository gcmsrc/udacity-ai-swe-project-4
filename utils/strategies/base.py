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

    def record_result(self, card: Flashcard, correct: bool) -> None:  # noqa: ARG002
        """Feed back the result of the last answer.

        No-op for strategies that do not adapt to user performance.

        Args:
            card: the card that was just answered.
            correct: whether the user's answer was correct.
        """
