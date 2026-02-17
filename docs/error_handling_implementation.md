# Error Handling Implementation Summary

## Overview

Comprehensive error handling has been implemented for the Steering Assistant feature, covering all error categories specified in requirements 3B.1-3B.7.

## Implementation Details

### 1. Core Error Handling Module (`src/hiveforge/steering/error_handling.py`)

Created a centralized error handling module with:

#### Error Categories
- **File System Errors**: Missing directories, permissions, disk full
- **Parsing Errors**: Corrupted files, encoding issues
- **Code Analysis Errors**: Unrecognized languages, malformed files, timeouts
- **LLM API Errors**: Rate limiting, timeouts, invalid responses
- **Validation Errors**: Missing sections, contradictions
- **User Input Errors**: Invalid commands, missing prerequisites
- **Conflict Resolution Errors**: Unresolvable conflicts

#### Error Severity Levels
- **CRITICAL**: Blocks workflow, must be fixed
- **WARNING**: Degraded functionality, can continue
- **INFO**: Informational, no impact

#### Key Components

**ErrorContext Class**
- Structured error information with category, severity, message, details, suggestion
- Optional file path and line number tracking
- Human-readable string formatting

**ErrorRecovery Class**
- Static methods for handling each error category
- Implements graceful degradation strategies
- Provides actionable suggestions for remediation

**Utility Functions**
- `with_retry()`: Decorator/wrapper for retrying operations with error handling
- `safe_file_operation()`: Safely execute file operations with error handling
- `collect_errors()`: Execute multiple operations and collect both results and errors

### 2. File System Error Handling

**Missing Directories**
- Automatically creates missing directories during create operations
- Returns INFO-level error context with success message

**Permission Denied**
- Returns CRITICAL error with specific chmod command suggestions
- Distinguishes between read and write operations

**Disk Full**
- Detects errno 28 (No space left on device)
- Returns CRITICAL error with cleanup suggestions
- Prevents partial writes

### 3. Parsing Error Handling

**Encoding Issues**
- Enhanced markdown parser with multiple fallback encodings (UTF-8 → latin-1 → cp1252 → iso-8859-1)
- Enhanced PDF parser with strict=False fallback
- Logs each encoding attempt for debugging

**Corrupted Files**
- Detects corrupted PDFs and attempts fallback parsing
- Logs errors but continues processing other files
- Returns WARNING-level errors to allow workflow continuation

**Invalid Formats**
- Gracefully handles unsupported file types
- Creates ParsedDocument with error information
- Continues processing remaining files

### 4. Code Analysis Error Handling

**Unrecognized Languages**
- Returns INFO-level error
- Continues with other detection methods
- Logs warning for debugging

**Missing Dependency Files**
- Returns WARNING-level error
- Suggests inferring tech stack from import statements
- Continues analysis with available information

**Malformed Dependency Files**
- Detects JSON/YAML parsing errors
- Skips malformed file and continues with others
- Returns WARNING-level error

**AST Parsing Failures**
- Detects syntax errors in source files
- Suggests falling back to regex-based analysis
- Returns WARNING-level error

**Analysis Timeouts**
- Detects timeout conditions
- Suggests using sampling strategy for large codebases
- Returns WARNING-level error

**.gitignore Parsing Failures**
- Logs warning and proceeds without exclusions
- Returns WARNING-level error
- Doesn't block analysis

**No Conventions Found**
- Returns INFO-level error
- Suggests asking user during conversation
- Continues with other analysis

**No Architecture Pattern**
- Returns INFO-level error
- Reports "custom" as the pattern
- Extracts directory structure as-is

### 5. LLM API Error Handling

**Rate Limiting**
- Implements exponential backoff (2^retry_count seconds)
- Maximum 3 retries by default
- Returns WARNING for retries, CRITICAL when max retries reached

**Timeouts**
- Retries with increased timeout
- Maximum 3 retries
- Returns WARNING for retries, CRITICAL when exhausted

**Invalid Responses**
- Requests regeneration
- Maximum 3 retries
- Logs invalid response for debugging

**Connection Errors**
- Implements exponential backoff
- Retries network operations
- Returns appropriate error context

### 6. Enhanced Parsers

**Markdown Parser** (`src/hiveforge/steering/parsers/markdown.py`)
- Added logging for all error conditions
- Multiple fallback encodings (UTF-8, latin-1, cp1252, iso-8859-1)
- Uses ErrorRecovery for consistent error handling
- Logs each encoding attempt

**PDF Parser** (`src/hiveforge/steering/parsers/pdf.py`)
- Added logging for all error conditions
- Fallback parsing with strict=False
- Uses ErrorRecovery for consistent error handling
- Handles encrypted PDFs gracefully

### 7. Graceful Degradation Strategies

