"""Sequential quiz strategy — preserves the original deck order."""

from flashcard_quiz.utils.models import Flashcard
from flashcard_quiz.utils.strategies.base import _BaseIndexedStrategy


class SequentialStrategy(_BaseIndexedStrategy):
    """Return cards in the same order they appear in the deck."""

    def setup(self, cards: list[Flashcard]) -> None:
        self._cards = list(cards)
        self._index = 0
