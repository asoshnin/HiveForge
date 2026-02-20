# HiveForge Steering Assistant Power

**Version**: 2.2.0  
**Category**: Documentation  
**Author**: HiveForge Team

---

## Overview

The HiveForge Steering Assistant is an AI-powered KIRO Power that automatically generates and maintains project steering files. It analyzes your codebase, discovers existing documentation, and creates comprehensive steering files that help developers understand your project's architecture, conventions, tech stack, and vision.

### What are Steering Files?

Steering files are structured documentation files stored in `.kiro/steering/` that provide essential context about your project:

- **tech-stack.md** - Technologies, frameworks, and dependencies
- **architecture.md** - System design and component relationships
- **conventions.md** - Coding standards and best practices
- **project-vision.md** - Goals, metrics, and roadmap

---

## Features

✅ **Automatic Project Discovery** - Analyzes code, configs, and existing docs  
✅ **AI-Powered Generation** - Creates contextually relevant content  
✅ **Smart Updates** - Preserves customizations while refreshing content  
✅ **Quality Validation** - Checks completeness and semantic quality  
✅ **Template Reset** - Restore files to default templates with backups

---

## Installation

### Via uvx (Recommended)

```bash
uvx hiveforge-steering-mcp@latest
```

### Via pip

```bash
pip install hiveforge-steering-mcp
```

---

## Usage

The Power activates automatically when you mention keywords like "steering", "documentation", or "onboarding" in your KIRO chat.

### Source Document Location

**Important**: By default, the Power looks for existing documentation in `.kiro/onboarding/` directory. This is where you should place any existing documentation you want the Power to analyze when generating steering files.

**Default behavior**:
- The Power scans `.kiro/onboarding/` for existing docs (README files, architecture docs, etc.)
- If found, these documents are used to generate more accurate steering files
- If the folder is empty, the Power will infer content from code analysis (with lower confidence)

**Custom source paths**:
You can specify a different location for your source documents:

```
"Initialize steering files using documents from my _DEVELOPMENT folder"
```

Or more explicitly:

```
"Initialize steering files with source_docs_path='docs/onboarding'"
```

**Examples**:
- `"Use documents from __DEVELOPMENT/ to initialize steering files"`
- `"Initialize steering with source_docs_path='documentation/project-docs'"`
- `"Generate steering files from docs in my-docs/ folder"`

### Initialize Steering Files

```
"Please initialize steering files for my project"
```

This will:
1. Look for documents in `.kiro/onboarding/` (or custom path if specified)
2. Analyze your project structure and code
3. Discover existing documentation
4. Generate 4-5 steering files with AI-powered content
5. Save files to `.kiro/steering/`

### Update Existing Files

```
"Update my steering files with latest changes"
```

This will:
1. Re-analyze your project
2. Update files while preserving your customizations
3. Show what changed

### Validate Files

```
"Validate my steering files"
```

This checks for:
- Missing required sections
- Placeholder content that needs filling
- Semantic quality issues

### Reset to Templates

```
"Reset steering files to default templates"
```

This will:
1. Create a backup in `.kiro/backups/`
2. Reset files to clean templates
3. Preserve your backup for reference

### Discover Documentation

```
"Discover existing documentation in my project"
```

This scans for:
- README files
- Documentation directories
- Configuration files
- Code comments and docstrings

---

## Available Tools

### 1. `init_steering`

Initialize steering files for a new project.

**Parameters**:
- `project_root` (string, default: "."): Path to project root
- `source_docs_path` (string, optional): Custom path to source documents, relative to project root (e.g., `"_DEVELOPMENT"`, `"docs/specs"`). When omitted, uses `.kiro/onboarding/` by default.
- `auto_discover` (boolean, default: true): Enable automatic discovery
- `autonomous` (boolean, default: true): Enable AI generation
- `confidence_threshold` (float, default: 0.7): Minimum confidence for autonomous decisions (autonomous mode only)
- `dry_run` (boolean, default: false): Preview what would be created without writing files
- `copy_files` (boolean, default: false): Copy source files to staging instead of using symlinks

**Example Response**:
```json
{
  "status": "success",
  "message": "Successfully initialized steering files (5 files created)",
  "files_created": [
    ".kiro/steering/tech-stack.md",
    ".kiro/steering/architecture.md",
    ".kiro/steering/conventions.md",
    ".kiro/steering/project-vision.md"
  ],
  "warnings": [],
  "autonomous": true,
  "files_count": 5,
  "source_documents_found": 3,
  "confidence_level": "high",
  "confidence_score": 0.82
}
```

### 2. `update_steering`

Update existing steering files with fresh analysis.

**Parameters**:
- `project_root` (string, default: "."): Path to project root
- `files_to_update` (array, optional): Specific files to update
- `preserve_customizations` (boolean, default: true): Keep user edits
- `incremental` (boolean, default: true): Use incremental update mode

