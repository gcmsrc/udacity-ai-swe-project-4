# Code Review: `data_loader.py` and `test_data_loader.py`

---

## Part 1 — Standard Analysis Framework

### 1. Duplication

**Issue 1.1 — Redundant `Path()` wrapping**
- Lines: 47, 50 (`load`)
- Category: Duplication / Code Smell
- Current:
  ```python
  if not Path(path).is_absolute():
      raise ValueError(f"Path must be absolute, got: {path}")
  path = Path(path).resolve()
  ```
- Suggested:
  ```python
  if not path.is_absolute():
      raise ValueError(f"Path must be absolute, got: {path}")
  path = path.resolve()
  ```
- Benefit: `path` is already typed as `Path`; wrapping it again is noise and implies the parameter might be `str`.
- Refactoring risk: LOW

---

**Issue 1.2 — Duplicate test pairs for array vs. wrapped format**
- Lines: 55–84 (`test_data_loader.py`)
- Category: Duplication
- Current: `test_loader_array_format_returns_flashcards` and `test_loader_wrapped_format_returns_flashcards` assert identical things; same for the `_maps_fields` pair.
- Suggested: Parametrize over fixtures:
  ```python
  @pytest.mark.parametrize("deck_fixture", ["valid_array_deck", "valid_wrapped_deck"])
  def test_loader_returns_two_flashcards(request, loader, deck_fixture):
      cards = loader.load(request.getfixturevalue(deck_fixture))
      assert len(cards) == 2
      assert all(isinstance(c, Flashcard) for c in cards)
  ```
- Benefit: Fewer tests to maintain; adding a third format only requires one fixture, not two new tests.
- Refactoring risk: LOW

---

**Issue 1.3 — Duplicated fixture card data**
- Lines: 21–27 and 31–40 (`test_data_loader.py`)
- Category: Duplication / Magic Values
- Current: The same two card dicts appear verbatim in both `valid_array_deck` and `valid_wrapped_deck`.
- Suggested: Extract to a module-level constant:
  ```python
  SAMPLE_CARDS = [
      {"front": "CPU", "back": "Central Processing Unit"},
      {"front": "RAM", "back": "Random Access Memory"},
  ]
  ```
- Benefit: Single place to update test data; values like `"CPU"` and `"Central Processing Unit"` stop floating freely.
- Refactoring risk: LOW

---

### 2. Magic Values

**Issue 2.1 — Repeated field name literals `"front"` / `"back"`**
- Lines: 108–113 (`data_loader.py`)
- Category: Magic Values
- Current:
  ```python
  for key in ("front", "back"):
      if key not in item:
          raise ValueError(f"Card at index {index} is missing '{key}' in {path}")
  return Flashcard(front=item["front"], back=item["back"])
  ```
- Suggested: Define constants at module level:
  ```python
  _REQUIRED_FIELDS = ("front", "back")
  ```
- Benefit: Avoids the string appearing in three different places; a rename only needs one edit.
- Refactoring risk: LOW

---

**Issue 2.2 — `"cards"` key used in two places**
- Lines: 86–89 (`data_loader.py`)
- Category: Magic Values
- Current:
  ```python
  if isinstance(data, dict) and "cards" in data:
      return data["cards"]
  raise ValueError(f"Expected a JSON array or an object with a 'cards' key in {path}")
  ```
- Suggested:
  ```python
  _WRAPPED_KEY = "cards"
  ...
  if isinstance(data, dict) and _WRAPPED_KEY in data:
      return data[_WRAPPED_KEY]
  raise ValueError(f"Expected a JSON array or an object with a '{_WRAPPED_KEY}' key in {path}")
  ```
- Benefit: If the key ever changes, only one line needs updating.
- Refactoring risk: LOW

---

### 3. Type Safety

**Issue 3.1 — `_extract_cards_list` return typed as `list[Any]`**
- Line: 71 (`data_loader.py`)
- Category: Type Safety
- Current: `def _extract_cards_list(self, data: Any, path: Path) -> list[Any]:`
- Note: This is accurate given the input is raw JSON, but the return value flows directly into `_parse_card` which expects `dict`-like items. The loose typing hides that the method's contract is "a list of things we believe are dicts."
- Suggested: No code change required, but a comment clarifying the expected shape of each element would reduce surprise. Alternatively, `list[dict[str, Any]]` could be used and checked with a runtime guard.
- Benefit: Clearer intent; type checkers can catch misuse downstream.
- Refactoring risk: LOW

---

### 4. Complexity

No methods exceed 30 lines. No deeply nested logic. This section passes cleanly.

---

### 5. Code Smells

