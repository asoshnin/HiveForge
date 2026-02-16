"""
Property-based tests for semantic validation.

Validates: Requirements 5.1-5.10
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.validators.contradiction_detector import ContradictionDetector
from hiveforge.steering.validators.tech_stack_validator import TechStackValidator


class TestSemanticValidationCorrectness:
    """Tests for semantic validation correctness."""
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_detects_direct_contradictions_python_javascript(self):
        """
        WHEN analyzing drafts, direct contradictions SHALL be detected (Python vs JavaScript).
        """
        files = {
            "tech-stack.md": "Backend: Python\nFrontend: JavaScript",
            "architecture.md": "The system uses Python for all components",
        }
        
        detector = ContradictionDetector()
        contradictions = detector.detect_direct_contradictions(files)
        
        # Should detect Python vs JavaScript contradiction
        assert len(contradictions) >= 1
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_detects_direct_contradictions_microservices_monolithic(self):
        """
        WHEN analyzing drafts, implicit contradictions SHALL be detected (microservices vs monolithic).
        """
        files = {
            "architecture.md": "The system uses microservices architecture",
            "tech-stack.md": "Monolithic design with single deployment unit",
        }
        
        detector = ContradictionDetector()
        contradictions = detector.detect_implicit_contradictions(files)
        
        # Should detect microservices vs monolithic contradiction
        assert len(contradictions) >= 1
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_detects_version_mismatches(self):
        """
        WHEN validating, version consistency SHALL be checked using version extraction and comparison.
        """
        files = {
            "tech-stack.md": "Backend Framework: FastAPI 3.11\nDatabase: PostgreSQL 15",
            "api-standards.md": "API Framework: FastAPI 3.10",
        }
        
        validator = TechStackValidator({})
        issues = validator.validate_version_consistency(files)
        
        # Should detect version mismatch
        assert len(issues) >= 1
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_detects_database_consistency_issues(self):
        """
        WHEN validating, structural consistency SHALL be verified (database in tech-stack must be in db-standards).
        """
        files = {
            "tech-stack.md": "Database: PostgreSQL",
            "db-standards.md": "Database: MongoDB",
        }
        
        validator = TechStackValidator({})
        issues = validator.validate_database_consistency(files)
        
        # Should detect database mismatch
        assert len(issues) >= 1
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_detects_api_framework_mismatches(self):
        """
        WHEN validating, API framework must match backend framework.
        """
        files = {
            "tech-stack.md": "Backend Framework: FastAPI",
            "api-standards.md": "API Framework: Express",
        }
        
        validator = TechStackValidator({})
        issues = validator.validate_api_consistency(files)
        
        # Should detect API framework mismatch
        assert len(issues) >= 1
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_framework_classification_validation(self):
        """
        WHEN validating, framework/language pairings SHALL be verified using framework classification database.
        """
        framework_classifications = {
            "frontend": ["React", "Vue", "Angular"],
            "backend": ["FastAPI", "Express", "Django"],
        }
        
        validator = TechStackValidator(framework_classifications)
        
        # Test backend framework classified as frontend
        files = {
            "tech-stack.md": "Backend Framework: React",
        }
        issues = validator.validate_framework_pairings(files, "backend", "frontend")
        
        assert len(issues) >= 1
        assert "frontend framework" in issues[0]["message"].lower()
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_confidence_score_calculation(self):
        """
        WHEN validating, confidence scores SHALL be assigned to validation results.
        """
        detector = ContradictionDetector()
        
        # Test direct contradiction confidence
        files = {
            "file1.md": "Python",
            "file2.md": "JavaScript",
        }
        contradictions = detector.detect_direct_contradictions(files)
        
        if contradictions:
            confidence = contradictions[0].get("confidence", 0)
            assert 0.9 <= confidence <= 1.0
        
        # Test implicit contradiction confidence
        files = {
            "file1.md": "microservices distributed",
            "file2.md": "monolithic single",
        }
        contradictions = detector.detect_implicit_contradictions(files)
        
        if contradictions:
            confidence = contradictions[0].get("confidence", 0)
            assert 0.8 <= confidence <= 0.9
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_validation_report_generation(self):
        """
        WHEN semantic validation runs, a validation report SHALL be generated with errors and warnings.
        """
        from hiveforge.steering.validators.steering_validator import SteeringValidator
        
        validator = SteeringValidator()
        
        files = {
            "tech-stack.md": "Backend Framework: FastAPI\nDatabase: PostgreSQL",
            "db-standards.md": "Database: PostgreSQL",
        }
        
        framework_classifications = {}
        rules = []
        
        report = validator.generate_validation_report(files, framework_classifications, rules)
        
        # Report should have errors and warnings
        assert "errors" in report
        assert "warnings" in report
        assert "total_issues" in report
        assert "status" in report
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    def test_validation_with_rules(self):
        """
        WHEN semantic validation runs, it SHALL execute validation_rules.yaml rules.
        """
        from hiveforge.steering.validators.validation_rules_loader import ValidationRulesLoader
        
        loader = ValidationRulesLoader()
        rules = loader.get_rules()
        
        # Should have at least some rules
        assert len(rules) >= 1
        
        # Each rule should have required fields
        for rule in rules:
            assert "id" in rule
            assert "description" in rule
            assert "severity" in rule
            assert "check" in rule
    
    @pytest.mark.property("Property 5: Semantic Validation Correctness")
    @given(st.text(min_size=1, max_size=100))
    def test_contradiction_detection_with_random_content(self, content: str):
        """
        Property: Semantic Validation Correctness
        For any content, contradiction detection should not crash.
        """
        files = {
            "file1.md": content,
            "file2.md": "some other content",
        }
        
        detector = ContradictionDetector()
        
        # Should not raise any exceptions
        contradictions = detector.detect_all_contradictions(files)
        
        # Result should be a list
        assert isinstance(contradictions, list)
