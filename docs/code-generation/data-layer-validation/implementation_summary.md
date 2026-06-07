# Implementation Summary: CardsDataLoader

## Files Changed

| File | Change |
|---|---|
| `utils/data_loader/data_loader.py` | Added `CardsDataLoader` class; refactored `load_flashcards` to delegate to it |
| `utils/data_loader/__init__.py` | Re-exported `CardsDataLoader` alongside `load_flashcards` |
| `tests/data_loader/test_data_loader.py` | Added 13 new tests for `CardsDataLoader`; kept all 8 existing `load_flashcards` tests |

---

## CardsDataLoader Design

### Public interface

```python
class CardsDataLoader:
    def load(self, path: Path) -> list[Flashcard]: ...
```

A single `load` method mirrors the existing `load_flashcards` function signature but raises standard Python exceptions instead of `typer.Exit`, keeping the class independent of the CLI layer.

### Supported JSON formats

1. **Array format** — direct list of card objects:
   ```json
   [{"front": "CPU", "back": "Central Processing Unit"}]
   ```

2. **Wrapped format** — object with a `"cards"` key:
   ```json
   {"cards": [{"front": "CPU", "back": "Central Processing Unit"}]}
   ```

Format detection is handled by `_extract_cards_list`, which checks whether the parsed value is a `list` or a `dict` containing `"cards"`.

### Error handling

| Condition | Exception raised |
|---|---|
| Non-absolute path | `ValueError` |
| File does not exist | `FileNotFoundError` |
| File is not valid JSON | `ValueError` |
| JSON is neither a list nor a `{"cards": ...}` object | `ValueError` |
| A card object is missing `"front"` or `"back"` | `ValueError` |
| Deck contains zero cards | `ValueError` |

All messages include the source path and, where applicable, the zero-based card index.

### Security

`load` checks `Path(path).is_absolute()` before doing any I/O. Relative paths (including `../` traversal attempts) raise `ValueError` immediately without touching the filesystem.

---

## load_flashcards (CLI wrapper)

`load_flashcards` now instantiates `CardsDataLoader`, calls `.load()`, and wraps any `FileNotFoundError` or `ValueError` in a `typer.echo` + `typer.Exit(1)`. All eight original tests continue to pass unchanged.

---

## Tests Added (CardsDataLoader)

| Test | What it covers |
|---|---|
| `test_loader_array_format_returns_flashcards` | Array format → list of Flashcard |
| `test_loader_array_format_maps_fields` | Field mapping (front / back) |
| `test_loader_wrapped_format_returns_flashcards` | Wrapped format → list of Flashcard |
| `test_loader_wrapped_format_maps_fields` | Field mapping from wrapped format |
| `test_loader_relative_path_raises_value_error` | Relative path rejected |
| `test_loader_path_traversal_raises_value_error` | `../../` traversal rejected |
| `test_loader_missing_file_raises_file_not_found` | Non-existent file |
| `test_loader_invalid_json_raises_value_error` | Malformed JSON |
| `test_loader_missing_front_raises_value_error` | Card missing `"front"` |
| `test_loader_missing_back_raises_value_error` | Card missing `"back"` |
| `test_loader_empty_deck_raises_value_error` | Empty array |
| `test_loader_plain_object_without_cards_key_raises_value_error` | Object without `"cards"` |
| `test_loader_non_dict_card_raises_value_error` | Array element is not a dict |

Total: **21 tests**, all passing.
