# 🏗️ Architecture

This document explains the internal architecture of **hiveforge** and how it works.

---

## Overview

hiveforge is a **CLI scaffolding tool** that generates KIRO Methodology v05 project structures and provides an AI-powered **Steering Assistant** to create and maintain steering files throughout your project lifecycle. It's designed to be simple, fast, and reliable.

### Core Architecture

```
┌─────────────┐
│   CLI       │  User runs: hiveforge -n my-project
│  (cli.py)   │            hiveforge steering init
└──────┬──────┘
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌─────────────┐                    ┌──────────────────┐
│ Validators  │  Kebab-case        │ Steering         │
│(validators) │  validation        │ Assistant        │
└──────┬──────┘                    │ (steering/)      │
       │                           └────────┬─────────┘
       ▼                                    │
┌─────────────┐                            │
│  Generator  │  Creates dirs,             │
│(generator)  │  copies templates          │
└──────┬──────┘                            │
       │                                   │
       ▼                                   ▼
┌─────────────┐                    ┌──────────────────┐
│  Templates  │  Static .md        │ Workflows        │
│ (templates/)│  files             │ Init/Update/     │
└─────────────┘                    │ Validate         │
                                   └──────────────────┘
```

### Steering Assistant Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Steering Assistant                   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  Document   │  │     Code     │  │ Knowledge  │ │
│  │  Parsers    │  │   Analyzers  │  │    Base    │ │
│  │ (MD/PDF/IMG)│  │ (Lang/Stack) │  │            │ │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘ │
│         │                │                 │        │
│         └────────────────┴─────────────────┘        │
│                          │                          │
│                          ▼                          │
│                 ┌────────────────┐                  │
│                 │ Gap Analysis   │                  │
│                 │    Engine      │                  │
│                 └────────┬───────┘                  │
│                          │                          │
│                          ▼                          │
│                 ┌────────────────┐                  │
│                 │ Conversation   │                  │
│                 │  Orchestrator  │                  │
│                 └────────┬───────┘                  │
│                          │                          │
│                          ▼                          │
│         ┌────────────────┴────────────────┐        │
│         │                                  │        │
│         ▼                                  ▼        │
│  ┌─────────────┐                  ┌──────────────┐ │
│  │  Template   │                  │  Validator   │ │
│  │  Populator  │                  │              │ │
│  └─────────────┘                  └──────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure

