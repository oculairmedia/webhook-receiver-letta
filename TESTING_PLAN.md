# Testing Plan for Letta Webhook Receiver (LWBHK)

**Project**: Letta Webhook Receiver  
**Identifier**: LWBHK  
**Created**: 2025-11-21  
**Status**: Planning Phase  

---

## Executive Summary

This document outlines the comprehensive testing strategy for the Letta Webhook Receiver project. Currently, the project has **0% active test coverage** with all 53 existing tests archived during the 2025-11-20 cleanup. This plan establishes a roadmap to restore and enhance test coverage to ensure production stability and enable confident iteration.

---

## Current State Assessment

### Test Coverage Status
- **Active tests**: 0 (all archived)
- **Archived tests**: 53 files
  - 5 unit tests (`archive/old_tests/`)
  - 48 integration tests (`archive/tests/`)
- **Production code**: ~836 lines across 6 core modules
- **Test framework**: Not configured (pytest not in requirements)
- **Coverage measurement**: Not configured
- **CI/CD**: Not configured

### Risk Level: **HIGH**
Without active tests, the project is vulnerable to:
- Undetected regressions when making changes
- Breaking changes in production
- Difficult refactoring without confidence
- No quality gates for new contributions

---

## Testing Strategy

### Goals
1. **Immediate**: Restore critical unit tests (70% coverage on core modules)
2. **Short-term**: Add integration tests and CI/CD (80% overall coverage)
3. **Long-term**: Achieve comprehensive test suite with performance and contract testing (85%+ coverage)

### Test Pyramid Approach
```
        /\
       /  \      E2E Tests (10%)
      /____\     - Full webhook flow
     /      \    - Production scenarios
    /________\   Integration Tests (30%)
   /          \  - API connectivity
  /____________\ - External service mocking
 /              \ Unit Tests (60%)
/________________\ - Pure functions
                   - Business logic
```

---

## Phase 1: Foundation (Week 1-2)

### Objective
Restore basic testing infrastructure and critical unit tests.

### Tasks

#### 1.1 Setup Test Infrastructure
- [ ] Add pytest and coverage tools to `requirements.txt`
  ```
  pytest==7.4.3
  pytest-cov==4.1.0
  pytest-mock==3.12.0
  responses==0.24.1
  ```
- [ ] Create `pytest.ini` configuration
- [ ] Create `.coveragerc` for coverage configuration
- [ ] Create `tests/` directory structure
- [ ] Add `conftest.py` with common fixtures

#### 1.2 Restore Core Unit Tests
Restore and update these critical tests from archive:

- [ ] **`tests/test_app.py`** - Flask webhook endpoints
  - Health check endpoint
  - Webhook receipt and parsing
  - Agent tracking logic
  - Error handling

- [ ] **`tests/test_memory_manager.py`** - Memory block operations
  - `create_memory_block()`
  - `update_memory_block()`
  - `attach_block_to_agent()`
  - `find_memory_block()`

- [ ] **`tests/test_context_utils.py`** - Context building
  - `_build_cumulative_context()`
  - `_truncate_oldest_entries()`
  - `_is_content_similar_with_query_awareness()`
  - Deduplication logic

- [ ] **`tests/test_config.py`** - Configuration validation
  - Environment variable loading
  - Default values
  - API URL construction

- [ ] **`tests/test_block_finders.py`** - Block finding logic
  - Finding blocks by label
  - Attachment status detection

#### 1.3 Create Missing Unit Tests
- [ ] **`tests/test_tool_manager.py`** - Tool attachment (NEW)
  - `find_attach_tools()` function
  - Keep-tools wildcard logic
  - Error handling for tool service unavailability

#### 1.4 Establish Coverage Baseline
- [ ] Run coverage report
- [ ] Document current coverage percentage
- [ ] Identify untested code paths
- [ ] Create coverage improvement roadmap

**Target**: 70% coverage on core modules by end of Phase 1

---

## Phase 2: Integration & CI/CD (Week 3-4)

### Objective
Add integration tests and automate testing in CI/CD pipeline.

### Tasks

#### 2.1 Integration Tests
Restore and enhance integration tests from archive:

- [ ] **Graphiti Integration** (`tests/integration/test_graphiti.py`)
  - API connectivity and health check
  - Node search functionality
  - Fact search functionality
  - Retry logic and timeout handling
  - Error responses

- [ ] **Letta API Integration** (`tests/integration/test_letta_api.py`)
  - Memory block CRUD operations
  - Agent listing and retrieval
  - Authentication headers
  - Error handling

