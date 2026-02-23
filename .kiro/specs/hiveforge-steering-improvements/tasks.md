# HiveForge Steering System Improvements - Tasks

## Overview

This document contains concrete, actionable tasks for implementing the 13 requirements specified in `requirements.md`. Tasks are organized by priority level (P0/P1/P2) and component, with clear acceptance criteria, dependencies, and effort estimates.

**Task Status Legend:**
- `[ ]` = Not started
- `[x]` = Completed
- `[-]` = In progress
- `[~]` = Queued

**Optional tasks** are marked with `*` asterisk.

---

## P0: Critical Fixes (Must Complete First)

### P0-1: Implement LLMProvider Abstraction with KIRO Native Primary Path

**Requirement:** P0-1  
**Effort:** 8 hours  
**Priority:** CRITICAL  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/llm/provider.py` (NEW)
- `hiveforge-power/hiveforge/steering/llm/__init__.py` (NEW)
- `hiveforge-power/hiveforge/steering/models.py` (MODIFY - add LLMConfig, ProviderType)
- `pyproject.toml` (MODIFY - add optional dependencies)

**Description:**
Implement LLMProvider class that routes LLM calls to available providers with priority: KIRO native (ctx.sample()) → Vertex AI → OpenAI → None. Must support async calls and graceful fallback when providers unavailable.

**Acceptance Criteria:**
- [ ] LLMProvider class created with ProviderType enum (KIRO_NATIVE, VERTEX_AI, OPENAI, NONE)
- [ ] LLMProvider.__init__(ctx) accepts optional KIRO context parameter
- [ ] LLMProvider._load_config() loads from env vars → ~/.hiveforge/llm_config.json → defaults
- [ ] LLMProvider._determine_primary_provider() returns KIRO_NATIVE if ctx available, else external provider
- [ ] LLMProvider.is_available() returns True if any provider configured and accessible
- [ ] LLMProvider.call_llm(prompt, system_prompt, temperature) is async and returns Optional[str]
- [ ] KIRO native calls use asyncio.to_thread() to avoid blocking
- [ ] Vertex AI calls use google-cloud-aiplatform with async support
- [ ] OpenAI calls use AsyncOpenAI client
- [ ] Fallback chain implemented: tries primary, then VERTEX_AI, then OPENAI, returns None if all fail
- [ ] All exceptions logged with warning level (never crash)
- [ ] pyproject.toml has optional dependencies: [vertex], [openai], [all-llm]
- [ ] Unit tests cover all provider paths and fallback chain

**Dependencies:**
- None (foundational component)

**Sub-tasks:**
- [ ] 1.1 Create LLMProvider class skeleton with ProviderType enum
- [ ] 1.2 Implement _load_config() with env var and file loading
- [ ] 1.3 Implement _determine_primary_provider() logic
- [ ] 1.4 Implement is_available() checks for each provider
- [ ] 1.5 Implement _call_kiro_native() with async ctx.sample()
- [ ] 1.6 Implement _call_vertex_ai() with google-cloud-aiplatform and asyncio.to_thread()
- [ ] 1.7 Implement _call_openai() with AsyncOpenAI
- [ ] 1.8 Implement _fallback_chain() with provider priority
- [ ] 1.9 Thread ctx parameter: init_steering.py → SharedInitWorkflow → AutonomousWorkflow → SteeringAssistant
- [ ] 1.10 Update all LLM-calling methods to use complete() with correct signature (system_prompt, user_prompt, max_tokens, temperature, json_mode)
- [ ] 1.11 Add unit tests for all provider paths
- [ ] 1.12 Update pyproject.toml with optional dependencies: [vertex], [openai], [all-llm]

---

### P0-2: Implement SteeringAssistant.generate_file() Method

**Requirement:** P0-2, P0-2a  
**Effort:** 6 hours  
**Priority:** CRITICAL  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/agents/steering_assistant.py` (MODIFY)
- `hiveforge-power/hiveforge/steering/models.py` (MODIFY - add PublicAPIInfo if needed)

**Description:**
Implement generate_file() method that loads templates, strips frontmatter, sends to LLM with context, and returns populated markdown. Must handle LLM failures gracefully with [INFERRED] markers.

