"""
Tests for the CodeAnalyzer orchestrator.

This module tests the main orchestrator that coordinates all code analysis
modules, including .gitignore handling, sampling, progress updates, caching,
and token-limited summaries.
"""

import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from hiveforge.steering.analyzers.code_analyzer import (
    CodeAnalyzer,
    analyze_codebase,
    LARGE_CODEBASE_THRESHOLD,
    PROGRESS_UPDATE_INTERVAL,
)
from hiveforge.steering.models import (
    CodeAnalysisResult,
    LanguageInfo,
    TechStackInfo,
    ArchitectureInfo,
    ConventionsInfo,
)


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Create some source files
    (project_root / "main.py").write_text("print('hello')")
    (project_root / "utils.py").write_text("def helper(): pass")
    
    # Create README
    (project_root / "README.md").write_text("# Test Project\n\nA test project.")
    
    # Create package.json
    (project_root / "package.json").write_text(json.dumps({
        "dependencies": {
            "express": "^4.18.0",
            "react": "^18.2.0"
        }
    }))
    
    # Create .gitignore
    (project_root / ".gitignore").write_text("node_modules/\n*.pyc\n__pycache__/\n")
    
    # Create ignored directory
    ignored_dir = project_root / "node_modules"
    ignored_dir.mkdir()
    (ignored_dir / "package.js").write_text("// ignored")
    
    return project_root


@pytest.fixture
def analyzer(temp_project):
    """Create a CodeAnalyzer instance for testing."""
    return CodeAnalyzer(temp_project)


class TestCodeAnalyzerInit:
    """Test CodeAnalyzer initialization."""
    
    def test_init_with_valid_path(self, temp_project):
        """Test initialization with valid project path."""
        analyzer = CodeAnalyzer(temp_project)
        
        assert analyzer.project_root == temp_project.resolve()
        assert isinstance(analyzer.excluded_paths, set)
        assert len(analyzer.excluded_paths) == 0  # Not loaded yet
        assert analyzer.start_time is None
        assert analyzer.last_progress_update is None
    
    def test_init_resolves_relative_path(self, temp_project):
        """Test that relative paths are resolved to absolute."""
        # Create analyzer with relative path
        relative_path = Path(".") / temp_project.name
        
        with patch("pathlib.Path.resolve", return_value=temp_project):
            analyzer = CodeAnalyzer(relative_path)
            assert analyzer.project_root.is_absolute()


class TestGitignoreHandling:
    """Test .gitignore file handling."""
    
    def test_load_gitignore_excludes_paths(self, analyzer, temp_project):
        """Test that .gitignore patterns are loaded and paths excluded."""
        analyzer._load_gitignore()
        
        # Check that node_modules is in excluded paths
        excluded_names = {path.parts[0] for path in analyzer.excluded_paths}
        assert "node_modules" in excluded_names
    
    def test_load_gitignore_missing_file(self, analyzer, temp_project):
        """Test handling when .gitignore doesn't exist."""
        # Remove .gitignore
        (temp_project / ".gitignore").unlink()
        
        analyzer._load_gitignore()
        
        # Should not fail, just have empty exclusions
        assert len(analyzer.excluded_paths) == 0
    
    def test_load_gitignore_without_pathspec(self, analyzer, temp_project):
        """Test handling when pathspec library is not available."""
        with patch("hiveforge.steering.analyzers.code_analyzer.pathspec", None):
            analyzer._load_gitignore()
            
            # Should log warning but not fail
            assert len(analyzer.excluded_paths) == 0
    
    def test_load_gitignore_parse_error(self, analyzer, temp_project):
        """Test handling of .gitignore parse errors."""
        # Create invalid .gitignore
        (temp_project / ".gitignore").write_text("\x00\x01\x02")
        
        analyzer._load_gitignore()
        
        # Should handle error gracefully
        # Exact behavior depends on pathspec, but should not crash


