from utils.models import Flashcard
from utils.strategies.base import QuizStrategy


class RandomStrategy(QuizStrategy):
    """Present cards in a randomly shuffled order."""

    def order(self, cards: list[Flashcard]) -> list[Flashcard]:
        raise NotImplementedError
