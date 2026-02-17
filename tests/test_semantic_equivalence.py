"""
Property-based tests for semantic equivalence validation.

Validates: Requirements 27.1-27.7 (v02.1)
Property 27: Semantic Equivalence Validation
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.semantic_equivalence import (
    SemanticEquivalenceValidator,
    KeyFact,
    EquivalenceResult,
)


class TestSemanticEquivalenceValidation:
    """Tests for semantic equivalence validation correctness."""
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_extracts_key_facts_from_content(self):
        """
        WHEN comparing generated content for equivalence, THE Steering_Assistant
        SHALL extract key facts, relationships, and technical specifications.
        """
        content = """
# Technology Stack

## Backend
- Language: Python 3.11
- Framework: FastAPI
- Runtime: CPython

## Database
- Primary: PostgreSQL 15
- Cache: Redis 7
        """
        
        validator = SemanticEquivalenceValidator()
        facts = validator.extract_key_facts(content)
        
        # Should extract key facts
        assert len(facts) >= 1
        
        # Should extract technology facts
        fact_categories = [f.category for f in facts]
        assert any(cat in fact_categories for cat in ["language", "framework", "database", "version"])
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_considers_content_equivalent_with_matching_key_facts(self):
        """
        THE Steering_Assistant SHALL consider content semantically equivalent
        if all key facts match, even if wording or structure differs.
        """
        content1 = """
# Tech Stack
Backend: Python with FastAPI
Database: PostgreSQL
        """
        
        content2 = """
# Technology Stack

## Backend Framework
- Python 3.11
- FastAPI framework

## Database
PostgreSQL 15
        """
        
        validator = SemanticEquivalenceValidator()
        result = validator.check_semantic_equivalence(content1, content2)
        
        # Should be considered equivalent despite different wording
        assert result.is_equivalent is True
        assert result.confidence >= 0.7
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_tolerates_minor_wording_variations(self):
        """
        THE Steering_Assistant SHALL implement equivalence validation that
        tolerates minor wording variations but catches substantive differences.
        """
        content1 = "The system uses Python for the backend"
        content2 = "The backend utilizes Python"
        
        validator = SemanticEquivalenceValidator()
        result = validator.check_semantic_equivalence(content1, content2)
        
        # Should tolerate "uses" vs "utilizes"
        assert result.is_equivalent is True
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_catches_substantive_differences(self):
        """
        THE Steering_Assistant SHALL implement equivalence validation that
        tolerates minor wording variations but catches substantive differences.
        """
        content1 = "The backend uses Python"
        content2 = "The backend uses JavaScript"
        
        validator = SemanticEquivalenceValidator()
        result = validator.check_semantic_equivalence(content1, content2)
        
        # Should catch Python vs JavaScript as substantive difference
        assert result.is_equivalent is False
        assert len(result.mismatched_facts) >= 1
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_flags_ambiguous_content_for_human_review(self):
        """
        WHEN semantic equivalence validation is ambiguous, THE Steering_Assistant
        SHALL flag the content for human review.
        """
        content1 = "The system uses a modern programming language"
        content2 = "The system uses Python for backend services"
        
        validator = SemanticEquivalenceValidator(min_confidence_threshold=0.7)
        result = validator.check_semantic_equivalence(content1, content2)
        
        # Should flag for review due to ambiguity
        assert result.needs_human_review is True
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_logs_validation_results(self):
        """
        THE Steering_Assistant SHALL log semantic equivalence validation
        results to improve validation algorithms over time.
        """
        content1 = "Backend: Python"
        content2 = "Backend: Python"
        
        validator = SemanticEquivalenceValidator(log_enabled=True)
        result = validator.check_semantic_equivalence(content1, content2)
        
        logs = validator.get_validation_logs()
        
        # Should have logged the validation
        assert len(logs) >= 1
        assert "timestamp" in logs[0]
        assert "result" in logs[0]
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_strict_equivalence_flag_for_exact_matching(self):
        """
        THE Steering_Assistant SHALL support a `--strict-equivalence` flag
        for exact matching (useful for testing and debugging).
        """
        content1 = "Python 3.11"
        content2 = "Python 3.11"
        content3 = "Python 3.11 "  # Extra trailing space
        
        validator = SemanticEquivalenceValidator(strict_equivalence=True)
        
        # Same content should be equivalent
        result1 = validator.check_semantic_equivalence(content1, content2)
        assert result1.is_equivalent is True
        assert result1.strict_mode_used is True
        
        # Different content should not be equivalent
        result2 = validator.check_semantic_equivalence(content1, content3)
        assert result2.is_equivalent is False
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_defines_specific_criteria_for_equivalence(self):
        """
        THE Steering_Assistant SHALL define specific criteria for semantic
        equivalence validation.
        """
        validator = SemanticEquivalenceValidator()
        
        # Should have specific criteria implemented
        assert hasattr(validator, "TECH_PATTERNS")
        assert hasattr(validator, "SYNONYMS")
        assert hasattr(validator, "SUBSTANTIVE_DIFFERENCES")
        
        # Criteria should be non-empty
        assert len(validator.TECH_PATTERNS) >= 1
        assert len(validator.SYNONYMS) >= 1
        assert len(validator.SUBSTANTIVE_DIFFERENCES) >= 1
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_extracts_technical_specifications(self):
        """
        WHEN comparing content, key facts, relationships, and technical
        specifications SHALL be extracted.
        """
        content = """
