"""
Tests for InitWorkflow class.

This module contains unit tests for the InitWorkflow orchestrator that
coordinates the complete workflow for creating steering files from scratch.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import shutil

from src.hiveforge.steering.workflows.init_workflow import InitWorkflow
from src.hiveforge.steering.models import (
    SteeringConfig,
    ParsedDocument,
    CodeAnalysisResult,
    GapAnalysisResult,
    ValidationReport,
    LanguageInfo,
    TechStackInfo,
    ArchitectureInfo,
    ConventionsInfo,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def basic_config(temp_project_dir):
    """Create a basic SteeringConfig for testing."""
    return SteeringConfig(
        research_enabled=False,
        skip_validation=False,
        interactive=False,  # Non-interactive for automated tests
        strict_mode=False,
        backup_enabled=True,
        backup_dir=temp_project_dir / ".kiro" / "backups",  # Use temp dir for backups
        analyze_code=False,
    )


@pytest.fixture
def config_with_code_analysis(temp_project_dir):
    """Create a SteeringConfig with code analysis enabled."""
    return SteeringConfig(
        research_enabled=False,
        skip_validation=False,
        interactive=False,
        strict_mode=False,
        backup_enabled=True,
        backup_dir=temp_project_dir / ".kiro" / "backups",  # Use temp dir for backups
        analyze_code=True,
    )


class TestInitWorkflowInitialization:
    """Test InitWorkflow initialization."""
    
    def test_init_with_default_project_root(self, basic_config):
        """Test initialization with default project root."""
        workflow = InitWorkflow(basic_config)
        
        assert workflow.config == basic_config
        assert workflow.project_root == Path.cwd()
        assert workflow.state.workflow_type == "init"
        assert workflow.state.staging_dir == Path.cwd() / ".kiro" / "onboarding"
        assert workflow.state.steering_dir == Path.cwd() / ".kiro" / "steering"
    
    def test_init_with_custom_project_root(self, basic_config, temp_project_dir):
        """Test initialization with custom project root."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        assert workflow.project_root == temp_project_dir
        assert workflow.state.staging_dir == temp_project_dir / ".kiro" / "onboarding"
        assert workflow.state.steering_dir == temp_project_dir / ".kiro" / "steering"


class TestStepCreateStagingDirectory:
    """Test staging directory creation step."""
    
    def test_creates_staging_directory(self, basic_config, temp_project_dir):
        """Test that staging directory is created if it doesn't exist."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        assert not workflow.state.staging_dir.exists()
        
        workflow._step_create_staging_directory()
        
        assert workflow.state.staging_dir.exists()
        assert workflow.state.staging_dir.is_dir()
    
    def test_handles_existing_staging_directory(self, basic_config, temp_project_dir):
        """Test that existing staging directory is handled gracefully."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        # Create staging directory manually
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Should not raise error
        workflow._step_create_staging_directory()
        
        assert workflow.state.staging_dir.exists()
    
    def test_detects_empty_staging_folder(self, basic_config, temp_project_dir):
        """Test detection of empty staging folder."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Should complete without error
        workflow._step_create_staging_directory()
    
    def test_detects_staging_folder_with_files(self, basic_config, temp_project_dir):
        """Test detection of staging folder with files."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Add some test files
        (workflow.state.staging_dir / "test.md").write_text("# Test")
        (workflow.state.staging_dir / "test.pdf").write_text("PDF content")
        
        workflow._step_create_staging_directory()
        
        # Should detect files (tested via output, not asserting here)


class TestStepCheckExistingFiles:
    """Test existing file detection and backup step."""
    
    def test_no_existing_files_returns_true(self, basic_config, temp_project_dir):
        """Test that workflow proceeds when no existing files found."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        result = workflow._step_check_existing_files()
        
        assert result is True
    
    def test_empty_steering_dir_returns_true(self, basic_config, temp_project_dir):
        """Test that workflow proceeds when steering dir is empty."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.steering_dir.mkdir(parents=True, exist_ok=True)
        
        result = workflow._step_check_existing_files()
        
        assert result is True
    
    @patch('builtins.input', return_value='2')
    def test_existing_files_user_aborts(self, mock_input, basic_config, temp_project_dir):
        """Test that workflow aborts when user chooses to abort."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.steering_dir.mkdir(parents=True, exist_ok=True)
        (workflow.state.steering_dir / "test.md").write_text("# Test")
        
        result = workflow._step_check_existing_files()
        
        assert result is False
    
    @patch('builtins.input', return_value='1')
    def test_existing_files_user_backs_up(self, mock_input, basic_config, temp_project_dir):
        """Test that workflow proceeds with backup when user chooses option 1."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.steering_dir.mkdir(parents=True, exist_ok=True)
        (workflow.state.steering_dir / "test.md").write_text("# Test")
        
        result = workflow._step_check_existing_files()
        
        assert result is True
        # Check that backup was created
        backup_dir = workflow.config.backup_dir
        assert backup_dir.exists()
        backup_files = list(backup_dir.glob("steering_backup_*/test.md"))
        assert len(backup_files) == 1


