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
- Performance benchmarking suite
- Security audit automation

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
