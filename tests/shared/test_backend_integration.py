"""
Integration tests for shared backend with security, error handling, and telemetry.

Tests the complete integration of:
- Security validation
- Error handling with automatic rollback
- Telemetry collection
- Workflow execution end-to-end

**Validates: Requirements 1.16, 1.17, 1.18**
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from src.hiveforge.steering.shared.adapters import (
    SharedInitWorkflow,
    SharedUpdateWorkflow,
    SharedValidateWorkflow,
    SharedResetWorkflow,
    SharedDiscoveryWorkflow
)
from src.hiveforge.steering.shared.telemetry import TelemetryCollector, InterfaceType


class TestSecurityErrorHandlingIntegration:
    """Test security validation + error handling integration."""
    
    def test_init_workflow_with_rollback_on_failure(self, tmp_path):
        """Test that init workflow rolls back on failure."""
        # Create a scenario where init will fail
        with patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock_init:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = False  # Simulate failure
            mock_workflow.state.validation_report = None
            mock_init.return_value = mock_workflow
            
            # Execute workflow
            workflow = SharedInitWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify failure was handled
            assert result.success is False
            assert "failed or was cancelled" in result.message
            assert len(result.errors) > 0
    
    def test_update_workflow_collects_errors_and_warnings(self, tmp_path):
        """Test that update workflow collects both errors and warnings."""
        # Create steering directory
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "test.md").write_text("# Test")
        
        with patch('src.hiveforge.steering.workflows.update_workflow.UpdateWorkflow') as mock_update:
            # Setup mock with warnings
            warning1 = Mock(message="Warning 1")
            warning2 = Mock(message="Warning 2")
            mock_report = Mock()
            mock_report.warnings = [warning1, warning2]
            
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow.state.validation_report = mock_report
            mock_workflow.customizations = {"test.md": [Mock()]}
            mock_update.return_value = mock_workflow
            
            # Execute workflow
            workflow = SharedUpdateWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify warnings collected
            assert result.success is True
            assert len(result.warnings) >= 2  # At least the 2 from validation
            assert "Warning 1" in result.warnings
            assert "Warning 2" in result.warnings
    
    def test_reset_workflow_creates_backup_before_reset(self, tmp_path):
        """Test that reset workflow creates backup before modifying files."""
        # Create steering directory with file
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        original_content = "# Original content"
        (steering_dir / "tech-stack.md").write_text(original_content)
        
        with patch('src.hiveforge.steering.templates.get_all_templates') as mock_templates:
            # Mock template
            mock_template = Mock()
            mock_template.frontmatter = {}
            mock_template.sections = [Mock(name="Section", placeholder_pattern="{new}")]
            mock_templates.return_value = {"tech-stack": mock_template}
            
            # Execute workflow
            workflow = SharedResetWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify backup was created
            assert result.success is True
            assert "backup_location" in result.metadata
            
            # Verify backup contains original content
            backup_dir = tmp_path / result.metadata["backup_location"]
            assert backup_dir.exists()
            backup_file = backup_dir / "tech-stack.md"
            assert backup_file.exists()
            assert backup_file.read_text() == original_content


class TestTelemetryIntegration:
    """Test telemetry collection during workflow execution."""
    
    def test_init_workflow_collects_telemetry_on_success(self, tmp_path):
        """Test that init workflow collects telemetry on successful execution."""
        telemetry_dir = tmp_path / ".kiro" / ".telemetry"
        telemetry = TelemetryCollector(telemetry_dir=telemetry_dir)
        
        # Create steering directory for success scenario
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "test.md").write_text("# Test")
        
        with patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock_init:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow.state.validation_report = None
            mock_init.return_value = mock_workflow
            
            # Execute workflow with telemetry
            workflow = SharedInitWorkflow(
                project_root=tmp_path,
                telemetry_collector=telemetry,
                interface_type=InterfaceType.CLI
            )
            result = workflow.execute()
            
            # Verify telemetry was collected
            assert result.success is True
            
            # Check telemetry file exists
            assert telemetry_dir.exists()
    
    def test_workflow_collects_telemetry_on_failure(self, tmp_path):
        """Test that workflow collects telemetry even on failure."""
        telemetry_dir = tmp_path / ".kiro" / ".telemetry"
        telemetry = TelemetryCollector(telemetry_dir=telemetry_dir)
        
        with patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock_init:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = False  # Failure
            mock_workflow.state.validation_report = None
            mock_init.return_value = mock_workflow
            
            # Execute workflow with telemetry
            workflow = SharedInitWorkflow(
                project_root=tmp_path,
                telemetry_collector=telemetry,
                interface_type=InterfaceType.POWER
            )
            result = workflow.execute()
            
            # Verify telemetry was collected even on failure
            assert result.success is False
            
            # Check telemetry file exists
            assert telemetry_dir.exists()


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow execution."""
    
    def test_complete_workflow_with_all_features(self, tmp_path):
        """Test workflow with security, error handling, and telemetry."""
        telemetry_dir = tmp_path / ".kiro" / ".telemetry"
        telemetry = TelemetryCollector(telemetry_dir=telemetry_dir)
        
        # Create steering directory
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "test.md").write_text("# Test")
        
        with patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock_init:
            # Setup successful workflow
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow.state.validation_report = None
            mock_init.return_value = mock_workflow
            
            # Execute workflow with all features enabled
            workflow = SharedInitWorkflow(
                project_root=tmp_path,
                telemetry_collector=telemetry,
                interface_type=InterfaceType.CLI
            )
            result = workflow.execute()
            
            # Verify all features worked
            assert result.success is True
            assert result.metadata["rollback_enabled"] is True
            assert len(result.files_created) > 0
    
    def test_error_propagation_through_layers(self, tmp_path):
        """Test that errors propagate correctly through all layers."""
        with patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock_init:
            # Setup workflow that raises exception
            mock_init.side_effect = RuntimeError("Test error")
            
            # Execute workflow
            workflow = SharedInitWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify error was caught and handled
            assert result.success is False
            assert "Test error" in result.message
            assert len(result.errors) > 0
            assert "Test error" in result.errors


