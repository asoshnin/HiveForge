# 🔍 Troubleshooting Guide

Common issues and solutions for **hiveforge**.

---

## Installation Issues

### "pip: command not found"

**Problem:** pip is not installed or not in PATH.

**Solution:**
```bash
# Install pip
python -m ensurepip --upgrade

# Or use python3
python3 -m ensurepip --upgrade
```

### "poetry: command not found"

**Problem:** Poetry is not installed.

**Solution:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Or using pip
pip install poetry
```

### "Python version mismatch"

**Problem:** Python 3.11+ required.

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.11+ from python.org
# Or use pyenv
pyenv install 3.11.5
pyenv global 3.11.5
```

---

## CLI Issues

### "hiveforge: command not found"

**Problem:** CLI not installed or not in PATH.

**Solutions:**

**Option 1:** Install globally
```bash
pip install hiveforge
```

**Option 2:** Use with poetry
```bash
poetry install
poetry run hiveforge --help
```

**Option 3:** Add to PATH
```bash
# Find installation path
pip show hiveforge

# Add to PATH (Linux/Mac)
export PATH="$PATH:/path/to/bin"

# Add to PATH (Windows)
set PATH=%PATH%;C:\path\to\Scripts
```

### "Invalid project name" Error

**Problem:**
```bash
❌ Invalid: 'My Project'. Use kebab-case (e.g., 'my-project')
```

**Solution:** Use kebab-case format:
```bash
# ✅ Valid
hiveforge -n my-project
hiveforge -n awesome-app-123
hiveforge -n app

# ❌ Invalid
hiveforge -n "My Project"      # Spaces
hiveforge -n my_project         # Underscores
hiveforge -n MyProject          # PascalCase
hiveforge -n my.project         # Dots
```

### ".kiro/ exists" Error

**Problem:**
```bash
❌ .kiro/ exists. Use --force to overwrite.
```

**Solutions:**

**Option 1:** Use force flag
```bash
hiveforge -n my-project --force
```

**Option 2:** Remove existing directory
```bash
rm -rf .kiro .swarm swarm_state.md
hiveforge -n my-project
```

**Option 3:** Create in new directory
```bash
mkdir new-project
cd new-project
hiveforge -n new-project
```

---

## File Generation Issues

### "No agent templates found"

**Problem:** Template files are missing.

**Solution:**
```bash
# Reinstall hiveforge
pip uninstall hiveforge
pip install hiveforge

# Or reinstall from source
git clone https://github.com/yourusername/hiveforge.git
cd hiveforge
poetry install
```

### "Permission denied" Error

**Problem:** Insufficient permissions to create files.

**Solutions:**

**Option 1:** Run with appropriate permissions
```bash
# Linux/Mac
sudo hiveforge -n my-project

# Or change directory permissions
chmod +w .
```

**Option 2:** Create in user directory
```bash
cd ~/projects
hiveforge -n my-project
```

### "UTF-8 encoding error"

**Problem:** System doesn't support UTF-8.

**Solution:**
```bash
# Set UTF-8 encoding (Linux/Mac)
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Windows (PowerShell)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

---

## Kiro IDE Integration Issues

### "Kiro IDE doesn't recognize agents"

**Problem:** IDE not detecting `.kiro/` directory.

**Solutions:**

**Option 1:** Reload IDE
```bash
# Restart Kiro IDE or reload window
```

**Option 2:** Verify structure
```bash
# Check directory exists
ls -la .kiro/agents/
ls -la .kiro/steering/

# Should show 7 agent files and 8 steering files
```

**Option 3:** Check file permissions
```bash
# Ensure files are readable
chmod -R +r .kiro/
```

### "toolsSettings not enforced"

**Problem:** Orchestrator can write to `src/`.

**Solution:** Verify `orchestrator.md` has correct toolsSettings:
```yaml
toolsSettings:
  write:
    allowedPaths: ["./docs/**", "./swarm_state.md", "./.kiro/steering/**"]
    deniedPaths: ["./src/**", "./tests/**", "./infra/**"]
```

---

## Performance Issues

### "Generation takes too long"

**Problem:** Project generation is slow (>5 seconds).

**Diagnosis:**
```bash
# Time the generation
time hiveforge -n test-project
```

**Solutions:**

**Option 1:** Check disk speed
```bash
# Test disk write speed
dd if=/dev/zero of=testfile bs=1M count=100
```

**Option 2:** Disable antivirus temporarily
```bash
# Windows Defender may slow file operations
```

**Option 3:** Use SSD instead of HDD

---

## Steering Assistant Issues

### "Steering files already exist" Error

**Problem:**
```bash
❌ Steering files already exist. Use --force to overwrite or backup first.
```

**Solutions:**

**Option 1:** Backup existing files
```bash
# Manual backup
cp -r .kiro/steering .kiro/steering.backup

