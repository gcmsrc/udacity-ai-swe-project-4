from typing import Protocol

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from flashcard_quiz.utils.models import Flashcard, SessionResult


class UI(Protocol):
    """Terminal I/O protocol — any object with these methods qualifies."""

    def prompt_answer(self, card: Flashcard) -> str: ...
    def show_feedback(self, correct: bool, expected: str) -> None: ...
    def show_summary(self, result: SessionResult) -> None: ...


class TerminalUI:
    """Concrete terminal I/O implementation using plain print/input."""

    def prompt_answer(self, card: Flashcard) -> str:
        """Display the card front and return the user's answer (stripped)."""
        return input(f"{card.front}: ").strip()

    def show_feedback(self, correct: bool, expected: str) -> None:
        """Print correct/wrong feedback; show the expected answer on failure."""
        if correct:
            print("Correct!")
        else:
            print(f"Wrong. Answer: {expected}")

    def show_summary(self, result: SessionResult) -> None:
        """Print the session score and, if any, the list of missed cards."""
        ratio = result.correct / result.total if result.total else 0
        print(f"\nResult: {result.correct}/{result.total} ({ratio:.0%})")
        if result.missed:
            print("Missed:", ", ".join(result.missed))


class TerminalRichUI:
    """`rich`-styled implementation of the UI Protocol.

    Aesthetic-only counterpart to ``TerminalUI``: identical I/O behaviour
    (same prompts, same correct/wrong decisions, same summary content) rendered
    with colored panels, an emoji-decorated score table, and styled prompts.
    """

    def __init__(self, console: Console | None = None) -> None:
        """Use the given Console, or create a default one (testable seam)."""
        self._console = console or Console()

    def prompt_answer(self, card: Flashcard) -> str:
        """Show the styled card front and return the user's answer (stripped)."""
        question = Text()
        question.append("❓  ", style="bold yellow")
        question.append(card.front, style="bold cyan")
        self._console.print(
            Panel(question, title="Flashcard", title_align="left", border_style="cyan")
        )
        return self._console.input("[bold magenta]➜ Your answer:[/] ").strip()

    def show_feedback(self, correct: bool, expected: str) -> None:
        """Render a green 'Correct!' panel, or a red panel with the answer."""
        if correct:
            self._console.print(
                Panel("✅ [bold green]Correct![/]", border_style="green")
            )
        else:
            body = Text()
            body.append("❌ Wrong. ", style="bold red")
            body.append("Answer: ", style="dim")
            body.append(expected, style="bold white")
            self._console.print(Panel(body, border_style="red"))

    def show_summary(self, result: SessionResult) -> None:
        """Render a score table and a panel listing any missed cards."""
        ratio = result.correct / result.total if result.total else 0
        table = Table(
            title="\U0001f4ca Session Summary",
            header_style="bold blue",
            border_style="blue",
        )
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold", justify="right")
        table.add_row("Total", str(result.total))
        table.add_row("Correct", f"[green]{result.correct}[/]")
        table.add_row("Score", f"[bold magenta]{ratio:.0%}[/]")
        self._console.print(table)
        if result.missed:
            missed = Text("\U0001f4cc Missed: ", style="bold yellow")
            missed.append(", ".join(result.missed), style="red")
            self._console.print(Panel(missed, border_style="yellow"))
