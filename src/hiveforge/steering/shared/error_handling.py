"""
Error handling with automatic rollback for shared backend.

This module provides:
- Atomic operations with automatic backup and rollback
- Error context tracking for debugging
- Error collection for batch processing
- Rollback decorator for functions

**Validates: Requirements 1.16, 1.17**
"""

import functools
import logging
import shutil
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Error Severity and Context
# ============================================================================

class ErrorSeverity(Enum):
    """Severity levels for errors."""
    INFO = "info"           # Informational, no action needed
    WARNING = "warning"     # Warning, operation continues
    ERROR = "error"         # Error, operation may fail
    CRITICAL = "critical"   # Critical error, operation must stop


@dataclass
class ErrorContext:
    """
    Context information for error tracking.
    
    Captures all relevant information about an error for:
    - Debugging
    - User-friendly error messages
    - Recovery suggestions
    - Telemetry
    """
    error_type: str
    message: str
    severity: ErrorSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    operation: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: List[str] = field(default_factory=list)
    user_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "stack_trace": self.stack_trace,
            "context_data": self.context_data,
            "recovery_suggestions": self.recovery_suggestions,
            "user_message": self.user_message,
        }
    
    def format_for_user(self) -> str:
        """
        Format error for user display.
        
        Returns:
            User-friendly error message
        """
        if self.user_message:
            return self.user_message
        
        lines = [f"Error: {self.message}"]
        
        if self.recovery_suggestions:
            lines.append("\nSuggestions:")
            for suggestion in self.recovery_suggestions:
                lines.append(f"  • {suggestion}")
        
        return "\n".join(lines)
    
    def format_for_log(self) -> str:
        """
        Format error for logging.
        
        Returns:
            Detailed error message for logs
        """
        lines = [
            f"[{self.severity.value.upper()}] {self.error_type}: {self.message}",
            f"  Operation: {self.operation}",
            f"  Timestamp: {self.timestamp.isoformat()}",
        ]
        
        if self.file_path:
            lines.append(f"  File: {self.file_path}")
            if self.line_number:
                lines.append(f"  Line: {self.line_number}")
        
        if self.context_data:
            lines.append(f"  Context: {self.context_data}")
        
        if self.stack_trace:
            lines.append(f"  Stack trace:\n{self.stack_trace}")
        
        return "\n".join(lines)


class ErrorCollector:
    """
    Collect and manage errors during workflow execution.
    
    Allows workflows to collect multiple errors and warnings
    without immediately failing, then decide how to handle them.
    """
    
    def __init__(self):
        """Initialize error collector."""
        self.errors: List[ErrorContext] = []
        self.warnings: List[ErrorContext] = []
    
    def add_error(
        self,
        error_type: str,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        **kwargs
    ) -> ErrorContext:
        """
        Add an error to the collection.
        
        Args:
            error_type: Type of error
            message: Error message
            severity: Error severity
            **kwargs: Additional context data
            
        Returns:
            Created ErrorContext
        """
        context = ErrorContext(
            error_type=error_type,
            message=message,
            severity=severity,
            **kwargs
        )
        
        if severity in (ErrorSeverity.ERROR, ErrorSeverity.CRITICAL):
            self.errors.append(context)
        else:
            self.warnings.append(context)
        
        return context
    
    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0
    
    def has_critical_errors(self) -> bool:
        """Check if any critical errors were collected."""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)
    
    def get_all_errors(self) -> List[ErrorContext]:
        """Get all errors and warnings."""
        return self.errors + self.warnings
    
    def clear(self) -> None:
        """Clear all collected errors and warnings."""
        self.errors = []
        self.warnings = []


# ============================================================================
# Tool Executor with Rollback
# ============================================================================

