# Shared Backend Interface Design

**Feature**: steering-power-conversion  
**Version**: 2.0.0  
**Status**: Draft  
**Based on**: v02 autonomous generation implementation

---

## 1. Overview

This document defines the shared backend interface design for the Steering Assistant Power conversion. The shared backend is a Python module that provides a single source of truth for all steering operations, used by both the CLI interface and the MCP Power tools.

### 1.1 Design Goals

1. **Single Source of Truth**: Both CLI and Power tools use identical backend code
2. **Interface Agnostic**: Backend produces structured results that can be formatted for any interface
3. **Security First**: Built-in security validation and resource limits
4. **Error Handling**: Comprehensive error handling with automatic rollback
5. **Telemetry**: Shared telemetry for both CLI and Power usage

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Shared Backend Layer                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SharedWorkflowExecutor                       │   │
│  │  (Orchestrates workflow execution with security/error)   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              ▼               ▼               ▼                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │  Init Adapter   │ │ Update Adapter  │ │ Validate Adapter│   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
│              │               │               │                  │
│              ▼               ▼               ▼                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              v02 Workflow Wrappers                        │   │
│  │  (InitWorkflow, UpdateWorkflow, ValidateWorkflow, etc.)  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│              ┌───────────────┼───────────────┐                  │
│              ▼               ▼               ▼                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
│  │  Security       │ │ Error Handling  │ │  Telemetry      │   │
│  │  Wrappers       │ │  with Rollback  │ │  System         │   │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   CLI Interface │ │ MCP Power Tools │ │  Test Suite     │
│   (typer CLI)   │ │  (FastMCP)      │ │  (Validation)   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## 2. Shared Backend Module Structure

### 2.1 Directory Structure

```
src/hiveforge/steering/shared/
├── __init__.py
├── executor.py              # SharedWorkflowExecutor
├── adapters/
│   ├── __init__.py
│   ├── init_adapter.py      # InitWorkflow adapter
│   ├── update_adapter.py    # UpdateWorkflow adapter
│   ├── validate_adapter.py  # ValidateWorkflow adapter
│   ├── reset_adapter.py     # ResetWorkflow adapter
│   └── discover_adapter.py  # DiscoveryWorkflow adapter
├── security/
│   ├── __init__.py
│   ├── validators.py        # Input validation
│   ├── path_sanitizer.py    # Path sanitization
│   ├── resource_limiter.py  # Resource limits
│   └── decorators.py        # Security decorators
├── error_handling/
│   ├── __init__.py
│   ├── executor.py          # ToolExecutor with error handling
│   ├── rollback.py          # Automatic rollback logic
│   └── errors.py            # Error types and utilities
├── telemetry/
│   ├── __init__.py
│   ├── collector.py         # Telemetry collection
│   ├── storage.py           # Telemetry storage
│   └── exporters.py         # Telemetry export formats
└── results/
    ├── __init__.py
    ├── formatters.py        # Result formatting utilities
    └── types.py             # Result type definitions
```

### 2.2 Core Module: executor.py

```python
"""
Shared workflow executor for both CLI and Power tools.

This module provides the SharedWorkflowExecutor class that orchestrates
workflow execution with security, error handling, and telemetry.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of workflows supported by the shared backend."""
    INIT = "init"
    UPDATE = "update"
    VALIDATE = "validate"
    RESET = "reset"
    DISCOVER = "discover"


class ExecutionStatus(Enum):
    """Status of workflow execution."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class ExecutionContext:
    """Context for workflow execution."""
    project_root: Path
    workflow_type: WorkflowType
    interface_type: InterfaceType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class InterfaceType(Enum):
    """Type of interface initiating the execution."""
    CLI = "cli"
    POWER = "power"
    TEST = "test"


@dataclass
class ExecutionResult:
    """Result of workflow execution."""
    status: ExecutionStatus
    workflow_type: WorkflowType
    interface_type: InterfaceType
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    errors: list[Dict[str, Any]] = field(default_factory=list)
    telemetry_id: Optional[str] = None
    execution_time_seconds: float = 0.0
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    files_validated: list[str] = field(default_factory=list)
    backup_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "workflow_type": self.workflow_type.value,
            "interface_type": self.interface_type.value,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "telemetry_id": self.telemetry_id,
            "execution_time_seconds": self.execution_time_seconds,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "files_validated": self.files_validated,
            "backup_path": self.backup_path,
        }
    
    def format_for_cli(self) -> str:
        """Format result for CLI output."""
        if self.status == ExecutionStatus.SUCCESS:
            lines = [f"✓ {self.message}"]
            if self.files_created:
                lines.append(f"  Created: {', '.join(self.files_created)}")
            if self.files_modified:
                lines.append(f"  Modified: {', '.join(self.files_modified)}")
            if self.files_validated:
                lines.append(f"  Validated: {', '.join(self.files_validated)}")
            return "\n".join(lines)
        elif self.status == ExecutionStatus.PARTIAL:
            lines = [f"⚠ {self.message}"]
            for error in self.errors:
                lines.append(f"  - {error.get('message', 'Unknown error')}")
            return "\n".join(lines)
        else:
            lines = [f"✗ {self.message}"]
            for error in self.errors:
                lines.append(f"  - {error.get('message', 'Unknown error')}")
            return "\n".join(lines)


@runtime_checkable
class WorkflowAdapter(Protocol):
    """Protocol for workflow adapters."""
    
    @property
    def workflow_type(self) -> WorkflowType:
        """Return the type of workflow this adapter handles."""
        ...
    
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the workflow and return the result."""
        ...
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and return normalized parameters."""
        ...


class SharedWorkflowExecutor:
    """
    Shared workflow executor for both CLI and Power tools.
    
    This class orchestrates workflow execution with:
    - Security validation
    - Error handling with automatic rollback
    - Telemetry collection
    - Result formatting for different interfaces
    """
    
    def __init__(
        self,
        project_root: Path = Path("."),
        interface_type: InterfaceType = InterfaceType.CLI,
        enable_telemetry: bool = True,
        enable_security: bool = True,
    ):
        """
        Initialize the shared workflow executor.
        
        Args:
            project_root: Root directory of the project
            interface_type: Type of interface (CLI or Power)
            enable_telemetry: Whether to collect telemetry
            enable_security: Whether to apply security checks
        """
        self.project_root = project_root
        self.interface_type = interface_type
        self.enable_telemetry = enable_telemetry
        self.enable_security = enable_security
        
        # Initialize components
        self._adapters: Dict[WorkflowType, WorkflowAdapter] = {}
        self._security_wrapper = SecurityWrapper()
        self._error_handler = ErrorHandler()
        self._telemetry_collector = TelemetryCollector() if enable_telemetry else None
        
        # Register default adapters
        self._register_default_adapters()
    
    def _register_default_adapters(self) -> None:
        """Register default workflow adapters."""
        from .adapters import (
            InitAdapter,
            UpdateAdapter,
            ValidateAdapter,
            ResetAdapter,
            DiscoverAdapter,
        )
        
        self.register_adapter(InitAdapter())
        self.register_adapter(UpdateAdapter())
        self.register_adapter(ValidateAdapter())
        self.register_adapter(ResetAdapter())
        self.register_adapter(DiscoverAdapter())
    
    def register_adapter(self, adapter: WorkflowAdapter) -> None:
        """Register a workflow adapter."""
        self._adapters[adapter.workflow_type] = adapter
        logger.debug(f"Registered adapter for {adapter.workflow_type.value}")
    
    def execute_workflow(
        self,
        workflow_type: WorkflowType,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute a workflow with full error handling and telemetry.
        
        Args:
            workflow_type: Type of workflow to execute
            parameters: Workflow parameters
            user_id: Optional user identifier for telemetry
            session_id: Optional session identifier for telemetry
            
        Returns:
            ExecutionResult with status, data, and any errors
        """
        import time
        start_time = time.time()
        
        # Create execution context
        context = ExecutionContext(
            project_root=self.project_root,
            workflow_type=workflow_type,
            interface_type=self.interface_type,
            user_id=user_id,
            session_id=session_id,
            parameters=parameters,
        )
        
        # Get adapter
        adapter = self._adapters.get(workflow_type)
        if not adapter:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                workflow_type=workflow_type,
                interface_type=self.interface_type,
                message=f"No adapter registered for workflow type: {workflow_type.value}",
                execution_time_seconds=time.time() - start_time,
            )
        
        # Execute with error handling
        try:
            # Security validation
            if self.enable_security:
                parameters = self._security_wrapper.validate_parameters(parameters)
                context.parameters = parameters
            
            # Validate parameters
            validated_params = adapter.validate_parameters(parameters)
            
            # Execute workflow
            result = adapter.execute(context)
            
            # Add telemetry
            if self._telemetry_collector and result.status == ExecutionStatus.SUCCESS:
                result.telemetry_id = self._telemetry_collector.collect(
                    workflow_type=workflow_type,
                    interface_type=self.interface_type,
                    parameters=validated_params,
                    result=result,
                    execution_time=time.time() - start_time,
                )
            
            return result
            
        except SecurityError as e:
            logger.error(f"Security error: {e}")
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                workflow_type=workflow_type,
                interface_type=self.interface_type,
                message="Security validation failed",
                errors=[{"type": "security", "message": str(e)}],
                execution_time_seconds=time.time() - start_time,
            )
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                workflow_type=workflow_type,
                interface_type=self.interface_type,
                message=f"Workflow execution failed: {str(e)}",
                errors=[{"type": "execution", "message": str(e)}],
                execution_time_seconds=time.time() - start_time,
            )
    
    def get_adapter(self, workflow_type: WorkflowType) -> Optional[WorkflowAdapter]:
        """Get a registered workflow adapter."""
        return self._adapters.get(workflow_type)


# Import components for type checking
from .security import SecurityWrapper, SecurityError
from .error_handling import ErrorHandler
from .telemetry import TelemetryCollector
---

## 3. Workflow Adapter Interfaces

### 3.1 Base Adapter Protocol

```python
"""
Workflow adapter protocols and base classes.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .executor import (
    WorkflowType,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)


class ConfidenceLevel(Enum):
    """Confidence levels for workflow decisions."""
    HIGH = "high"      # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"        # < 0.5


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution."""
    auto_discover: bool = True
    autonomous: bool = True
    confidence_threshold: float = 0.7
    preserve_customizations: bool = True
    incremental: bool = True
    strict: bool = False
    use_llm: bool = True
    include_git_history: bool = False
    target_files: Optional[List[str]] = None
    project_root: Path = Path(".")
    
    def validate(self) -> List[str]:
        """Validate configuration and return any errors."""
        errors = []
        if not 0.0 <= self.confidence_threshold <= 1.0:
            errors.append("confidence_threshold must be between 0.0 and 1.0")
        if self.confidence_threshold > 0.9:
            errors.append("confidence_threshold > 0.9 may cause excessive fallback")
        return errors


