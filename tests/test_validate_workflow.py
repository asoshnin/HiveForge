"""
Tests for ValidateWorkflow class.

This module tests the ValidateWorkflow orchestrator that coordinates
the validation of steering files.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.hiveforge.steering.workflows.validate_workflow import ValidateWorkflow
from src.hiveforge.steering.models import (
    SteeringConfig,
    ValidationReport,
    ValidationIssue,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    steering_dir = tmp_path / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    
    # Create sample steering files
    (steering_dir / "project-vision.md").write_text(
        "# Project Vision\n\nThis is a test project.",
        encoding='utf-8'
    )
    (steering_dir / "tech-stack.md").write_text(
        "# Tech Stack\n\nPython 3.11",
        encoding='utf-8'
    )
    
    return tmp_path


@pytest.fixture
def config():
    """Create a default SteeringConfig."""
    return SteeringConfig(
        research_enabled=False,
        skip_validation=False,
        interactive=True,
        strict_mode=False,
        backup_enabled=True,
        backup_dir=Path(".kiro/backups"),
        analyze_code=False,
    )


@pytest.fixture
def strict_config():
    """Create a SteeringConfig with strict mode enabled."""
    return SteeringConfig(
        research_enabled=False,
        skip_validation=False,
        interactive=True,
        strict_mode=True,
        backup_enabled=True,
        backup_dir=Path(".kiro/backups"),
        analyze_code=False,
    )


class TestValidateWorkflowInitialization:
    """Test ValidateWorkflow initialization."""
    
    def test_init_with_defaults(self, config):
        """Test initialization with default project root."""
        workflow = ValidateWorkflow(config)
        
        assert workflow.config == config
        assert workflow.project_root == Path.cwd()
        assert workflow.state.workflow_type == "validate"
        assert workflow.state.steering_dir == Path.cwd() / ".kiro" / "steering"
    
    def test_init_with_custom_root(self, config, tmp_path):
        """Test initialization with custom project root."""
        workflow = ValidateWorkflow(config, project_root=tmp_path)
        
        assert workflow.project_root == tmp_path
        assert workflow.state.steering_dir == tmp_path / ".kiro" / "steering"


class TestValidateWorkflowFileVerification:
    """Test file verification step."""
    
    def test_verify_files_exist_success(self, config, temp_project, capsys):
        """Test successful file verification."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        
        result = workflow._step_verify_files_exist()
        
        assert result is True
        
        captured = capsys.readouterr()
        assert "Found 2 steering file(s) to validate" in captured.out
    
    def test_verify_files_no_directory(self, config, tmp_path, capsys):
        """Test verification when steering directory doesn't exist."""
        workflow = ValidateWorkflow(config, project_root=tmp_path)
        
        result = workflow._step_verify_files_exist()
        
        assert result is False
        
        captured = capsys.readouterr()
        assert "ERROR: No steering directory found" in captured.out
        assert "hiveforge steering init" in captured.out
    
    def test_verify_files_empty_directory(self, config, tmp_path, capsys):
        """Test verification when steering directory is empty."""
        steering_dir = tmp_path / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        workflow = ValidateWorkflow(config, project_root=tmp_path)
        
        result = workflow._step_verify_files_exist()
        
        assert result is False
        
        captured = capsys.readouterr()
        assert "ERROR: No steering files found" in captured.out


class TestValidateWorkflowValidation:
    """Test validation step."""
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.SteeringValidator')
    def test_run_validator_success(self, mock_validator_class, config, temp_project):
        """Test successful validation run."""
        # Setup mock
        mock_validator = Mock()
        mock_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0
        )
        mock_validator.validate_all.return_value = mock_report
        mock_validator_class.return_value = mock_validator
        
        workflow = ValidateWorkflow(config, project_root=temp_project)
        workflow._step_run_validator()
        
        # Verify validator was created and called correctly
        mock_validator_class.assert_called_once_with(use_llm=False)
        mock_validator.validate_all.assert_called_once_with(
            workflow.state.steering_dir,
            use_llm=False
        )
        
        # Verify report was stored
        assert workflow.state.validation_report == mock_report
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.SteeringValidator')
    def test_run_validator_failure(self, mock_validator_class, config, temp_project):
        """Test validation run with exception."""
        # Setup mock to raise exception
        mock_validator = Mock()
        mock_validator.validate_all.side_effect = Exception("Validation error")
        mock_validator_class.return_value = mock_validator
        
        workflow = ValidateWorkflow(config, project_root=temp_project)
        
        with pytest.raises(RuntimeError, match="Could not validate steering files"):
            workflow._step_run_validator()


