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
Magic values
SQL literal
STATUS: ACCEPT, extract th SQL strings to named constant

PAYLOAD
STATUS: ACCEPT, should we have a "to_json" method in the SessionResult class so that is de-coupled from the SessionRepository class?

Type Safey
__new__
STATUS: ACCEPT, declare _conn: sqlite3.Connection | None = None as a class-level attribute

Missing generic type args
STATUS: ACCEPT, declare params: tuple[()] = () and -> list[dict[str, object]]

Any return
STATUS: ACCEPT, cast or type-guard: result_data: dict[str, object] = json.loads(...) then return list(result_data.get("missed", []))

Generator fixture type
STATUS: ACCEPT, -> Generator[DatabaseConnection, None, None]

Code smells
Unclear ownership of close() - update the docs/ARCHITECTURE.md to reflect the new changes

AI-specific checks

Context gaps
Update the docs/ARCHITECTURE.md to reflect the new changes (only the `sessions` table is needed)

Over-engineering
Reset the singleton between tests. can you implement a _reset() method for the session repository to clear the database entirely? and add it to the fixture (before close)

SQL injectin
STATUS: ACCEPT, remove the sql injection tests

Formatting checks
Please run black, isort and flake8 to fix the issues.
</suggested_fixes>

