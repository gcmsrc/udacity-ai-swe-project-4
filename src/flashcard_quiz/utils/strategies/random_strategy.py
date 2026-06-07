"""Random quiz strategy — shuffles the deck before presentation."""

import random

from flashcard_quiz.utils.models import Flashcard
from flashcard_quiz.utils.strategies.base import _BaseIndexedStrategy


class RandomStrategy(_BaseIndexedStrategy):
    """Return cards in a randomly shuffled order."""

    def setup(self, cards: list[Flashcard]) -> None:
        self._cards = list(cards)
        random.shuffle(self._cards)
        self._index = 0