@dataclass
class WorkflowState:
    """State tracking for workflow execution."""
    phase: str = "init"
    files_generated: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_validated: List[str] = field(default_factory=list)
    issues_found: List[Dict[str, Any]] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    knowledge_base: Dict[str, Any] = field(default_factory=dict)
    customizations_detected: List[Dict[str, Any]] = field(default_factory=list)
    conflicts_detected: List[Dict[str, Any]] = field(default_factory=list)
    backup_created: bool = False
    backup_path: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "phase": self.phase,
            "files_generated": self.files_generated,
            "files_modified": self.files_modified,
            "files_validated": self.files_validated,
            "issues_found": self.issues_found,
            "confidence_scores": self.confidence_scores,
            "knowledge_base": self.knowledge_base,
            "customizations_detected": self.customizations_detected,
            "conflicts_detected": self.conflicts_detected,
            "backup_created": self.backup_created,
            "backup_path": self.backup_path,
            "start_time": self.start_time.isoformat(),
        }


class BaseWorkflowAdapter(ABC):
    """Base class for workflow adapters."""
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        Initialize the adapter with optional configuration.
        
        Args:
            config: Optional workflow configuration
        """
        self.config = config or WorkflowConfig()
        self.state = WorkflowState()
        self._errors: List[Dict[str, Any]] = []
    
    @property
    @abstractmethod
    def workflow_type(self) -> WorkflowType:
        """Return the type of workflow this adapter handles."""
        pass
    
    @abstractmethod
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the workflow and return the result.
        
        Args:
            context: Execution context with project and interface info
            
        Returns:
            ExecutionResult with status, data, and any errors
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize parameters.
        
        Args:
            parameters: Raw parameters from caller
            
        Returns:
            Validated and normalized parameters
        """
        pass
    
    def _add_error(self, error_type: str, message: str, recoverable: bool = True) -> None:
        """Add an error to the error list."""
        self._errors.append({
            "type": error_type,
            "message": message,
            "recoverable": recoverable,
            "timestamp": datetime.now().isoformat(),
        })
    
    def _clear_errors(self) -> None:
        """Clear all errors."""
        self._errors = []
    
    def _get_errors(self) -> List[Dict[str, Any]]:
        """Get all errors."""
        return self._errors.copy()
```

### 3.2 Init Adapter

```python
"""
Init workflow adapter for steering file initialization.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import logging

from .base import (
    BaseWorkflowAdapter,
    WorkflowConfig,
    WorkflowType,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
    ConfidenceLevel,
)

logger = logging.getLogger(__name__)


class InitAdapter(BaseWorkflowAdapter):
    """
    Adapter for the init workflow.
    
    Wraps the v02 InitWorkflow class and provides a unified interface
    for both CLI and Power tool usage.
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize the init adapter."""
        super().__init__(config)
        self.workflow_type = WorkflowType.INIT
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize init parameters."""
        validated = {
            "auto_discover": parameters.get("auto_discover", True),
            "autonomous": parameters.get("autonomous", True),
            "confidence_threshold": parameters.get("confidence_threshold", 0.7),
            "project_root": str(parameters.get("project_root", ".")),
        }
        
        # Validate confidence threshold
        try:
            threshold = float(validated["confidence_threshold"])
            if not 0.0 <= threshold <= 1.0:
                raise ValueError("confidence_threshold must be between 0.0 and 1.0")
            validated["confidence_threshold"] = threshold
        except (TypeError, ValueError) as e:
            self._add_error("validation", f"Invalid confidence_threshold: {e}")
        
        return validated
    
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the init workflow.
        
        This method wraps the v02 InitWorkflow and provides:
        - Unified result format
        - Error handling with rollback
        - Telemetry integration
        """
        import time
        from hiveforge.steering.workflows.init_workflow import InitWorkflow
        from hiveforge.steering.models import SteeringConfig, FeatureFlagConfig
        
        start_time = time.time()
        self._clear_errors()
        
        try:
            # Create v02 workflow config
            config = SteeringConfig(
                interactive=not self.config.autonomous,
                analyze_code=self.config.auto_discover,
                feature_flags=FeatureFlagConfig(
                    use_autonomous_generation=self.config.autonomous,
                    confidence_threshold=self.config.confidence_threshold,
                ),
            )
            
            # Create v02 workflow
            workflow = InitWorkflow(
                config=config,
                project_root=Path(context.project_root),
            )
            
            # Execute v02 workflow
            success = workflow.execute()
            
            # Map v02 result to shared result
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Initialized steering files: {len(workflow.state.generated_files)} files created",
                data={
                    "files_generated": workflow.state.generated_files,
                    "confidence_scores": workflow.state.confidence_scores,
                    "validation_status": workflow.state.validation_status,
                },
                files_created=workflow.state.generated_files,
                execution_time_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"Init workflow failed: {e}", exc_info=True)
            self._add_error("execution", str(e), recoverable=True)
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Failed to initialize steering files: {str(e)}",
                errors=self._get_errors(),
                execution_time_seconds=time.time() - start_time,
            )
```

### 3.3 Update Adapter

```python
"""
Update workflow adapter for updating existing steering files.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .base import (
    BaseWorkflowAdapter,
    WorkflowConfig,
    WorkflowType,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)

logger = logging.getLogger(__name__)


class UpdateAdapter(BaseWorkflowAdapter):
    """
    Adapter for the update workflow.
    
    Wraps the v02 UpdateWorkflow class and provides:
    - Incremental update support
    - Customization preservation
    - Conflict detection and resolution
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize the update adapter."""
        super().__init__(config)
        self.workflow_type = WorkflowType.UPDATE
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize update parameters."""
        validated = {
            "files": parameters.get("files", []),
            "preserve_customizations": parameters.get("preserve_customizations", True),
            "incremental": parameters.get("incremental", True),
            "project_root": str(parameters.get("project_root", ".")),
        }
        
        # Validate files list
        if validated["files"] and not isinstance(validated["files"], list):
            self._add_error("validation", "files must be a list")
            validated["files"] = []
        
        return validated
    
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the update workflow.
        
        This method wraps the v02 UpdateWorkflow and provides:
        - Incremental updates
        - Customization preservation
        - Conflict detection
        """
        import time
        from hiveforge.steering.workflows.update_workflow import UpdateWorkflow
        from hiveforge.steering.models import SteeringConfig
        
        start_time = time.time()
        self._clear_errors()
        
        try:
            # Create v02 workflow config
            config = SteeringConfig(
                interactive=False,
                analyze_code=False,
            )
            
            # Create v02 workflow
            workflow = UpdateWorkflow(
                config=config,
                project_root=Path(context.project_root),
                files_to_update=self.config.target_files,
                preserve_customizations=self.config.preserve_customizations,
                incremental=self.config.incremental,
            )
            
            # Execute v02 workflow
            success = workflow.execute()
            
            # Map v02 result to shared result
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Updated steering files: {len(workflow.state.files_modified)} files modified",
                data={
                    "files_modified": workflow.state.files_modified,
                    "customizations_preserved": workflow.state.customizations_detected,
                    "conflicts_detected": workflow.state.conflicts_detected,
                },
                files_modified=workflow.state.files_modified,
                execution_time_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"Update workflow failed: {e}", exc_info=True)
            self._add_error("execution", str(e), recoverable=True)
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Failed to update steering files: {str(e)}",
                errors=self._get_errors(),
                execution_time_seconds=time.time() - start_time,
            )
