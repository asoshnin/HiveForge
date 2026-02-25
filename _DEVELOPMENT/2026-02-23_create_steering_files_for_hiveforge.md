# Testing HiveForge: Creating Steering Files for HiveForge Itself

**Date:** February 23, 2026  
**Purpose:** Test the HiveForge steering file generation system by using it on the HiveForge project itself  
**Expected Outcome:** Generate comprehensive steering files that document HiveForge's architecture, tech stack, and conventions

---

## Overview

This guide walks through using HiveForge to generate steering files for the HiveForge project itself. This serves as both a test of the system and a way to create proper documentation for the project.

**Why This Is Useful:**
- Tests the steering file generation system end-to-end
- Validates that code analysis works correctly
- Ensures LLM integration functions properly
- Creates actual documentation for HiveForge
- Demonstrates the system's capabilities

---

## Prerequisites

### 1. Environment Setup

Ensure you have:
- Python 3.11+ installed
- Virtual environment activated
- HiveForge installed in development mode

**Verify Installation:**
```bash
# Check Python version
python --version
# Should show: Python 3.11.x or higher

# Check if venv is activated
echo $VIRTUAL_ENV
# Should show path to .venv directory

# Verify HiveForge CLI is available
hiveforge --help
# Should show HiveForge commands

# Verify steering commands
hiveforge steering --help
# Should show: init, update, validate, reset, discover-docs
```

### 2. LLM Provider Configuration

**Option A: Using KIRO IDE (Recommended)**
- No configuration needed
- KIRO native LLM will be used automatically
- Skip to Step 3

**Option B: Using CLI with External LLM**

Choose one provider:

**Vertex AI:**
```bash
export HIVEFORGE_LLM_PROVIDER=vertex
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

**OpenAI:**
```bash
export HIVEFORGE_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-api-key
```

**No LLM (Fallback Mode):**
```bash
# Don't set any LLM variables
# System will use [INFERRED] markers
```

### 3. Project State

Ensure you're in the HiveForge project root:
```bash
pwd
# Should show: /path/to/HiveForge

ls -la # for Mac
Get-ChildItem # for Windows
# Should show: README.md, pyproject.toml, src/, tests/, docs/, etc.
```

---

## Step-by-Step Instructions

### Step 1: Prepare Source Documents (Optional but Recommended)

The steering assistant can use existing documentation as source material. Let's gather relevant docs.

**1.1 Create a staging folder for source documents:**
```bash
mkdir -p .kiro/onboarding
```

**1.2 Copy relevant documentation:**
```bash
# Copy main documentation files
cp README.md .kiro/onboarding/
cp CHANGELOG.md .kiro/onboarding/
cp CONTRIBUTING.md .kiro/onboarding/

# Copy architecture documentation
cp docs/architecture.md .kiro/onboarding/
cp docs/development.md .kiro/onboarding/
cp docs/steering-assistant-guide.md .kiro/onboarding/

# Copy spec documents (these describe the system design)
cp .kiro/specs/hiveforge-steering-improvements/requirements.md .kiro/onboarding/
cp .kiro/specs/hiveforge-steering-improvements/design.md .kiro/onboarding/

# Copy configuration documentation
cp hiveforge-power/docs/CONFIGURATION.md .kiro/onboarding/
cp hiveforge-power/docs/LLM_CONFIGURATION.md .kiro/onboarding/
```

**1.3 Verify source documents:**
```bash
ls -la .kiro/onboarding/
# Should show all copied files
```

**Expected Result:**
- `.kiro/onboarding/` contains 10+ markdown files
- These provide context for steering file generation
- Higher confidence scores in generated files

---

### Step 2: Run Dry-Run Mode (Preview)

Before generating actual files, preview what will be created.

**2.1 Run dry-run with code analysis:**
```bash
hiveforge steering init --analyze-code
```

**What This Does:**
1. Analyzes the HiveForge codebase
2. Parses documents in `.kiro/onboarding/`
3. Generates preview of steering files
4. Shows confidence scores
5. Does NOT write files to disk

**Expected Output:**
```
🔍 Analyzing codebase...
✓ Detected: Python 3.11, Poetry, pytest
✓ Architecture: CLI tool with MCP server capabilities
✓ Found 42 Python files, 863 tests

