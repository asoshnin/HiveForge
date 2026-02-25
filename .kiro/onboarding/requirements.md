# HiveForge Steering System Improvements - Requirements Document

## Introduction

The HiveForge Steering System generates steering files that help AI agents understand projects. The current implementation has critical failures in file generation, LLM integration, and error handling. This document specifies improvements across three priority levels: P0 (critical fixes), P1 (important improvements), and P2 (enhancements).

The improvements enable autonomous steering file generation with LLM synthesis, proper error handling with fallback markers, drift detection for updates, and project-type-aware templates.

## Glossary

- **Steering File**: Markdown document (e.g., `tech-stack.md`, `architecture.md`) that documents project structure and conventions for AI agents
- **LLMProvider**: Abstraction layer for LLM access with priority routing (KIRO native → Vertex AI → OpenAI → fallback)
- **[INFERRED] Marker**: Placeholder text indicating content that could not be generated (e.g., `[INFERRED: Python version]`)
- **DraftState**: Intermediate state containing generated files awaiting user review before writing to disk
- **DriftDetector**: Component that compares steering files against fresh code analysis to identify outdated content
- **MCP Mode**: Execution context where HiveForge runs inside KIRO IDE via FastMCP protocol
- **CLI Mode**: Execution context where HiveForge runs as standalone command-line tool
- **Interactive Mode**: Configuration flag controlling whether workflows prompt for user input
- **Template Variant**: Project-type-specific version of a steering template (e.g., CLI/MCP vs Web App)
- **Public API**: Extracted MCP tool names, CLI commands, and public classes from codebase
- **Significant Dependencies**: Runtime dependencies that are architecturally important (e.g., FastAPI, SQLAlchemy, not every transitive dep)

---

## Requirements

### P0: Critical Fixes

#### Requirement P0-1: LLM Provider Abstraction with KIRO Native Primary Path

**User Story:** As a KIRO IDE user, I want steering files generated using KIRO's native LLM capabilities, so that I don't need to configure external API credentials.

**Acceptance Criteria**

1. WHEN HiveForge runs in MCP mode (inside KIRO IDE), THE LLMProvider SHALL route LLM calls to `ctx.sample()` (KIRO native) as the primary path
2. WHEN `ctx` is not available (CLI mode), THE LLMProvider SHALL attempt external providers in priority order: Google Vertex AI → OpenAI → None
3. WHEN no LLM provider is available, THE LLMProvider SHALL return `None` and callers SHALL use `[INFERRED]` markers instead of crashing
4. WHEN external provider is selected, THE LLMProvider SHALL load configuration from `~/.hiveforge/llm_config.json` with environment variable overrides
5. WHEN Vertex AI is configured, THE LLMProvider SHALL use `google-cloud-aiplatform` library with async support via `asyncio.to_thread()`
6. WHEN OpenAI is configured, THE LLMProvider SHALL use `AsyncOpenAI` client for non-blocking calls
7. THE LLMProvider SHALL be available as optional dependencies: `pip install hiveforge-steering-mcp[vertex]` or `[openai]` or `[all-llm]`
8. WHEN `ctx.sample()` fails, THE LLMProvider SHALL log warning and fall back to next provider (not crash)
9. THE LLMProvider.is_available() method SHALL return `True` if any provider is configured and accessible

**Dependencies**
- Requires `ctx` parameter threading through `SharedInitWorkflow` → `AutonomousWorkflow` → `SteeringAssistant`
- Requires `pyproject.toml` updates to add optional dependencies
- Requires all LLM-calling methods to be `async def` with `await` calls

**Ctx Threading Path:**
```
init_steering.py (receives ctx from FastMCP)
  ↓
SharedInitWorkflow.__init__(ctx=ctx)
  ↓
AutonomousWorkflow.__init__(ctx=ctx)
  ↓
SteeringAssistant.__init__(ctx=ctx)
  ↓
LLMProvider(ctx=ctx)
```

---

#### Requirement P0-2: SteeringAssistant.generate_file() Method Implementation

**User Story:** As an autonomous workflow, I want to generate individual steering files using LLM synthesis, so that files are populated with project-specific content instead of remaining empty.

**Acceptance Criteria**