**Acceptance Criteria:**
- [ ] SteeringAssistant.generate_file(filename, context) is async method
- [ ] Method loads raw template with frontmatter intact
- [ ] Method strips YAML frontmatter before sending to LLM
- [ ] Method builds LLM prompt with template + context + last 3 generated files
- [ ] Method calls llm_provider.call_llm() with system prompt
- [ ] When LLM returns response, method returns populated markdown (never empty)
- [ ] When LLM returns None, method applies [INFERRED: placeholder] markers to template
- [ ] Method caps context to last 3 files to prevent token blowup
- [ ] System prompt instructs LLM to replace ALL {placeholder} text
- [ ] Method logs generation success with character count
- [ ] Method logs warnings for LLM failures
- [ ] _get_raw_template(template_name) raises FileNotFoundError if template not found
- [ ] _get_raw_template() returns complete template content including frontmatter
- [ ] _strip_frontmatter() removes YAML block between --- delimiters
- [ ] _apply_inferred_markers() replaces {placeholder} with [INFERRED: placeholder]
- [ ] Unit tests cover LLM success, LLM failure, and fallback paths

**Dependencies:**
- P0-1 (LLMProvider)

**Sub-tasks:**
- [x] 2.1 Implement _get_raw_template() method
- [x] 2.2 Implement _strip_frontmatter() method
- [x] 2.3 Implement _build_llm_prompt() with context formatting
- [x] 2.4 Implement _apply_inferred_markers() with regex replacement
- [x] 2.5 Implement generate_file() async method with LLM call using complete() method
- [x] 2.6 Update generate_file() to use correct method signature: complete(system_prompt, user_prompt, max_tokens, temperature, json_mode)
- [x] 2.7 Implement _track_generated_file() for context tracking
- [x] 2.8 Mark generate_file() as async def
- [x] 2.9 Add unit tests for template loading and frontmatter stripping
- [x] 2.10 Add unit tests for LLM success and failure paths

---

### P0-3: Fix AutonomousWorkflow Silent Failures with [INFERRED] Fallback

**Requirement:** P0-3  
**Effort:** 4 hours  
**Priority:** CRITICAL  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/workflows/autonomous_workflow.py` (MODIFY)

**Description:**
Fix AutonomousWorkflow to never write empty files. When generation fails, apply [INFERRED] markers as fallback. Track fallback reasons for reporting.

**Acceptance Criteria:**
- [ ] _step_generate_files_autonomously() catches all exceptions during file generation
- [ ] When exception caught, method calls _apply_fallback() instead of setting empty string
- [ ] _apply_fallback() loads template and applies [INFERRED] markers
- [ ] _apply_fallback() appends reason to self.fallback_reasons list
- [ ] _apply_fallback() sets confidence score to 0.1 (very low)
- [ ] When fallback exhausted, method writes [GENERATION FAILED — please fill manually] message
- [ ] No empty files written to disk (all files have content)
- [ ] Fallback reasons logged with exception type and message
- [ ] Unit tests verify fallback behavior on exception

**Dependencies:**
- P0-2 (SteeringAssistant.generate_file)

**Sub-tasks:**
- [x] 3.1 Implement _generate_file_with_fallback() method
- [x] 3.2 Implement _apply_fallback() method with [INFERRED] markers
- [x] 3.3 Add fallback_reasons tracking to workflow state
- [x] 3.4 Update _step_generate_files_autonomously() to use fallback and mark as async def
- [x] 3.5 Mark _generate_single_file() as async def and add await calls
- [x] 3.6 Add unit tests for fallback behavior

---

### P0-4: Fix input() Blocking in MCP Mode

**Requirement:** P0-4  
**Effort:** 3 hours  
**Priority:** CRITICAL  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/models.py` (MODIFY - add interactive to SteeringConfig)
- `hiveforge-power/hiveforge/steering/workflows/init_workflow.py` (MODIFY)
- `hiveforge-power/hiveforge/steering/workflows/shared_init_workflow.py` (MODIFY)

**Description:**
Add interactive flag to SteeringConfig. Guard all input() calls with `if self.config.interactive:` check. Set interactive=False in MCP mode to prevent blocking.

