"""
Unit tests for draft review functionality (P1-3).

Tests cover:
- DraftState and DraftFile dataclass creation
- Draft summary formatting
- CLI mode user prompt logic
- MCP mode draft storage logic
- Placeholder counting and confidence calculation
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import re

from hiveforge.steering.models import (
    DraftState,
    DraftFile,
    SteeringConfig,
    WorkflowState,
    FeatureFlagConfig,
)
from hiveforge.steering.workflows.autonomous_workflow import AutonomousWorkflow


class TestDraftFileDataclass:
    """Test DraftFile dataclass functionality."""
    
    def test_draft_file_creation(self):
        """Test creating a DraftFile with all fields."""
        draft_file = DraftFile(
            filename="tech-stack.md",
            content="# Tech Stack\n\nPython 3.11",
            confidence=0.85,
            placeholder_count=2,
            preview="# Tech Stack Python 3.11"
        )
        
        assert draft_file.filename == "tech-stack.md"
        assert draft_file.confidence == 0.85
        assert draft_file.placeholder_count == 2
        assert "Tech Stack" in draft_file.preview
    
    def test_draft_file_to_dict(self):
        """Test converting DraftFile to dictionary."""
        draft_file = DraftFile(
            filename="conventions.md",
            content="# Conventions\n\nUse snake_case",
            confidence=0.90,
            placeholder_count=1,
            preview="# Conventions Use snake_case"
        )
        
        result = draft_file.to_dict()
        
        assert result['filename'] == "conventions.md"
        assert result['confidence'] == 0.90
        assert result['placeholder_count'] == 1
        assert result['preview'] == "# Conventions Use snake_case"
        assert 'content' not in result  # Content not included in dict


class TestDraftStateDataclass:
    """Test DraftState dataclass functionality."""
    
    def test_draft_state_creation(self):
        """Test creating a DraftState with files."""
        files = [
            DraftFile("file1.md", "content1", 0.9, 1, "preview1"),
            DraftFile("file2.md", "content2", 0.8, 2, "preview2"),
        ]
        
        draft = DraftState(
            files=files,
            created_at=datetime.now(),
            is_approved=False
        )
        
        assert len(draft.files) == 2
        assert draft.is_approved is False
        assert draft.created_at is not None
    
    def test_draft_summary_formatting(self):
        """Test draft summary generation."""
        files = [
            DraftFile("tech-stack.md", "content", 0.85, 3, "Tech stack preview"),
            DraftFile("conventions.md", "content", 0.92, 1, "Conventions preview"),
        ]
        
        draft = DraftState(files=files, created_at=datetime.now())
        summary = draft.summary()
        
        # Check summary contains expected elements
        assert "# Draft Summary" in summary
        assert "## tech-stack.md" in summary
        assert "## conventions.md" in summary
        assert "Confidence: 85.0%" in summary
        assert "Confidence: 92.0%" in summary
        assert "Placeholders: 3" in summary
        assert "Placeholders: 1" in summary
        assert "Tech stack preview" in summary
        assert "Conventions preview" in summary


class TestPlaceholderCounting:
    """Test placeholder counting and confidence calculation."""
    
    def test_placeholder_regex_pattern(self):
        """Test regex pattern for counting placeholders."""
        content = """
        # Tech Stack
        
        Language: {Python version}
        Framework: {Backend framework}
        Database: {Database name}
        """
        
        # Pattern from implementation: {[^}]+}
        placeholder_count = len(re.findall(r'\{[^}]+\}', content))
        
        assert placeholder_count == 3
    
    def test_confidence_calculation(self):
        """Test confidence calculation: 1.0 - (placeholder_count * 0.1)."""
        # 0 placeholders -> 1.0 confidence
        assert max(0.0, 1.0 - (0 * 0.1)) == 1.0
        
        # 3 placeholders -> 0.7 confidence
        assert max(0.0, 1.0 - (3 * 0.1)) == 0.7
        
        # 10 placeholders -> 0.0 confidence (capped at 0)
        assert max(0.0, 1.0 - (10 * 0.1)) == 0.0
        
        # 15 placeholders -> 0.0 confidence (capped at 0)
        assert max(0.0, 1.0 - (15 * 0.1)) == 0.0
    
    def test_preview_generation(self):
        """Test preview generation (first 300 chars, newlines replaced)."""
        content = "Line 1\nLine 2\nLine 3\n" * 50  # Long content
        
        preview = content[:300].replace('\n', ' ')
        
        assert len(preview) <= 300
        assert '\n' not in preview
        assert ' ' in preview


class TestCLIModeReview:
    """Test CLI mode draft review functionality."""
    
    @pytest.fixture
    def workflow(self, tmp_path):
        """Create workflow instance for testing."""
        config = SteeringConfig(interactive=True)
        feature_flags = FeatureFlagConfig()
        
        workflow = AutonomousWorkflow(
            config=config,
            feature_flag_config=feature_flags,
            project_root=tmp_path
        )
        
        # Set up generated files
        workflow.generated_files = {
            "tech-stack.md": "# Tech Stack\n\n{Python version}",
            "conventions.md": "# Conventions\n\nUse snake_case",
        }
        
        return workflow
    
    @patch('builtins.input', return_value='y')
    @patch('builtins.print')
    def test_cli_mode_user_approves(self, mock_print, mock_input, workflow):
        """Test CLI mode when user approves draft."""
        result = workflow._step_review_draft()
        
        # Should return True (approved)
        assert result is True
        
        # Should have called input() for approval
        mock_input.assert_called_once()
        
        # Should have printed draft summary
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("DRAFT REVIEW" in str(call) for call in print_calls)
    
    @patch('builtins.input', return_value='n')
    @patch('builtins.print')
    def test_cli_mode_user_rejects(self, mock_print, mock_input, workflow):
        """Test CLI mode when user rejects draft."""
        result = workflow._step_review_draft()
        
        # Should return False (rejected)
        assert result is False
        
        # Should have called input() for approval
        mock_input.assert_called_once()
        
        # Should have printed rejection message
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("rejected" in str(call).lower() for call in print_calls)
    
    @patch('builtins.print')
    def test_cli_mode_draft_summary_display(self, mock_print, workflow):
        """Test that draft summary is displayed in CLI mode."""
        with patch('builtins.input', return_value='y'):
            workflow._step_review_draft()
        
        # Check that summary was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        summary_text = '\n'.join(print_calls)
        
        assert "tech-stack.md" in summary_text
        assert "conventions.md" in summary_text
        assert "Confidence" in summary_text
        assert "Placeholders" in summary_text


class TestMCPModeReview:
    """Test MCP mode draft review functionality."""
    
    @pytest.fixture
    def workflow(self, tmp_path):
        """Create workflow instance for MCP mode testing."""
        config = SteeringConfig(interactive=False)  # MCP mode
        feature_flags = FeatureFlagConfig()
        
        workflow = AutonomousWorkflow(
            config=config,
            feature_flag_config=feature_flags,
            project_root=tmp_path
        )
        
        # Set up generated files
        workflow.generated_files = {
            "tech-stack.md": "# Tech Stack\n\n{Python version}\n{Framework}",
            "conventions.md": "# Conventions\n\nUse snake_case",
        }
        
        return workflow
    
    def test_mcp_mode_stores_draft(self, workflow):
        """Test MCP mode stores draft in workflow state."""
        result = workflow._step_review_draft()
        
        # Should return False (don't write files)
        assert result is False
        
        # Should have stored draft in state
        assert workflow.state.draft is not None
        assert isinstance(workflow.state.draft, DraftState)
        assert len(workflow.state.draft.files) == 2
    
    def test_mcp_mode_no_user_prompt(self, workflow):
        """Test MCP mode doesn't prompt user."""
        with patch('builtins.input') as mock_input:
            workflow._step_review_draft()
            
            # Should NOT have called input()
            mock_input.assert_not_called()
    
    def test_mcp_mode_draft_metadata(self, workflow):
        """Test MCP mode draft contains correct metadata."""
        workflow._step_review_draft()
        
        draft = workflow.state.draft
        
        # Check first file
        file1 = draft.files[0]
        assert file1.filename == "tech-stack.md"
        assert file1.placeholder_count == 2  # {Python version}, {Framework}
        assert file1.confidence == 0.8  # 1.0 - (2 * 0.1)
        assert len(file1.preview) <= 300
        
        # Check second file
        file2 = draft.files[1]
        assert file2.filename == "conventions.md"
        assert file2.placeholder_count == 0
        assert file2.confidence == 1.0  # No placeholders
    
    def test_mcp_mode_draft_not_approved(self, workflow):
        """Test MCP mode draft is not auto-approved."""
        workflow._step_review_draft()
        
        assert workflow.state.draft.is_approved is False


