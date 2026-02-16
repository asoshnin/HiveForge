"""
Tests for comprehensive error handling in the Steering Assistant.

This module tests error handling for:
- File system errors (missing directories, permissions, disk full)
- Parsing errors (corrupted files, encoding issues)
- Code analysis errors (unrecognized languages, malformed files, timeouts)
- LLM API errors (rate limiting, timeouts, invalid responses)

Requirements: 3B.1-3B.7
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.hiveforge.steering.error_handling import (
    ErrorRecovery,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    SteeringError,
    FileSystemError,
    ParsingError,
    CodeAnalysisError,
    LLMAPIError,
    with_retry,
    safe_file_operation,
    collect_errors,
)


class TestFileSystemErrorHandling:
    """Test file system error handling."""
    
    def test_handle_missing_file_read(self):
        """Test handling of missing file during read operation."""
        error = FileNotFoundError("No such file")
        file_path = Path("/nonexistent/file.txt")
        
        context = ErrorRecovery.handle_file_system_error(error, file_path, "read")
        
        assert context.category == ErrorCategory.FILE_SYSTEM
        assert context.severity == ErrorSeverity.WARNING
        assert "File not found" in context.message
        assert context.file_path == file_path
        assert "Ensure the file exists" in context.suggestion
    
    def test_handle_missing_directory_create(self, tmp_path):
        """Test automatic creation of missing directories."""
        error = FileNotFoundError("No such directory")
        file_path = tmp_path / "new_dir" / "file.txt"
        
        context = ErrorRecovery.handle_file_system_error(error, file_path, "create")
        
        # Should create the directory
        assert context.category == ErrorCategory.FILE_SYSTEM
        assert context.severity == ErrorSeverity.INFO
        assert "Created missing directory" in context.message
    
    def test_handle_permission_denied(self):
        """Test handling of permission denied errors."""
        error = PermissionError("Permission denied")
        file_path = Path("/protected/file.txt")
        
        context = ErrorRecovery.handle_file_system_error(error, file_path, "write")
        
        assert context.category == ErrorCategory.FILE_SYSTEM
        assert context.severity == ErrorSeverity.CRITICAL
        assert "Permission denied" in context.message
        assert "chmod" in context.suggestion
    
    def test_handle_disk_full(self):
        """Test handling of disk full errors."""
        error = OSError(28, "No space left on device")
        error.errno = 28
        file_path = Path("/tmp/file.txt")
        
        context = ErrorRecovery.handle_file_system_error(error, file_path, "write")
        
        assert context.category == ErrorCategory.FILE_SYSTEM
        assert context.severity == ErrorSeverity.CRITICAL
        assert "Disk full" in context.message
        assert "Free up disk space" in context.suggestion


class TestParsingErrorHandling:
    """Test parsing error handling."""
    
    def test_handle_encoding_error(self):
        """Test handling of encoding errors."""
        error = UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
        file_path = Path("document.md")
        
        context = ErrorRecovery.handle_parsing_error(error, file_path, "markdown")
        
        assert context.category == ErrorCategory.PARSING
        assert context.severity == ErrorSeverity.WARNING
        assert "Encoding error" in context.message
        assert "UTF-8 encoding" in context.suggestion
    
    def test_handle_corrupted_file(self):
        """Test handling of corrupted files."""
        error = Exception("File is corrupted")
        file_path = Path("document.pdf")
        
        context = ErrorRecovery.handle_parsing_error(error, file_path, "pdf")
        
        assert context.category == ErrorCategory.PARSING
        assert context.severity == ErrorSeverity.WARNING
        assert "Corrupted" in context.message
        assert "not corrupted" in context.suggestion
    
    def test_handle_invalid_format(self):
        """Test handling of invalid file format."""
        error = Exception("Invalid PDF format")
        file_path = Path("document.pdf")
        
        context = ErrorRecovery.handle_parsing_error(error, file_path, "pdf")
        
        assert context.category == ErrorCategory.PARSING
        assert context.severity == ErrorSeverity.WARNING
        assert "Corrupted" in context.message or "Failed to parse" in context.message


class TestCodeAnalysisErrorHandling:
    """Test code analysis error handling."""
    
    def test_handle_unrecognized_language(self):
        """Test handling of unrecognized language."""
        error = Exception("Unknown language")
        
        context = ErrorRecovery.handle_code_analysis_error(
            error, "language detection", Path("file.xyz")
        )
        
        assert context.category == ErrorCategory.CODE_ANALYSIS
        assert context.severity == ErrorSeverity.INFO
        assert "Unrecognized language" in context.message
        assert "other detection methods" in context.suggestion
    
    def test_handle_missing_dependency_files(self):
        """Test handling of missing dependency files."""
        error = FileNotFoundError("No package.json found")
        
        context = ErrorRecovery.handle_code_analysis_error(
            error, "dependency extraction"
        )
        
        assert context.category == ErrorCategory.CODE_ANALYSIS
        assert context.severity == ErrorSeverity.WARNING
        assert "No dependency files found" in context.message
        assert "infer tech stack from import" in context.suggestion
    
    def test_handle_malformed_dependency_file(self):
        """Test handling of malformed dependency files."""
        error = Exception("JSON parse error")
        
        context = ErrorRecovery.handle_code_analysis_error(
            error, "package.json parsing", Path("package.json")
        )
        
        assert context.category == ErrorCategory.CODE_ANALYSIS
        assert context.severity == ErrorSeverity.WARNING
        assert "Malformed file" in context.message
        assert "Skipping this file" in context.suggestion
    
    def test_handle_ast_parsing_failure(self):
        """Test handling of AST parsing failures."""
        error = SyntaxError("Invalid syntax")
        
        context = ErrorRecovery.handle_code_analysis_error(
            error, "AST parsing", Path("file.py")
        )
        
        assert context.category == ErrorCategory.CODE_ANALYSIS
        assert context.severity == ErrorSeverity.WARNING
        assert "AST parsing failed" in context.message
        assert "regex-based analysis" in context.suggestion
    
    def test_handle_analysis_timeout(self):
        """Test handling of code analysis timeout."""
        error = TimeoutError("Analysis timed out")
        
        context = ErrorRecovery.handle_code_analysis_error(
            error, "code analysis timeout"
        )
        
        assert context.category == ErrorCategory.CODE_ANALYSIS
        assert context.severity == ErrorSeverity.WARNING
        assert "timeout" in context.message.lower()
        assert "sampling strategy" in context.suggestion
    
    def test_handle_gitignore_parsing_failure(self):
        """Test handling of .gitignore parsing failures."""
        error = Exception("Invalid pattern")
        
        context = ErrorRecovery.handle_code_analysis_error(
            error, ".gitignore parsing", Path(".gitignore")
        )
        
        assert context.category == ErrorCategory.CODE_ANALYSIS
        assert context.severity == ErrorSeverity.WARNING
        assert ".gitignore parsing failed" in context.message
        assert "without exclusions" in context.suggestion
    
    def test_handle_no_conventions_found(self):
        """Test handling when no conventions are found."""
        error = Exception("No conventions detected")
        
        context = ErrorRecovery.handle_code_analysis_error(
            error, "convention extraction"
        )
        
        assert context.category == ErrorCategory.CODE_ANALYSIS
        assert context.severity == ErrorSeverity.INFO
        assert "No clear coding conventions" in context.message
        assert "ask user" in context.suggestion
    
    def test_handle_no_architecture_pattern(self):
        """Test handling when no architecture pattern is recognized."""
        error = Exception("No pattern match")
        
        context = ErrorRecovery.handle_code_analysis_error(
            error, "architecture inference"
        )
        
        assert context.category == ErrorCategory.CODE_ANALYSIS
        assert context.severity == ErrorSeverity.INFO
        assert "No recognizable architecture" in context.message
        assert "custom" in context.suggestion


class TestLLMAPIErrorHandling:
    """Test LLM API error handling with retry logic."""
    
    def test_handle_rate_limiting_with_retry(self):
        """Test handling of rate limiting with exponential backoff."""
        error = Exception("Rate limit exceeded (429)")
        
        # First retry
        should_retry, context = ErrorRecovery.handle_llm_api_error(error, 0, max_retries=3)
        
        assert should_retry is True
        assert context.category == ErrorCategory.LLM_API
        assert context.severity == ErrorSeverity.WARNING
        assert "rate limit" in context.message.lower()
        assert "Waiting 1s" in context.suggestion
    
    def test_handle_rate_limiting_max_retries(self):
        """Test rate limiting after max retries."""
        error = Exception("Rate limit exceeded")
        
        # Max retries reached
        should_retry, context = ErrorRecovery.handle_llm_api_error(error, 3, max_retries=3)
        
        assert should_retry is False
        assert context.severity == ErrorSeverity.CRITICAL
        assert "max retries reached" in context.message.lower()
    
    def test_handle_timeout_with_retry(self):
        """Test handling of timeout errors."""
        error = Exception("Request timed out")
        
        should_retry, context = ErrorRecovery.handle_llm_api_error(error, 0, max_retries=3)
        
        assert should_retry is True
        assert context.category == ErrorCategory.LLM_API
        assert "timeout" in context.message.lower()
    
    def test_handle_invalid_response_with_retry(self):
        """Test handling of invalid API responses."""
        error = Exception("Invalid JSON response")
        
        should_retry, context = ErrorRecovery.handle_llm_api_error(error, 0, max_retries=3)
        
        assert should_retry is True
        assert context.category == ErrorCategory.LLM_API
        assert "Invalid" in context.message
    
    def test_handle_connection_error_with_backoff(self):
        """Test handling of connection errors with backoff."""
        error = Exception("Connection refused")
        
        # First retry - should wait 1 second
        should_retry, context = ErrorRecovery.handle_llm_api_error(error, 0, max_retries=3)
        assert should_retry is True
        assert "Waiting 1s" in context.suggestion
        
        # Second retry - should wait 2 seconds
        should_retry, context = ErrorRecovery.handle_llm_api_error(error, 1, max_retries=3)
        assert should_retry is True
        assert "Waiting 2s" in context.suggestion
        
        # Third retry - should wait 4 seconds
        should_retry, context = ErrorRecovery.handle_llm_api_error(error, 2, max_retries=3)
        assert should_retry is True
        assert "Waiting 4s" in context.suggestion
    
    def test_exponential_backoff_timing(self):
        """Test that exponential backoff actually waits."""
        error = Exception("Rate limit (429)")
        
        start_time = time.time()
        should_retry, context = ErrorRecovery.handle_llm_api_error(error, 0, max_retries=3)
        elapsed = time.time() - start_time
        
        # Should have waited approximately 1 second (2^0)
        assert elapsed >= 1.0
        assert elapsed < 1.5  # Allow some overhead


class TestRetryWrapper:
    """Test the retry wrapper function."""
    
    def test_successful_operation_no_retry(self):
        """Test that successful operations don't retry."""
        call_count = 0
        
        def operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = with_retry(operation, max_retries=3)
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure(self):
        """Test retry on transient failures."""
        call_count = 0
        
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return "success"
        
        def error_handler(error, retry_count, max_retries):
            return (retry_count < max_retries, ErrorContext(
                category=ErrorCategory.LLM_API,
                severity=ErrorSeverity.WARNING,
                message="Retrying"
            ))
        
        result = with_retry(operation, max_retries=3, error_handler=error_handler)
        
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test that max retries are respected."""
        call_count = 0
        
        def operation():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent error")
        
        def error_handler(error, retry_count, max_retries):
            return (retry_count < max_retries, ErrorContext(
                category=ErrorCategory.LLM_API,
                severity=ErrorSeverity.WARNING,
                message="Retrying"
            ))
        
        with pytest.raises(Exception, match="Persistent error"):
            with_retry(operation, max_retries=3, error_handler=error_handler)
        
        assert call_count == 4  # Initial + 3 retries


class TestSafeFileOperation:
    """Test safe file operation wrapper."""
    
    def test_successful_file_operation(self, tmp_path):
        """Test successful file operation."""
        file_path = tmp_path / "test.txt"
        
        def operation():
            file_path.write_text("test content")
            return "success"
        
        result = safe_file_operation(operation, file_path, "write")
        
        assert result == "success"
        assert file_path.read_text() == "test content"
    
    def test_file_operation_with_warning(self, tmp_path):
        """Test file operation that produces a warning."""
        file_path = tmp_path / "nonexistent.txt"
        
        def operation():
            # This will raise FileNotFoundError
            return file_path.read_text()
        
        result = safe_file_operation(
            operation,
            file_path,
            "read",
            default_return="default"
        )
        
        # Should return default value on warning-level error
        assert result == "default"
    
    def test_file_operation_with_critical_error(self, tmp_path):
        """Test file operation with critical error."""
        file_path = tmp_path / "test.txt"
        
        def operation():
            # Simulate permission error
            raise PermissionError("Permission denied")
        
        with pytest.raises(FileSystemError) as exc_info:
            safe_file_operation(operation, file_path, "write")
        
        assert exc_info.value.context.severity == ErrorSeverity.CRITICAL


class TestCollectErrors:
    """Test error collection for batch operations."""
    
    def test_all_operations_succeed(self):
        """Test when all operations succeed."""
        operations = [
            lambda: "result1",
            lambda: "result2",
            lambda: "result3",
        ]
        
        results, errors = collect_errors(operations)
        
        assert len(results) == 3
        assert len(errors) == 0
        assert results == ["result1", "result2", "result3"]
    
    def test_some_operations_fail(self):
        """Test when some operations fail."""
        def op1():
            return "success1"
        
        def op2():
            raise Exception("Error in op2")
        
        def op3():
            return "success3"
        
        operations = [op1, op2, op3]
        
        results, errors = collect_errors(operations)
        
        assert len(results) == 2
        assert len(errors) == 1
        assert results == ["success1", "success3"]
        assert "Operation failed" in errors[0].message
    
    def test_all_operations_fail(self):
        """Test when all operations fail."""
        operations = [
            lambda: (_ for _ in ()).throw(Exception("Error 1")),
            lambda: (_ for _ in ()).throw(Exception("Error 2")),
            lambda: (_ for _ in ()).throw(Exception("Error 3")),
        ]
        
        results, errors = collect_errors(operations)
        
        assert len(results) == 0
        assert len(errors) == 3


class TestErrorContext:
    """Test ErrorContext formatting."""
    
    def test_error_context_string_formatting(self):
        """Test that ErrorContext formats correctly."""
        context = ErrorContext(
            category=ErrorCategory.PARSING,
            severity=ErrorSeverity.WARNING,
            message="Test error message",
            details="Additional details",
            suggestion="Try this fix",
            file_path=Path("test.txt"),
            line_number=42
        )
        
        formatted = str(context)
        
        assert "[WARNING]" in formatted
        assert "Test error message" in formatted
        assert "test.txt:42" in formatted
        assert "Additional details" in formatted
        assert "Try this fix" in formatted
    
    def test_error_context_without_optional_fields(self):
        """Test ErrorContext with minimal fields."""
        context = ErrorContext(
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message="Critical error"
        )
        
        formatted = str(context)
        
        assert "[CRITICAL]" in formatted
        assert "Critical error" in formatted
        # Should not have location, details, or suggestion
        assert "Location:" not in formatted
        assert "Details:" not in formatted
        assert "Suggestion:" not in formatted


class TestGracefulDegradation:
    """Test graceful degradation strategies."""
    
    def test_parsing_continues_after_single_file_failure(self):
        """Test that parsing continues when one file fails."""
        # This is tested in the orchestrator, but we verify the error
        # handling supports this pattern
        
        errors = []
        
        def parse_file_1():
            return "content1"
        
        def parse_file_2():
            raise Exception("Corrupted file")
        
        def parse_file_3():
            return "content3"
        
        operations = [parse_file_1, parse_file_2, parse_file_3]
        results, errors = collect_errors(operations)
        
        # Should have 2 successful results and 1 error
        assert len(results) == 2
        assert len(errors) == 1
        assert "content1" in results
        assert "content3" in results
    
    def test_code_analysis_continues_after_component_failure(self):
        """Test that code analysis continues when one component fails."""
        # Simulate multiple analysis components
        def analyze_languages():
            return {"python": 0.8}
        
        def analyze_tech_stack():
            raise Exception("No dependency files")
        
        def analyze_architecture():
            return {"pattern": "layered"}
        
        operations = [analyze_languages, analyze_tech_stack, analyze_architecture]
        results, errors = collect_errors(operations)
        
        # Should have 2 successful results
        assert len(results) == 2
        assert len(errors) == 1
        assert {"python": 0.8} in results
        assert {"pattern": "layered"} in results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
