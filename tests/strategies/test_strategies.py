import pytest

from utils.models import Flashcard
from utils.strategies import (
    GamePlanner,
    RandomStrategy,
    SequentialStrategy,
    get_strategy,
)
from utils.strategies.base import QuizMode

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def deck() -> list[Flashcard]:
    return [
        Flashcard("CPU", "Central Processing Unit"),
        Flashcard("RAM", "Random Access Memory"),
        Flashcard("GPU", "Graphics Processing Unit"),
    ]


# ---------------------------------------------------------------------------
# QuizMode ABC
# ---------------------------------------------------------------------------


def test_quiz_strategy_is_abstract() -> None:
    """Instantiating the ABC directly must raise TypeError."""
    with pytest.raises(TypeError):
        QuizMode()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# SequentialStrategy
# ---------------------------------------------------------------------------


def test_sequential_preserves_order(deck: list[Flashcard]) -> None:
    result = SequentialStrategy().order(deck)
    assert result == deck


def test_sequential_does_not_mutate_input(deck: list[Flashcard]) -> None:
    original = list(deck)
    SequentialStrategy().order(deck)
    assert deck == original


# ---------------------------------------------------------------------------
# RandomStrategy
# ---------------------------------------------------------------------------


def test_random_returns_same_cards(deck: list[Flashcard]) -> None:
    result = RandomStrategy().order(deck)
    assert sorted(result, key=lambda c: c.front) == sorted(deck, key=lambda c: c.front)


def test_random_changes_order_statistically(deck: list[Flashcard]) -> None:
    orders = [tuple(c.front for c in RandomStrategy().order(deck)) for _ in range(50)]
    assert len(set(orders)) > 1, "RandomStrategy never produced a different order"


def test_random_does_not_mutate_input(deck: list[Flashcard]) -> None:
    original = list(deck)
    RandomStrategy().order(deck)
    assert deck == original


# ---------------------------------------------------------------------------
# get_strategy factory
# ---------------------------------------------------------------------------


def test_factory_returns_sequential() -> None:
    assert isinstance(get_strategy("sequential"), SequentialStrategy)


def test_factory_returns_random() -> None:
    assert isinstance(get_strategy("random"), RandomStrategy)


def test_factory_raises_for_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unknown strategy"):
        get_strategy("adaptive")


# ---------------------------------------------------------------------------
# GamePlanner context
# ---------------------------------------------------------------------------


def test_game_planner_plan_delegates_to_strategy(deck: list[Flashcard]) -> None:
    planner = GamePlanner(SequentialStrategy())
    assert planner.plan(deck) == deck


def test_game_planner_set_strategy_changes_behaviour(deck: list[Flashcard]) -> None:
    planner = GamePlanner(SequentialStrategy())
    planner.set_strategy(RandomStrategy())
    result = planner.plan(deck)
    assert sorted(result, key=lambda c: c.front) == sorted(deck, key=lambda c: c.front)


def test_game_planner_does_not_mutate_input(deck: list[Flashcard]) -> None:
    original = list(deck)
    GamePlanner(RandomStrategy()).plan(deck)
    assert deck == original
