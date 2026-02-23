"""
Unit tests for DriftDetector class (P1-4).

Tests cover all drift detection types:
- Language version drift detection
- Dependency drift detection
- Architecture pattern drift detection
- Convention mismatch detection
- DriftReport sorting and methods
"""

import logging
from pathlib import Path
from textwrap import dedent
from typing import Dict

import pytest

from hiveforge.steering.detectors.drift_detector import DriftDetector
from hiveforge.steering.models import (
    CodeAnalysisResult,
    ArchitectureInfo,
    ConventionsInfo,
    DriftCategory,
    DriftItem,
    DriftReport,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with pyproject.toml."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Create pyproject.toml with Python version and dependencies
    pyproject_content = dedent('''
        [project]
        name = "test-project"
        version = "0.1.0"
        requires-python = ">=3.11"
        dependencies = [
            "fastapi>=0.100.0",
            "sqlalchemy>=2.0.0",
            "redis>=4.5.0",
            "requests>=2.31.0",
            "pydantic>=2.0.0",
            "some-transitive-dep>=1.0.0",
        ]
    ''')
    
    pyproject_path = project_root / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)
    
    return project_root


@pytest.fixture
def detector(temp_project):
    """Create a DriftDetector instance."""
    return DriftDetector(temp_project)


@pytest.fixture
def code_analysis():
    """Create a CodeAnalysisResult for testing."""
    return CodeAnalysisResult(
        architecture=ArchitectureInfo(
            pattern="MVC",
            key_components=["Controller", "Model", "View"]
        ),
        conventions=ConventionsInfo(
            naming_style={
                "variables": "snake_case",
                "classes": "PascalCase",
                "constants": "UPPER_SNAKE_CASE"
            }
        )
    )


class TestLanguageVersionDrift:
    """Tests for _detect_language_version_drift() method."""
    
    def test_detects_python_version_drift(self, detector, code_analysis):
        """Test detection when Python version in tech-stack.md differs from pyproject.toml."""
        existing_files = {
            'tech-stack.md': dedent('''
                # Tech Stack
                
                ## Backend
                - **Language:** Python 3.10
                - **Framework:** FastAPI
            ''')
        }
        
        drift_item = detector._detect_language_version_drift(existing_files, code_analysis)
        
        assert drift_item is not None
        assert drift_item.category == DriftCategory.LANGUAGE_VERSION
        assert drift_item.confidence == 0.95
        assert "3.11" in drift_item.description
        assert "3.10" not in drift_item.description or "3.11" in drift_item.description
    
    def test_no_drift_when_version_matches(self, detector, code_analysis):
        """Test no drift when Python version matches."""
        existing_files = {
            'tech-stack.md': dedent('''
                # Tech Stack
                
                ## Backend
                - **Language:** Python 3.11
                - **Framework:** FastAPI
            ''')
        }
        
        drift_item = detector._detect_language_version_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_no_drift_when_tech_stack_missing(self, detector, code_analysis):
        """Test no drift when tech-stack.md is missing."""
        existing_files = {}
        
        drift_item = detector._detect_language_version_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_no_drift_when_pyproject_missing(self, temp_project, code_analysis):
        """Test no drift when pyproject.toml is missing."""
        # Remove pyproject.toml
        pyproject_path = temp_project / "pyproject.toml"
        pyproject_path.unlink()
        
        detector = DriftDetector(temp_project)
        existing_files = {
            'tech-stack.md': "# Tech Stack\n\nPython 3.10"
        }
        
        drift_item = detector._detect_language_version_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_confidence_score_is_0_95(self, detector, code_analysis):
        """Test that language version drift has confidence 0.95."""
        existing_files = {
            'tech-stack.md': "Python 3.10"
        }
        
        drift_item = detector._detect_language_version_drift(existing_files, code_analysis)
        
        assert drift_item is not None
        assert drift_item.confidence == 0.95


