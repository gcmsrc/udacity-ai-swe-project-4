"""Session persistence layer — stores quiz sessions and serialised results."""

import uuid
from datetime import datetime, timezone

from flashcard_quiz.utils.db.connection import DatabaseConnection
from flashcard_quiz.utils.models import SessionResult

_SQL_INSERT_SESSION = (
    "INSERT INTO sessions (id, dataset, created_at, result) VALUES (?, ?, ?, NULL)"
)
_SQL_UPDATE_RESULT = "UPDATE sessions SET result = ? WHERE id = ?"


class SessionRepository:
    """Persists quiz sessions and their results to the database.

    Each session is a single row in the ``sessions`` table.  The
    ``SessionResult`` is stored as a JSON blob in the ``result`` column once
    the session completes.

    Args:
        db: an open ``DatabaseConnection`` instance.
    """

    def __init__(self, db: DatabaseConnection) -> None:
        self.db = db

    def create_session(self, dataset: str) -> str:
        """Create a new session row and return its UUID.

        Args:
            dataset: path or name of the JSON deck.

        Returns:
            UUID4 string identifying the newly created session.

        Raises:
            sqlite3.OperationalError: if the database cannot be accessed.
            sqlite3.IntegrityError: if a session with the generated ID already
                exists (propagated for transparency; astronomically unlikely).
        """
        session_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        self.db.execute(_SQL_INSERT_SESSION, (session_id, dataset, created_at))
        return session_id

    def save_session_result(self, session_id: str, result: SessionResult) -> None:
        """Persist the completed session result as a JSON blob.

        Args:
            session_id: UUID of the session to update.
            result: the ``SessionResult`` produced by the quiz engine.

        Raises:
            sqlite3.OperationalError: if the database cannot be accessed.
        """
        self.db.execute(_SQL_UPDATE_RESULT, (result.to_json(), session_id))
