# HiveForge Steering Assistant Power

**Version**: 2.0.0  
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

### Initialize Steering Files

```
"Please initialize steering files for my project"
```

This will:
1. Analyze your project structure and code
2. Discover existing documentation
3. Generate 4-5 steering files with AI-powered content
4. Save files to `.kiro/steering/`

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
- `auto_discover` (boolean, default: true): Enable automatic discovery
- `autonomous` (boolean, default: true): Enable AI generation
- `confidence_threshold` (float, default: 0.7): Minimum confidence for AI decisions

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
  "autonomous": true,
  "files_count": 5
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