class TestDependencyDrift:
    """Tests for _detect_dependency_drift() method."""
    
    def test_detects_new_significant_dependency(self, detector, code_analysis):
        """Test detection of new significant dependencies."""
        existing_files = {
            'tech-stack.md': dedent('''
                # Tech Stack
                
                ## Key Dependencies
                | Purpose | Library | Version |
                | Testing | pytest | 7.0 |
            ''')
        }
        
        drift_items = detector._detect_dependency_drift(existing_files, code_analysis)
        
        # Should detect fastapi, sqlalchemy, redis, pydantic as new
        assert len(drift_items) > 0
        assert all(item.category == DriftCategory.NEW_DEPENDENCY for item in drift_items)
        assert all(item.confidence == 0.85 for item in drift_items)
    
    def test_no_drift_when_all_deps_documented(self, detector, code_analysis):
        """Test no drift when all significant dependencies are documented."""
        existing_files = {
            'tech-stack.md': dedent('''
                # Tech Stack
                
                ## Key Dependencies
                | Purpose | Library | Version |
                | Backend | FastAPI | 0.100 |
                | Database | SQLAlchemy | 2.0 |
                | Cache | Redis | 4.5 |
                | HTTP | Requests | 2.31 |
                | Validation | Pydantic | 2.0 |
            ''')
        }
        
        drift_items = detector._detect_dependency_drift(existing_files, code_analysis)
        
        # Should not detect drift for documented dependencies
        assert len(drift_items) == 0
    
    def test_no_drift_when_tech_stack_missing(self, detector, code_analysis):
        """Test no drift when tech-stack.md is missing."""
        existing_files = {}
        
        drift_items = detector._detect_dependency_drift(existing_files, code_analysis)
        
        assert drift_items == []
    
    def test_filters_transitive_dependencies(self, detector, code_analysis):
        """Test that transitive dependencies are filtered out."""
        existing_files = {
            'tech-stack.md': dedent('''
                # Tech Stack
                
                ## Key Dependencies
                | Purpose | Library | Version |
                | Backend | FastAPI | 0.100 |
                | Database | SQLAlchemy | 2.0 |
                | Cache | Redis | 4.5 |
                | HTTP | Requests | 2.31 |
                | Validation | Pydantic | 2.0 |
            ''')
        }
        
        drift_items = detector._detect_dependency_drift(existing_files, code_analysis)
        
        # Should not flag "some-transitive-dep" as it's not significant
        dep_names = [item.description for item in drift_items]
        assert not any("some-transitive-dep" in desc for desc in dep_names)
    
    def test_confidence_score_is_0_85(self, detector, code_analysis):
        """Test that dependency drift has confidence 0.85."""
        existing_files = {
            'tech-stack.md': "# Tech Stack"
        }
        
        drift_items = detector._detect_dependency_drift(existing_files, code_analysis)
        
        assert len(drift_items) > 0
        assert all(item.confidence == 0.85 for item in drift_items)


class TestArchitectureDrift:
    """Tests for _detect_architecture_drift() method."""
    
    def test_detects_architecture_pattern_drift(self, detector, code_analysis):
        """Test detection when architecture pattern differs."""
        existing_files = {
            'architecture.md': dedent('''
                # Architecture
                
                ## Pattern
                This project uses a Monolithic architecture.
            ''')
        }
        
        drift_item = detector._detect_architecture_drift(existing_files, code_analysis)
        
        assert drift_item is not None
        assert drift_item.category == DriftCategory.ARCHITECTURE_PATTERN
        assert drift_item.confidence == 0.75
        assert "MVC" in drift_item.description
    
    def test_no_drift_when_pattern_matches(self, detector, code_analysis):
        """Test no drift when architecture pattern matches."""
        existing_files = {
            'architecture.md': dedent('''
                # Architecture
                
                ## Pattern
                This project uses an MVC architecture.
            ''')
        }
        
        drift_item = detector._detect_architecture_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_no_drift_when_architecture_missing(self, detector, code_analysis):
        """Test no drift when architecture.md is missing."""
        existing_files = {}
        
        drift_item = detector._detect_architecture_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_no_drift_when_code_analysis_has_no_pattern(self, detector):
        """Test no drift when code analysis has no architecture pattern."""
        code_analysis = CodeAnalysisResult(
            architecture=ArchitectureInfo(pattern=None)
        )
        existing_files = {
            'architecture.md': "# Architecture"
        }
        
        drift_item = detector._detect_architecture_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_confidence_score_is_0_75(self, detector, code_analysis):
        """Test that architecture drift has confidence 0.75."""
        existing_files = {
            'architecture.md': "Monolithic"
        }
        
        drift_item = detector._detect_architecture_drift(existing_files, code_analysis)
        
        assert drift_item is not None
        assert drift_item.confidence == 0.75


