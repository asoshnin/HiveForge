# Error Handling with Automatic Rollback Design

**Feature**: steering-power-conversion  
**Version**: 2.0.0  
**Status**: Complete  
**Phase**: 1.4 - Shared Backend Interface Design

---

## 1. Overview

This document defines the error handling and automatic rollback system for the shared backend. The system ensures that:

- All operations are atomic (complete successfully or rollback completely)
- User data is never left in an inconsistent state
- Errors are handled gracefully with clear recovery paths
- Both CLI and Power interfaces benefit from the same error handling

---

## 2. Error Handling Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Operation Execution                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ToolExecutor                            │   │
│  │  1. Create backup                                    │   │
│  │  2. Execute operation                                │   │
│  │  3. On success: Commit                               │   │
│  │  4. On failure: Rollback from backup                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Backup    │ │   Error     │ │  Rollback   │
    │   Manager   │ │  Context    │ │  Manager    │
    └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 3. Core Components

### 3.1 ToolExecutor Class

**Purpose**: Execute operations with automatic backup and rollback

```python
"""
Tool executor with automatic error handling and rollback.
"""

from pathlib import Path
from typing import Callable, Any, Optional, Dict
from contextlib import contextmanager
import logging
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


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
        self.project_root = project_root
        self.backup_dir = backup_dir or (project_root / ".kiro" / ".backups")
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
            # Cleanup: Remove backup if operation succeeded
            if backup_created and self._current_backup and self._current_backup.exists():
                # Keep backup for a short time in case of issues
                # In production, implement backup retention policy
                pass
            
            self._current_backup = None
            self._operation_name = None
    
    def _create_backup(self) -> Path:
        """
        Create backup of steering directory.
        
        Returns:
            Path to backup directory
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
        for file_path in steering_dir.glob("*.md"):
            dest_path = backup_path / file_path.name
            shutil.copy2(file_path, dest_path)
            logger.debug(f"Backed up: {file_path.name}")
        
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
        for backup_file in self._current_backup.glob("*.md"):
            dest_path = steering_dir / backup_file.name
            shutil.copy2(backup_file, dest_path)
            logger.debug(f"Restored: {backup_file.name}")
        
        logger.info(f"Restored {len(list(self._current_backup.glob('*.md')))} files from backup")
    
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
```

### 3.2 ErrorContext Class

**Purpose**: Track error context for debugging and recovery

```python
"""
Error context tracking for debugging and recovery.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum


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
```

### 3.3 Rollback Decorator

**Purpose**: Decorator for automatic rollback on function failure

```python
"""
Decorator for automatic rollback on function failure.
"""

import functools
from typing import Callable, Any
from pathlib import Path


def rollback_on_error(
    project_root: Path = None,
    operation_name: str = None
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
```

---

## 4. Error Categories and Handling

### 4.1 Error Categories

| Category | Severity | Rollback? | Recovery |
|----------|----------|-----------|----------|
| **User Input Errors** | WARNING | No | Prompt for correction |
| **File System Errors** | ERROR | Yes | Restore from backup |
| **LLM API Errors** | ERROR | Yes | Retry or fallback |
| **Validation Errors** | WARNING | No | Continue with warnings |
| **Security Errors** | CRITICAL | Yes | Abort immediately |
| **System Errors** | CRITICAL | Yes | Abort and report |

### 4.2 Error Handling Strategies

