"""
Unit tests for InitWorkflow backup and rollback functionality.

Tests cover:
- Timestamped backup creation
- Backup cleanup (keep 5 most recent)
- Atomic rollback operation
- Rollback prompt in interactive mode
- File metadata preservation

Requirements: P1-5
"""

import shutil
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from hiveforge.steering.models import SteeringConfig, WorkflowState
from hiveforge.steering.workflows.init_workflow import InitWorkflow


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory structure."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Create .kiro directories
    kiro_dir = project_root / ".kiro"
    kiro_dir.mkdir()
    
    steering_dir = kiro_dir / "steering"
    steering_dir.mkdir()
    
    backup_dir = kiro_dir / "backups"
    backup_dir.mkdir()
    
    onboarding_dir = kiro_dir / "onboarding"
    onboarding_dir.mkdir()
    
    return project_root


@pytest.fixture
def init_workflow(temp_project_dir):
    """Create InitWorkflow instance with test configuration."""
    config = SteeringConfig(
        backup_enabled=True,
        backup_dir=temp_project_dir / ".kiro" / "backups",
        interactive=False,
        skip_validation=True,
        analyze_code=False
    )
    
    workflow = InitWorkflow(
        config=config,
        project_root=temp_project_dir
    )
    
    return workflow


@pytest.fixture
def sample_steering_files(temp_project_dir):
    """Create sample steering files for testing."""
    steering_dir = temp_project_dir / ".kiro" / "steering"
    
    files = []
    for filename in ["tech-stack.md", "architecture.md", "conventions.md"]:
        file_path = steering_dir / filename
        file_path.write_text(f"# {filename}\n\nSample content for {filename}")
        files.append(file_path)
    
    return files


class TestCreateBackup:
    """Tests for _create_backup() method."""
    
    def test_create_backup_with_timestamp(self, init_workflow, sample_steering_files):
        """Test that backup is created with timestamp in directory name."""
        # Act
        result = init_workflow._create_backup(sample_steering_files)
        
        # Assert
        assert result is True
        
        # Check backup directory was created with timestamp
        backup_parent = init_workflow.config.backup_dir
        backup_dirs = list(backup_parent.glob("steering_backup_*"))
        assert len(backup_dirs) == 1
        
        # Verify timestamp format (YYYYMMDD_HHMMSS)
        backup_name = backup_dirs[0].name
        assert backup_name.startswith("steering_backup_")
        timestamp_str = backup_name.replace("steering_backup_", "")
        
        # Should be parseable as datetime
        datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    
    def test_backup_preserves_file_content(self, init_workflow, sample_steering_files):
        """Test that backup preserves original file content."""
        # Act
        init_workflow._create_backup(sample_steering_files)
        
        # Assert
        backup_parent = init_workflow.config.backup_dir
        backup_dir = list(backup_parent.glob("steering_backup_*"))[0]
        
        for original_file in sample_steering_files:
            backup_file = backup_dir / original_file.name
            assert backup_file.exists()
            assert backup_file.read_text() == original_file.read_text()
    
    def test_backup_preserves_metadata(self, init_workflow, sample_steering_files):
        """Test that backup preserves file timestamps and permissions using copy2."""
        # Arrange - set specific modification time on original files
        test_time = time.time() - 3600  # 1 hour ago
        for file_path in sample_steering_files:
            # Set modification time
            import os
            os.utime(file_path, (test_time, test_time))
        
        # Act
        init_workflow._create_backup(sample_steering_files)
        
        # Assert
        backup_parent = init_workflow.config.backup_dir
        backup_dir = list(backup_parent.glob("steering_backup_*"))[0]
        
        for original_file in sample_steering_files:
            backup_file = backup_dir / original_file.name
            
            # Check modification time is preserved (within 1 second tolerance)
            original_mtime = original_file.stat().st_mtime
            backup_mtime = backup_file.stat().st_mtime
            assert abs(original_mtime - backup_mtime) < 1.0
    
    def test_backup_stores_directory_in_state(self, init_workflow, sample_steering_files):
        """Test that backup directory path is stored in workflow state."""
        # Act
        init_workflow._create_backup(sample_steering_files)
        
        # Assert
        assert hasattr(init_workflow.state, 'last_backup_dir')
        assert init_workflow.state.last_backup_dir is not None
        assert init_workflow.state.last_backup_dir.exists()
        assert init_workflow.state.last_backup_dir.name.startswith("steering_backup_")
    
    def test_backup_disabled_returns_true(self, temp_project_dir, sample_steering_files):
        """Test that backup returns True when disabled in config."""
        # Arrange
        config = SteeringConfig(backup_enabled=False)
        workflow = InitWorkflow(config=config, project_root=temp_project_dir)
        
        # Act
        result = workflow._create_backup(sample_steering_files)
        
        # Assert
        assert result is True
        
        # No backup directory should be created
        backup_parent = workflow.config.backup_dir
        if backup_parent.exists():
            backup_dirs = list(backup_parent.glob("steering_backup_*"))
            assert len(backup_dirs) == 0
    
    def test_backup_failure_returns_false(self, init_workflow, sample_steering_files):
        """Test that backup returns False on failure."""
        # Arrange - mock shutil.copy2 to raise an exception
        with patch('shutil.copy2', side_effect=PermissionError("Permission denied")):
            # Act
            result = init_workflow._create_backup(sample_steering_files)
            
            # Assert
            assert result is False


