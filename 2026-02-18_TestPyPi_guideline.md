# TestPyPI Testing Guide for HiveForge Steering MCP v2.1.0

**Date**: February 18, 2026  
**Purpose**: Novice-level instructions for testing the HiveForge Steering MCP package on TestPyPI before production release  
**Test Data**: HiveForge codebase and Original Documents from `__DEVELOPMENT/KIRO_HiveForge_OriginalDocs`

---

## Table of Contents

1. [What is TestPyPI?](#what-is-testpypi)
2. [Why Test on TestPyPI First?](#why-test-on-testpypi-first)
3. [Prerequisites](#prerequisites)
4. [Step 1: Upload to TestPyPI](#step-1-upload-to-testpypi)
5. [Step 2: Install from TestPyPI](#step-2-install-from-testpypi)
6. [Step 3: Test the Package](#step-3-test-the-package)
7. [Step 4: Verify Test Results](#step-4-verify-test-results)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

---

## What is TestPyPI?

TestPyPI is a separate instance of the Python Package Index (PyPI) designed for testing and experimentation. It's a staging environment where you can upload and install packages without affecting the real PyPI ecosystem.

**Key Points**:
- **Separate from production PyPI**: Packages uploaded here don't appear on the real PyPI
- **Safe for testing**: You can experiment without risking production issues
- **Temporary**: TestPyPI may periodically delete old packages
- **Same interface**: Uses the same tools (twine, pip) as production PyPI

---

## Why Test on TestPyPI First?

Testing on TestPyPI catches issues before they affect real users:

| Benefit | Description |
|---------|-------------|
| **Catch packaging errors** | Verify the package builds and installs correctly |
| **Test installation** | Confirm pip can download and install the package |
| **Validate dependencies** | Ensure all dependencies resolve correctly |
| **No production impact** | Mistakes don't affect real users |
| **Quick rollback** | Easy to delete and re-upload if issues found |

---

## Prerequisites

Before starting, ensure you have:

### 1. Twine Installed

```bash
# Verify twine is installed
which twine

# If not installed, install it
pip install twine
```

### 2. TestPyPI Account and API Token

**Important**: You need TestPyPI credentials to upload packages. Follow these steps:

#### Step 2.1: Create a TestPyPI Account

1. Go to [https://test.pypi.org](https://test.pypi.org)
2. Click **"Register"** in the top right corner
3. Fill in your details:
   - **Username**: Choose a unique username (note it down!)
   - **Email**: Required for verification (use a real email)
   - **Password**: Create a strong password
4. Click **"Create Account"**
5. **Verify your email**: Check your email and click the verification link
6. Log in to your TestPyPI account

#### Step 2.2: Create an API Token

API tokens are more secure than using your password directly.

1. Go to [https://test.pypi.org/manage/account/](https://test.pypi.org/manage/account/)
2. Scroll down to the **"API tokens"** section
3. Click **"Add API token"**
4. Fill in the details:
   - **Token name**: `TestPyPI upload token` (or any descriptive name)
   - **Scope**: Select **"Entire account"** (for full access)
   - **Expiration**: Optional - set if you want the token to expire
5. Click **"Add token"**
6. **IMPORTANT**: Copy the token immediately!
   - The token will look like: `pypi-test-ABC123xyz...`
   - You won't be able to see it again after leaving this page!
   - Store it securely (see next step)

#### Step 2.3: Configure Your Credentials

Create or edit the `~/.pypirc` file in your home directory:

```bash
# Create or edit ~/.pypirc
nano ~/.pypirc
```

Add the following content:

```ini
[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-test-YOUR-ACTUAL-TOKEN-HERE
```

**Example** (with a fake token):

```ini
[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-test-ABC123def456ghi789jkl012mno345pqr
```

#### Step 2.4: Secure Your Credentials

```bash
# Set restrictive permissions (important!)
chmod 600 ~/.pypirc

# Verify the file is secure
ls -la ~/.pypirc
# Should show: -rw-------
```

**Security Notes**:
- Never commit `.pypirc` to version control!
- Add it to your `.gitignore` if needed
- The token has the same access as your account - keep it secret!

#### Step 2.5: Verify Your Configuration

```bash
# Test that twine can authenticate
cd hiveforge-power
twine upload --repository testpypi --check dist/*

# If configured correctly, it will check the package without prompting for password
```

**Troubleshooting**:
- If you get authentication errors, verify your `.pypirc` file is correct
- Make sure the token hasn't expired
- Check that the token has the correct scope (entire account)

---

### 3. Automated Testing Script (Recommended)

We've created an automation script that handles the entire testing process for you!

#### What the Script Does

1. **Pre-flight checks** - Verifies Python, pip, twine, and required files
2. **Builds the package** - Creates distribution files if needed
3. **Uploads to TestPyPI** - Publishes the package
4. **Creates test environment** - Sets up an isolated virtual environment
5. **Installs from TestPyPI** - Installs the published package
6. **Runs all tests** - Executes 7 comprehensive automated tests
7. **Generates report** - Creates a detailed test report
8. **Auto-cleanup** - Removes test artifacts when done

#### Running the Automated Tests

```bash
# Make the script executable
chmod +x testpypi_automation.sh

# Run the script
./testpypi_automation.sh
```

#### Expected Output

The script will show progress for each step:

```
========================================================================
[INFO] Pre-flight Checks
========================================================================
[SUCCESS] Python found: Python 3.11.x
[SUCCESS] pip found
[SUCCESS] twine found
[SUCCESS] Power directory found: hiveforge-power
[SUCCESS] Distribution files found
[SUCCESS] Original Documents found: __DEVELOPMENT/KIRO_HiveForge_OriginalDocs

========================================================================
[INFO] Building Package
========================================================================
[INFO] Cleaning old dist...
[INFO] Building package...
[SUCCESS] Package built successfully

========================================================================
[INFO] Uploading to TestPyPI
========================================================================
[INFO] Uploading package to TestPyPI...
[SUCCESS] Package uploaded to TestPyPI
[INFO] Package URL: https://test.pypi.org/project/hiveforge-steering-mcp/2.1.0/

... (more steps)

========================================================================
[INFO] Running Automated Tests
========================================================================
[INFO] Running comprehensive automated tests...

  ✓ Import Validation
  ✓ Error Handling with Rollback
  ✓ Security Validation
  ✓ Telemetry Collection
  ✓ Workflow Adapters
  ✓ MCP Tools Available
  ✓ Original Documents Processing

[SUCCESS] All tests passed!

========================================================================
[INFO] Generating Test Report
========================================================================
[SUCCESS] Report generated: testpypi_test_report.md
```

#### Test Results

After running, you'll have:

- **`testpypi_test_report.md`** - Comprehensive test report
- **`test_output_2.1.0/test_results.json`** - Detailed test results in JSON format

#### If Tests Pass

```
========================================================================
[INFO] All Tests Passed! 🎉
========================================================================
[INFO] Package is ready for production PyPI upload
[INFO] Run: twine upload dist/*
```

#### If Tests Fail

```
========================================================================
[INFO] Tests Failed
========================================================================
[ERROR] Check testpypi_test_report.md for details
[ERROR] Fix issues and re-run this script
```

#### Re-running Tests

To fix issues and re-run:

```bash
# Fix the issues in the codebase
# Then re-run the script
./testpypi_automation.sh
```

The script will rebuild and re-upload automatically.

---

### 4. Test Data Ready

We have two sources of test data:

#### A. Original Documents
Location: `__DEVELOPMENT/KIRO_HiveForge_OriginalDocs/`

Files available:
- `Kiro_AgentFactory.md` - Agent factory documentation
- `KIRO_POWERS_2ND_OPINION_REPORT.md` - Powers research second opinion
- `KIRO_POWERS_research_report.md` - Powers research report
- `SteeringAssistantPowerConversionReqs.md` - Conversion requirements

#### B. HiveForge Codebase
Location: Root project directory

We'll use the codebase structure and files for testing.

---

## Step 1: Upload to TestPyPI

### 1.1 Navigate to the Power Package Directory

```bash
cd hiveforge-power
```

### 1.2 Verify the Package Files Exist

```bash
ls -la dist/
```

You should see:
- `hiveforge_steering_mcp-2.1.0-py3-none-any.whl`
- `hiveforge_steering_mcp-2.1.0.tar.gz`

### 1.3 Upload to TestPyPI

```bash
# Option A: Using API token (recommended)
twine upload --repository testpypi dist/*

# Option B: Using username/password (you'll be prompted)
twine upload --repository testpypi dist/*
```

### 1.4 Expected Output

```
Uploading distributions to https://test.pypi.org/legacy/
Enter your username: __token__
Enter your password: 
Uploading hiveforge_steering_mcp-2.1.0-py3-none-any.whl
100%|██████████████████████████████████████| 53.2k/53.2k
Uploading hiveforge_steering_mcp-2.1.0.tar.gz
100%|██████████████████████████████████████| 45.1k/45.1k
View at https://test.pypi.org/project/hiveforge-steering-mcp/2.1.0/
```

### 1.5 Verify Upload Success

1. Open browser to: [https://test.pypi.org/project/hiveforge-steering-mcp/](https://test.pypi.org/project/hiveforge-steering-mcp/)
2. You should see version 2.1.0 listed
3. Click on the version to see package details
4. Verify the description, dependencies, and files are correct

---

## Step 2: Install from TestPyPI

### 2.1 Create a Clean Virtual Environment (Recommended)

```bash
# Create a new virtual environment for testing
python -m venv test-hiveforge-env

# Activate it
source test-hiveforge-env/bin/activate  # On macOS/Linux
# OR
test-hiveforge-env\Scripts\activate     # On Windows

# Verify activation
which python  # Should show path to test environment
```

### 2.2 Install from TestPyPI

```bash
# Install the package from TestPyPI
pip install --index-url https://test.pypi.org/simple/ hiveforge-steering-mcp==2.1.0
```

### 2.3 Expected Output

```
Looking in indexes: https://test.pypi.org/simple/
Collecting hiveforge-steering-mcp==2.1.0
  Downloading https://test.pypi.org/packages/.../hiveforge_steering_mcp-2.1.0-py3-none-any.whl (124 kB)
     |████████████████████████████████| 124 kB 2.1 MB/s
Installing collected packages: hiveforge-steering-mcp
Successfully installed hiveforge-steering-mcp-2.1.0
```

### 2.4 Verify Installation

```bash
# Check the package is installed
pip list | grep hiveforge

# Should show:
# hiveforge-steering-mcp    2.1.0

# Test imports
python -c "from hiveforge.steering.shared import adapters, security, telemetry; print('All imports successful!')"
```

---

## Step 3: Test the Package

Now we'll test the package using the HiveForge codebase and Original Documents.

### 3.1 Create a Test Directory

```bash
# Go to your project root
cd /path/to/HiveForge

# Create a test directory
mkdir -p test_output
cd test_output
```

### 3.2 Test 1: Import Validation

```bash
python << 'EOF'
# Test that all modules can be imported
try:
    from hiveforge.steering.shared import adapters
    from hiveforge.steering.shared import base
    from hiveforge.steering.shared import error_handling
    from hiveforge.steering.shared import security
    from hiveforge.steering.shared import telemetry
    from hiveforge.steering.shared import __init__ as shared_init
    print("✓ All shared backend modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)

# Test workflow adapters
try:
    from hiveforge.steering.shared.adapters import (
        SharedInitWorkflow,
        SharedUpdateWorkflow,
        SharedValidateWorkflow,
        SharedResetWorkflow,
        SharedDiscoveryWorkflow
    )
    print("✓ All workflow adapters imported successfully")
except ImportError as e:
    print(f"✗ Adapter import error: {e}")
    exit(1)

print("\n✅ All imports successful!")
EOF
```

### 3.3 Test 2: Error Handling with Automatic Rollback

```bash
python << 'EOF'
import tempfile
import os
from pathlib import Path
from hiveforge.steering.shared.adapters import SharedInitWorkflow
from unittest.mock import Mock, patch

print("=" * 60)
print("Test 2: Error Handling with Automatic Rollback")
print("=" * 60)

with tempfile.TemporaryDirectory() as tmp_path:
    tmp_path = Path(tmp_path)
    
    # Create a steering directory with files
    steering_dir = tmp_path / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    (steering_dir / "test.md").write_text("# Test content")
    
    # Mock the InitWorkflow to simulate failure
    with patch('hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock_init:
        mock_workflow = Mock()
        mock_workflow.execute.return_value = False  # Simulate failure
        mock_workflow.state.validation_report = None
        mock_init.return_value = mock_workflow
        
        # Execute workflow
        workflow = SharedInitWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify error handling
        if not result.success:
            print("✓ Workflow correctly reported failure")
        else:
            print("✗ Workflow should have failed")
            exit(1)
        
        if len(result.errors) > 0:
            print(f"✓ Error collected: {result.errors[0]}")
        else:
            print("✗ No errors collected")
            exit(1)
        
        if "backup_location" in result.metadata:
            print(f"✓ Backup created at: {result.metadata['backup_location']}")
        else:
            print("✗ No backup location in metadata")
            exit(1)

print("\n✅ Error handling test passed!")
EOF
```

### 3.4 Test 3: Security Validation

```bash
python << 'EOF'
from hiveforge.steering.shared.security import (
    validate_parameters,
    sanitize_path,
    ResourceLimiter,
    SecurityContext
)
import tempfile
from pathlib import Path

print("=" * 60)
print("Test 3: Security Validation")
print("=" * 60)

# Test 3a: Parameter Validation
print("\n3a. Testing parameter validation...")
try:
    # Valid parameters
    result = validate_parameters(
        project_root="/valid/path",
        files_to_update=["file1.md"],
        confidence_threshold=0.7
    )
    print("✓ Valid parameters accepted")
    
    # Invalid parameters
    try:
        validate_parameters(
            project_root=None,  # Invalid
            files_to_update=[]
        )
        print("✗ Should have rejected None project_root")
    except ValueError:
        print("✓ None project_root correctly rejected")
        
except Exception as e:
    print(f"✗ Parameter validation error: {e}")
    exit(1)

# Test 3b: Path Sanitization
print("\n3b. Testing path sanitization...")
try:
    # Valid path
    safe_path = sanitize_path("/valid/project/path", "/valid")
    print(f"✓ Valid path sanitized: {safe_path}")
    
    # Path traversal attempt
    try:
        sanitize_path("/valid/../../../etc/passwd", "/valid")
        print("✗ Should have rejected path traversal")
    except ValueError:
        print("✓ Path traversal attempt correctly rejected")
        
except Exception as e:
    print(f"✗ Path sanitization error: {e}")
    exit(1)

# Test 3c: Resource Limiter
print("\n3c. Testing resource limiter...")
try:
    with ResourceLimiter(max_memory_mb=100, max_cpu_time_sec=60) as limiter:
        print("✓ Resource limiter context created successfully")
except Exception as e:
    print(f"✗ Resource limiter error: {e}")
    exit(1)

print("\n✅ Security validation test passed!")
EOF
```

### 3.5 Test 4: Telemetry Collection

```bash
python << 'EOF'
import tempfile
from pathlib import Path
from hiveforge.steering.shared.telemetry import TelemetryCollector, InterfaceType
from hiveforge.steering.shared.adapters import SharedInitWorkflow
from unittest.mock import Mock, patch

print("=" * 60)
print("Test 4: Telemetry Collection")
print("=" * 60)

with tempfile.TemporaryDirectory() as tmp_path:
    tmp_path = Path(tmp_path)
    telemetry_dir = tmp_path / ".kiro" / ".telemetry"
    
    # Create telemetry collector
    telemetry = TelemetryCollector(telemetry_dir=telemetry_dir)
    print(f"✓ Telemetry collector created at: {telemetry_dir}")
    
    # Create steering directory
    steering_dir = tmp_path / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    (steering_dir / "test.md").write_text("# Test")
    
    # Mock and execute workflow with telemetry
    with patch('hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock_init:
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_init.return_value = mock_workflow
        
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            telemetry_collector=telemetry,
            interface_type=InterfaceType.CLI
        )
        result = workflow.execute()
        
        if result.success:
            print("✓ Workflow executed successfully with telemetry")
        else:
            print("✗ Workflow should have succeeded")
            exit(1)
    
    # Verify telemetry file was created
    if telemetry_dir.exists():
        print(f"✓ Telemetry directory created: {telemetry_dir}")
        telemetry_files = list(telemetry_dir.glob("*.json"))
        print(f"✓ Telemetry files created: {len(telemetry_files)}")
    else:
        print("✗ Telemetry directory not created")
        exit(1)

print("\n✅ Telemetry collection test passed!")
EOF
```

### 3.6 Test 5: Process Original Documents

Now let's test processing the actual Original Documents:

```bash
python << 'EOF'
import sys
from pathlib import Path
from hiveforge.steering.shared.adapters import SharedDiscoveryWorkflow
from hiveforge.steering.shared.telemetry import TelemetryCollector, InterfaceType
from unittest.mock import Mock, patch

print("=" * 60)
print("Test 5: Process Original Documents")
print("=" * 60)

# Path to Original Documents
original_docs_path = Path("/path/to/HiveForge/__DEVELOPMENT/KIRO_HiveForge_OriginalDocs")

if not original_docs_path.exists():
    print(f"✗ Original Documents path not found: {original_docs_path}")
    print("  Please update the path in this script")
    sys.exit(1)

print(f"✓ Original Documents path: {original_docs_path}")

# List available documents
docs = list(original_docs_path.glob("*.md"))
print(f"✓ Found {len(docs)} markdown documents:")
for doc in docs:
    print(f"  - {doc.name}")

# Test discovery workflow on Original Documents
print("\nTesting discovery workflow on Original Documents...")

# Mock the DiscoveryOrchestrator
with patch('hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator') as mock_orch:
    mock_orchestrator = Mock()
    mock_orchestrator.discover_all.return_value = (
        [str(d) for d in docs],  # Return all docs as discovered
        {
            "file_count": len(docs),
            "method": "full_scan",
            "ranking_metadata": {
                "total_skipped": 0,
                "skip_reasons": {}
            }
        }
    )
    mock_orch.return_value = mock_orchestrator
    
    workflow = SharedDiscoveryWorkflow(
        project_root=original_docs_path,
        include_git_history=False,
        max_discovery_files=100,
        max_file_size_mb=10
    )
    result = workflow.execute()
    
    if result.success:
        print(f"✓ Discovery workflow succeeded")
        print(f"  Files discovered: {len(result.files_discovered)}")
        print(f"  Message: {result.message}")
    else:
        print(f"✗ Discovery workflow failed: {result.message}")
        exit(1)

print("\n✅ Original Documents processing test passed!")
EOF
```

**Important**: Replace `/path/to/HiveForge` with your actual project path.

### 3.7 Test 6: CLI Commands

```bash
# Test CLI help
hiveforge --help

# Test steering help
hiveforge steering --help

# Test init help
hiveforge steering init --help

# Test update help
hiveforge steering update --help

# Test validate help
hiveforge steering validate --help

# Test reset help
hiveforge steering reset --help

# Test discover help
hiveforge steering discover --help
```

### 3.8 Test 7: MCP Tools (If Available)

If you have an MCP client available:

```bash
# Test that MCP server can be imported
python << 'EOF'
try:
    from mcp_server.server import mcp
    print("✓ MCP server imported successfully")
    print(f"  Server name: {mcp.name}")
    print(f"  Tools registered: {len(mcp._tools)}")
except ImportError as e:
    print(f"✗ MCP server import error: {e}")
    exit(1)

# List available tools
print("\nAvailable MCP tools:")
for tool in mcp._tools:
    print(f"  - {tool.name}")
EOF
```

---

## Step 4: KIRO IDE Integration Testing

Now let's test the full workflow using KIRO IDE with HiveForge's own codebase and Original Documents.

### 4.1 Prerequisites

- KIRO IDE installed and running
- HiveForge package installed from TestPyPI (from Step 2)
- HiveForge project open in KIRO IDE

### 4.2 Test Scenario: Transform HiveForge's Original Documents

We'll use HiveForge's own documentation to test the Steering Assistant workflow.

#### Step 4.2.1: Prepare Test Environment

```bash
# In your HiveForge project root
# Copy Original Documents to onboarding folder
mkdir -p .kiro/onboarding
cp __DEVELOPMENT/KIRO_HiveForge_OriginalDocs/*.md .kiro/onboarding/

# Verify files copied
ls -la .kiro/onboarding/
# Should show:
# - Kiro_AgentFactory.md
# - KIRO_POWERS_2ND_OPINION_REPORT.md
# - KIRO_POWERS_research_report.md
# - SteeringAssistantPowerConversionReqs.md
```

#### Step 4.2.2: Use Steering Assistant in KIRO IDE

1. **Open KIRO IDE** with HiveForge project loaded
2. **Select Steering Assistant agent** from the agent dropdown
3. **Paste this prompt**:

```
I have original project documents in .kiro/onboarding/ that describe the HiveForge system design.

Please:
1. Read all documents in .kiro/onboarding/
2. Transform them into HiveForge steering documents
3. Create all 8 steering files in .kiro/steering/:
   - project-vision.md - Problem, solution, users, value proposition
   - tech-stack.md - Technologies, frameworks, libraries
   - conventions.md - Naming, formatting, commit messages
   - architecture.md - System design, components, data flow
   - db-standards.md - Schema design, migrations, queries
   - api-standards.md - Endpoint design, error handling, auth
   - ui-standards.md - Component structure, styling, accessibility
   - qa-standards.md - Testing strategy, coverage requirements

Extract all relevant information from the documents and format according to steering file templates.
```

4. **Wait for completion** (may take 2-5 minutes)

#### Step 4.2.3: Verify Generated Steering Files

```bash
# Check that steering files were created
ls -la .kiro/steering/

# Should show 8 files:
# - project-vision.md
# - tech-stack.md
# - conventions.md
# - architecture.md
# - db-standards.md
# - api-standards.md
# - ui-standards.md
# - qa-standards.md

# Spot-check content
cat .kiro/steering/project-vision.md
cat .kiro/steering/tech-stack.md
```

**Expected Results:**
- All 8 steering files created
- Files contain actual content (not just placeholders)
- Content extracted from Original Documents
- Proper markdown formatting

### 4.3 Test Scenario: Discrepancy Analysis with Orchestrator

Now test the full refactoring workflow using the Orchestrator.

#### Step 4.3.1: Use Orchestrator in KIRO IDE

1. **Select Orchestrator agent** from the agent dropdown
2. **Paste this prompt**:

```
I have steering documents in .kiro/steering/ that describe the intended HiveForge system design.
I need you to analyze the actual codebase and compare it against these steering documents.

Please:
1. Read all steering files in .kiro/steering/
2. Analyze the actual code implementation in src/
3. Create a comprehensive discrepancy report that identifies:
   - Features described in steering docs but not implemented in code
   - Code that doesn't match the documented design
   - Architectural differences between docs and implementation
   - Convention violations
   - Missing components
   - Technical debt items

Save the report to: DISCREPANCY_REPORT.md in the project root directory

Delegate this analysis to appropriate specialized agents (Backend Engineer, Frontend Engineer, Data Architect, QA Engineer, Red Team).
```

3. **Monitor progress** in KIRO chat
4. **Wait for completion** (may take 5-15 minutes)

#### Step 4.3.2: Verify Discrepancy Report

```bash
# Check that report was created
ls -la DISCREPANCY_REPORT.md

# Review the report
cat DISCREPANCY_REPORT.md
```

**Expected Results:**
- `DISCREPANCY_REPORT.md` created in project root
- Report contains Executive Summary with issue counts
- Report lists Critical Issues, Warnings, and Info items
- Each issue includes:
  - Steering Doc reference
  - Actual Code status
  - Impact assessment
  - Recommendation

### 4.4 Test Scenario: CLI Validation

Test that CLI commands work with the generated steering files.

```bash
# Validate the generated steering files
hiveforge steering validate --strict

# Expected output:
# Validation Report
# ================
# ✓ project-vision.md: PASS
# ✓ tech-stack.md: PASS
# ✓ conventions.md: PASS
# ✓ architecture.md: PASS
# ✓ db-standards.md: PASS
# ✓ api-standards.md: PASS
# ✓ ui-standards.md: PASS
# ✓ qa-standards.md: PASS
#
# Summary: All files passed validation
```

### 4.5 KIRO IDE Test Checklist

Mark each test as PASS/FAIL:

- [ ] **Steering Assistant Test**
  - [ ] Agent loaded successfully
  - [ ] Read Original Documents from `.kiro/onboarding/`
  - [ ] Generated all 8 steering files
  - [ ] Files contain actual content (not placeholders)
  - [ ] Content matches Original Documents

- [ ] **Orchestrator Test**
  - [ ] Agent loaded successfully
  - [ ] Read steering files from `.kiro/steering/`
  - [ ] Delegated to specialized agents
  - [ ] Generated `DISCREPANCY_REPORT.md`
  - [ ] Report contains meaningful analysis

- [ ] **CLI Validation Test**
  - [ ] `hiveforge steering validate --strict` runs
  - [ ] All steering files pass validation
  - [ ] No critical errors reported

- [ ] **Integration Test**
  - [ ] Full workflow (docs → steering → analysis) completed
  - [ ] No errors or crashes
  - [ ] Output files are well-formed

### 4.6 Document Test Results

Create a KIRO IDE test report:

```bash
cat > kiro_ide_test_report.md << 'EOF'
# KIRO IDE Integration Test Report

**Date**: [FILL IN]
**Version**: 2.1.0
**Source**: TestPyPI

## Test Environment
- KIRO IDE Version: [FILL IN]
- Python Version: [FILL IN]
- OS: [FILL IN]

## Test Results

### Steering Assistant Test
- Status: PASS/FAIL
- Files Generated: [COUNT]
- Notes: [OBSERVATIONS]

### Orchestrator Test
- Status: PASS/FAIL
- Report Generated: YES/NO
- Issues Found: [COUNT]
- Notes: [OBSERVATIONS]

### CLI Validation Test
- Status: PASS/FAIL
- Validation Errors: [COUNT]
- Notes: [OBSERVATIONS]

## Overall Result
**PASSED** / **FAILED**

## Issues Encountered
[LIST ANY ISSUES]

## Recommendations
[ANY SUGGESTIONS FOR IMPROVEMENT]
EOF

echo "KIRO IDE test report template created: kiro_ide_test_report.md"
```

---

## Step 5: Verify Test Results

### 5.1 Create a Comprehensive Test Report

```bash
python << 'EOF'
from datetime import datetime

report = f"""
# HiveForge Steering MCP v2.1.0 - TestPyPI Test Report

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version**: 2.1.0
**Source**: TestPyPI

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Import Validation | PASS/FAIL | |
| Error Handling | PASS/FAIL | |
| Security Validation | PASS/FAIL | |
| Telemetry Collection | PASS/FAIL | |
| Original Documents | PASS/FAIL | |
| CLI Commands | PASS/FAIL | |
| MCP Tools | PASS/FAIL | |

## Overall Result

**PASSED** / **FAILED**

## Notes

[Add any observations or issues here]

"""

print(report)

# Save to file
with open("test_report.md", "w") as f:
    f.write(report)

print("\nReport saved to: test_report.md")
EOF
```

### 5.2 Check for Issues

Review the test output and check for:

- [ ] All imports successful
- [ ] Error handling works correctly
- [ ] Security validation catches invalid inputs
- [ ] Telemetry is collected
- [ ] Original Documents can be processed
- [ ] CLI commands work
- [ ] MCP tools are available
- [ ] **KIRO IDE Steering Assistant works**
- [ ] **KIRO IDE Orchestrator generates discrepancy report**
- [ ] **Full refactoring workflow completes successfully**

---

## Troubleshooting

### Issue: "Could not find a version that satisfies the requirement"

**Cause**: Package not found on TestPyPI

**Solution**:
1. Verify the package was uploaded successfully
2. Check the package name is correct: `hiveforge-steering-mcp`
3. Verify the version is correct: `2.1.0`
4. Check TestPyPI website to confirm package exists

### Issue: "Permission denied" during upload

**Cause**: Authentication issue

**Solution**:
1. Verify your `.pypirc` file is correct
2. Check API token is valid
3. Ensure token has correct scope

### Issue: ImportError after installation

**Cause**: Package not installed correctly

**Solution**:
1. Verify installation: `pip list | grep hiveforge`
2. Try reinstalling: `pip install --force-reinstall hiveforge-steering-mcp`
3. Check Python version compatibility

### Issue: Tests failing

**Cause**: Various

**Solution**:
1. Check test output for specific error messages
2. Verify all dependencies are installed
3. Check Python version (requires 3.11+)
4. Review troubleshooting section in documentation

### Issue: MCP tools not available

**Cause**: MCP server not properly installed

**Solution**:
1. Verify MCP server package is installed
2. Check entry points are registered
3. Try reinstalling the package

---

## Next Steps

### If All Tests Pass

1. **Proceed to production PyPI upload**:
   ```bash
   twine upload dist/*
   ```

2. **Create GitHub release**:
   - Tag: `v2.1.0`
   - Title: "HiveForge Steering MCP v2.1.0"
   - Use `RELEASE_NOTES_v2.1.0.md` as body

3. **Update marketplace submission**:
   - Submit updated Power package
   - Include test results
   - Include release notes

### If Tests Fail

1. **Fix the issues** in the codebase
2. **Rebuild the package**:
   ```bash
   cd hiveforge-power
   rm -rf dist/*
   python -m build
   ```
3. **Upload new version** (e.g., `2.1.1`)
4. **Retest on TestPyPI**

---

## Quick Reference

### Upload to TestPyPI
```bash
cd hiveforge-power
twine upload --repository testpypi dist/*
```

### Install from TestPyPI
```bash
pip install --index-url https://test.pypi.org/simple/ hiveforge-steering-mcp==2.1.0
```

### Upload to Production PyPI
```bash
twine upload dist/*
```

### Install from Production PyPI
```bash
pip install hiveforge-steering-mcp==2.1.0
```

---

## Support

If you encounter issues:

1. **Check the documentation**: See `hiveforge-power/POWER.md`
2. **Review error messages**: They often contain specific guidance
3. **Check troubleshooting**: This guide's troubleshooting section
4. **Report issues**: Create a GitHub issue with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version)

---

**Happy Testing! 🚀**