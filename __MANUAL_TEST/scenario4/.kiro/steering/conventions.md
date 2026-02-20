---
generated_by: hiveforge v2.2.0
generated_at: 2026-02-20T00:40:53.769160+00:00
source_documents: 0
code_analysis: true
confidence:
  overall: 0.30
  level: low
  sources:
    documents: 0.00
    code_analysis: 0.00
    inferred: 0.30
  inferred_sections:
    - "Naming Conventions"
    - "Code Style"
---

> ⚠️ **LOW CONFIDENCE**: This file was generated with limited source material.
> Most content is inferred from code analysis. Please review and update with actual project information.

---
inclusion: always
priority: 1
description: "Coding style, naming, test ing rules. Enforced by hooks and linters."---

# Coding Conventions

## General Principles
1. **Readability > Cleverness**
2. **Explicit > Implicit**
3. **Tested > Assumed**

## Naming Conventions
<!-- INFERRED: Please verify this section -->
### Python
- `snake_case` for variables, functions
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- `_prefix` for private

### JavaScript/TypeScript
- `camelCase` for variables, functions
- `PascalCase` for classes, components, types
- `UPPER_SNAKE_CASE` for constants

<!-- END INFERRED -->

## Code Style
<!-- INFERRED: Please verify this section -->
### Formatting
- Line length: 100 characters
- Indent: 4 spaces (Python), 2 spaces (JS)
- Trailing commas: required

### Imports
- Group: stdlib, third-party, local
- Sort: alphabetical within groups
- No wildcard imports

### Documentation
- All public functions must have docstrings
- Complex logic needs inline comments (why, not what)
- README for every module

<!-- END INFERRED -->

## Testing
- Minimum coverage: 80%
- All new code needs tests
- Test file naming: `test_{module}.py` or `{module}.test.js`

## Git Conventions
- Format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Example: `feat(auth): add password reset endpoint`