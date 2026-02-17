"""
Inference engine for the Steering Assistant v02.

This module provides the InferenceEngine class for making intelligent inferences
about missing information based on patterns, context, and industry standards.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import Evidence, ConfidenceLevel


class InferenceEngine:
    """Makes intelligent inferences about missing information."""
    
    # Industry standard patterns for inference
    INFERENCE_PATTERNS = {
        "backend_framework": {
            "FastAPI": r"fastapi|FastAPI",
            "Express": r"express|Express",
            "Django": r"django|Django",
            "Flask": r"flask|Flask",
            "Gin": r"gin-gonic|Gin",
            "Spring Boot": r"spring-boot|Spring Boot",
        },
        "frontend_framework": {
            "React": r"react|React",
            "Vue": r"vue|Vue",
            "Angular": r"angular|Angular",
            "Svelte": r"svelte|Svelte",
            "Next.js": r"next\.js|Next\.js",
            "Nuxt.js": r"nuxt\.js|Nuxt\.js",
        },
        "database": {
            "PostgreSQL": r"postgresql|PostgreSQL|postgres",
            "MongoDB": r"mongodb|MongoDB",
            "MySQL": r"mysql|MySQL",
            "Redis": r"redis|Redis",
            "Cassandra": r"cassandra|Cassandra",
        },
        "cache": {
            "Redis": r"redis|Redis",
            "Memcached": r"memcached|Memcached",
        },
    }
    
    def __init__(self, conservative_mode: bool = False):
        """
        Initialize the InferenceEngine.
        
        Args:
            conservative_mode: If True, reduce inference aggressiveness
        """
        self.conservative_mode = conservative_mode
        self._inference_history: List[dict] = []
    
    def infer_from_patterns(
        self,
        content: str,
        inference_type: str,
    ) -> Optional[Tuple[str, float]]:
        """
        Infer information from content using pattern matching.
        
        Args:
            content: Content to analyze
            inference_type: Type of inference (backend_framework, frontend_framework, etc.)
            
        Returns:
            Tuple of (inferred_value, confidence) or None if no match
        """
        patterns = self.INFERENCE_PATTERNS.get(inference_type, {})
        
        for value, pattern in patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                confidence = 0.85 if not self.conservative_mode else 0.75
                return value, confidence
        
        return None
    
    def infer_from_context(
        self,
        context: Dict[str, str],
        target_key: str,
    ) -> Optional[Tuple[str, float]]:
        """
        Infer information from context.
        
        Args:
            context: Context dictionary with available information
            target_key: Key to infer (e.g., "backend_framework")
            
        Returns:
            Tuple of (inferred_value, confidence) or None if no match
        """
        # Combine all context for analysis
        combined_context = " ".join(context.values()).lower()
        
        # Try to infer from patterns
        for inference_type, patterns in self.INFERENCE_PATTERNS.items():
            for value, pattern in patterns.items():
                if re.search(pattern, combined_context, re.IGNORECASE):
                    # Check if this inference makes sense for the target
                    if self._is_valid_inference(inference_type, target_key):
                        confidence = 0.80 if not self.conservative_mode else 0.70
                        return value, confidence
        
        return None
    
    def _is_valid_inference(
        self,
        inference_type: str,
        target_key: str,
    ) -> bool:
        """
        Check if an inference is valid for the target key.
        
        Args:
            inference_type: Type of inference
            target_key: Target key to infer
            
        Returns:
            True if inference is valid
        """
        # Map inference types to target keys
        type_to_key = {
            "backend_framework": "backend_framework",
            "frontend_framework": "frontend_framework",
            "database": "database",
            "cache": "cache",
        }
        
        return type_to_key.get(inference_type) == target_key
    
    def mark_as_inferred(
        self,
        content: str,
        inference_type: str,
        value: str,
        confidence: float,
    ) -> str:
        """
        Mark content as inferred with appropriate markers.
        
        Args:
            content: Original content
            inference_type: Type of inference
            value: Inferred value
            confidence: Confidence score
            
        Returns:
            Content with inference markers
        """
        marker = f"[INFERRED: {inference_type}={value}, confidence={confidence:.2f}]"
        return f"{content}\n\n{marker}"
    
    def use_explicit_markers(
        self,
        content: str,
        reason: str = "Not yet defined",
    ) -> str:
        """
        Add explicit markers for content that cannot be inferred.
        
        Args:
            content: Original content
            reason: Reason for using explicit marker
            
        Returns:
            Content with explicit marker
        """
        marker = f"[TO BE DETERMINED: {reason}]"
        return f"{content}\n\n{marker}"
    
    def make_inference(
        self,
        content: str,
        context: Dict[str, str],
        target_key: str,
    ) -> Tuple[str, Evidence]:
        """
        Make an inference about missing information.
        
        Args:
            content: Content to analyze
            context: Context dictionary
            target_key: Key to infer
            
        Returns:
            Tuple of (inferred_value, evidence)
        """
        # Try pattern matching first
        for inference_type, patterns in self.INFERENCE_PATTERNS.items():
            for value, pattern in patterns.items():
                if re.search(pattern, content, re.IGNORECASE):
                    evidence = Evidence(
                        source="INFERENCE",
                        strength=0.80 if not self.conservative_mode else 0.70,
                        description=f"Inferred {inference_type}={value} from content patterns",
                        metadata={"pattern": pattern, "inference_type": inference_type},
                    )
                    return value, evidence
        
        # Try context-based inference
        result = self.infer_from_context(context, target_key)
        if result:
            value, confidence = result
            evidence = Evidence(
                source="INFERENCE",
                strength=confidence,
                description=f"Inferred {target_key}={value} from context",
                metadata={"context_keys": list(context.keys())},
            )
            return value, evidence
        
        # No inference possible
        evidence = Evidence(
            source="INFERENCE",
            strength=0.30,
            description="No clear inference possible from available information",
            metadata={"target_key": target_key},
        )
        return "To be determined", evidence
    
    def get_inference_summary(
        self,
    ) -> Dict[str, any]:
        """
        Get summary of inference history.
        
        Returns:
            Dictionary with inference statistics
        """
        total_inferences = len(self._inference_history)
        high_confidence = sum(
            1 for h in self._inference_history if h.get("confidence", 0) >= 0.8
        )
        medium_confidence = sum(
            1 for h in self._inference_history if 0.6 <= h.get("confidence", 0) < 0.8
        )
        low_confidence = sum(
            1 for h in self._inference_history if h.get("confidence", 0) < 0.6
        )
        
        return {
            "total_inferences": total_inferences,
            "high_confidence": high_confidence,
            "medium_confidence": medium_confidence,
            "low_confidence": low_confidence,
            "conservative_mode": self.conservative_mode,
        }
