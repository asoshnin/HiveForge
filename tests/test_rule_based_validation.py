"""
Tests for rule-based validation functions.

This module tests the completeness, structure, and consistency validation
functions that use regex and keyword matching without LLM calls.
"""

import pytest
from pathlib import Path

from src.hiveforge.steering.validators.rule_based import (
    check_completeness,
    check_structure,
    check_consistency,
)
from src.hiveforge.steering.models import Template, TemplateSection, ValidationIssue
from src.hiveforge.steering.templates import get_all_templates


class TestCheckCompleteness:
    """Tests for the check_completeness function."""
    
    def test_complete_file_no_issues(self):
        """Test that a complete file with no placeholders returns no issues."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[
                TemplateSection(
                    name="Section 1",
                    required=True,
                    placeholder_pattern=r"\{placeholder\}",
                )
            ],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """---
inclusion: auto
---

# Test File

## Section 1

This section is complete with actual content.
"""
        
        issues = check_completeness(content, template, "test.md")
        assert len(issues) == 0
    
    def test_detects_unreplaced_placeholder(self):
        """Test that unreplaced placeholders are detected."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[
                TemplateSection(
                    name="Section 1",
                    required=True,
                    placeholder_pattern=r"\{placeholder\}",
                )
            ],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """---
inclusion: auto
---

# Test File

## Section 1

This section has {placeholder} that needs to be replaced.
"""
        
        issues = check_completeness(content, template, "test.md")
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "incomplete_section"
        assert "{placeholder}" in issues[0].message
    
    def test_optional_section_placeholder_is_warning(self):
        """Test that unreplaced placeholders in optional sections are warnings."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[
                TemplateSection(
                    name="Optional Section",
                    required=False,
                    placeholder_pattern=r"\{optional\}",
                )
            ],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """---
inclusion: auto
---

# Test File

## Optional Section

This has {optional} placeholder.
"""
        
        issues = check_completeness(content, template, "test.md")
        assert len(issues) == 1
        assert issues[0].severity == "warning"
    
    def test_detects_multiple_placeholders(self):
        """Test that multiple placeholders are all detected."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[
                TemplateSection(
                    name="Section 1",
                    required=True,
                    placeholder_pattern=r"\{value\}",
                )
            ],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """---
inclusion: auto
---

# Test File

## Section 1

First {value} and second {value} need replacement.
"""
        
        issues = check_completeness(content, template, "test.md")
        assert len(issues) == 2
        assert all(issue.issue_type == "incomplete_section" for issue in issues)
    
    def test_detects_generic_placeholders(self):
        """Test that generic placeholder patterns are detected."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """---
inclusion: auto
---

# Test File

This has {TODO: fill this in} and {PLACEHOLDER} and {...}.
"""
        
        issues = check_completeness(content, template, "test.md")
        assert len(issues) >= 1  # Should detect at least one placeholder
        assert any("TODO" in issue.message or "PLACEHOLDER" in issue.message 
                  for issue in issues)
    
    def test_reports_correct_line_numbers(self):
        """Test that line numbers are correctly reported."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[
                TemplateSection(
                    name="Section 1",
                    required=True,
                    placeholder_pattern=r"\{placeholder\}",
                )
            ],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """---
inclusion: auto
---

# Test File

## Section 1

Line 1
Line 2
Line 3 with {placeholder}
Line 4
"""
        
        issues = check_completeness(content, template, "test.md")
        assert len(issues) == 1
        assert issues[0].line_number == 11  # Line with placeholder
    
    def test_real_tech_stack_template(self):
        """Test with real tech-stack template."""
        templates = get_all_templates()
        tech_stack_template = templates["tech-stack"]
        
        # Content with unreplaced placeholders
        content = """---
inclusion: auto
priority: 1
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** {Python 3.11|Node.js 18|Go 1.21|...}
- **Framework:** {FastAPI|Express|Gin|...}

### Database
- **Primary:** {PostgreSQL 15|MongoDB 6|...}
"""
        
        issues = check_completeness(content, tech_stack_template, "tech-stack.md")
        assert len(issues) > 0
        assert any("Backend" in issue.message for issue in issues)


class TestCheckStructure:
    """Tests for the check_structure function."""
    
    def test_valid_structure_no_issues(self):
        """Test that a file with valid structure returns no issues."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[
                TemplateSection(
                    name="Required Section",
                    required=True,
                    placeholder_pattern="",
                )
            ],
            frontmatter={"inclusion": "auto", "priority": 1},
        )
        
        content = """---
inclusion: auto
priority: 1
---

# Test File

## Required Section

Content here.
"""
        
        issues = check_structure(content, template, "test.md")
        assert len(issues) == 0
    
    def test_detects_missing_frontmatter(self):
        """Test that missing frontmatter is detected."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """# Test File

