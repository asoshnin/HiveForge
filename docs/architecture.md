# 🏗️ Architecture

This document explains the internal architecture of **hiveforge** and how it works.

---

## Overview

hiveforge is a **CLI scaffolding tool** that generates KIRO Methodology v05 project structures. It's designed to be simple, fast, and reliable.

```
┌─────────────┐
│   CLI       │  User runs: hiveforge -n my-project
│  (cli.py)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Validators  │  Validates project name (kebab-case)
│(validators) │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Generator  │  Creates directories, copies templates
│(generator)  │  Replaces placeholders in swarm_state.md
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Templates  │  Static .md files for agents & steering
│ (templates/)│
└─────────────┘
```

---

## Project Structure

```
hiveforge/
├── src/hiveforge/
│   ├── __init__.py          # Package metadata (__version__)
│   ├── cli.py               # CLI entry point (Typer app)
│   ├── validators.py        # Input validation (kebab-case)
│   ├── generator.py         # Project scaffolding logic
│   └── templates/           # Static template files
│       ├── agents/          # 7 agent definition files
│       ├── steering/        # 8 steering files
│       └── swarm_state.md   # Swarm state template
├── tests/                   # Test suite (66 tests)
│   ├── conftest.py          # Shared fixtures
│   ├── test_validators.py   # Validator tests
│   ├── test_generator.py    # Generator tests
│   ├── test_cli.py          # CLI tests
│   ├── test_generator_advanced.py
│   └── test_cli_advanced.py
├── docs/                    # Documentation
├── pyproject.toml           # Poetry configuration
├── README.md                # Main documentation
└── CHANGELOG.md             # Version history
```

---

## Module Breakdown

### 1. `cli.py` - Command Line Interface

**Responsibility:** Parse command-line arguments and orchestrate the workflow.

**Key Functions:**
- `main()` - Entry point decorated with `@app.command()`
- Accepts `--project-name` and `--force` flags
- Handles exceptions and displays user-friendly error messages

**Dependencies:**
- `typer` - CLI framework
- `validators.validate_project_name()`
- `generator.generate_project()`

**Example Flow:**
```python
@app.command()
def main(project_name: Optional[str], force: bool):
    try:
        if not project_name:
            project_name = Path.cwd().name  # Use current dir name
        project_name = validate_project_name(project_name)
        generate_project(project_name, force=force)
    except ValueError as e:
        typer.secho(f"❌ {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
```

---

### 2. `validators.py` - Input Validation

**Responsibility:** Validate user input (project names).

**Key Functions:**
- `validate_project_name(name: Optional[str]) -> str`

**Validation Rules:**
- Must not be empty
- Must match regex: `^[a-z0-9]+(-[a-z0-9]+)*$`
- Allows: `my-project`, `app-123`, `project`
- Rejects: `My Project`, `my_project`, `MyProject`

**Example:**
```python
def validate_project_name(name: Optional[str]) -> str:
    if not name:
        raise ValueError("Project name cannot be empty")
    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
        raise ValueError(f"Invalid: '{name}'. Use kebab-case (e.g., 'my-project')")
    return name
```

---

### 3. `generator.py` - Project Scaffolding

**Responsibility:** Create directories, copy templates, replace placeholders.

**Key Functions:**
- `generate_project(project_name: str, force: bool = False) -> None`

**Workflow:**

1. **Check for existing project:**
   ```python
   if kiro_dir.exists() and not force:
       raise FileExistsError(".kiro/ exists. Use --force to overwrite.")
   ```

2. **Create directories:**
   ```python
   (kiro_dir / "agents").mkdir(parents=True, exist_ok=True)
   (kiro_dir / "steering").mkdir(parents=True, exist_ok=True)
   (cwd / ".swarm" / "plan").mkdir(parents=True, exist_ok=True)
   (cwd / ".swarm" / "audit_logs").mkdir(parents=True, exist_ok=True)
   ```

3. **Copy agent templates:**
   ```python
   for f in (template_dir / "agents").glob("*.md"):
       (kiro_dir / "agents" / f.name).write_text(
           f.read_text(encoding="utf-8"), 
           encoding="utf-8"
       )
   ```

4. **Copy steering templates:**
   ```python
   for f in (template_dir / "steering").glob("*.md"):
       (kiro_dir / "steering" / f.name).write_text(
           f.read_text(encoding="utf-8"), 
           encoding="utf-8"
       )
   ```

5. **Process swarm_state.md:**
   ```python
   swarm = swarm_template.read_text(encoding="utf-8")
   swarm = swarm.replace("{PROJECT_NAME}", project_name)
   swarm = swarm.replace("{ISO_TIMESTAMP}", datetime.utcnow().isoformat() + "Z")
   (cwd / "swarm_state.md").write_text(swarm, encoding="utf-8")
   ```

---

### 4. `templates/` - Static Files

**Responsibility:** Store agent definitions, steering files, and swarm state template.

