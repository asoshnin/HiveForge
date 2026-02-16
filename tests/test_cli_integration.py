"""
Integration tests for CLI command integration with workflow orchestrators.

This module tests the complete integration between CLI commands and workflow
orchestrators, including:
- Command-line argument parsing and validation
- Progress feedback during operations
- Error handling with clear messages
- Exit codes

Requirements: 14.1-14.6, 15.2
"""

import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock, call
import sys

from hiveforge.cli import app
from hiveforge.steering.models import SteeringConfig


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


class TestCLIWorkflowIntegration:
    """Tests for CLI integration with workflow orchestrators."""
    
    def test_init_command_creates_workflow_with_correct_config(self, cli_runner):
        """Test that init command creates InitWorkflow with correct configuration."""
        with patch('hiveforge.steering.cli.InitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "init",
                "--research",
                "--analyze-code",
                "--skip-validation"
            ])
            
            # Verify workflow was created
            assert mock_workflow_class.called
            
            # Verify config passed to workflow
            call_args = mock_workflow_class.call_args
            config = call_args.kwargs['config']
            
            assert isinstance(config, SteeringConfig)
            assert config.research_enabled is True
            assert config.analyze_code is True
            assert config.skip_validation is True
            assert config.interactive is True  # Default
            assert config.backup_enabled is True
            
            # Verify workflow was executed
            mock_workflow.execute.assert_called_once()
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_update_command_creates_workflow_with_correct_config(self, cli_runner):
        """Test that update command creates UpdateWorkflow with correct configuration."""
        with patch('hiveforge.steering.cli.UpdateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "update",
                "--no-interactive",
                "--research"
            ])
            
            # Verify workflow was created
            assert mock_workflow_class.called
            
            # Verify config passed to workflow
            call_args = mock_workflow_class.call_args
            config = call_args.kwargs['config']
            
            assert isinstance(config, SteeringConfig)
            assert config.research_enabled is True
            assert config.interactive is False
            assert config.analyze_code is False  # Update never does code analysis
            assert config.backup_enabled is True
            
            # Verify workflow was executed
            mock_workflow.execute.assert_called_once()
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_validate_command_creates_workflow_with_correct_config(self, cli_runner):
        """Test that validate command creates ValidateWorkflow with correct configuration."""
        with patch('hiveforge.steering.cli.ValidateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = 0
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "validate",
                "--strict"
            ])
            
            # Verify workflow was created
            assert mock_workflow_class.called
            
            # Verify config passed to workflow
            call_args = mock_workflow_class.call_args
            config = call_args.kwargs['config']
            
            assert isinstance(config, SteeringConfig)
            assert config.strict_mode is True
            assert config.research_enabled is False
            assert config.interactive is False
            assert config.backup_enabled is False
            
            # Verify workflow was executed
            mock_workflow.execute.assert_called_once()
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_command_handles_workflow_failure(self, cli_runner):
        """Test that init command handles workflow failure gracefully."""
        with patch('hiveforge.steering.cli.InitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = False  # Workflow failed
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify exit code indicates failure
            assert result.exit_code == 1
    
    def test_update_command_handles_workflow_failure(self, cli_runner):
        """Test that update command handles workflow failure gracefully."""
        with patch('hiveforge.steering.cli.UpdateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = False  # Workflow failed
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "update"])
            
            # Verify exit code indicates failure
            assert result.exit_code == 1
    
    def test_validate_command_propagates_exit_code(self, cli_runner):
        """Test that validate command propagates workflow exit code."""
        with patch('hiveforge.steering.cli.ValidateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = 1  # Validation failed
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "validate"])
            
            # Verify exit code matches workflow exit code
            assert result.exit_code == 1


class TestCLIErrorHandling:
    """Tests for CLI error handling."""
    
    def test_init_handles_runtime_error_with_clear_message(self, cli_runner):
        """Test that init command displays clear error message on RuntimeError."""
        with patch('hiveforge.steering.cli.InitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = RuntimeError("Test error message")
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify error message is displayed
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "Test error message" in result.output
    
    def test_update_handles_runtime_error_with_clear_message(self, cli_runner):
        """Test that update command displays clear error message on RuntimeError."""
        with patch('hiveforge.steering.cli.UpdateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = RuntimeError("Update failed")
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "update"])
            
            # Verify error message is displayed
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "Update failed" in result.output
    
    def test_validate_handles_runtime_error_with_clear_message(self, cli_runner):
        """Test that validate command displays clear error message on RuntimeError."""
        with patch('hiveforge.steering.cli.ValidateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = RuntimeError("Validation error")
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "validate"])
            
            # Verify error message is displayed
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "Validation error" in result.output
    
    def test_init_handles_keyboard_interrupt_gracefully(self, cli_runner):
        """Test that init command handles KeyboardInterrupt with user-friendly message."""
        with patch('hiveforge.steering.cli.InitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = KeyboardInterrupt()
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify graceful handling
            assert result.exit_code == 130
            assert "cancelled" in result.output.lower()
    
    def test_update_handles_keyboard_interrupt_gracefully(self, cli_runner):
        """Test that update command handles KeyboardInterrupt with user-friendly message."""
        with patch('hiveforge.steering.cli.UpdateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = KeyboardInterrupt()
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "update"])
            
            # Verify graceful handling
            assert result.exit_code == 130
            assert "cancelled" in result.output.lower()
    
    def test_validate_handles_keyboard_interrupt_gracefully(self, cli_runner):
        """Test that validate command handles KeyboardInterrupt with user-friendly message."""
        with patch('hiveforge.steering.cli.ValidateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = KeyboardInterrupt()
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "validate"])
            
            # Verify graceful handling
            assert result.exit_code == 130
            assert "cancelled" in result.output.lower()