**Acceptance Criteria:**
- [ ] SteeringConfig has interactive: bool parameter (default True)
- [ ] SharedInitWorkflow.__init__ accepts interactive parameter
- [ ] When ctx is not None (MCP mode), interactive defaults to False
- [ ] When ctx is None (CLI mode), interactive defaults to True
- [ ] All input() calls guarded with `if self.config.interactive:` check
- [ ] When interactive=False, workflows auto-backup existing files and proceed
- [ ] When interactive=False, workflows skip all user prompts
- [ ] Logging message: "Non-interactive mode: auto-backing up existing files and proceeding"
- [ ] Unit tests verify non-interactive mode skips input() calls

**Dependencies:**
- None (can be done independently)

**Sub-tasks:**
- [x] 4.1 Add interactive parameter to SteeringConfig
- [x] 4.2 Update SharedInitWorkflow to set interactive based on ctx
- [x] 4.3 Guard all input() calls in init_workflow.py
- [x] 4.4 Guard all input() calls in autonomous_workflow.py
- [x] 4.5 Add unit tests for non-interactive mode

---

## P1: Important Improvements

### P1-1: Implement CodeAnalyzer.extract_public_api() for MCP Tools and CLI Commands

**Requirement:** P1-1  
**Effort:** 6 hours  
**Priority:** HIGH  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/analyzers/code_analyzer.py` (MODIFY)
- `hiveforge-power/hiveforge/steering/models.py` (MODIFY - add PublicAPIInfo, MCPToolInfo, CLICommandInfo)

**Description:**
Implement extract_public_api() method that scans Python files for @mcp.tool() and @command() decorators, extracts names and docstrings, and returns PublicAPIInfo dataclass.

**Acceptance Criteria:**
- [ ] extract_public_api() returns PublicAPIInfo with mcp_tools, cli_commands, public_classes lists
- [ ] Scans Python files for @mcp.tool() decorated functions
- [ ] Extracts MCP tool names and first-line docstrings (max 120 chars)
- [ ] Scans Python files for @command() or similar CLI decorators
- [ ] Extracts CLI command names and help text
- [ ] Finds non-private public classes with docstrings
- [ ] Excludes self and ctx parameters from parameter lists
- [ ] Skips files in excluded paths (__pycache__, .venv, tests/)
- [ ] Handles syntax errors gracefully (skip malformed files, continue)
- [ ] MCPToolInfo dataclass has name, docstring, parameters fields
- [ ] CLICommandInfo dataclass has name, help_text fields
- [ ] Unit tests cover decorator detection and docstring extraction

**Dependencies:**
- None (can be done independently)

**Sub-tasks:**
- [ ] 1.1 Create PublicAPIInfo, MCPToolInfo, CLICommandInfo dataclasses
- [ ] 1.2 Implement _scan_for_mcp_tools() method
- [ ] 1.3 Implement _scan_for_cli_commands() method
- [ ] 1.4 Implement _extract_public_classes() method
- [ ] 1.5 Implement extract_public_api() orchestration method
- [ ] 1.6 Add error handling for syntax errors
- [ ] 1.7 Add unit tests for decorator detection
- [ ] 1.8 Add unit tests for docstring extraction

---

### P1-2: Implement CodeAnalyzer._heuristic_classify() for Project Type Detection

**Requirement:** P1-2  
**Effort:** 5 hours  
**Priority:** HIGH  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/analyzers/code_analyzer.py` (MODIFY)

**Description:**
Implement _heuristic_classify() method that detects project type (CLI tool, MCP server, web app, library) based on directory structure and decorators. Returns dict with project_type, has_frontend, has_database, has_rest_api, primary_language.

**Acceptance Criteria:**
- [ ] _heuristic_classify(languages) returns dict with required keys
- [ ] Detects mcp_server if mcp_server/ directory exists OR @mcp.tool() decorators found
- [ ] Detects cli_and_mcp if both CLI commands and MCP tools present
- [ ] Detects cli_tool if CLI commands present but no MCP
- [ ] Detects web_app if src/components/ OR *.tsx files exist
- [ ] Defaults to library if no other pattern matches
- [ ] Detects database if migrations/, prisma/, alembic.ini, or models.py at project root
- [ ] Detects REST API if src/api/, routes/, or endpoints/ directories exist
- [ ] Does NOT call self.analyze() (avoids recursion)
- [ ] Accepts languages list as parameter
- [ ] Scans at most 50 Python files for decorators (timeout protection)
- [ ] Unit tests cover all project type classifications

