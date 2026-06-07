from utils.models import Flashcard, SessionResult


class UI:
    """Handles all terminal I/O: prompts, feedback, and summary."""

    def prompt_answer(self, card: Flashcard) -> str:
        """Display the card front and return the user's typed answer.

        Args:
            card: the card whose front is shown.

        Returns:
            The raw string the user entered.
        """
        raise NotImplementedError

    def show_feedback(self, correct: bool, expected: str) -> None:
        """Print correct/wrong feedback after each answer.

        Args:
            correct: whether the user's answer matched.
            expected: the correct answer, shown on wrong attempts.
        """
        raise NotImplementedError

    def show_summary(self, result: SessionResult) -> None:
        """Render the end-of-session summary table.

        Args:
            result: the completed session outcome.
        """
        raise NotImplementedError