1. WHEN `SteeringAssistant.generate_file(filename, context)` is called, THE method SHALL load the raw template and strip YAML frontmatter before sending to LLM
2. WHEN LLM provider is available, THE method SHALL send template + knowledge base context + previously generated files to LLM for synthesis
3. WHEN LLM returns a response, THE method SHALL return the populated markdown string (never empty)
4. WHEN LLM returns `None` or fails, THE method SHALL apply `[INFERRED: placeholder]` markers to template and return that as fallback
5. THE method SHALL cap context to last 3 generated files to prevent token budget blowup on later files
6. THE method SHALL use system prompt: "You are a technical documentation expert generating a KIRO steering file. Replace ALL {placeholder} text with real, specific content. Output ONLY the final Markdown. Never leave {placeholder} text in your output."
7. THE method SHALL be async (`async def`) to support non-blocking LLM calls
8. THE method SHALL log generation success with character count and log warnings for LLM failures

**Dependencies**
- Requires `LLMProvider` (P0-1)
- Requires `TemplatePopulator._get_raw_template()` (P0-2 sub-requirement)
- Requires `async` threading through `AutonomousWorkflow._generate_single_file()`

---

#### Requirement P0-2a: TemplatePopulator._get_raw_template() Method

**User Story:** As SteeringAssistant, I want to retrieve raw template content including frontmatter, so that I can strip it before sending to LLM.

**Acceptance Criteria**

1. WHEN `_get_raw_template(template_name)` is called, THE method SHALL return the complete template file content as string
2. WHEN template_name is not found, THE method SHALL raise `ValueError` with list of available templates
3. WHEN template file does not exist on disk, THE method SHALL raise `FileNotFoundError` with file path
4. THE method SHALL NOT strip frontmatter (caller does that)

---

#### Requirement P0-3: Fix AutonomousWorkflow Silent Failures with [INFERRED] Fallback

**User Story:** As a user running autonomous steering generation, I want to see `[INFERRED]` markers instead of empty files when generation fails, so that I know what content needs manual review.

**Acceptance Criteria**

1. WHEN `AutonomousWorkflow._step_generate_files_autonomously()` encounters an exception, THE workflow SHALL NOT silently set file to empty string
2. WHEN generation fails, THE workflow SHALL apply `[INFERRED: placeholder]` markers to template as fallback
3. WHEN fallback is triggered, THE workflow SHALL log error with exception type and message
4. WHEN fallback is triggered, THE workflow SHALL set confidence score to 0.1 (very low confidence)
5. WHEN fallback is triggered, THE workflow SHALL append reason to `self.fallback_reasons` list for reporting
6. THE workflow SHALL never write empty files to disk (all files have content, even if marked `[INFERRED]`)
7. WHEN all fallbacks are exhausted, THE workflow SHALL write template with `[GENERATION FAILED — please fill manually]` message

**Dependencies**
- Requires `TemplatePopulator._get_raw_template()` (P0-2a)

---

#### Requirement P0-4: Fix input() Blocking in MCP Mode

**User Story:** As a KIRO IDE user, I want steering workflows to complete without hanging, so that MCP calls don't block the IDE.

**Acceptance Criteria**

1. WHEN `init_workflow._step_check_existing_files()` is called in non-interactive mode, THE method SHALL NOT call `input()` and SHALL auto-backup existing files instead
2. WHEN `SteeringConfig.interactive` is `False`, THE workflow SHALL skip all user prompts and use sensible defaults
3. WHEN `SharedInitWorkflow` constructs config for MCP invocation, THE config SHALL explicitly set `interactive=False`
4. WHEN `interactive=False`, THE workflow SHALL log "Non-interactive mode: auto-backing up existing files and proceeding"
5. ALL `input()` calls in workflows SHALL be guarded with `if self.config.interactive:` check
6. WHEN running in MCP mode, THE `SteeringConfig.interactive` flag SHALL be set to `False` by the caller (not defaulted to `True`)

**Dependencies**
- Requires `SteeringConfig` modification to accept `interactive` parameter
- Requires `SharedInitWorkflow` to pass `interactive=False` when constructing config

---

### P1: Important Improvements

#### Requirement P1-1: CodeAnalyzer.extract_public_api() for MCP Tools and CLI Commands

**User Story:** As an LLM generating steering files, I want to know the project's MCP tool names and CLI commands, so that I can document them accurately in tech-stack.md and architecture.md.

**Acceptance Criteria**

