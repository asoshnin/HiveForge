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
