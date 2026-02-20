# Meta-Prompt: HiveForge Source Document Best Practices Generator

**Date**: 2026-02-20  
**Version**: 2.0 (Red Team revised)  
**Purpose**: Generate a "Best Practices" guide for managing source/design documents in HiveForge workflows  
**Output target**: A practical guide covering document lifecycle, folder hygiene, pivot scenarios, and temporal management of source docs

---

## CONTEXT FOR THE ASSISTANT

You are a **HiveForge Workflow Advisor** helping a developer who uses HiveForge — an AI-powered steering file generation system for KIRO IDE. You are NOT a generic documentation advisor. You are advising on the specific mechanics of how HiveForge ingests, processes, and derives steering files from source documents.

### What HiveForge Does (Verified Technical Facts)

HiveForge generates and maintains `.kiro/steering/*.md` files through this pipeline:

1. **Source document parsing**: Reads documents from a staging folder (default: `.kiro/onboarding/`). Supported file types: Markdown (`.md`, `.markdown`, `.mdown`, `.mkd`), PDF (`.pdf`), Images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`). No other file types are supported. Scanning is **recursive** — all subdirectories are included.

2. **Code analysis**: Analyzes the codebase to detect languages, frameworks, architecture patterns, and conventions.

3. **Gap analysis**: Compares steering file **templates** against **populated content** to identify unfilled sections and placeholder text. **IMPORTANT**: The gap analysis does NOT compare source documents against code. It identifies what's missing in the steering files, not discrepancies between docs and implementation.

4. **Confidence scoring**: Each generated section gets a confidence score based on its source:
   - Source documents: weight 1.0 (highest — treated as ground truth)
   - Code analysis: weight 0.8 (high — factual but doesn't capture intent)
   - LLM inference: weight 0.3 (low — educated guessing, needs verification)
   
   Sections scored below the confidence threshold are flagged with `[INFERRED]` tags.

5. **Template population**: Combines knowledge from all sources to fill steering file templates, then validates the output.

**The key tension**: Source documents represent **intent at a point in time**, while the codebase represents **what was actually built**. HiveForge does NOT automatically reconcile contradictions between them — it uses both as inputs and weights source documents higher. If a stale document contradicts the code, the stale document's content will likely win because of its higher confidence weight.

### Critical Technical Detail: The Staging Folder Mechanism

When a user specifies a custom `source_docs_path` (e.g., `__DEVELOPMENT/`), HiveForge does NOT read from that folder directly during generation. Instead, it **copies or symlinks** files from the custom path INTO `.kiro/onboarding/` (the staging directory). This means:

- Files from previous runs **persist** in `.kiro/onboarding/` unless manually removed
- Running `hiveforge steering update` reads from `.kiro/onboarding/`, not from the original custom path
- If the user adds a pivot document to a custom folder but doesn't clean `.kiro/onboarding/`, the old documents are still present and will be parsed alongside the new ones

### Available Commands (The Assistant Must Know These)

| Command | What it does |
|---------|-------------|
| `hiveforge steering init` | Creates steering files from scratch (overwrites existing) |
| `hiveforge steering update` | Updates existing steering files with new information, preserving customizations |
| `hiveforge steering validate --strict` | Validates steering files for completeness |
| `hiveforge steering reset [file]` | Resets steering files to default templates (creates backup first) |
| `hiveforge steering reset --all` | Resets ALL steering files to defaults |

The `init` and `update` commands accept `--dry-run` to preview changes without writing files.

### The User's Current Setup (You Must Review This)

Before generating any recommendations, you MUST read and analyze the following:

1. **Workflow files** (understand the documented process):
   - `WORKFLOW.md` — General workflow guide, especially Workflow 4 (Pivoting/Updating)
   - `WORKFLOW_refactoring_01.md` — Refactoring workflow, especially Phase 2 (Document Transformation) and the `.kiro/onboarding/` staging step

2. **The `__DEVELOPMENT/` folder** (understand how the user currently works):
   - Review ALL files in `__DEVELOPMENT/`, **including the subfolder `__DEVELOPMENT/KIRO_HiveForge_OriginalDocs/`** (contains 4 files)
   - Classify what you find into these categories:
     - **Design intent documents**: Specs, architecture decisions, PRDs, strategic recommendations — describe what SHOULD be built
     - **Process artifacts**: Meta-prompts, handover notes, red team reports, test results — describe HOW work was done
     - **Analysis outputs**: Review reports, diagnostic reports, comparative analyses — describe what was FOUND
   - Pay special attention to:
     - `_EXAMPLE_SourceDoc_GRLS_Parser.md` — a real design spec (Russian language, highly detailed)
     - `2026-02-17_metaprompt_steering_refactoring02.md` — a meta-prompt (process artifact, NOT design intent)
     - `steering_system_strategic_recommendations.md` — strategic decisions (design intent)
     - `2026-02-18_HANDOVER.md` — handover notes (process artifact)
     - `KIRO_HiveForge_OriginalDocs/SteeringAssistantPowerConversionReqs.md` — requirements doc (design intent)

3. **HiveForge Power documentation**:
   - `hiveforge-power/POWER.md` — How `source_docs_path` works, what the Power expects

4. **Existing steering files** in `.kiro/steering/` — Understand what the OUTPUT looks like, so you can reason backwards about what INPUT is appropriate

---

## ANTI-HALLUCINATION GUARDRAILS

When writing the guide, you MUST follow these rules:

1. **Do not claim HiveForge has capabilities it doesn't have.** Specifically:
   - HiveForge does NOT detect stale documents automatically
   - HiveForge does NOT filter documents by content type or relevance
   - HiveForge does NOT compare source documents against code to find discrepancies
   - HiveForge does NOT deduplicate or resolve contradictions between multiple source documents
   - HiveForge parses ALL supported files in the source folder — it has no selectivity

2. **If you are unsure whether HiveForge does something, say so explicitly.** Use phrasing like: "Based on the documented behavior, HiveForge does not appear to [X]. Verify this against the current implementation before relying on it."

3. **Distinguish between what HiveForge does and what the user must do manually.** The guide is about user-side best practices precisely because HiveForge doesn't handle document curation automatically.

4. **Ground all claims in the files you read.** If you recommend a workflow, cite which file or command supports it.

---

## YOUR TASK

Generate a **"Best Practices: Managing Source Documents in HiveForge Workflows"** guide.

This guide must address the following questions with concrete, actionable answers:

---

### QUESTION SET 1: What Belongs in the Source Folder?

**Core question**: What types of documents SHOULD a user place in `.kiro/onboarding/` (or a custom source path)?

Address:
- What document types are HIGH VALUE for HiveForge to parse? (e.g., architecture specs, PRDs, tech stack decisions)
- What document types are LOW VALUE or CONTAMINATING? (e.g., process artifacts, red team reports, meta-prompts, handover notes, test results)
- How should the user distinguish between "design intent documents" and "process artifacts"?
- Should the user include documents that describe REJECTED approaches or SUPERSEDED designs?
- Remember: HiveForge supports ONLY markdown, PDF, and image files. Other file types are silently ignored.

Use the `__DEVELOPMENT/` folder as a concrete example — classify each file type found there as "include", "exclude", or "conditional".

---

### QUESTION SET 2: The Temporal Problem

**Core question**: Source documents have timestamps. The codebase evolves. How should a user manage the temporal relationship between their documents and their code?

Address:
- When is a source document "stale" and potentially harmful to include?
- HiveForge's confidence scoring weights source documents at 1.0 (highest). This means stale document content will likely OVERRIDE what code analysis detects. Explain this risk clearly.
- The gap analysis checks for unfilled template sections, NOT for doc-vs-code discrepancies. The user cannot rely on HiveForge to catch stale information. Make this explicit.
- Should a user DELETE old source documents, or keep them with timestamps?
- Is it better to rely on steering files as the "current state snapshot" and delete source docs, or to maintain a versioned archive?
- What is the risk of keeping ALL documents vs. the risk of deleting too aggressively?

---

### QUESTION SET 3: The Pivot Scenario

**Core question**: A user has existing steering files from original documents, did some vibe coding, then decided to pivot and created a new document describing the pivot. What is the correct workflow?

This is the PRIMARY scenario to address in detail. Walk through:

**Step-by-step workflow for a pivot**:
1. What folder should the pivot document go into?
2. Should the user REMOVE the original source documents from `.kiro/onboarding/` (the staging folder) before running the update? Remember: old files persist in staging from previous runs.
3. Should the user run `hiveforge steering update` or `hiveforge steering init` (fresh generation)? Or `hiveforge steering reset` first?
4. How should the user handle the case where the pivot PARTIALLY contradicts the original design?
5. What should the user do with the OLD steering files — update them, reset them, or archive them?
6. How does `swarm_state.md` fit into documenting a pivot?
7. Should the user use `--dry-run` first to preview the impact?

Provide a concrete example workflow with commands and folder states at each step.

---

### QUESTION SET 4: Folder Strategy

**Core question**: Should a user use a single source folder, or multiple folders for different purposes?

Address:
- Single folder (`.kiro/onboarding/`) vs. multiple folders
- Remember: HiveForge scans recursively. If the user points to `__DEVELOPMENT/`, the subfolder `KIRO_HiveForge_OriginalDocs/` will also be scanned. Warn about this.
- When does it make sense to use a custom `source_docs_path` vs. the default?
- Should subfolders be used within the source folder? (e.g., `.kiro/onboarding/v1/`, `.kiro/onboarding/v2/`) — note that recursive scanning means ALL subfolders will be included
- What is the recommended folder structure for a project that has gone through multiple pivots?

---

### QUESTION SET 5: File Lifecycle and Hygiene

**Core question**: When should source documents be deleted, archived, or kept?

Address:
- Should source documents be committed to git? (pros/cons)
- When is it safe to delete a source document from the source folder?
- Is it acceptable to rely ONLY on steering files as the "memory" of design decisions, deleting all source docs?
- What is the recommended approach for a project that has been running for 6+ months with multiple pivots?
- Should the user keep a "master" source document that is continuously updated, or create new dated documents for each significant change?
- Remember to address the staging folder cleanup: `.kiro/onboarding/` accumulates files across runs.

---

### QUESTION SET 6: The `__DEVELOPMENT/` Folder — Fit and Contamination Risk

**Core question**: The user currently uses `__DEVELOPMENT/` as a working folder for all kinds of documents. Which of these "fit" the HiveForge approach and which might "contaminate" the process?

Based on your review of the actual `__DEVELOPMENT/` folder contents (including the `KIRO_HiveForge_OriginalDocs/` subfolder):
- Classify each document TYPE (not individual files) as: SAFE TO INCLUDE / RISKY / EXCLUDE
- Explain WHY each classification was made
- Recommend whether the user should use `__DEVELOPMENT/` as a `source_docs_path` or create a separate, curated folder
- If a separate folder is recommended, suggest a naming convention and what to put in it
- Warn that pointing `source_docs_path` at `__DEVELOPMENT/` will recursively include ALL subfolders

---

## OUTPUT FORMAT

The guide should be structured as follows:

```
# Best Practices: Managing Source Documents in HiveForge Workflows