**Dependencies:**
- P1-1 (extract_public_api for MCP tool detection)

**Sub-tasks:**
- [ ] 2.1 Implement _detect_mcp() helper method
- [ ] 2.2 Implement _detect_cli() helper method
- [ ] 2.3 Implement _detect_frontend() helper method
- [ ] 2.4 Implement _detect_database() helper method
- [ ] 2.5 Implement _detect_rest_api() helper method
- [ ] 2.6 Implement _heuristic_classify() orchestration method
- [ ] 2.7 Add timeout protection for decorator scanning
- [ ] 2.8 Add unit tests for all classification paths

---

### P1-3: Implement DraftState and User Review Step Before Writing Files

**Requirement:** P1-3  
**Effort:** 5 hours  
**Priority:** HIGH  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/models.py` (MODIFY - add DraftState, DraftFile)
- `hiveforge-power/hiveforge/steering/workflows/init_workflow.py` (MODIFY)

**Description:**
Implement DraftState dataclass and _step_review_draft() method. In CLI mode, prompt user for approval. In MCP mode, store draft and return False (don't write files).

**Acceptance Criteria:**
- [ ] DraftState dataclass created with files list and metadata
- [ ] DraftFile dataclass has filename, content, confidence, placeholder_count, preview
- [ ] _step_review_draft() creates DraftState with all generated files
- [ ] Calculates placeholder_count using regex {[^}]+}
- [ ] Calculates confidence as 1.0 - (placeholder_count * 0.1)
- [ ] In CLI mode (interactive=True), prints draft summary and prompts user
- [ ] In CLI mode, user can approve (write files) or reject (skip writing)
- [ ] In MCP mode (interactive=False), stores draft in self.state.draft
- [ ] In MCP mode, returns False (don't write files)
- [ ] Draft summary includes filename, confidence, placeholder count, preview (300 chars)
- [ ] WorkflowResult.metadata includes draft_summary for IDE display
- [ ] Unit tests cover CLI and MCP mode behaviors

**Dependencies:**
- P0-4 (interactive flag)

**Sub-tasks:**
- [x] 3.1 Create DraftState and DraftFile dataclasses
- [x] 3.2 Implement _step_review_draft() method
- [x] 3.3 Implement draft summary formatting
- [x] 3.4 Add CLI mode user prompt logic
- [x] 3.5 Add MCP mode draft storage logic with metadata population
- [x] 3.6 Document workflow integration: where _step_review_draft() is called in AutonomousWorkflow.execute()
- [x] 3.7 Document how WorkflowResult.metadata["draft_summary"] gets populated
- [x] 3.8 Document what calls update_steering(apply_draft=True) in MCP mode
- [x] 3.9 Update WorkflowResult to include draft_summary
- [x] 3.10 Add unit tests for CLI and MCP modes

---

### P1-4: Implement DriftDetector for Detecting Changes Between Steering Files and Codebase

**Requirement:** P1-4  
**Effort:** 7 hours  
**Priority:** HIGH  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/detectors/drift_detector.py` (NEW)
- `hiveforge-power/hiveforge/steering/models.py` (MODIFY - add DriftItem, DriftReport)

**Description:**
Implement DriftDetector class that compares steering files against fresh code analysis. Detects language version changes, new dependencies, architecture pattern changes, and convention mismatches.

**Acceptance Criteria:**
- [ ] DriftDetector.detect(existing_files, code_analysis) returns DriftReport
- [ ] Detects Python version drift between tech-stack.md and pyproject.toml (confidence 0.95)
- [ ] Detects new significant runtime dependencies (confidence 0.85)
- [ ] Filters dependencies to only architecturally significant ones (FastAPI, SQLAlchemy, etc.)
- [ ] Skips transitive dependencies
- [ ] Detects architecture pattern drift (confidence 0.75)
- [ ] Detects naming convention mismatches (confidence 0.70)
- [ ] Returns DriftReport with list of DriftItem objects sorted by confidence
- [ ] DriftReport.has_drift() returns True if any items exist
- [ ] DriftReport.by_severity() returns items sorted by confidence descending
- [ ] Returns empty DriftReport when no drift detected
- [ ] Unit tests cover all drift detection types

