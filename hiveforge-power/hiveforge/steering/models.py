"""
Data models for the Steering Assistant feature.

This module defines all data structures used throughout the steering assistant
system, including parsed documents, templates, workflow state, and analysis results.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .feature_flags import FeatureFlagConfig


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
class MCPToolInfo:
    """Information about an MCP tool."""
    
    name: str
    docstring: str
    parameters: List[str] = field(default_factory=list)


@dataclass
class CLICommandInfo:
    """Information about a CLI command."""
    
    name: str
    help_text: str
    parameters: List[str] = field(default_factory=list)


@dataclass
class PublicAPIInfo:
    """Extracted public API information from codebase."""
    
    mcp_tools: List[MCPToolInfo] = field(default_factory=list)
    cli_commands: List[CLICommandInfo] = field(default_factory=list)
    public_classes: List[str] = field(default_factory=list)


@dataclass
class CodeAnalysisResult:
    """Complete result of code analysis for a project."""
    
    languages: List[LanguageInfo] = field(default_factory=list)
    tech_stack: TechStackInfo = field(default_factory=TechStackInfo)
    architecture: ArchitectureInfo = field(default_factory=ArchitectureInfo)
    conventions: ConventionsInfo = field(default_factory=ConventionsInfo)
    documentation: List[ParsedDocument] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    classification: Optional[Dict[str, Any]] = None  # P1-2: Project type classification
    
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


@dataclass
class NamingConventions:
    """
    Naming convention patterns extracted from codebase.
    
    Requirements: 2.1
    """
    variables: str = ""       # e.g. "snake_case"
    classes: str = ""         # e.g. "PascalCase"
    constants: str = ""       # e.g. "UPPER_SNAKE_CASE"
    functions: str = ""       # e.g. "snake_case"


@dataclass
class CodeAnalysisFacts:
    """
    JSON-serializable structured output of CodeAnalyzer.
    Replaces to_summary() prose as the primary output format.
    Serializes to ≤2,000 tokens when injected into an LLM prompt.
    
    Requirements: 2.1, 2.2, 2.5
    """
    primary_language: str
    frameworks: List[str]
    dependencies: List[Dependency]          # reuses existing Dependency model
    architecture_pattern: str
    has_tests: bool
    test_framework: Optional[str]
    api_type: Optional[str]                 # "REST", "MCP", "CLI", None
    database: Optional[str]
    entry_points: List[str]
    naming_conventions: NamingConventions
    directory_structure: str                # compact tree representation

    def to_json_dict(self) -> Dict[str, Any]:
        """
        Returns JSON-serializable dict for LLM injection.
        
        Guarantees output serializes to ≤2,000 tokens by truncating lists
        if necessary. Truncation priority: dependencies → entry_points → frameworks.
        
        Returns:
            Dictionary representation suitable for JSON serialization
            
        Requirements: 2.2, 2.5
        """
        import json
        
        # Helper to estimate tokens (1 token ≈ 4 characters)
        def estimate_tokens(obj: Dict[str, Any]) -> int:
            return len(json.dumps(obj)) // 4
        
        # Start with full data
        result = {
            "primary_language": self.primary_language,
            "frameworks": self.frameworks[:],  # Copy to avoid modifying original
            "dependencies": [
                {"name": d.name, "version": d.version, "type": d.dependency_type}
                for d in self.dependencies
            ],
            "architecture_pattern": self.architecture_pattern,
            "has_tests": self.has_tests,
            "test_framework": self.test_framework,
            "api_type": self.api_type,
            "database": self.database,
            "entry_points": self.entry_points[:],  # Copy to avoid modifying original
            "naming_conventions": {
                "variables": self.naming_conventions.variables,
                "classes": self.naming_conventions.classes,
                "constants": self.naming_conventions.constants,
                "functions": self.naming_conventions.functions,
            },
            "directory_structure": self.directory_structure,
        }
        
        # Check if within budget
        token_count = estimate_tokens(result)
        if token_count <= 2000:
            return result
        
        # Truncate dependencies first (most verbose)
        if len(result["dependencies"]) > 20:
            result["dependencies"] = result["dependencies"][:20]
            token_count = estimate_tokens(result)
            if token_count <= 2000:
                return result
        
        if len(result["dependencies"]) > 10:
            result["dependencies"] = result["dependencies"][:10]
            token_count = estimate_tokens(result)
            if token_count <= 2000:
                return result
        
        # Truncate entry points
        if len(result["entry_points"]) > 10:
            result["entry_points"] = result["entry_points"][:10]
            token_count = estimate_tokens(result)
            if token_count <= 2000:
                return result
        
        if len(result["entry_points"]) > 5:
            result["entry_points"] = result["entry_points"][:5]
            token_count = estimate_tokens(result)
            if token_count <= 2000:
                return result
        
        # Truncate frameworks
        if len(result["frameworks"]) > 5:
            result["frameworks"] = result["frameworks"][:5]
            token_count = estimate_tokens(result)
            if token_count <= 2000:
                return result
        
        # Final fallback: truncate directory structure
        if len(result["directory_structure"]) > 100:
            result["directory_structure"] = result["directory_structure"][:100] + "..."
        
        return result


# ============================================================================
# LLM Generation Models
# ============================================================================

# Type alias for use case determination
UseCase = Literal[
    "new_from_docs",
    "reverse_engineer",
    "drift_correction",
    "error_recovery",
    "pivot",
    "update",
]


@dataclass
class GenerationContext:
    """
    Token-budgeted inputs for a single template's LLM prompt.
    Produced by ContextAssembler.
    
    Requirements: 4.6
    """
    template_name: str
    use_case: UseCase
    source_docs: List[ParsedDocument]                   # filtered to template-relevant content
    code_facts: "CodeAnalysisFacts"
    existing_steering: Dict[str, str]                   # truncated to budget
    previously_generated_summaries: Dict[str, str]      # rolling summaries
    delta: Optional["DeltaReport"]
    user_intent: Optional[str]
    debt_facts: Optional["DebtAnalysisResult"] = None   # NEW: structured debt analysis


@dataclass
class DeltaReport:
    """
    Three-way structural diff produced by DeltaAnalyzer.
    Structural drift only: technology mismatches, dependency changes.
    
    Requirements: 7.2
    """
    doc_vs_code: List[str]          # divergences between design docs and codebase
    steering_vs_code: List[str]     # drifts between steering files and codebase
    steering_vs_docs: List[str]     # conflicts between steering files and design docs
    missing_in_all: List[str]       # gaps absent from all three sources


@dataclass
class GenerationResult:
    """
    Output of SteeringFileGenerator.generate_all_files().
    
    Requirements: 5.5
    """
    success: bool
    files_written: List[str]        # empty on failure
    validation_errors: List[str]    # populated on failure


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
# Draft Models
# ============================================================================

@dataclass
class DraftFile:
    """Single file in draft state awaiting review."""
    
    filename: str
    content: str
    confidence: float
    placeholder_count: int
    preview: str  # First 300 chars
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            'filename': self.filename,
            'confidence': self.confidence,
            'placeholder_count': self.placeholder_count,
            'preview': self.preview,
        }


@dataclass
class DraftState:
    """State of generated files awaiting review."""
    
    files: List[DraftFile]
    created_at: Any = field(default_factory=lambda: None)  # datetime, avoid import
    is_approved: bool = False
    
    def summary(self) -> str:
        """Generate summary for display."""
        lines = ["# Draft Summary\n"]
        
        for file in self.files:
            lines.append(f"## {file.filename}")
            lines.append(f"- Confidence: {file.confidence:.1%}")
            lines.append(f"- Placeholders: {file.placeholder_count}")
            lines.append(f"- Preview: {file.preview}...\n")
        
        return '\n'.join(lines)


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
    draft: Optional[DraftState] = None  # NEW: stores draft for MCP mode review
    last_backup_dir: Optional[Path] = None  # NEW: stores last backup directory for rollback
    debt_analysis: Optional["DebtAnalysisResult"] = None  # NEW: debt detection results


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
    feature_flags: Optional["FeatureFlagConfig"] = None
    incremental: bool = False
    preview: bool = False
    skip_debt_detection: bool = False  # NEW: disable DebtDetector when True


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


# ============================================================================
# Drift Detection Models
# ============================================================================

class DriftCategory(Enum):
    """Categories of drift between steering files and codebase."""
    LANGUAGE_VERSION = "language_version"
    NEW_DEPENDENCY = "new_dependency"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    CONVENTION_MISMATCH = "convention_mismatch"


@dataclass
class DriftItem:
    """Single drift detection result."""
    
    category: DriftCategory
    description: str
    confidence: float  # 0.0-1.0
    suggested_action: str


@dataclass
class DriftReport:
    """Report of all detected drift."""
    
    items: List[DriftItem] = field(default_factory=list)
    detected_at: Any = field(default_factory=lambda: None)  # datetime, avoid import
    
    def has_drift(self) -> bool:
        """Check if any drift detected."""
        return len(self.items) > 0
    
    def by_severity(self) -> List[DriftItem]:
        """Return items sorted by confidence (highest first)."""
        return sorted(self.items, key=lambda x: x.confidence, reverse=True)


# ============================================================================
# Feature Flag Models
# ============================================================================

class ConfidenceLevel(Enum):
    """Confidence score levels for generated content."""
    HIGH = "HIGH"      # ≥0.9 - Direct extraction or strong evidence
    MEDIUM = "MEDIUM"  # 0.7-0.9 - Reasonable inference
    LOW = "LOW"        # <0.7 - Generic placeholder or weak evidence


@dataclass
class Evidence:
    """Evidence supporting a confidence score."""
    
    source: Literal["ARTIFACT", "CODE_ANALYSIS", "INFERENCE", "USER"]
    strength: float  # 0.0-1.0
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfidenceScore:
    """Represents a confidence score with calibration data."""
    
    value: float  # 0.0-1.0
    level: ConfidenceLevel
    evidence: List[Evidence] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and set confidence level based on value."""
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(f"Confidence value must be between 0.0 and 1.0, got {self.value}")
        
        if self.value >= 0.9:
            self.level = ConfidenceLevel.HIGH
        elif self.value >= 0.7:
            self.level = ConfidenceLevel.MEDIUM
        else:
            self.level = ConfidenceLevel.LOW


