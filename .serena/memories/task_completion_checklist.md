# Task Completion Checklist

## When a Task is Completed

### 1. Code Quality
- [ ] Ensure code follows snake_case naming conventions
- [ ] Add type hints to function signatures
- [ ] Add docstrings to public functions
- [ ] Use appropriate logging with categorized prefixes
- [ ] Handle errors with try-except blocks

### 2. Testing
- [ ] Test the changes locally if modifying core functionality
- [ ] Run relevant test files (test_*.py) to verify changes
- [ ] For webhook changes, test with `test_complete_webhook_flow.py`
- [ ] For retrieval changes, run simulation suite to verify quality

### 3. Integration Testing
- [ ] Test Graphiti API integration if context retrieval modified
- [ ] Test Letta API integration if memory management modified
- [ ] Test BigQuery integration if GDELT functionality modified
- [ ] Verify health endpoint still responds: `curl http://localhost:5005/health`

### 4. Documentation
- [ ] Update inline comments for complex logic
- [ ] Add CRITICAL FIX or Defensive fix markers for important changes
- [ ] Update README.md if adding new features or changing configuration
- [ ] Update .env.example if adding new environment variables

### 5. Docker/Deployment
- [ ] Verify Docker build succeeds: `docker build -t test .`
- [ ] Test docker-compose configuration if modified
- [ ] Update Dockerfile if adding new dependencies
- [ ] Update requirements.txt or requirements-light.txt for new packages

### 6. Version Control
- [ ] Review git diff to ensure only intended changes included
- [ ] Write clear commit message describing the change
- [ ] Ensure no sensitive credentials committed (check .gitignore)

## Specific Component Checks

### Memory Management Changes
- [ ] Verify cumulative context building works correctly
- [ ] Test truncation logic doesn't lose critical content
- [ ] Ensure deduplication prevents redundant context

### Integration Changes
- [ ] Test trigger detection logic (ArXiv, GDELT)
- [ ] Verify API calls succeed with proper error handling
- [ ] Check that integration results are properly formatted

### Configuration Changes
- [ ] Update both local and production compose files
- [ ] Verify environment variable defaults are reasonable
- [ ] Document new configuration options in README

## No Formal Linting/Formatting
This project does not use formal linting tools (black, flake8, pylint) or automated formatters. Manual code review for consistency is recommended.
