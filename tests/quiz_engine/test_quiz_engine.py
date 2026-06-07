from unittest.mock import MagicMock

import pytest

from flashcard_quiz.utils.models import Flashcard, SessionResult
from flashcard_quiz.utils.quiz_engine import QuizEngine
from flashcard_quiz.utils.strategies import SequentialStrategy
from flashcard_quiz.utils.strategies.base import QuizMode
from flashcard_quiz.utils.ui import UI


@pytest.fixture
def deck() -> list[Flashcard]:
    return [
        Flashcard("CPU", "Central Processing Unit"),
        Flashcard("RAM", "Random Access Memory"),
    ]


@pytest.fixture
def ui() -> UI:
    return MagicMock(spec=UI)


@pytest.fixture
def engine(ui: UI) -> QuizEngine:
    return QuizEngine(strategy=SequentialStrategy(), ui=ui)


def test_run_returns_session_result(
    engine: QuizEngine, deck: list[Flashcard], ui: MagicMock
) -> None:
    ui.prompt_answer.return_value = "Central Processing Unit"
    result = engine.run(deck)
    assert isinstance(result, SessionResult)


def test_run_total_equals_deck_size(
    engine: QuizEngine, deck: list[Flashcard], ui: MagicMock
) -> None:
    ui.prompt_answer.return_value = "wrong answer"
    result = engine.run(deck)
    assert result.total == len(deck)


def test_run_all_correct_answers(
    engine: QuizEngine, deck: list[Flashcard], ui: MagicMock
) -> None:
    answers = {"CPU": "Central Processing Unit", "RAM": "Random Access Memory"}
    ui.prompt_answer.side_effect = lambda card: answers[card.front]
    result = engine.run(deck)
    assert result.correct == len(deck)
    assert result.missed == []


def test_run_all_wrong_answers(
    engine: QuizEngine, deck: list[Flashcard], ui: MagicMock
) -> None:
    ui.prompt_answer.return_value = "wrong"
    result = engine.run(deck)
    assert result.correct == 0
    assert len(result.missed) == len(deck)


def test_run_tracks_missed_fronts(
    engine: QuizEngine, deck: list[Flashcard], ui: MagicMock
) -> None:
    ui.prompt_answer.return_value = "wrong"
    result = engine.run(deck)
    assert set(result.missed) == {"CPU", "RAM"}


def test_run_partial_correct(
    engine: QuizEngine, deck: list[Flashcard], ui: MagicMock
) -> None:
    ui.prompt_answer.side_effect = lambda card: (
        "Central Processing Unit" if card.front == "CPU" else "wrong"
    )
    result = engine.run(deck)
    assert result.correct == 1
    assert result.missed == ["RAM"]


def test_engine_calls_ui_feedback_for_each_card(
    engine: QuizEngine, deck: list[Flashcard], ui: MagicMock
) -> None:
    ui.prompt_answer.return_value = "wrong"
    engine.run(deck)
    assert ui.show_feedback.call_count == len(deck)


# ---------------------------------------------------------------------------
# Strategy interaction assertions
# ---------------------------------------------------------------------------


def test_run_calls_strategy_setup_once(deck: list[Flashcard], ui: MagicMock) -> None:
    strategy = MagicMock(spec=QuizMode)
    strategy.get_next_card.side_effect = [*deck, None]
    ui.prompt_answer.return_value = "wrong"
    engine = QuizEngine(strategy=strategy, ui=ui)
    engine.run(deck)
    strategy.setup.assert_called_once_with(deck)


def test_run_calls_get_next_card_until_exhausted(
    deck: list[Flashcard], ui: MagicMock
) -> None:
    strategy = MagicMock(spec=QuizMode)
    strategy.get_next_card.side_effect = [*deck, None]
    ui.prompt_answer.return_value = "wrong"
    engine = QuizEngine(strategy=strategy, ui=ui)
    engine.run(deck)
    assert strategy.get_next_card.call_count == len(deck) + 1


def test_run_calls_record_result_for_each_card(
    deck: list[Flashcard], ui: MagicMock
) -> None:
    strategy = MagicMock(spec=QuizMode)
    strategy.get_next_card.side_effect = [*deck, None]
    ui.prompt_answer.return_value = "wrong"
    engine = QuizEngine(strategy=strategy, ui=ui)
    engine.run(deck)
    assert strategy.record_result.call_count == len(deck)


def test_run_calls_record_result_with_correct_flag(
    deck: list[Flashcard], ui: MagicMock
) -> None:
    strategy = MagicMock(spec=QuizMode)
    strategy.get_next_card.side_effect = [deck[0], deck[1], None]
    answers = {"CPU": "Central Processing Unit", "RAM": "wrong"}
    ui.prompt_answer.side_effect = lambda card: answers[card.front]
    engine = QuizEngine(strategy=strategy, ui=ui)
    engine.run(deck)
    strategy.record_result.assert_any_call(deck[0], True)
    strategy.record_result.assert_any_call(deck[1], False)


def test_run_does_not_call_show_summary(deck: list[Flashcard], ui: MagicMock) -> None:
    strategy = MagicMock(spec=QuizMode)
    strategy.get_next_card.side_effect = [*deck, None]
    ui.prompt_answer.return_value = "wrong"
    engine = QuizEngine(strategy=strategy, ui=ui)
    engine.run(deck)
    ui.show_summary.assert_not_called()
