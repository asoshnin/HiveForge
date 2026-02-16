"""
Data models for the Steering Assistant feature.

This module defines all data structures used throughout the steering assistant
system, including parsed documents, templates, workflow state, and analysis results.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


# ============================================================================
# Document Parsing Models
# ============================================================================

@dataclass
class ParsedDocument:
    """Represents a document that has been parsed from a source file."""
    
    file_path: Path
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    parse_errors: List[str] = field(default_factory=list)


# ============================================================================
# Template Models
# ============================================================================

@dataclass
class ValidationRule:
    """Defines a validation rule for a template section."""
    
    rule_type: str  # "required", "pattern", "length", etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


@dataclass
class TemplateSection:
    """Represents a section within a steering file template."""
    
    name: str
    required: bool
    placeholder_pattern: str
    validation_rules: List[ValidationRule] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class Template:
    """Defines the structure of a steering file template."""
    
    name: str
    file_name: str
    priority: int
    sections: List[TemplateSection]
    frontmatter: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Code Analysis Models
# ============================================================================

@dataclass
class LanguageInfo:
    """Information about a programming language detected in the codebase."""
    
    name: str
    version: Optional[str] = None
    file_count: int = 0
    line_count: int = 0
    percentage: float = 0.0


@dataclass
class Dependency:
    """Represents a project dependency."""
    
    name: str
    version: Optional[str] = None
    dependency_type: str = "runtime"  # "runtime", "dev", "peer", etc.


@dataclass
class TechStackInfo:
    """Information about the technology stack used in the project."""
    
    backend_framework: Optional[str] = None
    frontend_framework: Optional[str] = None
    database: Optional[str] = None
    cache: Optional[str] = None
    dependencies: List[Dependency] = field(default_factory=list)


@dataclass
class ArchitectureInfo:
    """Information about the project's architecture pattern."""
    
    pattern: str = "custom"  # "monolithic", "microservices", "layered", etc.
    directory_structure: Dict[str, str] = field(default_factory=dict)
    key_components: List[str] = field(default_factory=list)


@dataclass
class ConventionsInfo:
    """Information about coding conventions used in the project."""
    
    naming_style: Dict[str, str] = field(default_factory=dict)  # "variables": "snake_case", etc.
    formatting: Dict[str, Any] = field(default_factory=dict)
    documentation_style: str = ""
    test_framework: Optional[str] = None


@dataclass
class CodeAnalysisResult:
    """Complete result of code analysis for a project."""
    
    languages: List[LanguageInfo] = field(default_factory=list)
    tech_stack: TechStackInfo = field(default_factory=TechStackInfo)
    architecture: ArchitectureInfo = field(default_factory=ArchitectureInfo)
    conventions: ConventionsInfo = field(default_factory=ConventionsInfo)
    documentation: List[ParsedDocument] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    def to_summary(self, max_tokens: int = 2000) -> str:
        """
        Convert analysis results to a token-limited summary for LLM context.
        
        Args:
            max_tokens: Maximum number of tokens to include in summary
            
        Returns:
            Summarized string representation of analysis results
        """
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        summary_parts = []
        
        # Languages
        if self.languages:
            lang_summary = "Languages: " + ", ".join(
                f"{lang.name} {lang.version or ''} ({lang.percentage:.1f}%)"
                for lang in sorted(self.languages, key=lambda x: x.percentage, reverse=True)[:5]
            )
            summary_parts.append(lang_summary)
        
        # Tech Stack
        tech_parts = []
        if self.tech_stack.backend_framework:
            tech_parts.append(f"Backend: {self.tech_stack.backend_framework}")
        if self.tech_stack.frontend_framework:
            tech_parts.append(f"Frontend: {self.tech_stack.frontend_framework}")
        if self.tech_stack.database:
            tech_parts.append(f"Database: {self.tech_stack.database}")
        if self.tech_stack.cache:
            tech_parts.append(f"Cache: {self.tech_stack.cache}")
        if tech_parts:
            summary_parts.append("Tech Stack: " + ", ".join(tech_parts))
        
        # Architecture
        if self.architecture.pattern:
            arch_summary = f"Architecture: {self.architecture.pattern}"
            if self.architecture.key_components:
                arch_summary += f" (Components: {', '.join(self.architecture.key_components[:5])})"
            summary_parts.append(arch_summary)
        
        # Conventions
        if self.conventions.naming_style:
            conv_summary = "Conventions: " + ", ".join(
                f"{k}={v}" for k, v in list(self.conventions.naming_style.items())[:5]
            )
            summary_parts.append(conv_summary)
        
        # Join and truncate if needed
        full_summary = "\n".join(summary_parts)
        if len(full_summary) > max_chars:
            full_summary = full_summary[:max_chars] + "..."
        
        return full_summary


