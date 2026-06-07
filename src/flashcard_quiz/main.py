"""CLI flashcard quiz application entry point.

Wires together the data loader, strategy selection, quiz engine, terminal UI,
and SQLite session persistence into a single Typer command.

Usage::

    flashcard DECK_FILE [--mode sequential|random|adaptive]
"""

from pathlib import Path
from typing import Annotated

import typer

from flashcard_quiz.utils.data_loader import load_flashcards
from flashcard_quiz.utils.db import DatabaseConnection, SessionRepository
from flashcard_quiz.utils.quiz_engine import QuizEngine
from flashcard_quiz.utils.strategies import get_strategy
from flashcard_quiz.utils.ui import TerminalUI

app = typer.Typer(help="CLI flashcard quiz application.")

_DB_PATH = Path.cwd() / "data" / "db" / "flashcards.db"


@app.command()
def main(
    deck: Annotated[Path, typer.Argument(help="Path to a JSON flashcard deck.")],
    mode: Annotated[
        str,
        typer.Option(help="Quiz mode: sequential | random | adaptive."),
    ] = "sequential",
) -> None:
    """Run an interactive flashcard quiz session.

    Args:
        deck: Path to a JSON flashcard deck file.
        mode: Quiz ordering mode; one of ``sequential``, ``random``, or
              ``adaptive``.

    Raises:
        typer.Exit: with code 1 on an unknown mode or deck-loading failure.
    """
    try:
        strategy = get_strategy(mode)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1)

    cards = load_flashcards(deck)

    db = DatabaseConnection()
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db.connect(_DB_PATH)
    repo = SessionRepository(db)
    session_id = repo.create_session(str(deck))

    ui = TerminalUI()
    engine = QuizEngine(strategy=strategy, ui=ui)
    result = engine.run(cards)

    repo.save_session_result(session_id, result)
    ui.show_summary(result)
    db.disconnect()


if __name__ == "__main__":
    app()