📄 Parsing source documents...
✓ Parsed 10 documents from .kiro/onboarding/

📊 Preview of steering files to be generated:

1. project-vision.md
   Confidence: 85% (HIGH)
   Source documents: 3
   Preview: # Project Vision: HiveForge
            
            ## Elevator Pitch
            HiveForge is a CLI scaffolding tool that generates KIRO...

2. tech-stack.md
   Confidence: 92% (HIGH)
   Source documents: 5
   Preview: # Technology Stack
            
            ## Core Technologies
            ### Backend
            - Language: Python 3.11
            - Framework: Typer (CLI), FastMCP (MCP server)...

3. architecture.md
   Confidence: 88% (HIGH)
   Source documents: 4
   Preview: # Architecture Overview
            
            ## System Diagram
            [Mermaid diagram showing CLI, Steering Assistant, workflows]...

[... continues for all 8 files ...]

Summary:
- Files to create: 8
- Average confidence: 87% (HIGH)
- Source documents used: 10
- Inferred sections: 3

⚠️  This is a DRY RUN - no files were written.
Run without --dry-run to create files.
```

**2.2 Review the preview:**
- Check confidence scores (should be >70% for most files)
- Look for [INFERRED] markers (indicates missing information)
- Verify that content looks accurate

**Decision Point:**
- ✅ If preview looks good → Proceed to Step 3
- ❌ If confidence is low → Add more source documents and re-run dry-run
- ⚠️ If [INFERRED] markers are excessive → Consider using LLM provider

---

### Step 3: Generate Steering Files (Interactive Mode)

Now generate the actual steering files with interactive review.

**3.1 Run init with code analysis:**
```bash
hiveforge steering init --analyze-code
```

**What Happens:**

**Phase 1: Analysis**
```
🔍 Analyzing codebase...
✓ Languages: Python 3.11
✓ Frameworks: Typer, FastMCP, pytest
✓ Architecture: CLI tool with MCP server
✓ MCP Tools: 5 detected (init_steering, update_steering, validate_steering, reset_steering, discover_docs)
✓ CLI Commands: 3 detected (init, update, validate)
✓ Public Classes: 15 detected (CodeAnalyzer, SteeringAssistant, LLMProvider, DriftDetector, etc.)
```

**Phase 2: Document Parsing**
```
📄 Parsing source documents...
✓ README.md (5,234 chars)
✓ architecture.md (12,456 chars)
✓ requirements.md (8,901 chars)
[... continues for all documents ...]
✓ Parsed 10 documents (45,678 total chars)
```

**Phase 3: Gap Analysis**
```
🔍 Running gap analysis...
✓ project-vision.md: 95% complete (1 question)
✓ tech-stack.md: 100% complete
✓ conventions.md: 90% complete (2 questions)
✓ architecture.md: 100% complete
✓ db-standards.md: N/A (no database detected)
✓ api-standards.md: 85% complete (3 questions)
✓ ui-standards.md: N/A (no frontend detected)
✓ qa-standards.md: 95% complete (1 question)

Total questions: 7
```

**Phase 4: Interactive Conversation (if needed)**

If gap analysis found missing information, you'll be asked questions:

```
📋 I need some additional information:

1. What is the target release date for v2.0?
   > March 2026

2. What is the minimum test coverage requirement?
   > 80%

3. Are there any specific API rate limiting requirements?
   > No rate limiting needed (local tool)

[... continues for remaining questions ...]

