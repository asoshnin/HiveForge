---
generated_by: hiveforge v2.2.0
generated_at: 2026-02-20T00:40:53.030278+00:00
source_documents: 3
source_docs_path: _DEVELOPMENT
code_analysis: true
confidence:
  overall: 0.00
  level: low
---

> ⚠️ **LOW CONFIDENCE**: This file was generated with limited source material.
> Most content is inferred from code analysis. Please review and update with actual project information.

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
- Pattern: `test_{what}_{condition}_{expected_outcome}`

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