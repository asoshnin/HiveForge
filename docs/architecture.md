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

### Steering Assistant Architecture (v3.0.0 - LLM-Primary Synthesis)

```
┌──────────────────────────────────────────────────────┐
│            Steering Assistant (v3.0.0)                │
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
│                 │ Use Case       │                  │
│                 │ Determination  │                  │
│                 └────────┬───────┘                  │
│                          │                          │
│         ┌────────────────┴────────────────┐        │
│         │                                  │        │
│         ▼                                  ▼        │
│  ┌─────────────┐                  ┌──────────────┐ │
│  │ new_from_   │                  │ reverse_     │ │
│  │ docs        │                  │ engineer     │ │
│  └──────┬──────┘                  └──────┬───────┘ │
│         │                                 │        │
│         └────────────────┬────────────────┘        │
│                          │                          │
│                          ▼                          │
│                 ┌────────────────┐                  │
│                 │ Context        │                  │
│                 │ Assembler      │                  │
│                 │ (Token Budget) │                  │
│                 └────────┬───────┘                  │
│                          │                          │
│                          ▼                          │
│                 ┌────────────────┐                  │
│                 │ LLM Synthesis  │                  │
│                 │ (8 templates)  │                  │
│                 └────────┬───────┘                  │
│                          │                          │
│                          ▼                          │
│                 ┌────────────────┐                  │
│                 │ Hallucination  │                  │
│                 │ Detection      │                  │
│                 └────────┬───────┘                  │
│                          │                          │
│                          ▼                          │
│                 ┌────────────────┐                  │
│                 │ Draft State    │                  │
│                 │ (Review)       │                  │
│                 └────────┬───────┘                  │
│                          │                          │
│         ┌────────────────┴────────────────┐        │
│         │                                  │        │
│         ▼                                  ▼        │
│  ┌─────────────┐                  ┌──────────────┐ │
│  │ Write Files │                  │  Validator   │ │
│  │ (Atomic)    │                  │              │ │
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
│   ├── steering_assistant.md
│   └── steering_validator.md
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

### v3.0.0 LLM-Primary Synthesis Pipeline

The v3.0.0 release introduced a fundamental architectural shift from template population to LLM-primary synthesis.

**Key Changes:**
- **Direct LLM Generation**: Steering files generated by LLM synthesis (one call per template) instead of template population with Q&A
- **Use Case Determination**: Automatic detection of `new_from_docs` vs `reverse_engineer` workflows
- **Context Assembly**: Intelligent context building with token budgets and keyword-based relevance filtering
- **Hallucination Detection**: Duplicate paragraph detection prevents LLM from repeating content
- **Draft Review**: Generated files stored for review before writing to disk
- **Atomic Transactions**: All 8 files written or none (rollback on failure)

**Architecture Flow:**

```
Source Documents + Code Analysis
         │
         ▼
   Use Case Determination
         │
         ├─► new_from_docs (has source documents)
         └─► reverse_engineer (no source documents)
         │
         ▼
   Context Assembler
   (Token Budget: 4000 tokens)
         │
         ├─► 50% Source Documents (keyword filtered)
         ├─► 25% Code Analysis Facts
         ├─► 15% Template Structure
         └─► 10% Buffer
         │
         ▼
   LLM Synthesis (8 calls)
   (One per template)
         │
         ▼
   Hallucination Detection
   (Duplicate paragraph check)
         │
         ▼
   Draft State
   (Review before writing)
         │
         ├─► CLI: Interactive approval
         └─► MCP: Deferred writing
         │
         ▼
   Atomic Write
   (All 8 files or rollback)
