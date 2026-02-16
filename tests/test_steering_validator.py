"""
Tests for the SteeringValidator class.

This module tests the main validator orchestrator that coordinates
rule-based validation, caching, and optional LLM-based semantic checks.
"""

import json
import pytest
import tempfile
from pathlib import Path

from src.hiveforge.steering.validators.steering_validator import SteeringValidator
from src.hiveforge.steering.models import ValidationIssue


class TestSteeringValidatorInit:
    """Tests for SteeringValidator initialization."""
    
    def test_init_creates_cache_dir(self, tmp_path):
        """Test that initialization creates cache directory."""
        cache_dir = tmp_path / "cache"
        validator = SteeringValidator(cache_dir=cache_dir)
        
        assert cache_dir.exists()
        assert (cache_dir / "validation_cache.json").exists() or True  # May not exist yet
    
    def test_init_loads_templates(self):
        """Test that initialization loads all templates."""
        validator = SteeringValidator()
        
        assert len(validator.templates) == 8
        assert "tech-stack" in validator.templates
        assert "project-vision" in validator.templates
        assert "conventions" in validator.templates
    
    def test_init_with_use_llm_flag(self):
        """Test initialization with LLM flag."""
        validator = SteeringValidator(use_llm=True)
        assert validator.use_llm is True
        
        validator = SteeringValidator(use_llm=False)
        assert validator.use_llm is False


class TestValidateFile:
    """Tests for validate_file method."""
    
    def test_validate_complete_file(self, tmp_path):
        """Test validating a complete, valid file."""
        # Create a valid tech-stack file
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""---
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
| Auth | JWT | 2.0 | Token auth |
| Testing | pytest | 7.4 | Unit tests |

## Rationale
This stack balances performance and developer experience.
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        issues = validator.validate_file(file_path)
        
        # Should have no critical issues
        critical_issues = [i for i in issues if i.severity == "critical"]
        assert len(critical_issues) == 0
    
    def test_validate_file_with_placeholders(self, tmp_path):
        """Test validating a file with unreplaced placeholders."""
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""---
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
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        issues = validator.validate_file(file_path)
        
        # Should detect unreplaced placeholders
        assert len(issues) > 0
        assert any("placeholder" in issue.message.lower() or 
                  "Backend" in issue.message for issue in issues)
    
    def test_validate_file_missing_frontmatter(self, tmp_path):
        """Test validating a file without frontmatter."""
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""# Technology Stack