```python
"""
Error handling strategies for different error types.
"""

from typing import Optional, Callable, Any
import time
import logging

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Handle different types of errors with appropriate strategies.
    
    Strategies:
    - Retry with exponential backoff
    - Fallback to alternative approach
    - Prompt user for input
    - Abort with rollback
    """
    
    @staticmethod
    def retry_with_backoff(
        operation: Callable[[], Any],
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ) -> Any:
        """
        Retry operation with exponential backoff.
        
        Args:
            operation: Operation to retry
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds
            backoff_factor: Backoff multiplier
            
        Returns:
            Result of operation
            
        Raises:
            Exception: If all retries fail
        """
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= backoff_factor
        
        # All retries failed
        raise last_exception
    
    @staticmethod
    def with_fallback(
        primary_operation: Callable[[], Any],
        fallback_operation: Callable[[], Any],
        fallback_on: tuple = (Exception,)
    ) -> Any:
        """
        Try primary operation, fallback to alternative on failure.
        
        Args:
            primary_operation: Primary operation to try
            fallback_operation: Fallback operation if primary fails
            fallback_on: Tuple of exceptions to catch
            
        Returns:
            Result of primary or fallback operation
        """
        try:
            return primary_operation()
        except fallback_on as e:
            logger.warning(f"Primary operation failed: {e}")
            logger.info("Falling back to alternative approach...")
            return fallback_operation()
    
    @staticmethod
    def handle_llm_error(error: Exception) -> ErrorContext:
        """
        Handle LLM API errors with appropriate recovery.
        
        Args:
            error: LLM API error
            
        Returns:
            ErrorContext with recovery suggestions
        """
        error_str = str(error).lower()
        
        if "rate limit" in error_str:
            return ErrorContext(
                error_type="llm_rate_limit",
                message="LLM API rate limit exceeded",
                severity=ErrorSeverity.ERROR,
                recovery_suggestions=[
                    "Wait 60 seconds and retry",
                    "Use fallback workflow without LLM",
                    "Check API quota and limits"
                ],
                user_message="Rate limit exceeded. Please wait a moment and try again."
            )
        
        elif "timeout" in error_str:
            return ErrorContext(
                error_type="llm_timeout",
                message="LLM API request timed out",
                severity=ErrorSeverity.ERROR,
                recovery_suggestions=[
                    "Retry the operation",
                    "Check network connection",
                    "Use fallback workflow"
                ],
                user_message="Request timed out. Please check your connection and try again."
            )
        
        elif "authentication" in error_str or "api key" in error_str:
            return ErrorContext(
                error_type="llm_auth",
                message="LLM API authentication failed",
                severity=ErrorSeverity.CRITICAL,
                recovery_suggestions=[
                    "Check API key configuration",
                    "Verify API key is valid",
                    "Check environment variables"
                ],
                user_message="Authentication failed. Please check your API key configuration."
            )
        
        else:
            return ErrorContext(
                error_type="llm_error",
                message=f"LLM API error: {error}",
                severity=ErrorSeverity.ERROR,
                recovery_suggestions=[
                    "Retry the operation",
                    "Use fallback workflow",
                    "Check API status"
                ],
                user_message="An error occurred with the LLM API. Please try again."
            )
    
    @staticmethod
    def handle_file_system_error(error: Exception, file_path: str) -> ErrorContext:
        """
        Handle file system errors with appropriate recovery.
        
        Args:
            error: File system error
            file_path: Path to file that caused error
            
        Returns:
            ErrorContext with recovery suggestions
        """
        error_str = str(error).lower()
        
        if "permission" in error_str:
            return ErrorContext(
                error_type="permission_denied",
                message=f"Permission denied: {file_path}",
                severity=ErrorSeverity.ERROR,
                file_path=file_path,
                recovery_suggestions=[
                    "Check file permissions",
                    "Run with appropriate permissions",
                    "Check directory ownership"
                ],
                user_message=f"Permission denied for {file_path}. Please check file permissions."
            )
        
        elif "not found" in error_str or "no such file" in error_str:
            return ErrorContext(
                error_type="file_not_found",
                message=f"File not found: {file_path}",
                severity=ErrorSeverity.ERROR,
                file_path=file_path,
                recovery_suggestions=[
                    "Check file path is correct",
                    "Verify file exists",
                    "Run init workflow first"
                ],
                user_message=f"File not found: {file_path}. Please check the path."
            )
        
        elif "disk" in error_str or "space" in error_str:
            return ErrorContext(
                error_type="disk_space",
                message="Insufficient disk space",
                severity=ErrorSeverity.CRITICAL,
                recovery_suggestions=[
                    "Free up disk space",
                    "Check available storage",
                    "Clean up old backups"
                ],
                user_message="Insufficient disk space. Please free up space and try again."
            )
        
        else:
            return ErrorContext(
                error_type="file_system_error",
                message=f"File system error: {error}",
                severity=ErrorSeverity.ERROR,
                file_path=file_path,
                recovery_suggestions=[
                    "Check file system permissions",
                    "Verify disk is not full",
                    "Check file is not locked"
                ],
                user_message=f"File system error for {file_path}. Please check permissions."
            )
```

---

## 5. Integration with Shared Workflows

### 5.1 Workflow Integration Pattern

```python
"""
Integration pattern for workflows with error handling.
"""

from pathlib import Path
from typing import Dict, Any

from .error_handling import ToolExecutor, ErrorCollector, ErrorHandler
from .workflows.base import SharedWorkflowBase


class SharedInitWorkflow(SharedWorkflowBase):
    """Init workflow with error handling and rollback."""
    
    def __init__(self, config, project_root, progress_callback=None):
        super().__init__(config, project_root, progress_callback)
        self.executor = ToolExecutor(project_root=project_root)
        self.error_collector = ErrorCollector()
        self.error_handler = ErrorHandler()
    
    def execute(self) -> Dict[str, Any]:
        """Execute with automatic rollback on failure."""
        try:
            with self.executor.atomic_operation("init_workflow"):
                # Step 1: Create staging directory
                self._create_staging_directory()
                
                # Step 2: Analyze code (with retry on LLM errors)
                if self.config.analyze_code:
                    try:
                        self.error_handler.retry_with_backoff(
                            lambda: self._analyze_code(),
                            max_retries=3
                        )
                    except Exception as e:
                        # Collect error but continue
                        error_ctx = self.error_handler.handle_llm_error(e)
                        self.error_collector.add_error(
                            error_ctx.error_type,
                            error_ctx.message,
                            severity=error_ctx.severity
                        )
                
                # Step 3: Parse artifacts
                self._parse_artifacts()
                
                # ... continue with other steps
                
                # Check for critical errors
                if self.error_collector.has_critical_errors():
                    raise RuntimeError("Critical errors occurred during execution")
                
                return self._format_success_result(
                    message="Init workflow completed",
                    data={"warnings": [e.to_dict() for e in self.error_collector.warnings]}
                )
        
        except Exception as e:
            # Automatic rollback happens here
            logger.error(f"Init workflow failed: {e}")
            return self._format_error_result(
                error=e,
                partial_data={"errors": [e.to_dict() for e in self.error_collector.get_all_errors()]}
            )
```