class TestValidateWorkflowReportDisplay:
    """Test report display step."""
    
    def test_display_report_all_pass(self, config, temp_project, capsys):
        """Test displaying report with all checks passing."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        workflow.state.validation_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0
        )
        
        workflow._step_display_report()
        
        captured = capsys.readouterr()
        assert "VALIDATION REPORT" in captured.out
        assert "Files checked: 2" in captured.out
        assert "Critical issues: 0" in captured.out
        assert "Warnings: 0" in captured.out
        assert "Overall status: PASS" in captured.out
        assert "All checks passed!" in captured.out
    
    def test_display_report_with_critical_issues(self, config, temp_project, capsys):
        """Test displaying report with critical issues."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        
        critical_issue = ValidationIssue(
            severity="critical",
            file_name="tech-stack.md",
            line_number=15,
            issue_type="missing_section",
            message="Required section 'Database' is missing",
            suggestion="Add the Database section to the file"
        )
        
        workflow.state.validation_report = ValidationReport(
            files_checked=2,
            overall_status="fail",
            llm_calls_made=0,
            tokens_used=0,
            critical_issues=[critical_issue]
        )
        
        workflow._step_display_report()
        
        captured = capsys.readouterr()
        assert "Critical issues: 1" in captured.out
        assert "❌ Critical Issues:" in captured.out
        assert "tech-stack.md:15" in captured.out
        assert "Required section 'Database' is missing" in captured.out
        assert "Add the Database section to the file" in captured.out
        assert "Validation failed" in captured.out
    
    def test_display_report_with_warnings(self, config, temp_project, capsys):
        """Test displaying report with warnings."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        
        warning = ValidationIssue(
            severity="warning",
            file_name="conventions.md",
            line_number=None,
            issue_type="inconsistency",
            message="Naming convention conflicts with tech-stack",
            suggestion="Review naming conventions"
        )
        
        workflow.state.validation_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0,
            warnings=[warning]
        )
        
        workflow._step_display_report()
        
        captured = capsys.readouterr()
        assert "Warnings: 1" in captured.out
        assert "⚠️  Warnings:" in captured.out
        assert "conventions.md" in captured.out
        assert "Naming convention conflicts with tech-stack" in captured.out
        assert "Validation passed with warnings" in captured.out
    
    def test_display_report_with_info(self, config, temp_project, capsys):
        """Test displaying report with info messages."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        
        info = ValidationIssue(
            severity="info",
            file_name="project-vision.md",
            line_number=10,
            issue_type="suggestion",
            message="Consider adding more detail to the problem statement",
            suggestion=None
        )
        
        workflow.state.validation_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0,
            info=[info]
        )
        
        workflow._step_display_report()
        
        captured = capsys.readouterr()
        assert "Info messages: 1" in captured.out
        assert "ℹ️  Info:" in captured.out
        assert "project-vision.md:10" in captured.out


