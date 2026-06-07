<role>
Senior Python developer implementing planned architecture
</role>

<task>
Implement the typer app in the main.py file to handle the CLI interface.
</task>

<context>
You are implementing code that was specified in @docs/ARCHITECTURE.md
</context>

<interface_specification>
A senior developer implemented a high-level interface and testing for the typer app. You need to build the actual implementation (as many things are not implemented yet)
</interface_specification>

<requirements>
<functionality>
- The app should be able to load the deck file using the CardsDataLoader class
- The app should be able to select the quiz mode using the QuizMode class
- The app should be able to run the quiz using the QuizEngine class
- The app should be able to handle the interaction via the UI class (TerminalUI by default)
- The app should be able to show the summary using the UI class
</functionality>

<error_handling>
We should handle the following errors:
* Issues with the deck file (handled by the CardsDataLoader class)
* Issues with the quiz mode (specified by the user, otherwise we use the default mode) (handled by the QuizMode class)
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
- The implementation of the main.py file
- The tests for the main.py file
- Provide a summary of the changes you did inside docs/code-generation/typer/implementation_summary.md`
</deliverables>