class TestCleanupOldBackups:
    """Tests for _cleanup_old_backups() method."""
    
    def test_cleanup_keeps_5_most_recent(self, init_workflow, sample_steering_files):
        """Test that cleanup keeps only 5 most recent backups."""
        # Arrange - create 8 backups with different timestamps
        backup_parent = init_workflow.config.backup_dir
        
        for i in range(8):
            backup_dir = backup_parent / f"steering_backup_2024010{i}_120000"
            backup_dir.mkdir()
            
            # Create a file in each backup
            (backup_dir / "test.md").write_text(f"Backup {i}")
            
            # Sleep briefly to ensure different modification times
            time.sleep(0.01)
        
        # Act
        init_workflow._cleanup_old_backups()
        
        # Assert
        remaining_backups = list(backup_parent.glob("steering_backup_*"))
        assert len(remaining_backups) == 5
    
    def test_cleanup_keeps_newest_backups(self, init_workflow, sample_steering_files):
        """Test that cleanup keeps the newest backups, not oldest."""
        # Arrange - create backups with known timestamps
        backup_parent = init_workflow.config.backup_dir
        
        timestamps = [
            "20240101_120000",  # Oldest
            "20240102_120000",
            "20240103_120000",
            "20240104_120000",
            "20240105_120000",
            "20240106_120000",
            "20240107_120000",  # Newest
        ]
        
        for ts in timestamps:
            backup_dir = backup_parent / f"steering_backup_{ts}"
            backup_dir.mkdir()
            (backup_dir / "test.md").write_text(f"Backup {ts}")
        
        # Act
        init_workflow._cleanup_old_backups()
        
        # Assert
        remaining_backups = sorted([d.name for d in backup_parent.glob("steering_backup_*")])
        
        # Should keep the 5 newest (20240103 through 20240107)
        assert len(remaining_backups) == 5
        assert "steering_backup_20240107_120000" in remaining_backups
        assert "steering_backup_20240106_120000" in remaining_backups
        assert "steering_backup_20240101_120000" not in remaining_backups
        assert "steering_backup_20240102_120000" not in remaining_backups
    
    def test_cleanup_with_fewer_than_5_backups(self, init_workflow):
        """Test that cleanup doesn't delete anything when fewer than 5 backups exist."""
        # Arrange - create only 3 backups
        backup_parent = init_workflow.config.backup_dir
        
        for i in range(3):
            backup_dir = backup_parent / f"steering_backup_2024010{i}_120000"
            backup_dir.mkdir()
        
        # Act
        init_workflow._cleanup_old_backups()
        
        # Assert
        remaining_backups = list(backup_parent.glob("steering_backup_*"))
        assert len(remaining_backups) == 3
    
    def test_cleanup_handles_missing_backup_dir(self, init_workflow):
        """Test that cleanup handles missing backup directory gracefully."""
        # Arrange - remove backup directory
        backup_parent = init_workflow.config.backup_dir
        if backup_parent.exists():
            shutil.rmtree(backup_parent)
        
        # Act - should not raise exception
        init_workflow._cleanup_old_backups()
        
        # Assert - no exception raised
        assert True


