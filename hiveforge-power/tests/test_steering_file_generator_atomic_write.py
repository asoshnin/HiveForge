"""
Property test for SteeringFileGenerator atomic write behavior.

Tests that SteeringFileGenerator writes all 8 files or none (atomic transaction).

Requirements: 5.1, 5.2, 5.3
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from hiveforge.steering.steering_file_generator import SteeringFileGenerator
from hiveforge.steering.context_assembler import ContextAssembler
from hiveforge.steering.prompt_builder import PromptBuilder
from hiveforge.steering.models import (
    CodeAnalysisFacts,
    Dependency,
    NamingConventions,
)


class TestAtomicWriteProperty:
    """
    Property 6: Atomic write — all 8 files or none.
    
    If any draft fails validation, zero files are written to disk;
    if all pass, exactly 8 files are written.
    
    Requirements: 5.1, 5.2, 5.3
    """
    
    @pytest.mark.asyncio
    async def test_all_files_written_when_all_pass_validation(self, tmp_path):
        """
        Test that all 8 files are written when all drafts pass validation.
        
        Requirements: 5.1, 5.2
        """
        # Create mock LLM provider
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(**kwargs):
            return "# Test Steering File\n\n## Section 1\n\nContent here."
        
        mock_llm.complete = AsyncMock(side_effect=mock_complete)
        
        # Create generator
        generator = SteeringFileGenerator(mock_llm)
        
        # Create minimal context assembler and prompt builder
        context_assembler = ContextAssembler()
        prompt_builder = PromptBuilder()
        
        # Create minimal code facts
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="",
        )
        
        # Mock validation to always pass
        generator._validate_draft = MagicMock(return_value=[])
        generator._check_duplicate_paragraphs = MagicMock(return_value=[])
        
        # Generate all files
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = await generator.generate_all_files(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            code_facts=code_facts,
            source_docs=[],
            existing_steering={},
            delta=None,
            user_intent=None,
            use_case="new_from_docs",
            output_dir=output_dir,
        )
        
        # Assert result is successful
        assert result.success is True
        assert len(result.files_written) == 8
        assert len(result.validation_errors) == 0
        
        # Assert all 8 files exist on disk
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        
        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"Expected file {filename} to exist"
            assert file_path.read_text().startswith("# Test Steering File")
    
    @pytest.mark.asyncio
    async def test_no_files_written_when_first_draft_fails_validation(self, tmp_path):
        """
        Test that zero files are written when the first draft fails validation.
        
        Requirements: 5.1, 5.3
        """
        # Create mock LLM provider
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(**kwargs):
            return "# Test Steering File\n\n## Section 1\n\nContent here."
        
        mock_llm.complete = AsyncMock(side_effect=mock_complete)
        
        # Create generator
        generator = SteeringFileGenerator(mock_llm)
        
        # Create minimal context assembler and prompt builder
        context_assembler = ContextAssembler()
        prompt_builder = PromptBuilder()
        
        # Create minimal code facts
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="",
        )
        
        # Mock validation to fail on first template
        generator._validate_draft = MagicMock(return_value=["Validation error"])
        generator._check_duplicate_paragraphs = MagicMock(return_value=[])
        
        # Generate all files
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = await generator.generate_all_files(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            code_facts=code_facts,
            source_docs=[],
            existing_steering={},
            delta=None,
            user_intent=None,
            use_case="new_from_docs",
            output_dir=output_dir,
        )
        
        # Assert result is failure
        assert result.success is False
        assert len(result.files_written) == 0
        assert len(result.validation_errors) > 0
        
        # Assert NO files exist on disk (atomic failure)
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        
        for filename in expected_files:
            file_path = output_dir / filename
            assert not file_path.exists(), (
                f"File {filename} should NOT exist after validation failure"
            )
    
    @pytest.mark.asyncio
    async def test_no_files_written_when_middle_draft_fails_validation(self, tmp_path):
        """
        Test that zero files are written when a middle draft fails validation.
        
        Requirements: 5.1, 5.3
        """
        # Create mock LLM provider
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(**kwargs):
            return "# Test Steering File\n\n## Section 1\n\nContent here."
        
        mock_llm.complete = AsyncMock(side_effect=mock_complete)
        
        # Create generator
        generator = SteeringFileGenerator(mock_llm)
        
        # Create minimal context assembler and prompt builder
        context_assembler = ContextAssembler()
        prompt_builder = PromptBuilder()
        
        # Create minimal code facts
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="",
        )
        
        # Mock validation to fail on 4th template (conventions.md)
        call_count = 0
        
        def mock_validate(template_name, draft, code_facts):
            nonlocal call_count
            call_count += 1
            if call_count == 4:  # Fail on 4th template
                return ["Validation error on 4th template"]
            return []
        
        generator._validate_draft = mock_validate
        generator._check_duplicate_paragraphs = MagicMock(return_value=[])
        
        # Generate all files
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = await generator.generate_all_files(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            code_facts=code_facts,
            source_docs=[],
            existing_steering={},
            delta=None,
            user_intent=None,
            use_case="new_from_docs",
            output_dir=output_dir,
        )
        
        # Assert result is failure
        assert result.success is False
        assert len(result.files_written) == 0
        assert len(result.validation_errors) > 0
        
        # Assert NO files exist on disk (atomic failure)
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        
        for filename in expected_files:
            file_path = output_dir / filename
            assert not file_path.exists(), (
                f"File {filename} should NOT exist after validation failure"
            )
    
    @pytest.mark.asyncio
    async def test_no_files_written_when_last_draft_fails_validation(self, tmp_path):
        """
        Test that zero files are written when the last draft fails validation.
        
        Requirements: 5.1, 5.3
        """
        # Create mock LLM provider
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(**kwargs):
            return "# Test Steering File\n\n## Section 1\n\nContent here."
        
        mock_llm.complete = AsyncMock(side_effect=mock_complete)
        
        # Create generator
        generator = SteeringFileGenerator(mock_llm)
        
        # Create minimal context assembler and prompt builder
        context_assembler = ContextAssembler()
        prompt_builder = PromptBuilder()
        
        # Create minimal code facts
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="",
        )
        
        # Mock validation to fail on last template (testing.md)
        call_count = 0
        
        def mock_validate(template_name, draft, code_facts):
            nonlocal call_count
            call_count += 1
            if call_count == 8:  # Fail on 8th template
                return ["Validation error on last template"]
            return []
        
        generator._validate_draft = mock_validate
        generator._check_duplicate_paragraphs = MagicMock(return_value=[])
        
        # Generate all files
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = await generator.generate_all_files(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            code_facts=code_facts,
            source_docs=[],
            existing_steering={},
            delta=None,
            user_intent=None,
            use_case="new_from_docs",
            output_dir=output_dir,
        )
        
        # Assert result is failure
        assert result.success is False
        assert len(result.files_written) == 0
        assert len(result.validation_errors) > 0
        
        # Assert NO files exist on disk (atomic failure)
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        
        for filename in expected_files:
            file_path = output_dir / filename
            assert not file_path.exists(), (
                f"File {filename} should NOT exist after validation failure"
            )
    
    @pytest.mark.asyncio
    async def test_no_files_written_when_duplicate_paragraphs_detected(self, tmp_path):
        """
        Test that zero files are written when duplicate paragraphs are detected.
        
        Requirements: 5.1, 5.3
        """
        # Create mock LLM provider
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(**kwargs):
            return "# Test Steering File\n\n## Section 1\n\nContent here."
        
        mock_llm.complete = AsyncMock(side_effect=mock_complete)
        
        # Create generator
        generator = SteeringFileGenerator(mock_llm)
        
        # Create minimal context assembler and prompt builder
        context_assembler = ContextAssembler()
        prompt_builder = PromptBuilder()
        
        # Create minimal code facts
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="",
        )
        
        # Mock validation to pass, but duplicate check to fail
        generator._validate_draft = MagicMock(return_value=[])
        generator._check_duplicate_paragraphs = MagicMock(
            return_value=["Duplicate paragraph detected"]
        )
        
        # Generate all files
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = await generator.generate_all_files(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            code_facts=code_facts,
            source_docs=[],
            existing_steering={},
            delta=None,
            user_intent=None,
            use_case="new_from_docs",
            output_dir=output_dir,
        )
        
        # Assert result is failure
        assert result.success is False
        assert len(result.files_written) == 0
        assert len(result.validation_errors) > 0
        
        # Assert NO files exist on disk (atomic failure)
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        
        for filename in expected_files:
            file_path = output_dir / filename
            assert not file_path.exists(), (
                f"File {filename} should NOT exist after duplicate paragraph detection"
            )
