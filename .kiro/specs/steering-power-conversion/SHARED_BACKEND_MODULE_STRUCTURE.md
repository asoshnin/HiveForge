# Shared Backend Module Structure Design

**Feature**: steering-power-conversion  
**Version**: 2.0.0  
**Status**: Complete  
**Phase**: 1.4 - Shared Backend Interface Design

---

## 1. Overview

This document defines the Python module structure for the shared backend that will be used by both CLI and Power interfaces. The design ensures:

- Clear separation between business logic and presentation
- Maximum code reuse (>95% target)
- Easy testing and maintenance
- Backward compatibility with existing v02 code

---

## 2. Directory Structure

```
src/hiveforge/steering/
│
├── shared/                              # NEW: Shared backend modules
│   ├── __init__.py                      # Exports: all shared classes/functions
│   │
│   ├── workflows/                       # Shared workflow implementations
│   │   ├── __init__.py                  # Exports: SharedInitWorkflow, etc.
│   │   ├── base.py                      # SharedWorkflowBase class
│   │   ├── init.py                      # SharedInitWorkflow class
│   │   ├── update.py                    # SharedUpdateWorkflow class
│   │   └── validate.py                  # SharedValidateWorkflow class
│   │
│   ├── security/                        # Security controls
│   │   ├── __init__.py                  # Exports: all security functions/classes
│   │   ├── wrappers.py                  # secure_tool_execution decorator
│   │   ├── validators.py                # Input validation functions
│   │   ├── sanitizers.py                # Path sanitization functions
│   │   ├── limiters.py                  # ResourceLimiter class
│   │   └── exceptions.py                # Security exception classes
│   │
│   ├── telemetry/                       # Usage tracking
│   │   ├── __init__.py                  # Exports: Telemetry class
│   │   ├── telemetry.py                 # Telemetry class implementation
│   │   ├── storage.py                   # Telemetry storage backend
│   │   └── models.py                    # Telemetry data models
│   │
│   ├── error_handling/                  # Enhanced error handling
│   │   ├── __init__.py                  # Exports: ToolExecutor, etc.
│   │   ├── executor.py                  # ToolExecutor with rollback
│   │   ├── context.py                   # ErrorContext class
│   │   ├── rollback.py                  # Rollback mechanisms
│   │   └── exceptions.py                # Error exception classes
│   │
│   └── adapters/                        # Interface adapters
│       ├── __init__.py                  # Exports: CLIAdapter, PowerAdapter
│       ├── base.py                      # BaseAdapter class
│       ├── cli.py                       # CLIAdapter class
│       └── power.py                     # PowerAdapter class
│
├── workflows/                           # EXISTING: CLI-specific workflows
│   ├── __init__.py                      # REFACTOR: Use shared workflows
│   ├── init_workflow.py                 # REFACTOR: Thin wrapper over shared
│   ├── update_workflow.py               # REFACTOR: Thin wrapper over shared
│   ├── validate_workflow.py             # REFACTOR: Thin wrapper over shared
│   └── autonomous_workflow.py           # EXISTING: Keep as-is
│
├── analyzers/                           # EXISTING: Reusable as-is
│   ├── __init__.py
│   ├── code_analyzer.py
│   ├── language_detector.py
│   ├── tech_stack_extractor.py
│   ├── architecture_inferrer.py
│   ├── conventions_extractor.py
│   └── documentation_parser.py
│
├── parsers/                             # EXISTING: Reusable as-is
│   ├── __init__.py
│   └── orchestrator.py
│
├── validators/                          # EXISTING: Reusable as-is
│   ├── __init__.py
│   ├── steering_validator.py
│   └── rule_based.py
│
├── agents/                              # EXISTING: Reusable as-is
│   ├── __init__.py
│   └── steering_assistant.py
│
├── models.py                            # EXISTING: Reusable as-is
├── templates.py                         # EXISTING: Reusable as-is
├── utils.py                             # EXISTING: Reusable as-is
├── knowledge_base.py                    # EXISTING: Reusable as-is
├── gap_analysis.py                      # EXISTING: Reusable as-is
├── template_populator.py                # EXISTING: Reusable as-is
├── conflict_resolver.py                 # EXISTING: Reusable as-is
├── customization_detector.py            # EXISTING: Reusable as-is
├── diff_generator.py                    # EXISTING: Reusable as-is
├── backup_manager.py                    # EXISTING: Reusable as-is
├── error_handling.py                    # DEPRECATED: Use shared/error_handling/
└── cli.py                               # REFACTOR: Use shared workflows
```

