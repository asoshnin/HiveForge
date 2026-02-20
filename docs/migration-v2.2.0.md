# Migration Guide: v2.2.0

This guide helps you migrate to HiveForge v2.2.0, which introduces custom source document paths, confidence scoring, and hallucination guardrails.

## What's New in v2.2.0

- **Custom source document paths**: Specify where your design documents are located
- **Confidence scoring**: Know which content is from documents vs. inferred
- **Hallucination guardrails**: Clear warnings when source material is missing
- **Dry-run mode**: Preview what will be generated before committing
- **Enhanced discovery**: Filter by file type, prioritize specific folders

## Do I Need to Migrate?

**No action required if:**
- Your documents are already in `.kiro/onboarding/`
- You're happy with the current behavior
- You don't need confidence metadata

**Consider migrating if:**
- Your documents are in a different folder (e.g., `_DEVELOPMENT/`, `docs/`)
- You want to see confidence scores in generated files
- You want warnings when source material is missing

## Migration Scenarios

### Scenario 1: Documents Already in `.kiro/onboarding/`

**Status:** ✅ No action needed

Your existing workflow continues to work unchanged:

```python
# Before v2.2.0
init_steering(project_root=".")

# After v2.2.0 (same behavior)
init_steering(project_root=".")
```

**What you get automatically:**
- Confidence metadata in generated files
- Warnings if `.kiro/onboarding/` is empty
- All new features work transparently

### Scenario 2: Want to Move Documents to Custom Folder

**Status:** 🔄 Optional migration

If you want to organize documents in a custom location:

**Step 1: Move documents**
```bash
# Create custom folder
mkdir _DEVELOPMENT

# Move documents
mv .kiro/onboarding/* _DEVELOPMENT/

# Or keep both (custom path takes precedence)
```

**Step 2: Update your workflow**

**From KIRO IDE (HiveForge Power):**
```
User: "Initialize steering files; my design docs are in _DEVELOPMENT"
KIRO: [calls init_steering(project_root=".", source_docs_path="_DEVELOPMENT")]
```

**From Python/CLI:**
```python
# New parameter
init_steering(
    project_root=".",
    source_docs_path="_DEVELOPMENT"
)
```

**Step 3: Verify**
```python
result = init_steering(
    project_root=".",
    source_docs_path="_DEVELOPMENT",
    dry_run=True  # Preview first
)

print(f"Found {result['source_documents_found']} documents")
print(f"Confidence: {result['confidence_level']}")
```

### Scenario 3: Documents in Multiple Locations

**Status:** ⚠️ Workaround required (v2.3.0 will support multiple paths)

**Current limitation:** v2.2.0 supports only one `source_docs_path`.

**Workaround Option A: Consolidate documents**
```bash
# Create single folder
mkdir _DEVELOPMENT/all-docs

# Copy/symlink all documents
cp docs/*.md _DEVELOPMENT/all-docs/
cp design/*.pdf _DEVELOPMENT/all-docs/
cp requirements/*.txt _DEVELOPMENT/all-docs/

# Use consolidated path
init_steering(source_docs_path="_DEVELOPMENT/all-docs")
```

**Workaround Option B: Prioritize one location**
```bash
# Use most important folder
init_steering(source_docs_path="design")

# Discovery will still scan other locations if budget remains
```

**Future (v2.3.0):**
```python
# Multiple paths support (coming soon)
init_steering(source_docs_path=["docs", "design", "_DEVELOPMENT"])
```

### Scenario 4: Using HiveForge Power from KIRO IDE

**Status:** 📝 Documentation updated

**Before v2.2.0:**
```
User: "Initialize steering files for my project"
KIRO: [calls init_steering(project_root=".")]
Result: Only uses .kiro/onboarding/ (often empty → silent failures)
```

**After v2.2.0:**
```
User: "Initialize steering files; my design docs are in _DEVELOPMENT"
KIRO: [calls init_steering(project_root=".", source_docs_path="_DEVELOPMENT")]
Result: Uses documents from _DEVELOPMENT/ + confidence metadata + warnings
```