class TestConventionDrift:
    """Tests for _detect_convention_drift() method."""
    
    def test_detects_incomplete_conventions(self, detector, code_analysis):
        """Test detection when conventions are incomplete."""
        existing_files = {
            'conventions.md': dedent('''
                # Conventions
                
                ## Naming
                Use descriptive names.
            ''')
        }
        
        drift_item = detector._detect_convention_drift(existing_files, code_analysis)
        
        assert drift_item is not None
        assert drift_item.category == DriftCategory.CONVENTION_MISMATCH
        assert drift_item.confidence == 0.70
    
    def test_no_drift_when_conventions_documented(self, detector, code_analysis):
        """Test no drift when conventions are well documented."""
        existing_files = {
            'conventions.md': dedent('''
                # Conventions
                
                ## Naming
                - Variables: snake_case
                - Classes: PascalCase
                - Constants: UPPER_SNAKE_CASE
                - Functions: camelCase
            ''')
        }
        
        drift_item = detector._detect_convention_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_no_drift_when_conventions_missing(self, detector, code_analysis):
        """Test no drift when conventions.md is missing."""
        existing_files = {}
        
        drift_item = detector._detect_convention_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_no_drift_when_code_analysis_has_no_conventions(self, detector):
        """Test no drift when code analysis has no conventions."""
        code_analysis = CodeAnalysisResult(
            conventions=ConventionsInfo(naming_style={})
        )
        existing_files = {
            'conventions.md': "# Conventions"
        }
        
        drift_item = detector._detect_convention_drift(existing_files, code_analysis)
        
        assert drift_item is None
    
    def test_confidence_score_is_0_70(self, detector, code_analysis):
        """Test that convention drift has confidence 0.70."""
        existing_files = {
            'conventions.md': "# Conventions\n\nMinimal content"
        }
        
        drift_item = detector._detect_convention_drift(existing_files, code_analysis)
        
        assert drift_item is not None
        assert drift_item.confidence == 0.70


class TestDetectOrchestration:
    """Tests for detect() orchestration method."""
    
    def test_detect_returns_drift_report(self, detector, code_analysis):
        """Test that detect() returns a DriftReport."""
        existing_files = {
            'tech-stack.md': "Python 3.10",
            'architecture.md': "Monolithic",
            'conventions.md': "Minimal"
        }
        
        report = detector.detect(existing_files, code_analysis)
        
        assert isinstance(report, DriftReport)
    
    def test_detect_returns_empty_report_when_no_drift(self, detector, code_analysis):
        """Test that detect() returns empty report when no drift detected."""
        existing_files = {
            'tech-stack.md': dedent('''
                Python 3.11
                FastAPI
                SQLAlchemy
                Redis
                Requests
                Pydantic
            '''),
            'architecture.md': "MVC",
            'conventions.md': dedent('''
                snake_case
                PascalCase
                UPPER_SNAKE_CASE
                camelCase
            ''')
        }
        
        report = detector.detect(existing_files, code_analysis)
        
        assert not report.has_drift()
        assert len(report.items) == 0
    
    def test_detect_sorts_items_by_confidence(self, detector, code_analysis):
        """Test that detect() sorts items by confidence (highest first)."""
        existing_files = {
            'tech-stack.md': "Python 3.10",
            'architecture.md': "Monolithic",
            'conventions.md': "Minimal"
        }
        
        report = detector.detect(existing_files, code_analysis)
        
        # Should have items sorted by confidence
        if len(report.items) > 1:
            for i in range(len(report.items) - 1):
                assert report.items[i].confidence >= report.items[i + 1].confidence
    
    def test_detect_includes_all_drift_types(self, detector, code_analysis):
        """Test that detect() checks all drift types."""
        existing_files = {
            'tech-stack.md': "Python 3.10",
            'architecture.md': "Monolithic",
            'conventions.md': "Minimal"
        }
        
        report = detector.detect(existing_files, code_analysis)
        
        # Should detect multiple types of drift
        assert len(report.items) > 0
        categories = {item.category for item in report.items}
        # Should have at least language version drift
        assert DriftCategory.LANGUAGE_VERSION in categories
    
    def test_detect_with_empty_existing_files(self, detector, code_analysis):
        """Test detect() with empty existing files dict."""
        existing_files = {}
        
        report = detector.detect(existing_files, code_analysis)
        
        assert isinstance(report, DriftReport)
        assert not report.has_drift()


