# Implementation Plan: Steering Assistant v02

## Overview

This implementation plan breaks down the Steering Assistant v02 feature into discrete, incremental coding tasks. The v02 feature introduces autonomous generation with confidence scoring, semantic validation, and a feature flag system to gradually migrate from the existing question-asking workflow.

**Key Architectural Decisions:**
- Sequential generation: Generate files one at a time with shared context (not batch)
- Extends v01: AutonomousWorkflow extends InitWorkflow, reuses existing components
- Rule-based validation: Uses validation_rules.yaml (not LLM-based semantic checks)
- Conservative confidence: HIGH ≥0.9, MEDIUM ≥0.7, LOW <0.7
- File-based telemetry: Stores data in `.kiro/.telemetry/` (not database)

**Implementation Approach:** Bottom-up - foundation components first, then autonomous generation, then validation and conflict resolution, and finally CLI integration.

## Phase 1: Foundation (Feature Flags, Discovery, Validation Rules)

- [x] 1.1 Create feature flag configuration system
  - [x] 1.1.1 Create FeatureFlagConfig dataclass in `src/hiveforge/steering/models.py`
    - Implement `use_autonomous_generation: bool` (default: False)
    - Implement `confidence_threshold: float` (default: 0.7 for MEDIUM threshold)
    - Implement `max_tokens: Optional[int]` (default: None)
    - Implement `discovery_paths: List[str]` (default: [])
    - Implement `preserve_all: bool` (default: False)
    - Implement `telemetry_off: bool` (default: False)
    - Implement `max_discovery_files: int` (default: 1000)
    - Implement `max_file_size_mb: int` (default: 10)
    - _Requirements: 1.1-1.5, 18.1-18.8, 24.2-24.4_

  - [x] 1.1.2 Create FeatureFlagManager class in `src/hiveforge/steering/feature_flags.py`
    - Implement `load_from_cli()` to parse CLI flags
    - Implement `validate()` to check flag combinations and ranges (0.0-1.0 for confidence)
    - Implement `get_workflow_type()` to return AUTONOMOUS or FALLBACK
    - Implement `should_fallback()` to check if fallback should be triggered
    - Implement `warn_high_threshold()` to warn when threshold >0.95
    - _Requirements: 1.1-1.5, 8.1-8.8, 18.1-18.8_

  - [x]* 1.1.3 Write property tests for feature flag routing in `tests/test_feature_flags.py`
    - **Property 1: Feature Flag Routing**
    - **Validates: Requirements 1.1-1.5**


- [x] 1.2 Expand discovery phase (extends existing DocumentParserOrchestrator)
  - [x] 1.2.1 Create DocumentationSearcher class in `src/hiveforge/steering/analyzers/documentation_searcher.py`
    - Implement `search_docs_files()` to find README*, CONTRIBUTING*, ARCHITECTURE*, DESIGN*, SPEC*, REQUIREMENTS*
    - Implement `search_docs_dirs()` to find docs/, documentation/, design/, .github/
    - Implement `search_package_files()` to find package.json, pyproject.toml, Cargo.toml, pom.xml
    - Implement `search_config_files()` to find CI/CD (.github/workflows/, .gitlab-ci.yml, .circleci/, Jenkinsfile) and deployment configs (Dockerfile, docker-compose.yml, k8s/, helm/)
    - Implement efficient traversal with configurable depth limits
    - Implement file size filtering (skip files >max_file_size_mb)
    - Implement file count limiting (stop at max_discovery_files)
    - _Requirements: 2.1-2.7, 24.1-24.8_

  - [x] 1.2.2 Create GitHistoryAnalyzer class in `src/hiveforge/steering/analyzers/git_history_analyzer.py`
    - Implement `analyze_commits()` to extract commit messages (last 100 commits)
    - Implement `analyze_prs()` to extract PR descriptions (if .git/refs/pull exists)
    - Implement `get_summary()` to create token-limited summary (max 2000 tokens)
    - _Requirements: 2.4_

  - [x] 1.2.3 Update DiscoveryOrchestrator in `src/hiveforge/steering/parsers/orchestrator.py`
    - Extend existing DocumentParserOrchestrator with new discovery methods
    - Implement `discover_all()` to run DocumentationSearcher and GitHistoryAnalyzer
    - Implement `present_to_user()` to show discovered files with relevance indicators
    - Implement `filter_by_user_selection()` to handle user selections
    - Implement `cache_results()` to save to `.kiro/.cache/discovery_cache.json`
    - Implement progress display for large repositories
    - Implement cancellation support after 30 seconds
    - _Requirements: 2.1-2.10, 24.5-24.7_

  - [x]* 1.2.4 Write property tests for discovery in `tests/test_discovery_phase.py`
    - **Property 2: Discovery Completeness**
    - **Validates: Requirements 2.1-2.10**

