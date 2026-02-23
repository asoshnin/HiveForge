"""
Unit tests for SteeringAssistant.generate_file() method (P0-2).

This module tests the LLM-based steering file generation with automatic
fallback to [INFERRED] markers when LLM is unavailable.
"""

import re
from pathlib import Path
from textwrap import dedent
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hiveforge.steering.agents.steering_assistant import SteeringAssistant
from hiveforge.steering.knowledge_base import KnowledgeBase
from hiveforge.steering.models import GapAnalysisResult
from hiveforge.steering.llm.provider import LLMProvider


@pytest.fixture
def mock_knowledge_base():
    """Create a mock knowledge base."""
    kb = MagicMock(spec=KnowledgeBase)
    kb.get_relevant_content.return_value = "Mock context"
    kb.extract_section.return_value = None
    return kb


@pytest.fixture
def mock_gap_analysis():
    """Create a mock gap analysis result."""
    gap = MagicMock(spec=GapAnalysisResult)
    gap.questions = []
    gap.complete_sections = {}
    gap.ambiguous_sections = {}
    gap.missing_sections = {}
    return gap


@pytest.fixture
def mock_llm_provider_available():
    """Create a mock LLM provider that is available."""
    provider = MagicMock(spec=LLMProvider)
    provider.is_available.return_value = True
    return provider


@pytest.fixture
def mock_llm_provider_unavailable():
    """Create a mock LLM provider that is unavailable."""
    provider = MagicMock(spec=LLMProvider)
    provider.is_available.return_value = False
    return provider


