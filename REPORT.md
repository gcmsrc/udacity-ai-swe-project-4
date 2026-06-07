# AI-Assisted Development Project Report

**Student Name:** Giacomo Sarchioni  
**Project Title:** Flashcard Quiz — A CLI Study Tool  
**Date:** 2026-06-07  

## Executive Summary

I built **Flashcard Quiz**, a command-line app to study JSON flashcard decks in three
quiz modes — sequential, random, and adaptive — with results persisted to a local SQLite
database. It presents a card front, checks the typed answer, and ends each session with a
scored summary in a styled terminal UI. An optional `--show-history` flag draws a bar
chart of past scores for the deck.

The app is built in Python with `typer` for the CLI, `rich` for rendering, and the
standard-library `sqlite3` for persistence. It follows SOLID principles: a Strategy
pattern for quiz modes, a Singleton database connection, a `UI` Protocol with two
interchangeable renderers, and plain dataclasses as models. The final codebase is ~350
source statements covered by **100 tests at 99% coverage**, passing `black`, `isort`,
`flake8`, and `mypy --strict`.

I collaborated with **Claude (via Claude Code)** at every stage — architecture, code
generation, review, and debugging. The defining theme: the AI is fast and fluent at
producing plausible, well-structured code, but biases toward *adding* — extra patterns,
tests, abstractions. My main contribution was subtraction and re-anchoring its output to
the spec.

## Project Overview

### Problem Statement
Learners need a lightweight, scriptable way to drill flashcards without a heavy GUI or an
online account. The app is a fast CLI that runs any JSON deck and remembers progress locally.

### Solution Approach
I wrote a full `ARCHITECTURE.md` *before* any code and treated it as a contract. Each
quiz mode is a Strategy subclass of a `QuizMode` ABC (adding a mode means adding one
file); the database is a Singleton sharing one connection; the UI sits behind a Protocol
so the plain and `rich` renderers are drop-in interchangeable. **Stack:** Python 3.11+,
`typer`, `rich`, `sqlite3`, `pytest`, and `uv`.

### Final Features
- [x] Three quiz modes (sequential, random, adaptive)
- [x] Answer checking with a scored end-of-session summary
- [x] SQLite session persistence
- [x] `--show-history` score bar chart and a `rich`-styled UI

## AI Collaboration Experience

### AI Tools Used
- [x] Claude (Claude Code)

### Collaboration Workflow
1. **Structuring requests:** anchored prompts to the architecture spec and stated
   non-functional intent ("I expect this to grow", "enforce at runtime") explicitly.
2. **Tasks delegated:** scaffolding modules, generating tests, designing alternatives,
   and — most valuably — reviewing the AI's *own* output for pitfalls.
3. **Review and validation:** ran `pytest`, coverage, and the full lint/type stack on
   every increment, reading each diff against the spec before accepting it.
4. **Refining suggestions:** iterated by narrowing scope — rejecting over-built options
   and asking for the simplest wiring that satisfied the contract.

### Most Valuable AI Interactions

#### Example 1: Forcing the strategy contract to an ABC
**Context:** Designing the quiz-mode interface.  
**AI Prompt:** Produce a SOLID architecture with a Strategy pattern for quiz modes.  
**AI Response:** It defaulted to a `Protocol` for `QuizMode`.  
**Your Changes:** I required an `ABC` with `@abstractmethod` instead.  
**Outcome:** A subclass that forgets `order()` now fails loudly at instantiation rather
than slipping past the type-checker — the guardrail I wanted.  

#### Example 2: Review catching a real correctness bug  
**Context:** Full-codebase review of the feature-complete app.  
**AI Prompt:** Review all source and tests against AI-specific pitfall checks.  
**AI Response:** It flagged that `AdaptiveStrategy` sampled with `random.choices`
(*with replacement*), letting a high-weight card starve others, and that
`get_missed_cards()` was **dead code** — the cross-session feature the spec claimed but
never wired in.  
**Your Changes:** I deleted the dead method and its tests, wrapped DB calls in
`try/finally`, and documented the sampling issue as a known limitation.  
**Outcome:** A spec that matched reality, no dead code, no leaked connection.  

#### Example 3: The AI correctly talking me out of changes  
**Context:** I proposed moving validation into a context class and into `__init__.py`.  
**AI Prompt:** Should `GamePlanner` validate unknown strategy names and move into `__init__.py`?  
**AI Response:** It **advised against both** — the class already receives a validated
strategy, so the test would assert nothing, and the move would couple concerns.  
**Your Changes:** None; I dropped both ideas.  
**Outcome:** Avoided test theatre and a needless coupling. Phrasing a request as "should I?"
rather than "do X" produced markedly better judgment.

#### Example 4: A passing suite that hid an untested branch
**Context:** Adding `--show-history`.  
**AI Prompt:** Add the feature, then run a high-effort review on the diff.  
**AI Response:** Unit tests passed, but the review found the `--show-history` branch had
**0% integration coverage** and an uncaught `JSONDecodeError` crash path.  
**Your Changes:** Added an end-to-end CLI test and moved JSON parsing into a
`SessionResult.from_json()` classmethod, fixing the crash at its source.  
**Outcome:** 100 passing tests including a real end-to-end test; parsing owned by the model.

