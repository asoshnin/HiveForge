"""
Unit tests for P2-3: LLM-Based Gap Analysis Section Classification.

Tests cover the _classify_section_with_llm() method and its integration
with the existing gap analysis workflow.
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
from hiveforge.steering.gap_analysis import GapAnalysisEngine
from hiveforge.steering.knowledge_base import KnowledgeBase
from hiveforge.steering.models import ParsedDocument


class TestLLMClassificationIntegration:
    """Test LLM classification integration with gap analysis."""
    
    def test_llm_called_when_keyword_matching_returns_missing(self):
        """Test that LLM is called when keyword matching returns 'missing'."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        
        # Create a coroutine that returns the JSON
        async def mock_complete(*args, **kwargs):
            return json.dumps({
                "classification": "complete",
                "reason": "Context contains backend framework information"
            })
        
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call _classify_section with content that has no keywords
        classification = engine._classify_section(
            template_name="tech-stack",
            section_name="Backend",
            placeholder_pattern=r"\{.*?\}",
            required=True,
            content="We use a modern web framework for our API."
        )
        
        # Verify classification was returned from LLM
        assert classification == "complete"
    
    def test_llm_not_called_when_keyword_matching_succeeds(self):
        """Test that LLM is not called when keyword matching finds information."""
        # Setup with content that has keywords
        docs = [
            ParsedDocument(
                file_path=Path("tech.md"),
                content="Backend: FastAPI framework with Python"
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.complete = Mock()
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call _classify_section with content that has keywords
        classification = engine._classify_section(
            template_name="tech-stack",
            section_name="Backend",
            placeholder_pattern=r"\{.*?\}",
            required=True,
            content="Backend: FastAPI framework with Python"
        )
        
        # Verify LLM was NOT called (keyword matching succeeded)
        assert not mock_llm.complete.called
        # Classification should be "ambiguous" due to keyword match
        assert classification == "ambiguous"
    
    def test_llm_not_called_when_provider_unavailable(self):
        """Test that LLM is not called when provider is unavailable."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Mock LLM provider as unavailable
        mock_llm = Mock()
        mock_llm.is_available.return_value = False
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call _classify_section
        classification = engine._classify_section(
            template_name="tech-stack",
            section_name="Backend",
            placeholder_pattern=r"\{.*?\}",
            required=True,
            content="Some unrelated content"
        )
        
        # Verify classification falls back to "missing"
        assert classification == "missing"


class TestClassifySectionWithLLM:
    """Test the _classify_section_with_llm method directly."""
    
    def test_classify_section_with_llm_complete(self):
        """Test LLM classification returns 'complete'."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        
        # Create async mock
        async def mock_complete(*args, **kwargs):
            return json.dumps({
                "classification": "complete",
                "reason": "Context clearly describes the backend framework"
            })
        
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        classification = engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="We use FastAPI as our backend framework with Python 3.11"
        )
        
        # Verify
        assert classification == "complete"
    
    def test_classify_section_with_llm_partial_maps_to_ambiguous(self):
        """Test LLM classification 'partial' maps to 'ambiguous'."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(*args, **kwargs):
            return json.dumps({
                "classification": "partial",
                "reason": "Some backend info but missing framework details"
            })
        
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        classification = engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="We have a backend service"
        )
        
        # Verify mapping: partial -> ambiguous
        assert classification == "ambiguous"
    
    def test_classify_section_with_llm_missing(self):
        """Test LLM classification returns 'missing'."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(*args, **kwargs):
            return json.dumps({
                "classification": "missing",
                "reason": "No backend information in context"
            })
        
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        classification = engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="This is about frontend components"
        )
        
        # Verify
        assert classification == "missing"
    
    def test_classify_section_with_llm_truncates_long_content(self):
        """Test that content is truncated to max 800 chars."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Track the call arguments
        call_args_captured = {}
        
        async def mock_complete(*args, **kwargs):
            call_args_captured.update(kwargs)
            return json.dumps({
                "classification": "complete",
                "reason": "Found information"
            })
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Create long content (> 800 chars)
        long_content = "A" * 1000
        
        # Call method
        classification = engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content=long_content
        )
        
        # Verify content was truncated in prompt
        user_prompt = call_args_captured.get("user_prompt", "")
        # The prompt should contain truncated content (800 chars max)
        assert "A" * 800 in user_prompt
        assert "A" * 1000 not in user_prompt
    
    def test_classify_section_with_llm_handles_json_parse_error(self):
        """Test fallback when LLM returns invalid JSON."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Mock LLM provider returning invalid JSON
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(*args, **kwargs):
            return "This is not JSON"
        
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        classification = engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Some content"
        )
        
        # Verify fallback to None (will use keyword matching)
        assert classification is None
    
    def test_classify_section_with_llm_handles_llm_failure(self):
        """Test fallback when LLM call fails."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Mock LLM provider that raises exception
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(*args, **kwargs):
            raise Exception("LLM API error")
        
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        classification = engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Some content"
        )
        
        # Verify fallback to None
        assert classification is None
    
    def test_classify_section_with_llm_handles_none_response(self):
        """Test fallback when LLM returns None."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Mock LLM provider returning None
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        
        async def mock_complete(*args, **kwargs):
            return None
        
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        classification = engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Some content"
        )
        
        # Verify fallback to None
        assert classification is None