- [ ] **Tool Service Integration** (`tests/integration/test_tool_service.py`)
  - Tool discovery API
  - Tool attachment API
  - Keep-tools preservation
  - Service unavailability handling

- [ ] **Matrix Notifications** (`tests/integration/test_matrix_client.py`)
  - New agent notification
  - Timeout handling
  - Background thread execution

#### 2.2 End-to-End Tests
- [ ] **Complete Webhook Flow** (`tests/e2e/test_webhook_flow.py`)
  - Full request processing pipeline
  - Graphiti → Memory → Tool attachment
  - Response validation
  - Performance benchmarks (< 3s target)

#### 2.3 CI/CD Pipeline
- [ ] Create GitHub Actions workflow (or GitLab CI)
  ```yaml
  # .github/workflows/test.yml
  name: Tests
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-python@v4
          with:
            python-version: '3.11'
        - run: pip install -r requirements.txt
        - run: pytest --cov=webhook_server --cov-report=term-missing
        - run: pytest --cov=webhook_server --cov-report=xml
        - uses: codecov/codecov-action@v3
  ```
- [ ] Configure branch protection rules
- [ ] Require tests to pass before merge
- [ ] Add coverage reporting (Codecov or similar)

#### 2.4 Test Documentation
- [ ] Document how to run tests locally
- [ ] Add testing section to README.md
- [ ] Create CONTRIBUTING.md with testing guidelines

**Target**: 80% overall coverage with automated CI/CD by end of Phase 2

---

## Phase 3: Comprehensive Coverage (Week 5-6)

### Objective
Achieve comprehensive test coverage with edge cases and performance testing.

### Tasks

#### 3.1 Edge Case Testing
- [ ] **Webhook Payload Variations**
  - Empty payloads
  - Malformed JSON
  - Missing required fields
  - List-format prompts vs string prompts
  - Different event types (message_sent, stream_started)

- [ ] **Context Truncation Edge Cases**
  - Single entry exceeding 4800 chars
  - Many small entries
  - Duplicate detection with minor variations
  - Timestamp parsing edge cases

- [ ] **Concurrent Operations**
  - Multiple webhooks for same agent
  - Race conditions in agent tracking
  - Thread safety verification

#### 3.2 Error Handling Tests
- [ ] Graphiti API failures (timeout, 503, 500)
- [ ] Letta API authentication failures
- [ ] Tool service unavailability
- [ ] Matrix client notification failures
- [ ] Network errors and retries

#### 3.3 Performance Testing
- [ ] **Load Testing** (`tests/performance/test_load.py`)
  - Concurrent webhook requests
  - Response time under load
  - Memory usage profiling

- [ ] **Benchmark Tests** (`tests/performance/test_benchmarks.py`)
  - Context generation speed
  - Memory block operations speed
  - Tool attachment speed
  - Full pipeline latency

#### 3.4 Contract Testing
- [ ] **External API Contracts** (`tests/contracts/`)
  - Graphiti API response schema validation
  - Letta API response schema validation
  - Tool service API response schema validation
  - Detect breaking changes in external services

**Target**: 85%+ coverage with performance benchmarks by end of Phase 3

---

## Phase 4: Advanced Testing (Ongoing)

### Objective
Maintain test quality and explore advanced testing techniques.

### Tasks

#### 4.1 Mutation Testing
- [ ] Install `mutmut` or `cosmic-ray`
- [ ] Run mutation testing to verify test quality
- [ ] Improve tests that don't catch mutations
- [ ] Target: 80%+ mutation score

#### 4.2 Property-Based Testing
- [ ] Install `hypothesis`
- [ ] Add property-based tests for:
  - Context truncation logic
  - Deduplication algorithms
  - Timestamp parsing

#### 4.3 Security Testing
- [ ] Test authentication header handling
- [ ] Test input sanitization
- [ ] Test for injection vulnerabilities
- [ ] Test resource limits (DoS prevention)

#### 4.4 Regression Test Suite
- [ ] Create regression test suite from production bugs
- [ ] Add tests for each bug fix
- [ ] Maintain regression suite as living documentation

---

## Test Organization

### Directory Structure
```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests (60%)
│   ├── test_app.py
│   ├── test_memory_manager.py
│   ├── test_context_utils.py
│   ├── test_config.py
│   ├── test_block_finders.py
│   └── test_tool_manager.py
├── integration/             # Integration tests (30%)
│   ├── test_graphiti.py
│   ├── test_letta_api.py
│   ├── test_tool_service.py
│   └── test_matrix_client.py
├── e2e/                     # End-to-end tests (10%)
│   └── test_webhook_flow.py
├── performance/             # Performance tests
│   ├── test_load.py
│   └── test_benchmarks.py
└── contracts/               # Contract tests
    ├── test_graphiti_contract.py
    ├── test_letta_contract.py
    └── test_tool_service_contract.py
```

