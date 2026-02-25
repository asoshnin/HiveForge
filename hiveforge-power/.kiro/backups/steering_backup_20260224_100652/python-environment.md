---
inclusion: always
priority: 1
description: "Python virtual environment requirements for all Python operations"
---

# Python Environment Standards

## Virtual Environment Usage

**CRITICAL:** Always check if venv is activated before running Python commands.

### Before Running Any Python Command:
1. Check if `VIRTUAL_ENV` environment variable is set
2. If not set and venv exists (`.venv/` or `venv/`), activate it first
3. Commands requiring venv: `pytest`, `pip install`, `python -m`, package imports

### Activation Commands:
- **Windows:** `.venv\Scripts\activate` or `source .venv/Scripts/activate` (bash)
- **Linux/Mac:** `source .venv/bin/activate`

### When to Remind User:
- Before running tests (`pytest`)
- Before installing packages (`pip install`)
- Before running Python scripts that import project code
- If import errors occur (may indicate wrong Python environment)

### Detection:
Check for venv activation by looking for `VIRTUAL_ENV` in environment or `(.venv)` in shell prompt.