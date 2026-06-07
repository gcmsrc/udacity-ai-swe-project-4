"""Session persistence layer — stores quiz sessions and serialised results."""

import json
import uuid
from datetime import datetime, timezone

from utils.db.connection import DatabaseConnection
from utils.models import SessionResult


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
        self.db.execute(
            "INSERT INTO sessions (id, dataset, created_at, result) VALUES (?, ?, ?, NULL)",
            (session_id, dataset, created_at),
        )
        return session_id

    def save_session_result(self, session_id: str, result: SessionResult) -> None:
        """Persist the completed session result as a JSON blob.

        Args:
            session_id: UUID of the session to update.
            result: the ``SessionResult`` produced by the quiz engine.

        Raises:
            sqlite3.OperationalError: if the database cannot be accessed.
        """
        payload = json.dumps(
            {"total": result.total, "correct": result.correct, "missed": result.missed}
        )
        self.db.execute(
            "UPDATE sessions SET result = ? WHERE id = ?",
            (payload, session_id),
        )

    def get_missed_cards(self, dataset: str) -> list[str]:
        """Return the missed card fronts from the most recent session for this dataset.

        Args:
            dataset: path or name of the JSON deck.

        Returns:
            List of ``card_front`` strings answered incorrectly in the last
            completed session, or an empty list if no completed session exists.

        Raises:
            sqlite3.OperationalError: if the database cannot be accessed.
        """
        rows = self.db.execute(
            """
            SELECT result FROM sessions
             WHERE dataset = ? AND result IS NOT NULL
             ORDER BY created_at DESC
             LIMIT 1
            """,
            (dataset,),
        )
        if not rows:
            return []
        return json.loads(rows[0]["result"]).get("missed", [])

    def close(self) -> None:
        """Commit and close the underlying database connection."""
        self.db.disconnect()
