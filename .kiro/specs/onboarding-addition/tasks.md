# Implementation Plan: Steering Assistant

## Overview

This implementation plan breaks down the Steering Assistant feature into discrete, incremental coding tasks. The feature will be implemented in Python 3.11+ as part of the HiveForge CLI tool. Each task builds on previous work, with property-based tests integrated throughout to catch errors early. The implementation follows a bottom-up approach: core utilities first, then parsers and analyzers, then workflows, and finally CLI integration.

## Tasks

- [x] 1. Set up project structure and core dependencies
  - Create directory structure: `src/hiveforge/steering/` with subdirectories for `parsers/`, `analyzers/`, `agents/`, `workflows/`, `validators/`
  - Add new dependencies to `pyproject.toml`: PyPDF2, pytesseract, Pillow, colorama, tree-sitter, pathspec
  - Create `__init__.py` files for all modules
  - Set up hypothesis for property-based testing in dev dependencies
  - _Requirements: 1.1-1.8_

- [ ] 2. Implement core data models and utilities
  - [x] 2.1 Create data models for parsed documents, templates, and workflow state
    - Implement `ParsedDocument`, `Template`, `TemplateSection`, `WorkflowState`, `SteeringConfig` classes using Pydantic or dataclasses
    - Add validation rules and type hints
    - _Requirements: 3.1-3.5, 4.1-4.8_

  - [ ]* 2.2 Write property test for data model validation
    - **Property 22: Completeness Validation**
    - **Validates: Requirements 10.2, 10.5**

  - [x] 2.3 Implement staging folder management utilities
    - Create functions to create `.kiro/onboarding/` directory, detect supported file types, list files
    - _Requirements: 2.1-2.5_

  - [ ]* 2.4 Write property test for staging folder operations
    - **Property 1: Staging Directory Creation**
    - **Property 5: File Detection**
    - **Validates: Requirements 2.1, 2.2**

- [ ] 3. Implement document parsers
  - [x] 3.1 Create markdown parser
    - Implement `parse_markdown()` function to extract text content and structure
    - Handle multi-language content (UTF-8 encoding)
    - Preserve code blocks with language tags
    - Preserve Mermaid diagrams
    - _Requirements: 3.1_

  - [x] 3.2 Create PDF parser
    - Implement `parse_pdf()` function using PyPDF2 or pdfplumber
    - Extract text from all pages
    - Handle encoding issues with fallback strategies
    - _Requirements: 3.2_

  - [ ] 3.3 Create image parser with OCR
    - Implement `parse_image()` function using pytesseract
    - Handle various image formats (PNG, JPG, etc.)
    - Extract text using OCR
    - _Requirements: 3.3_

  - [ ] 3.4 Create DocumentParser orchestrator
    - Implement `parse_directory()` to process all files in staging folder
    - Add error handling for parsing failures (log and continue)
    - Aggregate results into list of ParsedDocument objects
    - _Requirements: 3.4, 3.5_

  - [ ]* 3.5 Write property tests for document parsing
    - **Property 2: Multi-Format Parsing**
    - **Property 3: Artifact Preservation**
    - **Property 4: Resilient Parsing**
    - **Validates: Requirements 3.1-3.5**

