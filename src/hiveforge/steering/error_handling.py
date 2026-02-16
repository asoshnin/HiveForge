"""
Comprehensive error handling for the Steering Assistant.

This module provides centralized error handling, recovery strategies, and
graceful degradation for all components of the Steering Assistant.

Error Categories:
1. File System Errors (missing directories, permissions, disk full)
2. Parsing Errors (corrupted files, encoding issues)
3. Code Analysis Errors (unrecognized languages, malformed files, timeouts)
4. LLM API Errors (rate limiting, timeouts, invalid responses)
5. Validation Errors (missing sections, contradictions, malformed frontmatter)
6. User Input Errors (invalid commands, missing prerequisites)
7. Conflict Resolution Errors (unresolvable conflicts, circular dependencies)

Requirements: 3B.1-3B.7
"""

import logging
import time
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categories of errors that can occur."""
    FILE_SYSTEM = "file_system"
    PARSING = "parsing"
    CODE_ANALYSIS = "code_analysis"
    LLM_API = "llm_api"
    VALIDATION = "validation"
    USER_INPUT = "user_input"
    CONFLICT_RESOLUTION = "conflict_resolution"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    CRITICAL = "critical"  # Blocks workflow, must be fixed
    WARNING = "warning"    # Degraded functionality, can continue
    INFO = "info"          # Informational, no impact


@dataclass
class ErrorContext:
    """
    Context information for an error.
    
    Attributes:
        category: Error category
        severity: Error severity level
        message: Human-readable error message
        details: Additional error details
        suggestion: Suggested remediation
        file_path: Optional file path related to error
        line_number: Optional line number related to error
    """
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: str = ""
    suggestion: str = ""
    file_path: Optional[Path] = None
    line_number: Optional[int] = None
    
    def __str__(self) -> str:
        """Format error for display."""
        parts = [f"[{self.severity.value.upper()}] {self.message}"]
        
        if self.file_path:
            location = str(self.file_path)
            if self.line_number:
                location += f":{self.line_number}"
            parts.append(f"  Location: {location}")
        
        if self.details:
            parts.append(f"  Details: {self.details}")
        
        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")
        
        return "\n".join(parts)


class SteeringError(Exception):
    """Base exception for Steering Assistant errors."""
    
    def __init__(self, context: ErrorContext):
        """
        Initialize with error context.
        
        Args:
            context: ErrorContext with error information
        """
        self.context = context
        super().__init__(str(context))


class FileSystemError(SteeringError):
    """Exception for file system errors."""
    pass


class ParsingError(SteeringError):
    """Exception for parsing errors."""
    pass


class CodeAnalysisError(SteeringError):
    """Exception for code analysis errors."""
    pass


class LLMAPIError(SteeringError):
    """Exception for LLM API errors."""
    pass


class ValidationError(SteeringError):
    """Exception for validation errors."""
    pass


class ErrorRecovery:
    """
    Centralized error recovery strategies.
    
    This class provides methods for handling different types of errors
    with appropriate recovery strategies and graceful degradation.
    
    Requirements: 3B.1-3B.7
    """
    
    @staticmethod
    def handle_file_system_error(
        error: Exception,
        file_path: Path,
        operation: str
    ) -> ErrorContext:
        """
        Handle file system errors with appropriate recovery.
        
        Handles:
        - Missing directories: Create automatically
        - Permission denied: Display clear error with fix
        - Disk full: Fail gracefully with cleanup
        
        Args:
            error: The exception that occurred
            file_path: Path related to the error
            operation: Operation being performed (read, write, create)
            
        Returns:
            ErrorContext with error information and suggestions
        """
        if isinstance(error, FileNotFoundError):
            # Missing file or directory
            if operation == "read":
                return ErrorContext(
                    category=ErrorCategory.FILE_SYSTEM,
                    severity=ErrorSeverity.WARNING,
                    message=f"File not found: {file_path.name}",
                    details=str(error),
                    suggestion="Ensure the file exists and the path is correct",
                    file_path=file_path
                )
            elif operation == "create":
                # Try to create parent directories
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    return ErrorContext(
                        category=ErrorCategory.FILE_SYSTEM,
                        severity=ErrorSeverity.INFO,
                        message=f"Created missing directory: {file_path.parent}",
                        file_path=file_path
                    )
                except Exception as create_error:
                    return ErrorContext(
                        category=ErrorCategory.FILE_SYSTEM,
                        severity=ErrorSeverity.CRITICAL,
                        message=f"Cannot create directory: {file_path.parent}",
                        details=str(create_error),
                        suggestion="Check parent directory permissions",
                        file_path=file_path
                    )
        
        elif isinstance(error, PermissionError):
            # Permission denied
            return ErrorContext(
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"Permission denied: {file_path}",
                details=str(error),
                suggestion=f"Run: chmod u+rw {file_path}" if operation == "write" else f"Run: chmod u+r {file_path}",
                file_path=file_path
            )
        
        elif isinstance(error, OSError):
            # Check for disk full (errno 28)
            if hasattr(error, 'errno') and error.errno == 28:
                return ErrorContext(
                    category=ErrorCategory.FILE_SYSTEM,
                    severity=ErrorSeverity.CRITICAL,
                    message="Disk full: Cannot write file",
                    details=str(error),
                    suggestion="Free up disk space and try again",
                    file_path=file_path
                )
            else:
                return ErrorContext(
                    category=ErrorCategory.FILE_SYSTEM,
                    severity=ErrorSeverity.CRITICAL,
                    message=f"File system error: {file_path}",
                    details=str(error),
                    suggestion="Check file system and permissions",
                    file_path=file_path
                )
        
        else:
            # Unknown file system error
            return ErrorContext(
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"Unexpected file system error: {file_path}",
                details=str(error),
                suggestion="Check logs for details",
                file_path=file_path
            )
    
    @staticmethod
    def handle_parsing_error(
        error: Exception,
        file_path: Path,
        file_type: str
    ) -> ErrorContext:
        """
        Handle parsing errors with graceful degradation.
        
        Handles:
        - Corrupted files: Log error, skip file, continue
        - Invalid format: Log error, skip file, continue
        - Encoding issues: Attempt multiple encodings
        
        Args:
            error: The exception that occurred
            file_path: Path to the file being parsed
            file_type: Type of file (markdown, pdf, image)
            
        Returns:
            ErrorContext with error information
            
        Requirements: 3B.1
        """
        error_msg = str(error)
        
        # Check for encoding issues
        if "codec" in error_msg.lower() or "encoding" in error_msg.lower():
            return ErrorContext(
                category=ErrorCategory.PARSING,
                severity=ErrorSeverity.WARNING,
                message=f"Encoding error in {file_type} file: {file_path.name}",
                details=str(error),
                suggestion="Try saving the file with UTF-8 encoding",
                file_path=file_path
            )
        
        # Check for corrupted files
        elif "corrupt" in error_msg.lower() or "invalid" in error_msg.lower():
            return ErrorContext(
                category=ErrorCategory.PARSING,
                severity=ErrorSeverity.WARNING,
                message=f"Corrupted {file_type} file: {file_path.name}",
                details=str(error),
                suggestion="Verify the file is not corrupted and try again",
                file_path=file_path
            )
        
        # Generic parsing error
        else:
            return ErrorContext(
                category=ErrorCategory.PARSING,
                severity=ErrorSeverity.WARNING,
                message=f"Failed to parse {file_type} file: {file_path.name}",
                details=str(error),
                suggestion="Check file format and content",
                file_path=file_path
            )
    
    @staticmethod
    def handle_code_analysis_error(
        error: Exception,
        context: str,
        file_path: Optional[Path] = None
    ) -> ErrorContext:
        """
        Handle code analysis errors with fallback strategies.
        
        Handles:
        - Unrecognized language: Log warning, continue
        - Missing dependency files: Infer from imports
        - Malformed files: Skip file, continue
        - AST parsing failure: Fall back to regex
        - Timeout: Implement sampling strategy
        
        Args:
            error: The exception that occurred
            context: Context of the error (language detection, tech stack, etc.)
            file_path: Optional path to file being analyzed
            
        Returns:
            ErrorContext with error information
            
        Requirements: 3B.1, 3B.2, 3B.3, 3B.4, 3B.5, 3B.6
        """
        error_msg = str(error)
        
        # Unrecognized language
        if "language" in context.lower() and "unknown" in error_msg.lower():
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.INFO,
                message="Unrecognized language detected",
                details=str(error),
                suggestion="Analysis will continue with other detection methods",
                file_path=file_path
            )
        
        # AST parsing failure (check first for specific AST errors)
        if "ast" in error_msg.lower() or "ast" in context.lower():
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.WARNING,
                message="AST parsing failed",
                details=str(error),
                suggestion="Falling back to regex-based analysis",
                file_path=file_path
            )
        
        # Malformed dependency file (check before missing dependency)
        elif ("parse" in error_msg.lower() or "syntax" in error_msg.lower()) and ("package" in context.lower() or "dependency" in context.lower()):
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.WARNING,
                message=f"Malformed file in {context}",
                details=str(error),
                suggestion="Skipping this file and continuing with others",
                file_path=file_path
            )
        
        # Missing dependency files
        elif "dependency" in context.lower() or "package" in context.lower():
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.WARNING,
                message="No dependency files found",
                details=str(error),
                suggestion="Will attempt to infer tech stack from import statements",
                file_path=file_path
            )
        
        # Timeout
        elif "timeout" in error_msg.lower() or "time" in context.lower():
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.WARNING,
                message="Code analysis timeout",
                details=str(error),
                suggestion="Using sampling strategy for large codebase",
                file_path=file_path
            )
        
        # .gitignore parsing failure
        elif "gitignore" in context.lower():
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.WARNING,
                message=".gitignore parsing failed",
                details=str(error),
                suggestion="Proceeding without exclusions",
                file_path=file_path
            )
        
        # No clear conventions found
        elif "convention" in context.lower():
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.INFO,
                message="No clear coding conventions found",
                details=str(error),
                suggestion="Will ask user during conversation",
                file_path=file_path
            )
        
        # No recognizable architecture
        elif "architecture" in context.lower():
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.INFO,
                message="No recognizable architecture pattern found",
                details=str(error),
                suggestion="Reporting as 'custom' architecture",
                file_path=file_path
            )
        
        # Generic code analysis error
        else:
            return ErrorContext(
                category=ErrorCategory.CODE_ANALYSIS,
                severity=ErrorSeverity.WARNING,
                message=f"Code analysis error in {context}",
                details=str(error),
                suggestion="Continuing with partial results",
                file_path=file_path
            )
    
    @staticmethod
    def handle_llm_api_error(
        error: Exception,
        retry_count: int,
        max_retries: int = 3
    ) -> tuple[bool, ErrorContext]:
        """
        Handle LLM API errors with exponential backoff.
        
        Handles:
        - Rate limiting: Exponential backoff with max retries
        - Timeout: Retry with increased timeout
        - Invalid response: Request regeneration
        
        Args:
            error: The exception that occurred
            retry_count: Current retry attempt number
            max_retries: Maximum number of retries (default: 3)
            
        Returns:
            Tuple of (should_retry, ErrorContext)
            
        Requirements: 3B.7
        """
        error_msg = str(error).lower()
        
        # Rate limiting
        if "rate" in error_msg or "429" in error_msg or "quota" in error_msg:
            if retry_count < max_retries:
                # Calculate backoff time: 2^retry_count seconds
                backoff_time = 2 ** retry_count
                
                context = ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.WARNING,
                    message=f"LLM API rate limit hit (retry {retry_count + 1}/{max_retries})",
                    details=str(error),
                    suggestion=f"Waiting {backoff_time}s before retry"
                )
                
                logger.warning(f"Rate limited, waiting {backoff_time}s before retry")
                time.sleep(backoff_time)
                
                return True, context
            else:
                return False, ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.CRITICAL,
                    message="LLM API rate limit exceeded (max retries reached)",
                    details=str(error),
                    suggestion="Wait a few minutes and try again"
                )
        
        # Timeout
        elif "timeout" in error_msg or "timed out" in error_msg:
            if retry_count < max_retries:
                context = ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.WARNING,
                    message=f"LLM API timeout (retry {retry_count + 1}/{max_retries})",
                    details=str(error),
                    suggestion="Retrying with increased timeout"
                )
                
                return True, context
            else:
                return False, ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.CRITICAL,
                    message="LLM API timeout (max retries reached)",
                    details=str(error),
                    suggestion="Check network connection and try again"
                )
        
        # Invalid response
        elif "invalid" in error_msg or "malformed" in error_msg or "json" in error_msg:
            if retry_count < max_retries:
                context = ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.WARNING,
                    message=f"Invalid LLM API response (retry {retry_count + 1}/{max_retries})",
                    details=str(error),
                    suggestion="Requesting regeneration"
                )
                
                return True, context
            else:
                return False, ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.CRITICAL,
                    message="Invalid LLM API response (max retries reached)",
                    details=str(error),
                    suggestion="Check API configuration and try again"
                )
        
        # Connection error
        elif "connection" in error_msg or "network" in error_msg:
            if retry_count < max_retries:
                backoff_time = 2 ** retry_count
                
                context = ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.WARNING,
                    message=f"LLM API connection error (retry {retry_count + 1}/{max_retries})",
                    details=str(error),
                    suggestion=f"Waiting {backoff_time}s before retry"
                )
                
                time.sleep(backoff_time)
                return True, context
            else:
                return False, ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.CRITICAL,
                    message="LLM API connection error (max retries reached)",
                    details=str(error),
                    suggestion="Check network connection and API endpoint"
                )
        
        # Generic API error
        else:
            if retry_count < max_retries:
                context = ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.WARNING,
                    message=f"LLM API error (retry {retry_count + 1}/{max_retries})",
                    details=str(error),
                    suggestion="Retrying request"
                )
                
                return True, context
            else:
                return False, ErrorContext(
                    category=ErrorCategory.LLM_API,
                    severity=ErrorSeverity.CRITICAL,
                    message="LLM API error (max retries reached)",
                    details=str(error),
                    suggestion="Check API configuration and logs"
                )


def with_retry(
    func: Callable,
    max_retries: int = 3,
    error_handler: Optional[Callable] = None
) -> Any:
    """
    Decorator/wrapper for retrying operations with error handling.
    
    Args:
        func: Function to execute with retry logic
        max_retries: Maximum number of retry attempts
        error_handler: Optional custom error handler
        
    Returns:
        Result of the function call
        
    Raises:
        Last exception if all retries fail
    """
    retry_count = 0
    last_error = None
    
    while retry_count <= max_retries:
        try:
            return func()
        except Exception as e:
            last_error = e
            
            if error_handler:
                should_retry, context = error_handler(e, retry_count, max_retries)
                logger.warning(str(context))
                
                if not should_retry:
                    raise
            
            retry_count += 1
            
            if retry_count > max_retries:
                raise
    
    # Should never reach here, but just in case
    if last_error:
        raise last_error


def safe_file_operation(
    operation: Callable,
    file_path: Path,
    operation_type: str,
    default_return: Any = None
) -> Any:
    """
    Safely execute a file operation with error handling.
    
    Args:
        operation: File operation to execute
        file_path: Path to the file
        operation_type: Type of operation (read, write, create)
        default_return: Default value to return on error
        
    Returns:
        Result of operation or default_return on error
    """
    try:
        return operation()
    except Exception as e:
        context = ErrorRecovery.handle_file_system_error(e, file_path, operation_type)
        logger.error(str(context))
        
        if context.severity == ErrorSeverity.CRITICAL:
            raise FileSystemError(context)
        
        return default_return


def collect_errors(operations: List[Callable]) -> tuple[List[Any], List[ErrorContext]]:
    """
    Execute multiple operations and collect both results and errors.
    
    Useful for batch operations where some failures are acceptable.
    
    Args:
        operations: List of operations to execute
        
    Returns:
        Tuple of (results, errors) where results contains successful
        operation results and errors contains ErrorContext for failures
    """
    results = []
    errors = []
    
    for operation in operations:
        try:
            result = operation()
            results.append(result)
        except SteeringError as e:
            errors.append(e.context)
            logger.warning(str(e.context))
        except Exception as e:
            context = ErrorContext(
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.WARNING,
                message="Operation failed",
                details=str(e)
            )
            errors.append(context)
            logger.warning(str(context))
    
    return results, errors