| Purpose | Library | Version |
|---------|---------|---------|
| Auth | JWT | 1.0 |
| Testing | pytest | 7.0 |
        """
        
        validator = SemanticEquivalenceValidator()
        facts = validator.extract_key_facts(content)
        
        # Should extract table data as facts
        assert len(facts) >= 1
        
        # Should extract version information
        version_facts = [f for f in facts if f.category == "version"]
        assert len(version_facts) >= 1
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_compares_multiple_contents(self):
        """
        Test comparing multiple content pieces for semantic equivalence.
        """
        contents = {
            "file1": "Backend: Python FastAPI",
            "file2": "Backend uses Python with FastAPI",
            "file3": "Backend: JavaScript Express",
        }
        
        validator = SemanticEquivalenceValidator()
        results = validator.compare_multiple(contents)
        
        # Should have results for all pairs
        assert len(results) >= 1
        
        # file1 and file2 should be equivalent
        key = "file1 vs file2"
        if key in results:
            assert results[key].is_equivalent is True
        
        # file1 and file3 should not be equivalent
        key = "file1 vs file3"
        if key in results:
            assert results[key].is_equivalent is False
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_synonym_handling(self):
        """
        Test that synonyms are properly handled for wording variations.
        """
        content1 = "The system utilizes PostgreSQL for data storage"
        content2 = "The system uses PostgreSQL database"
        content3 = "The system uses MongoDB database"
        
        validator = SemanticEquivalenceValidator()
        
        # PostgreSQL should be equivalent
        result1 = validator.check_semantic_equivalence(content1, content2)
        assert result1.is_equivalent is True
        
        # PostgreSQL vs MongoDB should not be equivalent
        result2 = validator.check_semantic_equivalence(content1, content3)
        assert result2.is_equivalent is False
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_version_comparison(self):
        """
        Test version comparison for semantic equivalence.
        """
        content1 = "Python 3.11"
        content2 = "Python 3.11"  # Exact match
        content3 = "Python 3.10"  # Different version
        
        validator = SemanticEquivalenceValidator()
        
        # Same version should be equivalent
        result1 = validator.check_semantic_equivalence(content1, content2)
        assert result1.is_equivalent is True
        
        # Different version should not be equivalent
        result2 = validator.check_semantic_equivalence(content1, content3)
        assert result2.is_equivalent is False
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_architecture_pattern_comparison(self):
        """
        Test architecture pattern comparison for semantic equivalence.
        """
        content1 = "Architecture: microservices"
        content2 = "The system follows a microservices architecture"
        content3 = "Architecture: monolithic"
        
        validator = SemanticEquivalenceValidator()
        
        # Same architecture should be equivalent
        result1 = validator.check_semantic_equivalence(content1, content2)
        assert result1.is_equivalent is True
        
        # Different architecture should not be equivalent
        result2 = validator.check_semantic_equivalence(content1, content3)
        assert result2.is_equivalent is False
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_empty_content_handling(self):
        """
        Test handling of empty or minimal content.
        """
        content1 = ""
        content2 = ""
        
        validator = SemanticEquivalenceValidator()
        result = validator.check_semantic_equivalence(content1, content2)
        
        # Empty content should be considered equivalent
        assert result.is_equivalent is True
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_confidence_score_calculation(self):
        """
        Test that confidence scores are properly calculated.
        """
        content1 = "Python FastAPI PostgreSQL"
        content2 = "Python FastAPI PostgreSQL Redis"
        
        validator = SemanticEquivalenceValidator()
        result = validator.check_semantic_equivalence(content1, content2)
        
        # Should have a confidence score
        assert 0.0 <= result.confidence <= 1.0
        
        # Should explain the result
        assert len(result.explanation) > 0
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_fact_extraction_from_sections(self):
        """
        Test that key facts are extracted from markdown sections.
        """
        content = """
# Backend
Python 3.11
FastAPI

# Frontend
React 18
TypeScript
        """
        
        validator = SemanticEquivalenceValidator()
        facts = validator.extract_key_facts(content)
        
        # Should extract section titles
        section_facts = [f for f in facts if f.category == "section"]
        assert len(section_facts) >= 2
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    def test_tolerate_wording_variations_method(self):
        """
        Test the tolerate_wording_variations method directly.
        """
        validator = SemanticEquivalenceValidator()
        
        # Create test facts
        fact1 = KeyFact(category="language", key="python", value="Python")
        fact2 = KeyFact(category="language", key="python", value="python")
        
        # Should tolerate case differences
        assert validator.tolerate_wording_variations(fact1, fact2) is True
        
        # Different categories should not match
        fact3 = KeyFact(category="framework", key="fastapi", value="FastAPI")
        assert validator.tolerate_wording_variations(fact1, fact3) is False
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    @given(st.text(min_size=1, max_size=500))
    def test_extract_key_facts_with_random_content(self, content: str):
        """
        Property: Semantic Equivalence Validation
        For any content, key fact extraction should not crash.
        """
        validator = SemanticEquivalenceValidator()
        
        # Should not raise any exceptions
        facts = validator.extract_key_facts(content)
        
        # Result should be a list
        assert isinstance(facts, list)
    
    @pytest.mark.property("Property 27: Semantic Equivalence Validation")
    @given(st.text(min_size=1, max_size=500), st.text(min_size=1, max_size=500))
    def test_check_semantic_equivalence_with_random_content(
        self,
        content1: str,
        content2: str
    ):
        """
        Property: Semantic Equivalence Validation
        For any two content pieces, semantic equivalence check should not crash.
        """
        validator = SemanticEquivalenceValidator()
        
        # Should not raise any exceptions
        result = validator.check_semantic_equivalence(content1, content2)
        
        # Result should be an EquivalenceResult
        assert isinstance(result, EquivalenceResult)
        assert isinstance(result.is_equivalent, bool)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0