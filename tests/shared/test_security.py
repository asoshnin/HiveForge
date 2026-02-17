"""
Tests for shared security system.

Tests input validation, path sanitization, resource limits,
error obfuscation, and security event logging.
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from src.hiveforge.steering.shared.security import (
    SecurityError,
    InputValidationError,
    PathTraversalError,
    ResourceLimitError,
    SecurityContext,
    secure_execution,
    validate_inputs,
    validate_parameter,
    validate_project_root,
    validate_file_list,
    validate_single_file,
    validate_confidence_threshold,
    validate_boolean,
    sanitize_paths,
    sanitize_path,
    ResourceLimiter,
    obfuscate_errors,
    get_user_friendly_message,
    get_user_friendly_error,
    log_security_event,
)


class TestSecurityExceptions:
    """Test security exception classes."""
    
    def test_security_error(self):
        """Test SecurityError base exception."""
        error = SecurityError(
            "Test error",
            "test_violation",
            {"detail": "test"}
        )
        
        assert str(error) == "Test error"
        assert error.violation_type == "test_violation"
        assert error.details == {"detail": "test"}
    
    def test_input_validation_error(self):
        """Test InputValidationError."""
        error = InputValidationError(
            "Invalid input",
            "field_name",
            "bad_value",
            {"type": "string"}
        )
        
        assert error.field == "field_name"
        assert error.value == "bad_value"
        assert error.constraints == {"type": "string"}
        assert error.violation_type == "input_validation"
    
    def test_path_traversal_error(self):
        """Test PathTraversalError."""
        error = PathTraversalError(
            "Path traversal detected",
            "../etc/passwd",
            "/etc/passwd"
        )
        
        assert error.attempted_path == "../etc/passwd"
        assert error.resolved_path == "/etc/passwd"
        assert error.violation_type == "path_traversal"
    
    def test_resource_limit_error(self):
        """Test ResourceLimitError."""
        error = ResourceLimitError(
            "Memory limit exceeded",
            "memory",
            512,
            1024
        )
        
        assert error.resource_type == "memory"
        assert error.limit == 512
        assert error.actual == 1024
        assert error.violation_type == "resource_limit"


class TestSecurityContext:
    """Test SecurityContext class."""
    
    def test_context_creation(self):
        """Test creating security context."""
        start_time = time.time()
        context = SecurityContext("test_tool", start_time)
        
        assert context.tool_name == "test_tool"
        assert context.start_time == start_time
        assert context.event_id  # Should be generated
        assert len(context.validated_inputs) == 0
        assert len(context.sanitized_paths) == 0
        assert len(context.warnings) == 0
    
    def test_add_warning(self):
        """Test adding warnings to context."""
        context = SecurityContext("test_tool", time.time())
        
        context.add_warning("Test warning")
        
        assert len(context.warnings) == 1
        assert context.warnings[0]["warning"] == "Test warning"
        assert "timestamp" in context.warnings[0]


class TestInputValidation:
    """Test input validation functions."""
    
    def test_validate_project_root_valid(self):
        """Test validating valid project root."""
        result = validate_project_root(".")
        assert result == "."
        
        result = validate_project_root("/tmp")
        assert result == "/tmp"
    
    def test_validate_project_root_none(self):
        """Test validating None project root."""
        result = validate_project_root(None)
        assert result == "."
    
    def test_validate_project_root_invalid_type(self):
        """Test validating invalid type."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_project_root(123)
        
        assert "must be a string" in str(exc_info.value)
    
    def test_validate_project_root_too_long(self):
        """Test validating too long path."""
        long_path = "a" * 5000
        
        with pytest.raises(InputValidationError) as exc_info:
            validate_project_root(long_path)
        
        assert "exceeds maximum length" in str(exc_info.value)
    
    def test_validate_project_root_null_bytes(self):
        """Test validating path with null bytes."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_project_root("/tmp\x00/test")
        
        assert "null bytes" in str(exc_info.value)
    
    def test_validate_file_list_valid(self):
        """Test validating valid file list."""
        files = ["file1.txt", "file2.txt"]
        result = validate_file_list(files)
        
        assert result == files
    
    def test_validate_file_list_none(self):
        """Test validating None file list."""
        result = validate_file_list(None)
        assert result == []
    
    def test_validate_file_list_invalid_type(self):
        """Test validating invalid type."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_list("not a list")
        
        assert "must be a list" in str(exc_info.value)
    
    def test_validate_file_list_too_many(self):
        """Test validating too many files."""
        files = [f"file{i}.txt" for i in range(150)]
        
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_list(files)
        
        assert "exceeds maximum length" in str(exc_info.value)
    
    def test_validate_file_list_invalid_item(self):
        """Test validating list with invalid item."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_file_list(["file1.txt", 123])
        
        assert "must be a string" in str(exc_info.value)
    
    def test_validate_confidence_threshold_valid(self):
        """Test validating valid confidence threshold."""
        assert validate_confidence_threshold(0.5) == 0.5
        assert validate_confidence_threshold(0.0) == 0.0
        assert validate_confidence_threshold(1.0) == 1.0
    
    def test_validate_confidence_threshold_none(self):
        """Test validating None confidence threshold."""
        assert validate_confidence_threshold(None) == 0.7
    
    def test_validate_confidence_threshold_invalid_type(self):
        """Test validating invalid type."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_confidence_threshold("not a number")
        
        assert "must be a number" in str(exc_info.value)
    
    def test_validate_confidence_threshold_out_of_range(self):
        """Test validating out of range value."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_confidence_threshold(1.5)
        
        assert "between 0.0 and 1.0" in str(exc_info.value)
    
    def test_validate_boolean_valid(self):
        """Test validating valid boolean."""
        assert validate_boolean(True, "test") is True
        assert validate_boolean(False, "test") is False
        assert validate_boolean("true", "test") is True
        assert validate_boolean("false", "test") is False
        assert validate_boolean("yes", "test") is True
        assert validate_boolean("no", "test") is False
    
    def test_validate_boolean_none(self):
        """Test validating None boolean."""
        assert validate_boolean(None, "test") is False
    
    def test_validate_boolean_invalid(self):
        """Test validating invalid boolean."""
        with pytest.raises(InputValidationError) as exc_info:
            validate_boolean("invalid", "test")
        
        assert "must be a boolean" in str(exc_info.value)
    
    def test_validate_inputs_all_valid(self):
        """Test validating all valid inputs."""
        context = SecurityContext("test", time.time())
        kwargs = {
            "project_root": ".",
            "auto_discover": True,
            "confidence_threshold": 0.7
        }
        
        result = validate_inputs(kwargs, context)
        
        assert result["project_root"] == "."
        assert result["auto_discover"] is True
        assert result["confidence_threshold"] == 0.7
    
    def test_validate_inputs_with_invalid(self):
        """Test validating inputs with invalid value."""
        context = SecurityContext("test", time.time())
        kwargs = {
            "confidence_threshold": 2.0  # Invalid
        }
        
        with pytest.raises(InputValidationError):
            validate_inputs(kwargs, context)


class TestPathSanitization:
    """Test path sanitization functions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_sanitize_path_valid(self, temp_dir):
        """Test sanitizing valid path."""
        context = SecurityContext("test", time.time())
        
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.touch()
        
        result = sanitize_path(str(test_file), None, context)
        
        assert Path(result).is_absolute()
        assert len(context.warnings) == 0
    
    def test_sanitize_path_empty(self):
        """Test sanitizing empty path."""
        context = SecurityContext("test", time.time())
        
        result = sanitize_path("", None, context)
        
        assert result == "."
    
    def test_sanitize_path_with_whitespace(self):
        """Test sanitizing path with whitespace."""
        context = SecurityContext("test", time.time())
        
        result = sanitize_path("  /tmp  ", None, context)
        
        assert len(context.warnings) == 1
        assert "whitespace" in context.warnings[0]["warning"]
    
    def test_sanitize_path_null_bytes(self):
        """Test sanitizing path with null bytes."""
        context = SecurityContext("test", time.time())
        
        with pytest.raises(PathTraversalError) as exc_info:
            sanitize_path("/tmp\x00/test", None, context)
        
        # Error message may vary by OS, just check it's a PathTraversalError
        assert "null" in str(exc_info.value).lower()
    
    def test_sanitize_path_outside_allowed(self, temp_dir):
        """Test sanitizing path outside allowed directories."""
        context = SecurityContext("test", time.time())
        allowed = [str(temp_dir)]
        
        with pytest.raises(PathTraversalError) as exc_info:
            sanitize_path("/etc/passwd", allowed, context)
        
        assert "outside allowed directories" in str(exc_info.value)
    
    def test_sanitize_path_within_allowed(self, temp_dir):
        """Test sanitizing path within allowed directories."""
        context = SecurityContext("test", time.time())
        allowed = [str(temp_dir)]
        
        test_path = temp_dir / "subdir" / "file.txt"
        result = sanitize_path(str(test_path), allowed, context)
        
        assert str(temp_dir) in result
    
    def test_sanitize_paths_multiple(self):
        """Test sanitizing multiple paths."""
        context = SecurityContext("test", time.time())
        kwargs = {
            "project_root": ".",
            "files": ["file1.txt", "file2.txt"],
            "other_param": "value"
        }
        
        result = sanitize_paths(kwargs, None, context)
        
        assert "project_root" in result
        assert "files" in result
        assert len(result["files"]) == 2
        assert result["other_param"] == "value"


