# 🔧 Development Guide

This guide helps you set up a development environment and contribute to **hiveforge**.

---

## Quick Setup

```bash
# Clone repository
git clone https://github.com/asoshnin/HiveForge.git
cd hiveforge

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Verify setup
pytest tests/ -v
```

---

## Development Environment

### Prerequisites

- **Python:** 3.11 or higher
- **Poetry:** Latest version
- **Git:** Latest version
- **IDE:** VS Code, PyCharm, or your preferred editor

### Recommended VS Code Extensions

- Python (Microsoft)
- Pylance
- Python Test Explorer
- autoDocstring
- GitLens

---

## Project Structure

```
hiveforge/
├── src/hiveforge/        # Source code
├── tests/                # Test suite
├── docs/                 # Documentation
├── pyproject.toml        # Poetry configuration
├── README.md             # Main documentation
└── .github/              # GitHub templates (future)
```

---

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Specific Test File

```bash
pytest tests/test_cli.py -v
```

### With Coverage

```bash
pytest tests/ --cov=src/hiveforge --cov-report=term-missing
```

### Generate HTML Coverage Report

```bash
pytest tests/ --cov=src/hiveforge --cov-report=html
# Open htmlcov/index.html in browser
```

### Watch Mode (Auto-run on changes)

```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
ptw tests/
```

---

## Code Style

### Linting

```bash
# Install ruff (recommended)
pip install ruff

# Run linter
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/
```

### Formatting

```bash
# Install black
pip install black

# Format code
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Type Checking

```bash
# Install mypy
pip install mypy

# Run type checker
mypy src/
```

---

## Building and Installing Locally

### Build Package

```bash
poetry build
```

### Install Locally

```bash
# Install in editable mode
pip install -e .

# Test CLI
hiveforge --help
```

### Uninstall

```bash
pip uninstall hiveforge
```

---

## Debugging

### Using pytest with pdb

```bash
# Drop into debugger on failure
pytest tests/ --pdb

# Drop into debugger on first failure
pytest tests/ -x --pdb
```

### Using VS Code Debugger

Add to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    },
    {
      "name": "Python: pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Common Development Tasks

### Adding a New Feature

1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Update documentation
5. Run tests and linting
6. Submit PR

### Fixing a Bug

1. Write failing test that reproduces bug
2. Fix the bug
3. Verify test passes
4. Add regression test
5. Submit PR

### Updating Templates

1. Edit files in `src/hiveforge/templates/`
2. Test with: `hiveforge -n test-project --force`
3. Verify generated files
4. Update tests if needed

---

## Release Checklist

- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Git tag created
- [ ] PyPI package published

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'hiveforge'"

**Solution:** Install in editable mode:
```bash
pip install -e .
```

### "pytest: command not found"

**Solution:** Activate virtual environment:
```bash
poetry shell
```

### Tests fail with "FileNotFoundError"

**Solution:** Ensure you're in project root:
```bash
cd /path/to/hiveforge
pytest tests/ -v
```

---

## Resources

- **Poetry Docs:** https://python-poetry.org/docs/
- **pytest Docs:** https://docs.pytest.org/
- **Typer Docs:** https://typer.tiangolo.com/
- **Python Packaging:** https://packaging.python.org/

---

## Getting Help

- 💬 **Discord:** [Join our community](https://discord.gg/your-invite)
- 🐛 **Issues:** [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
- 📧 **Email:** 89580632+asoshnin@users.noreply.github.com
