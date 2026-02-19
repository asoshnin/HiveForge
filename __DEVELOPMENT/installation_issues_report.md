# Installation Issues Report

**Date**: February 18, 2026  
**Auditor**: Installation Documentation Auditor Agent  
**Document**: INSTALLATION_GUIDE.md

---

## Executive Summary

The current INSTALLATION_GUIDE.md is **incomplete** for users who want to use HiveForge as a KIRO Power. It only covers CLI installation but omits critical information about:

1. MCP server installation and configuration
2. KIRO Power registration process
3. Relationship between CLI and Power
4. Local development installation from source (not PyPI)

**Severity**: **HIGH** - Users cannot successfully install and use the Power without this information.

---

## Critical Gaps Identified

### 1. Missing MCP Server Installation (CRITICAL)

**Issue**: No instructions for installing the MCP server package.

**Impact**: Users cannot use HiveForge as a KIRO Power.

**Current State**: Guide only covers CLI installation (`pip install -e .` in main directory).

**Required State**: Must include:
- Installation of `hiveforge-power/` package
- Correct package name: `hiveforge-steering-mcp`
- Entry point: `hiveforge-steering-mcp` (from pyproject.toml)

**Fix Needed**:
```bash
# Install MCP server package
cd hiveforge-power
pip install -e .
```

---

### 2. Missing KIRO MCP Configuration (CRITICAL)

**Issue**: No instructions for configuring KIRO to recognize the MCP server.

**Impact**: Even if MCP server is installed, KIRO won't detect it.

**Current State**: Not mentioned at all.

**Required State**: Must include:
- Location of config file: `~/.kiro/settings/mcp.json`
- Configuration format and structure
- Both uvx and local development configurations
- How to verify configuration is correct

**Fix Needed**: Add section showing:
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

---

### 3. Missing Power Registration (CRITICAL)

**Issue**: No instructions for registering the Power in KIRO.

**Impact**: Users don't know how to make the Power appear in KIRO.

**Current State**: Not mentioned.

**Required State**: Must explain:
- Power metadata in `package.json`
- How KIRO discovers Powers
- How to verify Power is registered
- Activation keywords

**Fix Needed**: Add section explaining Power registration and verification.

---

### 4. Confusing Package Names (HIGH)

**Issue**: Multiple package names used inconsistently.

**Impact**: Users get confused about what to install.

**Current State**:
- Main package: `hiveforge` (CLI)
- Power package: `hiveforge-steering-mcp` (MCP server)
- Directory: `hiveforge-power/`

**Required State**: Clear explanation of:
- Two separate packages
- Different purposes (CLI vs Power)
- When to install each

**Fix Needed**: Add "Understanding the Packages" section.

---

### 5. Missing Local Development Setup (HIGH)

**Issue**: Guide assumes PyPI installation, but package isn't published yet.

**Impact**: Users can't install from source correctly.

**Current State**: Mentions "not yet published" but doesn't provide complete local setup.

**Required State**: Must include:
- Installing both packages from source
- Virtual environment considerations
- Path configuration for local development
- How to test local installation

**Fix Needed**: Add "Local Development Installation" section with complete steps.

---

### 6. Missing Verification Steps (MEDIUM)

**Issue**: No way to verify MCP server and Power are working.

**Impact**: Users don't know if installation succeeded.

**Current State**: Only CLI verification (`hiveforge --help`).

**Required State**: Must include:
- How to check MCP server is running
- How to verify Power appears in KIRO
- How to test Power activation
- Expected outputs at each step

**Fix Needed**: Add comprehensive verification section.

---

### 7. Missing Troubleshooting for MCP (MEDIUM)

**Issue**: No troubleshooting for MCP-specific issues.

**Impact**: Users get stuck on common MCP problems.

**Current State**: Only CLI troubleshooting.

**Required State**: Must include:
- MCP server not starting
- Power not appearing in KIRO
- Connection errors
- Permission issues
- Path problems in local development

**Fix Needed**: Expand troubleshooting section.

---

### 8. Unclear Relationship Between CLI and Power (MEDIUM)

**Issue**: Users don't understand they're two different interfaces to the same backend.

**Impact**: Confusion about when to use CLI vs Power.

**Current State**: Not explained.

**Required State**: Must explain:
- CLI is standalone tool
- Power is KIRO integration
- Both use same shared backend
- Identical outputs
- When to use each

**Fix Needed**: Add "CLI vs Power" section.

---

## Technical Accuracy Issues

### Issue 1: Entry Point Name

**File**: `hiveforge-power/pyproject.toml`  
**Line**: 52

**Current**:
```toml
[project.scripts]
hiveforge-steering-mcp = "mcp_server.server:main"
```

**Issue**: Entry point is `hiveforge-steering-mcp`, not `hiveforge-power`.

**Impact**: Documentation must use correct command name.

**Status**: ✅ Verified - Entry point is correct in code.

---

### Issue 2: Package Name

**File**: `hiveforge-power/pyproject.toml`  
**Line**: 7

**Current**:
```toml
name = "hiveforge-steering-mcp"
```

**Issue**: Package name is `hiveforge-steering-mcp`, not `hiveforge-power`.

**Impact**: Documentation must use correct package name.

**Status**: ✅ Verified - Package name is correct in code.

---

### Issue 3: Module Path

**File**: `hiveforge-power/pyproject.toml`  
**Line**: 52

**Current**:
```toml
hiveforge-steering-mcp = "mcp_server.server:main"
```

**Issue**: Module path is `mcp_server.server`, not `hiveforge_power.server`.

**Impact**: MCP configuration must use correct module path.

**Status**: ✅ Verified - Module path is correct in code.

---

## Codebase Issues Preventing Installation

### None Found

All code is correct. The issue is purely documentation gaps.

---

## Recommendations

### Priority 1: Add MCP Server Installation Section

Create a new section "Installing the MCP Server" with:
1. Navigate to `hiveforge-power/` directory
2. Install package: `pip install -e .`
3. Verify installation: `hiveforge-steering-mcp --help`

### Priority 2: Add KIRO Configuration Section

Create a new section "Configuring KIRO" with:
1. Locate/create `~/.kiro/settings/mcp.json`
2. Add server configuration
3. Reload KIRO
4. Verify Power appears

### Priority 3: Add Power Registration Section

Create a new section "Registering the Power" with:
1. Explain Power metadata
2. Show how to verify registration
3. List activation keywords
4. Provide usage examples

### Priority 4: Restructure Guide

Reorganize into:
1. **Prerequisites** (unchanged)
2. **Understanding the Packages** (new)
3. **Quick Start** (new - for experienced users)
4. **Detailed Installation**
   - Installing HiveForge CLI
   - Installing the MCP Server Package
   - Configuring KIRO MCP Settings
   - Registering the Power
5. **Verification Steps** (expanded)
6. **Troubleshooting** (expanded)
7. **Next Steps** (new)

---

## Success Criteria

After fixes, a novice user should be able to:

✅ Understand there are two packages (CLI and Power)  
✅ Install both packages from source  
✅ Configure KIRO to recognize the MCP server  
✅ See the Power appear in KIRO  
✅ Use the Power to generate steering files  
✅ Troubleshoot common issues independently  

---

## Notes

- All code is correct - this is purely a documentation issue
- Focus on novice users who may not understand Python packaging or MCP
- Provide copy-pasteable commands
- Show expected outputs for verification
- Include both macOS/Linux and Windows instructions where they differ

---

**Report Status**: Complete  
**Next Step**: Rewrite INSTALLATION_GUIDE.md based on this analysis