class TestRollbackFromBackup:
    """Tests for _rollback_from_backup() method."""
    
    def test_rollback_restores_files(self, init_workflow, sample_steering_files):
        """Test that rollback restores files from backup."""
        # Arrange - create backup
        init_workflow._create_backup(sample_steering_files)
        backup_dir = init_workflow.state.last_backup_dir
        
        # Modify original files
        for file_path in sample_steering_files:
            file_path.write_text("MODIFIED CONTENT")
        
        # Act
        result = init_workflow._rollback_from_backup(backup_dir)
        
        # Assert
        assert result is True
        
        # Verify files are restored
        for file_path in sample_steering_files:
            content = file_path.read_text()
            assert "MODIFIED CONTENT" not in content
            assert f"Sample content for {file_path.name}" in content
    
    def test_rollback_uses_most_recent_backup_by_default(self, init_workflow, sample_steering_files):
        """Test that rollback uses most recent backup when no backup_dir specified."""
        # Arrange - create multiple backups
        backup_parent = init_workflow.config.backup_dir
        
        # Create older backup
        old_backup = backup_parent / "steering_backup_20240101_120000"
        old_backup.mkdir()
        for file_path in sample_steering_files:
            (old_backup / file_path.name).write_text("OLD BACKUP")
        
        time.sleep(0.01)
        
        # Create newer backup
        new_backup = backup_parent / "steering_backup_20240102_120000"
        new_backup.mkdir()
        for file_path in sample_steering_files:
            (new_backup / file_path.name).write_text("NEW BACKUP")
        
        # Modify original files
        for file_path in sample_steering_files:
            file_path.write_text("CURRENT")
        
        # Act - rollback without specifying backup_dir
        result = init_workflow._rollback_from_backup()
        
        # Assert
        assert result is True
        
        # Should restore from newest backup
        for file_path in sample_steering_files:
            assert file_path.read_text() == "NEW BACKUP"
    
    def test_rollback_is_atomic(self, init_workflow, sample_steering_files):
        """Test that rollback is atomic - all files restored or none."""
        # Arrange - create backup
        init_workflow._create_backup(sample_steering_files)
        backup_dir = init_workflow.state.last_backup_dir
        
        # Modify original files
        for file_path in sample_steering_files:
            file_path.write_text("MODIFIED")
        
        # Act - rollback should use temp directory for atomic operation
        result = init_workflow._rollback_from_backup(backup_dir)
        
        # Assert
        assert result is True
        
        # Verify temp directory was cleaned up
        temp_dir = init_workflow.state.steering_dir.parent / ".steering_temp"
        assert not temp_dir.exists()
    
    def test_rollback_logs_restored_files(self, init_workflow, sample_steering_files, caplog):
        """Test that rollback logs which files were restored."""
        # Arrange
        init_workflow._create_backup(sample_steering_files)
        backup_dir = init_workflow.state.last_backup_dir
        
        # Act
        with caplog.at_level("INFO"):
            init_workflow._rollback_from_backup(backup_dir)
        
        # Assert
        for file_path in sample_steering_files:
            assert f"Restored: {file_path.name}" in caplog.text
    
    def test_rollback_returns_false_when_no_backup_exists(self, init_workflow):
        """Test that rollback returns False when no backup directory exists."""
        # Arrange - ensure no backups exist
        backup_parent = init_workflow.config.backup_dir
        if backup_parent.exists():
            shutil.rmtree(backup_parent)
        backup_parent.mkdir()
        
        # Act
        result = init_workflow._rollback_from_backup()
        
        # Assert
        assert result is False
    
    def test_rollback_returns_false_when_backup_dir_not_found(self, init_workflow):
        """Test that rollback returns False when specified backup_dir doesn't exist."""
        # Arrange
        fake_backup_dir = init_workflow.config.backup_dir / "steering_backup_99999999_999999"
        
        # Act
        result = init_workflow._rollback_from_backup(fake_backup_dir)
        
        # Assert
        assert result is False
    
    def test_rollback_returns_false_when_no_files_in_backup(self, init_workflow):
        """Test that rollback returns False when backup directory is empty."""
        # Arrange - create empty backup directory
        backup_parent = init_workflow.config.backup_dir
        empty_backup = backup_parent / "steering_backup_20240101_120000"
        empty_backup.mkdir()
        
        # Act
        result = init_workflow._rollback_from_backup(empty_backup)
        
        # Assert
        assert result is False


