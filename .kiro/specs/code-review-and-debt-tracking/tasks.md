# Implementation Plan: Code Review and Technical Debt Tracking

## Overview

Extend HiveForge v3.0.0 to generate a 9th steering file (`technical-debt.md`) by introducing a
`DebtDetector` component for static analysis, a `DebtReconciler` for update-cycle merging, and
wiring both into the existing LLM-primary synthesis pipeline. All implementation is in Python 3.11+
under `hiveforge-power/hiveforge/steering/`.

## Tasks

- [x] 1. Add debt data models to `models.py`
  - Add `DebtCategory`, `DebtPriority`, `DebtStatus`, `DebtEffort`, `DebtRisk` enums
  - Add `DebtRecommendation` dataclass with `title`, `description`, `trade_offs`, `is_recommended` fields
  - Add `DebtItem` dataclass with all required fields: `id`, `category`, `description`, `location`, `priority`, `effort`, `risk`, `status`, `confidence`, `recommendations`, `detected_at`, `resolved_at`
  - Add `DebtMetrics` dataclass with `total_active`, `by_category`, `by_priority`, `last_updated`
  - Add `DebtAnalysisResult` dataclass with `items`, `metrics`, `sampled`, `analysis_time_s`; implement `to_json_dict()`, `active_items()`, `resolved_items()` methods
  - Extend `WorkflowState` with optional `debt_analysis: Optional[DebtAnalysisResult] = None` field
  - Extend `SteeringConfig` with `skip_debt_detection: bool = False` field
  - Add `debt_facts: Optional[DebtAnalysisResult] = None` field to `GenerationContext`
  - _Requirements: 2.7, 2.8, 3.1, 3.2, 3.4, 3.5, 4.1, 5.5_

- [x] 2. Implement `DebtDetector` core and helpers
  - Create `hiveforge-power/hiveforge/steering/detectors/debt_detector.py`
  - Implement `__init__` accepting `project_root`, `conventions_content`, `logger_instance`
  - Implement `_load_gitignore()` using `pathspec` library
  - Implement `_collect_files()` respecting `.gitignore` patterns
  - Implement `_apply_sampling()`: return up to `SAMPLE_SIZE=2000` files when count exceeds `LARGE_CODEBASE_THRESHOLD=10000`
  - Implement `_make_item_id(category, location)` as `sha256[:12]` of `(category.value + location)`
  - Implement `_load_cache()` and `_save_cache()` for `.kiro/.cache/debt_analysis.json`; delete and re-run on corrupt cache
  - Implement `_apply_conventions_preferences()` to escalate priorities based on `conventions_content`
  - _Requirements: 2.5, 2.6, 7.1, 7.2, 7.3, 7.4, 7.5, 12.4, 12.5_

  - [x] 2.1 Write property test for `DebtItem` ID stability (Property 5)
    - **Property 5: DebtItem IDs are stable across re-runs**
    - For any unchanged codebase, two successive calls to `DebtDetector.detect()` must produce matching items with identical `id` values
    - **Validates: Requirements 2.7**

  - [x] 2.2 Write property test for gitignore exclusion (Property 6)
    - **Property 6: DebtDetector produces no items from gitignore-excluded paths**
    - For any codebase with a `.gitignore`, no `DebtItem.location` should reference a gitignore-matched path
    - **Validates: Requirements 2.6**

- [x] 3. Implement `DebtDetector` sub-detectors
  - Implement `_detect_dry_violations(files)`: AST-based normalized function body hashing; flag pairs with Jaccard ≥ 0.85 and ≥ 10 statements; fall back to line-hash comparison for non-Python files (≥ 15 consecutive non-blank lines)
  - Implement `_detect_test_gaps(files)`: compare source files against `test_{module}.py` naming; flag missing test files as HIGH priority; flag untested public functions via AST as MEDIUM (escalate to HIGH when conventions specify testing preference)
  - Implement `_detect_architecture_smells(files)`: build import graph from `import`/`from ... import` statements; run Tarjan's SCC to find cycles; flag `ClassDef` nodes with `(end_lineno - lineno) > 500` as god classes
  - Implement `_detect_performance_risks(files)`: regex pattern matching for N+1 query in loop (HIGH), unbounded `while True` (HIGH), string concat in loop (MEDIUM), list allocation in loop (LOW)
  - Each sub-detector must skip unparseable files with a `WARNING` log and continue
  - Each `DebtItem` must include at least two `DebtRecommendation` entries (recommended + alternative)
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7, 2.8, 8.1, 8.2, 8.3, 8.4, 11.2_

  - [x] 3.1 Write property test for DRY detection monotonicity (Property 12)
    - **Property 12: DRY violation detection is monotone**
    - Adding a verbatim copy of an existing function to a new file must produce at least one additional `DebtItem` with `category == DebtCategory.CODE_QUALITY`
    - **Validates: Requirements 2.1**

  - [x] 3.2 Write property test for test gap detection monotonicity (Property 13)
    - **Property 13: Test gap detection is monotone**
    - Removing the test file for a module with public functions must produce at least one additional `DebtItem` with `category == DebtCategory.TESTS`
    - **Validates: Requirements 2.2**

  - [x] 3.3 Write property test for `DebtItem` field validity (Property 4)
    - **Property 4: DebtItem fields are always valid**
    - For any `DebtItem` produced by `DebtDetector.detect()`, all enum fields must be valid members, `confidence` must be in `[0.0, 1.0]`, and `recommendations` must have ≥ 2 entries
    - **Validates: Requirements 2.7, 2.8, 3.1, 3.2, 3.4, 3.5, 4.1, 8.1**

