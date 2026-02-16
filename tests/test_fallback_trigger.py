"""
Property-based tests for fallback triggering.

Validates: Requirements 8.1-8.8
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.feature_flags import FeatureFlagManager, FeatureFlagConfig
from hiveforge.steering.fallback_trigger import FallbackTrigger


class TestFallbackTriggering:
    """Tests for fallback triggering behavior."""
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_fallback_triggered_for_low_confidence(self):
        """
        WHEN confidence is LOW (<0.6) for critical sections, fallback SHALL be triggered.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        # Low confidence should trigger fallback
        assert fallback_trigger.should_trigger(confidence=0.5) is True
        assert fallback_trigger.should_trigger(confidence=0.55) is True
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_fallback_not_triggered_for_high_confidence(self):
        """
        WHEN confidence is HIGH, fallback should NOT be triggered.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        # High confidence should not trigger fallback
        assert fallback_trigger.should_trigger(confidence=0.7) is False
        assert fallback_trigger.should_trigger(confidence=0.8) is False
        assert fallback_trigger.should_trigger(confidence=0.95) is False
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_fallback_triggered_for_validation_failure(self):
        """
        WHEN semantic validation fails, fallback SHALL be triggered.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        # Validation failure should trigger fallback
        assert fallback_trigger.should_trigger(
            confidence=0.9,
            validation_passed=False,
        ) is True
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_fallback_triggered_for_interactive_flag(self):
        """
        WHEN the user provides the --interactive flag, fallback SHALL be used.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        # Interactive flag should trigger fallback
        assert fallback_trigger.should_trigger(
            confidence=0.95,
            interactive=True,
        ) is True
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_fallback_triggered_for_token_budget_exceeded(self):
        """
        WHEN token budget is exceeded, fallback SHALL be triggered.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        # Token budget exceeded should trigger fallback
        assert fallback_trigger.should_trigger(
            confidence=0.95,
            token_budget_exceeded=True,
        ) is True
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_get_fallback_reason(self):
        """
        WHEN fallback is triggered, the system SHALL provide a reason.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        # Get reason for low confidence
        reason = fallback_trigger.get_fallback_reason(confidence=0.5)
        assert "Low confidence" in reason
        
        # Get reason for validation failure
        reason = fallback_trigger.get_fallback_reason(
            confidence=0.9,
            validation_passed=False,
        )
        assert "Semantic validation failed" in reason
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_get_fallback_workflow(self):
        """
        WHEN fallback is triggered, the system SHALL return the fallback workflow.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        workflow = fallback_trigger.get_fallback_workflow()
        assert workflow == "question-asking"
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_trigger_for_file(self):
        """
        WHEN fallback is triggered for a specific file, the system SHALL provide context.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        result = fallback_trigger.trigger_for_file(
            filename="tech-stack.md",
            confidence=0.5,
        )
        
        assert result["filename"] == "tech-stack.md"
        assert result["should_fallback"] is True
        assert "Low confidence" in result["reason"]
        assert result["confidence"] == 0.5
        assert result["fallback_workflow"] == "question-asking"
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    def test_get_context_for_questions(self):
        """
        WHEN fallback is triggered, the system SHALL provide context for questions.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        context = fallback_trigger.get_context_for_questions(
            filename="tech-stack.md",
            confidence=0.5,
            evidence=[{"source": "ARTIFACT", "description": "From README.md"}],
            discovered_files=["README.md", "package.json"],
        )
        
        assert context["filename"] == "tech-stack.md"
        assert context["confidence"] == 0.5
        assert len(context["evidence"]) == 1
        assert "README.md" in context["discovered_files"]
        assert "package.json" in context["discovered_files"]
    
    @pytest.mark.property("Property 8: Fallback Triggering")
    @given(st.floats(min_value=0.0, max_value=1.0))
    def test_fallback_trigger_property(self, confidence: float):
        """
        Property: Fallback Triggering
        For any confidence score, fallback should be triggered appropriately.
        """
        feature_config = FeatureFlagConfig(confidence_threshold=0.7)
        feature_manager = FeatureFlagManager(feature_config)
        
        fallback_trigger = FallbackTrigger(
            feature_flag_manager=feature_manager,
            confidence_threshold=0.6,
        )
        
        # Fallback should be triggered for low confidence
        if confidence < 0.6:
            assert fallback_trigger.should_trigger(confidence=confidence) is True
        else:
            # For higher confidence, fallback should not be triggered
            # (unless other conditions are met)
            assert fallback_trigger.should_trigger(confidence=confidence) is False