class TestWriteDraftToDisk:
    """Test writing draft files to disk."""
    
    @pytest.fixture
    def workflow_with_draft(self, tmp_path):
        """Create workflow with draft ready to write."""
        config = SteeringConfig(interactive=False)
        feature_flags = FeatureFlagConfig()
        
        workflow = AutonomousWorkflow(
            config=config,
            feature_flag_config=feature_flags,
            project_root=tmp_path
        )
        
        # Create draft
        files = [
            DraftFile(
                filename="tech-stack.md",
                content="# Tech Stack\n\nPython 3.11",
                confidence=0.9,
                placeholder_count=0,
                preview="Tech Stack"
            ),
            DraftFile(
                filename="conventions.md",
                content="# Conventions\n\nsnake_case",
                confidence=0.95,
                placeholder_count=0,
                preview="Conventions"
            ),
        ]
        
        workflow.state.draft = DraftState(
            files=files,
            created_at=datetime.now(),
            is_approved=False
        )
        
        return workflow
    
    def test_write_draft_to_disk_success(self, workflow_with_draft):
        """Test successfully writing draft files to disk."""
        result = workflow_with_draft.write_draft_to_disk()
        
        assert result is True
        assert workflow_with_draft.state.draft.is_approved is True
        
        # Check files were written
        steering_dir = workflow_with_draft.state.steering_dir
        assert (steering_dir / "tech-stack.md").exists()
        assert (steering_dir / "conventions.md").exists()
        
        # Check content
        tech_stack_content = (steering_dir / "tech-stack.md").read_text()
        assert "Python 3.11" in tech_stack_content
    
    def test_write_draft_no_draft_available(self, tmp_path):
        """Test writing draft when no draft exists."""
        config = SteeringConfig(interactive=False)
        feature_flags = FeatureFlagConfig()
        
        workflow = AutonomousWorkflow(
            config=config,
            feature_flag_config=feature_flags,
            project_root=tmp_path
        )
        
        # No draft set
        result = workflow.write_draft_to_disk()
        
        assert result is False