1. WHEN `CodeAnalyzer.extract_public_api()` is called, THE method SHALL scan Python files for `@mcp.tool()` decorated functions and extract their names and docstrings
2. WHEN scanning for CLI commands, THE method SHALL detect `@command()` or similar decorators and extract command names and help text
3. WHEN extracting public classes, THE method SHALL find non-private classes with docstrings and include them in results
4. THE method SHALL return `PublicAPIInfo` dataclass containing `mcp_tools`, `cli_commands`, and `public_classes` lists
5. WHEN extracting parameters, THE method SHALL exclude `self` and `ctx` parameters from the list
6. WHEN extracting docstrings, THE method SHALL use only the first line (max 120 characters)
7. THE method SHALL skip files in excluded paths (e.g., `__pycache__`, `.venv`, `tests/`)
8. THE method SHALL handle syntax errors gracefully (skip malformed files, continue scanning)

**Dependencies**
- Requires `PublicAPIInfo`, `MCPToolInfo`, `CLICommandInfo` dataclasses in `models.py`

---

#### Requirement P1-2: CodeAnalyzer._heuristic_classify() for Project Type Detection

**User Story:** As a template system, I want to detect whether a project is a CLI tool, MCP server, web app, or library, so that I can select appropriate template variants.

**Acceptance Criteria**

1. WHEN `_heuristic_classify()` is called, THE method SHALL return dict with keys: `project_type`, `has_frontend`, `has_database`, `has_rest_api`, `primary_language`, `one_line_description`, `key_capabilities`
2. WHEN project has `mcp_server/` directory OR `@mcp.tool()` decorators, THE method SHALL classify as `"mcp_server"`
3. WHEN project has both CLI commands AND MCP tools, THE method SHALL classify as `"cli_and_mcp"`
4. WHEN project has CLI commands but no MCP, THE method SHALL classify as `"cli_tool"`
5. WHEN project has `src/components/` OR `*.tsx` files, THE method SHALL classify as `"web_app"`
6. WHEN no other pattern matches, THE method SHALL classify as `"library"`
7. WHEN detecting database, THE method SHALL check for `migrations/`, `prisma/`, `alembic.ini`, or `models.py` at project root ONLY (not subdirectories)
8. WHEN detecting REST API, THE method SHALL check for `src/api/`, `routes/`, or `endpoints/` directories
9. THE method SHALL NOT call `self.analyze()` (to avoid infinite recursion) and SHALL accept `languages` list as parameter
10. THE method SHALL scan at most 50 Python files for decorators (to avoid timeout on large projects)

**Dependencies**
- Requires `CodeAnalyzer.extract_public_api()` (P1-1) for MCP tool detection
- Requires `_detect_mcp()`, `_detect_cli()`, `_detect_frontend()`, `_detect_database()`, `_detect_rest_api()` helper methods

---

#### Requirement P1-3: DraftState and User Review Step Before Writing Files

**User Story:** As a KIRO IDE user, I want to review generated steering files before they are written to disk, so that I can approve or edit them.

**Acceptance Criteria**

1. WHEN `init_workflow._step_review_draft()` is called, THE method SHALL create `DraftState` with all generated files and their metadata
2. FOR each file in draft, THE method SHALL calculate `placeholder_count` (regex match `{[^}]+}`) and `confidence` score (1.0 - placeholder_count * 0.1)
3. WHEN running in CLI mode (`interactive=True`), THE method SHALL print draft summary and prompt user for approval
4. WHEN user approves in CLI mode, THE method SHALL set `is_approved=True` for all files and return `True`
5. WHEN user rejects in CLI mode, THE method SHALL return `False` and skip file writing
6. WHEN running in MCP mode (`interactive=False`), THE method SHALL store draft in `self.state.draft` and return `False` (do NOT write files)
7. WHEN running in MCP mode, THE caller SHALL include draft summary in `WorkflowResult.metadata["draft_summary"]` for IDE display
8. THE draft summary SHALL include filename, confidence score, placeholder count, and preview (first 300 chars)
9. WHEN user calls `update_steering(apply_draft=True)` in MCP mode, THE workflow SHALL write approved files to disk

**Dependencies**
- Requires `DraftState`, `DraftFile` dataclasses in `models.py`
- Requires `SharedInitWorkflow` to read draft from state and include in result metadata

---

#### Requirement P1-4: DriftDetector for Detecting Changes Between Steering Files and Codebase

**User Story:** As an update workflow, I want to detect when steering files are outdated compared to the current codebase, so that I can suggest updates.

**Acceptance Criteria**