### Challenges with AI Collaboration
- Its default mode is **additive** — it produced a redundant `GamePlanner` context,
  SQL-injection "security theatre" tests, and three design alternatives I didn't need.
- It waved through **incidental implementation choices** (the `random.choices` sampler)
  even when the surrounding design was sound — the small unexamined decisions hid the bugs.
- Pattern: strong at structure and speed, weak at knowing when *not* to build.

## Software Engineering Practices

### Code Quality Measures
- [x] Code formatting (`black`, `isort`)
- [x] Linting (`flake8`, `mypy --strict`)
- [x] Type hints (strict, throughout)
- [x] Documentation (module docstrings + `ARCHITECTURE.md`)
- [x] Error handling (user-facing `typer.Exit`, no raw tracebacks)

### Testing Strategy
I wrote unit tests per package plus CLI integration tests via Typer's runner — **99%**
coverage across 100 tests. Not strict TDD, but I treated *per-feature integration
coverage*, not just the overall percentage, as the bar for "done" after a green unit
suite masked an untested branch.

### Design Patterns Used
- **Strategy:** `QuizMode` ABC with Sequential/Random/Adaptive subclasses for ordering.
- **Singleton:** `DatabaseConnection` owns the single SQLite connection per process.
- **Protocol (structural typing):** the `UI` contract with plain and `rich` renderers.

### Code Structure and Organization
Source is split into focused sub-packages (`models`, `data_loader`, `strategies`,
`quiz_engine`, `ui`, `db`), each re-exporting its public surface via `__init__.py`.
Separation of concerns is strict: models hold no logic, strategies are pure functions of
their cards, the UI does I/O only. Refactors included deleting the redundant `GamePlanner`,
collapsing two DB tables into one JSON-blob schema, and sharing bar-chart helpers.

## Technical Challenges and Solutions

### Challenge 1: Adaptive mode couldn't react mid-session
**Problem:** The original `order()` returned the whole deck up front, so adaptive mode
couldn't react to answers.  
**Solution:** I replaced it with a pull-based `get_next_card()` and a no-op
`record_result()`, keeping each strategy self-contained with no DB access.  
**AI Involvement:** It offered three repository-coupled alternatives; I rejected all
three and removed the shared constraint instead.  
**Lessons Learned:** Asking for alternatives is most useful for revealing the *question*
is wrong — the best option was none of them.

### Challenge 2: Spec drift after design changes
**Problem:** Letting the AI simplify the DB schema left `ARCHITECTURE.md` describing code
that no longer existed.  
**Solution:** I made updating the spec part of any design change; a review caught the drift.  
**Lessons Learned:** A documentation lie is worse than a missing function.

## Code Quality Analysis

### Metrics
- Lines of code: ~858 source / ~1,028 tests
- Test coverage: 99% (100 tests)
- Number of classes / functions: 14 classes, 47 functions
- Linting: clean under `black`, `isort`, `flake8`, `mypy --strict`

### Self-Assessment
- **Readability:** 5 — short modules, clear names, strict types.
- **Maintainability:** 5 — new modes/backends slot in via one file each.
- **Test Quality:** 4 — high coverage and real integration tests, once test theatre was removed.
- **Documentation:** 5 — a living architecture spec kept in sync with the code.

## Learning Outcomes

- **Technical skills:** Strategy/Singleton/Protocol patterns in idiomatic Python,
  `typer` + `rich` CLIs, SQLite persistence, and strict `mypy` typing.
- **AI collaboration:** the highest-leverage prompt was "review your own output for
  AI-specific pitfalls" — it caught scope creep and spec drift far better than a generic
  review. I learned to phrase proposals as questions and to separate "fix now" from
  "accept but schedule."
- **Engineering insight:** coverage percentage is not coverage of behaviour; a passing
  suite can hide an untested branch. Subtraction is a design activity, and the spec is
  the contract that makes review meaningful.

## Reflection

### What Worked Well
Writing the architecture first gave me a fixed reference to check the AI against. Self-review
prompts and a strict tooling gate caught the bugs the AI introduced — including one it wrote
itself. I'm proud of how cleanly the patterns let features drop in.

### What Could Be Improved
I carried the redundant `GamePlanner` for several sessions after a review first flagged it,
and waved through the `random.choices` sampler. Next time I'd act on findings sooner and
scrutinise incidental implementation choices, not just architecture.

### Future Enhancements
A spaced-repetition mode (already anticipated by the architecture), a without-replacement
adaptive sampler, deck-authoring commands, and a pluggable non-SQLite backend.

## Conclusion

AI made me far faster at producing structured code, but its instinct to add meant my real
value was editing down and enforcing the spec. I'll keep writing the architecture first,
gating each increment through tests and strict tooling, and asking the AI to audit its own
work — practices that consistently turned a fast first draft into something correct.

## Appendices

- **A — AI Interaction Log:** `docs/ai_edit_log.md` (curated) and `docs/background/traces.md`
  (raw hook-captured trail). Key entries: the ABC decision, the dead-code review, the
  0%-coverage `--show-history` finding.
- **B — Code Statistics:** 100 tests, 99% coverage, 348 source statements, clean
  `black`/`isort`/`flake8`/`mypy --strict`.
- **C — Additional Resources:** Typer and Rich docs; `docs/background/ARCHITECTURE.md`.