- [x] 4. Implement `DebtDetector.detect()` orchestration
  - Implement `detect()`: collect files → apply sampling if needed → run all four sub-detectors → apply conventions preferences → compute `DebtMetrics` → save cache → return `DebtAnalysisResult`
  - Load and return cached result when codebase is unchanged (compare file mtimes or hash)
  - Record `analysis_time_s` and set `sampled=True` when sampling was applied
  - _Requirements: 2.5, 2.6, 3.3, 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 4.1 Write property test for cache round-trip (Property 10)
    - **Property 10: Debt analysis cache round-trip**
    - Serializing a `DebtAnalysisResult` to `.kiro/.cache/debt_analysis.json` and deserializing it must produce an equivalent result (same item IDs, categories, priorities)
    - **Validates: Requirements 12.4**

- [x] 5. Checkpoint — Ensure all `DebtDetector` tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement `DebtReconciler`
  - Create `hiveforge-power/hiveforge/steering/detectors/debt_reconciler.py`
  - Implement `_parse_existing_items(content)`: extract `DebtItem` objects from markdown table rows in existing `technical-debt.md` using item `id` as primary key
  - Implement `_is_manually_added(item, detected_ids)`: return `True` when item `id` is absent from the last cached analysis
  - Implement `reconcile(existing_content, new_result)` applying all five reconciliation rules in priority order:
    1. User-edited items: keep existing description/priority when they differ from detected values
    2. Manually added items: preserve with current status unchanged
    3. Auto-resolved items: move to `Resolved` with `resolved_at` timestamp
    4. New items: add with `status=Active` and `detected_at` timestamp
    5. Historical resolved items: preserve verbatim from Resolved section
  - Log warning and treat existing file as empty on parse error; proceed with fresh analysis
  - _Requirements: 4.2, 4.3, 4.4, 4.5, 10.2, 10.3, 11.5_

  - [x] 6.1 Write property test for manual item preservation (Property 7)
    - **Property 7: Manual debt items survive an update cycle**
    - For any `technical-debt.md` with manually added items (IDs absent from fresh analysis), `DebtReconciler.reconcile()` must include all manual items in the returned result
    - **Validates: Requirements 4.4, 4.5**

  - [x] 6.2 Write property test for auto-resolved item handling (Property 8)
    - **Property 8: Auto-resolved items are moved, not deleted**
    - For any previously detected item absent from the new analysis, `reconcile()` must include it in `resolved_items()` with `status == DebtStatus.RESOLVED`
    - **Validates: Requirements 4.3, 10.2**

- [x] 7. Extend `SteeringFileGenerator` for `technical-debt.md`
  - Add `"technical-debt.md"` as the 9th entry in `GENERATION_ORDER` in `steering_file_generator.py`
  - Add schema entry in `_schema_sections()` for `"technical-debt.md"`: `["Overview", "Debt Categories", "Active Debt Items", "Resolved Debt Items", "Debt Metrics"]`
  - Add `debt_facts: Optional[DebtAnalysisResult] = None` parameter to `generate_all_files()`
  - Pass `debt_facts` through to `ContextAssembler.assemble()` when generating `technical-debt.md`
  - Atomic write guarantee must cover all 9 files: any validation failure → zero files written
  - _Requirements: 1.1, 1.3, 5.1, 5.4_

  - [x] 7.1 Write property test for atomic write with 9 files (Property 9)
    - **Property 9: Atomic write guarantee holds for 9 files**
    - If any single file (including `technical-debt.md`) fails validation, `GenerationResult.files_written` must be empty and no files written to disk
    - **Validates: Requirements 5.4**

- [x] 8. Extend `ContextAssembler` and `PromptBuilder` for `technical-debt.md`
  - In `context_assembler.py`: when `template_name == "technical-debt.md"`, include `conventions.md`, `qa-standards.md`, and `architecture.md` from `existing_steering` in the returned `GenerationContext`
  - Pass `debt_facts` from `GenerationContext` through to the assembled context
  - In `prompt_builder.py`: when building prompt for `technical-debt.md`, serialize `debt_facts.to_json_dict()` to JSON and append under a `## Detected Debt Facts` heading in the user prompt
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 8.1 Write property test for cross-reference context assembly (Property 11)
    - **Property 11: Context assembly includes cross-reference steering files**
    - For any call to `ContextAssembler.assemble()` with `template_name="technical-debt.md"` and `existing_steering` containing `conventions.md`, `qa-standards.md`, `architecture.md`, the returned context must include all three
    - **Validates: Requirements 9.1**

