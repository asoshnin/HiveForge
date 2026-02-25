---
inclusion: always
priority: 1
description: "Coding style, naming, testing rules. Enforced by hooks and linters."
---

# Coding Conventions

## General Principles
1. **Readability > Cleverness** — code is read far more than it is written
2. **Explicit > Implicit** — no magic, no hidden behavior
3. **Tested > Assumed** — if it's not tested, it's broken
4. **Local-first** — all core functionality must work without external APIs or network access

## Naming Conventions

### Python
- `snake_case` for variables, functions, module names
- `PascalCase` for classes and dataclasses
- `UPPER_SNAKE_CASE` for constants
- `_prefix` for private methods and attributes
- Workflow classes: `{Name}Workflow` (e.g., `InitWorkflow`, `AutonomousWorkflow`)
- Analyzer classes: `{Name}Analyzer` or `{Name}Extractor`
- Validator classes: `{Name}Validator` or `{Name}Detector`

### File Naming
- Modules: `snake_case.py`
- Test files: `test_{module}.py`
- Steering templates: `kebab-case.md` (e.g., `tech-stack.md`)

## Code Style

### Formatting
- Line length: 100 characters
- Indent: 4 spaces
- Trailing commas: required in multi-line collections
- String quotes: double quotes preferred

### Imports
- Group: stdlib → third-party → local (separated by blank lines)
- Sort: alphabetical within groups
- No wildcard imports (`from module import *`)
- Relative imports within the `hiveforge` package

### Documentation
- All public functions and classes must have docstrings (Google style)
- Complex logic needs inline comments explaining *why*, not *what*
- Every module needs a module-level docstring
- Requirements references in docstrings: `Requirements: 3.1, 4.6`

### Type Hints
- All function signatures must have type hints
- Use `Optional[X]` not `X | None` for Python 3.11 compatibility
- Use `Dict`, `List`, `Tuple` from `typing` for complex types

## Error Handling
- Use custom exception classes for domain errors
- Never silently swallow exceptions — log at minimum
- Provide actionable error messages (what failed + how to fix)
- LLM failures must always fall back gracefully, never crash the workflow

## Testing
- Minimum coverage: 80% overall; 100% for critical paths (workflow execution, file writing)
- All new code needs tests before merging
- Test file naming: `test_{module}.py`
- Use `pytest` with fixtures; avoid `unittest.TestCase`
- Mock all LLM calls in unit tests — never make real API calls in tests

## Git Conventions
- Format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Examples:
  - `feat(steering): add autonomous generation with confidence scoring`
  - `fix(template): resolve placeholder replacement for nested knowledge dicts`
  - `test(workflow): add integration tests for init workflow rollback`
- Branch naming: `feature/short-description`, `fix/issue-description`
- Never commit directly to `main`; use PRs with at least one review
