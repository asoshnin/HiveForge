"""
Unit tests for P2-1: Template Variants by Project Type

Tests the _filter_files_for_project_type() method in AutonomousWorkflow
that filters templates based on detected project type.

Requirements: P2-1
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from hiveforge.steering.workflows.autonomous_workflow import AutonomousWorkflow
from hiveforge.steering.models import (
    SteeringConfig,
    FeatureFlagConfig,
    CodeAnalysisResult,
    WorkflowState,
)


class TestFilterFilesForProjectType:
    """Test _filter_files_for_project_type() method (P2-1)."""
    
    @pytest.fixture
    def mock_workflow(self, tmp_path):
        """Create a mock AutonomousWorkflow for testing."""
        config = SteeringConfig(
            analyze_code=False,
            skip_validation=True,
            interactive=False,
        )
        
        feature_flag_config = FeatureFlagConfig(
            use_autonomous_generation=True,
            confidence_threshold=0.7,
        )
        
        workflow = AutonomousWorkflow(
            config=config,
            feature_flag_config=feature_flag_config,
            project_root=tmp_path,
        )
        
        # Mock state with just what we need
        workflow.state = Mock()
        workflow.state.code_analysis = None
        
        return workflow
    
    def test_filter_cli_tool_skips_ui_and_db(self, mock_workflow):
        """Test that CLI tool project skips ui-standards.md and db-standards.md."""
        # Setup: CLI tool without database
        mock_workflow.state.code_analysis = CodeAnalysisResult(
            classification={
                'project_type': 'cli_tool',
                'has_frontend': False,
                'has_database': False,
            }
        )
        
        template_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "api-standards.md",
            "db-standards.md",
            "qa-standards.md",
            "ui-standards.md",
        ]
        
        # Execute
        filtered = mock_workflow._filter_files_for_project_type(template_files)
        
        # Verify
        assert "ui-standards.md" not in filtered
        assert "db-standards.md" not in filtered
        assert "tech-stack.md" in filtered
        assert "architecture.md" in filtered
        assert len(filtered) == 6  # All except ui-standards and db-standards
    
    def test_filter_mcp_server_skips_ui(self, mock_workflow):
        """Test that MCP server project skips ui-standards.md."""
        # Setup: MCP server without frontend
        mock_workflow.state.code_analysis = CodeAnalysisResult(
            classification={
                'project_type': 'mcp_server',
                'has_frontend': False,
                'has_database': True,
            }
        )
        
        template_files = [
            "project-vision.md",
            "tech-stack.md",
            "ui-standards.md",
            "db-standards.md",
        ]
        
        # Execute
        filtered = mock_workflow._filter_files_for_project_type(template_files)
        
        # Verify
        assert "ui-standards.md" not in filtered
        assert "db-standards.md" in filtered  # Has database
        assert len(filtered) == 3
    
    def test_filter_web_app_includes_all(self, mock_workflow):
        """Test that web app project includes all templates."""
        # Setup: Web app with frontend and database
        mock_workflow.state.code_analysis = CodeAnalysisResult(
            classification={
                'project_type': 'web_app',
                'has_frontend': True,
                'has_database': True,
            }
        )
        
        template_files = [
            "project-vision.md",
            "tech-stack.md",
            "ui-standards.md",
            "db-standards.md",
        ]
        
        # Execute
        filtered = mock_workflow._filter_files_for_project_type(template_files)
        
        # Verify
        assert "ui-standards.md" in filtered
        assert "db-standards.md" in filtered
        assert len(filtered) == 4  # All templates included
    
    def test_filter_no_code_analysis_returns_all(self, mock_workflow):
        """Test that missing code analysis returns all templates."""
        # Setup: No code analysis
        mock_workflow.state.code_analysis = None
        
        template_files = [
            "project-vision.md",
            "tech-stack.md",
            "ui-standards.md",
            "db-standards.md",
        ]
        
        # Execute
        filtered = mock_workflow._filter_files_for_project_type(template_files)
        
        # Verify: All templates returned when no analysis available
        assert len(filtered) == 4
        assert filtered == template_files
    
    def test_filter_no_classification_returns_all(self, mock_workflow):
        """Test that missing classification returns all templates."""
        # Setup: Code analysis without classification
        mock_workflow.state.code_analysis = CodeAnalysisResult(
            classification=None
        )
        
        template_files = [
            "project-vision.md",
            "tech-stack.md",
            "ui-standards.md",
        ]
        
        # Execute
        filtered = mock_workflow._filter_files_for_project_type(template_files)
        
        # Verify: All templates returned when no classification
        assert len(filtered) == 3
        assert filtered == template_files
    
    def test_filter_cli_and_mcp_skips_ui(self, mock_workflow):
        """Test that CLI+MCP project skips ui-standards.md."""
        # Setup: CLI and MCP combined
        mock_workflow.state.code_analysis = CodeAnalysisResult(
            classification={
                'project_type': 'cli_and_mcp',
                'has_frontend': False,
                'has_database': False,
            }
        )
        
        template_files = [
            "tech-stack.md",
            "ui-standards.md",
            "api-standards.md",
        ]
        
        # Execute
        filtered = mock_workflow._filter_files_for_project_type(template_files)
        
        # Verify
        assert "ui-standards.md" not in filtered
        assert "api-standards.md" in filtered
        assert len(filtered) == 2
    
    def test_filter_library_with_database(self, mock_workflow):
        """Test that library with database includes db-standards.md."""
        # Setup: Library with database
        mock_workflow.state.code_analysis = CodeAnalysisResult(
            classification={
                'project_type': 'library',
                'has_frontend': False,
                'has_database': True,
            }
        )
        
        template_files = [
            "tech-stack.md",
            "db-standards.md",
            "ui-standards.md",
        ]
        
        # Execute
        filtered = mock_workflow._filter_files_for_project_type(template_files)
        
        # Verify
        assert "db-standards.md" in filtered
        assert "ui-standards.md" not in filtered
        assert len(filtered) == 2
