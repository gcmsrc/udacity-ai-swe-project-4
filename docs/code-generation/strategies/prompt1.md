<role>
Senior Python developer implementing planned architecture
</role>

<task>
Implement the three quiz strategies: Sequential, Random, and Adaptive.
</task>

<context>
You are implementing code that was specified in @docs/ARCHITECTURE.md
</context>

<interface_specification>
A senior developer implemented a high-level interface for the quiz strategies in `utils/strategies/base.py`. Such implementation, however, is just a ABC class while you would need to develop three concrete strategies: Sequential, Random, but not Adaptive
</interface_specification>

<requirements>
<functionality>
- Implement the two quiz strategies: Sequential and Random.
</functionality>

<error_handling>
The strategies should be able to handle the following errors:
* The factory should raise a ValueError if the strategy is not supported.
</error_handling>

<code_quality>
- Comprehensive module and class docstrings
- Method docstrings with Args, Returns, Raises sections
- Full type hints on all signatures
</code_quality>
</requirements>

<testing>
Please update the test_strategies.py accordingly.
Remove the AdaptiveStrategy test cases.
</testing>

<constraints>
- Python standard library only
- Follow PEP 8 style guide
- No external dependencies
</constraints>

<deliverables>
Provide:
- The implementation of the Sequential and Random strategies
- The tests for the Sequential and Random strategies
- Provide a summary of the changes you did inside docs/code-generation/strategies/implementation_summary.md`
</deliverables>