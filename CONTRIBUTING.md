# Contributing to Letta Webhook Receiver

Thank you for your interest in contributing to the Letta Webhook Receiver project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Testing Guidelines](#testing-guidelines)
- [Code Standards](#code-standards)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/webhook-receiver-letta.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Docker (optional, for containerized development)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables (copy `.env.example` to `.env` if available):
```bash
export LETTA_BASE_URL="http://localhost:8283"
export LETTA_PASSWORD="your-password"
export GRAPHITI_URL="http://localhost:8003"
```

3. Run the development server:
```bash
python run_server.py
```

## Testing Guidelines

### Running Tests

We use `pytest` for all tests. Tests are organized into categories:

#### Run All Tests
```bash
pytest
```

#### Run Unit Tests Only
```bash
pytest tests/unit/ -v
```

#### Run Integration Tests
```bash
pytest tests/integration/ -v
```

#### Run E2E Tests
```bash
pytest tests/e2e/ -v
```

#### Run with Coverage
```bash
pytest --cov=webhook_server --cov=tool_manager --cov=letta_tool_utils --cov-report=html
```

View coverage report in `htmlcov/index.html`.

### Writing Tests

#### Test Organization

- **Unit tests** (`tests/unit/`): Test individual functions and classes in isolation
- **Integration tests** (`tests/integration/`): Test interactions with external services (mocked)
- **E2E tests** (`tests/e2e/`): Test complete workflows from end to end

#### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<function_name>_<scenario>`

Example:
```python
class TestMemoryManager:
    def test_create_memory_block_success(self):
        """Test successful creation of a memory block."""
        pass

    def test_create_memory_block_with_invalid_data(self):
        """Test that invalid data raises appropriate error."""
        pass
```

#### Test Quality Standards

1. **Isolation**: Tests should not depend on each other
2. **Clarity**: Use descriptive names and docstrings
3. **Coverage**: Aim for >80% code coverage
4. **Mocking**: Use mocks for external dependencies
5. **Assertions**: Make specific, meaningful assertions

#### Example Test

```python
def test_query_graphiti_api_success(self):
    """Test successful Graphiti API query."""
    with patch('webhook_server.app.requests.Session') as mock_session:
        mock_response = Mock()
        mock_response.json.return_value = {
            "nodes": [{"name": "Test", "summary": "Test node"}]
        }
        mock_session.return_value.post.return_value = mock_response

        result = query_graphiti_api("test query")

        assert result['success'] is True
        assert 'Test' in result['context']
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit
def test_simple_function():
    pass

@pytest.mark.integration
def test_api_integration():
    pass

@pytest.mark.slow
def test_expensive_operation():
    pass
```

Run specific markers:
```bash
pytest -m unit          # Run only unit tests
pytest -m "not slow"    # Skip slow tests
```

### Coverage Requirements

- **Minimum**: 70% overall coverage
- **Target**: 80% overall coverage
- **Critical modules**: 90%+ coverage (app.py, memory_manager.py, context_utils.py)

Pull requests that decrease coverage will be flagged for review.

## Code Standards

### Style Guide

We follow PEP 8 with some modifications:

- Maximum line length: 127 characters
- Use type hints for function signatures
- Write descriptive docstrings for all public functions

### Code Formatting

Use `black` for code formatting:
```bash
black webhook_server/ tool_manager.py letta_tool_utils.py
```

### Import Sorting

Use `isort` for import sorting:
```bash
isort webhook_server/ tool_manager.py letta_tool_utils.py
```

### Linting

Use `flake8` for linting:
```bash
flake8 webhook_server/ tool_manager.py letta_tool_utils.py --max-line-length=127
```

### Type Checking

Use type hints where possible:
```python
def process_webhook(payload: dict) -> dict:
    """Process webhook payload and return result."""
    agent_id: str = payload.get("agent_id", "")
    return {"status": "success", "agent_id": agent_id}
```

### Documentation

- All public functions must have docstrings
- Use Google-style docstrings:

```python
def create_memory_block(block_data: dict, agent_id: Optional[str] = None) -> dict:
    """
    Create a memory block in Letta.

    Args:
        block_data: Dictionary containing block label and value
        agent_id: Optional agent ID to attach the block to

    Returns:
        Dictionary containing the created block information

    Raises:
        requests.exceptions.HTTPError: If the API request fails
    """
    pass
```

## Pull Request Process

### Before Submitting

1. **Run all tests**: `pytest`
2. **Check coverage**: Coverage should not decrease
3. **Format code**: `black .` and `isort .`
4. **Lint code**: `flake8 .`
5. **Update documentation**: If adding features, update README.md
6. **Add tests**: All new code must have tests

### PR Checklist

- [ ] Tests pass locally
- [ ] Code coverage maintained or improved
- [ ] Code formatted with black
- [ ] Imports sorted with isort
- [ ] No linting errors
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages are clear and descriptive

### PR Title Format

Use conventional commit format:
- `feat: Add new feature`
- `fix: Fix bug in memory manager`
- `docs: Update testing documentation`
- `test: Add tests for context utils`
- `refactor: Simplify block finding logic`
- `chore: Update dependencies`

### Review Process

1. Submit PR with clear description
2. Address reviewer feedback
3. Ensure CI/CD checks pass
4. Obtain approval from maintainer
5. PR will be merged by maintainer

## Reporting Issues

### Bug Reports

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (Python version, OS, etc.)
- Relevant logs or error messages

### Feature Requests

Include:
- Description of the feature
- Use case / motivation
- Proposed implementation (optional)
- Alternative solutions considered

### Security Issues

**Do not** open public issues for security vulnerabilities. Instead, email the maintainers directly.

## Development Workflow

### Feature Development

1. Create feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature
   ```

2. Make changes and add tests:
   ```bash
   # Write code
   # Write tests
   pytest
   ```

3. Commit with descriptive messages:
   ```bash
   git commit -m "feat: Add context deduplication logic"
   ```

4. Push and create PR:
   ```bash
   git push origin feature/your-feature
   ```

### Bug Fixes

1. Create bugfix branch:
   ```bash
   git checkout -b fix/bug-description
   ```

2. Fix bug and add regression test:
   ```bash
   # Fix the bug
   # Add test that would have caught the bug
   pytest
   ```

3. Commit and push:
   ```bash
   git commit -m "fix: Prevent duplicate memory block creation"
   git push origin fix/bug-description
   ```

## Questions?

If you have questions, please:
1. Check existing issues and discussions
2. Review the documentation
3. Open a new issue with the "question" label

Thank you for contributing!