**Example Response**:
```json
{
  "status": "success",
  "message": "Successfully updated steering files (3 files modified)",
  "files_modified": [
    ".kiro/steering/tech-stack.md",
    ".kiro/steering/architecture.md"
  ],
  "customizations_detected": 2
}
```

### 3. `validate_steering`

Validate steering files for completeness and quality.

**Parameters**:
- `project_root` (string, default: "."): Path to project root
- `strict` (boolean, default: false): Treat warnings as errors
- `use_llm` (boolean, default: true): Enable semantic validation

**Example Response**:
```json
{
  "status": "success",
  "message": "All validation checks passed",
  "files_checked": 5,
  "critical_issues": 0,
  "warnings": 0,
  "overall_status": "valid"
}
```

### 4. `reset_steering`

Reset steering files to default templates.

**Parameters**:
- `project_root` (string, default: "."): Path to project root
- `file` (string, optional): Specific file to reset
- `confirm` (boolean, default: false): Skip confirmation

**Example Response**:
```json
{
  "status": "success",
  "message": "Successfully reset 5 file(s) to default templates",
  "files_modified": [
    ".kiro/steering/tech-stack.md",
    ".kiro/steering/architecture.md"
  ],
  "backup_location": ".kiro/backups/reset_20260217_143022"
}
```

### 5. `discover_docs`

Discover existing documentation and project files.

**Parameters**:
- `project_root` (string, default: "."): Path to project root
- `source_docs_path` (string, optional): Prioritize this path for discovery (relative to project root)
- `file_types` (array, optional): Filter by file extensions (e.g., `[".md", ".pdf"]`)
- `include_git_history` (boolean, default: false): Analyze git commits
- `max_discovery_files` (integer, default: 1000): Maximum files to analyze
- `max_file_size_mb` (integer, default: 10): Maximum file size in MB

**Example Response**:
```json
{
  "status": "success",
  "message": "Discovery complete: 42 files found",
  "files_discovered": 42,
  "files_included": 37,
  "files_by_type": {".md": 25, ".pdf": 12},
  "files_by_path": {"_DEVELOPMENT": 37},
  "discovery_method": "scalable"
}
```

---

## Architecture

### Shared Backend Design

The Power uses a shared backend architecture that ensures **100% identical behavior** with the CLI version:

```
┌─────────────────────────────────────────┐
│         KIRO Orchestrator               │
└────────────────┬────────────────────────┘
                 │
                 ├─── Keywords: "steering", "documentation"
                 │
┌────────────────▼────────────────────────┐
│      HiveForge Steering Power (MCP)     │
│  ┌──────────────────────────────────┐   │
│  │   FastMCP Server                 │   │
│  │   - init_steering                │   │
│  │   - update_steering              │   │
│  │   - validate_steering            │   │
│  │   - reset_steering               │   │
│  │   - discover_docs                │   │
│  └──────────────┬───────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Shared Backend (Python)            │
│  ┌──────────────────────────────────┐   │
│  │   Workflow Adapters              │   │
│  │   - SharedInitWorkflow           │   │
│  │   - SharedUpdateWorkflow         │   │
│  │   - SharedValidateWorkflow       │   │
│  │   - SharedResetWorkflow          │   │
│  │   - SharedDiscoveryWorkflow      │   │
│  └──────────────┬───────────────────┘   │
└─────────────────┼───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      v02 Workflows (Stable)             │
│   - InitWorkflow                        │
│   - UpdateWorkflow                      │
│   - ValidateWorkflow                    │
│   - Discovery Components                │
└─────────────────────────────────────────┘
```

**Key Benefits**:
- ✅ CLI and Power produce identical outputs
- ✅ Zero code duplication (100% shared backend)
- ✅ Single source of truth for all logic
- ✅ Consistent error handling and validation

---

## Configuration

### Keyword Activation

The Power activates on these keywords:
- "steering"
- "steering files"
- "documentation"
- "onboarding"
- "project setup"
- "project documentation"

### Environment Variables

- `FASTMCP_LOG_LEVEL` - Set logging level (default: INFO)

---

## Examples

### Example 1: New Project Setup

**User**: "I just started a new Python project. Can you help me set up steering files?"

**Power Response**:
```json
{
  "status": "success",
  "message": "Successfully initialized steering files (5 files created)",
  "files_created": [
    ".kiro/steering/tech-stack.md",
    ".kiro/steering/architecture.md",
    ".kiro/steering/conventions.md",
    ".kiro/steering/project-vision.md"
  ],
  "files_count": 5
}
```

### Example 2: Update After Major Changes

**User**: "I just refactored my architecture. Update the steering files."

**Power Response**:
```json
{
  "status": "success",
  "message": "Successfully updated steering files (2 files modified)",
  "files_modified": [
    ".kiro/steering/architecture.md",
    ".kiro/steering/tech-stack.md"
  ],
  "customizations_detected": 3,
  "warnings": ["3 customizations preserved in architecture.md"]
}
```

