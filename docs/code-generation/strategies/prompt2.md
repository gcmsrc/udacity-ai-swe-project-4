<role>
Senior Python developer implementing fixes suggested by a code review.
</role>

<context>
Code review is provided in submission/docs/code-generation/strategies/code-review.md
</context>

<task>
Implement only suggested fixes provided below.
</task>

<suggested_fixes>
Magic values:
ISSUE 1
STATUS: ACCEPT, drop the explicit list from the docstring

Complexity:
Issue 2
STATUS: IGNORE, they will be implemented later in the next step.

Issue 3:
STATUS: IGNORE, the AdaptiveStrategy will be implemented later on.

Issue 4:
STATUS: ACCEPT, list the AdaptiveStrategy in the __all__ variable.

Context gaps:
Issue 5 and 6:
STATUS: IGNORE

OverEngineering:
Issue 7
STATUS: IGNORE, I plan to implement a different QuizEngine which will record a session and persist stuff to a database, so it will be conceptually different than the GamePlanner.

Test Theatre
Issue 8
STATUS: ACCEPT, remove trivial assertsions

Issue 9:
STATUS: ACCEPT, that was a big miss

Issue 10:
STATUS: IGNORE, the AdaptiveStrategy will be implemented later on.

Architectural mismatches:
Issue 11
STATUS: ACCEPT, use GamePlanner only

Formatting checks:
Issue flake8:
Run black, isort and flake8 to fix the issues.
</suggested_fixes>