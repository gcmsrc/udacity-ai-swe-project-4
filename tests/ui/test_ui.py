from unittest.mock import patch

import pytest

from utils.models import Flashcard, SessionResult
from utils.ui import TerminalUI


@pytest.fixture
def ui() -> TerminalUI:
    return TerminalUI()


@pytest.fixture
def card() -> Flashcard:
    return Flashcard("CPU", "Central Processing Unit")


@pytest.fixture
def result() -> SessionResult:
    return SessionResult(total=3, correct=2, missed=["GPU"])


# ---------------------------------------------------------------------------
# prompt_answer
# ---------------------------------------------------------------------------


def test_prompt_answer_returns_user_input(ui: TerminalUI, card: Flashcard) -> None:
    with patch("builtins.input", return_value="Central Processing Unit"):
        answer = ui.prompt_answer(card)
    assert answer == "Central Processing Unit"


def test_prompt_answer_strips_whitespace(ui: TerminalUI, card: Flashcard) -> None:
    with patch("builtins.input", return_value="  Central Processing Unit  "):
        answer = ui.prompt_answer(card)
    assert answer == "Central Processing Unit"


def test_prompt_answer_includes_card_front_in_prompt(
    ui: TerminalUI, card: Flashcard
) -> None:
    with patch("builtins.input", return_value="") as mock_input:
        ui.prompt_answer(card)
    prompt_text = mock_input.call_args[0][0]
    assert card.front in prompt_text


# ---------------------------------------------------------------------------
# show_feedback
# ---------------------------------------------------------------------------


def test_show_feedback_correct_prints_output(
    ui: TerminalUI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_feedback(correct=True, expected="Central Processing Unit")
    assert capsys.readouterr().out != ""


def test_show_feedback_correct_does_not_show_expected(
    ui: TerminalUI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_feedback(correct=True, expected="Central Processing Unit")
    assert "Central Processing Unit" not in capsys.readouterr().out


def test_show_feedback_wrong_indicates_wrong(
    ui: TerminalUI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_feedback(correct=False, expected="Central Processing Unit")
    assert "Wrong" in capsys.readouterr().out


def test_show_feedback_wrong_shows_expected(
    ui: TerminalUI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_feedback(correct=False, expected="Central Processing Unit")
    assert "Central Processing Unit" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# show_summary
# ---------------------------------------------------------------------------


def test_show_summary_prints_total(
    ui: TerminalUI, result: SessionResult, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(result)
    assert "3" in capsys.readouterr().out


def test_show_summary_prints_correct_count(
    ui: TerminalUI, result: SessionResult, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(result)
    assert "2" in capsys.readouterr().out


def test_show_summary_lists_missed_cards(
    ui: TerminalUI, result: SessionResult, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(result)
    assert "GPU" in capsys.readouterr().out


def test_show_summary_shows_percentage(
    ui: TerminalUI, result: SessionResult, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(result)
    assert "67%" in capsys.readouterr().out


def test_show_summary_no_missed_section_when_none(
    ui: TerminalUI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(SessionResult(total=2, correct=2, missed=[]))
    assert "Missed" not in capsys.readouterr().out
