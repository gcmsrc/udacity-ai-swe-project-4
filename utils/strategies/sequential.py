"""Sequential quiz strategy — preserves the original deck order."""

from utils.models import Flashcard
from utils.strategies.base import QuizMode


class SequentialStrategy(QuizMode):
    """Return cards in the same order they appear in the deck."""

    def order(self, cards: list[Flashcard]) -> list[Flashcard]:
        """Return a copy of *cards* in their original order.

        Args:
            cards: the full deck to order.

        Returns:
            A new list containing the same cards in the same order.
        """
        return list(cards)
