"""Adaptive quiz strategy — re-weights missed cards for higher draw probability."""

import random

from utils.models import Flashcard
from utils.strategies.base import QuizMode

_MISSED_WEIGHT_MULTIPLIER: float = 2.0


class AdaptiveStrategy(QuizMode):
    """Present cards using weighted random draws.

    Cards answered incorrectly have their weight doubled, making them
    progressively more likely to be drawn again within the same session.
    Total draws equal the original deck size.
    """

    def __init__(self) -> None:
        self._cards: list[Flashcard] | None = None
        self._card_index: dict[str, int] = {}
        self._weights: list[float] = []
        self._drawn: int = 0
        self._total: int = 0

    def setup(self, cards: list[Flashcard]) -> None:
        self._cards = list(cards)
        self._card_index = {c.front: i for i, c in enumerate(cards)}
        self._weights = [1.0] * len(cards)
        self._drawn = 0
        self._total = len(cards)

    def get_next_card(self) -> Flashcard | None:
        if self._cards is None:
            raise RuntimeError("call setup() before get_next_card()")
        if self._drawn >= self._total:
            return None
        self._drawn += 1
        return random.choices(self._cards, weights=self._weights, k=1)[0]

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Record whether a card was answered correctly and update its draw weight.

        A missed card has its weight multiplied by ``_MISSED_WEIGHT_MULTIPLIER``,
        increasing the probability of it being drawn again.  If the card is later
        answered correctly its weight is reset to ``1.0``.

        Args:
            card: The flashcard that was just answered.
            correct: ``True`` if the answer was correct, ``False`` otherwise.

        Raises:
            ValueError: If *card* is not part of the current deck.
        """
        if card.front not in self._card_index:
            raise ValueError(f"Card '{card.front}' not found in the current deck")
        idx = self._card_index[card.front]
        if correct:
            self._weights[idx] = 1.0
        else:
            self._weights[idx] *= _MISSED_WEIGHT_MULTIPLIER