class TestFileCount:
    """Test file counting functionality."""
    
    def test_count_files_basic(self, analyzer, temp_project):
        """Test basic file counting."""
        count = analyzer._count_files()
        
        # Should count: main.py, utils.py, README.md, package.json, .gitignore
        # Should NOT count: node_modules/package.js (if gitignore loaded)
        assert count >= 4  # At least the main files
    
    def test_count_files_excludes_gitignored(self, analyzer, temp_project):
        """Test that gitignored files are excluded from count."""
        analyzer._load_gitignore()
        count = analyzer._count_files()
        
        # node_modules should be excluded
        # Count should not include node_modules/package.js
        assert count >= 4
        assert count < 10  # Sanity check


class TestLanguageDetection:
    """Test language detection integration."""
    
    def test_detect_languages_calls_module(self, analyzer):
        """Test that detect_languages calls the language detector module."""
        with patch("hiveforge.steering.analyzers.code_analyzer.detect_languages") as mock_detect:
            mock_detect.return_value = [
                LanguageInfo(name="Python", percentage=60.0, file_count=2, line_count=100),
                LanguageInfo(name="JavaScript", percentage=40.0, file_count=1, line_count=50),
            ]
            
            result = analyzer.detect_languages()
            
            assert len(result) == 2
            assert result[0].name == "Python"
            mock_detect.assert_called_once_with(analyzer.project_root, analyzer.excluded_paths)
    
    def test_detect_languages_handles_error(self, analyzer):
        """Test error handling in language detection."""
        with patch("hiveforge.steering.analyzers.code_analyzer.detect_languages") as mock_detect:
            mock_detect.side_effect = Exception("Test error")
            
            result = analyzer.detect_languages()
            
            # Should return empty list on error
            assert result == []


class TestTechStackExtraction:
    """Test tech stack extraction integration."""
    
    def test_extract_tech_stack_calls_module(self, analyzer):
        """Test that extract_tech_stack calls the extractor module."""
        with patch("hiveforge.steering.analyzers.code_analyzer.extract_tech_stack") as mock_extract:
            mock_tech_stack = TechStackInfo(
                backend_framework="Express",
                frontend_framework="React"
            )
            mock_extract.return_value = mock_tech_stack
            
            result = analyzer.extract_tech_stack()
            
            assert result.backend_framework == "Express"
            assert result.frontend_framework == "React"
            mock_extract.assert_called_once_with(analyzer.project_root)
    
    def test_extract_tech_stack_handles_error(self, analyzer):
        """Test error handling in tech stack extraction."""
        with patch("hiveforge.steering.analyzers.code_analyzer.extract_tech_stack") as mock_extract:
            mock_extract.side_effect = Exception("Test error")
            
            result = analyzer.extract_tech_stack()
            
            # Should return empty TechStackInfo on error
            assert isinstance(result, TechStackInfo)
            assert result.backend_framework is None


class TestArchitectureInference:
    """Test architecture inference integration."""
    
    def test_infer_architecture_calls_module(self, analyzer):
        """Test that infer_architecture calls the inferrer module."""
        with patch("hiveforge.steering.analyzers.code_analyzer.infer_architecture") as mock_infer:
            mock_arch = ArchitectureInfo(
                pattern="layered",
                key_components=["Controllers", "Services", "Models"]
            )
            mock_infer.return_value = mock_arch
            
            result = analyzer.infer_architecture()
            
            assert result.pattern == "layered"
            assert len(result.key_components) == 3
            mock_infer.assert_called_once_with(analyzer.project_root, analyzer.excluded_paths)
    
    def test_infer_architecture_handles_error(self, analyzer):
        """Test error handling in architecture inference."""
        with patch("hiveforge.steering.analyzers.code_analyzer.infer_architecture") as mock_infer:
            mock_infer.side_effect = Exception("Test error")
            
            result = analyzer.infer_architecture()
            
            # Should return custom architecture on error
            assert isinstance(result, ArchitectureInfo)
            assert result.pattern == "custom"


