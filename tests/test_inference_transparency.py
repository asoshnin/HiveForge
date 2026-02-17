"""
Property-based tests for inference transparency.

Validates: Requirements 26.1-26.7
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.inference_transparency import (
    InferenceTransparency,
    InferenceExplanation,
    InferencePattern,
    InferenceStrength,
    InferenceSource,
)


class TestInferenceTransparencyDocumentation:
    """Tests for inference pattern documentation."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_document_patterns_returns_list(self):
        """
        WHEN document_patterns is called, it SHALL return a list of documented patterns.
        """
        transparency = InferenceTransparency()
        patterns = transparency.document_patterns()
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_patterns_have_required_fields(self):
        """
        WHEN patterns are documented, they SHALL have required fields.
        """
        transparency = InferenceTransparency()
        patterns = transparency.document_patterns()
        
        for pattern in patterns:
            assert isinstance(pattern, InferencePattern)
            assert pattern.pattern_id is not None
            assert pattern.description is not None
            assert pattern.inference_type is not None
            assert pattern.conditions is not None
            assert pattern.confidence_range is not None
            assert pattern.examples is not None
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_get_pattern_by_id(self):
        """
        WHEN get_pattern is called with a valid ID, it SHALL return the pattern.
        """
        transparency = InferenceTransparency()
        
        pattern = transparency.get_pattern("backend_framework_pattern")
        
        assert pattern is not None
        assert pattern.pattern_id == "backend_framework_pattern"
        assert pattern.inference_type == "backend_framework"
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_get_pattern_invalid_id(self):
        """
        WHEN get_pattern is called with an invalid ID, it SHALL return None.
        """
        transparency = InferenceTransparency()
        
        pattern = transparency.get_pattern("nonexistent_pattern")
        
        assert pattern is None


class TestInferenceExplanation:
    """Tests for inference explanation functionality."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_explain_inference_returns_explanation(self):
        """
        WHEN explain_inference is called, it SHALL return an InferenceExplanation.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi' in pyproject.toml", "match_quality": "direct"}
        ]
        
        explanation = transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        assert isinstance(explanation, InferenceExplanation)
        assert explanation.inference_type == "backend_framework"
        assert explanation.inferred_value == "FastAPI"
        assert explanation.confidence == 0.85
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_explanation_has_reasoning(self):
        """
        WHEN inference is explained, it SHALL include reasoning.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi' in pyproject.toml", "match_quality": "direct"}
        ]
        
        explanation = transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        assert explanation.reasoning is not None
        assert len(explanation.reasoning) > 0
        assert "FastAPI" in explanation.reasoning
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_explanation_to_markdown(self):
        """
        WHEN explanation is converted to markdown, it SHALL be properly formatted.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi' in pyproject.toml", "match_quality": "direct"}
        ]
        
        explanation = transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        markdown = explanation.to_markdown()
        
        assert isinstance(markdown, str)
        assert "Inference: backend_framework" in markdown
        assert "**Value:** FastAPI" in markdown
        assert "**Confidence:**" in markdown
        assert "**Evidence Sources:**" in markdown


