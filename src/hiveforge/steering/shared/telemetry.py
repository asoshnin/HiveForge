"""
Shared telemetry system for both CLI and Power tools.

Collects usage metrics, performance data, and error information
for both interfaces in a unified format.

**Validates: Requirements 1.18, 1.19**
"""

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Telemetry Enums
# ============================================================================

class TelemetryLevel(IntEnum):
    """Telemetry collection levels."""
    NONE = 0        # No telemetry
    BASIC = 1       # Usage only (workflow type, success/failure)
    DETAILED = 2    # Plus performance metrics
    FULL = 3        # Plus error details and context


from enum import Enum


class InterfaceType(Enum):
    """Type of interface collecting telemetry."""
    CLI = "cli"
    POWER = "power"
    TEST = "test"


# ============================================================================
# Telemetry Event
# ============================================================================

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


# ============================================================================
# Telemetry Collector
# ============================================================================

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
        if self.level != TelemetryLevel.NONE:
            self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        
        # Current session events
        self._events: List[TelemetryEvent] = []
    
    def collect_workflow_execution(
        self,
        workflow_type: str,
        interface_type: InterfaceType,
        parameters: Dict[str, Any],
        result_status: str,
        execution_time: float,
        files_created: Optional[List[str]] = None,
        files_modified: Optional[List[str]] = None,
        files_validated: Optional[List[str]] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        error_recoverable: bool = True,
        memory_usage: Optional[float] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Collect telemetry for a workflow execution.
        
        Args:
            workflow_type: Type of workflow executed
            interface_type: Interface that executed the workflow
            parameters: Parameters passed to workflow
            result_status: Status of the result (success, failed, etc.)
            execution_time: Time taken to execute
            files_created: List of files created
            files_modified: List of files modified
            files_validated: List of files validated
            error_type: Type of error if failed
            error_message: Error message if failed
            error_recoverable: Whether error is recoverable
            memory_usage: Memory usage in MB
            additional_data: Additional metadata (e.g., confidence scores, performance metrics)
            
        Returns:
            Event ID of the collected telemetry
        """
        if self.level == TelemetryLevel.NONE:
            return ""
        
        # Create event
        event = TelemetryEvent(
            event_type=f"workflow_{workflow_type}_complete",
            workflow_type=workflow_type,
            interface_type=interface_type,
            user_id=self.user_id,
            session_id=self.session_id,
            parameters=self._sanitize_parameters(parameters),
            result_status=result_status,
            execution_time_seconds=execution_time,
            memory_usage_mb=memory_usage,
            files_created=files_created or [],
            files_modified=files_modified or [],
            files_validated=files_validated or [],
            error_type=error_type,
            error_message=error_message if self.level >= TelemetryLevel.DETAILED else None,
            error_recoverable=error_recoverable,
            additional_data=additional_data or {},
        )
        
        # Store event
        self._events.append(event)
        self._persist_event(event)
        
        return event.event_id
    
    def collect_custom(
        self,
        event_type: str,
        interface_type: InterfaceType = InterfaceType.CLI,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Collect a custom telemetry event.
        
        Args:
            event_type: Type of event
            interface_type: Interface that triggered the event
            data: Additional event data
            
        Returns:
            Event ID of the collected telemetry
        """
        if self.level == TelemetryLevel.NONE:
            return ""
        
        event = TelemetryEvent(
            event_type=event_type,
            interface_type=interface_type,
            user_id=self.user_id,
            session_id=self.session_id,
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


# ============================================================================
# Telemetry Utilities
# ============================================================================

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