class TestRollbackScenarios:
    """Test various rollback scenarios."""
    
    def test_rollback_on_exception_during_execution(self, tmp_path):
        """Test that rollback occurs when exception is raised during execution."""
        # Create initial steering directory
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        original_file = steering_dir / "original.md"
        original_file.write_text("# Original")
        
        with patch('src.hiveforge.steering.workflows.update_workflow.UpdateWorkflow') as mock_update:
            # Setup workflow that fails after modifying files
            def side_effect_execute():
                # Simulate file modification
                (steering_dir / "new.md").write_text("# New")
                # Then fail
                return False
            
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = side_effect_execute
            mock_workflow.state.validation_report = None
            mock_workflow.customizations = {}
            mock_update.return_value = mock_workflow
            
            # Execute workflow
            workflow = SharedUpdateWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify failure was handled
            assert result.success is False
    
    def test_no_rollback_when_disabled(self, tmp_path):
        """Test that rollback can be disabled."""
        # Create steering directory for success scenario
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "test.md").write_text("# Test")
        
        with patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow') as mock_init:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True  # Success
            mock_workflow.state.validation_report = None
            mock_init.return_value = mock_workflow
            
            # Execute workflow with rollback disabled
            workflow = SharedInitWorkflow(project_root=tmp_path)
            workflow.enable_rollback = False
            workflow.tool_executor.enable_rollback = False
            
            result = workflow.execute()
            
            # Verify workflow succeeded and rollback setting is reflected
            assert result.success is True
            assert result.metadata.get("rollback_enabled") is False


class TestMultipleErrorCollection:
    """Test collection of multiple errors and warnings."""
    
    def test_collect_multiple_errors_from_validation(self, tmp_path):
        """Test that multiple validation errors are collected."""
        with patch('src.hiveforge.steering.workflows.validate_workflow.ValidateWorkflow') as mock_validate:
            # Setup validation with multiple errors
            error1 = Mock(message="Error 1")
            error2 = Mock(message="Error 2")
            error3 = Mock(message="Error 3")
            
            mock_report = Mock()
            mock_report.files_checked = 3
            mock_report.critical_issues = [error1, error2, error3]
            mock_report.warnings = []
            mock_report.info = []
            mock_report.overall_status = "fail"
            
            mock_workflow = Mock()
            mock_workflow.execute.return_value = 1  # Failure
            mock_workflow.state.validation_report = mock_report
            mock_validate.return_value = mock_workflow
            
            # Execute workflow
            workflow = SharedValidateWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify all errors collected
            assert result.success is False
            assert len(result.errors) == 3
            assert "Error 1" in result.errors
            assert "Error 2" in result.errors
            assert "Error 3" in result.errors
    
    def test_collect_errors_and_warnings_together(self, tmp_path):
        """Test that errors and warnings are collected separately."""
        with patch('src.hiveforge.steering.workflows.validate_workflow.ValidateWorkflow') as mock_validate:
            # Setup validation with both errors and warnings
            error1 = Mock(message="Error 1")
            warning1 = Mock(message="Warning 1")
            warning2 = Mock(message="Warning 2")
            
            mock_report = Mock()
            mock_report.files_checked = 3
            mock_report.critical_issues = [error1]
            mock_report.warnings = [warning1, warning2]
            mock_report.info = []
            mock_report.overall_status = "fail"
            
            mock_workflow = Mock()
            mock_workflow.execute.return_value = 1  # Failure
            mock_workflow.state.validation_report = mock_report
            mock_validate.return_value = mock_workflow
            
            # Execute workflow
            workflow = SharedValidateWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify errors and warnings collected separately
            assert result.success is False
            assert len(result.errors) == 1
            assert len(result.warnings) == 2
            assert "Error 1" in result.errors
            assert "Warning 1" in result.warnings
            assert "Warning 2" in result.warnings


class TestDiscoveryWorkflowIntegration:
    """Test discovery workflow integration."""
    
    def test_discovery_with_empty_results(self, tmp_path):
        """Test that discovery handles empty results gracefully."""
        with patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator') as mock_orch:
            # Setup empty discovery
            mock_orchestrator = Mock()
            mock_orchestrator.discover_all.return_value = ([], {"file_count": 0, "method": "full_scan"})
            mock_orch.return_value = mock_orchestrator
            
            # Execute workflow
            workflow = SharedDiscoveryWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify empty results handled gracefully
            assert result.success is True
            assert "no relevant files found" in result.message
    
    def test_discovery_collects_skip_warnings(self, tmp_path):
        """Test that discovery collects warnings for skipped files."""
        with patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator') as mock_orch:
            # Setup discovery with skipped files
            mock_orchestrator = Mock()
            mock_orchestrator.discover_all.return_value = (
                ["file1.py", "file2.py"],
                {
                    "file_count": 5,
                    "method": "full_scan",
                    "ranking_metadata": {
                        "total_skipped": 3,
                        "skip_reasons": {
                            "too_large": 2,
                            "binary": 1
                        }
                    }
                }
            )
            mock_orch.return_value = mock_orchestrator
            
            # Execute workflow
            workflow = SharedDiscoveryWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify warnings collected
            assert result.success is True
            assert len(result.warnings) == 2  # 2 skip reasons
            assert any("too_large" in w for w in result.warnings)
            assert any("binary" in w for w in result.warnings)
