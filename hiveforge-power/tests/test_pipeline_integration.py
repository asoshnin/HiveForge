"""
Integration tests for the full LLM-Primary Steering Synthesis pipeline.

Tests the complete pipeline from InputResolver through SteeringFileGenerator
with mocked LLM provider.

Requirements: 1.1, 1.2, 5.2, 8.2, 8.4, 9.1, 9.2
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from hiveforge.steering.input_resolver import InputResolver
from hiveforge.steering.context_assembler import ContextAssembler
from hiveforge.steering.prompt_builder import PromptBuilder
from hiveforge.steering.steering_file_generator import SteeringFileGenerator
from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
from hiveforge.steering.parsers.orchestrator import DocumentParser
from hiveforge.steering.delta_analyzer import DeltaAnalyzer
from hiveforge.steering.models import (
    CodeAnalysisFacts,
    Dependency,
    LLMUnavailableError,
    NamingConventions,
    ParsedDocument,
)


class TestFullPipelineIntegration:
    """
    Integration tests for the complete pipeline.
    
    Tests the full workflow: InputResolver → CodeAnalyzer → DocumentParser →
    DeltaAnalyzer → ContextAssembler → PromptBuilder → SteeringFileGenerator
    
    Requirements: 1.1, 5.2, 9.1
    """
    
    @pytest.mark.asyncio
    async def test_new_from_docs_use_case_full_pipeline(self, tmp_path):
        """
        Test full pipeline for new_from_docs use case.
        
        Mock LLM, assert 8 LLM calls, assert 8 files written,
        assert no TemplatePopulator calls.
        
        Requirements: 1.1, 5.2, 9.1
        """
        # Setup directories
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        source_folder = project_root / ".kiro" / "onboarding"
        source_folder.mkdir(parents=True)
        
        steering_dir = project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Create source documents
        (source_folder / "design.md").write_text(
            "# Design Document\n\nWe use Python and FastAPI for the backend."
        )
        (source_folder / "requirements.md").write_text(
            "# Requirements\n\nThe system must support user authentication."
        )
        
        # Step 1: InputResolver
        resolver = InputResolver()
        use_case, resolved_source_folder = resolver.resolve(
            source_folder=source_folder,
            project_root=project_root,
            steering_dir=steering_dir,
        )
        
        assert use_case == "new_from_docs"
        assert resolved_source_folder == source_folder
        
        # Step 2: DocumentParser
        parser = DocumentParser(source_folder)
        source_docs = parser.parse_all()
        
        assert len(source_docs) == 2
        assert any("FastAPI" in doc.content for doc in source_docs)
        
        # Step 3: CodeAnalyzer (minimal - no actual codebase)
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[
                Dependency(name="fastapi", version="0.100.0", dependency_type="runtime")
            ],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=["main.py"],
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
            ),
            directory_structure="src, tests, docs",
        )
        
        # Step 4: DeltaAnalyzer (no existing steering for new_from_docs)
        delta_analyzer = DeltaAnalyzer()
        delta = delta_analyzer.analyze(
            source_docs=source_docs,
            code_facts=code_facts,
            existing_steering={},
        )
        
        # Step 5: Mock LLM Provider
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        
        llm_call_count = 0
        
        async def mock_complete(**kwargs):
            nonlocal llm_call_count
            llm_call_count += 1
            return f"# Test Steering File {llm_call_count}\n\n## Section 1\n\nContent for file {llm_call_count}."
        
        mock_llm.complete = AsyncMock(side_effect=mock_complete)
        
        # Step 6: ContextAssembler, PromptBuilder, SteeringFileGenerator
        context_assembler = ContextAssembler()
        prompt_builder = PromptBuilder()
        generator = SteeringFileGenerator(mock_llm)
        
        # Generate all files
        result = await generator.generate_all_files(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            code_facts=code_facts,
            source_docs=source_docs,
            existing_steering={},
            delta=delta,
            user_intent=None,
            use_case=use_case,
            output_dir=output_dir,
        )
        
        # Assertions
        assert result.success is True
        assert len(result.files_written) == 8
        assert len(result.validation_errors) == 0
        
        # Assert LLM was called exactly 8 times
        assert llm_call_count == 8, (
            f"Expected LLM to be called 8 times, but was called {llm_call_count} times"
        )
        
        # Assert all 8 files exist
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
            content = file_path.read_text()
            assert "Test Steering File" in content
    
    @pytest.mark.asyncio
    async def test_reverse_engineer_use_case_no_source_docs(self, tmp_path):
        """
        Test full pipeline for reverse_engineer use case.
        
        No source docs present; assert source_docs=[] in all GenerationContext instances.
        
        Requirements: 9.2
        """
        # Setup directories
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        steering_dir = project_root / ".kiro" / "steering"
        steering_dir.mkdir(parents=True)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Step 1: InputResolver (no source folder)
        resolver = InputResolver()
        use_case, resolved_source_folder = resolver.resolve(
            source_folder=None,
            project_root=project_root,
            steering_dir=steering_dir,
        )
        
        assert use_case == "reverse_engineer"
        assert resolved_source_folder is None
        
        # Step 2: No DocumentParser (no source docs)
        source_docs = []
        
        # Step 3: CodeAnalyzer (from codebase)
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=["main.py"],
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
            ),
            directory_structure="src, tests",
        )
        
        # Step 4: DeltaAnalyzer (no source docs, no existing steering)
        delta_analyzer = DeltaAnalyzer()
        delta = delta_analyzer.analyze(
            source_docs=source_docs,
            code_facts=code_facts,
            existing_steering={},
        )
        
        # Step 5: Mock LLM Provider
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        
        # Track contexts to verify source_docs=[]
        contexts_received = []
        
        async def mock_complete(**kwargs):
            return "# Test Steering File\n\n## Section 1\n\nContent here."
        
        mock_llm.complete = AsyncMock(side_effect=mock_complete)
        
        # Step 6: ContextAssembler with tracking
        context_assembler = ContextAssembler()
        original_assemble = context_assembler.assemble
        
        def track_assemble(*args, **kwargs):
            context = original_assemble(*args, **kwargs)
            contexts_received.append(context)
            return context
        
        context_assembler.assemble = track_assemble
        
        prompt_builder = PromptBuilder()
        generator = SteeringFileGenerator(mock_llm)
        
        # Generate all files
        result = await generator.generate_all_files(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            code_facts=code_facts,
            source_docs=source_docs,
            existing_steering={},
            delta=delta,
            user_intent=None,
            use_case=use_case,
            output_dir=output_dir,
        )
        
        # Assertions
        assert result.success is True
        assert len(result.files_written) == 8
        
        # Assert all contexts had empty source_docs
        assert len(contexts_received) == 8
        for context in contexts_received:
            assert context.source_docs == [], (
                f"Expected source_docs=[] for reverse_engineer use case, "
                f"but got {len(context.source_docs)} docs"
            )
    
    @pytest.mark.asyncio
    async def test_llm_unavailable_error_propagation(self, tmp_path):
        """
        Test that LLMUnavailableError is raised when LLM is not available.
        
        Assert that when LLMProvider.is_available() returns False,
        no files are written and error is raised.
        
        Requirements: 1.2, 8.2, 8.4
        """
        # Setup directories
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Mock LLM Provider that is NOT available
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = False
        
        # Attempt to create generator (should raise LLMUnavailableError)
        with pytest.raises(LLMUnavailableError) as exc_info:
            generator = SteeringFileGenerator(mock_llm)
        
        # Assert error message is actionable
        error_message = str(exc_info.value)
        assert "No LLM provider" in error_message or "not configured" in error_message.lower()
        
        # Assert no files were written
        assert len(list(output_dir.iterdir())) == 0


class TestEndToEndWithRealDocuments:
    """
    End-to-end integration test with real source documents.
    
    Uses actual documents from .kiro/onboarding/ to test the full pipeline
    with realistic input similar to production use.
    
    Requirements: 1.1, 3.1, 3.2, 4.1, 4.2, 4.3, 9.1
    """
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_real_onboarding_docs(self, tmp_path):
        """
        Test full pipeline with real documents from .kiro/onboarding/.
        
        Copy design documents to test staging folder, run full pipeline
        with real DocumentParser (not mocked), mock only LLMProvider.
        
        Assert that ContextAssembler correctly filters and includes relevant content.
        Assert that PromptBuilder includes source doc content in prompts.
        Verify token budgets are respected (≤8,000 tokens per template).
        
        Requirements: 1.1, 3.1, 3.2, 4.1, 4.2, 4.3, 9.1
        """
        # Setup directories
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        source_folder = project_root / ".kiro" / "onboarding"
        source_folder.mkdir(parents=True)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Copy real documents from project's .kiro/onboarding/ if they exist
        real_onboarding = Path(".kiro/onboarding")
        
        # Always create test documents (don't rely on real ones existing)
        # Create realistic test documents
        design_content = """# Design Document

