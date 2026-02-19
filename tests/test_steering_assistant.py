"""
Unit tests for SteeringAssistant class.

Tests the conversation orchestration, question batching, token-efficient prompting,
response caching, and web research functionality.

Requirements: 7.1-7.8, 12.1-12.5
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from src.hiveforge.steering.agents.steering_assistant import (
    SteeringAssistant,
    QuestionBatch,
    ResearchResult,
)
from src.hiveforge.steering.knowledge_base import KnowledgeBase
from src.hiveforge.steering.models import (
    GapAnalysisResult,
    Question,
    ParsedDocument,
    CodeAnalysisResult,
)
from src.hiveforge.steering.response_cache import ResponseCache


@pytest.fixture
def sample_documents():
    """Create sample parsed documents for testing."""
    return [
        ParsedDocument(
            file_path=Path("project-spec.md"),
            content="# Project Spec\n\nThis is a web application for task management.",
            metadata={}
        ),
        ParsedDocument(
            file_path=Path("tech-notes.md"),
            content="# Tech Notes\n\nUsing Python FastAPI for backend.",
            metadata={}
        ),
    ]


@pytest.fixture
def sample_knowledge_base(sample_documents):
    """Create a sample knowledge base."""
    return KnowledgeBase(documents=sample_documents)


@pytest.fixture
def sample_gap_analysis():
    """Create a sample gap analysis result."""
    return GapAnalysisResult(
        complete_sections={
            "tech-stack": ["Backend"],
        },
        missing_sections={
            "project-vision": ["Elevator Pitch", "Problem Statement"],
            "tech-stack": ["Database", "Rationale"],
        },
        ambiguous_sections={
            "architecture": ["Component Responsibilities"],
        },
        questions=[
            Question(
                template_name="project-vision",
                section_name="Elevator Pitch",
                question_text="What is the one-sentence description of your project?",
                context="For project-vision.md",
                priority=1
            ),
            Question(
                template_name="project-vision",
                section_name="Problem Statement",
                question_text="What problem does this solve?",
                context="For project-vision.md",
                priority=1
            ),
            Question(
                template_name="tech-stack",
                section_name="Database",
                question_text="What database are you using?",
                context="For tech-stack.md",
                priority=1
            ),
        ]
    )


@pytest.fixture
def mock_response_cache(tmp_path):
    """Create a mock response cache."""
    cache_dir = tmp_path / "cache"
    return ResponseCache(cache_dir=cache_dir)


class TestSteeringAssistantInit:
    """Test SteeringAssistant initialization."""
    
    def test_init_with_defaults(self, sample_knowledge_base, sample_gap_analysis):
        """Test initialization with default parameters."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis
        )
        
        assert assistant.knowledge_base == sample_knowledge_base
        assert assistant.gap_analysis == sample_gap_analysis
        assert assistant.research_enabled is False
        assert assistant.interactive is True
        assert assistant.response_cache is not None
        assert assistant.gathered_info == {}
        assert assistant.research_results == []
    
    def test_init_with_custom_params(
        self,
        sample_knowledge_base,
        sample_gap_analysis,
        mock_response_cache
    ):
        """Test initialization with custom parameters."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            research_enabled=True,
            interactive=False,
            response_cache=mock_response_cache
        )
        
        assert assistant.research_enabled is True
        assert assistant.interactive is False
        assert assistant.response_cache == mock_response_cache


class TestQuestionBatching:
    """Test question batching functionality (Requirement 7.2)."""
    
    def test_batch_questions_single_template(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test batching questions from a single template."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis
        )
        
        questions = [
            Question("tech-stack", "Backend", "Q1", "C1", 1),
            Question("tech-stack", "Database", "Q2", "C2", 1),
            Question("tech-stack", "Cache", "Q3", "C3", 1),
        ]
        
        batches = assistant.batch_questions(questions, max_per_batch=8)
        
        assert len(batches) == 1
        assert batches[0].template_name == "tech-stack"
        assert len(batches[0].questions) == 3
        assert batches[0].batch_number == 1
    
    def test_batch_questions_multiple_templates(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test batching questions from multiple templates."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis
        )
        
        questions = [
            Question("project-vision", "Elevator Pitch", "Q1", "C1", 1),
            Question("project-vision", "Problem Statement", "Q2", "C2", 1),
            Question("tech-stack", "Backend", "Q3", "C3", 1),
            Question("tech-stack", "Database", "Q4", "C4", 1),
        ]
        
        batches = assistant.batch_questions(questions, max_per_batch=8)
        
        assert len(batches) == 2
        assert batches[0].template_name == "project-vision"
        assert len(batches[0].questions) == 2
        assert batches[1].template_name == "tech-stack"
        assert len(batches[1].questions) == 2
    
    def test_batch_questions_respects_max_limit(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that batching respects max_per_batch limit (Requirement 7.2)."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis
        )
        
        # Create 10 questions for same template
        questions = [
            Question("tech-stack", f"Section{i}", f"Q{i}", f"C{i}", 1)
            for i in range(10)
        ]
        
        batches = assistant.batch_questions(questions, max_per_batch=8)
        
        # Should split into 2 batches: 8 + 2
        assert len(batches) == 2
        assert len(batches[0].questions) == 8
        assert len(batches[1].questions) == 2
        assert batches[0].batch_number == 1
        assert batches[1].batch_number == 2
    
    def test_batch_questions_empty_list(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test batching with empty question list."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis
        )
        
        batches = assistant.batch_questions([], max_per_batch=8)
        
        assert len(batches) == 0


class TestNonInteractiveMode:
    """Test non-interactive mode functionality (Requirement 7.6)."""
    
    def test_non_interactive_mode_no_questions(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that non-interactive mode doesn't ask questions."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=False
        )
        
        with patch('builtins.input') as mock_input:
            result = assistant.conduct_conversation()
            
            # Should not call input() in non-interactive mode
            mock_input.assert_not_called()
            
            # Should return gathered info from knowledge base
            assert isinstance(result, dict)
    
    def test_non_interactive_uses_knowledge_base(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that non-interactive mode uses only parsed artifacts."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=False
        )
        
        result = assistant.conduct_conversation()
        
        # Should extract from complete sections
        assert "tech-stack" in result
        assert isinstance(result["tech-stack"], dict)


class TestResponseCaching:
    """Test response caching functionality (Requirement 7.8)."""
    
    def test_caches_responses(
        self,
        sample_knowledge_base,
        sample_gap_analysis,
        mock_response_cache
    ):
        """Test that responses are cached."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            response_cache=mock_response_cache
        )
        
        question = Question(
            "tech-stack",
            "Database",
            "What database?",
            "Context",
            1
        )
        
        # Mock user input
        with patch('builtins.input', return_value="PostgreSQL"):
            with patch('builtins.print'):
                assistant._ask_question(question, 1, 1, "context")
        
        # Check that response was cached
        cached = mock_response_cache.get("What database?")
        assert cached == "PostgreSQL"
    
    def test_uses_cached_responses(
        self,
        sample_knowledge_base,
        sample_gap_analysis,
        mock_response_cache
    ):
        """Test that cached responses are reused."""
        # Pre-populate cache
        mock_response_cache.set("What database?", "PostgreSQL")
        
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            response_cache=mock_response_cache
        )
        
        question = Question(
            "tech-stack",
            "Database",
            "What database?",
            "Context",
            1
        )
        
        # Should not ask for input, should use cache
        with patch('builtins.input') as mock_input:
            with patch('builtins.print'):
                assistant._ask_question(question, 1, 1, "context")
            
            # Input should not be called since we have cached response
            mock_input.assert_not_called()
        
        # Check that answer was stored
        assert assistant.gathered_info["tech-stack"]["Database"] == "PostgreSQL"