```

### 3.4 Validate Adapter

```python
"""
Validate workflow adapter for validating steering files.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import logging

from .base import (
    BaseWorkflowAdapter,
    WorkflowConfig,
    WorkflowType,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)

logger = logging.getLogger(__name__)


class ValidateAdapter(BaseWorkflowAdapter):
    """
    Adapter for the validate workflow.
    
    Wraps the v02 ValidateWorkflow class and provides:
    - Structural validation
    - Semantic validation (LLM-based)
    - Strict mode for CI/CD
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize the validate adapter."""
        super().__init__(config)
        self.workflow_type = WorkflowType.VALIDATE
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize validate parameters."""
        validated = {
            "strict": parameters.get("strict", False),
            "use_llm": parameters.get("use_llm", True),
            "project_root": str(parameters.get("project_root", ".")),
        }
        return validated
    
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the validate workflow.
        
        This method wraps the v02 ValidateWorkflow and provides:
        - File existence checks
        - Structural validation
        - Semantic validation
        """
        import time
        from hiveforge.steering.workflows.validate_workflow import ValidateWorkflow
        from hiveforge.steering.models import SteeringConfig
        
        start_time = time.time()
        self._clear_errors()
        
        try:
            # Create v02 workflow config
            config = SteeringConfig(
                interactive=False,
                analyze_code=False,
            )
            
            # Create v02 workflow
            workflow = ValidateWorkflow(
                config=config,
                project_root=Path(context.project_root),
                strict=self.config.strict,
                use_llm=self.config.use_llm,
            )
            
            # Execute v02 workflow
            exit_code = workflow.execute()
            success = exit_code == 0
            
            # Map v02 result to shared result
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Validation complete: {len(workflow.state.files_validated)} files checked",
                data={
                    "files_validated": workflow.state.files_validated,
                    "issues_found": workflow.state.issues_found,
                    "exit_code": exit_code,
                },
                files_validated=workflow.state.files_validated,
                execution_time_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"Validate workflow failed: {e}", exc_info=True)
            self._add_error("execution", str(e), recoverable=True)
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Failed to validate steering files: {str(e)}",
                errors=self._get_errors(),
                execution_time_seconds=time.time() - start_time,
            )
```

### 3.5 Reset Adapter

```python
"""
Reset workflow adapter for restoring default templates.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .base import (
    BaseWorkflowAdapter,
    WorkflowConfig,
    WorkflowType,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)

logger = logging.getLogger(__name__)


class ResetAdapter(BaseWorkflowAdapter):
    """
    Adapter for the reset workflow.
    
    Provides template restoration with:
    - Backup creation before reset
    - Single file or all files reset
    - Confirmation requirement
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize the reset adapter."""
        super().__init__(config)
        self.workflow_type = WorkflowType.RESET
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize reset parameters."""
        validated = {
            "file": parameters.get("file"),
            "confirm": parameters.get("confirm", False),
            "project_root": str(parameters.get("project_root", ".")),
        }
        
        # Validate file parameter
        if validated["file"] is not None and not isinstance(validated["file"], str):
            self._add_error("validation", "file must be a string or None")
            validated["file"] = None
        
        return validated
    
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the reset workflow.
        
        This method:
        1. Creates a backup of current files
        2. Resets files to default templates
        3. Returns result with backup location
        """
        import time
        from hiveforge.steering.backup_manager import BackupManager
        from hiveforge.steering.template_populator import TemplatePopulator
        
        start_time = time.time()
        self._clear_errors()
        
        project_root = Path(context.project_root)
        steering_dir = project_root / ".kiro" / "steering"
        template_dir = Path(__file__).parent.parent / "templates" / "steering"
        
        try:
            # Create backup first
            backup_mgr = BackupManager(
                backup_dir=project_root / ".kiro" / "backups"
            )
            
            # Get files to backup
            files_to_backup = list(steering_dir.glob("*.md")) if steering_dir.exists() else []
            
            if files_to_backup:
                backup_path = backup_mgr.create_backup(files_to_backup)
                self.state.backup_created = True
                self.state.backup_path = str(backup_path)
            
            # Reset files
            populator = TemplatePopulator(
                template_dir=template_dir,
                output_dir=steering_dir,
            )
            
            if self.config.target_files:
                # Reset specific files
                reset_files = []
                for file_name in self.config.target_files:
                    if (steering_dir / file_name).exists():
                        populator.populate_single(file_name)
                        reset_files.append(file_name)
            else:
                # Reset all files
                reset_files = populator.populate_all()
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Reset {len(reset_files)} file(s) to default templates",
                data={
                    "files_reset": reset_files,
                    "backup_created": self.state.backup_created,
                    "backup_path": self.state.backup_path,
                },
                files_modified=reset_files,
                backup_path=self.state.backup_path,
                execution_time_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"Reset workflow failed: {e}", exc_info=True)
            self._add_error("execution", str(e), recoverable=False)
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Failed to reset steering files: {str(e)}",
                errors=self._get_errors(),
                execution_time_seconds=time.time() - start_time,
            )
```

### 3.6 Discover Adapter

```python
"""
Discover workflow adapter for finding project documentation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .base import (
    BaseWorkflowAdapter,
    WorkflowConfig,
    WorkflowType,
    ExecutionContext,
    ExecutionResult,
    ExecutionStatus,
)

logger = logging.getLogger(__name__)


class DiscoverAdapter(BaseWorkflowAdapter):
    """
    Adapter for the discover workflow.
    
    Provides project documentation discovery with:
    - File pattern matching
    - Relevance scoring
    - Git history analysis (optional)
    """
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """Initialize the discover adapter."""
        super().__init__(config)
        self.workflow_type = WorkflowType.DISCOVER
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize discover parameters."""
        validated = {
            "include_git_history": parameters.get("include_git_history", False),
            "project_root": str(parameters.get("project_root", ".")),
        }
        return validated
    
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the discover workflow.
        
        This method:
        1. Scans project for documentation files
        2. Scores relevance to steering
        3. Returns ranked list of files
        """
        import time
        from hiveforge.steering.scalable_discovery import ScalableDiscovery
        
        start_time = time.time()
        self._clear_errors()
        
        project_root = Path(context.project_root)
        
        try:
            # Create discovery instance
            discovery = ScalableDiscovery(
                project_root=project_root,
                include_git_history=self.config.include_git_history,
            )
            
            # Run discovery
            found_docs = discovery.discover()
            
            # Calculate relevance scores
            relevance_scores = discovery.score_relevance(found_docs)
            
            # Filter to high-relevance docs
            high_relevance = [
                doc for doc, score in relevance_scores.items()
                if score >= 0.5
            ]
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Found {len(found_docs)} documentation files, {len(high_relevance)} high relevance",
                data={
                    "found_documents": [
                        {
                            "path": str(doc["path"]),
                            "type": doc["type"],
                            "relevance": relevance_scores.get(doc["path"], 0.0),
                        }
                        for doc in found_docs
                    ],
                    "high_relevance_count": len(high_relevance),
                    "suggested_import": len(high_relevance) > 0,
                },
                execution_time_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"Discover workflow failed: {e}", exc_info=True)
            self._add_error("execution", str(e), recoverable=True)
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                workflow_type=self.workflow_type,
                interface_type=context.interface_type,
                message=f"Failed to discover project documentation: {str(e)}",
                errors=self._get_errors(),
                execution_time_seconds=time.time() - start_time,
            )
```
---

## 4. Security Wrapper Interfaces

### 4.1 Security Module Structure

```python
"""
Security wrappers for shared backend.

Provides input validation, path sanitization, and resource limits
for both CLI and Power tool usage.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import re
import os
import resource
import time
from dataclasses import dataclass
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# Security constants
ALLOWED_DIRECTORIES = [
    ".kiro",
    "docs",
    "src",
    "tests",
    ".",
]

MAX_PATH_LENGTH = 4096
MAX_FILE_SIZE_MB = 10
MAX_MEMORY_MB = 512
MAX_CPU_TIME_SEC = 300
MAX_FILE_COUNT = 100


class SecurityError(Exception):
    """Exception raised for security violations."""
    pass


@dataclass
class ValidationResult:
    """Result of security validation."""
    is_valid: bool
    errors: List[str]
    sanitized_values: Dict[str, Any]