- [x] 1.3 Create validation_rules.yaml specification
  - [x] 1.3.1 Create validation_rules.yaml in `src/hiveforge/steering/validation_rules.yaml`
    - Define framework_classifications (frontend: React/Vue/Angular, backend: FastAPI/Express/Django, database: PostgreSQL/MongoDB/MySQL)
    - Define rule: tech_stack_backend_framework_classification (backend framework must not be frontend)
    - Define rule: tech_stack_frontend_framework_classification (frontend framework must not be backend)
    - Define rule: architecture_tech_stack_consistency (architecture pattern must match tech stack)
    - Define rule: version_consistency_across_files (versions must be consistent)
    - Define rule: database_standards_tech_stack_consistency (db in db-standards must be in tech-stack)
    - Define rule: api_standards_tech_stack_consistency (API framework must match backend framework)
    - _Requirements: 5.1-5.10_

  - [x] 1.3.2 Create ValidationRulesLoader class in `src/hiveforge/steering/validators/validation_rules_loader.py`
    - Implement `load_rules()` to parse validation_rules.yaml
    - Implement `get_framework_classifications()` to return framework database
    - Implement `get_rules()` to return list of validation rules
    - Implement `validate_rule_syntax()` to check rule definitions
    - _Requirements: 5.10_

- [x] 1.4 Implement rule-based semantic validation (extends existing SteeringValidator)
  - [x] 1.4.1 Create TechStackValidator class in `src/hiveforge/steering/validators/tech_stack_validator.py`
    - Implement `validate_tech_stack()` to cross-reference against code analysis
    - Implement `validate_framework_pairings()` to verify frontend/backend correctness using framework_classifications
    - Implement `validate_version_consistency()` to check version consistency across files
    - Implement `extract_versions()` to parse version strings from content
    - _Requirements: 5.1-5.4_

  - [x] 1.4.2 Create ContradictionDetector class in `src/hiveforge/steering/validators/contradiction_detector.py`
    - Implement `detect_direct_contradictions()` to find explicit contradictions (Python vs JavaScript)
    - Implement `detect_implicit_contradictions()` to find logical inconsistencies (microservices vs monolithic)
    - Implement `calculate_confidence()` for conflict detection confidence
    - Implement keyword matching rules for common contradictions
    - _Requirements: 5.2-5.3_

  - [x] 1.4.3 Update SemanticValidator in `src/hiveforge/steering/validators/steering_validator.py`
    - Extend existing SteeringValidator with semantic validation
    - Implement `validate_with_rules()` to execute validation_rules.yaml rules
    - Implement `check_structural_consistency()` for cross-file consistency (e.g., database in tech-stack must be in db-standards)
    - Implement `generate_validation_report()` with errors and warnings
    - Implement rule execution engine (parse condition, evaluate, report errors)
    - _Requirements: 5.1-5.10_

  - [x]* 1.4.4 Write property tests for semantic validation in `tests/test_semantic_validation.py`
    - **Property 5: Semantic Validation Correctness**
    - **Validates: Requirements 5.1-5.10**

- [x] 1.5 Implement confidence scoring system
  - [x] 1.5.1 Create Evidence and ConfidenceScore dataclasses in `src/hiveforge/steering/models.py`
    - Implement Evidence with source (ARTIFACT, CODE_ANALYSIS, INFERENCE, USER), strength (0.0-1.0), description
    - Implement ConfidenceScore with value (0.0-1.0), level (HIGH/MEDIUM/LOW), evidence list
    - Implement ConfidenceLevel enum (HIGH ≥0.9, MEDIUM ≥0.7, LOW <0.7)
    - _Requirements: 4.1-4.7_

  - [x] 1.5.2 Create ConfidenceScorer class in `src/hiveforge/steering/confidence_scorer.py`
    - Implement `calculate_confidence()` based on evidence strength (HIGH for direct extraction, MEDIUM for inference, LOW for placeholders)
    - Implement `get_level()` to convert score to HIGH/MEDIUM/LOW using conservative thresholds
    - Implement `calibrate()` to adjust scores based on actual correctness (deferred to v02.1, stub for now)
    - Implement `aggregate_section_confidences()` to calculate overall file confidence
    - _Requirements: 4.1-4.8_

  - [x]* 1.5.3 Write property tests for confidence scoring in `tests/test_confidence_scorer.py`
    - **Property 4: Confidence Score Accuracy**
    - **Validates: Requirements 4.1-4.8**


## Phase 2: Autonomous Generation (Sequential, Extends v01)