---

## 3. Module Specifications

### 3.1 shared/__init__.py

**Purpose**: Main entry point for shared backend, exports all public APIs

```python
"""
Shared backend for HiveForge Steering Assistant.

This module provides the shared backend implementation used by both
CLI and Power interfaces. It ensures >95% code sharing and consistent
behavior across interfaces.

Public API:
    Workflows:
        - SharedInitWorkflow
        - SharedUpdateWorkflow
        - SharedValidateWorkflow
    
    Security:
        - secure_tool_execution (decorator)
        - validate_parameters
        - sanitize_path
        - ResourceLimiter
    
    Telemetry:
        - Telemetry
    
    Error Handling:
        - ToolExecutor
        - ErrorContext
        - rollback_on_error (decorator)
    
    Adapters:
        - CLIAdapter
        - PowerAdapter
"""

# Workflows
from .workflows import (
    SharedWorkflowBase,
    SharedInitWorkflow,
    SharedUpdateWorkflow,
    SharedValidateWorkflow,
)

# Security
from .security import (
    secure_tool_execution,
    validate_parameters,
    sanitize_path,
    ResourceLimiter,
    SecurityError,
    InputValidationError,
    PathTraversalError,
    ResourceLimitError,
)

# Telemetry
from .telemetry import Telemetry

# Error Handling
from .error_handling import (
    ToolExecutor,
    ErrorContext,
    ErrorSeverity,
    rollback_on_error,
)

# Adapters
from .adapters import (
    BaseAdapter,
    CLIAdapter,
    PowerAdapter,
)

__all__ = [
    # Workflows
    "SharedWorkflowBase",
    "SharedInitWorkflow",
    "SharedUpdateWorkflow",
    "SharedValidateWorkflow",
    # Security
    "secure_tool_execution",
    "validate_parameters",
    "sanitize_path",
    "ResourceLimiter",
    "SecurityError",
    "InputValidationError",
    "PathTraversalError",
    "ResourceLimitError",
    # Telemetry
    "Telemetry",
    # Error Handling
    "ToolExecutor",
    "ErrorContext",
    "ErrorSeverity",
    "rollback_on_error",
    # Adapters
    "BaseAdapter",
    "CLIAdapter",
    "PowerAdapter",
]

__version__ = "2.0.0"
```

### 3.2 shared/workflows/base.py

**Purpose**: Base class for all shared workflows with common functionality

