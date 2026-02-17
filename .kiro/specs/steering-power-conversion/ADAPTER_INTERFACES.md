# Adapter Interface Specifications

**Feature**: steering-power-conversion  
**Version**: 2.0.0  
**Status**: Complete  
**Phase**: 1.4 - Shared Backend Interface Design

---

## 1. Overview

This document defines the adapter interfaces that bridge the shared backend with CLI and Power tool interfaces. Adapters handle:

- Parameter parsing and normalization
- Progress reporting
- Result formatting
- Error presentation

---

## 2. Adapter Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Layer                           │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │   CLI Interface      │    │  Power Tool Interface│      │
│  │   (typer commands)   │    │   (FastMCP tools)    │      │
│  └──────────────────────┘    └──────────────────────┘      │
│            │                            │                    │
│            ▼                            ▼                    │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │    CLIAdapter        │    │   PowerAdapter       │      │
│  │  - Parse CLI args    │    │  - Parse MCP params  │      │
│  │  - Format terminal   │    │  - Format JSON       │      │
│  │  - Show progress     │    │  - Stream progress   │      │
│  └──────────────────────┘    └──────────────────────┘      │
│            │                            │                    │
│            └────────────┬───────────────┘                    │
│                         ▼                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Shared Backend Layer                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           SharedWorkflowBase                         │   │
│  │  - Business logic only                               │   │
│  │  - Returns structured data                           │   │
│  │  - Accepts progress callbacks                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Base Adapter Interface

### 3.1 BaseAdapter Protocol

```python
"""
Base adapter protocol for interface implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional
from pathlib import Path


class BaseAdapter(ABC):
    """
    Base adapter for interface implementations.
    
    Adapters bridge the gap between shared workflows and
    interface-specific presentation. They handle:
    - Progress callback creation
    - Result formatting
    - Error presentation
    - Parameter normalization
    """
    
    @abstractmethod
    def create_progress_callback(self) -> Callable[[str, str, Optional[int]], None]:
        """
        Create a progress callback for this interface.
        
        Returns:
            Callback function(step, message, percentage)
            
        Example:
            callback = adapter.create_progress_callback()
            callback("init", "Starting workflow", 0)
            callback("parse", "Parsing artifacts", 50)
            callback("complete", "Workflow complete", 100)
        """
        pass
    
    @abstractmethod
    def format_result(self, result: Dict[str, Any]) -> Any:
        """
        Format workflow result for this interface.
        
        Args:
            result: Structured result from shared workflow:
            {
                "status": "success" | "failed" | "aborted",
                "message": str,
                "data": dict,
                "errors": list,
                "warnings": list
            }
            
        Returns:
            Interface-specific formatted result
            - CLI: Formatted string for terminal output
            - Power: JSON dict for MCP response
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
    
    @abstractmethod
    def normalize_parameters(self, raw_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize interface-specific parameters to shared format.
        
        Args:
            raw_params: Raw parameters from interface
            
        Returns:
            Normalized parameters for shared workflow
        """
        pass
```

---

## 4. CLI Adapter Implementation

### 4.1 CLIAdapter Class

