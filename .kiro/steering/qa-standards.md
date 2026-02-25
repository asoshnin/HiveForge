---
inclusion: fileMatch
patterns: ["tests/**", "conftest.py", "pytest.ini", ".github/workflows/**"]
priority: 2
description: "Testing strategy, coverage requirements, CI/CD. Loaded when working on tests or CI/CD."
---

# QA & Testing Standards

## Testing Strategy

### Test Pyramid
```
        /\
       /  \      E2E Tests (5%)
      /____\     Integration Tests (15%)
     /      \    Unit Tests (80%)
    /________\
```

### Test Types

#### Unit Tests (80% of tests)
- **Purpose:** Test individual functions and classes in isolation
- **Location:** `tests/test_{module}.py`
- **Naming:** `test_{function_name}_{scenario}`
- **Mocking:** Mock external dependencies (file system, LLM API, network)
- **Speed:** <1 second per test

**Examples:**
- `test_validate_project_name_valid()`
- `test_validate_project_name_invalid_spaces()`
- `test_code_analyzer_detect_python()`

#### Integration Tests (15% of tests)
- **Purpose:** Test component interactions
- **Location:** `tests/test_{workflow}_integration.py`
- **Naming:** `test_{workflow}_{scenario}_integration`
- **Mocking:** Mock only external services (LLM API)
- **Speed:** <5 seconds per test

**Examples:**
- `test_init_workflow_with_artifacts_integration()`
- `test_update_workflow_preserves_customizations_integration()`

#### End-to-End Tests (5% of tests)
- **Purpose:** Test complete workflows from CLI to file output
- **Location:** `tests/test_cli_integration.py`
- **Naming:** `test_e2e_{scenario}`
- **Mocking:** Minimal (only LLM API for cost control)
- **Speed:** <10 seconds per test

**Examples:**
- `test_e2e_init_creates_all_files()`
- `test_e2e_update_with_conflicts()`

## Coverage Requirements

### Minimum Coverage
- **Overall:** 80%
- **Critical Modules:** 90% (workflows, validators, parsers)
- **Utility Modules:** 70% (utils, templates)

### Coverage Exclusions
- Test files themselves
- `__init__.py` files
- Defensive error paths (unexpected exceptions)
- Deprecated code marked for removal

### Coverage Reporting
```bash
# Generate coverage report
pytest tests/ --cov=src/hiveforge --cov-report=term-missing

# Generate HTML report
pytest tests/ --cov=src/hiveforge --cov-report=html

# Fail if coverage below threshold
pytest tests/ --cov=src/hiveforge --cov-fail-under=80
```

## Test Organization

### Directory Structure
```
tests/
├── conftest.py                    # Shared fixtures
├── test_cli.py                    # CLI tests
├── test_validators.py             # Validator tests
├── test_generator.py              # Generator tests
├── test_steering_cli.py           # Steering CLI tests
├── test_init_workflow.py          # Init workflow tests
├── test_update_workflow.py        # Update workflow tests
├── test_validate_workflow.py      # Validate workflow tests
├── test_code_analyzer.py          # Code analyzer tests
├── test_*_parser.py               # Parser tests
├── test_*_analyzer.py             # Analyzer tests
├── test_cli_integration.py        # Integration tests
└── fixtures/                      # Test data
    ├── sample_project/
    ├── sample_artifacts/
    └── expected_outputs/
```

### Fixture Organization
```python
# conftest.py
@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory."""
    return tmp_path / "test-project"

@pytest.fixture
def sample_artifacts(tmp_path):
    """Create sample artifacts for testing."""
    artifacts_dir = tmp_path / ".kiro" / "onboarding"
    artifacts_dir.mkdir(parents=True)
    # Create sample files
    return artifacts_dir

@pytest.fixture
def mock_llm_response():
    """Mock LLM API response."""
    return {"answer": "Python 3.11", "confidence": 0.9}
```

## Test Naming Conventions

### Pattern
```
test_{function_name}_{scenario}_{expected_result}
```

### Examples
- `test_validate_project_name_valid_returns_name()`
- `test_validate_project_name_invalid_raises_error()`
- `test_init_workflow_no_artifacts_asks_questions()`
- `test_update_workflow_with_conflicts_shows_diff()`

## Assertion Best Practices

