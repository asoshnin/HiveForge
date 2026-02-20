"""
Tests for the TemplatePopulator class.

This module tests template population functionality including placeholder
replacement, frontmatter preservation, and batch processing.
"""

import pytest
from pathlib import Path

from hiveforge.steering.template_populator import TemplatePopulator


class TestTemplatePopulator:
    """Test suite for TemplatePopulator class."""
    
    @pytest.fixture
    def populator(self):
        """Create a TemplatePopulator instance for testing."""
        return TemplatePopulator()
    
    def test_initialization(self, populator):
        """Test that populator initializes with all templates."""
        assert len(populator.templates) == 8
        assert "project-vision" in populator.templates
        assert "tech-stack" in populator.templates
        assert "architecture" in populator.templates
        assert "conventions" in populator.templates
        assert "api-standards" in populator.templates
        assert "db-standards" in populator.templates
        assert "qa-standards" in populator.templates
        assert "ui-standards" in populator.templates
    
    def test_populate_project_vision(self, populator):
        """Test populating project-vision template."""
        knowledge = {
            "PROJECT_NAME": "TestProject",
            "One sentence description of what this does and for whom": "A test project for testing",
            "What pain does this solve? Be specific.": "Solves testing problems",
            "How do we solve it? High-level approach.": "By writing good tests",
            "Who benefits most": "Developers",
            "Who else benefits": "QA Engineers",
            "The one number that matters": "Test coverage",
            "Value": "95%",
            "Date": "2024-12-31",
        }
        
        result = populator.populate("project-vision", knowledge)
        
        # Check frontmatter is preserved
        assert result.startswith("---\n")
        assert "inclusion: always" in result
        assert "priority: 1" in result
        
        # Check placeholders are replaced
        assert "TestProject" in result
        assert "A test project for testing" in result
        assert "Solves testing problems" in result
        assert "By writing good tests" in result
        assert "Developers" in result
        assert "QA Engineers" in result
    
    def test_populate_tech_stack(self, populator):
        """Test populating tech-stack template."""
        knowledge = {
            "Python 3.11|Node.js 18|Go 1.21|...": "Python 3.11",
            "FastAPI|Express|Gin|...": "FastAPI",
            "CPython|Node|...": "CPython",
            "PostgreSQL 15|MongoDB 6|...": "PostgreSQL 15",
            "Redis 7|...": "Redis 7",
            "Why this stack? Trade-offs considered?": "Python for rapid development",
        }
        
        result = populator.populate("tech-stack", knowledge)
        
        # Check frontmatter is preserved
        assert result.startswith("---\n")
        assert "inclusion: always" in result
        
        # Check placeholders are replaced
        assert "Python 3.11" in result
        assert "FastAPI" in result
        assert "CPython" in result
        assert "PostgreSQL 15" in result
        assert "Redis 7" in result
        assert "Python for rapid development" in result
    
    def test_populate_with_nested_knowledge(self, populator):
        """Test populate_all with nested knowledge structure."""
        knowledge = {
            "project-vision": {
                "PROJECT_NAME": "NestedProject",
                "One sentence description of what this does and for whom": "Nested test",
            },
            "tech-stack": {
                "Python 3.11|Node.js 18|Go 1.21|...": "Python 3.11",
            }
        }
        
        result = populator.populate_all(knowledge)
        
        assert len(result) == 8
        assert "project-vision.md" in result
        assert "tech-stack.md" in result
        assert "NestedProject" in result["project-vision.md"]
        assert "Python 3.11" in result["tech-stack.md"]
    
    def test_populate_all_flat_knowledge(self, populator):
        """Test populate_all with flat knowledge structure."""
        knowledge = {
            "PROJECT_NAME": "FlatProject",
            "One sentence description of what this does and for whom": "Flat test",
            "Python 3.11|Node.js 18|Go 1.21|...": "Python 3.11",
        }
        
        result = populator.populate_all(knowledge)
        
        assert len(result) == 8
        # All templates should have access to flat knowledge
        assert "FlatProject" in result["project-vision.md"]
    
    def test_extract_frontmatter(self, populator):
        """Test frontmatter extraction."""
        content = """---
inclusion: always
priority: 1
description: "Test"
---

# Content
Body text here"""
        
        frontmatter, body = populator._extract_frontmatter(content)
        
        assert "inclusion: always" in frontmatter
        assert "priority: 1" in frontmatter
        assert "description: \"Test\"" in frontmatter
        assert "# Content" in body
        assert "Body text here" in body
        assert "---" not in body
    
    def test_extract_frontmatter_no_frontmatter(self, populator):
        """Test extraction when no frontmatter exists."""
        content = "# Just Content\nNo frontmatter here"
        
        frontmatter, body = populator._extract_frontmatter(content)
        
        assert frontmatter == ""
        assert body == content
    
    def test_preserve_frontmatter(self, populator):
        """Test that frontmatter is preserved from original."""
        original = """---
inclusion: always
priority: 1
custom_field: "original"
---

# Original Content"""
        
        populated = """---
inclusion: auto
priority: 2
---

# New Content"""
        
        result = populator.preserve_frontmatter(original, populated)
        
        # Should have original frontmatter
        assert "custom_field: \"original\"" in result
        assert "priority: 1" in result
        # Should have new body
        assert "# New Content" in result
        assert "# Original Content" not in result
    
    def test_replace_placeholders_simple(self, populator):
        """Test simple placeholder replacement."""
        content = "Hello {name}, welcome to {place}!"
        knowledge = {"name": "Alice", "place": "Wonderland"}
        
        result = populator._replace_placeholders(content, knowledge)
        
        assert result == "Hello Alice, welcome to Wonderland!"
    
    def test_replace_placeholders_with_options(self, populator):
        """Test placeholder replacement with pipe-separated options."""
        content = "Language: {Python|JavaScript|Go}"
        knowledge = {"Python": "Python 3.11"}
        
        result = populator._replace_placeholders(content, knowledge)
        
        assert "Python 3.11" in result
    
    def test_replace_placeholders_case_insensitive(self, populator):
        """Test that placeholder replacement is case-insensitive."""
        content = "Project: {PROJECT_NAME}"
        knowledge = {"project_name": "TestProject"}
        
        result = populator._replace_placeholders(content, knowledge)
        
        assert "TestProject" in result
    
    def test_replace_placeholders_with_none_values(self, populator):
        """Test that None values are skipped."""
        content = "Name: {name}, Age: {age}"
        knowledge = {"name": "Alice", "age": None}
        
        result = populator._replace_placeholders(content, knowledge)
        
        assert "Alice" in result
        assert "{age}" in result  # Should remain unchanged
    
    def test_replace_placeholders_with_non_string_values(self, populator):
        """Test that non-string values are converted to strings."""
        content = "Count: {count}, Price: {price}"
        knowledge = {"count": 42, "price": 19.99}
        
        result = populator._replace_placeholders(content, knowledge)
        
        assert "42" in result
        assert "19.99" in result
    
    def test_populate_invalid_template_name(self, populator):
        """Test that invalid template name raises ValueError."""
        with pytest.raises(ValueError, match="Template 'invalid' not found"):
            populator.populate("invalid", {})
    
    def test_populate_all_handles_errors_gracefully(self, populator, monkeypatch):
        """Test that populate_all continues even if one template fails."""
        # Mock populate to fail for one template
        original_populate = populator.populate
        
        def mock_populate(template_name, knowledge):
            if template_name == "project-vision":
                raise Exception("Test error")
            return original_populate(template_name, knowledge)
        
        monkeypatch.setattr(populator, "populate", mock_populate)
        
        result = populator.populate_all({})
        
        # Should have 7 templates (8 - 1 failed)
        assert len(result) == 7
        assert "project-vision.md" not in result
        assert "tech-stack.md" in result
    
    def test_populate_preserves_mermaid_diagrams(self, populator):
        """Test that Mermaid diagrams in templates are preserved."""
        result = populator.populate("architecture", {})
        
        # Check that Mermaid diagram is still present
        assert "```mermaid" in result
        assert "graph TD" in result
        assert "User -->|HTTP| API_Gateway" in result
    
    def test_populate_preserves_tables(self, populator):
        """Test that markdown tables are preserved."""
        result = populator.populate("tech-stack", {})
        
        # Check that table structure is preserved
        assert "| Purpose | Library | Version | Notes |" in result
        assert "|---------|---------|---------|-------|" in result
    
    def test_populate_all_returns_all_filenames(self, populator):
        """Test that populate_all returns correct filenames."""
        result = populator.populate_all({})
        
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "api-standards.md",
            "db-standards.md",
            "qa-standards.md",
            "ui-standards.md",
        ]
        
        for filename in expected_files:
            assert filename in result
    
    def test_frontmatter_format_consistency(self, populator):
        """Test that frontmatter format is consistent across all templates."""
        for template_name in populator.templates.keys():
            result = populator.populate(template_name, {})
            
            # All should start with frontmatter
            assert result.startswith("---\n")
            
            # Should have inclusion field
            assert "inclusion:" in result
            
            # Should have priority field
            assert "priority:" in result
    
    def test_populate_with_special_characters(self, populator):
        """Test placeholder replacement with special characters."""
        content = "Description: {desc}"
        knowledge = {"desc": "Test with $pecial ch@racters & symbols!"}
        
        result = populator._replace_placeholders(content, knowledge)
        
        assert "Test with $pecial ch@racters & symbols!" in result
    
    def test_populate_with_multiline_values(self, populator):
        """Test placeholder replacement with multiline values."""
        content = "Description: {desc}"
        knowledge = {"desc": "Line 1\nLine 2\nLine 3"}
        
        result = populator._replace_placeholders(content, knowledge)
        
        assert "Line 1\nLine 2\nLine 3" in result


