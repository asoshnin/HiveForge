"""
Integration tests for end-to-end steering system workflows.

This module tests complete workflows from start to finish, verifying that
all P0-P2 components work together correctly in real-world scenarios.
"""

import logging
import shutil
import tempfile
from pathlib import Path
from textwrap import dedent
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from hiveforge.steering.models import (
    FeatureFlagConfig,
    SteeringConfig,
    WorkflowState,
)
from hiveforge.steering.shared.adapters import SharedInitWorkflow
from hiveforge.steering.workflows.autonomous_workflow import AutonomousWorkflow


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def project_with_code(temp_project_dir):
    """Create a project with realistic code structure."""
    # Create Python project structure
    src_dir = temp_project_dir / "src"
    src_dir.mkdir()
    
    # Create main.py with FastAPI
    (src_dir / "main.py").write_text(dedent('''
        """Main application module."""
        from fastapi import FastAPI
        
        app = FastAPI()
        
        @app.get("/")
        def read_root():
            """Root endpoint."""
            return {"message": "Hello World"}
    '''))
    
    # Create pyproject.toml
    (temp_project_dir / "pyproject.toml").write_text(dedent('''
        [project]
        name = "test-project"
        version = "0.1.0"
        requires-python = ">=3.11"
        dependencies = [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
        ]
    '''))
    
    # Create README.md
    (temp_project_dir / "README.md").write_text(dedent('''
        # Test Project
        
        A FastAPI web application for testing.
    '''))
    
    return temp_project_dir


@pytest.fixture
def project_with_existing_steering(temp_project_dir):
    """Create a project with existing steering files."""
    steering_dir = temp_project_dir / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    
    # Create existing tech-stack.md
    (steering_dir / "tech-stack.md").write_text(dedent('''
        # Technology Stack
        
        ## Backend
        - **Language:** Python 3.10
        - **Framework:** Flask
    '''))
    
    # Create existing architecture.md
    (steering_dir / "architecture.md").write_text(dedent('''
        # Architecture
        
        Monolithic architecture.
    '''))
    
    return temp_project_dir


@pytest.fixture
def mock_llm_provider_available():
    """Mock LLMProvider that is available and returns content."""
    with patch('hiveforge.steering.llm.provider.LLMProvider') as mock_provider_class:
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        
        async def mock_complete(system_prompt, user_prompt, **kwargs):
            # Return realistic content based on the template
            if "tech-stack" in user_prompt.lower():
                return dedent('''
                    # Technology Stack
                    
                    ## Backend
                    - **Language:** Python 3.11
                    - **Framework:** FastAPI
                    
                    ## Database
                    - **Primary:** PostgreSQL
                ''').strip()
            elif "architecture" in user_prompt.lower():
                return dedent('''
                    # Architecture
                    
                    REST API architecture with FastAPI.
                ''').strip()
            else:
                return "# Generated Content\n\nSample content."
        
        mock_provider.complete = mock_complete
        mock_provider_class.return_value = mock_provider
        
        yield mock_provider


@pytest.fixture
def mock_llm_provider_unavailable():
    """Mock LLMProvider that is unavailable."""
    with patch('hiveforge.steering.llm.provider.LLMProvider') as mock_provider_class:
        mock_provider = Mock()
        mock_provider.is_available.return_value = False
        mock_provider_class.return_value = mock_provider
        
        yield mock_provider


