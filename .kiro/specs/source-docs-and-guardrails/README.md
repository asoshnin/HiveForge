# Spec: Source Documents Path & Hallucination Guardrails

**Version:** 2.2.0  
**Status:** Ready for Implementation  
**Created:** 2026-02-19

---

## Quick Summary

This spec addresses the critical UX failures identified in the Red Team Report (2026-02-19). It adds the ability for users to specify custom source document locations, provides clear warnings when documents are missing, and implements hallucination guardrails to prevent silent generation of fabricated content.

---

## Problem

Users cannot specify where their design documents are located, leading to:
- Silent failures when documents are in folders other than `.kiro/onboarding/`
- LLM hallucinating plausible-sounding content when source material is missing
- No visibility into which content was inferred vs. extracted from documents
- Documentation showing workflows that don't match actual tool behavior

---

## Solution

### 1. Custom Source Document Paths
Add `source_docs_path` parameter to `init_steering` and `discover_docs` tools, allowing users to specify any folder containing their design documents.

### 2. Empty Source Warnings
When no documents are found, return clear warnings explaining the situation and suggesting actions.

### 3. Confidence Scoring
Calculate and display confidence scores for all generated content, showing what percentage came from documents vs. code analysis vs. LLM inference.

### 4. Content Tagging
Tag all inferred sections with `[INFERRED]` markers and add confidence metadata headers to generated files.

### 5. Documentation Fixes
Update all workflow documentation to show correct Power invocation and explain the `.kiro/onboarding/` requirement.

---

## Key Features

- **Custom source paths:** `init_steering(source_docs_path="_DEVELOPMENT")`
- **File type filtering:** `discover_docs(file_types=[".md", ".pdf"])`
- **Confidence metadata:** Every file includes confidence score and source breakdown
- **Inferred content tags:** `<!-- INFERRED: Please verify this section -->`
- **Low confidence warnings:** Prominent warnings on files with < 50% confidence
- **Dry-run mode:** Preview what would be created without writing files
- **Backward compatible:** All existing code works unchanged

---

## Files

- **requirements.md** - Detailed requirements with acceptance criteria
- **design.md** - Architecture, data models, algorithms, API design
- **tasks.md** - Implementation tasks organized by phase
- **README.md** - This file

---

## Implementation Phases

1. **Phase 1:** Core parameter support (2-3 days)
2. **Phase 2:** Confidence & guardrails (2-3 days)
3. **Phase 3:** Enhanced discovery (1 day)
4. **Phase 4:** Dry-run mode (1 day)
5. **Phase 5:** Documentation updates (1-2 days)
6. **Phase 6:** Integration testing (1-2 days)
7. **Phase 7:** Release preparation (1 day)

**Total:** 9-13 days (2-3 weeks)

---

## Success Metrics

- 90%+ user success rate on first attempt
- Zero silent failures (all issues produce warnings)
- 100% of generated files include confidence metadata
- Backward compatibility maintained
- Documentation accurate and complete

---

## Priority Fixes from Red Team Report

| Issue | Priority | Status |
|-------|----------|--------|
| C1: No source_docs_path parameter | Critical | ✅ Addressed |
| C2: Hardcoded .kiro/onboarding/ | Critical | ✅ Addressed |
| C3: No hallucination guardrails | Critical | ✅ Addressed |
| C4: Wrong workflow documented | Critical | ✅ Addressed |
| I2: discover_docs can't target subfolder | Important | ✅ Addressed |
| I5: autonomous=True behavior unclear | Important | ✅ Addressed |
| N5: No dry-run mode | Nice to Have | ✅ Addressed |

---

## Getting Started

1. Read `requirements.md` for detailed requirements
2. Review `design.md` for architecture and algorithms
3. Open `tasks.md` to begin implementation
4. Follow phases sequentially for best results

---

## Questions?

Refer to the "Open Questions & Decisions" section in `design.md` for resolved design decisions.

---

## Related Documents

- `__DEVELOPMENT/2026-02-19_RED_TEAM_report.md` - Original red team findings
- `WORKFLOW_refactoring_01.md` - Workflow guide to be updated
- `hiveforge-power/POWER.md` - Power documentation to be updated
- `docs/steering-assistant-guide.md` - User guide to be updated