1. WHEN `DriftDetector.detect(existing_files, code_analysis)` is called, THE method SHALL compare steering files against fresh code analysis
2. WHEN Python version in `tech-stack.md` differs from `pyproject.toml`, THE method SHALL create `DriftItem` with category `"language_version"` and confidence 0.95
3. WHEN new significant runtime dependencies are detected, THE method SHALL create `DriftItem` with category `"new_dependency"` and confidence 0.85
4. WHEN filtering dependencies, THE method SHALL only flag architecturally significant ones (FastAPI, SQLAlchemy, Redis, etc.) and skip transitive deps
5. WHEN determining significance, THE method SHALL use a curated list of significant dependency keywords: `fastapi`, `flask`, `django`, `sqlalchemy`, `prisma`, `redis`, `celery`, `pydantic`, `typer`, `click`, `pytest`, `asyncio`, `aiohttp`, `requests`, `numpy`, `pandas`, `torch`, `tensorflow`, `scikit-learn`, `plotly`, `streamlit`
6. WHEN a dependency is not in the significant list, THE method SHALL skip it (do not create DriftItem)
7. WHEN architecture pattern in code differs from `architecture.md`, THE method SHALL create `DriftItem` with category `"architecture_pattern"` and confidence 0.75
6. WHEN naming conventions in code differ from `conventions.md`, THE method SHALL create `DriftItem` with category `"convention_mismatch"` and confidence 0.70
7. THE method SHALL return `DriftReport` with list of `DriftItem` objects sorted by confidence (highest first)
8. WHEN no drift is detected, THE method SHALL return empty `DriftReport`
9. THE `DriftReport.has_drift()` method SHALL return `True` if any items exist
10. THE `DriftReport.by_severity()` method SHALL return items sorted by confidence descending

**Dependencies**
- Requires `DriftItem`, `DriftReport` dataclasses in `models.py`
- Requires `CodeAnalyzer.extract_public_api()` (P1-1) for dependency extraction
- Requires `CodeAnalyzer._heuristic_classify()` (P1-2) for architecture pattern detection

---

#### Requirement P1-5: Rollback Mechanism for Failed Deployments

**User Story:** As a developer, I want to rollback to previous steering files if the new generation fails or produces incorrect content, so that I can recover from errors quickly.

**Acceptance Criteria**

1. WHEN `init_workflow._step_check_existing_files()` finds existing files, THE workflow SHALL create timestamped backup in `.kiro/steering_backup_{timestamp}/`
2. WHEN backup is created, THE workflow SHALL log the backup directory path
3. WHEN file generation fails after backup, THE workflow SHALL offer to restore from backup (in interactive mode)
4. WHEN user requests rollback, THE workflow SHALL copy files from most recent backup to `.kiro/steering/`
5. WHEN rollback completes, THE workflow SHALL log which files were restored
6. THE backup directory SHALL preserve original file timestamps and permissions
7. WHEN multiple backups exist, THE workflow SHALL keep the 5 most recent backups and delete older ones
8. THE rollback operation SHALL be atomic (all files restored or none)

**Dependencies**
- Requires P0-4 (interactive flag) for conditional rollback prompts

---

#### Requirement P1-6: Port Missing Files from src/ to hiveforge-power/

**User Story:** As a developer, I want all steering system files to be in one location, so that I don't maintain duplicate code.

**Acceptance Criteria**

1. WHEN `hiveforge-power/hiveforge/steering/` is checked, THE following files from `src/hiveforge/steering/` SHALL be ported: `content_tagger.py`, `confidence.py`, `source_resolver.py`
2. WHEN porting files, THE imports SHALL be updated to match `hiveforge-power/` structure
3. WHEN porting is complete, THE `src/` versions SHALL be marked as deprecated or removed
4. AFTER porting, THE `hiveforge-power/` directory SHALL be the canonical location for all steering system code

---

#### Requirement P2-1: Template Variants by Project Type

**User Story:** As a CLI tool developer, I want steering templates tailored to my project type, so that I don't see irrelevant sections like "Frontend Framework" or "Database Schema".

**Acceptance Criteria**

