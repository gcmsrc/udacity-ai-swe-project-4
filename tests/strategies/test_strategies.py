import pytest

from flashcard_quiz.utils.models import Flashcard
from flashcard_quiz.utils.strategies import (
    AdaptiveStrategy,
    RandomStrategy,
    SequentialStrategy,
    get_strategy,
)
from flashcard_quiz.utils.strategies.base import QuizMode

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


def test_sequential_get_next_card_before_setup_raises() -> None:
    s = SequentialStrategy()
    with pytest.raises(RuntimeError, match=r"call setup\(\) before get_next_card\(\)"):
        s.get_next_card()


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


def test_random_get_next_card_before_setup_raises() -> None:
    s = RandomStrategy()
    with pytest.raises(RuntimeError, match=r"call setup\(\) before get_next_card\(\)"):
        s.get_next_card()


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


def test_adaptive_missed_card_drawn_more_often() -> None:
    """A missed card accumulates higher weight and is drawn more frequently."""
    card_a = Flashcard("A", "a")
    card_b = Flashcard("B", "b")
    two_card = [card_a, card_b]

    counts: dict[str, int] = {"A": 0, "B": 0}
    for _ in range(300):
        s = AdaptiveStrategy()
        s.setup(two_card)
        s.record_result(card_a, correct=False)
        for card in _drain(s):
            counts[card.front] += 1

    assert counts["A"] > counts["B"]


def test_adaptive_get_next_card_before_setup_raises() -> None:
    s = AdaptiveStrategy()
    with pytest.raises(RuntimeError, match=r"call setup\(\) before get_next_card\(\)"):
        s.get_next_card()


def test_adaptive_record_result_before_setup_raises() -> None:
    s = AdaptiveStrategy()
    card = Flashcard("CPU", "Central Processing Unit")
    with pytest.raises(RuntimeError, match=r"call setup\(\) before record_result\(\)"):
        s.record_result(card, correct=False)


def test_adaptive_record_result_unknown_card_raises(deck: list[Flashcard]) -> None:
    s = AdaptiveStrategy()
    s.setup(deck)
    unknown = Flashcard("UNKNOWN", "answer")
    with pytest.raises(ValueError):
        s.record_result(unknown, correct=False)


def test_adaptive_missed_increase_weight_multiple_times() -> None:
    """Weight is increased multiple times after a miss."""
    card = Flashcard("CPU", "Central Processing Unit")
    s = AdaptiveStrategy()
    s.setup([card])

    s.record_result(card, correct=False)
    current_weight = s._weights[0]
    s.record_result(card, correct=False)
    assert s._weights[0] > current_weight


def test_adaptive_missed_then_correct_resets_weight() -> None:
    """Weight is raised after a miss and reset to 1.0 after a correct answer."""
    card = Flashcard("CPU", "Central Processing Unit")
    s = AdaptiveStrategy()
    s.setup([card])

    s.record_result(card, correct=False)
    assert s._weights[0] > 1.0

    s.record_result(card, correct=True)
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
