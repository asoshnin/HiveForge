"""
Tests for shared telemetry system.

Tests telemetry collection, storage, and export functionality.
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.hiveforge.steering.shared.telemetry import (
    TelemetryCollector,
    TelemetryEvent,
    TelemetryLevel,
    InterfaceType,
    get_telemetry_dir,
    configure_telemetry,
)


class TestTelemetryEvent:
    """Test TelemetryEvent dataclass."""
    
    def test_event_creation(self):
        """Test creating a telemetry event."""
        event = TelemetryEvent(
            event_type="workflow_init_complete",
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            result_status="success",
            execution_time_seconds=1.5,
        )
        
        assert event.event_type == "workflow_init_complete"
        assert event.workflow_type == "init"
        assert event.interface_type == InterfaceType.CLI
        assert event.result_status == "success"
        assert event.execution_time_seconds == 1.5
        assert event.event_id  # Should be auto-generated
        assert event.timestamp  # Should be auto-generated
    
    def test_event_to_dict(self):
        """Test converting event to dictionary."""
        event = TelemetryEvent(
            event_type="workflow_init_complete",
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            result_status="success",
        )
        
        data = event.to_dict()
        
        assert isinstance(data, dict)
        assert data["event_type"] == "workflow_init_complete"
        assert data["workflow_type"] == "init"
        assert data["interface_type"] == "cli"  # Enum converted to value
        assert data["result_status"] == "success"


class TestTelemetryCollector:
    """Test TelemetryCollector class."""
    
    @pytest.fixture
    def temp_telemetry_dir(self):
        """Create a temporary telemetry directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def collector(self, temp_telemetry_dir):
        """Create a telemetry collector with temp directory."""
        return TelemetryCollector(
            telemetry_dir=temp_telemetry_dir,
            level=TelemetryLevel.DETAILED,
            user_id="test_user",
        )
    
    def test_collector_initialization(self, temp_telemetry_dir):
        """Test collector initialization."""
        collector = TelemetryCollector(
            telemetry_dir=temp_telemetry_dir,
            level=TelemetryLevel.DETAILED,
            user_id="test_user",
        )
        
        assert collector.telemetry_dir == temp_telemetry_dir
        assert collector.level == TelemetryLevel.DETAILED
        assert collector.user_id == "test_user"
        assert collector.session_id  # Should be auto-generated
        assert len(collector._events) == 0
        assert temp_telemetry_dir.exists()
    
    def test_collect_workflow_execution(self, collector, temp_telemetry_dir):
        """Test collecting workflow execution telemetry."""
        event_id = collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            parameters={"auto_discover": True, "autonomous": True},
            result_status="success",
            execution_time=1.5,
            files_created=[".kiro/steering/tech-stack.md"],
        )
        
        assert event_id  # Should return event ID
        assert len(collector._events) == 1
        
        event = collector._events[0]
        assert event.workflow_type == "init"
        assert event.interface_type == InterfaceType.CLI
        assert event.result_status == "success"
        assert event.execution_time_seconds == 1.5
        assert event.files_created == [".kiro/steering/tech-stack.md"]
        
        # Check file was persisted
        date_str = datetime.now().strftime("%Y-%m-%d")
        telemetry_file = temp_telemetry_dir / f"telemetry_{date_str}.jsonl"
        assert telemetry_file.exists()
        
        # Read and verify content
        with open(telemetry_file) as f:
            line = f.readline()
            data = json.loads(line)
            assert data["workflow_type"] == "init"
            assert data["result_status"] == "success"
    
    def test_collect_with_error(self, collector):
        """Test collecting telemetry with error information."""
        event_id = collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            parameters={"auto_discover": True},
            result_status="failed",
            execution_time=0.5,
            error_type="ValueError",
            error_message="Invalid configuration",
            error_recoverable=True,
        )
        
        assert event_id
        assert len(collector._events) == 1
        
        event = collector._events[0]
        assert event.result_status == "failed"
        assert event.error_type == "ValueError"
        assert event.error_message == "Invalid configuration"
        assert event.error_recoverable is True
    
    def test_collect_custom_event(self, collector):
        """Test collecting custom telemetry event."""
        event_id = collector.collect_custom(
            event_type="user_action",
            interface_type=InterfaceType.POWER,
            data={"action": "keyword_activation", "keyword": "steering"},
        )
        
        assert event_id
        assert len(collector._events) == 1
        
        event = collector._events[0]
        assert event.event_type == "user_action"
        assert event.interface_type == InterfaceType.POWER
        assert event.additional_data["action"] == "keyword_activation"
    
    def test_sanitize_parameters_basic_level(self, temp_telemetry_dir):
        """Test parameter sanitization at BASIC level."""
        collector = TelemetryCollector(
            telemetry_dir=temp_telemetry_dir,
            level=TelemetryLevel.BASIC,
        )
        
        params = {"auto_discover": True, "api_key": "secret123"}
        sanitized = collector._sanitize_parameters(params)
        
        # At BASIC level, all values should be redacted
        assert sanitized["auto_discover"] == "<redacted>"
        assert sanitized["api_key"] == "<redacted>"
    
    def test_sanitize_parameters_detailed_level(self, collector):
        """Test parameter sanitization at DETAILED level."""
        params = {
            "auto_discover": True,
            "api_key": "secret123",
            "password": "pass123",
            "token": "token123",
            "normal_param": "value",
        }
        
        sanitized = collector._sanitize_parameters(params)
        
        # Sensitive fields should be redacted
        assert sanitized["api_key"] == "<redacted>"
        assert sanitized["password"] == "<redacted>"
        assert sanitized["token"] == "<redacted>"
        
        # Normal fields should be preserved
        assert sanitized["auto_discover"] is True
        assert sanitized["normal_param"] == "value"
    
    def test_get_session_summary(self, collector):
        """Test getting session summary."""
        # Collect some events
        collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            parameters={},
            result_status="success",
            execution_time=1.0,
        )
        
        collector.collect_workflow_execution(
            workflow_type="update",
            interface_type=InterfaceType.CLI,
            parameters={},
            result_status="failed",
            execution_time=0.5,
        )
        
        summary = collector.get_session_summary()
        
        assert summary["session_id"] == collector.session_id
        assert summary["user_id"] == "test_user"
        assert summary["event_count"] == 2
        assert set(summary["workflow_types"]) == {"init", "update"}
        assert summary["success_count"] == 1
        assert summary["failure_count"] == 1
        assert summary["total_execution_time"] == 1.5
    
    def test_export_session_json(self, collector):
        """Test exporting session as JSON."""
        collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            parameters={"auto_discover": True},
            result_status="success",
            execution_time=1.0,
        )
        
        exported = collector.export_session(format="json")
        
        assert exported
        data = json.loads(exported)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["workflow_type"] == "init"
    
    def test_export_session_csv(self, collector):
        """Test exporting session as CSV."""
        collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            parameters={},
            result_status="success",
            execution_time=1.0,
        )
        
        exported = collector.export_session(format="csv")
        
        assert exported
        lines = exported.split("\n")
        assert len(lines) >= 2  # Header + at least one data row
        
        # Check header contains expected fields
        header = lines[0]
        assert "workflow_type" in header
        assert "result_status" in header
        assert "execution_time_seconds" in header
    
    def test_clear_session(self, collector):
        """Test clearing session data."""
        # Collect some events
        collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            parameters={},
            result_status="success",
            execution_time=1.0,
        )
        
        assert len(collector._events) == 1
        old_session_id = collector.session_id
        
        # Clear session
        collector.clear_session()
        
        assert len(collector._events) == 0
        assert collector.session_id != old_session_id  # New session ID
    
    def test_telemetry_disabled(self, temp_telemetry_dir):
        """Test that telemetry is disabled at NONE level."""
        collector = TelemetryCollector(
            telemetry_dir=temp_telemetry_dir,
            level=TelemetryLevel.NONE,
        )
        
        event_id = collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            parameters={},
            result_status="success",
            execution_time=1.0,
        )
        
        assert event_id == ""  # No event ID returned
        assert len(collector._events) == 0  # No events collected
    
    def test_persist_event_failure_handling(self, collector, temp_telemetry_dir):
        """Test that persist failures don't crash the collector."""
        # Make telemetry directory read-only to cause persist failure
        temp_telemetry_dir.chmod(0o444)
        
        try:
            # This should not raise an exception
            event_id = collector.collect_workflow_execution(
                workflow_type="init",
                interface_type=InterfaceType.CLI,
                parameters={},
                result_status="success",
                execution_time=1.0,
            )
            
            # Event should still be in memory
            assert event_id
            assert len(collector._events) == 1
        finally:
            # Restore permissions
            temp_telemetry_dir.chmod(0o755)