No frontmatter here.
"""
        
        issues = check_structure(content, template, "test.md")
        assert len(issues) == 1
        assert issues[0].severity == "critical"
        assert issues[0].issue_type == "missing_frontmatter"
    
    def test_detects_missing_frontmatter_field(self):
        """Test that missing frontmatter fields are detected."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[],
            frontmatter={"inclusion": "auto", "priority": 1},
        )
        
        content = """---
inclusion: auto
---

# Test File
"""
        
        issues = check_structure(content, template, "test.md")
        assert len(issues) == 1
        assert issues[0].issue_type == "missing_frontmatter_field"
        assert "priority" in issues[0].message
    
    def test_detects_missing_required_section(self):
        """Test that missing required sections are detected."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[
                TemplateSection(
                    name="Required Section",
                    required=True,
                    placeholder_pattern="",
                ),
                TemplateSection(
                    name="Optional Section",
                    required=False,
                    placeholder_pattern="",
                ),
            ],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """---
inclusion: auto
---

# Test File

## Optional Section

Only optional section present.
"""
        
        issues = check_structure(content, template, "test.md")
        assert len(issues) == 1
        assert issues[0].issue_type == "missing_required_section"
        assert "Required Section" in issues[0].message
    
    def test_accepts_different_header_levels(self):
        """Test that sections with different header levels are accepted."""
        template = Template(
            name="test",
            file_name="test.md",
            priority=1,
            sections=[
                TemplateSection(
                    name="Section One",
                    required=True,
                    placeholder_pattern="",
                ),
                TemplateSection(
                    name="Section Two",
                    required=True,
                    placeholder_pattern="",
                ),
            ],
            frontmatter={"inclusion": "auto"},
        )
        
        content = """---
inclusion: auto
---

# Test File

## Section One

Content.

### Section Two

More content.
"""
        
        issues = check_structure(content, template, "test.md")
        assert len(issues) == 0
    
    def test_real_project_vision_template(self):
        """Test with real project-vision template."""
        templates = get_all_templates()
        project_vision_template = templates["project-vision"]
        
        # Valid content
        content = """---
inclusion: auto
priority: 1
---

# Project Vision: My Project

## Elevator Pitch
A tool that does something useful.

## Problem Statement
Users have a problem.

## Solution Overview
We solve it this way.

## Target Users
1. **Primary:** Developers
2. **Secondary:** Managers

## Success Metrics
- **North Star Metric:** User adoption
- **Target:** 1000 users by Q4

## Non-Goals (What We Explicitly Don't Do)
- We don't do X
- We don't do Y

## Constraints & Assumptions
- Budget constraint
- Technical constraint

## Timeline
- **MVP:** Q1 2024
- **V1.0:** Q2 2024
"""
        
        issues = check_structure(content, project_vision_template, "project-vision.md")
        # Should have no critical issues (all required sections present)
        critical_issues = [i for i in issues if i.severity == "critical"]
        assert len(critical_issues) == 0


class TestCheckConsistency:
    """Tests for the check_consistency function."""
    
    def test_consistent_files_no_issues(self):
        """Test that consistent files return no issues."""
        files = {
            "tech-stack.md": """
# Tech Stack

## Database
- **Primary:** PostgreSQL 15
""",
            "db-standards.md": """
# Database Standards

## Schema Design
Use SQL tables with proper foreign keys.
""",
        }
        
        issues = check_consistency(files)
        # Should have no critical issues
        critical_issues = [i for i in issues if i.severity == "critical"]
        assert len(critical_issues) == 0
    
    def test_detects_database_type_mismatch(self):
        """Test that database type mismatches are detected."""
        files = {
            "tech-stack.md": """
# Tech Stack

## Database
- **Primary:** PostgreSQL 15
""",
            "db-standards.md": """
# Database Standards

## Document Design
Use MongoDB collections and documents.
Store data in NoSQL format with key-value pairs.
""",
        }
        
        issues = check_consistency(files)
        assert len(issues) > 0
        assert any("database" in issue.message.lower() for issue in issues)
        assert any(issue.file_name == "db-standards.md" for issue in issues)
    
    def test_detects_nosql_with_sql_standards(self):
        """Test that NoSQL database with SQL standards is detected."""
        files = {
            "tech-stack.md": """
# Tech Stack

## Database
- **Primary:** MongoDB 6
""",
            "db-standards.md": """
# Database Standards

## Schema Design
Use SQL tables with foreign keys and joins.
""",
        }
        
        issues = check_consistency(files)
        assert len(issues) > 0
        assert any("nosql" in issue.message.lower() or "sql" in issue.message.lower() 
                  for issue in issues)
    
    def test_detects_missing_language_conventions(self):
        """Test that missing language-specific conventions are detected."""
        files = {
            "tech-stack.md": """