class TestCLIArgumentParsing:
    """Tests for command-line argument parsing and validation."""
    
    def test_init_parses_all_flags_correctly(self, cli_runner):
        """Test that init command parses all flags correctly."""
        with patch('hiveforge.steering.cli.InitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "init",
                "--research",
                "--skip-validation",
                "--no-interactive",
                "--analyze-code"
            ])
            
            # Verify all flags were parsed correctly
            config = mock_workflow_class.call_args.kwargs['config']
            assert config.research_enabled is True
            assert config.skip_validation is True
            assert config.interactive is False
            assert config.analyze_code is True
    
    def test_update_parses_all_flags_correctly(self, cli_runner):
        """Test that update command parses all flags correctly."""
        with patch('hiveforge.steering.cli.UpdateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "update",
                "--research",
                "--skip-validation",
                "--no-interactive"
            ])
            
            # Verify all flags were parsed correctly
            config = mock_workflow_class.call_args.kwargs['config']
            assert config.research_enabled is True
            assert config.skip_validation is True
            assert config.interactive is False
    
    def test_validate_parses_strict_flag_correctly(self, cli_runner):
        """Test that validate command parses strict flag correctly."""
        with patch('hiveforge.steering.cli.ValidateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = 0
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "validate",
                "--strict"
            ])
            
            # Verify strict flag was parsed correctly
            config = mock_workflow_class.call_args.kwargs['config']
            assert config.strict_mode is True
    
    def test_init_uses_correct_defaults(self, cli_runner):
        """Test that init command uses correct default values."""
        with patch('hiveforge.steering.cli.InitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify defaults
            config = mock_workflow_class.call_args.kwargs['config']
            assert config.research_enabled is False
            assert config.skip_validation is False
            assert config.interactive is True
            assert config.analyze_code is False
            assert config.backup_enabled is True
    
    def test_update_uses_correct_defaults(self, cli_runner):
        """Test that update command uses correct default values."""
        with patch('hiveforge.steering.cli.UpdateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "update"])
            
            # Verify defaults
            config = mock_workflow_class.call_args.kwargs['config']
            assert config.research_enabled is False
            assert config.skip_validation is False
            assert config.interactive is True
            assert config.analyze_code is False
            assert config.backup_enabled is True
    
    def test_validate_uses_correct_defaults(self, cli_runner):
        """Test that validate command uses correct default values."""
        with patch('hiveforge.steering.cli.ValidateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = 0
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "validate"])
            
            # Verify defaults
            config = mock_workflow_class.call_args.kwargs['config']
            assert config.strict_mode is False
            assert config.research_enabled is False
            assert config.interactive is False
            assert config.backup_enabled is False


class TestCLIProjectRootHandling:
    """Tests for project root directory handling."""
    
    def test_init_passes_current_directory_as_project_root(self, cli_runner):
        """Test that init command passes current directory as project root."""
        with patch('hiveforge.steering.cli.InitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow_class.return_value = mock_workflow
            
            with patch('hiveforge.steering.cli.Path.cwd') as mock_cwd:
                mock_cwd.return_value = Path("/test/project")
                
                result = cli_runner.invoke(app, ["steering", "init"])
                
                # Verify project_root was passed
                call_args = mock_workflow_class.call_args
                assert call_args.kwargs['project_root'] == Path("/test/project")
    
    def test_update_passes_current_directory_as_project_root(self, cli_runner):
        """Test that update command passes current directory as project root."""
        with patch('hiveforge.steering.cli.UpdateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = True
            mock_workflow_class.return_value = mock_workflow
            
            with patch('hiveforge.steering.cli.Path.cwd') as mock_cwd:
                mock_cwd.return_value = Path("/test/project")
                
                result = cli_runner.invoke(app, ["steering", "update"])
                
                # Verify project_root was passed
                call_args = mock_workflow_class.call_args
                assert call_args.kwargs['project_root'] == Path("/test/project")
    
    def test_validate_passes_current_directory_as_project_root(self, cli_runner):
        """Test that validate command passes current directory as project root."""
        with patch('hiveforge.steering.cli.ValidateWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.return_value = 0
            mock_workflow_class.return_value = mock_workflow
            
            with patch('hiveforge.steering.cli.Path.cwd') as mock_cwd:
                mock_cwd.return_value = Path("/test/project")
                
                result = cli_runner.invoke(app, ["steering", "validate"])
                
                # Verify project_root was passed
                call_args = mock_workflow_class.call_args
                assert call_args.kwargs['project_root'] == Path("/test/project")