1. WHEN `AutonomousWorkflow` generates files, THE workflow SHALL call `_filter_files_for_project_type()` to select appropriate templates
2. WHEN project is classified as `"cli_tool"` or `"mcp_server"`, THE workflow SHALL skip `ui-standards.md` (no frontend)
3. WHEN project has no database, THE workflow SHALL skip `db-standards.md` OR write N/A section
4. WHEN project is `"cli_tool"`, THE workflow SHALL use CLI-specific `tech-stack.md` variant (no Frontend section)
5. WHEN project is `"web_app"`, THE workflow SHALL use web-specific `tech-stack.md` variant (includes Frontend/Backend/DB)
6. WHEN project is `"mcp_server"`, THE workflow SHALL use MCP-specific `api-standards.md` variant (MCP Tool Standards instead of REST API)
7. WHEN template is not applicable, THE workflow SHALL log "Skipping {template} for {project_type}"
8. THE template variants SHALL be stored in `templates/steering/` with naming convention: `{template_name}.{project_type}.md`

**Dependencies**
- Requires `CodeAnalyzer._heuristic_classify()` (P1-2)
- Requires template variant files to be created

---

#### Requirement P2-2: LLM-Based Project Classification Enrichment

**User Story:** As an LLM generating steering files, I want a one-line description and key capabilities of the project, so that I can write more accurate documentation.

**Acceptance Criteria**

1. WHEN `CodeAnalyzer.classify_project_with_llm()` is called, THE method SHALL first run `_heuristic_classify()` to get base classification
2. WHEN LLM provider is available, THE method SHALL send code analysis summary to LLM for enrichment
3. WHEN LLM responds, THE method SHALL extract `one_line_description` and `key_capabilities` (list of 3 strings)
4. WHEN LLM fails or is unavailable, THE method SHALL return base classification without enrichment
5. THE LLM prompt SHALL request JSON response with exact keys: `project_type`, `has_frontend`, `has_database`, `has_rest_api`, `primary_language`, `one_line_description`, `key_capabilities`
6. THE method SHALL use temperature 0.1 (low randomness) for consistent results

**Dependencies**
- Requires `LLMProvider` (P0-1)
- Requires `CodeAnalyzer._heuristic_classify()` (P1-2)

---

#### Requirement P2-3: LLM-Based Gap Analysis Section Classification

**User Story:** As a gap analysis engine, I want to use LLM to determine if a section can be filled from available context, so that I ask fewer unnecessary questions.

**Acceptance Criteria**

1. WHEN `GapAnalysisEngine._classify_section()` returns `"missing"` AND LLM provider is available, THE engine SHALL call `_classify_section_with_llm()` for semantic classification
2. WHEN LLM is called, THE engine SHALL send template section name and available context (max 800 chars)
3. WHEN LLM responds, THE engine SHALL map response to classification: `"complete"` → `"complete"`, `"partial"` → `"ambiguous"`, `"missing"` → `"missing"`
4. WHEN LLM fails or is unavailable, THE engine SHALL fall back to keyword-matching classification
5. THE LLM prompt SHALL request JSON response with keys: `classification` (enum), `reason` (string)
6. THE method SHALL use temperature 0.1 for consistent results

**Dependencies**
- Requires `LLMProvider` (P0-1)

---

#### Requirement P2-4: Unify Template Directories

**User Story:** As a maintainer, I want a single source of truth for steering templates, so that I don't maintain duplicate files.

**Acceptance Criteria**

1. WHEN templates are loaded, THE system SHALL resolve to canonical location (either `src/` or `hiveforge-power/`, not both)
2. WHEN CI runs, THE system SHALL verify that `src/hiveforge/templates/steering/` and `hiveforge-power/hiveforge/templates/steering/` are byte-for-byte identical
3. WHEN templates are updated, THE update SHALL be made in canonical location only
4. WHEN CI detects divergence, THE CI check SHALL fail with message indicating which files differ

**Dependencies**
- Requires CI configuration update

---

## Acceptance Criteria Patterns

### Common Correctness Properties

#### Round-Trip Properties (for parsers/serializers)
- FOR ALL valid steering files, parsing then printing then parsing SHALL produce equivalent content
- FOR ALL template variants, generating then re-analyzing SHALL detect no new drift

#### Invariants
- Confidence scores SHALL always be between 0.0 and 1.0
- Placeholder count SHALL never be negative
- Draft files SHALL never be empty (always have content or `[INFERRED]` markers)

#### Idempotence
- Calling `DriftDetector.detect()` multiple times on same files SHALL produce same results
- Calling `CodeAnalyzer._heuristic_classify()` multiple times SHALL produce same classification

#### Metamorphic Properties
- Number of generated files SHALL equal number of selected templates
- Confidence score SHALL decrease as placeholder count increases
- Drift item count SHALL increase as code diverges from steering files

---

