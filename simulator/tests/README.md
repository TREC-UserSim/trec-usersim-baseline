# Test Suites

This directory contains test suites for the user simulator components using pytest.

## Test Files

- **test_persona.py** - Tests for persona management (`PersonaDefinition`, `PersonaRegistry`)
- **test_api_client.py** - Tests for API client and data models (`Source`, `Goal`, `Utterance`, `APIResponse`, `SimulatorAPIClient`)
- **test_response_strategies.py** - Tests for response generation strategies (`RandomStrategy`, `LLMStrategy`)
- **test_user_simulator.py** - Tests for the main user simulator (`ConversationState`, `UserSimulator`)

## Installation

Install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run tests with verbose output
```bash
pytest -v
```

### Run a specific test file
```bash
pytest tests/test_persona.py
```

### Run a specific test class
```bash
pytest tests/test_persona.py::TestPersonaDefinition
```

### Run a specific test function
```bash
pytest tests/test_persona.py::TestPersonaDefinition::test_persona_creation
```

## Coverage Reports

Generate coverage reports to see how much of the codebase is tested:

### Terminal coverage report
```bash
pytest --cov=simulator --cov-report=term-missing
```

### HTML coverage report
```bash
pytest --cov=simulator --cov-report=html
```
The HTML report will be generated in `htmlcov/index.html`

## Test Organization

### Unit Tests
All tests are unit tests that:
- Test individual functions and methods in isolation
- Use mocks to avoid external dependencies (API calls, LLM calls)
- Cover both happy paths and error cases
- Test edge cases and boundary conditions

### Test Structure
Each test file follows this structure:
1. **Imports** - Import the module under test and dependencies
2. **Test Classes** - Organized by class being tested (e.g., `TestPersonaDefinition`)
3. **Test Methods** - Named `test_*` following pytest conventions

### Mocking
Tests use `unittest.mock` to mock:
- API calls (SimulatorAPIClient)
- LLM completions (LiteLLM)
- External dependencies

This ensures tests are fast and don't depend on external services.

## Key Test Coverage

### Persona Tests (test_persona.py)
- Persona creation and properties
- Persona name generation logic
- Persona serialization (to_dict/from_dict)
- Persona registry file loading (JSON)
- Error handling (missing files, invalid JSON)
- Registry operations (add, get, list personas)

### API Client Tests (test_api_client.py)
- Data model creation (Source, Goal, Utterance, APIResponse)
- Serialization/deserialization
- API client initialization and headers
- API request mocking (start_run, continue_run)
- Error handling
- Conversation history retrieval

### Response Strategies Tests (test_response_strategies.py)
- Strategy base class abstraction
- Random strategy response generation
- Random strategy response pool validation
- LLM strategy initialization
- LLM response generation with mocked completion
- System prompt construction (includes persona and goal)
- Conversation history handling
- Error fallback behavior
- LLM kwargs passing

### User Simulator Tests (test_user_simulator.py)
- Conversation state creation and transitions
- Message history management
- Conversation active/inactive state
- User simulator initialization
- Run initiation
- Conversation initiation
- Response generation
- Error handling (concurrent conversations)
- Complete conversation flow

## Adding New Tests

When adding new tests:

1. **Create test file** - Place in `tests/` directory with `test_*.py` naming
2. **Import modules** - Import the module under test and dependencies
3. **Create test class** - Class name should be `Test*` (e.g., `TestMyFeature`)
4. **Write test methods** - Method names should start with `test_`
5. **Use descriptive names** - Test name should describe what it tests
6. **Follow arrange-act-assert** - Setup, execute, verify pattern

### Example Test Template
```python
def test_feature_behavior(self):
    """Test description in docstring."""
    # Arrange - set up test data
    obj = MyClass(param=value)
    
    # Act - perform the action
    result = obj.method()
    
    # Assert - verify the result
    assert result == expected
```

## Troubleshooting

### Import Errors
If you get import errors, ensure the simulator package is in your Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/simulator"
```

### Mock Issues
If mocks aren't working, check that:
- You're using the correct patch path (`module.Class` not just `Class`)
- Mock is imported: `from unittest.mock import Mock, patch`
- Mock is applied before the test runs (using `@patch` decorator)

### Test Discovery Issues
If pytest can't find tests:
- Ensure files are named `test_*.py`
- Ensure test classes are named `Test*`
- Ensure test methods are named `test_*`
- Check `pytest.ini` for configuration