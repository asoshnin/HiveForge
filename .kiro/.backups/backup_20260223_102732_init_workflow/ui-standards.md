---
inclusion: fileMatch
patterns: ["src/**/cli.py", "src/**/workflows/**", "hiveforge-power/**"]
priority: 2
description: "CLI interface design, output formatting, user experience. Loaded when working on CLI or Power interface."
---

# CLI & Interface Standards

## CLI Design Principles

### User Experience
1. **Intuitive Commands:** Use clear, action-oriented verbs (init, update, validate)
2. **Sensible Defaults:** Minimize required flags, provide good defaults
3. **Progressive Disclosure:** Show basic info by default, verbose with `-v`
4. **Fail Fast:** Validate inputs early, provide clear error messages
5. **Idempotent Operations:** Safe to run multiple times (with --force)

### Command Structure
```bash
hiveforge [OPTIONS] COMMAND [ARGS]

# Main commands
hiveforge -n my-project              # Initialize project
hiveforge steering init              # Create steering files
hiveforge steering update            # Update steering files
hiveforge steering validate          # Validate steering files
```

## Output Formatting

### Success Messages
```bash
✅ Project 'my-project' created successfully
✅ 8 steering files generated
✅ Validation passed
```

### Info Messages
```bash
ℹ️  Current branch: main
ℹ️  Staging folder is empty - will proceed with conversation-only mode
ℹ️  Checking if we need to push...
```

### Warning Messages
```bash
⚠️  WARNING: Existing steering files detected!
⚠️  No source documents found in .kiro/onboarding/
⚠️  Low confidence: mostly inferred content
```

### Error Messages
```bash
❌ Not a git repository. Aborting.
❌ Validation failed with 80 critical issue(s)
❌ Push failed!
```

### Progress Indicators
```bash
🔧 Setting up staging directory...
   ✓ Staging directory ready
🔍 Analyzing codebase...
   [1/8] Checking api-standards.md... ✓
   [2/8] Checking architecture.md... ✗ (8 critical, 8 warnings)
```

## Color Scheme

### Typer Colors
```python
# Success (green)
typer.secho("✅ Success", fg=typer.colors.GREEN)

# Info (cyan)
typer.secho("ℹ️  Info", fg=typer.colors.CYAN)

# Warning (yellow)
typer.secho("⚠️  Warning", fg=typer.colors.YELLOW)

# Error (red)
typer.secho("❌ Error", fg=typer.colors.RED, err=True)

# Dim (for less important info)
typer.secho("Details...", fg=typer.colors.BRIGHT_BLACK)
```

### ANSI Escape Codes (for non-Typer output)
```python
# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Usage
print(f"{GREEN}✅ Success{RESET}")
```

## Interactive Prompts

### Confirmation Prompts
```python
# Yes/No confirmation
response = typer.confirm("Proceed with commit and push?")

# With default
response = typer.confirm("Continue anyway?", default=False)

# Custom prompt
response = input("Choose option (1 or 2): ")
```

### Input Prompts
```python
# Simple input
name = typer.prompt("Project name")

# With default
name = typer.prompt("Project name", default="my-project")

# With validation
name = typer.prompt("Project name", value_proc=validate_project_name)
```

### Choice Prompts
```python
# Multiple choice
choice = typer.prompt(
    "Which value should we use?",
    type=typer.Choice(["1", "2", "3"])
)
```

## Help Text

### Command Help
```python
@app.command()
def init(
    project_name: Optional[str] = typer.Option(
        None,
        "--project-name", "-n",
        help="Project name (kebab-case)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing project"
    )
):
    """
    Initialize KIRO v05 project (7 agents, 8 steering files, swarm_state.md)
    
    Examples:
        hiveforge -n my-project
        hiveforge -n my-project --force
    """
    pass
```

### Auto-Generated Help
```bash
$ hiveforge --help

Usage: hiveforge [OPTIONS] COMMAND [ARGS]...

  Scaffold KIRO v05 projects

Options:
  --help  Show this message and exit.

Commands:
  main      Initialize KIRO v05 project
  steering  Manage steering files
```

## Error Handling

### User-Friendly Errors
```python
# Bad
raise ValueError("Invalid input")

# Good
typer.secho(
    "❌ Invalid project name: 'My Project'",
    fg=typer.colors.RED,
    err=True
)
typer.secho(
    "   Use kebab-case (e.g., 'my-project')",
    fg=typer.colors.YELLOW,
    err=True
)
raise typer.Exit(code=1)
```

