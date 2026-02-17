"""
Semantic Equivalence Validation for the Steering Assistant v02.1.

This module provides the SemanticEquivalenceValidator class for comparing
content meaning and determining semantic equivalence using NLP-based techniques.

Requirements: 27.1-27.7 (v02.1)
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class KeyFact:
    """Represents a key fact extracted from content for comparison."""
    category: str  # e.g., "technology", "architecture", "version", "framework"
    key: str       # e.g., "database", "backend_framework", "python_version"
    value: str     # e.g., "PostgreSQL", "FastAPI", "3.11"
    confidence: float = 0.8  # 0.0-1.0, confidence in extracted fact


@dataclass
class EquivalenceResult:
    """Result of semantic equivalence comparison."""
    is_equivalent: bool
    confidence: float  # 0.0-1.0, how confident we are in the equivalence decision
    matching_facts: List[KeyFact] = field(default_factory=list)
    mismatched_facts: List[KeyFact] = field(default_factory=list)
    missing_in_content1: List[str] = field(default_factory=list)
    missing_in_content2: List[str] = field(default_factory=list)
    ambiguous_facts: List[Dict[str, Any]] = field(default_factory=list)
    needs_human_review: bool = False
    explanation: str = ""
    strict_mode_used: bool = False


@dataclass
class ValidationLog:
    """Log entry for semantic equivalence validation."""
    timestamp: str
    content1_hash: str
    content2_hash: str
    result: Dict[str, Any]
    strict_mode: bool
    ambiguous_cases: List[Dict[str, Any]] = field(default_factory=list)


class SemanticEquivalenceValidator:
    """
    Validates semantic equivalence between two pieces of content.
    
    Uses NLP-based techniques to extract key facts, relationships, and technical
    specifications, then compares them to determine if content is semantically
    equivalent even when wording differs.
    
    Requirements: 27.1-27.7 (v02.1)
    """
    
    # Technical specification patterns for fact extraction
    TECH_PATTERNS = {
        "language": [
            r"(?:language|written in|uses?)\s*[:\s]+([A-Za-z]+(?:\s+[0-9.]+)?)",
            r"([A-Za-z]+)\s+(?:version\s+)?[0-9.]+",
            r"\b(Python|JavaScript|TypeScript|Java|Go|Rust|Ruby|PHP|C\+\+|C#)\b",
        ],
        "framework": [
            r"(?:framework|backend|frontend)\s*[:\s]+([A-Za-z]+(?:\.[A-Za-z0-9]+)?)",
            r"([A-Za-z]+(?:JS|\.js)?)\s+framework",
            r"\b(FastAPI|Express|Django|Flask|React|Vue|Angular|Svelte|Next\.js|Nuxt\.js)\b",
        ],
        "database": [
            r"(?:database|DB|data store)\s*[:\s]+([A-Za-z]+(?:\s+[0-9.]+)?)",
            r"([A-Za-z]+(?:SQL|NoSQL)?)\s+(?:database|storage)",
            r"\b(PostgreSQL|MongoDB|MySQL|Redis|Cassandra|SQLite|Oracle)\b",
        ],
        "version": [
            r"version\s*[:\s]+([0-9]+(?:\.[0-9]+)*)",
            r"\b([0-9]+(?:\.[0-9]+){1,2})\b",  # Standalone version numbers
        ],
        "architecture": [
            r"(?:architecture|pattern|design)\s*[:\s]+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
            r"(microservices|monolithic|serverless|layered|event[- ]driven|modular)",
        ],
        "api": [
            r"(?:API|REST|GraphQL|gRPC|web service)",
            r"(?:API|interface)\s*[:\s]+([A-Za-z]+)",
            r"\b(REST|RESTful|GraphQL|gRPC)\b",
        ],
        "container": [
            r"(?:container|containerization)\s*[:\s]+([A-Za-z]+)",
            r"(Docker|Podman|containerd)",
        ],
        "cloud": [
            r"(?:cloud|platform|hosting)\s*[:\s]+([A-Za-z]+)",
            r"(AWS|Azure|GCP|Google Cloud|Heroku|Vercel|Netlify)",
        ],
    }
    
    # Synonym mappings for tolerating wording variations
    SYNONYMS = {
        "uses": ["utilizes", "employs", "leverages", "runs on", "built with"],
        "backend": ["server-side", "server", "backend service", "backend API"],
        "frontend": ["client", "client-side", "UI", "user interface"],
        "database": ["DB", "data store", "persistence", "data layer"],
        "framework": ["library", "platform", "toolkit"],
        "fastapi": ["fast api", "fast-api", "FastAPI"],
        "express": ["Express", "expressjs", "Express.js"],
        "react": ["React", "ReactJS", "React.js"],
        "postgresql": ["PostgreSQL", "Postgres", "pg"],
        "mongodb": ["MongoDB", "Mongo", "mongo"],
        "microservices": ["micro-services", "microservice", "service-oriented"],
        "monolithic": ["monolith", "monolithically"],
    }
    
    # Substantive difference indicators (these should NOT be tolerated)
    SUBSTANTIVE_DIFFERENCES = [
        ("python", "javascript"),
        ("python", "java"),
        ("python", "go"),
        ("javascript", "java"),
        ("typescript", "javascript"),
        ("react", "vue"),
        ("react", "angular"),
        ("fastapi", "express"),
        ("fastapi", "django"),
        ("postgresql", "mongodb"),
        ("postgresql", "mysql"),
        ("mysql", "postgresql"),
        ("mongodb", "postgresql"),
        ("microservices", "monolithic"),
        ("rest", "graphql"),
        ("graphql", "rest"),
        ("docker", "kubernetes"),
        ("kubernetes", "docker"),
        ("aws", "azure"),
        ("aws", "gcp"),
    ]
    
    def __init__(
        self,
        strict_equivalence: bool = False,
        min_confidence_threshold: float = 0.7,
        log_enabled: bool = True
    ):
        """
        Initialize the SemanticEquivalenceValidator.
        
        Args:
            strict_equivalence: If True, use exact matching instead of semantic equivalence
            min_confidence_threshold: Minimum confidence threshold for equivalence decision
            log_enabled: Whether to log validation results
        """
        self.strict_equivalence = strict_equivalence
        self.min_confidence_threshold = min_confidence_threshold
        self.log_enabled = log_enabled
        self.validation_logs: List[ValidationLog] = []
    
    def extract_key_facts(self, content: str) -> List[KeyFact]:
        """
        Extract key facts, relationships, and technical specifications from content.
        
        Args:
            content: The content to extract facts from
            
        Returns:
            List of KeyFact objects representing extracted facts
            
        Requirements: 27.2
        """
        facts: List[KeyFact] = []
        content_lower = content.lower()
        
        # Extract technology facts
        for category, patterns in self.TECH_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        # Handle multi-group matches (e.g., "Python 3.11")
                        match = match[0] if match[0] else (match[1] if len(match) > 1 else "")
                    if match and len(match) > 1:
                        # Normalize the value
                        value = self._normalize_value(match)
                        fact = KeyFact(
                            category=category,
                            key=category,
                            value=value,
                            confidence=0.85
                        )
                        # Avoid duplicates
                        if not any(f.value.lower() == value.lower() and f.category == category for f in facts):
                            facts.append(fact)
        
        # Extract technology mentions from plain text
        tech_mentions = self._extract_tech_mentions(content)
        for mention in tech_mentions:
            if not any(f.value.lower() == mention.value.lower() and f.category == mention.category for f in facts):
                facts.append(mention)
        
        # Extract structured content sections
        section_pattern = r"(?:^|\n)(#{1,6})\s+(.+?)(?=\n#{1,6}|$)"
        section_matches = re.findall(section_pattern, content, re.MULTILINE)
        for level, title in section_matches:
            if len(title.strip()) > 2:
                fact = KeyFact(
                    category="section",
                    key="section_title",
                    value=title.strip().lower(),
                    confidence=0.9
                )
                if not any(f.value == fact.value for f in facts):
                    facts.append(fact)
        
        # Extract bullet points and key statements
        bullet_pattern = r"^\s*[-*•]\s+(.+?)$"
        bullet_matches = re.findall(bullet_pattern, content, re.MULTILINE)
        for bullet in bullet_matches:
            if len(bullet.strip()) > 5:
                # Check if bullet contains technical info
                fact = self._extract_fact_from_bullet(bullet.strip())
                if fact:
                    facts.append(fact)
        
        # Extract tables (key-value pairs)
        table_pattern = r"\|(.+?)\|"
        table_matches = re.findall(table_pattern, content)
        for table_row in table_matches:
            cells = [c.strip() for c in table_row.split("|") if c.strip()]
            if len(cells) >= 2:
                # First cell is typically key, second is value
                key = cells[0].lower()
                value = cells[1]
                if len(key) > 2 and len(value) > 0:
                    fact = KeyFact(
                        category="table",
                        key=key,
                        value=value,
                        confidence=0.9
                    )
                    if not any(f.key == key and f.value == value for f in facts):
                        facts.append(fact)
        
        return facts
    
    def _extract_tech_mentions(self, content: str) -> List[KeyFact]:
        """Extract technology mentions from plain text content."""
        facts: List[KeyFact] = []
        content_lower = content.lower()
        
        # Technology patterns to find in text
        tech_patterns = {
            "language": [
                r"\bpython\b(?:\s+[0-9.]+)?",
                r"\bjavascript\b",
                r"\btypescript\b",
                r"\bjava\b(?:\s+[0-9.]+)?",
                r"\bgo\b(?:\s+[0-9.]+)?",
                r"\brust\b",
                r"\bruby\b",
                r"\bphp\b",
                r"\bc\+\+\b",
                r"\bc#\b",
                r"\bnode\.?js\b(?:\s+v?[0-9.]+)?",
            ],
            "framework": [
                r"\bfastapi\b",
                r"\bexpress\b(?:\s+js)?",
                r"\bdjango\b",
                r"\bflask\b",
                r"\breact\b(?:\s+js)?",
                r"\bvue\.?js\b",
                r"\bangular\b",
                r"\bsvelte\b",
                r"\bnext\.?js\b",
                r"\bnuxt\.?js\b",
            ],
            "database": [
                r"\bpostgresql\b",
                r"\bpostgres\b",
                r"\bmongodb\b",
                r"\bmongo\b",
                r"\bmysql\b",
                r"\bredis\b",
                r"\bcassandra\b",
                r"\bsqlite\b",
                r"\boracle\b",
            ],
            "architecture": [
                r"\bmicroservices?\b",
                r"\bmonolithic\b",
                r"\bserverless\b",
                r"\blayered\b",
                r"\bevent[- ]driven\b",
                r"\bmodular\b",
            ],
            "api": [
                r"\brest\b(?:\s+api)?",
                r"\brestful\b",
                r"\bgraphql\b",
                r"\bgrpc\b",
            ],
            "container": [
                r"\bdocker\b",
                r"\bkubernetes\b",
                r"\bk8s\b",
                r"\bpodman\b",
            ],
            "cloud": [
                r"\baws\b",
                r"\bazure\b",
                r"\bgcp\b",
                r"\bgoogle cloud\b",
                r"\bheroku\b",
                r"\bvercel\b",
                r"\bnetlify\b",
            ],
        }
        
        for category, patterns in tech_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content_lower)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else ""
                    if match:
                        # Normalize the value
                        value = self._normalize_value(match)
                        # Skip if value looks like a version number
                        if re.match(r"^[0-9.]+$", value):
                            continue
                        fact = KeyFact(
                            category=category,
                            key=value.lower(),
                            value=value,
                            confidence=0.8
                        )
                        if not any(f.value.lower() == value.lower() and f.category == category for f in facts):
                            facts.append(fact)
        
        return facts
    
    def _normalize_value(self, value: str) -> str:
        """Normalize a value for comparison."""
        # Remove extra whitespace
        value = " ".join(value.split())
        # Capitalize first letter for consistency
        if value:
            value = value[0].upper() + value[1:] if len(value) > 1 else value.upper()
        return value
    
    def _extract_fact_from_bullet(self, bullet: str) -> Optional[KeyFact]:
        """Extract a fact from a bullet point."""
        bullet_lower = bullet.lower()
        
        # Check for technology mentions
        tech_keywords = {
            "python": "language",
            "javascript": "language",
            "typescript": "language",
            "java": "language",
            "go": "language",
            "rust": "language",
            "fastapi": "framework",
            "express": "framework",
            "django": "framework",
            "flask": "framework",
            "react": "framework",
            "vue": "framework",
            "angular": "framework",
            "postgresql": "database",
            "mongodb": "database",
            "mysql": "database",
            "redis": "database",
            "docker": "container",
            "kubernetes": "container",
            "aws": "cloud",
            "azure": "cloud",
            "gcp": "cloud",
            "node": "language",
            "nodejs": "language",
        }
        
        for tech, category in tech_keywords.items():
            if tech in bullet_lower:
                return KeyFact(
                    category=category,
                    key=tech,
                    value=tech,
                    confidence=0.85
                )
        
        # Also check for framework patterns like "FastAPI framework"
        framework_patterns = [
            (r"fastapi", "framework", "FastAPI"),
            (r"express", "framework", "Express"),
            (r"django", "framework", "Django"),
            (r"flask", "framework", "Flask"),
            (r"react", "framework", "React"),
            (r"vue\.?js", "framework", "Vue"),
            (r"angular", "framework", "Angular"),
        ]
        
        for pattern, category, value in framework_patterns:
            if re.search(pattern, bullet_lower):
                return KeyFact(
                    category=category,
                    key=value.lower(),
                    value=value,
                    confidence=0.85
                )
        
        return None
    
    def tolerate_wording_variations(
        self,
        fact1: KeyFact,
        fact2: KeyFact
    ) -> bool:
        """
        Check if two facts are equivalent despite wording variations.
        
        Args:
            fact1: First fact to compare
            fact2: Second fact to compare
            
        Returns:
            True if facts are equivalent despite wording differences
            
        Requirements: 27.4
        """
        # Same category and key
        if fact1.category != fact2.category:
            return False
        
        value1 = fact1.value.lower().strip()
        value2 = fact2.value.lower().strip()
        
        # Exact match (case-insensitive)
        if value1 == value2:
            return True
        
        # Check synonyms
        for canonical, synonyms in self.SYNONYMS.items():
            all_variants = [canonical] + synonyms
            if any(v in value1 for v in all_variants) and any(v in value2 for v in all_variants):
                return True
        
        # Check if one is a substring of the other (for version numbers, etc.)
        if value1 in value2 or value2 in value1:
            return True
        
        # Check for common prefixes/suffixes
        if value1.replace("-", "") == value2.replace("-", ""):
            return True
        
        return False
    
    def check_semantic_equivalence(
        self,
        content1: str,
        content2: str,
        strict_equivalence: Optional[bool] = None
    ) -> EquivalenceResult:
        """
        Compare content meaning to determine semantic equivalence.
        
        Args:
            content1: First content to compare
            content2: Second content to compare
            strict_equivalence: Override for strict equivalence mode
            
        Returns:
            EquivalenceResult with equivalence decision and details
            
        Requirements: 27.1, 27.3, 27.4
        """
        use_strict = strict_equivalence if strict_equivalence is not None else self.strict_equivalence
        
        # Extract key facts from both contents
        facts1 = self.extract_key_facts(content1)
        facts2 = self.extract_key_facts(content2)
        
        # If strict mode, do exact comparison
        if use_strict:
            return self._check_strict_equivalence(content1, content2, facts1, facts2)
        
        # Otherwise, do semantic equivalence check
        return self._check_semantic_equivalence(content1, content2, facts1, facts2)
    
    def _check_strict_equivalence(
        self,
        content1: str,
        content2: str,
        facts1: List[KeyFact],
        facts2: List[KeyFact]
    ) -> EquivalenceResult:
        """Check strict (exact) equivalence."""
        # Normalize content for comparison
        normalized1 = self._normalize_for_strict(content1)
        normalized2 = self._normalize_for_strict(content2)
        
        is_equivalent = normalized1 == normalized2
        
        result = EquivalenceResult(
            is_equivalent=is_equivalent,
            confidence=1.0 if is_equivalent else 0.95,
            matching_facts=facts1 if is_equivalent else [],
            mismatched_facts=facts1 if not is_equivalent else [],
            needs_human_review=False,
            explanation="Strict equivalence check: content is " + ("identical" if is_equivalent else "different"),
            strict_mode_used=True
        )
        
        # Log the result
        self._log_validation(content1, content2, result)
        
        return result
    
    def _normalize_for_strict(self, content: str) -> str:
        """Normalize content for strict comparison."""
        # For strict mode, we want to preserve exact content
        # Only remove trailing newlines, not spaces
        lines = content.split("\n")
        # Remove empty lines at the end (but preserve spaces in non-empty lines)
        while lines and not lines[-1] and lines[-1] == "":
            lines.pop()
        # Return the first line only (for single-line content)
        # This preserves trailing spaces within the line
        return lines[0] if lines else ""
    
    def _check_semantic_equivalence(
        self,
        content1: str,
        content2: str,
        facts1: List[KeyFact],
        facts2: List[KeyFact]
    ) -> EquivalenceResult:
        """Check semantic equivalence (allowing for wording variations)."""
        matching_facts: List[KeyFact] = []
        mismatched_facts: List[KeyFact] = []
        missing_in_content1: List[str] = []
        missing_in_content2: List[str] = []
        ambiguous_cases: List[Dict[str, Any]] = []
        
        # Match facts from content1 to content2
        for fact1 in facts1:
            matched = False
            for fact2 in facts2:
                # Check if facts are equivalent (allowing wording variations)
                if self.tolerate_wording_variations(fact1, fact2):
                    matching_facts.append(fact1)
                    matched = True
                    break
                # Check for substantive differences
                if self._is_substantive_difference(fact1.value, fact2.value):
                    mismatched_facts.append(fact1)
                    matched = True
                    break
            
            if not matched:
                # Check if this fact has a potential match that's ambiguous
                if self._has_potential_match(fact1, facts2):
                    ambiguous_cases.append({
                        "fact": fact1.value,
                        "category": fact1.category,
                        "reason": "Potential match found but confidence is low"
                    })
                else:
                    missing_in_content2.append(fact1.value)
        
        # Find facts in content2 that weren't matched
        for fact2 in facts2:
            if not any(self.tolerate_wording_variations(f, fact2) for f in facts1):
                if not any(d.get("fact") == fact2.value for d in ambiguous_cases):
                    missing_in_content1.append(fact2.value)
        
        # Calculate equivalence confidence
        total_facts = len(facts1) + len(facts2)
        if total_facts == 0:
            # No facts to compare - consider equivalent
            confidence = 0.8
            is_equivalent = True
            explanation = "No key facts to compare - content considered equivalent"
        else:
            # Calculate match ratio based on unique matching categories
            categories1 = set(f.category for f in facts1)
            categories2 = set(f.category for f in facts2)
            matching_categories = categories1 & categories2
            all_categories = categories1 | categories2
            
            # Base confidence on category overlap
            if all_categories:
                category_match_ratio = len(matching_categories) / len(all_categories)
            else:
                category_match_ratio = 1.0
            
            # Fact match ratio
            if len(facts1) > 0:
                fact_match_ratio = len(matching_facts) / len(facts1)
            else:
                fact_match_ratio = 1.0
            
            # Combined confidence - more lenient calculation
            confidence = 0.5 + (category_match_ratio * 0.3) + (fact_match_ratio * 0.2)
            
            # Reduce confidence for substantive differences
            if mismatched_facts:
                confidence -= (len(mismatched_facts) * 0.15)
            
            # Reduce confidence for missing facts (but not too much)
            missing_ratio = (len(missing_in_content1) + len(missing_in_content2)) / max(total_facts, 1)
            confidence -= missing_ratio * 0.1
            
            # Flag for human review if ambiguous
            needs_review = (
                len(ambiguous_cases) > 0 or
                confidence < self.min_confidence_threshold or
                len(mismatched_facts) > 0
            )
            
            # Determine equivalence - more lenient
            is_equivalent = (
                len(mismatched_facts) == 0 and
                confidence >= self.min_confidence_threshold and
                category_match_ratio >= 0.5  # At least 50% of categories match
            )
            
            explanation = self._generate_explanation(
                is_equivalent, confidence, matching_facts, mismatched_facts,
                missing_in_content1, missing_in_content2, ambiguous_cases
            )
        
        result = EquivalenceResult(
            is_equivalent=is_equivalent,
            confidence=max(0.0, min(1.0, confidence)),
            matching_facts=matching_facts,
            mismatched_facts=mismatched_facts,
            missing_in_content1=missing_in_content1,
            missing_in_content2=missing_in_content2,
            ambiguous_facts=ambiguous_cases,
            needs_human_review=len(ambiguous_cases) > 0 or confidence < self.min_confidence_threshold,
            explanation=explanation,
            strict_mode_used=False
        )
        
        # Log the result
        self._log_validation(content1, content2, result)
        
        return result
    
    def _is_substantive_difference(self, value1: str, value2: str) -> bool:
        """Check if two values represent a substantive difference."""
        v1 = value1.lower().strip()
        v2 = value2.lower().strip()
        
        # Check explicit substantive differences
        for diff in self.SUBSTANTIVE_DIFFERENCES:
            if (v1 in diff and v2 in diff) and v1 != v2:
                return True
        
        # Version differences are substantive (3.11 vs 3.10)
        if self._is_version_number(v1) and self._is_version_number(v2):
            if v1 != v2:
                return True
        
        return False
    
    def _is_version_number(self, value: str) -> bool:
        """Check if a value looks like a version number."""
        # Version numbers typically look like "3.11", "3.10.1", "1.0.0"
        return bool(re.match(r"^[0-9]+(?:\.[0-9]+)+$", value))
    
    def _has_potential_match(self, fact: KeyFact, facts: List[KeyFact]) -> bool:
        """Check if there's a potential but uncertain match for a fact."""
        for other in facts:
            if fact.category == other.category:
                # Same category but different value - potential match
                if not self.tolerate_wording_variations(fact, other):
                    return True
        return False
    
    def _generate_explanation(
        self,
        is_equivalent: bool,
        confidence: float,
        matching_facts: List[KeyFact],
        mismatched_facts: List[KeyFact],
        missing_in_content1: List[str],
        missing_in_content2: List[str],
        ambiguous_cases: List[Dict[str, Any]]
    ) -> str:
        """Generate a human-readable explanation of the equivalence result."""
        parts = []
        
        if is_equivalent:
            parts.append("Content is semantically equivalent.")
        else:
            parts.append("Content is NOT semantically equivalent.")
        
        parts.append(f"Confidence: {confidence:.0%}")
        
        if matching_facts:
            categories = set(f.category for f in matching_facts)
            parts.append(f"Matching facts in {len(matching_facts)} categories: {', '.join(categories)}")
        
        if mismatched_facts:
            values = [f.value for f in mismatched_facts]
            parts.append(f"Substantive differences found: {', '.join(values)}")
        
        if missing_in_content1 or missing_in_content2:
            parts.append("Some facts are present in one content but not the other.")
        
        if ambiguous_cases:
            facts = [a["fact"] for a in ambiguous_cases]
            parts.append(f"Ambiguous cases requiring review: {', '.join(facts)}")
        
        return " ".join(parts)
    
    def _log_validation(
        self,
        content1: str,
        content2: str,
        result: EquivalenceResult
    ) -> None:
        """Log validation results for analysis and improvement."""
        if not self.log_enabled:
            return
        
        import hashlib
        import datetime
        
        content1_hash = hashlib.sha256(content1.encode()).hexdigest()[:16]
        content2_hash = hashlib.sha256(content2.encode()).hexdigest()[:16]
        
        log_entry = ValidationLog(
            timestamp=datetime.datetime.utcnow().isoformat(),
            content1_hash=content1_hash,
            content2_hash=content2_hash,
            result={
                "is_equivalent": result.is_equivalent,
                "confidence": result.confidence,
                "matching_facts_count": len(result.matching_facts),
                "mismatched_facts_count": len(result.mismatched_facts),
                "missing_in_content1": result.missing_in_content1,
                "missing_in_content2": result.missing_in_content2,
                "needs_human_review": result.needs_human_review,
                "explanation": result.explanation,
            },
            strict_mode=result.strict_mode_used,
            ambiguous_cases=result.ambiguous_facts
        )
        
        self.validation_logs.append(log_entry)
    
    def get_validation_logs(self) -> List[Dict[str, Any]]:
        """
        Get all validation logs for analysis.
        
        Returns:
            List of validation log entries
            
        Requirements: 27.6
        """
        return [
            {
                "timestamp": log.timestamp,
                "content1_hash": log.content1_hash,
                "content2_hash": log.content2_hash,
                "result": log.result,
                "strict_mode": log.strict_mode,
                "ambiguous_cases": log.ambiguous_cases
            }
            for log in self.validation_logs
        ]
    
    def compare_multiple(
        self,
        contents: Dict[str, str],
        reference_key: Optional[str] = None
    ) -> Dict[str, EquivalenceResult]:
        """
        Compare multiple content pieces for semantic equivalence.
        
        Args:
            contents: Dictionary mapping names to content
            reference_key: If provided, compare all others to this reference
            
        Returns:
            Dictionary mapping content pairs to their equivalence results
            
        Requirements: 27.1-27.7
        """
        results: Dict[str, EquivalenceResult] = {}
        content_list = list(contents.items())
        
        if len(content_list) < 2:
            return results
        
        if reference_key and reference_key in contents:
            # Compare all others to reference
            reference_content = contents[reference_key]
            for name, content in contents.items():
                if name != reference_key:
                    key = f"{reference_key} vs {name}"
                    results[key] = self.check_semantic_equivalence(reference_content, content)
        else:
            # Compare all pairs
            for i in range(len(content_list)):
                for j in range(i + 1, len(content_list)):
                    name1, content1 = content_list[i]
                    name2, content2 = content_list[j]
                    key = f"{name1} vs {name2}"
                    results[key] = self.check_semantic_equivalence(content1, content2)
        
        return results