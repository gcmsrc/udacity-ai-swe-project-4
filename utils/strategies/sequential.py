from utils.models import Flashcard
from utils.strategies.base import QuizStrategy


class SequentialStrategy(QuizStrategy):
    """Present cards in the original deck order."""

    def order(self, cards: list[Flashcard]) -> list[Flashcard]:
        raise NotImplementedError
