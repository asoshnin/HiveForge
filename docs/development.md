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
├── src/hiveforge/
│   ├── cli.py                    # Main CLI entry point
│   ├── generator.py              # Project scaffolding
│   └── steering/                 # Steering Assistant module
│       ├── agents/               # AI agents
│       │   └── steering_assistant.py
│       ├── analyzers/            # Code & doc analyzers
│       │   ├── code_analyzer.py
│       │   ├── language_detector.py
│       │   ├── tech_stack_extractor.py
│       │   ├── architecture_inferrer.py
│       │   ├── conventions_extractor.py
│       │   └── documentation_parser.py
│       ├── parsers/              # Artifact parsers
│       │   ├── markdown.py
│       │   ├── pdf.py
│       │   ├── image.py
│       │   └── orchestrator.py
│       ├── validators/           # Validation logic
│       │   ├── steering_validator.py
│       │   └── rule_based.py
│       ├── workflows/            # Main workflows
│       │   ├── init_workflow.py
│       │   ├── update_workflow.py
│       │   └── validate_workflow.py
│       ├── cli.py                # Steering CLI commands
│       ├── models.py             # Data models
│       ├── knowledge_base.py     # Knowledge management
│       ├── gap_analysis.py       # Missing info detection
│       ├── template_populator.py # Template filling
│       ├── conflict_resolver.py  # Conflict handling
│       ├── diff_generator.py     # Diff generation
│       ├── customization_detector.py
│       ├── response_cache.py     # LLM response caching
│       ├── error_handling.py     # Error handling
│       └── templates.py          # Template definitions
├── tests/                        # Test suite (863 tests)
├── docs/                         # Documentation
├── pyproject.toml                # Poetry configuration
├── README.md                     # Main documentation
└── .github/                      # GitHub templates (future)
```

---

## Steering Assistant Development

### Architecture Overview

The Steering Assistant is a modular system with clear separation of concerns:

- **Workflows**: High-level orchestration (init, update, validate)
- **Agents**: AI-powered conversation and decision-making
- **Analyzers**: Extract information from code and documentation
- **Parsers**: Read artifacts (markdown, PDF, images)
- **Validators**: Check steering files for completeness
- **Utilities**: Knowledge base, caching, error handling

### Adding New Features

#### Adding a New Analyzer

```python
# src/hiveforge/steering/analyzers/my_analyzer.py
from pathlib import Path
from typing import Dict, Any

class MyAnalyzer:
    """Analyzes X to extract Y."""
    
    def analyze(self, project_root: Path) -> Dict[str, Any]:
        """
        Analyze project and return extracted information.
        
        Args:
            project_root: Root directory of project
            
        Returns:
            Dictionary with extracted information
        """
        # Implementation
        return {"key": "value"}
```

#### Adding a New Validator Rule

```python
# src/hiveforge/steering/validators/rule_based.py
def validate_my_rule(content: str, file_path: Path) -> List[ValidationIssue]:
    """Validate custom rule."""
    issues = []
    # Check for issues
    if problem_detected:
        issues.append(ValidationIssue(
            severity="critical",
            message="Problem description",
            line_number=line_num,
            suggestion="How to fix"
        ))
    return issues
```

#### Adding a New Workflow

```python
# src/hiveforge/steering/workflows/my_workflow.py
from hiveforge.steering.models import SteeringConfig
from pathlib import Path

class MyWorkflow:
    """Custom workflow for X."""
    
    def __init__(self, config: SteeringConfig):
        self.config = config
        
    def execute(self, project_root: Path) -> bool:
        """Execute workflow."""
        # Implementation
        return True
```

### Testing Steering Assistant

#### Unit Tests

```bash
# Test specific module
pytest tests/test_code_analyzer.py -v
pytest tests/test_steering_assistant.py -v
pytest tests/test_init_workflow.py -v

# Test all steering modules
pytest tests/test_*.py -k steering -v
```

#### Integration Tests

```bash
# Test full workflows
pytest tests/test_cli_integration.py -v

# Test with real LLM (requires API key)
export OPENAI_API_KEY=your_key
pytest tests/test_steering_assistant.py::test_real_conversation -v
```

#### Property-Based Tests

```bash
# Run property-based tests (uses Hypothesis)
pytest tests/test_code_analyzer.py::test_property_* -v
```

### Debugging Steering Assistant

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Inspect Response Cache

```bash
# View cached LLM responses
cat .kiro/.cache/response_cache.json | jq
```

#### Test Individual Components

```python
# Test code analyzer
from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
from pathlib import Path

analyzer = CodeAnalyzer()
result = analyzer.analyze(Path("."))
print(result)
```

#### Test Workflows Manually

```bash
# Test init workflow
python -m hiveforge.steering.cli init --analyze-code

# Test with debug output
python -m pdb -m hiveforge.steering.cli init
```

### Performance Optimization

#### Token Usage

Monitor token usage to optimize LLM costs:

```python
# Add token counting
from hiveforge.steering.utils import count_tokens

text = "Your prompt here"
tokens = count_tokens(text)
print(f"Token count: {tokens}")
```

#### Response Caching

The response cache reduces redundant LLM calls:

```python
# Clear cache for testing
import os
os.remove(".kiro/.cache/response_cache.json")
```

#### Code Analysis Performance

For large codebases, use sampling:

```python
# Automatic sampling for >10k files
analyzer = CodeAnalyzer(max_files=1000)
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