```python
"""
CLI adapter for terminal-based interface.
"""

from typing import Dict, Any, Callable, Optional
from pathlib import Path
import sys

from .base import BaseAdapter


class CLIAdapter(BaseAdapter):
    """
    Adapter for CLI interface.
    
    Handles:
    - Terminal progress display with spinners/bars
    - Colored output for success/error/warning
    - Human-readable error messages
    - Exit code management
    """
    
    def __init__(self, verbose: bool = False, color: bool = True):
        """
        Initialize CLI adapter.
        
        Args:
            verbose: Whether to show verbose output
            color: Whether to use colored output
        """
        self.verbose = verbose
        self.color = color
        self._progress_lines = []
    
    def create_progress_callback(self) -> Callable[[str, str, Optional[int]], None]:
        """
        Create progress callback for CLI.
        
        Returns:
            Callback that prints progress to terminal
        """
        def cli_progress(step: str, message: str, percentage: Optional[int]):
            """Display progress in terminal."""
            if percentage is not None:
                # Show progress bar
                bar_width = 40
                filled = int(bar_width * percentage / 100)
                bar = "█" * filled + "░" * (bar_width - filled)
                print(f"\r  [{bar}] {percentage:3d}% {message}", end="", flush=True)
                
                if percentage >= 100:
                    print()  # New line when complete
            else:
                # Show step message
                if self.verbose:
                    print(f"  • {message}")
        
        return cli_progress
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """
        Format result for CLI display.
        
        Args:
            result: Structured result from workflow
            
        Returns:
            Formatted string for terminal output
        """
        status = result["status"]
        message = result["message"]
        data = result.get("data", {})
        errors = result.get("errors", [])
        warnings = result.get("warnings", [])
        
        lines = []
        
        # Status line
        if status == "success":
            lines.append(self._colorize("✅ SUCCESS", "green"))
            lines.append(f"   {message}")
        elif status == "failed":
            lines.append(self._colorize("❌ FAILED", "red"))
            lines.append(f"   {message}")
        elif status == "aborted":
            lines.append(self._colorize("⚠️  ABORTED", "yellow"))
            lines.append(f"   {message}")
        
        # Data details
        if data:
            lines.append("")
            lines.append("Details:")
            
            if "files_created" in data:
                lines.append(f"  • Files created: {data['files_created']}")
            
            if "files_modified" in data:
                lines.append(f"  • Files modified: {len(data['files_modified'])}")
                if self.verbose and data['files_modified']:
                    for file in data['files_modified']:
                        lines.append(f"    - {file}")
            
            if "validation_report" in data:
                report = data['validation_report']
                lines.append(f"  • Validation: {report.get('status', 'unknown')}")
                if report.get('issues'):
                    lines.append(f"    - Issues: {len(report['issues'])}")
        
        # Warnings
        if warnings:
            lines.append("")
            lines.append(self._colorize("Warnings:", "yellow"))
            for warning in warnings:
                lines.append(f"  ⚠️  {warning}")
        
        # Errors
        if errors:
            lines.append("")
            lines.append(self._colorize("Errors:", "red"))
            for error in errors:
                lines.append(f"  ✗ {error}")
        
        return "\n".join(lines)
    
    def format_error(self, error: Exception) -> str:
        """
        Format error for CLI display.
        
        Args:
            error: Exception that occurred
            
        Returns:
            Formatted error string
        """
        lines = [
            self._colorize("❌ ERROR", "red"),
            f"   {str(error)}",
        ]
        
        if self.verbose:
            import traceback
            lines.append("")
            lines.append("Traceback:")
            lines.append(traceback.format_exc())
        
        return "\n".join(lines)
    
    def normalize_parameters(self, raw_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize CLI parameters to shared format.
        
        Args:
            raw_params: Raw CLI arguments
            
        Returns:
            Normalized parameters
        """
        # CLI uses underscores, shared backend uses consistent naming
        normalized = {}
        
        # Map CLI flags to shared parameters
        param_mapping = {
            "analyze_code": "auto_discover",
            "no_autonomous": lambda v: {"autonomous": not v},
            "confidence": "confidence_threshold",
            "project_root": "project_root",
            "files": "target_files",
            "strict": "strict",
            "use_llm": "use_llm",
        }
        
        for cli_param, shared_param in param_mapping.items():
            if cli_param in raw_params:
                value = raw_params[cli_param]
                
                if callable(shared_param):
                    # Custom mapping function
                    normalized.update(shared_param(value))
                else:
                    # Direct mapping
                    normalized[shared_param] = value
        
        return normalized
    
    def _colorize(self, text: str, color: str) -> str:
        """
        Colorize text for terminal output.
        
        Args:
            text: Text to colorize
            color: Color name (red, green, yellow, blue)
            
        Returns:
            Colorized text (or plain if color disabled)
        """
        if not self.color:
            return text
        
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "reset": "\033[0m",
        }
        
        color_code = colors.get(color, "")
        reset_code = colors["reset"]
        
        return f"{color_code}{text}{reset_code}"
    
    def get_exit_code(self, result: Dict[str, Any]) -> int:
        """
        Get exit code from result.
        
        Args:
            result: Workflow result
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        status = result["status"]
        
        if status == "success":
            return 0
        elif status == "aborted":
            return 2
        else:
            return 1
```

---

## 5. Power Adapter Implementation

### 5.1 PowerAdapter Class