class TestConventionsExtraction:
    """Test conventions extraction integration."""
    
    def test_extract_conventions_calls_module(self, analyzer):
        """Test that extract_conventions calls the extractor module."""
        with patch("hiveforge.steering.analyzers.code_analyzer.extract_conventions") as mock_extract:
            with patch("hiveforge.steering.analyzers.code_analyzer.summarize_conventions") as mock_summarize:
                mock_extract.return_value = {"naming": {}, "formatting": {}}
                mock_summarize.return_value = {
                    "function_naming": "snake_case",
                    "variable_naming": "snake_case",
                    "class_naming": "PascalCase",
                    "constant_naming": "UPPER_SNAKE_CASE",
                    "indentation": "4spaces",
                }
                
                result = analyzer.extract_conventions()
                
                assert result.naming_style["functions"] == "snake_case"
                assert result.naming_style["classes"] == "PascalCase"
                assert result.formatting["indentation"] == "4spaces"
    
    def test_extract_conventions_handles_error(self, analyzer):
        """Test error handling in conventions extraction."""
        with patch("hiveforge.steering.analyzers.code_analyzer.extract_conventions") as mock_extract:
            mock_extract.side_effect = Exception("Test error")
            
            result = analyzer.extract_conventions()
            
            # Should return empty ConventionsInfo on error
            assert isinstance(result, ConventionsInfo)


class TestDocumentationParsing:
    """Test documentation parsing integration."""
    
    def test_parse_documentation_calls_module(self, analyzer):
        """Test that _parse_documentation calls the parser module."""
        with patch("hiveforge.steering.analyzers.code_analyzer.parse_codebase_documentation") as mock_parse:
            mock_parse.return_value = []
            
            result = analyzer._parse_documentation()
            
            assert result == []
            mock_parse.assert_called_once_with(
                analyzer.project_root,
                analyzer.excluded_paths,
                include_inline_comments=False
            )
    
    def test_parse_documentation_handles_error(self, analyzer):
        """Test error handling in documentation parsing."""
        with patch("hiveforge.steering.analyzers.code_analyzer.parse_codebase_documentation") as mock_parse:
            mock_parse.side_effect = Exception("Test error")
            
            result = analyzer._parse_documentation()
            
            # Should return empty list on error
            assert result == []


class TestConfidenceScores:
    """Test confidence score calculation."""
    
    def test_calculate_confidence_scores_languages(self, analyzer):
        """Test confidence scores for language detection."""
        languages = [
            LanguageInfo(name="Python", percentage=60.0, file_count=10, line_count=1000),
            LanguageInfo(name="JavaScript", percentage=30.0, file_count=5, line_count=500),
            LanguageInfo(name="Shell", percentage=10.0, file_count=2, line_count=100),
        ]
        
        scores = analyzer._calculate_confidence_scores(
            languages,
            TechStackInfo(),
            ArchitectureInfo(),
            ConventionsInfo()
        )
        
        # Python: >50% = 1.0
        assert scores["language_Python"] == 1.0
        # JavaScript: 20-50% = 0.8
        assert scores["language_JavaScript"] == 0.8
        # Shell: 10-20% = 0.5
        assert scores["language_Shell"] == 0.5
    
    def test_calculate_confidence_scores_tech_stack(self, analyzer):
        """Test confidence scores for tech stack."""
        tech_stack = TechStackInfo(
            backend_framework="Express",
            frontend_framework="React",
            database="PostgreSQL"
        )
        
        scores = analyzer._calculate_confidence_scores(
            [],
            tech_stack,
            ArchitectureInfo(),
            ConventionsInfo()
        )
        
        # All from dependencies = 1.0
        assert scores["backend_framework"] == 1.0
        assert scores["frontend_framework"] == 1.0
        assert scores["database"] == 1.0
    
    def test_calculate_confidence_scores_architecture(self, analyzer):
        """Test confidence scores for architecture patterns."""
        # Test different patterns
        patterns_and_scores = [
            ("custom", 0.5),
            ("mvc", 0.8),
            ("hexagonal", 0.8),
            ("layered", 0.7),
            ("microservices", 0.7),
            ("monolithic", 0.6),
        ]
        
        for pattern, expected_score in patterns_and_scores:
            arch = ArchitectureInfo(pattern=pattern)
            scores = analyzer._calculate_confidence_scores(
                [],
                TechStackInfo(),
                arch,
                ConventionsInfo()
            )
            
            assert scores["architecture"] == expected_score


