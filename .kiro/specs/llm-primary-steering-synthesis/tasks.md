# Implementation Plan: LLM-Primary Steering Synthesis

## Overview

Refactor the steering file generation pipeline from a regex-based `TemplatePopulator` fallback to an
LLM-primary synthesis engine. Five new components are introduced (`InputResolver`, `ContextAssembler`,
`PromptBuilder`, `SteeringFileGenerator`, `DeltaAnalyzer`) and the `AutonomousWorkflow` is rewired to
use the new pipeline. All implementation is in Python 3.11+ under `hiveforge-power/hiveforge/steering/`.

## Tasks

- [ ] 1. Add new data models to `models.py`
  - Add `NamingConventions` dataclass with `variables`, `classes`, `constants`, `functions` fields
  - Add `CodeAnalysisFacts` dataclass with all required fields and `to_json_dict()` method
  - Add `GenerationContext` dataclass
  - Add `DeltaReport` dataclass with `doc_vs_code`, `steering_vs_code`, `steering_vs_docs`, `missing_in_all`
  - Add `GenerationResult` dataclass with `success`, `files_written`, `validation_errors`
  - Add `LLMUnavailableError` exception class
  - Add `UseCase` `Literal` type alias
  - _Requirements: 1.1, 2.1, 2.2, 4.6, 5.5, 7.2, 8.2_

- [ ] 2. Extend `CodeAnalyzer` with structured output and progress logging
  - [ ] 2.1 Add `to_facts()` method to `CodeAnalyzer` that returns `CodeAnalysisFacts`
    - Map existing AST/regex analysis results to the new dataclass fields
    - Preserve `to_summary()` as deprecated but functional for backward compatibility
    - Ensure `to_json_dict()` serializes to ≤2,000 tokens
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

  - [ ]* 2.2 Write property test for `CodeAnalysisFacts` token budget
    - **Property 5 (partial): Token budget never exceeded**
    - For any codebase, `CodeAnalysisFacts.to_json_dict()` serialized to JSON string must be ≤2,000 tokens
    - **Validates: Requirements 2.5**

  - [ ] 2.3 Add `_log_progress()` method and integrate into directory traversal in `CodeAnalyzer`
    - Emit `Scanning directory X of Y` messages to CLI output during deep traversal
    - _Requirements: 2.4_

- [ ] 3. Enforce bounded scope in `DocumentParser`
  - [ ] 3.1 Add `source_folder` constructor parameter to `DocumentParser`
    - Store resolved absolute path as `self._source_folder`
    - Raise `SourceFolderError` if a requested path resolves outside `_source_folder`
    - Update `parse_all()` to read exclusively from `_source_folder`
    - _Requirements: 3.1, 3.2_

  - [ ]* 3.2 Write property test for source folder boundary enforcement
    - **Property 9: Source folder boundary enforcement**
    - For any path outside `source_folder`, `DocumentParser` must raise `SourceFolderError`
    - **Validates: Requirements 3.1, 3.2**

- [ ] 4. Implement `InputResolver`
  - Create `hiveforge-power/hiveforge/steering/input_resolver.py`
  - Implement `resolve(source_folder, project_root, steering_dir)` returning `(UseCase, Path | None)`
  - Apply use case determination table from design: `new_from_docs`, `reverse_engineer`, `drift_correction`, `error_recovery`, `pivot`, `update`
  - Handle empty/absent source folder → `source_docs = []` in context
  - Detect intent document in source folder → set `user_intent` in context
  - _Requirements: 3.3, 3.4, 3.5, 9.5_

  - [ ]* 4.1 Write property test for use case determination
    - **Property 10: Use case determination correctness**
    - For all combinations of (source_docs_present, codebase_present, steering_present), `InputResolver.resolve()` must return the correct `UseCase`
    - **Validates: Requirements 3.5_