```
hiveforge/
├── src/hiveforge/
│   ├── __init__.py          # Package metadata (__version__)
│   ├── cli.py               # Main CLI entry point (Typer app)
│   ├── validators.py        # Input validation (kebab-case)
│   ├── generator.py         # Project scaffolding logic
│   ├── steering/            # Steering Assistant feature
│   │   ├── cli.py           # Steering CLI commands
│   │   ├── models.py        # Data models (SteeringConfig, etc.)
│   │   ├── parsers/         # Document parsers (MD, PDF, image)
│   │   ├── analyzers/       # Code analyzers (language, tech stack, etc.)
│   │   ├── agents/          # AI agents (SteeringAssistant)
│   │   ├── workflows/       # Workflow orchestrators (Init, Update, Validate)
│   │   ├── validators/      # Steering file validators
│   │   ├── knowledge_base.py
│   │   ├── gap_analysis.py
│   │   ├── template_populator.py
│   │   ├── diff_generator.py
│   │   ├── conflict_resolver.py
│   │   ├── customization_detector.py
│   │   ├── response_cache.py
│   │   ├── error_handling.py
│   │   └── templates.py
│   └── templates/           # Static template files
│       ├── agents/          # 7 agent definition files
│       ├── steering/        # 8 steering file templates
│       └── swarm_state.md   # Swarm state template
├── tests/                   # Test suite (863 tests)
│   ├── conftest.py          # Shared fixtures
│   ├── test_validators.py   # Validator tests
│   ├── test_generator.py    # Generator tests
│   ├── test_cli.py          # Main CLI tests
│   ├── test_steering_cli.py # Steering CLI tests
│   ├── test_*_workflow.py   # Workflow tests
│   ├── test_*_analyzer.py   # Code analyzer tests
│   └── ...                  # 40+ test files
├── docs/                    # Documentation
│   ├── architecture.md      # This file
│   ├── development.md       # Development guide
│   ├── troubleshooting.md   # Troubleshooting guide
│   └── steering-assistant-guide.md  # Steering Assistant user guide
├── .kiro/agents/            # Agent definitions
│   ├── steering-assistant.md
│   └── steering-validator.md
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


---

## Steering Assistant Architecture

The Steering Assistant is a comprehensive AI-powered system for creating and maintaining steering files.

### Component Overview

#### 1. Document Parsers (`steering/parsers/`)

**Responsibility:** Parse various document formats into structured data.

**Components:**
- `markdown.py` - Parse markdown files with UTF-8 encoding, preserve code blocks and Mermaid diagrams
- `pdf.py` - Extract text from PDFs with fallback encoding strategies
- `image.py` - OCR text extraction from images using pytesseract
- `orchestrator.py` - Coordinate parsing of all files in staging folder

**Key Features:**
- Multi-format support (MD, PDF, PNG, JPG)
- Error resilience (skip corrupted files, continue processing)
- Encoding fallback (UTF-8 → latin-1 → cp1252 → iso-8859-1)

#### 2. Code Analyzers (`steering/analyzers/`)

**Responsibility:** Analyze existing codebase to extract project information.

**Components:**
- `language_detector.py` - Detect languages and versions from file extensions and dependency files
- `tech_stack_extractor.py` - Extract frameworks, libraries, databases from package.json, requirements.txt, etc.
- `architecture_inferrer.py` - Infer architecture patterns (MVC, layered, microservices, etc.) from directory structure
- `conventions_extractor.py` - Extract naming patterns, indentation, docstring styles from code
- `documentation_parser.py` - Parse README files, docs folders, inline comments
- `code_analyzer.py` - Orchestrate all analysis modules

**Key Features:**
- Local analysis (no LLM calls)
- Confidence scoring (0.0-1.0)
- Sampling strategy for large codebases (>10k files)
- .gitignore respect using pathspec library
- Caching in `.kiro/.cache/code_analysis.json`

#### 3. Knowledge Base (`steering/knowledge_base.py`)

**Responsibility:** Store and retrieve gathered information.

**Key Features:**
- Initialize with parsed documents and code analysis results
- Search for content retrieval
- Token limiting (max 4000 tokens per query)
- Extract tech stack, conventions, architecture

#### 4. Gap Analysis Engine (`steering/gap_analysis.py`)

**Responsibility:** Identify missing information by comparing knowledge base against template requirements.

**Key Features:**
- Classify sections as complete, missing, or ambiguous
- Generate prioritized list of questions
- Group questions by steering file
- Provide context for each question

#### 5. Steering Assistant Agent (`steering/agents/steering_assistant.py`)

**Responsibility:** Conduct conversations to gather missing information.

**Key Features:**
- Question batching (max 8 per batch)
- Token-efficient prompting (max 4000 tokens knowledge base content)
- Response caching to avoid redundant API calls
- Optional web research (when --research flag enabled)
- Interactive vs non-interactive modes

#### 6. Template Populator (`steering/template_populator.py`)

**Responsibility:** Populate steering file templates with gathered information.

**Key Features:**
- Load template definitions for all 8 steering files
- Replace placeholders with contextually appropriate content
- Preserve frontmatter
- Generate token-efficient summaries (max 2000 tokens per template)

#### 7. Validators (`steering/validators/`)

**Responsibility:** Validate steering files for completeness and consistency.

**Components:**
- `rule_based.py` - Rule-based validation functions (completeness, structure, consistency)
- `steering_validator.py` - Orchestrate validation, generate reports

**Key Features:**
- Detect unreplaced placeholders
- Verify frontmatter and template structure
- Check cross-file consistency
- Optional semantic validation using LLM (max 1000 tokens per check)
- Validation result caching

#### 8. Workflows (`steering/workflows/`)

**Responsibility:** Orchestrate end-to-end workflows.

**Components:**
- `init_workflow.py` - Create steering files from scratch
- `update_workflow.py` - Update existing steering files
- `validate_workflow.py` - Validate steering files

**Init Workflow Steps:**
1. Create staging directory
2. Optionally analyze code
3. Parse artifacts
4. Build knowledge base
5. Run gap analysis
6. Conduct conversation
7. Populate templates
8. Write files
9. Run validation

**Update Workflow Steps:**
1. Verify files exist
2. Parse existing files
3. Parse new artifacts
4. Detect customizations
5. Run gap analysis
6. Conduct conversation
7. Detect conflicts
8. Generate diffs
9. Get user approval
10. Apply changes
11. Run validation

**Validate Workflow Steps:**
1. Verify files exist
2. Run validator
3. Generate report
4. Display report
5. Return exit code

#### 9. Supporting Components

- `diff_generator.py` - Generate and format diffs using difflib and colorama
- `conflict_resolver.py` - Detect and resolve conflicts between old and new information
- `customization_detector.py` - Detect user customizations using diff comparison
- `response_cache.py` - Cache LLM responses to avoid redundant API calls
- `error_handling.py` - Centralized error handling with graceful degradation
- `templates.py` - Template definitions and metadata

### Data Flow

#### Init Workflow Data Flow

```
Artifacts (.kiro/onboarding/)
         │
         ▼
   Document Parsers ──────┐
         │                │
         ▼                │
