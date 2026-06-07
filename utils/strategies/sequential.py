"""Sequential quiz strategy — preserves the original deck order."""

from utils.models import Flashcard
from utils.strategies.base import _BaseIndexedStrategy


class SequentialStrategy(_BaseIndexedStrategy):
    """Return cards in the same order they appear in the deck."""

    def setup(self, cards: list[Flashcard]) -> None:
        self._cards = list(cards)
        self._index = 0
