"""
Property-based tests for token budget management.

Validates: Requirements 10.1-10.7, 11.1-11.7
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.token_budget import TokenBudgetManager


class TestTokenBudget:
    """Tests for token budget management."""
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    def test_track_usage(self):
        """
        WHEN tracking token usage, the system SHALL track LLM token usage per file generation.
        """
        manager = TokenBudgetManager(max_tokens=10000)
        
        # Track usage for multiple files
        manager.track_usage("project-vision.md", 2000)
        manager.track_usage("tech-stack.md", 1500)
        manager.track_usage("architecture.md", 2500)
        
        # Verify total usage
        assert manager._current_usage == 6000
        
        # Verify per-file usage
        assert manager._usage_per_file["project-vision.md"] == 2000
        assert manager._usage_per_file["tech-stack.md"] == 1500
        assert manager._usage_per_file["architecture.md"] == 2500
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    def test_warn_at_threshold(self):
        """
        WHEN token usage approaches the budget limit (90%), the system SHALL warn the user.
        """
        manager = TokenBudgetManager(max_tokens=10000, warning_threshold=0.9)
        
        # At 80% usage, no warning
        manager._current_usage = 8000
        assert manager.warn_at_threshold() is False
        
        # At 90% usage, warning should be shown
        manager._current_usage = 9000
        # First call should return True
        assert manager.warn_at_threshold() is True
        
        # Second call should return False (already warned)
        assert manager.warn_at_threshold() is False
        
        # At 95% usage, warning should be shown (if not already shown)
        manager2 = TokenBudgetManager(max_tokens=10000, warning_threshold=0.9)
        manager2._current_usage = 9500
        assert manager2.warn_at_threshold() is True
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    def test_exceeded(self):
        """
        WHEN token budget is exceeded, the system SHALL detect it.
        """
        manager = TokenBudgetManager(max_tokens=10000)
        
        # At 9000 tokens, not exceeded
        manager._current_usage = 9000
        assert manager.exceeded() is False
        
        # At 10000 tokens, not exceeded (equal is OK)
        manager._current_usage = 10000
        assert manager.exceeded() is False
        
        # At 10001 tokens, exceeded
        manager._current_usage = 10001
        assert manager.exceeded() is True
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    def test_get_remaining(self):
        """
        WHEN calculating remaining tokens, the system SHALL compute correctly.
        """
        manager = TokenBudgetManager(max_tokens=10000)
        
        # At 0 tokens used
        manager._current_usage = 0
        assert manager.get_remaining() == 10000
        
        # At 5000 tokens used
        manager._current_usage = 5000
        assert manager.get_remaining() == 5000
        
        # At 10000 tokens used
        manager._current_usage = 10000
        assert manager.get_remaining() == 0
        
        # At 11000 tokens used (should not go negative)
        manager._current_usage = 11000
        assert manager.get_remaining() == 0
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    def test_estimate_cost(self):
        """
        WHEN estimating cost, the system SHALL calculate correctly.
        """
        manager = TokenBudgetManager(max_tokens=10000)
        
        # Test cost estimation
        cost_1m_tokens = manager.estimate_cost(1_000_000, cost_per_million_tokens=0.50)
        assert cost_1m_tokens == 0.50
        
        cost_500k_tokens = manager.estimate_cost(500_000, cost_per_million_tokens=0.50)
        assert cost_500k_tokens == 0.25
        
        cost_10k_tokens = manager.estimate_cost(10_000, cost_per_million_tokens=0.50)
        assert cost_10k_tokens == 0.005
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    def test_get_usage_summary(self):
        """
        WHEN getting usage summary, the system SHALL provide complete statistics.
        """
        manager = TokenBudgetManager(max_tokens=10000)
        
        # Track some usage
        manager.track_usage("file1.md", 2000)
        manager.track_usage("file2.md", 3000)
        
        summary = manager.get_usage_summary()
        
        assert summary["current_usage"] == 5000
        assert summary["max_tokens"] == 10000
        assert summary["remaining"] == 5000
        assert summary["total_files"] == 2
        assert summary["usage_per_file"]["file1.md"] == 2000
        assert summary["usage_per_file"]["file2.md"] == 3000
        assert summary["usage_percentage"] == 50.0
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    def test_unlimited_budget(self):
        """
        WHEN no max_tokens is set, the system SHALL allow unlimited usage.
        """
        manager = TokenBudgetManager(max_tokens=None)
        
        # Should not exceed
        assert manager.exceeded() is False
        
        # Remaining should be -1 (unlimited)
        assert manager.get_remaining() == -1
        
        # No warning at threshold
        assert manager.warn_at_threshold() is False
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    def test_reset(self):
        """
        WHEN reset is called, the system SHALL clear all tracking.
        """
        manager = TokenBudgetManager(max_tokens=10000)
        
        # Track some usage
        manager.track_usage("file1.md", 5000)
        assert manager._current_usage == 5000
        
        # Reset
        manager.reset()
        
        # Verify reset
        assert manager._current_usage == 0
        assert manager._usage_per_file == {}
        assert manager._warnings_shown == set()
    
    @pytest.mark.property("Property 10: Performance Bounds")
    @pytest.mark.property("Property 11: Token Budget Enforcement")
    @given(st.integers(min_value=0, max_value=10000))
    def test_token_budget_property(self, tokens_used: int):
        """
        Property: Token Budget Enforcement
        For any token usage, the system should track correctly.
        """
        manager = TokenBudgetManager(max_tokens=10000)
        
        # Track usage
        manager.track_usage("test.md", tokens_used)
        
        # Verify usage is tracked
        assert manager._current_usage == tokens_used
        
        # Verify remaining
        expected_remaining = max(0, 10000 - tokens_used)
        assert manager.get_remaining() == expected_remaining
        
        # Verify exceeded status
        assert manager.exceeded() == (tokens_used > 10000)
