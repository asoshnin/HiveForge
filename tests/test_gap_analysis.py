"""
Unit tests for the GapAnalysisEngine class.

Tests cover gap analysis, section classification, question generation,
and prioritization functionality.
"""

import pytest
from pathlib import Path
from src.hiveforge.steering.gap_analysis import GapAnalysisEngine
from src.hiveforge.steering.knowledge_base import KnowledgeBase
from src.hiveforge.steering.models import (
    ParsedDocument,
    CodeAnalysisResult,
    TechStackInfo,
    ConventionsInfo,
    ArchitectureInfo,
    Template,
    TemplateSection,
)


class TestGapAnalysisEngineInitialization:
    """Test GapAnalysisEngine initialization."""
    
    def test_init_with_default_templates(self):
        """Test initialization with default templates."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        assert engine.knowledge_base == kb
        assert len(engine.templates) == 8  # All 8 steering files
        assert "project-vision" in engine.templates
        assert "tech-stack" in engine.templates
    
    def test_init_with_custom_templates(self):
        """Test initialization with custom templates."""
        kb = KnowledgeBase(documents=[])
        custom_templates = {
            "test-template": Template(
                name="test-template",
                file_name="test.md",
                priority=1,
                sections=[]
            )
        }
        engine = GapAnalysisEngine(knowledge_base=kb, templates=custom_templates)
        
        assert len(engine.templates) == 1
        assert "test-template" in engine.templates


class TestGapAnalysisBasic:
    """Test basic gap analysis functionality."""
    
    def test_analyze_with_empty_knowledge_base(self):
        """Test analysis with no information available."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Should have missing sections for all required sections
        assert len(result.missing_sections) > 0
        # Should have questions generated
        assert len(result.questions) > 0
        # Questions should be prioritized (project-vision and tech-stack first)
        assert result.questions[0].template_name in ["project-vision", "tech-stack"]
    
    def test_analyze_with_complete_information(self):
        """Test analysis when information is available for some templates."""
        docs = [
            ParsedDocument(
                file_path=Path("complete.md"),
                content="""
# Elevator Pitch
A comprehensive project management tool for agile teams.

# Problem Statement
Teams struggle with coordinating work across distributed members.

# Solution Overview
We provide real-time collaboration with integrated task tracking.

# Target Users
Primary: Software development teams
Secondary: Project managers

# Success Metrics
North Star Metric: Daily active users
Target: 10,000 by Q4 2024

# Technology Stack
Backend: Python 3.11 with FastAPI
Frontend: React 18 with TypeScript
Database: PostgreSQL 15
Cache: Redis 7

# Architecture
Component: API Gateway handles all incoming requests
Component: Auth Service manages authentication
Component: Task Service handles task operations

# Naming Conventions
Variables: snake_case
Classes: PascalCase
Constants: UPPER_SNAKE_CASE

# Code Style
Indentation: 4 spaces
Line length: 100 characters
"""
            )
        ]
        kb = KnowledgeBase(documents=docs)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Should have some complete sections from the provided information
        assert len(result.complete_sections) > 0
        assert "project-vision" in result.complete_sections
        assert "conventions" in result.complete_sections
        
        # Should still have missing sections for templates not covered
        assert len(result.missing_sections) > 0