**Parsing Failures**
- Continue processing remaining files when one fails
- Collect all errors for reporting
- Return partial results with error information

**Code Analysis Failures**
- Continue with other analysis components when one fails
- Use fallback strategies (regex instead of AST)
- Return partial results with confidence scores

**LLM API Failures**
- Retry with exponential backoff
- Cache successful responses to avoid redundant calls
- Fail gracefully after max retries

**Validation Failures**
- Still write files but warn user
- Provide detailed error report
- Suggest fixes for each issue

## Testing

### Test Coverage

Created comprehensive test suite (`tests/test_error_handling.py`) with 34 tests covering:

1. **File System Error Handling** (4 tests)
   - Missing file read operations
   - Missing directory creation
   - Permission denied errors
   - Disk full errors

2. **Parsing Error Handling** (3 tests)
   - Encoding errors
   - Corrupted files
   - Invalid formats

3. **Code Analysis Error Handling** (8 tests)
   - Unrecognized languages
   - Missing dependency files
   - Malformed dependency files
   - AST parsing failures
   - Analysis timeouts
   - .gitignore parsing failures
   - No conventions found
   - No architecture pattern

4. **LLM API Error Handling** (6 tests)
   - Rate limiting with retry
   - Rate limiting max retries
   - Timeout with retry
   - Invalid response with retry
   - Connection error with backoff
   - Exponential backoff timing

5. **Retry Wrapper** (3 tests)
   - Successful operation (no retry)
   - Retry on failure
   - Max retries exceeded

6. **Safe File Operation** (3 tests)
   - Successful file operation
   - File operation with warning
   - File operation with critical error

7. **Error Collection** (3 tests)
   - All operations succeed
   - Some operations fail
   - All operations fail

8. **Error Context** (2 tests)
   - String formatting with all fields
   - String formatting with minimal fields

9. **Graceful Degradation** (2 tests)
   - Parsing continues after single file failure
   - Code analysis continues after component failure

### Test Results

All 34 tests pass successfully, validating:
- Correct error categorization
- Appropriate severity levels
- Actionable suggestions
- Retry logic with exponential backoff
- Graceful degradation
- Error collection for batch operations

## Requirements Coverage

### Requirement 3B.1: Source File Parsing Errors
✅ **Implemented**: Code analyzer logs errors, skips unparseable files, continues with remaining files

### Requirement 3B.2: Missing Dependency Files
✅ **Implemented**: Attempts to infer tech stack from import statements, logs warning

### Requirement 3B.3: No Recognizable Architecture
✅ **Implemented**: Reports "custom" as pattern, extracts directory structure as-is

### Requirement 3B.4: No Clear Conventions
✅ **Implemented**: Reports in gap analysis, asks user during conversation

### Requirement 3B.5: .gitignore Parsing Failure
✅ **Implemented**: Logs warning, proceeds without exclusions

### Requirement 3B.6: Code Analysis Interruption
✅ **Implemented**: Saves partial results, offers to resume or start fresh (via caching)

### Requirement 3B.7: Low Confidence Scores
✅ **Implemented**: Flags items with confidence < 0.3 as "uncertain", prioritizes asking user

## Usage Examples

### Example 1: Handling File System Errors

```python
from src.hiveforge.steering.error_handling import ErrorRecovery, safe_file_operation
from pathlib import Path

def write_file(file_path: Path, content: str):
    def operation():
        file_path.write_text(content)
        return True
    
    return safe_file_operation(
        operation,
        file_path,
        "write",
        default_return=False
    )
```

### Example 2: Handling LLM API Errors with Retry

```python
from src.hiveforge.steering.error_handling import with_retry, ErrorRecovery

def call_llm_api(prompt: str):
    def operation():
        # Make LLM API call
        return api.generate(prompt)
    
    return with_retry(
        operation,
        max_retries=3,
        error_handler=ErrorRecovery.handle_llm_api_error
    )
```

### Example 3: Collecting Errors from Batch Operations

```python
from src.hiveforge.steering.error_handling import collect_errors

def parse_all_files(file_paths):
    operations = [
        lambda fp=fp: parse_file(fp)
        for fp in file_paths
    ]
    
    results, errors = collect_errors(operations)
    
    # Process successful results
    for result in results:
        process(result)
    
    # Log errors
    for error in errors:
        logger.warning(str(error))
```

## Benefits

1. **Consistent Error Handling**: All components use the same error handling patterns
2. **Actionable Feedback**: Every error includes suggestions for remediation
3. **Graceful Degradation**: Failures in one component don't block the entire workflow
4. **Detailed Logging**: All errors are logged with context for debugging
5. **User-Friendly Messages**: Error messages are clear and actionable
6. **Retry Logic**: Transient failures are automatically retried with backoff
7. **Comprehensive Testing**: 34 tests ensure error handling works correctly

