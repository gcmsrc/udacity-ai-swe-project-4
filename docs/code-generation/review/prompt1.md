<role>
Senior Python developer implementing fixes suggested by a code review.
</role>

<context>
Code review is provided in submission/docs/code-generation/review/code-review.md
</context>

<task>
Implement only suggested fixes provided below.
</task>

<suggested_fixes>
Issue D1
STATUS: ACCEPT, import the constant from the production module

Issue D2
STATUS: ACCEPT, use a default value equal to "cwd()/data/db/flashcards.db" (but this may require creting this path, so we need to update the code)

Issue T1
STATUS: ACCEPT, fix

Issue S1
STATUS: ACCEPT, please add the finally block

Issue S2
STATUS: ACCEPT, remove the dead assignment

Issue S3
STATUS: ACCEPT

Issue A1
STATUS: DISCARD, it is ok to use random.choices with replacement, it is not a big issue.

Issue A2
STATUS: drop the cross-session data

Issue 01
STATUS: ACCEPT, pass the QuizMode directly to the QuizEngine constructor

Issue TT1
STATUS: ACCEPT

Formatting
1. Run black
2. Fix flake8 issues
3. Fix mypy errors

Testing
Ignore the uncovered lines.