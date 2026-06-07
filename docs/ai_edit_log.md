# AI Edit Log

This log documents meaningful interactions with AI (Claude, via Claude Code) during
the development of the FlashCard CLI application. It records what I asked for, what the
AI produced, which suggestions I accepted or rejected and **why**, and what I took away
from each interaction. The entries are ordered chronologically so the progression in how
I worked with the AI is visible.

A recurring theme emerges across these entries: the AI is excellent at producing
plausible, well-structured code quickly, but it tends toward **scope creep**,
**over-engineering**, and **test theatre**. The value I added was almost always in
*editing down* and re-anchoring its output to the agreed spec, not in generating more.

---

## 2026-06-07 11:09:37 - Designing the architecture, then forcing it to a stricter contract

**Context:** Before writing any code I wanted a complete architecture for a Typer-based
flashcard quiz app: module breakdown, design patterns, dependency diagram, and extension
points.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** I asked Claude to act as a senior Python developer following SOLID
principles and produce a full architecture in `docs/ARCHITECTURE.md` — six modules, design
patterns, a data-flow diagram, key interfaces, and a guide for adding a new quiz mode. In a
follow-up I asked for two specific changes: (1) replace the `Protocol`-based strategy
interface with a strict ABC, and (2) reorganise `utils/` and `tests/` into sub-packages
(each with its own `__init__.py`) instead of flat modules.

**AI Response:** The first pass defined `models`, `data_loader`, `strategies`,
`quiz_engine`, `ui`, and `main`, applied the Strategy pattern via a `QuizMode` **Protocol**,
and gave an extension guide. After my follow-up it redefined `QuizMode` as an ABC with
`@abstractmethod`, split `strategies` into one file per strategy, and mirrored the layout
under `tests/`.

**Changes Made:** I rejected the AI's default of a `Protocol` and required an ABC. I also
imposed the sub-package structure rather than the flat layout it proposed.

**Reasoning:** A `Protocol` only enforces structural typing at type-check time; a subclass
that forgets to implement a method still instantiates at runtime. An ABC fails loudly at
instantiation, which I wanted as a guardrail while implementing several strategies. The
sub-package layout was a deliberate bet that each module would grow, and I'd rather pay the
`__init__.py` cost up front than refactor flat files later.

**Outcome:** A clear `ARCHITECTURE.md` that became the contract for every later session —
and, crucially, the document I kept checking the AI's output *against*.

**Lessons Learned:** The AI's first design choice is a reasonable default, not a
recommendation tuned to my goals. It's worth stating non-functional intentions ("I expect
this to grow", "I want runtime enforcement") explicitly, because the AI optimises for the
literal request otherwise.

---

## 2026-06-07 14:07:55 - The GamePlanner that should never have existed (an unsuccessful arc)

**Context:** Completing the Strategy pattern. This entry spans several sessions because the
mistake took a while to fully unwind — which is itself the lesson.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** I asked for the concrete `SequentialStrategy` and `RandomStrategy`, a
`get_strategy` factory, and tests. In a follow-up I said the Strategy pattern was "missing a
piece" and asked for a context class — `GamePlanner` — with `set_strategy()` and `plan()`.

**AI Response:** It dutifully built `GamePlanner` as a context object holding a `QuizMode`
and delegating ordering. It looked like a textbook Strategy-pattern context.

**Changes Made / Reasoning (over time):** This is where I got it wrong *with* the AI rather
than the AI getting it wrong alone. A later code review (which I prompted) pointed out that
`GamePlanner` **duplicated the context role already filled by `QuizEngine`** and wasn't in
the architecture spec — classic over-engineering driven by my own "complete the pattern by
the book" instinct. I initially kept it. Several sessions later, the full-codebase review
flagged it again as **dead production code never referenced by `main.py`**. At that point I
accepted the finding and **deleted `GamePlanner` and all its tests entirely**, passing the
`QuizMode` directly to `QuizEngine`.

**Outcome:** A simpler call graph with one context object, not two. Removing it deleted code
and tests with zero behavioural loss.

**Lessons Learned:** The AI happily implements patterns for their own sake when I ask in
those terms. "Complete the Strategy pattern" is the wrong framing; "what's the simplest
wiring that works" is the right one. I also learned that a finding I dismiss in one review
is worth re-reading when it resurfaces — the review was right the first time, and I carried
dead code for several sessions because I didn't act on it.

---

## 2026-06-07 14:47:14 - When I asked the AI to add something and it correctly said no