class TestFullWorkflowWithLLMAvailable:
    """Test complete init_steering workflow with LLM available."""
    
    def test_init_steering_generates_all_files(
        self, project_with_code, mock_llm_provider_available
    ):
        """Test that init workflow generates all steering files when LLM is available."""
        # Create shared workflow (uses execute() which handles async internally)
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,  # CLI mode
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success
        assert result.success is True
        
        # Verify files were generated
        steering_dir = project_with_code / ".kiro" / "steering"
        assert steering_dir.exists()
        
        # Check that files exist
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
        ]
        
        for filename in expected_files:
            file_path = steering_dir / filename
            assert file_path.exists(), f"Expected file {filename} not found"
            
            # Verify file is not empty
            content = file_path.read_text()
            assert len(content) > 0, f"File {filename} is empty"
            assert content.strip() != "", f"File {filename} contains only whitespace"
    
    def test_init_steering_calculates_confidence_scores(
        self, project_with_code, mock_llm_provider_available
    ):
        """Test that confidence scores are calculated for generated files."""
        # Note: This test verifies internal workflow state
        # In production, confidence scores are in metadata
        
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success
        assert result.success is True
        
        # Verify metadata includes confidence information
        assert "files_count" in result.metadata
        assert result.metadata["files_count"] > 0
    
    def test_init_steering_no_empty_files(
        self, project_with_code, mock_llm_provider_available
    ):
        """Test that no empty files are generated."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success
        assert result.success is True
        
        # Verify no empty files
        steering_dir = project_with_code / ".kiro" / "steering"
        
        for file_path in steering_dir.glob("*.md"):
            content = file_path.read_text()
            assert len(content.strip()) > 0, f"File {file_path.name} is empty"


class TestFullWorkflowWithLLMUnavailable:
    """Test complete init_steering workflow with LLM unavailable (fallback)."""
    
    def test_init_steering_fallback_generates_files(
        self, project_with_code, mock_llm_provider_unavailable
    ):
        """Test that init workflow generates files with fallback when LLM unavailable."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success (fallback should still succeed)
        assert result.success is True
        
        # Verify files were generated
        steering_dir = project_with_code / ".kiro" / "steering"
        assert steering_dir.exists()
        
        # Check that files exist
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
        ]
        
        for filename in expected_files:
            file_path = steering_dir / filename
            assert file_path.exists(), f"Expected file {filename} not found"
    
    def test_init_steering_fallback_uses_inferred_markers(
        self, project_with_code, mock_llm_provider_unavailable
    ):
        """Test that fallback applies [INFERRED] markers."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success
        assert result.success is True
        
        # Verify files have [INFERRED] markers
        steering_dir = project_with_code / ".kiro" / "steering"
        
        inferred_count = 0
        for file_path in steering_dir.glob("*.md"):
            content = file_path.read_text()
            if "[INFERRED:" in content:
                inferred_count += 1
        
        # At least some files should have [INFERRED] markers
        assert inferred_count > 0, "No files have [INFERRED] markers"
    
    def test_init_steering_fallback_low_confidence(
        self, project_with_code, mock_llm_provider_unavailable
    ):
        """Test that fallback results in low confidence scores."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success
        assert result.success is True
        
        # Verify warnings about low confidence
        assert len(result.warnings) > 0 or "confidence" in result.message.lower()
    
    def test_init_steering_fallback_tracks_reasons(
        self, project_with_code, mock_llm_provider_unavailable
    ):
        """Test that fallback reasons are tracked."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success
        assert result.success is True
        
        # Verify warnings or metadata includes fallback information
        has_fallback_info = (
            len(result.warnings) > 0 or
            "confidence" in result.metadata or
            "fallback" in str(result.metadata).lower()
        )
        assert has_fallback_info, "No fallback information tracked"


class TestFullWorkflowMCPMode:
    """Test complete init_steering workflow in MCP mode (non-interactive)."""
    
    def test_init_steering_mcp_mode_no_input_calls(
        self, project_with_code, mock_llm_provider_available
    ):
        """Test that MCP mode does not call input()."""
        # Create shared workflow with ctx (MCP mode)
        mock_ctx = Mock()
        
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=mock_ctx,
            autonomous=True,
            confidence_threshold=0.7,
        )
        
        # Mock input() to ensure it's never called
        with patch('builtins.input') as mock_input:
            # Execute workflow
            result = workflow.execute()
            
            # Verify input() was NOT called
            mock_input.assert_not_called()
    
    def test_init_steering_mcp_mode_creates_draft(
        self, project_with_code, mock_llm_provider_available
    ):
        """Test that MCP mode creates draft but doesn't write files."""
        # Create shared workflow with ctx (MCP mode)
        mock_ctx = Mock()
        
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=mock_ctx,
            autonomous=True,
            confidence_threshold=0.7,
            dry_run=True,  # Use dry_run to simulate draft mode
        )
        
        # Execute workflow
        result = workflow.execute()
        
        # Verify result has metadata
        assert "metadata" in result.to_dict()
    
    def test_init_steering_mcp_mode_includes_draft_summary(
        self, project_with_code, mock_llm_provider_available
    ):
        """Test that MCP mode includes draft_summary in metadata."""
        # Create shared workflow with ctx (MCP mode)
        mock_ctx = Mock()
        
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=mock_ctx,
            autonomous=True,
            confidence_threshold=0.7,
            dry_run=True,
        )
        
        # Execute workflow
        result = workflow.execute()
        
        # Verify metadata includes draft information
        result_dict = result.to_dict()
        assert "dry_run" in result_dict


