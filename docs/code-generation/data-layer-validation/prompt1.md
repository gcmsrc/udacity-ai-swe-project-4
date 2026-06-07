<role>
Senior Python developer implementing planned architecture
</role>

<task>
Implement CardsDataLoader class following the interface specification
</task>

<context>
You are implementing code that was specified in @docs/ARCHITECTURE.md
<>
</context>

<interface_specification>
A senior developer implemented a high-level interface for loading cards in `utils/data_loader/data_loader.py`. Such implementation, however, is just a function while you would need to develop a class that implements the interface. The class is called `CardsDataLoader` and it must have a `load` method.
</interface_specification>

<requirements>
<functionality>
- Implement CardsDataLoader class following the interface specification
- The class must be able to load cards from a JSON file
- The class should be able to handle two different formats of the JSON file: array of objects with a "front" and "back" fields, or an object with a "cards" field that is an array of objects with a "front" and "back" fields.
</functionality>

<error_handling>
The class should be able to handle the following errors:
- FileNotFoundError: if the file does not exist
- ValueError: if the file is not a valid JSON file
- ValueError: if the file does not contain the "front" and "back" fields
- ValueError: if the file does not contain the "cards" field
- ValueError: if the file does not contain the "front" and "back" fields

In all cases, the error should be handled gracefully and the user should be informed about the error in a way that is easy to understand.
</error_handling>

<security>
The class should handle file traversal attacks and only accepts absolute paths to the json files.
</security>

<code_quality>
- Comprehensive module and class docstrings
- Method docstrings with Args, Returns, Raises sections
- Full type hints on all signatures
</code_quality>
</requirements>

<testing>
Please update the test_data_loader.py accordingly
</testing>

<constraints>
- Python standard library only
- Follow PEP 8 style guide
- No external dependencies
</constraints>

<deliverables>
Provide:
- The implementation of the CardsDataLoader class
- The tests for the CardsDataLoader class
- Provide a summary of the changes you did inside docs/code-generation/data-layer-validation/implementation_summary.md`
</deliverables>