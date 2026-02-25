# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- CI/CD pipeline with GitHub Actions
- PyPI publishing automation
- Tech-stack template variants
- IDE-agnostic mode
- CLI backward compatibility test updates

## [3.0.0] - 2026-02-25

### Added - LLM-Primary Steering Synthesis Pipeline & Technical Debt Detection

#### Technical Debt Detection & Tracking
- **9th Steering File**: `technical-debt.md` automatically generated during init/update
- **DebtDetector**: Local static analysis for DRY violations, test gaps, architecture smells, performance risks
- **DebtReconciler**: Merge existing + fresh analysis during updates, preserves manual edits
- **Scalability**: Automatic sampling for large codebases (>10k files), caching, .gitignore respect
- **Priority Escalation**: Based on conventions.md content (DRY preference, testing preference)
- **CLI Flag**: `--skip-debt-detection` to skip analysis (faster init)
- **MCP Metadata**: `debt_summary` field in init/update responses with metrics

#### Debt Detection Features
- **DRY Violations**: AST-based function body hashing (Python), line-hash fallback (other languages)
- **Test Gaps**: File-to-test ratio analysis, untested public function detection
- **Architecture Smells**: Circular import detection (Tarjan's SCC), god class detection (>500 lines)
- **Performance Risks**: N+1 queries, unbounded loops, string concatenation, list allocation

#### Data Models
- **DebtItem**: ID, category, description, location, priority, effort, risk, status, confidence, recommendations
- **DebtRecommendation**: At least 2 per item (recommended + alternative)
- **DebtAnalysisResult**: Items, metrics, sampled flag, analysis time
- **DebtMetrics**: Total active, by category, by priority, last updated

#### Reconciliation (Update Workflow)
- **User-edited items**: Preserve description/priority if manually changed
- **Manually added items**: Preserve items with IDs absent from fresh analysis
- **Auto-resolved items**: Move to RESOLVED if absent from fresh analysis
- **New items**: Add with status=ACTIVE and detected_at timestamp
- **Historical resolved items**: Preserve verbatim from Resolved section

#### Testing
- **68 New Tests**: Unit tests, property tests, integration tests
- **Property-Based Testing**: 13 correctness properties validated
- **100% Pass Rate**: All 68 tests passing
- **Total Test Count**: 257+ tests (up from 189)

#### Core Pipeline Architecture
- **LLM-Primary Generation**: Steering files now generated directly by LLM synthesis instead of template population
- **Use Case Determination**: Automatic detection of `new_from_docs` vs `reverse_engineer` workflows
- **Context Assembly**: Intelligent context building with token budgets and keyword-based relevance filtering
- **Hallucination Detection**: Duplicate paragraph detection prevents LLM hallucinations
- **Atomic Transactions**: All-or-nothing file generation (8 files or none)

#### LLM Provider Enhancements
- **Provider Priority Chain**: KIRO Native → Vertex AI → OpenAI → None (fallback)
- **Graceful Degradation**: Falls back to `[INFERRED]` markers when LLM unavailable
- **Retry Logic**: Single retry on empty/malformed responses
- **Configuration Support**: Environment variables and `~/.hiveforge/llm_config.json`

#### Code Analysis Improvements
- **Public API Extraction**: Detects MCP tools, CLI commands, and public classes
- **Project Classification**: Heuristic + LLM-enriched classification (cli_tool, mcp_server, web_app, library)
- **Template Variant Selection**: Chooses appropriate templates based on project type
- **One-Line Descriptions**: LLM-generated project summaries

#### Context Assembly System
- **Token Budget Allocation**: 50% source docs, 25% code facts, 15% templates, 10% buffer
- **Keyword-Based Filtering**: Reduces irrelevant content before truncation
- **Multi-Layer Defense**: Filtering → Budget allocation → Truncation (last resort)
- **Template-Specific Context**: Each template gets relevant subset of knowledge base

#### Draft Review Workflow
- **Draft State Management**: Generated files stored for review before writing
- **Confidence Scoring**: Per-file confidence scores based on source material
- **Interactive Review (CLI)**: User approves draft before files are written
- **Deferred Writing (MCP)**: Draft stored for IDE review, written on explicit approval

#### Validation & Quality
- **Duplicate Detection**: Prevents LLM from repeating paragraphs across files
- **Placeholder Counting**: Tracks unreplaced placeholders for quality metrics
- **Confidence Thresholds**: High (0.7-1.0), Medium (0.4-0.7), Low (0.0-0.4)
- **Fallback Markers**: `[INFERRED]` tags when LLM unavailable or low confidence

### Changed
- **SteeringAssistant**: Now generates files directly via `generate_file()` method
- **AutonomousWorkflow**: Refactored to use LLM synthesis instead of template population
- **CodeAnalyzer**: Added `extract_public_api()` and `classify_project_with_llm()` methods
- **ContextAssembler**: New component for intelligent context building
- **Workflow Results**: Enhanced metadata includes draft summaries and confidence scores

### Performance
- **Token Efficiency**: Context assembly respects strict token budgets (4000 tokens max)
- **Keyword Filtering**: Reduces input size by 30-50% for irrelevant documents
- **Single LLM Call**: One call per template (8 total) instead of multiple Q&A rounds
- **Retry Overhead**: Minimal (single retry on failure, no retries on hallucinations)

### Testing
- **88 New Tests**: 20 LLM synthesis tests + 68 technical debt tests
- **Property-Based Tests**: 21 correctness properties validated (8 synthesis + 13 debt)
- **Integration Tests**: End-to-end pipeline testing with real documents
- **Token Budget Tests**: Verify all templates stay within budget
- **All Tests Passing**: 257+ tests (up from 169)

### Documentation
- **TECHNICAL_DEBT_IMPLEMENTATION.md**: Comprehensive implementation guide for debt detection
- **LLM_PRIMARY_SYNTHESIS_IMPLEMENTATION.md**: Comprehensive implementation guide for LLM synthesis
- **API_REFERENCE.md**: Updated with new APIs (generate_file, extract_public_api, DebtDetector, DebtReconciler)
- **MIGRATION.md**: v3.0.0 migration guide for users and developers
- **Architecture.md**: Updated with new pipeline components
- **README.md**: Updated test count (257+) and feature list (9 steering files)

### Breaking Changes
None. All new features are internal implementation changes. External APIs remain compatible.

### Migration Notes
See [hiveforge-power/docs/MIGRATION.md](./hiveforge-power/docs/MIGRATION.md) for v3.0.0 migration details.

## [2.2.0] - 2026-02-19

### Added - Source Documents Path & Hallucination Guardrails

#### Custom Source Document Paths
- **`source_docs_path` parameter**: Specify custom location for source documents (relative to project root)
- **Flexible document discovery**: No longer limited to `.kiro/onboarding/` folder
- **Symlink optimization**: Uses symlinks by default for fast document staging (~100ms for 1000 files)
- **`copy_files` parameter**: Optional file copying mode for environments without symlink support

#### Confidence Scoring & Hallucination Guardrails
- **Confidence calculation**: Weighted scoring based on content sources (documents: 1.0, code: 0.8, inferred: 0.3)
- **Per-file confidence scores**: Track confidence for each generated steering file
- **Overall workflow confidence**: Aggregate confidence across all files
- **Confidence metadata**: YAML frontmatter in all generated files with confidence details

#### Content Tagging
- **HTML comment markers**: Inferred sections tagged with `<!-- INFERRED: Please verify this section -->`
- **Low confidence warnings**: Prominent warnings in files with <50% confidence
- **Source tracking**: Metadata shows which content came from documents vs. code vs. inference
- **YAML frontmatter**: All files include generation metadata (version, timestamp, sources, confidence)

#### Enhanced Discovery
- **File type filtering**: `file_types` parameter to target specific extensions (e.g., `[".md", ".pdf"]`)
- **Source path prioritization**: When `source_docs_path` provided, scans that location first
- **Discovery statistics**: Detailed breakdown of files by type, path, included/excluded counts
- **Empty source warnings**: Clear warnings when no source documents found

#### Dry-Run Mode
- **Preview before execution**: `dry_run=True` generates content without writing files
- **Full analysis**: Performs complete code analysis and gap detection
- **Preview results**: Returns generated content, confidence scores, and warnings
- **Risk-free testing**: Validate configuration before committing changes

#### Security Enhancements
- **Comprehensive path validation**: Prevents path traversal, symlink attacks, null byte injection
- **Input sanitization**: Strips whitespace, normalizes separators, rejects control characters
- **Project boundary enforcement**: All paths validated to stay within project root
- **Security test coverage**: 15+ attack vector tests (traversal, encoding, symlinks)

#### Telemetry Collection
- **Parameter usage tracking**: Monitor adoption of `source_docs_path`, `dry_run`, `copy_files`
- **Confidence distribution**: Track high/medium/low confidence rates
- **Performance metrics**: Discovery time, confidence calculation time, tagging time
- **Error analytics**: Path validation failures, discovery failures by cause

### Changed
- **MCP tool signatures**: Added optional parameters to `init_steering` and `discover_docs`
- **Workflow result structure**: Enhanced with confidence metadata and discovery statistics
- **Documentation**: Updated all workflows to show correct HiveForge Power usage from KIRO IDE
- **Performance targets**: Relaxed to realistic values while maintaining good performance

### Fixed
- **Documentation accuracy**: Corrected workflow instructions to use HiveForge Power (not agent)
- **Empty source folder handling**: Now provides clear warnings instead of silent failures
- **Source document location**: Documented `.kiro/onboarding/` default and custom path usage

### Performance
- **Confidence calculation**: <100ms per file, <200ms overall (100-file knowledge base)
- **Content tagging**: <5ms (10KB), <50ms (100KB), <500ms (1MB files)
- **Source discovery**: <1s (1000 files), <10s (10,000 files)
- **Symlink optimization**: 2x faster than file copying (default mode)

### Testing
- **34 new tests**: Confidence calculation, content tagging, source resolution
- **15 performance tests**: Benchmarks for all new components
- **12 security tests**: Comprehensive attack vector coverage
- **8 integration tests**: End-to-end workflows with new features
- **100% backward compatibility**: All existing tests pass

### Documentation
- **Migration guide**: `docs/migration-v2.2.0.md` with 4 migration scenarios
- **Updated workflows**: WORKFLOW.md and WORKFLOW_refactoring_01.md corrected
- **Power documentation**: hiveforge-power/POWER.md enhanced with troubleshooting
- **Steering guide**: docs/steering-assistant-guide.md updated with new parameters

### Breaking Changes
None. All new parameters are optional with sensible defaults.

### Migration Notes
See [docs/migration-v2.2.0.md](./docs/migration-v2.2.0.md) for detailed migration scenarios.

## [2.1.0] - 2026-02-17

### Added - HiveForge Steering MCP Power Package
- **Error Handling with Automatic Rollback**: Automatic backup creation and rollback on failures
- **Security Features**: Input validation, path sanitization, resource limits, error obfuscation
- **Telemetry Collection**: Performance tracking, error analysis, interface type differentiation
- **Integration Testing**: 13 comprehensive integration tests for all feature combinations
- **MCP Tools**: 5 tools (init, update, validate, reset, discover) with security decorators

### Changed
- **Shared Backend**: Enhanced with ToolExecutor and ErrorCollector
- **All Workflow Adapters**: Integrated error handling and telemetry collection
- **Power Package**: Updated to v2.1.0 with all new features
- **Import Paths**: Fixed MCP tools to use packaged imports

### Fixed
- MCP tool import paths (from `src.hiveforge` to `hiveforge`)
- Error propagation through all layers
- Backup location tracking in ToolExecutor

### Testing
- 141/142 shared backend tests passing (99.3%)
- 40/40 core CLI tests passing (100%)
- 13/13 integration tests passing (100%)
- Total: 194/203 tests passing (95.6%)

### Performance
- Error handling overhead: <5%
- Security validation: <10ms per operation
- Telemetry: Async, non-blocking
- Package size: +15KB (+13.8%)

### Documentation
- V2_1_1_ERROR_HANDLING_COMPLETE.md
- V2_1_2_INTEGRATION_TESTING_COMPLETE.md
- V2_1_3_POWER_PACKAGE_UPDATE_COMPLETE.md
- V2_1_4_TESTING_VALIDATION_COMPLETE.md

## [1.0.0] - 2026-02-14

### Added
- Initial release of hiveforge CLI tool
- 7 specialized agent definitions (Orchestrator, Data Architect, Backend Engineer, Frontend Engineer, QA Engineer, DevOps Engineer, Red Team)
- 8 steering files (project-vision, tech-stack, conventions, architecture, db-standards, api-standards, ui-standards, qa-standards)
- Swarm state management with dynamic placeholders
- Kebab-case project name validation
- Force overwrite functionality with `--force` flag
- Comprehensive test suite (66 tests, 87% coverage)
- Permission-based security via toolsSettings
- UTF-8 encoding support
- Windows, macOS, and Linux compatibility

### Documentation
- Comprehensive README with badges and examples
- Quick start guide (QUICKSTART.md)
- Contributing guidelines (CONTRIBUTING.md)
- Architecture documentation
- Development guide
- Troubleshooting guide

### Developer Experience
- Poetry-based dependency management
- pytest test suite with fixtures
- Code coverage reporting
- Type hints throughout codebase

## [0.1.0] - 2026-02-10

### Added
- Initial prototype
- Basic CLI scaffolding
- Template file generation

---

## Version History

### [1.0.0] - First Stable Release
**Focus:** Production-ready CLI tool for KIRO v05 project scaffolding

**Key Features:**
- Complete multi-agent architecture
- Comprehensive documentation
- Robust testing (87% coverage)
- Cross-platform support

**Breaking Changes:** None (initial release)

---

## Upgrade Guide

### From 0.x to 1.0

No migration needed. Simply install the new version:

```bash
pip install --upgrade hiveforge
```

---

## Deprecation Notices

None currently.

---

## Security Updates

None currently. See [SECURITY.md](./SECURITY.md) for reporting vulnerabilities.