**Structure:**
```
templates/
├── agents/
│   ├── orchestrator.md       # Delegation & planning
│   ├── data_architect.md     # Database design
│   ├── backend_engineer.md   # API implementation
│   ├── frontend_engineer.md  # UI/UX
│   ├── qa_engineer.md        # Testing
│   ├── devops_engineer.md    # Infrastructure
│   └── red_team.md           # Security audits
├── steering/
│   ├── project-vision.md     # Goals & objectives
│   ├── tech-stack.md         # Technology choices
│   ├── conventions.md        # Code style
│   ├── architecture.md       # System design
│   ├── db-standards.md       # Database patterns
│   ├── api-standards.md      # API design
│   ├── ui-standards.md       # UI guidelines
│   └── qa-standards.md       # Testing strategy
└── swarm_state.md            # Central state document
```

**Why Static Templates?**
- **Simplicity:** No templating engine needed (Jinja2, etc.)
- **Maintainability:** Easy to edit and version control
- **Performance:** Fast file copying
- **Reliability:** No runtime template errors

---

## Design Decisions

### 1. Static Templates vs. Jinja2

**Decision:** Use static `.md` files with simple string replacement.

**Rationale:**
- Reduces dependencies
- Easier to maintain
- Faster execution
- Only 2 placeholders needed (`{PROJECT_NAME}`, `{ISO_TIMESTAMP}`)

**Trade-off:** Less flexible for complex templating, but sufficient for MVP.

---

### 2. Typer vs. Click vs. argparse

**Decision:** Use Typer for CLI framework.

**Rationale:**
- Modern, type-safe API
- Automatic help generation
- Built on Click (battle-tested)
- Excellent error messages

---

### 3. Poetry vs. pip

**Decision:** Use Poetry for dependency management.

**Rationale:**
- Deterministic builds (`poetry.lock`)
- Better dependency resolution
- Built-in virtual environment management
- Easy PyPI publishing

---

### 4. No `--tech-stack` Flag (MVP)

**Decision:** Omit tech-stack templates in v1.0.

**Rationale:**
- Reduces complexity for MVP
- Users can manually edit steering files
- Can be added in v2.0 without breaking changes

---

## Security Considerations

### 1. toolsSettings Enforcement

Agent definitions include `toolsSettings` to enforce role boundaries:

```yaml
toolsSettings:
  write:
    allowedPaths: ["./docs/**", "./swarm_state.md", "./.kiro/steering/**"]
    deniedPaths: ["./src/**", "./tests/**", "./infra/**"]
```

**Why?** Prevents Orchestrator from accidentally modifying source code.

### 2. Input Validation

All user input is validated before use:
- Project names must match kebab-case regex
- No path traversal attacks (e.g., `../../etc/passwd`)

### 3. UTF-8 Encoding

All files use UTF-8 encoding to prevent encoding-related vulnerabilities.

---

## Performance Characteristics

### Benchmarks

- **Project generation:** <1 second (typical)
- **File operations:** 15 files copied (7 agents + 8 steering)
- **Memory usage:** <50 MB
- **Disk usage:** ~200 KB per project

### Optimization Opportunities

1. **Parallel file copying** - Could use `concurrent.futures` for large template sets
2. **Template caching** - Cache parsed templates in memory (not needed for current scale)
3. **Lazy loading** - Only load templates when needed (not needed for current scale)

**Decision:** No optimization needed for MVP. Current performance is excellent.

---

## Error Handling

### Error Types

1. **ValueError** - Invalid project name
2. **FileExistsError** - Project already exists (without `--force`)
3. **FileNotFoundError** - Missing template files
4. **RuntimeError** - Empty template directories

### Error Flow

```
User Input
    ↓
Validation (ValueError)
    ↓
Duplicate Check (FileExistsError)
    ↓
Template Validation (FileNotFoundError, RuntimeError)
    ↓
File Generation
    ↓
Success Message
```

---

## Testing Strategy

### Test Coverage

- **Unit Tests:** `validators.py`, `generator.py` (isolated functions)
- **Integration Tests:** `cli.py` (end-to-end workflows)
- **Content Validation:** Verify generated files have correct structure
- **Edge Cases:** Long names, numbers, UTF-8, multiple projects

### Test Fixtures

```python
@pytest.fixture
def sample_project_name():
    return "test-project"

@pytest.fixture
def expected_agent_files():
    return ["orchestrator.md", "data_architect.md", ...]
```

### Coverage Target

- **Minimum:** 80%
- **Current:** 87%
- **Uncovered:** Defensive error paths (missing templates, unexpected exceptions)

---

## Future Architecture

### Planned Enhancements

1. **Tech-Stack Templates** - Multiple template variants (FastAPI, Django, React, etc.)
2. **Plugin System** - Allow custom templates via plugins
3. **IDE-Agnostic Mode** - Generate projects without Kiro-specific features
4. **Configuration File** - `.hiveforge.yaml` for project defaults

### Architectural Considerations

- **Backward Compatibility:** New features must not break existing projects
- **Extensibility:** Plugin system should be simple and well-documented
- **Performance:** Keep generation time <5 seconds even with 100+ templates

---

## Conclusion

hiveforge's architecture is intentionally simple:
- **4 core modules** (cli, validators, generator, templates)
- **Static templates** (no complex templating engine)
- **Minimal dependencies** (typer, pathlib, datetime)
- **Fast execution** (<1 second)
- **High reliability** (87% test coverage)

This simplicity makes it easy to understand, maintain, and extend.