@dataclass
class FeatureFlagConfig:
    """Configuration for feature flags controlling autonomous generation."""
    
    use_autonomous_generation: bool = False
    confidence_threshold: float = 0.7  # MEDIUM threshold
    max_tokens: Optional[int] = None
    discovery_paths: List[str] = field(default_factory=list)
    preserve_all: bool = False
    telemetry_off: bool = False
    max_discovery_files: int = 1000
    max_file_size_mb: int = 10
    conservative_inference: bool = False
    interactive: bool = False
    
    def validate(self) -> List[str]:
        """
        Validate feature flag combinations and ranges.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate confidence_threshold range
        if not (0.0 <= self.confidence_threshold <= 1.0):
            errors.append(
                f"confidence_threshold must be between 0.0 and 1.0, got {self.confidence_threshold}"
            )
        
        # Validate max_discovery_files
        if self.max_discovery_files < 1:
            errors.append(
                f"max_discovery_files must be at least 1, got {self.max_discovery_files}"
            )
        
        # Validate max_file_size_mb
        if self.max_file_size_mb < 1:
            errors.append(
                f"max_file_size_mb must be at least 1, got {self.max_file_size_mb}"
            )
        
        # Warn about high confidence threshold
        if self.confidence_threshold > 0.95:
            errors.append(
                f"confidence_threshold is very high ({self.confidence_threshold}), "
                "most sections may trigger fallback to question workflow"
            )
        
        return errors
    
    def get_workflow_type(self) -> Literal["AUTONOMOUS", "FALLBACK"]:
        """
        Determine which workflow type to use based on feature flags.
        
        Returns:
            "AUTONOMOUS" if autonomous generation is enabled, "FALLBACK" otherwise
        """
        if self.use_autonomous_generation and not self.interactive:
            return "AUTONOMOUS"
        return "FALLBACK"
    
    def should_fallback(self, confidence: float) -> bool:
        """
        Check if fallback should be triggered based on confidence.
        
        Args:
            confidence: The confidence score to check
            
        Returns:
            True if fallback should be triggered
        """
        return confidence < self.confidence_threshold
    
    def warn_high_threshold(self) -> bool:
        """
        Check if confidence threshold is high enough to warrant a warning.
        
        Returns:
            True if threshold > 0.95
        """
        return self.confidence_threshold > 0.95


# ============================================================================
# Technical Debt Models
# ============================================================================

class DebtCategory(Enum):
    """Categories of technical debt items."""
    ARCHITECTURE = "Architecture"
    CODE_QUALITY = "Code Quality"
    TESTS = "Tests"
    PERFORMANCE = "Performance"


class DebtPriority(Enum):
    """Priority levels for technical debt items."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DebtStatus(Enum):
    """Status values for technical debt items."""
    ACTIVE = "Active"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    DEFERRED = "Deferred"