**Issue 5.1 — Stateless class `CardsDataLoader`**
- Lines: 17–113 (`data_loader.py`)
- Category: Code Smell / Over-engineering
- Current: `CardsDataLoader` holds no state; every method only receives arguments and returns values.
- Suggested: Replace with module-level functions (`_extract_cards_list`, `_parse_card`, `_load`) and keep `load_flashcards` as the single public entry point.
- Benefit: Eliminates unnecessary object instantiation in `load_flashcards` (`CardsDataLoader().load(path)`); reduces indirection.
- Refactoring risk: MEDIUM — tests import `CardsDataLoader` directly; the `__init__.py` public surface would need updating.

---

## Part 2 — AI-Specific Checks

### 1. Context Gaps

**Issue A1 — `CardsDataLoader` is not part of the architecture spec**
- Relevant file: `docs/ARCHITECTURE.md`, section 5 "Key Interfaces"
- The architecture specifies `load_flashcards(path: Path) -> list[Flashcard]` as the only public symbol. `CardsDataLoader` is an implementation detail, but the tests import it directly (`from utils.data_loader import CardsDataLoader`), effectively making it part of the public API.
- Suggested: Either document `CardsDataLoader` in the architecture, or keep it internal and test only through `load_flashcards`.
- Refactoring risk: MEDIUM

---

**Issue A2 — No tests for `load_flashcards` (the public CLI wrapper)**
- File: `test_data_loader.py`
- The public function `load_flashcards` converts exceptions into `typer.Exit(1)` — this behaviour is untested. A future refactor that accidentally swallows an error or exits with the wrong code would not be caught.
- Suggested: Add at least two tests:
  ```python
  def test_load_flashcards_returns_cards(valid_array_deck):
      cards = load_flashcards(valid_array_deck)
      assert len(cards) == 2

  def test_load_flashcards_exits_on_missing_file(tmp_path):
      with pytest.raises(SystemExit):
          load_flashcards(tmp_path / "missing.json")
  ```
- Refactoring risk: LOW

---

### 2. Phantom Dependencies

No phantom dependencies. `typer`, `json`, and `pathlib` are all standard or explicitly listed in `requirements.txt`.

---

### 3. Over-engineering

**Issue A3 — Undocumented wrapped JSON format**
- Lines: 22–26, 84–90 (`data_loader.py`)
- The architecture doc only shows the array format. The wrapped format (`{"cards": [...]}`) is an AI addition not requested in the spec.
- If downstream tooling always produces the array format, this branch is dead code. If it is needed, it should be documented in the architecture.
- Suggested: Either remove the wrapped-format branch, or add it to `docs/ARCHITECTURE.md` and confirm with stakeholders.
- Refactoring risk: LOW (removal) / LOW (documentation)

---

### 4. Test Theatre

**Issue A4 — `isinstance` assertion adds little value**
- Lines: 60, 76 (`test_data_loader.py`)
- Current:
  ```python
  assert all(isinstance(c, Flashcard) for c in cards)
  ```
- This tests Python's dataclass constructor, not application logic. If `load` returns the wrong type the downstream `assert cards[0].front == "CPU"` would fail more informatively anyway.
- Suggested: Remove the `isinstance` assertions; rely on field-level assertions to implicitly verify the type.
- Refactoring risk: LOW

---

### 5. Missing Edge Cases

**Issue A5 — No test for non-string `front`/`back` values**
- `{"front": 123, "back": true}` would silently produce a `Flashcard(front=123, back=True)`. The loader does not validate that field values are strings.
- Suggested: Add a validation step in `_parse_card` and a corresponding test.
- Refactoring risk: LOW (test), MEDIUM (production code — a breaking change if callers pass numeric keys intentionally).

---

**Issue A6 — No test for wrapped format with empty `cards` list**
- `{"cards": []}` should raise `ValueError("Deck is empty: ...")` (handled by the `if not cards_data` guard in `load`), but this code path is not tested for the wrapped format specifically.
- Suggested:
  ```python
  def test_loader_wrapped_empty_deck_raises_value_error(loader, tmp_path):
      p = tmp_path / "wrapped_empty.json"
      p.write_text(json.dumps({"cards": []}))
      with pytest.raises(ValueError, match="empty"):
          loader.load(p)
  ```
- Refactoring risk: LOW

---

**Issue A7 — No test for extra fields in card objects**
- `{"front": "CPU", "back": "...", "tags": ["hardware"]}` — does the loader ignore extra fields? It does (only `front`/`back` are accessed), but this is unverified. A regression that starts rejecting extra fields would go undetected.
- Suggested: Add a test asserting extra fields are silently ignored.
- Refactoring risk: LOW
