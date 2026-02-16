# Requirements Document

## Introduction

The Steering Assistant feature enhances HiveForge by providing intelligent automation for creating and maintaining steering files throughout a project's lifecycle. This feature addresses three critical workflows: (1) initial steering file creation from raw project artifacts, (2) importing existing codebases into HiveForge by analyzing source code and documentation, and (3) ongoing refinement and updates to existing steering files as projects evolve. Users can provide project artifacts (markdown, PDFs, images), point to existing codebases, and engage in guided conversations to generate or update comprehensive steering files. The system validates completeness and consistency, shows diffs for updates, and preserves user customizations.

## Glossary

- **HiveForge**: The Python CLI tool that scaffolds KIRO v05 projects with multi-agent architecture
- **Steering_Files**: Configuration files in `.kiro/steering/` that guide AI agent behavior (project-vision.md, tech-stack.md, architecture.md, conventions.md, api-standards.md, db-standards.md, qa-standards.md, ui-standards.md)
- **Steering_Assistant**: The AI agent responsible for parsing artifacts, conversing with users, and creating or updating steering files
- **Steering_Validator**: The AI agent responsible for checking steering file completeness, consistency, and identifying conflicts
- **Staging_Folder**: The `.kiro/onboarding/` directory where users place source artifacts
- **Source_Artifacts**: User-provided documents (markdown, PDF, images) containing project information
- **Codebase_Import**: The process of analyzing an existing codebase to extract project information for steering file generation
- **Code_Analyzer**: Component that examines source code to infer technology stack, architecture patterns, and conventions
- **Gap_Analysis**: The process of identifying missing information required to populate steering file templates
- **Template_Population**: The process of replacing placeholders in steering file templates with extracted or user-provided information
- **Update_Workflow**: The process of modifying existing steering files while preserving valid content and showing diffs
- **Conflict_Resolution**: The process of identifying and resolving contradictions between old and new information
- **Validation_Report**: Output from Steering_Validator showing completeness, consistency issues, and conflicts

## Requirements

### Requirement 1: CLI Command Structure

**User Story:** As a developer, I want clear CLI commands for different steering file operations, so that I can easily create, update, or validate steering files.

#### Acceptance Criteria

1. THE System SHALL provide a `hiveforge steering init` command to create steering files from scratch
2. THE System SHALL provide a `hiveforge steering update` command to modify existing steering files
3. THE System SHALL provide a `hiveforge steering validate` command to check steering file quality
4. THE System SHALL provide a `--analyze-code` flag that works with the init command to enable codebase analysis
5. THE System SHALL provide a `--research` flag that works with init and update commands to enable web research
6. THE System SHALL provide a `--skip-validation` flag that works with init and update commands to skip validation
7. THE System SHALL provide `--interactive` and `--no-interactive` flags to control conversation mode
8. WHEN a subcommand is not provided, THE System SHALL display help text with available subcommands

### Requirement 2: Staging Folder Management

**User Story:** As a user, I want to place my project documents in a staging folder, so that the steering assistant can access them for analysis.

#### Acceptance Criteria

1. WHEN any steering command is initiated, THE System SHALL create a `.kiro/onboarding/` directory if it does not exist
2. WHEN source artifacts are placed in the Staging_Folder, THE System SHALL detect and list all supported file types (markdown, PDF, images)
3. WHEN the Staging_Folder is empty, THE System SHALL proceed with conversation-only mode without parsing
4. THE System SHALL preserve original source artifacts in the Staging_Folder after processing
5. WHEN the update command is run, THE System SHALL parse both old steering files and new artifacts from Staging_Folder

### Requirement 3: Multi-Format Document Parsing

**User Story:** As a user, I want the system to extract information from various document formats, so that I don't need to manually transcribe existing documentation.

#### Acceptance Criteria

1. WHEN a markdown file is provided, THE Parser SHALL extract all text content and structure
2. WHEN a PDF file is provided, THE Parser SHALL extract text content from all pages
3. WHEN an image file is provided, THE Parser SHALL extract text using OCR capabilities
4. WHEN parsing fails for any file, THE System SHALL log the error and continue processing remaining files
5. THE Parser SHALL aggregate extracted content from all successfully parsed files into a unified knowledge base

### Requirement 3A: Existing Codebase Import

**User Story:** As a developer with an existing codebase, I want to import my project into HiveForge by analyzing the source code, so that I can continue development using the multi-agent architecture.

#### Acceptance Criteria

