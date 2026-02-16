# RED TEAM Revisions: Steering Assistant v02

**Date:** 2026-02-16  
**Status:** APPROVED FOR IMPLEMENTATION  
**Version:** v02.0 MVP

## Critical Issues Addressed

### 1. Single LLM Call → Sequential Generation ✅
**Issue:** Generating all 8 files in a single LLM call would hit token limits and fail.

**Fix:**
- Changed to sequential generation: generate files one at a time
- Pass previously generated files as context to maintain consistency
- Allows partial failure handling (if one file fails, continue with others)
- Updated Requirement 3.1, Property 3, Data Flow section

### 2. Unrealistic Confidence Thresholds → Conservative Thresholds ✅
**Issue:** No justification for HIGH ≥0.8, MEDIUM 0.6-0.8, LOW <0.6 thresholds.

**Fix:**
- Changed to conservative thresholds: HIGH ≥0.9, MEDIUM ≥0.7, LOW <0.7
- Added calibration support to adjust thresholds based on telemetry data
- Added `--calibration-mode` flag for collecting adjustment data
- Updated Requirement 4.1, 4.8, Property 4, Property 18

### 3. Vague Semantic Validation → Rule-Based Validation ✅
**Issue:** No concrete algorithms for detecting "React is frontend, not backend" or "microservices vs monolithic" contradictions.

**Fix:**
- Created `validation_rules.yaml` specification with concrete rules
- Added framework classification database (frontend/backend/database)
- Defined specific validation checks with conditions and error messages
- Added validation rule execution algorithm
- Updated Requirement 5 (10 acceptance criteria), Property 5, Design document

### 4. Missing Integration with v01 → Explicit Integration Points ✅
**Issue:** No specification of how v02 integrates with existing 40+ v01 modules.

**Fix:**
- Added Requirement 16.8-16.11 for integration
- Specified that AutonomousWorkflow extends InitWorkflow
- Listed reused components: KnowledgeBase, GapAnalysisEngine, TemplatePopulator, ConflictResolver, CustomizationDetector
- Added `workflow_type` parameter to existing classes
- Updated Component Responsibilities with integration notes
- Updated Property 16

### 5. Database Schema → File-Based Telemetry ✅
**Issue:** SQL database schema with no migration strategy or integration plan.

**Fix:**
- Changed to file-based telemetry in `.kiro/.telemetry/` directory
- Defined JSON file structure for sessions, calibration, and summary
- Deferred database export to v02.1 as optional feature
- Updated Requirement 14, Property 14, Design document

### 6. Round-Trip Consistency → Deferred to v02.1 ✅
**Issue:** Semantic equivalence is untestable with non-deterministic LLMs.

**Fix:**
- Deferred Requirement 21 to v02.1
- Changed from "semantic equivalence" to "structural consistency"
- Focus v02.0 on single-pass generation quality
- Updated Property 21 with deferral note

### 7. Incremental Updates Conflict → Per-File Updates ✅
**Issue:** Incremental updates (per-section) conflict with batch generation.

**Fix:**
- Changed incremental updates to per-file (not per-section)
- Clarified that incremental mode works with sequential generation
- Added caching in `.kiro/.cache/steering_cache.json`
- Updated Requirement 23, Property 23

### 8. Arbitrary Performance Limits → Configurable Limits ✅
**Issue:** Hard limits (1000 files, 10MB, 30 seconds) with no justification.

**Fix:**
- Made limits configurable with flags (`--max-discovery-files`, `--max-file-size`)
- Added warnings when limits are hit
- Added logging of skipped files with reasons
- Updated Requirement 24, Property 24

### 9. Semantic Equivalence Validation → Deferred to v02.1 ✅
**Issue:** Requires advanced NLP techniques not available in v02.0.

**Fix:**
- Deferred Requirement 27 to v02.1
- Changed from "semantic equivalence" to "structural similarity"
- Focus v02.0 on structural validation
- Updated Property 27 with deferral note

## Version Scope Clarification

### v02.0 MVP (Current Spec)
- Feature flag system
- Expanded discovery phase
- Sequential autonomous generation
- Conservative confidence scoring
- Rule-based semantic validation
- Conflict detection and resolution
- Customization preservation
- Fallback workflow
- Rollback mechanism
- Performance monitoring
- Token budget management
- File-based telemetry
- Backward compatibility
- Partial failure handling
- Batch conflict resolution
- Preview mode

### v02.1 Advanced Features (Deferred)
- Round-trip generation consistency (structural)
- Confidence score calibration with feedback loop
- Incremental updates (per-section)
- Advanced discovery scalability (100k+ files)
- Intelligent inference transparency
- Semantic equivalence validation (NLP-based)
- Database export for telemetry
- Multi-project confidence calibration

## Implementation Risk Assessment

### Low Risk ✅
- Feature flag system (simple routing)
- Expanded discovery (extends existing parser)
- Sequential generation (proven pattern)
- File-based telemetry (no external dependencies)
- Backward compatibility (extends existing classes)

### Medium Risk ⚠️
- Rule-based semantic validation (requires validation_rules.yaml design)
- Confidence scoring (requires calibration data collection)
- Partial failure handling (requires careful error handling)

### High Risk (Deferred to v02.1) 🔴
- Round-trip consistency (non-deterministic LLMs)
- Semantic equivalence (requires NLP)
- Confidence calibration (requires feedback loop)

## Next Steps

1. ✅ Requirements updated with v02.0/v02.1 split
2. ✅ Design updated with integration points and validation rules
3. ⏳ Tasks.md needs update to reflect sequential generation and integration
4. ⏳ Create validation_rules.yaml specification file
5. ⏳ Update existing v01 classes to support workflow_type parameter
6. ⏳ Begin Phase 1 implementation (Foundation)

## Sign-Off

**RED TEAM VERDICT:** ✅ APPROVED FOR IMPLEMENTATION

The revised spec addresses all critical issues and provides a realistic, implementable path forward. The v02.0 MVP scope is achievable within reasonable timeframes, and the v02.1 deferral removes high-risk features that require research.

**Confidence Level:** HIGH (0.9)  
**Risk Level:** MEDIUM (manageable with proper testing)  
**Estimated Implementation Time:** 4-6 weeks for v02.0 MVP
