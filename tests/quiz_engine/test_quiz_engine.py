from unittest.mock import MagicMock

import pytest

from utils.models import Flashcard, SessionResult
from utils.quiz_engine import QuizEngine
from utils.strategies import SequentialStrategy
from utils.ui import UI


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


def test_engine_calls_show_summary_once(
    engine: QuizEngine, deck: list[Flashcard], ui: MagicMock
) -> None:
    ui.prompt_answer.return_value = "wrong"
    engine.run(deck)
    ui.show_summary.assert_called_once()
