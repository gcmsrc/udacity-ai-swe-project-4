from pathlib import Path
from typing import Annotated

import typer

from utils.data_loader import load_flashcards
from utils.quiz_engine import QuizEngine
from utils.strategies import get_strategy
from utils.ui import UI

app = typer.Typer(help="CLI flashcard quiz application.")


@app.command()
def quiz(
    deck: Annotated[Path, typer.Argument(help="Path to a JSON flashcard deck.")],
    mode: Annotated[
        str, typer.Option(help="Quiz mode: sequential | random.")
    ] = "sequential",
) -> None:
    """Run an interactive flashcard quiz session."""
    raise NotImplementedError
