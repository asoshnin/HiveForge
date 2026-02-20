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


class TestCLINewParameters:
    """Tests for new CLI parameters added in v2.2.0."""
    
    def test_init_with_dry_run_flag(self, cli_runner):
        """Test that init command passes dry_run parameter correctly."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = "Preview output"
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "init",
                "--dry-run"
            ])
            
            # Verify workflow was created with dry_run=True
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['dry_run'] is True
            
            # Verify workflow was executed
            mock_workflow.execute.assert_called_once()
            
            # Verify output contains preview
            assert "Preview output" in result.output
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_without_dry_run_flag(self, cli_runner):
        """Test that init command defaults dry_run to False."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = "Success"
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify workflow was created with dry_run=False (default)
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['dry_run'] is False
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_dry_run_displays_preview_without_writing_files(self, cli_runner):
        """Test that dry-run mode displays preview without writing files."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = (
                "DRY RUN MODE - No files written\n"
                "Preview of steering files:\n"
                "- tech-stack.md\n"
                "- architecture.md\n"
            )
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "init",
                "--dry-run"
            ])
            
            # Verify preview is displayed
            assert "DRY RUN MODE" in result.output
            assert "No files written" in result.output
            assert "Preview" in result.output
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_dry_run_with_other_flags(self, cli_runner):
        """Test that dry-run works with other flags."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = "Preview"
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "init",
                "--dry-run",
                "--research",
                "--analyze-code"
            ])
            
            # Verify all parameters were passed
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['dry_run'] is True
            assert call_args.kwargs['config']['research_enabled'] is True
            assert call_args.kwargs['auto_discover'] is True
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_dry_run_handles_errors_gracefully(self, cli_runner):
        """Test that dry-run mode handles errors gracefully."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = RuntimeError("Dry run failed")
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "init",
                "--dry-run"
            ])
            
            # Verify error is displayed
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "Dry run failed" in result.output


class TestCLIOutputFormatting:
    """Tests for CLI output formatting with new features."""
    
    def test_init_displays_confidence_metadata(self, cli_runner):
        """Test that init command displays confidence metadata in output."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = (
                "✓ Steering files created successfully\n"
                "Confidence: HIGH (0.85)\n"
                "Source documents: 5 found\n"
            )
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify confidence metadata is displayed
            assert "Confidence" in result.output
            assert "Source documents" in result.output
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_displays_low_confidence_warning(self, cli_runner):
        """Test that init command displays warning for low confidence."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = (
                "⚠️  Warning: Low confidence (0.25)\n"
                "No source documents found in .kiro/onboarding/\n"
                "Consider using --analyze-code or providing documentation\n"
            )
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify warning is displayed
            assert "Warning" in result.output or "⚠️" in result.output
            assert "Low confidence" in result.output or "confidence" in result.output.lower()
            
            # Verify exit code (should still be 0 - warning, not error)
            assert result.exit_code == 0
    
    def test_init_displays_inferred_sections_notice(self, cli_runner):
        """Test that init command displays notice about inferred sections."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = (
                "✓ Steering files created\n"
                "Note: Some sections marked as [INFERRED] - review and update as needed\n"
            )
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify notice is displayed
            assert "[INFERRED]" in result.output or "inferred" in result.output.lower()
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_displays_discovery_statistics(self, cli_runner):
        """Test that init command displays discovery statistics."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = (
                "✓ Steering files created\n"
                "Discovery statistics:\n"
                "  - Files discovered: 42\n"
                "  - Files included: 38\n"
                "  - Files excluded: 4\n"
            )
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify statistics are displayed
            assert "discovered" in result.output.lower() or "Discovery" in result.output
            
            # Verify exit code
            assert result.exit_code == 0


class TestCLIErrorHandlingNewFeatures:
    """Tests for error handling with new features."""
    
    def test_init_handles_empty_source_folder_gracefully(self, cli_runner):
        """Test that init command handles empty source folder with clear message."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = (
                "⚠️  Warning: No source documents found\n"
                "Steering files created with inferred content\n"
                "Confidence: LOW (0.30)\n"
            )
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify warning is displayed
            assert "Warning" in result.output or "⚠️" in result.output
            assert "No source documents" in result.output or "no source" in result.output.lower()
            
            # Verify exit code (warning, not error)
            assert result.exit_code == 0
    
    def test_init_handles_confidence_calculation_failure(self, cli_runner):
        """Test that init command handles confidence calculation failure."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = RuntimeError(
                "Failed to calculate confidence scores"
            )
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify error is displayed
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "confidence" in result.output.lower()
    
    def test_init_handles_tagging_failure(self, cli_runner):
        """Test that init command handles content tagging failure."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_workflow.execute.side_effect = RuntimeError(
                "Failed to tag inferred sections"
            )
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify error is displayed
            assert result.exit_code == 1
            assert "Error" in result.output
            assert "tag" in result.output.lower() or "Failed" in result.output


class TestCLIBackwardCompatibility:
    """Tests to ensure backward compatibility with existing CLI behavior."""
    
    def test_init_without_new_parameters_works_as_before(self, cli_runner):
        """Test that init command works without new parameters (backward compatibility)."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = "Success"
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, ["steering", "init"])
            
            # Verify workflow was created with defaults
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['dry_run'] is False
            assert call_args.kwargs['project_root'] == Path.cwd()
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_with_existing_flags_still_works(self, cli_runner):
        """Test that existing flags still work with new features."""
        with patch('hiveforge.steering.cli.SharedInitWorkflow') as mock_workflow_class:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.success = True
            mock_result.format_for_cli.return_value = "Success"
            mock_workflow.execute.return_value = mock_result
            mock_workflow_class.return_value = mock_workflow
            
            result = cli_runner.invoke(app, [
                "steering", "init",
                "--research",
                "--analyze-code",
                "--no-interactive"
            ])
            
            # Verify all existing flags work
            call_args = mock_workflow_class.call_args
            assert call_args.kwargs['config']['research_enabled'] is True
            assert call_args.kwargs['auto_discover'] is True
            assert call_args.kwargs['config']['interactive'] is False
            
            # Verify exit code
            assert result.exit_code == 0
    
    def test_init_help_text_includes_new_flags(self, cli_runner):
        """Test that help text includes documentation for new flags."""
        result = cli_runner.invoke(app, ["steering", "init", "--help"])
        
        # Verify help text includes dry-run flag
        assert "--dry-run" in result.output
        assert "preview" in result.output.lower() or "Preview" in result.output
        
        # Verify exit code
        assert result.exit_code == 0
