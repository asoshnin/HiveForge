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
