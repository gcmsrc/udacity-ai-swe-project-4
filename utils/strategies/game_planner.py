"""Context class for the Strategy pattern — holds and swaps a quiz strategy."""

from utils.strategies.base import QuizMode


class GamePlanner:
    """Context that holds a :class:`QuizMode` strategy and allows swapping it.

    The strategy is passed to :class:`~utils.quiz_engine.QuizEngine` for
    execution. Session lifecycle (create / save) is handled at a higher level.
    """

    def __init__(self, strategy: QuizMode) -> None:
        self._strategy = strategy

    def set_strategy(self, strategy: QuizMode) -> None:
        """Replace the current strategy.

        Args:
            strategy: the new ordering strategy to use.
        """
        self._strategy = strategy

    @property
    def strategy(self) -> QuizMode:
        """The active strategy."""
        return self._strategy
