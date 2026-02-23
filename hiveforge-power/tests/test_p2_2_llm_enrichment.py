"""
Tests for CodeAnalyzer.classify_project_with_llm() method (P2-2).

This module tests the LLM-based project classification enrichment that adds
one_line_description and key_capabilities to heuristic classification.
"""

import json
from pathlib import Path
from textwrap import dedent
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
from hiveforge.steering.llm.provider import LLMProvider


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
def temp_mcp_project(tmp_path):
    """Create a temporary MCP server project."""
    project_root = tmp_path / "mcp_project"
    project_root.mkdir()
    
    # Create MCP server file
    (project_root / "server.py").write_text(dedent('''
        from mcp import mcp
        
        @mcp.tool()
        def get_data(query: str):
            """Retrieve data based on query."""
            return {}
    '''))
    
    # Create pyproject.toml
    (project_root / "pyproject.toml").write_text(dedent('''
        [project]
        name = "test-mcp-server"
        version = "0.1.0"
        dependencies = ["fastmcp>=0.1.0"]
    '''))
    
    return project_root


class TestClassifyProjectWithLLM:
    """Test classify_project_with_llm() orchestration method."""
    
    @pytest.mark.asyncio
    async def test_calls_heuristic_classify_first(self, temp_mcp_project, mock_llm_provider_unavailable):
        """Test that heuristic classification is called first."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        result = await analyzer.classify_project_with_llm(mock_llm_provider_unavailable)
        
        # Should return base classification when LLM unavailable
        assert isinstance(result, dict)
        assert 'project_type' in result
        assert 'has_frontend' in result
        assert 'has_database' in result
        assert 'has_rest_api' in result
        assert 'primary_language' in result
        assert 'one_line_description' in result
        assert 'key_capabilities' in result
        
        # Should have [INFERRED] markers for LLM-enriched fields
        assert '[INFERRED' in result['one_line_description']
        assert all('[INFERRED' in cap for cap in result['key_capabilities'])
    
    @pytest.mark.asyncio
    async def test_returns_base_classification_when_llm_unavailable(
        self, temp_mcp_project, mock_llm_provider_unavailable
    ):
        """Test fallback to base classification when LLM unavailable."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        result = await analyzer.classify_project_with_llm(mock_llm_provider_unavailable)
        
        # Should return heuristic classification
        assert result['project_type'] == 'mcp_server'
        assert result['has_frontend'] is False
        assert '[INFERRED' in result['one_line_description']
    
    @pytest.mark.asyncio
    async def test_enriches_with_llm_when_available(self, temp_mcp_project, mock_llm_provider_available):
        """Test LLM enrichment when provider is available."""
        # Mock LLM response
        llm_response = json.dumps({
            "project_type": "mcp_server",
            "has_frontend": False,
            "has_database": False,
            "has_rest_api": False,
            "primary_language": "Python",
            "one_line_description": "An MCP server for data retrieval operations",
            "key_capabilities": [
                "Query-based data retrieval",
                "MCP tool integration",
                "Async operation support"
            ]
        })
        
        mock_llm_provider_available.complete = AsyncMock(return_value=llm_response)
        
        analyzer = CodeAnalyzer(temp_mcp_project)
        result = await analyzer.classify_project_with_llm(mock_llm_provider_available)
        
        # Should have LLM-enriched fields
        assert result['one_line_description'] == "An MCP server for data retrieval operations"
        assert len(result['key_capabilities']) == 3
        assert "Query-based data retrieval" in result['key_capabilities']
        assert '[INFERRED' not in result['one_line_description']
    
    @pytest.mark.asyncio
    async def test_uses_temperature_0_1(self, temp_mcp_project, mock_llm_provider_available):
        """Test that temperature 0.1 is used for consistent results."""
        mock_llm_provider_available.complete = AsyncMock(return_value='{"project_type": "mcp_server"}')
        
        analyzer = CodeAnalyzer(temp_mcp_project)
        await analyzer.classify_project_with_llm(mock_llm_provider_available)
        
        # Verify complete() was called with temperature=0.1
        mock_llm_provider_available.complete.assert_called_once()
        call_kwargs = mock_llm_provider_available.complete.call_args.kwargs
        assert call_kwargs['temperature'] == 0.1
    
    @pytest.mark.asyncio
    async def test_requests_json_mode(self, temp_mcp_project, mock_llm_provider_available):
        """Test that json_mode=True is requested."""
        mock_llm_provider_available.complete = AsyncMock(return_value='{"project_type": "mcp_server"}')
        
        analyzer = CodeAnalyzer(temp_mcp_project)
        await analyzer.classify_project_with_llm(mock_llm_provider_available)
        
        # Verify json_mode=True
        call_kwargs = mock_llm_provider_available.complete.call_args.kwargs
        assert call_kwargs['json_mode'] is True
    
    @pytest.mark.asyncio
    async def test_falls_back_on_llm_exception(self, temp_mcp_project, mock_llm_provider_available):
        """Test fallback to base classification when LLM raises exception."""
        mock_llm_provider_available.complete = AsyncMock(side_effect=Exception("LLM error"))
        
        analyzer = CodeAnalyzer(temp_mcp_project)
        result = await analyzer.classify_project_with_llm(mock_llm_provider_available)
        
        # Should return base classification with [INFERRED] markers
        assert '[INFERRED' in result['one_line_description']
        assert all('[INFERRED' in cap for cap in result['key_capabilities'])
    
    @pytest.mark.asyncio
    async def test_falls_back_on_none_response(self, temp_mcp_project, mock_llm_provider_available):
        """Test fallback when LLM returns None."""
        mock_llm_provider_available.complete = AsyncMock(return_value=None)
        
        analyzer = CodeAnalyzer(temp_mcp_project)
        result = await analyzer.classify_project_with_llm(mock_llm_provider_available)
        
        # Should return base classification
        assert '[INFERRED' in result['one_line_description']