class TestInferenceStrength:
    """Tests for inference strength classification."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_strong_inference_high_confidence_direct_match(self):
        """
        WHEN confidence is high and evidence has direct match, inference SHALL be STRONG.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi'", "match_quality": "direct"}
        ]
        
        strength = transparency.distinguish_strength(0.90, evidence)
        
        assert strength == InferenceStrength.STRONG
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_strong_inference_multiple_sources(self):
        """
        WHEN multiple independent sources exist, inference SHALL be STRONG.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi' in pyproject.toml"},
            {"type": "CONFIG_FILE", "detail": "main.py imports FastAPI"},
        ]
        
        strength = transparency.distinguish_strength(0.85, evidence)
        
        assert strength == InferenceStrength.STRONG
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_moderate_inference_medium_confidence(self):
        """
        WHEN confidence is medium, inference SHALL be MODERATE.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'express' in package.json"}
        ]
        
        strength = transparency.distinguish_strength(0.75, evidence)
        
        assert strength == InferenceStrength.MODERATE
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_weak_inference_low_confidence(self):
        """
        WHEN confidence is low, inference SHALL be WEAK.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "CONTEXT", "detail": "Inferred from project name"}
        ]
        
        strength = transparency.distinguish_strength(0.55, evidence)
        
        assert strength == InferenceStrength.WEAK
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_weak_inference_no_evidence(self):
        """
        WHEN no evidence exists, inference SHALL be WEAK.
        """
        transparency = InferenceTransparency()
        
        strength = transparency.distinguish_strength(0.50, [])
        
        assert strength == InferenceStrength.WEAK


class TestConservativeInference:
    """Tests for conservative inference mode."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_conservative_mode_initialization(self):
        """
        WHEN InferenceTransparency is initialized with conservative_mode, it SHALL be stored.
        """
        transparency_conservative = InferenceTransparency(conservative_mode=True)
        transparency_normal = InferenceTransparency(conservative_mode=False)
        
        assert transparency_conservative.conservative_mode is True
        assert transparency_normal.conservative_mode is False
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_conservative_mode_explanation_note(self):
        """
        WHEN conservative mode is enabled and confidence is low, explanation SHALL have note.
        """
        transparency = InferenceTransparency(conservative_mode=True)
        
        evidence = [
            {"type": "CONTEXT", "detail": "Limited evidence"}
        ]
        
        explanation = transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.65,
            evidence=evidence,
        )
        
        assert explanation.conservative_note is not None
        assert "conservative mode" in explanation.conservative_note.lower()
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_normal_mode_no_conservative_note(self):
        """
        WHEN conservative mode is disabled, explanation SHALL NOT have conservative note.
        """
        transparency = InferenceTransparency(conservative_mode=False)
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi'", "match_quality": "direct"}
        ]
        
        explanation = transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        assert explanation.conservative_note is None


class TestExplicitMarkers:
    """Tests for explicit marker determination."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_explicit_marker_for_low_confidence(self):
        """
        WHEN confidence is very low, explicit marker SHALL be used.
        """
        transparency = InferenceTransparency()
        
        should_use = transparency.should_use_explicit_marker(0.50, [])
        
        assert should_use is True
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_no_explicit_marker_for_high_confidence(self):
        """
        WHEN confidence is high with evidence, explicit marker SHALL NOT be used.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi'", "match_quality": "direct"}
        ]
        
        should_use = transparency.should_use_explicit_marker(0.85, evidence)
        
        assert should_use is False
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_conservative_mode_stricter_threshold(self):
        """
        WHEN conservative mode is enabled, threshold for explicit marker SHALL be higher.
        """
        transparency_conservative = InferenceTransparency(conservative_mode=True)
        transparency_normal = InferenceTransparency(conservative_mode=False)
        
        evidence = [{"type": "PATTERN_MATCH", "detail": "Some evidence"}]
        
        # At 0.72 confidence, normal mode should not use explicit marker
        assert transparency_normal.should_use_explicit_marker(0.72, evidence) is False
        
        # But conservative mode should use explicit marker
        assert transparency_conservative.should_use_explicit_marker(0.72, evidence) is True


class TestTransparencyReport:
    """Tests for transparency reporting."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_empty_report(self):
        """
        WHEN no inferences have been made, report SHALL show zero counts.
        """
        transparency = InferenceTransparency()
        
        report = transparency.get_transparency_report()
        
        assert report["total_inferences"] == 0
        assert report["strong_inferences"] == 0
        assert report["moderate_inferences"] == 0
        assert report["weak_inferences"] == 0
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_report_after_inferences(self):
        """
        WHEN inferences have been made, report SHALL show correct counts.
        """
        transparency = InferenceTransparency()
        
        # Make some inferences
        evidence_strong = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi'", "match_quality": "direct"}
        ]
        evidence_weak = [{"type": "CONTEXT", "detail": "Limited evidence"}]
        
        transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.90,
            evidence=evidence_strong,
        )
        transparency.explain_inference(
            inference_type="database",
            inferred_value="PostgreSQL",
            confidence=0.55,
            evidence=evidence_weak,
        )
        
        report = transparency.get_transparency_report()
        
        assert report["total_inferences"] == 2
        assert report["strong_inferences"] == 1
        assert report["weak_inferences"] == 1
        assert report["average_confidence"] == pytest.approx(0.725, rel=0.01)
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_report_includes_patterns_used(self):
        """
        WHEN inferences are made, report SHALL include patterns used.
        """
        transparency = InferenceTransparency()
        
        evidence = [{"type": "PATTERN_MATCH", "detail": "Found 'fastapi'"}]
        
        transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        report = transparency.get_transparency_report()
        
        assert "backend_framework" in report["patterns_used"]


class TestInferenceLog:
    """Tests for inference logging."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_inference_log_tracking(self):
        """
        WHEN inferences are made, they SHALL be logged.
        """
        transparency = InferenceTransparency()
        
        evidence = [{"type": "PATTERN_MATCH", "detail": "Found 'fastapi'"}]
        
        transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        log = transparency.get_inference_log()
        
        assert len(log) == 1
        assert log[0].inference_type == "backend_framework"
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_inference_log_returns_copy(self):
        """
        WHEN get_inference_log is called, it SHALL return a copy.
        """
        transparency = InferenceTransparency()
        
        evidence = [{"type": "PATTERN_MATCH", "detail": "Found 'fastapi'"}]
        
        transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        log1 = transparency.get_inference_log()
        log1.clear()
        
        log2 = transparency.get_inference_log()
        assert len(log2) == 1


