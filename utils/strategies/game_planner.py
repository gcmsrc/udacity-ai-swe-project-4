"""Context class for the Strategy pattern — holds and executes a quiz strategy."""

from utils.models import Flashcard
from utils.strategies.base import QuizMode


class GamePlanner:
    """Context that delegates card ordering to a :class:`QuizMode` strategy.

    The strategy can be swapped at any time via :meth:`set_strategy`.
    """

    def __init__(self, strategy: QuizMode) -> None:
        """Initialise with an initial strategy.

        Args:
            strategy: the ordering strategy to use.
        """
        self._strategy = strategy

    def set_strategy(self, strategy: QuizMode) -> None:
        """Replace the current strategy.

        Args:
            strategy: the new ordering strategy to use.
        """
        self._strategy = strategy

    def plan(self, cards: list[Flashcard]) -> list[Flashcard]:
        """Order *cards* using the current strategy.

        Args:
            cards: the full deck to order.

        Returns:
            A (possibly re-ordered) list of the same cards.
        """
        return self._strategy.order(cards)
