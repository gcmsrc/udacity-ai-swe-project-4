import pytest

from utils.models import Flashcard
from utils.strategies import (
    AdaptiveStrategy,
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


def _drain(strategy: QuizMode) -> list[Flashcard]:
    """Collect all cards from a set-up strategy until exhausted."""
    cards = []
    while (card := strategy.get_next_card()) is not None:
        cards.append(card)
    return cards


# ---------------------------------------------------------------------------
# QuizMode ABC
# ---------------------------------------------------------------------------


def test_quiz_strategy_is_abstract() -> None:
    with pytest.raises(TypeError):
        QuizMode()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# SequentialStrategy
# ---------------------------------------------------------------------------


def test_sequential_preserves_order(deck: list[Flashcard]) -> None:
    s = SequentialStrategy()
    s.setup(deck)
    assert _drain(s) == deck


def test_sequential_exhausts_after_deck(deck: list[Flashcard]) -> None:
    s = SequentialStrategy()
    s.setup(deck)
    _drain(s)
    assert s.get_next_card() is None


def test_sequential_does_not_mutate_input(deck: list[Flashcard]) -> None:
    original = list(deck)
    s = SequentialStrategy()
    s.setup(deck)
    assert deck == original


# ---------------------------------------------------------------------------
# RandomStrategy
# ---------------------------------------------------------------------------


def test_random_returns_same_cards(deck: list[Flashcard]) -> None:
    s = RandomStrategy()
    s.setup(deck)
    result = _drain(s)
    assert sorted(result, key=lambda c: c.front) == sorted(deck, key=lambda c: c.front)


def test_random_changes_order_statistically(deck: list[Flashcard]) -> None:
    orders = []
    for _ in range(50):
        s = RandomStrategy()
        s.setup(deck)
        orders.append(tuple(c.front for c in _drain(s)))
    assert len(set(orders)) > 1, "RandomStrategy never produced a different order"


def test_random_exhausts_after_deck(deck: list[Flashcard]) -> None:
    s = RandomStrategy()
    s.setup(deck)
    _drain(s)
    assert s.get_next_card() is None


def test_random_does_not_mutate_input(deck: list[Flashcard]) -> None:
    original = list(deck)
    s = RandomStrategy()
    s.setup(deck)
    assert deck == original


# ---------------------------------------------------------------------------
# AdaptiveStrategy
# ---------------------------------------------------------------------------


def test_adaptive_draws_exactly_deck_size_cards(deck: list[Flashcard]) -> None:
    s = AdaptiveStrategy()
    s.setup(deck)
    assert len(_drain(s)) == len(deck)


def test_adaptive_only_draws_cards_from_deck(deck: list[Flashcard]) -> None:
    s = AdaptiveStrategy()
    s.setup(deck)
    assert all(c in deck for c in _drain(s))


def test_adaptive_exhausts_after_total_draws(deck: list[Flashcard]) -> None:
    s = AdaptiveStrategy()
    s.setup(deck)
    _drain(s)
    assert s.get_next_card() is None


def test_adaptive_doubles_weight_on_miss(deck: list[Flashcard]) -> None:
    s = AdaptiveStrategy()
    s.setup(deck)
    s.record_result(deck[0], correct=False)
    assert s._weights[0] == 2.0


def test_adaptive_correct_answer_does_not_change_weight(deck: list[Flashcard]) -> None:
    s = AdaptiveStrategy()
    s.setup(deck)
    s.record_result(deck[0], correct=True)
    assert s._weights[0] == 1.0


# ---------------------------------------------------------------------------
# get_strategy factory
# ---------------------------------------------------------------------------


def test_factory_returns_sequential() -> None:
    assert isinstance(get_strategy("sequential"), SequentialStrategy)


def test_factory_returns_random() -> None:
    assert isinstance(get_strategy("random"), RandomStrategy)


def test_factory_returns_adaptive() -> None:
    assert isinstance(get_strategy("adaptive"), AdaptiveStrategy)


def test_factory_raises_for_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unknown strategy"):
        get_strategy("unknown")


# ---------------------------------------------------------------------------
# GamePlanner context
# ---------------------------------------------------------------------------


def test_game_planner_exposes_strategy() -> None:
    strategy = SequentialStrategy()
    planner = GamePlanner(strategy)
    assert planner.strategy is strategy


def test_game_planner_set_strategy_replaces_strategy() -> None:
    planner = GamePlanner(SequentialStrategy())
    new_strategy = RandomStrategy()
    planner.set_strategy(new_strategy)
    assert planner.strategy is new_strategy