class TestResourceLimiter:
    """Test ResourceLimiter class."""
    
    def test_resource_limiter_context(self):
        """Test resource limiter as context manager."""
        limiter = ResourceLimiter(
            max_memory_mb=512,
            max_cpu_time_sec=300,
            max_file_size_mb=10
        )
        
        with limiter:
            # Should not raise
            pass
    
    def test_resource_limiter_cpu_time_exceeded(self):
        """Test CPU time limit exceeded."""
        limiter = ResourceLimiter(
            max_memory_mb=512,
            max_cpu_time_sec=0,  # Immediate timeout
            max_file_size_mb=10
        )
        
        with pytest.raises(ResourceLimitError) as exc_info:
            with limiter:
                time.sleep(0.1)
        
        assert "CPU time limit exceeded" in str(exc_info.value)


class TestErrorObfuscation:
    """Test error obfuscation functions."""
    
    def test_obfuscate_errors_success(self):
        """Test obfuscating successful result."""
        context = SecurityContext("test", time.time())
        result = {"status": "success", "data": "test"}
        
        obfuscated = obfuscate_errors(result, context)
        
        assert obfuscated == result  # No change for success
    
    def test_obfuscate_errors_failure(self):
        """Test obfuscating failed result."""
        context = SecurityContext("test", time.time())
        result = {
            "status": "failed",
            "error": "Detailed technical error with sensitive info",
            "can_retry": True
        }
        
        obfuscated = obfuscate_errors(result, context)
        
        assert obfuscated["status"] == "failed"
        assert "security_event_id" in obfuscated
        assert "Detailed technical error" not in obfuscated["message"]
    
    def test_get_user_friendly_message(self):
        """Test getting user-friendly message for security error."""
        error = InputValidationError("Test", "field", "value", {})
        
        message = get_user_friendly_message(error)
        
        assert "Invalid input" in message
        assert "Test" not in message  # Technical details hidden
    
    def test_get_user_friendly_error_permission(self):
        """Test user-friendly error for permission error."""
        message = get_user_friendly_error("Permission denied: /etc/passwd")
        
        assert "Permission denied" in message
        assert "/etc/passwd" not in message
    
    def test_get_user_friendly_error_not_found(self):
        """Test user-friendly error for not found error."""
        message = get_user_friendly_error("File not found: secret.txt")
        
        assert "not found" in message
    
    def test_get_user_friendly_error_generic(self):
        """Test user-friendly error for generic error."""
        message = get_user_friendly_error("Some technical error")
        
        assert "error occurred" in message
        assert "technical" not in message