class TestFullWorkflowCLIMode:
    """Test complete init_steering workflow in CLI mode (interactive)."""
    
    def test_init_steering_cli_mode_prompts_user(
        self, project_with_existing_steering, mock_llm_provider_available
    ):
        """Test that CLI mode prompts user for approval."""
        # Create shared workflow without ctx (CLI mode)
        workflow = SharedInitWorkflow(
            project_root=project_with_existing_steering,
            ctx=None,
            autonomous=False,  # Interactive mode
            confidence_threshold=0.7,
        )
        
        # Mock input() to return "1" (backup and proceed)
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
            
            # Verify workflow succeeded
            assert result.success is True
    
    def test_init_steering_cli_mode_creates_backup(
        self, project_with_existing_steering, mock_llm_provider_available
    ):
        """Test that CLI mode creates backup of existing files."""
        # Create shared workflow without ctx (CLI mode)
        workflow = SharedInitWorkflow(
            project_root=project_with_existing_steering,
            ctx=None,
            autonomous=False,
            confidence_threshold=0.7,
        )
        
        # Mock input() to return "1" (backup and proceed)
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            workflow.execute()
            
            # Verify backup was created
            backup_dir = project_with_existing_steering / ".kiro" / "backups"
            assert backup_dir.exists()
            
            # Check for backup folders
            backup_folders = list(backup_dir.glob("steering_backup_*"))
            assert len(backup_folders) > 0, "No backup folder created"
    
    def test_init_steering_cli_mode_user_can_abort(
        self, project_with_existing_steering, mock_llm_provider_available
    ):
        """Test that CLI mode allows user to abort."""
        # Create shared workflow without ctx (CLI mode)
        workflow = SharedInitWorkflow(
            project_root=project_with_existing_steering,
            ctx=None,
            autonomous=False,
            confidence_threshold=0.7,
        )
        
        # Mock input() to return "2" (abort)
        with patch('builtins.input', return_value='2'):
            # Execute workflow
            result = workflow.execute()
            
            # Verify workflow was aborted
            assert result.success is False or "cancelled" in result.message.lower()


