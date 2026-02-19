# Requirements: Source Documents Path & Hallucination Guardrails

**Spec ID:** `source-docs-and-guardrails`  
**Created:** 2026-02-19  
**Updated:** 2026-02-19 (Red Team Review)  
**Status:** Approved with Modifications  
**Priority:** Critical  
**Version:** 2.2.1

---

## Problem Statement

Based on Red Team Report (2026-02-19), HiveForge has critical UX failures:

1. **No source document path parameter** - Users cannot specify where their design documents are located
2. **Hardcoded staging folder** - `.kiro/onboarding/` is hardcoded but never communicated to Power users
3. **Silent hallucination** - When documents are missing, LLM invents plausible content with no warnings
4. **Wrong workflow documented** - WORKFLOW.md points users to KIRO agent instead of HiveForge Power

These issues cause the majority of user failures in real-world usage.

---

## Goals

### Primary Goals
1. Allow users to specify custom source document locations
2. Provide clear feedback when source documents are missing
3. Add hallucination guardrails to autonomous mode
4. Fix documentation to show correct Power invocation

### Secondary Goals
5. Improve `discover_docs` to target specific subfolders
6. Add confidence scoring to generated steering files
7. Provide dry-run mode for preview before execution

### Non-Goals
- Changing the shared backend architecture (v2.1.0 is solid)
- Rewriting the entire workflow system
- Removing `.kiro/onboarding/` (keep for backward compatibility)

---

## Success Metrics

- **User Success Rate:** 90%+ of users successfully generate steering files on first attempt
- **Hallucination Detection:** 100% of empty-source-folder cases show clear warnings
- **Documentation Accuracy:** Zero workflow steps that reference non-existent features
- **Confidence Visibility:** 100% of generated files include confidence metadata

---

## Requirements

### R1: Source Document Path Parameter (Critical - C1, C2)

**R1.1** Add `source_docs_path: Optional[str] = None` parameter to `init_steering` MCP tool

**R1.2** Add `source_docs_path: Optional[str] = None` parameter to `discover_docs` MCP tool

**R1.3** When `source_docs_path` is provided:
- Restrict document discovery to that path (relative to `project_root`)
- Still create staging folder at `.kiro/onboarding/` for backward compatibility
- Copy/symlink discovered documents to staging folder for workflow processing

**R1.4** When `source_docs_path` is NOT provided:
- Use default behavior: scan `.kiro/onboarding/` first
- If `.kiro/onboarding/` is empty, scan `project_root` (current behavior)

**R1.5** Update `SharedInitWorkflow` to accept and use `source_docs_path`

**R1.6** Update `SharedDiscoveryWorkflow` to accept and use `source_docs_path`

**Acceptance Criteria:**
- User can call `init_steering(project_root=".", source_docs_path="_DEVELOPMENT")`
- Tool discovers documents in `_DEVELOPMENT/` folder
- Tool returns list of discovered documents in result metadata
- Backward compatibility: existing calls without `source_docs_path` work unchanged

---

### R2: Empty Source Folder Warning (Critical - C2, C3)

**R2.1** When `init_steering` runs and discovers ZERO documents in staging folder:
- Add warning to result: `"No source documents found. Steering files will be generated from code analysis only. Consider adding design documents to improve accuracy."`
- Set `source_documents_found: 0` in result metadata
- Set `confidence_level: "low"` in result metadata

**R2.2** When `init_steering` runs in `autonomous=True` mode with zero documents:
- Add additional warning: `"Autonomous mode with no source documents may produce inferred content. Review generated files carefully."`

**R2.3** When `discover_docs` finds zero documents:
- Return status `"success"` but with warning
- Include suggestion: `"Try specifying source_docs_path parameter to target a specific folder"`

**Acceptance Criteria:**
- Empty staging folder produces visible warning in result
- Warning includes actionable suggestion
- Result metadata includes document count and confidence level

---

### R3: Hallucination Guardrails (Critical - C3)

**R3.1** Add `[INFERRED]` tags to steering file sections generated without source document grounding

**R3.2** When `SteeringAssistant` fills gaps in autonomous mode:
- Track which sections came from source documents vs. LLM inference
- Mark inferred sections with `<!-- INFERRED: Please verify this section -->`
- Add confidence score to each section

**R3.3** Add confidence metadata header to each generated steering file:
```markdown
---
generated_by: hiveforge v2.2.0
source_documents: 3
code_analysis: true
confidence: medium
inferred_sections: ["Problem Statement", "Target Users"]
---
```