### Error Context
```python
# Provide context and suggestions
try:
    validate_project_name(name)
except ValueError as e:
    typer.secho(f"❌ {e}", fg=typer.colors.RED, err=True)
    typer.secho(
        "   Valid examples: my-project, awesome-app, project-123",
        fg=typer.colors.CYAN
    )
    raise typer.Exit(code=1)
```

## Validation Reports

### Structured Output
```bash
======================================================================
VALIDATION REPORT
======================================================================

📊 Summary:
   • Files checked: 8
   • Critical issues: 80
   • Warnings: 92
   • Info messages: 1
   • Overall status: FAIL

❌ Critical Issues:

   [incomplete_section] api-standards.md:12
   Section 'API Design Principles' contains unreplaced placeholder: {id}
   💡 Suggestion: Replace the placeholder with actual content

⚠️  Warnings:

   [incomplete_section] architecture.md:31
   Section 'Data Flow' contains unreplaced placeholder: {Step 1}
   💡 Suggestion: Replace the placeholder with actual content

======================================================================
❌ Validation failed - fix critical issues and re-run
======================================================================
```

## MCP Power Interface

### Natural Language Responses
```
"I've initialized steering files for your project. Here's what I created:

✅ 5 steering files generated:
   • tech-stack.md
   • architecture.md
   • conventions.md
   • project-vision.md
   • qa-standards.md

⚠️  Note: No source documents found in .kiro/onboarding/
   Content was inferred from code analysis with medium confidence.

You can review the files in .kiro/steering/ and update them as needed."
```

### Structured Responses
```json
{
  "status": "success",
  "message": "Successfully initialized steering files (5 files created)",
  "files_created": [
    ".kiro/steering/tech-stack.md",
    ".kiro/steering/architecture.md"
  ],
  "warnings": ["No source documents found"],
  "confidence_level": "medium"
}
```

## Accessibility

### Screen Reader Support
- Use descriptive text, not just icons
- Provide alternative text for symbols
- Structure output hierarchically

### Color Blindness
- Don't rely solely on color for meaning
- Use symbols in addition to colors (✅ ❌ ⚠️)
- Provide text descriptions

### Terminal Compatibility
- Detect terminal capabilities
- Fallback to plain text if colors not supported
- Test on multiple terminals (bash, zsh, PowerShell)

## Performance Feedback

### Long-Running Operations
```python
# Show progress
with typer.progressbar(files, label="Processing files") as progress:
    for file in progress:
        process_file(file)

# Show spinner (for indeterminate operations)
with console.status("[bold green]Analyzing codebase..."):
    result = analyze_code()
```

### Time Estimates
```bash
🔍 Analyzing codebase... (this may take 30-60 seconds)
⏱️  Estimated time: 15 seconds
```

## Logging

### Log Levels
```python
import logging

# Debug (verbose mode only)
logging.debug("Parsing file: %s", file_path)

# Info (default)
logging.info("Staging directory ready")

# Warning (always shown)
logging.warning("No source documents found")

# Error (always shown)
logging.error("Validation failed")
```

### Log Format
```python
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# Verbose mode
if verbose:
    logging.getLogger().setLevel(logging.DEBUG)
```

## Documentation

### Inline Examples
```bash
# Show examples in help text
hiveforge steering init --help

Examples:
    # Basic init with conversation
    hiveforge steering init
    
    # Import existing codebase
    hiveforge steering init --analyze-code
    
    # Non-interactive mode
    hiveforge steering init --no-interactive
```

### Quick Start Guide
- Provide QUICKSTART.md with 5-minute walkthrough
- Include common workflows
- Show expected output
- Link to detailed documentation

## Testing CLI Interface

### Test Output
```python
def test_cli_success_message(cli_runner):
    """Test success message formatting."""
    result = cli_runner.invoke(app, ["-n", "test-project"])
    
    assert result.exit_code == 0
    assert "✅" in result.output
    assert "created successfully" in result.output
```

### Test Error Messages
```python
def test_cli_error_message(cli_runner):
    """Test error message formatting."""
    result = cli_runner.invoke(app, ["-n", "My Project"])
    
    assert result.exit_code == 1
    assert "❌" in result.output
    assert "kebab-case" in result.output
```

## Best Practices

### Do's
- ✅ Use consistent formatting across all commands
- ✅ Provide clear, actionable error messages
- ✅ Show progress for long-running operations
- ✅ Use colors and symbols for visual hierarchy
- ✅ Test CLI output in automated tests

### Don'ts
- ❌ Don't use technical jargon in user-facing messages
- ❌ Don't show stack traces to users (log them instead)
- ❌ Don't use ambiguous language ("maybe", "possibly")
- ❌ Don't rely solely on color for meaning
- ❌ Don't block without showing progress
