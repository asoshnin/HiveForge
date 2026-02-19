"""
Unit tests for shared workflow adapters.

Tests the adapter layer that wraps v02 workflows for use by both
CLI and Power interfaces.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.hiveforge.steering.shared.adapters import (
    SharedValidateWorkflow,
    SharedInitWorkflow,
    SharedUpdateWorkflow,
    SharedResetWorkflow,
    SharedDiscoveryWorkflow
)
from src.hiveforge.steering.shared.base import WorkflowResult


class TestSharedValidateWorkflow:
    """Tests for SharedValidateWorkflow adapter."""
    
    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default parameters."""
        workflow = SharedValidateWorkflow(project_root=tmp_path)
        
        assert workflow.project_root == tmp_path
        assert workflow.strict is False
        assert workflow.use_llm is True
    
    def test_init_with_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        workflow = SharedValidateWorkflow(
            project_root=tmp_path,
            strict=True,
            use_llm=False
        )
        
        assert workflow.strict is True
        assert workflow.use_llm is False
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.ValidateWorkflow')
    def test_execute_success_no_warnings(self, mock_validate_class, tmp_path):
        """Test successful validation with no warnings."""
        # Setup mock validation report
        mock_report = Mock()
        mock_report.files_checked = 3
        mock_report.critical_issues = []
        mock_report.warnings = []
        mock_report.info = []
        mock_report.overall_status = "pass"
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = 0  # Success exit code
        mock_workflow.state.validation_report = mock_report
        mock_validate_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedValidateWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is True
        assert "All validation checks passed" in result.message
        assert len(result.warnings) == 0
        assert len(result.errors) == 0
        assert result.metadata["files_checked"] == 3
        assert result.metadata["overall_status"] == "pass"
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.ValidateWorkflow')
    def test_execute_success_with_warnings(self, mock_validate_class, tmp_path):
        """Test successful validation with warnings."""
        # Setup mock validation report with warnings
        warning1 = Mock(message="Warning 1")
        warning2 = Mock(message="Warning 2")
        
        mock_report = Mock()
        mock_report.files_checked = 3
        mock_report.critical_issues = []
        mock_report.warnings = [warning1, warning2]
        mock_report.info = []
        mock_report.overall_status = "pass"
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = 0  # Success exit code
        mock_workflow.state.validation_report = mock_report
        mock_validate_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedValidateWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is True
        assert "passed with 2 warning(s)" in result.message
        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings
        assert "Warning 2" in result.warnings
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.ValidateWorkflow')
    def test_execute_failure_with_critical_issues(self, mock_validate_class, tmp_path):
        """Test failed validation with critical issues."""
        # Setup mock validation report with critical issues
        error1 = Mock(message="Critical error 1")
        error2 = Mock(message="Critical error 2")
        
        mock_report = Mock()
        mock_report.files_checked = 3
        mock_report.critical_issues = [error1, error2]
        mock_report.warnings = []
        mock_report.info = []
        mock_report.overall_status = "fail"
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = 1  # Failure exit code
        mock_workflow.state.validation_report = mock_report
        mock_validate_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedValidateWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is False
        assert "failed with 2 critical issue(s)" in result.message
        assert len(result.errors) == 2
        assert "Critical error 1" in result.errors
        assert "Critical error 2" in result.errors
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.ValidateWorkflow')
    def test_execute_strict_mode_treats_warnings_as_errors(self, mock_validate_class, tmp_path):
        """Test that strict mode treats warnings as errors."""
        # Setup mock validation report with warnings
        warning1 = Mock(message="Warning 1")
        
        mock_report = Mock()
        mock_report.files_checked = 3
        mock_report.critical_issues = []
        mock_report.warnings = [warning1]
        mock_report.info = []
        mock_report.overall_status = "pass"
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = 1  # Failure exit code in strict mode
        mock_workflow.state.validation_report = mock_report
        mock_validate_class.return_value = mock_workflow
        
        # Execute with strict mode
        workflow = SharedValidateWorkflow(project_root=tmp_path, strict=True)
        result = workflow.execute()
        
        # Verify result - should fail due to warnings in strict mode
        assert result.success is False
        assert len(result.warnings) == 1
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.ValidateWorkflow')
    def test_execute_passes_config_to_v02_workflow(self, mock_validate_class, tmp_path):
        """Test that configuration is passed correctly to v02 workflow."""
        # Setup mock
        mock_workflow = Mock()
        mock_workflow.execute.return_value = 0
        mock_workflow.state.validation_report = Mock(
            files_checked=0,
            critical_issues=[],
            warnings=[],
            info=[],
            overall_status="pass"
        )
        mock_validate_class.return_value = mock_workflow
        
        # Execute with custom config
        workflow = SharedValidateWorkflow(
            project_root=tmp_path,
            strict=True,
            use_llm=False
        )
        result = workflow.execute()
        
        # Verify v02 workflow was created with correct config
        mock_validate_class.assert_called_once()
        call_kwargs = mock_validate_class.call_args[1]
        assert call_kwargs['project_root'] == tmp_path
        
        # Verify config object (note: use_llm is not in SteeringConfig, only strict_mode)
        config = call_kwargs['config']
        assert config.strict_mode is True
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.ValidateWorkflow')
    def test_execute_handles_exceptions(self, mock_validate_class, tmp_path):
        """Test that exceptions are handled gracefully."""
        # Setup mock to raise exception
        mock_validate_class.side_effect = RuntimeError("Test error")
        
        # Execute
        workflow = SharedValidateWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify error handling
        assert result.success is False
        assert "Test error" in result.message
        assert len(result.errors) > 0
    
    def test_result_to_dict_format(self, tmp_path):
        """Test that result can be converted to dict for JSON (Power interface)."""
        # Create a sample result directly (no need to mock ValidateWorkflow)
        result = WorkflowResult(
            success=True,
            message="Test message",
            warnings=["Warning 1"],
            metadata={"test": "value"}
        )
        
        # Convert to dict
        result_dict = result.to_dict()
        
        # Verify format
        assert result_dict["status"] == "success"
        assert result_dict["message"] == "Test message"
        assert result_dict["warnings"] == ["Warning 1"]
        assert result_dict["test"] == "value"
    
    def test_result_format_for_cli(self, tmp_path):
        """Test that result can be formatted for CLI output."""
        # Create a sample result
        result = WorkflowResult(
            success=True,
            message="Test message",
            warnings=["Warning 1"],
            errors=[]
        )
        
        # Format for CLI
        cli_output = result.format_for_cli()
        
        # Verify format
        assert "✓ Test message" in cli_output
        assert "Warning 1" in cli_output


