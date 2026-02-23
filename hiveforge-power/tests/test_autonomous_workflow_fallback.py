"""
Unit tests for AutonomousWorkflow fallback handling (P0-3).

This module tests the fallback mechanisms in AutonomousWorkflow that ensure
no empty files are written and [INFERRED] markers are applied when generation fails.
"""

import re
from pathlib import Path
from textwrap import dedent
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hiveforge.steering.workflows.autonomous_workflow import AutonomousWorkflow
from hiveforge.steering.models import (
    SteeringConfig,
    FeatureFlagConfig,
    ConfidenceScore,
    WorkflowState,
)


@pytest.fixture
def temp_project_with_templates(tmp_path):
    """Create a temporary project with template files."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    # Create templates directory
    templates_dir = project_root / "hiveforge" / "templates" / "steering"
    templates_dir.mkdir(parents=True)
    
    # Create tech-stack.md template
    tech_stack_template = dedent('''
        ---
        title: Technology Stack
        ---
        
        # Technology Stack
        
        ## Backend
        - **Language:** {Python|Node.js|Go}
        
        ## Database
        - **Primary:** {PostgreSQL|MongoDB}
    ''').strip()
    
    (templates_dir / "tech-stack.md").write_text(tech_stack_template)
    
    # Create conventions.md template
    conventions_template = dedent('''
        ---
        title: Conventions
        ---
        
        # Conventions
        
        ## Naming
        {Describe naming conventions}
    ''').strip()
    
    (templates_dir / "conventions.md").write_text(conventions_template)
    
    return project_root


@pytest.fixture
def steering_config():
    """Create a basic steering config."""
    return SteeringConfig(
        analyze_code=False,
        skip_validation=True,
        interactive=False,
        research_enabled=False,
    )


@pytest.fixture
def feature_flag_config():
    """Create a feature flag config."""
    return FeatureFlagConfig(
        use_autonomous_generation=True,
        confidence_threshold=0.7,
    )


class TestGenerateFilesAutonomously:
    """Test _step_generate_files_autonomously() method."""
    
    @pytest.mark.asyncio
    async def test_catches_exceptions_during_generation(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that exceptions during generation are caught and handled."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Mock _generate_file_with_fallback to raise exception
        with patch.object(
            workflow,
            '_generate_file_with_fallback',
            side_effect=Exception("Generation error")
        ):
            # Should not raise exception
            await workflow._step_generate_files_autonomously()
            
            # Should have fallback content
            assert len(workflow.generated_files) > 0
            
            # All files should have content (no empty files)
            for filename, content in workflow.generated_files.items():
                assert content
                assert len(content.strip()) > 0
    
    @pytest.mark.asyncio
    async def test_applies_fallback_on_exception(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that _apply_fallback() is called when generation fails."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Mock _generate_file_with_fallback to raise exception
        with patch.object(
            workflow,
            '_generate_file_with_fallback',
            side_effect=Exception("Generation error")
        ):
            await workflow._step_generate_files_autonomously()
            
            # Should have applied fallback
            assert len(workflow.fallback_reasons) > 0
            
            # Fallback content should have [INFERRED] markers
            for filename, content in workflow.generated_files.items():
                assert "[INFERRED:" in content or "[GENERATION FAILED" in content


class TestApplyFallback:
    """Test _apply_fallback() method."""
    
    def test_loads_template_and_applies_inferred_markers(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that fallback loads template and applies [INFERRED] markers."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        content, confidence = workflow._apply_fallback(
            filename="tech-stack.md",
            error_reason="LLM unavailable"
        )
        
        # Should have [INFERRED] markers
        assert "[INFERRED:" in content
        assert "{" not in content  # Placeholders replaced
        
        # Should have low confidence
        assert confidence.value == 0.1

    
    def test_tracks_fallback_reason(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that fallback reason is tracked."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        initial_count = len(workflow.fallback_reasons)
        
        workflow._apply_fallback(
            filename="tech-stack.md",
            error_reason="Test error"
        )
        
        # Should have added fallback reason
        assert len(workflow.fallback_reasons) == initial_count + 1
        assert any("tech-stack.md" in reason for reason in workflow.fallback_reasons)
        assert any("Test error" in reason for reason in workflow.fallback_reasons)
    
    def test_sets_confidence_to_0_1(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that fallback sets confidence score to 0.1."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        content, confidence = workflow._apply_fallback(
            filename="tech-stack.md",
            error_reason="Test error"
        )
        
        assert confidence.value == 0.1
        assert isinstance(confidence, ConfidenceScore)
    
    def test_returns_error_message_when_fallback_fails(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that error message is returned when fallback also fails."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        # Try to apply fallback for non-existent template
        content, confidence = workflow._apply_fallback(
            filename="nonexistent.md",
            error_reason="Original error"
        )
        
        # Should return error message
        assert "[GENERATION FAILED" in content
        assert "nonexistent.md" in content
        assert "Original error" in content
        
        # Should have zero confidence
        assert confidence.value == 0.0


class TestFallbackReasonTracking:
    """Test fallback reason tracking."""
    
    def test_fallback_reasons_list_initialized(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that fallback_reasons list is initialized."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        assert hasattr(workflow, 'fallback_reasons')
        assert isinstance(workflow.fallback_reasons, list)
        assert len(workflow.fallback_reasons) == 0
    
    def test_fallback_reasons_include_exception_type(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that fallback reasons include exception type."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        workflow._apply_fallback(
            filename="tech-stack.md",
            error_reason="ValueError: Invalid input"
        )
        
        # Should track the error reason
        assert len(workflow.fallback_reasons) > 0
        assert any("ValueError" in reason or "Invalid input" in reason 
                  for reason in workflow.fallback_reasons)


class TestNoEmptyFiles:
    """Test that no empty files are written."""
    
    @pytest.mark.asyncio
    async def test_verifies_no_empty_files_after_generation(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that empty files are detected and replaced."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Mock to return empty content
        async def mock_generate_empty(*args, **kwargs):
            return ("", ConfidenceScore(value=0.0, level=None, evidence=[]))
        
        with patch.object(
            workflow,
            '_generate_file_with_fallback',
            side_effect=mock_generate_empty
        ):
            await workflow._step_generate_files_autonomously()
            
            # Should have replaced empty files
            for filename, content in workflow.generated_files.items():
                assert content
                assert len(content.strip()) > 0
                assert "[GENERATION FAILED" in content
    
    @pytest.mark.asyncio
    async def test_replaces_empty_files_with_error_message(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that empty files are replaced with error message."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Mock to return empty content
        async def mock_generate_empty(*args, **kwargs):
            return ("", ConfidenceScore(value=0.0, level=None, evidence=[]))
        
        with patch.object(
            workflow,
            '_generate_file_with_fallback',
            side_effect=mock_generate_empty
        ):
            await workflow._step_generate_files_autonomously()
            
            # All files should have error message
            for filename, content in workflow.generated_files.items():
                assert "[GENERATION FAILED" in content
                assert filename in content
    
    @pytest.mark.asyncio
    async def test_sets_zero_confidence_for_empty_files(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that empty files get zero confidence score."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Mock to return empty content
        async def mock_generate_empty(*args, **kwargs):
            return ("", ConfidenceScore(value=0.0, level=None, evidence=[]))
        
        with patch.object(
            workflow,
            '_generate_file_with_fallback',
            side_effect=mock_generate_empty
        ):
            await workflow._step_generate_files_autonomously()
            
            # All confidence scores should be 0.0
            for filename, confidence in workflow.confidence_scores.items():
                assert confidence.value == 0.0


class TestGenerateFileWithFallback:
    """Test _generate_file_with_fallback() method."""
    
    @pytest.mark.asyncio
    async def test_returns_content_on_success(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that content is returned on successful generation."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        # Mock successful generation
        async def mock_generate_success(*args, **kwargs):
            return ("# Content", ConfidenceScore(value=0.9, level=None, evidence=[]))
        
        with patch.object(
            workflow,
            '_generate_single_file',
            side_effect=mock_generate_success
        ):
            content, confidence = await workflow._generate_file_with_fallback(
                filename="tech-stack.md",
                previous_files={},
                questions=[]
            )
            
            assert content == "# Content"
            assert confidence.value == 0.9
    
    @pytest.mark.asyncio
    async def test_applies_fallback_on_exception(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that fallback is applied when generation raises exception."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        # Mock generation to raise exception
        async def mock_generate_error(*args, **kwargs):
            raise ValueError("Generation failed")
        
        with patch.object(
            workflow,
            '_generate_single_file',
            side_effect=mock_generate_error
        ):
            content, confidence = await workflow._generate_file_with_fallback(
                filename="tech-stack.md",
                previous_files={},
                questions=[]
            )
            
            # Should have fallback content
            assert "[INFERRED:" in content
            assert confidence.value == 0.1
    
    @pytest.mark.asyncio
    async def test_applies_fallback_on_empty_content(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that fallback is applied when LLM returns empty content."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        # Mock generation to return empty content
        async def mock_generate_empty(*args, **kwargs):
            return ("", ConfidenceScore(value=0.0, level=None, evidence=[]))
        
        with patch.object(
            workflow,
            '_generate_single_file',
            side_effect=mock_generate_empty
        ):
            content, confidence = await workflow._generate_file_with_fallback(
                filename="tech-stack.md",
                previous_files={},
                questions=[]
            )
            
            # Should have fallback content
            assert len(content) > 0
            assert "[INFERRED:" in content
            assert confidence.value == 0.1


class TestFallbackLogging:
    """Test that fallback reasons are logged."""
    
    def test_logs_fallback_with_exception_type(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test that fallback logs include exception type."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        workflow._apply_fallback(
            filename="tech-stack.md",
            error_reason="ValueError: Invalid configuration"
        )
        
        # Should have logged the error
        assert len(workflow.fallback_reasons) > 0
        reason = workflow.fallback_reasons[-1]
        assert "tech-stack.md" in reason
        assert "ValueError" in reason or "Invalid configuration" in reason


class TestIntegration:
    """Integration tests for fallback handling."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_fallback_flow(
        self, temp_project_with_templates, steering_config, feature_flag_config
    ):
        """Test complete fallback flow from generation to file writing."""
        workflow = AutonomousWorkflow(
            config=steering_config,
            feature_flag_config=feature_flag_config,
            project_root=temp_project_with_templates,
        )
        
        # Initialize workflow state
        workflow.state = WorkflowState(
            workflow_type="init",
            staging_dir=temp_project_with_templates / ".kiro" / "onboarding",
            steering_dir=temp_project_with_templates / ".kiro" / "steering",
        )
        
        # Mock generation to fail
        async def mock_generate_error(*args, **kwargs):
            raise Exception("LLM unavailable")
        
        with patch.object(
            workflow,
            '_generate_single_file',
            side_effect=mock_generate_error
        ):
            await workflow._step_generate_files_autonomously()
            
            # Should have generated files with fallback
            assert len(workflow.generated_files) > 0
            
            # All files should have [INFERRED] markers or error messages
            for filename, content in workflow.generated_files.items():
                assert content
                assert len(content.strip()) > 0
                # Should have either [INFERRED] markers or [GENERATION FAILED] message
                assert "[INFERRED:" in content or "[GENERATION FAILED" in content
            
            # Should have tracked fallback reasons
            assert len(workflow.fallback_reasons) > 0
            
            # All confidence scores should be low
            for filename, confidence in workflow.confidence_scores.items():
                assert confidence.value <= 0.1