- [x] 2.1 Create autonomous generator (extends InitWorkflow)
  - [x] 2.1.1 Create AutonomousWorkflow class in `src/hiveforge/steering/workflows/autonomous_workflow.py`
    - Extend existing InitWorkflow class from `src/hiveforge/steering/workflows/init_workflow.py`
    - Implement `generate_files_sequentially()` to generate files one at a time (NOT batch)
    - Implement generation order: project-vision.md → tech-stack.md → architecture.md → conventions.md → api-standards.md, db-standards.md, qa-standards.md, ui-standards.md
    - Implement `pass_previous_as_context()` to include previously generated files in LLM context
    - Implement `handle_partial_failure()` to continue with remaining files if one fails
    - Reuse existing KnowledgeBase, GapAnalysisEngine, TemplatePopulator from v01
    - Add `workflow_type` parameter to distinguish AUTONOMOUS vs FALLBACK mode
    - _Requirements: 3.1-3.10, 16.8-16.11, 25.1-25.7_

  - [x] 2.1.2 Create InferenceEngine class in `src/hiveforge/steering/inference_engine.py`
    - Implement `infer_from_patterns()` to use industry standards (e.g., if FastAPI detected, infer Python backend)
    - Implement `infer_from_context()` to use project context (e.g., if React in package.json, infer frontend framework)
    - Implement `mark_as_inferred()` to add inference markers with confidence levels
    - Implement `use_explicit_markers()` to add "To be determined" when inference impossible
    - Implement `--conservative-inference` support to reduce inference aggressiveness
    - _Requirements: 3.4-3.6, 26.1-26.7_

  - [x] 2.1.3 Update existing KnowledgeBase in `src/hiveforge/steering/knowledge_base.py`
    - Add `get_relevant_content_for_file()` to extract context for specific file generation
    - Add `track_generated_files()` to maintain list of already-generated files for context
    - Add `get_token_limited_context()` to respect token budget when building context
    - _Requirements: 3.2, 11.1-11.7_

  - [x]* 2.1.4 Write property tests for autonomous generation in `tests/test_autonomous_workflow.py`
    - **Property 3: Autonomous Generation Completeness**
    - **Validates: Requirements 3.1-3.10**