- [ ] 4. Checkpoint - Ensure parsing tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement code analyzer for codebase import
  - [ ] 5.1 Create language detection module
    - Implement `detect_languages()` using file extension counting and line counting
    - Parse version specifiers from dependency files and runtime configs
    - Calculate language percentages
    - Assign confidence scores based on file count thresholds
    - _Requirements: 3A.3, 3A.4_

  - [ ] 5.2 Create tech stack extraction module
    - Implement parsers for dependency files: package.json, requirements.txt, go.mod, Cargo.toml, pom.xml, Gemfile
    - Extract frameworks, libraries, databases, and versions
    - Assign confidence scores (1.0 for dependencies, 0.7 for imports, 0.4 for guesses)
    - _Requirements: 3A.5_

  - [ ] 5.3 Create architecture inference module
    - Implement directory structure analysis with pattern matching
    - Detect patterns: monolithic, microservices, layered, MVC, hexagonal
    - Assign confidence scores based on pattern match strength
    - Fall back to "custom" for unrecognized patterns
    - _Requirements: 3A.6_

  - [ ] 5.4 Create conventions extraction module
    - Implement AST-based analysis for naming patterns (sample 100 functions/variables)
    - Detect indentation style (sample 100 code blocks)
    - Identify docstring/comment patterns
    - Parse config files (.editorconfig, .prettierrc, .eslintrc, .pylintrc, pyproject.toml) with priority
    - _Requirements: 3A.7, 3A.11_

  - [ ] 5.5 Create documentation parser for codebases
    - Parse README files, docs/ folders, inline comments
    - Extract project context and add to knowledge base
    - _Requirements: 3A.8_

  - [ ] 5.6 Create CodeAnalyzer orchestrator
    - Implement main `analyze()` method that coordinates all analysis modules
    - Respect .gitignore files using pathspec library
    - Implement sampling strategy for large codebases (>10k files)
    - Add progress updates every 30 seconds for long-running analysis
    - Implement caching in `.kiro/.cache/code_analysis.json`
    - Generate token-limited summaries (max 2000 tokens per template)
    - _Requirements: 3A.1-3A.15, 3B.1-3B.7, 3C.1-3C.5_

  - [ ]* 5.7 Write property tests for code analysis
    - **Property 32: Language Detection Accuracy**
    - **Property 33: Tech Stack Extraction**
    - **Property 34: Architecture Pattern Inference**
    - **Property 35: Convention Extraction**
    - **Property 36: Documentation Parsing**
    - **Property 39: Gitignore Respect**
    - **Property 40: Config File Extraction**
    - **Property 47: Local Code Analysis**
    - **Property 48: Code Analysis Token Limiting**
    - **Validates: Requirements 3A.3-3A.15, 3B.1-3B.7, 3C.1-3C.5**

- [ ] 6. Checkpoint - Ensure code analysis tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement knowledge base and gap analysis
  - [ ] 7.1 Create KnowledgeBase class
    - Implement initialization with parsed documents and optional code analysis results
    - Implement `search()` for content retrieval
    - Implement `get_relevant_content()` with token limiting (max 4000 tokens)
    - Implement extraction methods for tech stack, conventions, architecture
    - _Requirements: 6.1-6.5_

  - [ ] 7.2 Create GapAnalysisEngine class
    - Load steering file template definitions
    - Compare knowledge base content against template requirements
    - Classify sections as complete, missing, or ambiguous
    - Generate prioritized list of questions grouped by steering file
    - _Requirements: 6.1-6.5_

  - [ ]* 7.3 Write property tests for gap analysis
    - **Property 9: Gap Classification**
    - **Property 10: Priority Ordering**
    - **Property 11: Question Grouping**
    - **Property 12: Question Context**
    - **Property 50: Knowledge Base Token Limiting**
    - **Validates: Requirements 6.1-6.5, 7.7**

- [ ] 8. Implement steering assistant agent
  - [ ] 8.1 Create ResponseCache for LLM response caching
    - Implement cache storage using file-based or Redis backend
    - Implement `get()` and `set()` methods with question hashing
    - _Requirements: 7.8_

  - [ ] 8.2 Create SteeringAssistant class
    - Implement conversation orchestration with question batching (max 8 per batch)
    - Implement token-efficient LLM prompting (max 4000 tokens knowledge base content)
    - Integrate ResponseCache for avoiding redundant API calls
    - Implement optional web research functionality (when --research flag is set)
    - Handle interactive vs non-interactive modes
    - _Requirements: 7.1-7.8, 12.1-12.5_

  - [ ]* 8.3 Write property tests for steering assistant
    - **Property 13: Non-Interactive Mode**
    - **Property 14: Research Isolation**
    - **Property 49: Question Batch Size Limiting**
    - **Property 51: LLM Response Caching**
    - **Validates: Requirements 7.2, 7.6, 7.8, 12.4**

- [ ] 9. Implement template population and diff generation
  - [ ] 9.1 Create TemplatePopulator class
    - Load template definitions for all 8 steering files
    - Implement `populate()` to replace placeholders with gathered information
    - Implement `populate_all()` for batch processing
    - Preserve frontmatter in templates
    - _Requirements: 4.6, 4.7_

  - [ ] 9.2 Create DiffGenerator class
    - Implement `compute_diff()` using difflib
    - Implement `format_diff()` with colorama for terminal output
    - Show additions in green, deletions in red, context lines
    - _Requirements: 5.6, 9.1-9.4_

  - [ ]* 9.3 Write property tests for template population and diffs
    - **Property 6: Complete Template Generation**
    - **Property 7: Correct File Placement**
    - **Property 19: Comprehensive Diff Generation**
    - **Property 20: Unchanged File Indication**
    - **Validates: Requirements 4.6, 4.7, 5.6, 9.1-9.4**