## TL;DR (Quick Reference)
[A concise table or bullet list of the most important rules — max 10 items]

## 1. What Belongs in the Source Folder
[Answer to Question Set 1]

## 2. The Temporal Problem: Keeping Documents Fresh
[Answer to Question Set 2]

## 3. The Pivot Workflow (Step-by-Step)
[Answer to Question Set 3 — this is the most important section, allocate the most space here]

## 4. Folder Strategy
[Answer to Question Set 4]

## 5. File Lifecycle and Hygiene
[Answer to Question Set 5]

## 6. The __DEVELOPMENT/ Folder: What Fits and What Contaminates
[Answer to Question Set 6]

## Appendix: Decision Flowchart
[A mermaid flowchart helping users decide: "Should I include this document in my source folder?"]
```

---

## TONE AND APPROACH

- Be **concrete and opinionated**. The user wants clear guidance, not "it depends" hedging.
- Where genuine trade-offs exist, state them clearly and give a **recommended default**.
- Use the user's actual `__DEVELOPMENT/` folder as examples throughout — this makes the guide immediately actionable.
- Do NOT overstate HiveForge's ability to handle messy input. The whole point of this guide is that the user must curate their input because HiveForge doesn't do it for them.
- The guide should be usable by someone who has just read `WORKFLOW_refactoring_01.md` and is about to run `hiveforge steering init` or `hiveforge steering update` for the first time after a pivot.

---

## CONSTRAINTS

- Do NOT recommend changes to HiveForge's code or architecture. This is a user-facing best practices guide, not a product roadmap.
- Do NOT repeat information already well-covered in `WORKFLOW.md` or `WORKFLOW_refactoring_01.md`. Reference those documents where appropriate, but add new guidance.
- Keep the guide under **2000 words** (excluding the appendix flowchart). Density over length. The pivot scenario (Section 3) may use up to 500 of those words.
- Write in English.
- Do NOT invent HiveForge features or behaviors. If you're unsure whether HiveForge does something, state the uncertainty.

---

## SUCCESS CRITERIA

The guide is successful if a user can answer YES to all of the following after reading it:

1. I know exactly which documents from my `__DEVELOPMENT/` folder to include when running HiveForge.
2. I know what to do with my source documents when I pivot.
3. I know whether to delete or keep old source documents after steering files are generated.
4. I know whether to use `.kiro/onboarding/` or a custom folder for my use case.
5. I understand the temporal risk of stale documents and how to mitigate it.
6. I understand that HiveForge does NOT automatically filter or reconcile contradictory documents.
7. I know I need to clean `.kiro/onboarding/` between runs if I change my source document set.
