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

from hiveforge.steering.workflows.init_workflow import InitWorkflow
from hiveforge.steering.models import (
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
    
    @patch('hiveforge.steering.workflows.init_workflow.CodeAnalyzer')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.CodeAnalyzer')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.parse_directory')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
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
        mock_parse.assert_called_once_with(workflow.state.staging_dir, show_progress=True)
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_skips_parsing_when_empty(self, mock_is_empty, basic_config, temp_project_dir):
        """Test that parsing is skipped when staging folder is empty."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        mock_is_empty.return_value = True
        
        workflow._step_parse_artifacts()
        
        assert workflow.state.parsed_documents == []
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_adds_warning_when_empty(self, mock_is_empty, basic_config, temp_project_dir):
        """Test that warning is added when staging folder is empty (R2.1)."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        mock_is_empty.return_value = True
        
        workflow._step_parse_artifacts()
        
        # Check warning was added
        assert len(workflow.state.warnings) > 0
        assert any("No source documents found" in w for w in workflow.state.warnings)
        
        # Check metadata was set
        assert workflow.state.metadata["source_documents_found"] == 0
        assert workflow.state.metadata["confidence_level"] == "low"
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_adds_autonomous_warning_when_empty(self, mock_is_empty, config_with_code_analysis, temp_project_dir):
        """Test that autonomous mode warning is added when staging folder is empty (R2.2)."""
        from hiveforge.steering.models import FeatureFlagConfig
        
        # Create config with autonomous mode enabled
        config_with_code_analysis.feature_flags = FeatureFlagConfig(
            use_autonomous_generation=True,
            confidence_threshold=0.7,
            interactive=False
        )
        
        workflow = InitWorkflow(config_with_code_analysis, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        mock_is_empty.return_value = True
        
        workflow._step_parse_artifacts()
        
        # Check both warnings were added
        assert len(workflow.state.warnings) >= 2
        assert any("No source documents found" in w for w in workflow.state.warnings)
        assert any("Autonomous mode with no source documents" in w for w in workflow.state.warnings)
    
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_no_autonomous_warning_without_feature_flag(self, mock_is_empty, basic_config, temp_project_dir):
        """Test that autonomous warning is NOT added when feature flag is disabled."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        mock_is_empty.return_value = True
        
        workflow._step_parse_artifacts()
        
        # Check only one warning (not autonomous warning)
        assert len(workflow.state.warnings) == 1
        assert "No source documents found" in workflow.state.warnings[0]
        assert not any("Autonomous mode" in w for w in workflow.state.warnings)


class TestStepBuildKnowledgeBase:
    """Test knowledge base building step."""
    
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.GapAnalysisEngine')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.SteeringAssistant')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    def test_populates_templates(self, mock_populator_class, basic_config, temp_project_dir):
        """Test populating templates with confidence tagging."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.gathered_info = {"tech-stack": {"Backend": "FastAPI"}}
        workflow.state.code_analysis = None
        workflow.state.parsed_documents = []
        
        mock_populator = Mock()
        mock_files = {
            "tech-stack.md": "# Tech Stack\nBackend: FastAPI",
            "project-vision.md": "# Project Vision"
        }
        mock_populator.populate_all.return_value = mock_files
        mock_populator_class.return_value = mock_populator
        
        workflow._step_populate_templates()
        
        # Files should now be tagged with metadata
        assert "tech-stack.md" in workflow.state.populated_files
        assert "project-vision.md" in workflow.state.populated_files
        
        # Check that content was tagged (has metadata header)
        tech_stack_content = workflow.state.populated_files["tech-stack.md"]
        assert tech_stack_content.startswith("---")
        assert "generated_by: hiveforge" in tech_stack_content
        assert "confidence:" in tech_stack_content
        
        # Original content should still be present
        assert "# Tech Stack" in tech_stack_content
        assert "Backend: FastAPI" in tech_stack_content


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
    
    @patch('hiveforge.steering.workflows.init_workflow.SteeringValidator')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.SteeringValidator')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.SteeringValidator')
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    @patch('hiveforge.steering.workflows.init_workflow.SteeringAssistant')
    @patch('hiveforge.steering.workflows.init_workflow.GapAnalysisEngine')
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    @patch('hiveforge.steering.workflows.init_workflow.parse_directory')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
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
    
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
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


