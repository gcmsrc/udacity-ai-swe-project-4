from abc import ABC, abstractmethod

from utils.models import Flashcard


class QuizStrategy(ABC):
    """Contract for all quiz-ordering strategies."""

    @abstractmethod
    def order(self, cards: list[Flashcard]) -> list[Flashcard]:
        """Return cards in the order they should be presented.

        Args:
            cards: the full deck to order.

        Returns:
            A (possibly re-ordered) list of the same cards.
        """