```

**Component Responsibilities:**

#### Use Case Determiner
- **Input**: Source documents count, code analysis results
- **Output**: `new_from_docs` or `reverse_engineer`
- **Logic**: If source documents > 0 → `new_from_docs`, else → `reverse_engineer`

#### Context Assembler
- **Input**: Knowledge base, template name
- **Output**: Context dict with token-limited content
- **Token Budget**: 4000 tokens total
  - 50% (2000 tokens): Source documents (keyword filtered)
  - 25% (1000 tokens): Code analysis facts
  - 15% (600 tokens): Template structure
  - 10% (400 tokens): Buffer
- **Keyword Filtering**: Reduces irrelevant content by 30-50%

#### LLM Synthesis
- **Input**: Template + context
- **Output**: Populated markdown content
- **Behavior**:
  - Strips YAML frontmatter before LLM call
  - Single LLM call per template (8 total)
  - Retry once on empty/malformed response
  - No retry on hallucinations (reject and fail)
  - Falls back to `[INFERRED]` markers if LLM unavailable

#### Hallucination Detector
- **Input**: Generated content
- **Output**: Pass/fail validation
- **Detection**: Checks for duplicate paragraphs (3+ sentences repeated)
- **Action**: Rejects file if duplicates found, triggers atomic rollback

#### Draft State Manager
- **Input**: 8 generated files
- **Output**: DraftState with metadata
- **Metadata**:
  - Per-file confidence scores
  - Placeholder counts
  - Content previews (first 300 chars)
  - Generation timestamp
- **Review Modes**:
  - CLI: Interactive approval prompt
  - MCP: Stored for IDE review, written on explicit approval

#### Atomic Writer
- **Input**: Approved draft state
- **Output**: 8 files written or rollback
- **Behavior**:
  - Validates all 8 files before writing
  - Writes all files in single transaction
  - Rolls back on any failure
  - Creates backup before writing

### v2.2.0 Enhancements

The v2.2.0 release introduced significant improvements to the Steering Assistant:

#### LLM Provider Abstraction

**Priority-based provider routing:**
1. **KIRO Native** (primary in MCP mode) - Uses KIRO IDE's built-in LLM via `ctx.sample()`
2. **Google Vertex AI** - Google Cloud's AI platform
3. **OpenAI** - OpenAI's GPT models
4. **None** - Falls back to `[INFERRED]` markers

**Key Features:**
- Automatic provider selection based on context
- Graceful fallback chain on provider failure
- Configuration via environment variables or `~/.hiveforge/llm_config.json`
- Optional dependencies: `pip install hiveforge-steering-mcp[vertex]` or `[openai]`

#### Confidence Scoring System

Generated steering files include confidence metadata:

```yaml
---
confidence_level: medium
confidence_score: 0.65
source_documents_found: 3
inferred_sections: ["Rationale", "Trade-offs"]
---
```

**Confidence Levels:**
- **High (0.7-1.0)**: Most content from source documents, minimal inference
- **Medium (0.4-0.7)**: Mix of source documents and code analysis
- **Low (0.0-0.4)**: Mostly inferred from code, few source documents

**[INFERRED] Markers:**
Sections generated without source documents are marked:
```markdown
## Rationale [INFERRED]
{Why this stack? Trade-offs considered?}
```

#### Custom Source Document Paths

Users can specify custom locations for source documents:
```bash
hiveforge steering init --source-docs-path="docs/design"
```

**Default behavior**: Looks in `.kiro/onboarding/` directory
**Custom paths**: Any directory relative to project root

#### Dry-Run Mode

Preview what will be generated without creating files:
```bash
hiveforge steering init --dry-run
```

Returns preview of all files with metadata and confidence scores.

#### Draft Review Workflow

**In MCP mode (KIRO IDE):**
1. Generate files and create DraftState
2. Store draft in workflow state
3. Return draft summary in result metadata
4. User reviews draft in IDE
5. User calls `update_steering(apply_draft=True)` to write files

**In CLI mode:**
1. Generate files and create DraftState
2. Display draft summary
3. Prompt user for approval
4. Write files if approved

### Component Overview

#### 1. LLM Provider (`steering/llm/provider.py`)

**Responsibility:** Route LLM calls to available providers with automatic fallback.

**Components:**
- `LLMProvider` - Main provider abstraction
- `ProviderType` - Enum for provider types (KIRO_NATIVE, VERTEX_AI, OPENAI, NONE)
- `LLMConfig` - Configuration dataclass

**Key Features:**
- Priority-based routing (KIRO → Vertex → OpenAI → None)
- Async support for non-blocking calls
- Configuration loading from env vars and files
- Graceful fallback on provider failure

#### 2. Document Parsers (`steering/parsers/`)

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

#### 3. Code Analyzers (`steering/analyzers/`)

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

**v2.2.0 Enhancements:**
- `extract_public_api()` - Extracts MCP tools, CLI commands, and public classes
- `_heuristic_classify()` - Detects project type (CLI tool, MCP server, web app, library)
- Project type detection for template variant selection

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

#### 6. Steering Assistant Agent (`steering/agents/steering_assistant.py`)

**Responsibility:** Generate steering file content using LLM synthesis (v3.0.0).

**v3.0.0 Key Features:**
- `generate_file()` method - Generates individual steering files using LLM synthesis
- Single LLM call per template (8 total)
- Automatic frontmatter stripping before LLM calls
- `[INFERRED]` marker fallback when LLM unavailable
- Context tracking (last 3 generated files for consistency)
- Template variant resolution based on project type
- Retry logic: Single retry on empty/malformed response, no retry on hallucinations

**v2.x Legacy Features (deprecated in v3.0.0):**
- Question batching (max 8 per batch) - replaced by direct LLM synthesis
- Interactive Q&A mode - replaced by draft review workflow
- Optional web research (when --research flag enabled)

**Dependencies:** LLMProvider, response_cache

#### 7. Template Populator (`steering/template_populator.py`)

**Responsibility:** Populate steering file templates with gathered information.

**Status:** Deprecated in v3.0.0 (replaced by LLM synthesis in SteeringAssistant)

**Legacy Features (v2.x):**
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

#### 10. Drift Detection (`steering/detectors/drift_detector.py`)

**Responsibility:** Detect drift between steering files and codebase.

**Key Features:**
- Language version drift detection (tech-stack.md vs pyproject.toml)
- New dependency detection (filters to significant dependencies only)
- Architecture pattern drift detection
- Naming convention mismatch detection
- Confidence scoring for each drift item (0.0-1.0)

**Significant Dependencies:**
Only architecturally important dependencies are flagged:
- Frameworks: FastAPI, Flask, Django
- Databases: SQLAlchemy, Prisma, Redis
- Testing: pytest
- Data Science: NumPy, Pandas, PyTorch, TensorFlow

#### 11. v3.0.0 New Components

**ContextAssembler (`steering/context_assembler.py`):**
- Assembles context for LLM with token budgets and keyword filtering
- Token budget allocation: 50% source docs, 25% code facts, 15% templates, 10% buffer
- Keyword-based relevance filtering reduces input by 30-50%
- Template-specific context (each template gets relevant subset)

**UseCaseDeterminer (`steering/use_case_determiner.py`):**
- Determines workflow type: `new_from_docs` vs `reverse_engineer`
- Logic: source documents > 0 → `new_from_docs`, else → `reverse_engineer`
- Influences context assembly and LLM prompting strategy

**HallucinationDetector (`steering/hallucination_detector.py`):**
- Detects duplicate paragraphs in generated content
- Threshold: 3+ sentences repeated across files
- Action: Rejects file and triggers atomic rollback

**DraftStateManager (`steering/draft_state_manager.py`):**
- Manages draft state before writing files
- Stores per-file confidence scores, placeholder counts, previews
- Supports interactive review (CLI) and deferred writing (MCP)

**AtomicWriter (`steering/atomic_writer.py`):**
- Writes all 8 files in single transaction
- Validates all files before writing
- Rolls back on any failure
- Creates backup before writing

#### 12. Supporting Components

- `diff_generator.py` - Generate and format diffs using difflib and colorama
- `conflict_resolver.py` - Detect and resolve conflicts between old and new information
- `customization_detector.py` - Detect user customizations using diff comparison
- `response_cache.py` - Cache LLM responses to avoid redundant API calls
- `error_handling.py` - Centralized error handling with graceful degradation
- `templates.py` - Template definitions and metadata
- `content_tagger.py` - Tag content with [INFERRED] markers
- `confidence.py` - Calculate confidence scores
- `source_resolver.py` - Resolve custom source document paths

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

---

## v2.1.0 Shared Backend Architecture

The v2.1.0 release introduced a **Shared Backend Architecture** that unifies CLI and Power (MCP) implementations.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      KIRO Orchestrator                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                          ┌─────────────────┐ │
│  │    CLI       │                          │   Power (MCP)   │ │
│  │  Interface   │                          │   Interface     │ │
│  └──────┬───────┘                          └────────┬────────┘ │
│         │                                            │          │
│         └──────────────────┬─────────────────────────┘          │
│                            │                                      │
│                            ▼                                      │
│              ┌─────────────────────────────┐                     │
│              │   Shared Backend Adapters   │                     │
│              │   (src/hiveforge/steering/  │                     │
│              │    shared/)                 │                     │
│              └──────────────┬──────────────┘                     │
│                             │                                     │
│         ┌───────────────────┼───────────────────┐                │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Error     │    │  Security   │    │  Telemetry  │         │
│  │  Handling   │    │  Wrapper    │    │  Collector  │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                             │                                     │
│                             ▼                                     │
│              ┌─────────────────────────────┐                     │
│              │      v02 Workflows          │                     │
│              │  Init/Update/Validate/      │                     │
│              │  Reset/Discover             │                     │
│              └─────────────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Benefits

1. **Single Source of Truth**: Both CLI and Power use identical workflow logic
2. **Consistent Behavior**: Same features, same error handling, same output
3. **Easier Maintenance**: Bug fixes and features apply to both interfaces
4. **Reduced Duplication**: No separate implementations to maintain

---

### Error Handling with Automatic Rollback

The shared backend includes comprehensive error handling with automatic rollback.

#### Key Features

- **Automatic Backup Creation**: When workflows fail, backups are created automatically
- **Graceful Degradation**: Partial results are preserved even on failure
- **Detailed Error Context**: Every error includes category, severity, and suggestions
- **Retry Logic**: Transient failures are retried with exponential backoff

#### WorkflowResult Structure

```python
@dataclass
class WorkflowResult:
    success: bool                    # Whether the workflow succeeded
    files_created: List[Path]        # Files that were created
    files_modified: List[Path]       # Files that were modified
    errors: List[str]                # List of error messages
    warnings: List[str]              # List of warning messages
    metadata: Dict[str, Any]         # Additional metadata
    backup_location: Optional[Path]  # Path to backup (if created)
