<role>
Senior Python developer implementing planned architecture
</role>

<task>
Implement the session-based handling to keep track of the users' progress
</task>

<context>
You are implementing code that was specified in @docs/ARCHITECTURE.md
</context>

<interface_specification>
A senior developer implemented a high-level interface and testing for the db-based session handling. You need to build the actual implementation (as many things are not implemented yet)
</interface_specification>

<requirements>
<functionality>
- Sessions are stored in a "sessions.db" file in the `data` directory
- If the "sessions.db" does not exist, it should be created the first time.
- The schema for the database includes a session id (unique), a timestamp of the session, a hashed key of the dataset path, the Session result
- There should be some built-in functions to 1) save a session result, 2) retrieve the missed cards for a given dataset for the last session (use the timestamp), a method to close the session so it does not remaing hanging
</functionality>

<error_handling>
We should handle the following errors:
* sqlite3.OperationalError: if the sqlite database cannot be accessed
* sqlite3.IntegrityError: when haddding two sessions with same ID
* raise all other errors gracefully
</error_handling>

<security>
You must handles SQL injection attacks
</security>

<code_quality>
- Comprehensive module and class docstrings
- Method docstrings with Args, Returns, Raises sections
- Full type hints on all signatures
</code_quality>
</requirements>

<testing>
Update the testing accordingly.
</testing>

<constraints>
- Python standard library only
- Follow PEP 8 style guide
- Ok to inite sqlite3
</constraints>

<deliverables>
Provide:
- The implementation of the SessionRepository class
- The tests for the SessionRepository class
- Provide a summary of the changes you did inside docs/code-generation/db/implementation_summary.md`
</deliverables>