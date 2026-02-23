"""
Security wrapper for MCP tool execution.

This module provides comprehensive security controls for all MCP tool invocations:
- Input validation for all parameters
- Path sanitization to prevent directory traversal
- Resource limits to prevent denial of service
- Error obfuscation to prevent information disclosure
- Audit logging for security events

**Validates: Requirements 1.13, 1.14, 1.15**
"""

import functools
import time
import logging
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Security Exceptions
# ============================================================================

class SecurityError(Exception):
    """Base exception for security violations."""
    
    def __init__(self, message: str, violation_type: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.violation_type = violation_type
        self.details = details or {}


class InputValidationError(SecurityError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str, value: Any, constraints: Dict[str, Any]):
        super().__init__(message, "input_validation", {
            "field": field,
            "value": repr(value),
            "constraints": constraints
        })
        self.field = field
        self.value = value
        self.constraints = constraints


class PathTraversalError(SecurityError):
    """Raised when path traversal is detected."""
    
    def __init__(self, message: str, attempted_path: str, resolved_path: str):
        super().__init__(message, "path_traversal", {
            "attempted_path": attempted_path,
            "resolved_path": resolved_path
        })
        self.attempted_path = attempted_path
        self.resolved_path = resolved_path


class ResourceLimitError(SecurityError):
    """Raised when resource limits are exceeded."""
    
    def __init__(self, message: str, resource_type: str, limit: Any, actual: Any):
        super().__init__(message, "resource_limit", {
            "resource_type": resource_type,
            "limit": limit,
            "actual": actual
        })
        self.resource_type = resource_type
        self.limit = limit
        self.actual = actual


# ============================================================================
# Security Context
# ============================================================================

class SecurityContext:
    """Context for security tracking."""
    
    def __init__(self, tool_name: str, start_time: float):
        self.tool_name = tool_name
        self.start_time = start_time
        self.event_id = str(uuid.uuid4())[:8]
        self.validated_inputs: Dict[str, Any] = {}
        self.sanitized_paths: Dict[str, str] = {}
        self.resource_usage: Dict[str, Any] = {}
        self.warnings: list = []
    
    def add_warning(self, warning: str) -> None:
        """Add a security warning."""
        self.warnings.append({
            "warning": warning,
            "timestamp": time.time(),
        })


# ============================================================================
# Security Decorator
# ============================================================================

def secure_execution(
    max_memory_mb: int = 512,
    max_cpu_time_sec: int = 300,
    max_file_size_mb: int = 10,
    allowed_directories: Optional[list] = None,
    enable_input_validation: bool = True,
    enable_path_sanitization: bool = True,
    enable_resource_limits: bool = True,
    enable_error_obfuscation: bool = True,
):
    """
    Security decorator for MCP tool execution.
    
    This decorator wraps tool functions with comprehensive security controls:
    - Input validation for all parameters
    - Path sanitization to prevent directory traversal
    - Resource limits to prevent denial of service
    - Error obfuscation to prevent information disclosure
    
    Args:
        max_memory_mb: Maximum memory usage in megabytes
        max_cpu_time_sec: Maximum CPU time in seconds
        max_file_size_mb: Maximum file size for operations
        allowed_directories: List of allowed base directories
        enable_input_validation: Whether to validate inputs
        enable_path_sanitization: Whether to sanitize paths
        enable_resource_limits: Whether to enforce resource limits
        enable_error_obfuscation: Whether to obfuscate errors
        
    Returns:
        Decorated function with security controls
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Start security context
            security_context = SecurityContext(
                tool_name=func.__name__,
                start_time=time.time(),
            )
            
            try:
                # Step 1: Validate all inputs
                if enable_input_validation:
                    kwargs = validate_inputs(kwargs, security_context)
                
                # Step 2: Sanitize paths
                if enable_path_sanitization:
                    kwargs = sanitize_paths(kwargs, allowed_directories, security_context)
                
                # Step 3: Enforce resource limits
                if enable_resource_limits:
                    with ResourceLimiter(
                        max_memory_mb=max_memory_mb,
                        max_cpu_time_sec=max_cpu_time_sec,
                        max_file_size_mb=max_file_size_mb,
                    ):
                        result = await func(*args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                # Step 4: Obfuscate errors for users
                if enable_error_obfuscation:
                    result = obfuscate_errors(result, security_context)
                
                # Log successful execution
                log_security_event(
                    event_type="execution_success",
                    tool_name=func.__name__,
                    duration=time.time() - security_context.start_time,
                    context=security_context,
                )
                
                return result
                
            except SecurityError as e:
                # Log security violation
                log_security_event(
                    event_type="security_violation",
                    tool_name=func.__name__,
                    error=e,
                    context=security_context,
                )
                
                # Return user-friendly error
                return {
                    "status": "failed",
                    "error_type": e.violation_type,
                    "message": get_user_friendly_message(e),
                    "can_retry": False,
                    "security_event_id": security_context.event_id,
                }
                
            except Exception as e:
                # Log unexpected error
                logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                
                log_security_event(
                    event_type="unexpected_error",
                    tool_name=func.__name__,
                    error=e,
                    context=security_context,
                )
                
                # Return obfuscated error
                return {
                    "status": "failed",
                    "error_type": "internal_error",
                    "message": "An internal error occurred. Please try again.",
                    "can_retry": True,
                    "security_event_id": security_context.event_id,
                }
        
        return wrapper
    return decorator


# ============================================================================
# Input Validation
# ============================================================================

def validate_inputs(kwargs: Dict[str, Any], context: SecurityContext) -> Dict[str, Any]:
    """Validate all input parameters."""
    validated = {}
    
    for key, value in kwargs.items():
        try:
            validated[key] = validate_parameter(key, value, context)
        except InputValidationError as e:
            logger.warning(f"Input validation failed for {key}: {e}")
            raise
    
    context.validated_inputs = validated
    return validated


def validate_parameter(name: str, value: Any, context: SecurityContext) -> Any:
    """Validate a single parameter."""
    # Type-specific validation
    if name == "project_root":
        return validate_project_root(value)
    elif name == "source_docs_path":
        return validate_source_docs_path(value)
    elif name in ("files", "target_files"):
        return validate_file_list(value)
    elif name == "confidence_threshold":
        return validate_confidence_threshold(value)
    elif name in ("auto_discover", "autonomous", "preserve_customizations", 
                  "incremental", "strict", "use_llm", "include_git_history", "confirm",
                  "dry_run", "copy_files"):
        return validate_boolean(value, name)
    elif name == "file":
        return validate_single_file(value)
    elif name in ("max_discovery_files", "max_file_size_mb"):
        return validate_positive_integer(value, name)
    elif name == "file_types":
        return validate_file_types(value)
    else:
        # Unknown parameter - log warning
        context.add_warning(f"Unknown parameter: {name}")
        return value


def validate_project_root(value: Any) -> str:
    """Validate project root parameter."""
    if value is None:
        return "."
    
    if not isinstance(value, str):
        raise InputValidationError(
            f"project_root must be a string, got {type(value).__name__}",
            field="project_root",
            value=value,
            constraints={"type": "string"}
        )
    
    if len(value) > 4096:
        raise InputValidationError(
            f"project_root exceeds maximum length",
            field="project_root",
            value=value[:100] + "...",
            constraints={"max_length": 4096}
        )
    
    # Check for null bytes and other dangerous characters
    if "\x00" in value:
        raise InputValidationError(
            "project_root contains null bytes",
            field="project_root",
            value=value,
            constraints={"forbidden_chars": ["\x00"]}
        )
    
    return value


def validate_file_list(value: Any) -> list:
    """Validate file list parameter."""
    if value is None:
        return []
    
    if not isinstance(value, list):
        raise InputValidationError(
            f"files must be a list, got {type(value).__name__}",
            field="files",
            value=value,
            constraints={"type": "list"}
        )
    
    if len(value) > 100:
        raise InputValidationError(
            f"files list exceeds maximum length",
            field="files",
            value=f"list of {len(value)} items",
            constraints={"max_items": 100}
        )
    
    validated = []
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise InputValidationError(
                f"files[{i}] must be a string, got {type(item).__name__}",
                field=f"files[{i}]",
                value=item,
                constraints={"type": "string"}
            )
        
        # Validate each file path
        validated.append(validate_single_file(item))
    
    return validated


def validate_single_file(value: Any) -> str:
    """Validate a single file path parameter."""
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise InputValidationError(
            f"file path must be a string, got {type(value).__name__}",
            field="file",
            value=value,
            constraints={"type": "string"}
        )
    
    if len(value) > 4096:
        raise InputValidationError(
            f"file path exceeds maximum length",
            field="file",
            value=value[:100] + "...",
            constraints={"max_length": 4096}
        )
    
    # Check for null bytes
    if "\x00" in value:
        raise InputValidationError(
            "file path contains null bytes",
            field="file",
            value=value,
            constraints={"forbidden_chars": ["\x00"]}
        )
    
    return value


def validate_confidence_threshold(value: Any) -> float:
    """Validate confidence threshold parameter."""
    if value is None:
        return 0.7
    
    try:
        threshold = float(value)
    except (TypeError, ValueError):
        raise InputValidationError(
            f"confidence_threshold must be a number, got {type(value).__name__}",
            field="confidence_threshold",
            value=value,
            constraints={"type": "number"}
        )
    
    if not 0.0 <= threshold <= 1.0:
        raise InputValidationError(
            f"confidence_threshold must be between 0.0 and 1.0, got {threshold}",
            field="confidence_threshold",
            value=threshold,
            constraints={"min": 0.0, "max": 1.0}
        )
    
    return threshold


def validate_boolean(value: Any, name: str) -> bool:
    """Validate boolean parameter."""
    if value is None:
        return False
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        lower = value.lower()
        if lower in ("true", "1", "yes", "on"):
            return True
        elif lower in ("false", "0", "no", "off"):
            return False
    
    raise InputValidationError(
        f"{name} must be a boolean, got {type(value).__name__}",
        field=name,
        value=value,
        constraints={"type": "boolean"}
    )


def validate_source_docs_path(value: Any) -> Optional[str]:
    """Validate source_docs_path parameter."""
    if value is None:
        return None
    
    if not isinstance(value, str):
        raise InputValidationError(
            f"source_docs_path must be a string, got {type(value).__name__}",
            field="source_docs_path",
            value=value,
            constraints={"type": "string"}
        )
    
    if len(value) > 4096:
        raise InputValidationError(
            f"source_docs_path exceeds maximum length",
            field="source_docs_path",
            value=value[:100] + "...",
            constraints={"max_length": 4096}
        )
    
    # Check for null bytes
    if "\x00" in value:
        raise InputValidationError(
            "source_docs_path contains null bytes",
            field="source_docs_path",
            value=value,
            constraints={"forbidden_chars": ["\x00"]}
        )
    
    return value


def validate_positive_integer(value: Any, name: str) -> int:
    """Validate positive integer parameter."""
    if value is None:
        return 0
    
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise InputValidationError(
            f"{name} must be an integer, got {type(value).__name__}",
            field=name,
            value=value,
            constraints={"type": "integer"}
        )
    
    if int_value < 0:
        raise InputValidationError(
            f"{name} must be positive, got {int_value}",
            field=name,
            value=int_value,
            constraints={"min": 0}
        )
    
    return int_value


def validate_file_types(value: Any) -> Optional[list]:
    """Validate file_types parameter."""
    if value is None:
        return None
    
    if not isinstance(value, list):
        raise InputValidationError(
            f"file_types must be a list, got {type(value).__name__}",
            field="file_types",
            value=value,
            constraints={"type": "list"}
        )
    
    if len(value) > 50:
        raise InputValidationError(
            f"file_types list exceeds maximum length",
            field="file_types",
            value=f"list of {len(value)} items",
            constraints={"max_items": 50}
        )
    
    validated = []
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise InputValidationError(
                f"file_types[{i}] must be a string, got {type(item).__name__}",
                field=f"file_types[{i}]",
                value=item,
                constraints={"type": "string"}
            )
        validated.append(item)
    
    return validated


# ============================================================================
# Path Sanitization
# ============================================================================

def sanitize_paths(
    kwargs: Dict[str, Any],
    allowed_directories: Optional[list],
    context: SecurityContext
) -> Dict[str, Any]:
    """Sanitize all path parameters."""
    sanitized = {}
    
    for key, value in kwargs.items():
        # source_docs_path should remain relative, not be converted to absolute
        if key == "source_docs_path":
            sanitized[key] = value
        elif key in ("project_root", "file", "files", "target_files"):
            if isinstance(value, str):
                sanitized[key] = sanitize_path(value, allowed_directories, context)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_path(v, allowed_directories, context) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        else:
            sanitized[key] = value
    
    context.sanitized_paths = sanitized
    return sanitized


def sanitize_path(
    path: str,
    allowed_directories: Optional[list],
    context: SecurityContext
) -> str:
    """
    Sanitize a file path to prevent directory traversal attacks.
    
    This function:
    1. Resolves the path to an absolute path
    2. Normalizes the path (removes redundant components)
    3. Checks for path traversal attempts
    4. Validates the path is within allowed directories
    5. Returns the sanitized path
    
    Args:
        path: The path to sanitize
        allowed_directories: List of allowed base directories
        context: Security context for tracking
        
    Returns:
        Sanitized absolute path
        
    Raises:
        PathTraversalError: If the path is malicious or outside allowed directories
    """
    if not path:
        return "."
    
    # Create Path object
    path_obj = Path(path)
    
    # Resolve to absolute path
    try:
        abs_path = path_obj.resolve()
    except (OSError, ValueError) as e:
        raise PathTraversalError(
            f"Invalid path: {e}",
            attempted_path=path,
            resolved_path=str(path_obj),
        )
    
    # Check for null bytes (already validated in input, but double-check)
    path_str = str(abs_path)
    if "\x00" in path_str:
        raise PathTraversalError(
            "Path contains null bytes",
            attempted_path=path,
            resolved_path=path_str,
        )
    
    # Check for unusual path separators or encoding
    if path != path.strip():
        context.add_warning(f"Path had leading/trailing whitespace: {path}")
        path = path.strip()
        abs_path = Path(path).resolve()
    
    # Validate against allowed directories
    if allowed_directories:
        allowed = [Path(d).resolve() for d in allowed_directories]
        is_allowed = any(
            str(abs_path).startswith(str(allowed_dir) + "/") or str(abs_path) == str(allowed_dir)
            for allowed_dir in allowed
        )
        
        if not is_allowed:
            raise PathTraversalError(
                f"Path is outside allowed directories",
                attempted_path=path,
                resolved_path=path_str,
            )
    
    return str(abs_path)


# ============================================================================
# Resource Limiter
# ============================================================================

class ResourceLimiter:
    """
    Enforce resource limits for tool execution.
    
    This class uses Python's resource module to set limits on:
    - Maximum memory usage (RLIMIT_AS)
    - Maximum CPU time (RLIMIT_CPU)
    - Maximum file size (RLIMIT_FSIZE)
    """
    
    def __init__(
        self,
        max_memory_mb: int = 512,
        max_cpu_time_sec: int = 300,
        max_file_size_mb: int = 10,
    ):
        """
        Initialize resource limiter.
        
        Args:
            max_memory_mb: Maximum memory usage in megabytes
            max_cpu_time_sec: Maximum CPU time in seconds
            max_file_size_mb: Maximum file size for writes
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_cpu_time_sec = max_cpu_time_sec
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        self.original_limits = {}
        self.start_time = None
    
    def __enter__(self) -> "ResourceLimiter":
        """Enter resource limit context."""
        try:
            import resource
            
            self.start_time = time.time()
            
            # Save original limits
            try:
                self.original_limits["as"] = resource.getrlimit(resource.RLIMIT_AS)
                self.original_limits["cpu"] = resource.getrlimit(resource.RLIMIT_CPU)
                self.original_limits["fsize"] = resource.getrlimit(resource.RLIMIT_FSIZE)
            except (ValueError, OSError) as e:
                logger.warning(f"Could not get resource limits: {e}")
            
            # Set new limits
            try:
                # Set memory limit
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (self.max_memory_bytes, self.original_limits.get("as", (resource.RLIM_INFINITY, resource.RLIM_INFINITY))[1])
                )
            except (ValueError, OSError) as e:
                logger.warning(f"Could not set memory limit: {e}")
            
            try:
                # Set CPU time limit
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (self.max_cpu_time_sec, self.original_limits.get("cpu", (resource.RLIM_INFINITY, resource.RLIM_INFINITY))[1])
                )
            except (ValueError, OSError) as e:
                logger.warning(f"Could not set CPU time limit: {e}")
            
            try:
                # Set file size limit
                resource.setrlimit(
                    resource.RLIMIT_FSIZE,
                    (self.max_file_size_bytes, self.original_limits.get("fsize", (resource.RLIM_INFINITY, resource.RLIM_INFINITY))[1])
                )
            except (ValueError, OSError) as e:
                logger.warning(f"Could not set file size limit: {e}")
        
        except ImportError:
            logger.warning("resource module not available, resource limits disabled")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit resource limit context and restore original limits."""
        try:
            import resource
            
            # Restore original limits
            for resource_type, (soft, hard) in self.original_limits.items():
                try:
                    resource.setrlimit(getattr(resource, f"RLIMIT_{resource_type.upper()}"), (soft, hard))
                except (ValueError, OSError, AttributeError):
                    pass
            
            # Check if we exceeded CPU time
            if exc_type is None and self.start_time:
                elapsed = time.time() - self.start_time
                if elapsed > self.max_cpu_time_sec:
                    raise ResourceLimitError(
                        f"CPU time limit exceeded: {elapsed:.2f}s > {self.max_cpu_time_sec}s",
                        resource_type="cpu_time",
                        limit=self.max_cpu_time_sec,
                        actual=elapsed,
                    )
        except ImportError:
            pass


# ============================================================================
# Error Obfuscation
# ============================================================================

def obfuscate_errors(result: Dict[str, Any], context: SecurityContext) -> Dict[str, Any]:
    """
    Obfuscate error details for user-facing responses.
    
    This function:
    1. Logs detailed error information internally
    2. Returns user-friendly error messages
    3. Removes sensitive information from responses
    4. Adds event ID for debugging
    
    Args:
        result: The result to potentially obfuscate
        context: Security context with event ID
        
    Returns:
        Obfuscated result safe for user consumption
    """
    # If result indicates failure, obfuscate the error
    if isinstance(result, dict) and result.get("status") == "failed":
        # Log detailed error internally
        if "error" in result:
            logger.error(
                f"Tool failed: {context.tool_name}, event_id={context.event_id}, error={result['error']}"
            )
        
        # Create user-friendly message
        user_message = get_user_friendly_error(result.get("error"))
        
        # Return obfuscated result
        return {
            "status": "failed",
            "message": user_message,
            "can_retry": result.get("can_retry", True),
            "security_event_id": context.event_id,
        }
    
    return result


def get_user_friendly_message(error: SecurityError) -> str:
    """Get a user-friendly message for a security error."""
    error_messages = {
        "input_validation": "Invalid input provided. Please check your parameters and try again.",
        "path_traversal": "Access to the requested path is denied.",
        "resource_limit": "The operation exceeded resource limits. Please try again with smaller inputs.",
        "internal_error": "An internal error occurred. Please try again.",
    }
    
    return error_messages.get(error.violation_type, "An error occurred. Please try again.")


def get_user_friendly_error(error: Any) -> str:
    """Convert a technical error to a user-friendly message."""
    if error is None:
        return "An error occurred. Please try again."
    
    error_str = str(error).lower()
    
    # Map technical errors to user-friendly messages
    if "permission" in error_str:
        return "Permission denied. Please check file permissions and try again."
    elif "not found" in error_str or "does not exist" in error_str:
        return "The requested resource was not found."
    elif "rate limit" in error_str or "too many requests" in error_str:
        return "Rate limit exceeded. Please wait and try again."
    elif "timeout" in error_str:
        return "The operation timed out. Please try again."
    elif "memory" in error_str:
        return "The operation requires too much memory. Please try with a smaller project."
    elif "disk" in error_str or "space" in error_str:
        return "Insufficient disk space. Please free up space and try again."
    else:
        return "An error occurred. Please try again."


# ============================================================================
# Security Event Logging
# ============================================================================

def log_security_event(
    event_type: str,
    tool_name: str,
    error: Exception = None,
    duration: float = None,
    context: SecurityContext = None,
) -> None:
    """
    Log a security event for monitoring and audit.
    
    Args:
        event_type: Type of event (security_violation, execution_success, etc.)
        tool_name: Name of the tool that was executed
        error: Optional exception that occurred
        duration: Optional execution duration
        context: Optional security context with additional details
    """
    event = {
        "event_id": context.event_id if context else str(uuid.uuid4())[:8],
        "event_type": event_type,
        "tool_name": tool_name,
        "timestamp": time.time(),
        "source": "security_wrapper",
    }
    
    if error:
        event["error"] = {
            "type": type(error).__name__,
            "message": str(error),
        }
    
    if duration is not None:
        event["duration_seconds"] = duration
    
    if context:
        event["validated_inputs"] = context.validated_inputs
        event["sanitized_paths"] = context.sanitized_paths
        event["warnings"] = context.warnings
    
    # Log to file
    logger.info(f"Security event: {event}")
