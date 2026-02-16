"""
Property-based tests for confidence scoring.

Validates: Requirements 4.1-4.8
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.confidence_scorer import ConfidenceScorer
from hiveforge.steering.models import ConfidenceScore, Evidence, ConfidenceLevel


class TestConfidenceScoreAccuracy:
    """Tests for confidence score accuracy."""
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_high_confidence_for_direct_extraction(self):
        """
        WHEN content is directly extracted from artifacts or code, HIGH confidence SHALL be assigned.
        """
        scorer = ConfidenceScorer()
        
        evidence = [
            Evidence(
                source="ARTIFACT",
                strength=0.95,
                description="Directly extracted from README.md",
            )
        ]
        
        confidence = scorer.calculate_confidence("content", evidence)
        level = scorer.get_level(confidence)
        
        assert level == ConfidenceLevel.HIGH
        assert confidence >= 0.9
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_medium_confidence_for_inference(self):
        """
        WHEN content is reasonably inferred from available information, MEDIUM confidence SHALL be assigned.
        """
        scorer = ConfidenceScorer()
        
        evidence = [
            Evidence(
                source="INFERENCE",
                strength=0.70,
                description="Inferred from package.json",
            )
        ]
        
        confidence = scorer.calculate_confidence("content", evidence)
        level = scorer.get_level(confidence)
        
        assert level == ConfidenceLevel.MEDIUM
        assert 0.7 <= confidence < 0.9
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_low_confidence_for_placeholders(self):
        """
        WHEN content is a generic placeholder or guess, LOW confidence SHALL be assigned.
        """
        scorer = ConfidenceScorer()
        
        evidence = [
            Evidence(
                source="ARTIFACT",
                strength=0.50,
                description="Generic placeholder",
            )
        ]
        
        confidence = scorer.calculate_confidence("content", evidence, is_placeholder=True)
        level = scorer.get_level(confidence)
        
        assert level == ConfidenceLevel.LOW
        assert confidence < 0.7
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_confidence_threshold_configuration(self):
        """
        WHEN confidence threshold is configured, it SHALL be used for MEDIUM level classification.
        """
        # Test with default threshold (0.7)
        scorer_default = ConfidenceScorer()
        
        # Score at threshold boundary
        confidence_at_threshold = 0.7
        level = scorer_default.get_level(confidence_at_threshold)
        assert level == ConfidenceLevel.MEDIUM
        
        # Score just below threshold
        confidence_below = 0.69
        level = scorer_default.get_level(confidence_below)
        assert level == ConfidenceLevel.LOW
        
        # Score just above threshold
        confidence_above = 0.71
        level = scorer_default.get_level(confidence_above)
        assert level == ConfidenceLevel.MEDIUM
        
        # Test with custom threshold
        scorer_custom = ConfidenceScorer(conservative_threshold=0.8)
        
        # Score at new threshold boundary
        confidence_at_new_threshold = 0.8
        level = scorer_custom.get_level(confidence_at_new_threshold)
        assert level == ConfidenceLevel.MEDIUM
        
        # Score just below new threshold
        confidence_below_new = 0.79
        level = scorer_custom.get_level(confidence_below_new)
        assert level == ConfidenceLevel.LOW
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_confidence_score_dataclass(self):
        """
        WHEN ConfidenceScore is created, it SHALL have value, level, and evidence.
        """
        evidence = [
            Evidence(
                source="ARTIFACT",
                strength=0.95,
                description="Test evidence",
            )
        ]
        
        score = ConfidenceScore(
            value=0.92,
            level=ConfidenceLevel.HIGH,
            evidence=evidence,
        )
        
        assert score.value == 0.92
        assert score.level == ConfidenceLevel.HIGH
        assert len(score.evidence) == 1
        assert score.evidence[0].source == "ARTIFACT"
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_confidence_level_enum(self):
        """
        WHEN confidence levels are used, they SHALL be HIGH, MEDIUM, or LOW.
        """
        scorer = ConfidenceScorer()
        
        # Test HIGH level
        high_score = scorer.get_level(0.95)
        assert high_score == ConfidenceLevel.HIGH
        
        # Test MEDIUM level
        medium_score = scorer.get_level(0.80)
        assert medium_score == ConfidenceLevel.MEDIUM
        
        # Test LOW level
        low_score = scorer.get_level(0.50)
        assert low_score == ConfidenceLevel.LOW
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_aggregate_section_confidences(self):
        """
        WHEN aggregating section confidences, overall file confidence SHALL be calculated.
        """
        scorer = ConfidenceScorer()
        
        section_confidences = {
            "section1": 0.95,
            "section2": 0.85,
            "section3": 0.75,
        }
        
        overall = scorer.aggregate_section_confidences(section_confidences)
        
        # Overall should be between min and average
        min_conf = min(section_confidences.values())  # 0.75
        avg_conf = sum(section_confidences.values()) / len(section_confidences)  # 0.85
        
        assert min_conf <= overall <= avg_conf
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_calibrate_method(self):
        """
        WHEN calibrate is called, it SHALL return calibration data.
        """
        scorer = ConfidenceScorer()
        
        predicted = [0.95, 0.85, 0.75, 0.65, 0.55]
        actual = [True, True, True, False, False]
        
        calibration = scorer.calibrate(predicted, actual)
        
        assert calibration["calibration_status"] == "calibrated"
        assert "calibration_data" in calibration
        assert "high_accuracy" in calibration["calibration_data"]
        assert "total_samples" in calibration["calibration_data"]
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_evidence_creation(self):
        """
        WHEN evidence is created, it SHALL have source, strength, and description.
        """
        scorer = ConfidenceScorer()
        
        evidence = scorer.create_evidence(
            source="ARTIFACT",
            description="Test evidence",
            strength=0.95,
        )
        
        assert evidence.source == "ARTIFACT"
        assert evidence.strength == 0.95
        assert evidence.description == "Test evidence"
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    def test_score_content_method(self):
        """
        WHEN content is scored, it SHALL return a ConfidenceScore object.
        """
        scorer = ConfidenceScorer()
        
        score = scorer.score_content(
            content="Test content",
            source="ARTIFACT",
            description="Test score",
        )
        
        assert isinstance(score, ConfidenceScore)
        assert 0.0 <= score.value <= 1.0
        assert score.level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
        assert len(score.evidence) >= 1
    
    @pytest.mark.property("Property 4: Confidence Score Accuracy")
    @given(st.floats(min_value=0.0, max_value=1.0))
    def test_confidence_score_property(self, score_value: float):
        """
        Property: Confidence Score Accuracy
        For any confidence score, the level should be correctly assigned.
        """
        scorer = ConfidenceScorer()
        level = scorer.get_level(score_value)
        
        # Verify level assignment
        if score_value >= 0.9:
            assert level == ConfidenceLevel.HIGH
        elif score_value >= 0.7:
            assert level == ConfidenceLevel.MEDIUM
        else:
            assert level == ConfidenceLevel.LOW
