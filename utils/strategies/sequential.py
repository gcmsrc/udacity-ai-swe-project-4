"""Sequential quiz strategy — preserves the original deck order."""

from utils.models import Flashcard
from utils.strategies.base import QuizMode


class SequentialStrategy(QuizMode):
    """Return cards in the same order they appear in the deck."""

    def __init__(self) -> None:
        self._cards: list[Flashcard] = []
        self._index: int = 0

    def setup(self, cards: list[Flashcard]) -> None:
        self._cards = list(cards)
        self._index = 0

    def get_next_card(self) -> Flashcard | None:
        if self._index >= len(self._cards):
            return None
        card = self._cards[self._index]
        self._index += 1
        return card