```

#### Rollback Process

```
Workflow Execution
        │
        ▼
   ┌─────────┐
   │ Success │────► Continue
   └────┬────┘
        │
   ┌────▼────┐
   │ Failure │────► Create Backup
   └────┬────┘              │
        │                  ▼
        │         ┌───────────────┐
        └────────►│ Rollback      │
                  │ (if needed)   │
                  └───────────────┘
```

---

### Security Wrapper

The security wrapper provides input validation, path sanitization, and resource limits.

#### Components

##### 1. Parameter Validation

```python
def validate_parameters(
    project_root: Optional[Path] = None,
    files_to_update: Optional[List[Path]] = None,
    confidence_threshold: float = 0.7
) -> ValidationResult:
    """Validate all input parameters before workflow execution."""
    # Validates project_root exists and is accessible
    # Validates files_to_update are within allowed paths
    # Validates confidence_threshold is in valid range [0.0, 1.0]
```

##### 2. Path Sanitization

```python
def sanitize_path(user_path: Path, base_path: Path) -> Path:
    """Sanitize user-provided paths to prevent path traversal."""
    # Rejects paths with ".." components
    # Resolves symlinks
    # Ensures result is within base_path
```

**Security Features:**
- Prevents path traversal attacks (e.g., `../../../etc/passwd`)
- Validates all file paths before access
- Logs suspicious access attempts

##### 3. Resource Limiter

```python
@dataclass
class ResourceLimiter:
    max_memory_mb: int = 512
    max_cpu_time_sec: int = 300
    max_file_size_mb: int = 100
    
    def __enter__(self):
        """Start monitoring resource usage."""
        
    def __exit__(self, *args):
        """Stop monitoring and cleanup."""