@pytest.fixture
def temp_project_with_templates(tmp_path):
    """Create a temporary project with template files."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    # Create templates directory
    templates_dir = project_root / "hiveforge" / "templates" / "steering"
    templates_dir.mkdir(parents=True)
    
    # Create tech-stack.md template with frontmatter
    tech_stack_template = dedent('''
        ---
        title: Technology Stack
        category: technical
        ---
        
        # Technology Stack
        
        ## Core Technologies
        
        ### Backend
        - **Language:** {Python 3.11|Node.js 18|Go 1.21|...}
        - **Framework:** {FastAPI|Express|Gin|...}
        
        ### Database
        - **Primary:** {PostgreSQL 15|MongoDB 6|...}
        
        ## Key Dependencies
        {List key dependencies here}
        
        ## Rationale
        {Why this stack? Trade-offs considered?}
    ''').strip()
    
    (templates_dir / "tech-stack.md").write_text(tech_stack_template)
    
    # Create conventions.md template
    conventions_template = dedent('''
        ---
        title: Coding Conventions
        category: standards
        ---
        
        # Coding Conventions
        
        ## General Principles
        {List principles}
        
        ## Naming Conventions
        {Describe naming conventions}
    ''').strip()
    
    (templates_dir / "conventions.md").write_text(conventions_template)
    
    return project_root


class TestGenerateFile:
    """Test generate_file() orchestration method."""
    
    @pytest.mark.asyncio
    async def test_returns_populated_markdown_on_llm_success(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test that generate_file() returns populated markdown when LLM succeeds."""
        # Mock LLM response
        llm_response = dedent('''
            # Technology Stack
            
            ## Core Technologies
            
            ### Backend
            - **Language:** Python 3.11
            - **Framework:** FastAPI
            
            ### Database
            - **Primary:** PostgreSQL 15
            
            ## Key Dependencies
            - fastapi==0.104.0
            - sqlalchemy==2.0.0
            
            ## Rationale
            FastAPI provides excellent async support and automatic API documentation.
        ''').strip()
        
        mock_llm_provider_available.complete = AsyncMock(return_value=llm_response)
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        result = await assistant.generate_file(
            filename="tech-stack.md",
            context={"languages": ["Python"], "dependencies": ["fastapi"]}
        )
        
        # Should return populated markdown
        assert "Python 3.11" in result
        assert "FastAPI" in result
        assert "PostgreSQL 15" in result
        assert "{" not in result  # No placeholders
        assert "[INFERRED" not in result
    
    @pytest.mark.asyncio
    async def test_applies_inferred_markers_on_llm_failure(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_unavailable
    ):
        """Test that generate_file() applies [INFERRED] markers when LLM unavailable."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_unavailable
        )
        
        result = await assistant.generate_file(
            filename="tech-stack.md",
            context={}
        )
        
        # Should have [INFERRED] markers
        assert "[INFERRED:" in result
        assert "{" not in result  # Placeholders replaced
        assert "Python 3.11|Node.js 18|Go 1.21|..." in result or "[INFERRED:" in result
    
    @pytest.mark.asyncio
    async def test_strips_frontmatter_before_llm_call(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test that frontmatter is stripped before sending to LLM."""
        llm_response = "# Technology Stack\n\nContent here"
        mock_llm_provider_available.complete = AsyncMock(return_value=llm_response)
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        result = await assistant.generate_file(
            filename="tech-stack.md",
            context={}
        )
        
        # Verify LLM was called
        mock_llm_provider_available.complete.assert_called_once()
        call_kwargs = mock_llm_provider_available.complete.call_args.kwargs
        user_prompt = call_kwargs['user_prompt']
        
        # Frontmatter should not be in prompt
        assert "---" not in user_prompt or user_prompt.count("---") < 2
        assert "title: Technology Stack" not in user_prompt
        assert "category: technical" not in user_prompt
    
    @pytest.mark.asyncio
    async def test_tracks_generated_files_for_context(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test that generated files are tracked for context."""
        llm_response = "# Content"
        mock_llm_provider_available.complete = AsyncMock(return_value=llm_response)
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        # Initially empty
        assert len(assistant.generated_files) == 0
        
        # Generate first file
        await assistant.generate_file(filename="tech-stack.md", context={})
        assert len(assistant.generated_files) == 1
        
        # Generate second file
        await assistant.generate_file(filename="conventions.md", context={})
        assert len(assistant.generated_files) == 2
    
    @pytest.mark.asyncio
    async def test_limits_context_to_last_3_files(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test that context is limited to last 3 generated files."""
        llm_response = "# Content " + ("x" * 1000)  # Long content
        mock_llm_provider_available.complete = AsyncMock(return_value=llm_response)
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        # Generate 4 files
        for i in range(4):
            await assistant.generate_file(filename="tech-stack.md", context={})
        
        # Should only keep last 3
        assert len(assistant.generated_files) == 3
    
    @pytest.mark.asyncio
    async def test_async_method_execution(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test that generate_file() is properly async."""
        llm_response = "# Content"
        mock_llm_provider_available.complete = AsyncMock(return_value=llm_response)
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        # Should be awaitable
        result = await assistant.generate_file(filename="tech-stack.md", context={})
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetRawTemplate:
    """Test _get_raw_template() method."""
    
    def test_loads_template_with_frontmatter(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test that template is loaded with frontmatter intact."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        template = assistant._get_raw_template("tech-stack.md")
        
        # Should include frontmatter
        assert template.startswith("---")
        assert "title: Technology Stack" in template
        assert "category: technical" in template
    
    def test_raises_filenotfounderror_for_missing_template(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test that FileNotFoundError is raised for missing template."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        with pytest.raises(FileNotFoundError, match="Template nonexistent.md not found"):
            assistant._get_raw_template("nonexistent.md")
    
    def test_raises_valueerror_for_empty_template_name(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test that ValueError is raised for empty template name."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        with pytest.raises(ValueError, match="template_name cannot be empty"):
            assistant._get_raw_template("")


class TestStripFrontmatter:
    """Test _strip_frontmatter() method."""
    
    def test_removes_yaml_frontmatter(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test that YAML frontmatter is removed correctly."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        content_with_frontmatter = dedent('''
            ---
            title: Test
            category: test
            ---
            
            # Content
            
            Body text
        ''').strip()
        
        result = assistant._strip_frontmatter(content_with_frontmatter)
        
        # Should not contain frontmatter
        assert "---" not in result or result.count("---") == 0
        assert "title: Test" not in result
        assert "category: test" not in result
        
        # Should contain content
        assert "# Content" in result
        assert "Body text" in result
    
    def test_returns_content_unchanged_without_frontmatter(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test that content without frontmatter is returned unchanged."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        content_without_frontmatter = "# Content\n\nBody text"
        
        result = assistant._strip_frontmatter(content_without_frontmatter)
        
        assert result == content_without_frontmatter
    
    def test_handles_malformed_frontmatter(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test handling of malformed frontmatter (missing closing ---)."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        malformed_content = dedent('''
            ---
            title: Test
            
            # Content
        ''').strip()
        
        result = assistant._strip_frontmatter(malformed_content)
        
        # Should return as-is when malformed
        assert result == malformed_content


class TestApplyInferredMarkers:
    """Test _apply_inferred_markers() method."""
    
    def test_replaces_placeholders_with_inferred_markers(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test that {placeholder} is replaced with [INFERRED: placeholder]."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        template = "Language: {Python|Node.js|Go}\nFramework: {FastAPI|Express}"
        
        result = assistant._apply_inferred_markers(template)
        
        # Should replace placeholders
        assert "{" not in result
        assert "}" not in result
        assert "[INFERRED: Python|Node.js|Go]" in result
        assert "[INFERRED: FastAPI|Express]" in result
    
    def test_handles_multiple_placeholders(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test handling of multiple placeholders."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        template = "{A} and {B} and {C}"
        
        result = assistant._apply_inferred_markers(template)
        
        assert result == "[INFERRED: A] and [INFERRED: B] and [INFERRED: C]"
    
    def test_preserves_non_placeholder_braces(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis
    ):
        """Test that non-placeholder braces are preserved."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates
        )
        
        # Empty braces should be replaced
        template = "Code: {} and Placeholder: {value}"
        
        result = assistant._apply_inferred_markers(template)
        
        # Both should be replaced
        assert "[INFERRED: ]" in result or "[INFERRED:" in result
        assert "[INFERRED: value]" in result


class TestContextTracking:
    """Test context tracking for generated files."""
    
    @pytest.mark.asyncio
    async def test_tracks_last_3_files_only(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test that only last 3 files are tracked."""
        llm_response = "# Content " + ("x" * 1000)
        mock_llm_provider_available.complete = AsyncMock(return_value=llm_response)
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        # Generate 5 files
        for i in range(5):
            await assistant.generate_file(filename="tech-stack.md", context={})
        
        # Should only keep last 3
        assert len(assistant.generated_files) == 3
    
    @pytest.mark.asyncio
    async def test_truncates_content_to_500_chars(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test that tracked content is truncated to 500 chars."""
        llm_response = "# Content " + ("x" * 1000)
        mock_llm_provider_available.complete = AsyncMock(return_value=llm_response)
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        await assistant.generate_file(filename="tech-stack.md", context={})
        
        # Should be truncated to 500 chars
        assert len(assistant.generated_files[0]) == 500


class TestErrorHandling:
    """Test error handling in generate_file()."""
    
    @pytest.mark.asyncio
    async def test_falls_back_on_llm_exception(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test fallback to [INFERRED] markers when LLM raises exception."""
        mock_llm_provider_available.complete = AsyncMock(side_effect=Exception("LLM error"))
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        result = await assistant.generate_file(filename="tech-stack.md", context={})
        
        # Should return fallback with [INFERRED] markers
        assert "[INFERRED:" in result
        assert "{" not in result
    
    @pytest.mark.asyncio
    async def test_never_returns_empty_content(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test that generate_file() never returns empty content."""
        # Mock LLM to return empty string
        mock_llm_provider_available.complete = AsyncMock(return_value="")
        
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        result = await assistant.generate_file(filename="tech-stack.md", context={})
        
        # Should return fallback content
        assert len(result) > 0
        assert "[INFERRED:" in result or "[GENERATION FAILED" in result
    
    @pytest.mark.asyncio
    async def test_handles_missing_template_gracefully(
        self, temp_project_with_templates, mock_knowledge_base, mock_gap_analysis, mock_llm_provider_available
    ):
        """Test graceful handling of missing template."""
        assistant = SteeringAssistant(
            knowledge_base=mock_knowledge_base,
            gap_analysis=mock_gap_analysis,
            project_root=temp_project_with_templates,
            llm_provider=mock_llm_provider_available
        )
        
        result = await assistant.generate_file(filename="nonexistent.md", context={})
        
        # Should return error message
        assert "[GENERATION FAILED" in result
        assert "nonexistent.md" in result
