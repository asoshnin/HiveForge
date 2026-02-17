"""
Steering Assistant module for HiveForge.

This module provides intelligent automation for creating and maintaining
steering files throughout a project's lifecycle.
"""

from .models import (
    # Document models
    ParsedDocument,
    
    # Template models
    Template,
    TemplateSection,
    ValidationRule,
    
    # Code analysis models
    LanguageInfo,
    Dependency,
    TechStackInfo,
    ArchitectureInfo,
    ConventionsInfo,
    CodeAnalysisResult,
    
    # Gap analysis models
    Question,
    GapAnalysisResult,
    
    # Conflict models
    Conflict,
    Customization,
    
    # Diff models
    DiffLine,
    DiffHunk,
    FileDiff,
    
    # Validation models
    ValidationIssue,
    ValidationReport,
    
    # Workflow models
    WorkflowState,
    SteeringConfig,
    
    # Cache models
    CachedResponse,
)

from .response_cache import ResponseCache

__version__ = "1.0.0"

__all__ = [
    # Document models
    "ParsedDocument",
    
    # Template models
    "Template",
    "TemplateSection",
    "ValidationRule",
    
    # Code analysis models
    "LanguageInfo",
    "Dependency",
    "TechStackInfo",
    "ArchitectureInfo",
    "ConventionsInfo",
    "CodeAnalysisResult",
    
    # Gap analysis models
    "Question",
    "GapAnalysisResult",
    
    # Conflict models
    "Conflict",
    "Customization",
    
    # Diff models
    "DiffLine",
    "DiffHunk",
    "FileDiff",
    
    # Validation models
    "ValidationIssue",
    "ValidationReport",
    
    # Workflow models
    "WorkflowState",
    "SteeringConfig",
    
    # Cache models
    "CachedResponse",
    "ResponseCache",
]
