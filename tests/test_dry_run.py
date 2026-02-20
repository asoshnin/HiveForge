"""
Tests for dry-run mode functionality.

This module tests the dry-run mode that allows users to preview
what would be created without actually writing files.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from hiveforge.steering.models import SteeringConfig
from hiveforge.steering.workflows.init_workflow import InitWorkflow


class TestDryRunMode:
    """Tests for dry-run mode in InitWorkflow."""
    
    @pytest.fixture
    def basic_config(self):
        """Create a basic steering config."""
        return SteeringConfig(
            analyze_code=False,
            skip_validation=True,
            interactive=False
        )
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    def test_dry_run_no_files_written(self, mock_populator_class, mock_is_empty, basic_config, tmp_path):
        """Test that dry-run mode does not write any files."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()
        steering_dir = project_root / ".kiro" / "steering"
        
        # Mock empty staging folder
        mock_is_empty.return_value = True
        
        # Mock template populator
        mock_populator = Mock()
        mock_populator.populate_all.return_value = {
            "tech-stack.md": "# Tech Stack\n\nContent here"
        }
        mock_populator_class.return_value = mock_populator
        
        # Create workflow with dry_run=True
        workflow = InitWorkflow(
            config=basic_config,
            project_root=project_root,
            dry_run=True
        )
        
        # Execute workflow
        success = workflow.execute()
        
        # Verify success
        assert success
        
        # Verify no files were written
        assert not steering_dir.exists() or len(list(steering_dir.glob("*.md"))) == 0
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    def test_dry_run_preview_in_metadata(self, mock_populator_class, mock_is_empty, basic_config, tmp_path):
        """Test that dry-run mode stores preview in metadata."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Mock empty staging folder
        mock_is_empty.return_value = True
        
        # Mock template populator
        mock_populator = Mock()
        mock_populator.populate_all.return_value = {
            "tech-stack.md": "# Tech Stack\n\nContent here",
            "conventions.md": "# Conventions\n\nMore content"
        }
        mock_populator_class.return_value = mock_populator
        
        # Create workflow with dry_run=True
        workflow = InitWorkflow(
            config=basic_config,
            project_root=project_root,
            dry_run=True
        )
        
        # Execute workflow
        success = workflow.execute()
        
        # Verify success
        assert success
        
        # Verify preview is in metadata
        assert "dry_run_preview" in workflow.state.metadata
        assert "dry_run" in workflow.state.metadata
        assert workflow.state.metadata["dry_run"] is True
        
        # Verify preview content
        preview = workflow.state.metadata["dry_run_preview"]
        assert "tech-stack.md" in preview
        assert "conventions.md" in preview
        assert "# Tech Stack" in preview["tech-stack.md"]
        assert "# Conventions" in preview["conventions.md"]
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    def test_dry_run_includes_all_metadata(self, mock_populator_class, mock_is_empty, basic_config, tmp_path):
        """Test that dry-run mode includes all metadata (warnings, confidence, etc.)."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Mock empty staging folder (will trigger warnings)
        mock_is_empty.return_value = True
        
        # Mock template populator
        mock_populator = Mock()
        mock_populator.populate_all.return_value = {
            "tech-stack.md": "# Tech Stack\n\nContent here"
        }
        mock_populator_class.return_value = mock_populator
        
        # Create workflow with dry_run=True
        workflow = InitWorkflow(
            config=basic_config,
            project_root=project_root,
            dry_run=True
        )
        
        # Execute workflow
        success = workflow.execute()
        
        # Verify success
        assert success
        
        # Verify warnings are present (from empty source folder)
        assert len(workflow.state.warnings) > 0
        
        # Verify confidence metadata is present
        assert "source_documents_found" in workflow.state.metadata
        assert "confidence_level" in workflow.state.metadata
        assert workflow.state.metadata["confidence_level"] == "low"
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    def test_normal_mode_writes_files(self, mock_populator_class, mock_is_empty, basic_config, tmp_path):
        """Test that normal mode (dry_run=False) writes files as expected."""
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()
        steering_dir = project_root / ".kiro" / "steering"
        
        # Mock empty staging folder
        mock_is_empty.return_value = True
        
        # Mock template populator
        mock_populator = Mock()
        mock_populator.populate_all.return_value = {
            "tech-stack.md": "# Tech Stack\n\nContent here"
        }
        mock_populator_class.return_value = mock_populator
        
        # Create workflow with dry_run=False (default)
        workflow = InitWorkflow(
            config=basic_config,
            project_root=project_root,
            dry_run=False
        )
        
        # Execute workflow
        success = workflow.execute()
        
        # Verify success
        assert success
        
        # Verify files were written
        assert steering_dir.exists()
        assert (steering_dir / "tech-stack.md").exists()
        assert "# Tech Stack" in (steering_dir / "tech-stack.md").read_text()
        
        # Verify no dry_run_preview in metadata
        assert "dry_run_preview" not in workflow.state.metadata


class TestDryRunIntegration:
    """Integration tests for dry-run mode with SharedInitWorkflow."""
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    def test_shared_workflow_dry_run(self, mock_populator_class, mock_is_empty, tmp_path):
        """Test dry-run mode through SharedInitWorkflow."""
        from hiveforge.steering.shared.adapters import SharedInitWorkflow
        
        # Setup
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Mock empty staging folder
        mock_is_empty.return_value = True
        
        # Mock template populator
        mock_populator = Mock()
        mock_populator.populate_all.return_value = {
            "tech-stack.md": "# Tech Stack\n\nContent here"
        }
        mock_populator_class.return_value = mock_populator
        
        # Create shared workflow with dry_run=True
        workflow = SharedInitWorkflow(
            project_root=project_root,
            dry_run=True,
            autonomous=True
        )
        
        # Execute workflow
        result = workflow.execute()
        
        # Verify success
        assert result.success
        
        # Verify message indicates dry-run
        assert "Dry-run preview" in result.message or "would be created" in result.message
        
        # Verify files_created list is populated (even though not written)
        assert len(result.files_created) > 0
        
        # Verify metadata includes dry_run flag
        assert result.metadata["dry_run"] is True
        
        # Verify no actual files were written
        steering_dir = project_root / ".kiro" / "steering"
        assert not steering_dir.exists() or len(list(steering_dir.glob("*.md"))) == 0
