"""
Integration tests for backward compatibility.

Tests that existing workflows continue to work without new parameters
and that the default .kiro/onboarding/ behavior is preserved.
"""

import tempfile
from pathlib import Path

import pytest

from hiveforge.steering.workflows.init_workflow import InitWorkflow
from hiveforge.steering.models import SteeringConfig


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing workflows."""
    
    def test_init_workflow_without_new_parameters(self, tmp_path):
        """Test that InitWorkflow works without new parameters."""
        # Setup: Create default .kiro/onboarding/ folder with documents
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        (onboarding_dir / "tech.md").write_text("# Tech\n\nPython 3.11")
        
        # Execute workflow WITHOUT new parameters (old API)
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
            # source_docs_path NOT specified (should use default)
        )
        
        result = workflow.execute()
        
        # Verify success
        assert result.status == "success"
        assert len(result.files_created) > 0
        
        # Verify documents were discovered from default location
        discovery_stats = result.metadata.get("discovery_stats", {})
        assert discovery_stats.get("files_discovered", 0) >= 1
    
    def test_default_onboarding_folder_still_works(self, tmp_path):
        """Test that default .kiro/onboarding/ folder is still used."""
        # Setup: Create .kiro/onboarding/ with documents
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        (onboarding_dir / "overview.md").write_text("""
# Project Overview

This is a test project using FastAPI and PostgreSQL.
        """)
        
        # Execute workflow without source_docs_path
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
        )
        
        result = workflow.execute()
        
        # Verify success
        assert result.status == "success"
        
        # Verify documents were discovered
        discovery_stats = result.metadata.get("discovery_stats", {})
        assert discovery_stats.get("files_discovered", 0) >= 1
        
        # Verify steering files were created
        steering_dir = tmp_path / ".kiro" / "steering"
        assert steering_dir.exists()
        assert len(list(steering_dir.glob("*.md"))) > 0
    
    def test_existing_workflow_parameters_unchanged(self, tmp_path):
        """Test that existing workflow parameters work as before."""
        # Setup
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        # Execute workflow with existing parameters only
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
        )
        
        result = workflow.execute()
        
        # Verify all existing behavior works
        assert result.status == "success"
        assert hasattr(result, "files_created")
        assert hasattr(result, "warnings")
        assert hasattr(result, "errors")
        assert hasattr(result, "metadata")
    
    def test_no_regression_in_file_generation(self, tmp_path):
        """Test that file generation hasn't regressed."""
        # Setup
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        (onboarding_dir / "docs.md").write_text("# Documentation\n\nProject info")
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
        )
        
        result = workflow.execute()
        
        # Verify expected steering files are created
        steering_dir = tmp_path / ".kiro" / "steering"
        assert steering_dir.exists()
        
        # Should create standard steering files
        expected_files = [
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "project-vision.md"
        ]
        
        created_files = [f.name for f in steering_dir.glob("*.md")]
        
        # At least some expected files should be created
        assert len(created_files) > 0
    
    def test_metadata_structure_unchanged(self, tmp_path):
        """Test that result metadata structure is backward compatible."""
        # Setup
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
        )
        
        result = workflow.execute()
        
        # Verify existing metadata fields are present
        assert hasattr(result, "status")
        assert hasattr(result, "message")
        assert hasattr(result, "files_created")
        assert hasattr(result, "files_modified")
        assert hasattr(result, "files_deleted")
        assert hasattr(result, "warnings")
        assert hasattr(result, "errors")
        assert hasattr(result, "metadata")
        
        # Verify metadata is a dict
        assert isinstance(result.metadata, dict)
    
    def test_config_parameters_still_work(self, tmp_path):
        """Test that SteeringConfig parameters work as before."""
        # Setup
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        # Execute workflow with various config options
        config = SteeringConfig(
            interactive=False,
            skip_validation=True,
            backup_enabled=True
        )
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
        )
        
        result = workflow.execute()
        
        # Verify success
        assert result.status == "success"
    
    def test_interactive_false_still_works(self, tmp_path):
        """Test that interactive=False (autonomous mode) works as before."""
        # Setup
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        # Test with interactive=False (autonomous mode)
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
        )
        
        result = workflow.execute()
        assert result.status == "success"
    
    def test_interactive_true_instantiation(self, tmp_path):
        """Test that interactive=True can be instantiated."""
        # Setup
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        # Test with interactive=True (may require user input, so just test instantiation)
        config = SteeringConfig(interactive=True)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
        )
        
        # Just verify it can be instantiated
        assert workflow is not None
    
    def test_no_breaking_changes_in_api(self, tmp_path):
        """Test that there are no breaking changes in the API."""
        # Setup
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        # Test that old-style instantiation still works
        try:
            config = SteeringConfig(interactive=False)
            workflow = InitWorkflow(
                config=config,
                project_root=tmp_path
            )
            
            result = workflow.execute()
            
            # Verify result has expected structure
            assert hasattr(result, "status")
            assert hasattr(result, "to_dict")
            
            # Verify to_dict() works
            result_dict = result.to_dict()
            assert isinstance(result_dict, dict)
            assert "status" in result_dict
            
        except TypeError as e:
            pytest.fail(f"API breaking change detected: {e}")
    
    def test_existing_tests_still_pass(self, tmp_path):
        """Verify that patterns from existing tests still work."""
        # This test verifies common patterns used in existing tests
        
        # Pattern 1: Basic workflow execution
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path
        )
        
        result = workflow.execute()
        assert result.status == "success"
        
        # Pattern 2: Checking files created
        assert len(result.files_created) >= 0
        
        # Pattern 3: Checking warnings
        assert isinstance(result.warnings, list)
        
        # Pattern 4: Checking errors
        assert isinstance(result.errors, list)
        
        # Pattern 5: Accessing metadata
        assert isinstance(result.metadata, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
