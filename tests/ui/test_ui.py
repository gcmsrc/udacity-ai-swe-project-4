from unittest.mock import patch

import pytest

from utils.models import Flashcard, SessionResult
from utils.ui import UI


@pytest.fixture
def ui() -> UI:
    return UI()


@pytest.fixture
def card() -> Flashcard:
    return Flashcard("CPU", "Central Processing Unit")


@pytest.fixture
def result() -> SessionResult:
    return SessionResult(total=3, correct=2, missed=["GPU"])


def test_prompt_answer_returns_user_input(ui: UI, card: Flashcard) -> None:
    with patch("builtins.input", return_value="Central Processing Unit"):
        answer = ui.prompt_answer(card)
    assert answer == "Central Processing Unit"


def test_prompt_answer_strips_whitespace(ui: UI, card: Flashcard) -> None:
    with patch("builtins.input", return_value="  Central Processing Unit  "):
        answer = ui.prompt_answer(card)
    assert answer == "Central Processing Unit"


def test_show_feedback_correct_prints_output(
    ui: UI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_feedback(correct=True, expected="Central Processing Unit")
    captured = capsys.readouterr()
    assert captured.out != ""


def test_show_feedback_wrong_shows_expected(
    ui: UI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_feedback(correct=False, expected="Central Processing Unit")
    captured = capsys.readouterr()
    assert "Central Processing Unit" in captured.out


def test_show_summary_prints_total(
    ui: UI, result: SessionResult, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(result)
    captured = capsys.readouterr()
    assert "3" in captured.out


def test_show_summary_prints_correct_count(
    ui: UI, result: SessionResult, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(result)
    captured = capsys.readouterr()
    assert "2" in captured.out


def test_show_summary_lists_missed_cards(
    ui: UI, result: SessionResult, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(result)
    captured = capsys.readouterr()
    assert "GPU" in captured.out