```python
"""
Power adapter for MCP tool interface.
"""

from typing import Dict, Any, Callable, Optional
from pathlib import Path
import json

from .base import BaseAdapter


class PowerAdapter(BaseAdapter):
    """
    Adapter for Power tool interface.
    
    Handles:
    - JSON parameter parsing
    - Structured JSON responses
    - Progress streaming (optional)
    - MCP-compliant error formatting
    """
    
    def __init__(self, stream_progress: bool = False):
        """
        Initialize Power adapter.
        
        Args:
            stream_progress: Whether to stream progress updates
        """
        self.stream_progress = stream_progress
        self._progress_updates = []
    
    def create_progress_callback(self) -> Callable[[str, str, Optional[int]], None]:
        """
        Create progress callback for Power tools.
        
        Returns:
            Callback that collects progress updates
        """
        def power_progress(step: str, message: str, percentage: Optional[int]):
            """Collect progress updates for JSON response."""
            update = {
                "step": step,
                "message": message,
                "percentage": percentage,
            }
            self._progress_updates.append(update)
            
            # Optionally stream progress (for real-time updates)
            if self.stream_progress:
                # TODO: Implement streaming via MCP protocol
                pass
        
        return power_progress
    
    def format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format result for Power tool JSON response.
        
        Args:
            result: Structured result from workflow
            
        Returns:
            JSON-serializable dict for MCP response
        """
        status = result["status"]
        message = result["message"]
        data = result.get("data", {})
        errors = result.get("errors", [])
        warnings = result.get("warnings", [])
        
        # Build MCP-compliant response
        response = {
            "status": status,
            "message": message,
            "data": data,
            "progress": self._progress_updates,
        }
        
        # Add optional fields
        if errors:
            response["errors"] = errors
        
        if warnings:
            response["warnings"] = warnings
        
        # Add metadata
        response["metadata"] = {
            "interface": "power",
            "version": "2.0.0",
        }
        
        return response
    
    def format_error(self, error: Exception) -> Dict[str, Any]:
        """
        Format error for Power tool JSON response.
        
        Args:
            error: Exception that occurred
            
        Returns:
            JSON-serializable error dict
        """
        return {
            "status": "failed",
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
            "message": f"Operation failed: {str(error)}",
            "data": {},
            "progress": self._progress_updates,
        }
    
    def normalize_parameters(self, raw_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Power tool parameters to shared format.
        
        Args:
            raw_params: Raw MCP tool parameters
            
        Returns:
            Normalized parameters
        """
        # Power tools use camelCase, shared backend uses snake_case
        normalized = {}
        
        # Map MCP parameters to shared parameters
        param_mapping = {
            "autoDiscover": "auto_discover",
            "autonomous": "autonomous",
            "confidenceThreshold": "confidence_threshold",
            "projectRoot": "project_root",
            "files": "target_files",
            "strict": "strict",
            "useLlm": "use_llm",
            "preserveCustomizations": "preserve_customizations",
            "incremental": "incremental",
        }
        
        for mcp_param, shared_param in param_mapping.items():
            if mcp_param in raw_params:
                normalized[shared_param] = raw_params[mcp_param]
        
        return normalized
    
    def get_progress_updates(self) -> list:
        """
        Get collected progress updates.
        
        Returns:
            List of progress update dicts
        """
        return self._progress_updates.copy()
    
    def clear_progress(self) -> None:
        """Clear collected progress updates."""
        self._progress_updates = []
```

---

## 6. Usage Examples

### 6.1 CLI Usage

```python
# src/hiveforge/steering/cli.py

from pathlib import Path
from .shared import SharedInitWorkflow, CLIAdapter
from .models import SteeringConfig

def steering_init(
    analyze_code: bool = True,
    autonomous: bool = True,
    confidence: float = 0.7,
    project_root: str = ".",
):
    """CLI command for init workflow."""
    
    # Create adapter
    adapter = CLIAdapter(verbose=True, color=True)
    
    # Normalize CLI parameters
    params = adapter.normalize_parameters({
        "analyze_code": analyze_code,
        "no_autonomous": not autonomous,
        "confidence": confidence,
        "project_root": project_root,
    })
    
    # Create config
    config = SteeringConfig(**params)
    
    # Create workflow with progress callback
    workflow = SharedInitWorkflow(
        config=config,
        project_root=Path(project_root),
        progress_callback=adapter.create_progress_callback()
    )
    
    # Execute workflow
    result = workflow.execute()
    
    # Format and display result
    output = adapter.format_result(result)
    print(output)
    
    # Return exit code
    return adapter.get_exit_code(result)
```

### 6.2 Power Tool Usage

```python
# mcp-server/tools/init_steering.py

from fastmcp import FastMCP
from pathlib import Path
from src.hiveforge.steering.shared import SharedInitWorkflow, PowerAdapter
from src.hiveforge.steering.shared.security import secure_tool_execution
from src.hiveforge.steering.models import SteeringConfig

mcp = FastMCP("hiveforge-steering")

@mcp.tool()
@secure_tool_execution(
    max_memory_mb=512,
    max_cpu_time_sec=300,
    allowed_directories=["."]
)
async def init_steering(
    autoDiscover: bool = True,
    autonomous: bool = True,
    confidenceThreshold: float = 0.7,
    projectRoot: str = ".",
) -> dict:
    """Initialize steering files with autonomous generation."""
    
    # Create adapter
    adapter = PowerAdapter(stream_progress=False)
    
    # Normalize MCP parameters
    params = adapter.normalize_parameters({
        "autoDiscover": autoDiscover,
        "autonomous": autonomous,
        "confidenceThreshold": confidenceThreshold,
        "projectRoot": projectRoot,
    })
    
    # Create config
    config = SteeringConfig(**params)
    
    # Create workflow with progress callback
    workflow = SharedInitWorkflow(
        config=config,
        project_root=Path(projectRoot),
        progress_callback=adapter.create_progress_callback()
    )
    
    # Execute workflow
    result = workflow.execute()
    
    # Format and return JSON response
    return adapter.format_result(result)
```