class TestStepAnalyzeCode:
    """Test code analysis step."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.CodeAnalyzer')
    def test_analyzes_code_successfully(self, mock_analyzer_class, config_with_code_analysis, temp_project_dir):
        """Test successful code analysis."""
        workflow = InitWorkflow(config_with_code_analysis, project_root=temp_project_dir)
        
        # Mock analyzer
        mock_analyzer = Mock()
        mock_result = CodeAnalysisResult(
            languages=[LanguageInfo(name="Python", version="3.11", percentage=100.0)],
            tech_stack=TechStackInfo(backend_framework="FastAPI"),
            architecture=ArchitectureInfo(pattern="layered"),
            conventions=ConventionsInfo(naming_style={"functions": "snake_case"}),
        )
        mock_analyzer.analyze.return_value = mock_result
        mock_analyzer_class.return_value = mock_analyzer
        
        workflow._step_analyze_code()
        
        assert workflow.state.code_analysis == mock_result
        mock_analyzer_class.assert_called_once_with(temp_project_dir)
        mock_analyzer.analyze.assert_called_once()
    
    @patch('src.hiveforge.steering.workflows.init_workflow.CodeAnalyzer')
    def test_handles_code_analysis_failure(self, mock_analyzer_class, config_with_code_analysis, temp_project_dir):
        """Test graceful handling of code analysis failure."""
        workflow = InitWorkflow(config_with_code_analysis, project_root=temp_project_dir)
        
        # Mock analyzer to raise exception
        mock_analyzer = Mock()
        mock_analyzer.analyze.side_effect = Exception("Analysis failed")
        mock_analyzer_class.return_value = mock_analyzer
        
        # Should not raise exception
        workflow._step_analyze_code()
        
        assert workflow.state.code_analysis is None


class TestStepParseArtifacts:
    """Test artifact parsing step."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.parse_directory')
    @patch('src.hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_parses_artifacts_successfully(self, mock_is_empty, mock_parse, basic_config, temp_project_dir):
        """Test successful artifact parsing."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock non-empty staging folder
        mock_is_empty.return_value = False
        
        # Mock parsed documents
        mock_docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Test content",
                metadata={},
                parse_errors=[]
            )
        ]
        mock_parse.return_value = mock_docs
        
        workflow._step_parse_artifacts()
        
        assert workflow.state.parsed_documents == mock_docs
        mock_parse.assert_called_once_with(workflow.state.staging_dir)
    
    @patch('src.hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_skips_parsing_when_empty(self, mock_is_empty, basic_config, temp_project_dir):
        """Test that parsing is skipped when staging folder is empty."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        mock_is_empty.return_value = True
        
        workflow._step_parse_artifacts()
        
        assert workflow.state.parsed_documents == []


class TestStepBuildKnowledgeBase:
    """Test knowledge base building step."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    def test_builds_knowledge_base_with_documents_only(self, mock_kb_class, basic_config, temp_project_dir):
        """Test building knowledge base with only documents."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.parsed_documents = [
            ParsedDocument(file_path=Path("test.md"), content="Test", metadata={}, parse_errors=[])
        ]
        workflow.state.code_analysis = None
        
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        workflow._step_build_knowledge_base()
        
        assert workflow.state.knowledge_base == mock_kb
        mock_kb_class.assert_called_once_with(
            documents=workflow.state.parsed_documents,
            code_analysis=None
        )
    
    @patch('src.hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    def test_builds_knowledge_base_with_code_analysis(self, mock_kb_class, basic_config, temp_project_dir):
        """Test building knowledge base with code analysis."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.parsed_documents = []
        workflow.state.code_analysis = CodeAnalysisResult()
        
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        workflow._step_build_knowledge_base()
        
        assert workflow.state.knowledge_base == mock_kb
        mock_kb_class.assert_called_once_with(
            documents=[],
            code_analysis=workflow.state.code_analysis
        )


class TestStepRunGapAnalysis:
    """Test gap analysis step."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.GapAnalysisEngine')
    def test_runs_gap_analysis(self, mock_engine_class, basic_config, temp_project_dir):
        """Test running gap analysis."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.knowledge_base = Mock()
        
        mock_engine = Mock()
        mock_result = GapAnalysisResult(
            complete_sections={"tech-stack": ["Backend"]},
            missing_sections={"tech-stack": ["Frontend"]},
            ambiguous_sections={},
            questions=[]
        )
        mock_engine.analyze.return_value = mock_result
        mock_engine_class.return_value = mock_engine
        
        workflow._step_run_gap_analysis()
        
        assert workflow.state.gap_analysis == mock_result
        mock_engine_class.assert_called_once_with(workflow.state.knowledge_base)
        mock_engine.analyze.assert_called_once()


class TestStepConductConversation:
    """Test conversation step."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.SteeringAssistant')
    def test_conducts_conversation(self, mock_assistant_class, basic_config, temp_project_dir):
        """Test conducting conversation."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.knowledge_base = Mock()
        workflow.state.gap_analysis = GapAnalysisResult()
        
        mock_assistant = Mock()
        mock_gathered = {"tech-stack": {"Backend": "FastAPI"}}
        mock_assistant.conduct_conversation.return_value = mock_gathered
        mock_assistant_class.return_value = mock_assistant
        
        workflow._step_conduct_conversation()
        
        assert workflow.state.gathered_info == mock_gathered
        mock_assistant.conduct_conversation.assert_called_once_with(max_questions_per_batch=8)


class TestStepPopulateTemplates:
    """Test template population step."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    def test_populates_templates(self, mock_populator_class, basic_config, temp_project_dir):
        """Test populating templates."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.gathered_info = {"tech-stack": {"Backend": "FastAPI"}}
        workflow.state.code_analysis = None
        
        mock_populator = Mock()
        mock_files = {
            "tech-stack.md": "# Tech Stack\nBackend: FastAPI",
            "project-vision.md": "# Project Vision"
        }
        mock_populator.populate_all.return_value = mock_files
        mock_populator_class.return_value = mock_populator
        
        workflow._step_populate_templates()
        
        assert workflow.state.populated_files == mock_files


class TestStepWriteFiles:
    """Test file writing step."""
    
    def test_writes_files_to_steering_dir(self, basic_config, temp_project_dir):
        """Test writing files to steering directory."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.populated_files = {
            "tech-stack.md": "# Tech Stack",
            "project-vision.md": "# Project Vision"
        }
        
        workflow._step_write_files()
        
        # Check files were written
        assert (workflow.state.steering_dir / "tech-stack.md").exists()
        assert (workflow.state.steering_dir / "project-vision.md").exists()
        
        # Check content
        content = (workflow.state.steering_dir / "tech-stack.md").read_text()
        assert content == "# Tech Stack"