## Dependencies Between Requirements

```
P0-1 (LLMProvider)
  ├─ P0-2 (generate_file)
  │   ├─ P0-2a (TemplatePopulator._get_raw_template)
  │   └─ P0-3 (Fix silent failures)
  ├─ P2-2 (LLM project classification)
  └─ P2-3 (LLM gap analysis)

P0-4 (Fix input() blocking)
  └─ P1-3 (DraftState review)

P1-1 (extract_public_api)
  ├─ P1-2 (_heuristic_classify)
  │   └─ P2-1 (Template variants)
  └─ P1-4 (DriftDetector)

P1-3 (DraftState)
  └─ P1-4 (DriftDetector)

P1-5 (Port missing files)
  └─ (No dependencies)

P2-1 (Template variants)
  └─ P1-2 (_heuristic_classify)

P2-4 (Unify templates)
  └─ (No dependencies)
```

---

## Success Metrics

1. **File Generation Success Rate**: 100% of steering files generated have content (no empty files)
2. **Placeholder Coverage**: ≥95% of `{placeholder}` text replaced with real content (when LLM available)
3. **Fallback Reliability**: When LLM unavailable, 100% of files have `[INFERRED]` markers (never crash)
4. **MCP Mode Stability**: No `input()` calls block MCP execution; all workflows complete within 30 seconds
5. **Drift Detection Accuracy**: ≥90% of detected drift items are actionable (not false positives)
6. **Template Applicability**: ≥95% of generated sections are relevant to project type (no "Frontend" for CLI tools)
7. **Code Coverage**: All new methods have ≥80% test coverage
8. **Performance**: LLM calls complete within 10 seconds per file; total workflow ≤2 minutes for 8 files

---

## Non-Goals

- Real-time steering file synchronization (drift detection is manual/on-demand)
- Automatic steering file updates without user review
- Support for non-Python projects (scope limited to Python CLI/MCP tools)
- Custom LLM model fine-tuning (use provided models only)
- Steering file version control integration (separate concern)

---

## Constraints & Assumptions

### Technical Constraints
- LLM calls must be async to avoid blocking event loop in MCP mode
- Template frontmatter must be stripped before sending to LLM (to reduce token usage)
- Dependency filtering must exclude transitive deps (only flag significant ones)
- Database detection must check project root only (not subdirectories like `steering/models.py`)

### Business Constraints
- Optional LLM dependencies (Vertex AI, OpenAI) must not be required for basic functionality
- KIRO native (`ctx.sample()`) must be primary path for MCP users (no extra config)
- Fallback to `[INFERRED]` markers must always work (no LLM required)

### Key Assumptions
- Project has `pyproject.toml` for Python version and dependency detection
- MCP tools are decorated with `@mcp.tool()` (detectable via AST)
- CLI commands are decorated with `@command()` or similar (detectable via AST)
- Users will review draft files before writing (MCP mode does not auto-approve)
- Significant dependencies are known set (FastAPI, SQLAlchemy, Redis, etc.)

---

## Implementation Notes

### Async Threading Strategy
- `ctx` parameter flows: `init_steering.py` → `SharedInitWorkflow.__init__` → `AutonomousWorkflow.__init__` → `SteeringAssistant.__init__`
- All LLM calls wrapped in `try/except` with fallback
- Vertex AI SDK is sync; use `asyncio.to_thread()` to avoid blocking

### Configuration Priority
1. Environment variables (highest priority)
2. `~/.hiveforge/llm_config.json` file
3. Defaults (KIRO native if `ctx` available, else no LLM)

### Error Handling Strategy
- Never crash on LLM failure (always have fallback)
- Log all errors with context (file name, exception type, message)
- Track fallback reasons for reporting to user
- Confidence scores reflect uncertainty (0.1 for fallback, 0.95 for high-confidence drift)

---

## Glossary Expansion

- **Frontmatter**: YAML metadata block at top of Markdown file (between `---` delimiters)
- **Token Budget**: Maximum number of tokens allowed in LLM request (context + prompt + response)
- **Transitive Dependency**: Dependency of a dependency (not directly required by project)
- **AST**: Abstract Syntax Tree (parsed representation of source code)
- **Confidence Score**: Numeric value (0.0-1.0) indicating certainty of generated content
- **Drift**: Discrepancy between steering file content and current codebase state
- **Fallback**: Alternative behavior when primary method fails (e.g., `[INFERRED]` markers when LLM unavailable)
