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
