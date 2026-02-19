# Red Team Report: HiveForge UX & Codebase Assessment
**Date:** 2026-02-19
**Perspective:** Expert Product Owner + KIRO Vibe Coder (novice-to-intermediate user)
**Scope:** UX, documentation, MCP tools, CLI, workflows, hallucination risks, guardrails

---

## Executive Summary

HiveForge has a solid technical foundation — the shared backend architecture, security wrapper, and telemetry are well-engineered. However, the **user-facing layer is broken in several critical ways**. The gap between what the documentation promises and what the tools actually deliver is large enough to cause consistent failure for real users. The most damaging issue is that the primary recommended workflow (KIRO IDE + Steering Assistant) relies on a hardcoded staging folder (`.kiro/onboarding/`) that users cannot override, while the documentation never clearly explains this constraint. Users with documents in any other folder — which is the majority of real-world cases — will silently get wrong results or no results.

---

## CRITICAL Issues

### C1. No `source_docs_path` Parameter in Any MCP Tool

**What the code does:**
All five MCP tools (`init_steering`, `update_steering`, `discover_docs`, `validate_steering`, `reset_steering`) accept only `project_root` as a path parameter. There is no way to specify where source/design documents are located.

**What the user expects:**
When a user says "Initialize steering files for my project; the original documents are in the folder `_DEVELOPMENT`", KIRO will pass this as natural language to the LLM. The LLM will call `init_steering(project_root=".")` — the `_DEVELOPMENT` instruction is **silently dropped**. The tool then scans the entire project root, not the specified folder.

**Why this is critical:**
- Users with organized project structures (docs in `_DEVELOPMENT`, `original_docs`, `design/`, etc.) get no benefit from their organization
- There is zero feedback that the folder specification was ignored
- The tool may generate steering files based on code analysis alone, producing generic/wrong output
- This is the #1 source of hallucination risk: the LLM confidently generates steering files from insufficient or wrong source material

**Fix required:** Add `source_docs_path: str = None` parameter to `init_steering` and `discover_docs`. When provided, restrict document discovery to that path instead of (or in addition to) the project root.

---

### C2. Hardcoded `.kiro/onboarding/` Staging Folder — Never Explained to Users

**What the code does:**
`InitWorkflow.__init__()` hardcodes the staging directory:
```python
self.state = WorkflowState(
    workflow_type="init",
    staging_dir=self.project_root / ".kiro" / "onboarding",
    ...
)
```

**What the documentation says:**
`WORKFLOW_refactoring_01.md` Step 2.1 says: "Place your original documents in the `.kiro/onboarding/` folder." This is correct but buried in a multi-phase workflow guide. The `steering-assistant-guide.md` also mentions it. However:

- `WORKFLOW.md` Workflow 2 ("Converting Existing Documents") describes an "AI-Assisted Conversion" approach that never mentions `.kiro/onboarding/` at all
- The KIRO Power's `POWER.md` and the MCP tool descriptions do not mention this requirement
- A user who types "Initialize steering files for my project" in KIRO chat will get a tool call with no document context, because their docs are not in `.kiro/onboarding/`

**Why this is critical:**
The recommended path (KIRO IDE + Power) has no mechanism to tell the user "please copy your documents to `.kiro/onboarding/` first." The tool runs, produces output, and the user has no idea the output was generated without their documents.

**Fix required:** Either (a) add `source_docs_path` parameter (see C1), or (b) make `init_steering` return a warning when `.kiro/onboarding/` is empty AND no `source_docs_path` was provided, explicitly telling the user what to do.

---

### C3. No Hallucination Guardrails in Steering File Generation

**What the code does:**
`SharedInitWorkflow` (via adapters) runs gap analysis and then calls `SteeringAssistant.conduct_conversation()`. In autonomous/non-interactive mode (the default for the MCP Power), the assistant fills gaps using LLM inference with no grounding check.

**The risk:**
When source documents are absent or sparse, the LLM will invent plausible-sounding content for all 8 steering files. A user running `init_steering` on a project with no documents in `.kiro/onboarding/` will receive 8 fully-populated steering files that look authoritative but are fabricated.

**Concrete example:**
- User has a Python FastAPI project
- `.kiro/onboarding/` is empty
- `init_steering` runs code analysis, finds FastAPI
- LLM fills `project-vision.md` with invented problem statements, target users, success metrics
- User doesn't realize these are hallucinated — they look real
- These hallucinated steering files then guide all future agent behavior

**Fix required:**
- When `auto_discover` finds zero documents in the staging folder, the tool should either (a) refuse to generate content-heavy files like `project-vision.md` and return a warning, or (b) clearly mark all LLM-inferred sections with `[INFERRED - PLEASE VERIFY]` tags
- Add a `confidence_score` field to the output for each generated file

---

### C4. WORKFLOW.md Recommends a Workflow That Doesn't Work as Described

