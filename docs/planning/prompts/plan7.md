<role>
Senior Python developer following SOLID principles
</role>
<task>
Update the architecture document to include integration of a `typer` app in the main.py file to handle the CLI interface.
</task>

<architecture_decisions>
Please refer to the documentation for typer:
https://typer.tiangolo.com/tutorial/typer-app/

Here you can find information on how to handle the CLI arguments:
https://typer.tiangolo.com/tutorial/first-steps/

You can use `python main.py` but also directly have an app called "flashcard" that will be called with `flashcard ...`

The arguments for the users to select should be:
* the path to the deck file
* the quiz mode (sequential, random, adaptive) - with sequential being the default option

The app should be able to:
* Load the deck file
* Select the quiz mode
* Run the quiz
* Show the summary

The app should be able to handle errors gracefully and show a friendly message to the user.


</architecture_decisions>

<deliverables>
Update the ARCHITECTURE.md document to reflect the new changes.
</deliverables>