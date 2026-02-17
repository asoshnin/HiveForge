"""
Backup management for the Steering Assistant v02.

This module provides the BackupManager class for creating, restoring, and managing
backups of steering files.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class BackupManager:
    """Manages backups of steering files for rollback capability."""
    
    def __init__(
        self,
        backup_dir: Path = Path(".kiro/backups/steering"),
        max_backups: int = 5,
    ):
        """
        Initialize the BackupManager.
        
        Args:
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to keep
        """
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(
        self,
        files: List[Path],
        backup_name: Optional[str] = None,
    ) -> Path:
        """
        Create a backup of the current state.
        
        Args:
            files: List of file paths to backup
            backup_name: Optional backup name (defaults to timestamp)
            
        Returns:
            Path to the backup directory
        """
        # Generate backup name
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # Include microseconds
            backup_name = f"backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Copy each file
        for file_path in files:
            dest_path = backup_path / file_path.name
            shutil.copy2(file_path, dest_path)
        
        return backup_path
    
    def restore_backup(
        self,
        backup_path: Path,
        target_dir: Path,
    ) -> List[Path]:
        """
        Restore files from a backup.
        
        Args:
            backup_path: Path to the backup directory
            target_dir: Target directory to restore files to
            
        Returns:
            List of restored file paths
        """
        restored_files = []
        
        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy each file from backup
        for file_path in backup_path.glob("*.md"):
            dest_path = target_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            restored_files.append(dest_path)
        
        return restored_files
    
    def cleanup_old_backups(
        self,
        max_backups: Optional[int] = None,
    ) -> int:
        """
        Delete backups exceeding the limit.
        
        Args:
            max_backups: Maximum number of backups to keep (defaults to instance value)
            
        Returns:
            Number of backups deleted
        """
        if max_backups is None:
            max_backups = self.max_backups
        
        # Get all backups sorted by timestamp
        backups = sorted(
            self.backup_dir.glob("backup_*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        # Delete old backups
        deleted = 0
        for backup in backups[max_backups:]:
            shutil.rmtree(backup)
            deleted += 1
        
        return deleted
    
    def list_backups(self) -> List[dict]:
        """
        List available backups with timestamps.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        for backup_path in sorted(
            self.backup_dir.glob("backup_*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        ):
            # Get file count
            file_count = len(list(backup_path.glob("*.md")))
            
            # Get timestamp
            timestamp = datetime.fromtimestamp(backup_path.stat().st_mtime)
            
            backups.append({
                "path": backup_path,
                "name": backup_path.name,
                "timestamp": timestamp,
                "file_count": file_count,
            })
        
        return backups
    
    def get_latest_backup(self) -> Optional[Path]:
        """
        Get the most recent backup.
        
        Returns:
            Path to the latest backup or None if no backups exist
        """
        backups = list(self.backup_dir.glob("backup_*"))
        
        if not backups:
            return None
        
        return max(backups, key=lambda x: x.stat().st_mtime)
    
    def get_backup_count(self) -> int:
        """
        Get the number of available backups.
        
        Returns:
            Number of backups
        """
        return len(list(self.backup_dir.glob("backup_*")))