**The claim in WORKFLOW_refactoring_01.md Step 2.2:**
> "Use KIRO IDE + Steering Assistant Agent... Act as Steering Assistant agent... Use this exact prompt: 'I have original project documents in `.kiro/onboarding/`...'"

**The reality:**
The "Steering Assistant" agent (`.kiro/agents/steering_assistant.md`) is a KIRO agent definition, not the HiveForge Power. When a user "acts as Steering Assistant agent" in KIRO, they are using a general KIRO agent with a custom system prompt — not the HiveForge MCP tools. This agent reads `.kiro/onboarding/` directly via KIRO's file tools, which works, but:

1. It bypasses all HiveForge validation, gap analysis, and template population logic
2. The output quality depends entirely on the agent prompt, not the HiveForge engine
3. The workflow guide presents this as equivalent to `hiveforge steering init` — it is not
4. There is no mention that the Power tools (`init_steering` MCP tool) are the correct way to invoke HiveForge from KIRO

**The user confusion this creates:**
A user following the guide will use the Steering Assistant agent (KIRO agent), get some steering files, and believe they used HiveForge. They never actually invoked the HiveForge Power. The Power's 5 MCP tools are never mentioned in the recommended workflow.

**Fix required:** WORKFLOW_refactoring_01.md Step 2.2 must be rewritten to show the correct Power invocation: "In KIRO chat, type: `Initialize steering files for my project`" — which triggers the `init_steering` MCP tool. The Steering Assistant agent approach should be documented separately as a manual fallback.

---

## IMPORTANT Issues

### I1. Two-Package Installation Is Confusing and Error-Prone

**Current state:**
Users must install two separate packages:
1. `pip install -e /path/to/HiveForge` (the core library)
2. `pip install /path/to/HiveForge/hiveforge-power` (the MCP server)

Plus configure `~/.kiro/settings/mcp.json` with an absolute path to the venv Python binary.

**The problem:**
- The README only documents the first install
- `INSTALLATION_GUIDE.md` was incomplete until recently patched
- The venv Python path in `mcp.json` is machine-specific and breaks when the venv is recreated or moved
- There is no `pip install hiveforge-power` from PyPI — users who try this get a confusing error
- The Power registration step (KIRO Powers panel → "Add Custom Power" → local folder) is a separate manual step not covered in any automated way

**Fix required:** Create a single `install.sh` script that does all steps. Or at minimum, consolidate into one `pyproject.toml` that installs both packages together.

---

### I2. `discover_docs` Tool Has No Subfolder Targeting

**Current state:**
`discover_docs` accepts `project_root` and scans up to `max_discovery_files` files from that root. On a real project with hundreds of source files, this means the tool spends most of its budget on `.py`, `.ts`, and config files rather than design documents.

**The problem:**
A user with 500 source files and 10 design docs in `_DEVELOPMENT/` will have their design docs diluted or missed entirely if the file budget is exhausted by source files first.

**Fix required:** Add `docs_path: str = None` parameter. When provided, prioritize or restrict discovery to that path.

---

### I3. `mcp.json` Requires Hardcoded Absolute Venv Path — Fragile

**Current state:**
```json
{
  "command": "/Users/alexeysoshnin/.../venv/bin/python",
  "args": ["-m", "mcp_server.server"]
}
```

**The problem:**
- Path breaks if venv is recreated
- Path is machine-specific — cannot be committed to a shared repo
- No documentation on how to update this when the venv changes
- New team members must manually find their Python path

**Fix required:** The `hiveforge-power` package should install a proper console script entry point (`hiveforge-steering-mcp`) that can be invoked without a full path. The `mcp.json` should then use `"command": "hiveforge-steering-mcp"` with the venv activated via `PATH` or an `env` block.

---

### I4. Phase 3 (Discrepancy Analysis) Is Described as Automated But Is Fully Manual

**What WORKFLOW_refactoring_01.md implies:**
Phase 3 is presented as a structured, multi-agent workflow with delegation trees, specialized agents, and a generated `DISCREPANCY_REPORT.md`. The Mermaid diagram shows it as an automated pipeline.

**The reality (stated in the same document, buried in a warning box):**
> "⚠️ Critical Limitation: HiveForge does NOT have built-in discrepancy analysis."

This disclaimer appears *after* 3 pages of detailed instructions that make it look automated. A user following the guide will spend significant time setting up Phase 3 before discovering it's just "ask KIRO to do it manually."

**Fix required:** Move the limitation warning to the top of Phase 3, before any instructions. Rename Phase 3 to "Manual Discrepancy Analysis (KIRO IDE)" to set expectations correctly.

---

### I5. `init_steering` in Autonomous Mode Skips the Conversation — Undocumented