- [x] 9. Wire `DebtDetector` into `AutonomousWorkflow`
  - Add `"technical-debt.md"` as the 9th entry in `GENERATION_ORDER` in `autonomous_workflow.py`
  - In `_step_generate_files_autonomously()`: instantiate `DebtDetector` with `project_root` and `conventions_content` from `existing_steering.get("conventions.md")` unless `self.config.skip_debt_detection` is `True`
  - Wrap `detector.detect()` in try/except: on any exception log warning, set `debt_facts=None`, continue
  - Store result in `self.state.debt_analysis`
  - Pass `debt_facts` to `generator.generate_all_files()`
  - For update workflow: read existing `technical-debt.md`, run `DebtDetector`, run `DebtReconciler.reconcile()`, pass merged result as `debt_facts`
  - _Requirements: 1.1, 2.5, 5.1, 5.2, 5.5, 11.1_

  - [x] 9.1 Write property test for `technical-debt.md` always in `files_written` (Property 1)
    - **Property 1: technical-debt.md is always generated during init**
    - For any valid project root and `SteeringConfig` (with or without `skip_debt_detection`), the init workflow must produce a `files_written` list that includes `technical-debt.md`
    - **Validates: Requirements 1.1, 5.1**

- [x] 10. Checkpoint — Ensure all pipeline integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Add `--skip-debt-detection` CLI flag and MCP `debt_summary` metadata
  - In `hiveforge-power/hiveforge/steering/cli.py`: add `--skip-debt-detection` Typer option that sets `SteeringConfig.skip_debt_detection = True`
  - In MCP tool wrappers for `init_steering` and `update_steering`: include `debt_summary` field in response metadata containing `DebtAnalysisResult.metrics` when `debt_analysis` is present on `WorkflowState`
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 12. Write unit tests for `DebtDetector` and `DebtReconciler`
  - Create `hiveforge-power/tests/test_debt_detector.py`
    - Test each sub-detector with a synthetic in-memory codebase containing one known violation per type
    - Test `_make_item_id()` produces identical output for identical inputs
    - Test empty codebase produces `DebtAnalysisResult` with zero items and no exceptions
    - Test unparseable `.py` file is skipped without raising
    - Test `to_json_dict()` output fits within 1000 tokens
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 11.2, 11.4_
  - Create `hiveforge-power/tests/test_debt_reconciler.py`
    - Test hand-crafted `technical-debt.md` with manual items: all preserved after reconcile
    - Test previously auto-detected item absent from new result: moved to Resolved
    - Test user-edited description in existing file: kept over freshly detected value
    - Test parse error on existing file: treated as empty, fresh analysis used
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 11.5_

- [x] 13. Write integration tests for `technical-debt.md` generation
  - Create `hiveforge-power/tests/test_technical_debt_generation.py`
  - Test full init pipeline with mocked `LLMProvider`: assert `technical-debt.md` in `files_written`, assert all 5 required sections present, assert valid YAML frontmatter
  - Test `--skip-debt-detection`: assert `technical-debt.md` still generated with placeholder content
  - Test `DebtDetector` exception during init: assert workflow continues and `technical-debt.md` generated with placeholder content
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 5.1, 11.1_

  - [x] 13.1 Write property test for required sections (Property 2)
    - **Property 2: technical-debt.md always contains required sections**
    - For any generated `technical-debt.md` content, the file must contain all five sections: Overview, Debt Categories, Active Debt Items, Resolved Debt Items, Debt Metrics
    - **Validates: Requirements 1.3, 10.1**

  - [x] 13.2 Write property test for valid YAML frontmatter (Property 3)
    - **Property 3: technical-debt.md always contains valid YAML frontmatter**
    - For any generated `technical-debt.md`, parsing its YAML frontmatter must yield `inclusion == "always"` and `priority == 3`
    - **Validates: Requirements 1.2**

- [x] 14. Final checkpoint — Ensure all tests pass
  - Run all tests: `python -m pytest tests/ -q --tb=short --no-header` from `hiveforge-power/` directory
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests use `hypothesis` library; each test runs a minimum of 100 iterations
- Tag format for property tests: `# Feature: code-review-and-debt-tracking, Property {N}: {property_text}`
- `DebtDetector` lives in `steering/detectors/` alongside the existing `drift_detector.py`
- `technical-debt.md` is generated last (position 9) so it can reference all other steering files
- The atomic write guarantee covers all 9 files — no partial writes
- `DebtReconciler` is only invoked during the update workflow, not init