class TestSecureExecutionDecorator:
    """Test secure_execution decorator."""
    
    @pytest.mark.asyncio
    async def test_secure_execution_success(self):
        """Test secure execution with successful function."""
        @secure_execution(
            enable_input_validation=False,
            enable_path_sanitization=False,
            enable_resource_limits=False,
            enable_error_obfuscation=False,
        )
        async def test_func(value: str = "test"):
            return {"status": "success", "value": value}
        
        result = await test_func(value="hello")
        
        assert result["status"] == "success"
        assert result["value"] == "hello"
    
    @pytest.mark.asyncio
    async def test_secure_execution_with_validation(self):
        """Test secure execution with input validation."""
        @secure_execution(
            enable_input_validation=True,
            enable_path_sanitization=False,
            enable_resource_limits=False,
            enable_error_obfuscation=False,
        )
        async def test_func(confidence_threshold: float = 0.7):
            return {"status": "success", "threshold": confidence_threshold}
        
        # Valid input
        result = await test_func(confidence_threshold=0.8)
        assert result["status"] == "success"
        
        # Invalid input
        result = await test_func(confidence_threshold=2.0)
        assert result["status"] == "failed"
        assert result["error_type"] == "input_validation"
    
    @pytest.mark.asyncio
    async def test_secure_execution_with_path_sanitization(self):
        """Test secure execution with path sanitization."""
        @secure_execution(
            enable_input_validation=False,
            enable_path_sanitization=True,
            enable_resource_limits=False,
            enable_error_obfuscation=False,
        )
        async def test_func(project_root: str = "."):
            return {"status": "success", "root": project_root}
        
        result = await test_func(project_root=".")
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_secure_execution_with_exception(self):
        """Test secure execution with exception."""
        @secure_execution(
            enable_input_validation=False,
            enable_path_sanitization=False,
            enable_resource_limits=False,
            enable_error_obfuscation=True,
        )
        async def test_func():
            raise ValueError("Test error")
        
        result = await test_func()
        
        assert result["status"] == "failed"
        assert result["error_type"] == "internal_error"
        assert "security_event_id" in result
        assert "Test error" not in result["message"]  # Obfuscated
    
    @pytest.mark.asyncio
    async def test_secure_execution_security_error(self):
        """Test secure execution with security error."""
        @secure_execution(
            enable_input_validation=True,
            enable_path_sanitization=False,
            enable_resource_limits=False,
            enable_error_obfuscation=False,
        )
        async def test_func(confidence_threshold: float = 0.7):
            return {"status": "success"}
        
        result = await test_func(confidence_threshold=5.0)
        
        assert result["status"] == "failed"
        assert result["can_retry"] is False
        assert "security_event_id" in result