✓ All questions answered
```

**Phase 5: File Generation**
```
✨ Generating steering files...
✓ project-vision.md (confidence: 85%)
✓ tech-stack.md (confidence: 92%)
✓ conventions.md (confidence: 88%)
✓ architecture.md (confidence: 90%)
✓ api-standards.md (confidence: 82%)
✓ qa-standards.md (confidence: 87%)

⚠️  Skipped files (not applicable):
  - db-standards.md (no database detected)
  - ui-standards.md (no frontend detected)

✓ Generated 6 steering files
```

**Phase 6: Validation**
```
🔍 Validating generated files...
✓ project-vision.md: PASS
✓ tech-stack.md: PASS
✓ conventions.md: PASS
✓ architecture.md: PASS
✓ api-standards.md: PASS
✓ qa-standards.md: PASS

Summary:
- Files validated: 6
- Passed: 6
- Warnings: 0
- Critical issues: 0

✅ All validation checks passed!
```

**Expected Result:**
- 6 steering files created in `.kiro/steering/`
- All files have high confidence scores (>80%)
- Validation passes with no critical issues

---

### Step 4: Review Generated Files

Manually review the generated steering files to ensure accuracy.

**4.1 Check project-vision.md:**
```bash
cat .kiro/steering/project-vision.md
```

**What to verify:**
- ✅ Elevator pitch accurately describes HiveForge
- ✅ Problem statement matches actual use case
- ✅ Target users are correct (developers using KIRO methodology)
- ✅ Success metrics are reasonable
- ✅ Timeline is accurate

**4.2 Check tech-stack.md:**
```bash
cat .kiro/steering/tech-stack.md
```

**What to verify:**
- ✅ Python version is correct (3.11+)
- ✅ Key dependencies listed (Typer, FastMCP, pytest, etc.)
- ✅ No database section (HiveForge doesn't use a database)
- ✅ Infrastructure section mentions Poetry, pip

**4.3 Check architecture.md:**
```bash
cat .kiro/steering/architecture.md
```

**What to verify:**
- ✅ System diagram shows CLI, Steering Assistant, workflows
- ✅ Component responsibilities are accurate
- ✅ Data flow is correct
- ✅ Key decisions are documented

**4.4 Check conventions.md:**
```bash
cat .kiro/steering/conventions.md
```

**What to verify:**
- ✅ Python naming conventions (snake_case, PascalCase)
- ✅ Code style (line length, indentation)
- ✅ Testing requirements (80% coverage)
- ✅ Git conventions (conventional commits)

**4.5 Check api-standards.md:**
```bash
cat .kiro/steering/api-standards.md
```

**What to verify:**
- ✅ MCP tool standards documented
- ✅ CLI command standards documented
- ✅ Error handling patterns
- ✅ No REST API section (HiveForge is a CLI tool)

**4.6 Check qa-standards.md:**
```bash
cat .kiro/steering/qa-standards.md
```

**What to verify:**
- ✅ Test coverage requirement (80%)
- ✅ Test file naming conventions
- ✅ Testing frameworks (pytest)
- ✅ CI/CD integration

---

### Step 5: Check Confidence Metadata

Each file should have confidence metadata in the frontmatter.

**5.1 Check frontmatter:**
```bash
head -n 10 .kiro/steering/tech-stack.md
```

**Expected Output:**
```yaml
---
confidence_level: high
confidence_score: 0.92
source_documents_found: 5
inferred_sections: []
generated_at: 2026-02-23T10:30:00Z
---

# Technology Stack
```

**What to verify:**
- ✅ `confidence_level` is "high" or "medium" (not "low")
- ✅ `confidence_score` is >0.7
- ✅ `source_documents_found` is >0
- ✅ `inferred_sections` is empty or minimal

**5.2 Check for [INFERRED] markers:**
```bash
grep -r "\[INFERRED" .kiro/steering/
```

**Expected Result:**
- Few or no [INFERRED] markers
- If present, they should be in non-critical sections

---

### Step 6: Validate Steering Files

Run strict validation to ensure completeness.

**6.1 Run validation:**
```bash
hiveforge steering validate --strict
```

**Expected Output:**
```
🔍 Validating steering files...

