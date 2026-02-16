# Steering Validator Agent

## Overview

The Steering Validator is an AI agent that validates steering files for completeness, consistency, and quality. It performs rule-based checks and optional semantic validation to ensure steering files meet project standards.

## Capabilities

### Rule-Based Validation

**Completeness Checks**
- Detects unreplaced placeholders (e.g., `{PROJECT_NAME}`, `{TECHNOLOGY}`)
- Verifies all required sections are populated
- Checks for empty or stub content
- Validates frontmatter structure

**Structure Checks**
- Verifies frontmatter format and required fields
- Validates markdown structure and hierarchy
- Checks for proper section organization
- Ensures template structure is preserved

**Consistency Checks**
- Detects contradictions across files (e.g., conflicting tech stack)
- Validates cross-references between files
- Checks for consistent terminology and naming
- Verifies version numbers match across files

### Semantic Validation (Optional)

**LLM-Powered Checks**
- Detects logical contradictions in content
- Validates technical accuracy of descriptions
- Checks for coherence and clarity
- Identifies potential improvements

**Token Efficiency**
- Max 1000 tokens per semantic check
- Caches validation results to avoid redundant checks
- Only runs when explicitly enabled or for critical issues

### Validation Reporting

**Issue Categorization**
- **Critical**: Blocks workflow, must be fixed (e.g., unreplaced placeholders)
- **Warning**: Should be fixed but doesn't block (e.g., inconsistencies)
- **Info**: Suggestions for improvement (e.g., missing optional sections)

**Detailed Reports**
- File path and line number for each issue
- Clear description of the problem
- Actionable fix suggestions
- Severity level and category

## Usage

### Validate Command

```bash
# Basic validation
hiveforge steering validate

# Strict mode (warnings as errors)
hiveforge steering validate --strict
```

### Exit Codes

- **0**: Validation passed (or only warnings in non-strict mode)
- **1**: Validation failed (critical issues or warnings in strict mode)

### Automatic Validation

The validator runs automatically after:
- `hiveforge steering init` (unless --skip-validation)
- `hiveforge steering update` (unless --skip-validation)

## Validation Rules

### Completeness Rules

1. **No Unreplaced Placeholders**
   - Pattern: `\{[A-Z_]+\}`
   - Severity: Critical
   - Fix: Replace with actual values

2. **Required Sections Populated**
   - Checks: All template sections have content
   - Severity: Critical
   - Fix: Add missing content

3. **No Stub Content**
   - Pattern: `TODO`, `FIXME`, `...`, `TBD`
   - Severity: Warning
   - Fix: Replace with actual content

### Structure Rules

1. **Valid Frontmatter**
   - Format: YAML between `---` delimiters
   - Required fields: Varies by template
   - Severity: Critical
   - Fix: Add or correct frontmatter

2. **Proper Markdown Structure**
   - Checks: Valid headers, lists, code blocks
   - Severity: Warning
   - Fix: Correct markdown syntax

3. **Template Structure Preserved**
   - Checks: Original sections still present
   - Severity: Warning
   - Fix: Restore missing sections

### Consistency Rules

1. **Tech Stack Consistency**
   - Checks: tech-stack.md matches other files
   - Severity: Warning
   - Fix: Align technology references

2. **Architecture Consistency**
   - Checks: architecture.md matches conventions.md
   - Severity: Warning
   - Fix: Align architectural descriptions

3. **Terminology Consistency**
   - Checks: Consistent naming across files
   - Severity: Info
   - Fix: Standardize terminology

## Configuration

The Steering Validator behavior is controlled by `SteeringConfig`:

```python
config = SteeringConfig(
    strict_mode=False,           # Treat warnings as errors
    skip_validation=False,       # Skip validation entirely
    semantic_validation=False,   # Enable LLM-powered checks
)
```

## Validation Report Format

```
Validation Report
================

✓ project-vision.md: PASS
✓ tech-stack.md: PASS
⚠ architecture.md: 2 warnings
  Line 15: [WARNING] Inconsistent technology reference
    Found: "PostgreSQL 14" but tech-stack.md specifies "PostgreSQL 15"
    Suggestion: Update to match tech-stack.md
  
  Line 42: [INFO] Missing optional section
    Section "Scalability Considerations" is empty
    Suggestion: Add scalability information

✗ conventions.md: 1 critical issue
  Line 8: [CRITICAL] Unreplaced placeholder
    Found: "{INDENT_STYLE}"
    Suggestion: Replace with actual indentation style (e.g., "4 spaces")

Summary
-------
Files checked: 8
Passed: 6
Warnings: 1
Critical issues: 1

Validation FAILED (1 critical issue)
```