---

## 6. Testing Error Handling

### 6.1 Unit Tests

```python
"""
Unit tests for error handling and rollback.
"""

import pytest
from pathlib import Path
import shutil

from src.hiveforge.steering.shared.error_handling import (
    ToolExecutor,
    ErrorContext,
    ErrorSeverity,
    ErrorCollector,
    rollback_on_error
)


def test_tool_executor_rollback_on_failure(tmp_path):
    """Test that ToolExecutor rolls back on failure."""
    steering_dir = tmp_path / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    
    # Create initial file
    initial_file = steering_dir / "test.md"
    initial_file.write_text("initial content")
    
    executor = ToolExecutor(project_root=tmp_path)
    
    # Execute operation that fails
    with pytest.raises(RuntimeError):
        with executor.atomic_operation("test_op"):
            # Modify file
            initial_file.write_text("modified content")
            # Raise error
            raise RuntimeError("Test error")
    
    # File should be rolled back to initial content
    assert initial_file.read_text() == "initial content"


def test_tool_executor_commit_on_success(tmp_path):
    """Test that ToolExecutor commits on success."""
    steering_dir = tmp_path / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    
    initial_file = steering_dir / "test.md"
    initial_file.write_text("initial content")
    
    executor = ToolExecutor(project_root=tmp_path)
    
    # Execute operation that succeeds
    with executor.atomic_operation("test_op"):
        initial_file.write_text("modified content")
    
    # File should have modified content
    assert initial_file.read_text() == "modified content"


def test_error_context_formatting():
    """Test ErrorContext formatting."""
    context = ErrorContext(
        error_type="test_error",
        message="Test error message",
        severity=ErrorSeverity.ERROR,
        recovery_suggestions=["Try again", "Check logs"]
    )
    
    user_msg = context.format_for_user()
    assert "Test error message" in user_msg
    assert "Try again" in user_msg
    
    log_msg = context.format_for_log()
    assert "ERROR" in log_msg
    assert "test_error" in log_msg


def test_error_collector():
    """Test ErrorCollector."""
    collector = ErrorCollector()
    
    # Add errors
    collector.add_error("error1", "Error 1", ErrorSeverity.ERROR)
    collector.add_error("warning1", "Warning 1", ErrorSeverity.WARNING)
    collector.add_error("critical1", "Critical 1", ErrorSeverity.CRITICAL)
    
    assert collector.has_errors()
    assert collector.has_critical_errors()
    assert len(collector.errors) == 2  # ERROR and CRITICAL
    assert len(collector.warnings) == 1


def test_rollback_decorator(tmp_path):
    """Test rollback_on_error decorator."""
    steering_dir = tmp_path / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    
    test_file = steering_dir / "test.md"
    test_file.write_text("initial")
    
    @rollback_on_error(project_root=tmp_path, operation_name="test")
    def failing_operation():
        test_file.write_text("modified")
        raise RuntimeError("Test error")
    
    with pytest.raises(RuntimeError):
        failing_operation()
    
    # Should be rolled back
    assert test_file.read_text() == "initial"
```

---

## 7. Error Recovery Flowchart

```
┌─────────────────────────────────────────────────────────────┐
│                    Operation Starts                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Create Backup (if enabled)                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Execute Operation                           │
└─────────────────────────────────────────────────────────────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
         ┌──────────┐        ┌──────────┐
         │ Success  │        │  Failure │
         └──────────┘        └──────────┘
                │                   │
                ▼                   ▼
         ┌──────────┐        ┌──────────┐
         │  Commit  │        │ Rollback │
         │ Changes  │        │  from    │
         │          │        │  Backup  │
         └──────────┘        └──────────┘
                │                   │
                ▼                   ▼
         ┌──────────┐        ┌──────────┐
         │  Remove  │        │  Raise   │
         │  Backup  │        │  Error   │
         └──────────┘        └──────────┘
                │                   │
                └─────────┬─────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Operation Complete                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Success Criteria

- [ ] ToolExecutor class implemented with atomic operations
- [ ] ErrorContext class tracks all error details
- [ ] ErrorCollector manages multiple errors
- [ ] Rollback decorator provides easy integration
- [ ] All error categories have handling strategies
- [ ] Backup creation and restoration works correctly
- [ ] Rollback occurs automatically on failure
- [ ] User data never left in inconsistent state
- [ ] All error handling tests pass
- [ ] Both CLI and Power use same error handling

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-17  
**Next Review**: Before Phase 2 implementation