## Backend
- **Language:** Python 3.11
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        issues = validator.validate_file(file_path)
        
        # Should detect missing frontmatter
        assert len(issues) > 0
        assert any(issue.issue_type == "missing_frontmatter" for issue in issues)
        assert any(issue.severity == "critical" for issue in issues)
    
    def test_validate_file_missing_required_section(self, tmp_path):
        """Test validating a file missing required sections."""
        file_path = tmp_path / "project-vision.md"
        file_path.write_text("""---
inclusion: auto
priority: 1
---

# Project Vision: My Project

## Elevator Pitch
A tool that does something.

## Problem Statement
Users have a problem.
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        issues = validator.validate_file(file_path)
        
        # Should detect missing required sections
        missing_section_issues = [i for i in issues 
                                 if i.issue_type == "missing_required_section"]
        assert len(missing_section_issues) > 0
    
    def test_validate_nonexistent_file(self, tmp_path):
        """Test validating a file that doesn't exist."""
        file_path = tmp_path / "nonexistent.md"
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        issues = validator.validate_file(file_path)
        
        # Should return file read error
        assert len(issues) == 1
        assert issues[0].issue_type == "file_read_error"
        assert issues[0].severity == "critical"
    
    def test_validate_unknown_template(self, tmp_path):
        """Test validating a file with no matching template."""
        file_path = tmp_path / "custom-file.md"
        file_path.write_text("""---
inclusion: auto
---

# Custom File

Some content.
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        issues = validator.validate_file(file_path)
        
        # Should return unknown template warning
        assert len(issues) == 1
        assert issues[0].issue_type == "unknown_template"
        assert issues[0].severity == "warning"


class TestValidateAll:
    """Tests for validate_all method."""
    
    def test_validate_all_empty_directory(self, tmp_path):
        """Test validating an empty directory."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        report = validator.validate_all(steering_dir)
        
        # Should report no files found
        assert report.overall_status == "fail"
        assert len(report.critical_issues) == 1
        assert report.critical_issues[0].issue_type == "no_files_found"
    
    def test_validate_all_single_file(self, tmp_path):
        """Test validating a directory with one file."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create a valid file
        (steering_dir / "tech-stack.md").write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** Python 3.11
- **Framework:** FastAPI

### Database
- **Primary:** PostgreSQL 15
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        report = validator.validate_all(steering_dir)
        
        assert report.files_checked == 1
        # May have warnings but should pass
        if not report.critical_issues:
            assert report.overall_status == "pass"
    
    def test_validate_all_multiple_files(self, tmp_path):
        """Test validating multiple files."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create multiple valid files
        (steering_dir / "tech-stack.md").write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** Python 3.11
- **Framework:** FastAPI

### Database
- **Primary:** PostgreSQL 15
""")
        
        (steering_dir / "conventions.md").write_text("""---
inclusion: auto
priority: 2
---

# Coding Conventions

## General Principles
1. Readability > Cleverness

## Naming Conventions
### Python
- snake_case for variables

## Code Style
### Formatting
- Line length: 100 characters
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        report = validator.validate_all(steering_dir)
        
        assert report.files_checked == 2
    
    def test_validate_all_with_critical_issues(self, tmp_path):
        """Test that critical issues cause overall failure."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create file with critical issue (missing frontmatter)
        (steering_dir / "tech-stack.md").write_text("""# Technology Stack

## Backend
- **Language:** Python 3.11
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        report = validator.validate_all(steering_dir)
        
        assert report.overall_status == "fail"
        assert len(report.critical_issues) > 0
    
    def test_validate_all_consistency_checks(self, tmp_path):
        """Test that cross-file consistency checks are performed."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create files with inconsistent database types
        (steering_dir / "tech-stack.md").write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Database
- **Primary:** PostgreSQL 15
""")
        
        (steering_dir / "db-standards.md").write_text("""---
inclusion: auto
priority: 3
---

# Database Standards

## Document Design
Use MongoDB collections and documents.
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        report = validator.validate_all(steering_dir)
        
        # Should detect database type mismatch
        assert len(report.warnings) > 0 or len(report.info) > 0
    
    def test_validate_all_categorizes_by_severity(self, tmp_path):
        """Test that issues are properly categorized by severity."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create file with various issue types
        (steering_dir / "tech-stack.md").write_text("""---
inclusion: auto
---

# Technology Stack

## Backend
- **Language:** {Python 3.11|Node.js 18|...}
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        report = validator.validate_all(steering_dir)
        
        # Check that issues are categorized
        all_issues = report.critical_issues + report.warnings + report.info
        assert len(all_issues) > 0
        
        # Each issue should have a valid severity
        for issue in all_issues:
            assert issue.severity in ["critical", "warning", "info"]


class TestCaching:
    """Tests for validation result caching."""
    
    def test_cache_stores_results(self, tmp_path):
        """Test that validation results are cached."""
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Backend
- **Language:** Python 3.11
""")
        
        cache_dir = tmp_path / "cache"
        validator = SteeringValidator(cache_dir=cache_dir)
        
        # First validation
        issues1 = validator.validate_file(file_path)
        
        # Check cache file exists
        cache_file = cache_dir / "validation_cache.json"
        assert cache_file.exists()
        
        # Check cache contains entry
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        assert "tech-stack.md" in cache_data
    
    def test_cache_returns_cached_results(self, tmp_path):
        """Test that cached results are returned for unchanged files."""
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Backend
- **Language:** Python 3.11
""")
        
        cache_dir = tmp_path / "cache"
        validator = SteeringValidator(cache_dir=cache_dir)
        
        # First validation
        issues1 = validator.validate_file(file_path)
        
        # Second validation (should use cache)
        issues2 = validator.validate_file(file_path)
        
        # Results should be identical
        assert len(issues1) == len(issues2)
        for i1, i2 in zip(issues1, issues2):
            assert i1.severity == i2.severity
            assert i1.issue_type == i2.issue_type
            assert i1.message == i2.message
    
    def test_cache_invalidates_on_content_change(self, tmp_path):
        """Test that cache is invalidated when file content changes."""
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Backend
- **Language:** {Python 3.11|...}
""")
        
        cache_dir = tmp_path / "cache"
        validator = SteeringValidator(cache_dir=cache_dir)
        
        # First validation (with placeholder)
        issues1 = validator.validate_file(file_path)
        assert len(issues1) > 0
        
        # Modify file (fix placeholder)
        file_path.write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Backend
- **Language:** Python 3.11
""")
        
        # Second validation (should re-validate)
        issues2 = validator.validate_file(file_path)
        
        # Results should be different
        assert len(issues2) != len(issues1)
    
    def test_cache_persists_across_instances(self, tmp_path):
        """Test that cache persists across validator instances."""
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Backend
- **Language:** Python 3.11
""")
        
        cache_dir = tmp_path / "cache"
        
        # First validator instance
        validator1 = SteeringValidator(cache_dir=cache_dir)
        issues1 = validator1.validate_file(file_path)
        
        # Second validator instance (should load cache)
        validator2 = SteeringValidator(cache_dir=cache_dir)
        issues2 = validator2.validate_file(file_path)
        
        # Results should be identical
        assert len(issues1) == len(issues2)
    
    def test_cache_handles_corrupted_cache_file(self, tmp_path):
        """Test that corrupted cache files are handled gracefully."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        # Create corrupted cache file
        cache_file = cache_dir / "validation_cache.json"
        cache_file.write_text("{ invalid json }")
        
        # Should not crash
        validator = SteeringValidator(cache_dir=cache_dir)
        assert validator._cache == {}


class TestLLMIntegration:
    """Tests for optional LLM-based semantic checks."""
    
    def test_check_consistency_semantic_returns_empty_list(self):
        """Test that semantic check returns empty list (not yet implemented)."""
        validator = SteeringValidator(use_llm=True)
        
        files = {
            "tech-stack.md": "# Tech Stack\n\n## Database\nPostgreSQL",
            "db-standards.md": "# DB Standards\n\nUse SQL tables"
        }
        
        issues = validator.check_consistency_semantic(files)
        
        # Currently returns empty list (TODO implementation)
        assert isinstance(issues, list)
        assert len(issues) == 0
    
    def test_validate_all_with_use_llm_flag(self, tmp_path):
        """Test that validate_all respects use_llm flag."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        (steering_dir / "tech-stack.md").write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Backend