class TestLLMPromptConstruction:
    """Test that LLM prompts are constructed correctly."""
    
    def test_system_prompt_includes_json_instruction(self):
        """Test that system prompt requests JSON response."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Track call arguments
        call_args_captured = {}
        
        async def mock_complete(*args, **kwargs):
            call_args_captured.update(kwargs)
            return json.dumps({
                "classification": "complete",
                "reason": "Test"
            })
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Test content"
        )
        
        # Verify system prompt
        system_prompt = call_args_captured.get("system_prompt", "")
        assert "JSON" in system_prompt
        assert "documentation" in system_prompt.lower()
    
    def test_user_prompt_includes_template_and_section(self):
        """Test that user prompt includes template name and section name."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Track call arguments
        call_args_captured = {}
        
        async def mock_complete(*args, **kwargs):
            call_args_captured.update(kwargs)
            return json.dumps({
                "classification": "complete",
                "reason": "Test"
            })
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Test content"
        )
        
        # Verify user prompt
        user_prompt = call_args_captured.get("user_prompt", "")
        assert "tech-stack" in user_prompt
        assert "Backend" in user_prompt
        assert "Test content" in user_prompt
    
    def test_user_prompt_includes_classification_options(self):
        """Test that user prompt explains classification options."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Track call arguments
        call_args_captured = {}
        
        async def mock_complete(*args, **kwargs):
            call_args_captured.update(kwargs)
            return json.dumps({
                "classification": "complete",
                "reason": "Test"
            })
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Test content"
        )
        
        # Verify user prompt includes classification options
        user_prompt = call_args_captured.get("user_prompt", "")
        assert "complete" in user_prompt
        assert "partial" in user_prompt
        assert "missing" in user_prompt


class TestTemperatureAndParameters:
    """Test that LLM is called with correct parameters."""
    
    def test_temperature_is_0_1(self):
        """Test that temperature is set to 0.1 for consistent results."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Track call arguments
        call_args_captured = {}
        
        async def mock_complete(*args, **kwargs):
            call_args_captured.update(kwargs)
            return json.dumps({
                "classification": "complete",
                "reason": "Test"
            })
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Test content"
        )
        
        # Verify temperature
        assert call_args_captured.get("temperature") == 0.1
    
    def test_json_mode_enabled(self):
        """Test that json_mode is enabled."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Track call arguments
        call_args_captured = {}
        
        async def mock_complete(*args, **kwargs):
            call_args_captured.update(kwargs)
            return json.dumps({
                "classification": "complete",
                "reason": "Test"
            })
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Test content"
        )
        
        # Verify json_mode
        assert call_args_captured.get("json_mode") is True
    
    def test_max_tokens_set(self):
        """Test that max_tokens is set appropriately."""
        # Setup
        kb = KnowledgeBase(documents=[])
        
        # Track call arguments
        call_args_captured = {}
        
        async def mock_complete(*args, **kwargs):
            call_args_captured.update(kwargs)
            return json.dumps({
                "classification": "complete",
                "reason": "Test"
            })
        
        # Mock LLM provider
        mock_llm = Mock()
        mock_llm.is_available.return_value = True
        mock_llm.complete = mock_complete
        
        engine = GapAnalysisEngine(knowledge_base=kb, llm_provider=mock_llm)
        
        # Call method
        engine._classify_section_with_llm(
            template_name="tech-stack",
            section_name="Backend",
            content="Test content"
        )
        
        # Verify max_tokens
        assert call_args_captured.get("max_tokens") == 200