```python
"""
Base class for shared workflows.

Provides common functionality for all workflow implementations:
- Progress reporting via callbacks
- Error handling
- State management
- Result formatting
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable, Dict, Any
import logging

from ...models import SteeringConfig, WorkflowState

logger = logging.getLogger(__name__)


class SharedWorkflowBase(ABC):
    """
    Base class for shared workflows.
    
    All shared workflows inherit from this class and implement the
    execute() method. The base class provides:
    - Progress reporting via callbacks
    - Consistent error handling
    - State management
    - Result formatting
    
    Attributes:
        config: SteeringConfig with workflow settings
        project_root: Root directory of the project
        progress_callback: Optional callback for progress updates
        state: WorkflowState tracking workflow progress
    """
    
    def __init__(
        self,
        config: SteeringConfig,
        project_root: Path,
        progress_callback: Optional[Callable[[str, str, Optional[int]], None]] = None
    ):
        """
        Initialize shared workflow.
        
        Args:
            config: SteeringConfig with workflow settings
            project_root: Root directory of the project
            progress_callback: Optional callback(step, message, percentage)
        """
        self.config = config
        self.project_root = project_root
        self.progress_callback = progress_callback or self._default_progress
        self.state = WorkflowState(
            workflow_type=self._get_workflow_type(),
            staging_dir=project_root / ".kiro" / "onboarding",
            steering_dir=project_root / ".kiro" / "steering",
        )
        
        logger.info(f"Initialized {self.__class__.__name__} for project: {project_root}")
    
    @abstractmethod
    def _get_workflow_type(self) -> str:
        """Return workflow type identifier."""
        pass
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Returns:
            Dictionary with workflow results:
            {
                "status": "success" | "failed" | "aborted",
                "message": str,
                "data": dict,  # Workflow-specific data
                "errors": list,
                "warnings": list
            }
        """
        pass
    
    def _default_progress(self, step: str, message: str, percentage: Optional[int]) -> None:
        """Default progress callback (no-op)."""
        pass
    
    def _report_progress(
        self,
        step: str,
        message: str,
        percentage: Optional[int] = None
    ) -> None:
        """
        Report progress via callback.
        
        Args:
            step: Step identifier (e.g., "init", "parse", "validate")
            message: Human-readable progress message
            percentage: Optional completion percentage (0-100)
        """
        try:
            self.progress_callback(step, message, percentage)
        except Exception as e:
            logger.warning(f"Progress callback failed: {e}")
    
    def _format_success_result(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format a success result.
        
        Args:
            message: Success message
            data: Optional workflow-specific data
            
        Returns:
            Formatted result dictionary
        """
        return {
            "status": "success",
            "message": message,
            "data": data or {},
            "errors": [],
            "warnings": getattr(self.state, 'warnings', [])
        }
    
    def _format_error_result(
        self,
        error: Exception,
        partial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format an error result.
        
        Args:
            error: Exception that occurred
            partial_data: Optional partial results before error
            
        Returns:
            Formatted error result dictionary
        """
        return {
            "status": "failed",
            "message": str(error),
            "error_type": type(error).__name__,
            "data": partial_data or {},
            "errors": [str(error)],
            "warnings": getattr(self.state, 'warnings', [])
        }
    
    def _format_aborted_result(
        self,
        reason: str
    ) -> Dict[str, Any]:
        """
        Format an aborted result.
        
        Args:
            reason: Reason for abortion
            
        Returns:
            Formatted aborted result dictionary
        """
        return {
            "status": "aborted",
            "message": f"Workflow aborted: {reason}",
            "reason": reason,
            "data": {},
            "errors": [],
            "warnings": []
        }
```

### 3.3 shared/workflows/init.py

**Purpose**: Shared init workflow implementation

