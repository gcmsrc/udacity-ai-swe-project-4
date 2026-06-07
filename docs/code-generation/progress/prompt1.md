<role>
Senior Python developer implementing planned architecture
</role>

<task>
Add the functionality to show the user history of a specific deck, by retrievving the user performance from the database.
</task>

<context>
You are implementing code that was specified in @docs/ARCHITECTURE.md
</context>

<requirements>
<functionality>
- Users specify if they wnt to shw the progress or not via a flag in the main.py file
- If the user wants to show the progress, the application should retrieve the user performance from the database and show it to the user
- For the TerminalUI, show a ASCII-based bar chart representing (sorted from oldest to latest) the percengate of correct answes
- For the TerminalRichUI, show a visually appealing bar chart using the rich library
</functionality>

<error_handling>
If there is no history, the performance is already showed and simply returna a message saing: "No history found for this deck; keep on exercising and you will see it here soon!"
</error_handling>

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
- The implementation of the show_history function in the TerminalUI and TerminalRichUI classes
- Update the main.py file to add the flag to show the progress and the functionality to retrieve the history from the database.
</deliverables>