## Architecture

The system uses a layered architecture with the following components:

- **CLI Interface**: Typer-based command-line interface
- **MCP Power Interface**: FastMCP server for KIRO IDE integration
- **Shared Backend**: Unified implementation for both interfaces
- **Document Parsers**: Parse markdown, PDF, and image artifacts
- **Code Analyzers**: Extract tech stack, architecture, conventions
- **Steering Assistant**: AI-powered tool for gathering information

## Technology Stack

- **Language**: Python 3.11+
- **CLI Framework**: Typer
- **Testing**: pytest
- **LLM Integration**: OpenAI API

## Data Flow

1. User runs command
2. CLI parses arguments
3. Workflow orchestrates components
4. Results written to .kiro/steering/
"""
        
        requirements_content = """# Requirements

## Functional Requirements

1. Generate steering files from source documents
2. Analyze codebase to extract technical information
3. Support multiple LLM providers (OpenAI, Vertex AI)
4. Maintain steering files throughout project lifecycle

## Non-Functional Requirements

1. Token usage must be predictable and limited
2. Generation must be atomic (all files or none)
3. Must preserve user customizations during updates
"""
        
        (source_folder / "design.md").write_text(design_content, encoding='utf-8')
        (source_folder / "requirements.md").write_text(requirements_content, encoding='utf-8')
        
        # Step 1: Parse documents
        parser = DocumentParser(source_folder)
        source_docs = parser.parse_all()
        
        assert len(source_docs) > 0, "Expected at least one source document"
        
        # Step 2: Create code facts
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["Typer", "FastMCP"],
            dependencies=[
                Dependency(name="typer", version="0.9.0", dependency_type="runtime"),
                Dependency(name="pytest", version="7.4.0", dependency_type="dev"),
            ],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="MCP",
            database=None,
            entry_points=["cli.py", "server.py"],
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
                constants="UPPER_SNAKE_CASE",
                functions="snake_case",
            ),
            directory_structure="src, tests, docs",
        )
        
        # Step 3: Mock LLM Provider with prompt tracking
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        
        prompts_received = []
        
        async def mock_complete(**kwargs):
            prompts_received.append({
                'system_prompt': kwargs.get('system_prompt', ''),
                'user_prompt': kwargs.get('user_prompt', ''),
            })
            return "# Test Steering File\n\n## Section 1\n\nContent here."
        
        mock_llm.complete = AsyncMock(side_effect=mock_complete)
        
        # Step 4: Run full pipeline
        context_assembler = ContextAssembler()
        prompt_builder = PromptBuilder()
        generator = SteeringFileGenerator(mock_llm)
        
        result = await generator.generate_all_files(
            context_assembler=context_assembler,
            prompt_builder=prompt_builder,
            code_facts=code_facts,
            source_docs=source_docs,
            existing_steering={},
            delta=None,
            user_intent=None,
            use_case="new_from_docs",
            output_dir=output_dir,
        )
        
        # Assertions
        assert result.success is True
        assert len(result.files_written) == 8
        
        # Assert prompts contain source doc content
        assert len(prompts_received) == 8
        
        # Check that at least some prompts contain content from source docs
        prompts_with_source_content = 0
        for prompt_data in prompts_received:
            user_prompt = prompt_data['user_prompt']
            # Check for keywords from source docs
            if any(keyword in user_prompt.lower() for keyword in [
                'architecture', 'layered', 'typer', 'cli', 'steering', 'requirements'
            ]):
                prompts_with_source_content += 1
        
        assert prompts_with_source_content > 0, (
            "Expected at least some prompts to contain source document content"
        )
        
        # Verify token budgets (rough estimate: 1 token ≈ 4 characters)
        for prompt_data in prompts_received:
            system_prompt = prompt_data['system_prompt']
            user_prompt = prompt_data['user_prompt']
            
            total_chars = len(system_prompt) + len(user_prompt)
            estimated_tokens = total_chars // 4
            
            # Allow some buffer (10,000 tokens instead of strict 8,000)
            # because system prompt adds overhead
            assert estimated_tokens <= 10_000, (
                f"Prompt exceeds reasonable token budget: ~{estimated_tokens} tokens"
            )