- [ ] 10. Implement conflict resolution and customization detection
  - [ ] 10.1 Create ConflictResolver class
    - Implement `detect_conflicts()` to identify contradictions in technology choices, architecture, goals
    - Implement `resolve_conflict()` to apply user's resolution choice
    - Present conflicts side-by-side with explanations
    - _Requirements: 5.5, 8.1-8.4_

  - [ ] 10.2 Create CustomizationDetector class
    - Implement `detect_customizations()` using diff comparison with original templates
    - Use heuristics: content beyond placeholders, unique formatting, custom sections
    - Assign confidence scores (0.0-1.0)
    - _Requirements: 15.1-15.5_

  - [ ]* 10.3 Write property tests for conflict resolution and customization
    - **Property 15: Conflict Detection**
    - **Property 16: Conflict Presentation**
    - **Property 17: Customization Preservation**
    - **Property 18: Customization Detection**
    - **Validates: Requirements 5.5, 8.1-8.5, 15.1-15.5**

- [ ] 11. Checkpoint - Ensure core component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement steering validator agent
  - [ ] 12.1 Create rule-based validation functions
    - Implement `check_completeness()` using regex to detect unreplaced placeholders
    - Implement `check_structure()` to verify frontmatter and template structure
    - Implement `check_consistency()` using keyword matching and value comparison
    - _Requirements: 10.2, 10.4, 10.5, 10.6_

  - [ ] 12.2 Create SteeringValidator class
    - Implement `validate_file()` for single file validation using rule-based checks
    - Implement `validate_all()` for batch validation
    - Implement optional `check_consistency_semantic()` using LLM (max 1000 tokens per check)
    - Generate ValidationReport with categorized issues (critical, warning, info)
    - Include line numbers and fix suggestions
    - Track LLM usage (calls and tokens)
    - Implement validation result caching
    - _Requirements: 10.1-10.10_

  - [ ]* 12.3 Write property tests for validation
    - **Property 23: Cross-File Consistency**
    - **Property 24: Structure Validation**
    - **Property 25: Comprehensive Validation Report**
    - **Property 53: Rule-Based Validation Priority**
    - **Property 54: Validation Token Limiting**
    - **Property 55: Validation Result Caching**
    - **Validates: Requirements 10.1-10.10**

- [ ] 13. Implement workflow orchestrators
  - [ ] 13.1 Create InitWorkflow class
    - Implement workflow steps: create staging dir, optionally analyze code, parse artifacts, build knowledge base, run gap analysis, conduct conversation, populate templates, write files, run validation
    - Handle existing file detection and backup creation
    - Integrate all components: DocumentParser, CodeAnalyzer, KnowledgeBase, GapAnalysisEngine, SteeringAssistant, TemplatePopulator, SteeringValidator
    - _Requirements: 4.1-4.8, 13.1-13.2_

  - [ ] 13.2 Create UpdateWorkflow class
    - Implement workflow steps: verify files exist, parse existing files, parse new artifacts, detect customizations, run gap analysis, conduct conversation, detect conflicts, generate diffs, get user approval, apply changes, run validation
    - Implement incremental update logic (only send changed sections to LLM, max 3000 tokens per file)
    - Integrate ConflictResolver, CustomizationDetector, DiffGenerator
    - _Requirements: 5.1-5.11, 13.3-13.5_

  - [ ] 13.3 Create ValidateWorkflow class
    - Implement workflow steps: verify files exist, run validator, generate report, display report, return exit code
    - Support --strict flag for treating warnings as errors
    - _Requirements: 11.1-11.7_

  - [ ]* 13.4 Write property tests for workflows
    - **Property 8: Conditional Validation**
    - **Property 21: Update Rejection Idempotence**
    - **Property 26: Validation Exit Codes**
    - **Property 27: Backup Creation**
    - **Property 28: Update Idempotence**
    - **Property 29: Validation Determinism**
    - **Property 30: Incremental Updates**
    - **Property 31: Existing File Detection**
    - **Property 37: Code Analysis Integration**
    - **Property 38: Post-Analysis Gap Detection**
    - **Property 52: Incremental Update Analysis**
    - **Validates: Requirements 4.8, 5.9-5.11, 11.5-11.7, 13.1-13.5, 3A.9-3A.10**