1. WHEN `hiveforge steering init` is run with a `--analyze-code` flag, THE System SHALL analyze the existing codebase starting from the current directory
2. WHEN analyzing code, THE Code_Analyzer SHALL respect .gitignore files and exclude ignored paths from analysis
3. WHEN analyzing code, THE Code_Analyzer SHALL detect the primary programming language(s) used in the project with their respective percentages
4. WHEN analyzing code, THE Code_Analyzer SHALL detect language versions from version specifiers in dependency files or runtime configuration files
5. WHEN analyzing code, THE Code_Analyzer SHALL identify the technology stack (frameworks, libraries, databases) from dependency files (package.json, requirements.txt, go.mod, Cargo.toml, pom.xml, Gemfile)
6. WHEN analyzing code, THE Code_Analyzer SHALL infer architectural patterns (monolithic, microservices, layered, MVC, hexagonal) from directory structure and code organization
7. WHEN analyzing code, THE Code_Analyzer SHALL extract coding conventions including naming patterns (snake_case, camelCase, PascalCase), indentation style (spaces/tabs, count), line length, and documentation style
8. WHEN analyzing code, THE Code_Analyzer SHALL parse README files, documentation folders (docs/, documentation/), and inline comments for project context
9. WHEN code analysis is complete, THE System SHALL merge findings with any artifacts in Staging_Folder, prioritizing code analysis for technical details (tech stack, conventions) and artifacts for business context (vision, goals)
10. WHEN both code analysis and artifact parsing are complete, THE System SHALL perform Gap_Analysis to identify remaining missing information
11. WHEN the codebase contains configuration files (.editorconfig, .prettierrc, .eslintrc, .pylintrc, pyproject.toml), THE Code_Analyzer SHALL extract conventions from them
12. WHEN the codebase exceeds 10,000 files, THE Code_Analyzer SHALL use sampling strategy (analyze representative files from each directory) and warn the user
13. WHEN code analysis takes longer than 5 minutes, THE System SHALL display progress updates every 30 seconds
14. WHEN the codebase contains multiple project roots (monorepo), THE System SHALL analyze the current directory and its subdirectories, treating it as a single project
15. WHEN code analysis produces findings, THE System SHALL include confidence scores (0.0-1.0) for each inferred item and display low-confidence items (<0.6) to the user for confirmation

### Requirement 3B: Code Analysis Error Handling

**User Story:** As a developer, I want code analysis to handle errors gracefully, so that analysis failures don't block my workflow.

#### Acceptance Criteria

1. WHEN a source file cannot be parsed, THE Code_Analyzer SHALL log the error, skip that file, and continue analyzing remaining files
2. WHEN no dependency files are found, THE Code_Analyzer SHALL attempt to infer technology stack from import statements and log a warning
3. WHEN no recognizable architecture pattern is found, THE Code_Analyzer SHALL report "custom" as the pattern and extract directory structure as-is
4. WHEN code analysis finds no clear conventions, THE Code_Analyzer SHALL report this in the gap analysis and ask the user during conversation
5. WHEN .gitignore parsing fails, THE Code_Analyzer SHALL log a warning and proceed without exclusions
6. WHEN code analysis is interrupted (timeout, user cancellation), THE System SHALL save partial results and offer to resume or start fresh
7. WHEN confidence scores are below 0.3 for critical items (language, framework), THE System SHALL flag them as "uncertain" and prioritize asking the user

### Requirement 3C: Token-Efficient Code Analysis

**User Story:** As a user, I want code analysis to minimize LLM token usage, so that the process is fast and cost-effective.

#### Acceptance Criteria

1. THE Code_Analyzer SHALL perform all analysis using local algorithms (AST parsing, regex, file counting) without LLM API calls
2. WHEN code analysis is complete, THE System SHALL extract only summary statistics and key findings (not full file contents) for LLM context
3. THE System SHALL limit code analysis results sent to LLM to maximum 2000 tokens per steering file template
4. WHEN multiple code files contain similar patterns, THE Code_Analyzer SHALL deduplicate findings before presenting to LLM
5. THE System SHALL cache code analysis results in `.kiro/.cache/code_analysis.json` to avoid re-analyzing unchanged codebases

### Requirement 4: Initial Steering File Creation (Init Workflow)

**User Story:** As a user starting a new project, I want to generate steering files from scratch, so that I can quickly set up my project configuration.

#### Acceptance Criteria

1. WHEN `hiveforge steering init` is run, THE System SHALL check if steering files already exist
2. WHEN steering files already exist, THE System SHALL warn the user and offer to back them up or abort
3. WHEN proceeding with init, THE Steering_Assistant SHALL parse all source artifacts from Staging_Folder
4. WHEN artifacts are parsed, THE Steering_Assistant SHALL perform Gap_Analysis to identify missing information
5. WHEN gaps are identified, THE Steering_Assistant SHALL engage in a guided conversation to collect missing information
6. WHEN all information is gathered, THE Steering_Assistant SHALL populate all eight steering file templates
7. WHEN population is complete, THE System SHALL write the populated files to `.kiro/steering/`
8. WHEN `--skip-validation` is not set, THE System SHALL automatically run Steering_Validator on generated files

