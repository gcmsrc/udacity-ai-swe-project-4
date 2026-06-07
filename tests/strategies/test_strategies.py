import pytest

from utils.models import Flashcard
from utils.strategies import AdaptiveStrategy, RandomStrategy, SequentialStrategy
from utils.strategies.base import QuizStrategy


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
# QuizStrategy ABC
# ---------------------------------------------------------------------------

def test_quiz_strategy_is_abstract() -> None:
    """Instantiating the ABC directly must raise TypeError."""
    with pytest.raises(TypeError):
        QuizStrategy()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# SequentialStrategy
# ---------------------------------------------------------------------------

def test_sequential_preserves_order(deck: list[Flashcard]) -> None:
    result = SequentialStrategy().order(deck)
    assert result == deck


def test_sequential_returns_all_cards(deck: list[Flashcard]) -> None:
    result = SequentialStrategy().order(deck)
    assert len(result) == len(deck)


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


def test_random_returns_all_cards(deck: list[Flashcard]) -> None:
    result = RandomStrategy().order(deck)
    assert len(result) == len(deck)


def test_random_does_not_mutate_input(deck: list[Flashcard]) -> None:
    original = list(deck)
    RandomStrategy().order(deck)
    assert deck == original


# ---------------------------------------------------------------------------
# AdaptiveStrategy
# ---------------------------------------------------------------------------

def test_adaptive_missed_cards_come_first(deck: list[Flashcard]) -> None:
    missed = ["GPU"]
    result = AdaptiveStrategy(missed=missed).order(deck)
    assert result[0].front == "GPU"


def test_adaptive_all_cards_present(deck: list[Flashcard]) -> None:
    missed = ["RAM"]
    result = AdaptiveStrategy(missed=missed).order(deck)
    assert len(result) == len(deck)


def test_adaptive_no_missed_preserves_order(deck: list[Flashcard]) -> None:
    result = AdaptiveStrategy().order(deck)
    assert result == deck


def test_adaptive_multiple_missed_all_appear_first(deck: list[Flashcard]) -> None:
    missed = ["GPU", "RAM"]
    result = AdaptiveStrategy(missed=missed).order(deck)
    missed_fronts = {c.front for c in result[: len(missed)]}
    assert missed_fronts == set(missed)


def test_adaptive_does_not_mutate_input(deck: list[Flashcard]) -> None:
    original = list(deck)
    AdaptiveStrategy(missed=["RAM"]).order(deck)
    assert deck == original