### Example 3: Validation Before Release

**User**: "Validate my steering files before I release"

**Power Response**:
```json
{
  "status": "success",
  "message": "Validation passed with 2 warning(s)",
  "files_checked": 5,
  "critical_issues": 0,
  "warnings": 2,
  "overall_status": "valid"
}
```

---

## Troubleshooting

### No Documents Found / Low Confidence Warning

**Problem**: Power generates files but warns "No source documents found" or shows low confidence scores

**Cause**: The Power couldn't find existing documentation in the expected location (`.kiro/onboarding/` by default)

**Solution**:
1. **If you have existing docs**: Place them in `.kiro/onboarding/` directory before running init
2. **If docs are elsewhere**: Use `source_docs_path` parameter to point to your docs:
   ```
   "Initialize steering files with source_docs_path='docs/project-info'"
   ```
3. **If you have no docs**: This is expected - the Power will infer content from code analysis. Generated files will have `[INFERRED]` tags on sections that were generated without source documents.

**Understanding confidence scores**:
- **High confidence (0.7-1.0)**: Most content came from source documents
- **Medium confidence (0.4-0.7)**: Mix of source documents and code analysis
- **Low confidence (0.0-0.4)**: Mostly inferred from code, few source documents

Files with low confidence will have warnings at the top and `[INFERRED]` tags on sections that need review.

### Power Not Activating

**Problem**: Power doesn't respond to keywords

**Solution**:
1. Check that the Power is installed: `uvx hiveforge-steering-mcp@latest`
2. Verify keywords in your message: "steering", "documentation", etc.
3. Check KIRO Power configuration

### Files Not Generated

**Problem**: Init command completes but no files created

**Solution**:
1. Check project root path is correct
2. Verify `.kiro/steering/` directory permissions
3. Check logs for errors: `FASTMCP_LOG_LEVEL=DEBUG`

### Wrong Documents Being Used

**Problem**: Power is using the wrong documentation files

**Solution**:
1. Specify the correct path explicitly:
   ```
   "Initialize steering with source_docs_path='path/to/correct/docs'"
   ```
2. Check that `.kiro/onboarding/` doesn't contain old/incorrect docs
3. Use dry-run mode to preview what will be generated:
   ```
   "Initialize steering files in dry-run mode with source_docs_path='my-docs'"
   ```

### Customizations Lost

**Problem**: Updates overwrote my custom content

**Solution**:
1. Check `.kiro/backups/` for automatic backups
2. Use `preserve_customizations=true` (default)
3. Use `incremental=true` for safer updates

### Validation Fails

**Problem**: Validation reports issues

**Solution**:
1. Review specific issues in the response
2. Edit files to address critical issues
3. Use `strict=false` to allow warnings

---

## Performance

- **Generation Time**: < 2 minutes for typical projects
- **Memory Usage**: < 50MB
- **File Size Limits**: 10MB per file (configurable)
- **Discovery Limits**: 1000 files (configurable)

---

## Testing

The Power has comprehensive test coverage:

- **119 total tests** (100% passing)
- **21 orchestrator integration tests**
- **43 shared backend tests**
- **40 CLI compatibility tests**
- **10 MCP tool tests**
- **5 base class tests**

---

## Changelog

### Version 2.2.0 (2026-02-20)

**Feature Release**: Source Documents Path & Hallucination Guardrails

- ✅ `source_docs_path` parameter for custom document locations
- ✅ `dry_run` mode to preview without writing files
- ✅ `copy_files` parameter for symlink vs. copy control
- ✅ Confidence scoring and hallucination guardrails
- ✅ `[INFERRED]` tags on sections generated without source documents
- ✅ `file_types` filter for `discover_docs`
- ✅ Enhanced discovery statistics
- ✅ Security: path traversal, symlink attack, null byte injection prevention

**Breaking Changes**: None (all new parameters are optional)

### Version 2.0.0 (2026-02-17)

**Major Release**: Power Framework Conversion

- ✅ Converted to KIRO Power with MCP server
- ✅ Implemented shared backend architecture
- ✅ 100% CLI/Power output equivalence
- ✅ Added 5 MCP tools for orchestrator integration
- ✅ Comprehensive test coverage (119 tests)
- ✅ Keyword-based activation
- ✅ Structured JSON responses

**Breaking Changes**: None (backward compatible with v1.x CLI)

---

## Support

- **Documentation**: https://docs.hiveforge.dev/steering
- **Issues**: https://github.com/yourusername/hiveforge-steering-mcp/issues
- **Repository**: https://github.com/yourusername/hiveforge-steering-mcp

---

## License

MIT License - See LICENSE file for details

---

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

---

## Acknowledgments

Built with:
- **FastMCP** - MCP server framework
- **KIRO** - AI IDE platform
- **Python 3.11+** - Core implementation

---

**Made with ❤️ by the HiveForge Team**
