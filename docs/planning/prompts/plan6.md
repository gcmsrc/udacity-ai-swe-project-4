<role>
Senior Python developer following SOLID principles
</role>
<task>
Provide three alternative solutions to the UI module.
</task>

<architecture_decisions>
The UI module is passed to the QuizEngine and it is responsible to handle the terminal I/O.
Ultimately it should:
* Be called to present the front card to the user
* Collect the users's answer and pass it back to the QuizEngine
Then it can be called to show the feedback to the user based on a specific reporting strategy (to be implemented later, for now we can assume to return just a proportion of correct answers)
</architecture_decisions>

<deliverables>
Save the suggested alternatives in docs/planning/alternatives/ui-alternatives.md
</deliverables>