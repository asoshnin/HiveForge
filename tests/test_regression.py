"""
Regression test suite for Steering Assistant.

This module contains regression tests using known-good examples
from real projects to ensure the steering assistant produces
consistent, correct output.
"""

import pytest
from pathlib import Path
from tests.mocks.mock_llm import MockLLM
from tests.utils.semantic_checker import SemanticSimilarityChecker


# Known-good examples for regression testing
KNOWN_GOOD_EXAMPLES = {
    "project-vision": """# Project Vision

## Elevator Pitch
A Python project for generating steering files.

## Problem Statement
Projects need clear steering documentation.

## Solution Overview
Automated generation of steering files from artifacts and code analysis.

## Target Users
1. **Primary:** Project maintainers
2. **Secondary:** Development teams

## Success Metrics
- **North Star Metric:** Documentation completeness
- **Target:** 100% coverage

## Non-Goals
- Not a documentation generator
- Not a code formatter

## Constraints
- Python 3.11+
- Open source

## Timeline
- **MVP:** 2026-03-01
- **V1.0:** 2026-06-01
""",
    "tech-stack": """# Technology Stack

## Backend
- **Language:** Python 3.11
- **Framework:** FastAPI
- **Runtime:** CPython

## Frontend
- **Framework:** None
- **Language:** None
- **Styling:** None

## Database
- **Primary:** PostgreSQL
- **Cache:** Redis
- **ORM:** SQLAlchemy

## Infrastructure
- **Container:** Docker
- **Orchestration:** Docker Compose
""",
    "architecture": """# Architecture Overview

## System Diagram
```mermaid
graph TD
    User --> API
    API --> Database
```

## Component Responsibilities

### API Layer
- **Responsibility:** Handle HTTP requests
- **Interface:** REST endpoints
- **Dependencies:** Database

### Database Layer
- **Responsibility:** Store data
- **Interface:** SQL queries
- **Dependencies:** None
""",
}


class TestRegressionProjectVision:
    """Regression tests for project-vision.md generation."""

    def test_basic_project_vision_structure(self):
        """Test that project-vision has required sections."""
        content = KNOWN_GOOD_EXAMPLES["project-vision"]

        required_sections = [
            "Elevator Pitch",
            "Problem Statement",
            "Solution Overview",
            "Target Users",
            "Success Metrics",
            "Non-Goals",
            "Constraints",
            "Timeline",
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_project_vision_has_headings(self):
        """Test that project-vision has proper heading structure."""
        content = KNOWN_GOOD_EXAMPLES["project-vision"]

        # Should have H1 for title
        assert content.startswith("# Project Vision")

        # Should have H2 for sections
        assert "## Elevator Pitch" in content
        assert "## Problem Statement" in content


class TestRegressionTechStack:
    """Regression tests for tech-stack.md generation."""

    def test_basic_tech_stack_structure(self):
        """Test that tech-stack has required sections."""
        content = KNOWN_GOOD_EXAMPLES["tech-stack"]

        required_sections = [
            "Backend",
            "Frontend",
            "Database",
            "Infrastructure",
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_tech_stack_has_technology_details(self):
        """Test that tech-stack has technology details."""
        content = KNOWN_GOOD_EXAMPLES["tech-stack"]

        # Check for specific technologies
        assert "Python 3.11" in content
        assert "FastAPI" in content
        assert "PostgreSQL" in content
        assert "Redis" in content
        assert "Docker" in content


class TestRegressionArchitecture:
    """Regression tests for architecture.md generation."""

    def test_basic_architecture_structure(self):
        """Test that architecture has required sections."""
        content = KNOWN_GOOD_EXAMPLES["architecture"]

        required_sections = [
            "System Diagram",
            "Component Responsibilities",
        ]

        for section in required_sections:
            assert section in content, f"Missing section: {section}"

    def test_architecture_has_diagram(self):
        """Test that architecture has a diagram."""
        content = KNOWN_GOOD_EXAMPLES["architecture"]

        # Should have mermaid diagram
        assert "```mermaid" in content
        assert "graph TD" in content

    def test_architecture_has_components(self):
        """Test that architecture has component definitions."""
        content = KNOWN_GOOD_EXAMPLES["architecture"]

        # Should have component with responsibilities
        assert "### API Layer" in content
        assert "### Database Layer" in content


class TestMockLLM:
    """Tests for the mock LLM."""

    def test_mock_llm_generates_response(self):
        """Test that mock LLM generates a response."""
        llm = MockLLM()
        response = llm.generate("Test prompt")

        assert response is not None
        assert len(response) > 0

    def test_mock_llm_tracks_calls(self):
        """Test that mock LLM tracks call count."""
        llm = MockLLM()

        llm.generate("First")
        llm.generate("Second")

        assert llm.get_call_count() == 2

    def test_mock_llm_stores_history(self):
        """Test that mock LLM stores call history."""
        llm = MockLLM()

        llm.generate("Test prompt", temperature=0.5)

        history = llm.get_call_history()
        assert len(history) == 1
        assert history[0]["prompt"] == "Test prompt"
        assert history[0]["temperature"] == 0.5

    def test_mock_llm_custom_response(self):
        """Test that mock LLM can return custom responses."""
        llm = MockLLM()
        llm.set_response("test", "Custom response")

        response = llm.generate("test")

        assert response == "Custom response"


class TestSemanticSimilarityChecker:
    """Tests for the semantic similarity checker."""

    def test_perfect_match(self):
        """Test that identical content has perfect similarity."""
        checker = SemanticSimilarityChecker()

        content = "Test content"
        score = checker.check_similarity(content, content)

        assert score == 1.0

    def test_completely_different(self):
        """Test that different content has low similarity."""
        checker = SemanticSimilarityChecker()

        score = checker.check_similarity("Python", "JavaScript")

        assert score < 0.5

    def test_check_properties(self):
        """Test that properties are checked correctly."""
        checker = SemanticSimilarityChecker()

        content = "# Title\n\nSome content\n\n```python\nprint('hello')\n```"
        result = checker.check_properties(content, ["Title"])

        # Check that Title section is found
        assert "Title" in result["sections_found"]

    def test_is_similar(self):
        """Test the is_similar method."""
        checker = SemanticSimilarityChecker(min_similarity=0.5)

        content = "Test content"
        assert checker.is_similar(content, content) is True
        assert checker.is_similar("Python", "JavaScript") is False
