<role>
Senior Python developer following SOLID principles
</role>
<task>
Update the architecture document to integrate a session-based handling to keep track of the users' progress
</task>

<architecture_decisions>
It would be important for a user to keep track of her progress over time. To do so, we need to integrate a session-based handling to keep track of the users' progress.

The session-based handling should be able to:
- Assing a unique identifier to each session
- Store the user results (correct/incorrect) for each flashcard for a given dataset in a persisted database

This approach would be particularly useful for the Adaptive strategy, where the user should be able to see (more often)the cards that she got wrong in a prior session.

The database connection should be handled by a singleton class that will be used to connect to the database.
The singleton class should be able to:
- Connect to the database
- Disconnect from the database
- Execute queries
- Return the results
</architecture_decisions>

<deliverables>
Update the ARCHITECTURE.md document to reflect the new changes.
</deliverables>