class TestStepRunValidation:
    """Test validation step."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.SteeringValidator')
    def test_runs_validation(self, mock_validator_class, basic_config, temp_project_dir):
        """Test running validation."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.steering_dir.mkdir(parents=True, exist_ok=True)
        
        mock_validator = Mock()
        mock_report = ValidationReport(
            files_checked=2,
            overall_status="pass"
        )
        mock_validator.validate_all.return_value = mock_report
        mock_validator_class.return_value = mock_validator
        
        workflow._step_run_validation()
        
        assert workflow.state.validation_report == mock_report
        mock_validator.validate_all.assert_called_once()
    
    @patch('src.hiveforge.steering.workflows.init_workflow.SteeringValidator')
    def test_handles_validation_failure(self, mock_validator_class, basic_config, temp_project_dir):
        """Test graceful handling of validation failure."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.steering_dir.mkdir(parents=True, exist_ok=True)
        
        mock_validator = Mock()
        mock_validator.validate_all.side_effect = Exception("Validation failed")
        mock_validator_class.return_value = mock_validator
        
        # Should not raise exception
        workflow._step_run_validation()


class TestCombineKnowledge:
    """Test knowledge combination logic."""
    
    def test_combines_gathered_info_and_code_analysis(self, basic_config, temp_project_dir):
        """Test combining gathered info with code analysis."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        workflow.state.gathered_info = {
            "project-vision": {"Elevator Pitch": "Test project"}
        }
        
        workflow.state.code_analysis = CodeAnalysisResult(
            tech_stack=TechStackInfo(
                backend_framework="FastAPI",
                database="PostgreSQL"
            ),
            architecture=ArchitectureInfo(
                pattern="layered",
                key_components=["API", "Service", "Database"]
            ),
            conventions=ConventionsInfo(
                naming_style={"functions": "snake_case"}
            )
        )
        
        combined = workflow._combine_knowledge()
        
        # Check gathered info is included
        assert "project-vision" in combined
        
        # Check code analysis is included
        assert "tech-stack" in combined
        assert combined["tech-stack"]["Backend"] == "FastAPI"
        assert combined["tech-stack"]["Database"] == "PostgreSQL"
        
        assert "architecture" in combined
        assert combined["architecture"]["Pattern"] == "layered"
        
        assert "conventions" in combined


