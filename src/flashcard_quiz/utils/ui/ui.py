from typing import Protocol

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from flashcard_quiz.utils.models import Flashcard, SessionResult

_BAR_WIDTH = 20
_NO_HISTORY_MSG = (
    "No history found for this deck;"
    " keep on exercising and you will see it here soon!"
)


class UI(Protocol):
    """Terminal I/O protocol — any object with these methods qualifies."""

    def prompt_answer(self, card: Flashcard) -> str: ...
    def show_feedback(self, correct: bool, expected: str) -> None: ...
    def show_summary(self, result: SessionResult) -> None: ...
    def show_history(self, history: list[float]) -> None: ...


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

    def show_history(self, history: list[float]) -> None:
        """Print an ASCII bar chart of per-attempt scores, oldest first.

        Each bar is ``_BAR_WIDTH`` characters wide.  When *history* is empty
        a short encouragement message is printed instead.

        Args:
            history: Per-attempt scores as fractions in [0.0, 1.0], ordered
                oldest first.
        """
        if not history:
            print(_NO_HISTORY_MSG)
            return
        n = len(history)
        label = "attempt" if n == 1 else "attempts"
        print(f"\nDeck History ({n} {label}):")
        for i, pct in enumerate(history, start=1):
            filled = round(pct * _BAR_WIDTH)
            bar = "█" * filled + "░" * (_BAR_WIDTH - filled)
            print(f"  #{i:>3}: {pct:>5.0%}  {bar}")


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

    def show_history(self, history: list[float]) -> None:
        """Render a rich table with per-attempt scores and colored bars, oldest first.

        Scores >= 80 % are shown in green, >= 50 % in yellow, and below 50 %
        in red.  When *history* is empty a styled panel with an encouragement
        message is rendered instead.

        Args:
            history: Per-attempt scores as fractions in [0.0, 1.0], ordered
                oldest first.
        """
        if not history:
            self._console.print(Panel(_NO_HISTORY_MSG, border_style="dim"))
            return
        n = len(history)
        label = "attempt" if n == 1 else "attempts"
        table = Table(
            title=f"Deck History ({n} {label})",
            header_style="bold blue",
            border_style="blue",
        )
        table.add_column("#", style="dim", justify="right")
        table.add_column("Score", justify="right")
        table.add_column("Bar", min_width=_BAR_WIDTH)
        for i, pct in enumerate(history, start=1):
            filled = round(pct * _BAR_WIDTH)
            color = "green" if pct >= 0.8 else "yellow" if pct >= 0.5 else "red"
            bar = (
                f"[{color}]"
                + "█" * filled
                + "[/]"
                + "[dim]"
                + "░" * (_BAR_WIDTH - filled)
                + "[/]"
            )
            table.add_row(str(i), f"[bold]{pct:.0%}[/]", bar)
        self._console.print(table)