**R3.4** When overall confidence is "low" (< 30% content from source docs):
- Add prominent warning at top of file:
```markdown
> ⚠️ **LOW CONFIDENCE**: This file was generated with limited source material.
> Most content is inferred. Please review and update with actual project information.
```

**Acceptance Criteria:**
- All inferred sections are clearly marked
- Confidence metadata is present in every generated file
- Low-confidence files have visible warnings
- Users can easily identify which content to verify

---

### R4: Fix Documentation (Critical - C4)

**R4.1** Update `WORKFLOW_refactoring_01.md` Step 2.2:
- Remove reference to "Steering Assistant agent"
- Replace with correct Power invocation: `"In KIRO chat, type: Initialize steering files for my project"`
- Explain that this triggers the `init_steering` MCP tool
- Add note: "The Steering Assistant agent is a fallback for manual document transformation"

**R4.2** Update `WORKFLOW.md` Workflow 2:
- Add section on using HiveForge Power from KIRO
- Show correct MCP tool invocation
- Explain `source_docs_path` parameter usage

**R4.3** Update `hiveforge-power/POWER.md`:
- Add prominent section on source document location
- Explain `.kiro/onboarding/` default behavior
- Show `source_docs_path` parameter usage examples
- Add troubleshooting section for "no documents found" scenario

**R4.4** Update `docs/steering-assistant-guide.md`:
- Add "Using from KIRO IDE" section
- Show Power invocation examples
- Explain difference between Power and Steering Assistant agent

**Acceptance Criteria:**
- All workflow documents show correct Power invocation
- `.kiro/onboarding/` requirement is explained upfront
- `source_docs_path` parameter is documented with examples
- No references to non-existent automated features

---

### R5: Improve discover_docs Targeting (Important - I2)

**R5.1** When `source_docs_path` is provided to `discover_docs`:
- Prioritize files in that path
- Use full `max_discovery_files` budget for that path first
- Only scan other paths if budget remains

**R5.2** Add file type filtering to `discover_docs`:
- Add `file_types: Optional[List[str]] = None` parameter
- When provided, only discover files matching those extensions
- Example: `file_types=[".md", ".pdf"]` skips source code files

**R5.3** Return discovery statistics in result:
```python
{
    "files_discovered": 42,
    "files_by_type": {".md": 15, ".pdf": 3, ".py": 24},
    "files_by_path": {"_DEVELOPMENT": 18, "docs": 10, "src": 14},
    "files_included": 18,  # After filtering
    "files_excluded": 24   # Didn't match criteria
}
```

**Acceptance Criteria:**
- `source_docs_path` prioritizes target folder
- File type filtering works correctly
- Discovery statistics are returned in result

---

### R6: Confidence Scoring System (Important)

**R6.1** Define confidence levels:
- **High (80-100%):** 80%+ content from source documents, code analysis confirms
- **Medium (50-79%):** 50-79% from source documents, some inference
- **Low (< 50%):** Majority inferred, minimal source material

**R6.2** Calculate per-file confidence:
- Track source of each template section (document, code, inferred)
- Weight by section importance (vision > conventions)
- Return confidence score in result metadata

**R6.3** Calculate overall workflow confidence:
- Average of all file confidences
- Include in workflow result
- Warn if overall confidence < 60%

**Acceptance Criteria:**
- Each file has calculated confidence score
- Confidence calculation is transparent and documented
- Low confidence triggers warnings

---

### R7: Dry-Run Mode (Nice to Have - N5)

**R7.1** Add `dry_run: bool = False` parameter to `init_steering`

**R7.2** In dry-run mode:
- Perform all analysis (code, documents, gap analysis)
- Generate steering file content in memory
- Return preview in result without writing files
- Include file list, confidence scores, warnings

**R7.3** Return dry-run result structure:
```python
{
    "status": "dry_run_complete",
    "files_to_create": ["project-vision.md", "tech-stack.md", ...],
    "files_to_overwrite": ["conventions.md"],
    "source_documents_found": 5,
    "confidence_level": "medium",
    "warnings": ["No documents found for db-standards.md"],
    "preview": {
        "project-vision.md": "# Project Vision\n...",
        # ... truncated previews
    }
}
```

**Acceptance Criteria:**
- Dry-run performs full analysis without writing files
- Result includes preview of what would be created
- User can review before committing

---

## Technical Design