class InputValidator:
    """
    Validates and sanitizes input parameters.
    """
    
    # Regex patterns for validation
    PATH_PATTERN = re.compile(r'^[\w\-\./\\]+$')
    FILE_PATTERN = re.compile(r'^[\w\-\.]+\.md$')
    CONFIDENCE_PATTERN = re.compile(r'^0\.\d+$')
    
    @classmethod
    def validate_parameters(
        cls,
        parameters: Dict[str, Any],
        allowed_keys: List[str],
    ) -> ValidationResult:
        """
        Validate all input parameters.
        
        Args:
            parameters: Input parameters to validate
            allowed_keys: List of allowed parameter keys
            
        Returns:
            ValidationResult with sanitized values and any errors
        """
        errors = []
        sanitized = {}
        
        # Check for unknown keys
        unknown_keys = set(parameters.keys()) - set(allowed_keys)
        if unknown_keys:
            errors.append(f"Unknown parameters: {', '.join(unknown_keys)}")
        
        # Validate each parameter
        for key, value in parameters.items():
            if key not in allowed_keys:
                continue
            
            try:
                sanitized[key] = cls._validate_single(key, value)
            except (ValueError, SecurityError) as e:
                errors.append(f"Invalid {key}: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_values=sanitized,
        )
    
    @classmethod
    def _validate_single(cls, key: str, value: Any) -> Any:
        """Validate a single parameter value."""
        if key == "project_root":
            return cls._validate_path(value)
        elif key == "file":
            return cls._validate_file(value)
        elif key == "files":
            return cls._validate_file_list(value)
        elif key == "confidence_threshold":
            return cls._validate_confidence(value)
        elif key == "target_files":
            return cls._validate_file_list(value)
        elif key in ["auto_discover", "autonomous", "preserve_customizations", 
                     "incremental", "strict", "use_llm", "include_git_history", "confirm"]:
            return cls._validate_bool(value)
        else:
            return value
    
    @classmethod
    def _validate_path(cls, path: Any) -> str:
        """Validate and sanitize a path."""
        if not isinstance(path, (str, Path)):
            raise ValueError("Path must be a string or Path")
        
        path_str = str(path)
        
        # Check length
        if len(path_str) > MAX_PATH_LENGTH:
            raise SecurityError(f"Path exceeds maximum length: {MAX_PATH_LENGTH}")
        
        # Check for path traversal
        if ".." in path_str:
            raise SecurityError("Path traversal attempt detected")
        
        # Check for absolute path outside project
        abs_path = Path(path_str).resolve()
        if not str(abs_path).startswith(os.getcwd()):
            raise SecurityError("Path outside project directory not allowed")
        
        return path_str
    
    @classmethod
    def _validate_file(cls, file: Any) -> Optional[str]:
        """Validate a single file name."""
        if file is None:
            return None
        
        if not isinstance(file, str):
            raise ValueError("File must be a string")
        
        if not cls.FILE_PATTERN.match(file):
            raise ValueError(f"Invalid file name: {file}")
        
        return file
    
    @classmethod
    def _validate_file_list(cls, files: Any) -> List[str]:
        """Validate a list of file names."""
        if files is None:
            return []
        
        if not isinstance(files, (list, tuple)):
            raise ValueError("Files must be a list or tuple")
        
        if len(files) > MAX_FILE_COUNT:
            raise ValueError(f"Too many files: {len(files)} (max: {MAX_FILE_COUNT})")
        
        return [cls._validate_file(f) for f in files]
    
    @classmethod
    def _validate_confidence(cls, confidence: Any) -> float:
        """Validate confidence threshold."""
        try:
            value = float(confidence)
        except (TypeError, ValueError):
            raise ValueError("Confidence must be a number")
        
        if not 0.0 <= value <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        return value
    
    @classmethod
    def _validate_bool(cls, value: Any) -> bool:
        """Validate boolean value."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)


class PathSanitizer:
    """
    Sanitizes paths to prevent directory traversal and other attacks.
    """
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """
        Sanitize a path to prevent directory traversal.
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized path
            
        Raises:
            SecurityError: If path is malicious
        """
        # Resolve to absolute path
        try:
            abs_path = Path(path).resolve()
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid path: {e}")
        
        # Check for path traversal attempts
        normalized = str(abs_path)
        if ".." in normalized:
            raise SecurityError("Path traversal attempt detected")
        
        # Ensure path is within allowed directories
        cwd = os.getcwd()
        if not normalized.startswith(cwd):
            raise SecurityError("Path outside project directory not allowed")
        
        return str(abs_path)
    
    @staticmethod
    def sanitize_file_list(files: List[str]) -> List[str]:
        """Sanitize a list of file names."""
        return [PathSanitizer.sanitize_path(f) for f in files]


class ResourceLimiter:
    """
    Enforces resource limits for workflow execution.
    """
    
    def __init__(
        self,
        max_memory_mb: int = MAX_MEMORY_MB,
        max_cpu_time_sec: int = MAX_CPU_TIME_SEC,
        max_file_size_mb: int = MAX_FILE_SIZE_MB,
    ):
        """
        Initialize resource limiter.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            max_cpu_time_sec: Maximum CPU time in seconds
            max_file_size_mb: Maximum file size in MB
        """
        self.max_memory_mb = max_memory_mb
        self.max_cpu_time_sec = max_cpu_time_sec
        self.max_file_size_mb = max_file_size_mb
        self.start_time: Optional[float] = None
    
    def __enter__(self) -> "ResourceLimiter":
        """Enter resource limit context."""
        self.start_time = time.time()
        
        # Set memory limit
        try:
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.max_memory_mb * 1024 * 1024, resource.RLIM_INFINITY),
            )
        except (ValueError, OSError):
            logger.warning("Could not set memory limit - running without limit")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit resource limit context and check limits."""
        if self.start_time is None:
            return
        
        # Check CPU time
        elapsed = time.time() - self.start_time
        if elapsed > self.max_cpu_time_sec:
            raise ResourceLimitError(
                f"CPU time limit exceeded: {elapsed:.1f}s > {self.max_cpu_time_max}s"
            )
    
    def check_file_size(self, file_path: Path) -> None:
        """Check if a file is within size limits."""
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                raise ResourceLimitError(
                    f"File {file_path} exceeds size limit: {size_mb:.1f}MB > {self.max_file_size_mb}MB"
                )
        except OSError as e:
            raise ResourceLimitError(f"Could not check file size: {e}")


class ResourceLimitError(Exception):
    """Exception raised when resource limits are exceeded."""
    pass