**Key improvements:**
- KIRO can now understand custom document locations from natural language
- Empty source folders produce clear warnings (no more silent failures)
- Confidence scores help you identify inferred content

## Understanding Confidence Scores

### What Do Confidence Levels Mean?

**High (80-100%):**
- 80%+ content from source documents
- Code analysis confirms technical details
- Minimal inference needed
- ✅ Safe to use as-is

**Medium (50-79%):**
- 50-79% from source documents
- Some sections inferred from code patterns
- ⚠️ Review inferred sections (marked with `<!-- INFERRED -->`)

**Low (<50%):**
- Majority inferred by LLM
- Minimal source material available
- 🚨 Requires thorough review and updates

### Reading Confidence Metadata

Every generated file includes YAML frontmatter:

```markdown
---
generated_by: hiveforge v2.2.0
generated_at: 2026-02-19T10:30:00Z
source_documents: 3
source_docs_path: _DEVELOPMENT
code_analysis: true
confidence:
  overall: 0.65
  level: medium
  sources:
    documents: 0.40
    code_analysis: 0.20
    inferred: 0.05
  inferred_sections:
    - "Problem Statement"
    - "Target Users"
---

# Project Vision

## Problem Statement
<!-- INFERRED: Please verify this section -->
Users struggle with managing multiple documentation sources...
<!-- END INFERRED -->
```

**What to do:**
1. Check `confidence.level` (high/medium/low)
2. Review sections listed in `inferred_sections`
3. Look for `<!-- INFERRED -->` markers in content
4. Update inferred sections with actual project information

## Precedence Rules

### When Both `.kiro/onboarding/` and `source_docs_path` Exist

**Rule:** Only one path is used (no merging)

**Priority:**
1. If `source_docs_path` is provided → use only that path
2. If `source_docs_path` is NOT provided → use `.kiro/onboarding/` (default)

**Example:**
```python
# Scenario: Both folders exist
# .kiro/onboarding/ has 5 files
# _DEVELOPMENT/ has 10 files

# Case 1: No parameter
init_steering(project_root=".")
# Uses: .kiro/onboarding/ (5 files)

# Case 2: Custom path
init_steering(project_root=".", source_docs_path="_DEVELOPMENT")
# Uses: _DEVELOPMENT/ (10 files)
# Ignores: .kiro/onboarding/
```

## New Parameters Reference

### `init_steering` Parameters

```python
init_steering(
    project_root: str = ".",
    source_docs_path: Optional[str] = None,  # NEW
    auto_discover: bool = True,
    autonomous: bool = True,
    confidence_threshold: float = 0.7,
    dry_run: bool = False,  # NEW
    copy_files: bool = False  # NEW
)
```

**New parameters:**
- `source_docs_path`: Relative path to source documents (e.g., `"_DEVELOPMENT"`, `"docs"`)
- `dry_run`: Preview what would be created without writing files
- `copy_files`: If `True`, copy files to staging. If `False`, use symlinks (default, faster)

### `discover_docs` Parameters

```python
discover_docs(
    project_root: str = ".",
    source_docs_path: Optional[str] = None,  # NEW
    file_types: Optional[List[str]] = None,  # NEW
    include_git_history: bool = False,
    max_discovery_files: int = 1000,
    max_file_size_mb: int = 10
)
```

**New parameters:**
- `source_docs_path`: Prioritize this path for discovery
- `file_types`: Filter by extensions (e.g., `[".md", ".pdf"]`)

## Testing Your Migration

### Step 1: Dry-Run First

Always test with `dry_run=True` before committing:

```python
result = init_steering(
    project_root=".",
    source_docs_path="_DEVELOPMENT",
    dry_run=True
)

# Check results
print(f"Status: {result['status']}")
print(f"Documents found: {result['source_documents_found']}")
print(f"Confidence: {result['confidence_level']}")
print(f"Warnings: {result['warnings']}")

# Review preview
for file_name, content in result['preview'].items():
    print(f"\n=== {file_name} ===")
    print(content[:500])  # First 500 chars
```