class TestDriftReportMethods:
    """Tests for DriftReport methods."""
    
    def test_has_drift_returns_true_when_items_exist(self):
        """Test has_drift() returns True when items exist."""
        items = [
            DriftItem(
                category=DriftCategory.LANGUAGE_VERSION,
                description="Version mismatch",
                confidence=0.95,
                suggested_action="Update version"
            )
        ]
        report = DriftReport(items=items)
        
        assert report.has_drift() is True
    
    def test_has_drift_returns_false_when_no_items(self):
        """Test has_drift() returns False when no items."""
        report = DriftReport(items=[])
        
        assert report.has_drift() is False
    
    def test_by_severity_sorts_by_confidence_descending(self):
        """Test by_severity() sorts items by confidence descending."""
        items = [
            DriftItem(
                category=DriftCategory.CONVENTION_MISMATCH,
                description="Convention drift",
                confidence=0.70,
                suggested_action="Update conventions"
            ),
            DriftItem(
                category=DriftCategory.LANGUAGE_VERSION,
                description="Version mismatch",
                confidence=0.95,
                suggested_action="Update version"
            ),
            DriftItem(
                category=DriftCategory.ARCHITECTURE_PATTERN,
                description="Architecture drift",
                confidence=0.75,
                suggested_action="Update architecture"
            ),
        ]
        report = DriftReport(items=items)
        
        sorted_items = report.by_severity()
        
        assert sorted_items[0].confidence == 0.95
        assert sorted_items[1].confidence == 0.75
        assert sorted_items[2].confidence == 0.70
    
    def test_by_severity_returns_all_items(self):
        """Test by_severity() returns all items."""
        items = [
            DriftItem(
                category=DriftCategory.LANGUAGE_VERSION,
                description="Version mismatch",
                confidence=0.95,
                suggested_action="Update version"
            ),
            DriftItem(
                category=DriftCategory.NEW_DEPENDENCY,
                description="New dependency",
                confidence=0.85,
                suggested_action="Add dependency"
            ),
        ]
        report = DriftReport(items=items)
        
        sorted_items = report.by_severity()
        
        assert len(sorted_items) == 2


class TestFilterSignificantDependencies:
    """Tests for _filter_significant_dependencies() method."""
    
    def test_filters_to_significant_only(self, detector):
        """Test that only significant dependencies are returned."""
        dependencies = [
            'fastapi',
            'some-random-package',
            'sqlalchemy',
            'another-transitive-dep',
            'redis',
        ]
        
        significant = detector._filter_significant_dependencies(dependencies)
        
        assert 'fastapi' in significant
        assert 'sqlalchemy' in significant
        assert 'redis' in significant
        assert 'some-random-package' not in significant
        assert 'another-transitive-dep' not in significant
    
    def test_matches_by_keyword(self, detector):
        """Test that dependencies matching keywords are included."""
        dependencies = [
            'fastapi-cors',
            'sqlalchemy-utils',
            'redis-py',
        ]
        
        significant = detector._filter_significant_dependencies(dependencies)
        
        # Should match by keyword
        assert len(significant) > 0
    
    def test_case_insensitive_matching(self, detector):
        """Test that matching is case-insensitive."""
        dependencies = [
            'FastAPI',
            'SQLAlchemy',
            'REDIS',
        ]
        
        significant = detector._filter_significant_dependencies(dependencies)
        
        assert len(significant) == 3
    
    def test_empty_list_returns_empty(self, detector):
        """Test that empty dependency list returns empty."""
        dependencies = []
        
        significant = detector._filter_significant_dependencies(dependencies)
        
        assert significant == []


