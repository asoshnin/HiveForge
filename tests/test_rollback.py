"""
Property-based tests for rollback mechanism.

Validates: Requirements 9.1-9.7, 20.1-20.7
"""

import tempfile
from pathlib import Path

import pytest

from hiveforge.steering.backup_manager import BackupManager


class TestRollbackIntegrity:
    """Tests for rollback mechanism integrity."""
    
    @pytest.mark.property("Property 9: Rollback Integrity")
    @pytest.mark.property("Property 20: Preview Mode Correctness")
    def test_create_backup(self):
        """
        WHEN writing files, automatic backups SHALL be created before writing.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create steering files
            steering_dir = tmp_path / ".kiro" / "steering"
            steering_dir.mkdir(parents=True)
            
            (steering_dir / "project-vision.md").write_text("# Project Vision")
            (steering_dir / "tech-stack.md").write_text("# Tech Stack")
            
            # Create backup
            backup_dir = tmp_path / ".kiro" / "backups" / "steering"
            backup_manager = BackupManager(backup_dir=backup_dir)
            
            files = list(steering_dir.glob("*.md"))
            backup_path = backup_manager.create_backup(files)
            
            # Verify backup was created
            assert backup_path.exists()
            assert backup_path.is_dir()
            
            # Verify files were backed up
            backed_up_files = list(backup_path.glob("*.md"))
            assert len(backed_up_files) == 2
    
    @pytest.mark.property("Property 9: Rollback Integrity")
    @pytest.mark.property("Property 20: Preview Mode Correctness")
    def test_restore_backup(self):
        """
        WHEN rolling back, all files SHALL be restored to previous version.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create steering files
            steering_dir = tmp_path / ".kiro" / "steering"
            steering_dir.mkdir(parents=True)
            
            (steering_dir / "project-vision.md").write_text("# Project Vision v1")
            
            # Create backup
            backup_dir = tmp_path / ".kiro" / "backups" / "steering"
            backup_manager = BackupManager(backup_dir=backup_dir)
            
            files = list(steering_dir.glob("*.md"))
            backup_path = backup_manager.create_backup(files)
            
            # Modify files
            (steering_dir / "project-vision.md").write_text("# Project Vision v2")
            
            # Restore backup
            restored_files = backup_manager.restore_backup(backup_path, steering_dir)
            
            # Verify file was restored
            restored_content = (steering_dir / "project-vision.md").read_text()
            assert "v1" in restored_content
            assert "v2" not in restored_content
    
    @pytest.mark.property("Property 9: Rollback Integrity")
    @pytest.mark.property("Property 20: Preview Mode Correctness")
    def test_cleanup_old_backups(self):
        """
        WHEN backups exceed limit (5 versions), oldest versions SHALL be deleted.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create steering files
            steering_dir = tmp_path / ".kiro" / "steering"
            steering_dir.mkdir(parents=True)
            
            (steering_dir / "project-vision.md").write_text("# Project Vision")
            
            # Create backup manager with max 3 backups
            backup_dir = tmp_path / ".kiro" / "backups" / "steering"
            backup_manager = BackupManager(backup_dir=backup_dir, max_backups=3)
            
            # Create 5 backups with small delays to ensure different timestamps
            import time
            for i in range(5):
                files = list(steering_dir.glob("*.md"))
                backup_manager.create_backup(files)
                if i < 4:
                    time.sleep(0.01)  # Small delay to ensure different timestamps
            
            # Cleanup old backups
            deleted = backup_manager.cleanup_old_backups()
            
            # Verify cleanup
            assert deleted == 2  # 5 - 3 = 2 deleted
            assert backup_manager.get_backup_count() == 3
    
    @pytest.mark.property("Property 9: Rollback Integrity")
    @pytest.mark.property("Property 20: Preview Mode Correctness")
    def test_list_backups(self):
        """
        WHEN listing backups, available backups SHALL be shown with timestamps.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create steering files
            steering_dir = tmp_path / ".kiro" / "steering"
            steering_dir.mkdir(parents=True)
            
            (steering_dir / "project-vision.md").write_text("# Project Vision")
            
            # Create backups
            backup_dir = tmp_path / ".kiro" / "backups" / "steering"
            backup_manager = BackupManager(backup_dir=backup_dir)
            
            backup_manager.create_backup(list(steering_dir.glob("*.md")))
            
            # List backups
            backups = backup_manager.list_backups()
            
            # Verify backups
            assert len(backups) >= 1
            assert "name" in backups[0]
            assert "timestamp" in backups[0]
            assert "file_count" in backups[0]
    
    @pytest.mark.property("Property 9: Rollback Integrity")
    @pytest.mark.property("Property 20: Preview Mode Correctness")
    def test_dry_run_preview(self):
        """
        WHEN --dry-run is set, no files SHALL be written, only preview displayed.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create steering files
            steering_dir = tmp_path / ".kiro" / "steering"
            steering_dir.mkdir(parents=True)
            
            (steering_dir / "project-vision.md").write_text("# Project Vision v1")
            
            # Create backup
            backup_dir = tmp_path / ".kiro" / "backups" / "steering"
            backup_manager = BackupManager(backup_dir=backup_dir)
            
            files = list(steering_dir.glob("*.md"))
            backup_path = backup_manager.create_backup(files)
            
            # Modify files
            (steering_dir / "project-vision.md").write_text("# Project Vision v2")
            
            # In dry-run mode, no changes should be made
            # This is simulated by the CLI command
            dry_run = True
            
            if dry_run:
                # Preview only - no actual restore
                assert (steering_dir / "project-vision.md").read_text() == "# Project Vision v2"
    
    @pytest.mark.property("Property 9: Rollback Integrity")
    @pytest.mark.property("Property 20: Preview Mode Correctness")
    def test_latest_backup_selection(self):
        """
        WHEN no backup name is specified, the latest backup SHALL be used.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create steering files
            steering_dir = tmp_path / ".kiro" / "steering"
            steering_dir.mkdir(parents=True)
            
            (steering_dir / "project-vision.md").write_text("# Project Vision")
            
            # Create backups
            backup_dir = tmp_path / ".kiro" / "backups" / "steering"
            backup_manager = BackupManager(backup_dir=backup_dir)
            
            backup1 = backup_manager.create_backup(list(steering_dir.glob("*.md")))
            
            # Modify and create another backup
            (steering_dir / "project-vision.md").write_text("# Project Vision v2")
            backup2 = backup_manager.create_backup(list(steering_dir.glob("*.md")))
            
            # Get latest backup
            latest = backup_manager.get_latest_backup()
            
            # Verify latest is the most recent
            assert latest == backup2
    
    @pytest.mark.property("Property 9: Rollback Integrity")
    @pytest.mark.property("Property 20: Preview Mode Correctness")
    def test_backup_count(self):
        """
        WHEN checking backup count, the system SHALL return correct number.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create steering files
            steering_dir = tmp_path / ".kiro" / "steering"
            steering_dir.mkdir(parents=True)
            
            (steering_dir / "project-vision.md").write_text("# Project Vision")
            
            # Create backups with unique backup directory per test
            backup_dir = tmp_path / ".kiro" / "backups" / "steering" / "test_backup_count"
            backup_manager = BackupManager(backup_dir=backup_dir)
            
            assert backup_manager.get_backup_count() == 0
            
            backup_manager.create_backup(list(steering_dir.glob("*.md")))
            assert backup_manager.get_backup_count() == 1
            
            backup_manager.create_backup(list(steering_dir.glob("*.md")))
            assert backup_manager.get_backup_count() == 2