Validation Report
================

✓ project-vision.md: PASS
✓ tech-stack.md: PASS
✓ conventions.md: PASS
✓ architecture.md: PASS
✓ api-standards.md: PASS
✓ qa-standards.md: PASS

Summary
-------
Files checked: 6
Passed: 6
Warnings: 0
Critical issues: 0

✅ Validation PASSED
```

**If validation fails:**
```bash
# Review the validation report
# Fix issues manually
# Re-run validation
hiveforge steering validate --strict
```

---

### Step 7: Test Drift Detection (Optional)

Test the drift detection system by checking if steering files match the codebase.

**7.1 Run drift detection:**
```bash
# This is done via update workflow
hiveforge steering update --dry-run
```

**Expected Output:**
```
🔍 Analyzing codebase for drift...
✓ No drift detected

Summary:
- Language version: ✓ Matches (Python 3.11)
- Dependencies: ✓ All documented
- Architecture: ✓ Matches codebase
- Conventions: ✓ Consistent

✅ Steering files are up to date!
```

**If drift is detected:**
```
⚠️  Drift detected:

1. [language_version] Confidence: 95%
   Python version mismatch: tech-stack.md says 3.10, pyproject.toml has 3.11
   → Update tech-stack.md to Python 3.11

2. [new_dependency] Confidence: 85%
   New significant dependency detected: pydantic
   → Add pydantic to tech-stack.md dependencies table
```

**Action:** Update steering files to fix drift.

---

### Step 8: Commit Steering Files

If everything looks good, commit the steering files to git.

**8.1 Review changes:**
```bash
git status
# Should show new files in .kiro/steering/

git diff .kiro/steering/
# Review the content
```

**8.2 Commit:**
```bash
git add .kiro/steering/
git commit -m "docs: generate steering files for HiveForge project

- Generated 6 steering files using hiveforge steering init
- High confidence scores (avg 87%)
- All validation checks passed
- Documented project vision, tech stack, architecture, conventions, API standards, QA standards

Generated with: hiveforge steering init --analyze-code"
```

**8.3 Push (optional):**
```bash
git push origin main
```

---

## Alternative: Using KIRO IDE (MCP Mode)

If you prefer using KIRO IDE instead of CLI:

### Step 1: Open HiveForge in KIRO IDE

```bash
# Open KIRO IDE with HiveForge project
code .  # or your IDE command
```

### Step 2: Use HiveForge Power

In KIRO chat, type:

```
Initialize steering files for the HiveForge project using documents from .kiro/onboarding/
```

**What happens:**
1. KIRO invokes the HiveForge Power's `init_steering` MCP tool
2. Tool analyzes codebase and parses documents
3. LLM generates steering files
4. Draft is created and shown in IDE
5. You review and approve

### Step 3: Review Draft

KIRO will show a draft summary:

```
# Draft Summary

## project-vision.md
- Confidence: 85%
- Placeholders: 0
- Preview: # Project Vision: HiveForge

## Elevator Pitch
HiveForge is a CLI scaffolding tool...

