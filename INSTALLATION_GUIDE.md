# Installation Guide for HiveForge

## Current Status

HiveForge has been renamed from `kiro-init` but is **not yet published to PyPI**. This means you cannot install it with `pip install hiveforge` yet.

## How to Install Right Now

### Method 1: Editable Install (Recommended for Testing)

This is the best method if you want to test the package or make changes:

```bash
# Navigate to the HiveForge directory
cd /path/to/HiveForge

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate.bat  # Windows CMD
# OR
venv\Scripts\Activate.ps1  # Windows PowerShell

# Install in editable mode
pip install -e .

# Test it
hiveforge --help
```

**Benefits:**
- Changes to the code are immediately reflected
- No need to reinstall after modifications
- Perfect for development and testing

### Method 2: Poetry Install (For Contributors)

```bash
cd /path/to/HiveForge

# Install dependencies and create virtual environment
poetry install

# Activate Poetry's virtual environment
poetry shell

# Test it
hiveforge --help
```

### Method 3: Build and Install Wheel

```bash
cd /path/to/HiveForge

# Build the package
poetry build

# This creates: dist/hiveforge-1.0.0-py3-none-any.whl

# Install the wheel
pip install dist/hiveforge-1.0.0-py3-none-any.whl

# Test it
hiveforge --help
```

## Testing the Installation

Once installed, test it by creating a sample project:

```bash
# Create a test directory
mkdir ~/test-hiveforge
cd ~/test-hiveforge

# Initialize a project
hiveforge -n my-test-project

# Check what was created
ls -la
tree .kiro/  # if you have tree installed
```

You should see:
```
✅ KIRO v05 'my-test-project' initialized!
📁 .kiro/agents/ (7), .kiro/steering/ (8), swarm_state.md
```

## Publishing to PyPI (Future Steps)

When you're ready to publish HiveForge to PyPI:

### 1. Create PyPI Account
- Go to https://pypi.org and create an account
- Verify your email

### 2. Create API Token
- Go to Account Settings → API tokens
- Create a new token with scope "Entire account"
- Save the token securely (you'll only see it once)

### 3. Configure Poetry

```bash
# Add PyPI token to Poetry
poetry config pypi-token.pypi pypi-YOUR_TOKEN_HERE
```

### 4. Build and Publish

```bash
# Make sure version is correct in pyproject.toml
# Build the package
poetry build

# Publish to PyPI
poetry publish

# Or combine both steps
poetry publish --build
```

### 5. Verify Publication

```bash
# Wait a few minutes, then try:
pip install hiveforge

# Check on PyPI
# Visit: https://pypi.org/project/hiveforge/
```

### 6. Update Documentation

Once published, update README.md and QUICKSTART.md to change:
- "From Source (Current Method)" → "From PyPI (Recommended)"
- Remove the "Coming Soon" notes

## Troubleshooting

### "No module named 'hiveforge'"

Make sure you're in the virtual environment where you installed it:
```bash
source venv/bin/activate  # macOS/Linux
```

### "hiveforge: command not found"

The package isn't installed or the venv isn't activated:
```bash
# Check if installed
pip list | grep hiveforge

# If not, install it
pip install -e .
```

### "Permission denied" when installing

Don't use `sudo` with pip. Use a virtual environment instead:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Summary

**Right now:** Install from source using `pip install -e .`

**After publishing to PyPI:** Users can install with `pip install hiveforge`

**For development:** Use `poetry install` and `poetry shell`
