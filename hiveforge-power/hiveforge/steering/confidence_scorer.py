"""
Confidence scoring for the Steering Assistant v02.

This module provides the ConfidenceScorer class for calculating and managing
confidence scores for generated content.
"""

from typing import Dict, List, Optional

from .models import ConfidenceScore, Evidence, ConfidenceLevel


class ConfidenceScorer:
    """Calculates and manages confidence scores for generated content."""
    
    # Evidence strength values
    EVIDENCE_STRENGTH = {
        "ARTIFACT": 0.95,      # Direct extraction from artifacts
        "CODE_ANALYSIS": 0.90, # Direct extraction from code analysis
        "INFERENCE": 0.70,     # Reasonable inference from context
        "USER": 0.85,          # User-provided information
    }
    
    def __init__(self, conservative_threshold: float = 0.7):
        """
        Initialize the ConfidenceScorer.
        
        Args:
            conservative_threshold: Threshold for MEDIUM confidence (default: 0.7)
        """
        self.conservative_threshold = conservative_threshold
    
    def calculate_confidence(
        self,
        content: str,
        evidence: List[Evidence],
        is_placeholder: bool = False,
        is_inferred: bool = False,
    ) -> float:
        """
        Calculate confidence score based on evidence strength.
        
        Args:
            content: The generated content
            evidence: List of evidence supporting the content
            is_placeholder: Whether content contains placeholders
            is_inferred: Whether content was inferred
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not evidence:
            # No evidence - use conservative defaults
            if is_placeholder:
                return 0.3
            if is_inferred:
                return 0.5
            return 0.4
        
        # Calculate average evidence strength
        total_strength = sum(e.strength for e in evidence)
        avg_strength = total_strength / len(evidence)
        
        # Adjust based on content characteristics
        confidence = avg_strength
        
        # Reduce confidence for placeholders
        if is_placeholder:
            confidence = min(confidence - 0.3, 0.5)
        
        # Reduce confidence for inferences
        if is_inferred:
            confidence = min(confidence - 0.1, 0.8)
        
        # Ensure confidence is in valid range
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
    
    def get_level(self, score: float) -> ConfidenceLevel:
        """
        Convert numeric score to HIGH/MEDIUM/LOW level.
        
        Args:
            score: Confidence score between 0.0 and 1.0
            
        Returns:
            ConfidenceLevel enum value
        """
        if score >= 0.9:
            return ConfidenceLevel.HIGH
        elif score >= self.conservative_threshold:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def calibrate(
        self,
        predicted: List[float],
        actual: List[bool],
    ) -> Dict[str, any]:
        """
        Calibrate confidence scores against actual correctness.
        
        Args:
            predicted: List of predicted confidence scores
            actual: List of actual correctness (True/False)
            
        Returns:
            Calibration result dictionary
        """
        if len(predicted) != len(actual):
            raise ValueError("Predicted and actual lists must have same length")
        
        if not predicted:
            return {
                "calibration_status": "uncalibrated",
                "calibration_data": {},
            }
        
        # Calculate calibration metrics
        correct_high = 0
        correct_medium = 0
        correct_low = 0
        total_high = 0
        total_medium = 0
        total_low = 0
        
        for pred, act in zip(predicted, actual):
            level = self.get_level(pred)
            
            if level == ConfidenceLevel.HIGH:
                total_high += 1
                if act:
                    correct_high += 1
            elif level == ConfidenceLevel.MEDIUM:
                total_medium += 1
                if act:
                    correct_medium += 1
            else:
                total_low += 1
                if act:
                    correct_low += 1
        
        # Calculate accuracy per level
        high_accuracy = correct_high / total_high if total_high > 0 else 0.0
        medium_accuracy = correct_medium / total_medium if total_medium > 0 else 0.0
        low_accuracy = correct_low / total_low if total_low > 0 else 0.0
        
        return {
            "calibration_status": "calibrated",
            "calibration_data": {
                "high_accuracy": high_accuracy,
                "medium_accuracy": medium_accuracy,
                "low_accuracy": low_accuracy,
                "total_samples": len(predicted),
            },
        }
    
    def aggregate_section_confidences(
        self,
        section_confidences: Dict[str, float],
    ) -> float:
        """
        Calculate overall file confidence from section confidences.
        
        Args:
            section_confidences: Dictionary mapping section names to confidence scores
            
        Returns:
            Overall file confidence score
        """
        if not section_confidences:
            return 0.0
        
        # Use minimum confidence as overall score (conservative approach)
        # This ensures that any low-confidence section drags down the overall score
        min_confidence = min(section_confidences.values())
        
        # Also calculate average for reference
        avg_confidence = sum(section_confidences.values()) / len(section_confidences)
        
        # Use weighted average with emphasis on minimum
        # This gives more weight to the weakest section
        overall = (min_confidence + avg_confidence) / 2
        
        return overall
    
    def create_evidence(
        self,
        source: str,
        description: str,
        strength: Optional[float] = None,
        metadata: Optional[Dict[str, any]] = None,
    ) -> Evidence:
        """
        Create an Evidence object.
        
        Args:
            source: Source of evidence (ARTIFACT, CODE_ANALYSIS, INFERENCE, USER)
            description: Description of the evidence
            strength: Evidence strength (0.0-1.0). If None, uses default for source.
            metadata: Optional metadata
            
        Returns:
            Evidence object
        """
        if strength is None:
            strength = self.EVIDENCE_STRENGTH.get(source, 0.5)
        
        return Evidence(
            source=source,
            strength=strength,
            description=description,
            metadata=metadata or {},
        )
    
    def score_content(
        self,
        content: str,
        source: str = "ARTIFACT",
        description: str = "",
        metadata: Optional[Dict[str, any]] = None,
    ) -> ConfidenceScore:
        """
        Score content with a single piece of evidence.
        
        Args:
            content: The content to score
            source: Source of evidence
            description: Description of the evidence
            metadata: Optional metadata
            
        Returns:
            ConfidenceScore object
        """
        evidence = self.create_evidence(source, description, metadata=metadata)
        confidence = self.calculate_confidence(content, [evidence])
        level = self.get_level(confidence)
        
        return ConfidenceScore(
            value=confidence,
            level=level,
            evidence=[evidence],
        )
