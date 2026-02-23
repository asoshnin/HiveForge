# Installation Guide for HiveForge

## Overview

HiveForge provides two ways to work with steering files:

1. **CLI Tool** - Standalone command-line interface
2. **KIRO Power** - Integrated AI assistant within KIRO IDE

This guide covers installation of both components from source code (not PyPI).

---

## Understanding the Packages

HiveForge consists of **two separate packages**:

| Package | Purpose | Command | When to Use |
|---------|---------|---------|-------------|
| **hiveforge** | CLI tool for scaffolding and steering files | `hiveforge` | Standalone use, CI/CD, scripts |
| **hiveforge-steering-mcp** | MCP server for KIRO Power integration | `hiveforge-steering-mcp` | KIRO IDE integration |

**Key Points**:
- Both packages use the **same shared backend** - identical outputs
- You can install one or both depending on your needs
- CLI works independently; Power requires KIRO IDE
- Installing the Power also gives you CLI access to MCP tools

---

## Prerequisites

Before installing HiveForge, ensure you have:

- **Python 3.11 or higher** - [Download from python.org](https://www.python.org/downloads/)
- **Git** - [Download from git-scm.com](https://git-scm.com/downloads)
- **pip** - Usually comes with Python
- **KIRO IDE** (optional) - Only needed for Power integration
- **Internet connection** - To clone the repository

### Verify Prerequisites

```bash
# Check Python version (must be 3.11+)
python --version
# or
python3 --version

# Check pip
pip --version
# or
pip3 --version

# Check git
git --version
```

**Expected output:**
```
Python 3.11.5 (or higher, but do not use 3.14 or above)
pip 23.x.x
git version 2.x.x
```

---

## Quick Start (Experienced Users)

```bash
# Clone repository
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge

# Install CLI
 py -3.12 -m venv venv # or whatever version between 11 and 13 which is installed on your pc
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -e .

# Install MCP Server (for KIRO Power)
cd hiveforge-power
pip install -e .
cd ..

# Configure KIRO (create or edit ~/.kiro/settings/mcp.json)
# See "Configuring KIRO MCP Settings" section below

# Verify
hiveforge --help
hiveforge-steering-mcp --help
```

---

## Detailed Installation Steps

### Step 1: Clone HiveForge Repository

```bash
# Navigate to where you want to store HiveForge
cd ~/projects  # or any directory you prefer

# Clone the repository
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge
```

**What you should see:**
```
Cloning into 'HiveForge'...
remote: Enumerating objects: 1234, done.
remote: Counting objects: 100% (1234/1234), done.
```

---

### Step 2: Create Virtual Environment

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

**Windows (Command Prompt):**
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Your prompt should now show (venv)
```

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\Activate.ps1

# Your prompt should now show (venv)
```

**⚠️ Important**: Keep this virtual environment activated for all subsequent steps.

---

### Step 3: Install HiveForge CLI

```bash
# Make sure you're in the HiveForge root directory
# and virtual environment is activated (you should see (venv) in prompt)

# Install in editable mode
pip install -e .
```

**What you should see:**
```
Successfully installed hiveforge-1.0.0
```

**Verify CLI installation:**
```bash
hiveforge --help
```

**Expected output:**
```
Usage: hiveforge [OPTIONS]

  Scaffold KIRO Methodology v05 projects

Options:
  -n, --project-name TEXT  Project name (kebab-case)
  -f, --force             Overwrite existing project
  --help                  Show this message and exit.
```

✅ **CLI Installation Complete!**

---

### Step 4: Install MCP Server Package (For KIRO Power)

**Skip this step if you only want the CLI tool.**

```bash
# Navigate to the Power package directory
cd hiveforge-power

# Install the MCP server package (venv should still be activated)
pip install -e .
```

**What you should see:**
```
Successfully installed hiveforge-steering-mcp-2.1.0 fastmcp-0.1.0 pydantic-2.0.0
```

**Verify MCP server installation:**
```bash
hiveforge-steering-mcp --help
```

**Expected output:**
```
Usage: hiveforge-steering-mcp [OPTIONS]

  HiveForge Steering MCP Server

Options:
  --help  Show this message and exit.
```

**Return to root directory:**
```bash
cd ..
```

✅ **MCP Server Installation Complete!**

---

### Step 5: Configure KIRO MCP Settings

**Skip this step if you only want the CLI tool.**

KIRO needs to know about the MCP server. You'll configure this in KIRO's MCP settings file.

**⚠️ IMPORTANT**: The MCP configuration should be placed in **your target project's folder** (the project you want to use HiveForge with), NOT in the HiveForge installation folder.

**Example**: If you want to use HiveForge with a project at `D:\Users\asosh\playground\_KIRO\VeriQ_MVP`, you'll create the config file at `D:\Users\asosh\playground\_KIRO\VeriQ_MVP\.kiro\settings\mcp.json`

#### Option A: Using uvx (Recommended for Production)

**Note**: This option requires the package to be published to PyPI. Since HiveForge is not yet published, use Option B for local development.

Create or edit `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "hiveforge-steering": {
      "command": "uvx",
      "args": ["hiveforge-steering-mcp@latest"],
      "disabled": false,
      "autoApprove": ["init_steering", "update_steering", "validate_steering"]
    }
  }
}
```

#### Option B: Using Local Installation (For Development)

Create or edit `~/.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "hiveforge-steering": {
      "command": "/absolute/path/to/HiveForge/venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "disabled": false,
      "autoApprove": ["init_steering", "update_steering", "validate_steering"]
    }
  }
}
```
(!!! Could be different, see below for MAC)
```
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {},
      "disabled": true,
      "autoApprove": []
    },
    "hiveforge-steering": {
      "command": "/absolute/path/to/HiveForge/venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "disabled": false,
      "autoApprove": ["init_steering", "update_steering", "validate_steering"]
    }
  }
}
```
or for windows:
```
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "env": {},
      "disabled": true,
      "autoApprove": []
    },
    "hiveforge-steering": {
      "command": "/absolute/path/to/HiveForge/venv/Scripts/python.exe",
      "args": ["-m", "mcp_server.server"],
      "disabled": false,
      "autoApprove": ["init_steering", "update_steering", "validate_steering"]
    }
  }
}
```

**⚠️ Important**: Replace `/absolute/path/to/HiveForge/` with your actual path.

**To find your path:**

**macOS/Linux:**
```bash
cd ~/projects/HiveForge
pwd
# Copy the output and use it in the config
```

**Windows:**
```cmd
cd C:\Users\YourName\projects\HiveForge
cd
# Copy the output and use it in the config
# Replace backslashes with forward slashes in JSON
```

**Example for macOS:**
```json
{
  "mcpServers": {
    "hiveforge-steering": {
      "command": "/Users/john/projects/HiveForge/venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "disabled": false,
      "autoApprove": ["init_steering", "update_steering", "validate_steering"]
    }
  }
}
```

**Example for Windows:**
```json
{
  "mcpServers": {
    "hiveforge-steering": {
      "command": "C:/Users/john/projects/HiveForge/venv/Scripts/python.exe",
      "args": ["-m", "mcp_server.server"],
      "disabled": false,
      "autoApprove": ["init_steering", "update_steering", "validate_steering"]
    }
  }
}
```

#### Configuration Options Explained

- **`command`**: Path to Python interpreter in your virtual environment
- **`args`**: Arguments to run the MCP server module
- **`disabled`**: Set to `false` to enable the server
- **`autoApprove`**: Tools that don't require user confirmation

#### Create the Config File

**⚠️ CRITICAL**: Create this file in **your target project**, not in the HiveForge folder!

**Steps:**

1. **Open your target project in KIRO IDE** (e.g., `D:\Users\asosh\playground\_KIRO\VeriQ_MVP`)
2. **Create the config file in that project**:

**macOS/Linux:**
```bash
# Navigate to YOUR project (not HiveForge!)
cd /path/to/your/project

# Create directory if it doesn't exist
mkdir -p .kiro/settings

# Create or edit the file
nano .kiro/settings/mcp.json
# or use your preferred editor: vim, code, etc.
```

**Windows:**
```cmd
# Navigate to YOUR project (not HiveForge!)
cd D:\Users\asosh\playground\_KIRO\VeriQ_MVP

# Create directory if it doesn't exist
mkdir .kiro\settings

# Create or edit the file
notepad .kiro\settings\mcp.json
```

3. **Paste the configuration** from Option B above (with your correct HiveForge installation path)
4. **Save and close**
5. **Restart KIRO** or reload the MCP server from the MCP Server view

✅ **KIRO Configuration Complete!**

---

### Step 6: Register the Power in KIRO

The Power must be manually registered in KIRO's Powers panel.

**In KIRO IDE:**

1. Open the **Powers** panel (sidebar)
2. Go to **Installed** tab
3. Click **"Add Custom Power"** button
4. Select **"Local folder"**
5. Navigate to: `/path/to/HiveForge/hiveforge-power`
6. Select the folder and confirm

**Expected result**: Power appears in Installed Powers list as "HiveForge Steering Assistant"

**Activation Keywords:**

The Power activates automatically when you mention these keywords in KIRO chat:
- "steering"
- "steering files"
- "documentation"
- "onboarding"
- "project setup"
- "project documentation"

✅ **Power Registration Complete!**

---

## Verification Steps

### Verify CLI Installation

```bash
# Activate virtual environment if not already active
cd ~/projects/HiveForge
source venv/bin/activate  # Windows: venv\Scripts\activate.bat

# Test CLI
hiveforge --help

# Create a test project
mkdir ~/test-hiveforge
cd ~/test-hiveforge
hiveforge -n my-test-project

# Verify structure was created
ls -la
# Should show: .kiro/, .swarm/, swarm_state.md
```

**Expected result**: Project structure created successfully.

---

### Verify MCP Server Installation

```bash
# Activate virtual environment if not already active
cd ~/projects/HiveForge
source venv/bin/activate

# Test MCP server command
hiveforge-steering-mcp --help
```

**Expected result**: Help message displays without errors.

---

### Verify KIRO Power Integration

**⚠️ IMPORTANT**: Before testing, make sure you have:
1. Opened your target project (not HiveForge) in KIRO IDE
2. Created `.kiro/settings/mcp.json` in that project folder
3. Restarted KIRO or reloaded MCP servers

**Then test:**

1. **Open KIRO IDE** with your target project folder open

2. **Check MCP Server Status**:
   - Look for MCP server indicator in KIRO UI
   - Should show "hiveforge-steering" as connected

3. **Test Power Activation**:
   - In KIRO chat, type: "Can you help me create steering files?"
   - The Power should activate automatically
   - You should see a response about steering file generation

4. **Test Power Tools**:
   - In KIRO chat, type: "Initialize steering files for my project"
   - The Power should use the `init_steering` tool
   - Files should be created in `.kiro/steering/` of your current project

**Expected result**: Power responds and creates steering files in your project folder (not in HiveForge folder).

---

### Verify Shared Backend

Both CLI and Power should produce identical outputs:

```bash
# Test with CLI
cd ~/test-project
hiveforge steering init

# Note the files created in .kiro/steering/

# Test with Power (in KIRO chat)
"Initialize steering files"

# Compare outputs - they should be identical
```

**Expected result**: Identical steering files from both methods.

---

## Troubleshooting

### CLI Issues

#### "hiveforge: command not found"

**Problem**: Command not in PATH or venv not activated.

**Solution**:
```bash
# Activate HiveForge venv
cd ~/projects/HiveForge
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate.bat  # Windows

# Verify hiveforge is available
which hiveforge  # macOS/Linux
where hiveforge  # Windows
```

#### "No module named 'hiveforge'"

**Problem**: HiveForge not installed or wrong venv activated.

**Solution**:
```bash
# Make sure you're in HiveForge's venv
cd ~/projects/HiveForge
source venv/bin/activate

# Verify installation
pip list | grep hiveforge

# If not installed, reinstall
pip install -e .
```

---

### MCP Server Issues

#### "hiveforge-steering-mcp: command not found"

**Problem**: MCP server package not installed.

**Solution**:
```bash
# Activate venv
cd ~/projects/HiveForge
source venv/bin/activate

# Install MCP server package
cd hiveforge-power
pip install -e .
cd ..

# Verify
hiveforge-steering-mcp --help
```

#### "Module 'mcp_server.server' not found"

**Problem**: Incorrect module path in KIRO config.

**Solution**:
1. Verify the module exists:
   ```bash
   cd ~/projects/HiveForge/hiveforge-power
   ls mcp_server/server.py
   # Should exist
   ```

2. Check your `~/.kiro/settings/mcp.json`:
   - `args` should be: `["-m", "mcp_server.server"]`
   - NOT: `["-m", "hiveforge_power.server"]`

3. Restart KIRO after fixing

---

### KIRO Power Issues

#### Power Not Appearing in KIRO

**Problem**: KIRO not detecting the MCP server.

**Solution**:

1. **Check config file exists**:
   ```bash
   cat ~/.kiro/settings/mcp.json
   # Should show your configuration
   ```

2. **Verify JSON syntax**:
   - Use a JSON validator: https://jsonlint.com/
   - Common errors: missing commas, trailing commas, wrong quotes

3. **Check Python path is correct**:
   ```bash
   # Test the exact command from your config
   /path/to/HiveForge/venv/bin/python -m mcp_server.server --help
   # Should work without errors
   ```

4. **Check file permissions**:
   ```bash
   ls -la ~/.kiro/settings/mcp.json
   # Should be readable
   ```

5. **Restart KIRO completely**:
   - Close all KIRO windows
   - Reopen KIRO
   - Wait 10-15 seconds for MCP servers to connect

#### Power Not Activating on Keywords

**Problem**: Power installed but doesn't respond to keywords.

**Solution**:

1. **Check MCP server is connected**:
   - Look for server status in KIRO UI
   - Should show "hiveforge-steering" as active

2. **Try explicit activation**:
   - Instead of: "help with documentation"
   - Try: "use the steering power to initialize files"

3. **Check KIRO logs**:
   - Look for MCP connection errors
   - Check for Power activation messages

#### Power Tools Fail

**Problem**: Power activates but tools return errors.

**Solution**:

1. **Check working directory**:
   - Power tools need to run in a project directory
   - Make sure you're in a directory with write permissions

2. **Check Python dependencies**:
   ```bash
   cd ~/projects/HiveForge
   source venv/bin/activate
   cd hiveforge-power
   pip install -e .
   ```

3. **Test tools directly**:
   ```bash
   cd ~/test-project
   python -m mcp_server.server
   # Should start without errors
   ```

4. **Check logs**:
   - Set `FASTMCP_LOG_LEVEL=DEBUG` in mcp.json
   - Restart KIRO
   - Check logs for detailed error messages

---

### Path Issues (Local Development)

#### "Cannot find Python interpreter"

**Problem**: Path in mcp.json is incorrect.

**Solution**:

1. **Find correct path**:
   ```bash
   cd ~/projects/HiveForge
   source venv/bin/activate
   which python  # macOS/Linux
   where python  # Windows
   ```

2. **Update mcp.json** with the exact path shown

3. **Restart KIRO**

#### "Working directory not found"

**Problem**: MCP server can't find project files.

**Solution**:

1. **Check current directory**:
   - Power tools use the current working directory
   - Make sure you're in a valid project directory

2. **Use absolute paths**:
   - When calling tools, provide full paths
   - Example: `project_root="/full/path/to/project"`

---

### Permission Issues

#### "Permission denied" when installing

**Problem**: Trying to install system-wide without permissions.

**Solution**: Always use a virtual environment:
```bash
# Don't use sudo!
# Instead, create venv
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

#### "Permission denied" when creating files

**Problem**: No write permissions in target directory.

**Solution**:
```bash
# Check permissions
ls -la .kiro/

# Fix permissions if needed
chmod -R u+w .kiro/
```

---

### Version Issues

#### "Python version too old"

**Problem**: Python 3.11+ required.

**Solution**:
```bash
# Check version
python --version

# If < 3.11, install newer Python from python.org
# Or use pyenv:
curl https://pyenv.run | bash
pyenv install 3.11.5
pyenv global 3.11.5
```

#### "Dependency conflict"

**Problem**: Conflicting package versions.

**Solution**:
```bash
# Create fresh virtual environment
cd ~/projects/HiveForge
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# Reinstall
pip install -e .
cd hiveforge-power
pip install -e .
```

---

## Using HiveForge with Your Existing Project

This section explains how to use HiveForge with a project you're already working on.

### Scenario 1: Using HiveForge with a New Local Project

```bash
# 1. Create your project directory
mkdir ~/my-new-project
cd ~/my-new-project

# 2. Initialize git (optional)
git init

# 3. Open the project in KIRO IDE
# File → Open Folder → Select ~/my-new-project

# 4. Create MCP config in your project
mkdir -p .kiro/settings
nano .kiro/settings/mcp.json
# Paste the HiveForge MCP configuration (see Step 5 above)

# 5. Restart KIRO or reload MCP servers

# 6. Use HiveForge in KIRO chat
# "Initialize steering files for my project"
```

### Scenario 2: Using HiveForge with an Existing GitHub Project

```bash
# 1. Clone your existing project
cd ~/projects
git clone https://github.com/yourusername/your-project.git
cd your-project

# 2. Open the project in KIRO IDE
# File → Open Folder → Select ~/projects/your-project

# 3. Create MCP config in your project
mkdir -p .kiro/settings
nano .kiro/settings/mcp.json
# Paste the HiveForge MCP configuration (see Step 5 above)

# 4. Restart KIRO or reload MCP servers

# 5. Use HiveForge in KIRO chat
# "Initialize steering files for my project"
# HiveForge will analyze your existing code and documentation
```

### Scenario 3: Using HiveForge CLI with Any Project

```bash
# 1. Activate HiveForge virtual environment
cd ~/projects/HiveForge
source venv/bin/activate  # Windows: venv\Scripts\activate.bat

# 2. Navigate to your project
cd ~/projects/your-project

# 3. Use HiveForge CLI commands
hiveforge steering init
hiveforge steering validate

# 4. Deactivate when done
deactivate
```

### Key Points

- **HiveForge installation location**: `~/projects/HiveForge` (or wherever you cloned it)
- **Your project location**: Can be anywhere (e.g., `~/projects/your-project`, `D:\Users\asosh\playground\_KIRO\VeriQ_MVP`)
- **MCP config location**: Always in your project's `.kiro/settings/mcp.json`, NOT in HiveForge folder
- **Virtual environment**: Only activate HiveForge's venv when using the CLI; KIRO Power doesn't require manual activation

### Workflow Summary

1. **Install HiveForge once** (Steps 1-4 above) → This creates the tool
2. **For each project you want to use HiveForge with**:
   - Open that project in KIRO IDE
   - Create `.kiro/settings/mcp.json` in that project
   - Point it to your HiveForge installation
   - Use HiveForge tools in KIRO chat or via CLI

---

## Using HiveForge

### CLI Usage

```bash
# Activate virtual environment
cd ~/projects/HiveForge
source venv/bin/activate

# Initialize a new project
cd ~/my-project
hiveforge -n my-project

# Generate steering files
hiveforge steering init --analyze-code

# Update steering files
hiveforge steering update

# Validate steering files
hiveforge steering validate
```

See [WORKFLOW.md](./WORKFLOW.md) for detailed workflows.

---

### Power Usage

In KIRO chat:

```
"Initialize steering files for my project"
→ Power uses init_steering tool

"Update my steering files"
→ Power uses update_steering tool

"Validate my steering files"
→ Power uses validate_steering tool

"Reset steering files to templates"
→ Power uses reset_steering tool

"Discover existing documentation"
→ Power uses discover_docs tool
```

The Power provides the same functionality as the CLI but integrated into KIRO's conversational interface.

---

## Updating HiveForge

### Update from Git

```bash
cd ~/projects/HiveForge

# Pull latest changes
git pull origin main

# Reinstall CLI
source venv/bin/activate
pip install -e .

# Reinstall MCP server
cd hiveforge-power
pip install -e .
cd ..

# Restart KIRO to reload Power
```

---

## Uninstalling HiveForge

### Remove CLI

```bash
# Deactivate venv if active
deactivate

# Remove HiveForge directory
rm -rf ~/projects/HiveForge
```

### Remove Power from KIRO

1. **Edit `~/.kiro/settings/mcp.json`**:
   - Remove the `"hiveforge-steering"` entry
   - Or set `"disabled": true`

2. **Restart KIRO**

---

## Next Steps

After successful installation:

1. **Read the Documentation**:
   - [WORKFLOW.md](./WORKFLOW.md) - End-to-end workflows
   - [QUICKSTART.md](./QUICKSTART.md) - 5-minute walkthrough
   - [POWER.md](./hiveforge-power/POWER.md) - Power documentation

2. **Try the Examples**:
   - Initialize a test project
   - Generate steering files
   - Experiment with both CLI and Power

3. **Join the Community**:
   - [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
   - [GitHub Discussions](https://github.com/asoshnin/HiveForge/discussions)

---

## Getting Help

- **Installation Issues**: [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
- **Documentation**: [README.md](./README.md), [WORKFLOW.md](./WORKFLOW.md)
- **Power Documentation**: [hiveforge-power/POWER.md](./hiveforge-power/POWER.md)
- **Email**: 89580632+asoshnin@users.noreply.github.com

---

## Summary

**For CLI Only**:
1. Clone repository
2. Create virtual environment
3. `pip install -e .`
4. Verify with `hiveforge --help`

**For KIRO Power**:
1. Clone repository
2. Create virtual environment
3. `pip install -e .` (CLI)
4. `cd hiveforge-power && pip install -e .` (MCP server)
5. Configure `~/.kiro/settings/mcp.json`
6. Restart KIRO
7. Test with "initialize steering files"

**Both CLI and Power use the same shared backend - identical outputs!**

---

**Last Updated**: February 18, 2026  
**HiveForge Version**: 1.0.0  
**Power Version**: 2.1.0