### Step 2: Verify Discovery

Check what documents will be discovered:

```python
result = discover_docs(
    project_root=".",
    source_docs_path="_DEVELOPMENT",
    file_types=[".md", ".pdf"]
)

print(f"Files discovered: {result['files_discovered']}")
print(f"By type: {result['files_by_type']}")
print(f"By path: {result['files_by_path']}")
```

### Step 3: Run and Review

```python
result = init_steering(
    project_root=".",
    source_docs_path="_DEVELOPMENT"
)

# Check confidence
if result['confidence_level'] == 'low':
    print("⚠️ Low confidence - review inferred sections")
    print(f"Inferred sections: {result['confidence_scores']}")
```

## Common Issues

### Issue 1: "No source documents found"

**Cause:** `source_docs_path` points to empty or non-existent folder

**Solution:**
```bash
# Check folder exists
ls -la _DEVELOPMENT/

# Check for documents
find _DEVELOPMENT/ -name "*.md" -o -name "*.pdf"

# Try discovery first
hiveforge steering discover --source-docs-path _DEVELOPMENT
```

### Issue 2: "Path is outside project root"

**Cause:** Trying to use absolute path or path traversal

**Solution:**
```python
# ❌ Wrong: Absolute path
init_steering(source_docs_path="/Users/me/docs")

# ❌ Wrong: Path traversal
init_steering(source_docs_path="../other-project/docs")

# ✅ Correct: Relative path within project
init_steering(source_docs_path="_DEVELOPMENT")
init_steering(source_docs_path="docs/design")
```

### Issue 3: Low confidence scores

**Cause:** Not enough source documents

**Solution:**
1. Add more design documents to `source_docs_path`
2. Review and update inferred sections (marked with `<!-- INFERRED -->`)
3. Re-run with updated documents:
   ```python
   init_steering(source_docs_path="_DEVELOPMENT", force=True)
   ```

### Issue 4: Symlinks not supported

**Cause:** Windows without Developer Mode or network filesystems

**Solution:**
```python
# Use copy mode instead of symlinks
init_steering(
    source_docs_path="_DEVELOPMENT",
    copy_files=True  # Slower but works everywhere
)
```

## Rollback Plan

If you encounter issues with v2.2.0:

### Option 1: Use Default Behavior

```python
# Don't use new parameters
init_steering(project_root=".")
```

### Option 2: Downgrade to v2.1.0

```bash
pip install hiveforge==2.1.0
```

### Option 3: Report Issue

```bash
# Collect diagnostics
hiveforge steering validate --strict

# Report at: https://github.com/asoshnin/HiveForge/issues
```

## Future Enhancements (v2.3.0)

Planned features based on user feedback:

- **Multiple source paths**: `source_docs_path=["docs", "design", "_DEVELOPMENT"]`
- **Configurable confidence weights**: Adjust scoring algorithm
- **Confidence threshold warnings**: Customize when warnings trigger
- **Source path templates**: Pre-configured paths for common project structures
- **Deprecation of `.kiro/onboarding/`**: Move to explicit configuration

## Getting Help

- **Documentation**: [docs/steering-assistant-guide.md](./steering-assistant-guide.md)
- **Issues**: [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/asoshnin/HiveForge/discussions)

## Summary

v2.2.0 is a **backward-compatible** release that adds powerful new features while maintaining existing workflows. The key improvements are:

1. ✅ Custom source document paths (no more `.kiro/onboarding/` requirement)
2. ✅ Confidence scoring (know what's inferred vs. documented)
3. ✅ Clear warnings (no more silent failures)
4. ✅ Dry-run mode (preview before committing)
5. ✅ Enhanced discovery (filter by type, prioritize folders)

**Most users don't need to change anything** - existing workflows continue to work with added benefits.