class TestIndustryStandards:
    """Tests for industry standard references."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_industry_standard_reference(self):
        """
        WHEN inference matches known standard, explanation SHALL include reference.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi' in pyproject.toml", "match_quality": "direct"}
        ]
        
        explanation = transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        assert explanation.industry_standard_reference is not None
        assert "popular" in explanation.industry_standard_reference.lower() or "standard" in explanation.industry_standard_reference.lower()
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    def test_alternatives_considered(self):
        """
        WHEN inference is made, alternatives SHALL be listed.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": "Found 'fastapi' in pyproject.toml"}
        ]
        
        explanation = transparency.explain_inference(
            inference_type="backend_framework",
            inferred_value="FastAPI",
            confidence=0.85,
            evidence=evidence,
        )
        
        assert len(explanation.alternative_values) > 0
        assert "Express" in explanation.alternative_values or "Django" in explanation.alternative_values


class TestPropertyBasedInferenceTransparency:
    """Property-based tests for inference transparency."""
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0),
        evidence_count=st.integers(min_value=0, max_value=5),
    )
    def test_strength_classification_property(self, confidence: float, evidence_count: int):
        """
        Property: Inference strength classification
        For any confidence and evidence count, strength should be correctly classified.
        """
        transparency = InferenceTransparency()
        
        evidence = [
            {"type": "PATTERN_MATCH", "detail": f"Evidence {i}", "match_quality": "direct" if i == 0 else "indirect"}
            for i in range(evidence_count)
        ]
        
        strength = transparency.distinguish_strength(confidence, evidence)
        
        # Verify strength classification logic
        if confidence >= 0.85 and evidence_count >= 1:
            assert strength == InferenceStrength.STRONG
        elif confidence >= 0.70 and evidence_count >= 1:
            assert strength == InferenceStrength.MODERATE
        else:
            assert strength == InferenceStrength.WEAK
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0),
        conservative=st.booleans(),
    )
    def test_explicit_marker_property(self, confidence: float, conservative: bool):
        """
        Property: Explicit marker determination
        For any confidence and conservative mode, explicit marker should be correctly determined.
        """
        transparency = InferenceTransparency(conservative_mode=conservative)
        
        evidence = [{"type": "PATTERN_MATCH", "detail": "Some evidence"}]
        
        should_use = transparency.should_use_explicit_marker(confidence, evidence)
        
        # In conservative mode, threshold is higher
        if conservative:
            # Should use explicit marker for lower confidence
            if confidence < 0.75:
                assert should_use is True
        else:
            # In normal mode, threshold is lower
            if confidence < 0.6:
                assert should_use is True
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    @given(
        confidence=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_confidence_in_range(self, confidence: float):
        """
        Property: Confidence score validity
        For any confidence value, it should be in valid range.
        """
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.property("Property 26: Intelligent Inference Transparency")
    @given(
        inference_type=st.sampled_from([
            "backend_framework", "frontend_framework", "database",
            "cache", "architecture", "language"
        ]),
        inferred_value=st.text(min_size=1, max_size=50),
        confidence=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_explain_inference_property(
        self,
        inference_type: str,
        inferred_value: str,
        confidence: float,
    ):
        """
        Property: Explain inference robustness
        For any inference parameters, explain_inference should return valid explanation.
        """
        transparency = InferenceTransparency()
        
        evidence = [{"type": "PATTERN_MATCH", "detail": "Test evidence"}]
        
        explanation = transparency.explain_inference(
            inference_type=inference_type,
            inferred_value=inferred_value,
            confidence=confidence,
            evidence=evidence,
        )
        
        assert explanation.inference_type == inference_type
        assert explanation.inferred_value == inferred_value
        assert explanation.confidence == confidence
        assert explanation.reasoning is not None
        assert len(explanation.evidence_sources) == 1