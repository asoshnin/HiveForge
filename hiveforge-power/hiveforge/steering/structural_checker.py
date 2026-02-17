"""
Structural consistency validation for the Steering Assistant v02.1.

This module provides the StructuralConsistencyChecker class for verifying that
generated content maintains structural consistency across multiple generations.

Validates: Requirements 21.1-21.6 (v02.1)
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import ConfidenceLevel


@dataclass
class StructuralCheckResult:
    """Result of a structural consistency check."""
    is_consistent: bool
    similarity_score: float  # 0.0-1.0
    sections_matched: List[str]
    sections_missing: List[str]
    sections_extra: List[str]
    length_similarity: float  # 0.0-1.0
    key_facts_present: List[str]
    key_facts_missing: List[str]
    details: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RoundTripResult:
    """Result of a round-trip generation test."""
    success: bool
    generations: List[str]
    consistency_scores: List[float]
    average_consistency: float
    unstable_sections: List[str]
    attempts: int
    details: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsistencyMetric:
    """A tracked consistency metric."""
    section_type: str
    total_checks: int
    consistent_checks: int
    consistency_rate: float  # 0.0-1.0
    last_checked: datetime
    average_similarity: float


class StructuralConsistencyChecker:
    """
    Validates structural consistency of generated content.
    
    This class implements the v02.1 requirement for structural consistency
    validation, ensuring that regenerated content maintains the same structure
    (sections, length, key facts) when generated with consistent parameters.
    """
    
    # Generation parameters for consistency
    DEFAULT_TEMPERATURE: float = 0.0
    DEFAULT_SEED: int = 42
    
    # Consistency thresholds
    MIN_CONSISTENCY_RATE: float = 0.80  # 80% threshold from requirement 21.6
    MIN_SIMILARITY_SCORE: float = 0.70
    LENGTH_TOLERANCE: float = 0.20  # 20% length variation allowed
    
    # Section types for tracking
    SECTION_TYPES = [
        "project-vision",
        "tech-stack",
        "architecture",
        "conventions",
        "api-standards",
        "db-standards",
        "qa-standards",
        "ui-standards",
    ]
    
    def __init__(
        self,
        telemetry_dir: Optional[Path] = None,
        min_consistency_rate: float = 0.80,
        min_similarity_score: float = 0.70,
        length_tolerance: float = 0.20,
    ):
        """
        Initialize the StructuralConsistencyChecker.
        
        Args:
            telemetry_dir: Directory for storing consistency telemetry
            min_consistency_rate: Minimum consistency rate threshold (default: 0.80)
            min_similarity_score: Minimum similarity score threshold (default: 0.70)
            length_tolerance: Allowed length variation (default: 0.20 = 20%)
        """
        self.telemetry_dir = telemetry_dir or Path(".kiro/.telemetry/structural")
        self.min_consistency_rate = min_consistency_rate
        self.min_similarity_score = min_similarity_score
        self.length_tolerance = length_tolerance
        
        # Track consistency metrics per section type
        self._consistency_metrics: Dict[str, ConsistencyMetric] = {}
        
        # Generation parameters
        self._temperature: float = self.DEFAULT_TEMPERATURE
        self._seed: int = self.DEFAULT_SEED
        
        # Ensure telemetry directory exists
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
    
    def set_generation_parameters(
        self,
        temperature: float = DEFAULT_TEMPERATURE,
        seed: int = DEFAULT_SEED,
    ) -> None:
        """
        Set generation parameters for consistent output.
        
        Args:
            temperature: Temperature for generation (0.0 for deterministic)
            seed: Random seed for reproducibility
        """
        self._temperature = temperature
        self._seed = seed
    
    def get_generation_parameters(self) -> Dict[str, float]:
        """
        Get current generation parameters.
        
        Returns:
            Dictionary with temperature and seed
        """
        return {
            "temperature": self._temperature,
            "seed": self._seed,
        }
    
    def extract_sections(self, content: str) -> List[str]:
        """
        Extract section headers from markdown content.
        
        Args:
            content: The markdown content to parse
            
        Returns:
            List of section header names
        """
        # Match markdown headers (# ## ### etc.)
        pattern = r'^(#{1,6})\s+(.+)$'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        sections = []
        for level, title in matches:
            # Clean up the title
            title = title.strip()
            # Only include top-level and second-level sections for structural consistency
            if len(level) <= 2:
                sections.append(title)
        
        return sections
    
    def extract_key_facts(self, content: str) -> List[str]:
        """
        Extract key facts from content based on common patterns.
        
        Args:
            content: The content to analyze
            
        Returns:
            List of key fact strings
        """
        key_facts = []
        
        # Extract technology names and versions using search
        # Version pattern matches both "18" and "3.11" formats
        tech_patterns = [
            (r'Python', r'(\d+(?:\.\d+)?)'),
            (r'Node\.?js', r'(\d+(?:\.\d+)?)'),
            (r'Go', r'(\d+(?:\.\d+)?)'),
            (r'Rust', r'(\d+(?:\.\d+)?)'),
            (r'TypeScript', r'(\d+(?:\.\d+)?)'),
            (r'JavaScript', r'(\d+(?:\.\d+)?)'),
            (r'React', r'(\d+(?:\.\d+)?)'),
            (r'Vue', r'(\d+(?:\.\d+)?)'),
            (r'Angular', r'(\d+(?:\.\d+)?)'),
            (r'FastAPI', r'(\d+(?:\.\d+)?)'),
            (r'Express', r'(\d+(?:\.\d+)?)'),
            (r'Django', r'(\d+(?:\.\d+)?)'),
            (r'Flask', r'(\d+(?:\.\d+)?)'),
            (r'PostgreSQL', r'(\d+(?:\.\d+)?)'),
            (r'MongoDB', r'(\d+(?:\.\d+)?)'),
            (r'MySQL', r'(\d+(?:\.\d+)?)'),
            (r'Redis', r'(\d+(?:\.\d+)?)'),
        ]
        
        for tech_name, version_pattern in tech_patterns:
            pattern = tech_name + r'\s*' + version_pattern
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    key_facts.append(f"{match[0]} {match[1]}")
                elif isinstance(match, str):
                    key_facts.append(f"{tech_name} {match}")
        
        # Also extract just the technology names without versions
        tech_name_patterns = [
            r'Docker',
            r'Kubernetes',
            r'AWS',
            r'GCP',
            r'Azure',
        ]
        
        for pattern in tech_name_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                key_facts.append(match)
        
        # Extract architecture patterns
        arch_patterns = [
            r'microservices',
            r'monolithic',
            r'serverless',
            r'event-driven',
            r'REST',
            r'GraphQL',
            r'gRPC',
            r'containerized',
            r'monorepo',
        ]
        
        for pattern in arch_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                key_facts.append(match.lower())
        
        return list(set(key_facts))  # Remove duplicates
    
    def calculate_length_similarity(
        self,
        content1: str,
        content2: str,
    ) -> float:
        """
        Calculate similarity based on content length.
        
        Args:
            content1: First content
            content2: Second content
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        len1 = len(content1)
        len2 = len(content2)
        
        if len1 == 0 and len2 == 0:
            return 1.0
        
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Calculate relative difference
        max_len = max(len1, len2)
        min_len = min(len1, len2)
        
        difference = (max_len - min_len) / max_len
        
        # Convert to similarity (1.0 = identical length)
        similarity = max(0.0, 1.0 - difference)
        
        return similarity
    
    def calculate_section_similarity(
        self,
        sections1: List[str],
        sections2: List[str],
    ) -> Tuple[float, List[str], List[str], List[str]]:
        """
        Calculate similarity based on section matching.
        
        Args:
            sections1: Sections from first content
            sections2: Sections from second content
            
        Returns:
            Tuple of (similarity_score, matched, missing, extra)
        """
        set1 = set(sections1)
        set2 = set(sections2)
        
        matched = set1 & set2
        missing = set1 - set2
        extra = set2 - set1
        
        if not set1 and not set2:
            return 1.0, [], [], []
        
        if not set1:
            return 0.0, [], [], list(set2)
        
        if not set2:
            return 0.0, list(set1), [], []
        
        # Jaccard similarity
        similarity = len(matched) / len(set1 | set2)
        
        return (
            similarity,
            list(matched),
            list(missing),
            list(extra),
        )
    
    def calculate_key_facts_similarity(
        self,
        facts1: List[str],
        facts2: List[str],
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate similarity based on key facts.
        
        Args:
            facts1: Key facts from first content
            facts2: Key facts from second content
            
        Returns:
            Tuple of (similarity_score, present, missing)
        """
        set1 = set(facts1)
        set2 = set(facts2)
        
        present = set1 & set2
        missing = set1 - set2
        
        if not set1 and not set2:
            return 1.0, [], []
        
        if not set1:
            return 0.0, [], list(set2)
        
        if not set2:
            return 0.0, [], list(set1)
        
        # Jaccard similarity
        similarity = len(present) / len(set1)
        
        return (
            similarity,
            list(present),
            list(missing),
        )
    
    def check_structural_similarity(
        self,
        content1: str,
        content2: str,
        section_type: Optional[str] = None,
    ) -> StructuralCheckResult:
        """
        Check structural similarity between two content pieces.
        
        This method verifies:
        - Same sections present
        - Similar length
        - Key facts present
        
        Args:
            content1: First content
            content2: Second content
            section_type: Optional section type for tracking
            
        Returns:
            StructuralCheckResult with similarity details
        """
        # Extract sections
        sections1 = self.extract_sections(content1)
        sections2 = self.extract_sections(content2)
        
        # Calculate section similarity
        (
            section_similarity,
            sections_matched,
            sections_missing,
            sections_extra,
        ) = self.calculate_section_similarity(sections1, sections2)
        
        # Calculate length similarity
        length_similarity = self.calculate_length_similarity(content1, content2)
        
        # Extract and compare key facts
        facts1 = self.extract_key_facts(content1)
        facts2 = self.extract_key_facts(content2)
        
        (
            facts_similarity,
            facts_present,
            facts_missing,
        ) = self.calculate_key_facts_similarity(facts1, facts2)
        
        # Calculate overall similarity score
        # Weight: sections 40%, length 20%, key facts 40%
        overall_similarity = (
            section_similarity * 0.4 +
            length_similarity * 0.2 +
            facts_similarity * 0.4
        )
        
        # Determine consistency
        is_consistent = (
            overall_similarity >= self.min_similarity_score and
            length_similarity >= (1.0 - self.length_tolerance) and
            len(sections_missing) == 0
        )
        
        # Build details string
        details_parts = [
            f"Overall similarity: {overall_similarity:.2%}",
            f"Section match: {section_similarity:.2%} ({len(sections_matched)}/{len(sections1)} sections)",
            f"Length similarity: {length_similarity:.2%}",
            f"Key facts match: {facts_similarity:.2%} ({len(facts_present)}/{len(facts1)} facts)",
        ]
        
        if sections_missing:
            details_parts.append(f"Missing sections: {', '.join(sections_missing)}")
        if sections_extra:
            details_parts.append(f"Extra sections: {', '.join(sections_extra)}")
        if facts_missing:
            details_parts.append(f"Missing facts: {', '.join(facts_missing)}")
        
        result = StructuralCheckResult(
            is_consistent=is_consistent,
            similarity_score=overall_similarity,
            sections_matched=sections_matched,
            sections_missing=sections_missing,
            sections_extra=sections_extra,
            length_similarity=length_similarity,
            key_facts_present=facts_present,
            key_facts_missing=facts_missing,
            details="; ".join(details_parts),
        )
        
        # Track metrics if section type provided
        if section_type:
            self._track_consistency_check(section_type, result)
        
        return result
    
    def test_round_trip(
        self,
        generate_func,
        context: Dict[str, str],
        max_attempts: int = 2,
    ) -> RoundTripResult:
        """
        Test round-trip generation consistency.
        
        This method:
        1. Generates content
        2. Validates structure
        3. Regenerates with same parameters
        4. Compares results
        
        Args:
            generate_func: Function that generates content (takes context, temperature, seed)
            context: Context dictionary for generation
            max_attempts: Maximum regeneration attempts (default: 2)
            
        Returns:
            RoundTripResult with comparison details
        """
        generations: List[str] = []
        consistency_scores: List[float] = []
        
        # Generate first version
        try:
            gen1 = generate_func(
                context=context,
                temperature=self._temperature,
                seed=self._seed,
            )
            generations.append(gen1)
        except Exception as e:
            return RoundTripResult(
                success=False,
                generations=[],
                consistency_scores=[],
                average_consistency=0.0,
                unstable_sections=[],
                attempts=1,
                details=f"Initial generation failed: {str(e)}",
            )
        
        # Regenerate and compare
        for attempt in range(1, max_attempts + 1):
            try:
                gen_new = generate_func(
                    context=context,
                    temperature=self._temperature,
                    seed=self._seed,
                )
                generations.append(gen_new)
                
                # Compare with first generation
                check_result = self.check_structural_similarity(generations[0], gen_new)
                consistency_scores.append(check_result.similarity_score)
                
                if not check_result.is_consistent:
                    # Log inconsistency
                    self._log_inconsistency(context, check_result, attempt)
                    
            except Exception as e:
                return RoundTripResult(
                    success=False,
                    generations=generations,
                    consistency_scores=consistency_scores,
                    average_consistency=sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0,
                    unstable_sections=check_result.sections_missing if 'check_result' in dir() else [],
                    attempts=attempt,
                    details=f"Regeneration attempt {attempt} failed: {str(e)}",
                )
        
        # Calculate average consistency
        avg_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0
        
        # Identify unstable sections
        unstable_sections = []
        for i, score in enumerate(consistency_scores):
            if score < self.min_consistency_rate:
                unstable_sections.append(f"attempt_{i + 1}")
        
        return RoundTripResult(
            success=True,
            generations=generations,
            consistency_scores=consistency_scores,
            average_consistency=avg_consistency,
            unstable_sections=unstable_sections,
            attempts=len(generations),
            details=f"Round-trip completed with {len(generations)} generations, "
                   f"average consistency: {avg_consistency:.2%}",
        )
    
    def _track_consistency_check(
        self,
        section_type: str,
        result: StructuralCheckResult,
    ) -> None:
        """
        Track a consistency check result for a section type.
        
        Args:
            section_type: Type of section checked
            result: Check result
        """
        if section_type not in self._consistency_metrics:
            self._consistency_metrics[section_type] = ConsistencyMetric(
                section_type=section_type,
                total_checks=0,
                consistent_checks=0,
                consistency_rate=0.0,
                last_checked=datetime.now(),
                average_similarity=0.0,
            )
        
        metric = self._consistency_metrics[section_type]
        metric.total_checks += 1
        if result.is_consistent:
            metric.consistent_checks += 1
        
        # Update rates
        metric.consistency_rate = metric.consistent_checks / metric.total_checks
        metric.average_similarity = (
            (metric.average_similarity * (metric.total_checks - 1) + result.similarity_score)
            / metric.total_checks
        )
        metric.last_checked = datetime.now()
    
    def track_consistency_rate(self, section_type: Optional[str] = None) -> Dict[str, any]:
        """
        Track and return consistency rate as a quality metric.
        
        Args:
            section_type: Optional specific section type, or all sections
            
        Returns:
            Dictionary with consistency metrics
        """
        if section_type:
            if section_type not in self._consistency_metrics:
                return {
                    "section_type": section_type,
                    "total_checks": 0,
                    "consistent_checks": 0,
                    "consistency_rate": 0.0,
                    "average_similarity": 0.0,
                    "status": "no_data",
                }
            
            metric = self._consistency_metrics[section_type]
            return {
                "section_type": metric.section_type,
                "total_checks": metric.total_checks,
                "consistent_checks": metric.consistent_checks,
                "consistency_rate": metric.consistency_rate,
                "average_similarity": metric.average_similarity,
                "last_checked": metric.last_checked.isoformat(),
                "status": "healthy" if metric.consistency_rate >= self.min_consistency_rate else "needs_attention",
            }
        
        # Return all section metrics
        results = {}
        for section_type, metric in self._consistency_metrics.items():
            results[section_type] = {
                "section_type": metric.section_type,
                "total_checks": metric.total_checks,
                "consistent_checks": metric.consistent_checks,
                "consistency_rate": metric.consistency_rate,
                "average_similarity": metric.average_similarity,
                "last_checked": metric.last_checked.isoformat(),
                "status": "healthy" if metric.consistency_rate >= self.min_consistency_rate else "needs_attention",
            }
        
        # Add summary
        total_checks = sum(m.total_checks for m in self._consistency_metrics.values())
        total_consistent = sum(m.consistent_checks for m in self._consistency_metrics.values())
        
        results["_summary"] = {
            "total_checks": total_checks,
            "total_consistent": total_consistent,
            "overall_consistency_rate": total_consistent / total_checks if total_checks > 0 else 0.0,
            "sections_below_threshold": [
                s for s, m in self._consistency_metrics.items()
                if m.consistency_rate < self.min_consistency_rate
            ],
        }
        
        return results
    
    def check_strategy_adjustment(
        self,
        section_type: str,
    ) -> Dict[str, any]:
        """
        Check if generation strategy needs adjustment for a section type.
        
        Per requirement 21.6: When structural consistency is below 80% for a
        specific section type, the system SHALL adjust generation strategy.
        
        Args:
            section_type: Section type to check
            
        Returns:
            Dictionary with adjustment recommendation
        """
        metrics = self.track_consistency_rate(section_type)
        
        if metrics["total_checks"] < 5:
            return {
                "section_type": section_type,
                "needs_adjustment": False,
                "reason": "insufficient_data",
                "recommendation": "Continue collecting consistency data (minimum 5 checks required)",
            }
        
        consistency_rate = metrics["consistency_rate"]
        
        if consistency_rate < self.min_consistency_rate:
            return {
                "section_type": section_type,
                "needs_adjustment": True,
                "reason": f"consistency_below_threshold",
                "current_rate": consistency_rate,
                "threshold": self.min_consistency_rate,
                "recommendation": [
                    "Consider increasing temperature slightly for more exploration",
                    "Review and simplify the prompt for this section type",
                    "Add more specific examples in the context",
                    "Consider breaking the section into smaller subsections",
                ],
            }
        
        return {
            "section_type": section_type,
            "needs_adjustment": False,
            "reason": "consistency_acceptable",
            "current_rate": consistency_rate,
            "recommendation": "Current strategy is working well",
        }
    
    def _log_inconsistency(
        self,
        context: Dict[str, str],
        result: StructuralCheckResult,
        attempt: int,
    ) -> None:
        """
        Log structural inconsistency for analysis.
        
        Args:
            context: Generation context
            result: Check result showing inconsistency
            attempt: Attempt number
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "attempt": attempt,
            "similarity_score": result.similarity_score,
            "sections_missing": result.sections_missing,
            "sections_extra": result.sections_extra,
            "key_facts_missing": result.key_facts_missing,
            "length_similarity": result.length_similarity,
            "details": result.details,
        }
        
        # Write to log file
        log_file = self.telemetry_dir / "inconsistencies.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def save_metrics(self) -> Path:
        """
        Save consistency metrics to file.
        
        Returns:
            Path to saved metrics file
        """
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "generation_parameters": {
                "temperature": self._temperature,
                "seed": self._seed,
            },
            "thresholds": {
                "min_consistency_rate": self.min_consistency_rate,
                "min_similarity_score": self.min_similarity_score,
                "length_tolerance": self.length_tolerance,
            },
            "metrics": self.track_consistency_rate(),
        }
        
        output_file = self.telemetry_dir / "consistency_metrics.json"
        with open(output_file, "w") as f:
            json.dump(metrics_data, f, indent=2)
        
        return output_file
    
    def reset_metrics(self, section_type: Optional[str] = None) -> None:
        """
        Reset consistency metrics.
        
        Args:
            section_type: Optional specific section to reset, or all
        """
        if section_type:
            if section_type in self._consistency_metrics:
                del self._consistency_metrics[section_type]
        else:
            self._consistency_metrics.clear()