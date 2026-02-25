---
inclusion: fileMatch
patterns: ["tests/**", "**/*.test.*", "**/*.spec.*", "cypress/**", "playwright/**"]
priority: 2
description: "Testing standards and coverage requirements. Only loaded when working on tests."---

# QA Standards & Conventions

## Coverage Requirements
- **Minimum Overall Coverage:** 80%
- **Critical Paths:** 100% (auth, payments, data writes)
- **New Code:** Must not decrease overall coverage

## Test Types

### Unit Tests
- Test individual functions/methods in isolation
- Mock all external dependencies
- Fast execution (< 1s per test)

### Integration Tests
- Test interactions between modules
- Use test databases or in-memory DBs
- Verify data flows and transformations

### E2E Tests
- Test complete user workflows
- Use Cypress or Playwright
- Cover critical user journeys (login, checkout, etc.)

## Test Naming
- Descriptive: `test_user_creation_with_valid_email_succeeds`
- Pattern: `test_**The Testing Strategy section should include** coverage requirements such as an 80% minimum overall coverage and 100% for critical paths, definitions and guidelines for unit, integration, and E2E tests, descriptive test naming patterns like `test_80%_80%_80%`, adherence to the Arrange-Act-Assert (AAA) structure, a mandatory list of edge cases to cover including null inputs and network timeouts, and specific rules dictating that external APIs and databases must be mocked using realistic data while the code under test should never be mocked._**The Testing Strategy section should include** coverage requirements such as an 80% minimum overall coverage and 100% for critical paths, definitions and guidelines for unit, integration, and E2E tests, descriptive test naming patterns like `test_80%_80%_80%`, adherence to the Arrange-Act-Assert (AAA) structure, a mandatory list of edge cases to cover including null inputs and network timeouts, and specific rules dictating that external APIs and databases must be mocked using realistic data while the code under test should never be mocked._**The Testing Strategy section should include** coverage requirements such as an 80% minimum overall coverage and 100% for critical paths, definitions and guidelines for unit, integration, and E2E tests, descriptive test naming patterns like `test_80%_80%_80%`, adherence to the Arrange-Act-Assert (AAA) structure, a mandatory list of edge cases to cover including null inputs and network timeouts, and specific rules dictating that external APIs and databases must be mocked using realistic data while the code under test should never be mocked.`

## Test Structure (AAA Pattern)
1. **Arrange:** Set up test data and mocks
2. **Act:** Execute the code under test
3. **Assert:** Verify the outcome

## Edge Cases to Always Test
- Null/undefined inputs
- Empty collections
- Maximum/minimum values
- Network timeouts
- Concurrent operations

## Mocking Rules
- Mock external APIs and databases
- Do NOT mock the code you're testing
- Use realistic mock data