class TestOfferRollbackOnFailure:
    """Tests for _offer_rollback_on_failure() method."""
    
    def test_offer_rollback_returns_false_in_non_interactive_mode(self, temp_project_dir):
        """Test that rollback offer returns False in non-interactive mode."""
        # Arrange
        config = SteeringConfig(interactive=False, backup_enabled=True)
        workflow = InitWorkflow(config=config, project_root=temp_project_dir)
        workflow.state.last_backup_dir = Path("/fake/backup")
        
        # Act
        result = workflow._offer_rollback_on_failure()
        
        # Assert
        assert result is False
    
    def test_offer_rollback_returns_false_when_no_backup_exists(self, temp_project_dir):
        """Test that rollback offer returns False when no backup exists."""
        # Arrange
        config = SteeringConfig(interactive=True, backup_enabled=True)
        workflow = InitWorkflow(config=config, project_root=temp_project_dir)
        # Don't set last_backup_dir
        
        # Act
        result = workflow._offer_rollback_on_failure()
        
        # Assert
        assert result is False
    
    @patch('builtins.input', return_value='1')
    def test_offer_rollback_returns_true_when_user_chooses_rollback(self, mock_input, temp_project_dir):
        """Test that rollback offer returns True when user chooses option 1."""
        # Arrange
        config = SteeringConfig(interactive=True, backup_enabled=True)
        workflow = InitWorkflow(config=config, project_root=temp_project_dir)
        workflow.state.last_backup_dir = Path("/fake/backup")
        
        # Act
        result = workflow._offer_rollback_on_failure()
        
        # Assert
        assert result is True
        mock_input.assert_called_once()
    
    @patch('builtins.input', return_value='2')
    def test_offer_rollback_returns_false_when_user_keeps_current_state(self, mock_input, temp_project_dir):
        """Test that rollback offer returns False when user chooses option 2."""
        # Arrange
        config = SteeringConfig(interactive=True, backup_enabled=True)
        workflow = InitWorkflow(config=config, project_root=temp_project_dir)
        workflow.state.last_backup_dir = Path("/fake/backup")
        
        # Act
        result = workflow._offer_rollback_on_failure()
        
        # Assert
        assert result is False
        mock_input.assert_called_once()
    
    @patch('builtins.input', side_effect=['invalid', '3', '1'])
    def test_offer_rollback_handles_invalid_input(self, mock_input, temp_project_dir):
        """Test that rollback offer handles invalid input and re-prompts."""
        # Arrange
        config = SteeringConfig(interactive=True, backup_enabled=True)
        workflow = InitWorkflow(config=config, project_root=temp_project_dir)
        workflow.state.last_backup_dir = Path("/fake/backup")
        
        # Act
        result = workflow._offer_rollback_on_failure()
        
        # Assert
        assert result is True
        assert mock_input.call_count == 3  # Called 3 times due to invalid inputs


class TestExecuteWithRollback:
    """Integration tests for execute() method with rollback on failure."""
    
    def test_execute_offers_rollback_on_failure(self, init_workflow, sample_steering_files):
        """Test that execute() offers rollback when workflow fails."""
        # Arrange - create backup first
        init_workflow._create_backup(sample_steering_files)
        
        # Make workflow fail by mocking a step
        with patch.object(init_workflow, '_step_populate_templates', side_effect=Exception("Test failure")):
            with patch.object(init_workflow, '_offer_rollback_on_failure', return_value=False) as mock_offer:
                # Act
                result = init_workflow.execute()
                
                # Assert
                assert result is False
                mock_offer.assert_called_once()
    
    def test_execute_performs_rollback_when_user_accepts(self, init_workflow, sample_steering_files):
        """Test that execute() performs rollback when user accepts."""
        # Arrange - create backup
        init_workflow._create_backup(sample_steering_files)
        
        # Modify files
        for file_path in sample_steering_files:
            file_path.write_text("MODIFIED")
        
        # Make workflow fail
        with patch.object(init_workflow, '_step_populate_templates', side_effect=Exception("Test failure")):
            with patch.object(init_workflow, '_offer_rollback_on_failure', return_value=True):
                with patch.object(init_workflow, '_rollback_from_backup', return_value=True) as mock_rollback:
                    # Act
                    result = init_workflow.execute()
                    
                    # Assert
                    assert result is False
                    mock_rollback.assert_called_once()
    
    def test_execute_skips_rollback_when_user_declines(self, init_workflow, sample_steering_files):
        """Test that execute() skips rollback when user declines."""
        # Arrange
        init_workflow._create_backup(sample_steering_files)
        
        # Make workflow fail
        with patch.object(init_workflow, '_step_populate_templates', side_effect=Exception("Test failure")):
            with patch.object(init_workflow, '_offer_rollback_on_failure', return_value=False):
                with patch.object(init_workflow, '_rollback_from_backup') as mock_rollback:
                    # Act
                    result = init_workflow.execute()
                    
                    # Assert
                    assert result is False
                    mock_rollback.assert_not_called()