class TestTokenLimiting:
    """Test token-efficient prompting (Requirements 7.7)."""
    
    def test_limits_knowledge_base_content(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that knowledge base content is limited to 4000 tokens."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis
        )
        
        # Mock get_relevant_content to track calls
        with patch.object(
            sample_knowledge_base,
            'get_relevant_content',
            wraps=sample_knowledge_base.get_relevant_content
        ) as mock_get:
            batch = QuestionBatch(
                questions=[Question("tech-stack", "Backend", "Q", "C", 1)],
                template_name="tech-stack",
                batch_number=1
            )
            
            with patch('builtins.input', return_value="FastAPI"):
                with patch('builtins.print'):
                    assistant._process_batch(batch)
            
            # Verify get_relevant_content was called with max_tokens=4000
            mock_get.assert_called_with("tech-stack", max_tokens=4000)


class TestResponseValidation:
    """Test response validation (Requirement 7.4)."""
    
    def test_validate_response_valid(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test validation of valid responses."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis
        )
        
        question = Question("tech-stack", "Database", "Q", "C", 1)
        
        assert assistant._validate_response("PostgreSQL 15", question) is True
        assert assistant._validate_response("We use MongoDB for flexibility", question) is True
    
    def test_validate_response_invalid(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test validation rejects invalid responses."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis
        )
        
        question = Question("tech-stack", "Database", "Q", "C", 1)
        
        # Too short
        assert assistant._validate_response("", question) is False
        assert assistant._validate_response("ab", question) is False
        
        # Placeholder responses
        assert assistant._validate_response("TODO", question) is False
        assert assistant._validate_response("TBD", question) is False
        assert assistant._validate_response("N/A", question) is False
        assert assistant._validate_response("idk", question) is False
        assert assistant._validate_response("don't know", question) is False


