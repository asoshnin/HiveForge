# Installation Verification Checklist

**Purpose**: Step-by-step checklist to verify HiveForge installation is complete and working.

**Use this checklist after following the INSTALLATION_GUIDE.md**

---

## Prerequisites Verification

### ✅ Python Version

```bash
python --version
# or
python3 --version
```

**Expected**: `Python 3.11.x` or higher

- [ ] Python 3.11+ installed
- [ ] Version displays correctly

---

### ✅ Git Installation

```bash
git --version
```

**Expected**: `git version 2.x.x`

- [ ] Git installed
- [ ] Version displays correctly

---

### ✅ Pip Installation

```bash
pip --version
# or
pip3 --version
```

**Expected**: `pip 23.x.x`

- [ ] Pip installed
- [ ] Version displays correctly

---

## Repository Setup

### ✅ Clone Repository

```bash
cd ~/projects
ls HiveForge
```

**Expected**: Directory exists with project files

- [ ] Repository cloned successfully
- [ ] Can navigate to HiveForge directory
- [ ] Files visible: `pyproject.toml`, `README.md`, `hiveforge-power/`

---

### ✅ Virtual Environment

```bash
cd ~/projects/HiveForge
ls venv
```

**Expected**: `venv/` directory exists

- [ ] Virtual environment created
- [ ] Directory contains: `bin/` (macOS/Linux) or `Scripts/` (Windows)

---

### ✅ Activate Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate.bat
```

**Expected**: Prompt shows `(venv)` prefix

- [ ] Virtual environment activated
- [ ] Prompt shows `(venv)`

---

## CLI Installation Verification

### ✅ HiveForge Package Installed

```bash
pip list | grep hiveforge
```

**Expected**: Shows `hiveforge` with version number

- [ ] Package appears in pip list
- [ ] Version number displayed

---

### ✅ HiveForge Command Available

```bash
hiveforge --help
```

**Expected**: Help message displays

```
Usage: hiveforge [OPTIONS]

  Scaffold KIRO Methodology v05 projects

Options:
  -n, --project-name TEXT  Project name (kebab-case)
  -f, --force             Overwrite existing project
  --help                  Show this message and exit.
```

- [ ] Command runs without errors
- [ ] Help message displays
- [ ] Options listed correctly

---

### ✅ CLI Functional Test

```bash
mkdir ~/test-hiveforge
cd ~/test-hiveforge
hiveforge -n test-project
```

**Expected**: Project structure created

- [ ] Command completes without errors
- [ ] `.kiro/` directory created
- [ ] `.kiro/agents/` contains 7 agent files
- [ ] `.kiro/steering/` contains 8 steering files
- [ ] `.swarm/` directory created
- [ ] `swarm_state.md` file created

**Verify specific files:**
```bash
ls .kiro/agents/
# Should show: orchestrator.md, data_architect.md, backend_engineer.md, 
#              frontend_engineer.md, qa_engineer.md, devops_engineer.md, red_team.md