- [ ] 14. Checkpoint - Ensure workflow tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Implement CLI commands
  - [ ] 15.1 Create CLI command handler using typer
    - Implement `steering_init()` command with flags: --research, --skip-validation, --interactive/--no-interactive, --analyze-code
    - Implement `steering_update()` command with flags: --research, --skip-validation, --interactive/--no-interactive
    - Implement `steering_validate()` command with flag: --strict
    - Add help text and command descriptions
    - _Requirements: 1.1-1.8_

  - [ ] 15.2 Integrate CLI with workflow orchestrators
    - Wire CLI commands to InitWorkflow, UpdateWorkflow, ValidateWorkflow
    - Handle command-line argument parsing and validation
    - Display progress feedback during operations
    - Handle errors gracefully with clear messages
    - _Requirements: 14.1-14.6_

  - [ ]* 15.3 Write integration tests for CLI
    - Test command parsing and routing
    - Test flag combinations
    - Test error handling for invalid commands
    - Test end-to-end workflows through CLI
    - _Requirements: 1.1-1.8, 14.1-14.6_

- [ ] 16. Implement progress feedback and error handling
  - [ ] 16.1 Add progress indicators
    - Display progress for file parsing, gap analysis, template population, validation
    - Show which files are being processed
    - Display summary of actions taken and next steps
    - _Requirements: 14.1-14.6_

  - [ ] 16.2 Implement comprehensive error handling
    - Handle file system errors (missing directories, permissions, disk full)
    - Handle parsing errors (corrupted files, encoding issues)
    - Handle code analysis errors (unrecognized languages, malformed files, timeouts)
    - Handle LLM API errors (rate limiting, timeouts, invalid responses)
    - Implement graceful degradation strategies
    - _Requirements: 3B.1-3B.7_

  - [ ]* 16.3 Write property tests for error handling
    - **Property 41: Large Codebase Sampling**
    - **Property 42: Progress Updates**
    - **Property 43: Confidence Score Display**
    - **Property 44: Parsing Error Resilience**
    - **Property 45: Missing Dependency Fallback**
    - **Property 46: Unknown Architecture Handling**
    - **Validates: Requirements 3A.12-3A.15, 3B.1-3B.7**

- [ ] 17. Create agent definition files
  - [ ] 17.1 Create Steering_Assistant agent definition
    - Write `.kiro/agents/steering-assistant.md` with agent description, capabilities, and usage instructions
    - _Requirements: 4.1-4.8, 5.1-5.11_

  - [ ] 17.2 Create Steering_Validator agent definition
    - Write `.kiro/agents/steering-validator.md` with agent description, capabilities, and usage instructions
    - _Requirements: 10.1-10.10, 11.1-11.7_

- [ ] 18. Write documentation
  - [ ] 18.1 Update HiveForge README
    - Add section on steering assistant feature
    - Document CLI commands and flags
    - Provide usage examples
    - _Requirements: 1.1-1.8_

  - [ ] 18.2 Create user guide
    - Write guide for init workflow (with and without --analyze-code)
    - Write guide for update workflow
    - Write guide for validate workflow
    - Include troubleshooting section
    - _Requirements: 4.1-4.8, 5.1-5.11, 11.1-11.7_

- [ ] 19. Final checkpoint - Integration testing
  - [ ] 19.1 Test end-to-end init workflow with real artifacts
    - Test with markdown files, PDFs, images
    - Verify all 8 steering files are generated correctly
    - _Requirements: 4.1-4.8_

  - [ ] 19.2 Test end-to-end init workflow with code analysis
    - Test with real codebases in multiple languages
    - Verify tech stack, architecture, conventions are extracted correctly
    - _Requirements: 3A.1-3A.15_

  - [ ] 19.3 Test end-to-end update workflow
    - Test with existing steering files and new artifacts
    - Verify conflicts are detected and resolved
    - Verify customizations are preserved
    - _Requirements: 5.1-5.11_

  - [ ] 19.4 Test end-to-end validate workflow
    - Test with valid and invalid steering files
    - Verify validation report is comprehensive
    - Verify exit codes are correct
    - _Requirements: 11.1-11.7_

  - [ ] 19.5 Test with complex real-world documents
    - Test with multi-language documents (Cyrillic, CJK, mixed scripts)
    - Test with documents containing Mermaid diagrams, code blocks, tables
    - Test with deeply nested section hierarchies
    - Verify all content is preserved correctly
    - _Requirements: 3.1_

- [ ] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties across all inputs
- Unit tests (not listed) should be written for specific examples, edge cases, and integration points
- The implementation uses Python 3.11+ with type hints and Pydantic for data validation
- All code analysis is performed locally without LLM calls for token efficiency
- LLM usage is minimized through caching, batching, and token limiting strategies
