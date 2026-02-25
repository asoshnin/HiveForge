# Requirements Document

## Introduction

This document defines requirements for adding code review and technical debt tracking capabilities to HiveForge. The feature adapts a consultant's proposal for a KIRO IDE swarm agent into HiveForge's architecture as a CLI tool and MCP Power interface for generating and maintaining steering files.

HiveForge is a CLI scaffolding tool and AI-powered Steering Assistant that generates KIRO Methodology v05 projects with multi-agent architecture. It currently generates 8 steering files (project-vision.md, tech-stack.md, architecture.md, conventions.md, api-standards.md, db-standards.md, qa-standards.md, ui-standards.md) using an LLM-primary synthesis pipeline. This feature extends HiveForge to analyze codebases for technical debt and generate a 9th steering file (technical-debt.md) that tracks debt items, their priority, and remediation status.

## Glossary

- **HiveForge**: CLI scaffolding tool and MCP Power interface for generating KIRO v05 project structures and steering files
- **Steering_File**: Markdown documentation file in .kiro/steering/ that guides development (e.g., tech-stack.md, conventions.md)
- **Technical_Debt**: Code quality issues, architectural shortcuts, or maintenance burdens that should be addressed
- **Debt_Item**: A single tracked technical debt issue with description, category, priority, and status
- **Code_Analyzer**: HiveForge component that extracts facts from codebases (languages, frameworks, architecture patterns)
- **Debt_Detector**: New component that analyzes code for technical debt patterns
- **LLM_Provider**: Abstraction for routing LLM calls (KIRO Native, Vertex AI, OpenAI)
- **Steering_Assistant**: AI-powered component that generates steering file content using LLM synthesis
- **Init_Workflow**: HiveForge workflow that creates steering files from scratch
- **Update_Workflow**: HiveForge workflow that refreshes existing steering files
- **Validate_Workflow**: HiveForge workflow that checks steering file quality
- **MCP_Power**: Model Context Protocol interface for KIRO IDE integration
- **CLI_Interface**: Command-line interface for HiveForge (Typer-based)
- **DRY_Violation**: Code duplication that violates "Don't Repeat Yourself" principle
- **Test_Gap**: Missing test coverage for code paths or edge cases
- **Architecture_Smell**: Design pattern that indicates potential architectural problems
- **Performance_Risk**: Code pattern that may cause performance issues (N+1 queries, memory leaks)

## Requirements

### Requirement 1: Generate Technical Debt Steering File

**User Story:** As a developer, I want HiveForge to generate a technical-debt.md steering file, so that I have a centralized document tracking code quality issues and maintenance priorities.

#### Acceptance Criteria

1. THE Steering_Assistant SHALL generate technical-debt.md as a 9th steering file during init workflow
2. THE technical-debt.md file SHALL include YAML frontmatter with inclusion: always and priority: 3
3. THE technical-debt.md file SHALL contain sections for: Overview, Debt Categories, Active Debt Items, Resolved Debt Items, and Debt Metrics
4. WHEN no technical debt is detected, THE technical-debt.md file SHALL contain empty sections with placeholder text
5. THE technical-debt.md file SHALL follow the same LLM-primary synthesis pipeline as other steering files (InputResolver → CodeAnalyzer → ContextAssembler → PromptBuilder → SteeringFileGenerator)

### Requirement 2: Detect Technical Debt Patterns

**User Story:** As a developer, I want HiveForge to automatically detect technical debt in my codebase, so that I don't have to manually identify all code quality issues.

#### Acceptance Criteria

1. THE Debt_Detector SHALL analyze code for DRY violations by detecting repeated code patterns across files
2. THE Debt_Detector SHALL identify Test_Gaps by comparing code files against test files
3. THE Debt_Detector SHALL detect Architecture_Smells using heuristics (circular dependencies, god classes, tight coupling)
4. THE Debt_Detector SHALL identify Performance_Risks using pattern matching (N+1 query patterns, unbounded loops, memory allocation in loops)
5. WHEN analyzing codebases larger than 10,000 files, THE Debt_Detector SHALL use sampling strategy to limit analysis time
6. THE Debt_Detector SHALL respect .gitignore patterns using pathspec library
7. THE Debt_Detector SHALL output structured DebtItem objects with fields: id, category, description, location, priority, effort, risk, status
8. FOR ALL detected debt items, THE Debt_Detector SHALL assign confidence scores between 0.0 and 1.0

### Requirement 3: Categorize and Prioritize Debt

**User Story:** As a developer, I want technical debt items categorized and prioritized, so that I can focus on the most important issues first.

#### Acceptance Criteria

1. THE Debt_Detector SHALL categorize debt items into exactly four categories: Architecture, Code Quality, Tests, Performance
2. THE Debt_Detector SHALL assign priority levels: Critical, High, Medium, Low
3. WHEN assigning priority, THE Debt_Detector SHALL consider: risk level, effort required, and impact on maintainability
4. THE Debt_Detector SHALL assign effort estimates: Low (L), Medium (M), High (H)
5. THE Debt_Detector SHALL assign risk levels: Low (L), Medium (M), High (H)
6. THE technical-debt.md file SHALL list debt items sorted by priority within each category

### Requirement 4: Track Debt Resolution Status

**User Story:** As a developer, I want to track which debt items have been resolved, so that I can see progress on code quality improvements.

#### Acceptance Criteria

1. THE technical-debt.md file SHALL include status field for each debt item: Active, In Progress, Resolved, Deferred
2. WHEN running update workflow, THE Debt_Detector SHALL re-analyze code to detect resolved debt items
3. WHEN a previously detected debt item is no longer present, THE Update_Workflow SHALL move it to Resolved Debt Items section
4. THE Update_Workflow SHALL preserve manually added debt items that are not auto-detected
5. THE Update_Workflow SHALL preserve user edits to debt item descriptions and priorities

