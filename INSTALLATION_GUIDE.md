# Installation Guide for HiveForge

## Overview

HiveForge is a CLI tool for scaffolding KIRO Methodology v05 projects. This guide covers installation on a fresh computer where you don't have HiveForge installed yet.

## Current Status

HiveForge is **not yet published to PyPI**. This means you cannot install it with `pip install hiveforge` yet. You must install from source.

---

## Prerequisites

Before installing HiveForge, ensure you have:

- **Python 3.11 or higher** - [Download from python.org](https://www.python.org/downloads/)
- **Git** - [Download from git-scm.com](https://git-scm.com/downloads)
- **pip** - Usually comes with Python
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
Python 3.11.5 (or higher)
pip 23.x.x
git version 2.x.x
```

---

## Installation Methods

### Method 1: Editable Install (Recommended)

This is the best method for most users. Changes to HiveForge code are immediately reflected without reinstalling.

#### Step 1: Clone HiveForge Repository

```bash
# Navigate to where you want to store HiveForge
cd ~/projects  # or any directory you prefer

# Clone the repository
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge
```

#### Step 2: Create Virtual Environment

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

#### Step 3: Install HiveForge

```bash
# Install in editable mode
pip install -e .

# This installs HiveForge and all dependencies
```

#### Step 4: Verify Installation

```bash
# Check that hiveforge command is available
hiveforge --help

# Should show:
# Usage: hiveforge [OPTIONS]
# ...
```

#### Step 5: Test with Sample Project

```bash
# Create a test directory
mkdir ~/test-hiveforge
cd ~/test-hiveforge

# Initialize a project
hiveforge -n my-test-project

# Verify structure was created
ls -la
# Should show: .kiro/, .swarm/, swarm_state.md
```

**Success!** You can now use HiveForge.

---

### Method 2: Poetry Install (For Contributors)

If you plan to contribute to HiveForge development, use Poetry for dependency management.

#### Step 1: Install Poetry

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

**Verify Poetry installation:**
```bash
poetry --version
```

#### Step 2: Clone and Install

```bash
# Clone repository
cd ~/projects
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge

# Install dependencies (Poetry creates venv automatically)
poetry install

# Activate Poetry's virtual environment
poetry shell

# Your prompt should now show the venv name
```

#### Step 3: Verify Installation

```bash
hiveforge --help
```

#### Step 4: Run Tests (Optional)

```bash
# Run test suite
pytest tests/ -v

# Should show: 863 tests passing
```

---

### Method 3: Build and Install Wheel

This method creates a distributable package file.

#### Step 1: Clone and Build

```bash
cd ~/projects
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge

# Install Poetry if not already installed
pip install poetry

# Build the package
poetry build
```

**Output:**
```
Building hiveforge (1.0.0)
  - Building sdist
  - Built hiveforge-1.0.0.tar.gz
  - Building wheel
  - Built hiveforge-1.0.0-py3-none-any.whl
```

#### Step 2: Install the Wheel

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate.bat  # Windows

# Install the wheel
pip install dist/hiveforge-1.0.0-py3-none-any.whl
```

#### Step 3: Verify Installation

```bash
hiveforge --help
```

---

## Post-Installation Setup

### Configure for Your Workflow

#### Option A: Keep HiveForge Venv Separate

Activate HiveForge's venv whenever you need to use it:

```bash
# Activate HiveForge venv
cd ~/projects/HiveForge
source venv/bin/activate  # macOS/Linux

# Use hiveforge
hiveforge -n my-project

# Deactivate when done
deactivate
```

#### Option B: Install Globally (Not Recommended)

```bash
# Install without venv (not recommended)
cd ~/projects/HiveForge
pip install -e .

# Now hiveforge is available system-wide
```

**Warning:** This can cause dependency conflicts with other Python projects.

#### Option C: Create Alias (Recommended)

Add to your shell config (`~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`):

```bash
# Alias to activate HiveForge venv and run command
alias hiveforge='source ~/projects/HiveForge/venv/bin/activate && hiveforge'
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

Now you can run `hiveforge` from anywhere without manually activating the venv.

---

## Using HiveForge with Existing Projects

### Scenario: Clone Existing Project and Continue Work

You're on a new computer and want to continue working on an existing GitHub repository.

#### Step 1: Install HiveForge

Follow Method 1 above (Editable Install).

#### Step 2: Clone Your Project

```bash
cd ~/projects
git clone https://github.com/youruser/your-project.git
cd your-project
```

#### Step 3: Check for KIRO Structure

```bash
# Check if project has KIRO structure
ls -la .kiro/

# If .kiro/ exists, you're good to go
# If not, initialize KIRO (see next section)
```

#### Step 4: Set Up Project Environment

```bash
# Create project's virtual environment (separate from HiveForge)
python3 -m venv venv
source venv/bin/activate

# Install project dependencies
pip install -r requirements.txt  # or poetry install

# Run tests to verify setup
pytest tests/ -v
```

#### Step 5: Use HiveForge Commands

```bash
# If project doesn't have KIRO structure, initialize it
# (Make sure HiveForge venv is activated)
cd ~/projects/HiveForge
source venv/bin/activate
cd ~/projects/your-project

hiveforge -n your-project

# Generate steering files from existing code
hiveforge steering init --analyze-code
```

See [WORKFLOW.md](./WORKFLOW.md) for detailed workflows.

---

## Troubleshooting

### "No module named 'hiveforge'"

**Problem:** HiveForge not installed or wrong venv activated.

**Solution:**
```bash
# Make sure you're in HiveForge's venv
cd ~/projects/HiveForge
source venv/bin/activate

# Verify installation
pip list | grep hiveforge

# If not installed, reinstall
pip install -e .
```

### "hiveforge: command not found"

**Problem:** Command not in PATH or venv not activated.

**Solution:**
```bash
# Activate HiveForge venv
cd ~/projects/HiveForge
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate.bat  # Windows

# Verify hiveforge is available
which hiveforge  # macOS/Linux
where hiveforge  # Windows
```

### "Permission denied" when installing

**Problem:** Trying to install system-wide without permissions.

**Solution:** Always use a virtual environment:
```bash
# Don't use sudo!
# Instead, create venv
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### "Python version too old"

**Problem:** Python 3.11+ required.

**Solution:**
```bash
# Check version
python --version

# If < 3.11, install newer Python from python.org
# Or use pyenv:
curl https://pyenv.run | bash
pyenv install 3.11.5
pyenv global 3.11.5
```

### "git: command not found"

**Problem:** Git not installed.

**Solution:**
- **macOS:** Install Xcode Command Line Tools: `xcode-select --install`
- **Linux:** `sudo apt-get install git` (Ubuntu/Debian) or `sudo yum install git` (CentOS/RHEL)
- **Windows:** Download from [git-scm.com](https://git-scm.com/downloads)

### "poetry: command not found"

**Problem:** Poetry not installed (only needed for Method 2).

**Solution:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (follow instructions from installer)
```

### Tests fail after installation

**Problem:** Dependencies not installed correctly.

**Solution:**
```bash
# Reinstall dependencies
cd ~/projects/HiveForge
source venv/bin/activate
pip install -e .

# Or with Poetry
poetry install

# Run tests
pytest tests/ -v
```

---

## Updating HiveForge

### Update from Git

```bash
cd ~/projects/HiveForge

# Pull latest changes
git pull origin main

# Reinstall (if dependencies changed)
source venv/bin/activate
pip install -e .

# Or with Poetry
poetry install
```

### Check Version

```bash
# Check installed version
pip show hiveforge

# Or
python -c "import hiveforge; print(hiveforge.__version__)"
```

---

## Uninstalling HiveForge

### Remove Installation

```bash
# Deactivate venv if active
deactivate

# Remove HiveForge directory
rm -rf ~/projects/HiveForge

# Remove any aliases from shell config
# Edit ~/.bashrc or ~/.zshrc and remove hiveforge alias
```

### Remove from Project

```bash
# If you want to remove KIRO structure from a project
cd your-project
rm -rf .kiro/ .swarm/ swarm_state.md
```

---

## Publishing to PyPI (Future)

When HiveForge is published to PyPI, installation will be simpler:

```bash
# Future installation (not available yet)
pip install hiveforge

# Verify
hiveforge --help
```

### For Maintainers: Publishing Steps

#### 1. Create PyPI Account
- Go to https://pypi.org and create an account
- Verify your email

#### 2. Create API Token
- Go to Account Settings → API tokens
- Create a new token with scope "Entire account"
- Save the token securely

#### 3. Configure Poetry

```bash
# Add PyPI token to Poetry
poetry config pypi-token.pypi pypi-YOUR_TOKEN_HERE
```

#### 4. Build and Publish

```bash
# Ensure version is correct in pyproject.toml
# Build and publish
poetry publish --build
```

#### 5. Verify Publication

```bash
# Wait a few minutes, then try:
pip install hiveforge

# Check on PyPI
# Visit: https://pypi.org/project/hiveforge/
```

#### 6. Update Documentation

Once published, update README.md, QUICKSTART.md, and this guide to reflect PyPI availability.

---

## Summary

**Current Installation (from source):**
1. Clone HiveForge repository
2. Create virtual environment
3. Install with `pip install -e .`
4. Verify with `hiveforge --help`

**Future Installation (after PyPI publish):**
1. `pip install hiveforge`
2. Verify with `hiveforge --help`

**For Development:**
1. Install Poetry
2. Clone repository
3. `poetry install`
4. `poetry shell`

---

## Getting Help

- **Installation Issues:** [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
- **Documentation:** [README.md](./README.md), [WORKFLOW.md](./WORKFLOW.md)
- **Troubleshooting:** [docs/troubleshooting.md](./docs/troubleshooting.md)

---

**Last Updated:** February 2026  
**HiveForge Version:** 1.0.0
