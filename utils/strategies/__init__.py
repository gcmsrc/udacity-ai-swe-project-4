"""Quiz strategy package — exports concrete strategies and a factory."""

from .adaptive import AdaptiveStrategy
from .base import QuizMode
from .game_planner import GamePlanner
from .random_strategy import RandomStrategy
from .sequential import SequentialStrategy

__all__ = [
    "QuizMode",
    "SequentialStrategy",
    "RandomStrategy",
    "AdaptiveStrategy",
    "GamePlanner",
]

_REGISTRY: dict[str, type[QuizMode]] = {
    "sequential": SequentialStrategy,
    "random": RandomStrategy,
    "adaptive": AdaptiveStrategy,
}


def get_strategy(mode: str) -> QuizMode:
    """Instantiate and return the strategy for *mode*.

    Args:
        mode: strategy name; supported values are derived from the internal registry.

    Returns:
        A concrete :class:`QuizMode` instance.

    Raises:
        ValueError: if *mode* is not a supported strategy name.
    """
    if mode not in _REGISTRY:
        supported = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown strategy '{mode}'. Supported: {supported}.")
    return _REGISTRY[mode]()
