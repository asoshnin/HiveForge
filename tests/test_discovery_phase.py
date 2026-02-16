"""
Property-based tests for discovery phase.

Validates: Requirements 2.1-2.10
"""

import tempfile
from pathlib import Path
from typing import List

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.analyzers.documentation_searcher import DocumentationSearcher
from hiveforge.steering.parsers.orchestrator import DiscoveryOrchestrator


class TestDiscoveryCompleteness:
    """Tests for discovery phase completeness."""
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_readme_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for documentation files (README*).
        """
        # Create test README files
        (tmp_path / "README.md").write_text("# Test Project")
        (tmp_path / "README.txt").write_text("Test Project")
        (tmp_path / "README").write_text("Test Project")
        
        searcher = DocumentationSearcher(max_files=100)
        docs_files = searcher.search_docs_files(tmp_path)
        
        assert len(docs_files) >= 3
        assert any(f.name == "README.md" for f in docs_files)
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_contributing_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for CONTRIBUTING* files.
        """
        (tmp_path / "CONTRIBUTING.md").write_text("# Contributing")
        
        searcher = DocumentationSearcher(max_files=100)
        docs_files = searcher.search_docs_files(tmp_path)
        
        assert any(f.name == "CONTRIBUTING.md" for f in docs_files)
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_architecture_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for ARCHITECTURE* files.
        """
        (tmp_path / "ARCHITECTURE.md").write_text("# Architecture")
        
        searcher = DocumentationSearcher(max_files=100)
        docs_files = searcher.search_docs_files(tmp_path)
        
        assert any(f.name == "ARCHITECTURE.md" for f in docs_files)
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_design_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for DESIGN* files.
        """
        (tmp_path / "DESIGN.md").write_text("# Design")
        
        searcher = DocumentationSearcher(max_files=100)
        docs_files = searcher.search_docs_files(tmp_path)
        
        assert any(f.name == "DESIGN.md" for f in docs_files)
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_spec_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for SPEC* files.
        """
        (tmp_path / "SPEC.md").write_text("# Specification")
        
        searcher = DocumentationSearcher(max_files=100)
        docs_files = searcher.search_docs_files(tmp_path)
        
        assert any(f.name == "SPEC.md" for f in docs_files)
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_requirements_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for REQUIREMENTS* files.
        """
        (tmp_path / "REQUIREMENTS.md").write_text("# Requirements")
        
        searcher = DocumentationSearcher(max_files=100)
        docs_files = searcher.search_docs_files(tmp_path)
        
        assert any(f.name == "REQUIREMENTS.md" for f in docs_files)
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_docs_directories(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search documentation directories (docs/, etc.).
        """
        # Create docs directories with files
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "api.md").write_text("# API")
        
        (tmp_path / "documentation").mkdir()
        (tmp_path / "documentation" / "readme.md").write_text("# Documentation")
        
        (tmp_path / "design").mkdir()
        (tmp_path / "design" / "diagram.md").write_text("# Diagram")
        
        searcher = DocumentationSearcher(max_files=100)
        docs_dirs = searcher.search_docs_dirs(tmp_path)
        
        assert len(docs_dirs) >= 3
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_package_metadata_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for package metadata files.
        """
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"')
        
        searcher = DocumentationSearcher(max_files=100)
        package_files = searcher.search_package_files(tmp_path)
        
        assert len(package_files) >= 2
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_ci_cd_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for CI/CD configuration files.
        """
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github" / "workflows").mkdir()
        (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: CI")
        
        (tmp_path / ".gitlab-ci.yml").write_text("stages: [build]")
        
        searcher = DocumentationSearcher(max_files=100)
        config_files = searcher.search_config_files(tmp_path)
        
        # Should find at least one config file
        assert len(config_files) >= 1
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_finds_deployment_files(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL search for deployment manifests.
        """
        (tmp_path / "Dockerfile").write_text("FROM python:3.11")
        (tmp_path / "docker-compose.yml").write_text("version: '3'")
        
        searcher = DocumentationSearcher(max_files=100)
        config_files = searcher.search_config_files(tmp_path)
        
        assert len(config_files) >= 2
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_file_size_filtering(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL implement file size filtering.
        """
        # Create small documentation file
        small_file = tmp_path / "README_small.txt"
        small_file.write_text("small content")
        
        # Create large file (11 MB)
        large_file = tmp_path / "README_large.txt"
        large_file.write_text("x" * (11 * 1024 * 1024))
        
        searcher = DocumentationSearcher(max_file_size_mb=10, max_files=100)
        all_files, _ = searcher.discover_all(tmp_path)
        
        # Large file should be filtered out
        assert large_file not in all_files
        # Small file should be included
        assert small_file in all_files
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_file_count_limiting(self, tmp_path: Path):
        """
        WHEN the discovery phase runs, the system SHALL implement file count limiting.
        """
        # Create 10 files
        for i in range(10):
            (tmp_path / f"file{i}.txt").write_text(f"content {i}")
        
        searcher = DocumentationSearcher(max_files=5, max_file_size_mb=100)
        all_files, count = searcher.discover_all(tmp_path)
        
        # Should be limited to max_files
        assert count <= 5
        assert len(all_files) <= 5
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    def test_discovery_orchestrator_integration(self, tmp_path: Path):
        """
        WHEN DiscoveryOrchestrator.discover_all is called, it should run all discovery methods.
        """
        # Create various files
        (tmp_path / "README.md").write_text("# Test")
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / ".github").mkdir()
        (tmp_path / ".github" / "workflows").mkdir()
        (tmp_path / ".github" / "workflows" / "ci.yml").write_text("name: CI")
        
        orchestrator = DiscoveryOrchestrator(max_discovery_files=100)
        discovered_files, metadata = orchestrator.discover_all(tmp_path)
        
        # Should have found files
        assert len(discovered_files) >= 3
        assert metadata["file_count"] >= 3
    
    @pytest.mark.property("Property 2: Discovery Completeness")
    @given(st.integers(min_value=1, max_value=100))
    def test_discovery_with_various_limits(self, max_files: int):
        """
        Property: Discovery Completeness
        For any max_files limit, discovery should respect the limit.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create more files than the limit
            for i in range(max_files * 2):
                (tmp_path / f"file{i}.txt").write_text(f"content {i}")
            
            searcher = DocumentationSearcher(max_files=max_files, max_file_size_mb=100)
            all_files, count = searcher.discover_all(tmp_path)
            
            # Should respect the limit
            assert count <= max_files
            assert len(all_files) <= max_files
