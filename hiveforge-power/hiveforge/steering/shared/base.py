"""
Base classes for shared workflow implementation.

This module provides the foundation for all workflow adapters, ensuring
consistent behavior between CLI and Power interfaces.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from abc import ABC, abstractmethod

# Import error handling for rollback support
from .error_handling import ToolExecutor, ErrorCollector, ErrorSeverity


@dataclass
class WorkflowResult:
    """Result of a workflow execution.
    
    This standardized result format is used by both CLI and Power interfaces,
    ensuring consistent output regardless of the interface used.
    """
    
    success: bool
    message: str
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    files_deleted: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for JSON serialization (Power interface)."""
        return {
            "status": "success" if self.success else "failed",
            "message": self.message,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,
            "errors": self.errors,
            "warnings": self.warnings,
            **self.metadata
        }
    
    def format_for_cli(self) -> str:
        """Format result for CLI output."""
        lines = []
        
        if self.success:
            lines.append(f"✓ {self.message}")
        else:
            lines.append(f"✗ {self.message}")
        
        if self.files_created:
            lines.append(f"\nCreated {len(self.files_created)} file(s):")
            for file in self.files_created:
                lines.append(f"  + {file}")
        
        if self.files_modified:
            lines.append(f"\nModified {len(self.files_modified)} file(s):")
            for file in self.files_modified:
                lines.append(f"  ~ {file}")
        
        if self.files_deleted:
            lines.append(f"\nDeleted {len(self.files_deleted)} file(s):")
            for file in self.files_deleted:
                lines.append(f"  - {file}")
        
        if self.warnings:
            lines.append(f"\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
        
        if self.errors:
            lines.append(f"\nErrors:")
            for error in self.errors:
                lines.append(f"  ✗ {error}")
        
        return "\n".join(lines)


class SharedWorkflowBase(ABC):
    """Base class for all shared workflows.
    
    This class provides common functionality used by all workflow adapters,
    ensuring consistent behavior between CLI and Power interfaces.
    
    Key responsibilities:
    - Configuration validation
    - Path resolution and sanitization
    - Error handling hooks
    - Result formatting
    """
    
    def __init__(
        self,
        project_root: str | Path = ".",
        config: Optional[dict[str, Any]] = None,
        enable_rollback: bool = True
    ):
        """Initialize workflow with configuration.
        
        Args:
            project_root: Path to project root directory
            config: Optional configuration dictionary
            enable_rollback: Enable automatic rollback on failure (default: True)
        """
        self.project_root = Path(project_root).resolve()
        self.config = config or {}
        self.result = WorkflowResult(success=False, message="Not executed")
        self.enable_rollback = enable_rollback
        
        # Initialize error handling components
        self.tool_executor = ToolExecutor(
            project_root=self.project_root,
            enable_rollback=enable_rollback
        )
        self.error_collector = ErrorCollector()
        
        # Validate configuration
        self.validate_config()
    
    def validate_config(self) -> None:
        """Validate workflow configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate project root exists
        if not self.project_root.exists():
            raise ValueError(f"Project root does not exist: {self.project_root}")
        
        if not self.project_root.is_dir():
            raise ValueError(f"Project root is not a directory: {self.project_root}")
        
        # Subclasses can override to add more validation
        self._validate_specific_config()
    
    def _validate_specific_config(self) -> None:
        """Validate workflow-specific configuration.
        
        Subclasses should override this to add their own validation.
        """
        pass
    
    @abstractmethod
    def execute(self) -> WorkflowResult:
        """Execute the workflow.
        
        This is the main entry point for workflow execution.
        Subclasses must implement this method.
        
        Returns:
            WorkflowResult with execution results
        """
        pass
    
    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to project root.
        
        Args:
            path: Path to resolve (can be relative or absolute)
        
        Returns:
            Resolved absolute path
        """
        path = Path(path)
        
        if path.is_absolute():
            return path
        
        return (self.project_root / path).resolve()
    
    def _get_steering_dir(self) -> Path:
        """Get the steering directory path.
        
        Returns:
            Path to .kiro/steering directory
        """
        return self.project_root / ".kiro" / "steering"
    
    def _ensure_steering_dir(self) -> None:
        """Ensure steering directory exists."""
        steering_dir = self._get_steering_dir()
        steering_dir.mkdir(parents=True, exist_ok=True)
    
    def handle_error(self, error: Exception) -> WorkflowResult:
        """Handle workflow errors.
        
        This method provides consistent error handling across all workflows.
        Preserves any errors and warnings collected before the exception.
        
        Args:
            error: Exception that occurred
        
        Returns:
            WorkflowResult with error information
        """
        error_message = str(error)
        
        # Add error to collector
        self.error_collector.add_error(
            error_type=type(error).__name__,
            message=error_message,
            severity=ErrorSeverity.ERROR
        )
        
        # Get all collected errors and warnings (including the new one)
        all_errors = self._get_collected_errors()
        all_warnings = self._get_collected_warnings()
        
        return WorkflowResult(
            success=False,
            message=f"Workflow failed: {error_message}",
            errors=all_errors,
            warnings=all_warnings
        )
    
    def _add_warning(self, message: str) -> None:
        """Add a warning to the error collector.
        
        Args:
            message: Warning message
        """
        self.error_collector.add_error(
            error_type="Warning",
            message=message,
            severity=ErrorSeverity.WARNING
        )
    
    def _add_error(self, message: str, error_type: str = "Error") -> None:
        """Add an error to the error collector.
        
        Args:
            message: Error message
            error_type: Type of error
        """
        self.error_collector.add_error(
            error_type=error_type,
            message=message,
            severity=ErrorSeverity.ERROR
        )
    
    def _get_collected_errors(self) -> list[str]:
        """Get all collected error messages.
        
        Returns:
            List of error messages
        """
        return [error.message for error in self.error_collector.errors]
    
    def _get_collected_warnings(self) -> list[str]:
        """Get all collected warning messages.
        
        Returns:
            List of warning messages
        """
        return [warning.message for warning in self.error_collector.warnings]
    
    def _create_success_result(
        self,
        message: str,
        **kwargs: Any
    ) -> WorkflowResult:
        """Create a success result.
        
        Args:
            message: Success message
            **kwargs: Additional result fields
        
        Returns:
            WorkflowResult indicating success
        """
        return WorkflowResult(
            success=True,
            message=message,
            **kwargs
        )
    
    def _create_failure_result(
        self,
        message: str,
        errors: Optional[list[str]] = None,
        **kwargs: Any
    ) -> WorkflowResult:
        """Create a failure result.
        
        Args:
            message: Failure message
            errors: List of error messages
            **kwargs: Additional result fields
        
        Returns:
            WorkflowResult indicating failure
        """
        return WorkflowResult(
            success=False,
            message=message,
            errors=errors or [],
            **kwargs
        )