## Workflow Integration

### Init Workflow
1. Generate steering files
2. **Run validator** (unless --skip-validation)
3. Display validation report
4. Exit with appropriate code

### Update Workflow
1. Apply approved changes
2. **Run validator** (unless --skip-validation)
3. Display validation report
4. Exit with appropriate code

### Validate Workflow
1. Verify files exist
2. **Run validator**
3. Display validation report
4. Return exit code

## Caching

The validator caches validation results to improve performance:

- **Cache key**: Hash of file content
- **Cache location**: `.kiro/.cache/validation_cache.json`
- **Cache invalidation**: Automatic when file changes
- **Benefits**: Faster validation, reduced LLM calls

## Error Handling

The validator handles various error conditions gracefully:

- **Missing Files**: Reports as critical issue
- **Malformed Files**: Reports parsing errors
- **LLM API Errors**: Falls back to rule-based validation only
- **Cache Errors**: Continues without cache

## Best Practices

### For Users

1. **Run Validation Regularly**: Validate after manual edits
2. **Fix Critical Issues First**: Address critical issues before warnings
3. **Use Strict Mode in CI**: Enable --strict in continuous integration
4. **Review Suggestions**: Validation suggestions are helpful but not always required
5. **Customize Carefully**: Preserve template structure when customizing

### For Developers

1. **Rule-Based First**: Implement rule-based checks before semantic checks
2. **Clear Messages**: Provide actionable fix suggestions
3. **Token Limiting**: Respect 1000 token limit for semantic checks
4. **Cache Results**: Use validation cache to avoid redundant checks
5. **Graceful Degradation**: Fall back to rule-based validation if LLM fails

## Examples

### Example 1: Basic Validation

```bash
# Validate steering files
hiveforge steering validate

# Output:
# ✓ All files passed validation
# Exit code: 0
```

### Example 2: Validation with Issues

```bash
# Validate steering files
hiveforge steering validate

# Output:
# ⚠ 2 warnings found
# ✗ 1 critical issue found
# See report above for details
# Exit code: 1
```

### Example 3: Strict Mode

```bash
# Treat warnings as errors
hiveforge steering validate --strict

# Output:
# ⚠ 2 warnings found (treated as errors in strict mode)
# Exit code: 1
```

### Example 4: Validation in CI

```yaml
# .github/workflows/validate.yml
name: Validate Steering Files

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install HiveForge
        run: pip install hiveforge
      - name: Validate steering files
        run: hiveforge steering validate --strict
```

## Troubleshooting

### Issue: Too many false positives

**Solution**: Review validation rules and adjust thresholds. Some warnings may be acceptable for your project.

### Issue: Validation is too slow

**Solution**: Disable semantic validation or check cache configuration. Rule-based validation should be fast.

### Issue: Validator doesn't detect my issue

**Solution**: Validation rules may not cover your specific case. Consider adding custom validation rules or reporting the issue.

### Issue: Strict mode is too strict

**Solution**: Fix warnings or use normal mode. Strict mode is designed for CI/CD where all issues should be addressed.

## Validation Rules Reference

### Critical Issues (Block Workflow)
- Unreplaced placeholders
- Missing required sections
- Invalid frontmatter
- Malformed markdown

### Warnings (Should Fix)
- Inconsistencies across files
- Stub content (TODO, FIXME)
- Missing optional sections
- Terminology inconsistencies

### Info (Suggestions)
- Potential improvements
- Style suggestions
- Completeness suggestions

## LLM Usage Tracking

The validator tracks LLM usage for semantic validation:

```python
report = validator.validate_all(files)

print(f"LLM calls: {report.llm_calls}")
print(f"Tokens used: {report.tokens_used}")
```

This helps monitor API costs and optimize validation performance.

## Related Components

- **Rule-Based Validators**: Implement specific validation rules
- **SteeringAssistant**: Generates steering files that validator checks
- **TemplatePopulator**: Populates templates that validator validates
- **ValidateWorkflow**: Orchestrates validation process

## Requirements

Implements requirements:
- 10.1-10.10: Validation rules and reporting
- 11.1-11.7: Validate workflow and exit codes

## See Also

- [Steering Assistant Agent](./steering-assistant.md)
- [Validate Workflow Documentation](../docs/validate-workflow.md)
- [Validation Rules Reference](../docs/validation-rules.md)