# ============================================================================
# Gap Analysis Models
# ============================================================================

@dataclass
class Question:
    """Represents a question to ask the user during gap analysis."""
    
    template_name: str
    section_name: str
    question_text: str
    context: str
    priority: int = 0


@dataclass
class GapAnalysisResult:
    """Result of gap analysis comparing knowledge base against templates."""
    
    complete_sections: Dict[str, List[str]] = field(default_factory=dict)  # template -> sections
    missing_sections: Dict[str, List[str]] = field(default_factory=dict)   # template -> sections
    ambiguous_sections: Dict[str, List[str]] = field(default_factory=dict) # template -> sections
    questions: List[Question] = field(default_factory=list)  # ordered by priority


# ============================================================================
# Conflict Resolution Models
# ============================================================================

@dataclass
class Conflict:
    """Represents a conflict between old and new information."""
    
    section: str
    old_value: str
    new_value: str
    explanation: str
    resolution_options: List[str] = field(default_factory=lambda: ["keep_old", "use_new", "merge"])


@dataclass
class Customization:
    """Represents a user customization in a steering file."""
    
    section: str
    original: str
    customized: str
    confidence: float = 0.0  # 0.0-1.0


# ============================================================================
# Diff Models
# ============================================================================

@dataclass
class DiffLine:
    """Represents a single line in a diff."""
    
    type: Literal["context", "addition", "deletion"]
    content: str


@dataclass
class DiffHunk:
    """Represents a hunk (section) of changes in a diff."""
    
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[DiffLine] = field(default_factory=list)


@dataclass
class FileDiff:
    """Represents the complete diff for a file."""
    
    file_name: str
    old_lines: List[str] = field(default_factory=list)
    new_lines: List[str] = field(default_factory=list)
    hunks: List[DiffHunk] = field(default_factory=list)


# ============================================================================
# Validation Models
# ============================================================================

@dataclass
class ValidationIssue:
    """Represents a validation issue found in a steering file."""
    
    severity: Literal["critical", "warning", "info"]
    file_name: str
    line_number: Optional[int] = None
    issue_type: str = ""
    message: str = ""
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """Complete validation report for steering files."""
    
    critical_issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    files_checked: int = 0
    overall_status: Literal["pass", "fail"] = "pass"
    llm_calls_made: int = 0  # Track LLM usage
    tokens_used: int = 0  # Track token usage


# ============================================================================
# Workflow Models
# ============================================================================

@dataclass
class WorkflowState:
    """Represents the state of a steering workflow (init, update, validate)."""
    
    workflow_type: Literal["init", "update", "validate"]
    staging_dir: Path
    steering_dir: Path
    parsed_documents: List[ParsedDocument] = field(default_factory=list)
    knowledge_base: Optional[Any] = None  # KnowledgeBase type (avoid circular import)
    code_analysis: Optional[CodeAnalysisResult] = None
    gap_analysis: Optional[GapAnalysisResult] = None
    gathered_info: Dict[str, Any] = field(default_factory=dict)
    conflicts: List[Conflict] = field(default_factory=list)
    validation_report: Optional[ValidationReport] = None


@dataclass
class SteeringConfig:
    """Configuration for steering operations."""
    
    research_enabled: bool = False
    skip_validation: bool = False
    interactive: bool = True
    strict_mode: bool = False
    backup_enabled: bool = True
    backup_dir: Path = field(default_factory=lambda: Path(".kiro/backups"))
    analyze_code: bool = False


# ============================================================================
# Response Cache Models
# ============================================================================

@dataclass
class CachedResponse:
    """Represents a cached LLM response."""
    
    question_hash: str
    response: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
