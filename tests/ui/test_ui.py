from typing import cast
from unittest.mock import patch

import pytest

from flashcard_quiz.utils.models import Flashcard, SessionResult
from flashcard_quiz.utils.ui import UI, TerminalRichUI, TerminalUI


@pytest.fixture(params=[TerminalUI, TerminalRichUI], ids=["plain", "rich"])
def ui(request: pytest.FixtureRequest) -> UI:
    """Each contract test runs against both UI implementations."""
    return cast(UI, request.param())


@pytest.fixture
def card() -> Flashcard:
    return Flashcard("CPU", "Central Processing Unit")


@pytest.fixture
def result() -> SessionResult:
    return SessionResult(total=3, correct=2, missed=["GPU"])


# ---------------------------------------------------------------------------
# Shared Protocol contract — asserted against every UI implementation.
# (rich's Console.input delegates to builtins.input, so patching it and
# capturing stdout via capsys works uniformly for both renderers.)
# ---------------------------------------------------------------------------


def test_prompt_answer_strips_and_returns_input(ui: UI, card: Flashcard) -> None:
    with patch("builtins.input", return_value="  Central Processing Unit  "):
        assert ui.prompt_answer(card) == "Central Processing Unit"


def test_feedback_correct_does_not_leak_expected(
    ui: UI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_feedback(correct=True, expected="Central Processing Unit")
    out = capsys.readouterr().out
    assert out.strip()
    assert "Central Processing Unit" not in out


def test_feedback_wrong_shows_expected(
    ui: UI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_feedback(correct=False, expected="Central Processing Unit")
    out = capsys.readouterr().out
    assert "Wrong" in out
    assert "Central Processing Unit" in out


def test_summary_reports_counts_and_percentage(
    ui: UI, result: SessionResult, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(result)
    out = capsys.readouterr().out
    assert "3" in out  # total
    assert "2" in out  # correct
    assert "67%" in out  # score ratio
    assert "GPU" in out  # missed card


def test_summary_omits_missed_section_when_none(
    ui: UI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_summary(SessionResult(total=2, correct=2, missed=[]))
    assert "Missed" not in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Implementation-specific — the card front reaches the user differently:
# TerminalUI puts it in the input() prompt; TerminalRichUI renders it first.
# ---------------------------------------------------------------------------


def test_plain_prompt_puts_front_in_input_prompt(card: Flashcard) -> None:
    with patch("builtins.input", return_value="") as mock_input:
        TerminalUI().prompt_answer(card)
    assert card.front in mock_input.call_args[0][0]


def test_rich_prompt_renders_front(
    card: Flashcard, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch("builtins.input", return_value=""):
        TerminalRichUI().prompt_answer(card)
    assert card.front in capsys.readouterr().out


# ---------------------------------------------------------------------------
# show_history — shared contract + implementation-specific details.
# ---------------------------------------------------------------------------


def test_show_history_empty_prints_no_history_message(
    ui: UI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_history([])
    assert "No history" in capsys.readouterr().out


def test_show_history_shows_attempt_count(
    ui: UI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_history([0.5, 0.75, 1.0])
    assert "3" in capsys.readouterr().out


def test_show_history_shows_all_percentages(
    ui: UI, capsys: pytest.CaptureFixture[str]
) -> None:
    ui.show_history([0.5, 1.0])
    out = capsys.readouterr().out
    assert "50%" in out
    assert "100%" in out


def test_plain_show_history_renders_bar_characters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    TerminalUI().show_history([0.5])
    out = capsys.readouterr().out
    assert "█" in out
    assert "░" in out


def test_rich_show_history_renders_bar_characters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    TerminalRichUI().show_history([0.5])
    out = capsys.readouterr().out
    assert "█" in out
    assert "░" in out