class TestSharedInitWorkflow:
    """Tests for SharedInitWorkflow adapter."""
    
    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default parameters."""
        workflow = SharedInitWorkflow(project_root=tmp_path)
        
        assert workflow.project_root == tmp_path
        assert workflow.source_docs_path is None
        assert workflow.auto_discover is True
        assert workflow.autonomous is True
        assert workflow.confidence_threshold == 0.7
    
    def test_init_with_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            auto_discover=False,
            autonomous=False,
            confidence_threshold=0.9
        )
        
        assert workflow.auto_discover is False
        assert workflow.autonomous is False
        assert workflow.confidence_threshold == 0.9
    
    def test_init_with_source_docs_path(self, tmp_path):
        """Test initialization with source_docs_path parameter."""
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            source_docs_path="_DEVELOPMENT"
        )
        
        assert workflow.source_docs_path == "_DEVELOPMENT"
        assert workflow.auto_discover is True
        assert workflow.autonomous is True
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_execute_success(self, mock_init_class, tmp_path):
        """Test successful init workflow execution."""
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        (steering_dir / "conventions.md").touch()
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []  # Add warnings field
        mock_workflow.state.metadata = {}  # Add metadata field
        mock_init_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedInitWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is True
        assert "Successfully initialized" in result.message
        assert len(result.files_created) == 2
        assert result.metadata["files_count"] == 2
        assert result.metadata["source_docs_path"] is None
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_execute_with_source_docs_path_in_metadata(self, mock_init_class, tmp_path):
        """Test that source_docs_path is included in result metadata."""
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []  # Add warnings field
        mock_workflow.state.metadata = {}  # Add metadata field
        mock_init_class.return_value = mock_workflow
        
        # Execute with source_docs_path
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            source_docs_path="_DEVELOPMENT"
        )
        result = workflow.execute()
        
        # Verify metadata includes source_docs_path
        assert result.success is True
        assert result.metadata["source_docs_path"] == "_DEVELOPMENT"
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_execute_failure(self, mock_init_class, tmp_path):
        """Test failed init workflow execution."""
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = False
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {}
        mock_init_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedInitWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is False
        assert "failed or was cancelled" in result.message
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_execute_with_autonomous_mode(self, mock_init_class, tmp_path):
        """Test that autonomous mode is configured correctly."""
        # Setup mock
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {}
        mock_init_class.return_value = mock_workflow
        
        # Execute with autonomous mode
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            autonomous=True,
            confidence_threshold=0.8
        )
        result = workflow.execute()
        
        # Verify v02 workflow was created with correct config
        mock_init_class.assert_called_once()
        call_kwargs = mock_init_class.call_args[1]
        
        # Verify config
        config = call_kwargs['config']
        assert config.interactive is False
        assert config.feature_flags is not None
        assert config.feature_flags.use_autonomous_generation is True
        assert config.feature_flags.confidence_threshold == 0.8
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_execute_with_non_autonomous_mode(self, mock_init_class, tmp_path):
        """Test that non-autonomous mode is configured correctly."""
        # Setup mock
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {}
        mock_init_class.return_value = mock_workflow
        
        # Execute with non-autonomous mode
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            autonomous=False
        )
        result = workflow.execute()
        
        # Verify v02 workflow was created with correct config
        mock_init_class.assert_called_once()
        call_kwargs = mock_init_class.call_args[1]
        
        # Verify config
        config = call_kwargs['config']
        assert config.interactive is True
        assert config.feature_flags is None
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_execute_with_warnings(self, mock_init_class, tmp_path):
        """Test that warnings are collected from validation report."""
        # Setup mock with validation warnings
        warning1 = Mock(message="Warning 1")
        warning2 = Mock(message="Warning 2")
        
        mock_report = Mock()
        mock_report.warnings = [warning1, warning2]
        
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = mock_report
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {}
        mock_init_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedInitWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify warnings collected
        assert result.success is True
        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings
        assert "Warning 2" in result.warnings
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_execute_handles_exceptions(self, mock_init_class, tmp_path):
        """Test that exceptions are handled gracefully."""
        # Setup mock to raise exception
        mock_init_class.side_effect = RuntimeError("Test error")
        
        # Execute
        workflow = SharedInitWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify error handling
        assert result.success is False
        assert "Test error" in result.message
        assert len(result.errors) > 0
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_backward_compatibility_without_source_docs_path(self, mock_init_class, tmp_path):
        """Test backward compatibility when source_docs_path is not provided."""
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {}
        mock_init_class.return_value = mock_workflow
        
        # Execute without source_docs_path (old behavior)
        workflow = SharedInitWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify it works as before
        assert result.success is True
        assert result.metadata["source_docs_path"] is None
        assert "Successfully initialized" in result.message
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_empty_source_folder_warnings_collected(self, mock_init_class, tmp_path):
        """Test that empty source folder warnings are collected in result (R2.1, R2.2)."""
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        
        # Setup mock workflow with empty source folder warnings
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = [
            "No source documents found. Steering files will be generated from code analysis only. Consider adding design documents to improve accuracy.",
            "Autonomous mode with no source documents may produce inferred content. Review generated files carefully."
        ]
        mock_workflow.state.metadata = {
            "source_documents_found": 0,
            "confidence_level": "low"
        }
        mock_init_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedInitWorkflow(project_root=tmp_path, autonomous=True)
        result = workflow.execute()
        
        # Verify warnings are collected
        assert result.success is True
        assert len(result.warnings) == 2
        assert any("No source documents found" in w for w in result.warnings)
        assert any("Autonomous mode with no source documents" in w for w in result.warnings)
        
        # Verify metadata is included
        assert result.metadata["source_documents_found"] == 0
        assert result.metadata["confidence_level"] == "low"


class TestSharedUpdateWorkflow:
    """Tests for SharedUpdateWorkflow adapter."""
    
    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default parameters."""
        workflow = SharedUpdateWorkflow(project_root=tmp_path)
        
        assert workflow.project_root == tmp_path
        assert workflow.preserve_customizations is True
        assert workflow.incremental is True
        assert workflow.files_to_update is None
    
    def test_init_with_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        workflow = SharedUpdateWorkflow(
            project_root=tmp_path,
            files_to_update=["tech-stack.md"],
            preserve_customizations=False,
            incremental=False
        )
        
        assert workflow.files_to_update == ["tech-stack.md"]
        assert workflow.preserve_customizations is False
        assert workflow.incremental is False
    
    @patch('src.hiveforge.steering.workflows.update_workflow.UpdateWorkflow')
    def test_execute_success(self, mock_update_class, tmp_path):
        """Test successful update workflow execution."""
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        (steering_dir / "conventions.md").touch()
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.customizations = {"tech-stack.md": [Mock()]}
        mock_update_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedUpdateWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is True
        assert "Successfully updated" in result.message
        assert len(result.files_modified) == 2
        assert result.metadata["customizations_detected"] == 1
    
    @patch('src.hiveforge.steering.workflows.update_workflow.UpdateWorkflow')
    def test_execute_failure(self, mock_update_class, tmp_path):
        """Test failed update workflow execution."""
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = False
        mock_workflow.state.validation_report = None
        mock_workflow.customizations = {}
        mock_update_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedUpdateWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is False
        assert "failed or was cancelled" in result.message
    
    @patch('src.hiveforge.steering.workflows.update_workflow.UpdateWorkflow')
    def test_execute_with_specific_files(self, mock_update_class, tmp_path):
        """Test update with specific files filter."""
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        (steering_dir / "conventions.md").touch()
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.customizations = {}
        mock_update_class.return_value = mock_workflow
        
        # Execute with specific file filter
        workflow = SharedUpdateWorkflow(
            project_root=tmp_path,
            files_to_update=["tech-stack"]
        )
        result = workflow.execute()
        
        # Verify only tech-stack file is in modified list
        assert result.success is True
        assert len(result.files_modified) == 1
        assert "tech-stack.md" in result.files_modified[0]
    
    @patch('src.hiveforge.steering.workflows.update_workflow.UpdateWorkflow')
    def test_execute_with_incremental_mode(self, mock_update_class, tmp_path):
        """Test that incremental mode is configured correctly."""
        # Setup mock
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.customizations = {}
        mock_update_class.return_value = mock_workflow
        
        # Execute with incremental mode
        workflow = SharedUpdateWorkflow(
            project_root=tmp_path,
            incremental=True
        )
        result = workflow.execute()
        
        # Verify v02 workflow was created with correct config
        mock_update_class.assert_called_once()
        call_kwargs = mock_update_class.call_args[1]
        
        # Verify config
        config = call_kwargs['config']
        assert config.incremental is True
    
    @patch('src.hiveforge.steering.workflows.update_workflow.UpdateWorkflow')
    def test_execute_with_warnings(self, mock_update_class, tmp_path):
        """Test that warnings are collected from validation report."""
        # Setup mock with validation warnings
        warning1 = Mock(message="Warning 1")
        warning2 = Mock(message="Warning 2")
        
        mock_report = Mock()
        mock_report.warnings = [warning1, warning2]
        
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = mock_report
        mock_workflow.customizations = {}
        mock_update_class.return_value = mock_workflow
        
        # Execute
        workflow = SharedUpdateWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify warnings collected
        assert result.success is True
        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings
        assert "Warning 2" in result.warnings
    
    @patch('src.hiveforge.steering.workflows.update_workflow.UpdateWorkflow')
    def test_execute_handles_exceptions(self, mock_update_class, tmp_path):
        """Test that exceptions are handled gracefully."""
        # Setup mock to raise exception
        mock_update_class.side_effect = RuntimeError("Test error")
        
        # Execute
        workflow = SharedUpdateWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify error handling
        assert result.success is False
        assert "Test error" in result.message
        assert len(result.errors) > 0


