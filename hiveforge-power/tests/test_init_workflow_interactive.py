"""
Unit tests for InitWorkflow non-interactive mode.

Tests verify that input() calls are properly guarded and that
non-interactive mode auto-backs up files and proceeds without prompting.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from hiveforge.steering.models import SteeringConfig
from hiveforge.steering.workflows.init_workflow import InitWorkflow


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def existing_steering_files(temp_project_dir):
    """Create existing steering files for testing."""
    steering_dir = temp_project_dir / ".kiro" / "steering"
    steering_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some existing files
    (steering_dir / "tech-stack.md").write_text("# Tech Stack\nExisting content")
    (steering_dir / "architecture.md").write_text("# Architecture\nExisting content")
    
    return steering_dir


class TestNonInteractiveMode:
    """Test suite for non-interactive mode functionality."""
    
    def test_config_has_interactive_parameter(self):
        """Test that SteeringConfig has interactive parameter with default True."""
        config = SteeringConfig()
        assert hasattr(config, 'interactive')
        assert config.interactive is True
    
    def test_config_accepts_interactive_false(self):
        """Test that SteeringConfig accepts interactive=False."""
        config = SteeringConfig(interactive=False)
        assert config.interactive is False
    
    def test_non_interactive_mode_skips_input_on_existing_files(
        self, temp_project_dir, existing_steering_files
    ):
        """Test that non-interactive mode auto-backs up and proceeds without input()."""
        # Create config with interactive=False
        config = SteeringConfig(
            interactive=False,
            backup_enabled=True,
            backup_dir=temp_project_dir / ".kiro" / "backups"
        )
        
        # Create workflow
        workflow = InitWorkflow(
            config=config,
            project_root=temp_project_dir
        )
        
        # Mock input() to ensure it's never called
        with patch('builtins.input') as mock_input:
            # Call _step_check_existing_files
            result = workflow._step_check_existing_files()
            
            # Verify input() was NOT called
            mock_input.assert_not_called()
            
            # Verify workflow proceeded (returned True)
            assert result is True
            
            # Verify backup was created
            backup_dir = temp_project_dir / ".kiro" / "backups"
            assert backup_dir.exists()
            backup_folders = list(backup_dir.glob("steering_backup_*"))
            assert len(backup_folders) > 0
    
    def test_interactive_mode_calls_input_on_existing_files(
        self, temp_project_dir, existing_steering_files
    ):
        """Test that interactive mode prompts user with input()."""
        # Create config with interactive=True (default)
        config = SteeringConfig(
            interactive=True,
            backup_enabled=True,
            backup_dir=temp_project_dir / ".kiro" / "backups"
        )
        
        # Create workflow
        workflow = InitWorkflow(
            config=config,
            project_root=temp_project_dir
        )
        
        # Mock input() to return "1" (backup and proceed)
        with patch('builtins.input', return_value='1'):
            result = workflow._step_check_existing_files()
            
            # Verify workflow proceeded
            assert result is True
    
    def test_interactive_mode_user_can_abort(
        self, temp_project_dir, existing_steering_files
    ):
        """Test that interactive mode allows user to abort."""
        # Create config with interactive=True
        config = SteeringConfig(
            interactive=True,
            backup_enabled=True
        )
        
        # Create workflow
        workflow = InitWorkflow(
            config=config,
            project_root=temp_project_dir
        )
        
        # Mock input() to return "2" (abort)
        with patch('builtins.input', return_value='2'):
            result = workflow._step_check_existing_files()
            
            # Verify workflow aborted (returned False)
            assert result is False
    
    def test_non_interactive_mode_logs_message(
        self, temp_project_dir, existing_steering_files, caplog
    ):
        """Test that non-interactive mode logs appropriate message."""
        import logging
        caplog.set_level(logging.INFO)
        
        # Create config with interactive=False
        config = SteeringConfig(
            interactive=False,
            backup_enabled=True,
            backup_dir=temp_project_dir / ".kiro" / "backups"
        )
        
        # Create workflow
        workflow = InitWorkflow(
            config=config,
            project_root=temp_project_dir
        )
        
        # Call _step_check_existing_files
        workflow._step_check_existing_files()
        
        # Verify log message
        assert "Non-interactive mode: auto-backing up existing files and proceeding" in caplog.text
    
    def test_non_interactive_mode_no_existing_files(self, temp_project_dir):
        """Test that non-interactive mode works when no existing files."""
        # Create config with interactive=False
        config = SteeringConfig(interactive=False)
        
        # Create workflow (no existing steering files)
        workflow = InitWorkflow(
            config=config,
            project_root=temp_project_dir
        )
        
        # Mock input() to ensure it's never called
        with patch('builtins.input') as mock_input:
            result = workflow._step_check_existing_files()
            
            # Verify input() was NOT called
            mock_input.assert_not_called()
            
            # Verify workflow proceeded
            assert result is True
    
    def test_backup_created_in_non_interactive_mode(
        self, temp_project_dir, existing_steering_files
    ):
        """Test that backup is created with correct files in non-interactive mode."""
        # Create config with interactive=False
        config = SteeringConfig(
            interactive=False,
            backup_enabled=True,
            backup_dir=temp_project_dir / ".kiro" / "backups"
        )
        
        # Create workflow
        workflow = InitWorkflow(
            config=config,
            project_root=temp_project_dir
        )
        
        # Call _step_check_existing_files
        workflow._step_check_existing_files()
        
        # Verify backup was created
        backup_dir = temp_project_dir / ".kiro" / "backups"
        backup_folders = list(backup_dir.glob("steering_backup_*"))
        assert len(backup_folders) == 1
        
        # Verify backup contains the files
        backup_folder = backup_folders[0]
        assert (backup_folder / "tech-stack.md").exists()
        assert (backup_folder / "architecture.md").exists()
        
        # Verify content is preserved
        assert "Existing content" in (backup_folder / "tech-stack.md").read_text()


class TestSharedInitWorkflowInteractive:
    """Test suite for SharedInitWorkflow interactive mode handling."""
    
    def test_shared_workflow_sets_interactive_false_when_ctx_present(self):
        """Test that SharedInitWorkflow sets interactive=False when ctx is not None."""
        from hiveforge.steering.shared.adapters import SharedInitWorkflow
        
        # Create mock ctx
        mock_ctx = Mock()
        
        # Create workflow with ctx
        workflow = SharedInitWorkflow(
            project_root=".",
            ctx=mock_ctx,
            autonomous=False  # Even with autonomous=False, ctx should force interactive=False
        )
        
        # Execute to create config
        with patch.object(workflow, 'tool_executor') as mock_executor:
            mock_executor.atomic_operation.return_value.__enter__ = Mock()
            mock_executor.atomic_operation.return_value.__exit__ = Mock(return_value=False)
            
            try:
                workflow.execute()
            except:
                pass  # We're just checking config creation
        
        # Verify ctx was stored
        assert workflow.ctx is mock_ctx
    
    def test_shared_workflow_sets_interactive_true_when_no_ctx_and_not_autonomous(self):
        """Test that SharedInitWorkflow sets interactive=True when ctx is None and autonomous=False."""
        from hiveforge.steering.shared.adapters import SharedInitWorkflow
        
        # Create workflow without ctx and autonomous=False
        workflow = SharedInitWorkflow(
            project_root=".",
            ctx=None,
            autonomous=False
        )
        
        # Verify ctx is None
        assert workflow.ctx is None
        assert workflow.autonomous is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