class TestWebResearch:
    """Test web research functionality (Requirements 12.1-12.5)."""
    
    def test_research_disabled_by_default(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that research is disabled by default (Requirement 12.4)."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            research_enabled=False
        )
        
        with patch.object(assistant, '_perform_research') as mock_research:
            with patch('builtins.input', return_value="answer"):
                with patch('builtins.print'):
                    assistant.conduct_conversation()
            
            # Research should not be called
            mock_research.assert_not_called()
    
    def test_research_enabled_when_flag_set(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that research is performed when enabled (Requirement 12.1)."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            research_enabled=True,
            interactive=True
        )
        
        with patch.object(assistant, '_perform_research') as mock_research:
            with patch('builtins.input', return_value="answer"):
                with patch('builtins.print'):
                    assistant.conduct_conversation()
            
            # Research should be called
            mock_research.assert_called_once()
    
    def test_research_topic_presents_findings(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that research findings are presented for approval (Requirement 12.3)."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            research_enabled=True
        )
        
        with patch('builtins.input', return_value='y'):
            with patch('builtins.print') as mock_print:
                result = assistant.research_topic("API error handling")
                
                # Should print findings
                assert any('Research findings' in str(call) for call in mock_print.call_args_list)
                
                # Should return result
                assert isinstance(result, ResearchResult)
                assert result.topic == "API error handling"
                assert result.approved is True
    
    def test_research_topic_user_rejection(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that research can be rejected by user."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            research_enabled=True
        )
        
        with patch('builtins.input', return_value='n'):
            with patch('builtins.print'):
                result = assistant.research_topic("API error handling")
                
                assert result.approved is False
    
    def test_identify_critical_gaps(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test identification of critical gaps for research (Requirement 12.1)."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            research_enabled=True
        )
        
        critical_gaps = assistant._identify_critical_gaps()
        
        # Should identify gaps in critical sections
        assert isinstance(critical_gaps, list)
        
        # Each gap should have template, section, and topic
        for gap in critical_gaps:
            assert 'template' in gap
            assert 'section' in gap
            assert 'topic' in gap