class TestSharedResetWorkflow:
    """Tests for SharedResetWorkflow adapter."""
    
    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default parameters."""
        workflow = SharedResetWorkflow(project_root=tmp_path)
        
        assert workflow.project_root == tmp_path
        assert workflow.file is None
        assert workflow.confirm is False
    
    def test_init_with_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        workflow = SharedResetWorkflow(
            project_root=tmp_path,
            file="tech-stack.md",
            confirm=True
        )
        
        assert workflow.file == "tech-stack.md"
        assert workflow.confirm is True
    
    def test_execute_no_steering_directory(self, tmp_path):
        """Test reset when steering directory doesn't exist."""
        workflow = SharedResetWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        assert result.success is False
        assert "No steering directory found" in result.message
    
    def test_execute_specific_file_not_found(self, tmp_path):
        """Test reset when specific file doesn't exist."""
        # Create steering directory but no files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        workflow = SharedResetWorkflow(
            project_root=tmp_path,
            file="nonexistent.md"
        )
        result = workflow.execute()
        
        assert result.success is False
        assert "File not found" in result.message
    
    def test_execute_empty_directory(self, tmp_path):
        """Test reset when steering directory is empty."""
        # Create empty steering directory
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        workflow = SharedResetWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        assert result.success is False
        assert "No steering files found" in result.message
    
    @patch('src.hiveforge.steering.templates.get_all_templates')
    def test_execute_reset_all_files(self, mock_get_templates, tmp_path):
        """Test resetting all files."""
        # Create steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").write_text("# Old content")
        (steering_dir / "conventions.md").write_text("# Old content")
        
        # Mock templates
        mock_template1 = Mock()
        mock_template1.file_name = "tech-stack.md"
        mock_template1.frontmatter = {}
        mock_template1.sections = [Mock(name="Section 1", placeholder_pattern="{placeholder}")]
        
        mock_template2 = Mock()
        mock_template2.file_name = "conventions.md"
        mock_template2.frontmatter = {}
        mock_template2.sections = [Mock(name="Section 2", placeholder_pattern="{placeholder}")]
        
        mock_get_templates.return_value = {
            "tech-stack": mock_template1,
            "conventions": mock_template2
        }
        
        # Execute
        workflow = SharedResetWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is True
        assert "Successfully reset 2 file(s)" in result.message
        assert len(result.files_modified) == 2
        assert "backup_location" in result.metadata
    
    @patch('src.hiveforge.steering.templates.get_all_templates')
    def test_execute_reset_specific_file(self, mock_get_templates, tmp_path):
        """Test resetting a specific file."""
        # Create steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").write_text("# Old content")
        (steering_dir / "conventions.md").write_text("# Old content")
        
        # Mock template
        mock_template = Mock()
        mock_template.file_name = "tech-stack.md"
        mock_template.frontmatter = {}
        mock_template.sections = [Mock(name="Section 1", placeholder_pattern="{placeholder}")]
        
        mock_get_templates.return_value = {
            "tech-stack": mock_template
        }
        
        # Execute with specific file
        workflow = SharedResetWorkflow(
            project_root=tmp_path,
            file="tech-stack.md"
        )
        result = workflow.execute()
        
        # Verify result
        assert result.success is True
        assert "Successfully reset 1 file(s)" in result.message
        assert len(result.files_modified) == 1
        assert "tech-stack.md" in result.files_modified[0]
    
    @patch('src.hiveforge.steering.templates.get_all_templates')
    def test_execute_creates_backup(self, mock_get_templates, tmp_path):
        """Test that backup is created before reset."""
        # Create steering directory with file
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        original_content = "# Original content"
        (steering_dir / "tech-stack.md").write_text(original_content)
        
        # Mock template
        mock_template = Mock()
        mock_template.file_name = "tech-stack.md"
        mock_template.frontmatter = {}
        mock_template.sections = [Mock(name="Section", placeholder_pattern="{new}")]
        
        mock_get_templates.return_value = {
            "tech-stack": mock_template
        }
        
        # Execute
        workflow = SharedResetWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify backup was created
        assert result.success is True
        backup_location = tmp_path / result.metadata["backup_location"]
        assert backup_location.exists()
        backup_file = backup_location / "tech-stack.md"
        assert backup_file.exists()
        assert backup_file.read_text() == original_content
    
    def test_execute_handles_exceptions(self, tmp_path):
        """Test that exceptions are handled gracefully."""
        # Create steering directory
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        # Create a file but make it unreadable to trigger an error
        test_file = steering_dir / "test.md"
        test_file.write_text("content")
        
        # Mock get_all_templates to raise an exception
        with patch('src.hiveforge.steering.templates.get_all_templates', side_effect=RuntimeError("Test error")):
            workflow = SharedResetWorkflow(project_root=tmp_path)
            result = workflow.execute()
            
            # Verify error handling
            assert result.success is False
            assert "Test error" in result.message