---

## 7. Testing Adapters

### 7.1 CLI Adapter Tests

```python
# tests/shared/test_cli_adapter.py

def test_cli_adapter_progress_callback():
    """Test CLI progress callback."""
    adapter = CLIAdapter(verbose=True)
    callback = adapter.create_progress_callback()
    
    # Should not raise
    callback("init", "Starting", 0)
    callback("parse", "Parsing", 50)
    callback("complete", "Done", 100)

def test_cli_adapter_format_success():
    """Test CLI success formatting."""
    adapter = CLIAdapter(color=False)
    result = {
        "status": "success",
        "message": "Created 5 files",
        "data": {"files_created": 5},
        "errors": [],
        "warnings": []
    }
    
    output = adapter.format_result(result)
    assert "SUCCESS" in output
    assert "Created 5 files" in output

def test_cli_adapter_normalize_parameters():
    """Test CLI parameter normalization."""
    adapter = CLIAdapter()
    raw = {
        "analyze_code": True,
        "no_autonomous": False,
        "confidence": 0.8,
    }
    
    normalized = adapter.normalize_parameters(raw)
    assert normalized["auto_discover"] == True
    assert normalized["autonomous"] == True
    assert normalized["confidence_threshold"] == 0.8
```

### 7.2 Power Adapter Tests

```python
# tests/shared/test_power_adapter.py

def test_power_adapter_progress_callback():
    """Test Power progress callback."""
    adapter = PowerAdapter()
    callback = adapter.create_progress_callback()
    
    callback("init", "Starting", 0)
    callback("parse", "Parsing", 50)
    callback("complete", "Done", 100)
    
    updates = adapter.get_progress_updates()
    assert len(updates) == 3
    assert updates[0]["step"] == "init"
    assert updates[-1]["percentage"] == 100

def test_power_adapter_format_success():
    """Test Power success formatting."""
    adapter = PowerAdapter()
    result = {
        "status": "success",
        "message": "Created 5 files",
        "data": {"files_created": 5},
        "errors": [],
        "warnings": []
    }
    
    output = adapter.format_result(result)
    assert output["status"] == "success"
    assert output["data"]["files_created"] == 5
    assert "progress" in output

def test_power_adapter_normalize_parameters():
    """Test Power parameter normalization."""
    adapter = PowerAdapter()
    raw = {
        "autoDiscover": True,
        "autonomous": True,
        "confidenceThreshold": 0.8,
    }
    
    normalized = adapter.normalize_parameters(raw)
    assert normalized["auto_discover"] == True
    assert normalized["autonomous"] == True
    assert normalized["confidence_threshold"] == 0.8
```

---

## 8. Adapter Interface Contract

### 8.1 Required Methods

All adapters MUST implement:

| Method | Purpose | Input | Output |
|--------|---------|-------|--------|
| `create_progress_callback()` | Create progress callback | None | Callable[[str, str, Optional[int]], None] |
| `format_result()` | Format workflow result | Dict[str, Any] | Any (interface-specific) |
| `format_error()` | Format error | Exception | Any (interface-specific) |
| `normalize_parameters()` | Normalize parameters | Dict[str, Any] | Dict[str, Any] |

### 8.2 Optional Methods

Adapters MAY implement:

| Method | Purpose | Input | Output |
|--------|---------|-------|--------|
| `get_exit_code()` | Get exit code (CLI only) | Dict[str, Any] | int |
| `get_progress_updates()` | Get progress history (Power only) | None | list |
| `clear_progress()` | Clear progress history | None | None |

---

## 9. Success Criteria

- [ ] Both CLI and Power adapters implemented
- [ ] All required methods implemented
- [ ] Parameter normalization works correctly
- [ ] Progress callbacks work for both interfaces
- [ ] Result formatting produces correct output
- [ ] Error formatting is user-friendly
- [ ] All adapter tests pass
- [ ] CLI and Power use >95% shared code

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-17  
**Next Review**: Before Phase 3 implementation
