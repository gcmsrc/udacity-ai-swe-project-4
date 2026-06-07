# Flashcard Quiz

A CLI flashcard quiz application built with Python and [Typer](https://typer.tiangolo.com/).

## Features

- **Three quiz modes**
  - `sequential` — cards presented in deck order
  - `random` — cards shuffled each session
  - `adaptive` — missed cards are re-weighted and drawn more often until the session ends
- **Session persistence** — results are saved to a local SQLite database (`data/db/flashcards.db`)
- **Score history** — `--show-history` displays a per-attempt bar chart for the current deck after each session
- **Rich terminal UI** — clean prompts and a summary table powered by [Rich](https://github.com/Textualize/rich)
- **Bundled sample decks** — `data/sample_cards.json` and `data/countries.json` to get started immediately

## Demo

Running a quiz session (without history):

![Flashcard quiz without history](docs/gifs/flashcard-no-history.gif)

Running a quiz session with `--show-history`:

![Flashcard quiz with history](docs/gifs/demo-history.gif)

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) **or** pip

## Installation

### With uv (recommended)

```bash
uv sync
```

### With pip

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                 # installs the flashcard CLI entry-point
```

## Usage

Activate the environment before running (if using pip):

```bash
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### Via the `flashcard` CLI entry-point

```bash
flashcard data/sample_cards.json                       # sequential (default)
flashcard data/sample_cards.json --mode random
flashcard data/sample_cards.json --mode adaptive
flashcard data/sample_cards.json --show-history        # show score history after session
```

### Via Python directly

```bash
python src/flashcard_quiz/main.py data/sample_cards.json
python src/flashcard_quiz/main.py data/sample_cards.json --mode random
python src/flashcard_quiz/main.py data/sample_cards.json --mode adaptive
python src/flashcard_quiz/main.py data/sample_cards.json --show-history
```

### With uv (no manual activation needed)

```bash
uv run flashcard data/sample_cards.json
uv run flashcard data/sample_cards.json --mode adaptive
uv run flashcard data/sample_cards.json --show-history
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--mode` | `sequential` | Quiz ordering: `sequential`, `random`, or `adaptive` |
| `--show-history` | off | After the session, display a bar chart of per-attempt scores for the deck |
| `--plain-terminal` | off | Use plain text output instead of the Rich-styled UI |

## Deck format

Two JSON formats are supported.

**Array format** — a top-level list of card objects:

```json
[
  {"front": "CPU", "back": "Central Processing Unit"},
  {"front": "RAM", "back": "Random Access Memory"}
]
```

**Wrapped format** — an object with a `cards` key:

```json
{
  "cards": [
    {"front": "CPU", "back": "Central Processing Unit"},
    {"front": "RAM", "back": "Random Access Memory"}
  ]
}
```

Each card requires a `front` (question) and `back` (answer) string field.

## Environment configuration

The project reads configuration from a local `.env` file (git-ignored). Create it by copying the template:

```bash
cp .env.template .env
```

Then edit `.env` and set `TRACE_FILE` to the path where AI session traces should be written, e.g.:

```bash
TRACE_FILE="docs/background/traces.md"
```

## AI collaboration logs

This project keeps two records of its AI-assisted development:

- **`docs/background/traces.md`** — an automatic, raw log. A Claude Code `Stop` hook (`.claude/log_to_traces.sh`) appends the last user request and Claude response to the file pointed to by `TRACE_FILE` at the end of every session. To view it:

  ```bash
  less docs/background/traces.md
  ```

  Its purpose is an unfiltered audit trail of every prompt/response exchange, captured without manual effort.

- **`docs/background/ai_edit_log_full.md`** — a curated summary. The `/log-session` command summarises the current session (context, request, and what changed) and appends a structured entry. Unlike the raw traces, this is a readable, high-level history of what was built and why.

## Development

Install dev dependencies:

```bash
uv sync --all-groups
```

| Command | Purpose |
|---|---|
| `uv run pytest` | Run tests |
| `uv run pytest --cov=src --cov-report=html` | Tests with coverage |
| `uv run black .` | Format code |
| `uv run isort .` | Sort imports |
| `uv run flake8 .` | Lint |
| `uv run mypy src` | Type-check |
