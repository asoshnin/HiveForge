"""
Inference transparency system for the Steering Assistant v02.1.

This module provides the InferenceTransparency class for documenting and explaining
how intelligent inferences are made about missing information.

Validates: Requirements 26.1-26.7
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class InferenceStrength(Enum):
    """Classification of inference strength based on evidence quality."""
    STRONG = "STRONG"   # Clear patterns, multiple sources, high confidence
    MODERATE = "MODERATE"  # Some evidence, reasonable inference
    WEAK = "WEAK"       # Educated guess, limited evidence


class InferenceSource(Enum):
    """Source of information used for inference."""
    PATTERN_MATCH = "PATTERN_MATCH"  # Regex/pattern matching in code
    CONTEXT = "CONTEXT"  # Derived from project context
    INDUSTRY_STANDARD = "INDUSTRY_STANDARD"  # Common industry patterns
    FILE_STRUCTURE = "FILE_STRUCTURE"  # Directory structure analysis
    DEPENDENCY = "DEPENDENCY"  # Package manager dependencies
    CONFIG_FILE = "CONFIG_FILE"  # Configuration files


@dataclass
class InferenceExplanation:
    """Detailed explanation of an inference made by the system."""
    inference_type: str
    inferred_value: str
    confidence: float
    strength: InferenceStrength
    reasoning: str
    evidence_sources: List[Dict[str, Any]]
    industry_standard_reference: Optional[str] = None
    alternative_values: List[str] = field(default_factory=list)
    conservative_note: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Convert explanation to markdown format for display."""
        strength_emoji = {
            InferenceStrength.STRONG: "✓",
            InferenceStrength.MODERATE: "◐",
            InferenceStrength.WEAK: "○",
        }.get(self.strength, "?")
        
        lines = [
            f"### {strength_emoji} Inference: {self.inference_type}",
            f"**Value:** {self.inferred_value}",
            f"**Confidence:** {self.confidence:.2f} ({self.strength.value})",
            f"",
            f"**Reasoning:** {self.reasoning}",
            f"",
            f"**Evidence Sources:**",
        ]
        
        for source in self.evidence_sources:
            source_type = source.get("type", "unknown")
            source_detail = source.get("detail", "")
            lines.append(f"  - {source_type}: {source_detail}")
        
        if self.industry_standard_reference:
            lines.append(f"")
            lines.append(f"**Industry Standard:** {self.industry_standard_reference}")
        
        if self.alternative_values:
            lines.append(f"")
            lines.append(f"**Alternatives Considered:** {', '.join(self.alternative_values)}")
        
        if self.conservative_note:
            lines.append(f"")
            lines.append(f"**Note:** {self.conservative_note}")
        
        return "\n".join(lines)


@dataclass
class InferencePattern:
    """Documents an inference pattern/heuristic used by the system."""
    pattern_id: str
    description: str
    inference_type: str
    conditions: List[str]
    confidence_range: Tuple[float, float]
    examples: List[str]
    industry_standard_basis: Optional[str] = None
    conservative_mode_adjustment: Optional[str] = None