# Then run init
hiveforge steering init
```

**Option 2:** Use update instead
```bash
# Update existing files instead of recreating
hiveforge steering update
```

**Option 3:** Remove existing files (careful!)
```bash
rm -rf .kiro/steering
hiveforge steering init
```

### "No artifacts found" Warning

**Problem:**
```bash
⚠ No artifacts found in .kiro/onboarding/
```

**Solutions:**

**Option 1:** Add artifacts
```bash
mkdir -p .kiro/onboarding
cp project-spec.md .kiro/onboarding/
cp architecture.pdf .kiro/onboarding/
```

**Option 2:** Use code analysis
```bash
hiveforge steering init --analyze-code
```

**Option 3:** Continue with conversation
```bash
# Just answer questions during interactive mode
hiveforge steering init
```

### "Code analysis timeout" Error

**Problem:**
```bash
❌ Code analysis timed out after 300 seconds
```

**Solutions:**

**Option 1:** Reduce scope
```bash
# Ensure .gitignore excludes large directories
echo "node_modules/" >> .gitignore
echo "venv/" >> .gitignore
echo ".hypothesis/" >> .gitignore
```

**Option 2:** Skip code analysis
```bash
# Use artifacts only
hiveforge steering init --no-interactive
```

**Option 3:** Increase timeout (advanced)
```python
# In code
from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
analyzer = CodeAnalyzer(timeout=600)  # 10 minutes
```

### "LLM API rate limit exceeded" Error

**Problem:**
```bash
❌ Rate limit exceeded. Retrying in 2 seconds...
```

**Solutions:**

**Option 1:** Wait for automatic retry
```bash
# The system will retry with exponential backoff
# Just wait a few minutes
```

**Option 2:** Use cached responses
```bash
# Check if responses are cached
cat .kiro/.cache/response_cache.json
```

**Option 3:** Reduce API calls
```bash
# Use non-interactive mode
hiveforge steering init --no-interactive --analyze-code
```

### "Validation failed" Error

**Problem:**
```bash
❌ Validation FAILED (3 critical issues)
```

**Solutions:**

**Option 1:** Review validation report
```bash
# Read the detailed report
hiveforge steering validate
```

**Option 2:** Fix issues manually
```bash
# Edit steering files to fix reported issues
vim .kiro/steering/tech-stack.md
```

**Option 3:** Skip validation temporarily
```bash
# Skip validation during development
hiveforge steering init --skip-validation
```

### "PDF parsing failed" Error

**Problem:**
```bash
❌ Failed to parse architecture.pdf: Encrypted or corrupted
```

**Solutions:**

**Option 1:** Check PDF encryption
```bash
# Remove password protection
# Use Adobe Acrobat or online tools
```

**Option 2:** Convert to markdown
```bash
# Use pandoc or online converters
pandoc architecture.pdf -o architecture.md
cp architecture.md .kiro/onboarding/
```

**Option 3:** Extract text manually
```bash
# Copy text from PDF and create markdown file
cat > .kiro/onboarding/architecture.md << EOF
# Architecture
...
EOF
```

### "Image OCR failed" Error

**Problem:**
```bash
❌ Failed to extract text from diagram.png: tesseract not found
```

**Solutions:**

**Option 1:** Install tesseract
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Option 2:** Convert image to text manually
```bash
# Describe the image in markdown
cat > .kiro/onboarding/diagram.md << EOF
# Architecture Diagram
- Component A connects to Component B
- Database is PostgreSQL
...
EOF
```

**Option 3:** Skip image parsing
```bash
# Remove images from onboarding folder
rm .kiro/onboarding/*.png .kiro/onboarding/*.jpg
```

### "Customizations not preserved" Issue

**Problem:** Manual edits to steering files are overwritten during update.

**Solutions:**

**Option 1:** Review diff before accepting
```bash
# Carefully review proposed changes
hiveforge steering update
# Choose "Review" option to see detailed diffs
```

**Option 2:** Backup before update
```bash
cp -r .kiro/steering .kiro/steering.backup
hiveforge steering update
```

**Option 3:** Report issue
```bash
# If customizations should have been preserved, report bug
# Include before/after files
```

### "Conversation takes too long" Issue

**Problem:** Too many questions during interactive mode.

**Solutions:**

**Option 1:** Use code analysis
```bash
# Auto-extract most information
hiveforge steering init --analyze-code
```

**Option 2:** Add more artifacts
```bash
# Provide comprehensive documentation
cp README.md .kiro/onboarding/
cp docs/*.md .kiro/onboarding/
```

**Option 3:** Use non-interactive mode
```bash
# Skip conversation entirely
hiveforge steering init --no-interactive --analyze-code
```

### "Inconsistent information" Warning

**Problem:**
```bash
⚠ Inconsistency detected: tech-stack.md says "PostgreSQL 14" but architecture.md says "PostgreSQL 15"
```

**Solutions:**

**Option 1:** Resolve during validation
```bash
hiveforge steering validate
# Follow prompts to resolve inconsistencies
```

**Option 2:** Fix manually
```bash
# Edit files to ensure consistency
vim .kiro/steering/tech-stack.md
vim .kiro/steering/architecture.md
```

**Option 3:** Re-run update
```bash
# Update with correct information
echo "PostgreSQL 15" > .kiro/onboarding/db-version.txt
hiveforge steering update
```

---

## Common Questions (FAQ)

### Q: Can I customize agent definitions?

**A:** Yes, but not recommended. Instead:
1. Generate project with `hiveforge`
2. Edit `.kiro/agents/` files after generation
3. Don't use `--force` to avoid overwriting your changes

### Q: Can I add more agents?

**A:** Yes, manually create new `.md` files in `.kiro/agents/`:
```bash
# Create custom agent
cat > .kiro/agents/security_engineer.md << EOF
# Security Engineer

**Role:** Security audits and penetration testing
...
EOF
```

### Q: Can I use different tech stacks?

**A:** Currently, templates are generic. Edit `.kiro/steering/tech-stack.md` after generation. Tech-stack variants planned for v2.0.

### Q: Can I use this without Kiro IDE?

**A:** Yes! The generated files are just markdown. You can use them with any IDE or text editor. IDE-agnostic mode planned for v2.0.

### Q: How does the Steering Assistant work?

**A:** The Steering Assistant:
1. Analyzes your codebase (if --analyze-code is used)
2. Parses artifacts from .kiro/onboarding/
3. Identifies missing information
4. Asks targeted questions (if interactive)
5. Generates steering files from templates
6. Validates generated files

### Q: What artifacts can I provide?

**A:** Supported formats:
- **Markdown** (.md): Project specs, requirements, documentation
- **PDF** (.pdf): Architecture diagrams, design docs
- **Images** (.png, .jpg): Screenshots, diagrams (requires tesseract)

### Q: How do I preserve my customizations?

**A:** The update workflow automatically detects and preserves customizations:
- Custom sections you added
- Modified content beyond placeholder replacements
- Additional formatting and structure

Always review diffs before accepting changes.

### Q: Can I use Steering Assistant in CI/CD?

**A:** Yes! Use non-interactive mode with strict validation:
```bash
hiveforge steering validate --strict
```

Exit code 0 = success, 1 = failure.

### Q: How much does it cost (LLM API)?

**A:** Token usage is optimized:
- Init: ~10-20K tokens (depends on project size)
- Update: ~3-5K tokens per file
- Validate: No LLM calls (local validation)

Response caching reduces costs for repeated operations.

### Q: How do I update hiveforge?

**A:**
```bash
pip install --upgrade hiveforge
```

### Q: Where are templates stored?

**A:**
```bash
# Find installation path
pip show hiveforge

# Templates are in:
# <site-packages>/hiveforge/templates/
```

### Q: Can I contribute custom templates?

**A:** Yes! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## Error Messages Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid: 'X'. Use kebab-case` | Invalid project name | Use lowercase, hyphens only |
| `.kiro/ exists` | Project already initialized | Use `--force` flag |
| `No agent templates found` | Missing template files | Reinstall hiveforge |
| `Permission denied` | Insufficient permissions | Run with sudo or change directory |
| `command not found` | CLI not in PATH | Install globally or use `poetry run` |

---

## Debug Mode

### Enable Verbose Output

```bash
# Run with Python's verbose mode
python -v -m hiveforge.cli -n my-project

# Or use pytest for debugging
pytest tests/test_cli.py::TestCLI::test_generate_project_with_name_flag -vv -s
```

### Check Installation

```bash
# Verify package is installed
pip show hiveforge

# Check CLI entry point
which hiveforge  # Linux/Mac
where hiveforge  # Windows

# Test import
python -c "import hiveforge; print(hiveforge.__version__)"
```

---

## Getting Help

If you're still stuck:

1. **Search existing issues:** [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
2. **Ask in Discord:** [Join community](https://discord.gg/your-invite)
3. **Create new issue:** Include:
   - OS and Python version
   - Full error message
   - Steps to reproduce
   - Output of `pip show hiveforge`

---

## Reporting Bugs

When reporting bugs, include:

```bash
# System information
python --version
pip --version
pip show hiveforge

# Error output
hiveforge -n test-project 2>&1 | tee error.log

# Directory structure
tree -L 2 .kiro/
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for bug report template.