class TestExtractCurrentDependencies:
    """Tests for _extract_current_dependencies() method."""
    
    def test_extracts_dependencies_from_pyproject(self, detector):
        """Test that dependencies are extracted from pyproject.toml."""
        dependencies = detector._extract_current_dependencies()
        
        assert 'fastapi' in dependencies
        assert 'sqlalchemy' in dependencies
        assert 'redis' in dependencies
    
    def test_strips_version_specifiers(self, detector):
        """Test that version specifiers are stripped."""
        dependencies = detector._extract_current_dependencies()
        
        # Should not contain version specifiers
        assert not any('>=' in dep or '<=' in dep or '==' in dep for dep in dependencies)
    
    def test_returns_empty_when_pyproject_missing(self, temp_project):
        """Test that empty list is returned when pyproject.toml is missing."""
        # Remove pyproject.toml
        pyproject_path = temp_project / "pyproject.toml"
        pyproject_path.unlink()
        
        detector = DriftDetector(temp_project)
        dependencies = detector._extract_current_dependencies()
        
        assert dependencies == []


class TestDriftItemConfidenceScores:
    """Tests for correct confidence scores across all drift types."""
    
    def test_language_version_confidence_is_0_95(self, detector, code_analysis):
        """Test language version drift confidence is 0.95."""
        existing_files = {'tech-stack.md': "Python 3.10"}
        drift_item = detector._detect_language_version_drift(existing_files, code_analysis)
        assert drift_item.confidence == 0.95
    
    def test_dependency_confidence_is_0_85(self, detector, code_analysis):
        """Test dependency drift confidence is 0.85."""
        existing_files = {'tech-stack.md': "# Tech Stack"}
        drift_items = detector._detect_dependency_drift(existing_files, code_analysis)
        assert all(item.confidence == 0.85 for item in drift_items)
    
    def test_architecture_confidence_is_0_75(self, detector, code_analysis):
        """Test architecture drift confidence is 0.75."""
        existing_files = {'architecture.md': "Monolithic"}
        drift_item = detector._detect_architecture_drift(existing_files, code_analysis)
        assert drift_item.confidence == 0.75
    
    def test_convention_confidence_is_0_70(self, detector, code_analysis):
        """Test convention drift confidence is 0.70."""
        existing_files = {'conventions.md': "Minimal"}
        drift_item = detector._detect_convention_drift(existing_files, code_analysis)
        assert drift_item.confidence == 0.70


class TestGracefulErrorHandling:
    """Tests for graceful error handling."""
    
    def test_handles_malformed_pyproject(self, temp_project, code_analysis):
        """Test graceful handling of malformed pyproject.toml."""
        # Write invalid TOML
        pyproject_path = temp_project / "pyproject.toml"
        pyproject_path.write_text("invalid toml content [[[")
        
        detector = DriftDetector(temp_project)
        existing_files = {'tech-stack.md': "Python 3.10"}
        
        # Should not crash
        drift_item = detector._detect_language_version_drift(existing_files, code_analysis)
        assert drift_item is None
    
    def test_handles_missing_project_section(self, temp_project, code_analysis):
        """Test graceful handling when project section is missing."""
        # Write TOML without project section
        pyproject_path = temp_project / "pyproject.toml"
        pyproject_path.write_text("[tool.poetry]\nname = 'test'")
        
        detector = DriftDetector(temp_project)
        existing_files = {'tech-stack.md': "Python 3.10"}
        
        # Should not crash
        drift_item = detector._detect_language_version_drift(existing_files, code_analysis)
        assert drift_item is None
    
    def test_handles_missing_dependencies_section(self, temp_project, code_analysis):
        """Test graceful handling when dependencies section is missing."""
        # Write TOML without dependencies
        pyproject_path = temp_project / "pyproject.toml"
        pyproject_path.write_text("[project]\nname = 'test'")
        
        detector = DriftDetector(temp_project)
        dependencies = detector._extract_current_dependencies()
        
        assert dependencies == []
