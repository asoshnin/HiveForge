---
inclusion: fileMatch
patterns: ["hiveforge/**/cli.py", "hiveforge/**/mcp_server.py"]
priority: 2
description: "CLI and terminal output standards. HiveForge has no web UI — this covers terminal UX conventions."
---

# CLI & Terminal Output Standards

## Overview
HiveForge has no web frontend. "UI" means the terminal interface (CLI) and the KIRO IDE panel (MCP). These standards ensure consistent, readable, and actionable terminal output.

## Component Patterns

### CLI Commands (Typer)
- One command group per domain: `hiveforge steering <subcommand>`
- Each subcommand is a single function with typed parameters
- Use `typer.Option` with `help=` strings for all options
- Use `typer.Argument` only for required positional inputs
- Always provide `--help` documentation

### Progress Display
Use consistent emoji prefixes for output sections:
- `🔧` Setup/configuration steps
- `🔍` Analysis steps
- `📄` File parsing steps
- `🧠` Knowledge/AI processing steps
- `📊` Analysis results
- `📝` Generation steps
- `💾` File writing steps
- `✅` Success
- `⚠️` Warning
- `✗` Error/failure

### Progress Indicators
```python
# Per-item progress: [current/total] item... ✓ or ✗
print(f"   [{idx}/{total}] Processing {filename}...", end=" ")
print("✓")  # or print(f"✗ (error: {msg})")

# Section headers: separator line + title
print("\n" + "="*70)
print("SECTION TITLE")
print("="*70)
```

## Styling Guidelines

### Output Formatting
- Indent nested items with 3 spaces (`   `)
- Use bullet points (`•`) for list items in terminal output
- Separate major sections with `="*70` dividers
- Keep lines under 100 characters
- Never use ANSI color codes directly — use `colorama` if color is needed

### Verbosity
- Default output: progress + summary only
- Errors always shown regardless of verbosity
- Debug output: use Python `logging` module, not `print()`
- Never print raw stack traces to users — catch and format

### Interactive Prompts
- Always show the question clearly before the input prompt
- Provide context for why the question is being asked
- Accept `y/n` for boolean confirmations (case-insensitive)
- Provide a default value where sensible: `(y/n) [y]:`
- Validate input and re-prompt on invalid responses — never crash

## Accessibility
- All output must be readable in plain text (no color-only information)
- Error messages must be self-contained — no "see above" references
- Progress indicators must work in non-TTY environments (CI/CD pipelines)
- Avoid Unicode characters that may not render in all terminals; use ASCII fallbacks

## MCP Tool Output
- Return structured dicts, never raw strings
- Include both machine-readable `status` and human-readable `message`
- List all created/modified/deleted files explicitly
- Warnings and errors in separate arrays for IDE display