class TestSharedDiscoveryWorkflow:
    """Tests for SharedDiscoveryWorkflow adapter."""
    
    def test_init_with_defaults(self, tmp_path):
        """Test initialization with default parameters."""
        workflow = SharedDiscoveryWorkflow(project_root=tmp_path)
        
        assert workflow.project_root == tmp_path
        assert workflow.source_docs_path is None
        assert workflow.include_git_history is False
        assert workflow.max_discovery_files == 1000
        assert workflow.max_file_size_mb == 10
    
    def test_init_with_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        workflow = SharedDiscoveryWorkflow(
            project_root=tmp_path,
            include_git_history=True,
            max_discovery_files=500,
            max_file_size_mb=5
        )
        
        assert workflow.include_git_history is True
        assert workflow.max_discovery_files == 500
        assert workflow.max_file_size_mb == 5
    
    def test_init_with_source_docs_path(self, tmp_path):
        """Test initialization with source_docs_path parameter."""
        workflow = SharedDiscoveryWorkflow(
            project_root=tmp_path,
            source_docs_path="docs"
        )
        
        assert workflow.source_docs_path == "docs"
    
    @patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator')
    def test_execute_success_with_files(self, mock_orchestrator_class, tmp_path):
        """Test successful discovery with files found."""
        # Setup mock discovered files
        discovered_files = [
            Path("README.md"),
            Path("docs/architecture.md"),
            Path("package.json")
        ]
        
        metadata = {
            "file_count": 3,
            "commit_count": 10,
            "method": "full_scan",
            "ranking_metadata": {
                "total_included": 3,
                "total_skipped": 0
            }
        }
        
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.discover_all.return_value = (discovered_files, metadata)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute
        workflow = SharedDiscoveryWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is True
        assert "Discovery complete: 3 files found" in result.message
        assert result.metadata["files_discovered"] == 3
        assert result.metadata["files_included"] == 3
        assert result.metadata["discovery_method"] == "full_scan"
        assert result.metadata["source_docs_path"] is None
    
    @patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator')
    def test_execute_with_source_docs_path_in_metadata(self, mock_orchestrator_class, tmp_path):
        """Test that source_docs_path is included in result metadata."""
        # Setup mock discovered files
        discovered_files = [Path("README.md")]
        metadata = {
            "file_count": 1,
            "commit_count": 0,
            "method": "full_scan"
        }
        
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.discover_all.return_value = (discovered_files, metadata)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute with source_docs_path
        workflow = SharedDiscoveryWorkflow(
            project_root=tmp_path,
            source_docs_path="_DEVELOPMENT"
        )
        result = workflow.execute()
        
        # Verify metadata includes source_docs_path
        assert result.success is True
        assert result.metadata["source_docs_path"] == "_DEVELOPMENT"
    
    @patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator')
    def test_execute_success_with_git_history(self, mock_orchestrator_class, tmp_path):
        """Test successful discovery with git history analysis."""
        # Setup mock discovered files
        discovered_files = [Path("README.md")]
        
        metadata = {
            "file_count": 1,
            "commit_count": 25,
            "method": "full_scan"
        }
        
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.discover_all.return_value = (discovered_files, metadata)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute with git history
        workflow = SharedDiscoveryWorkflow(
            project_root=tmp_path,
            include_git_history=True
        )
        result = workflow.execute()
        
        # Verify result includes commit count
        assert result.success is True
        assert "25 commits analyzed" in result.message
        assert result.metadata["commit_count"] == 25
        assert result.metadata["include_git_history"] is True
    
    @patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator')
    def test_execute_no_files_found(self, mock_orchestrator_class, tmp_path):
        """Test discovery when no files are found."""
        # Setup mock with no files
        discovered_files = []
        metadata = {
            "file_count": 0,
            "commit_count": 0,
            "method": "full_scan"
        }
        
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.discover_all.return_value = (discovered_files, metadata)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute
        workflow = SharedDiscoveryWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify result
        assert result.success is True
        assert "no relevant files found" in result.message
        assert result.metadata["files_discovered"] == 0
    
    @patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator')
    def test_execute_with_skipped_files(self, mock_orchestrator_class, tmp_path):
        """Test discovery with some files skipped."""
        # Setup mock discovered files
        discovered_files = [Path("README.md")]
        
        metadata = {
            "file_count": 10,
            "commit_count": 0,
            "method": "sampling",
            "ranking_metadata": {
                "total_included": 1,
                "total_skipped": 9,
                "skip_reasons": {
                    "file_too_large": 5,
                    "binary_file": 3,
                    "limit_reached": 1
                }
            }
        }
        
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.discover_all.return_value = (discovered_files, metadata)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute
        workflow = SharedDiscoveryWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify warnings about skipped files
        assert result.success is True
        assert len(result.warnings) == 3
        assert any("5 files skipped: file_too_large" in w for w in result.warnings)
        assert any("3 files skipped: binary_file" in w for w in result.warnings)
        assert any("1 files skipped: limit_reached" in w for w in result.warnings)
    
    @patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator')
    def test_execute_passes_config_to_orchestrator(self, mock_orchestrator_class, tmp_path):
        """Test that configuration is passed correctly to orchestrator."""
        # Setup mock
        mock_orchestrator = Mock()
        mock_orchestrator.discover_all.return_value = ([], {"file_count": 0, "commit_count": 0})
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute with custom config
        workflow = SharedDiscoveryWorkflow(
            project_root=tmp_path,
            max_discovery_files=500,
            max_file_size_mb=5
        )
        result = workflow.execute()
        
        # Verify orchestrator was created with correct config (including new parameters)
        mock_orchestrator_class.assert_called_once_with(
            max_discovery_files=500,
            max_file_size_mb=5,
            source_docs_path=None,
            file_types=None
        )
    
    @patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator')
    def test_execute_handles_exceptions(self, mock_orchestrator_class, tmp_path):
        """Test that exceptions are handled gracefully."""
        # Setup mock to raise exception
        mock_orchestrator_class.side_effect = RuntimeError("Test error")
        
        # Execute
        workflow = SharedDiscoveryWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify error handling
        assert result.success is False
        assert "Test error" in result.message
        assert len(result.errors) > 0
    
    @patch('src.hiveforge.steering.parsers.orchestrator.DiscoveryOrchestrator')
    def test_backward_compatibility_without_source_docs_path(self, mock_orchestrator_class, tmp_path):
        """Test backward compatibility when source_docs_path is not provided."""
        # Setup mock discovered files
        discovered_files = [Path("README.md")]
        metadata = {
            "file_count": 1,
            "commit_count": 0,
            "method": "full_scan"
        }
        
        # Setup mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.discover_all.return_value = (discovered_files, metadata)
        mock_orchestrator_class.return_value = mock_orchestrator
        
        # Execute without source_docs_path (old behavior)
        workflow = SharedDiscoveryWorkflow(project_root=tmp_path)
        result = workflow.execute()
        
        # Verify it works as before
        assert result.success is True
        assert result.metadata["source_docs_path"] is None
        assert "Discovery complete" in result.message