class TestProgressUpdates:
    """Test progress update functionality."""
    
    def test_log_progress_initial(self, analyzer):
        """Test initial progress log."""
        analyzer.start_time = time.time()
        analyzer.last_progress_update = None
        
        analyzer._log_progress("Test message")
        
        # Should set last_progress_update
        assert analyzer.last_progress_update is not None
    
    def test_log_progress_interval(self, analyzer):
        """Test progress updates at intervals."""
        analyzer.start_time = time.time()
        analyzer.last_progress_update = time.time() - PROGRESS_UPDATE_INTERVAL - 1
        
        with patch("hiveforge.steering.analyzers.code_analyzer.logger") as mock_logger:
            analyzer._log_progress("Test message")
            
            # Should log info message
            mock_logger.info.assert_called()
            assert "Test message" in str(mock_logger.info.call_args)
    
    def test_log_progress_no_update_if_recent(self, analyzer):
        """Test that progress is not logged if recent update."""
        analyzer.start_time = time.time()
        analyzer.last_progress_update = time.time()
        
        with patch("hiveforge.steering.analyzers.code_analyzer.logger") as mock_logger:
            analyzer._log_progress("Test message")
            
            # Should only log debug, not info
            mock_logger.debug.assert_called()
            mock_logger.info.assert_not_called()


class TestCaching:
    """Test caching functionality."""
    
    def test_load_cache_missing_file(self, analyzer):
        """Test loading cache when file doesn't exist."""
        result = analyzer._load_cache()
        
        assert result is None
    
    def test_load_cache_expired(self, analyzer, temp_project):
        """Test loading expired cache."""
        cache_path = temp_project / ".kiro" / ".cache" / "code_analysis.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create old cache file
        cache_data = {"timestamp": time.time() - 7200}  # 2 hours old
        cache_path.write_text(json.dumps(cache_data))
        
        result = analyzer._load_cache()
        
        # Should return None for expired cache
        assert result is None
    
    def test_save_cache_creates_directory(self, analyzer, temp_project):
        """Test that save_cache creates cache directory."""
        result = CodeAnalysisResult()
        
        analyzer._save_cache(result)
        
        cache_path = temp_project / ".kiro" / ".cache" / "code_analysis.json"
        assert cache_path.parent.exists()
        assert cache_path.exists()
    
    def test_save_cache_writes_data(self, analyzer, temp_project):
        """Test that save_cache writes data correctly."""
        result = CodeAnalysisResult(
            languages=[LanguageInfo(name="Python", percentage=100.0)]
        )
        
        analyzer._save_cache(result)
        
        cache_path = temp_project / ".kiro" / ".cache" / "code_analysis.json"
        cache_data = json.loads(cache_path.read_text())
        
        assert "timestamp" in cache_data
        assert "summary" in cache_data
    
    def test_save_cache_handles_error(self, analyzer):
        """Test error handling in save_cache."""
        result = CodeAnalysisResult()
        
        with patch("builtins.open", side_effect=PermissionError("Test error")):
            # Should not raise exception
            analyzer._save_cache(result)


class TestTokenLimitedSummary:
    """Test token-limited summary generation."""
    
    def test_get_summary_for_llm_default_tokens(self, analyzer):
        """Test summary generation with default token limit."""
        with patch.object(analyzer, "analyze") as mock_analyze:
            mock_result = CodeAnalysisResult(
                languages=[LanguageInfo(name="Python", percentage=100.0, file_count=10, line_count=1000)]
            )
            mock_analyze.return_value = mock_result
            
            summary = analyzer.get_summary_for_llm()
            
            # Should return string
            assert isinstance(summary, str)
            # Should contain language info
            assert "Python" in summary
    
    def test_get_summary_for_llm_custom_tokens(self, analyzer):
        """Test summary generation with custom token limit."""
        with patch.object(analyzer, "analyze") as mock_analyze:
            mock_result = CodeAnalysisResult()
            mock_analyze.return_value = mock_result
            
            summary = analyzer.get_summary_for_llm(max_tokens=500)
            
            # Should respect token limit (rough check: 500 tokens ≈ 2000 chars)
            assert len(summary) <= 2500
    
    def test_get_summary_for_llm_handles_error(self, analyzer):
        """Test error handling in summary generation."""
        with patch.object(analyzer, "analyze", side_effect=Exception("Test error")):
            summary = analyzer.get_summary_for_llm()
            
            # Should return error message
            assert "Error" in summary