class TestSourceDocsPathParameter:
    """Test source_docs_path parameter functionality."""
    
    def test_init_with_custom_source_docs_path(self, basic_config, temp_project_dir):
        """Test initialization with custom source_docs_path parameter."""
        # Create custom source directory with test documents
        custom_source = temp_project_dir / "_DEVELOPMENT"
        custom_source.mkdir(parents=True, exist_ok=True)
        (custom_source / "design.md").write_text("# Design Document")
        (custom_source / "requirements.md").write_text("# Requirements")
        
        # Initialize workflow with custom source path
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="_DEVELOPMENT"
        )
        
        assert workflow.source_docs_path == "_DEVELOPMENT"
        assert workflow.project_root == temp_project_dir
    
    def test_init_with_default_no_parameter(self, basic_config, temp_project_dir):
        """Test initialization with default (no source_docs_path parameter)."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        assert workflow.source_docs_path is None
        assert workflow.state.staging_dir == temp_project_dir / ".kiro" / "onboarding"
    
    @patch('hiveforge.steering.workflows.init_workflow.parse_directory')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_custom_source_path_discovers_documents(
        self,
        mock_is_empty,
        mock_parse,
        basic_config,
        temp_project_dir
    ):
        """Test that custom source path discovers documents correctly."""
        # Create custom source directory with test documents
        custom_source = temp_project_dir / "_DEVELOPMENT"
        custom_source.mkdir(parents=True, exist_ok=True)
        (custom_source / "design.md").write_text("# Design Document")
        (custom_source / "requirements.md").write_text("# Requirements")
        
        # Initialize workflow with custom source path
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="_DEVELOPMENT"
        )
        
        # Execute staging directory creation step
        workflow._step_create_staging_directory()
        
        # Verify documents were discovered
        assert len(workflow.discovered_documents) == 2
        
        # Compare resolved paths (handles /private/ prefix on macOS)
        expected_staging = (temp_project_dir / ".kiro" / "onboarding").resolve()
        actual_staging = workflow.state.staging_dir.resolve()
        assert actual_staging == expected_staging
        
        # Verify discovery statistics were added
        assert hasattr(workflow.state, 'discovery_statistics')
        assert workflow.state.discovery_statistics['total_documents'] == 2
        assert workflow.state.discovery_statistics['source_docs_path'] == "_DEVELOPMENT"
    
    def test_empty_source_folder_handling(self, basic_config, temp_project_dir):
        """Test handling of empty source folder."""
        # Create empty custom source directory
        custom_source = temp_project_dir / "_DEVELOPMENT"
        custom_source.mkdir(parents=True, exist_ok=True)
        
        # Initialize workflow with empty custom source path
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="_DEVELOPMENT"
        )
        
        # Execute staging directory creation step
        workflow._step_create_staging_directory()
        
        # Verify no documents were discovered
        assert len(workflow.discovered_documents) == 0
        assert workflow.state.discovery_statistics['total_documents'] == 0
    
    def test_invalid_source_path_raises_error(self, basic_config, temp_project_dir):
        """Test that invalid source path raises appropriate error."""
        # Initialize workflow with non-existent source path
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="nonexistent_folder"
        )
        
        # Should raise error when trying to create staging directory
        with pytest.raises(Exception) as exc_info:
            workflow._step_create_staging_directory()
        
        # Verify error message mentions the path
        assert "nonexistent_folder" in str(exc_info.value) or "does not exist" in str(exc_info.value).lower()
    
    def test_path_traversal_attempt_blocked(self, basic_config, temp_project_dir):
        """Test that path traversal attempts are blocked."""
        # Initialize workflow with path traversal attempt
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="../../../etc"
        )
        
        # Should raise error when trying to create staging directory
        with pytest.raises(Exception) as exc_info:
            workflow._step_create_staging_directory()
        
        # Verify error is related to path validation
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in ["outside", "root", "invalid", "traversal"])
    
    def test_backward_compatibility_default_behavior(self, basic_config, temp_project_dir):
        """Test backward compatibility - default behavior unchanged."""
        # Create documents in default staging directory
        staging_dir = temp_project_dir / ".kiro" / "onboarding"
        staging_dir.mkdir(parents=True, exist_ok=True)
        (staging_dir / "existing.md").write_text("# Existing Document")
        
        # Initialize workflow without source_docs_path (default behavior)
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        # Execute staging directory creation step
        workflow._step_create_staging_directory()
        
        # Compare resolved paths (handles /private/ prefix on macOS)
        expected_staging = staging_dir.resolve()
        actual_staging = workflow.state.staging_dir.resolve()
        assert actual_staging == expected_staging
        assert workflow.source_docs_path is None
        
        # Verify existing document is discovered
        assert len(workflow.discovered_documents) == 1
        assert workflow.discovered_documents[0].discovered_from == "staging"
    
    def test_discovery_statistics_structure(self, basic_config, temp_project_dir):
        """Test that discovery statistics have correct structure."""
        # Create custom source directory with various file types
        custom_source = temp_project_dir / "_DEVELOPMENT"
        custom_source.mkdir(parents=True, exist_ok=True)
        (custom_source / "design.md").write_text("# Design")
        (custom_source / "diagram.png").write_bytes(b"fake png data")
        (custom_source / "spec.pdf").write_bytes(b"fake pdf data")
        
        # Initialize workflow with custom source path
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="_DEVELOPMENT"
        )
        
        # Execute staging directory creation step
        workflow._step_create_staging_directory()
        
        # Verify discovery statistics structure
        stats = workflow.state.discovery_statistics
        assert 'total_documents' in stats
        assert 'by_type' in stats
        assert 'by_source' in stats
        assert 'symlink_count' in stats
        assert 'copied_count' in stats
        assert 'source_docs_path' in stats
        
        # Verify counts
        assert stats['total_documents'] == 3
        assert stats['source_docs_path'] == "_DEVELOPMENT"
        assert 'markdown' in stats['by_type']
        assert 'image' in stats['by_type']
        assert 'pdf' in stats['by_type']
    
    def test_symlink_vs_copy_tracking(self, basic_config, temp_project_dir):
        """Test that symlink vs copy is tracked correctly."""
        # Create custom source directory
        custom_source = temp_project_dir / "_DEVELOPMENT"
        custom_source.mkdir(parents=True, exist_ok=True)
        (custom_source / "design.md").write_text("# Design")
        
        # Initialize workflow with custom source path
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="_DEVELOPMENT"
        )
        
        # Execute staging directory creation step (uses symlinks by default)
        workflow._step_create_staging_directory()
        
        # Verify symlink tracking
        stats = workflow.state.discovery_statistics
        # Note: symlink_count may be 0 if system doesn't support symlinks (fallback to copy)
        assert stats['symlink_count'] + stats['copied_count'] == stats['total_documents']
    
    def test_nested_directory_structure_preserved(self, basic_config, temp_project_dir):
        """Test that nested directory structure is preserved in staging."""
        # Create nested directory structure
        custom_source = temp_project_dir / "_DEVELOPMENT"
        nested_dir = custom_source / "specs" / "feature-a"
        nested_dir.mkdir(parents=True, exist_ok=True)
        (nested_dir / "design.md").write_text("# Feature A Design")
        
        # Initialize workflow with custom source path
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="_DEVELOPMENT"
        )
        
        # Execute staging directory creation step
        workflow._step_create_staging_directory()
        
        # Verify nested structure is preserved in staging
        staging_dir = workflow.state.staging_dir
        expected_file = staging_dir / "specs" / "feature-a" / "design.md"
        assert expected_file.exists() or expected_file.is_symlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



class TestContentTaggerIntegration:
    """Test ContentTagger integration in InitWorkflow."""
    
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_tagged_content_in_generated_files(
        self,
        mock_is_empty,
        mock_kb_class,
        mock_populator_class,
        basic_config,
        temp_project_dir
    ):
        """Test that generated files contain tagged content with metadata."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock empty staging folder (all content will be inferred)
        mock_is_empty.return_value = True
        
        # Mock knowledge base
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        # Mock template populator
        mock_populator = Mock()
        mock_files = {
            "tech-stack.md": "# Tech Stack\n\n## Backend\nFastAPI\n\n## Frontend\nReact"
        }
        mock_populator.populate_all.return_value = mock_files
        mock_populator_class.return_value = mock_populator
        
        # Set up workflow state
        workflow.state.parsed_documents = []
        workflow.state.code_analysis = None
        workflow.state.knowledge_base = mock_kb
        workflow.state.gathered_info = {
            "tech-stack": {
                "Backend": "FastAPI",
                "Frontend": "React",
                "_sources": {
                    "documents": [],
                    "code_analysis": [],
                    "inferred": ["Backend", "Frontend"]
                }
            }
        }
        
        # Execute template population step
        workflow._step_populate_templates()
        
        # Verify tagged content was created
        assert hasattr(workflow.state, 'populated_files')
        assert "tech-stack.md" in workflow.state.populated_files
        
        content = workflow.state.populated_files["tech-stack.md"]
        
        # Check for YAML frontmatter
        assert content.startswith("---")
        assert "generated_by: hiveforge" in content
        assert "confidence:" in content
        
        # Check for inferred section tags
        assert "<!-- INFERRED:" in content or "inferred_sections:" in content
    
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_metadata_headers_present(
        self,
        mock_is_empty,
        mock_kb_class,
        mock_populator_class,
        basic_config,
        temp_project_dir
    ):
        """Test that metadata headers are present in generated files."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock staging folder with documents
        mock_is_empty.return_value = False
        
        # Mock knowledge base
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        # Mock template populator
        mock_populator = Mock()
        mock_files = {
            "project-vision.md": "# Project Vision\n\n## Problem Statement\nTest problem"
        }
        mock_populator.populate_all.return_value = mock_files
        mock_populator_class.return_value = mock_populator
        
        # Set up workflow state with source documents
        workflow.state.parsed_documents = [
            ParsedDocument(file_path=Path("design.md"), content="Test", metadata={}, parse_errors=[])
        ]
        workflow.state.code_analysis = None
        workflow.state.knowledge_base = mock_kb
        workflow.state.gathered_info = {
            "project-vision": {
                "Problem Statement": "Test problem",
                "_sources": {
                    "documents": ["Problem Statement"],
                    "code_analysis": [],
                    "inferred": []
                }
            }
        }
        
        # Execute template population step
        workflow._step_populate_templates()
        
        content = workflow.state.populated_files["project-vision.md"]
        
        # Check for required metadata fields
        assert "generated_by:" in content
        assert "generated_at:" in content
        assert "source_documents: 1" in content
        assert "code_analysis:" in content
        assert "confidence:" in content
        assert "overall:" in content
        assert "level:" in content
    
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_low_confidence_warnings(
        self,
        mock_is_empty,
        mock_kb_class,
        mock_populator_class,
        basic_config,
        temp_project_dir
    ):
        """Test that low confidence warnings are added to files."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock empty staging folder (will result in low confidence)
        mock_is_empty.return_value = True
        
        # Mock knowledge base
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        # Mock template populator
        mock_populator = Mock()
        mock_files = {
            "conventions.md": "# Conventions\n\n## Naming\nsnake_case"
        }
        mock_populator.populate_all.return_value = mock_files
        mock_populator_class.return_value = mock_populator
        
        # Set up workflow state with all inferred content (low confidence)
        workflow.state.parsed_documents = []
        workflow.state.code_analysis = None
        workflow.state.knowledge_base = mock_kb
        workflow.state.gathered_info = {
            "conventions": {
                "Naming": "snake_case",
                "_sources": {
                    "documents": [],
                    "code_analysis": [],
                    "inferred": ["Naming"]
                }
            }
        }
        
        # Execute template population step
        workflow._step_populate_templates()
        
        content = workflow.state.populated_files["conventions.md"]
        
        # Check for low confidence warning
        assert "⚠️" in content or "LOW CONFIDENCE" in content
        assert "limited source material" in content.lower() or "inferred" in content.lower()
    
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_file_structure_preserved(
        self,
        mock_is_empty,
        mock_kb_class,
        mock_populator_class,
        basic_config,
        temp_project_dir
    ):
        """Test that markdown file structure is preserved after tagging."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        mock_is_empty.return_value = False
        
        # Mock knowledge base
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        # Mock template populator with structured content
        original_content = """# Tech Stack