### Requirement 5: Steering File Updates (Update Workflow)

**User Story:** As a user with existing steering files, I want to update them based on new information, so that my configuration stays current as my project evolves.

#### Acceptance Criteria

1. WHEN `hiveforge steering update` is run, THE System SHALL verify that steering files exist in `.kiro/steering/`
2. WHEN steering files do not exist, THE System SHALL display an error and suggest using `steering init` instead
3. WHEN proceeding with update, THE Steering_Assistant SHALL parse existing steering files to understand current state
4. WHEN new artifacts are in Staging_Folder, THE Steering_Assistant SHALL parse them and identify new information
5. WHEN new information conflicts with existing content, THE Steering_Assistant SHALL flag conflicts for user review
6. WHEN proposing changes, THE System SHALL display a diff showing old vs new content for each modified section
7. WHEN the user approves changes, THE Steering_Assistant SHALL update steering files while preserving user customizations
8. WHEN the user rejects changes, THE Steering_Assistant SHALL keep existing content unchanged
9. WHEN `--skip-validation` is not set, THE System SHALL automatically run Steering_Validator on updated files
10. THE System SHALL only send changed sections (not entire files) to LLM for analysis, limiting context to maximum 3000 tokens per file
11. THE System SHALL cache previous update analysis and skip re-analyzing unchanged artifacts

### Requirement 6: Intelligent Gap Analysis

**User Story:** As a user, I want the system to identify what information is missing, so that I'm only asked relevant questions.

#### Acceptance Criteria

1. WHEN source artifacts are parsed, THE Gap_Analysis SHALL compare extracted information against all Steering_Files template requirements
2. WHEN information for a template section is found, THE Gap_Analysis SHALL mark that section as complete
3. WHEN information for a template section is missing or ambiguous, THE Gap_Analysis SHALL mark that section as requiring clarification
4. THE Gap_Analysis SHALL prioritize missing information by steering file priority (project-vision and tech-stack first)
5. THE Gap_Analysis SHALL generate a structured list of questions grouped by steering file

### Requirement 7: Token-Efficient Conversational Interface

**User Story:** As a user, I want to answer targeted questions in batches, so that the process is efficient and doesn't waste tokens.

#### Acceptance Criteria

1. WHEN gaps are identified, THE Steering_Assistant SHALL present extracted information for user confirmation before asking questions
2. WHEN asking questions, THE Steering_Assistant SHALL batch related questions together by steering file or topic with a maximum of 8 questions per batch
3. WHEN presenting questions, THE Steering_Assistant SHALL provide context about why the information is needed
4. WHEN a user provides an answer, THE Steering_Assistant SHALL validate the response format and request clarification if needed
5. THE Steering_Assistant SHALL minimize back-and-forth by asking comprehensive questions upfront
6. WHERE `--no-interactive` is set, THE Steering_Assistant SHALL use only parsed artifacts without asking questions
7. THE System SHALL limit knowledge base content sent to LLM to maximum 4000 tokens per gap analysis request by extracting only relevant sections
8. THE System SHALL cache LLM responses for identical questions to avoid redundant API calls during re-runs

### Requirement 8: Conflict Detection and Resolution

**User Story:** As a user updating steering files, I want to see conflicts between old and new information, so that I can make informed decisions about what to keep.

#### Acceptance Criteria

1. WHEN comparing old and new information, THE Conflict_Resolution SHALL identify contradictions in technology choices, architecture decisions, or project goals
2. WHEN conflicts are detected, THE System SHALL present both versions side-by-side with context
3. WHEN presenting conflicts, THE System SHALL explain why the information conflicts
4. WHEN resolving conflicts, THE System SHALL allow users to choose old, new, or manually merge information
5. THE Conflict_Resolution SHALL preserve user customizations that don't conflict with new information

### Requirement 9: Diff Display for Updates

**User Story:** As a user, I want to see exactly what will change in my steering files, so that I can review updates before applying them.

#### Acceptance Criteria

1. WHEN proposing updates, THE System SHALL generate a unified diff for each modified steering file
2. WHEN displaying diffs, THE System SHALL highlight additions in green and deletions in red
3. WHEN no changes are proposed for a file, THE System SHALL indicate that the file is unchanged
4. WHEN displaying diffs, THE System SHALL show context lines around changes for clarity
5. THE System SHALL allow users to approve or reject changes on a per-file or per-section basis