### Requirement 5: Integrate with Existing Workflows

**User Story:** As a developer, I want technical debt detection integrated into existing HiveForge workflows, so that I don't need to learn new commands.

#### Acceptance Criteria

1. WHEN running hiveforge steering init, THE Init_Workflow SHALL generate technical-debt.md alongside other 8 steering files
2. WHEN running hiveforge steering update, THE Update_Workflow SHALL refresh technical-debt.md with newly detected debt
3. WHEN running hiveforge steering validate, THE Validate_Workflow SHALL check technical-debt.md for completeness and structure
4. THE Init_Workflow SHALL include technical-debt.md in atomic transaction (all 9 files written or none)
5. THE Update_Workflow SHALL detect drift between technical-debt.md and current codebase state

### Requirement 6: Provide CLI and MCP Interfaces

**User Story:** As a developer, I want to access technical debt tracking through both CLI and KIRO IDE, so that I can use it in my preferred environment.

#### Acceptance Criteria

1. THE CLI_Interface SHALL support hiveforge steering init with technical debt detection enabled by default
2. THE CLI_Interface SHALL support --skip-debt-detection flag to disable technical debt analysis
3. THE MCP_Power SHALL expose init_steering tool that generates technical-debt.md
4. THE MCP_Power SHALL expose update_steering tool that refreshes technical-debt.md
5. THE MCP_Power SHALL include technical debt summary in tool response metadata

### Requirement 7: Respect Engineering Preferences

**User Story:** As a developer, I want technical debt detection to align with my team's engineering standards, so that flagged issues match our priorities.

#### Acceptance Criteria

1. THE Debt_Detector SHALL read engineering preferences from .kiro/steering/conventions.md if present
2. WHEN conventions.md specifies DRY preference, THE Debt_Detector SHALL aggressively flag code duplication
3. WHEN conventions.md specifies testing preference, THE Debt_Detector SHALL flag missing test coverage as high priority
4. WHEN conventions.md specifies clarity preference, THE Debt_Detector SHALL flag complex or clever code
5. THE Debt_Detector SHALL use default preferences when conventions.md is absent or incomplete

### Requirement 8: Generate Actionable Recommendations

**User Story:** As a developer, I want technical debt items to include actionable recommendations, so that I know how to resolve them.

#### Acceptance Criteria

1. THE Debt_Detector SHALL generate at least two resolution options for each debt item
2. THE first option SHALL be the recommended approach with justification
3. THE second option SHALL be an alternative approach with trade-offs
4. WHEN appropriate, THE Debt_Detector SHALL include a "Do Nothing" option with risks of status quo
5. THE recommendations SHALL reference specific file paths and line numbers

### Requirement 9: Maintain Consistency with Existing Steering Files

**User Story:** As a developer, I want technical-debt.md to reference information from other steering files, so that debt tracking is consistent with project standards.

#### Acceptance Criteria

1. WHEN generating technical-debt.md, THE Steering_Assistant SHALL include context from conventions.md, qa-standards.md, and architecture.md
2. THE Debt_Detector SHALL flag violations of conventions defined in conventions.md
3. THE Debt_Detector SHALL flag test gaps based on testing strategy in qa-standards.md
4. THE Debt_Detector SHALL flag architecture smells based on patterns in architecture.md
5. THE technical-debt.md file SHALL cross-reference related steering files using markdown links

### Requirement 10: Support Incremental Debt Tracking

**User Story:** As a developer, I want to track technical debt over time, so that I can measure code quality trends.

#### Acceptance Criteria

1. THE technical-debt.md file SHALL include Debt Metrics section with: total active items, items by category, items by priority
2. WHEN running update workflow, THE Update_Workflow SHALL preserve historical resolved items
3. THE technical-debt.md file SHALL include timestamp of last update
4. THE Debt_Detector SHALL detect new debt items introduced since last update
5. THE Update_Workflow SHALL highlight newly introduced debt in update summary

### Requirement 11: Handle Edge Cases Gracefully

**User Story:** As a developer, I want technical debt detection to handle edge cases without failing, so that the workflow remains reliable.

#### Acceptance Criteria

1. WHEN code analysis fails, THE Init_Workflow SHALL generate technical-debt.md with placeholder content and continue
2. WHEN Debt_Detector encounters unparseable files, THE Debt_Detector SHALL skip them and log warnings
3. WHEN LLM_Provider is unavailable, THE Steering_Assistant SHALL generate technical-debt.md with [INFERRED] markers
4. WHEN codebase has zero detected debt, THE technical-debt.md file SHALL state "No technical debt detected" in Overview
5. WHEN update workflow detects conflicts in technical-debt.md, THE Update_Workflow SHALL preserve user edits and append new items

### Requirement 12: Optimize Performance for Large Codebases

**User Story:** As a developer, I want technical debt detection to complete in reasonable time for large codebases, so that I don't wait excessively for results.

#### Acceptance Criteria

1. THE Debt_Detector SHALL complete analysis in under 30 seconds for codebases with fewer than 1,000 files
2. THE Debt_Detector SHALL complete analysis in under 2 minutes for codebases with 1,000-10,000 files
3. WHEN analyzing codebases larger than 10,000 files, THE Debt_Detector SHALL use sampling strategy and complete in under 5 minutes
4. THE Debt_Detector SHALL cache analysis results in .kiro/.cache/debt_analysis.json
5. THE Update_Workflow SHALL use cached results when codebase has not changed since last analysis
