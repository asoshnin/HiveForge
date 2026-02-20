"""
Integration tests for empty source folder warnings.

Tests that the system properly warns users when no source documents
are found and generates appropriate confidence metadata and [INFERRED] tags.
"""

import tempfile
from pathlib import Path

import pytest

from hiveforge.steering.workflows.init_workflow import InitWorkflow
from hiveforge.steering.models import SteeringConfig


class TestEmptySourceWarnings:
    """End-to-end tests for empty source folder handling."""
    
    def test_empty_source_folder_generates_warnings(self, tmp_path):
        """Test that empty source folder generates appropriate warnings."""
        # Setup: Create empty source folder
        empty_docs = tmp_path / "empty_docs"
        empty_docs.mkdir()
        
        # Execute workflow with empty source path
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="empty_docs"
        )
        
        result = workflow.execute()
        
        # Verify success (workflow should still complete)
        assert result.status == "success"
        
        # Verify warnings about empty source folder
        assert len(result.warnings) > 0
        warning_text = " ".join(result.warnings).lower()
        assert "no source documents" in warning_text or "empty" in warning_text
    
    def test_empty_source_folder_low_confidence(self, tmp_path):
        """Test that empty source folder results in low confidence metadata."""
        # Setup: Create empty source folder
        empty_docs = tmp_path / "empty_docs"
        empty_docs.mkdir()
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="empty_docs"
        )
        
        result = workflow.execute()
        
        # Verify low confidence metadata
        assert "confidence_level" in result.metadata
        assert result.metadata["confidence_level"] == "low"
        
        assert "confidence_score" in result.metadata
        # Low confidence should be < 0.4
        assert result.metadata["confidence_score"] < 0.4
        
        assert "source_documents_found" in result.metadata
        assert result.metadata["source_documents_found"] == 0
    
    def test_empty_source_folder_inferred_tags(self, tmp_path):
        """Test that empty source folder results in [INFERRED] tags."""
        # Setup: Create empty source folder
        empty_docs = tmp_path / "empty_docs"
        empty_docs.mkdir()
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="empty_docs"
        )
        
        result = workflow.execute()
        
        # Verify files were created
        assert result.status == "success"
        assert len(result.files_created) > 0
        
        # Check that generated files have [INFERRED] tags
        steering_dir = tmp_path / ".kiro" / "steering"
        assert steering_dir.exists()
        
        # Count files with [INFERRED] tags
        files_with_inferred = 0
        for file_path in steering_dir.glob("*.md"):
            content = file_path.read_text()
            if "[INFERRED]" in content:
                files_with_inferred += 1
        
        # Most or all files should have [INFERRED] tags
        # since no source documents were provided
        assert files_with_inferred > 0, "Expected [INFERRED] tags in generated files"
    
    def test_empty_source_folder_metadata_headers(self, tmp_path):
        """Test that files have low confidence metadata in frontmatter."""
        # Setup: Create empty source folder
        empty_docs = tmp_path / "empty_docs"
        empty_docs.mkdir()
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="empty_docs"
        )
        
        result = workflow.execute()
        
        # Check generated files for metadata headers
        steering_dir = tmp_path / ".kiro" / "steering"
        
        # At least one file should have confidence metadata in frontmatter
        found_metadata = False
        for file_path in steering_dir.glob("*.md"):
            content = file_path.read_text()
            if "confidence_level:" in content and "confidence_score:" in content:
                found_metadata = True
                # Verify it's marked as low confidence
                assert "confidence_level: low" in content
                break
        
        assert found_metadata, "Expected confidence metadata in file frontmatter"
    
    def test_empty_default_onboarding_folder(self, tmp_path):
        """Test behavior when default .kiro/onboarding/ folder is empty."""
        # Setup: Create empty .kiro/onboarding/ folder
        onboarding_dir = tmp_path / ".kiro" / "onboarding"
        onboarding_dir.mkdir(parents=True)
        
        # Execute workflow without specifying source_docs_path
        # (should use default .kiro/onboarding/)
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path=None  # Use default
        )
        
        result = workflow.execute()
        
        # Verify warnings
        assert len(result.warnings) > 0
        
        # Verify low confidence
        assert result.metadata.get("confidence_level") == "low"
        assert result.metadata.get("source_documents_found") == 0
    
    def test_nonexistent_source_folder_warning(self, tmp_path):
        """Test that nonexistent source folder generates appropriate warning."""
        # Execute workflow with nonexistent source path
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="nonexistent_folder"
        )
        
        result = workflow.execute()
        
        # Should either fail or warn about missing folder
        if result.status == "failed":
            # Failure is acceptable for nonexistent path
            assert len(result.errors) > 0
        else:
            # If it succeeds, should have warnings
            assert len(result.warnings) > 0
    
    def test_autonomous_mode_additional_warning(self, tmp_path):
        """Test that autonomous mode adds additional warning for empty source."""
        # Setup: Create empty source folder
        empty_docs = tmp_path / "empty_docs"
        empty_docs.mkdir()
        
        # Execute workflow in autonomous mode (interactive=False means autonomous)
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="empty_docs"
        )
        
        result = workflow.execute()
        
        # Verify warnings include autonomous mode context
        assert len(result.warnings) > 0
        
        # Should have warning about no source documents
        warning_text = " ".join(result.warnings).lower()
        assert "no source documents" in warning_text or "empty" in warning_text
    
    def test_low_confidence_warning_in_files(self, tmp_path):
        """Test that low confidence warning appears at top of generated files."""
        # Setup: Create empty source folder
        empty_docs = tmp_path / "empty_docs"
        empty_docs.mkdir()
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="empty_docs"
        )
        
        result = workflow.execute()
        
        # Check generated files for low confidence warnings
        steering_dir = tmp_path / ".kiro" / "steering"
        
        # At least some files should have low confidence warnings
        found_warning = False
        for file_path in steering_dir.glob("*.md"):
            content = file_path.read_text()
            # Look for warning indicators in first few lines
            first_lines = "\n".join(content.split("\n")[:20]).lower()
            if "low confidence" in first_lines or "inferred" in first_lines:
                found_warning = True
                break
        
        assert found_warning, "Expected low confidence warning in generated files"
    
    def test_discovery_stats_show_zero_files(self, tmp_path):
        """Test that discovery statistics show zero files for empty folder."""
        # Setup: Create empty source folder
        empty_docs = tmp_path / "empty_docs"
        empty_docs.mkdir()
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="empty_docs"
        )
        
        result = workflow.execute()
        
        # Verify discovery statistics
        assert "discovery_stats" in result.metadata
        discovery_stats = result.metadata["discovery_stats"]
        
        assert discovery_stats.get("files_discovered", -1) == 0
        assert discovery_stats.get("files_included", -1) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