class TestBuildClassificationPrompt:
    """Test _build_classification_prompt() method."""
    
    def test_includes_base_classification(self, temp_mcp_project):
        """Test that prompt includes base classification."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        base_classification = {
            'project_type': 'mcp_server',
            'has_frontend': False,
            'has_database': False,
            'has_rest_api': False,
            'primary_language': 'Python',
            'one_line_description': '[INFERRED]',
            'key_capabilities': ['[INFERRED]']
        }
        
        prompt = analyzer._build_classification_prompt(base_classification)
        
        assert 'mcp_server' in prompt
        assert 'Python' in prompt
        assert 'Has Frontend: False' in prompt
        assert 'Has Database: False' in prompt
    
    def test_includes_code_summary(self, temp_mcp_project):
        """Test that prompt includes code summary."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        base_classification = {
            'project_type': 'mcp_server',
            'has_frontend': False,
            'has_database': False,
            'has_rest_api': False,
            'primary_language': 'Python',
            'one_line_description': '[INFERRED]',
            'key_capabilities': ['[INFERRED]']
        }
        
        prompt = analyzer._build_classification_prompt(base_classification)
        
        # Should include code summary section
        assert 'Code Summary:' in prompt
        assert 'Languages:' in prompt
    
    def test_requests_json_format(self, temp_mcp_project):
        """Test that prompt requests JSON response."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        base_classification = {
            'project_type': 'library',
            'has_frontend': False,
            'has_database': False,
            'has_rest_api': False,
            'primary_language': 'Python',
            'one_line_description': '[INFERRED]',
            'key_capabilities': ['[INFERRED]']
        }
        
        prompt = analyzer._build_classification_prompt(base_classification)
        
        # Should request JSON with specific keys
        assert 'one_line_description' in prompt
        assert 'key_capabilities' in prompt
        assert '{' in prompt and '}' in prompt


class TestParseClassificationResponse:
    """Test _parse_classification_response() method."""
    
    def test_parses_valid_json(self, temp_mcp_project):
        """Test parsing of valid JSON response."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        response = json.dumps({
            "project_type": "mcp_server",
            "has_frontend": False,
            "has_database": False,
            "has_rest_api": False,
            "primary_language": "Python",
            "one_line_description": "A data retrieval MCP server",
            "key_capabilities": ["Data queries", "MCP integration", "Async support"]
        })
        
        result = analyzer._parse_classification_response(response)
        
        assert result['one_line_description'] == "A data retrieval MCP server"
        assert len(result['key_capabilities']) == 3
        assert "Data queries" in result['key_capabilities']
    
    def test_extracts_json_from_markdown(self, temp_mcp_project):
        """Test extraction of JSON from markdown code blocks."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        response = '''
Here is the classification:

```json
{
    "project_type": "cli_tool",
    "has_frontend": false,
    "has_database": false,
    "has_rest_api": false,
    "primary_language": "Python",
    "one_line_description": "A CLI tool for project management",
    "key_capabilities": ["Project init", "Build automation", "Deployment"]
}
```
'''
        
        result = analyzer._parse_classification_response(response)
        
        assert result['one_line_description'] == "A CLI tool for project management"
        assert len(result['key_capabilities']) == 3
    
    def test_falls_back_on_invalid_json(self, temp_mcp_project):
        """Test fallback when JSON is invalid."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        response = "This is not valid JSON"
        
        result = analyzer._parse_classification_response(response)
        
        # Should return base classification with [INFERRED] markers
        assert '[INFERRED' in result['one_line_description']
    
    def test_falls_back_on_missing_keys(self, temp_mcp_project):
        """Test fallback when required keys are missing."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        # Missing one_line_description and key_capabilities
        response = json.dumps({
            "project_type": "library",
            "has_frontend": False
        })
        
        result = analyzer._parse_classification_response(response)
        
        # Should return base classification
        assert '[INFERRED' in result['one_line_description']
    
    def test_validates_all_required_keys(self, temp_mcp_project):
        """Test that all required keys are validated."""
        analyzer = CodeAnalyzer(temp_mcp_project)
        
        # Complete response with all keys
        response = json.dumps({
            "project_type": "web_app",
            "has_frontend": True,
            "has_database": True,
            "has_rest_api": True,
            "primary_language": "TypeScript",
            "one_line_description": "A web application for task management",
            "key_capabilities": ["Task tracking", "User auth", "Real-time updates"]
        })
        
        result = analyzer._parse_classification_response(response)
        
        # Should parse successfully
        assert result['project_type'] == "web_app"
        assert result['one_line_description'] == "A web application for task management"
        assert len(result['key_capabilities']) == 3


class TestIntegration:
    """Integration tests for LLM enrichment."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_enrichment(self, temp_mcp_project):
        """Test complete enrichment flow."""
        # Create mock LLM provider
        provider = MagicMock(spec=LLMProvider)
        provider.is_available.return_value = True
        
        llm_response = json.dumps({
            "project_type": "mcp_server",
            "has_frontend": False,
            "has_database": False,
            "has_rest_api": False,
            "primary_language": "Python",
            "one_line_description": "MCP server providing data retrieval capabilities",
            "key_capabilities": [
                "Query-based data access",
                "FastMCP integration",
                "Async operation support"
            ]
        })
        
        provider.complete = AsyncMock(return_value=llm_response)
        
        analyzer = CodeAnalyzer(temp_mcp_project)
        result = await analyzer.classify_project_with_llm(provider)
        
        # Verify complete enrichment
        assert result['project_type'] == 'mcp_server'
        assert result['one_line_description'] == "MCP server providing data retrieval capabilities"
        assert len(result['key_capabilities']) == 3
        assert all('[INFERRED' not in cap for cap in result['key_capabilities'])
        
        # Verify LLM was called with correct parameters
        provider.complete.assert_called_once()
        call_kwargs = provider.complete.call_args.kwargs
        assert call_kwargs['temperature'] == 0.1
        assert call_kwargs['json_mode'] is True
        assert 'system_prompt' in call_kwargs
        assert 'user_prompt' in call_kwargs