class DebtEffort(Enum):
    """Effort estimates for resolving debt items."""
    LOW = "L"
    MEDIUM = "M"
    HIGH = "H"


class DebtRisk(Enum):
    """Risk levels for technical debt items."""
    LOW = "L"
    MEDIUM = "M"
    HIGH = "H"


@dataclass
class DebtRecommendation:
    """One resolution option for a debt item."""

    title: str           # e.g. "Extract shared helper"
    description: str     # actionable steps
    trade_offs: str      # risks / downsides
    is_recommended: bool = False


@dataclass
class DebtItem:
    """
    A single tracked technical debt issue.

    id is a stable hash of (category, file_path, line_number) so it
    survives re-runs as long as the code location is unchanged.

    Requirements: 2.7, 2.8, 3.1, 3.2, 3.4, 3.5, 4.1
    """

    id: str                                                   # sha256[:12] of (category + location)
    category: DebtCategory
    description: str
    location: str                                             # "path/to/file.py:42" or "path/to/file.py"
    priority: DebtPriority
    effort: DebtEffort
    risk: DebtRisk
    status: DebtStatus
    confidence: float                                         # 0.0–1.0
    recommendations: List[DebtRecommendation] = field(default_factory=list)
    detected_at: Optional[str] = None                        # ISO-8601 timestamp
    resolved_at: Optional[str] = None                        # ISO-8601 timestamp


