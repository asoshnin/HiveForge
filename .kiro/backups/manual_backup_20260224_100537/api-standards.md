---
inclusion: fileMatch
patterns: ["src/api/**", "tests/api/**", "src/**/api.py", "src/**/routes/**", "hiveforge/**/mcp_server.py", "hiveforge/**/cli.py"]
priority: 2
description: "API naming, versioning, error handling. Applies to CLI commands and MCP tool interfaces."
---

# API Standards & Conventions

## API Design Principles

HiveForge exposes two interfaces that must remain consistent:
1. **CLI interface** — Typer commands with typed options (`hiveforge steering init|update|validate|discover`)
2. **MCP tool interface** — FastMCP tools callable from KIRO IDE with identical semantics

Both interfaces must:
- Accept the same logical parameters (mapped appropriately per interface)
- Return the same structured result format
- Handle errors consistently with actionable messages
- Never break existing callers when adding new options (additive only)

## CLI Command Naming
- Use verb-noun format: `steering init`, `steering update`, `steering validate`
- Options use `--kebab-case` flags: `--analyze-code`, `--source-docs-path`, `--skip-validation`
- Boolean flags: `--flag` to enable, `--no-flag` to disable
- Positional args only for required primary inputs

## MCP Tool Naming
- Use `snake_case` tool names matching CLI commands: `init_steering`, `update_steering`, `validate_steering`
- Parameters mirror CLI options with `snake_case` names
- All parameters must have descriptions for IDE auto-complete

## Response Format (MCP Tools)
```json
{
  "status": "success | error | draft_ready",
  "message": "Human-readable summary",
  "files_created": ["path/to/file.md"],
  "files_modified": ["path/to/file.md"],
  "files_deleted": [],
  "warnings": ["Warning message"],
  "errors": [],
  "metadata": {}
}
```

## Versioning
- CLI: Semantic versioning via `pyproject.toml`; breaking changes require major version bump
- MCP tools: Tool signatures are versioned implicitly — never remove or rename parameters
- Deprecation: Add `deprecated=True` annotation before removal; keep for at least one minor version

## Error Handling
- CLI errors: Print user-friendly message with `typer.echo()`, exit with non-zero code
- MCP errors: Return structured error in response dict, never raise unhandled exceptions
- All errors must include: what failed, why it failed, and how to fix it

```json
{
  "status": "error",
  "errors": ["No steering templates found. Run 'hiveforge steering init' first."],
  "message": "Validation failed: steering directory not found"
}
```

## Authentication
- No authentication required — HiveForge operates on local filesystem only
- MCP server runs in-process within KIRO IDE; no network exposure
- LLM API keys are read from environment variables, never hardcoded or logged

## Rate Limiting
- No rate limiting on CLI or MCP interface
- LLM calls are subject to provider rate limits; handled via retry logic in `LLMProvider`
- Token budget enforced per-session via `token_budget.py` to prevent runaway LLM costs
