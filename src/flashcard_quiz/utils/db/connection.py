"""SQLite connection singleton for the flashcard application."""

import sqlite3
from pathlib import Path


class DatabaseConnection:
    """Singleton managing the SQLite connection for the process lifetime.

    Only one connection is ever opened per process. Call ``connect()`` once at
    application startup and ``disconnect()`` at shutdown.  In tests, pass a
    ``tmp_path``-based path to ``connect()`` to get an isolated on-disk
    database that is cleaned up automatically.

    Raises:
        sqlite3.OperationalError: propagated when the database file cannot be
            opened or a query cannot be executed.
        sqlite3.IntegrityError: propagated when a constraint (e.g. PRIMARY KEY)
            is violated.
    """

    _instance: "DatabaseConnection | None" = None
    _conn: sqlite3.Connection | None = None

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self, db_path: Path) -> None:
        """Open the connection and create the schema if the file is new.

        Args:
            db_path: filesystem path for the SQLite database file.

        Raises:
            sqlite3.OperationalError: if the file cannot be created or opened.
        """
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_schema()

    def disconnect(self) -> None:
        """Commit pending writes and close the connection."""
        if self._conn is not None:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    @classmethod
    def _reset(cls) -> None:
        """Reset the singleton — for use in tests only."""
        cls._instance = None

    # ------------------------------------------------------------------
    # Query execution
    # ------------------------------------------------------------------

    def execute(
        self, query: str, params: tuple[object, ...] = ()
    ) -> list[dict[str, object]]:
        """Execute a parameterised query and return rows as plain dicts.

        Parameterised queries (``?`` placeholders) are used throughout to
        prevent SQL injection.

        Args:
            query: SQL statement with ``?`` placeholders.
            params: values bound to the placeholders.

        Returns:
            List of result rows, each represented as a ``{column: value}`` dict.

        Raises:
            sqlite3.OperationalError: if the query cannot be executed.
            sqlite3.IntegrityError: if a constraint is violated.
        """
        if self._conn is None:
            raise RuntimeError("call connect() before execute()")
        cursor = self._conn.execute(query, params)
        self._conn.commit()
        return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_schema(self) -> None:
        if self._conn is None:
            raise RuntimeError("call connect() before using the connection")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id         TEXT PRIMARY KEY,
                dataset    TEXT NOT NULL,
                created_at TEXT NOT NULL,
                result     TEXT
            );
            """)
        self._conn.commit()
