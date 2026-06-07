"""Data loading utilities for flashcard decks.

Provides :class:`CardsDataLoader` for loading JSON flashcard files and
:func:`load_flashcards` as a thin CLI-facing wrapper that converts exceptions
into user-friendly ``typer.Exit`` calls.
"""

import json
from pathlib import Path
from typing import Any, cast

from utils.models import Flashcard

_WRAPPED_KEY = "cards"
_REQUIRED_FIELDS = ("front", "back")


class CardsDataLoader:
    """Loads flashcard decks from JSON files.

    Accepts two JSON formats:

    - **Array format**: ``[{"front": "...", "back": "..."}, ...]``
    - **Wrapped format**: ``{"cards": [{"front": "...", "back": "..."}, ...]}``

    Only absolute paths are accepted.
    """

    def load(self, path: Path | str) -> list[Flashcard]:
        """Load flashcards from a JSON file.

        Args:
            path: Absolute path to the JSON deck file (``Path`` or ``str``).
                  String values are converted to ``Path`` before validation.

        Returns:
            Non-empty list of :class:`~utils.models.Flashcard` objects.

        Raises:
            ValueError: If *path* is not absolute.
            FileNotFoundError: If the file does not exist.
            ValueError: If the file content is not valid JSON.
            ValueError: If the JSON structure is neither a list nor a dict
                with a ``"cards"`` key.
            ValueError: If any card object is missing a ``"front"`` or
                ``"back"`` field, or those fields are not strings.
            ValueError: If the deck contains no cards.
        """
        if isinstance(path, str):
            path = Path(path)
        if not path.is_absolute():
            raise ValueError(f"Path must be absolute, got: {path}")
        path = path.resolve()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

        cards_data = self._extract_cards_list(raw, path)

        if not cards_data:
            raise ValueError(f"Deck is empty: {path}")

        return [
            self._parse_card(item, idx, path) for idx, item in enumerate(cards_data)
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_cards_list(self, data: Any, path: Path) -> list[Any]:
        """Return the raw list of card dicts from either supported format.

        Args:
            data: Parsed JSON value.
            path: Source path (used in error messages).

        Returns:
            List of raw card objects (may be empty); each element is expected
            to be a ``dict[str, Any]`` and is validated downstream by
            ``_parse_card``.

        Raises:
            ValueError: If *data* matches neither supported format.
        """
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and _WRAPPED_KEY in data:
            return cast(list[Any], data[_WRAPPED_KEY])
        raise ValueError(
            f"Expected a JSON array or an object with a '{_WRAPPED_KEY}' key in {path}"
        )

    def _parse_card(self, item: Any, index: int, path: Path) -> Flashcard:
        """Parse a single raw card dict into a :class:`~utils.models.Flashcard`.

        Args:
            item: Raw value from the JSON array.
            index: Zero-based position (used in error messages).
            path: Source path (used in error messages).

        Returns:
            A :class:`~utils.models.Flashcard` instance.

        Raises:
            ValueError: If *item* is not a dict, is missing required keys, or
                has non-string values for ``"front"`` / ``"back"``.
        """
        if not isinstance(item, dict):
            raise ValueError(f"Card at index {index} must be a JSON object in {path}")
        for key in _REQUIRED_FIELDS:
            if key not in item:
                raise ValueError(f"Card at index {index} is missing '{key}' in {path}")
            if not isinstance(item[key], str):
                raise ValueError(
                    f"Card at index {index} has non-string value for '{key}' in {path}"
                )
        return Flashcard(front=item["front"], back=item["back"])


def load_flashcards(path: Path) -> list[Flashcard]:
    """Load and validate a JSON deck (CLI-facing wrapper).

    .. note::
        Not yet implemented — will be completed in the next step.
    """
    raise NotImplementedError
