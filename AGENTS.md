# FlashCard Application
The FlashCard application is a simple CLI application that allows users to create, view, and study flashcards.

## Coding principles
The application follows SOLID principles. When it comes to developing new features, the following asepcts should be taken into account:
* correctness, i.e. the new features should do what they are supposed to do
* readability, i.e. the new features should be easy to understand by a new developer
* maintainability, i.e. the new features should be easy to modify and extend
* performance, i.e., the new features should be efficient and not introduce performance regressions

In addition, it is important that the application maintains high levels of standard in terms of security and reliability.

## Development Tools
The core application is built in Python and leverage the following libraries:
* `typer` for CLI
* `json` for data loading and saving
* other basic built-in Python libraries (e.g., os, pathlib, etc.)

For code quality, the following tools are used:
- `pytest` for testing
- `black` for code formatting
- `isort` for import organization
- `flake8` for linting
- `mypy` for type checking

## AI Assistant Guidelines

### Code Generation
- Provide clean, well-documented code that follows Python best practices
- Include type hints and proper error handling
- Suggest appropriate design patterns when beneficial
- Ask clarifying questions if requirements are unclear

### Code Review
- Point out potential security vulnerabilities
- Suggest improvements for readability and maintainability
- Identify edge cases that need testing
- Recommend refactoring opportunities

### Educational Support
- Explain complex concepts and design decisions
- Provide examples of best practices
- Suggest learning resources when appropriate
- Help debug issues and understand error messages

## Project Structure

The project follows this organization:
- `main.py` - Application entry point
- `utils/` - Reusable utility modules
- `tests/` - Comprehensive unit test suite
- `docs/` - Project documentation and templates
- `ai_guidance/` - AI collaboration best practices
- `.claude/` - Claude-specific configuration

## Common Commands

Students can use these commands during development:
- `python main.py` - Run the application
- `pytest` - Run all tests
- `pytest --cov=. --cov-report=html` - Run tests with coverage
- `black .` - Format code
- `isort .` - Organize imports
- `flake8 .` - Check linting
- `mypy .` - Type checking