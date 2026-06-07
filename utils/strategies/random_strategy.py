"""Random quiz strategy — shuffles the deck before presentation."""

import random

from utils.models import Flashcard
from utils.strategies.base import QuizMode


class RandomStrategy(QuizMode):
    """Return cards in a randomly shuffled order."""

    def order(self, cards: list[Flashcard]) -> list[Flashcard]:
        """Return a shuffled copy of *cards*.

        Args:
            cards: the full deck to order.

        Returns:
            A new list containing the same cards in random order.
        """
        shuffled = list(cards)
        random.shuffle(shuffled)
        return shuffled