class TestSharedInitWorkflowTelemetry:
    """Tests for telemetry collection in SharedInitWorkflow (Task 2.6)."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_telemetry_collects_new_parameters(self, mock_init_class, tmp_path):
        """Test that telemetry collects dry_run and copy_files parameters."""
        from src.hiveforge.steering.shared.telemetry import TelemetryCollector, TelemetryLevel, InterfaceType
        
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {}
        mock_init_class.return_value = mock_workflow
        
        # Create telemetry collector
        telemetry_collector = TelemetryCollector(
            telemetry_dir=tmp_path / ".telemetry",
            level=TelemetryLevel.DETAILED
        )
        
        # Execute with new parameters
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            source_docs_path="_DEVELOPMENT",
            dry_run=True,
            copy_files=True,
            telemetry_collector=telemetry_collector,
            interface_type=InterfaceType.CLI
        )
        result = workflow.execute()
        
        # Verify telemetry was collected
        assert len(telemetry_collector._events) == 1
        event = telemetry_collector._events[0]
        
        # Verify new parameters are in telemetry
        assert event.parameters["source_docs_path"] == "_DEVELOPMENT"
        assert event.parameters["dry_run"] is True
        assert event.parameters["copy_files"] is True
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_telemetry_collects_confidence_metrics(self, mock_init_class, tmp_path):
        """Test that telemetry collects confidence level distribution."""
        from src.hiveforge.steering.shared.telemetry import TelemetryCollector, TelemetryLevel, InterfaceType
        
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        
        # Setup mock workflow with confidence metadata
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {
            "confidence_level": "medium",
            "overall_confidence_score": 0.65,
            "source_documents_found": 3
        }
        mock_init_class.return_value = mock_workflow
        
        # Create telemetry collector
        telemetry_collector = TelemetryCollector(
            telemetry_dir=tmp_path / ".telemetry",
            level=TelemetryLevel.DETAILED
        )
        
        # Execute
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            telemetry_collector=telemetry_collector,
            interface_type=InterfaceType.CLI
        )
        result = workflow.execute()
        
        # Verify confidence metrics in telemetry
        assert len(telemetry_collector._events) == 1
        event = telemetry_collector._events[0]
        
        assert event.additional_data["confidence_level"] == "medium"
        assert event.additional_data["overall_confidence_score"] == 0.65
        assert event.additional_data["source_documents_found"] == 3
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_telemetry_collects_performance_metrics(self, mock_init_class, tmp_path):
        """Test that telemetry collects performance metrics."""
        from src.hiveforge.steering.shared.telemetry import TelemetryCollector, TelemetryLevel, InterfaceType
        
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        
        # Setup mock workflow with performance metadata
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {
            "discovery_time_ms": 500,
            "confidence_calc_time_ms": 150,
            "content_tagging_time_ms": 50
        }
        mock_init_class.return_value = mock_workflow
        
        # Create telemetry collector
        telemetry_collector = TelemetryCollector(
            telemetry_dir=tmp_path / ".telemetry",
            level=TelemetryLevel.DETAILED
        )
        
        # Execute
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            telemetry_collector=telemetry_collector,
            interface_type=InterfaceType.CLI
        )
        result = workflow.execute()
        
        # Verify performance metrics in telemetry
        assert len(telemetry_collector._events) == 1
        event = telemetry_collector._events[0]
        
        assert event.additional_data["discovery_time_ms"] == 500
        assert event.additional_data["confidence_calc_time_ms"] == 150
        assert event.additional_data["content_tagging_time_ms"] == 50
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_telemetry_collects_error_metrics(self, mock_init_class, tmp_path):
        """Test that telemetry collects error metrics."""
        from src.hiveforge.steering.shared.telemetry import TelemetryCollector, TelemetryLevel, InterfaceType
        
        # Setup mock to raise exception
        mock_init_class.side_effect = ValueError("Path validation failed")
        
        # Create telemetry collector
        telemetry_collector = TelemetryCollector(
            telemetry_dir=tmp_path / ".telemetry",
            level=TelemetryLevel.DETAILED
        )
        
        # Execute
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            source_docs_path="../../../etc/passwd",
            telemetry_collector=telemetry_collector,
            interface_type=InterfaceType.CLI
        )
        result = workflow.execute()
        
        # Verify error metrics in telemetry
        assert len(telemetry_collector._events) == 1
        event = telemetry_collector._events[0]
        
        assert event.result_status == "failed"
        assert event.error_type == "ValueError"
        assert "Path validation failed" in event.error_message
        assert event.error_recoverable is True
    
    @patch('src.hiveforge.steering.workflows.init_workflow.InitWorkflow')
    def test_result_metadata_includes_new_parameters(self, mock_init_class, tmp_path):
        """Test that result metadata includes dry_run and copy_files."""
        # Create mock steering directory with files
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        (steering_dir / "tech-stack.md").touch()
        
        # Setup mock workflow
        mock_workflow = Mock()
        mock_workflow.execute.return_value = True
        mock_workflow.state.validation_report = None
        mock_workflow.state.warnings = []
        mock_workflow.state.metadata = {}
        mock_init_class.return_value = mock_workflow
        
        # Execute with new parameters
        workflow = SharedInitWorkflow(
            project_root=tmp_path,
            dry_run=True,
            copy_files=True
        )
        result = workflow.execute()
        
        # Verify metadata includes new parameters
        assert result.metadata["dry_run"] is True
        assert result.metadata["copy_files"] is True