### Use Specific Assertions
```python
# Good
assert result == "my-project"
assert len(files) == 8
assert "tech-stack.md" in files

# Bad
assert result  # Too vague
assert files   # Doesn't check content
```

### Use pytest Helpers
```python
# Check exceptions
with pytest.raises(ValueError, match="Invalid project name"):
    validate_project_name("My Project")

# Check warnings
with pytest.warns(UserWarning):
    parse_corrupted_file(path)

# Approximate equality
assert result == pytest.approx(0.85, abs=0.01)
```

## Mocking Strategy

### Mock External Dependencies
```python
# Mock file system
@patch("pathlib.Path.exists")
def test_file_not_found(mock_exists):
    mock_exists.return_value = False
    # Test code

# Mock LLM API
@patch("openai.ChatCompletion.create")
def test_llm_call(mock_create):
    mock_create.return_value = {"choices": [{"message": {"content": "Python"}}]}
    # Test code

# Mock environment variables
@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
def test_api_key():
    # Test code
```

### Don't Mock Internal Logic
```python
# Bad - mocking internal function
@patch("hiveforge.steering.gap_analysis.analyze_gaps")
def test_init_workflow(mock_analyze):
    # This doesn't test the actual logic

# Good - mock only external dependencies
@patch("openai.ChatCompletion.create")
def test_init_workflow(mock_llm):
    # This tests the actual workflow logic
```

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      
      - name: Run tests
        run: poetry run pytest tests/ -v --cov=src/hiveforge --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: poetry run pytest tests/ --cov-fail-under=80
        language: system
        pass_filenames: false
        always_run: true
```

## Performance Testing

### Benchmark Tests
```python
import time

def test_init_workflow_performance(benchmark):
    """Ensure init workflow completes in <30 seconds."""
    start = time.time()
    result = init_workflow.execute()
    duration = time.time() - start
    
    assert duration < 30, f"Init took {duration}s (expected <30s)"
    assert result.success
```

### Load Testing
```python
def test_code_analyzer_large_codebase():
    """Test code analyzer with 10k files."""
    # Create 10k dummy files
    files = create_dummy_files(10000)
    
    start = time.time()
    result = code_analyzer.analyze(files)
    duration = time.time() - start
    
    assert duration < 60, f"Analysis took {duration}s (expected <60s)"
    assert result.files_analyzed <= 1000  # Sampling kicks in
```

## Test Data Management

### Fixtures Location
- **Small Data:** Inline in test files
- **Medium Data:** `tests/fixtures/` directory
- **Large Data:** Generate dynamically in tests

### Sample Artifacts
```
tests/fixtures/
├── sample_project/
│   ├── src/
│   ├── tests/
│   └── README.md
├── sample_artifacts/
│   ├── project-spec.md
│   ├── architecture.pdf
│   └── requirements.png
└── expected_outputs/
    ├── tech-stack.md
    └── architecture.md
```

## Debugging Tests

### Run Specific Test
```bash
# Run single test
pytest tests/test_cli.py::test_validate_project_name_valid -v

# Run tests matching pattern
pytest tests/ -k "test_init" -v

# Run with debugger
pytest tests/ --pdb

# Run with print statements
pytest tests/ -s
```

### Test Isolation
- Each test should be independent
- Use fixtures for setup/teardown
- Clean up temporary files
- Reset mocks between tests

## Test Documentation

### Docstrings
```python
def test_init_workflow_with_artifacts():
    """
    Test init workflow with artifacts in staging folder.
    
    Given:
        - Staging folder contains project-spec.md
        - No existing steering files
    
    When:
        - User runs init workflow
    
    Then:
        - 8 steering files created
        - Content extracted from artifacts
        - Validation passes
    """
    # Test implementation
```

## Quality Gates

### Required Checks
- All tests pass
- Coverage ≥80%
- No linting errors (ruff)
- No type errors (mypy)
- No security issues (bandit)

### Optional Checks
- Performance benchmarks pass
- Documentation builds successfully
- Examples run without errors

## Current Test Status

### Statistics
- **Total Tests:** 863
- **Passing:** 835+ (97% pass rate)
- **Coverage:** 87%
- **Average Duration:** 45 seconds

### Test Distribution
- Unit Tests: 690 (80%)
- Integration Tests: 130 (15%)
- E2E Tests: 43 (5%)
