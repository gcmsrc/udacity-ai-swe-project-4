<role>
Senior Python developer following SOLID principles
</role>

<task>
Design a modular architecture for a CLI flashcard application
</task>

<context>
<application_type>Typer CLI application for flashcard quizzing and integrated reporting tool</application_type>
<tech_stack>Python 3.8+, Typer, JSON, standard library only</tech_stack>
<user_workflow>
1. User runs the application via a CLI interface specifying the source data (a json file containing the flashcards) and the quiz mode
2. User responds to each question one after the other, obtaining immediate feedback on the correctness of the answer
3. At the end of the quiz, user shows its summary stats
</user_workflow>
</context>

<requirements>
<client_brief>
"We need a lightweight internal tool to help new hires memorize our server acronyms. It needs to run in the terminal, load data from JSON, and have different quiz modes. The code needs to be clean so we can extend it later."
<functional>
**Data Ingestion:**
- The app must load flashcards from a JSON file.
- It must validate the JSON structure. If the file is missing or malformed, the app should crash gracefully with a helpful error message, not a stack trace.
**Quiz Loop:**
- Present the "Front" of the card to the user.
- Accept text input for the answer.
- Compare input to the "Back" of the card (case-insensitive).
- Provide immediate feedback (Correct/Incorrect).
**Quiz Modes:**
- Sequential: Go through cards from 1 to N.
- Random: Shuffle the deck.
-Adaptive: This is the challenge feature. The app should prioritize cards the user previously got wrong.
**Session Stats:**
- At the end of a quiz, show a summary table: Total Questions, Accuracy %, and a list of terms the user missed.
</functional>
<technical>
**Architecture:**
The code must be modular. Do not submit a single main.py file. Separation of concerns is required (e.g., data_loader.py, quiz_engine.py, ui.py).
**Design Patterns:**
Use the Strategy Pattern for the Quiz Modes.
Why? Because Sequential, Random, and Adaptive are different algorithms for the same task (selecting the next card). This allows you to easily add a "Spaced Repetition" mode later without rewriting the whole app.
**Type Safety:**
All functions must have Python Type Hints.
**Testing:**
The project must include a test suite (using pytest).
You need at least 80% code coverage.
</technical>
</requirements>

<repo_structure>
The repo structure must have the following structure:
- main.py: Currently empty. This will be your entry point.
- data/: Place your sample JSON files here.
utils/: For helper modules (you will generate file_handler.py here).
tests/: Currently empty. You will direct the AI to fill this with pytest cases.
docs/: Contains templates for your "AI Interaction Log." You must update this log as you work.
.claude/ or .env: Configuration files for your AI tools.
</repo_structure>

<phases>
At a high level, the project should be developed in the following sequential phases:
1. Data Layer and Validation
2. Core Logic Design and Patterns
3. CLI and Interaction
</phases>

<deliverables>
Provide:
1. High-level archucture with module names and responisiblies
2. Specific design patterns to use and why they fit
3. Module dependency diagram showing data flow
4. File/folder structure
5. Extension points for adding new quiz modes

Save all this inside docs/ARCHITECTURE.md
</deliverables>