**Dependencies:**
- P1-1 (extract_public_api for dependency extraction)
- P1-2 (_heuristic_classify for architecture pattern detection)

**Sub-tasks:**
- [x] 4.1 Create DriftItem and DriftReport dataclasses
- [x] 4.2 Implement _detect_language_version_drift() method
- [x] 4.3 Implement _detect_dependency_drift() method
- [x] 4.4 Implement _filter_significant_dependencies() method using curated keyword list
- [x] 4.5 Implement _detect_architecture_drift() method
- [x] 4.6 Implement _detect_convention_drift() method
- [x] 4.7 Implement DriftDetector.detect() orchestration method
- [x] 4.8 Add unit tests for all drift detection types
- [x] 4.9 Add unit tests for dependency filtering (verify only significant deps flagged)

---

### P1-5: Implement Rollback Mechanism for Failed Deployments

**Requirement:** P1-5 (NEW)  
**Effort:** 3 hours  
**Priority:** HIGH  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/workflows/init_workflow.py` (MODIFY)
- `hiveforge-power/hiveforge/steering/workflows/shared_init_workflow.py` (MODIFY)

**Description:**
Implement rollback mechanism to restore previous steering files if generation fails. Maintains timestamped backups and provides atomic restore operation.

**Acceptance Criteria:**
- [ ] _step_check_existing_files() creates timestamped backup in .kiro/steering_backup_{timestamp}/
- [ ] Backup directory path logged when created
- [ ] In interactive mode, offer to restore from backup if generation fails
- [ ] Rollback copies files from most recent backup to .kiro/steering/
- [ ] Rollback logs which files were restored
- [ ] Backup preserves original file timestamps and permissions
- [ ] Keep 5 most recent backups, delete older ones
- [ ] Rollback operation is atomic (all files restored or none)

**Dependencies:**
- P0-4 (interactive flag)

**Sub-tasks:**
- [x] 5.1 Implement _create_backup() method with timestamp
- [x] 5.2 Implement _cleanup_old_backups() method (keep 5 most recent)
- [x] 5.3 Implement _rollback_from_backup() method with atomic operation
- [x] 5.4 Add rollback prompt in interactive mode on generation failure
- [x] 5.5 Add unit tests for backup and rollback

---

### P1-6: Port Missing Files from src/ to hiveforge-power/

**Requirement:** P1-6 (was P1-5)  
**Effort:** 2 hours  
**Priority:** HIGH  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/content_tagger.py` (NEW - port from src/)
- `hiveforge-power/hiveforge/steering/confidence.py` (NEW - port from src/)
- `hiveforge-power/hiveforge/steering/source_resolver.py` (NEW - port from src/)
- `src/hiveforge/steering/` (MARK AS DEPRECATED)

**Description:**
Port content_tagger.py, confidence.py, and source_resolver.py from src/ to hiveforge-power/. Update imports to match new structure. Mark src/ versions as deprecated.

**Acceptance Criteria:**
- [ ] content_tagger.py ported to hiveforge-power/hiveforge/steering/
- [ ] confidence.py ported to hiveforge-power/hiveforge/steering/
- [ ] source_resolver.py ported to hiveforge-power/hiveforge/steering/
- [ ] All imports updated to match hiveforge-power/ structure
- [ ] src/ versions marked as deprecated with migration notes
- [ ] hiveforge-power/ is canonical location for all steering code
- [ ] Unit tests pass after porting

**Dependencies:**
- None (can be done independently)

**Sub-tasks:**
- [x] 6.1 Copy content_tagger.py and update imports
- [x] 6.2 Copy confidence.py and update imports
- [x] 6.3 Copy source_resolver.py and update imports
- [x] 6.4 Mark src/ versions as deprecated
- [x] 6.5 Run tests to verify porting

---

## P2: Enhancements

### P2-1: Implement Template Variants by Project Type