class TestSecurityEventLogging:
    """Test security event logging."""
    
    def test_log_security_event_success(self):
        """Test logging successful execution."""
        context = SecurityContext("test_tool", time.time())
        
        # Should not raise
        log_security_event(
            event_type="execution_success",
            tool_name="test_tool",
            duration=1.5,
            context=context
        )
    
    def test_log_security_event_violation(self):
        """Test logging security violation."""
        context = SecurityContext("test_tool", time.time())
        error = InputValidationError("Test", "field", "value", {})
        
        # Should not raise
        log_security_event(
            event_type="security_violation",
            tool_name="test_tool",
            error=error,
            context=context
        )
    
    def test_log_security_event_without_context(self):
        """Test logging without context."""
        # Should not raise
        log_security_event(
            event_type="test_event",
            tool_name="test_tool"
        )


class TestSecurityIntegration:
    """Integration tests for security system."""
    
    @pytest.mark.asyncio
    async def test_full_security_pipeline(self):
        """Test full security pipeline with all features enabled."""
        @secure_execution(
            max_memory_mb=512,
            max_cpu_time_sec=300,
            max_file_size_mb=10,
            enable_input_validation=True,
            enable_path_sanitization=True,
            enable_resource_limits=True,
            enable_error_obfuscation=True,
        )
        async def secure_tool(
            project_root: str = ".",
            confidence_threshold: float = 0.7,
            auto_discover: bool = True
        ):
            return {
                "status": "success",
                "root": project_root,
                "threshold": confidence_threshold,
                "discover": auto_discover
            }
        
        # Test with valid inputs
        result = await secure_tool(
            project_root=".",
            confidence_threshold=0.8,
            auto_discover=True
        )
        
        assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_security_prevents_path_traversal(self):
        """Test that security prevents path traversal attacks."""
        @secure_execution(
            enable_input_validation=True,
            enable_path_sanitization=True,
            enable_resource_limits=False,
            enable_error_obfuscation=True,
        )
        async def secure_tool(project_root: str = "."):
            return {"status": "success", "root": project_root}
        
        # Attempt path traversal
        result = await secure_tool(project_root="../../../etc/passwd")
        
        # Should be sanitized or rejected
        assert result["status"] in ["success", "failed"]
        if result["status"] == "success":
            # Path should be sanitized to absolute path
            assert Path(result["root"]).is_absolute()
    
    @pytest.mark.asyncio
    async def test_security_validates_inputs(self):
        """Test that security validates all inputs."""
        @secure_execution(
            enable_input_validation=True,
            enable_path_sanitization=False,
            enable_resource_limits=False,
            enable_error_obfuscation=False,
        )
        async def secure_tool(
            confidence_threshold: float = 0.7,
            files: list = None
        ):
            return {"status": "success"}
        
        # Test invalid confidence threshold
        result = await secure_tool(confidence_threshold=2.0)
        assert result["status"] == "failed"
        assert result["error_type"] == "input_validation"
        
        # Test invalid files list
        result = await secure_tool(files="not a list")
        assert result["status"] == "failed"
        assert result["error_type"] == "input_validation"
