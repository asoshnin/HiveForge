"""
Semantic similarity checker for testing.

This module provides the SemanticSimilarityChecker class for comparing
content semantically rather than by exact match.
"""

import re
from typing import Any, Dict, List, Optional, Set


class SemanticSimilarityChecker:
    """Checks semantic similarity between content strings."""
    
    def __init__(
        self,
        min_similarity: float = 0.7,
    ):
        """
        Initialize the checker.
        
        Args:
            min_similarity: Minimum similarity score for match
        """
        self.min_similarity = min_similarity
    
    def check_similarity(
        self,
        content1: str,
        content2: str,
    ) -> float:
        """
        Check semantic similarity between two content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity score from 0.0 to 1.0
        """
        # Extract key facts from both contents
        facts1 = self._extract_facts(content1)
        facts2 = self._extract_facts(content2)
        
        if not facts1 or not facts2:
            # Fall back to simple comparison
            return self._simple_similarity(content1, content2)
        
        # Calculate overlap of key facts
        common_facts = facts1 & facts2
        all_facts = facts1 | facts2
        
        if not all_facts:
            return 1.0
        
        return len(common_facts) / len(all_facts)
    
    def _extract_facts(self, content: str) -> Set[str]:
        """Extract key facts from content."""
        facts = set()
        
        # Extract headings
        headings = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)
        facts.update(headings)
        
        # Extract key technical terms (simplified)
        technical_terms = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b", content)
        facts.update(technical_terms)
        
        # Extract version numbers
        versions = re.findall(r"\b\d+\.\d+(?:\.\d+)?\b", content)
        facts.update(versions)
        
        return facts
    
    def _simple_similarity(self, content1: str, content2: str) -> float:
        """Calculate simple similarity based on character overlap."""
        if not content1 or not content2:
            return 0.0
        
        # Normalize
        s1 = content1.lower().strip()
        s2 = content2.lower().strip()
        
        if s1 == s2:
            return 1.0
        
        # Calculate Jaccard similarity of words
        words1 = set(re.findall(r"\b\w+\b", s1))
        words2 = set(re.findall(r"\b\w+\b", s2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def check_properties(
        self,
        content: str,
        required_sections: List[str],
        min_length: int = 100,
    ) -> Dict[str, Any]:
        """
        Check if content has required properties.
        
        Args:
            content: Content to check
            required_sections: List of required section names
            min_length: Minimum content length
            
        Returns:
            Dictionary with check results
        """
        results = {
            "passed": True,
            "issues": [],
            "length": len(content),
            "sections_found": [],
        }
        
        # Check length
        if len(content) < min_length:
            results["passed"] = False
            results["issues"].append(f"Content too short: {len(content)} < {min_length}")
        
        # Check for required sections
        for section in required_sections:
            if section.lower() in content.lower():
                results["sections_found"].append(section)
        
        # Check for key structural elements
        has_headings = bool(re.search(r"^#+\s+", content, re.MULTILINE))
        if not has_headings:
            results["issues"].append("Missing headings")
        
        # Check for code blocks
        has_code_blocks = bool(re.search(r"```", content))
        if not has_code_blocks:
            results["issues"].append("Missing code blocks")
        
        if results["issues"]:
            results["passed"] = False
        
        return results
    
    def calculate_similarity_score(
        self,
        content1: str,
        content2: str,
    ) -> float:
        """
        Calculate similarity score between two contents.
        
        Args:
            content1: First content
            content2: Second content
            
        Returns:
            Similarity score from 0.0 to 1.0
        """
        return self.check_similarity(content1, content2)
    
    def is_similar(
        self,
        content1: str,
        content2: str,
        threshold: Optional[float] = None,
    ) -> bool:
        """
        Check if contents are similar above threshold.
        
        Args:
            content1: First content
            content2: Second content
            threshold: Minimum similarity (uses default if None)
            
        Returns:
            True if similar enough
        """
        if threshold is None:
            threshold = self.min_similarity
        
        return self.check_similarity(content1, content2) >= threshold
