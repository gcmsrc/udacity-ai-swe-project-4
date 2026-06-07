from utils.models import Flashcard, SessionResult
from utils.strategies.base import QuizMode
from utils.ui import UI


class QuizEngine:
    """Drives the quiz loop: present cards, collect answers, track score."""

    def __init__(self, strategy: QuizMode, ui: UI) -> None:
        self._strategy = strategy
        self._ui = ui

    def run(self, cards: list[Flashcard]) -> SessionResult:
        """Run a full quiz session and return the result.

        Args:
            cards: the deck to quiz on.

        Returns:
            A SessionResult with totals and missed card fronts.
        """
        self._strategy.setup(cards)
        correct_count = 0
        missed: list[str] = []

        while (card := self._strategy.get_next_card()) is not None:
            answer = self._ui.prompt_answer(card)
            correct = answer.strip().lower() == card.back.strip().lower()
            self._ui.show_feedback(correct, card.back)
            self._strategy.record_result(card, correct)
            if correct:
                correct_count += 1
            else:
                missed.append(card.front)

        return SessionResult(total=len(cards), correct=correct_count, missed=missed)
