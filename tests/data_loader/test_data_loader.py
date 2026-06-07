import json
from pathlib import Path
from typing import Any

import pytest

from utils.data_loader import CardsDataLoader

SAMPLE_CARDS = [
    {"front": "CPU", "back": "Central Processing Unit"},
    {"front": "RAM", "back": "Random Access Memory"},
]

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def loader() -> CardsDataLoader:
    return CardsDataLoader()


@pytest.fixture
def valid_array_deck(tmp_path: Path) -> Path:
    p = tmp_path / "deck.json"
    p.write_text(json.dumps(SAMPLE_CARDS))
    return p


@pytest.fixture
def valid_wrapped_deck(tmp_path: Path) -> Path:
    data = {"cards": SAMPLE_CARDS}
    p = tmp_path / "wrapped.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture
def empty_deck(tmp_path: Path) -> Path:
    p = tmp_path / "empty.json"
    p.write_text("[]")
    return p


# ---------------------------------------------------------------------------
# CardsDataLoader — happy path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("deck_fixture", ["valid_array_deck", "valid_wrapped_deck"])
def test_loader_returns_two_flashcards(
    request: pytest.FixtureRequest, loader: CardsDataLoader, deck_fixture: str
) -> None:
    cards = loader.load(request.getfixturevalue(deck_fixture))
    assert len(cards) == 2


@pytest.mark.parametrize("deck_fixture", ["valid_array_deck", "valid_wrapped_deck"])
def test_loader_maps_card_fields(
    request: pytest.FixtureRequest, loader: CardsDataLoader, deck_fixture: str
) -> None:
    cards = loader.load(request.getfixturevalue(deck_fixture))
    assert cards[0].front == SAMPLE_CARDS[0]["front"]
    assert cards[0].back == SAMPLE_CARDS[0]["back"]


def test_loader_accepts_str_path(
    loader: CardsDataLoader, valid_array_deck: Path
) -> None:
    cards = loader.load(str(valid_array_deck))
    assert len(cards) == 2


# ---------------------------------------------------------------------------
# CardsDataLoader — security: path validation
# ---------------------------------------------------------------------------


def test_loader_relative_path_raises_value_error(
    loader: CardsDataLoader,
) -> None:
    with pytest.raises(ValueError, match="absolute"):
        loader.load(Path("relative/path/deck.json"))


def test_loader_relative_str_path_raises_value_error(
    loader: CardsDataLoader,
) -> None:
    with pytest.raises(ValueError, match="absolute"):
        loader.load("relative/path/deck.json")


def test_loader_path_traversal_raises_value_error(loader: CardsDataLoader) -> None:
    with pytest.raises(ValueError, match="absolute"):
        loader.load(Path("../../etc/passwd"))


# ---------------------------------------------------------------------------
# CardsDataLoader — error handling
# ---------------------------------------------------------------------------


def test_loader_missing_file_raises_file_not_found(
    loader: CardsDataLoader, tmp_path: Path
) -> None:
    with pytest.raises(FileNotFoundError):
        loader.load(tmp_path / "missing.json")


def test_loader_invalid_json_raises_value_error(
    loader: CardsDataLoader, tmp_path: Path
) -> None:
    p = tmp_path / "bad.json"
    p.write_text("not valid json {{{")
    with pytest.raises(ValueError, match="Invalid JSON"):
        loader.load(p)


def test_loader_missing_front_raises_value_error(
    loader: CardsDataLoader, tmp_path: Path
) -> None:
    p = tmp_path / "no_front.json"
    p.write_text(json.dumps([{"back": "Central Processing Unit"}]))
    with pytest.raises(ValueError, match="is missing 'front'"):
        loader.load(p)


def test_loader_missing_back_raises_value_error(
    loader: CardsDataLoader, tmp_path: Path
) -> None:
    p = tmp_path / "no_back.json"
    p.write_text(json.dumps([{"front": "CPU"}]))
    with pytest.raises(ValueError, match="is missing 'back'"):
        loader.load(p)


def test_loader_empty_deck_raises_value_error(
    loader: CardsDataLoader, empty_deck: Path
) -> None:
    with pytest.raises(ValueError, match="empty"):
        loader.load(empty_deck)


def test_loader_wrapped_empty_deck_raises_value_error(
    loader: CardsDataLoader, tmp_path: Path
) -> None:
    p = tmp_path / "wrapped_empty.json"
    p.write_text(json.dumps({"cards": []}))
    with pytest.raises(ValueError, match="empty"):
        loader.load(p)


def test_loader_plain_object_without_cards_key_raises_value_error(
    loader: CardsDataLoader, tmp_path: Path
) -> None:
    p = tmp_path / "object.json"
    p.write_text(json.dumps({"front": "CPU", "back": "Central Processing Unit"}))
    with pytest.raises(ValueError, match="'cards'"):
        loader.load(p)


def test_loader_non_dict_card_raises_value_error(
    loader: CardsDataLoader, tmp_path: Path
) -> None:
    p = tmp_path / "bad_card.json"
    p.write_text(json.dumps(["not a dict"]))
    with pytest.raises(ValueError, match="JSON object"):
        loader.load(p)


@pytest.mark.parametrize(
    "card",
    [
        {"front": 123, "back": "Central Processing Unit"},
        {"front": "CPU", "back": True},
    ],
)
def test_loader_non_string_field_value_raises_value_error(
    loader: CardsDataLoader, tmp_path: Path, card: dict[str, Any]
) -> None:
    p = tmp_path / "bad_type.json"
    p.write_text(json.dumps([card]))
    with pytest.raises(ValueError, match="non-string"):
        loader.load(p)


@pytest.mark.parametrize(
    "extra",
    [
        {"tags": ["hardware"]},
        {"difficulty": "easy", "source": "textbook"},
    ],
)
def test_loader_ignores_extra_fields(
    loader: CardsDataLoader, tmp_path: Path, extra: dict[str, Any]
) -> None:
    card = {**SAMPLE_CARDS[0], **extra}
    p = tmp_path / "extra_fields.json"
    p.write_text(json.dumps([card]))
    cards = loader.load(p)
    assert cards[0].front == SAMPLE_CARDS[0]["front"]
    assert cards[0].back == SAMPLE_CARDS[0]["back"]
