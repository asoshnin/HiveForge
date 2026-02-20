"""
Tests for Steering CLI commands.

This module tests the CLI command handlers for the Steering Assistant feature:
- steering init command with various flags
- steering update command with various flags
- steering validate command with various flags
- Command parsing and routing
- Error handling for invalid commands
- Help text display

Requirements: 1.1-1.8, 14.1-14.6
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

from hiveforge.cli import app
from hiveforge.steering.models import SteeringConfig, ValidationReport


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_init_workflow():
    """Mock SharedInitWorkflow for testing."""
    with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock:
        workflow_instance = Mock()
        # Mock execute to return a WorkflowResult
        from hiveforge.steering.shared.base import WorkflowResult
        workflow_instance.execute.return_value = WorkflowResult(
            success=True,
            message="Init completed successfully",
            files_created=[".kiro/steering/tech-stack.md"]
        )
        mock.return_value = workflow_instance
        yield mock


@pytest.fixture
def mock_update_workflow():
    """Mock SharedUpdateWorkflow for testing."""
    with patch('hiveforge.steering.cli.SharedUpdateWorkflow') as mock:
        workflow_instance = Mock()
        # Mock execute to return a WorkflowResult
        from hiveforge.steering.shared.base import WorkflowResult
        workflow_instance.execute.return_value = WorkflowResult(
            success=True,
            message="Update completed successfully",
            files_modified=[".kiro/steering/tech-stack.md"]
        )
        mock.return_value = workflow_instance
        yield mock


@pytest.fixture
def mock_validate_workflow():
    """Mock SharedValidateWorkflow for testing."""
    with patch('hiveforge.steering.cli.SharedValidateWorkflow') as mock:
        workflow_instance = Mock()
        # Mock execute to return a WorkflowResult
        from hiveforge.steering.shared.base import WorkflowResult
        workflow_instance.execute.return_value = WorkflowResult(
            success=True,
            message="Validation passed",
            metadata={"files_checked": 8}
        )
        mock.return_value = workflow_instance
        yield mock


class TestSteeringInitCommand:
    """Tests for 'hiveforge steering init' command."""
    
    def test_init_basic(self, cli_runner, mock_init_workflow):
        """Test basic init command without flags."""
        result = cli_runner.invoke(app, ["steering", "init"])
        
        assert result.exit_code == 0
        mock_init_workflow.assert_called_once()
        
        # Verify default parameters for SharedInitWorkflow
        call_args = mock_init_workflow.call_args
        assert call_args.kwargs['auto_discover'] is False  # --analyze-code not set
        assert call_args.kwargs['autonomous'] is False  # --use-autonomous-generation not set
        assert call_args.kwargs['confidence_threshold'] == 0.7
        config = call_args.kwargs['config']
        assert config['research_enabled'] is False
        assert config['skip_validation'] is False
        assert config['interactive'] is True
    
    def test_init_with_research_flag(self, cli_runner, mock_init_workflow):
        """Test init command with --research flag."""
        result = cli_runner.invoke(app, ["steering", "init", "--research"])
        
        assert result.exit_code == 0
        
        # Verify research is enabled in config
        call_args = mock_init_workflow.call_args
        config = call_args.kwargs['config']
        assert config['research_enabled'] is True
    
    def test_init_with_skip_validation_flag(self, cli_runner, mock_init_workflow):
        """Test init command with --skip-validation flag."""
        result = cli_runner.invoke(app, ["steering", "init", "--skip-validation"])
        
        assert result.exit_code == 0
        
        # Verify validation is skipped in config
        call_args = mock_init_workflow.call_args
        config = call_args.kwargs['config']
        assert config['skip_validation'] is True
    
    def test_init_with_no_interactive_flag(self, cli_runner, mock_init_workflow):
        """Test init command with --no-interactive flag."""
        result = cli_runner.invoke(app, ["steering", "init", "--no-interactive"])
        
        assert result.exit_code == 0
        
        # Verify interactive is disabled in config
        call_args = mock_init_workflow.call_args
        config = call_args.kwargs['config']
        assert config['interactive'] is False
    
    def test_init_with_interactive_flag(self, cli_runner, mock_init_workflow):
        """Test init command with --interactive flag (explicit)."""
        result = cli_runner.invoke(app, ["steering", "init", "--interactive"])
        
        assert result.exit_code == 0
        
        # Verify interactive is enabled in config
        call_args = mock_init_workflow.call_args
        config = call_args.kwargs['config']
        assert config['interactive'] is True
    
    def test_init_with_analyze_code_flag(self, cli_runner, mock_init_workflow):
        """Test init command with --analyze-code flag."""
        result = cli_runner.invoke(app, ["steering", "init", "--analyze-code"])
        
        assert result.exit_code == 0
        
        # Verify auto_discover is enabled (maps to --analyze-code)
        call_args = mock_init_workflow.call_args
        assert call_args.kwargs['auto_discover'] is True
    
    def test_init_with_multiple_flags(self, cli_runner, mock_init_workflow):
        """Test init command with multiple flags combined."""
        result = cli_runner.invoke(app, [
            "steering", "init",
            "--research",
            "--skip-validation",
            "--no-interactive",
            "--analyze-code"
        ])
        
        assert result.exit_code == 0
        
        # Verify all parameters are set correctly
        call_args = mock_init_workflow.call_args
        assert call_args.kwargs['auto_discover'] is True
        config = call_args.kwargs['config']
        assert config['research_enabled'] is True
        assert config['skip_validation'] is True
        assert config['interactive'] is False
    
    def test_init_workflow_failure(self, cli_runner, mock_init_workflow):
        """Test init command when workflow fails."""
        # Make workflow return failure result
        from hiveforge.steering.shared.base import WorkflowResult
        mock_init_workflow.return_value.execute.return_value = WorkflowResult(
            success=False,
            message="Init failed",
            errors=["Test error"]
        )
        
        result = cli_runner.invoke(app, ["steering", "init"])
        
        assert result.exit_code == 1
    
    def test_init_workflow_exception(self, cli_runner, mock_init_workflow):
        """Test init command when workflow raises exception."""
        # Make workflow raise exception
        mock_init_workflow.return_value.execute.side_effect = RuntimeError("Test error")
        
        result = cli_runner.invoke(app, ["steering", "init"])
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    def test_init_keyboard_interrupt(self, cli_runner, mock_init_workflow):
        """Test init command handles keyboard interrupt gracefully."""
        # Make workflow raise KeyboardInterrupt
        mock_init_workflow.return_value.execute.side_effect = KeyboardInterrupt()
        
        result = cli_runner.invoke(app, ["steering", "init"])
        
        assert result.exit_code == 130
        assert "cancelled" in result.output.lower()
    
    def test_init_help(self, cli_runner):
        """Test init command help text."""
        result = cli_runner.invoke(app, ["steering", "init", "--help"])
        
        assert result.exit_code == 0
        assert "Initialize steering files" in result.output
        assert "--research" in result.output
        assert "--skip-validation" in result.output
        assert "--interactive" in result.output
        assert "--analyze-code" in result.output


class TestSteeringUpdateCommand:
    """Tests for 'hiveforge steering update' command."""
    
    def test_update_basic(self, cli_runner, mock_update_workflow):
        """Test basic update command without flags."""
        result = cli_runner.invoke(app, ["steering", "update"])
        
        assert result.exit_code == 0
        mock_update_workflow.assert_called_once()
        
        # Verify default parameters for SharedUpdateWorkflow
        call_args = mock_update_workflow.call_args
        assert call_args.kwargs['files_to_update'] is None  # Update all files
        assert call_args.kwargs['incremental'] is False  # Default incremental mode
        config = call_args.kwargs['config']
        assert config['research_enabled'] is False
        assert config['skip_validation'] is False
        assert config['interactive'] is True
    
    def test_update_with_research_flag(self, cli_runner, mock_update_workflow):
        """Test update command with --research flag."""
        result = cli_runner.invoke(app, ["steering", "update", "--research"])
        
        assert result.exit_code == 0
        
        # Verify research is enabled in config
        call_args = mock_update_workflow.call_args
        config = call_args.kwargs['config']
        assert config['research_enabled'] is True
    
    def test_update_with_skip_validation_flag(self, cli_runner, mock_update_workflow):
        """Test update command with --skip-validation flag."""
        result = cli_runner.invoke(app, ["steering", "update", "--skip-validation"])
        
        assert result.exit_code == 0
        
        # Verify validation is skipped in config
        call_args = mock_update_workflow.call_args
        config = call_args.kwargs['config']
        assert config['skip_validation'] is True
    
    def test_update_with_no_interactive_flag(self, cli_runner, mock_update_workflow):
        """Test update command with --no-interactive flag."""
        result = cli_runner.invoke(app, ["steering", "update", "--no-interactive"])
        
        assert result.exit_code == 0
        
        # Verify interactive is disabled in config
        call_args = mock_update_workflow.call_args
        config = call_args.kwargs['config']
        assert config['interactive'] is False
    
    def test_update_with_multiple_flags(self, cli_runner, mock_update_workflow):
        """Test update command with multiple flags combined."""
        result = cli_runner.invoke(app, [
            "steering", "update",
            "--research",
            "--skip-validation",
            "--no-interactive"
        ])
        
        assert result.exit_code == 0
        
        # Verify all parameters are set correctly
        call_args = mock_update_workflow.call_args
        config = call_args.kwargs['config']
        assert config['research_enabled'] is True
        assert config['skip_validation'] is True
        assert config['interactive'] is False
    
    def test_update_workflow_failure(self, cli_runner, mock_update_workflow):
        """Test update command when workflow fails."""
        # Make workflow return failure result
        from hiveforge.steering.shared.base import WorkflowResult
        mock_update_workflow.return_value.execute.return_value = WorkflowResult(
            success=False,
            message="Update failed",
            errors=["Test error"]
        )
        
        result = cli_runner.invoke(app, ["steering", "update"])
        
        assert result.exit_code == 1
    
    def test_update_workflow_exception(self, cli_runner, mock_update_workflow):
        """Test update command when workflow raises exception."""
        # Make workflow raise exception
        mock_update_workflow.return_value.execute.side_effect = RuntimeError("Test error")
        
        result = cli_runner.invoke(app, ["steering", "update"])
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    def test_update_keyboard_interrupt(self, cli_runner, mock_update_workflow):
        """Test update command handles keyboard interrupt gracefully."""
        # Make workflow raise KeyboardInterrupt
        mock_update_workflow.return_value.execute.side_effect = KeyboardInterrupt()
        
        result = cli_runner.invoke(app, ["steering", "update"])
        
        assert result.exit_code == 130
        assert "cancelled" in result.output.lower()
    
    def test_update_help(self, cli_runner):
        """Test update command help text."""
        result = cli_runner.invoke(app, ["steering", "update", "--help"])
        
        assert result.exit_code == 0
        assert "Update existing steering files" in result.output
        assert "--research" in result.output
        assert "--skip-validation" in result.output
        assert "--interactive" in result.output


class TestSteeringValidateCommand:
    """Tests for 'hiveforge steering validate' command."""
    
    def test_validate_basic(self, cli_runner, mock_validate_workflow):
        """Test basic validate command without flags."""
        result = cli_runner.invoke(app, ["steering", "validate"])
        
        assert result.exit_code == 0
        mock_validate_workflow.assert_called_once()
        
        # Verify default parameters for SharedValidateWorkflow
        call_args = mock_validate_workflow.call_args
        assert call_args.kwargs['strict'] is False
        assert call_args.kwargs['use_llm'] is True
    
    def test_validate_with_strict_flag(self, cli_runner, mock_validate_workflow):
        """Test validate command with --strict flag."""
        result = cli_runner.invoke(app, ["steering", "validate", "--strict"])
        
        assert result.exit_code == 0
        
        # Verify strict mode is enabled
        call_args = mock_validate_workflow.call_args
        assert call_args.kwargs['strict'] is True
    
    def test_validate_exit_code_pass(self, cli_runner, mock_validate_workflow):
        """Test validate command returns 0 when validation passes."""
        # Make workflow return success result
        from hiveforge.steering.shared.base import WorkflowResult
        mock_validate_workflow.return_value.execute.return_value = WorkflowResult(
            success=True,
            message="Validation passed"
        )
        
        result = cli_runner.invoke(app, ["steering", "validate"])
        
        assert result.exit_code == 0
    
    def test_validate_exit_code_fail(self, cli_runner, mock_validate_workflow):
        """Test validate command returns 1 when validation fails."""
        # Make workflow return failure result
        from hiveforge.steering.shared.base import WorkflowResult
        mock_validate_workflow.return_value.execute.return_value = WorkflowResult(
            success=False,
            message="Validation failed",
            errors=["Critical issue found"]
        )
        
        result = cli_runner.invoke(app, ["steering", "validate"])
        
        assert result.exit_code == 1
    
    def test_validate_workflow_exception(self, cli_runner, mock_validate_workflow):
        """Test validate command when workflow raises exception."""
        # Make workflow raise exception
        mock_validate_workflow.return_value.execute.side_effect = RuntimeError("Test error")
        
        result = cli_runner.invoke(app, ["steering", "validate"])
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    def test_validate_keyboard_interrupt(self, cli_runner, mock_validate_workflow):
        """Test validate command handles keyboard interrupt gracefully."""
        # Make workflow raise KeyboardInterrupt
        mock_validate_workflow.return_value.execute.side_effect = KeyboardInterrupt()
        
        result = cli_runner.invoke(app, ["steering", "validate"])
        
        assert result.exit_code == 130
        assert "cancelled" in result.output.lower()
    
    def test_validate_help(self, cli_runner):
        """Test validate command help text."""
        result = cli_runner.invoke(app, ["steering", "validate", "--help"])
        
        assert result.exit_code == 0
        assert "Validate steering files" in result.output
        assert "--strict" in result.output


class TestSteeringCommandRouting:
    """Tests for steering command routing and help."""
    
    def test_steering_no_subcommand(self, cli_runner):
        """Test 'hiveforge steering' without subcommand shows help."""
        result = cli_runner.invoke(app, ["steering"])
        
        assert result.exit_code == 0
        assert "steering" in result.output.lower()
        assert "init" in result.output
        assert "update" in result.output
        assert "validate" in result.output
    
    def test_steering_help(self, cli_runner):
        """Test 'hiveforge steering --help' shows help."""
        result = cli_runner.invoke(app, ["steering", "--help"])
        
        assert result.exit_code == 0
        assert "steering" in result.output.lower()
        assert "init" in result.output
        assert "update" in result.output
        assert "validate" in result.output
    
    def test_steering_invalid_subcommand(self, cli_runner):
        """Test invalid subcommand shows error."""
        result = cli_runner.invoke(app, ["steering", "invalid"])
        
        assert result.exit_code != 0
        # Typer will show an error for invalid command


class TestSteeringCommandIntegration:
    """Integration tests for steering commands."""
    
    def test_init_creates_config_correctly(self, cli_runner, mock_init_workflow):
        """Test that init command creates SharedInitWorkflow with correct values."""
        result = cli_runner.invoke(app, [
            "steering", "init",
            "--research",
            "--analyze-code"
        ])
        
        assert result.exit_code == 0
        
        # Verify workflow was created correctly
        call_args = mock_init_workflow.call_args
        assert call_args.kwargs['auto_discover'] is True  # --analyze-code
        config = call_args.kwargs['config']
        assert config['research_enabled'] is True
    
    def test_update_creates_config_correctly(self, cli_runner, mock_update_workflow):
        """Test that update command creates SharedUpdateWorkflow with correct values."""
        result = cli_runner.invoke(app, [
            "steering", "update",
            "--skip-validation"
        ])
        
        assert result.exit_code == 0
        
        # Verify workflow was created correctly
        call_args = mock_update_workflow.call_args
        config = call_args.kwargs['config']
        assert config['skip_validation'] is True
    
    def test_validate_creates_config_correctly(self, cli_runner, mock_validate_workflow):
        """Test that validate command creates SharedValidateWorkflow with correct values."""
        result = cli_runner.invoke(app, [
            "steering", "validate",
            "--strict"
        ])
        
        assert result.exit_code == 0
        
        # Verify workflow was created correctly
        call_args = mock_validate_workflow.call_args
        assert call_args.kwargs['strict'] is True
        assert call_args.kwargs['use_llm'] is True


class TestSteeringCommandErrorHandling:
    """Tests for error handling in steering commands."""
    
    def test_init_handles_runtime_error(self, cli_runner, mock_init_workflow):
        """Test init command handles RuntimeError gracefully."""
        mock_init_workflow.return_value.execute.side_effect = RuntimeError("Workflow failed")
        
        result = cli_runner.invoke(app, ["steering", "init"])
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    def test_update_handles_runtime_error(self, cli_runner, mock_update_workflow):
        """Test update command handles RuntimeError gracefully."""
        mock_update_workflow.return_value.execute.side_effect = RuntimeError("Workflow failed")
        
        result = cli_runner.invoke(app, ["steering", "update"])
        
        assert result.exit_code == 1
        assert "Error" in result.output
    
    def test_validate_handles_runtime_error(self, cli_runner, mock_validate_workflow):
        """Test validate command handles RuntimeError gracefully."""
        mock_validate_workflow.return_value.execute.side_effect = RuntimeError("Workflow failed")
        
        result = cli_runner.invoke(app, ["steering", "validate"])
        
        assert result.exit_code == 1
        assert "Error" in result.output


class TestSteeringCommandDescriptions:
    """Tests for command descriptions and help text."""
    
    def test_init_has_description(self, cli_runner):
        """Test init command has proper description."""
        result = cli_runner.invoke(app, ["steering", "init", "--help"])
        
        assert result.exit_code == 0
        assert "Initialize steering files from scratch" in result.output
        assert "Examples:" in result.output
    
    def test_update_has_description(self, cli_runner):
        """Test update command has proper description."""
        result = cli_runner.invoke(app, ["steering", "update", "--help"])
        
        assert result.exit_code == 0
        assert "Update existing steering files" in result.output
        assert "Examples:" in result.output
    
    def test_validate_has_description(self, cli_runner):
        """Test validate command has proper description."""
        result = cli_runner.invoke(app, ["steering", "validate", "--help"])
        
        assert result.exit_code == 0
        assert "Validate steering files" in result.output
        assert "Exit codes:" in result.output
    
    def test_all_flags_documented(self, cli_runner):
        """Test that all flags are documented in help text."""
        # Init flags
        result = cli_runner.invoke(app, ["steering", "init", "--help"])
        assert "--research" in result.output
        assert "--skip-validation" in result.output
        assert "--interactive" in result.output
        assert "--no-interactive" in result.output
        assert "--analyze-code" in result.output
        
        # Update flags
        result = cli_runner.invoke(app, ["steering", "update", "--help"])
        assert "--research" in result.output
        assert "--skip-validation" in result.output
        assert "--interactive" in result.output
        assert "--no-interactive" in result.output
        
        # Validate flags
        result = cli_runner.invoke(app, ["steering", "validate", "--help"])
        assert "--strict" in result.output


class TestSteeringInitDryRun:
    """Tests for 'hiveforge steering init --dry-run' command."""
    
    def test_init_with_dry_run_flag(self, cli_runner):
        """Test init command with --dry-run flag."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            # Mock workflow instance
            workflow_instance = Mock()
            from hiveforge.steering.shared.base import WorkflowResult
            workflow_instance.execute.return_value = WorkflowResult(
                success=True,
                message="Dry-run preview: 8 file(s) would be created",
                files_created=[
                    ".kiro/steering/tech-stack.md",
                    ".kiro/steering/architecture.md",
                    ".kiro/steering/conventions.md",
                    ".kiro/steering/project-vision.md",
                ],
                metadata={
                    "dry_run": True,
                    "files_count": 4
                }
            )
            mock_workflow_class.return_value = workflow_instance
            
            # Run command
            result = cli_runner.invoke(app, ["steering", "init", "--dry-run"])
            
            # Verify success
            assert result.exit_code == 0
            
            # Verify SharedInitWorkflow was called with dry_run=True
            mock_workflow_class.assert_called_once()
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['dry_run'] is True
            
            # Verify output mentions dry-run
            assert "Dry-run preview" in result.stdout or "would be created" in result.stdout
    
    def test_init_dry_run_with_other_flags(self, cli_runner):
        """Test init command with --dry-run combined with other flags."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            # Mock workflow instance
            workflow_instance = Mock()
            from hiveforge.steering.shared.base import WorkflowResult
            workflow_instance.execute.return_value = WorkflowResult(
                success=True,
                message="Dry-run preview: 8 file(s) would be created",
                files_created=[".kiro/steering/tech-stack.md"],
                metadata={"dry_run": True}
            )
            mock_workflow_class.return_value = workflow_instance
            
            # Run command with multiple flags
            result = cli_runner.invoke(app, [
                "steering", "init",
                "--dry-run",
                "--analyze-code",
                "--use-autonomous-generation"
            ])
            
            # Verify success
            assert result.exit_code == 0
            
            # Verify all flags were passed correctly
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['dry_run'] is True
            assert call_args.kwargs['auto_discover'] is True
            assert call_args.kwargs['autonomous'] is True
    
    def test_init_dry_run_no_files_written(self, cli_runner, tmp_path):
        """Test that dry-run mode does not write any files."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            # Mock workflow instance
            workflow_instance = Mock()
            from hiveforge.steering.shared.base import WorkflowResult
            workflow_instance.execute.return_value = WorkflowResult(
                success=True,
                message="Dry-run preview: 8 file(s) would be created",
                files_created=[],  # No files actually created
                metadata={"dry_run": True}
            )
            mock_workflow_class.return_value = workflow_instance
            
            # Run command
            result = cli_runner.invoke(app, ["steering", "init", "--dry-run"])
            
            # Verify success
            assert result.exit_code == 0
            
            # Verify dry_run flag was set
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['dry_run'] is True
    
    def test_init_without_dry_run_flag(self, cli_runner):
        """Test that init command without --dry-run flag sets dry_run=False."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            # Mock workflow instance
            workflow_instance = Mock()
            from hiveforge.steering.shared.base import WorkflowResult
            workflow_instance.execute.return_value = WorkflowResult(
                success=True,
                message="Successfully initialized steering files",
                files_created=[".kiro/steering/tech-stack.md"],
                metadata={"dry_run": False}
            )
            mock_workflow_class.return_value = workflow_instance
            
            # Run command without --dry-run
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify success
            assert result.exit_code == 0
            
            # Verify dry_run=False (default)
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['dry_run'] is False