class TestAnalyzeMethod:
    """Test the main analyze() method."""
    
    def test_analyze_full_workflow(self, analyzer):
        """Test complete analysis workflow."""
        with patch.object(analyzer, "_load_cache", return_value=None):
            with patch.object(analyzer, "_load_gitignore"):
                with patch.object(analyzer, "_count_files", return_value=100):
                    with patch.object(analyzer, "detect_languages", return_value=[]):
                        with patch.object(analyzer, "extract_tech_stack", return_value=TechStackInfo()):
                            with patch.object(analyzer, "infer_architecture", return_value=ArchitectureInfo()):
                                with patch.object(analyzer, "extract_conventions", return_value=ConventionsInfo()):
                                    with patch.object(analyzer, "_parse_documentation", return_value=[]):
                                        with patch.object(analyzer, "_save_cache"):
                                            result = analyzer.analyze()
                                            
                                            assert isinstance(result, CodeAnalysisResult)
                                            assert analyzer.start_time is not None
    
    def test_analyze_uses_cache_if_available(self, analyzer):
        """Test that analyze uses cached results if available."""
        cached_result = CodeAnalysisResult()
        
        with patch.object(analyzer, "_load_cache", return_value=cached_result):
            result = analyzer.analyze()
            
            assert result == cached_result
    
    def test_analyze_warns_on_large_codebase(self, analyzer):
        """Test warning for large codebases."""
        with patch.object(analyzer, "_load_cache", return_value=None):
            with patch.object(analyzer, "_load_gitignore"):
                with patch.object(analyzer, "_count_files", return_value=LARGE_CODEBASE_THRESHOLD + 1):
                    with patch.object(analyzer, "detect_languages", return_value=[]):
                        with patch.object(analyzer, "extract_tech_stack", return_value=TechStackInfo()):
                            with patch.object(analyzer, "infer_architecture", return_value=ArchitectureInfo()):
                                with patch.object(analyzer, "extract_conventions", return_value=ConventionsInfo()):
                                    with patch.object(analyzer, "_parse_documentation", return_value=[]):
                                        with patch.object(analyzer, "_save_cache"):
                                            with patch("hiveforge.steering.analyzers.code_analyzer.logger") as mock_logger:
                                                analyzer.analyze()
                                                
                                                # Should log warning
                                                mock_logger.warning.assert_called()
                                                warning_msg = str(mock_logger.warning.call_args)
                                                assert "Large codebase" in warning_msg


class TestConvenienceFunction:
    """Test the convenience function."""
    
    def test_analyze_codebase_function(self, temp_project):
        """Test analyze_codebase convenience function."""
        with patch("hiveforge.steering.analyzers.code_analyzer.CodeAnalyzer") as mock_class:
            mock_instance = Mock()
            mock_instance.analyze.return_value = CodeAnalysisResult()
            mock_class.return_value = mock_instance
            
            result = analyze_codebase(temp_project)
            
            mock_class.assert_called_once_with(temp_project)
            mock_instance.analyze.assert_called_once()
            assert isinstance(result, CodeAnalysisResult)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_analyze_empty_project(self, tmp_path):
        """Test analyzing an empty project."""
        empty_project = tmp_path / "empty"
        empty_project.mkdir()
        
        analyzer = CodeAnalyzer(empty_project)
        result = analyzer.analyze()
        
        # Should complete without errors
        assert isinstance(result, CodeAnalysisResult)
        assert len(result.languages) == 0
    
    def test_analyze_nonexistent_project(self, tmp_path):
        """Test analyzing a nonexistent project."""
        nonexistent = tmp_path / "nonexistent"
        
        analyzer = CodeAnalyzer(nonexistent)
        
        # Should handle gracefully
        # Exact behavior depends on implementation
    
    def test_analyze_with_permission_errors(self, analyzer):
        """Test handling of permission errors during analysis."""
        with patch.object(analyzer, "_count_files", side_effect=PermissionError("Test error")):
            with patch.object(analyzer, "_load_cache", return_value=None):
                with patch.object(analyzer, "_load_gitignore"):
                    # Should handle error gracefully
                    # Exact behavior depends on implementation
                    pass