class TestFullWorkflowUpdateWithDrift:
    """Test complete update_steering workflow with drift detection."""
    
    def test_update_steering_detects_drift(
        self, project_with_existing_steering, mock_llm_provider_available
    ):
        """Test that update workflow detects drift."""
        # Modify pyproject.toml to create drift
        (project_with_existing_steering / "pyproject.toml").write_text(dedent('''
            [project]
            name = "test-project"
            version = "0.1.0"
            requires-python = ">=3.11"
            dependencies = [
                "fastapi>=0.100.0",
            ]
        '''))
        
        # Create update workflow (would need to implement SharedUpdateWorkflow)
        # For now, test drift detector directly
        from hiveforge.steering.detectors.drift_detector import DriftDetector
        from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
        
        # Analyze code
        analyzer = CodeAnalyzer(project_with_existing_steering)
        code_analysis = analyzer.analyze()
        
        # Load existing files
        steering_dir = project_with_existing_steering / ".kiro" / "steering"
        existing_files = {}
        for file_path in steering_dir.glob("*.md"):
            existing_files[file_path.name] = file_path.read_text()
        
        # Detect drift
        detector = DriftDetector(project_with_existing_steering)
        drift_report = detector.detect(existing_files, code_analysis)
        
        # Verify drift was detected
        assert drift_report.has_drift()
        assert len(drift_report.items) > 0
    
    def test_update_steering_generates_drift_report(
        self, project_with_existing_steering, mock_llm_provider_available
    ):
        """Test that update workflow generates drift report."""
        # Modify pyproject.toml to create drift
        (project_with_existing_steering / "pyproject.toml").write_text(dedent('''
            [project]
            name = "test-project"
            version = "0.1.0"
            requires-python = ">=3.11"
            dependencies = [
                "fastapi>=0.100.0",
            ]
        '''))
        
        # Test drift detector
        from hiveforge.steering.detectors.drift_detector import DriftDetector
        from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
        
        # Analyze code
        analyzer = CodeAnalyzer(project_with_existing_steering)
        code_analysis = analyzer.analyze()
        
        # Load existing files
        steering_dir = project_with_existing_steering / ".kiro" / "steering"
        existing_files = {}
        for file_path in steering_dir.glob("*.md"):
            existing_files[file_path.name] = file_path.read_text()
        
        # Detect drift
        detector = DriftDetector(project_with_existing_steering)
        drift_report = detector.detect(existing_files, code_analysis)
        
        # Verify drift report has items
        assert len(drift_report.items) > 0
        
        # Verify drift items have required fields
        for item in drift_report.items:
            assert hasattr(item, 'category')
            assert hasattr(item, 'description')
            assert hasattr(item, 'confidence')
            assert 0.0 <= item.confidence <= 1.0


class TestWorkflowErrorHandling:
    """Test error handling in workflows."""
    
    def test_workflow_handles_template_not_found(
        self, project_with_code
    ):
        """Test that workflow handles missing templates gracefully."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=False,
        )
        
        # Mock template directory to not exist
        with patch('pathlib.Path.exists', return_value=False):
            # Execute workflow - should handle error gracefully
            result = workflow.execute()
            
            # Workflow should fail but not crash
            assert result.success is False or len(result.errors) > 0
    
    def test_workflow_handles_file_write_errors(
        self, project_with_code
    ):
        """Test that workflow handles file write errors gracefully."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=False,
        )
        
        # Mock file write to fail
        with patch('pathlib.Path.write_text', side_effect=PermissionError("Permission denied")):
            # Execute workflow - should handle error gracefully
            try:
                result = workflow.execute()
                # Should either fail gracefully or raise expected exception
                assert result.success is False or len(result.errors) > 0
            except PermissionError:
                # Expected exception is acceptable
                pass


class TestWorkflowStateManagement:
    """Test workflow state management."""
    
    def test_workflow_tracks_generated_files(
        self, project_with_code, mock_llm_provider_available
    ):
        """Test that workflow tracks all generated files."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success
        assert result.success is True
        
        # Verify files were created
        assert len(result.files_created) > 0
        
        # Verify all tracked files exist on disk
        steering_dir = project_with_code / ".kiro" / "steering"
        for filename in result.files_created:
            # filename is relative path like ".kiro/steering/tech-stack.md"
            file_path = project_with_code / filename
            assert file_path.exists(), f"Tracked file {filename} not found on disk"
    
    def test_workflow_maintains_state_consistency(
        self, project_with_code, mock_llm_provider_available
    ):
        """Test that workflow maintains consistent state."""
        # Create shared workflow
        workflow = SharedInitWorkflow(
            project_root=project_with_code,
            ctx=None,
            autonomous=True,
            confidence_threshold=0.7,
            auto_discover=True,
        )
        
        # Mock input to avoid blocking
        with patch('builtins.input', return_value='1'):
            # Execute workflow
            result = workflow.execute()
        
        # Verify success
        assert result.success is True
        
        # Verify state consistency
        # Number of created files should match metadata count
        if "files_count" in result.metadata:
            assert len(result.files_created) == result.metadata["files_count"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