---

## Automatic Rollback (v2.1.0)

The v2.1.0 release introduced **Automatic Rollback** functionality that creates backups and restores previous state when workflows fail.

### Overview

When a workflow fails, the system automatically:
1. Creates a backup of the current state
2. Preserves any partially completed work
3. Provides the backup location in the result metadata
4. Allows easy recovery by restoring from backup

### Backup Creation

```python
from pathlib import Path
from datetime import datetime

def create_backup(
    project_root: Path,
    backup_dir: Path = None
) -> Path:
    """Create a timestamped backup of steering files."""
    if backup_dir is None:
        backup_dir = project_root / ".kiro" / "backups"
    
    # Create timestamped backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"backup_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)
    
    # Copy steering files to backup
    steering_dir = project_root / ".kiro" / "steering"
    if steering_dir.exists():
        import shutil
        shutil.copytree(steering_dir, backup_path / "steering")
    
    return backup_path
```

### Rollback Process

```
Workflow Failure Detected
            │
            ▼
    Create Backup
            │
            ▼
    ┌─────────────────┐
    │ Was this an     │
    │ Init workflow?  │
    └────────┬────────┘
             │
    ┌────────┴────────┐
    │                 │
   YES                NO
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│ Restore │    │ Preserve     │
│ .kiro/  │    │ modified     │
│ steering│    │ files only   │
└─────────┘    └──────────────┘
```

### WorkflowResult with Backup

```python
@dataclass
class WorkflowResult:
    success: bool                    # Whether the workflow succeeded
    files_created: List[Path]        # Files that were created
    files_modified: List[Path]       # Files that were modified
    errors: List[str]                # List of error messages
    warnings: List[str]              # List of warning messages
    metadata: Dict[str, Any]         # Additional metadata
    backup_location: Optional[Path]  # Path to backup (if created)
```

### Example: Rollback in Init Workflow

```python
from hiveforge.steering.shared.adapters import SharedInitWorkflow

def init_with_rollback(project_root: Path) -> WorkflowResult:
    """Initialize steering files with automatic rollback on failure."""
    workflow = SharedInitWorkflow(project_root=project_root)
    result = workflow.execute()
    
    if not result.success and result.backup_location:
        print(f"⚠️  Workflow failed. Backup created at:")
        print(f"   {result.backup_location}")
        print(f"\nTo restore from backup:")
        print(f"   cp -r {result.backup_location}/steering .kiro/")
    
    return result
```

### Rollback Verification

```python
def verify_rollback(backup_path: Path, project_root: Path) -> bool:
    """Verify that rollback restored the correct state."""
    backup_steering = backup_path / "steering"
    current_steering = project_root / ".kiro" / "steering"
    
    if not backup_steering.exists():
        return False
    
    # Compare file counts
    backup_files = list(backup_steering.glob("*.md"))
    current_files = list(current_steering.glob("*.md"))
    
    return len(backup_files) == len(current_files)
```

### Testing Rollback

```python
def test_rollback_on_failure():
    """Test that rollback creates backup on workflow failure."""
    with tempfile.TemporaryDirectory() as tmp_path:
        tmp_path = Path(tmp_path)
        
        # Create steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "test.md").write_text("# Test")
        
        # Mock workflow to fail
        with patch('hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = False
            mock_workflow.state.validation_report = None
            mock.return_value = mock_workflow
            
            workflow = SharedInitWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify backup was created
            assert result.backup_location is not None
            assert result.backup_location.exists()
            assert (result.backup_location / "steering" / "test.md").exists()
```

### Rollback Best Practices

1. **Always Check Backup Location**: After a failed workflow, check `result.backup_location`
2. **Verify Before Restoring**: Use `verify_rollback()` to ensure backup is valid
3. **Clean Up Old Backups**: Periodically remove old backups to save space
4. **Test Rollback**: Regularly test rollback functionality to ensure it works

### Rollback Configuration

```python
@dataclass
class RollbackConfig:
    enabled: bool = True              # Enable/disable rollback
    max_backups: int = 10             # Maximum number of backups to keep
    backup_dir: Path = None           # Custom backup directory
    include_cache: bool = False       # Include .kiro/.cache in backup
    include_git: bool = False         # Include .git directory in backup
```

---

## Future Enhancements

1. **Error Metrics**: Track error rates and types for monitoring
2. **Custom Error Handlers**: Allow users to register custom error handlers
3. **Error Recovery Strategies**: More sophisticated recovery strategies for specific errors
4. **Error Reporting**: Aggregate errors and generate summary reports
5. **Retry Configuration**: Make retry parameters configurable per operation type
6. **Incremental Rollback**: Rollback only changed files, preserve new additions
7. **Cloud Backup**: Optional cloud backup for critical workflows