class TestWorkflowIntegration:
    """Test draft review integration in workflow execution."""
    
    @pytest.fixture
    def workflow(self, tmp_path):
        """Create workflow for integration testing."""
        config = SteeringConfig(interactive=False, skip_validation=True)
        feature_flags = FeatureFlagConfig()
        
        workflow = AutonomousWorkflow(
            config=config,
            feature_flag_config=feature_flags,
            project_root=tmp_path
        )
        
        return workflow
    
    def test_workflow_calls_review_before_write(self, workflow):
        """Test that workflow calls _step_review_draft before writing files."""
        # Mock the review step
        with patch.object(workflow, '_step_review_draft', return_value=False) as mock_review:
            with patch.object(workflow, '_step_write_files') as mock_write:
                with patch.object(workflow, '_step_generate_files_autonomously'):
                    with patch.object(workflow, '_step_create_staging_directory'):
                        with patch.object(workflow, '_step_check_existing_files', return_value=True):
                            with patch.object(workflow, '_step_analyze_code'):
                                with patch.object(workflow, '_step_parse_artifacts'):
                                    with patch.object(workflow, '_step_build_knowledge_base'):
                                        with patch.object(workflow, '_step_run_gap_analysis'):
                                            workflow.execute()
                
                # Review should be called
                mock_review.assert_called_once()
                
                # Write should NOT be called (review returned False)
                mock_write.assert_not_called()
    
    def test_mcp_mode_returns_success_with_draft(self, workflow):
        """Test MCP mode returns success even when files not written."""
        workflow.generated_files = {"test.md": "content"}
        
        with patch.object(workflow, '_step_generate_files_autonomously'):
            with patch.object(workflow, '_step_create_staging_directory'):
                with patch.object(workflow, '_step_check_existing_files', return_value=True):
                    with patch.object(workflow, '_step_analyze_code'):
                        with patch.object(workflow, '_step_parse_artifacts'):
                            with patch.object(workflow, '_step_build_knowledge_base'):
                                with patch.object(workflow, '_step_run_gap_analysis'):
                                    result = workflow.execute()
        
        # Should return True (success) even though files not written
        assert result is True
        
        # Draft should be stored
        assert workflow.state.draft is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
