"""
Property-based tests for feature flag routing.

Validates: Requirements 1.1-1.5
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.feature_flags import FeatureFlagManager
from hiveforge.steering.models import FeatureFlagConfig


class TestFeatureFlagRouting:
    """Tests for feature flag routing behavior."""
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    def test_autonomous_workflow_when_flag_enabled(self):
        """
        WHEN the flag is provided, the system SHALL use the autonomous generation workflow.
        """
        manager = FeatureFlagManager()
        manager.load_from_cli(use_autonomous_generation=True, interactive=False)
        
        assert manager.get_workflow_type() == "AUTONOMOUS"
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    def test_fallback_workflow_when_flag_not_provided(self):
        """
        WHEN the flag is not provided, the system SHALL use the existing question-asking workflow.
        """
        manager = FeatureFlagManager()
        manager.load_from_cli(use_autonomous_generation=False)
        
        assert manager.get_workflow_type() == "FALLBACK"
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    def test_fallback_workflow_when_interactive_flag_set(self):
        """
        WHEN interactive flag is set, fallback workflow should be used even if autonomous is enabled.
        """
        manager = FeatureFlagManager()
        manager.load_from_cli(use_autonomous_generation=True, interactive=True)
        
        assert manager.get_workflow_type() == "FALLBACK"
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    def test_both_workflows_maintain_in_parallel(self):
        """
        WHEN both workflows are present, the system SHALL maintain them in parallel without interference.
        """
        # Test autonomous workflow
        manager_auto = FeatureFlagManager()
        manager_auto.load_from_cli(use_autonomous_generation=True, interactive=False)
        assert manager_auto.get_workflow_type() == "AUTONOMOUS"
        
        # Test fallback workflow
        manager_fallback = FeatureFlagManager()
        manager_fallback.load_from_cli(use_autonomous_generation=False)
        assert manager_fallback.get_workflow_type() == "FALLBACK"
        
        # Verify they don't interfere
        assert manager_auto.get_workflow_type() == "AUTONOMOUS"
        assert manager_fallback.get_workflow_type() == "FALLBACK"
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    def test_confidence_threshold_validation(self):
        """
        WHEN confidence_threshold is set, the system SHALL validate it is between 0.0 and 1.0.
        """
        # Valid thresholds should not produce errors
        for valid_threshold in [0.0, 0.5, 0.7, 0.95]:
            manager = FeatureFlagManager()
            manager.load_from_cli(confidence_threshold=valid_threshold)
            errors = manager.validate()
            assert all("confidence_threshold" not in e for e in errors)
        
        # Invalid thresholds should produce errors
        for invalid_threshold in [-0.1, 1.1, 2.0]:
            manager = FeatureFlagManager()
            manager.load_from_cli(confidence_threshold=invalid_threshold)
            errors = manager.validate()
            assert any("confidence_threshold" in e for e in errors)
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    def test_high_threshold_warning(self):
        """
        WHEN threshold is set too high (>0.95), the system SHALL warn that most sections may trigger fallback.
        """
        manager = FeatureFlagManager()
        manager.load_from_cli(confidence_threshold=0.96)
        
        assert manager.warn_high_threshold() is True
        warning = manager.get_threshold_warning()
        assert warning is not None
        assert "very high" in warning.lower()
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    def test_default_threshold_is_acceptable(self):
        """
        WHEN threshold is not specified, default thresholds SHALL be used.
        """
        manager = FeatureFlagManager()
        # Default confidence_threshold is 0.7
        assert manager.config.confidence_threshold == 0.7
        assert manager.warn_high_threshold() is False
        assert manager.get_threshold_warning() is None
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    @given(st.floats(min_value=0.0, max_value=0.95))
    def test_confidence_threshold_property(self, threshold: float):
        """
        Property: Feature Flag Routing
        For any valid confidence threshold, the system should route correctly.
        """
        manager = FeatureFlagManager()
        manager.load_from_cli(
            use_autonomous_generation=True,
            confidence_threshold=threshold,
            interactive=False
        )
        
        # Should be autonomous when flag is set and not interactive
        assert manager.get_workflow_type() == "AUTONOMOUS"
        
        # Validation should pass for valid thresholds
        errors = manager.validate()
        assert all("confidence_threshold" not in e for e in errors)
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    @given(st.floats(min_value=0.0, max_value=0.6))
    def test_fallback_triggered_for_low_confidence(self, confidence: float):
        """
        WHEN confidence is below threshold, fallback should be triggered.
        """
        manager = FeatureFlagManager()
        manager.load_from_cli(confidence_threshold=0.7)
        
        assert manager.should_fallback(confidence) is True
    
    @pytest.mark.property("Property 1: Feature Flag Routing")
    @given(st.floats(min_value=0.7, max_value=1.0))
    def test_fallback_not_triggered_for_high_confidence(self, confidence: float):
        """
        WHEN confidence is at or above threshold, fallback should not be triggered.
        """
        manager = FeatureFlagManager()
        manager.load_from_cli(confidence_threshold=0.7)
        
        assert manager.should_fallback(confidence) is False