class InferenceTransparency:
    """
    Provides transparency about how intelligent inferences are made.
    
    This class documents inference patterns, explains reasoning for each inference,
    and distinguishes between strong and weak inferences.
    
    Validates: Requirements 26.1-26.7
    """
    
    # Industry standard patterns for documentation
    INDUSTRY_STANDARDS = {
        "fastapi_python": "FastAPI is the most popular Python web framework for APIs (2024)",
        "react_typescript": "React with TypeScript is the industry standard for frontend",
        "postgresql_enterprise": "PostgreSQL is the most popular open-source relational database",
        "redis_caching": "Redis is the de facto standard for application caching",
        "docker_containerization": "Docker is the industry standard for containerization",
        "microservices_distributed": "Microservices is the dominant architecture for scalable systems",
        "ci_cd_automation": "CI/CD is standard practice for modern software delivery",
    }
    
    def __init__(self, conservative_mode: bool = False):
        """
        Initialize the InferenceTransparency system.
        
        Args:
            conservative_mode: If True, reduce inference aggressiveness
        """
        self.conservative_mode = conservative_mode
        self._inference_log: List[InferenceExplanation] = []
        self._documented_patterns = self._create_documented_patterns()
    
    def document_patterns(self) -> List[InferencePattern]:
        """
        Document inference patterns and heuristics for filling missing information.
        
        Returns:
            List of documented inference patterns with descriptions and examples
        """
        return self._documented_patterns
    
    def get_pattern(self, pattern_id: str) -> Optional[InferencePattern]:
        """
        Get a specific inference pattern by ID.
        
        Args:
            pattern_id: The pattern identifier
            
        Returns:
            InferencePattern if found, None otherwise
        """
        for pattern in self._documented_patterns:
            if pattern.pattern_id == pattern_id:
                return pattern
        return None
    
    def explain_inference(
        self,
        inference_type: str,
        inferred_value: str,
        confidence: float,
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> InferenceExplanation:
        """
        Provide detailed reasoning for an inference.
        
        Args:
            inference_type: Type of inference (e.g., "backend_framework")
            inferred_value: The value that was inferred
            confidence: Confidence score (0.0-1.0)
            evidence: List of evidence sources used
            context: Optional additional context
            
        Returns:
            InferenceExplanation with detailed reasoning
        """
        strength = self.distinguish_strength(confidence, evidence)
        reasoning = self._build_reasoning(inference_type, inferred_value, evidence, context)
        industry_ref = self._get_industry_standard(inference_type, inferred_value)
        alternatives = self._get_alternatives(inference_type, inferred_value)
        conservative_note = self._get_conservative_note(confidence, evidence) if self.conservative_mode else None
        
        explanation = InferenceExplanation(
            inference_type=inference_type,
            inferred_value=inferred_value,
            confidence=confidence,
            strength=strength,
            reasoning=reasoning,
            evidence_sources=evidence,
            industry_standard_reference=industry_ref,
            alternative_values=alternatives,
            conservative_note=conservative_note,
        )
        
        self._inference_log.append(explanation)
        return explanation
    
    def distinguish_strength(
        self,
        confidence: float,
        evidence: List[Dict[str, Any]],
    ) -> InferenceStrength:
        """
        Distinguish between strong and weak inferences.
        
        Strong inferences are based on clear patterns and multiple evidence sources.
        Weak inferences are educated guesses with limited evidence.
        
        Args:
            confidence: Confidence score (0.0-1.0)
            evidence: List of evidence sources used
            
        Returns:
            InferenceStrength classification
        """
        # Count evidence sources
        source_count = len(evidence)
        
        # Check for direct pattern matches
        has_direct_match = any(
            e.get("type") == "PATTERN_MATCH" and e.get("match_quality") == "direct"
            for e in evidence
        )
        
        # Check for multiple independent sources
        source_types = set(e.get("type") for e in evidence)
        has_multiple_sources = len(source_types) >= 2
        
        # Determine strength based on evidence quality
        if confidence >= 0.85 and (has_direct_match or has_multiple_sources):
            return InferenceStrength.STRONG
        elif confidence >= 0.70 and source_count >= 1:
            return InferenceStrength.MODERATE
        else:
            return InferenceStrength.WEAK
    
    def get_inference_log(self) -> List[InferenceExplanation]:
        """
        Get the log of all inferences made.
        
        Returns:
            List of InferenceExplanation objects
        """
        return self._inference_log.copy()
    
    def get_transparency_report(self) -> Dict[str, Any]:
        """
        Generate a transparency report for all inferences.
        
        Returns:
            Dictionary with transparency statistics
        """
        if not self._inference_log:
            return {
                "total_inferences": 0,
                "strong_inferences": 0,
                "moderate_inferences": 0,
                "weak_inferences": 0,
                "average_confidence": 0.0,
                "patterns_used": [],
            }
        
        strong = sum(1 for e in self._inference_log if e.strength == InferenceStrength.STRONG)
        moderate = sum(1 for e in self._inference_log if e.strength == InferenceStrength.MODERATE)
        weak = sum(1 for e in self._inference_log if e.strength == InferenceStrength.WEAK)
        avg_confidence = sum(e.confidence for e in self._inference_log) / len(self._inference_log)
        
        # Get unique patterns used
        patterns_used = list(set(e.inference_type for e in self._inference_log))
        
        return {
            "total_inferences": len(self._inference_log),
            "strong_inferences": strong,
            "moderate_inferences": moderate,
            "weak_inferences": weak,
            "average_confidence": round(avg_confidence, 2),
            "patterns_used": patterns_used,
            "conservative_mode": self.conservative_mode,
        }
    
    def should_use_explicit_marker(
        self,
        confidence: float,
        evidence: List[Dict[str, Any]],
    ) -> bool:
        """
        Determine if explicit marker ("To be determined") should be used.
        
        This implements the "avoid over-inference" requirement.
        
        Args:
            confidence: Confidence score
            evidence: List of evidence sources
            
        Returns:
            True if explicit marker should be used
        """
        if self.conservative_mode:
            # In conservative mode, use explicit marker for lower confidence
            return confidence < 0.75 or len(evidence) == 0
        
        # Default: use explicit marker only for very low confidence or no evidence
        return confidence < 0.6 or len(evidence) == 0
    
    def _create_documented_patterns(self) -> List[InferencePattern]:
        """Create documented inference patterns with descriptions and examples."""
        return [
            InferencePattern(
                pattern_id="backend_framework_pattern",
                description="Infer backend framework from package dependencies or code patterns",
                inference_type="backend_framework",
                conditions=[
                    "package.json contains 'express' → Express framework",
                    "pyproject.toml contains 'fastapi' → FastAPI framework",
                    "requirements.txt contains 'django' → Django framework",
                    "go.mod contains 'gin-gonic' → Gin framework",
                ],
                confidence_range=(0.75, 0.90),
                examples=[
                    "package.json: {\"express\": \"^4.18.0\"} → Backend: Express",
                    "pyproject.toml: dependencies = [\"fastapi>=0.100\"] → Backend: FastAPI",
                ],
                industry_standard_basis="Framework detection from package dependencies is standard practice",
                conservative_mode_adjustment="Reduce confidence by 0.10 in conservative mode",
            ),
            InferencePattern(
                pattern_id="frontend_framework_pattern",
                description="Infer frontend framework from package dependencies",
                inference_type="frontend_framework",
                conditions=[
                    "package.json contains 'react' → React framework",
                    "package.json contains 'vue' → Vue framework",
                    "package.json contains '@angular/core' → Angular framework",
                ],
                confidence_range=(0.80, 0.95),
                examples=[
                    "package.json: {\"react\": \"^18.2.0\"} → Frontend: React",
                    "package.json: {\"vue\": \"^3.3.0\"} → Frontend: Vue",
                ],
                industry_standard_basis="Frontend framework detection from package.json is industry standard",
            ),
            InferencePattern(
                pattern_id="database_pattern",
                description="Infer database from dependencies or configuration files",
                inference_type="database",
                conditions=[
                    "dependencies contain 'postgresql' → PostgreSQL",
                    "dependencies contain 'mongoose' → MongoDB",
                    "dependencies contain 'mysql' → MySQL",
                    "docker-compose.yml specifies postgres → PostgreSQL",
                ],
                confidence_range=(0.70, 0.90),
                examples=[
                    "requirements.txt: psycopg2-binary → Database: PostgreSQL",
                    "package.json: {\"mongoose\": \"^6.0\"} → Database: MongoDB",
                ],
                industry_standard_basis="PostgreSQL is the most popular open-source relational database",
                conservative_mode_adjustment="Require at least 2 evidence sources for database inference",
            ),
            InferencePattern(
                pattern_id="architecture_pattern",
                description="Infer architecture pattern from directory structure",
                inference_type="architecture",
                conditions=[
                    "Contains 'services/' or 'microservices/' → Microservices",
                    "Contains 'api/', 'models/', 'controllers/' → Layered/MVC",
                    "Single directory with all code → Monolithic",
                ],
                confidence_range=(0.60, 0.85),
                examples=[
                    "Directory structure: services/user/, services/payment/ → Microservices",
                    "Directory structure: api/, models/, controllers/ → Layered Architecture",
                ],
                industry_standard_basis="Directory structure analysis is common for architecture inference",
                conservative_mode_adjustment="Use explicit marker when directory structure is ambiguous",
            ),
            InferencePattern(
                pattern_id="language_pattern",
                description="Infer programming language from file extensions",
                inference_type="language",
                conditions=[
                    "Majority of .py files → Python",
                    "Majority of .js/.ts files → JavaScript/TypeScript",
                    "Majority of .go files → Go",
                ],
                confidence_range=(0.85, 0.99),
                examples=[
                    "Project has 500 .py files and 10 .js files → Language: Python",
                    "Project has 300 .ts files and 50 .py files → Language: TypeScript",
                ],
                industry_standard_basis="File extension analysis is the most reliable inference method",
            ),
            InferencePattern(
                pattern_id="cache_pattern",
                description="Infer caching solution from dependencies",
                inference_type="cache",
                conditions=[
                    "dependencies contain 'redis' → Redis",
                    "dependencies contain 'memcached' → Memcached",
                ],
                confidence_range=(0.75, 0.90),
                examples=[
                    "requirements.txt: redis → Cache: Redis",
                    "package.json: {\"memcached\": \"^3.0\"} → Cache: Memcached",
                ],
                industry_standard_basis="Redis is the de facto standard for application caching",
            ),
        ]
    
    def _build_reasoning(
        self,
        inference_type: str,
        inferred_value: str,
        evidence: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build a human-readable reasoning string for the inference."""
        reasoning_parts = []
        
        # Describe evidence found
        if evidence:
            evidence_types = [e.get("type", "unknown") for e in evidence]
            if len(evidence) == 1:
                reasoning_parts.append(f"Found {evidence_types[0].lower().replace('_', ' ')}")
            else:
                reasoning_parts.append(f"Found {len(evidence)} evidence sources: {', '.join(evidence_types).lower().replace('_', ' ')}")
        
        # Describe the inference
        type_descriptions = {
            "backend_framework": "backend framework",
            "frontend_framework": "frontend framework",
            "database": "database",
            "cache": "caching solution",
            "architecture": "architecture pattern",
            "language": "programming language",
        }
        
        type_desc = type_descriptions.get(inference_type, inference_type)
        reasoning_parts.append(f"inferred {type_desc} as {inferred_value}")
        
        # Add context if available
        if context:
            context_keys = list(context.keys())[:3]  # Limit to 3 keys
            if context_keys:
                reasoning_parts.append(f"based on context: {', '.join(context_keys)}")
        
        return " ".join(reasoning_parts) + "."
    
    def _get_industry_standard(
        self,
        inference_type: str,
        inferred_value: str,
    ) -> Optional[str]:
        """Get industry standard reference for the inference."""
        standard_mapping = {
            ("backend_framework", "FastAPI"): self.INDUSTRY_STANDARDS.get("fastapi_python"),
            ("frontend_framework", "React"): self.INDUSTRY_STANDARDS.get("react_typescript"),
            ("database", "PostgreSQL"): self.INDUSTRY_STANDARDS.get("postgresql_enterprise"),
            ("cache", "Redis"): self.INDUSTRY_STANDARDS.get("redis_caching"),
        }
        
        return standard_mapping.get((inference_type, inferred_value))
    
    def _get_alternatives(
        self,
        inference_type: str,
        inferred_value: str,
    ) -> List[str]:
        """Get alternative values that were considered."""
        alternatives_map = {
            "backend_framework": ["FastAPI", "Express", "Django", "Flask", "Gin"],
            "frontend_framework": ["React", "Vue", "Angular", "Svelte"],
            "database": ["PostgreSQL", "MongoDB", "MySQL", "Redis"],
            "cache": ["Redis", "Memcached"],
            "architecture": ["Monolithic", "Microservices", "Layered", "Serverless"],
            "language": ["Python", "TypeScript", "Go", "Java"],
        }
        
        all_alternatives = alternatives_map.get(inference_type, [])
        return [a for a in all_alternatives if a != inferred_value]
    
    def _get_conservative_note(
        self,
        confidence: float,
        evidence: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Get a note about conservative inference mode."""
        if confidence < 0.7:
            return "In conservative mode, this inference has lower confidence due to limited evidence."
        if len(evidence) < 2:
            return "In conservative mode, multiple evidence sources are preferred for higher confidence."
        return None