[... continues for all files ...]
```

### Step 4: Apply Draft

If draft looks good, in KIRO chat:

```
Apply the steering file draft
```

This writes the files to `.kiro/steering/`.

---

## Troubleshooting

### Issue: Low Confidence Scores

**Symptoms:**
- Confidence scores <0.5
- Many [INFERRED] markers
- Generic content

**Solutions:**
1. Add more source documents to `.kiro/onboarding/`
2. Configure an LLM provider (Vertex AI or OpenAI)
3. Run with `--research` flag to enable web research

### Issue: Validation Failures

**Symptoms:**
- Validation reports critical issues
- Unreplaced placeholders
- Missing required sections

**Solutions:**
1. Review validation report carefully
2. Manually edit problematic files
3. Re-run validation
4. If persistent, regenerate with more source documents

### Issue: LLM Provider Not Available

**Symptoms:**
- Warning: "No LLM provider available"
- All content has [INFERRED] markers

**Solutions:**
1. Configure LLM provider (see Prerequisites)
2. Use KIRO IDE (automatic LLM access)
3. Accept [INFERRED] markers and manually fill in content

### Issue: Code Analysis Timeout

**Symptoms:**
- "Code analysis timeout" error
- Analysis takes >5 minutes

**Solutions:**
1. Check for very large codebase (>10k files)
2. Ensure `.gitignore` is properly configured
3. Remove unnecessary files (node_modules, .venv, etc.)

### Issue: Empty or Generic Content

**Symptoms:**
- Steering files contain only templates
- No project-specific information

**Solutions:**
1. Ensure source documents are in `.kiro/onboarding/`
2. Run with `--analyze-code` flag
3. Check that LLM provider is configured
4. Verify source documents are relevant and detailed

---

## Expected Results Summary

After completing all steps, you should have:

✅ **6 steering files** in `.kiro/steering/`:
- project-vision.md
- tech-stack.md
- conventions.md
- architecture.md
- api-standards.md
- qa-standards.md

✅ **High confidence scores** (>80% average)

✅ **Minimal [INFERRED] markers** (<5% of content)

✅ **All validation checks passed**

✅ **No drift detected** (steering files match codebase)

✅ **Committed to git** with descriptive commit message

---

## Next Steps

After generating steering files for HiveForge:

1. **Use them in development:**
   - Reference steering files when making changes
   - Update them when architecture evolves
   - Use them for onboarding new contributors

2. **Test update workflow:**
   - Make a code change
   - Run `hiveforge steering update`
   - Verify drift detection works

3. **Test on other projects:**
   - Try generating steering files for other projects
   - Compare results
   - Refine the system based on feedback

4. **Document learnings:**
   - Note what worked well
   - Identify areas for improvement
   - Update documentation

---

## Success Criteria

This test is successful if:

- ✅ All 6 steering files generated without errors
- ✅ Average confidence score >80%
- ✅ Validation passes with no critical issues
- ✅ Content is accurate and project-specific
- ✅ [INFERRED] markers are minimal (<5%)
- ✅ Files are useful for actual project documentation

---

## Appendix: File Checklist

Use this checklist to verify each generated file:

### project-vision.md
- [ ] Elevator pitch is accurate
- [ ] Problem statement is clear
- [ ] Solution overview matches HiveForge's approach
- [ ] Target users are correct
- [ ] Success metrics are defined
- [ ] Timeline is realistic

### tech-stack.md
- [ ] Python version is correct (3.11+)
- [ ] Key dependencies listed (Typer, FastMCP, pytest)
- [ ] No database section (not applicable)
- [ ] Infrastructure section mentions Poetry
- [ ] Rationale explains technology choices

### conventions.md
- [ ] Python naming conventions documented
- [ ] Code style rules defined (line length, indentation)
- [ ] Testing requirements specified (80% coverage)
- [ ] Git conventions documented (conventional commits)
- [ ] Documentation standards defined

### architecture.md
- [ ] System diagram shows main components
- [ ] Component responsibilities are clear
- [ ] Data flow is documented
- [ ] Key decisions are explained
- [ ] Scalability considerations mentioned

### api-standards.md
- [ ] MCP tool standards documented
- [ ] CLI command standards documented
- [ ] Error handling patterns defined
- [ ] No REST API section (not applicable)
- [ ] Versioning strategy explained

### qa-standards.md
- [ ] Test coverage requirement (80%)
- [ ] Test file naming conventions
- [ ] Testing frameworks (pytest)
- [ ] CI/CD integration documented
- [ ] Quality gates defined

---

**Last Updated:** February 23, 2026  
**Author:** HiveForge Team  
**Status:** Ready for Testing