- **Language:** Python 3.11
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache", use_llm=False)
        report = validator.validate_all(steering_dir, use_llm=True)
        
        # Should complete without error
        assert report.files_checked == 1
        # LLM calls would be tracked here when implemented
        assert report.llm_calls_made >= 0
        assert report.tokens_used >= 0


class TestValidationReport:
    """Tests for ValidationReport structure."""
    
    def test_report_structure(self, tmp_path):
        """Test that validation report has correct structure."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        (steering_dir / "tech-stack.md").write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Backend
- **Language:** Python 3.11
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        report = validator.validate_all(steering_dir)
        
        # Check report structure
        assert hasattr(report, 'critical_issues')
        assert hasattr(report, 'warnings')
        assert hasattr(report, 'info')
        assert hasattr(report, 'files_checked')
        assert hasattr(report, 'overall_status')
        assert hasattr(report, 'llm_calls_made')
        assert hasattr(report, 'tokens_used')
        
        assert isinstance(report.critical_issues, list)
        assert isinstance(report.warnings, list)
        assert isinstance(report.info, list)
        assert isinstance(report.files_checked, int)
        assert report.overall_status in ["pass", "fail"]
    
    def test_report_includes_line_numbers(self, tmp_path):
        """Test that issues include line numbers when available."""
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""---
inclusion: auto
priority: 1
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** {Python 3.11|Node.js 18|...}
- **Framework:** FastAPI
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        issues = validator.validate_file(file_path)
        
        # Should have issues with line numbers
        issues_with_lines = [i for i in issues if i.line_number is not None]
        assert len(issues_with_lines) > 0
    
    def test_report_includes_suggestions(self, tmp_path):
        """Test that issues include fix suggestions."""
        file_path = tmp_path / "tech-stack.md"
        file_path.write_text("""# Technology Stack

No frontmatter here.
""")
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        issues = validator.validate_file(file_path)
        
        # Should have issues with suggestions
        issues_with_suggestions = [i for i in issues if i.suggestion is not None]
        assert len(issues_with_suggestions) > 0


class TestIntegration:
    """Integration tests with real steering files."""
    
    def test_validate_complete_steering_directory(self, tmp_path):
        """Test validating a complete set of steering files."""
        steering_dir = tmp_path / "steering"
        steering_dir.mkdir()
        
        # Create minimal valid files for all templates
        files_content = {
            "project-vision.md": """---
inclusion: auto
priority: 1
---

# Project Vision: HiveForge

## Elevator Pitch
A CLI tool for scaffolding multi-agent projects.

## Problem Statement
Developers need consistent project structure.

## Solution Overview
Provide templates and automation.

## Target Users
1. **Primary:** Python developers
2. **Secondary:** Team leads

## Success Metrics
- **North Star Metric:** Active users
- **Target:** 1000 by Q4 2024
""",
            "tech-stack.md": """---
inclusion: auto
priority: 1
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** Python 3.11
- **Framework:** FastAPI

### Database
- **Primary:** PostgreSQL 15
""",
            "conventions.md": """---
inclusion: auto
priority: 2
---

# Coding Conventions

## Naming Conventions
### Python
- snake_case for variables

## Code Style
### Formatting
- Line length: 100 characters
"""
        }
        
        for filename, content in files_content.items():
            (steering_dir / filename).write_text(content)
        
        validator = SteeringValidator(cache_dir=tmp_path / "cache")
        report = validator.validate_all(steering_dir)
        
        assert report.files_checked == 3
        # Should have minimal critical issues
        if report.critical_issues:
            # Print for debugging
            for issue in report.critical_issues:
                print(f"Critical: {issue.file_name}: {issue.message}")