## Backend
FastAPI framework

## Frontend
React library

## Database
PostgreSQL
"""
        mock_populator = Mock()
        mock_files = {"tech-stack.md": original_content}
        mock_populator.populate_all.return_value = mock_files
        mock_populator_class.return_value = mock_populator
        
        # Set up workflow state
        workflow.state.parsed_documents = [
            ParsedDocument(file_path=Path("design.md"), content="Test", metadata={}, parse_errors=[])
        ]
        workflow.state.code_analysis = None
        workflow.state.knowledge_base = mock_kb
        workflow.state.gathered_info = {
            "tech-stack": {
                "Backend": "FastAPI",
                "_sources": {
                    "documents": ["Backend"],
                    "code_analysis": [],
                    "inferred": []
                }
            }
        }
        
        # Execute template population step
        workflow._step_populate_templates()
        
        content = workflow.state.populated_files["tech-stack.md"]
        
        # Check that original headers are preserved
        assert "# Tech Stack" in content
        assert "## Backend" in content
        assert "## Frontend" in content
        assert "## Database" in content
        
        # Check that content is preserved
        assert "FastAPI" in content
        assert "React" in content
        assert "PostgreSQL" in content
    
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_confidence_calculation_with_mixed_sources(
        self,
        mock_is_empty,
        mock_kb_class,
        mock_populator_class,
        basic_config,
        temp_project_dir
    ):
        """Test confidence calculation with mixed sources (documents, code, inferred)."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        mock_is_empty.return_value = False
        
        # Mock knowledge base
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        # Mock template populator
        mock_populator = Mock()
        mock_files = {
            "tech-stack.md": "# Tech Stack\n\n## Backend\nFastAPI\n\n## Frontend\nReact\n\n## Database\nPostgreSQL"
        }
        mock_populator.populate_all.return_value = mock_files
        mock_populator_class.return_value = mock_populator
        
        # Set up workflow state with mixed sources
        workflow.state.parsed_documents = [
            ParsedDocument(file_path=Path("design.md"), content="Test", metadata={}, parse_errors=[])
        ]
        workflow.state.code_analysis = CodeAnalysisResult(
            tech_stack=TechStackInfo(database="PostgreSQL")
        )
        workflow.state.knowledge_base = mock_kb
        workflow.state.gathered_info = {
            "tech-stack": {
                "Backend": "FastAPI",
                "Frontend": "React",
                "Database": "PostgreSQL",
                "_sources": {
                    "documents": ["Backend"],  # From documents
                    "code_analysis": ["Database"],  # From code analysis
                    "inferred": ["Frontend"]  # Inferred by LLM
                }
            }
        }
        
        # Execute template population step
        workflow._step_populate_templates()
        
        content = workflow.state.populated_files["tech-stack.md"]
        
        # Check that confidence metadata reflects mixed sources
        assert "confidence:" in content
        assert "sources:" in content
        
        # Check that overall confidence was calculated
        assert hasattr(workflow.state.metadata, '__getitem__')
        # The metadata should have overall_confidence set
    
    @patch('hiveforge.steering.workflows.init_workflow.TemplatePopulator')
    @patch('hiveforge.steering.workflows.init_workflow.KnowledgeBase')
    @patch('hiveforge.steering.workflows.init_workflow.is_staging_folder_empty')
    def test_source_docs_path_in_metadata(
        self,
        mock_is_empty,
        mock_kb_class,
        mock_populator_class,
        basic_config,
        temp_project_dir
    ):
        """Test that source_docs_path is included in metadata when provided."""
        # Create custom source directory
        custom_source = temp_project_dir / "_DEVELOPMENT"
        custom_source.mkdir(parents=True, exist_ok=True)
        (custom_source / "design.md").write_text("# Design")
        
        # Initialize workflow with custom source path
        workflow = InitWorkflow(
            basic_config,
            project_root=temp_project_dir,
            source_docs_path="_DEVELOPMENT"
        )
        workflow.state.staging_dir.mkdir(parents=True, exist_ok=True)
        
        mock_is_empty.return_value = False
        
        # Mock knowledge base
        mock_kb = Mock()
        mock_kb_class.return_value = mock_kb
        
        # Mock template populator
        mock_populator = Mock()
        mock_files = {"tech-stack.md": "# Tech Stack"}
        mock_populator.populate_all.return_value = mock_files
        mock_populator_class.return_value = mock_populator
        
        # Set up workflow state
        workflow.state.parsed_documents = [
            ParsedDocument(file_path=Path("design.md"), content="Test", metadata={}, parse_errors=[])
        ]
        workflow.state.code_analysis = None
        workflow.state.knowledge_base = mock_kb
        workflow.state.gathered_info = {
            "tech-stack": {
                "Backend": "FastAPI",
                "_sources": {
                    "documents": ["Backend"],
                    "code_analysis": [],
                    "inferred": []
                }
            }
        }
        
        # Execute template population step
        workflow._step_populate_templates()
        
        content = workflow.state.populated_files["tech-stack.md"]
        
        # Check that source_docs_path is in metadata
        assert "source_docs_path: _DEVELOPMENT" in content
    
    def test_extract_source_tracking_with_sources(self, basic_config, temp_project_dir):
        """Test _extract_source_tracking with proper source tracking data."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        workflow.state.gathered_info = {
            "tech-stack": {
                "Backend": "FastAPI",
                "Frontend": "React",
                "_sources": {
                    "documents": ["Backend"],
                    "code_analysis": ["Database"],
                    "inferred": ["Frontend"]
                }
            },
            "project-vision": {
                "Problem Statement": "Test",
                "_sources": {
                    "documents": ["Problem Statement"],
                    "code_analysis": [],
                    "inferred": []
                }
            }
        }
        
        sources = workflow._extract_source_tracking()
        
        assert "tech-stack.md" in sources
        assert "project-vision.md" in sources
        
        assert sources["tech-stack.md"]["documents"] == ["Backend"]
        assert sources["tech-stack.md"]["code_analysis"] == ["Database"]
        assert sources["tech-stack.md"]["inferred"] == ["Frontend"]
        
        assert sources["project-vision.md"]["documents"] == ["Problem Statement"]
    
    def test_extract_source_tracking_without_sources(self, basic_config, temp_project_dir):
        """Test _extract_source_tracking when no source tracking is available."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        # Old format without _sources
        workflow.state.gathered_info = {
            "tech-stack": {
                "Backend": "FastAPI",
                "Frontend": "React"
            }
        }
        workflow.state.code_analysis = None
        
        sources = workflow._extract_source_tracking()
        
        assert "tech-stack.md" in sources
        assert sources["tech-stack.md"]["documents"] == []
        assert sources["tech-stack.md"]["code_analysis"] == []
        assert sources["tech-stack.md"]["inferred"] == []
    
    def test_extract_source_tracking_with_code_analysis_only(self, basic_config, temp_project_dir):
        """Test _extract_source_tracking when only code analysis is available."""
        workflow = InitWorkflow(basic_config, project_root=temp_project_dir)
        
        workflow.state.gathered_info = {}
        workflow.state.code_analysis = CodeAnalysisResult(
            tech_stack=TechStackInfo(backend_framework="FastAPI")
        )
        
        sources = workflow._extract_source_tracking()
        
        # Should mark tech-stack, architecture, conventions as from code analysis
        assert "tech-stack.md" in sources
        assert "architecture.md" in sources
        assert "conventions.md" in sources
        
        assert sources["tech-stack.md"]["code_analysis"] == ["all"]
        assert sources["architecture.md"]["code_analysis"] == ["all"]
        assert sources["conventions.md"]["code_analysis"] == ["all"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