```python
"""
Shared init workflow implementation.

Provides interface-agnostic init workflow that can be used by both
CLI and Power interfaces. Contains all business logic with no
presentation code.
"""

from pathlib import Path
from typing import Dict, Any

from .base import SharedWorkflowBase
from ...models import SteeringConfig


class SharedInitWorkflow(SharedWorkflowBase):
    """
    Shared init workflow for creating steering files from scratch.
    
    This workflow is used by both CLI and Power interfaces. It contains
    all business logic and returns structured results that can be
    formatted by the interface layer.
    
    Workflow steps:
    1. Create staging directory
    2. Check for existing files
    3. Optionally analyze code
    4. Parse artifacts
    5. Build knowledge base
    6. Run gap analysis
    7. Conduct conversation
    8. Populate templates
    9. Write files
    10. Run validation
    """
    
    def _get_workflow_type(self) -> str:
        return "init"
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute the init workflow.
        
        Returns:
            {
                "status": "success" | "failed" | "aborted",
                "message": str,
                "data": {
                    "files_created": int,
                    "validation_report": dict,
                    "code_analysis": dict,
                    "confidence_scores": dict
                },
                "errors": list,
                "warnings": list
            }
        """
        try:
            self._report_progress("init", "Starting init workflow", 0)
            
            # Step 1: Create staging directory
            self._create_staging_directory()
            self._report_progress("staging", "Staging directory ready", 10)
            
            # Step 2: Check existing files
            if not self._check_existing_files():
                return self._format_aborted_result("user_cancelled")
            self._report_progress("check", "Existing files checked", 15)
            
            # Step 3: Optionally analyze code
            if self.config.analyze_code:
                self._analyze_code()
                self._report_progress("analyze", "Code analysis complete", 30)
            
            # Step 4: Parse artifacts
            self._parse_artifacts()
            self._report_progress("parse", "Artifacts parsed", 40)
            
            # Step 5: Build knowledge base
            self._build_knowledge_base()
            self._report_progress("knowledge", "Knowledge base built", 50)
            
            # Step 6: Run gap analysis
            self._run_gap_analysis()
            self._report_progress("gaps", "Gap analysis complete", 60)
            
            # Step 7: Conduct conversation
            self._conduct_conversation()
            self._report_progress("conversation", "Information gathered", 70)
            
            # Step 8: Populate templates
            self._populate_templates()
            self._report_progress("populate", "Templates populated", 80)
            
            # Step 9: Write files
            self._write_files()
            self._report_progress("write", "Files written", 90)
            
            # Step 10: Run validation
            if not self.config.skip_validation:
                self._run_validation()
                self._report_progress("validate", "Validation complete", 95)
            
            self._report_progress("complete", "Init workflow complete", 100)
            
            return self._format_success_result(
                message=f"Created {len(self.state.populated_files)} steering files",
                data={
                    "files_created": len(self.state.populated_files),
                    "validation_report": self._format_validation_report(),
                    "code_analysis": self._format_code_analysis(),
                    "confidence_scores": self._get_confidence_scores()
                }
            )
        
        except Exception as e:
            logger.error(f"Init workflow failed: {e}", exc_info=True)
            return self._format_error_result(
                error=e,
                partial_data=self._get_partial_results()
            )
    
    # Private methods for each step (business logic only)
    # Implementation details omitted for brevity
    # See SHARED_BACKEND_ANALYSIS.md for full details
```

### 3.4 shared/security/__init__.py

**Purpose**: Security module exports

```python
"""
Security controls for shared backend.

Provides input validation, path sanitization, resource limits,
and error obfuscation for both CLI and Power interfaces.
"""

from .wrappers import secure_tool_execution
from .validators import validate_parameters
from .sanitizers import sanitize_path
from .limiters import ResourceLimiter
from .exceptions import (
    SecurityError,
    InputValidationError,
    PathTraversalError,
    ResourceLimitError,
)

__all__ = [
    "secure_tool_execution",
    "validate_parameters",
    "sanitize_path",
    "ResourceLimiter",
    "SecurityError",
    "InputValidationError",
    "PathTraversalError",
    "ResourceLimitError",
]
```

### 3.5 shared/telemetry/telemetry.py

**Purpose**: Telemetry tracking for both interfaces

