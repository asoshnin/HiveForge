"""
Unit tests for the KnowledgeBase class.

Tests cover initialization, search, content retrieval, section extraction,
and token limiting functionality.
"""

import pytest
from pathlib import Path
from src.hiveforge.steering.knowledge_base import KnowledgeBase
from src.hiveforge.steering.models import (
    ParsedDocument,
    CodeAnalysisResult,
    TechStackInfo,
    ConventionsInfo,
    ArchitectureInfo,
    LanguageInfo,
    Dependency,
)


class TestKnowledgeBaseInitialization:
    """Test KnowledgeBase initialization."""
    
    def test_init_with_documents_only(self):
        """Test initialization with only parsed documents."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Test Document\nSome content here."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        assert kb.documents == docs
        assert kb.code_analysis is None
        assert len(kb._content_index) > 0
    
    def test_init_with_documents_and_code_analysis(self):
        """Test initialization with documents and code analysis."""
        docs = [
            ParsedDocument(
                file_path=Path("readme.md"),
                content="# Project\nA test project."
            )
        ]
        code_analysis = CodeAnalysisResult(
            languages=[LanguageInfo(name="Python", version="3.11", percentage=100.0)],
            tech_stack=TechStackInfo(backend_framework="FastAPI"),
        )
        kb = KnowledgeBase(documents=docs, code_analysis=code_analysis)
        
        assert kb.documents == docs
        assert kb.code_analysis == code_analysis
        assert "Code Analysis" in kb._content_index
    
    def test_init_with_empty_documents(self):
        """Test initialization with empty document list."""
        kb = KnowledgeBase(documents=[])
        
        assert kb.documents == []
        assert kb.code_analysis is None
        assert kb._content_index == ""


class TestKnowledgeBaseSearch:
    """Test KnowledgeBase search functionality."""
    
    def test_search_finds_matching_content(self):
        """Test that search finds content matching the query."""
        docs = [
            ParsedDocument(
                file_path=Path("doc1.md"),
                content="# Architecture\nWe use microservices architecture.\nEach service is independent."
            ),
            ParsedDocument(
                file_path=Path("doc2.md"),
                content="# Tech Stack\nPython and FastAPI for backend."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        results = kb.search("architecture")
        
        assert len(results) > 0
        assert any("microservices" in result.lower() for result in results)
        assert any("doc1.md" in result for result in results)
    
    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Testing\nWe use PYTEST for testing."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        results_lower = kb.search("pytest")
        results_upper = kb.search("PYTEST")
        results_mixed = kb.search("PyTest")
        
        assert len(results_lower) > 0
        assert len(results_upper) > 0
        assert len(results_mixed) > 0
    
    def test_search_includes_context(self):
        """Test that search results include surrounding context."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="Line 1\nLine 2\nTarget line with keyword\nLine 4\nLine 5"
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        results = kb.search("keyword")
        
        assert len(results) > 0
        # Should include lines before and after
        assert "Line 2" in results[0] or "Line 4" in results[0]
    
    def test_search_no_matches(self):
        """Test search with no matching content."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Document\nSome content here."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        results = kb.search("nonexistent")
        
        assert results == []


class TestGetRelevantContent:
    """Test get_relevant_content method."""
    
    def test_get_relevant_content_for_tech_stack(self):
        """Test getting relevant content for tech-stack template."""
        docs = [
            ParsedDocument(
                file_path=Path("spec.md"),
                content="# Technology Stack\nWe use Python 3.11 and FastAPI framework.\nDatabase is PostgreSQL."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        content = kb.get_relevant_content("tech-stack")
        
        assert "Python" in content or "FastAPI" in content or "PostgreSQL" in content
    
    def test_get_relevant_content_with_code_analysis(self):
        """Test that code analysis is included for relevant templates."""
        docs = [ParsedDocument(file_path=Path("test.md"), content="Test")]
        code_analysis = CodeAnalysisResult(
            tech_stack=TechStackInfo(
                backend_framework="FastAPI",
                database="PostgreSQL"
            )
        )
        kb = KnowledgeBase(documents=docs, code_analysis=code_analysis)
        
        content = kb.get_relevant_content("tech-stack")
        
        assert "FastAPI" in content or "PostgreSQL" in content
    
    def test_get_relevant_content_token_limiting(self):
        """Test that content is limited to max tokens."""
        # Create a large document
        large_content = "technology " * 5000  # Very large content
        docs = [
            ParsedDocument(
                file_path=Path("large.md"),
                content=large_content
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        content = kb.get_relevant_content("tech-stack", max_tokens=100)
        
        # Should be truncated (100 tokens ≈ 400 chars)
        assert len(content) <= 500  # Allow some margin
        assert "truncated" in content.lower() or len(content) < len(large_content)
    
    def test_get_relevant_content_for_architecture(self):
        """Test getting relevant content for architecture template."""
        docs = [
            ParsedDocument(
                file_path=Path("arch.md"),
                content="# System Architecture\nWe use microservices pattern.\nComponents include API Gateway and Auth Service."
            )
        ]
        code_analysis = CodeAnalysisResult(
            architecture=ArchitectureInfo(
                pattern="microservices",
                key_components=["API Gateway", "Auth Service", "User Service"]
            )
        )
        kb = KnowledgeBase(documents=docs, code_analysis=code_analysis)
        
        content = kb.get_relevant_content("architecture")
        
        assert "microservices" in content.lower()
        assert "API Gateway" in content or "Auth Service" in content
    
    def test_get_relevant_content_for_conventions(self):
        """Test getting relevant content for conventions template."""
        docs = [
            ParsedDocument(
                file_path=Path("conv.md"),
                content="# Coding Conventions\nUse snake_case for variables.\nIndent with 4 spaces."
            )
        ]
        code_analysis = CodeAnalysisResult(
            conventions=ConventionsInfo(
                naming_style={"variables": "snake_case", "classes": "PascalCase"},
                formatting={"indent": "4 spaces"},
                documentation_style="docstrings"
            )
        )
        kb = KnowledgeBase(documents=docs, code_analysis=code_analysis)
        
        content = kb.get_relevant_content("conventions")
        
        assert "snake_case" in content or "PascalCase" in content or "4 spaces" in content


class TestExtractSection:
    """Test extract_section method."""
    
    def test_extract_section_found(self):
        """Test extracting a section that exists."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Introduction\nIntro content.\n\n# Problem Statement\nThe problem is...\n\n# Solution\nThe solution is..."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        section = kb.extract_section("Problem Statement")
        
        assert section is not None
        assert "Problem Statement" in section
        assert "The problem is" in section
        assert "Solution" not in section  # Should stop at next header
    
    def test_extract_section_case_insensitive(self):
        """Test that section extraction is case-insensitive."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Technology Stack\nPython and FastAPI."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        section = kb.extract_section("technology stack")
        
        assert section is not None
        assert "Python" in section
    
    def test_extract_section_not_found(self):
        """Test extracting a section that doesn't exist."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Introduction\nSome content."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        section = kb.extract_section("Nonexistent Section")
        
        assert section is None
    
    def test_extract_section_partial_match(self):
        """Test that partial section name matches work."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Project Vision and Goals\nOur vision is..."
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        section = kb.extract_section("vision")
        
        assert section is not None
        assert "Our vision" in section


class TestCodeAnalysisAccessors:
    """Test methods for accessing code analysis results."""
    
    def test_get_tech_stack_with_analysis(self):
        """Test getting tech stack when code analysis is available."""
        tech_stack = TechStackInfo(
            backend_framework="FastAPI",
            frontend_framework="React",
            database="PostgreSQL"
        )
        code_analysis = CodeAnalysisResult(tech_stack=tech_stack)
        kb = KnowledgeBase(documents=[], code_analysis=code_analysis)
        
        result = kb.get_tech_stack()
        
        assert result == tech_stack
        assert result.backend_framework == "FastAPI"
    
    def test_get_tech_stack_without_analysis(self):
        """Test getting tech stack when no code analysis is available."""
        kb = KnowledgeBase(documents=[])
        
        result = kb.get_tech_stack()
        
        assert result is None
    
    def test_get_conventions_with_analysis(self):
        """Test getting conventions when code analysis is available."""
        conventions = ConventionsInfo(
            naming_style={"variables": "snake_case"},
            formatting={"indent": "4 spaces"}
        )
        code_analysis = CodeAnalysisResult(conventions=conventions)
        kb = KnowledgeBase(documents=[], code_analysis=code_analysis)
        
        result = kb.get_conventions()
        
        assert result == conventions
        assert result.naming_style["variables"] == "snake_case"
    
    def test_get_conventions_without_analysis(self):
        """Test getting conventions when no code analysis is available."""
        kb = KnowledgeBase(documents=[])
        
        result = kb.get_conventions()
        
        assert result is None
    
    def test_get_architecture_with_analysis(self):
        """Test getting architecture when code analysis is available."""
        architecture = ArchitectureInfo(
            pattern="microservices",
            key_components=["API Gateway", "Auth Service"]
        )
        code_analysis = CodeAnalysisResult(architecture=architecture)
        kb = KnowledgeBase(documents=[], code_analysis=code_analysis)
        
        result = kb.get_architecture()
        
        assert result == architecture
        assert result.pattern == "microservices"
    
    def test_get_architecture_without_analysis(self):
        """Test getting architecture when no code analysis is available."""
        kb = KnowledgeBase(documents=[])
        
        result = kb.get_architecture()
        
        assert result is None


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_multiple_documents_with_same_content(self):
        """Test handling multiple documents with overlapping content."""
        docs = [
            ParsedDocument(file_path=Path("doc1.md"), content="Python framework"),
            ParsedDocument(file_path=Path("doc2.md"), content="Python framework"),
        ]
        kb = KnowledgeBase(documents=docs)
        
        results = kb.search("Python")
        
        # Should find matches in both documents
        assert len(results) >= 2
    
    def test_document_with_special_characters(self):
        """Test handling documents with special characters."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Test\nSpecial chars: @#$%^&*()\nUnicode: 你好世界"
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        # Should not crash
        content = kb.get_relevant_content("tech-stack")
        assert content is not None
    
    def test_very_long_lines(self):
        """Test handling documents with very long lines."""
        long_line = "word " * 10000
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content=f"# Test\n{long_line}"
            )
        ]
        kb = KnowledgeBase(documents=docs)
        
        # Should handle gracefully with token limiting
        content = kb.get_relevant_content("tech-stack", max_tokens=100)
        assert len(content) < len(long_line)
    
    def test_empty_document_content(self):
        """Test handling documents with empty content."""
        docs = [
            ParsedDocument(file_path=Path("empty.md"), content="")
        ]
        kb = KnowledgeBase(documents=docs)
        
        results = kb.search("anything")
        assert results == []
        
        content = kb.get_relevant_content("tech-stack")
        assert content is not None  # Should return something, even if empty



class TestCodeAnalysisCheck:
    """Test has_code_analysis method (Requirement R3.2)."""
    
    def test_has_code_analysis_with_analysis(self):
        """Test has_code_analysis returns True when code analysis is present."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Test Document"
            )
        ]
        code_analysis = CodeAnalysisResult(
            languages=[LanguageInfo(name="Python", version="3.11", percentage=100.0)],
            tech_stack=TechStackInfo(backend_framework="FastAPI"),
        )
        kb = KnowledgeBase(
            documents=docs,
            code_analysis=code_analysis
        )
        
        assert kb.has_code_analysis() is True
    
    def test_has_code_analysis_without_analysis(self):
        """Test has_code_analysis returns False when code analysis is absent."""
        docs = [
            ParsedDocument(
                file_path=Path("test.md"),
                content="# Test Document"
            )
        ]
        kb = KnowledgeBase(
            documents=docs,
            code_analysis=None
        )
        
        assert kb.has_code_analysis() is False