class TestSectionClassification:
    """Test section classification logic."""
    
    def test_classify_section_with_code_analysis_tech_stack(self):
        """Test that code analysis data marks tech-stack sections as complete."""
        code_analysis = CodeAnalysisResult(
            tech_stack=TechStackInfo(
                backend_framework="FastAPI",
                frontend_framework="React",
                database="PostgreSQL",
                cache="Redis"
            )
        )
        kb = KnowledgeBase(documents=[], code_analysis=code_analysis)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Tech-stack sections should be marked as complete
        assert "tech-stack" in result.complete_sections
        assert "Backend" in result.complete_sections["tech-stack"]
        assert "Frontend" in result.complete_sections["tech-stack"]
        assert "Database" in result.complete_sections["tech-stack"]
        assert "Cache" in result.complete_sections["tech-stack"]
    
    def test_classify_section_with_code_analysis_architecture(self):
        """Test that code analysis marks architecture sections as complete."""
        code_analysis = CodeAnalysisResult(
            architecture=ArchitectureInfo(
                pattern="microservices",
                key_components=["API Gateway", "Auth Service", "User Service"]
            )
        )
        kb = KnowledgeBase(documents=[], code_analysis=code_analysis)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Architecture sections should be marked as complete
        assert "architecture" in result.complete_sections
        assert "Component Responsibilities" in result.complete_sections["architecture"]
    
    def test_classify_section_with_code_analysis_conventions(self):
        """Test that code analysis marks conventions sections as complete."""
        code_analysis = CodeAnalysisResult(
            conventions=ConventionsInfo(
                naming_style={"variables": "snake_case", "classes": "PascalCase"},
                formatting={"indent": "4 spaces", "line_length": 100}
            )
        )
        kb = KnowledgeBase(documents=[], code_analysis=code_analysis)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Conventions sections should be marked as complete
        assert "conventions" in result.complete_sections
        assert "Naming Conventions" in result.complete_sections["conventions"]
        assert "Code Style" in result.complete_sections["conventions"]
    
    def test_classify_section_as_ambiguous(self):
        """Test that sections with partial information are marked as ambiguous."""
        docs = [
            ParsedDocument(
                file_path=Path("partial.md"),
                content="""
# Problem Statement
{What pain does this solve? Be specific.}
We have some issues with coordination.
"""
            )
        ]
        kb = KnowledgeBase(documents=docs)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Section with placeholders should be ambiguous
        assert "project-vision" in result.ambiguous_sections
        assert "Problem Statement" in result.ambiguous_sections["project-vision"]
    
    def test_classify_section_as_missing(self):
        """Test that sections with no information are marked as missing."""
        docs = [
            ParsedDocument(
                file_path=Path("other.md"),
                content="# Unrelated Content\nSome other information."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Most sections should be missing
        assert len(result.missing_sections) > 0
        assert "project-vision" in result.missing_sections


class TestQuestionGeneration:
    """Test question generation functionality."""
    
    def test_questions_generated_for_missing_sections(self):
        """Test that questions are generated for missing required sections."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Should have questions for missing sections
        assert len(result.questions) > 0
        
        # Questions should have all required fields
        for question in result.questions:
            assert question.template_name
            assert question.section_name
            assert question.question_text
            assert question.context
            assert question.priority >= 0
    
    def test_questions_have_appropriate_text(self):
        """Test that generated questions have meaningful text."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Find a specific question
        problem_question = next(
            (q for q in result.questions 
             if q.template_name == "project-vision" and q.section_name == "Problem Statement"),
            None
        )
        
        if problem_question:
            assert "problem" in problem_question.question_text.lower()
            assert len(problem_question.question_text) > 10
    
    def test_clarification_questions_for_ambiguous_sections(self):
        """Test that clarification questions are generated for ambiguous sections."""
        docs = [
            ParsedDocument(
                file_path=Path("ambiguous.md"),
                content="""
# Problem Statement
{TODO: Fill this in}
Something about problems.
"""
            )
        ]
        kb = KnowledgeBase(documents=docs)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Should have clarification questions
        clarification_questions = [
            q for q in result.questions
            if "clarify" in q.question_text.lower()
        ]
        assert len(clarification_questions) > 0


class TestPrioritization:
    """Test question prioritization functionality."""
    
    def test_questions_sorted_by_priority(self):
        """Test that questions are sorted by priority."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Questions should be sorted (lower priority number = higher priority)
        priorities = [q.priority for q in result.questions]
        assert priorities == sorted(priorities)
    
    def test_project_vision_and_tech_stack_prioritized(self):
        """Test that project-vision and tech-stack questions come first."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # First several questions should be from high-priority templates
        high_priority_templates = {"project-vision", "tech-stack"}
        first_questions = result.questions[:5]
        
        high_priority_count = sum(
            1 for q in first_questions
            if q.template_name in high_priority_templates
        )
        
        # At least half of first questions should be high priority
        assert high_priority_count >= len(first_questions) // 2
    
    def test_clarification_questions_lower_priority(self):
        """Test that clarification questions have lower priority than missing sections."""
        docs = [
            ParsedDocument(
                file_path=Path("mixed.md"),
                content="""
# Problem Statement
{TODO}
Some vague content.
"""
            )
        ]
        kb = KnowledgeBase(documents=docs)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Find clarification and missing questions
        clarification_q = next(
            (q for q in result.questions if "clarify" in q.question_text.lower()),
            None
        )
        missing_q = next(
            (q for q in result.questions 
             if "clarify" not in q.question_text.lower() and q.template_name == "project-vision"),
            None
        )
        
        if clarification_q and missing_q:
            # Clarification should have higher priority number (lower priority)
            assert clarification_q.priority > missing_q.priority


class TestQuestionGrouping:
    """Test that questions are grouped by steering file."""
    
    def test_questions_include_template_name(self):
        """Test that all questions include template name for grouping."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # All questions should have template_name
        for question in result.questions:
            assert question.template_name in engine.templates
    
    def test_questions_can_be_grouped_by_template(self):
        """Test that questions can be easily grouped by template."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Group questions by template
        grouped = {}
        for question in result.questions:
            if question.template_name not in grouped:
                grouped[question.template_name] = []
            grouped[question.template_name].append(question)
        
        # Should have questions for multiple templates
        assert len(grouped) > 1
        
        # Each group should have at least one question
        for template_name, questions in grouped.items():
            assert len(questions) > 0


class TestContextInclusion:
    """Test that questions include relevant context."""
    
    def test_questions_include_context(self):
        """Test that all questions include context explaining why info is needed."""
        docs = [
            ParsedDocument(
                file_path=Path("context.md"),
                content="We are building a project management tool."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # All questions should have context
        for question in result.questions:
            assert question.context
            assert len(question.context) > 0
            # Context should mention the template and section
            assert question.template_name in question.context or question.section_name in question.context


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_analyze_with_only_code_analysis(self):
        """Test analysis with only code analysis, no documents."""
        code_analysis = CodeAnalysisResult(
            tech_stack=TechStackInfo(backend_framework="FastAPI"),
            conventions=ConventionsInfo(naming_style={"variables": "snake_case"})
        )
        kb = KnowledgeBase(documents=[], code_analysis=code_analysis)
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        result = engine.analyze()
        
        # Should have some complete sections from code analysis
        assert len(result.complete_sections) > 0
        # Should still have missing sections for non-technical info
        assert len(result.missing_sections) > 0
    
    def test_analyze_with_single_template(self):
        """Test analysis with only one template."""
        kb = KnowledgeBase(documents=[])
        single_template = {
            "project-vision": engine.templates["project-vision"]
            for engine in [GapAnalysisEngine(knowledge_base=kb)]
        }
        engine = GapAnalysisEngine(knowledge_base=kb, templates=single_template)
        
        result = engine.analyze()
        
        # Should only analyze the single template
        all_template_names = set()
        for sections in [result.complete_sections, result.missing_sections, result.ambiguous_sections]:
            all_template_names.update(sections.keys())
        
        assert len(all_template_names) <= 1
    
    def test_has_substantial_content_with_placeholders(self):
        """Test detection of placeholder content."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        # Content with many placeholders
        placeholder_content = "# Section\n{TODO} {FIXME} {TBD} ..."
        assert not engine._has_substantial_content(placeholder_content, r"\{.*?\}")
        
        # Content with real information
        real_content = "# Section\nThis is a detailed explanation of the problem we are solving."
        assert engine._has_substantial_content(real_content, r"\{.*?\}")
    
    def test_get_section_keywords(self):
        """Test keyword retrieval for sections."""
        kb = KnowledgeBase(documents=[])
        engine = GapAnalysisEngine(knowledge_base=kb)
        
        # Should return keywords for known sections
        keywords = engine._get_section_keywords("project-vision", "Problem Statement")
        assert len(keywords) > 0
        assert "problem" in keywords
        
        # Should return empty list for unknown sections
        keywords = engine._get_section_keywords("unknown", "Unknown Section")
        assert keywords == []
