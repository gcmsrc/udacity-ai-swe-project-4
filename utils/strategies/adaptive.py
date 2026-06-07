"""Adaptive quiz strategy — re-weights missed cards for higher draw probability."""

import random

from utils.models import Flashcard
from utils.strategies.base import QuizMode


class AdaptiveStrategy(QuizMode):
    """Present cards using weighted random draws.

    Cards answered incorrectly have their weight doubled, making them
    progressively more likely to be drawn again within the same session.
    Total draws equal the original deck size.
    """

    def __init__(self) -> None:
        self._cards: list[Flashcard] = []
        self._weights: list[float] = []
        self._drawn: int = 0
        self._total: int = 0

    def setup(self, cards: list[Flashcard]) -> None:
        self._cards = list(cards)
        self._weights = [1.0] * len(cards)
        self._drawn = 0
        self._total = len(cards)

    def get_next_card(self) -> Flashcard | None:
        if self._drawn >= self._total:
            return None
        self._drawn += 1
        return random.choices(self._cards, weights=self._weights, k=1)[0]

    def record_result(self, card: Flashcard, correct: bool) -> None:
        if not correct:
            idx = next(i for i, c in enumerate(self._cards) if c.front == card.front)
            self._weights[idx] *= 2.0