- [ ] 5. Implement `ContextAssembler`
  - Create `hiveforge-power/hiveforge/steering/context_assembler.py`
  - Implement `assemble()` with token budget constants: `TOKEN_BUDGET=8000`, `BUDGET_SOURCE_DOCS=4000`, `BUDGET_CODE_FACTS=2000`, `BUDGET_EXISTING_STEERING=1000`, `BUDGET_PREV_GENERATED=1000`
  - Implement keyword-based relevance filtering of source docs per template schema
  - Implement rolling summary extraction for previously generated files
  - Implement truncation priority: `previously_generated` → `existing_steering` → `code_facts`
  - Return `GenerationContext` struct per template
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 5.1 Write property test for token budget enforcement
    - **Property 5: Token budget never exceeded per template**
    - For any combination of inputs, `ContextAssembler.assemble()` must return a `GenerationContext` whose total token count is ≤8,000
    - **Validates: Requirements 4.1, 4.2**

- [ ] 6. Implement `PromptBuilder`
  - Create `hiveforge-power/hiveforge/steering/prompt_builder.py`
  - Implement `build(template_name, template_content, context)` returning `(system_prompt, user_prompt)`
  - System prompt must include all five instruction strings: fill every section independently, write `N/A` for absent info, write `[NOT FOUND]` for expected-but-absent fields, no content repeated across sections, output only final Markdown with no preamble
  - User prompt must include: template section schema, source doc content, code facts JSON, existing steering content, `DeltaReport` (when `use_case` is `drift_correction` or `update`), `user_intent` (when present), previously generated summaries
  - Implement `build_simplified()` for retry on empty/malformed response
  - _Requirements: 1.4, 1.5, 7.3, 7.5, 10.1, 10.2, 10.3, 10.4_

  - [ ]* 6.1 Write property test for required context fields in prompt
    - **Property 3: Prompt contains all required context fields**
    - For any `GenerationContext` with all fields populated, `PromptBuilder.build()` output must contain each field's content
    - **Validates: Requirements 1.4**

  - [ ]* 6.2 Write property test for required instruction strings in prompt
    - **Property 4: Prompt contains all required instruction strings**
    - For any template and context, the system prompt must contain all five required instruction strings
    - **Validates: Requirements 1.5, 10.1, 10.2, 10.3, 10.4**

- [ ] 7. Implement `SteeringFileGenerator` (core transactional logic)
  - Create `hiveforge-power/hiveforge/steering/steering_file_generator.py`
  - Implement `__init__` that raises `LLMUnavailableError` if `llm_provider.is_available()` is `False`
  - Implement `generate_all_files()`: generate all 8 files in memory in fixed sequential order, validate each draft, atomic write only if all pass
  - Implement `_validate_draft()`: deterministic string-matching for database name and backend framework contradictions against `CodeAnalysisFacts`
  - Implement `_check_duplicate_paragraphs()`: detect verbatim paragraph duplication across sections
  - On hallucination error: abort entire transaction immediately, no retry
  - On empty/malformed response: call `build_simplified()` exactly once before failing
  - Return `GenerationResult` with `success`, `files_written`, `validation_errors`
  - _Requirements: 1.1, 1.2, 1.3, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.3, 8.4, 10.5_

  - [ ]* 7.1 Write property test for LLM called exactly once per template
    - **Property 1: LLM called for every template**
    - For any successful run, `LLMProvider.complete()` must be called exactly 8 times with no regex path taken
    - **Validates: Requirements 1.1**

  - [ ]* 7.2 Write property test for retry-once behavior
    - **Property 2: Retry exactly once on empty/malformed response**
    - For any template returning empty or malformed Markdown, `build_simplified()` is called exactly once; hallucination errors must never trigger `build_simplified()`
    - **Validates: Requirements 1.3, 6.5**

  - [ ]* 7.3 Write property test for atomic write
    - **Property 6: Atomic write — all 8 files or none**
    - If any draft fails validation, zero files are written to disk; if all pass, exactly 8 files are written
    - **Validates: Requirements 5.1, 5.2, 5.3**

  - [ ]* 7.4 Write property test for hallucination detection
    - **Property 7: Hallucination detection — database/framework contradictions caught**
    - For any draft containing a database or framework name that contradicts `CodeAnalysisFacts`, `_validate_draft()` must return a non-empty error list
    - **Validates: Requirements 6.1, 6.2, 6.3**

  - [ ]* 7.5 Write property test for duplicate paragraph detection
    - **Property 8: Duplicate paragraph detection**
    - For any draft containing the same paragraph verbatim in more than one section, `_check_duplicate_paragraphs()` must return a non-empty error list
    - **Validates: Requirements 10.5**