@dataclass
class DebtMetrics:
    """Aggregate metrics for a debt analysis result.

    Requirements: 3.1, 3.2, 10.1
    """

    total_active: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)   # DebtCategory.value → int
    by_priority: Dict[str, int] = field(default_factory=dict)   # DebtPriority.value → int
    last_updated: Optional[str] = None                          # ISO-8601 timestamp


@dataclass
class DebtAnalysisResult:
    """Complete output of DebtDetector.detect().

    Requirements: 2.5, 2.6, 3.3, 12.1, 12.2, 12.3, 12.4, 12.5
    """

    items: List[DebtItem] = field(default_factory=list)
    metrics: DebtMetrics = field(default_factory=DebtMetrics)
    sampled: bool = False          # True when sampling was applied (>10k files)
    analysis_time_s: float = 0.0

    def to_json_dict(self) -> Dict[str, Any]:
        """JSON-serializable dict for LLM context injection (≤1000 tokens).

        Requirements: 2.5
        """
        import json

        def _item_to_dict(item: DebtItem) -> Dict[str, Any]:
            return {
                "id": item.id,
                "category": item.category.value,
                "description": item.description[:120],   # truncate for token budget
                "location": item.location,
                "priority": item.priority.value,
                "effort": item.effort.value,
                "risk": item.risk.value,
                "status": item.status.value,
                "confidence": round(item.confidence, 2),
            }

        active = self.active_items()
        # Limit to 20 items to stay within 1000-token budget
        items_subset = active[:20]

        result: Dict[str, Any] = {
            "sampled": self.sampled,
            "analysis_time_s": round(self.analysis_time_s, 2),
            "metrics": {
                "total_active": self.metrics.total_active,
                "by_category": self.metrics.by_category,
                "by_priority": self.metrics.by_priority,
                "last_updated": self.metrics.last_updated,
            },
            "active_items": [_item_to_dict(i) for i in items_subset],
        }

        # Verify token budget (rough: 1 token ≈ 4 chars)
        serialized = json.dumps(result)
        if len(serialized) > 4000:  # ~1000 tokens
            # Reduce items further
            result["active_items"] = result["active_items"][:10]

        return result

    def active_items(self) -> List[DebtItem]:
        """Return items that are not resolved."""
        return [i for i in self.items if i.status != DebtStatus.RESOLVED]

    def resolved_items(self) -> List[DebtItem]:
        """Return items that have been resolved."""
        return [i for i in self.items if i.status == DebtStatus.RESOLVED]


# ============================================================================
# Exception Models
# ============================================================================

class LLMUnavailableError(Exception):
    """
    Raised when LLM provider is not available or configured.
    
    This exception is raised when:
    - No LLM provider is configured in CLI mode
    - LLM API credentials are missing or invalid
    - LLM service is unreachable after retries
    
    Requirements: 8.2, 8.3
    """
    pass