ls .kiro/steering/
# Should show: project-vision.md, tech-stack.md, conventions.md, architecture.md,
#              db-standards.md, api-standards.md, ui-standards.md, qa-standards.md
```

- [ ] All 7 agent files present
- [ ] All 8 steering files present
- [ ] Files contain content (not empty)

---

### ✅ CLI Steering Commands

```bash
cd ~/test-hiveforge
hiveforge steering --help
```

**Expected**: Steering subcommands listed

- [ ] `init` command available
- [ ] `update` command available
- [ ] `validate` command available

---

## MCP Server Installation Verification

**Skip this section if you only installed the CLI.**

### ✅ MCP Server Package Installed

```bash
cd ~/projects/HiveForge
source venv/bin/activate  # if not already active
pip list | grep hiveforge-steering-mcp
```

**Expected**: Shows `hiveforge-steering-mcp` with version number

- [ ] Package appears in pip list
- [ ] Version 2.1.0 or higher

---

### ✅ MCP Server Command Available

```bash
hiveforge-steering-mcp --help
```

**Expected**: Help message displays

- [ ] Command runs without errors
- [ ] Help message displays

---

### ✅ MCP Server Module Accessible

```bash
cd ~/projects/HiveForge/hiveforge-power
python -c "import mcp_server.server; print('Module found')"
```

**Expected**: Prints "Module found"

- [ ] Module imports successfully
- [ ] No import errors

---

### ✅ MCP Server Dependencies

```bash
pip list | grep -E "(fastmcp|pydantic|typer)"
```

**Expected**: All three packages listed

- [ ] `fastmcp` installed
- [ ] `pydantic` installed (version 2.0+)
- [ ] `typer` installed

---

## KIRO Configuration Verification

**Skip this section if you only installed the CLI.**

### ✅ KIRO Settings Directory

```bash
ls ~/.kiro/settings/
```

**Expected**: Directory exists

- [ ] Directory exists
- [ ] Can list contents

---

### ✅ MCP Configuration File

```bash
cat ~/.kiro/settings/mcp.json
```

**Expected**: JSON file with hiveforge-steering configuration

- [ ] File exists
- [ ] Contains `"mcpServers"` key
- [ ] Contains `"hiveforge-steering"` entry
- [ ] `"disabled"` is `false`

---

### ✅ Configuration Syntax Valid

```bash
python -m json.tool ~/.kiro/settings/mcp.json
```

**Expected**: JSON formatted output (no errors)

- [ ] JSON is valid
- [ ] No syntax errors

---

### ✅ Python Path Correct (Local Development)

**If using local installation (not uvx):**

```bash
# Check the path in your config
cat ~/.kiro/settings/mcp.json | grep command