class TestConversationFlow:
    """Test overall conversation flow (Requirement 7.1, 7.3, 7.5)."""
    
    def test_presents_extracted_info(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that extracted information is presented (Requirement 7.1)."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=True
        )
        
        with patch('builtins.print') as mock_print:
            assistant._present_extracted_info()
            
            # Should print extracted information
            print_output = ' '.join(str(call) for call in mock_print.call_args_list)
            assert 'EXTRACTED INFORMATION' in print_output
            assert 'tech-stack' in print_output
    
    def test_provides_question_context(
        self,
        sample_knowledge_base,
        sample_gap_analysis,
        tmp_path
    ):
        """Test that questions include context (Requirement 7.3)."""
        # Use fresh cache to avoid cached responses
        cache_dir = tmp_path / "test_cache"
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            response_cache=ResponseCache(cache_dir=cache_dir)
        )
        
        question = Question(
            "tech-stack",
            "Database",
            "What database?",
            "For tech-stack.md - Database section",
            1
        )
        
        with patch('builtins.input', return_value="PostgreSQL"):
            with patch('builtins.print') as mock_print:
                assistant._ask_question(question, 1, 1, "context")
                
                # Should print context
                print_output = ' '.join(str(call) for call in mock_print.call_args_list)
                assert 'Context:' in print_output
                assert 'tech-stack.md' in print_output
    
    def test_full_conversation_flow(
        self,
        sample_knowledge_base,
        sample_gap_analysis,
        mock_response_cache
    ):
        """Test complete conversation flow."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=True,
            response_cache=mock_response_cache
        )
        
        # Mock user inputs for all questions
        answers = ["A task management app", "People forget tasks", "PostgreSQL"]
        
        with patch('builtins.input', side_effect=answers):
            with patch('builtins.print'):
                result = assistant.conduct_conversation()
        
        # Should have gathered all answers
        assert "project-vision" in result
        assert "tech-stack" in result
        assert result["project-vision"]["Elevator Pitch"] == "A task management app"
        assert result["project-vision"]["Problem Statement"] == "People forget tasks"
        assert result["tech-stack"]["Database"] == "PostgreSQL"


class TestQuestionBatchClass:
    """Test QuestionBatch class."""
    
    def test_question_batch_init(self):
        """Test QuestionBatch initialization."""
        questions = [
            Question("tech-stack", "Backend", "Q1", "C1", 1),
            Question("tech-stack", "Database", "Q2", "C2", 1),
        ]
        
        batch = QuestionBatch(
            questions=questions,
            template_name="tech-stack",
            batch_number=1
        )
        
        assert batch.questions == questions
        assert batch.template_name == "tech-stack"
        assert batch.batch_number == 1


class TestResearchResultClass:
    """Test ResearchResult class."""
    
    def test_research_result_init(self):
        """Test ResearchResult initialization."""
        result = ResearchResult(
            topic="API standards",
            findings=["Finding 1", "Finding 2"],
            sources=["https://example.com"],
            approved=True
        )
        
        assert result.topic == "API standards"
        assert len(result.findings) == 2
        assert len(result.sources) == 1
        assert result.approved is True
    
    def test_research_result_default_approved(self):
        """Test ResearchResult default approved value."""
        result = ResearchResult(
            topic="API standards",
            findings=[],
            sources=[]
        )
        
        assert result.approved is False



class TestSourceTracking:
    """Test source tracking functionality (Requirement R3.2)."""
    
    def test_tracks_sources_in_result(
        self,
        sample_knowledge_base,
        sample_gap_analysis,
        mock_response_cache
    ):
        """Test that sources are tracked and returned in result."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=True,
            response_cache=mock_response_cache
        )
        
        # Mock user inputs for all questions
        answers = ["A task management app", "People forget tasks", "PostgreSQL"]
        
        with patch('builtins.input', side_effect=answers):
            with patch('builtins.print'):
                result = assistant.conduct_conversation()
        
        # Result should have template sections
        assert "project-vision" in result
        assert "tech-stack" in result
        
        # Each template should have _sources key
        assert "_sources" in result["project-vision"]
        assert "_sources" in result["tech-stack"]
        
        # Sources should have the three categories
        sources = result["project-vision"]["_sources"]
        assert "documents" in sources
        assert "code_analysis" in sources
        assert "inferred" in sources
        assert isinstance(sources["documents"], list)
        assert isinstance(sources["code_analysis"], list)
        assert isinstance(sources["inferred"], list)
    
    def test_marks_inferred_sections(
        self,
        sample_knowledge_base,
        sample_gap_analysis,
        mock_response_cache
    ):
        """Test that user-provided answers are marked as inferred."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=True,
            response_cache=mock_response_cache
        )
        
        # Mock user inputs
        answers = ["A task management app", "People forget tasks", "PostgreSQL"]
        
        with patch('builtins.input', side_effect=answers):
            with patch('builtins.print'):
                result = assistant.conduct_conversation()
        
        # Questions that were asked should be marked as inferred
        # (since they're in missing_sections, not complete_sections)
        sources = result["project-vision"]["_sources"]
        assert "Elevator Pitch" in sources["inferred"]
        assert "Problem Statement" in sources["inferred"]
    
    def test_marks_document_sections(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that sections from documents are marked correctly."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=False
        )
        
        result = assistant.conduct_conversation()
        
        # Complete sections should be marked as from documents or inferred
        # (depending on whether extract_section finds content)
        if "tech-stack" in result and "_sources" in result["tech-stack"]:
            sources = result["tech-stack"]["_sources"]
            # Backend is in complete_sections, so should be tracked
            # It may be in documents or inferred depending on extraction success
            assert "Backend" in sources["documents"] or "Backend" in sources["inferred"]
    
    def test_non_interactive_tracks_sources(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that non-interactive mode tracks sources."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=False
        )
        
        result = assistant.conduct_conversation()
        
        # Should have source tracking even in non-interactive mode
        if "tech-stack" in result:
            assert "_sources" in result["tech-stack"]
            sources = result["tech-stack"]["_sources"]
            assert "documents" in sources
            assert "code_analysis" in sources
            assert "inferred" in sources


class TestConfidenceIntegration:
    """Test confidence calculation integration (Requirement R3.2)."""
    
    def test_result_format_compatible_with_confidence_calculator(
        self,
        sample_knowledge_base,
        sample_gap_analysis,
        mock_response_cache
    ):
        """Test that result format is compatible with ConfidenceCalculator."""
        from src.hiveforge.steering.confidence import ConfidenceCalculator
        
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=True,
            response_cache=mock_response_cache
        )
        
        # Mock user inputs
        answers = ["A task management app", "People forget tasks", "PostgreSQL"]
        
        with patch('builtins.input', side_effect=answers):
            with patch('builtins.print'):
                result = assistant.conduct_conversation()
        
        # Test that ConfidenceCalculator can process the result
        calculator = ConfidenceCalculator()
        
        for template_name, template_data in result.items():
            if "_sources" in template_data:
                sources = template_data["_sources"]
                
                # Should be able to calculate confidence
                score = calculator.calculate_file_confidence(
                    file_name=f"{template_name}.md",
                    sources=sources,
                    content="test content"
                )
                
                assert score is not None
                assert 0.0 <= score.overall <= 1.0
                assert score.level in ["high", "medium", "low"]
    
    def test_autonomous_mode_with_tracking(
        self,
        sample_knowledge_base,
        sample_gap_analysis
    ):
        """Test that autonomous mode tracks sources correctly."""
        assistant = SteeringAssistant(
            knowledge_base=sample_knowledge_base,
            gap_analysis=sample_gap_analysis,
            interactive=False  # Autonomous/non-interactive
        )
        
        result = assistant.conduct_conversation()
        
        # Should have gathered info with source tracking
        assert isinstance(result, dict)
        
        # Check that at least one template has source tracking
        has_sources = False
        for template_data in result.values():
            if isinstance(template_data, dict) and "_sources" in template_data:
                has_sources = True
                break
        
        assert has_sources, "Result should include source tracking"