### Requirement 10: Steering Validator Agent

**User Story:** As a user, I want to validate my steering files for completeness and consistency, so that I can catch issues before they affect development.

#### Acceptance Criteria

1. THE System SHALL provide a standalone Steering_Validator agent that can be invoked independently
2. WHEN validating, THE Steering_Validator SHALL check that all required template sections are populated using rule-based validation (regex, structure checks) without LLM calls
3. WHEN validating, THE Steering_Validator SHALL check for contradictions across all steering files using rule-based checks (keyword matching, value comparison)
4. WHEN rule-based validation cannot determine consistency, THE Steering_Validator MAY use LLM for semantic analysis with maximum 1000 tokens per check
5. WHEN validating, THE Steering_Validator SHALL check that template structure and frontmatter are preserved
6. WHEN validating, THE Steering_Validator SHALL flag placeholder text that was not replaced using regex patterns
7. WHEN validation completes, THE Steering_Validator SHALL generate a Validation_Report with findings
8. THE Validation_Report SHALL categorize issues by severity (critical, warning, info)
9. THE Validation_Report SHALL provide specific line numbers and suggestions for fixing issues
10. THE System SHALL cache validation results and skip re-validating unchanged files

### Requirement 11: Standalone Validation Workflow

**User Story:** As a developer, I want to run validation independently, so that I can check steering file quality in CI/CD or before commits.

#### Acceptance Criteria

1. WHEN `hiveforge steering validate` is run, THE System SHALL check if steering files exist
2. WHEN steering files do not exist, THE System SHALL display an error and exit
3. WHEN steering files exist, THE System SHALL invoke Steering_Validator to analyze them
4. WHEN validation completes, THE System SHALL display the Validation_Report to the user
5. WHEN critical issues are found, THE System SHALL exit with a non-zero status code
6. WHEN only warnings or info are found, THE System SHALL exit with status code 0
7. THE System SHALL support a `--strict` flag that treats warnings as errors

### Requirement 12: Optional Web Research

**User Story:** As a user, I want the system to optionally research missing information online, so that I can get comprehensive steering files even when my artifacts are incomplete.

#### Acceptance Criteria

1. WHERE `--research` is enabled, WHEN critical information is missing, THE Steering_Assistant SHALL offer to search for relevant information
2. WHERE `--research` is enabled, THE Steering_Assistant SHALL search for technology trade-offs, best practices, and standard configurations
3. WHERE `--research` is enabled, THE Steering_Assistant SHALL present research findings to the user for approval before using them
4. WHERE `--research` is disabled, THE Steering_Assistant SHALL only use extracted and user-provided information
5. THE System SHALL make web research opt-in and clearly indicate when research is being performed

### Requirement 13: Idempotent Operations

**User Story:** As a user, I want to run steering commands multiple times safely, so that I can refine my configuration iteratively.

#### Acceptance Criteria

1. WHEN `steering init` is run multiple times, THE System SHALL detect existing steering files and warn before overwriting
2. WHEN overwriting is confirmed, THE System SHALL back up existing steering files with a timestamp
3. WHEN `steering update` is run multiple times, THE System SHALL only propose changes that differ from current state
4. WHEN `steering validate` is run multiple times, THE System SHALL produce consistent results for unchanged files
5. THE System SHALL allow users to add new source artifacts and re-run analysis without losing previous work

### Requirement 14: Progress Feedback

**User Story:** As a user, I want to see progress during steering operations, so that I know the system is working and what stage it's at.

#### Acceptance Criteria

1. WHEN parsing files, THE System SHALL display progress for each file being processed
2. WHEN performing gap analysis, THE System SHALL indicate which steering files are being analyzed
3. WHEN populating or updating templates, THE System SHALL show which files are being generated or modified
4. WHEN running validation, THE System SHALL indicate which checks are being performed
5. WHEN errors occur, THE System SHALL display clear error messages with suggested remediation
6. WHEN any operation completes, THE System SHALL display a summary of actions taken and next steps

### Requirement 15: Preservation of User Customizations

**User Story:** As a user, I want my manual edits to steering files to be preserved during updates, so that I don't lose custom configurations.

#### Acceptance Criteria

1. WHEN updating steering files, THE System SHALL identify sections that were manually customized by the user
2. WHEN a customized section has no conflicts with new information, THE System SHALL preserve it unchanged
3. WHEN a customized section conflicts with new information, THE System SHALL present both versions for user decision
4. THE System SHALL use heuristics to detect customizations (content beyond template placeholders, unique formatting, custom sections)
5. WHEN uncertain about customizations, THE System SHALL err on the side of preserving existing content and asking the user
