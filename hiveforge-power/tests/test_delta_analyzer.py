"""
Unit tests for DeltaAnalyzer.

Tests technology mismatch detection, dependency change detection,
and design-doc-wins-on-conflict behavior.

Requirements: 7.1, 7.4, 7.5
"""

import pytest
from pathlib import Path

from hiveforge.steering.delta_analyzer import DeltaAnalyzer
from hiveforge.steering.models import (
    CodeAnalysisFacts,
    DeltaReport,
    Dependency,
    NamingConventions,
    ParsedDocument,
)


class TestDeltaAnalyzer:
    """Unit tests for DeltaAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DeltaAnalyzer()
    
    # ------------------------------------------------------------------
    # Technology mismatch detection tests (Requirement 7.1)
    # ------------------------------------------------------------------
    
    def test_database_mismatch_docs_vs_code(self):
        """
        Test that database mismatches between docs and code are detected.
        
        Requirement: 7.1
        """
        # Design docs mention PostgreSQL
        source_docs = [
            ParsedDocument(
                file_path=Path("design.md"),
                content="We use PostgreSQL as our primary database.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        # Code uses MySQL
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["Django"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="MySQL",
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        existing_steering = {}
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect mismatch in doc_vs_code
        assert len(report.doc_vs_code) > 0
        assert any("database" in msg.lower() for msg in report.doc_vs_code)
        assert any("postgresql" in msg.lower() for msg in report.doc_vs_code)
    
    def test_framework_mismatch_docs_vs_code(self):
        """
        Test that framework mismatches between docs and code are detected.
        
        Requirement: 7.1
        """
        # Design docs mention Flask
        source_docs = [
            ParsedDocument(
                file_path=Path("architecture.md"),
                content="Built with Flask web framework for simplicity.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        # Code uses FastAPI
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        existing_steering = {}
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect framework mismatch
        assert len(report.doc_vs_code) > 0
        assert any("framework" in msg.lower() for msg in report.doc_vs_code)
    
    def test_language_mismatch_docs_vs_code(self):
        """
        Test that language mismatches between docs and code are detected.
        
        Requirement: 7.1
        """
        # Design docs mention TypeScript
        source_docs = [
            ParsedDocument(
                file_path=Path("tech-stack.md"),
                content="Primary language: TypeScript for type safety.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        # Code is Python
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src",
        )
        
        existing_steering = {}
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect language mismatch
        assert len(report.doc_vs_code) > 0
        assert any("language" in msg.lower() for msg in report.doc_vs_code)
    
    # ------------------------------------------------------------------
    # Dependency change detection tests (Requirement 7.4)
    # ------------------------------------------------------------------
    
    def test_dependency_added_in_code(self):
        """
        Test detection of dependencies in code not mentioned in docs.
        
        Requirement: 7.4
        """
        # Design docs don't mention FastAPI
        source_docs = [
            ParsedDocument(
                file_path=Path("requirements.md"),
                content="Basic Python CLI tool.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        # Code uses FastAPI
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[
                Dependency(name="fastapi", version="0.100.0"),
            ],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        existing_steering = {}
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect framework in code not in docs
        assert len(report.doc_vs_code) > 0
        assert any("fastapi" in msg.lower() for msg in report.doc_vs_code)
    
    def test_steering_drift_new_framework(self):
        """
        Test detection of new frameworks in code not yet in steering files.
        
        Requirement: 7.4
        """
        source_docs = []
        
        # Code uses FastAPI
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        # Steering files mention Flask (outdated)
        existing_steering = {
            "tech-stack.md": "Backend: Flask web framework"
        }
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect drift in steering_vs_code
        assert len(report.steering_vs_code) > 0
        assert any("fastapi" in msg.lower() for msg in report.steering_vs_code)
    
    def test_steering_drift_removed_framework(self):
        """
        Test detection of frameworks in steering files no longer in code.
        
        Requirement: 7.4
        """
        source_docs = []
        
        # Code uses FastAPI only
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        # Steering files mention both Flask and FastAPI
        existing_steering = {
            "tech-stack.md": "Backend: Flask and FastAPI frameworks"
        }
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect stale framework reference
        assert len(report.steering_vs_code) > 0
        assert any("flask" in msg.lower() for msg in report.steering_vs_code)
    
    # ------------------------------------------------------------------
    # Design-doc-wins-on-conflict tests (Requirement 7.5)
    # ------------------------------------------------------------------
    
    def test_design_docs_take_precedence_over_code(self):
        """
        Test that when docs and code diverge, docs are treated as source of truth.
        
        Requirement: 7.5
        """
        # Design docs specify PostgreSQL
        source_docs = [
            ParsedDocument(
                file_path=Path("design.md"),
                content="Database: PostgreSQL for ACID compliance.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        # Code currently uses SQLite
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["Django"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="SQLite",
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        existing_steering = {}
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should report divergence with note that design docs take precedence
        assert len(report.doc_vs_code) > 0
        divergence_msg = " ".join(report.doc_vs_code).lower()
        assert "postgresql" in divergence_msg
        assert "precedence" in divergence_msg or "design docs" in divergence_msg
    
    def test_steering_vs_docs_conflict_docs_win(self):
        """
        Test that conflicts between steering and docs favor design docs.
        
        Requirement: 7.5
        """
        # Design docs specify MongoDB
        source_docs = [
            ParsedDocument(
                file_path=Path("architecture.md"),
                content="We use MongoDB for flexible schema.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        # Code facts (neutral)
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src",
        )
        
        # Steering files mention PostgreSQL (conflict)
        existing_steering = {
            "tech-stack.md": "Database: PostgreSQL"
        }
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect conflict in steering_vs_docs
        assert len(report.steering_vs_docs) > 0
        conflict_msg = " ".join(report.steering_vs_docs).lower()
        assert "precedence" in conflict_msg or "design docs" in conflict_msg
    
    # ------------------------------------------------------------------
    # Missing information detection tests
    # ------------------------------------------------------------------
    
    def test_missing_database_in_all_sources(self):
        """Test detection of database missing from all sources."""
        source_docs = [
            ParsedDocument(
                file_path=Path("readme.md"),
                content="A simple CLI tool.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type="CLI",
            database=None,  # No database
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src",
        )
        
        existing_steering = {}
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect missing database
        assert len(report.missing_in_all) > 0
        assert any("database" in msg.lower() for msg in report.missing_in_all)
    
    def test_missing_testing_strategy_in_all_sources(self):
        """Test detection of testing strategy missing from all sources."""
        source_docs = [
            ParsedDocument(
                file_path=Path("readme.md"),
                content="A web application.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["Flask"],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=False,  # No tests
            test_framework=None,
            api_type="REST",
            database="SQLite",
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src",
        )
        
        existing_steering = {
            "tech-stack.md": "Backend: Flask"
        }
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect missing testing strategy
        assert len(report.missing_in_all) > 0
        assert any("test" in msg.lower() for msg in report.missing_in_all)
    
    def test_missing_architecture_pattern_in_all_sources(self):
        """Test detection of architecture pattern missing from all sources."""
        source_docs = [
            ParsedDocument(
                file_path=Path("readme.md"),
                content="A Python application.",
                metadata={},
                parse_errors=[],
            )
        ]
        
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",  # No clear pattern
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src",
        )
        
        existing_steering = {}
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should detect missing architecture pattern
        assert len(report.missing_in_all) > 0
        assert any("architecture" in msg.lower() for msg in report.missing_in_all)
    
    # ------------------------------------------------------------------
    # Edge cases and empty inputs
    # ------------------------------------------------------------------
    
    def test_empty_inputs_returns_empty_report(self):
        """Test that empty inputs produce an empty report."""
        source_docs = []
        
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="custom",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="",
        )
        
        existing_steering = {}
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Report should exist but may have missing_in_all entries
        assert isinstance(report, DeltaReport)
        assert isinstance(report.doc_vs_code, list)
        assert isinstance(report.steering_vs_code, list)
        assert isinstance(report.steering_vs_docs, list)
        assert isinstance(report.missing_in_all, list)
    
    def test_matching_sources_no_divergences(self):
        """Test that matching sources produce no divergences."""
        # All sources agree on PostgreSQL
        source_docs = [
            ParsedDocument(
                file_path=Path("design.md"),
                content="Database: PostgreSQL",
                metadata={},
                parse_errors=[],
            )
        ]
        
        code_facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=[],
            dependencies=[],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type=None,
            database="PostgreSQL",
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="src, tests",
        )
        
        existing_steering = {
            "tech-stack.md": "Database: PostgreSQL"
        }
        
        report = self.analyzer.analyze(source_docs, code_facts, existing_steering)
        
        # Should have no divergences (but may have missing_in_all)
        assert len(report.doc_vs_code) == 0
        assert len(report.steering_vs_code) == 0
        assert len(report.steering_vs_docs) == 0