```python
"""
Telemetry tracking for shared backend.

Tracks usage metrics for both CLI and Power interfaces,
storing data in a shared location for unified analytics.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class Telemetry:
    """
    Telemetry tracker for both CLI and Power interfaces.
    
    Records usage events with interface type, enabling analytics
    to compare CLI vs Power usage patterns.
    
    Attributes:
        storage_dir: Path to telemetry storage (.kiro/.telemetry/)
        interface: Interface type ("cli" or "power")
    """
    
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        interface: str = "cli"
    ):
        """
        Initialize telemetry tracker.
        
        Args:
            storage_dir: Optional custom storage directory
            interface: Interface type ("cli" or "power")
        """
        self.storage_dir = storage_dir or Path.cwd() / ".kiro" / ".telemetry"
        self.interface = interface
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._events_file = self.storage_dir / "events.jsonl"
    
    def record_cli_command(
        self,
        command: str,
        parameters: Dict[str, Any]
    ) -> None:
        """
        Record a CLI command execution.
        
        Args:
            command: Command name (e.g., "init", "update")
            parameters: Command parameters
        """
        self._record_event({
            "interface": "cli",
            "command": command,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": None,  # Set by caller if available
            "success": None  # Set by caller if available
        })
    
    def record_power_invocation(
        self,
        tool: str,
        parameters: Dict[str, Any]
    ) -> None:
        """
        Record a Power tool invocation.
        
        Args:
            tool: Tool name (e.g., "init_steering")
            parameters: Tool parameters
        """
        self._record_event({
            "interface": "power",
            "tool": tool,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": None,
            "success": None
        })
    
    def get_last_entry(self) -> Optional[Dict[str, Any]]:
        """
        Get the last telemetry entry.
        
        Returns:
            Last entry dict or None if no entries
        """
        if not self._events_file.exists():
            return None
        
        with open(self._events_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return None
            return json.loads(lines[-1])
    
    def _record_event(self, event: Dict[str, Any]) -> None:
        """Record an event to storage."""
        with open(self._events_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
```

### 3.6 shared/adapters/base.py

**Purpose**: Base adapter class for interface implementations

```python
"""
Base adapter for interface implementations.

Provides common functionality for CLI and Power adapters,
including progress formatting and result transformation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable


class BaseAdapter(ABC):
    """
    Base adapter for interface implementations.
    
    Adapters bridge the gap between shared workflows and
    interface-specific presentation. They handle:
    - Progress callback creation
    - Result formatting
    - Error presentation
    """
    
    @abstractmethod
    def create_progress_callback(self) -> Callable[[str, str, int], None]:
        """
        Create a progress callback for this interface.
        
        Returns:
            Callback function(step, message, percentage)
        """
        pass
    
    @abstractmethod
    def format_result(self, result: Dict[str, Any]) -> Any:
        """
        Format workflow result for this interface.
        
        Args:
            result: Structured result from shared workflow
            
        Returns:
            Interface-specific formatted result
        """
        pass
    
    @abstractmethod
    def format_error(self, error: Exception) -> Any:
        """
        Format error for this interface.
        
        Args:
            error: Exception that occurred
            
        Returns:
            Interface-specific formatted error
        """
        pass
```

---

## 4. Import Patterns

### 4.1 From CLI Code

```python
# Old pattern (v02)
from src.hiveforge.steering.workflows.init_workflow import InitWorkflow

# New pattern (v2.0)
from src.hiveforge.steering.shared import SharedInitWorkflow, CLIAdapter

# Usage
workflow = SharedInitWorkflow(config, project_root, adapter.create_progress_callback())
result = workflow.execute()
formatted = adapter.format_result(result)
```

### 4.2 From Power Tools

```python
# Power tool pattern
from src.hiveforge.steering.shared import (
    SharedInitWorkflow,
    PowerAdapter,
    secure_tool_execution
)

@secure_tool_execution()
async def init_steering(**kwargs):
    adapter = PowerAdapter()
    workflow = SharedInitWorkflow(config, project_root, adapter.create_progress_callback())
    result = workflow.execute()
    return adapter.format_result(result)
```

### 4.3 From Tests

```python
# Test pattern
from src.hiveforge.steering.shared import SharedInitWorkflow
from src.hiveforge.steering.models import SteeringConfig

def test_init_workflow():
    config = SteeringConfig()
    workflow = SharedInitWorkflow(config, Path("/tmp/test"))
    result = workflow.execute()
    assert result["status"] == "success"
```

---

## 5. Backward Compatibility

### 5.1 Existing CLI Workflow Wrappers

To maintain backward compatibility, existing workflow classes become thin wrappers:

```python
# src/hiveforge/steering/workflows/init_workflow.py (refactored)

from pathlib import Path
from typing import Optional

from ..models import SteeringConfig
from ..shared import SharedInitWorkflow, CLIAdapter


class InitWorkflow:
    """
    CLI-specific init workflow (backward compatibility wrapper).
    
    This class maintains the existing CLI interface while delegating
    to the shared backend implementation.
    """
    
    def __init__(self, config: SteeringConfig, project_root: Optional[Path] = None):
        self.config = config
        self.project_root = project_root or Path.cwd()
        self.adapter = CLIAdapter()
        self.shared_workflow = SharedInitWorkflow(
            config=config,
            project_root=self.project_root,
            progress_callback=self.adapter.create_progress_callback()
        )
    
    def execute(self) -> bool:
        """
        Execute init workflow (CLI interface).
        
        Returns:
            True if successful, False otherwise
        """
        result = self.shared_workflow.execute()
        
        # Format and display result using CLI adapter
        self.adapter.format_result(result)
        
        # Return boolean for backward compatibility
        return result["status"] == "success"
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

```python
# tests/shared/test_init_workflow.py

def test_shared_init_workflow_success():
    """Test successful init workflow execution."""
    config = SteeringConfig()
    workflow = SharedInitWorkflow(config, tmp_path)
    result = workflow.execute()
    
    assert result["status"] == "success"
    assert "files_created" in result["data"]
    assert result["data"]["files_created"] > 0

def test_shared_init_workflow_with_progress():
    """Test progress reporting."""
    progress_calls = []
    
    def progress_callback(step, message, percentage):
        progress_calls.append((step, message, percentage))
    
    workflow = SharedInitWorkflow(config, tmp_path, progress_callback)
    result = workflow.execute()
    
    assert len(progress_calls) > 0
    assert progress_calls[0][0] == "init"
    assert progress_calls[-1][0] == "complete"
```

### 6.2 Integration Tests

```python
# tests/architecture_validation/test_shared_backend_utilization.py

def test_cli_and_power_use_same_workflow():
    """Test that CLI and Power use the same shared workflow."""
    # CLI execution
    cli_workflow = SharedInitWorkflow(config, tmp_path)
    cli_result = cli_workflow.execute()
    
    # Power execution (same config, same path)
    power_workflow = SharedInitWorkflow(config, tmp_path)
    power_result = power_workflow.execute()
    
    # Results should be identical
    assert cli_result["status"] == power_result["status"]
    assert cli_result["data"] == power_result["data"]
```

---

## 7. Migration Checklist

### Phase 2.1: Create Foundation
- [ ] Create `src/hiveforge/steering/shared/` directory
- [ ] Create `shared/__init__.py` with exports
- [ ] Create `shared/workflows/base.py`
- [ ] Create `shared/security/` module structure
- [ ] Create `shared/telemetry/` module structure
- [ ] Create `shared/error_handling/` module structure
- [ ] Create `shared/adapters/` module structure

### Phase 2.2-2.4: Implement Workflows
- [ ] Implement `SharedInitWorkflow`
- [ ] Implement `SharedUpdateWorkflow`
- [ ] Implement `SharedValidateWorkflow`
- [ ] Write unit tests for each workflow

### Phase 3: Refactor CLI
- [ ] Refactor `workflows/init_workflow.py` to use shared
- [ ] Refactor `workflows/update_workflow.py` to use shared
- [ ] Refactor `workflows/validate_workflow.py` to use shared
- [ ] Implement `CLIAdapter`
- [ ] Test backward compatibility

### Phase 4: Implement Power
- [ ] Implement `PowerAdapter`
- [ ] Create MCP server structure
- [ ] Implement Power tools using shared workflows
- [ ] Test with KIRO orchestrator

---

## 8. Success Metrics

- [ ] All shared modules importable without errors
- [ ] Shared workflows return structured results
- [ ] CLI and Power use >95% shared code
- [ ] All tests pass
- [ ] No duplicate business logic
- [ ] Clear separation of concerns

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-17  
**Next Review**: Before Phase 2 implementation