class ToolExecutor:
    """
    Execute operations with automatic backup and rollback.
    
    Provides atomic operation execution:
    - Creates backup before operation
    - Executes operation
    - On success: Keeps changes, removes backup
    - On failure: Restores from backup
    
    Usage:
        executor = ToolExecutor(project_root=Path("."))
        
        with executor.atomic_operation("init_workflow"):
            # Perform operations
            create_files()
            modify_files()
            # If any exception occurs, automatic rollback
    """
    
    def __init__(
        self,
        project_root: Path,
        backup_dir: Optional[Path] = None,
        enable_rollback: bool = True
    ):
        """
        Initialize tool executor.
        
        Args:
            project_root: Root directory of the project
            backup_dir: Optional custom backup directory
            enable_rollback: Whether to enable automatic rollback
        """
        self.project_root = Path(project_root) if not isinstance(project_root, Path) else project_root
        self.backup_dir = backup_dir or (self.project_root / ".kiro" / ".backups")
        self.enable_rollback = enable_rollback
        self._current_backup: Optional[Path] = None
        self._operation_name: Optional[str] = None
    
    @contextmanager
    def atomic_operation(self, operation_name: str):
        """
        Context manager for atomic operations with rollback.
        
        Args:
            operation_name: Name of the operation (for logging)
            
        Yields:
            None
            
        Example:
            with executor.atomic_operation("create_files"):
                create_steering_files()
                # If exception occurs, automatic rollback
        """
        self._operation_name = operation_name
        backup_created = False
        
        try:
            # Step 1: Create backup
            if self.enable_rollback:
                self._current_backup = self._create_backup()
                if self._current_backup:
                    backup_created = True
                    logger.info(f"Created backup for {operation_name}: {self._current_backup}")
            
            # Step 2: Execute operation
            yield
            
            # Step 3: Success - commit changes
            logger.info(f"Operation {operation_name} completed successfully")
            
        except Exception as e:
            # Step 4: Failure - rollback
            logger.error(f"Operation {operation_name} failed: {e}")
            
            if backup_created and self.enable_rollback:
                logger.info(f"Rolling back {operation_name}...")
                self._rollback()
                logger.info(f"Rollback complete")
            
            # Re-raise exception for caller to handle
            raise
        
        finally:
            # Cleanup: Keep backup for retention policy
            self._current_backup = None
            self._operation_name = None
    
    def _create_backup(self) -> Optional[Path]:
        """
        Create backup of steering directory.
        
        Returns:
            Path to backup directory, or None if nothing to backup
        """
        steering_dir = self.project_root / ".kiro" / "steering"
        
        if not steering_dir.exists():
            # No steering directory to backup
            return None
        
        # Create backup directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}_{self._operation_name}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy all files
        file_count = 0
        for file_path in steering_dir.glob("*.md"):
            dest_path = backup_path / file_path.name
            shutil.copy2(file_path, dest_path)
            logger.debug(f"Backed up: {file_path.name}")
            file_count += 1
        
        if file_count == 0:
            # No files to backup, remove empty directory
            backup_path.rmdir()
            return None
        
        return backup_path
    
    def _rollback(self) -> None:
        """
        Rollback to backup.
        
        Restores all files from backup directory to steering directory.
        """
        if not self._current_backup or not self._current_backup.exists():
            logger.warning("No backup available for rollback")
            return
        
        steering_dir = self.project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove current files
        for file_path in steering_dir.glob("*.md"):
            file_path.unlink()
            logger.debug(f"Removed: {file_path.name}")
        
        # Restore from backup
        file_count = 0
        for backup_file in self._current_backup.glob("*.md"):
            dest_path = steering_dir / backup_file.name
            shutil.copy2(backup_file, dest_path)
            logger.debug(f"Restored: {backup_file.name}")
            file_count += 1
        
        logger.info(f"Restored {file_count} files from backup")
    
    def execute_with_rollback(
        self,
        operation: Callable[[], Any],
        operation_name: str
    ) -> Any:
        """
        Execute operation with automatic rollback on failure.
        
        Args:
            operation: Callable to execute
            operation_name: Name of the operation
            
        Returns:
            Result of operation
            
        Raises:
            Exception: If operation fails (after rollback)
        """
        with self.atomic_operation(operation_name):
            return operation()


# ============================================================================
# Rollback Decorator
# ============================================================================

def rollback_on_error(
    project_root: Optional[Path] = None,
    operation_name: Optional[str] = None
):
    """
    Decorator for automatic rollback on function failure.
    
    Args:
        project_root: Project root directory
        operation_name: Name of the operation (defaults to function name)
        
    Example:
        @rollback_on_error(project_root=Path("."), operation_name="init")
        def create_steering_files():
            # Create files
            # If exception occurs, automatic rollback
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get project_root from args if not provided
            root = project_root
            if root is None:
                # Try to extract from function arguments
                if args and isinstance(args[0], Path):
                    root = args[0]
                elif 'project_root' in kwargs:
                    root = kwargs['project_root']
                else:
                    root = Path(".")
            
            # Get operation name
            op_name = operation_name or func.__name__
            
            # Execute with rollback
            executor = ToolExecutor(project_root=root)
            return executor.execute_with_rollback(
                lambda: func(*args, **kwargs),
                op_name
            )
        
        return wrapper
    return decorator


# ============================================================================
# Error Handler with Retry Logic
# ============================================================================

class ErrorHandler:
    """
    Handle different types of errors with appropriate strategies.
    
    Strategies:
    - Retry with exponential backoff
    - Fallback to alternative approach
    - Collect and continue
    - Abort immediately
    """
    
    @staticmethod
    def retry_with_backoff(
        operation: Callable[[], Any],
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Retry operation with exponential backoff.
        
        Args:
            operation: Callable to retry
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds
            backoff_factor: Multiplier for delay after each retry
            exceptions: Tuple of exceptions to catch and retry
            
        Returns:
            Result of operation
            
        Raises:
            Exception: If all retries fail
        """
        import time
        
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except exceptions as e:
                last_exception = e
                
                if attempt < max_retries:
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
        
        # All retries failed
        raise last_exception
    
    @staticmethod
    def with_fallback(
        primary_operation: Callable[[], Any],
        fallback_operation: Callable[[], Any],
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Try primary operation, fallback to alternative on failure.
        
        Args:
            primary_operation: Primary operation to try
            fallback_operation: Fallback operation if primary fails
            exceptions: Tuple of exceptions to catch
            
        Returns:
            Result of primary or fallback operation
        """
        try:
            return primary_operation()
        except exceptions as e:
            logger.warning(f"Primary operation failed: {e}. Using fallback...")
            return fallback_operation()
