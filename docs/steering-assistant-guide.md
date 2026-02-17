# Steering Assistant User Guide

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Init Workflow](#init-workflow)
4. [Update Workflow](#update-workflow)
5. [Validate Workflow](#validate-workflow)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

## Overview

The Steering Assistant is an AI-powered tool that helps you create and maintain steering files throughout your project lifecycle. It automates the tedious process of documenting your project's vision, tech stack, architecture, and conventions.

### What It Does

- **Analyzes Your Codebase**: Automatically extracts tech stack, architecture, and coding conventions
- **Parses Artifacts**: Reads project specs, diagrams, and documentation (markdown, PDF, images)
- **Fills Knowledge Gaps**: Conducts interactive conversations to gather missing information
- **Generates Steering Files**: Creates 8 comprehensive steering files
- **Maintains Over Time**: Updates steering files as your project evolves
- **Preserves Customizations**: Keeps your manual edits during updates

### When to Use It

- **New Projects**: Generate steering files from project specs and requirements
- **Existing Projects**: Import existing codebase and documentation
- **Project Updates**: Keep steering files in sync with code changes
- **Team Onboarding**: Create comprehensive documentation for new team members
- **Compliance**: Ensure documentation meets organizational standards

## Getting Started

### Prerequisites

- HiveForge installed (`pip install hiveforge` or install from source)
- A HiveForge project initialized (`hiveforge -n my-project`)
- Optional: Project artifacts (specs, diagrams, docs) to import

### Quick Start

```bash
# 1. Create a new HiveForge project
hiveforge -n my-awesome-app
cd my-awesome-app

# 2. Generate steering files
hiveforge steering init

# 3. Answer questions during conversation
# The assistant will ask about your project

# 4. Review generated files
ls .kiro/steering/
```

## Init Workflow

The init workflow creates steering files from scratch.

### Basic Init

```bash
# Interactive mode (default)
hiveforge steering init
```

This will:
1. Create `.kiro/onboarding/` staging folder
2. Check for existing steering files (prompts for backup if found)
3. Parse any artifacts in `.kiro/onboarding/`
4. Conduct interactive conversation to gather missing information
5. Generate 8 steering files in `.kiro/steering/`
6. Validate generated files

### Init with Code Analysis

```bash
# Analyze existing codebase
hiveforge steering init --analyze-code
```

This automatically extracts:
- **Languages & Versions**: From file extensions and dependency files
- **Tech Stack**: From package.json, requirements.txt, go.mod, etc.
- **Architecture**: From directory structure patterns
- **Conventions**: From actual code (naming, indentation, docstrings)
- **Documentation**: From README files and docs folders

**Benefits:**
- Reduces questions during conversation
- More accurate information extraction
- Faster setup for existing projects

### Init with Artifacts

```bash
# 1. Place artifacts in staging folder
mkdir -p .kiro/onboarding
cp project-spec.md .kiro/onboarding/
cp architecture-diagram.pdf .kiro/onboarding/
cp requirements.png .kiro/onboarding/

# 2. Run init
hiveforge steering init
```

**Supported Formats:**
- **Markdown** (.md): Project specs, requirements, documentation
- **PDF** (.pdf): Architecture diagrams, design docs, presentations
- **Images** (.png, .jpg): Screenshots, diagrams, mockups (OCR)

### Non-Interactive Mode

```bash
# Skip conversation, use only artifacts and code analysis
hiveforge steering init --no-interactive --analyze-code
```

**Use Cases:**
- CI/CD pipelines
- Batch processing
- When all information is available in artifacts

### Init with Web Research

```bash
# Enable web research for missing information
hiveforge steering init --research
```

**When to Use:**
- Looking up library versions
- Finding best practices
- Researching technology choices

**Note:** Requires internet connection and may increase processing time.

### Skip Validation

```bash
# Skip automatic validation after generation
hiveforge steering init --skip-validation
```

**Use Cases:**
- Faster iteration during development
- When you plan to manually review files
- When validation is done separately

### Complete Example

```bash
# Full-featured init
hiveforge steering init \
  --analyze-code \
  --research \
  --interactive
```

## Update Workflow

The update workflow updates existing steering files with new information.

### Basic Update

```bash
# 1. Add new artifacts
cp updated-requirements.md .kiro/onboarding/

# 2. Run update
hiveforge steering update
```

This will:
1. Verify existing steering files exist
2. Parse existing steering files
3. Parse new artifacts from `.kiro/onboarding/`
4. Detect user customizations (preserves them)
5. Conduct conversation to gather missing information
6. Detect conflicts between old and new information
7. Generate diffs showing proposed changes
8. Ask for user approval
9. Apply approved changes
10. Validate updated files

### Update with Research

```bash
# Enable web research during update
hiveforge steering update --research
```

### Non-Interactive Update

```bash
# Skip conversation, use only artifacts
hiveforge steering update --no-interactive
```

**Note:** Non-interactive updates will only apply changes that don't conflict with existing content.

### Reviewing Diffs

During update, you'll see diffs like this:

```diff
--- tech-stack.md (original)
+++ tech-stack.md (updated)
@@ -5,7 +5,7 @@
 ### Backend
-- **Language:** Python 3.10
+- **Language:** Python 3.11
 - **Framework:** FastAPI
```

**Options:**
- **Accept**: Apply all changes
- **Reject**: Keep existing content
- **Review**: See detailed diff for each file

### Conflict Resolution

If conflicts are detected, you'll be prompted to resolve them:

```
Conflict detected in tech-stack.md:

Old value: PostgreSQL 14
New value: PostgreSQL 15

Which value should we use?
1. Keep old value (PostgreSQL 14)
2. Use new value (PostgreSQL 15)
3. Enter custom value

Choice:
```

### Customization Preservation

The update workflow automatically preserves your customizations:

- **Detected Customizations**: Content beyond placeholder replacements
- **Preserved**: Custom sections, formatting, additional content
- **Updated**: Only template placeholders and conflicting information

**Example:**

```markdown
# Original template
## Tech Stack
{BACKEND_LANGUAGE}

# Your customization
## Tech Stack
Python 3.11

### Why Python?
We chose Python for its excellent data science libraries...

# After update (customization preserved)
## Tech Stack
Python 3.11

### Why Python?
We chose Python for its excellent data science libraries...
```

## Validate Workflow

The validate workflow checks steering files for completeness and consistency.

### Basic Validation

```bash
# Validate steering files
hiveforge steering validate
```

**Checks:**
- Unreplaced placeholders (e.g., `{PROJECT_NAME}`)
- Missing required sections
- Invalid frontmatter
- Inconsistencies across files
- Stub content (TODO, FIXME)

### Strict Mode

```bash
# Treat warnings as errors
hiveforge steering validate --strict
```

**Use Cases:**
- CI/CD pipelines
- Pre-commit hooks
- Quality gates

### Validation Report

```
Validation Report
================

✓ project-vision.md: PASS
✓ tech-stack.md: PASS
⚠ architecture.md: 2 warnings
  Line 15: [WARNING] Inconsistent technology reference
    Found: "PostgreSQL 14" but tech-stack.md specifies "PostgreSQL 15"
    Suggestion: Update to match tech-stack.md

✗ conventions.md: 1 critical issue
  Line 8: [CRITICAL] Unreplaced placeholder
    Found: "{INDENT_STYLE}"
    Suggestion: Replace with actual indentation style

Summary
-------
Files checked: 8
Passed: 6
Warnings: 1
Critical issues: 1

Validation FAILED (1 critical issue)
```

### Exit Codes

- **0**: Validation passed (or only warnings in non-strict mode)
- **1**: Validation failed (critical issues or warnings in strict mode)

### Automatic Validation

Validation runs automatically after:
- `hiveforge steering init` (unless --skip-validation)
- `hiveforge steering update` (unless --skip-validation)

## Best Practices

### For New Projects

1. **Start with Artifacts**: Place project specs in `.kiro/onboarding/` before running init
2. **Use Code Analysis**: If you have existing code, use `--analyze-code`
3. **Be Specific**: Provide detailed answers during conversation
4. **Review Output**: Always review generated files before committing
5. **Validate**: Run `hiveforge steering validate --strict` before committing

### For Existing Projects

1. **Import Codebase**: Always use `--analyze-code` for existing projects
2. **Import Documentation**: Copy existing docs to `.kiro/onboarding/`
3. **Incremental Approach**: Start with basic info, refine over time
4. **Preserve History**: Keep backups of manual edits
5. **Regular Updates**: Update steering files when architecture changes

### For Team Collaboration

1. **Version Control**: Commit steering files to git
2. **Review Changes**: Use pull requests for steering file updates
3. **Consistent Updates**: Designate team members to maintain steering files
4. **Validation in CI**: Add `hiveforge steering validate --strict` to CI pipeline
5. **Documentation Culture**: Encourage team to reference steering files

### For Maintenance

1. **Regular Updates**: Update steering files quarterly or after major changes
2. **Artifact Management**: Keep `.kiro/onboarding/` clean (remove outdated artifacts)
3. **Customization Tracking**: Document why you made customizations
4. **Validation Checks**: Run validation before releases
5. **Backup Strategy**: Keep backups in `.kiro/backups/`

## Troubleshooting

### Issue: Assistant asks too many questions

**Symptoms:**
- Long conversation with many questions
- Questions about information that should be obvious

**Solutions:**
1. Use `--analyze-code` to auto-extract information
2. Place more artifacts in `.kiro/onboarding/`
3. Use `--no-interactive` if you have all information in artifacts

### Issue: Generated content is too generic

**Symptoms:**
- Steering files contain placeholder-like content
- Information lacks specificity

**Solutions:**
1. Provide more detailed answers during conversation
2. Add more specific artifacts (detailed specs, architecture diagrams)
3. Use `--research` to find more accurate information
4. Manually edit generated files and run update to refine

### Issue: Customizations not preserved during update

**Symptoms:**
- Manual edits are overwritten during update
- Custom sections disappear

**Solutions:**
1. Ensure customizations are substantial (not just placeholder replacements)
2. Check that customizations are in proper markdown format
3. Review diff carefully before accepting changes
4. Report issue if customizations should have been preserved

### Issue: LLM API rate limiting

**Symptoms:**
- "Rate limit exceeded" errors
- Slow processing with retries

**Solutions:**
1. Wait a few minutes (automatic retry with exponential backoff)
2. Use `--no-interactive` to reduce API calls
3. Check response cache (`.kiro/.cache/response_cache.json`)
4. Reduce batch size in configuration (advanced)

### Issue: Validation fails with false positives

**Symptoms:**
- Validation reports issues that aren't actually problems
- Warnings for acceptable content

**Solutions:**
1. Review validation rules (may be too strict for your project)
2. Use normal mode instead of strict mode
3. Manually verify reported issues
4. Report false positives as bugs

### Issue: Code analysis fails or times out

**Symptoms:**
- "Code analysis timeout" errors
- Analysis takes too long

**Solutions:**
1. Check for very large codebases (>10k files)
2. Ensure `.gitignore` is properly configured
3. Remove unnecessary files from analysis
4. Use sampling strategy (automatic for large codebases)

### Issue: Artifacts not parsed correctly

**Symptoms:**
- PDF content is garbled
- Images not recognized
- Markdown formatting lost

**Solutions:**
1. **PDF Issues**: Ensure PDF is not encrypted or corrupted
2. **Image Issues**: Install tesseract for OCR (`brew install tesseract` on macOS)
3. **Markdown Issues**: Check UTF-8 encoding
4. **General**: Try converting to different format

### Issue: Conversation takes too long

**Symptoms:**
- Many back-and-forth questions
- Slow progress

**Solutions:**
1. Use `--no-interactive` to skip conversation
2. Provide more complete artifacts upfront
3. Use `--analyze-code` to reduce questions
4. Answer questions in batches (max 8 per batch)

## Advanced Usage

### Custom Workflows

#### Workflow 1: Import Existing Project

```bash
# 1. Initialize HiveForge project
hiveforge -n existing-app
cd existing-app

# 2. Copy existing documentation
cp ../old-project/README.md .kiro/onboarding/
cp ../old-project/docs/architecture.md .kiro/onboarding/

# 3. Generate steering files with code analysis
hiveforge steering init --analyze-code --research

# 4. Review and refine
hiveforge steering validate --strict
```

#### Workflow 2: Continuous Documentation

```bash
# 1. Make code changes
git checkout -b feature/new-api

# 2. Update documentation
cp api-spec.md .kiro/onboarding/

# 3. Update steering files
hiveforge steering update --no-interactive

# 4. Validate
hiveforge steering validate --strict

# 5. Commit
git add .kiro/steering/
git commit -m "docs: update steering files for new API"
```

#### Workflow 3: CI/CD Integration

```yaml
# .github/workflows/validate-steering.yml
name: Validate Steering Files

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install HiveForge
        run: pip install hiveforge
      
      - name: Validate steering files
        run: hiveforge steering validate --strict
```

### Configuration

The Steering Assistant can be configured via `SteeringConfig`:

```python
from hiveforge.steering.models import SteeringConfig
from pathlib import Path

config = SteeringConfig(
    research_enabled=True,       # Enable web research
    skip_validation=False,       # Run validation
    interactive=True,            # Enable conversation
    analyze_code=True,           # Analyze codebase
    backup_enabled=True,         # Create backups
    backup_dir=Path(".kiro/backups"),
    strict_mode=False,           # Validation strictness
)
```

### Response Caching

The Steering Assistant caches LLM responses to avoid redundant API calls:

**Cache Location:** `.kiro/.cache/response_cache.json`

**Clear Cache:**
```bash
rm .kiro/.cache/response_cache.json
```

**Benefits:**
- Faster responses for repeated questions
- Reduced API costs
- Consistent answers

### Token Efficiency

The Steering Assistant minimizes token usage:

- **Question Batching**: Max 8 questions per batch
- **Knowledge Base Limiting**: Max 4000 tokens of context
- **Template Summaries**: Max 2000 tokens per steering file
- **Incremental Updates**: Max 3000 tokens per file update
- **Local Analysis**: All code analysis runs locally (no LLM calls)

### Error Recovery

The Steering Assistant handles errors gracefully:

- **Corrupted Files**: Skips and continues with other files
- **Missing Dependencies**: Infers from import statements
- **LLM Rate Limiting**: Automatic retry with exponential backoff (2^retry_count seconds)
- **Network Issues**: Retries with backoff, falls back to cached responses
- **Parsing Errors**: Logs error, continues with remaining files

## Related Documentation

- [Steering Assistant Agent Definition](../.kiro/agents/steering_assistant.md)
- [Steering Validator Agent Definition](../.kiro/agents/steering_validator.md)
- [HiveForge README](../README.md)
- [Architecture Documentation](./architecture.md)
- [Troubleshooting Guide](./troubleshooting.md)

## Support

- **Bug Reports**: [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/asoshnin/HiveForge/discussions)
- **Questions**: Check [Troubleshooting](#troubleshooting) section first

---

**Last Updated**: February 2026
**Version**: 1.0.0
