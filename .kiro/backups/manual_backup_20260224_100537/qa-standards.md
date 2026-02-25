---
inclusion: fileMatch
patterns: ["tests/**", "**/*.test.*", "**/*.spec.*", "hiveforge-power/tests/**"]
priority: 2
description: "Testing standards and coverage requirements."
---

# QA Standards & Conventions

## Coverage Requirements
- **Minimum Overall Coverage:** 80%
- **Critical Paths:** 100% (workflow execution, file writing, backup/restore)
- **New Code:** Must not decrease overall coverage
- Run with: `pytest --cov=hiveforge --cov-report=term-missing`

## Testing Strategy
HiveForge uses a three-tier testing approach:

1. **Unit tests** — isolated component testing with all external dependencies mocked
2. **Integration tests** — workflow-level tests using real filesystem (temp directories)
3. **Regression tests** — snapshot tests for generated steering file content

LLM calls are always mocked in tests. No test should make real API calls.

## Test Types

### Unit Tests
- Test individual functions/methods in isolation
- Mock all LLM calls, filesystem operations where appropriate
- Fast execution (< 1s per test)
- Location: `tests/test_{module}.py`

### Integration Tests
- Test complete workflow execution (init, update, validate)
- Use `tmp_path` pytest fixture for real filesystem operations
- Verify file creation, content, and backup behavior
- Location: `tests/test_integration_*.py` or `tests/test_{workflow}_workflow.py`

### Regression Tests
- Snapshot-style tests for generated steering file content
- Catch unintended changes to template population logic
- Location: `tests/test_regression.py`

## Test Naming
- Pattern: `test_{what}_{condition}_{expected_outcome}`
- Examples:
  - `test_init_workflow_with_existing_files_creates_backup`
  - `test_template_populator_with_nested_knowledge_replaces_placeholders`
  - `test_llm_provider_when_unavailable_returns_inferred_markers`

## Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange
    config = SteeringConfig(project_root=tmp_path, analyze_code=False)
    
    # Act
    result = workflow.execute()
    
    # Assert
    assert result is True
    assert (tmp_path / ".kiro/steering/tech-stack.md").exists()
```

## Fixtures & Mocking Rules
- Use `pytest` fixtures for shared setup (not `setUp`/`tearDown`)
- Mock LLM provider with `unittest.mock.patch` or `pytest-mock`
- Use `tmp_path` fixture for all filesystem tests — never write to real project directories in tests
- Mock external APIs and network calls
- Do NOT mock the code under test
- Use realistic mock data that matches production shapes

## Edge Cases to Always Test
- Empty project directory (no source files)
- Existing steering files (backup + overwrite flow)
- LLM unavailable (fallback to `[INFERRED]` markers)
- Invalid/missing template files
- Malformed YAML frontmatter in steering files
- Very large codebases (token budget enforcement)
- User rejects draft in interactive mode

## CI Requirements
- All tests must pass before merging to `main`
- Coverage report generated on every PR
- No test may depend on external network access
- Tests must be deterministic (no random seeds, no time-dependent assertions without mocking)
