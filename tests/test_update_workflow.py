"""
Tests for UpdateWorkflow class.

This module tests the update workflow for modifying existing steering files,
including conflict detection, customization preservation, diff generation,
and incremental updates.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from hiveforge.steering.workflows.update_workflow import UpdateWorkflow
from hiveforge.steering.models import (
    SteeringConfig,
    ParsedDocument,
    GapAnalysisResult,
    Conflict,
    Customization,
    FileDiff,
    DiffHunk,
    DiffLine,
    ValidationReport,
    ValidationIssue,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure with existing steering files."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    # Create steering directory with existing files
    steering_dir = project_root / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    
    # Create sample steering files
    (steering_dir / "project-vision.md").write_text(
        "# Project Vision\n\n## Problem Statement\nOld problem description\n"
    )
    (steering_dir / "tech-stack.md").write_text(
        "# Tech Stack\n\n## Backend\nOld: Python 3.10\n"
    )
    
    # Create staging directory
    staging_dir = project_root / ".kiro" / "onboarding"
    staging_dir.mkdir(parents=True)
    
    return project_root


@pytest.fixture
def config():
    """Create a default SteeringConfig."""
    return SteeringConfig(
        research_enabled=False,
        skip_validation=True,
        interactive=False,
        strict_mode=False,
        backup_enabled=False,
        backup_dir=Path("/tmp/backups")
    )


class TestUpdateWorkflowInitialization:
    """Test UpdateWorkflow initialization."""
    
    def test_init_creates_workflow_state(self, config, temp_project):
        """Test that initialization creates proper workflow state."""
        workflow = UpdateWorkflow(config, temp_project)
        
        assert workflow.config == config
        assert workflow.project_root == temp_project
        assert workflow.state.workflow_type == "update"
        assert workflow.state.staging_dir == temp_project / ".kiro" / "onboarding"
        assert workflow.state.steering_dir == temp_project / ".kiro" / "steering"
    
    def test_init_with_default_project_root(self, config):
        """Test initialization with default project root."""
        workflow = UpdateWorkflow(config)
        
        assert workflow.project_root == Path.cwd()
    
    def test_init_creates_empty_storage(self, config, temp_project):
        """Test that initialization creates empty storage dictionaries."""
        workflow = UpdateWorkflow(config, temp_project)
        
        assert workflow.existing_files == {}
        assert workflow.customizations == {}
        assert workflow.proposed_changes == {}
        assert workflow.diffs == {}


class TestUpdateWorkflowVerification:
    """Test verification of existing steering files."""
    
    def test_verify_existing_files_success(self, config, temp_project):
        """Test successful verification when files exist."""
        workflow = UpdateWorkflow(config, temp_project)
        
        result = workflow._step_verify_existing_files()
        
        assert result is True
    
    def test_verify_existing_files_no_directory(self, config, tmp_path):
        """Test verification fails when steering directory doesn't exist."""
        project_root = tmp_path / "empty_project"
        project_root.mkdir()
        
        workflow = UpdateWorkflow(config, project_root)
        
        result = workflow._step_verify_existing_files()
        
        assert result is False
    
    def test_verify_existing_files_empty_directory(self, config, tmp_path):
        """Test verification fails when steering directory is empty."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        steering_dir = project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        workflow = UpdateWorkflow(config, project_root)
        
        result = workflow._step_verify_existing_files()
        
        assert result is False


class TestUpdateWorkflowParsing:
    """Test parsing of existing files and new artifacts."""
    
    def test_parse_existing_files(self, config, temp_project):
        """Test parsing of existing steering files."""
        workflow = UpdateWorkflow(config, temp_project)
        
        workflow._step_parse_existing_files()
        
        assert len(workflow.existing_files) == 2
        assert "project-vision.md" in workflow.existing_files
        assert "tech-stack.md" in workflow.existing_files
        assert "Old problem description" in workflow.existing_files["project-vision.md"]
    
    def test_parse_new_artifacts_empty_staging(self, config, temp_project):
        """Test parsing when staging folder is empty."""
        workflow = UpdateWorkflow(config, temp_project)
        workflow.state.parsed_documents = []
        
        workflow._step_parse_new_artifacts()
        
        assert workflow.state.parsed_documents == []
    
    @patch('hiveforge.steering.workflows.update_workflow.parse_directory')
    def test_parse_new_artifacts_with_files(self, mock_parse, config, temp_project):
        """Test parsing when staging folder has artifacts."""
        # Create artifact in staging
        staging_dir = temp_project / ".kiro" / "onboarding"
        (staging_dir / "new-info.md").write_text("New information")
        
        # Mock parse_directory
        mock_doc = ParsedDocument(
            file_path=staging_dir / "new-info.md",
            content="New information",
            metadata={},
            parse_errors=[]
        )
        mock_parse.return_value = [mock_doc]
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow._step_parse_new_artifacts()
        
        assert len(workflow.state.parsed_documents) == 1
        assert workflow.state.parsed_documents[0].content == "New information"


class TestUpdateWorkflowCustomizationDetection:
    """Test detection of user customizations."""
    
    @patch('hiveforge.steering.workflows.update_workflow.get_all_templates')
    @patch('hiveforge.steering.workflows.update_workflow.CustomizationDetector')
    def test_detect_customizations(self, mock_detector_class, mock_get_templates, config, temp_project):
        """Test customization detection."""
        # Setup mocks
        mock_get_templates.return_value = {
            "project-vision": Mock()
        }
        
        mock_detector = Mock()
        mock_customization = Customization(
            section="Problem Statement",
            original="Old",
            customized="New",
            confidence=0.9
        )
        mock_detector.detect_customizations.return_value = [mock_customization]
        mock_detector_class.return_value = mock_detector
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.existing_files = {
            "project-vision.md": "# Project Vision\n\nCustomized content"
        }
        
        workflow._step_detect_customizations()
        
        assert "project-vision.md" in workflow.customizations
        assert len(workflow.customizations["project-vision.md"]) == 1
        assert workflow.customizations["project-vision.md"][0].confidence == 0.9


class TestUpdateWorkflowConflictDetection:
    """Test conflict detection between old and new information."""
    
    @patch('hiveforge.steering.workflows.update_workflow.ConflictResolver')
    def test_detect_conflicts_found(self, mock_resolver, config, temp_project):
        """Test conflict detection when conflicts exist."""
        mock_conflict = Conflict(
            section="Backend",
            old_value="Python 3.10",
            new_value="Python 3.11",
            explanation="Version conflict",
            resolution_options=["keep_old", "use_new", "merge"]
        )
        mock_resolver.detect_conflicts.return_value = [mock_conflict]
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.existing_files = {"tech-stack.md": "Backend: Python 3.10"}
        workflow.state.gathered_info = {"Backend": "Python 3.11"}
        
        workflow._step_detect_conflicts()
        
        assert len(workflow.state.conflicts) == 1
        assert workflow.state.conflicts[0].section == "Backend"
    
    @patch('hiveforge.steering.workflows.update_workflow.ConflictResolver')
    def test_detect_conflicts_none_found(self, mock_resolver, config, temp_project):
        """Test conflict detection when no conflicts exist."""
        mock_resolver.detect_conflicts.return_value = []
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.existing_files = {"tech-stack.md": "Backend: Python 3.10"}
        workflow.state.gathered_info = {"Frontend": "React 18"}
        
        workflow._step_detect_conflicts()
        
        assert len(workflow.state.conflicts) == 0


class TestUpdateWorkflowDiffGeneration:
    """Test diff generation for proposed changes."""
    
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    def test_generate_diffs(self, mock_diff_gen, config, temp_project):
        """Test diff generation."""
        mock_diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Backend: Python 3.10"],
            new_lines=["Backend: Python 3.11"],
            hunks=[
                DiffHunk(
                    old_start=1,
                    old_count=1,
                    new_start=1,
                    new_count=1,
                    lines=[
                        DiffLine(type="deletion", content="Backend: Python 3.10"),
                        DiffLine(type="addition", content="Backend: Python 3.11")
                    ]
                )
            ]
        )
        mock_diff_gen.compute_diff.return_value = mock_diff
        mock_diff_gen.has_changes.return_value = True
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.existing_files = {"tech-stack.md": "Backend: Python 3.10"}
        workflow.proposed_changes = {"tech-stack.md": "Backend: Python 3.11"}
        
        workflow._step_generate_diffs()
        
        assert "tech-stack.md" in workflow.diffs
        assert workflow.diffs["tech-stack.md"].file_name == "tech-stack.md"
    
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    def test_generate_diffs_no_changes(self, mock_diff_gen, config, temp_project):
        """Test diff generation when no changes exist."""
        mock_diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Backend: Python 3.10"],
            new_lines=["Backend: Python 3.10"],
            hunks=[]
        )
        mock_diff_gen.compute_diff.return_value = mock_diff
        mock_diff_gen.has_changes.return_value = False
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.existing_files = {"tech-stack.md": "Backend: Python 3.10"}
        workflow.proposed_changes = {"tech-stack.md": "Backend: Python 3.10"}
        
        workflow._step_generate_diffs()
        
        assert "tech-stack.md" in workflow.diffs


class TestUpdateWorkflowUserApproval:
    """Test user approval process."""
    
    @patch('builtins.input', return_value='y')
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    def test_get_user_approval_accepted(self, mock_diff_gen, mock_input, config, temp_project):
        """Test user approval when changes are accepted."""
        mock_diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Old"],
            new_lines=["New"],
            hunks=[DiffHunk(old_start=1, old_count=1, new_start=1, new_count=1, lines=[])]
        )
        mock_diff_gen.has_changes.return_value = True
        mock_diff_gen.format_diff.return_value = "diff output"
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.state.conflicts = []
        workflow.diffs = {"tech-stack.md": mock_diff}
        
        result = workflow._step_get_user_approval()
        
        assert result is True
    
    @patch('builtins.input', return_value='n')
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    def test_get_user_approval_rejected(self, mock_diff_gen, mock_input, config, temp_project):
        """Test user approval when changes are rejected."""
        mock_diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Old"],
            new_lines=["New"],
            hunks=[DiffHunk(old_start=1, old_count=1, new_start=1, new_count=1, lines=[])]
        )
        mock_diff_gen.has_changes.return_value = True
        mock_diff_gen.format_diff.return_value = "diff output"
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.state.conflicts = []
        workflow.diffs = {"tech-stack.md": mock_diff}
        
        result = workflow._step_get_user_approval()
        
        assert result is False
    
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    def test_get_user_approval_no_changes(self, mock_diff_gen, config, temp_project):
        """Test user approval when no changes exist."""
        mock_diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Same"],
            new_lines=["Same"],
            hunks=[]
        )
        mock_diff_gen.has_changes.return_value = False
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.state.conflicts = []
        workflow.diffs = {"tech-stack.md": mock_diff}
        
        result = workflow._step_get_user_approval()
        
        assert result is False


class TestUpdateWorkflowApplyChanges:
    """Test applying approved changes."""
    
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    def test_apply_changes(self, mock_diff_gen, config, temp_project):
        """Test applying changes to files."""
        mock_diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Old"],
            new_lines=["New"],
            hunks=[DiffHunk(old_start=1, old_count=1, new_start=1, new_count=1, lines=[])]
        )
        mock_diff_gen.has_changes.return_value = True
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.diffs = {"tech-stack.md": mock_diff}
        workflow.proposed_changes = {"tech-stack.md": "New content"}
        
        workflow._step_apply_changes()
        
        # Verify file was written
        file_path = temp_project / ".kiro" / "steering" / "tech-stack.md"
        assert file_path.read_text() == "New content"


class TestUpdateWorkflowValidation:
    """Test validation of updated files."""
    
    @patch('hiveforge.steering.workflows.update_workflow.SteeringValidator')
    def test_run_validation(self, mock_validator_class, config, temp_project):
        """Test validation step."""
        mock_validator = Mock()
        mock_report = ValidationReport(
            critical_issues=[],
            warnings=[],
            info=[],
            files_checked=2,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0
        )
        mock_validator.validate_all.return_value = mock_report
        mock_validator_class.return_value = mock_validator
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow._step_run_validation()
        
        assert workflow.state.validation_report is not None
        assert workflow.state.validation_report.overall_status == "pass"


class TestUpdateWorkflowIntegration:
    """Integration tests for complete update workflow."""
    
    @patch('hiveforge.steering.workflows.update_workflow.SteeringValidator')
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    @patch('hiveforge.steering.workflows.update_workflow.ConflictResolver')
    @patch('hiveforge.steering.workflows.update_workflow.CustomizationDetector')
    @patch('hiveforge.steering.workflows.update_workflow.TemplatePopulator')
    @patch('hiveforge.steering.workflows.update_workflow.SteeringAssistant')
    @patch('hiveforge.steering.workflows.update_workflow.GapAnalysisEngine')
    @patch('hiveforge.steering.workflows.update_workflow.KnowledgeBase')
    @patch('hiveforge.steering.workflows.update_workflow.parse_directory')
    @patch('builtins.input', return_value='y')
    def test_execute_complete_workflow(
        self,
        mock_input,
        mock_parse,
        mock_kb,
        mock_gap,
        mock_assistant,
        mock_populator,
        mock_detector_class,
        mock_resolver,
        mock_diff_gen,
        mock_validator_class,
        config,
        temp_project
    ):
        """Test complete update workflow execution."""
        # Setup mocks
        mock_parse.return_value = []
        
        mock_kb_instance = Mock()
        mock_kb.return_value = mock_kb_instance
        
        mock_gap_instance = Mock()
        mock_gap_instance.analyze.return_value = GapAnalysisResult(
            complete_sections={},
            missing_sections={},
            ambiguous_sections={},
            questions=[]
        )
        mock_gap.return_value = mock_gap_instance
        
        mock_assistant_instance = Mock()
        mock_assistant_instance.conduct_conversation.return_value = {}
        mock_assistant.return_value = mock_assistant_instance
        
        mock_populator_instance = Mock()
        mock_populator_instance.populate_all.return_value = {
            "tech-stack.md": "New content"
        }
        mock_populator.return_value = mock_populator_instance
        
        mock_detector = Mock()
        mock_detector.detect_customizations.return_value = []
        mock_detector_class.return_value = mock_detector
        
        mock_resolver.detect_conflicts.return_value = []
        
        mock_diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Old"],
            new_lines=["New"],
            hunks=[DiffHunk(old_start=1, old_count=1, new_start=1, new_count=1, lines=[])]
        )
        mock_diff_gen.compute_diff.return_value = mock_diff
        mock_diff_gen.has_changes.return_value = True
        mock_diff_gen.format_diff.return_value = "diff"
        
        mock_validator = Mock()
        mock_validator.validate_all.return_value = ValidationReport(
            critical_issues=[],
            warnings=[],
            info=[],
            files_checked=1,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0
        )
        mock_validator_class.return_value = mock_validator
        
        # Execute workflow
        config.skip_validation = False
        workflow = UpdateWorkflow(config, temp_project)
        result = workflow.execute()
        
        assert result is True
    
    def test_execute_no_existing_files(self, config, tmp_path):
        """Test workflow execution when no existing files exist."""
        project_root = tmp_path / "empty_project"
        project_root.mkdir()
        
        workflow = UpdateWorkflow(config, project_root)
        result = workflow.execute()
        
        assert result is False


class TestUpdateWorkflowErrorHandling:
    """Test error handling in update workflow."""
    
    def test_parse_existing_files_error(self, config, temp_project):
        """Test error handling when parsing existing files fails."""
        # Create a file with invalid encoding
        steering_dir = temp_project / ".kiro" / "steering"
        bad_file = steering_dir / "bad.md"
        bad_file.write_bytes(b'\x80\x81\x82')  # Invalid UTF-8
        
        workflow = UpdateWorkflow(config, temp_project)
        
        with pytest.raises(RuntimeError):
            workflow._step_parse_existing_files()
    
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    def test_apply_changes_error(self, mock_diff_gen, config, temp_project):
        """Test error handling when applying changes fails."""
        mock_diff_gen.has_changes.return_value = True
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.diffs = {"tech-stack.md": Mock()}
        workflow.proposed_changes = {"tech-stack.md": "New content"}
        
        # Make directory read-only to cause write error
        steering_dir = temp_project / ".kiro" / "steering"
        steering_dir.chmod(0o444)
        
        try:
            with pytest.raises(RuntimeError):
                workflow._step_apply_changes()
        finally:
            # Restore permissions
            steering_dir.chmod(0o755)


class TestUpdateWorkflowHelperMethods:
    """Test helper methods in UpdateWorkflow."""
    
    def test_parse_existing_content(self, config, temp_project):
        """Test parsing existing content into structured format."""
        workflow = UpdateWorkflow(config, temp_project)
        workflow.existing_files = {
            "tech-stack.md": "# Backend\nPython 3.10\n\n# Frontend\nReact 18"
        }
        
        content = workflow._parse_existing_content()
        
        assert "Backend" in content
        assert "Frontend" in content
        assert "Python 3.10" in content["Backend"]
        assert "React 18" in content["Frontend"]
    
    def test_combine_knowledge(self, config, temp_project):
        """Test combining existing and new knowledge."""
        workflow = UpdateWorkflow(config, temp_project)
        workflow.state.gathered_info = {
            "Backend": "Python 3.11",
            "Frontend": "React 18"
        }
        workflow.state.conflicts = []
        
        combined = workflow._combine_knowledge()
        
        assert combined["Backend"] == "Python 3.11"
        assert combined["Frontend"] == "React 18"
    
    def test_combine_knowledge_with_conflict_resolution(self, config, temp_project):
        """Test combining knowledge with resolved conflicts."""
        conflict = Conflict(
            section="Backend",
            old_value="Python 3.10",
            new_value="Python 3.11",
            explanation="Version conflict",
            resolution_options=["keep_old", "use_new", "merge"]
        )
        conflict.resolution = "Python 3.11"
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.state.gathered_info = {"Frontend": "React 18"}
        workflow.state.conflicts = [conflict]
        
        combined = workflow._combine_knowledge()
        
        assert combined["Backend"] == "Python 3.11"
        assert combined["Frontend"] == "React 18"


class TestUpdateWorkflowIdempotence:
    """Test idempotent behavior of update workflow."""
    
    @patch('hiveforge.steering.workflows.update_workflow.DiffGenerator')
    def test_no_changes_when_content_identical(self, mock_diff_gen, config, temp_project):
        """Test that no changes are proposed when content is identical."""
        mock_diff = FileDiff(
            file_name="tech-stack.md",
            old_lines=["Same"],
            new_lines=["Same"],
            hunks=[]
        )
        mock_diff_gen.compute_diff.return_value = mock_diff
        mock_diff_gen.has_changes.return_value = False
        
        workflow = UpdateWorkflow(config, temp_project)
        workflow.existing_files = {"tech-stack.md": "Same content"}
        workflow.proposed_changes = {"tech-stack.md": "Same content"}
        
        workflow._step_generate_diffs()
        
        # Verify no changes detected
        assert not mock_diff_gen.has_changes(workflow.diffs["tech-stack.md"])
