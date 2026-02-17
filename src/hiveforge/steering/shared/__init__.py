"""
Shared backend module for steering assistant.

This module provides common functionality used by both CLI and Power interfaces,
ensuring identical behavior and maintaining a single source of truth.

Architecture:
- base.py: Base classes for workflows
- adapters.py: Workflow adapters for CLI and Power
- security_wrappers.py: Security validation and sanitization
- error_handling.py: Error handling with automatic rollback
- telemetry.py: Usage tracking and analytics
"""

from .base import SharedWorkflowBase, WorkflowResult
from .adapters import (
    SharedInitWorkflow,
    SharedUpdateWorkflow,
    SharedValidateWorkflow,
    SharedResetWorkflow,
    SharedDiscoveryWorkflow,
)

__all__ = [
    "SharedWorkflowBase",
    "WorkflowResult",
    "SharedInitWorkflow",
    "SharedUpdateWorkflow",
    "SharedValidateWorkflow",
    "SharedResetWorkflow",
    "SharedDiscoveryWorkflow",
]