class SecurityWrapper:
    """
    Main security wrapper for workflow execution.
    
    Combines input validation, path sanitization, and resource limits.
    """
    
    def __init__(self):
        """Initialize security wrapper."""
        self.validator = InputValidator()
        self.sanitizer = PathSanitizer()
    
    def validate_parameters(
        self,
        parameters: Dict[str, Any],
        allowed_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validate and sanitize all parameters.
        
        Args:
            parameters: Parameters to validate
            allowed_keys: Optional list of allowed keys (defaults to all common keys)
            
        Returns:
            Validated and sanitized parameters
            
        Raises:
            SecurityError: If validation fails
        """
        if allowed_keys is None:
            allowed_keys = [
                "project_root", "file", "files", "target_files",
                "auto_discover", "autonomous", "confidence_threshold",
                "preserve_customizations", "incremental", "strict",
                "use_llm", "include_git_history", "confirm",
            ]
        
        result = self.validator.validate_parameters(parameters, allowed_keys)
        
        if not result.is_valid:
            raise SecurityError(f"Parameter validation failed: {', '.join(result.errors)}")
        
        return result.sanitized_values
    
    def sanitize_path(self, path: str) -> str:
        """Sanitize a single path."""
        return self.sanitizer.sanitize_path(path)
    
    def get_resource_limiter(self) -> ResourceLimiter:
        """Get a resource limiter instance."""
        return ResourceLimiter()


def secure_execution(
    max_memory_mb: int = MAX_MEMORY_MB,
    max_cpu_time_sec: int = MAX_CPU_TIME_SEC,
) -> Callable:
    """
    Decorator for secure workflow execution.
    
    Applies input validation, path sanitization, and resource limits.
    
    Args:
        max_memory_mb: Maximum memory in MB
        max_cpu_time_sec: Maximum CPU time in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate parameters
            security = SecurityWrapper()
            
            # Get parameters from kwargs
            if kwargs:
                validated = security.validate_parameters(kwargs)
                kwargs.update(validated)
            
            # Apply resource limits
            limiter = security.get_resource_limiter()
            with limiter:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

---

## 5. Error Handling with Automatic Rollback

### 5.1 Error Handling Module Structure

```python
"""
Error handling with automatic rollback for shared backend.

Provides comprehensive error handling, automatic backups,
and rollback capabilities for both CLI and Power tools.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import shutil
import traceback

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors."""
    FILE_SYSTEM = "file_system"
    PARSING = "parsing"
    CODE_ANALYSIS = "code_analysis"
    LLM_API = "llm_api"
    VALIDATION = "validation"
    SECURITY = "security"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for an error."""
    error_type: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    suggested_action: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.error_type,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "timestamp": self.timestamp,
            "details": self.details,
            "recoverable": self.recoverable,
            "suggested_action": self.suggested_action,
        }


@dataclass
class RollbackInfo:
    """Information about a rollback operation."""
    backup_path: Optional[Path] = None
    files_affected: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reason: str = ""
    success: bool = True
    error_message: Optional[str] = None


class BackupManager:
    """
    Manages backups for rollback capability.
    
    Creates backups before operations and can restore from them.
    """
    
    def __init__(
        self,
        backup_dir: Path = Path(".kiro/backups/steering"),
        max_backups: int = 5,
    ):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to keep
        """
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(
        self,
        files: List[Path],
        backup_name: Optional[str] = None,
    ) -> Path:
        """
        Create a backup of files.
        
        Args:
            files: List of file paths to backup
            backup_name: Optional backup name
            
        Returns:
            Path to backup directory
        """
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_name = f"backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for file_path in files:
            if file_path.exists():
                dest_path = backup_path / file_path.name
                shutil.copy2(file_path, dest_path)
        
        logger.info(f"Created backup at {backup_path}")
        return backup_path
    
    def restore_backup(
        self,
        backup_path: Path,
        target_dir: Path,
    ) -> List[Path]:
        """
        Restore files from a backup.
        
        Args:
            backup_path: Path to backup directory
            target_dir: Target directory to restore to
            
        Returns:
            List of restored file paths
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        restored = []
        
        for file_path in backup_path.glob("*.md"):
            dest_path = target_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            restored.append(dest_path)
        
        logger.info(f"Restored {len(restored)} files from {backup_path}")
        return restored
    
    def cleanup_old_backups(self, max_backups: Optional[int] = None) -> int:
        """Delete old backups exceeding the limit."""
        if max_backups is None:
            max_backups = self.max_backups
        
        backups = sorted(
            self.backup_dir.glob("backup_*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        
        deleted = 0
        for backup in backups[max_backups:]:
            shutil.rmtree(backup)
            deleted += 1
        
        return deleted


class ErrorHandler:
    """
    Comprehensive error handler with automatic rollback.
    
    Features:
    - Categorized error handling
    - Automatic backup before operations
    - Rollback on failure
    - User-friendly error messages
    - Detailed error logging
    """
    
    def __init__(
        self,
        backup_dir: Optional[Path] = None,
        auto_backup: bool = True,
        auto_rollback: bool = True,
    ):
        """
        Initialize error handler.
        
        Args:
            backup_dir: Directory for backups
            auto_backup: Whether to create backups automatically
            auto_rollback: Whether to rollback on failure
        """
        self.backup_dir = backup_dir or Path(".kiro/backups/steering")
        self.auto_backup = auto_backup
        self.auto_rollback = auto_rollback
        self.backup_manager = BackupManager(backup_dir=self.backup_dir)
        self._current_backup: Optional[Path] = None
        self._rollback_info: Optional[RollbackInfo] = None
    
    def create_backup(self, files: List[Path]) -> Optional[Path]:
        """
        Create a backup before operations.
        
        Args:
            files: Files to backup
            
        Returns:
            Path to backup or None if failed
        """
        if not self.auto_backup:
            return None
        
        try:
            self._current_backup = self.backup_manager.create_backup(files)
            return self._current_backup
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
    ) -> ErrorContext:
        """
        Handle an error and create error context.
        
        Args:
            error: The exception that occurred
            context: Optional additional context
            
        Returns:
            ErrorContext with error details
        """
        # Determine error category
        category = self._categorize_error(error)
        
        # Determine severity
        severity = self._determine_severity(error, category)
        
        # Create error context
        error_context = ErrorContext(
            error_type=type(error).__name__,
            message=str(error),
            severity=severity,
            category=category,
            details={
                "traceback": traceback.format_exc(),
            },
            recoverable=self._is_recoverable(error, category),
            suggested_action=self._get_suggested_action(error, category),
        )
        
        # Merge with provided context
        if context:
            error_context.details.update(context.details)
            if context.suggested_action:
                error_context.suggested_action = context.suggested_action
        
        # Log error
        logger.error(
            f"Error: {error_context.message}",
            extra={"error_context": error_context.to_dict()},
        )
        
        # Trigger rollback if needed
        if self.auto_rollback and self._current_backup:
            self._rollback()
        
        return error_context
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize an error based on its type."""
        error_name = type(error).__name__.lower()
        
        if "file" in error_name or "path" in error_name or "permission" in error_name:
            return ErrorCategory.FILE_SYSTEM
        elif "parse" in error_name or "syntax" in error_name:
            return ErrorCategory.PARSING
        elif "analysis" in error_name or "lint" in error_name:
            return ErrorCategory.CODE_ANALYSIS
        elif "api" in error_name or "llm" in error_name or "openai" in error_name:
            return ErrorCategory.LLM_API
        elif "valid" in error_name or "check" in error_name:
            return ErrorCategory.VALIDATION
        elif "security" in error_name or "path traversal" in error_name:
            return ErrorCategory.SECURITY
        elif "resource" in error_name or "memory" in error_name or "time" in error_name:
            return ErrorCategory.RESOURCE
        else:
            return ErrorCategory.UNKNOWN
    
    def _determine_severity(
        self,
        error: Exception,
        category: ErrorCategory,
    ) -> ErrorSeverity:
        """Determine error severity."""
        if category == ErrorCategory.SECURITY:
            return ErrorSeverity.CRITICAL
        elif category == ErrorCategory.RESOURCE:
            return ErrorSeverity.ERROR
        elif category == ErrorCategory.LLM_API:
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.ERROR
    
    def _is_recoverable(
        self,
        error: Exception,
        category: ErrorCategory,
    ) -> bool:
        """Determine if an error is recoverable."""
        if category == ErrorCategory.SECURITY:
            return False
        elif category == ErrorCategory.RESOURCE:
            return False
        return True
    
    def _get_suggested_action(
        self,
        error: Exception,
        category: ErrorCategory,
    ) -> str:
        """Get suggested action for error."""
        suggestions = {
            ErrorCategory.FILE_SYSTEM: "Check file permissions and disk space",
            ErrorCategory.PARSING: "Verify file format is correct",
            ErrorCategory.CODE_ANALYSIS: "Check code for syntax errors",
            ErrorCategory.LLM_API: "Check API key and rate limits",
            ErrorCategory.VALIDATION: "Review input parameters",
            ErrorCategory.SECURITY: "Contact system administrator",
            ErrorCategory.RESOURCE: "Reduce scope or increase limits",
            ErrorCategory.UNKNOWN: "Try again or contact support",
        }
        return suggestions.get(category, "Try again")
    
    def _rollback(self) -> RollbackInfo:
        """Perform rollback from backup."""
        self._rollback_info = RollbackInfo(
            backup_path=self._current_backup,
            reason="Automatic rollback on error",
        )
        
        if not self._current_backup or not self._current_backup.exists():
            self._rollback_info.success = False
            self._rollback_info.error_message = "No backup to restore"
            return self._rollback_info
        
        try:
            steering_dir = Path(".kiro/steering")
            self.backup_manager.restore_backup(self._current_backup, steering_dir)
            self._rollback_info.success = True
            logger.info("Rollback completed successfully")
        except Exception as e:
            self._rollback_info.success = False
            self._rollback_info.error_message = str(e)
            logger.error(f"Rollback failed: {e}")
        
        return self._rollback_info
    
    def get_rollback_info(self) -> Optional[RollbackInfo]:
        """Get information about the last rollback."""
        return self._rollback_info


class ToolExecutor:
    """
    Executor for tools with comprehensive error handling.
    
    Usage:
        executor = ToolExecutor()
        result = executor.execute(
            operation=my_workflow.execute,
            files_to_backup=[...],
            on_success=lambda r: format_result(r),
            on_error=lambda e: handle_error(e),
        )
    """
    
    def __init__(
        self,
        backup_dir: Optional[Path] = None,
        auto_backup: bool = True,
        auto_rollback: bool = True,
    ):
        """
        Initialize tool executor.
        
        Args:
            backup_dir: Directory for backups
            auto_backup: Whether to create backups automatically
            auto_rollback: Whether to rollback on failure
        """
        self.error_handler = ErrorHandler(
            backup_dir=backup_dir,
            auto_backup=auto_backup,
            auto_rollback=auto_rollback,
        )
    
    def execute(
        self,
        operation: Callable,
        files_to_backup: Optional[List[Path]] = None,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        **operation_kwargs,
    ) -> Any:
        """
        Execute an operation with error handling.
        
        Args:
            operation: Callable to execute
            files_to_backup: Files to backup before operation
            on_success: Callback on success
            on_error: Callback on error
            **operation_kwargs: Arguments to pass to operation
            
        Returns:
            Result of operation or error handling
        """
        # Create backup
        backup_path = None
        if files_to_backup:
            backup_path = self.error_handler.create_backup(files_to_backup)
        
        try:
            # Execute operation
            result = operation(**operation_kwargs)
            
            # Success callback
            if on_success:
                return on_success(result)
            
            return result
            
        except Exception as e:
            # Handle error
            error_context = self.error_handler.handle_error(e)
            
            # Error callback
            if on_error:
                return on_error(error_context)
            
            # Re-raise if no callback
            raise
        
        finally:
            # Cleanup old backups
            try:
                self.error_handler.backup_manager.cleanup_old_backups()
            except Exception as e:
                logger.warning(f"Failed to cleanup old backups: {e}")
```

---

## 6. Shared Telemetry System

### 6.1 Telemetry Module Structure

```python
"""
Shared telemetry system for both CLI and Power tools.

Collects usage metrics, performance data, and error information
for both interfaces in a unified format.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import logging
import uuid
import os

logger = logging.getLogger(__name__)


class TelemetryLevel(Enum):
    """Telemetry collection levels."""
    NONE = "none"       # No telemetry
    BASIC = "basic"     # Usage only (workflow type, success/failure)
    DETAILED = "detailed"  # Plus performance metrics
    FULL = "full"       # Plus error details and context


class InterfaceType(Enum):
    """Type of interface collecting telemetry."""
    CLI = "cli"
    POWER = "power"
    TEST = "test"


@dataclass
class TelemetryEvent:
    """A single telemetry event."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_type: str = ""
    workflow_type: Optional[str] = None
    interface_type: InterfaceType = InterfaceType.CLI
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    result_status: Optional[str] = None
    execution_time_seconds: float = 0.0
    memory_usage_mb: Optional[float] = None
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_validated: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    error_recoverable: bool = True
    additional_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        # Convert enum values
        data["interface_type"] = self.interface_type.value
        return data
    
    @classmethod
    def from_execution_result(
        cls,
        result: "ExecutionResult",
        interface_type: InterfaceType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> "TelemetryEvent":
        """Create telemetry event from execution result."""
        event = cls(
            event_type=f"workflow_{result.workflow_type.value}_complete",
            workflow_type=result.workflow_type.value,
            interface_type=interface_type,
            user_id=user_id,
            session_id=session_id,
            result_status=result.status.value,
            execution_time_seconds=result.execution_time_seconds,
            files_created=result.files_created,
            files_modified=result.files_modified,
            files_validated=result.files_validated,
        )
        
        if result.errors:
            event.error_type = result.errors[0].get("type", "unknown")
            event.error_message = result.errors[0].get("message", "Unknown error")
            event.error_recoverable = result.errors[0].get("recoverable", True)
        
        return event


class TelemetryCollector:
    """
    Collects and stores telemetry data.
    
    Features:
    - Unified format for CLI and Power
    - Local storage in .kiro/.telemetry/
    - Privacy-respecting (no PII by default)
    - Configurable collection level
    """
    
    def __init__(
        self,
        telemetry_dir: Optional[Path] = None,
        level: TelemetryLevel = TelemetryLevel.DETAILED,
        user_id: Optional[str] = None,
    ):
        """
        Initialize telemetry collector.
        
        Args:
            telemetry_dir: Directory for telemetry storage
            level: Collection level
            user_id: Optional user identifier
        """
        self.telemetry_dir = telemetry_dir or Path(".kiro/.telemetry")
        self.level = level
        self.user_id = user_id
        self.session_id = str(uuid.uuid4())
        
        # Ensure telemetry directory exists
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session events
        self._events: List[TelemetryEvent] = []
    
    def collect(
        self,
        workflow_type: "WorkflowType",
        interface_type: InterfaceType,
        parameters: Dict[str, Any],
        result: "ExecutionResult",
        execution_time: float,
        memory_usage: Optional[float] = None,
    ) -> str:
        """
        Collect telemetry for a workflow execution.
        
        Args:
            workflow_type: Type of workflow executed
            interface_type: Interface that executed the workflow
            parameters: Parameters passed to workflow
            result: Result of the execution
            execution_time: Time taken to execute
            memory_usage: Memory usage in MB
            
        Returns:
            Event ID of the collected telemetry
        """
        if self.level == TelemetryLevel.NONE:
            return ""
        
        # Create event
        event = TelemetryEvent(
            event_type=f"workflow_{workflow_type.value}_complete",
            workflow_type=workflow_type.value,
            interface_type=interface_type,
            user_id=self.user_id,
            session_id=self.session_id,
            parameters=self._sanitize_parameters(parameters),
            result_status=result.status.value,
            execution_time_seconds=execution_time,
            memory_usage_mb=memory_usage,
            files_created=result.files_created,
            files_modified=result.files_modified,
            files_validated=result.files_validated,
        )
        
        # Add error info if present
        if result.errors and self.level >= TelemetryLevel.DETAILED:
            event.error_type = result.errors[0].get("type")
            event.error_message = result.errors[0].get("message")
            event.error_recoverable = result.errors[0].get("recoverable", True)
        
        # Store event
        self._events.append(event)
        self._persist_event(event)
        
        return event.event_id
    
    def collect_custom(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Collect a custom telemetry event.
        
        Args:
            event_type: Type of event
            data: Additional event data
            
        Returns:
            Event ID of the collected telemetry
        """
        if self.level == TelemetryLevel.NONE:
            return ""
        
        event = TelemetryEvent(
            event_type=event_type,
            interface_type=InterfaceType.CLI,  # Default
            additional_data=data or {},
        )
        
        self._events.append(event)
        self._persist_event(event)
        
        return event.event_id
    
    def _sanitize_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters to remove sensitive data."""
        if self.level == TelemetryLevel.BASIC:
            # Only store parameter names, not values
            return {k: "<redacted>" for k in parameters.keys()}
        
        # Remove known sensitive fields
        sensitive_fields = {"api_key", "password", "token", "secret"}
        sanitized = {}
        
        for key, value in parameters.items():
            if any(s in key.lower() for s in sensitive_fields):
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _persist_event(self, event: TelemetryEvent) -> None:
        """Persist a telemetry event to disk."""
        try:
            # Create daily file
            date_str = datetime.now().strftime("%Y-%m-%d")
            file_path = self.telemetry_dir / f"telemetry_{date_str}.jsonl"
            
            # Append to file
            with open(file_path, "a") as f:
                f.write(json.dumps(event.to_dict()) + "\n")
                
        except Exception as e:
            logger.warning(f"Failed to persist telemetry event: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the current session."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self._events[0].timestamp if self._events else None,
            "end_time": self._events[-1].timestamp if self._events else None,
            "event_count": len(self._events),
            "workflow_types": list(set(e.workflow_type for e in self._events if e.workflow_type)),
            "success_count": sum(1 for e in self._events if e.result_status == "success"),
            "failure_count": sum(1 for e in self._events if e.result_status == "failed"),
            "total_execution_time": sum(e.execution_time_seconds for e in self._events),
        }
    
    def export_session(self, format: str = "json") -> str:
        """
        Export session telemetry data.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        if format == "json":
            return json.dumps(
                [e.to_dict() for e in self._events],
                indent=2,
            )
        elif format == "csv":
            if not self._events:
                return ""
            
            # Get all possible fields
            fields = set()
            for event in self._events:
                fields.update(event.to_dict().keys())
            
            # Build CSV
            lines = [",".join(sorted(fields))]
            for event in self._events:
                row = []
                for field in sorted(fields):
                    value = event.to_dict().get(field, "")
                    # Escape CSV values
                    if isinstance(value, str) and ("," in value or '"' in value):
                        value = f'"{value.replace("\"", "\"\"")}"'
                    row.append(str(value))
                lines.append(",".join(row))
            
            return "\n".join(lines)
        
        return ""
    
    def clear_session(self) -> None:
        """Clear current session data from memory."""
        self._events = []
        self.session_id = str(uuid.uuid4())


def get_telemetry_dir() -> Path:
    """Get the telemetry directory, creating it if needed."""
    telemetry_dir = Path(".kiro/.telemetry")
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    return telemetry_dir


def configure_telemetry(
    level: TelemetryLevel = TelemetryLevel.DETAILED,
    user_id: Optional[str] = None,
) -> TelemetryCollector:
    """
    Configure and return a telemetry collector.
    
    Args:
        level: Collection level
        user_id: Optional user identifier
        
    Returns:
        Configured TelemetryCollector
    """
    return TelemetryCollector(
        telemetry_dir=get_telemetry_dir(),
        level=level,
        user_id=user_id,
    )
```
---

## 7. CLI Adapter Interface

### 7.1 CLI Integration Pattern

```python
"""
CLI adapter for shared backend.

Provides typer-based CLI commands that use the shared backend
for all steering operations.
"""

from pathlib import Path
from typing import Optional
import typer
from typing_extensions import Annotated

from .shared.executor import (
    SharedWorkflowExecutor,
    WorkflowType,
    InterfaceType,
    ExecutionResult,
)
from .shared.security import SecurityWrapper

app = typer.Typer(
    name="steering",
    help="Steering file management commands",
    add_completion=False,
)


def get_executor() -> SharedWorkflowExecutor:
    """Get a shared workflow executor for CLI use."""
    return SharedWorkflowExecutor(
        project_root=Path("."),
        interface_type=InterfaceType.CLI,
        enable_telemetry=True,
        enable_security=True,
    )


@app.command("init")
def steering_init(
    project_root: Annotated[
        Optional[str],
        typer.Option("--project-root", "-p", help="Project root directory"),
    ] = ".",
    auto_discover: Annotated[
        bool,
        typer.Option("--analyze-code/--no-analyze-code", "-a", help="Analyze project code"),
    ] = True,
    autonomous: Annotated[
        bool,
        typer.Option("--autonomous/--interactive", help="Run in autonomous mode"),
    ] = True,
    confidence_threshold: Annotated[
        float,
        typer.Option("--confidence", "-c", help="Confidence threshold (0.0-1.0)"),
    ] = 0.7,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (text, json)"),
    ] = "text",
) -> None:
    """
    Initialize steering files for a project.
    
    Examples:
        hiveforge steering init
        hiveforge steering init --autonomous
        hiveforge steering init --confidence 0.8
    """
    executor = get_executor()
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.INIT,
        parameters={
            "project_root": project_root,
            "auto_discover": auto_discover,
            "autonomous": autonomous,
            "confidence_threshold": confidence_threshold,
        },
    )
    
    if output_format == "json":
        typer.echo(result.to_dict())
    else:
        typer.echo(result.format_for_cli())
    
    raise typer.Exit(code=0 if result.status.value == "success" else 1)


@app.command("update")
def steering_update(
    project_root: Annotated[
        Optional[str],
        typer.Option("--project-root", "-p", help="Project root directory"),
    ] = ".",
    files: Annotated[
        Optional[str],
        typer.Option("--files", "-F", help="Comma-separated files to update"),
    ] = None,
    preserve_customizations: Annotated[
        bool,
        typer.Option(
            "--preserve/--overwrite",
            "-P",
            help="Preserve existing customizations",
        ),
    ] = True,
    incremental: Annotated[
        bool,
        typer.Option("--incremental/--full", help="Incremental update"),
    ] = True,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (text, json)"),
    ] = "text",
) -> None:
    """
    Update existing steering files.
    
    Examples:
        hiveforge steering update
        hiveforge steering update --files tech-stack.md,architecture.md
        hiveforge steering update --incremental
    """
    executor = get_executor()
    
    file_list = [f.strip() for f in files.split(",")] if files else None
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.UPDATE,
        parameters={
            "project_root": project_root,
            "files": file_list,
            "preserve_customizations": preserve_customizations,
            "incremental": incremental,
        },
    )
    
    if output_format == "json":
        typer.echo(result.to_dict())
    else:
        typer.echo(result.format_for_cli())
    
    raise typer.Exit(code=0 if result.status.value == "success" else 1)


@app.command("validate")
def steering_validate(
    project_root: Annotated[
        Optional[str],
        typer.Option("--project-root", "-p", help="Project root directory"),
    ] = ".",
    strict: Annotated[
        bool,
        typer.Option("--strict", "-s", help="Treat warnings as errors"),
    ] = False,
    use_llm: Annotated[
        bool,
        typer.Option("--llm/--no-llm", help="Use LLM for semantic validation"),
    ] = True,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (text, json)"),
    ] = "text",
) -> None:
    """
    Validate steering files.
    
    Examples:
        hiveforge steering validate
        hiveforge steering validate --strict
        hiveforge steering validate --no-llm
    """
    executor = get_executor()
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.VALIDATE,
        parameters={
            "project_root": project_root,
            "strict": strict,
            "use_llm": use_llm,
        },
    )
    
    if output_format == "json":
        typer.echo(result.to_dict())
    else:
        typer.echo(result.format_for_cli())
    
    raise typer.Exit(code=0 if result.status.value == "success" else 1)


@app.command("reset")
def steering_reset(
    project_root: Annotated[
        Optional[str],
        typer.Option("--project-root", "-p", help="Project root directory"),
    ] = ".",
    file: Annotated[
        Optional[str],
        typer.Option("--file", "-F", help="Specific file to reset"),
    ] = None,
    confirm: Annotated[
        bool,
        typer.Option("--confirm", "-y", help="Skip confirmation prompt"),
    ] = False,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (text, json)"),
    ] = "text",
) -> None:
    """
    Reset steering files to default templates.
    
    Examples:
        hiveforge steering reset
        hiveforge steering reset --file tech-stack.md --confirm
    """
    executor = get_executor()
    
    if not confirm and file is None:
        if not typer.confirm("Reset ALL steering files to defaults?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.RESET,
        parameters={
            "project_root": project_root,
            "file": file,
            "confirm": confirm,
        },
    )
    
    if output_format == "json":
        typer.echo(result.to_dict())
    else:
        typer.echo(result.format_for_cli())
    
    raise typer.Exit(code=0 if result.status.value == "success" else 1)


@app.command("discover")
def steering_discover(
    project_root: Annotated[
        Optional[str],
        typer.Option("--project-root", "-p", help="Project root directory"),
    ] = ".",
    include_git: Annotated[
        bool,
        typer.Option("--git/--no-git", help="Include git history analysis"),
    ] = False,
    output_format: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format (text, json)"),
    ] = "text",
) -> None:
    """
    Discover project documentation.
    
    Examples:
        hiveforge steering discover
        hiveforge steering discover --git
    """
    executor = get_executor()
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.DISCOVER,
        parameters={
            "project_root": project_root,
            "include_git_history": include_git,
        },
    )
    
    if output_format == "json":
        typer.echo(result.to_dict())
    else:
        typer.echo(result.format_for_cli())
    
    raise typer.Exit(code=0 if result.status.value == "success" else 1)


@app.command("rollback")
def steering_rollback(
    list_only: Annotated[
        bool,
        typer.Option("--list", "-l", help="List available backups"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show what would be restored"),
    ] = False,
) -> None:
    """
    Rollback to a previous backup.
    
    Examples:
        hiveforge steering rollback --list
        hiveforge steering rollback --dry-run
    """
    from .backup_manager import BackupManager
    
    backup_mgr = BackupManager()
    backups = backup_mgr.list_backups()
    
    if not backups:
        typer.echo("No backups available.")
        raise typer.Exit(0)
    
    if list_only:
        typer.echo("Available backups:")
        for i, backup in enumerate(backups, 1):
            typer.echo(
                f"  {i}. {backup['name']} - "
                f"{backup['file_count']} files - "
                f"{backup['timestamp'].strftime('%Y-%m-%d %H:%M')}"
            )
        return
    
    # Interactive selection
    typer.echo("Select backup to restore:")
    for i, backup in enumerate(backups, 1):
        typer.echo(
            f"  {i}. {backup['name']} - "
            f"{backup['file_count']} files - "
            f"{backup['timestamp'].strftime('%Y-%m-%d %H:%M')}"
        )
    
    selection = typer.prompt("Enter backup number", type=int)
    
    if not 1 <= selection <= len(backups):
        typer.echo("Invalid selection.")
        raise typer.Exit(1)
    
    selected_backup = backups[selection - 1]
    
    if dry_run:
        typer.echo(f"Dry run: Would restore from {selected_backup['name']}")
        return
    
    if not typer.confirm(f"Restore from {selected_backup['name']}?"):
        typer.echo("Cancelled.")
        raise typer.Exit(0)
    
    # Restore
    steering_dir = Path(".kiro/steering")
    restored = backup_mgr.restore_backup(selected_backup["path"], steering_dir)
    
    typer.echo(f"Restored {len(restored)} files from {selected_backup['name']}")


def main() -> None:
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
```

---

## 8. Power Tool Adapter Interface

### 8.1 MCP Tool Integration Pattern

```python
"""
MCP Power tool adapters for shared backend.

Provides FastMCP tool functions that use the shared backend
for all steering operations.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import logging

from fastmcp import FastMCP

from .shared.executor import (
    SharedWorkflowExecutor,
    WorkflowType,
    InterfaceType,
    ExecutionResult,
)
from .shared.security import SecurityWrapper

logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("hiveforge-steering")

# Global executor instance (created on first tool call)
_executor: Optional[SharedWorkflowExecutor] = None


def get_executor() -> SharedWorkflowExecutor:
    """Get or create the shared workflow executor."""
    global _executor
    if _executor is None:
        _executor = SharedWorkflowExecutor(
            project_root=Path("."),
            interface_type=InterfaceType.POWER,
            enable_telemetry=True,
            enable_security=True,
        )
    return _executor


@mcp.tool()
async def init_steering(
    auto_discover: bool = True,
    autonomous: bool = True,
    project_root: str = ".",
    confidence_threshold: float = 0.7,
) -> Dict[str, Any]:
    """
    Initialize steering files with autonomous generation.
    
    Args:
        auto_discover: Analyze project code and documentation
        autonomous: Generate without user interaction
        project_root: Project root directory
        confidence_threshold: Minimum confidence for autonomous generation
        
    Returns:
        Structured result with status, files created, and confidence scores
    """
    executor = get_executor()
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.INIT,
        parameters={
            "auto_discover": auto_discover,
            "autonomous": autonomous,
            "project_root": project_root,
            "confidence_threshold": confidence_threshold,
        },
    )
    
    return result.to_dict()


@mcp.tool()
async def update_steering(
    files: Optional[list[str]] = None,
    preserve_customizations: bool = True,
    incremental: bool = True,
    project_root: str = ".",
) -> Dict[str, Any]:
    """
    Update existing steering files with new information.
    
    Args:
        files: Specific files to update (None = all files)
        preserve_customizations: Keep user customizations
        incremental: Only update changed sections
        project_root: Project root directory
        
    Returns:
        Structured result with status, files modified, and conflicts
    """
    executor = get_executor()
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.UPDATE,
        parameters={
            "files": files,
            "preserve_customizations": preserve_customizations,
            "incremental": incremental,
            "project_root": project_root,
        },
    )
    
    return result.to_dict()


@mcp.tool()
async def validate_steering(
    strict: bool = False,
    use_llm: bool = True,
    project_root: str = ".",
) -> Dict[str, Any]:
    """
    Validate steering files for completeness and consistency.
    
    Args:
        strict: Treat warnings as errors
        use_llm: Enable semantic validation
        project_root: Project root directory
        
    Returns:
        Structured result with validation status and any issues
    """
    executor = get_executor()
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.VALIDATE,
        parameters={
            "strict": strict,
            "use_llm": use_llm,
            "project_root": project_root,
        },
    )
    
    return result.to_dict()


@mcp.tool()
async def reset_steering(
    file: Optional[str] = None,
    confirm: bool = False,
    project_root: str = ".",
) -> Dict[str, Any]:
    """
    Reset steering files to default templates.
    
    Args:
        file: Specific file to reset (None = all files)
        confirm: Skip confirmation prompt
        project_root: Project root directory
        
    Returns:
        Structured result with status and backup information
    """
    executor = get_executor()
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.RESET,
        parameters={
            "file": file,
            "confirm": confirm,
            "project_root": project_root,
        },
    )
    
    return result.to_dict()


@mcp.tool()
async def discover_project_docs(
    project_root: str = ".",
    include_git_history: bool = False,
) -> Dict[str, Any]:
    """
    Discover existing project documentation.
    
    Args:
        project_root: Project root directory
        include_git_history: Analyze git commits and PRs
        
    Returns:
        Structured result with discovered documents and relevance scores
    """
    executor = get_executor()
    
    result = executor.execute_workflow(
        workflow_type=WorkflowType.DISCOVER,
        parameters={
            "project_root": project_root,
            "include_git_history": include_git_history,
        },
    )
    
    return result.to_dict()


def run_server() -> None:
    """Run the MCP server."""
    mcp.run()
```

---

## 9. Integration Points

### 9.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         KIRO Orchestrator                                │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Keyword Detection: "steering", "documentation", "onboarding"    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Power Activation: HiveForge Steering Power                       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Tool Discovery: MCP protocol tool enumeration                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│         ┌──────────────────────────┼──────────────────────────┐         │
│         ▼                          ▼                          ▼         │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐     │
│  │ init_steering│         │update_steering│         │validate_steering│  │
│  └─────────────┘          └─────────────┘          └─────────────┘     │
│         │                          │                          │         │
│         └──────────────────────────┼──────────────────────────┘         │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Shared Backend (Single Source of Truth)              │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │
│  │  │   Security  │ │   Error     │ │  Telemetry  │ │  Workflow   │ │   │
│  │  │  Wrappers   │ │  Handling   │ │   System    │ │  Adapters   │ │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    ▼                                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    v02 Workflows                                   │   │
│  │  (InitWorkflow, UpdateWorkflow, ValidateWorkflow, etc.)           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 CLI Integration Points

```python
# CLI integration is direct - no middleware required

from hiveforge.steering.cli import app

# CLI commands are registered directly with typer
# Each command calls SharedWorkflowExecutor.execute_workflow()
# Results are formatted for terminal output

# Usage:
# $ hiveforge steering init --autonomous
# $ hiveforge steering update --files tech-stack.md
# $ hiveforge steering validate --strict
```

### 9.3 Power Integration Points

```python
# Power integration via FastMCP

from hiveforge.steering.mcp_server import mcp, run_server

# MCP tools are decorated with @mcp.tool()
# Each tool calls SharedWorkflowExecutor.execute_workflow()
# Results are automatically serialized to JSON for MCP protocol

# Usage (via KIRO Orchestrator):
# 1. User mentions "steering" keyword
# 2. Orchestrator activates HiveForge Power
# 3. Orchestrator discovers tools via MCP
# 4. Orchestrator calls init_steering(auto_discover=True)
# 5. Result returned to orchestrator for presentation
```

### 9.4 v02 Workflow Integration

```python
# v02 workflows are wrapped by adapters

from hiveforge.steering.shared.adapters import (
    InitAdapter,
    UpdateAdapter,
    ValidateAdapter,
)

# Each adapter:
# 1. Converts shared backend parameters to v02 format
# 2. Creates v02 workflow instance
# 3. Executes v02 workflow
# 4. Converts v02 result to shared backend format

# Example: InitAdapter
class InitAdapter(BaseWorkflowAdapter):
    def execute(self, context):
        # Convert parameters
        config = SteeringConfig(
            interactive=not self.config.autonomous,
            feature_flags=FeatureFlagConfig(
                use_autonomous_generation=self.config.autonomous,
                confidence_threshold=self.config.confidence_threshold,
            ),
        )
        
        # Create v02 workflow
        workflow = InitWorkflow(
            config=config,
            project_root=context.project_root,
        )
        
        # Execute
        success = workflow.execute()
        
        # Convert result
        return ExecutionResult(
            status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
            files_created=workflow.state.generated_files,
            ...
        )
```

### 9.5 Telemetry Integration

```python
# Telemetry is collected automatically by SharedWorkflowExecutor

from hiveforge.steering.shared.telemetry import (
    TelemetryCollector,
    TelemetryLevel,
)

# Configure telemetry
collector = TelemetryCollector(
    level=TelemetryLevel.DETAILED,
    user_id="user123",
)

# Events are automatically collected
# Stored in .kiro/.telemetry/telemetry_YYYY-MM-DD.jsonl

# Export session data
summary = collector.get_session_summary()
export = collector.export_session(format="json")
```

### 9.6 Error Handling Integration

```python
# Error handling is built into SharedWorkflowExecutor

from hiveforge.steering.shared.error_handling import (
    ToolExecutor,
    ErrorHandler,
)

# ToolExecutor provides error handling wrapper
executor = ToolExecutor(
    auto_backup=True,
    auto_rollback=True,
)

result = executor.execute(
    operation=my_workflow.execute,
    files_to_backup=[file1, file2],
    on_success=lambda r: format_result(r),
    on_error=lambda e: handle_error(e),
)

# On error:
# 1. Error is categorized and logged
# 2. Backup is created if not already
# 3. Files are restored from backup
# 4. User-friendly error is returned
```

---

## 10. Usage Examples

### 10.1 CLI Usage

```bash
# Initialize steering files
hiveforge steering init

# Initialize with autonomous generation
hiveforge steering init --autonomous

# Update specific files
hiveforge steering update --files tech-stack.md,architecture.md

# Validate with strict mode
hiveforge steering validate --strict

# Reset to defaults (with confirmation)
hiveforge steering reset --file tech-stack.md --confirm

# Discover project documentation
hiveforge steering discover --git

# List available backups
hiveforge steering rollback --list

# JSON output for scripting
hiveforge steering init --format json
```

### 10.2 Power Tool Usage (via Orchestrator)

```python
# Via KIRO Orchestrator - natural language

user: "Generate steering files for my project"

# Orchestrator:
# 1. Detects "steering" keyword
# 2. Activates HiveForge Power
# 3. Calls init_steering(auto_discover=True, autonomous=True)
# 4. Returns result to user

# Direct tool call (if using MCP directly)
import mcp

client = mcp.Client("hiveforge-steering")
result = await client.call_tool("init_steering", {
    "auto_discover": True,
    "autonomous": True,
    "confidence_threshold": 0.7,
})
```

### 10.3 Programmatic Usage

```python
from pathlib import Path
from hiveforge.steering.shared.executor import (
    SharedWorkflowExecutor,
    WorkflowType,
    InterfaceType,
)

# Create executor
executor = SharedWorkflowExecutor(
    project_root=Path("/path/to/project"),
    interface_type=InterfaceType.CLI,
    enable_telemetry=True,
    enable_security=True,
)

# Execute init workflow
result = executor.execute_workflow(
    workflow_type=WorkflowType.INIT,
    parameters={
        "auto_discover": True,
        "autonomous": True,
        "confidence_threshold": 0.7,
    },
)

# Check result
if result.status.value == "success":
    print(f"Created {len(result.files_created)} files")
    for file in result.files_created:
        print(f"  - {file}")
else:
    print(f"Failed: {result.message}")
    for error in result.errors:
        print(f"  - {error.get('message')}")
```

### 10.4 Custom Adapter Usage

```python
from hiveforge.steering.shared.adapters import InitAdapter
from hiveforge.steering.shared.base import WorkflowConfig

# Create custom configuration
config = WorkflowConfig(
    auto_discover=True,
    autonomous=False,  # Interactive mode
    confidence_threshold=0.8,
)

# Create adapter
adapter = InitAdapter(config=config)

# Execute
from hiveforge.steering.shared.executor import ExecutionContext
context = ExecutionContext(
    project_root=Path("/path/to/project"),
    workflow_type=WorkflowType.INIT,
    interface_type=InterfaceType.CLI,
)

result = adapter.execute(context)
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# tests/test_shared_backend.py

import pytest
from pathlib import Path
from hiveforge.steering.shared.executor import (
    SharedWorkflowExecutor,
    WorkflowType,
    InterfaceType,
    ExecutionStatus,
)
from hiveforge.steering.shared.adapters import InitAdapter
from hiveforge.steering.shared.security import SecurityWrapper, InputValidator


class TestSecurityWrapper:
    def test_validate_parameters_valid(self):
        """Test valid parameter validation."""
        wrapper = SecurityWrapper()
        result = wrapper.validate_parameters({
            "project_root": ".",
            "auto_discover": True,
            "confidence_threshold": 0.7,
        })
        assert result["project_root"] == "."
        assert result["auto_discover"] is True
    
    def test_validate_parameters_invalid(self):
        """Test invalid parameter validation."""
        wrapper = SecurityWrapper()
        with pytest.raises(Exception):
            wrapper.validate_parameters({
                "unknown_param": "value",
            })
    
    def test_path_traversal_prevention(self):
        """Test path traversal prevention."""
        wrapper = SecurityWrapper()
        with pytest.raises(Exception):
            wrapper.validate_parameters({
                "project_root": "../../../etc/passwd",
            })


class TestAdapters:
    def test_init_adapter_parameters(self):
        """Test init adapter parameter validation."""
        adapter = InitAdapter()
        validated = adapter.validate_parameters({
            "autonomous": True,
            "confidence_threshold": 0.8,
        })
        assert validated["autonomous"] is True
        assert validated["confidence_threshold"] == 0.8
    
    def test_init_adapter_invalid_confidence(self):
        """Test init adapter rejects invalid confidence."""
        adapter = InitAdapter()
        with pytest.raises(Exception):
            adapter.validate_parameters({
                "confidence_threshold": 1.5,
            })


class TestExecutor:
    def test_execute_workflow_success(self):
        """Test successful workflow execution."""
        executor = SharedWorkflowExecutor(
            project_root=Path("tests/fixtures/minimal_project"),
            interface_type=InterfaceType.TEST,
            enable_telemetry=False,
            enable_security=False,
        )
        
        result = executor.execute_workflow(
            workflow_type=WorkflowType.DISCOVER,
            parameters={},
        )
        
        # Should succeed or partial (depending on fixture)
        assert result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.PARTIAL]
```

### 11.2 Integration Tests

```python
# tests/test_cli_power_equivalence.py

import pytest
import subprocess
import json
from pathlib import Path
from hiveforge.steering.mcp_server import mcp
from hiveforge.steering.shared.executor import (
    SharedWorkflowExecutor,
    WorkflowType,
    InterfaceType,
)


class TestCLIPowerEquivalence:
    """Test that CLI and Power produce identical results."""
    
    @pytest.fixture
    def test_project(self, tmp_path):
        """Create a test project."""
        # Create minimal project structure
        (tmp_path / "README.md").write_text("# Test Project")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        return tmp_path
    
    def test_discover_equivalence(self, test_project):
        """Test discover produces same results via CLI and Power."""
        # CLI result
        cli_result = subprocess.run(
            [
                "hiveforge", "steering", "discover",
                "--project-root", str(test_project),
                "--format", "json",
            ],
            capture_output=True,
            text=True,
        )
        cli_data = json.loads(cli_result.stdout)
        
        # Power result (via shared backend)
        executor = SharedWorkflowExecutor(
            project_root=test_project,
            interface_type=InterfaceType.TEST,
            enable_telemetry=False,
            enable_security=False,
        )
        power_result = executor.execute_workflow(
            workflow_type=WorkflowType.DISCOVER,
            parameters={},
        )
        power_data = power_result.to_dict()
        
        # Compare key fields
        assert cli_data["status"] == power_data["status"]
        assert cli_data["message"] == power_data["message"]
```

---

## 12. Migration Guide

### 12.1 From v02 to Shared Backend

**For CLI Users:**
- No changes required - CLI commands work exactly as before
- New `--format json` option for programmatic use
- New `--project-root` option for non-current directories

**For Power Users:**
- Power tools now use the same backend as CLI
- Identical behavior between CLI and Power
- Improved error messages and rollback

**For Developers:**
- Use `SharedWorkflowExecutor` for new tools
- Implement `WorkflowAdapter` for new workflows
- Use `ToolExecutor` for error handling wrapper

### 12.2 Backward Compatibility

All existing CLI commands continue to work:
- `hiveforge steering init` → Uses `InitAdapter`
- `hiveforge steering update` → Uses `UpdateAdapter`
- `hiveforge steering validate` → Uses `ValidateAdapter`
- `hiveforge steering rollback` → Uses `BackupManager`

All parameters are preserved:
- `--analyze-code` / `--no-analyze-code`
- `--autonomous` / `--interactive`
- `--confidence` / `-c`
- `--strict` / `-s`
- `--preserve` / `-P`

---

## 13. References

- **Requirements**: `.kiro/specs/steering-power-conversion/requirements.md`
- **Design**: `.kiro/specs/steering-power-conversion/design.md`
- **Tasks**: `.kiro/specs/steering-power-conversion/tasks.md`
- **v02 Code**: `src/hiveforge/steering/workflows/`
- **CLI Code**: `src/hiveforge/steering/cli.py`
- **Error Handling**: `src/hiveforge/steering/error_handling.py`
- **Backup Manager**: `src/hiveforge/steering/backup_manager.py`

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Draft - Ready for Review