# Tech Stack

## Backend
- **Language:** Python 3.11
""",
            "conventions.md": """
# Conventions

## Naming
Use consistent naming.
""",
        }
        
        issues = check_consistency(files)
        # Should suggest Python conventions
        assert any("python" in issue.message.lower() for issue in issues)
        assert any(issue.severity == "info" for issue in issues)
    
    def test_detects_missing_framework_conventions(self):
        """Test that missing framework-specific conventions are detected."""
        files = {
            "tech-stack.md": """
# Tech Stack

## Frontend
- **Framework:** React 18
""",
            "conventions.md": """
# Conventions

## Code Style
Write clean code.
""",
        }
        
        issues = check_consistency(files)
        # Should suggest React conventions
        assert any("react" in issue.message.lower() for issue in issues)
    
    def test_accepts_matching_conventions(self):
        """Test that matching conventions don't generate issues."""
        files = {
            "tech-stack.md": """
# Tech Stack

## Backend
- **Language:** Python 3.11
""",
            "conventions.md": """
# Conventions

## Naming Conventions
### Python
- `snake_case` for variables, functions
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
""",
        }
        
        issues = check_consistency(files)
        # Should have no issues about Python conventions
        python_issues = [i for i in issues if "python" in i.message.lower()]
        assert len(python_issues) == 0
    
    def test_handles_multiple_languages(self):
        """Test consistency checking with multiple languages."""
        files = {
            "tech-stack.md": """
# Tech Stack

## Backend
- **Language:** Python 3.11

## Frontend
- **Language:** TypeScript
""",
            "conventions.md": """
# Conventions

## Naming Conventions
### Python
- `snake_case` for variables

### TypeScript
- `camelCase` for variables
- `PascalCase` for classes
""",
        }
        
        issues = check_consistency(files)
        # Should have no issues since both languages have conventions
        lang_issues = [i for i in issues if "python" in i.message.lower() or 
                      "typescript" in i.message.lower()]
        assert len(lang_issues) == 0
    
    def test_empty_files_no_crash(self):
        """Test that empty files don't cause crashes."""
        files = {
            "tech-stack.md": "",
            "conventions.md": "",
            "db-standards.md": "",
        }
        
        issues = check_consistency(files)
        # Should not crash, may or may not have issues
        assert isinstance(issues, list)
    
    def test_missing_files_handled(self):
        """Test that missing files are handled gracefully."""
        files = {
            "tech-stack.md": """
# Tech Stack

## Database
- **Primary:** PostgreSQL 15
""",
        }
        
        issues = check_consistency(files)
        # Should not crash when db-standards.md is missing
        assert isinstance(issues, list)


class TestIntegration:
    """Integration tests using real templates."""
    
    def test_complete_valid_file(self):
        """Test a complete, valid steering file."""
        templates = get_all_templates()
        tech_stack_template = templates["tech-stack"]
        
        content = """---
inclusion: auto
priority: 1
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** Python 3.11
- **Framework:** FastAPI
- **Runtime:** CPython

### Frontend
- **Framework:** React 18
- **Language:** TypeScript
- **Styling:** Tailwind

### Database
- **Primary:** PostgreSQL 15
- **Cache:** Redis 7
- **ORM/ODM:** SQLAlchemy

### Infrastructure
- **Container:** Docker
- **Orchestration:** Docker Compose
- **Cloud:** AWS

## Key Dependencies
| Purpose | Library | Version | Notes |
|---------|---------|---------|-------|
| Auth | JWT | 2.0 | Token-based auth |
| Testing | pytest | 7.4 | Unit testing |

## Rationale
This stack provides a balance of performance and developer experience.
"""
        
        completeness_issues = check_completeness(
            content, tech_stack_template, "tech-stack.md"
        )
        structure_issues = check_structure(
            content, tech_stack_template, "tech-stack.md"
        )
        
        # Should have no critical issues
        all_issues = completeness_issues + structure_issues
        critical_issues = [i for i in all_issues if i.severity == "critical"]
        assert len(critical_issues) == 0
    
    def test_incomplete_file_detected(self):
        """Test that incomplete files are properly detected."""
        templates = get_all_templates()
        tech_stack_template = templates["tech-stack"]
        
        content = """---
inclusion: auto
priority: 1
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** {Python 3.11|Node.js 18|Go 1.21|...}
- **Framework:** {FastAPI|Express|Gin|...}

### Database
- **Primary:** {PostgreSQL 15|MongoDB 6|...}
"""
        
        completeness_issues = check_completeness(
            content, tech_stack_template, "tech-stack.md"
        )
        
        # Should detect unreplaced placeholders
        assert len(completeness_issues) > 0
        assert all(issue.severity in ["critical", "warning"] 
                  for issue in completeness_issues)
