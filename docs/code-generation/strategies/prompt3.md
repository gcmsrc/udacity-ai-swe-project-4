<role>
Senior Python developer implementing planned architecture
</role>

<task>
Update the AdaptiveStrategy to update the weight of a previously missed card. If the card is now answered correctly, reset the weight to 1.0
</task>

<context>
You are udpating the logic in adapter.py
</context>

<requirements>
<functionality>
- Update the AdaptiveStrategy to update the weight of a previously missed card. If the card is now answered correctly, reset the weight to 1.0
</functionality>


<code_quality>
- Comprehensive module and class docstrings
- Method docstrings with Args, Returns, Raises sections
- Full type hints on all signatures
</code_quality>
</requirements>

<testing>
Add a test where a card is missed, then answered correctly. Check that weight is increased first, then reset to 1.0 when the user answrs correctly to the same card
</testing>

<constraints>
- Python standard library only
- Follow PEP 8 style guide
- No external dependencies
</constraints>

<deliverables>
Update the code in adaptive.py and the associated tests
</deliverables>