```

**Resource Limits:**
- Memory usage limit (default: 512 MB)
- CPU time limit (default: 300 seconds)
- Maximum file size for processing (default: 100 MB)

---

### Telemetry Collection

The telemetry collector tracks workflow execution for monitoring and optimization.

#### TelemetryCollector Class

```python
class TelemetryCollector:
    def __init__(self, telemetry_dir: Path):
        """Initialize telemetry collector."""
        self.telemetry_dir = telemetry_dir
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        
    def record_workflow_start(
        self,
        workflow_name: str,
        interface_type: InterfaceType,
        parameters: Dict[str, Any]
    ):
        """Record workflow start event."""
        
    def record_workflow_complete(
        self,
        workflow_name: str,
        success: bool,
        duration_ms: float,
        files_created: int,
        files_modified: int
    ):
        """Record workflow completion event."""
        
    def record_error(
        self,
        error_type: str,
        error_message: str,
        workflow_name: str
    ):
        """Record error event."""
```

#### Interface Types

```python
enum InterfaceType:
    CLI      # Command-line interface
    MCP      # Model Context Protocol (Power)
    API      # Direct API access
    TEST     # Test execution
```

#### Telemetry Data

**Workflow Events:**
- `workflow_start`: When a workflow begins execution
- `workflow_complete`: When a workflow finishes (success or failure)
- `workflow_error`: When an error occurs during execution

**Performance Metrics:**
- Duration (milliseconds)
- Files created/modified
- Memory usage
- CPU time

**Error Tracking:**
- Error type and message
- Error frequency
- Recovery success rate

#### Telemetry Files

Telemetry data is stored as JSON files in `.kiro/.telemetry/`:

```
.kiro/.telemetry/
├── workflow_start_2026-02-17T10-30-00.json
├── workflow_complete_2026-02-17T10-30-05.json
├── workflow_error_2026-02-17T10-31-00.json
└── ...
```

---

### Shared Backend Module Structure

```
src/hiveforge/steering/shared/
├── __init__.py              # Package exports
├── base.py                  # SharedWorkflow base class
├── adapters.py              # CLI and Power adapters
├── error_handling.py        # Error handling and rollback
├── security.py              # Input validation and sanitization
└── telemetry.py             # Telemetry collection
```

---

### Design Decisions (v2.1.0)

#### 9. Shared Backend Architecture

**Decision:** Create shared backend module used by both CLI and Power.

**Rationale:**
- Eliminates code duplication
- Ensures consistent behavior
- Simplifies maintenance
- Easier testing

**Trade-off:** More complex initial implementation, but long-term benefits.

#### 10. Automatic Rollback

**Decision:** Automatically create backups and rollback on workflow failure.

**Rationale:**
- Prevents data loss
- Allows easy recovery
- Improves user confidence
- Enables safe experimentation

**Trade-off:** Additional storage overhead for backups.

#### 11. Security First

**Decision:** Validate all inputs and sanitize all paths.

**Rationale:**
- Prevents security vulnerabilities
- Blocks path traversal attacks
- Limits resource consumption
- Protects user systems

**Trade-off:** Slight performance overhead for validation.

#### 12. Telemetry for Insights

**Decision:** Collect telemetry data for monitoring and optimization.

**Rationale:**
- Understand usage patterns
- Identify performance issues
- Track error rates
- Guide future improvements

**Trade-off:** Privacy concerns, storage overhead.

---

### Future Architecture (v2.1.0 Updated)

#### Planned Enhancements

1. **Advanced Telemetry**: Real-time monitoring dashboards
2. **Security Auditing**: Automated security vulnerability scanning
3. **Performance Profiling**: Detailed performance analysis
4. **Custom Rollback Strategies**: User-defined rollback procedures
5. **Distributed Telemetry**: Aggregate telemetry across projects

### Architectural Considerations (v2.1.0)

- **Backward Compatibility:** v2.1.0 features are additive, no breaking changes
- **Extensibility:** New security checks and telemetry events can be added easily
- **Performance:** Validation and telemetry have minimal overhead (<5%)
- **Privacy:** Telemetry data is local-only, never sent externally
- **Security:** All inputs are validated, all paths are sanitized
