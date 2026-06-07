from utils.models import Flashcard
from utils.strategies.base import QuizStrategy


class AdaptiveStrategy(QuizStrategy):
    """Present previously-missed cards first, then the rest.

    Args:
        missed: front-values of cards the user got wrong in a prior session.
    """

    def __init__(self, missed: list[str] | None = None) -> None:
        self.missed: list[str] = missed or []

    def order(self, cards: list[Flashcard]) -> list[Flashcard]:
        raise NotImplementedError