class TestValidateWorkflowExitCode:
    """Test exit code determination."""
    
    def test_exit_code_all_pass(self, config, temp_project):
        """Test exit code when all checks pass."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        workflow.state.validation_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0
        )
        
        exit_code = workflow._determine_exit_code()
        
        assert exit_code == 0
    
    def test_exit_code_with_critical_issues(self, config, temp_project):
        """Test exit code when critical issues are found."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        
        critical_issue = ValidationIssue(
            severity="critical",
            file_name="tech-stack.md",
            line_number=15,
            issue_type="missing_section",
            message="Required section missing",
            suggestion=None
        )
        
        workflow.state.validation_report = ValidationReport(
            files_checked=2,
            overall_status="fail",
            llm_calls_made=0,
            tokens_used=0,
            critical_issues=[critical_issue]
        )
        
        exit_code = workflow._determine_exit_code()
        
        assert exit_code == 1
    
    def test_exit_code_warnings_normal_mode(self, config, temp_project):
        """Test exit code with warnings in normal mode (should pass)."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        
        warning = ValidationIssue(
            severity="warning",
            file_name="conventions.md",
            line_number=None,
            issue_type="inconsistency",
            message="Minor inconsistency",
            suggestion=None
        )
        
        workflow.state.validation_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0,
            warnings=[warning]
        )
        
        exit_code = workflow._determine_exit_code()
        
        assert exit_code == 0
    
    def test_exit_code_warnings_strict_mode(self, strict_config, temp_project, capsys):
        """Test exit code with warnings in strict mode (should fail)."""
        workflow = ValidateWorkflow(strict_config, project_root=temp_project)
        
        warning = ValidationIssue(
            severity="warning",
            file_name="conventions.md",
            line_number=None,
            issue_type="inconsistency",
            message="Minor inconsistency",
            suggestion=None
        )
        
        workflow.state.validation_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0,
            warnings=[warning]
        )
        
        exit_code = workflow._determine_exit_code()
        
        assert exit_code == 1
        
        captured = capsys.readouterr()
        assert "strict mode" in captured.out


class TestValidateWorkflowExecution:
    """Test complete workflow execution."""
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.SteeringValidator')
    def test_execute_success(self, mock_validator_class, config, temp_project):
        """Test successful complete workflow execution."""
        # Setup mock
        mock_validator = Mock()
        mock_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0
        )
        mock_validator.validate_all.return_value = mock_report
        mock_validator_class.return_value = mock_validator
        
        workflow = ValidateWorkflow(config, project_root=temp_project)
        exit_code = workflow.execute()
        
        assert exit_code == 0
        assert workflow.state.validation_report == mock_report
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.SteeringValidator')
    def test_execute_with_critical_issues(self, mock_validator_class, config, temp_project):
        """Test workflow execution with critical issues."""
        # Setup mock
        mock_validator = Mock()
        
        critical_issue = ValidationIssue(
            severity="critical",
            file_name="tech-stack.md",
            line_number=15,
            issue_type="missing_section",
            message="Required section missing",
            suggestion=None
        )
        
        mock_report = ValidationReport(
            files_checked=2,
            overall_status="fail",
            llm_calls_made=0,
            tokens_used=0,
            critical_issues=[critical_issue]
        )
        mock_validator.validate_all.return_value = mock_report
        mock_validator_class.return_value = mock_validator
        
        workflow = ValidateWorkflow(config, project_root=temp_project)
        exit_code = workflow.execute()
        
        assert exit_code == 1
    
    def test_execute_no_files(self, config, tmp_path):
        """Test workflow execution when no files exist."""
        workflow = ValidateWorkflow(config, project_root=tmp_path)
        exit_code = workflow.execute()
        
        assert exit_code == 1
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.SteeringValidator')
    def test_execute_with_exception(self, mock_validator_class, config, temp_project):
        """Test workflow execution with exception."""
        # Setup mock to raise exception
        mock_validator = Mock()
        mock_validator.validate_all.side_effect = Exception("Validation error")
        mock_validator_class.return_value = mock_validator
        
        workflow = ValidateWorkflow(config, project_root=temp_project)
        exit_code = workflow.execute()
        
        assert exit_code == 1


class TestValidateWorkflowStrictMode:
    """Test strict mode behavior."""
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.SteeringValidator')
    def test_strict_mode_treats_warnings_as_errors(
        self,
        mock_validator_class,
        strict_config,
        temp_project
    ):
        """Test that strict mode treats warnings as errors."""
        # Setup mock
        mock_validator = Mock()
        
        warning = ValidationIssue(
            severity="warning",
            file_name="conventions.md",
            line_number=None,
            issue_type="inconsistency",
            message="Minor inconsistency",
            suggestion=None
        )
        
        mock_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0,
            warnings=[warning]
        )
        mock_validator.validate_all.return_value = mock_report
        mock_validator_class.return_value = mock_validator
        
        workflow = ValidateWorkflow(strict_config, project_root=temp_project)
        exit_code = workflow.execute()
        
        # In strict mode, warnings should cause non-zero exit code
        assert exit_code == 1
    
    @patch('src.hiveforge.steering.workflows.validate_workflow.SteeringValidator')
    def test_normal_mode_allows_warnings(
        self,
        mock_validator_class,
        config,
        temp_project
    ):
        """Test that normal mode allows warnings."""
        # Setup mock
        mock_validator = Mock()
        
        warning = ValidationIssue(
            severity="warning",
            file_name="conventions.md",
            line_number=None,
            issue_type="inconsistency",
            message="Minor inconsistency",
            suggestion=None
        )
        
        mock_report = ValidationReport(
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0,
            warnings=[warning]
        )
        mock_validator.validate_all.return_value = mock_report
        mock_validator_class.return_value = mock_validator
        
        workflow = ValidateWorkflow(config, project_root=temp_project)
        exit_code = workflow.execute()
        
        # In normal mode, warnings should not cause non-zero exit code
        assert exit_code == 0


class TestValidateWorkflowErrorHandling:
    """Test error handling and display."""
    
    def test_display_error_message(self, config, temp_project, capsys):
        """Test error message display."""
        workflow = ValidateWorkflow(config, project_root=temp_project)
        
        workflow._display_error_message("Test error message")
        
        captured = capsys.readouterr()
        assert "VALIDATION WORKFLOW FAILED" in captured.out
        assert "Test error message" in captured.out
        assert "Troubleshooting:" in captured.out