**Requirement:** P2-1  
**Effort:** 4 hours  
**Priority:** MEDIUM  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/workflows/autonomous_workflow.py` (MODIFY)
- `hiveforge-power/hiveforge/templates/steering/` (MODIFY - create variants)

**Description:**
Implement _filter_files_for_project_type() method that selects appropriate templates based on project type. Create template variants for different project types (CLI, MCP, web app).

**Acceptance Criteria:**
- [ ] _filter_files_for_project_type() filters templates based on project_type
- [ ] Skips ui-standards.md for CLI tools and MCP servers (no frontend)
- [ ] Skips db-standards.md for projects without database OR writes N/A section
- [ ] Uses CLI-specific tech-stack.md variant for CLI tools
- [ ] Uses web-specific tech-stack.md variant for web apps
- [ ] Uses MCP-specific api-standards.md variant for MCP servers
- [ ] Logs "Skipping {template} for {project_type}" when template not applicable
- [ ] Template variants stored in templates/steering/ with naming: {template_name}.{project_type}.md
- [ ] Unit tests verify template filtering for each project type

**Dependencies:**
- P1-2 (_heuristic_classify for project type detection)

**Sub-tasks:**
- [x] 1.1 Implement _filter_files_for_project_type() method
- [x] 1.2 Create tech-stack.cli.md variant
- [x] 1.3 Create tech-stack.web_app.md variant
- [x] 1.4 Create api-standards.mcp_server.md variant
- [x] 1.5 Add unit tests for template filtering

---

### P2-2: Implement LLM-Based Project Classification Enrichment

**Requirement:** P2-2  
**Effort:** 3 hours  
**Priority:** MEDIUM  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/analyzers/code_analyzer.py` (MODIFY)

**Description:**
Implement classify_project_with_llm() method that enriches heuristic classification with LLM-generated one-line description and key capabilities.

**Acceptance Criteria:**
- [ ] classify_project_with_llm() calls _heuristic_classify() first
- [ ] When LLM available, sends code analysis summary to LLM for enrichment
- [ ] LLM prompt requests JSON with keys: project_type, has_frontend, has_database, has_rest_api, primary_language, one_line_description, key_capabilities
- [ ] Extracts one_line_description and key_capabilities (list of 3 strings) from LLM response
- [ ] When LLM fails or unavailable, returns base classification without enrichment
- [ ] Uses temperature 0.1 for consistent results
- [ ] Unit tests cover LLM success and failure paths

**Dependencies:**
- P0-1 (LLMProvider)
- P1-2 (_heuristic_classify)

**Sub-tasks:**
- [x] 2.1 Implement classify_project_with_llm() method
- [x] 2.2 Implement LLM prompt for project enrichment
- [x] 2.3 Implement JSON response parsing
- [x] 2.4 Add error handling for LLM failures
- [x] 2.5 Add unit tests for enrichment

---

### P2-3: Implement LLM-Based Gap Analysis Section Classification

