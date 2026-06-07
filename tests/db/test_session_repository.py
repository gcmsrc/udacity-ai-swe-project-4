"""Tests for DatabaseConnection and SessionRepository."""

import sqlite3
from pathlib import Path
from typing import Generator

import pytest

from flashcard_quiz.utils.db import DatabaseConnection, SessionRepository
from flashcard_quiz.utils.db.session_repository import _SQL_INSERT_SESSION
from flashcard_quiz.utils.models import SessionResult


@pytest.fixture
def db(tmp_path: Path) -> Generator[DatabaseConnection, None, None]:
    """Provide a fresh DatabaseConnection for each test."""
    conn = DatabaseConnection()
    conn.connect(tmp_path / "test.db")
    yield conn
    DatabaseConnection._reset()
    conn.disconnect()


@pytest.fixture
def repo(db: DatabaseConnection) -> SessionRepository:
    return SessionRepository(db)


# --- create_session ---


def test_create_session_returns_string(repo: SessionRepository) -> None:
    assert isinstance(repo.create_session("data/sample.json"), str)


def test_create_session_returns_unique_ids(repo: SessionRepository) -> None:
    id1 = repo.create_session("data/sample.json")
    id2 = repo.create_session("data/sample.json")
    assert id1 != id2


def test_create_session_stores_dataset(
    repo: SessionRepository, db: DatabaseConnection
) -> None:
    repo.create_session("data/sample.json")
    rows = db.execute("SELECT dataset FROM sessions")
    assert rows[0]["dataset"] == "data/sample.json"


# --- save_session_result ---


def test_save_session_result_persists_result(
    repo: SessionRepository, db: DatabaseConnection
) -> None:
    session_id = repo.create_session("data/deck.json")
    result = SessionResult(total=3, correct=2, missed=["CPU"])
    repo.save_session_result(session_id, result)
    rows = db.execute("SELECT result FROM sessions WHERE id = ?", (session_id,))
    assert rows[0]["result"] is not None


def test_save_session_result_stores_missed_cards(
    repo: SessionRepository, db: DatabaseConnection
) -> None:
    import json

    session_id = repo.create_session("data/deck.json")
    result = SessionResult(total=2, correct=1, missed=["RAM"])
    repo.save_session_result(session_id, result)
    rows = db.execute("SELECT result FROM sessions WHERE id = ?", (session_id,))
    data = json.loads(str(rows[0]["result"]))
    assert data["missed"] == ["RAM"]
    assert data["total"] == 2
    assert data["correct"] == 1


# --- error handling ---


def test_integrity_error_on_duplicate_session_id(db: DatabaseConnection) -> None:
    params1 = ("fixed-id", "data/deck.json", "2024-01-01T00:00:00+00:00")
    params2 = ("fixed-id", "data/deck.json", "2024-01-01T00:00:01+00:00")
    db.execute(_SQL_INSERT_SESSION, params1)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(_SQL_INSERT_SESSION, params2)


def test_operational_error_on_bad_query(db: DatabaseConnection) -> None:
    with pytest.raises(sqlite3.OperationalError):
        db.execute("SELECT * FROM nonexistent_table")


# --- get_history ---


def test_get_history_empty_when_no_sessions(repo: SessionRepository) -> None:
    assert repo.get_history("data/unknown.json") == []


def test_get_history_empty_when_no_completed_sessions(repo: SessionRepository) -> None:
    repo.create_session("data/deck.json")  # result column stays NULL
    assert repo.get_history("data/deck.json") == []


def test_get_history_single_session(repo: SessionRepository) -> None:
    session_id = repo.create_session("data/deck.json")
    repo.save_session_result(session_id, SessionResult(total=4, correct=3, missed=[]))
    history = repo.get_history("data/deck.json")
    assert history == pytest.approx([0.75])


def test_get_history_multiple_sessions_ordered_oldest_first(
    repo: SessionRepository,
) -> None:
    for total, correct in [(4, 2), (4, 3), (4, 4)]:
        sid = repo.create_session("data/deck.json")
        repo.save_session_result(sid, SessionResult(total=total, correct=correct, missed=[]))
    history = repo.get_history("data/deck.json")
    assert history == pytest.approx([0.5, 0.75, 1.0])


def test_get_history_ignores_other_datasets(repo: SessionRepository) -> None:
    sid = repo.create_session("data/other.json")
    repo.save_session_result(sid, SessionResult(total=2, correct=1, missed=[]))
    assert repo.get_history("data/deck.json") == []
