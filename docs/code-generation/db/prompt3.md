<role>
Senior Python developer implementing fixes suggested by a code review.
</role>

<context>
Code review is provided in submission/docs/code-generation/db/code-review-rethink.md
</context>

<task>
Implement only suggested fixes provided below.
</task>

<suggested_fixes>
1. Duplication
BaseIndexedStrategy
STATUS: ACCEPT, extract a _BaseIndexedStrategy mixin with shared __init__, _cards, _index, and get_next_card() methods. Each subclass only needs to override setup().

2. Magic Values
_MISSED_WEIGHT_MULTIPLIER: float = 2.0
STATUS: ACCEPT

3. Type Safety
All issues - accept and implement all

4. Complexity
STATUS: ACCEPT, show_summary will be implemented later on, not now. Remove from the quiz engine and remove from testing.

5. Code smells
Discard everyting. but game_planner.py remove the @property for the strategy (just use the `_strategy` attribute)

----
AI CHECKS

4. Test theatre
test_adaptive_correct_answer_does_not_change_weight - replace with a statistical assertion, I agree

`AdaptiveStrategy.record_result()` with a card not in `_cards` — currently raises `StopIteration` (opaque); no test covers this. --- agree fix it
- Any strategy's `get_next_card()` called before `setup()` — returns `None` silently; no test documents or verifies this contract - agree, fix it

Also, I would like you to add more "assert ....called_once and called_once_with(....)" to the tests, especialyl given the nested nature of the QuizEngine (e.g., `quiz_engine.run()` calls `strategy.setup()` once, then loops on `get_next_card()`, feeds `record_result()` after each answer, returns a `SessionResult`.)


</suggested_fixes>