**Requirement:** P2-3  
**Effort:** 3 hours  
**Priority:** MEDIUM  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/steering/gap_analysis/gap_analyzer.py` (MODIFY)

**Description:**
Implement _classify_section_with_llm() method that uses LLM to determine if a template section can be filled from available context.

**Acceptance Criteria:**
- [ ] _classify_section_with_llm() called when keyword-matching returns "missing"
- [ ] Sends template section name and available context (max 800 chars) to LLM
- [ ] LLM prompt requests JSON with keys: classification (enum), reason (string)
- [ ] Maps LLM response: "complete" → "complete", "partial" → "ambiguous", "missing" → "missing"
- [ ] When LLM fails or unavailable, falls back to keyword-matching classification
- [ ] Uses temperature 0.1 for consistent results
- [ ] Unit tests cover LLM success and failure paths

**Dependencies:**
- P0-1 (LLMProvider)

**Sub-tasks:**
- [ ] 3.1 Implement _classify_section_with_llm() method
- [ ] 3.2 Implement LLM prompt for section classification
- [ ] 3.3 Implement JSON response parsing and mapping
- [ ] 3.4 Add fallback to keyword-matching
- [ ] 3.5 Add unit tests for classification

---

### P2-4: Unify Template Directories

**Requirement:** P2-4  
**Effort:** 2 hours  
**Priority:** MEDIUM  
**Files to Create/Modify:**
- `hiveforge-power/hiveforge/templates/steering/` (VERIFY)
- `src/hiveforge/templates/steering/` (VERIFY)
- `.github/workflows/ci.yml` (MODIFY - add template sync check)

**Description:**
Verify that template directories are unified. Add CI check to ensure src/ and hiveforge-power/ templates are byte-for-byte identical.

**Acceptance Criteria:**
- [x] Canonical template location identified (hiveforge-power/ preferred)
- [x] CI check added to verify src/ and hiveforge-power/ templates are identical
- [x] CI fails if templates diverge
- [x] CI failure message indicates which files differ
- [x] Documentation updated to specify canonical location
- [x] Unit tests verify template resolution

**Dependencies:**
- None (can be done independently)

**Sub-tasks:**
- [x] 4.1 Identify canonical template location
- [x] 4.2 Implement template sync verification script
- [x] 4.3 Add CI check to .github/workflows/ci.yml
- [x] 4.4 Update documentation with canonical location
- [x] 4.5 Add unit tests for template resolution

---

## Testing Tasks

### Unit Tests for P0 Components

- [ ] Test P0-1: LLMProvider with all provider paths (KIRO, Vertex, OpenAI, None)
- [ ] Test P0-1: LLMProvider fallback chain on provider failure
- [ ] Test P0-1: LLMProvider configuration loading from env vars and file
- [ ] Test P0-2: SteeringAssistant.generate_file() with LLM success
- [ ] Test P0-2: SteeringAssistant.generate_file() with LLM failure and fallback
- [ ] Test P0-2: Template loading and frontmatter stripping
- [ ] Test P0-3: AutonomousWorkflow fallback on exception
- [ ] Test P0-4: Non-interactive mode skips input() calls

### Unit Tests for P1 Components

- [ ] Test P1-1: CodeAnalyzer.extract_public_api() for MCP tools
- [ ] Test P1-1: CodeAnalyzer.extract_public_api() for CLI commands
- [ ] Test P1-1: CodeAnalyzer.extract_public_api() error handling
- [ ] Test P1-2: CodeAnalyzer._heuristic_classify() for all project types
- [ ] Test P1-2: CodeAnalyzer._heuristic_classify() database detection
- [ ] Test P1-3: DraftState creation and summary formatting
- [ ] Test P1-3: Review step in CLI and MCP modes
- [ ] Test P1-4: DriftDetector for all drift types
- [ ] Test P1-4: DriftDetector dependency filtering

### Integration Tests

- [ ] Test full workflow: init_steering with LLM available
- [ ] Test full workflow: init_steering with LLM unavailable (fallback)
- [ ] Test full workflow: init_steering in MCP mode (non-interactive)
- [ ] Test full workflow: init_steering in CLI mode (interactive)
- [ ] Test full workflow: update_steering with drift detection

---

## Documentation Tasks

- [x] Update README.md with LLMProvider configuration instructions
- [x] Create CONFIGURATION.md documenting ~/.hiveforge/llm_config.json format
- [x] Update API documentation for new public methods
- [-] Create MIGRATION.md for porting files from src/ to hiveforge-power/
- [x] Update ARCHITECTURE.md with new component diagrams

---

## Summary

**Total Effort:** ~60 hours  
**P0 Tasks:** 21 hours (critical path)  
**P1 Tasks:** 25 hours (important improvements)  
**P2 Tasks:** 12 hours (enhancements)  
**Testing:** ~10 hours (integrated with each task)  
**Documentation:** ~5 hours

**Recommended Execution Order:**
1. P0-1 (LLMProvider) - foundational
2. P0-2 (generate_file) - depends on P0-1
3. P0-3 (fallback handling) - depends on P0-2
4. P0-4 (interactive flag) - independent, can run in parallel
5. P1-1 (extract_public_api) - independent
6. P1-2 (_heuristic_classify) - depends on P1-1
7. P1-3 (DraftState) - depends on P0-4
8. P1-4 (DriftDetector) - depends on P1-1, P1-2
9. P1-5 (port files) - independent
10. P2-1 (template variants) - depends on P1-2
11. P2-2 (LLM enrichment) - depends on P0-1, P1-2
12. P2-3 (gap analysis) - depends on P0-1
13. P2-4 (unify templates) - independent