Code Analyzer (optional)  │
         │                │
         ▼                │
   Knowledge Base ◄───────┘
         │
         ▼
   Gap Analysis Engine
         │
         ▼
   Steering Assistant
         │
         ▼
   Template Populator
         │
         ▼
   Steering Files (.kiro/steering/)
         │
         ▼
   Steering Validator
```

#### Update Workflow Data Flow

```
Existing Files + New Artifacts
         │
         ▼
   Document Parsers
         │
         ▼
   Knowledge Base
         │
         ▼
   Customization Detector
         │
         ▼
   Gap Analysis Engine
         │
         ▼
   Steering Assistant
         │
         ▼
   Conflict Resolver
         │
         ▼
   Diff Generator
         │
         ▼
   User Approval
         │
         ▼
   Apply Changes
         │
         ▼
   Steering Validator
```

### Token Efficiency Strategies

The Steering Assistant implements several strategies to minimize LLM API costs:

1. **Question Batching**: Max 8 questions per batch
2. **Knowledge Base Limiting**: Max 4000 tokens of context per prompt
3. **Template Summaries**: Max 2000 tokens per steering file
4. **Response Caching**: Avoid re-asking answered questions
5. **Incremental Updates**: Only send changed sections (max 3000 tokens per file)
6. **Local Analysis**: All code analysis runs locally without LLM calls

### Error Handling

The Steering Assistant implements comprehensive error handling:

**Error Categories:**
- File System Errors (missing directories, permissions, disk full)
- Parsing Errors (corrupted files, encoding issues)
- Code Analysis Errors (unrecognized languages, malformed files, timeouts)
- LLM API Errors (rate limiting, timeouts, invalid responses)

**Recovery Strategies:**
- Automatic directory creation
- Multiple encoding fallbacks
- Exponential backoff for rate limiting (2^retry_count seconds)
- Graceful degradation (continue with partial results)
- Detailed error reporting with actionable suggestions

### Performance Characteristics

**Benchmarks:**
- **Init without code analysis:** 10-30 seconds (depends on LLM API)
- **Init with code analysis:** 30-60 seconds (depends on codebase size)
- **Update:** 10-20 seconds (incremental)
- **Validate:** <1 second (rule-based only)
- **Code analysis:** 5-15 seconds for typical projects (<1000 files)

**Caching:**
- Response cache: `.kiro/.cache/response_cache.json`
- Code analysis cache: `.kiro/.cache/code_analysis.json`
- Validation cache: `.kiro/.cache/validation_cache.json`

### Security Considerations

1. **Input Validation**: All user input validated before processing
2. **Path Traversal Prevention**: File paths validated to prevent directory traversal
3. **UTF-8 Encoding**: All files use UTF-8 to prevent encoding vulnerabilities
4. **LLM Prompt Injection**: User input sanitized before sending to LLM
5. **Token Limiting**: Hard limits on token usage to prevent excessive API costs

### Testing Strategy

**Test Coverage:**
- 863 total tests
- 835+ passing (97% pass rate)
- Unit tests for all components
- Integration tests for workflows
- Error handling tests for all error categories

**Test Organization:**
- `test_*_parser.py` - Parser tests
- `test_*_analyzer.py` - Code analyzer tests
- `test_*_workflow.py` - Workflow tests
- `test_steering_cli.py` - CLI tests
- `test_cli_integration.py` - Integration tests
- `test_error_handling.py` - Error handling tests

---

## Design Decisions (Updated)

### 5. Steering Assistant Architecture

**Decision:** Modular architecture with clear separation of concerns.

**Rationale:**
- Each component has single responsibility
- Easy to test and maintain
- Extensible for future features
- Reusable components

**Trade-off:** More files and complexity, but better maintainability.

### 6. Local Code Analysis

**Decision:** Perform all code analysis locally without LLM calls.

**Rationale:**
- Reduces API costs
- Faster execution
- No privacy concerns
- Deterministic results

**Trade-off:** Less sophisticated analysis, but sufficient for most projects.

### 7. Token Limiting

**Decision:** Implement hard limits on token usage.

**Rationale:**
- Prevents excessive API costs
- Forces efficient prompting
- Predictable performance

**Trade-off:** May require multiple API calls for complex projects.

### 8. Response Caching

**Decision:** Cache LLM responses by question hash.

**Rationale:**
- Avoids redundant API calls
- Faster responses
- Consistent answers
- Reduces costs

**Trade-off:** Cache invalidation complexity, but manageable.

---

## Future Architecture (Updated)

### Planned Enhancements

1. **Semantic Code Analysis** - Use LLM for deeper code understanding (optional, token-limited)
2. **Multi-Language Support** - Support for non-English documentation
3. **Custom Templates** - Allow users to define custom steering file templates
4. **Plugin System** - Allow custom analyzers and validators
5. **Collaborative Editing** - Support for team-based steering file maintenance
6. **Version Control Integration** - Track steering file changes in git
7. **CI/CD Integration** - Automated validation in pipelines

### Architectural Considerations

- **Backward Compatibility:** New features must not break existing workflows
- **Extensibility:** Plugin system should be simple and well-documented
- **Performance:** Keep workflows under 60 seconds even with large codebases
- **Token Efficiency:** Maintain token limits to control API costs
- **Error Resilience:** Continue to handle errors gracefully

---

## Conclusion (Updated)

hiveforge's architecture has evolved from a simple scaffolding tool to a comprehensive project documentation system:

**Core Features:**
- **4 core modules** (cli, validators, generator, templates) - Original scaffolding
- **Steering Assistant** (40+ modules) - AI-powered documentation system
- **863 tests** (97% pass rate) - Comprehensive test coverage
- **Token-efficient** (<10K tokens per workflow) - Cost-effective LLM usage
- **Error-resilient** (graceful degradation) - Handles failures gracefully

This architecture balances simplicity with power, making it easy to use while providing sophisticated documentation capabilities.
