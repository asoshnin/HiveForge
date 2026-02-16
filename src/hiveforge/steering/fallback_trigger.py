"""
Fallback trigger for the Steering Assistant v02.

This module provides the FallbackTrigger class for determining when to fall back
to the question-asking workflow based on confidence, validation failures, and other factors.
"""

from typing import Dict, List, Optional

from .feature_flags import FeatureFlagManager
from .models import ConfidenceScore


class FallbackTrigger:
    """Determines when to fall back to question-asking workflow."""
    
    def __init__(
        self,
        feature_flag_manager: FeatureFlagManager,
        confidence_threshold: float = 0.6,
    ):
        """
        Initialize the FallbackTrigger.
        
        Args:
            feature_flag_manager: FeatureFlagManager for flag handling
            confidence_threshold: Minimum confidence for autonomous generation
        """
        self.feature_flag_manager = feature_flag_manager
        self.confidence_threshold = confidence_threshold
    
    def should_trigger(
        self,
        confidence: float,
        validation_passed: bool = True,
        token_budget_exceeded: bool = False,
        interactive: bool = False,
    ) -> bool:
        """
        Determine if fallback should be triggered.
        
        Args:
            confidence: Confidence score of generated content
            validation_passed: Whether semantic validation passed
            token_budget_exceeded: Whether token budget was exceeded
            interactive: Whether interactive mode is enabled
            
        Returns:
            True if fallback should be triggered
        """
        # Check interactive flag
        if interactive:
            return True
        
        # Check token budget
        if token_budget_exceeded:
            return True
        
        # Check confidence threshold
        if confidence < self.confidence_threshold:
            return True
        
        # Check validation
        if not validation_passed:
            return True
        
        return False
    
    def get_fallback_reason(
        self,
        confidence: float,
        validation_passed: bool = True,
        token_budget_exceeded: bool = False,
        interactive: bool = False,
    ) -> str:
        """
        Get the reason why fallback was triggered.
        
        Args:
            confidence: Confidence score of generated content
            validation_passed: Whether semantic validation passed
            token_budget_exceeded: Whether token budget was exceeded
            interactive: Whether interactive mode is enabled
            
        Returns:
            Reason string explaining why fallback was triggered
        """
        reasons = []
        
        if interactive:
            reasons.append("Interactive mode enabled")
        
        if token_budget_exceeded:
            reasons.append("Token budget exceeded")
        
        if confidence < self.confidence_threshold:
            reasons.append(f"Low confidence ({confidence:.2f} < {self.confidence_threshold})")
        
        if not validation_passed:
            reasons.append("Semantic validation failed")
        
        if not reasons:
            return "No fallback reason detected"
        
        return "; ".join(reasons)
    
    def get_fallback_workflow(self) -> str:
        """
        Get the fallback workflow type.
        
        Returns:
            Name of the fallback workflow (question-asking workflow)
        """
        return "question-asking"
    
    def trigger_for_file(
        self,
        filename: str,
        confidence: float,
        validation_passed: bool = True,
        token_budget_exceeded: bool = False,
        interactive: bool = False,
    ) -> Dict[str, any]:
        """
        Determine if fallback should be triggered for a specific file.
        
        Args:
            filename: Name of the file being generated
            confidence: Confidence score of generated content
            validation_passed: Whether semantic validation passed
            token_budget_exceeded: Whether token budget was exceeded
            interactive: Whether interactive mode is enabled
            
        Returns:
            Dictionary with fallback decision and context
        """
        should_fallback = self.should_trigger(
            confidence=confidence,
            validation_passed=validation_passed,
            token_budget_exceeded=token_budget_exceeded,
            interactive=interactive,
        )
        
        return {
            "filename": filename,
            "should_fallback": should_fallback,
            "reason": self.get_fallback_reason(
                confidence=confidence,
                validation_passed=validation_passed,
                token_budget_exceeded=token_budget_exceeded,
                interactive=interactive,
            ),
            "confidence": confidence,
            "confidence_threshold": self.confidence_threshold,
            "fallback_workflow": self.get_fallback_workflow(),
        }
    
    def get_context_for_questions(
        self,
        filename: str,
        confidence: float,
        evidence: List[dict],
        discovered_files: List[str],
    ) -> Dict[str, any]:
        """
        Get context for questions when fallback is triggered.
        
        Args:
            filename: Name of the file being generated
            confidence: Confidence score of generated content
            evidence: List of evidence supporting the content
            discovered_files: List of discovered files
            
        Returns:
            Context dictionary for questions
        """
        return {
            "filename": filename,
            "confidence": confidence,
            "evidence": evidence,
            "discovered_files": discovered_files,
            "reason_for_fallback": self.get_fallback_reason(confidence=confidence),
        }
