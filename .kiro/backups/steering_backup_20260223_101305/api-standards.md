---
inclusion: fileMatch
patterns: ["hiveforge-power/**", "mcp_server/**", "src/**/shared/**"]
priority: 2
description: "MCP server tool design, response formats, error handling. Loaded when working on MCP/Power code."
---

# MCP Server Standards

## MCP Tool Design Principles

### Tool Naming
- Use descriptive, action-oriented names: `init_steering`, `update_steering`, `validate_steering`
- Prefix with domain: `mcp_hiveforge_steering_*`
- Use snake_case for consistency with Python backend

### Tool Parameters
- Use Pydantic models for validation
- Provide sensible defaults (e.g., `project_root="."`)
- Make parameters optional when possible
- Use clear, descriptive parameter names

### Response Format
- Return structured JSON with consistent schema:
  ```json
  {
    "status": "success|failed",
    "message": "Human-readable description",
    "files_created": [],
    "files_modified": [],
    "warnings": [],
    "errors": [],
    "metadata": {}
  }
  ```

### Error Handling
- Return structured errors, never raise exceptions to MCP client
- Include `can_retry` flag for transient errors
- Provide actionable error messages
- Log errors to telemetry

## Tool Catalog

### Core Tools

| Tool | Purpose | Parameters | Returns |
|------|---------|------------|---------|
| `init_steering` | Create steering files | project_root, source_docs_path, auto_discover, autonomous, dry_run | Files created, warnings, confidence scores |
| `update_steering` | Update existing files | project_root, files_to_update, preserve_customizations | Files modified, conflicts resolved |
| `validate_steering` | Validate completeness | project_root, strict, use_llm | Validation report, issues found |
| `reset_steering` | Reset to templates | project_root, file, confirm | Files reset, backup location |
| `discover_docs` | Find existing docs | project_root, source_docs_path, file_types, include_git_history | Files discovered, metadata |
| `rollback_steering` | Restore from backup | project_root, backup_id | Files restored, success status |

## Authentication

### MCP Server Authentication
- No authentication required (local execution)
- Security enforced by KIRO IDE permissions
- Tools run with user's file system permissions

### API Key Management (for LLM calls)
- OpenAI API key from environment variable: `OPENAI_API_KEY`
- Anthropic API key from environment variable: `ANTHROPIC_API_KEY`
- Keys never logged or transmitted
- Fallback to cached responses if API unavailable

## Versioning

### MCP Protocol Version
- Current: MCP 1.0
- Backward compatibility maintained for tool schemas
- Breaking changes require major version bump

### Tool Schema Versioning
- Tool schemas defined in `mcp_server/server.py`
- Changes to parameters require version bump
- Deprecated parameters supported for 2 major versions

## Rate Limiting

### LLM API Rate Limits
- Automatic exponential backoff: 2^retry_count seconds
- Max retries: 3
- Fallback to cached responses after max retries

### File System Rate Limits
- No rate limiting (local file system)
- Concurrent access handled by OS

## Security

### Input Validation
- All paths validated to prevent directory traversal
- File types validated against whitelist
- Parameter types validated by Pydantic

### Output Sanitization
- File paths normalized before writing
- User input sanitized before LLM prompts
- Error messages sanitized (no sensitive data)

### Permission Model
- Tools run with user's file system permissions
- No privilege escalation
- Read-only operations for validation/discovery
- Write operations require explicit confirmation (dry_run mode)

## Performance

### Response Times
- `init_steering`: 10-30 seconds (with LLM calls)
- `update_steering`: 10-20 seconds (incremental)
- `validate_steering`: <1 second (rule-based)
- `discover_docs`: 5-15 seconds (depends on file count)

### Caching Strategy
- Response cache: `.kiro/.cache/response_cache.json`
- Code analysis cache: `.kiro/.cache/code_analysis.json`
- Validation cache: `.kiro/.cache/validation_cache.json`
- Cache invalidation: Manual or on file changes

### Token Efficiency
- Max 4000 tokens context per LLM call
- Max 2000 tokens per template
- Max 3000 tokens per file update
- Question batching: Max 8 questions per batch

## Monitoring

### Telemetry Collection
- Workflow events logged to `.kiro/.telemetry/`
- Performance metrics: duration, memory, CPU
- Error tracking: types, frequency, recovery
- No PII collected, local storage only

### Health Checks
- MCP server status: Check connection to KIRO IDE
- LLM API status: Check API key validity
- File system status: Check write permissions

## Documentation

### Tool Descriptions
- Each tool has detailed description in schema
- Parameter descriptions explain purpose and format
- Examples provided in POWER.md
- Error messages include suggestions

### User-Facing Documentation
- POWER.md: Power usage guide
- INSTALLATION_GUIDE.md: Setup instructions
- steering-assistant-guide.md: Detailed workflows
- README.md: Quick start