class TestTelemetryUtilities:
    """Test telemetry utility functions."""
    
    def test_get_telemetry_dir(self):
        """Test getting telemetry directory."""
        telemetry_dir = get_telemetry_dir()
        
        assert telemetry_dir == Path(".kiro/.telemetry")
        # Note: This creates the directory in the current working directory
        # In a real test, we'd use a temp directory
    
    def test_configure_telemetry(self):
        """Test configuring telemetry collector."""
        collector = configure_telemetry(
            level=TelemetryLevel.FULL,
            user_id="test_user",
        )
        
        assert isinstance(collector, TelemetryCollector)
        assert collector.level == TelemetryLevel.FULL
        assert collector.user_id == "test_user"


class TestTelemetryIntegration:
    """Integration tests for telemetry system."""
    
    @pytest.fixture
    def temp_telemetry_dir(self):
        """Create a temporary telemetry directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_multiple_workflows_same_session(self, temp_telemetry_dir):
        """Test collecting telemetry for multiple workflows in same session."""
        collector = TelemetryCollector(
            telemetry_dir=temp_telemetry_dir,
            level=TelemetryLevel.DETAILED,
            user_id="test_user",
        )
        
        # Collect multiple workflow executions
        workflows = ["init", "update", "validate"]
        for workflow in workflows:
            collector.collect_workflow_execution(
                workflow_type=workflow,
                interface_type=InterfaceType.CLI,
                parameters={},
                result_status="success",
                execution_time=1.0,
            )
        
        # Verify all events collected
        assert len(collector._events) == 3
        
        # Verify session summary
        summary = collector.get_session_summary()
        assert summary["event_count"] == 3
        assert set(summary["workflow_types"]) == set(workflows)
        
        # Verify all events persisted to same file
        date_str = datetime.now().strftime("%Y-%m-%d")
        telemetry_file = temp_telemetry_dir / f"telemetry_{date_str}.jsonl"
        assert telemetry_file.exists()
        
        with open(telemetry_file) as f:
            lines = f.readlines()
            assert len(lines) == 3
    
    def test_cli_vs_power_telemetry(self, temp_telemetry_dir):
        """Test telemetry collection from both CLI and Power interfaces."""
        collector = TelemetryCollector(
            telemetry_dir=temp_telemetry_dir,
            level=TelemetryLevel.DETAILED,
        )
        
        # Collect from CLI
        collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.CLI,
            parameters={},
            result_status="success",
            execution_time=1.0,
        )
        
        # Collect from Power
        collector.collect_workflow_execution(
            workflow_type="init",
            interface_type=InterfaceType.POWER,
            parameters={},
            result_status="success",
            execution_time=1.2,
        )
        
        # Verify both interfaces tracked
        assert len(collector._events) == 2
        assert collector._events[0].interface_type == InterfaceType.CLI
        assert collector._events[1].interface_type == InterfaceType.POWER