- [ ] 8. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Enhance `LLMProvider` with availability enforcement
  - Add `LLMUnavailableError` import/re-export in `llm/provider.py`
  - Add `is_available()` method that returns `True` when at least one provider is configured or running in MCP mode
  - Enforce `ctx.sample()` as default in MCP mode without requiring additional configuration
  - Raise `LLMUnavailableError` with actionable message in CLI mode when no provider is configured
  - Implement exponential backoff retry for transient API errors before raising terminal error
  - Remove any code path that falls back to `TemplatePopulator`
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 10. Implement `DeltaAnalyzer`
  - Create `hiveforge-power/hiveforge/steering/delta_analyzer.py`
  - Implement `analyze(source_docs, code_facts, existing_steering)` returning `DeltaReport`
  - Detect structural drift only: technology mismatches, dependency changes
  - Prefer design documents over codebase when they diverge on a factual field
  - Populate all four `DeltaReport` fields: `doc_vs_code`, `steering_vs_code`, `steering_vs_docs`, `missing_in_all`
  - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [ ]* 10.1 Write unit tests for `DeltaAnalyzer`
    - Test technology mismatch detection between docs and code facts
    - Test dependency change detection
    - Test design-doc-wins-on-conflict behavior
    - _Requirements: 7.1, 7.4, 7.5_

- [ ] 11. Update `PromptBuilder` to include `DeltaReport` in drift/update prompts
  - When `use_case` is `drift_correction` or `update`, include `DeltaReport` in the user prompt
  - Instruct LLM to prefer design documents as source of truth unless `user_intent` specifies otherwise
  - _Requirements: 7.3, 7.5_

- [ ] 12. Refactor `AutonomousWorkflow` to use the new pipeline
  - Update `hiveforge-power/hiveforge/steering/workflows/autonomous_workflow.py`
  - Wire `InputResolver` → `CodeAnalyzer.to_facts()` → `DocumentParser` (bounded) → `DeltaAnalyzer` → `ContextAssembler` → `PromptBuilder` → `SteeringFileGenerator`
  - Remove all calls to `TemplatePopulator` from the workflow
  - Remove all calls to `SteeringAssistant.generate_file()` from the workflow
  - Propagate `LLMUnavailableError` to the caller (CLI or MCP tool)
  - _Requirements: 1.1, 1.2, 3.3, 8.3, 9.1, 9.2, 9.3, 9.4_

  - [ ]* 12.1 Write integration test for full pipeline (new_from_docs use case)
    - Mock `LLMProvider`, assert 8 LLM calls, assert 8 files written, assert no `TemplatePopulator` calls
    - _Requirements: 1.1, 5.2, 9.1_

  - [ ]* 12.2 Write integration test for reverse_engineer use case
    - No source docs present; assert `source_docs=[]` in all `GenerationContext` instances
    - _Requirements: 9.2_

  - [ ]* 12.3 Write integration test for LLMUnavailableError propagation
    - Assert that when `LLMProvider.is_available()` returns `False`, no files are written and error is raised
    - _Requirements: 1.2, 8.2, 8.4_

- [ ] 13. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests use `hypothesis` (already available in the test suite) for generative testing
- The fixed generation order is: `project-vision.md`, `tech-stack.md`, `architecture.md`, `conventions.md`, `agents.md`, `workflows.md`, `security.md`, `testing.md`
- `TemplatePopulator` is NOT deleted — it is simply removed from the primary generation path; existing tests that cover it remain valid
- All new files go under `hiveforge-power/hiveforge/steering/`; test files go under `hiveforge-power/tests/`
