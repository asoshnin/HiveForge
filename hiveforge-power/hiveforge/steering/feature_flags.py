"""
Feature flag management for the Steering Assistant v02.

This module provides the FeatureFlagManager class for parsing CLI flags,
validating configurations, and determining workflow routing.
"""

from typing import List, Optional

from .models import FeatureFlagConfig


class FeatureFlagManager:
    """Manages feature flags for autonomous generation workflow."""
    
    def __init__(self, config: Optional[FeatureFlagConfig] = None):
        """
        Initialize the FeatureFlagManager.
        
        Args:
            config: Optional FeatureFlagConfig. If None, defaults are used.
        """
        self.config = config or FeatureFlagConfig()
    
    def load_from_cli(
        self,
        use_autonomous_generation: bool = False,
        confidence_threshold: float = 0.7,
        max_tokens: Optional[int] = None,
        discovery_paths: Optional[List[str]] = None,
        preserve_all: bool = False,
        telemetry_off: bool = False,
        max_discovery_files: int = 1000,
        max_file_size_mb: int = 10,
        conservative_inference: bool = False,
        interactive: bool = False,
    ) -> None:
        """
        Load feature flags from CLI arguments.
        
        Args:
            use_autonomous_generation: Enable autonomous generation workflow
            confidence_threshold: Minimum confidence for autonomous generation (0.0-1.0)
            max_tokens: Maximum tokens for LLM calls
            discovery_paths: Custom paths to search for documentation
            preserve_all: Skip updates to customized sections
            telemetry_off: Disable telemetry collection
            max_discovery_files: Maximum files to analyze during discovery
            max_file_size_mb: Maximum file size in MB to analyze
            conservative_inference: Reduce inference aggressiveness
            interactive: Force fallback to question workflow
        """
        self.config.use_autonomous_generation = use_autonomous_generation
        self.config.confidence_threshold = confidence_threshold
        self.config.max_tokens = max_tokens
        self.config.discovery_paths = discovery_paths or []
        self.config.preserve_all = preserve_all
        self.config.telemetry_off = telemetry_off
        self.config.max_discovery_files = max_discovery_files
        self.config.max_file_size_mb = max_file_size_mb
        self.config.conservative_inference = conservative_inference
        self.config.interactive = interactive
    
    def validate(self) -> List[str]:
        """
        Validate feature flag combinations and ranges.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        return self.config.validate()
    
    def get_workflow_type(self) -> str:
        """
        Determine which workflow type to use based on feature flags.
        
        Returns:
            "AUTONOMOUS" if autonomous generation is enabled and not interactive,
            "FALLBACK" otherwise
        """
        return self.config.get_workflow_type()
    
    def should_fallback(self, confidence: float) -> bool:
        """
        Check if fallback should be triggered based on confidence.
        
        Args:
            confidence: The confidence score to check
            
        Returns:
            True if fallback should be triggered
        """
        return self.config.should_fallback(confidence)
    
    def warn_high_threshold(self) -> bool:
        """
        Check if confidence threshold is high enough to warrant a warning.
        
        Returns:
            True if threshold > 0.95
        """
        return self.config.warn_high_threshold()
    
    def get_threshold_warning(self) -> Optional[str]:
        """
        Get warning message if threshold is too high.
        
        Returns:
            Warning message or None if threshold is acceptable
        """
        if self.warn_high_threshold():
            return (
                f"Warning: confidence_threshold is very high "
                f"({self.config.confidence_threshold}), most sections may "
                f"trigger fallback to question workflow"
            )
        return None
