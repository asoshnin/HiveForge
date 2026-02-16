# 🤝 Contributing to hiveforge

Thank you for your interest in contributing to **hiveforge**! This document provides guidelines and instructions for contributing.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

---

## 📜 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Our Standards

**✅ Positive Behavior:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**❌ Unacceptable Behavior:**
- Trolling, insulting/derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- Poetry (package manager)
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/asoshnin/HiveForge.git
cd hiveforge
```

### Install Dependencies

```bash
# Install with development dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Verify Setup

```bash
# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src/hiveforge --cov-report=term

# Run the CLI
hiveforge --help
```

---

## 🔄 Development Workflow

### 1. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/issue-123
```

### 2. Make Changes

- Write clean, readable code
- Follow coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_cli.py -v

# Check coverage
pytest tests/ --cov=src/hiveforge --cov-report=term-missing
```

### 4. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat: add support for custom template directories"
```

**Commit Message Format:**

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 5. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
```

---

## 📏 Coding Standards

### Python Style

- **PEP 8** compliance
- **Type hints** for all function signatures
- **Docstrings** for all public functions/classes
- **Line length:** 100 characters max

**Example:**

```python
def validate_project_name(name: Optional[str]) -> str:
    """Validate project name follows kebab-case format.
    
    Args:
        name: Project name to validate
        
    Returns:
        Validated project name
        
    Raises:
        ValueError: If name is empty or invalid format
    """
    if not name:
        raise ValueError("Project name cannot be empty")
    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
        raise ValueError(f"Invalid: '{name}'. Use kebab-case (e.g., 'my-project')")
    return name
```

### File Organization

```
src/hiveforge/
├── __init__.py          # Package metadata
├── cli.py               # CLI entry point
├── validators.py        # Input validation
├── generator.py         # Project scaffolding
└── templates/           # Agent & steering templates
    ├── agents/
    ├── steering/
    └── swarm_state.md
```

### Naming Conventions

- **Modules:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions:** `snake_case()`
- **Constants:** `SCREAMING_SNAKE_CASE`
- **Private:** `_leading_underscore`

---

## 🧪 Testing Guidelines

### Test Structure

```python
class TestFeatureName:
    """Test suite for feature description."""
    
    def test_specific_behavior(self, fixtures):
        """Test description following AAA pattern."""
        # Arrange
        input_data = "test-project"
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected_output
```

### Coverage Requirements

- **Minimum:** 80% coverage
- **Target:** 90%+ coverage
- **Critical paths:** 100% coverage (validators, CLI)

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_validators.py -v

# Specific test
pytest tests/test_cli.py::TestCLI::test_help_command -v

# With coverage
pytest tests/ --cov=src/hiveforge --cov-report=html

# Fast (skip slow tests)
pytest tests/ -v -m "not slow"
```

### Writing Good Tests

**✅ Do:**
- Test one thing per test
- Use descriptive test names
- Use fixtures for common setup
- Test edge cases and error paths
- Keep tests fast (<1s each)

**❌ Don't:**
- Test implementation details
- Use hard-coded paths
- Depend on external services
- Share state between tests

---

## 🔀 Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Coverage is ≥80%
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with `main`

### PR Checklist

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Coverage maintained/improved

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. **Automated Checks** - CI runs tests, linting, coverage
2. **Code Review** - Maintainer reviews code quality
3. **Feedback** - Address review comments
4. **Approval** - Maintainer approves PR
5. **Merge** - Squash and merge to `main`

---

## 🚢 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes

### Release Steps

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release commit
4. Tag release: `git tag v1.2.3`
5. Push tag: `git push origin v1.2.3`
6. GitHub Actions builds and publishes to PyPI

---

## 🐛 Reporting Bugs

### Before Reporting

- Search existing issues
- Verify it's reproducible
- Collect relevant information

### Bug Report Template

```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
1. Run `hiveforge -n test-project`
2. See error

**Expected behavior**
What should happen

**Actual behavior**
What actually happens

**Environment:**
- OS: Windows 11
- Python: 3.11.5
- hiveforge: 1.0.0

**Additional context**
Any other relevant information
```

---

## 💡 Feature Requests

### Before Requesting

- Check if it aligns with project goals
- Search existing feature requests
- Consider if it can be a plugin/extension

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Clear description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other approaches you've thought about

**Additional context**
Mockups, examples, etc.
```

---

## 📞 Getting Help

- 💬 **Discord:** [Join our community](https://discord.gg/your-invite)
- 📧 **Email:** 89580632+asoshnin@users.noreply.github.com
- 🐛 **Issues:** [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
- 💡 **Discussions:** [GitHub Discussions](https://github.com/asoshnin/HiveForge/discussions)

---

## 🙏 Recognition

Contributors are recognized in:
- `README.md` acknowledgments
- GitHub contributors page
- Release notes

---

<div align="center">

**Thank you for contributing to hiveforge!** 🎉

Your contributions help make multi-agent development accessible to everyone.

</div>
