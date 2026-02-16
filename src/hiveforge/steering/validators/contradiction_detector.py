"""
Contradiction detection for the Steering Assistant v02.

This module provides the ContradictionDetector class for detecting direct and
implicit contradictions in generated content.
"""

import re
from typing import Dict, List, Optional, Tuple


class ContradictionDetector:
    """Detects contradictions between different pieces of content."""
    
    # Direct contradiction keywords
    DIRECT_CONTRADICTIONS = {
        "python": "javascript",
        "javascript": "python",
        "react": "vue",
        "vue": "react",
        "microservices": "monolithic",
        "monolithic": "microservices",
        "rest": "graphql",
        "graphql": "rest",
        "sql": "nosql",
        "nosql": "sql",
        "postgresql": "mongodb",
        "mongodb": "postgresql",
        "docker": "kubernetes",
        "kubernetes": "docker",
    }
    
    # Implicit contradiction patterns
    IMPLICIT_CONTRADICTIONS = [
        {
            "patterns": ["microservices", "distributed"],
            "opposite": ["monolithic", "single"],
            "message": "Architecture mentions microservices but tech stack describes monolithic design",
        },
        {
            "patterns": ["monolithic", "single"],
            "opposite": ["microservices", "distributed"],
            "message": "Architecture mentions monolithic but tech stack describes microservices",
        },
        {
            "patterns": ["rest", "RESTful"],
            "opposite": ["graphql", "GraphQL"],
            "message": "API design mentions REST but tech stack specifies GraphQL",
        },
        {
            "patterns": ["graphql", "GraphQL"],
            "opposite": ["rest", "RESTful"],
            "message": "API design mentions GraphQL but tech stack specifies REST",
        },
        {
            "patterns": ["react", "React"],
            "opposite": ["angular", "Angular", "vue", "Vue"],
            "message": "Frontend mentions React but tech stack specifies different framework",
        },
    ]
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize the ContradictionDetector.
        
        Args:
            confidence_threshold: Minimum confidence to report a contradiction
        """
        self.confidence_threshold = confidence_threshold
    
    def detect_direct_contradictions(
        self,
        files: Dict[str, str],
        keywords: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict[str, any]]:
        """
        Detect direct contradictions between files.
        
        Args:
            files: Dictionary mapping file names to their content
            keywords: Optional custom keyword mappings
            
        Returns:
            List of detected contradictions
        """
        contradictions = []
        keyword_map = keywords or self.DIRECT_CONTRADICTIONS
        
        # Combine all content for analysis
        all_content = " ".join(files.values()).lower()
        
        # Check for direct contradictions
        for term1, term2 in keyword_map.items():
            term1_lower = term1.lower()
            term2_lower = term2.lower()
            
            if term1_lower in all_content and term2_lower in all_content:
                contradictions.append({
                    "type": "direct",
                    "term1": term1,
                    "term2": term2,
                    "message": f"Contradictory terms found: '{term1}' and '{term2}'",
                    "confidence": 0.95,
                    "files": self._find_files_with_terms(files, [term1, term2]),
                })
        
        return contradictions
    
    def detect_implicit_contradictions(
        self,
        files: Dict[str, str],
        target_files: Optional[List[str]] = None
    ) -> List[Dict[str, any]]:
        """
        Detect implicit contradictions using pattern matching.
        
        Args:
            files: Dictionary mapping file names to their content
            target_files: Optional list of files to check
            
        Returns:
            List of detected contradictions
        """
        contradictions = []
        
        # Filter to target files if specified
        check_files = files
        if target_files:
            check_files = {k: v for k, v in files.items() if k in target_files}
        
        # Combine content for analysis
        all_content = " ".join(check_files.values()).lower()
        
        # Check implicit contradiction patterns
        for pattern_info in self.IMPLICIT_CONTRADICTIONS:
            patterns = pattern_info["patterns"]
            opposites = pattern_info["opposite"]
            message = pattern_info["message"]
            
            # Check if patterns are present
            patterns_found = any(p.lower() in all_content for p in patterns)
            opposites_found = any(o.lower() in all_content for o in opposites)
            
            if patterns_found and opposites_found:
                contradictions.append({
                    "type": "implicit",
                    "patterns": patterns,
                    "opposites": opposites,
                    "message": message,
                    "confidence": 0.85,
                    "files": list(check_files.keys()),
                })
        
        return contradictions
    
    def calculate_confidence(
        self,
        contradiction_type: str,
        evidence: List[str],
        context: Optional[Dict[str, any]] = None
    ) -> float:
        """
        Calculate confidence score for a detected contradiction.
        
        Args:
            contradiction_type: Type of contradiction (direct/implicit)
            evidence: List of evidence strings
            context: Optional context information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = {
            "direct": 0.95,
            "implicit": 0.85,
        }.get(contradiction_type, 0.7)
        
        # Adjust based on evidence strength
        if len(evidence) >= 3:
            base_confidence = min(base_confidence + 0.05, 1.0)
        elif len(evidence) == 1:
            base_confidence = max(base_confidence - 0.05, 0.5)
        
        # Adjust based on context
        if context:
            if context.get("file_count", 1) > 2:
                base_confidence = min(base_confidence + 0.05, 1.0)
            if context.get("explicit_markers", False):
                base_confidence = max(base_confidence - 0.1, 0.5)
        
        return base_confidence
    
    def get_contradiction_confidence(
        self,
        contradiction: Dict[str, any]
    ) -> float:
        """
        Get confidence score for a contradiction.
        
        Args:
            contradiction: Contradiction dictionary
            
        Returns:
            Confidence score
        """
        return contradiction.get("confidence", 0.7)
    
    def _find_files_with_terms(
        self,
        files: Dict[str, str],
        terms: List[str]
    ) -> List[str]:
        """
        Find files containing any of the given terms.
        
        Args:
            files: Dictionary mapping file names to their content
            terms: List of terms to search for
            
        Returns:
            List of file names containing the terms
        """
        matching_files = []
        
        for file_name, content in files.items():
            content_lower = content.lower()
            if any(term.lower() in content_lower for term in terms):
                matching_files.append(file_name)
        
        return matching_files
    
    def detect_all_contradictions(
        self,
        files: Dict[str, str]
    ) -> List[Dict[str, any]]:
        """
        Detect all types of contradictions in files.
        
        Args:
            files: Dictionary mapping file names to their content
            
        Returns:
            List of all detected contradictions
        """
        contradictions = []
        
        # Detect direct contradictions
        direct = self.detect_direct_contradictions(files)
        contradictions.extend(direct)
        
        # Detect implicit contradictions
        implicit = self.detect_implicit_contradictions(files)
        contradictions.extend(implicit)
        
        return contradictions
