"""Tests for the main Typer CLI application (main.py)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner, Result

from flashcard_quiz.main import app
from flashcard_quiz.utils.models import SessionResult


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def deck_file(tmp_path: Path) -> Path:
    """A valid single-card deck JSON file."""
    path = tmp_path / "deck.json"
    path.write_text(json.dumps([{"front": "CPU", "back": "Central Processing Unit"}]))
    return path


# ---------------------------------------------------------------------------
# Error paths — no DB interaction required
# ---------------------------------------------------------------------------


def test_unknown_mode_exits_with_error(runner: CliRunner, deck_file: Path) -> None:
    result = runner.invoke(app, [str(deck_file), "--mode", "bogus"])
    assert result.exit_code == 1
    assert "bogus" in result.output


def test_missing_deck_file_exits_with_error(runner: CliRunner, tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    result = runner.invoke(app, [str(missing)])
    assert result.exit_code == 1
    assert "nope.json" in result.output


def test_invalid_json_deck_exits_with_error(runner: CliRunner, tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not json at all")
    result = runner.invoke(app, [str(bad_file)])
    assert result.exit_code == 1
    assert "Could not read deck" in result.output


def test_empty_deck_exits_with_error(runner: CliRunner, tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("[]")
    result = runner.invoke(app, [str(empty_file)])
    assert result.exit_code == 1
    assert "Could not read deck" in result.output


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


def _run_with_mocked_db_and_engine(
    runner: CliRunner,
    deck_file: Path,
    mode: str,
    fake_result: SessionResult,
) -> Result:
    """Invoke the quiz command with DB and engine mocked out."""
    with (
        patch("flashcard_quiz.main.DatabaseConnection"),
        patch("flashcard_quiz.main.SessionRepository") as mock_repo_cls,
        patch("flashcard_quiz.main.QuizEngine") as mock_engine_cls,
    ):
        mock_repo_cls.return_value.create_session.return_value = "test-session-id"
        mock_engine_cls.return_value.run.return_value = fake_result
        return runner.invoke(app, [str(deck_file), "--mode", mode])


def test_sequential_mode_succeeds(runner: CliRunner, deck_file: Path) -> None:
    fake_result = SessionResult(total=1, correct=1, missed=[])
    result = _run_with_mocked_db_and_engine(
        runner, deck_file, "sequential", fake_result
    )
    assert result.exit_code == 0


def test_random_mode_succeeds(runner: CliRunner, deck_file: Path) -> None:
    fake_result = SessionResult(total=1, correct=0, missed=["CPU"])
    result = _run_with_mocked_db_and_engine(runner, deck_file, "random", fake_result)
    assert result.exit_code == 0


def test_adaptive_mode_succeeds(runner: CliRunner, deck_file: Path) -> None:
    fake_result = SessionResult(total=1, correct=1, missed=[])
    result = _run_with_mocked_db_and_engine(runner, deck_file, "adaptive", fake_result)
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Renderer selection — --plain-terminal flag
# ---------------------------------------------------------------------------


def _run_and_capture_ui(
    runner: CliRunner, deck_file: Path, extra_args: list[str]
) -> tuple[Result, MagicMock, MagicMock]:
    """Invoke the command with DB/engine/UI classes mocked; return the mocks."""
    fake_result = SessionResult(total=1, correct=1, missed=[])
    with (
        patch("flashcard_quiz.main.DatabaseConnection"),
        patch("flashcard_quiz.main.SessionRepository") as mock_repo_cls,
        patch("flashcard_quiz.main.QuizEngine") as mock_engine_cls,
        patch("flashcard_quiz.main.TerminalRichUI") as mock_rich,
        patch("flashcard_quiz.main.TerminalUI") as mock_plain,
    ):
        mock_repo_cls.return_value.create_session.return_value = "test-session-id"
        mock_engine_cls.return_value.run.return_value = fake_result
        result = runner.invoke(app, [str(deck_file), *extra_args])
    return result, mock_rich, mock_plain


def test_default_uses_rich_ui(runner: CliRunner, deck_file: Path) -> None:
    result, mock_rich, mock_plain = _run_and_capture_ui(runner, deck_file, [])
    assert result.exit_code == 0
    mock_rich.assert_called_once()
    mock_plain.assert_not_called()


def test_plain_terminal_flag_uses_plain_ui(
    runner: CliRunner, deck_file: Path
) -> None:
    result, mock_rich, mock_plain = _run_and_capture_ui(
        runner, deck_file, ["--plain-terminal"]
    )
    assert result.exit_code == 0
    mock_plain.assert_called_once()
    mock_rich.assert_not_called()


def test_summary_score_printed(runner: CliRunner, deck_file: Path) -> None:
    fake_result = SessionResult(total=2, correct=1, missed=["CPU"])
    result = _run_with_mocked_db_and_engine(
        runner, deck_file, "sequential", fake_result
    )
    assert "50%" in result.output


def test_summary_missed_cards_printed(runner: CliRunner, deck_file: Path) -> None:
    fake_result = SessionResult(total=1, correct=0, missed=["CPU"])
    result = _run_with_mocked_db_and_engine(
        runner, deck_file, "sequential", fake_result
    )
    assert "CPU" in result.output


def test_session_result_persisted(runner: CliRunner, deck_file: Path) -> None:
    """Verify save_session_result is called with the engine's return value."""
    fake_result = SessionResult(total=1, correct=1, missed=[])
    with (
        patch("flashcard_quiz.main.DatabaseConnection"),
        patch("flashcard_quiz.main.SessionRepository") as mock_repo_cls,
        patch("flashcard_quiz.main.QuizEngine") as mock_engine_cls,
    ):
        mock_repo_cls.return_value.create_session.return_value = "sid"
        mock_engine_cls.return_value.run.return_value = fake_result
        runner.invoke(app, [str(deck_file)])
        mock_repo_cls.return_value.save_session_result.assert_called_once_with(
            "sid", fake_result
        )


def test_show_history_flag_invokes_get_and_show_history(
    runner: CliRunner, deck_file: Path
) -> None:
    fake_result = SessionResult(total=1, correct=1, missed=[])
    with (
        patch("flashcard_quiz.main.DatabaseConnection"),
        patch("flashcard_quiz.main.SessionRepository") as mock_repo_cls,
        patch("flashcard_quiz.main.QuizEngine") as mock_engine_cls,
        patch("flashcard_quiz.main.TerminalRichUI") as mock_rich,
        patch("flashcard_quiz.main.TerminalUI"),
    ):
        mock_repo_cls.return_value.create_session.return_value = "test-session-id"
        mock_engine_cls.return_value.run.return_value = fake_result
        mock_repo_cls.return_value.get_history.return_value = [0.5, 1.0]
        result = runner.invoke(app, [str(deck_file), "--show-history"])
    assert result.exit_code == 0
    mock_repo_cls.return_value.get_history.assert_called_once_with(str(deck_file))
    mock_rich.return_value.show_history.assert_called_once_with([0.5, 1.0])