class TestFullWorkflowExecution:
    """Test complete workflow execution."""
    
    @patch('src.hiveforge.steering.workflows.init_workflow.SteeringValidator')
    @patch('src.hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    @patch('src.hiveforge.steering.workflows.init_workflow.SteeringAssistant')
    @patch('src.hiveforge.steering.workflows.init_workflow.GapAnalysisEngine')
    @patch('src.hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    @patch('src.hiveforge.steering.workflows.init_workflow.parse_directory')
    @patch('src.hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_successful_workflow_execution(
        self,
        mock_is_empty,
        mock_parse,
        mock_kb_class,
        mock_engine_class,
        mock_assistant_class,
        mock_populator_class,
        mock_validator_class,
        basic_config,
        temp_project_dir
    ):
        """Test successful execution of complete workflow."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        # Mock all components
        mock_is_empty.return_value = False
        mock_parse.return_value = [
            ParsedDocument(file_path=Path("test.md"), content="Test", metadata={}, parse_errors=[])
        ]
        
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        mock_engine = Mock()
        mock_engine.analyze.return_value = GapAnalysisResult()
        mock_engine_class.return_value = mock_engine
        
        mock_assistant = Mock()
        mock_assistant.conduct_conversation.return_value = {}
        mock_assistant_class.return_value = mock_assistant
        
        mock_populator = Mock()
        mock_populator.populate_all.return_value = {"tech-stack.md": "# Tech Stack"}
        mock_populator_class.return_value = mock_populator
        
        mock_validator = Mock()
        mock_validator.validate_all.return_value = ValidationReport(files_checked=1, overall_status="pass")
        mock_validator_class.return_value = mock_validator
        
        # Execute workflow
        result = workflow.execute()
        
        assert result is True
        assert (workflow.state.steering_dir / "tech-stack.md").exists()
    
    @patch('src.hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    def test_workflow_handles_knowledge_base_failure(self, mock_kb_class, basic_config, temp_project_dir):
        """Test that workflow handles knowledge base failure gracefully."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        # Mock knowledge base to raise exception
        mock_kb_class.side_effect = Exception("Knowledge base failed")
        
        # Should handle error and return False
        result = workflow.execute()
        
        assert result is False


class TestBackupCreation:
    """Test backup creation functionality."""
    
    def test_creates_backup_with_timestamp(self, basic_config, temp_project_dir):
        """Test that backup is created with timestamp."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.steering_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test files
        test_file = workflow.state.steering_dir / "test.md"
        test_file.write_text("# Test")
        
        result = workflow._create_backup([test_file])
        
        assert result is True
        
        # Check backup was created
        backup_files = list(workflow.config.backup_dir.glob("steering_backup_*/test.md"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == "# Test"
    
    def test_backup_disabled_returns_true(self, basic_config, temp_project_dir):
        """Test that backup returns True when disabled."""
        basic_config.backup_enabled = False
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        result = workflow._create_backup([])
        
        assert result is True
    
    def test_backup_handles_failure(self, basic_config, temp_project_dir):
        """Test that backup handles failure gracefully."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        # Try to backup non-existent file
        result = workflow._create_backup([Path("/nonexistent/file.md")])
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