**What the code does:**
`SharedInitWorkflow` is called with `autonomous=True` (the default). In this mode, the `SteeringAssistant.conduct_conversation()` is called but the interactive Q&A is skipped — the LLM fills gaps autonomously.

**The problem:**
The POWER.md and tool docstring say `autonomous: Enable autonomous generation mode (default: True)` but don't explain what "autonomous" means in practice: that the LLM will invent answers to questions it would otherwise ask the user. This is the primary hallucination vector.

**Fix required:** The tool description should explicitly state: "When `autonomous=True`, the LLM will infer missing information without asking the user. Set to `False` to enable interactive Q&A mode (CLI only)."

---

### I6. Cache Is Broken by Design

**What the code does:**
`CodeAnalyzer._load_cache()` always returns `None`:
```python
logger.info("Cache found and valid")
return None  # For now, always re-analyze
```

**The problem:**
The cache feature is documented (in code comments and architecture docs) as a performance optimization for large codebases. It is silently non-functional. Every `init_steering` call re-runs full code analysis regardless of cache state. On large codebases this can take minutes.

**Fix required:** Either implement the cache properly or remove the cache infrastructure and documentation references to avoid misleading users.

---

## NICE TO HAVE

### N1. `discover_docs` Should Return a Preview Before `init_steering` Runs

Currently, users have no way to verify what documents HiveForge will use before generating steering files. A pre-flight check — "I found these 12 files, proceed?" — would prevent silent failures.

---

### N2. Steering File Generation Should Show Per-File Confidence

Each generated steering file should include a metadata header or footer showing:
- Source documents used
- Confidence level (high/medium/low/inferred)
- Which sections were inferred vs. extracted

This gives users immediate visibility into hallucination risk.

---

### N3. INSTALLATION_GUIDE.md Should Be the Single Source of Truth

Currently installation information is spread across:
- `README.md` (core library only)
- `hiveforge-power/POWER.md` (Power installation)
- `INSTALLATION_GUIDE.md` (patched, but still incomplete)
- `WORKFLOW_refactoring_01.md` Phase 1 (another version of install steps)

These are inconsistent. One canonical guide should exist; others should link to it.

---

### N4. The `.kiro/onboarding/` Folder Name Is Not Intuitive

"Onboarding" implies a one-time setup process. Users who want to add new design documents later won't think to put them in "onboarding." A name like `.kiro/source-docs/` or `.kiro/design-artifacts/` would better communicate the folder's ongoing purpose.

---

### N5. No Dry-Run Mode for `init_steering`

Users cannot preview what files will be created/overwritten before committing. A `--dry-run` flag (CLI) or `dry_run: bool = False` parameter (MCP) would reduce anxiety for first-time users.

---

## Summary Table

| ID | Category | Issue | Impact | Effort to Fix |
|----|----------|-------|--------|---------------|
| C1 | Critical | No `source_docs_path` parameter | Users' design docs silently ignored | Medium |
| C2 | Critical | Hardcoded `.kiro/onboarding/` not communicated via Power | Tool runs without user docs | Low |
| C3 | Critical | No hallucination guardrails in autonomous mode | Fabricated steering files look real | Medium |
| C4 | Critical | WORKFLOW.md recommends wrong workflow path | Users never invoke the actual Power | Low |
| I1 | Important | Two-package install is fragile and underdocumented | High failure rate for new users | Medium |
| I2 | Important | `discover_docs` can't target a subfolder | Design docs diluted by source files | Low |
| I3 | Important | Hardcoded venv path in `mcp.json` | Breaks on venv recreation | Low |
| I4 | Important | Phase 3 looks automated but is manual | User time wasted on setup | Low |
| I5 | Important | `autonomous=True` behavior not explained | Silent hallucination risk | Low |
| I6 | Important | Cache always returns `None` | Performance regression on large codebases | Medium |
| N1 | Nice to Have | No pre-flight document preview | Blind trust in tool | Low |
| N2 | Nice to Have | No per-file confidence scores | Hard to spot hallucinations | Medium |
| N3 | Nice to Have | Installation info scattered | Confusion for new users | Low |
| N4 | Nice to Have | `.kiro/onboarding/` name unintuitive | Discoverability issue | Low |
| N5 | Nice to Have | No dry-run mode | Anxiety for first-time users | Low |

---

## Recommended Priority Order for Fixes

1. **C1 + C2 together** — Add `source_docs_path` to `init_steering` and `discover_docs`. This single change fixes the most common failure mode.
2. **C4** — Rewrite WORKFLOW_refactoring_01.md Step 2.2 to show correct Power invocation. Zero code change required.
3. **C3** — Add empty-staging-folder warning and `[INFERRED]` tags to autonomous output.
4. **I3** — Fix `mcp.json` to use console script entry point instead of absolute Python path.
5. **I4** — Move Phase 3 limitation warning to top of section.
6. **I6** — Fix or remove the broken cache.
7. **I1** — Create unified install script.