# Verify that path exists
ls /path/from/config/python
```

**Expected**: Python executable exists at specified path

- [ ] Path in config is absolute
- [ ] Python executable exists at that path
- [ ] Path points to venv Python (not system Python)

---

### ✅ Module Path Correct

**Check your mcp.json has:**
```json
"args": ["-m", "mcp_server.server"]
```

**NOT:**
```json
"args": ["-m", "hiveforge_power.server"]  // WRONG
```

- [ ] Args use `mcp_server.server`
- [ ] Args format is correct: `["-m", "mcp_server.server"]`

---

## KIRO Power Verification

**Skip this section if you only installed the CLI.**

### ✅ KIRO Restart

- [ ] KIRO IDE closed completely
- [ ] KIRO IDE reopened
- [ ] Waited 10-15 seconds for servers to connect

---

### ✅ MCP Server Connection

**In KIRO IDE:**

- [ ] MCP server indicator visible in UI
- [ ] "hiveforge-steering" shows as connected
- [ ] No connection errors in KIRO logs

---

### ✅ Power Activation Test

**In KIRO chat, type:**
```
Can you help me create steering files?
```

**Expected**: Power responds with information about steering files

- [ ] Power responds (not generic response)
- [ ] Response mentions steering files
- [ ] Response offers to help

---

### ✅ Power Tool Test - Init

**In KIRO chat, type:**
```
Initialize steering files for my project
```

**Expected**: Power uses `init_steering` tool

- [ ] Power acknowledges request
- [ ] Tool execution starts
- [ ] Files created in `.kiro/steering/`
- [ ] Success message displayed

**Verify files created:**
```bash
ls .kiro/steering/
```

- [ ] `tech-stack.md` created
- [ ] `architecture.md` created
- [ ] `conventions.md` created
- [ ] `project-vision.md` created
- [ ] Files contain generated content (not just templates)

---

### ✅ Power Tool Test - Validate

**In KIRO chat, type:**
```
Validate my steering files
```

**Expected**: Power uses `validate_steering` tool

- [ ] Power runs validation
- [ ] Validation results displayed
- [ ] Shows number of files checked
- [ ] Shows any issues found

---

### ✅ Power Tool Test - Discover

**In KIRO chat, type:**
```
Discover existing documentation in my project
```

**Expected**: Power uses `discover_docs` tool

- [ ] Power scans project
- [ ] Lists discovered files
- [ ] Shows discovery statistics

---

## Shared Backend Verification

### ✅ CLI and Power Output Equivalence

**Test 1: Create files with CLI**
```bash
cd ~/test-cli
hiveforge steering init
cat .kiro/steering/tech-stack.md
```

**Test 2: Create files with Power**
```
In KIRO: "Initialize steering files"
Check .kiro/steering/tech-stack.md
```

**Expected**: Files should have similar structure and quality

- [ ] Both methods create files
- [ ] File structure is similar
- [ ] Content quality is comparable
- [ ] No major differences in output

---

## Troubleshooting Verification

### ✅ Error Handling Test

**Test invalid project name:**
```bash
hiveforge -n "Invalid Name"
```

**Expected**: Clear error message about kebab-case

- [ ] Error message displayed
- [ ] Message explains the issue
- [ ] Suggests correct format

---

### ✅ Help System Test

```bash
hiveforge --help
hiveforge steering --help
hiveforge steering init --help
```

**Expected**: Help displays for all commands

- [ ] Main help works
- [ ] Subcommand help works
- [ ] Command-specific help works

---

## Final Verification

### ✅ Complete Installation Checklist

**CLI Installation:**
- [ ] Python 3.11+ installed
- [ ] Repository cloned
- [ ] Virtual environment created and activated
- [ ] HiveForge CLI installed
- [ ] CLI commands work
- [ ] Can create test projects
- [ ] Steering commands available

**MCP Server Installation (if applicable):**
- [ ] MCP server package installed
- [ ] MCP server command works
- [ ] Dependencies installed
- [ ] Module imports successfully

**KIRO Integration (if applicable):**
- [ ] KIRO settings directory exists
- [ ] mcp.json configured correctly
- [ ] JSON syntax valid
- [ ] Paths correct
- [ ] KIRO restarted
- [ ] MCP server connected
- [ ] Power activates on keywords
- [ ] Power tools work
- [ ] Files generated successfully

---

## Quick Troubleshooting

### If CLI doesn't work:

1. Check virtual environment is activated: `(venv)` in prompt
2. Reinstall: `pip install -e .`
3. Check Python version: `python --version`

### If MCP server doesn't work:

1. Check package installed: `pip list | grep hiveforge-steering-mcp`
2. Check module exists: `ls hiveforge-power/mcp_server/server.py`
3. Reinstall: `cd hiveforge-power && pip install -e .`

### If Power doesn't activate:

1. Check mcp.json exists: `cat ~/.kiro/settings/mcp.json`
2. Validate JSON: `python -m json.tool ~/.kiro/settings/mcp.json`
3. Check Python path is correct
4. Restart KIRO completely
5. Wait 15 seconds after restart

### If Power tools fail:

1. Check you're in a valid project directory
2. Check write permissions: `ls -la .kiro/`
3. Check MCP server logs in KIRO
4. Test module directly: `python -m mcp_server.server`

---

## Success Criteria

✅ **Installation is successful if:**

1. CLI commands run without errors
2. Can create test projects with CLI
3. MCP server package installed (if needed)
4. KIRO recognizes the Power (if needed)
5. Power responds to keywords (if needed)
6. Power tools create files successfully (if needed)
7. No critical errors in any step

---

## Getting Help

If any step fails:

1. **Check the Troubleshooting section** in INSTALLATION_GUIDE.md
2. **Review error messages** carefully
3. **Check file paths** are correct
4. **Verify Python version** is 3.11+
5. **Try reinstalling** in a fresh virtual environment
6. **Open an issue**: https://github.com/asoshnin/HiveForge/issues

---

## Report Issues

When reporting installation issues, include:

- [ ] Operating system and version
- [ ] Python version: `python --version`
- [ ] Installation method used (CLI only, or CLI + Power)
- [ ] Which step failed (reference checklist item)
- [ ] Complete error message
- [ ] Output of: `pip list | grep hiveforge`
- [ ] Contents of mcp.json (if using Power)

---

**Checklist Version**: 1.0  
**Last Updated**: February 18, 2026  
**Compatible with**: HiveForge 1.0.0, Power 2.1.0