class TestTemplatePopulatorIntegration:
    """Integration tests for TemplatePopulator with real templates."""
    
    @pytest.fixture
    def populator(self):
        """Create a TemplatePopulator instance."""
        return TemplatePopulator()
    
    def test_full_project_vision_population(self, populator):
        """Test complete population of project-vision template."""
        knowledge = {
            "project_name": "HiveForge",
            "One sentence description of what this does and for whom": 
                "A Python CLI tool for scaffolding KIRO v05 projects with multi-agent architecture",
            "What pain does this solve? Be specific.": 
                "Eliminates manual setup of complex multi-agent project structures",
            "How do we solve it? High-level approach.": 
                "Automated scaffolding with best-practice templates and agent definitions",
            "Who benefits most": "Python developers building AI agent systems",
            "Who else benefits": "DevOps engineers and team leads",
            "The one number that matters": "Projects scaffolded per week",
            "Value": "100",
            "Date": "Q1 2025",
            "Out of scope feature 1": "Custom agent creation UI",
            "Out of scope feature 2": "Cloud deployment automation",
            "Business constraint": "Must work offline",
            "Technical constraint": "Python 3.11+ required",
            "Key assumption that if wrong, invalidates project": 
                "Users have basic CLI knowledge",
        }
        
        result = populator.populate("project-vision", knowledge)
        
        # Verify all major sections are populated
        assert "HiveForge" in result
        assert "Python CLI tool" in result
        assert "Eliminates manual setup" in result
        assert "Automated scaffolding" in result
        assert "Python developers" in result
        assert "DevOps engineers" in result
        assert "Projects scaffolded per week" in result
        assert "100" in result
        assert "Q1 2025" in result
        assert "Custom agent creation UI" in result
        assert "Must work offline" in result
        
        # Verify structure is maintained
        assert "## Elevator Pitch" in result
        assert "## Problem Statement" in result
        assert "## Solution Overview" in result
        assert "## Target Users" in result
        assert "## Success Metrics" in result
    
    def test_full_tech_stack_population(self, populator):
        """Test complete population of tech-stack template."""
        knowledge = {
            "Python 3.11|Node.js 18|Go 1.21|...": "Python 3.11",
            "FastAPI|Express|Gin|...": "FastAPI",
            "CPython|Node|...": "CPython",
            "React 18|Vue 3|Svelte|...": "React 18",
            "TypeScript|JavaScript|...": "TypeScript",
            "Tailwind|Styled Components|...": "Tailwind CSS",
            "PostgreSQL 15|MongoDB 6|...": "PostgreSQL 15",
            "Redis 7|...": "Redis 7",
            "SQLAlchemy|Prisma|Mongoose|...": "SQLAlchemy",
            "Docker|...": "Docker",
            "K8s|Docker Compose|...": "Docker Compose",
            "AWS|GCP|Azure|...": "AWS",
            "Why this stack? Trade-offs considered?": 
                "Python for AI/ML ecosystem, FastAPI for performance, PostgreSQL for reliability",
        }
        
        result = populator.populate("tech-stack", knowledge)
        
        # Verify all technologies are populated
        assert "Python 3.11" in result
        assert "FastAPI" in result
        assert "React 18" in result
        assert "TypeScript" in result
        assert "PostgreSQL 15" in result
        assert "Redis 7" in result
        assert "Docker" in result
        assert "AWS" in result
        
        # Verify rationale is included
        assert "Python for AI/ML ecosystem" in result