- [x] 2.2 Implement fallback trigger (integrates with v01 question workflow)
  - [x] 2.2.1 Create FallbackTrigger class in `src/hiveforge/steering/fallback_trigger.py`
    - Implement `should_trigger()` to check confidence (<0.6 for critical sections), validation failures, token budget exceeded, `--interactive` flag
    - Implement `get_fallback_reason()` to explain why fallback was triggered
    - Implement `get_fallback_workflow()` to return existing SteeringAssistant question-asking workflow
    - Implement `trigger_for_file()` to fall back for specific file only (not entire batch)
    - Implement context provision for questions (what was found, why it's unclear)
    - _Requirements: 8.1-8.8_

  - [x]* 2.2.2 Write property tests for fallback triggering in `tests/test_fallback_trigger.py`
    - **Property 8: Fallback Triggering**
    - **Validates: Requirements 8.1-8.8**

- [x] 2.3 Implement token budget management
  - [x] 2.3.1 Create TokenBudgetManager class in `src/hiveforge/steering/token_budget.py`
    - Implement `track_usage()` to track LLM token usage per file generation
    - Implement `warn_at_threshold()` to warn at 90% of budget
    - Implement `exceeded()` to check if budget exceeded
    - Implement `get_remaining()` to calculate remaining tokens
    - Implement `estimate_cost()` to display estimated token cost before generation
    - Implement `get_usage_summary()` to display total usage at end
    - _Requirements: 11.1-11.7_

  - [x]* 2.3.2 Write property tests for token budget in `tests/test_token_budget.py`
    - **Property 10: Performance Bounds**
    - **Property 11: Token Budget Enforcement**
    - **Validates: Requirements 10.1-10.7, 11.1-11.7**


## Phase 3: Conflict Resolution and Customization (Reuses v01 Components)

- [x] 3.1 Implement conflict detection (extends existing ConflictResolver)
  - [x] 3.1.1 Update ConflictDetector in `src/hiveforge/steering/conflict_resolver.py`
    - Extend existing ConflictResolver with confidence-based conflict detection
    - Implement `detect_direct_conflicts()` to find explicit contradictions (Python vs JavaScript)
    - Implement `detect_implicit_conflicts()` to find logical inconsistencies (REST vs GraphQL)
    - Implement `detect_version_conflicts()` to find version mismatches (React 17 vs React 18)
    - Implement `calculate_conflict_confidence()` for conflict detection confidence (only present high-confidence conflicts)
    - Implement `present_side_by_side()` to show comparisons with evidence
    - _Requirements: 6.1-6.8_

  - [x] 3.1.2 Add batch conflict resolution to ConflictResolver
    - Implement `batch_conflicts()` to group similar conflicts (e.g., all version mismatches)
    - Implement `present_batch_view()` to show multiple conflicts together
    - Implement `apply_batch_resolution()` to apply same strategy to similar conflicts
    - Implement resolution options: "Keep all old", "Use all new", "Review individually"
    - Implement `skip_conflicts()` to allow resolving later
    - _Requirements: 6.1-6.8, 19.1-19.7_

  - [x]* 3.1.3 Write property tests for conflict detection in `tests/test_conflict_detection.py`
    - **Property 6: Conflict Detection Precision**
    - **Property 19: Batch Conflict Resolution**
    - **Validates: Requirements 6.1-6.8, 19.1-19.7**

- [x] 3.2 Update customization preservation (extends existing CustomizationDetector)
  - [x] 3.2.1 Update CustomizationDetector in `src/hiveforge/steering/customization_detector.py`
    - Extend existing CustomizationDetector with confidence scoring
    - Implement `detect_customizations()` to find user modifications by diffing against templates
    - Implement `mark_protected()` to mark customized sections as protected
    - Implement `calculate_customization_confidence()` for detection confidence
    - Implement `--preserve-all` flag support to skip updates to customized sections
    - Implement `highlight_customizations()` to add visual indicators in diffs
    - _Requirements: 7.1-7.7_

  - [x]* 3.2.2 Write property tests for customization preservation in `tests/test_customization_preservation.py`
    - **Property 7: Customization Preservation**
    - **Validates: Requirements 7.1-7.7**

## Phase 4: Rollback, Performance, Telemetry, and Testing

- [x] 4.1 Implement rollback mechanism
  - [x] 4.1.1 Create BackupManager class in `src/hiveforge/steering/backup_manager.py`
    - Implement `create_backup()` to save current state before writing to `.kiro/backups/steering/`
    - Implement `restore_backup()` to restore previous version
    - Implement `cleanup_old_backups()` to delete backups exceeding limit (default: 5 versions)
    - Implement `list_backups()` to show available backups with timestamps
    - _Requirements: 9.1-9.7_

  - [x] 4.1.2 Create RollbackCommand in `src/hiveforge/steering/cli.py`
    - Implement `steering rollback` command to restore all files to previous version
    - Implement `--dry-run` flag to preview changes without writing
    - Implement `--preview` flag to display summary of changes before committing
    - _Requirements: 9.1-9.7, 20.1-20.7_

  - [x]* 4.1.3 Write property tests for rollback in `tests/test_rollback.py`
    - **Property 9: Rollback Integrity**
    - **Property 20: Preview Mode Correctness**
    - **Validates: Requirements 9.1-9.7, 20.1-20.7**

- [x] 4.2 Implement performance monitoring
  - [x] 4.2.1 Create PerformanceMonitor class in `src/hiveforge/steering/performance_monitor.py`
    - Implement `start_timer()` to track operation duration
    - Implement `display_working_message()` to show progress after 5 seconds
    - Implement `display_progress_indicators()` to show file generation progress
    - Implement `check_timeout()` to enforce 60-second limit per LLM call
    - Implement `retry_on_timeout()` to retry once before failing
    - Implement `get_duration_ms()` to return operation duration
    - Implement streaming response support for better UX
    - _Requirements: 10.1-10.7_

  - [x]* 4.2.2 Write property tests for performance in `tests/test_performance_monitor.py`
    - **Property 10: Performance Bounds**
    - **Validates: Requirements 10.1-10.7**

- [x] 4.3 Implement file-based telemetry logging
  - [x] 4.3.1 Create TelemetryLogger class in `src/hiveforge/steering/telemetry_logger.py`
    - Implement `log_session()` to write session data to `.kiro/.telemetry/sessions/{timestamp}_{session_id}.json`
    - Implement `log_workflow_type()` to log AUTONOMOUS vs FALLBACK
    - Implement `log_confidence_scores()` to log confidence scores per file and section
    - Implement `log_validation_results()` to log structural and semantic validation results
    - Implement `log_token_usage()` to log token usage per file and total
    - Implement `log_error_rates()` to log error rates and failure modes
    - Implement `log_user_interactions()` to log conflict resolutions and question answers
    - Implement `update_summary()` to update `.kiro/.telemetry/summary.json` with aggregated stats
    - Implement `--telemetry-off` flag support to disable data collection
    - _Requirements: 14.1-14.9_

  - [x]* 4.3.2 Write property tests for telemetry in `tests/test_telemetry_logger.py`
    - **Property 14: Telemetry Completeness**
    - **Validates: Requirements 14.1-14.9**

- [x] 4.4 Implement testing strategy for non-deterministic generation
  - [x] 4.4.1 Create MockLLM class in `tests/mocks/mock_llm.py`
    - Implement `generate()` with mocked responses for deterministic unit tests
    - Implement `set_response()` to configure mock responses
    - Implement `get_call_count()` to track LLM calls
    - Implement `get_call_history()` to inspect prompts sent to LLM
    - _Requirements: 12.1_

  - [x] 4.4.2 Create SemanticSimilarityChecker class in `tests/utils/semantic_checker.py`
    - Implement `check_similarity()` to compare content semantically (not exact match)
    - Implement `calculate_similarity_score()` to return 0.0-1.0
    - Implement `check_properties()` to test structure, completeness, confidence scores
    - _Requirements: 12.2-12.3_

  - [x] 4.4.3 Create regression test suite in `tests/test_regression.py`
    - Implement tests with known-good examples from real projects
    - Implement integration tests with real LLM calls (marked as slow/optional with pytest.mark.slow)
    - Implement error handling and recovery tests
    - _Requirements: 12.4-12.7_

  - [x]* 4.4.4 Write property tests for testability in `tests/test_testability.py`
    - **Property 12: Testability for Non-Deterministic Generation**
    - **Validates: Requirements 12.1-12.7**


## Phase 5: CLI Integration, Documentation, and UX

- [x] 5.1 Update CLI commands in `src/hiveforge/steering/cli.py`
  - [x] 5.1.1 Update steering_init command
    - Add `--use-autonomous-generation` flag to enable autonomous workflow
    - Add `--confidence-threshold` flag (default: 0.7, range: 0.0-1.0)
    - Add `--max-tokens` flag for token budget limit
    - Add `--discovery-paths` flag for custom search locations
    - Add `--preserve-all` flag to skip updates to customized sections
    - Add `--telemetry-off` flag to disable telemetry
    - Add `--max-discovery-files` flag (default: 1000)
    - Add `--max-file-size` flag (default: 10MB)
    - Add `--conservative-inference` flag to reduce inference aggressiveness
    - Add `--interactive` flag to force fallback workflow
    - Implement workflow routing based on feature flags
    - _Requirements: 1.1-1.5, 18.1-18.8, 24.2-24.4, 26.6_

  - [x] 5.1.2 Update steering_update command
    - Add `--incremental` flag to force incremental update mode
    - Add `--preview` flag to display changes without writing
    - Implement incremental analysis using `.kiro/.cache/steering_cache.json`
    - _Requirements: 20.1-20.7, 23.1-23.8_

  - [x] 5.1.3 Add new CLI commands
    - Add `steering rollback` command to restore previous version
    - Add `steering rollback --list` to show available backups
    - Add `steering calibrate --calibrate-confidence` command (stub for v02.1)
    - _Requirements: 9.3, 22.6_

  - [x]* 5.1.4 Write integration tests for CLI in `tests/test_cli_integration_v02.py`
    - Test command parsing and routing
    - Test flag combinations and validation
    - Test error handling and recovery
    - Test backward compatibility (v01 workflow without flags)
    - **Property 1: Feature Flag Routing**
    - **Property 16: Backward Compatibility and Integration**
    - **Validates: Requirements 1.1-1.5, 16.1-16.11, 18.1-18.8**

- [x] 5.2 Update documentation
  - [x] 5.2.1 Update README.md
    - Add section on autonomous generation feature
    - Document feature flag system and gradual rollout
    - Document confidence scoring and interpretation (HIGH ≥0.9, MEDIUM ≥0.7, LOW <0.7)
    - Add quick start example with `--use-autonomous-generation` flag
    - Document UX improvements (14 questions → 0-3, 10 min → 2 min, 83 errors → 0)
    - _Requirements: 15.1-15.7_

  - [x] 5.2.2 Update docs/steering-assistant-guide.md
    - Add v02 autonomous workflow section
    - Document sequential generation process (file-by-file with context)
    - Document fallback workflow triggers and when to use `--interactive`
    - Document confidence scoring system with visual indicators
    - Document semantic validation with validation_rules.yaml
    - Document conflict resolution and batch operations
    - Document rollback and preview modes
    - Add troubleshooting section for common v02 issues
    - _Requirements: 15.1-15.7_

  - [x] 5.2.3 Create docs/migration-v01-to-v02.md
    - Document transition from v01 to v02
    - Document feature flag usage and when to enable autonomous generation
    - Document confidence threshold configuration for different use cases
    - Document integration points (AutonomousWorkflow extends InitWorkflow)
    - Document reused components (KnowledgeBase, GapAnalysisEngine, TemplatePopulator, ConflictResolver, CustomizationDetector)
    - Document backward compatibility guarantees
    - Provide migration checklist
    - _Requirements: 15.1-15.7, 16.1-16.11_

  - [x] 5.2.4 Update docs/architecture.md
    - Add v02 architecture diagram with AutonomousWorkflow
    - Document component responsibilities for new classes
    - Document data flow for sequential generation
    - Document integration with v01 components
    - _Requirements: 15.1-15.7_

- [x] 5.3 Implement UX improvements and validation
  - [x] 5.3.1 Create UX metrics tracker in `src/hiveforge/steering/ux_metrics.py`
    - Implement `track_question_count()` to measure question reduction (target: 14 → 0-3)
    - Implement `track_completion_time()` to measure time reduction (target: 10 min → 2 min)
    - Implement `track_validation_errors()` to measure error reduction (target: 83 → 0)
    - Implement `display_summary()` to show UX improvements at end
    - _Requirements: 13.1-13.7_

  - [x] 5.3.2 Implement visual indicators for confidence levels
    - Implement `display_confidence_indicator()` to show ✓ (HIGH), ⚠ (MEDIUM), ⚠ (LOW)
    - Implement `highlight_low_confidence()` to flag sections needing review
    - Implement `format_conflict_presentation()` for easy-to-understand conflict display
    - _Requirements: 13.3-13.4_

  - [x]* 5.3.3 Write property tests for UX improvements in `tests/test_ux_improvements.py`
    - **Property 13: UX Improvement Targets**
    - **Validates: Requirements 13.1-13.7**

- [x] 5.4 Implement error handling and recovery
  - [x] 5.4.1 Create ErrorHandler class in `src/hiveforge/steering/error_handler.py`
    - Implement `handle_llm_failure()` to provide clear error messages and recovery options (retry, fallback, abort)
    - Implement `handle_validation_failure()` to explain which checks failed and why
    - Implement `handle_conflict_resolution_failure()` to guide manual resolution
    - Implement `handle_token_budget_exceeded()` to explain limit and offer continuation options
    - Implement `handle_file_io_error()` to preserve backups and prevent data loss
    - Implement comprehensive error logging with context for debugging
    - _Requirements: 17.1-17.7_

  - [x]* 5.4.2 Write property tests for error handling in `tests/test_error_handling_v02.py`
    - **Property 17: Error Recovery**
    - **Validates: Requirements 17.1-17.7**


## Phase 6: Advanced Features (v02.1 - DEFERRED)

**Note:** Phase 6 features are deferred to v02.1. These are advanced capabilities that require additional research and calibration data.

- [x]* 6.1 Implement structural consistency validation (v02.1)
  - [ ]* 6.1.1 Create StructuralConsistencyChecker class in `src/hiveforge/steering/structural_checker.py`
    - Implement `check_structural_similarity()` to verify same sections, similar length, key facts present
    - Implement `test_round_trip()` to generate → validate → regenerate → compare
    - Implement `track_consistency_rate()` to track consistency as quality metric
    - Implement temperature=0 and fixed seed for generation
    - _Requirements: 21.1-21.6 (v02.1)_

  - [ ]* 6.1.2 Write property tests for structural consistency in `tests/test_structural_consistency.py`
    - **Property 21: Generation Consistency (DEFERRED TO v02.1)**
    - **Validates: Requirements 21.1-21.6 (v02.1)**

- [x]* 6.2 Implement confidence calibration (v02.1)
  - [x]* 6.2.1 Create ConfidenceCalibrator class in `src/hiveforge/steering/confidence_calibrator.py`
    - Implement `record_corrections()` to record user corrections with original confidence
    - Implement `analyze_calibration()` to analyze score accuracy (predicted vs actual)
    - Implement `adjust_algorithms()` to adjust confidence calculation based on data
    - Implement `calibrate_across_projects()` to use multi-project data
    - _Requirements: 22.1-22.7_

  - [x]* 6.2.2 Write property tests for calibration in `tests/test_confidence_calibration.py`
    - **Property 22: Confidence Score Calibration**
    - **Validates: Requirements 22.1-22.7**

- [x]* 6.3 Implement incremental updates (per-section) (v02.1)
  - [-]* 6.3.1 Create IncrementalUpdater class in `src/hiveforge/steering/incremental_updater.py`
    - Implement `detect_section_changes()` to identify changed sections (not just files)
    - Implement `update_only_changed_sections()` to update modified sections only
    - Implement `preserve_unchanged_sections()` to preserve unchanged content
    - Implement section-level caching in `.kiro/.cache/steering_cache.json`
    - _Requirements: 23.1-23.8 (enhanced for v02.1)_

  - [-]* 6.3.2 Write property tests for incremental updates in `tests/test_incremental_updates.py`
    - **Property 23: Incremental Update Correctness**
    - **Validates: Requirements 23.1-23.8**

- [x]* 6.4 Implement advanced discovery scalability (v02.1)
  - [ ]* 6.4.1 Create ScalableDiscovery class in `src/hiveforge/steering/scalable_discovery.py`
    - Implement `heuristic_sampling()` for 100k+ file repositories
    - Implement `intelligent_file_ranking()` to prioritize relevant files
    - Implement `parallel_scanning()` for faster discovery
    - _Requirements: 24.1-24.8 (enhanced for v02.1)_

  - [ ]* 6.4.2 Write property tests for scalability in `tests/test_discovery_scalability.py`
    - **Property 24: Discovery Phase Scalability**
    - **Validates: Requirements 24.1-24.8**

- [x]* 6.5 Implement inference transparency system (v02.1)
  - [x]* 6.5.1 Create InferenceTransparency class in `src/hiveforge/steering/inference_transparency.py`
    - Implement `document_patterns()` to document inference heuristics
    - Implement `explain_inference()` to provide reasoning for each inference
    - Implement `distinguish_strength()` to distinguish strong vs weak inferences
    - _Requirements: 26.1-26.7 (enhanced for v02.1)_

  - [x]* 6.5.2 Write property tests for inference transparency in `tests/test_inference_transparency.py`
    - **Property 26: Intelligent Inference Transparency**
    - **Validates: Requirements 26.1-26.7**

- [x]* 6.6 Implement semantic equivalence validation (v02.1)
  - [x]* 6.6.1 Create SemanticEquivalenceValidator class in `src/hiveforge/steering/semantic_equivalence.py`
    - Implement `extract_key_facts()` to extract facts for comparison
    - Implement `check_semantic_equivalence()` to compare content meaning (NLP-based)
    - Implement `tolerate_wording_variations()` to allow minor differences
    - Implement `--strict-equivalence` flag for exact matching
    - _Requirements: 27.1-27.7 (v02.1)_

  - [x]* 6.6.2 Write property tests for semantic equivalence in `tests/test_semantic_equivalence.py`
    - **Property 27: Semantic Equivalence Validation (DEFERRED TO v02.1)**
    - **Validates: Requirements 27.1-27.7 (v02.1)**

- [x]* 6.7 Implement database export for telemetry (v02.1)
  - [ ]* 6.7.1 Create TelemetryExporter class in `src/hiveforge/steering/telemetry_exporter.py`
    - Implement `export_to_database()` to export file-based telemetry to PostgreSQL/SQLite
    - Implement `steering telemetry export` CLI command
    - Implement schema migration for database
    - _Requirements: 14.9 (v02.1)_


## Implementation Notes

### Phase Breakdown
- **Phase 1 (Foundation)**: Feature flags, discovery, validation rules, confidence scoring - establishes core infrastructure
- **Phase 2 (Autonomous Generation)**: Sequential file generation, inference engine, fallback triggers - core autonomous workflow
- **Phase 3 (Conflict Resolution)**: Extends v01 ConflictResolver and CustomizationDetector with confidence-based detection
- **Phase 4 (Rollback & Telemetry)**: Backup/rollback, performance monitoring, file-based telemetry, testing infrastructure
- **Phase 5 (CLI & Documentation)**: CLI integration, documentation updates, UX improvements, migration guide
- **Phase 6 (Advanced Features)**: DEFERRED TO v02.1 - structural consistency, calibration, semantic equivalence, database export

### Key Architectural Decisions
- **Sequential Generation**: Files generated one at a time with shared context (NOT batch) to avoid token limits and enable partial failure handling
- **Extends v01**: AutonomousWorkflow extends InitWorkflow; reuses KnowledgeBase, GapAnalysisEngine, TemplatePopulator, ConflictResolver, CustomizationDetector
- **Rule-Based Validation**: Uses validation_rules.yaml with framework classifications and semantic rules (NOT LLM-based validation)
- **Conservative Confidence**: HIGH ≥0.9, MEDIUM ≥0.7, LOW <0.7 (adjustable with --confidence-threshold)
- **File-Based Telemetry**: Stores data in `.kiro/.telemetry/` as JSON (database export deferred to v02.1)
- **Backward Compatibility**: v01 workflow remains default; v02 enabled with --use-autonomous-generation flag

### Testing Strategy
- Tasks marked with `*` are optional property-based tests
- Each task references specific requirements for traceability
- MockLLM class enables deterministic unit tests
- SemanticSimilarityChecker tests properties (structure, completeness) not exact content
- Integration tests with real LLM calls marked as slow/optional
- Regression test suite with known-good examples

### UX Improvements (Target Metrics)
- Question count: 14 → 0-3 (80% reduction)
- Completion time: 10 minutes → 2 minutes (80% reduction)
- Validation errors: 83 → 0 (100% reduction)

### Token Efficiency
- LLM used at final steps (generation), not intermediate steps (gap analysis)
- Discovery phase proactively searches for existing documentation before asking questions
- Token budget management with warnings at 90% and graceful degradation

### File Paths Reference
- Feature flags: `src/hiveforge/steering/feature_flags.py`, `src/hiveforge/steering/models.py`
- Discovery: `src/hiveforge/steering/analyzers/documentation_searcher.py`, `src/hiveforge/steering/analyzers/git_history_analyzer.py`
- Validation: `src/hiveforge/steering/validation_rules.yaml`, `src/hiveforge/steering/validators/`
- Autonomous workflow: `src/hiveforge/steering/workflows/autonomous_workflow.py`
- Telemetry: `.kiro/.telemetry/sessions/`, `.kiro/.telemetry/summary.json`
- Cache: `.kiro/.cache/discovery_cache.json`, `.kiro/.cache/steering_cache.json`
- Backups: `.kiro/backups/steering/`

### Property-Based Test Coverage

All 27 correctness properties from the design document are covered by property tests:

**Phase 1 Properties:**
- Property 1: Feature Flag Routing (1.1.3)
- Property 2: Discovery Completeness (1.2.4)
- Property 4: Confidence Score Accuracy (1.5.3)
- Property 5: Semantic Validation Correctness (1.4.4)

**Phase 2 Properties:**
- Property 3: Autonomous Generation Completeness (2.1.4)
- Property 8: Fallback Triggering (2.2.2)
- Property 10: Performance Bounds (2.3.2)
- Property 11: Token Budget Enforcement (2.3.2)

**Phase 3 Properties:**
- Property 6: Conflict Detection Precision (3.1.3)
- Property 7: Customization Preservation (3.2.2)
- Property 19: Batch Conflict Resolution (3.1.3)

**Phase 4 Properties:**
- Property 9: Rollback Integrity (4.1.3)
- Property 12: Testability for Non-Deterministic Generation (4.4.4)
- Property 14: Telemetry Completeness (4.3.2)
- Property 20: Preview Mode Correctness (4.1.3)

**Phase 5 Properties:**
- Property 13: UX Improvement Targets (5.3.3)
- Property 15: Migration Support (5.1.4, 5.2.3)
- Property 16: Backward Compatibility and Integration (5.1.4)
- Property 17: Error Recovery (5.4.2)
- Property 18: Confidence Threshold Configuration (5.1.4)

**Phase 6 Properties (v02.1 - DEFERRED):**
- Property 21: Generation Consistency (6.1.2)
- Property 22: Confidence Score Calibration (6.2.2)
- Property 23: Incremental Update Correctness (6.3.2)
- Property 24: Discovery Phase Scalability (6.4.2)
- Property 25: Partial Failure Isolation (covered in 2.1.4)
- Property 26: Intelligent Inference Transparency (6.5.2)
- Property 27: Semantic Equivalence Validation (6.6.2)

### Requirements Coverage

All 27 requirements are covered across the 6 phases:

**Requirements 1-5**: Feature flags, discovery, autonomous generation, confidence scoring, semantic validation (Phases 1-2)
**Requirements 6-9**: Conflict detection, customization preservation, fallback workflow, rollback (Phases 2-4)
**Requirements 10-14**: Performance, token budget, testing strategy, UX improvements, telemetry (Phases 4-5)
**Requirements 15-20**: Migration, backward compatibility, error handling, confidence thresholds, batch resolution, preview mode (Phase 5)
**Requirements 21-27**: Advanced features deferred to v02.1 (Phase 6)

### Checkpoints

- [ ] Checkpoint 1: After Phase 1 completion
  - Ensure all foundation tests pass
  - Verify feature flag routing works correctly
  - Verify discovery phase finds all artifact types
  - Verify validation_rules.yaml loads correctly
  - Ask user if questions arise

- [ ] Checkpoint 2: After Phase 2 completion
  - Ensure autonomous generation produces complete files
  - Verify sequential generation with context passing
  - Verify fallback triggers correctly
  - Verify token budget management works
  - Ask user if questions arise

- [ ] Checkpoint 3: After Phase 3 completion
  - Ensure conflict detection identifies contradictions
  - Verify customization preservation works
  - Verify batch conflict resolution works
  - Ask user if questions arise

- [ ] Checkpoint 4: After Phase 4 completion
  - Ensure rollback mechanism works correctly
  - Verify performance monitoring displays progress
  - Verify telemetry logging writes to files
  - Verify all tests pass (unit and property tests)
  - Ask user if questions arise

- [ ] Checkpoint 5: After Phase 5 completion
  - Ensure CLI integration works with all flags
  - Verify documentation is complete and accurate
  - Verify UX improvements meet target metrics
  - Verify error handling provides clear recovery options
  - Verify backward compatibility with v01
  - Ask user if questions arise

- [ ] Final Checkpoint: Before v02.0 release
  - Run full regression test suite
  - Verify all 27 requirements are implemented (except v02.1 deferred features)
  - Verify all property tests pass
  - Verify UX metrics: 14→0-3 questions, 10→2 min completion, 83→0 errors
  - Verify backward compatibility: v01 workflow works without flags
  - Ask user for final approval
