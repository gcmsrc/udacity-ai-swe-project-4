<role>
Senior Python developer following SOLID principles
</role>
<task>
Provide three alternative solutions to include the handling of the SessionRepository between GamePlanner and the underlying strategy.
</task>

<architecture_decisions>
GamePlanner is the context class responsible for selecting the list of cards to be presented to the user. It uses a strategy to order the cards.
Each session should be stored using the SessionRepository class.

The GamePlanner should be able to:
- Create a new session
- Store the session result
- Retrieve the missed cards for the last session
- Close the session

The key question is how to handle the Adaptive Strategy as this would require to extract the latest missed cards (for the same dataset) from the SessionRepository. This has a high risk of creating a tight coupling between the Strategy and the SessionRepository.

Please provide three alternative solutions to handle the SessionRepository between GamePlanner and the underlying strategy.
</architecture_decisions>

<deliverables>
Save the suggested alternatives in docs/planning/alternatives/session-repository-alternatives.md
</deliverables>