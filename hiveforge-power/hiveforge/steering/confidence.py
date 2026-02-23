"""
Confidence Calculator for Steering File Generation.

This module provides confidence scoring for generated steering files based on
the sources of information used (source documents, code analysis, LLM inference).

The confidence scoring system helps users understand which content is grounded
in actual project artifacts vs. inferred by the LLM, enabling them to identify
sections that need verification.

Weight Rationale:
- Source documents: 1.0 - Highest confidence. User-provided design documents
  are the ground truth for project vision, requirements, and business context.
- Code analysis: 0.8 - High confidence. Code is factual and accurate for
  technical details (tech stack, architecture patterns, conventions), but
  doesn't capture business intent or future plans.
- LLM inference: 0.3 - Low confidence. Inferred content is educated guessing
  based on patterns. Useful for filling gaps but requires user verification.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class ConfidenceScore:
    """
    Confidence score for generated content.
    
    Attributes:
        overall: Overall confidence score (0.0 to 1.0)
        level: Human-readable confidence level ("high", "medium", "low")
        sources: Dictionary mapping source type to contribution percentage
        inferred_sections: List of section names that were inferred by LLM
    """
    
    overall: float  # 0.0 to 1.0
    level: str  # "high", "medium", "low"
    sources: Dict[str, float]  # source -> contribution percentage
    inferred_sections: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert confidence score to dictionary for serialization.
        
        Returns:
            Dictionary representation of the confidence score
        """
        return {
            "overall": self.overall,
            "level": self.level,
            "sources": self.sources,
            "inferred_sections": self.inferred_sections
        }


class ConfidenceCalculator:
    """
    Calculates confidence scores for generated steering file content.
    
    The calculator uses a weighted scoring system based on the source of
    information:
    - Source documents: 1.0 weight (ground truth)
    - Code analysis: 0.8 weight (factual but incomplete)
    - LLM inference: 0.3 weight (speculative, needs verification)
    
    These weights are fixed in v2.2.0 for simplicity. Configurable weights
    may be added in v2.3.0 based on user feedback.
    """
    
    # Confidence weights for different sources
    WEIGHT_SOURCE_DOCUMENTS = 1.0
    WEIGHT_CODE_ANALYSIS = 0.8
    WEIGHT_LLM_INFERENCE = 0.3
    
    # File importance weights for overall confidence calculation
    FILE_WEIGHTS = {
        "project-vision.md": 1.5,
        "tech-stack.md": 1.2,
        "architecture.md": 1.2,
        "conventions.md": 1.0,
        "db-standards.md": 0.8,
        "api-standards.md": 0.8,
        "ui-standards.md": 0.8,
        "qa-standards.md": 0.8,
    }
    
    def calculate_file_confidence(
        self,
        file_name: str,
        sources: Dict[str, List[str]],
        content: str
    ) -> ConfidenceScore:
        """
        Calculate confidence for a single steering file.
        
        The confidence is calculated based on the percentage of sections
        derived from each source type, weighted by the source's reliability.
        
        Args:
            file_name: Name of the steering file (e.g., "project-vision.md")
            sources: Dictionary mapping source type to list of section names
                     Expected keys: "documents", "code_analysis", "inferred"
            content: Generated file content (for validation)
        
        Returns:
            ConfidenceScore with overall score, level, and breakdown
            
        Example:
            >>> calculator = ConfidenceCalculator()
            >>> sources = {
            ...     "documents": ["Problem Statement", "Target Users"],
            ...     "code_analysis": ["Tech Stack"],
            ...     "inferred": ["Success Metrics"]
            ... }
            >>> score = calculator.calculate_file_confidence(
            ...     "project-vision.md", sources, content
            ... )
            >>> print(f"{score.level}: {score.overall:.2f}")
            medium: 0.65
        """
        # Extract section lists from sources
        doc_sections = sources.get("documents", [])
        code_sections = sources.get("code_analysis", [])
        inferred_sections = sources.get("inferred", [])
        
        total_sections = len(doc_sections) + len(code_sections) + len(inferred_sections)
        
        # Handle edge case: no sections tracked
        if total_sections == 0:
            return ConfidenceScore(
                overall=0.0,
                level="low",
                sources={},
                inferred_sections=[]
            )
        
        # Calculate weighted contributions
        doc_contribution = len(doc_sections) / total_sections
        code_contribution = len(code_sections) / total_sections
        inferred_contribution = len(inferred_sections) / total_sections
        
        # Apply weights to get overall score
        doc_weight = doc_contribution * self.WEIGHT_SOURCE_DOCUMENTS
        code_weight = code_contribution * self.WEIGHT_CODE_ANALYSIS
        inferred_weight = inferred_contribution * self.WEIGHT_LLM_INFERENCE
        
        overall = doc_weight + code_weight + inferred_weight
        
        # Determine confidence level
        if overall >= 0.8:
            level = "high"
        elif overall >= 0.5:
            level = "medium"
        else:
            level = "low"
        
        return ConfidenceScore(
            overall=overall,
            level=level,
            sources={
                "documents": doc_weight,
                "code_analysis": code_weight,
                "inferred": inferred_weight
            },
            inferred_sections=inferred_sections
        )
    
    def calculate_overall_confidence(
        self,
        file_scores: Dict[str, ConfidenceScore]
    ) -> ConfidenceScore:
        """
        Calculate overall workflow confidence from individual file scores.
        
        The overall confidence is a weighted average of file scores, where
        more important files (like project-vision.md) have higher weights.
        
        Args:
            file_scores: Dictionary mapping file names to their confidence scores
        
        Returns:
            ConfidenceScore representing overall workflow confidence
            
        Example:
            >>> calculator = ConfidenceCalculator()
            >>> file_scores = {
            ...     "project-vision.md": ConfidenceScore(0.8, "high", {}, []),
            ...     "tech-stack.md": ConfidenceScore(0.6, "medium", {}, []),
            ...     "conventions.md": ConfidenceScore(0.4, "low", {}, ["Naming"])
            ... }
            >>> overall = calculator.calculate_overall_confidence(file_scores)
            >>> print(f"{overall.level}: {overall.overall:.2f}")
            medium: 0.65
        """
        if not file_scores:
            return ConfidenceScore(
                overall=0.0,
                level="low",
                sources={},
                inferred_sections=[]
            )
        
        weighted_sum = 0.0
        weight_total = 0.0
        all_inferred = []
        
        for file_name, score in file_scores.items():
            # Get weight for this file (default to 1.0 if not specified)
            weight = self.FILE_WEIGHTS.get(file_name, 1.0)
            weighted_sum += score.overall * weight
            weight_total += weight
            all_inferred.extend(score.inferred_sections)
        
        overall = weighted_sum / weight_total if weight_total > 0 else 0.0
        
        # Determine overall confidence level
        if overall >= 0.8:
            level = "high"
        elif overall >= 0.5:
            level = "medium"
        else:
            level = "low"
        
        return ConfidenceScore(
            overall=overall,
            level=level,
            sources={},  # Aggregated, not per-source
            inferred_sections=all_inferred
        )