### Architecture Changes

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Tool Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  init_steering(                                                  │
│    project_root: str = ".",                                      │
│    source_docs_path: Optional[str] = None,  ← NEW               │
│    auto_discover: bool = True,                                   │
│    autonomous: bool = True,                                      │
│    confidence_threshold: float = 0.7,                            │
│    dry_run: bool = False  ← NEW                                  │
│  )                                                               │
│                                                                  │
│  discover_docs(                                                  │
│    project_root: str = ".",                                      │
│    source_docs_path: Optional[str] = None,  ← NEW               │
│    file_types: Optional[List[str]] = None,  ← NEW               │
│    include_git_history: bool = False,                            │
│    max_discovery_files: int = 1000,                              │
│    max_file_size_mb: int = 10                                    │
│  )                                                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Shared Backend Adapters                        │
├─────────────────────────────────────────────────────────────────┤
│  SharedInitWorkflow(                                             │
│    project_root: Path,                                           │
│    source_docs_path: Optional[Path] = None,  ← NEW              │
│    auto_discover: bool = True,                                   │
│    autonomous: bool = True,                                      │
│    confidence_threshold: float = 0.7,                            │
│    dry_run: bool = False  ← NEW                                  │
│  )                                                               │
│                                                                  │
│  SharedDiscoveryWorkflow(                                        │
│    project_root: Path,                                           │
│    source_docs_path: Optional[Path] = None,  ← NEW              │
│    file_types: Optional[List[str]] = None,  ← NEW               │
│    include_git_history: bool = False,                            │
│    max_discovery_files: int = 1000,                              │
│    max_file_size_mb: int = 10                                    │
│  )                                                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Core Workflows                              │
├─────────────────────────────────────────────────────────────────┤
│  InitWorkflow:                                                   │
│    - Accept source_docs_path parameter                           │
│    - Discover documents from custom path                         │
│    - Calculate confidence scores                                 │
│    - Add [INFERRED] tags to generated content                    │
│    - Return enhanced result with metadata                        │
│                                                                  │
│  DiscoveryWorkflow:                                              │
│    - Prioritize source_docs_path if provided                     │
│    - Filter by file_types if provided                            │
│    - Return discovery statistics                                 │
└─────────────────────────────────────────────────────────────────┘
```

### New Components

**1. ConfidenceCalculator** (`src/hiveforge/steering/confidence.py`)
- Calculates per-section confidence based on source
- Aggregates to per-file and overall confidence
- Returns confidence metadata

**2. ContentTagger** (`src/hiveforge/steering/content_tagger.py`)
- Tags inferred sections with `[INFERRED]` markers
- Adds confidence metadata headers to files
- Inserts warnings for low-confidence files

**3. SourceDocumentResolver** (`src/hiveforge/steering/source_resolver.py`)
- Resolves `source_docs_path` relative to `project_root`
- Validates path exists and is readable
- Discovers documents in custom path
- Copies/symlinks to staging folder for workflow

---

## Implementation Plan

### Phase 1: Core Parameter Support (Week 1)
- [ ] Add `source_docs_path` parameter to MCP tools
- [ ] Add `source_docs_path` to shared adapters
- [ ] Implement `SourceDocumentResolver`
- [ ] Update `InitWorkflow` to use custom source path
- [ ] Update `DiscoveryWorkflow` to use custom source path
- [ ] Write unit tests for new parameters

### Phase 2: Confidence & Guardrails (Week 1-2)
- [ ] Implement `ConfidenceCalculator`
- [ ] Implement `ContentTagger`
- [ ] Add confidence tracking to `SteeringAssistant`
- [ ] Add `[INFERRED]` tags to generated content
- [ ] Add metadata headers to steering files
- [ ] Add empty-source-folder warnings
- [ ] Write unit tests for confidence system

### Phase 3: Enhanced Discovery (Week 2)
- [ ] Add `file_types` parameter to `discover_docs`
- [ ] Implement file type filtering
- [ ] Add discovery statistics to results
- [ ] Prioritize `source_docs_path` in discovery
- [ ] Write unit tests for discovery enhancements

### Phase 4: Dry-Run Mode (Week 2)
- [ ] Add `dry_run` parameter to `init_steering`
- [ ] Implement dry-run execution path
- [ ] Return preview results without writing files
- [ ] Write unit tests for dry-run mode

### Phase 5: Documentation Updates (Week 3)
- [ ] Update `WORKFLOW_refactoring_01.md`
- [ ] Update `WORKFLOW.md`
- [ ] Update `hiveforge-power/POWER.md`
- [ ] Update `docs/steering-assistant-guide.md`
- [ ] Add troubleshooting guide for common issues
- [ ] Update tool docstrings with examples

### Phase 6: Integration Testing (Week 3)
- [ ] Test full workflow with custom source path
- [ ] Test empty source folder warnings
- [ ] Test confidence scoring accuracy
- [ ] Test dry-run mode
- [ ] Test backward compatibility (no source_docs_path)
- [ ] Update integration tests

### Phase 7: Release (Week 4)
- [ ] Version bump to 2.2.0
- [ ] Update CHANGELOG.md
- [ ] Create migration guide for users
- [ ] Release to PyPI (when ready)

---

## Testing Strategy

### Unit Tests
- `test_source_document_resolver.py` - Path resolution, validation
- `test_confidence_calculator.py` - Confidence scoring logic
- `test_content_tagger.py` - Tag insertion, metadata headers
- `test_init_workflow_source_path.py` - Custom source path handling
- `test_discover_docs_enhancements.py` - File type filtering, statistics

### Integration Tests
- `test_init_with_custom_source.py` - End-to-end with custom path
- `test_empty_source_warnings.py` - Warning generation
- `test_confidence_metadata.py` - Metadata in generated files
- `test_dry_run_mode.py` - Dry-run execution
- `test_backward_compatibility.py` - Existing workflows unchanged

### Manual Testing Scenarios
1. User with docs in `_DEVELOPMENT/` folder
2. User with empty `.kiro/onboarding/` folder
3. User running dry-run before commit
4. User checking confidence scores in generated files
5. User following updated WORKFLOW.md instructions

---

## Risks & Mitigations

### Risk 1: Breaking Changes
**Mitigation:** All new parameters are optional with sensible defaults. Existing code works unchanged.

### Risk 2: Performance Impact
**Mitigation:** Confidence calculation is lightweight. Dry-run mode is opt-in.

### Risk 3: User Confusion with Two Paths
**Mitigation:** Clear documentation explaining when to use `source_docs_path` vs. default `.kiro/onboarding/`.

### Risk 4: Confidence Scoring Accuracy
**Mitigation:** Start with simple heuristics, iterate based on user feedback.

---

## Open Questions & Decisions

### Q1: Should `source_docs_path` support multiple paths (list)?
**Decision:** Not in v2.2.0. Single path is simpler and sufficient. Can add in v2.3.0 if user demand exists.

### Q2: Should we deprecate `.kiro/onboarding/` in favor of explicit parameter?
**Decision:** No. Keep for backward compatibility. Add deprecation warning in v2.3.0, remove in v3.0.0.

### Q3: What confidence threshold should trigger warnings?
**Decision:** < 0.5 (50%) triggers warnings. The `confidence_threshold` parameter controls autonomous mode decisions, not warning generation.

### Q4: Should dry-run mode be available in CLI as well as Power?
**Decision:** Yes. Add `--dry-run` flag to CLI in same release (Phase 4.3).

---

## Red Team Review Modifications

### Required Changes Implemented (v2.2.1)

1. **Security Test Cases Added** - Comprehensive path traversal, symlink, and encoding attack tests
2. **Confidence Weights Justified** - Rationale documented in design.md
3. **Rollback Testing Added** - New component failure scenarios covered
4. **Migration Guide Added** - Clear path for existing users documented

### Recommended Changes

5. **Performance Tests Added** - Benchmarks for all new components
6. **confidence_threshold Clarified** - Usage documented (autonomous mode only)
7. **Telemetry Added** - Tracking for new parameter usage and confidence levels
8. **Symlink Optimization** - Use symlinks by default, add `copy_files` parameter

### Deferred to Future Versions

- Multiple source paths support → v2.3.0
- Configurable confidence weights → v2.3.0
- `.kiro/onboarding/` deprecation → v3.0.0

---

## Dependencies

- Existing shared backend architecture (v2.1.0)
- MCP tool infrastructure
- Steering file templates
- Gap analysis engine

---

## Success Criteria

- [ ] Users can specify custom source document paths
- [ ] Empty source folder produces clear warnings
- [ ] Generated files include confidence metadata
- [ ] Inferred content is clearly marked
- [ ] Documentation shows correct Power invocation
- [ ] All tests pass
- [ ] Backward compatibility maintained
- [ ] User success rate improves to 90%+
