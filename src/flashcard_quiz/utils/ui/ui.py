from typing import Protocol

from flashcard_quiz.utils.models import Flashcard, SessionResult


class UI(Protocol):
    """Structural interface for terminal I/O — any object with these methods qualifies."""

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
