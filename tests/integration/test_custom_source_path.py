"""
Integration tests for custom source_docs_path parameter.

Tests the full workflow with custom source document paths to ensure:
- Documents are discovered correctly from custom paths
- Steering files are generated with proper content
- Confidence metadata reflects source document usage
"""

import tempfile
from pathlib import Path

import pytest

from hiveforge.steering.workflows.init_workflow import InitWorkflow
from hiveforge.steering.models import SteeringConfig


class TestCustomSourcePath:
    """End-to-end tests for custom source_docs_path functionality."""
    
    def test_custom_source_path_full_workflow(self, tmp_path):
        """Test full workflow with custom source path."""
        # Setup: Create custom source folder with documents
        custom_docs = tmp_path / "my_custom_docs"
        custom_docs.mkdir()
        
        # Create sample documentation
        (custom_docs / "tech-overview.md").write_text("""
# Technology Overview

We use Python 3.11 with FastAPI for our backend.
PostgreSQL 15 is our primary database.
Redis 7 for caching.
        """)
        
        (custom_docs / "architecture.md").write_text("""
# Architecture

Our system follows a microservices architecture.
We have an API Gateway that routes to backend services.
        """)
        
        # Execute workflow with custom source path
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="my_custom_docs"
        )
        
        result = workflow.execute()
        
        # Verify success
        assert result.status == "success"
        assert len(result.files_created) > 0
        
        # Verify documents were discovered from custom path
        assert result.metadata.get("source_docs_path") == "my_custom_docs"
        discovery_stats = result.metadata.get("discovery_stats", {})
        assert discovery_stats.get("files_discovered", 0) >= 2
        
        # Verify steering files were created
        steering_dir = tmp_path / ".kiro" / "steering"
        assert steering_dir.exists()
        assert (steering_dir / "tech-stack.md").exists()
        assert (steering_dir / "architecture.md").exists()
        
        # Verify confidence metadata is present and reasonable
        assert "confidence_level" in result.metadata
        assert "confidence_score" in result.metadata
        assert "source_documents_found" in result.metadata
        
        # With source documents, confidence should be medium or high
        confidence_level = result.metadata["confidence_level"]
        assert confidence_level in ["medium", "high"]
        
        # Verify content from source documents was used
        tech_stack_content = (steering_dir / "tech-stack.md").read_text()
        assert "Python 3.11" in tech_stack_content or "FastAPI" in tech_stack_content
    
    def test_custom_source_path_with_nested_folder(self, tmp_path):
        """Test custom source path with nested folder structure."""
        # Setup: Create nested folder structure
        nested_docs = tmp_path / "docs" / "project-info"
        nested_docs.mkdir(parents=True)
        
        (nested_docs / "requirements.md").write_text("""
# Requirements

Our project needs to handle 1000 requests per second.
We need 99.9% uptime.
        """)
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="docs/project-info"
        )
        
        result = workflow.execute()
        
        # Verify success
        assert result.status == "success"
        assert result.metadata.get("source_docs_path") == "docs/project-info"
        
        # Verify documents were discovered
        discovery_stats = result.metadata.get("discovery_stats", {})
        assert discovery_stats.get("files_discovered", 0) >= 1
    
    def test_custom_source_path_relative_to_project_root(self, tmp_path):
        """Test that source_docs_path is resolved relative to project_root."""
        # Setup: Create source folder
        source_folder = tmp_path / "project_docs"
        source_folder.mkdir()
        
        (source_folder / "overview.md").write_text("# Project Overview\n\nThis is our project.")
        
        # Execute workflow with relative path
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="project_docs"  # Relative to project_root
        )
        
        result = workflow.execute()
        
        # Verify success
        assert result.status == "success"
        
        # Verify path was resolved correctly
        assert result.metadata.get("source_docs_path") == "project_docs"
        discovery_stats = result.metadata.get("discovery_stats", {})
        assert discovery_stats.get("files_discovered", 0) >= 1
    
    def test_confidence_metadata_with_source_documents(self, tmp_path):
        """Test that confidence metadata reflects source document usage."""
        # Setup: Create source documents
        source_docs = tmp_path / "source_docs"
        source_docs.mkdir()
        
        # Create comprehensive documentation
        (source_docs / "tech.md").write_text("# Tech\n\nPython 3.11, FastAPI, PostgreSQL 15")
        (source_docs / "arch.md").write_text("# Architecture\n\nMicroservices with API Gateway")
        (source_docs / "vision.md").write_text("# Vision\n\nBuild the best product")
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="source_docs"
        )
        
        result = workflow.execute()
        
        # Verify confidence metadata
        assert "confidence_level" in result.metadata
        assert "confidence_score" in result.metadata
        assert "source_documents_found" in result.metadata
        
        # With multiple source documents, confidence should be medium or high
        confidence_level = result.metadata["confidence_level"]
        assert confidence_level in ["medium", "high"]
        
        # Confidence score should be reasonable (> 0.4 for medium)
        confidence_score = result.metadata["confidence_score"]
        assert confidence_score >= 0.4
        
        # Source documents should be counted
        source_docs_found = result.metadata["source_documents_found"]
        assert source_docs_found >= 3
    
    def test_inferred_tags_with_partial_documentation(self, tmp_path):
        """Test that [INFERRED] tags appear when documentation is incomplete."""
        # Setup: Create minimal documentation (only tech stack)
        source_docs = tmp_path / "minimal_docs"
        source_docs.mkdir()
        
        (source_docs / "tech.md").write_text("# Tech\n\nPython 3.11")
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="minimal_docs"
        )
        
        result = workflow.execute()
        
        # Verify success
        assert result.status == "success"
        
        # Check generated files for [INFERRED] tags
        steering_dir = tmp_path / ".kiro" / "steering"
        
        # At least some files should have [INFERRED] tags
        # since we only provided minimal documentation
        has_inferred_tags = False
        for file_path in steering_dir.glob("*.md"):
            content = file_path.read_text()
            if "[INFERRED]" in content:
                has_inferred_tags = True
                break
        
        assert has_inferred_tags, "Expected [INFERRED] tags in generated files"
    
    def test_discovery_statistics_in_metadata(self, tmp_path):
        """Test that discovery statistics are included in result metadata."""
        # Setup: Create source documents
        source_docs = tmp_path / "docs"
        source_docs.mkdir()
        
        (source_docs / "file1.md").write_text("# File 1")
        (source_docs / "file2.md").write_text("# File 2")
        (source_docs / "file3.pdf").write_text("PDF content")  # Will be discovered
        
        # Execute workflow
        config = SteeringConfig(interactive=False)
        workflow = InitWorkflow(
            config=config,
            project_root=tmp_path,
            source_docs_path="docs"
        )
        
        result = workflow.execute()
        
        # Verify discovery statistics
        assert "discovery_stats" in result.metadata
        discovery_stats = result.metadata["discovery_stats"]
        
        assert "files_discovered" in discovery_stats
        assert "files_included" in discovery_stats
        assert discovery_stats["files_discovered"] >= 2  # At least the .md files


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