**Context:** I was uneasy about a possible test gap and an organisational tweak, and asked
the AI to make both changes.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** I asked whether `GamePlanner` should validate unknown strategy names
internally (replacing `get_strategy`'s check) and whether `GamePlanner` should be moved into
the package `__init__.py`. The framing assumed both were good ideas.

**AI Response:** It **advised against both**. It explained that `GamePlanner` already
receives an already-validated `QuizMode` instance, so there's nothing to test for unknown
modes at that layer — invalid strings are caught upstream by `get_strategy`, which already
has its own test. Moving validation into `GamePlanner` would couple the context class to the
registry (mixing concerns), and inlining it into `__init__.py` would overload that file. It
made no code changes.

**Changes Made:** None — I accepted the AI's pushback and dropped both ideas.

**Reasoning:** Its argument about where validation belongs was correct: adding a test for
"unknown mode" at a layer that can't receive an unknown mode would have been more test
theatre, and duplicating validation would have created two sources of truth. I had been
pattern-matching on "more tests = better" rather than thinking about which layer owns the
invariant.

**Outcome:** No change, and I avoided adding a meaningless test plus a coupling I'd have
later had to unpick.

**Lessons Learned:** It's worth asking the AI "should I?" rather than only "do X." When I
phrase a request as a question instead of an instruction, it's far more willing to challenge
the premise — and here that pushback saved me from work that would have been actively
harmful. (Ironically the AI defended `GamePlanner`'s boundaries here while a later review
showed the class itself shouldn't exist — both judgments were locally correct.)

---

## 2026-06-07 15:58:05 - DB layer: rejecting the AI's schema and its security-theatre tests

**Context:** Implementing session persistence — a `DatabaseConnection` singleton and a
`SessionRepository`.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** I asked Claude to implement the stubs per the spec, then to simplify to
a single `sessions` table with a JSON-serialised result (dropping the separate
`card_results` table), and finally to add explicit SQL-injection tests using a classic
`OR '1'='1'` payload.

**AI Response:** It first built the two-table schema from the spec, then simplified to the
single-table JSON design on request. For the injection tests it wrote three cases firing the
`OR '1'='1'` payload through the repository and asserting it was treated as a literal.

**Changes Made:** I kept the simplified single-table schema but **updated `ARCHITECTURE.md`
to match it** (the review caught that code now deviated from spec). I later **deleted all
three SQL-injection tests**.

**Reasoning:** The injection tests were test theatre: with parameterised queries, those
tests really verify that Python's `sqlite3` library binds parameters correctly — they test
the standard library, not my application logic. They'd pass forever regardless of bugs in my
code, so they bought no signal. The schema simplification was genuinely worth keeping
(card-level querying turned out to be unused — see the full-codebase review below), but only
once the spec reflected reality.

**Outcome:** A leaner DB layer, a spec that matched the code, and a test suite that tests my
logic rather than SQLite's.

**Lessons Learned:** "Add security tests" sounds responsible but can produce tests that
assert nothing about your own code. The right question is "what behaviour of *mine* could
break here?" — and for parameterised queries, the answer was "nothing these tests would
catch." Also: every time I let the AI change a design, I now treat updating the spec as part
of the same task, not a follow-up.

---

## 2026-06-07 17:06:14 - Redesigning the strategy interface: alternatives first, then cutting back

**Context:** The `QuizMode` strategies originally exposed a single `order()` method that
returned the full deck up front. I wanted to support an Adaptive mode that reacts to answers
mid-session, which `order()` couldn't express. Before committing, I asked the AI to map out
how `SessionRepository` should reach the strategy layer.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** I first asked for three architecture alternatives for wiring
`SessionRepository` between `GamePlanner` and the strategies, with trade-offs. After reading
them I reconsidered and gave a much narrower instruction: `SessionRepository` is only for
session create/save, the Adaptive strategy should be self-contained (in-session weighted
draws, no DB), and all strategies should replace `order()` with a pull-based
`get_next_card()`.

**AI Response:** It produced `docs/planning/alternatives/session-repository-alternatives.md`
with three options (a `configure()` hook, a callable provider, and an `OrderingContext`).
Once I narrowed the scope it reworked the `QuizMode` ABC to `setup(cards)` +
`get_next_card() -> Flashcard | None` with a default no-op `record_result()`, rewrote
Sequential and Random to advance an index, and implemented Adaptive as a weighted
`random.choices` draw that doubles a card's weight when it's missed.

**Changes Made:** I rejected all three of the AI's original alternatives. Every one of them
assumed the strategy needed access to the repository; I decided it didn't, and collapsed the
problem to a self-contained per-card loop instead.

**Reasoning:** The three alternatives were each solving a coupling problem I could avoid
entirely by removing the coupling. Letting strategies read the DB would have spread
persistence concerns into the ordering layer and made every strategy harder to test in
isolation. A pull-based `get_next_card()` kept each strategy a pure function of the cards it
was given, which is far simpler to reason about and test.

**Reasoning (in hindsight):** Picking `random.choices` was the AI's choice and I accepted it
without thinking hard about replacement — it samples **with replacement**, which a later
review showed could starve some cards of any draw. That was a real flaw I let through here.

**Outcome:** 27 strategy/engine tests passing and a cleaner interface — but with a latent
sampling bug I didn't catch until the full-codebase review.

**Lessons Learned:** Asking for alternatives is most useful as a way to notice the question
is wrong: the best move was none of the three, it was to delete the constraint they all
shared. I also learned not to wave through the AI's incidental implementation choices
(`random.choices`) just because the surrounding design is sound — the small unexamined
decisions are where the real bugs hid.

---

## 2026-06-07 20:02:08 - Full-codebase review: the AI catching a real correctness bug it wrote

**Context:** With the app feature-complete, I asked for an exhaustive review of all source
and tests.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** I asked Claude to review everything under the source and test trees
against the standard framework plus the five AI-specific pitfall checks, run all
format/lint/type/coverage tools, and write a ranked report.

**AI Response:** It produced 10 findings. Two were HIGH severity and genuinely important:
(1) `AdaptiveStrategy` sampled with `random.choices` (**with replacement**), so a
high-weight card could consume every remaining draw slot and leave other cards never shown —
a real behavioural bug, not a style nit; and (2) `SessionRepository.get_missed_cards()` was
**dead production code** — never called by `main.py` or the adaptive strategy, meaning the
cross-session adaptive seeding described in `ARCHITECTURE.md` was never actually
implemented. It also flagged a missing `try/finally` around DB operations (a leaked
connection if the engine raised) and several lower-severity items.

**Changes Made:** I accepted the dead-code finding and **removed `get_missed_cards()` and
its tests entirely**, dropping the unimplemented cross-session feature rather than pretending
it existed. I wrapped the DB block in `try/finally` so `disconnect()` always runs. I
deferred the `random.choices` with-replacement fix as a known, documented limitation rather
than rushing a sampling rewrite.

**Reasoning:** The dead `get_missed_cards()` was the more dangerous problem because the
*spec claimed a feature the code didn't deliver* — a documentation lie is worse than a
missing function. Deleting it made the spec honest. The `try/finally` was a clear
reliability win for a few lines. I held off on the sampling change because a correct
fix (sampling without replacement while respecting weights) deserved its own focused session
rather than being bundled into review cleanup.

**Outcome:** 84 passing tests, no dead code, a spec that matched reality, and a documented
known-limitation instead of a hidden bug.

**Lessons Learned:** The most valuable AI review findings weren't the lint-level ones — they
were "this code claims to do something it doesn't" and "this branch can leak a resource."
Those are exactly the things I'd skim past reading my own diff. I also learned to **separate
"accept and fix now" from "accept but schedule"**: not every true finding should be fixed in
the same commit, and saying so explicitly kept the cleanup focused.

---

## 2026-06-07 21:03:32 - `--show-history` feature: review caught a crash path and a coverage hole

**Context:** Adding a `--show-history` flag that prints a bar chart of past scores for a
deck, then reviewing the change.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** I asked for `get_history()` on the repository, a `show_history()` renderer
on both the plain and rich UIs, a `--show-history` CLI flag, and updated tests. Then I ran a
high-effort review on the diff.

**AI Response:** The feature worked and tests passed. The review, however, surfaced an
uncaught `json.JSONDecodeError` from `get_history` that would surface as a raw traceback to
the user (HIGH), a path-string mismatch between how `create_session` and `get_history`
identified a deck across runs (MEDIUM), duplicated bar-chart math across the two renderers,
and a **critical test gap: the `--show-history` branch in `main.py` had 0% integration
coverage** despite the unit tests passing.

**Changes Made:** I had the AI move JSON parsing into the model itself via a
`SessionResult.from_json()` classmethod (removing manual key access in the repository),
extract shared `_make_bar()` / `_attempt_label()` helpers so both renderers used one
implementation, add a `score` property to `SessionResult` to replace inline `correct/total`
divisions, and add the missing integration test that drives `--show-history` through the CLI
runner and asserts both `get_history` and `show_history` are actually called.

**Reasoning:** The 0%-coverage finding mattered most: every unit test passed, so the green
suite *looked* like proof the feature worked end-to-end when nothing exercised the actual CLI
branch. Centralising JSON parsing in the model fixed the crash path at its source rather than
catching the exception downstream, and the shared helpers removed the duplicated math that
would otherwise drift between the two UIs.

**Outcome:** 100 passing tests including a real end-to-end test of the new flag, no duplicated
rendering logic, and parsing owned by the model.

**Lessons Learned:** A passing unit suite is not the same as a covered feature. The review's
coverage check was the thing that caught "this whole branch is untested" — something the
green checkmarks actively hid. I now treat per-feature integration coverage, not just the
overall percentage, as the bar for "done."

---

## Cross-cutting reflections

- **The AI's default mode is additive.** Across these sessions it added a `GamePlanner`
  context, security-theatre tests, three design alternatives I didn't need, and a dead
  cross-session method. My main job was subtraction — deleting things and re-anchoring to the
  spec.
- **"Review your own output for AI-specific pitfalls" was the highest-leverage prompt.** It
  reliably caught the AI's own scope creep, test theatre, and spec drift far better than a
  generic "review this code" request.
- **Phrasing a request as a question ("should I?") rather than a command ("do X") produced
  better judgment** — it's when the AI was most willing to talk me out of bad ideas.
- **A spec is only useful if you enforce it.** Every time I let the AI change a design, the
  fix was incomplete until `ARCHITECTURE.md` was updated in the same step. The most dangerous
  bugs were the ones where the doc promised behaviour the code didn't deliver.
