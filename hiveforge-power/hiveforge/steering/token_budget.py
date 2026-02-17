"""
Token budget management for the Steering Assistant v02.

This module provides the TokenBudgetManager class for tracking and managing
LLM token usage during generation.
"""

from typing import Dict, Optional


class TokenBudgetManager:
    """Manages token budget for LLM calls during generation."""
    
    def __init__(
        self,
        max_tokens: Optional[int] = None,
        warning_threshold: float = 0.9,
    ):
        """
        Initialize the TokenBudgetManager.
        
        Args:
            max_tokens: Maximum tokens allowed (None for unlimited)
            warning_threshold: Threshold for warning (0.0-1.0)
        """
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self._current_usage = 0
        self._usage_per_file: Dict[str, int] = {}
        self._warnings_shown: set = set()
    
    def track_usage(
        self,
        filename: str,
        tokens: int,
    ) -> None:
        """
        Track token usage for a file generation.
        
        Args:
            filename: Name of the file being generated
            tokens: Number of tokens used
        """
        self._current_usage += tokens
        self._usage_per_file[filename] = self._usage_per_file.get(filename, 0) + tokens
    
    def warn_at_threshold(self) -> bool:
        """
        Check if warning should be shown at threshold.
        
        Returns:
            True if warning should be shown
        """
        if self.max_tokens is None:
            return False
        
        usage_ratio = self._current_usage / self.max_tokens
        should_warn = usage_ratio >= self.warning_threshold
        
        if should_warn and "threshold" not in self._warnings_shown:
            self._warnings_shown.add("threshold")
            return True
        
        return False
    
    def exceeded(self) -> bool:
        """
        Check if token budget has been exceeded.
        
        Returns:
            True if budget exceeded
        """
        if self.max_tokens is None:
            return False
        
        return self._current_usage > self.max_tokens
    
    def get_remaining(self) -> int:
        """
        Calculate remaining tokens.
        
        Returns:
            Number of tokens remaining
        """
        if self.max_tokens is None:
            return -1  # Unlimited
        
        return max(0, self.max_tokens - self._current_usage)
    
    def estimate_cost(
        self,
        tokens: int,
        cost_per_million_tokens: float = 0.50,
    ) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            tokens: Number of tokens
            cost_per_million_tokens: Cost per million tokens (default: $0.50)
            
        Returns:
            Estimated cost in dollars
        """
        return (tokens / 1_000_000) * cost_per_million_tokens
    
    def get_usage_summary(self) -> Dict[str, any]:
        """
        Get usage summary.
        
        Returns:
            Dictionary with usage statistics
        """
        summary = {
            "current_usage": self._current_usage,
            "max_tokens": self.max_tokens,
            "remaining": self.get_remaining(),
            "usage_per_file": self._usage_per_file,
            "total_files": len(self._usage_per_file),
        }
        
        if self.max_tokens:
            summary["usage_percentage"] = (self._current_usage / self.max_tokens) * 100
        
        return summary
    
    def reset(self) -> None:
        """Reset token usage tracking."""
        self._current_usage = 0
        self._usage_per_file = {}
        self._warnings_shown = set()
    
    def display_warning(self) -> str:
        """
        Display warning message for approaching budget.
        
        Returns:
            Warning message string
        """
        if self.max_tokens is None:
            return "No token budget set"
        
        remaining = self.get_remaining()
        percentage = (self._current_usage / self.max_tokens) * 100
        
        return (
            f"⚠️  Token budget warning: {percentage:.1f}% used "
            f"({self._current_usage:,}/{self.max_tokens:,} tokens, {remaining:,} remaining)"
        )
    
    def display_exceeded_message(self) -> str:
        """
        Display message when budget is exceeded.
        
        Returns:
            Exceeded message string
        """
        if self.max_tokens is None:
            return "No token budget set"
        
        return (
            f"❌ Token budget exceeded: {self._current_usage:,}/{self.max_tokens:,} tokens. "
            f"Consider using fallback workflow or increasing budget."
        )