### Naming Conventions
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<function_name>_<scenario>`
- Fixtures: Descriptive names (e.g., `mock_graphiti_response`)

---

## Test Quality Standards

### Code Coverage
- **Minimum**: 70% overall coverage
- **Target**: 80% overall coverage
- **Stretch**: 85%+ overall coverage
- **Critical modules**: 90%+ coverage (app.py, memory_manager.py, context_utils.py)

### Test Characteristics
- **Fast**: Unit tests < 100ms, integration tests < 1s
- **Isolated**: No dependencies between tests
- **Repeatable**: Same results every run
- **Self-documenting**: Clear test names and docstrings
- **Maintainable**: DRY principle, use fixtures

### Documentation
- Every test module has a module docstring
- Complex tests have inline comments
- Edge cases are explicitly documented
- Test data is realistic and representative

---

## Monitoring & Metrics

### Key Metrics to Track
1. **Coverage percentage** (overall and per-module)
2. **Test execution time** (total and per-test)
3. **Test failure rate** (flaky test detection)
4. **Mutation score** (test quality)
5. **CI/CD pipeline success rate**

### Reporting
- Coverage reports generated on every CI run
- Weekly coverage trend analysis
- Monthly test quality review
- Quarterly testing strategy review

---

## Dependencies & Tools

### Required Dependencies
```python
# Testing framework
pytest==7.4.3
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-asyncio==0.21.1

# HTTP mocking
responses==0.24.1
requests-mock==1.11.0

# Performance testing
pytest-benchmark==4.0.0

# Property-based testing
hypothesis==6.92.0

# Mutation testing
mutmut==2.4.4

# Contract testing
pact-python==2.0.0
```

### Development Tools
- **Coverage visualization**: coverage.py + HTML reports
- **CI/CD**: GitHub Actions or GitLab CI
- **Coverage tracking**: Codecov or Coveralls
- **Test reporting**: pytest-html for HTML reports

---

## Success Criteria

### Phase 1 Complete
- ✅ 70% coverage on core modules
- ✅ All critical unit tests passing
- ✅ Coverage baseline documented

### Phase 2 Complete
- ✅ 80% overall coverage
- ✅ Integration tests for all external services
- ✅ CI/CD pipeline operational
- ✅ Tests run on every PR

### Phase 3 Complete
- ✅ 85%+ overall coverage
- ✅ Edge cases covered
- ✅ Performance benchmarks established
- ✅ Contract tests for external APIs

### Phase 4 Complete
- ✅ 80%+ mutation score
- ✅ Property-based tests for critical logic
- ✅ Security testing implemented
- ✅ Regression suite maintained

---

## Risks & Mitigations

### Risk: External Service Dependencies
**Impact**: Integration tests may be flaky or slow  
**Mitigation**: 
- Use mocking for unit tests
- Use Docker containers for integration tests
- Implement retry logic in tests
- Separate fast unit tests from slower integration tests

### Risk: Test Maintenance Burden
**Impact**: Tests become outdated or brittle  
**Mitigation**:
- Follow DRY principle with fixtures
- Regular refactoring of test code
- Clear documentation and ownership
- Automated test quality checks (mutation testing)

### Risk: Slow Test Execution
**Impact**: Developers skip running tests locally  
**Mitigation**:
- Optimize test performance (< 30s for unit tests)
- Parallelize test execution
- Use test markers to run subsets
- Cache dependencies in CI/CD

---

## Next Steps

1. **Review and approve** this testing plan
2. **Allocate resources** for Phase 1 implementation
3. **Set up project tracking** for testing tasks (add to Kanban board)
4. **Schedule kickoff** for Phase 1 (target: this week)
5. **Assign ownership** for each testing phase

---

## Appendix

### Archived Test Inventory

**Unit Tests** (archive/old_tests/):
- test_app.py (42 lines)
- test_block_finders.py
- test_config.py
- test_context_utils.py
- test_memory_manager.py

**Integration Tests** (archive/tests/):
- Graphiti: 8 test files
- Webhook Flow: 12 test files
- Memory Operations: 6 test files
- ArXiv Integration: 5 test files
- GDELT Integration: 5 test files
- Tool Attachment: 3 test files
- Production Verification: 9 test files

### References
- [pytest documentation](https://docs.pytest.org/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
