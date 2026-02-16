"""
Tests for language detection module.

This module tests the language detection functionality to ensure it correctly
identifies programming languages, counts files and lines, detects versions,
and assigns confidence scores.
"""

import pytest
from pathlib import Path

from src.hiveforge.steering.analyzers.language_detector import (
    detect_languages,
    get_language_confidence_score,
    check_language_markers,
    _count_lines_in_file,
    _detect_language_from_shebang,
)
from src.hiveforge.steering.models import LanguageInfo


def create_source_file(file_path: Path, content: str, lines: int = None):
    """Helper to create a source file with content."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if lines:
        # Create file with specified number of lines
        content = '\n'.join([f"line {i}" for i in range(lines)])
    file_path.write_text(content, encoding='utf-8')


class TestDetectLanguages:
    """Tests for detect_languages function."""
    
    def test_detect_single_language(self, tmp_path):
        """Should detect a single language."""
        # Create Python files
        create_source_file(tmp_path / "main.py", "print('hello')", lines=10)
        create_source_file(tmp_path / "utils.py", "def helper(): pass", lines=5)
        
        result = detect_languages(tmp_path)
        
        assert len(result) == 1
        assert result[0].name == "Python"
        assert result[0].file_count == 2
        assert result[0].line_count == 15
        assert result[0].percentage == 100.0
    
    def test_detect_multiple_languages(self, tmp_path):
        """Should detect multiple languages with correct percentages."""
        # Create Python files (60 lines)
        create_source_file(tmp_path / "main.py", "", lines=40)
        create_source_file(tmp_path / "utils.py", "", lines=20)
        
        # Create JavaScript files (40 lines)
        create_source_file(tmp_path / "app.js", "", lines=30)
        create_source_file(tmp_path / "helper.js", "", lines=10)
        
        result = detect_languages(tmp_path)
        
        assert len(result) == 2
        # Should be sorted by percentage (descending)
        assert result[0].name == "Python"
        assert result[0].percentage == 60.0
        assert result[1].name == "JavaScript"
        assert result[1].percentage == 40.0
    
    def test_detect_languages_in_subdirectories(self, tmp_path):
        """Should detect languages in subdirectories."""
        # Create files in subdirectories
        create_source_file(tmp_path / "src" / "main.py", "", lines=10)
        create_source_file(tmp_path / "tests" / "test_main.py", "", lines=5)
        create_source_file(tmp_path / "lib" / "utils.py", "", lines=3)
        
        result = detect_languages(tmp_path)
        
        assert len(result) == 1
        assert result[0].name == "Python"
        assert result[0].file_count == 3
        assert result[0].line_count == 18
    
    def test_detect_languages_with_exclusions(self, tmp_path):
        """Should exclude specified paths from detection."""
        # Create files
        create_source_file(tmp_path / "src" / "main.py", "", lines=10)
        create_source_file(tmp_path / "node_modules" / "lib.js", "", lines=100)
        
        # Exclude node_modules
        excluded = {Path("node_modules")}
        result = detect_languages(tmp_path, excluded_paths=excluded)
        
        # Should only detect Python, not JavaScript
        assert len(result) == 1
        assert result[0].name == "Python"
    
    def test_detect_empty_directory(self, tmp_path):
        """Should return empty list for directory with no source files."""
        result = detect_languages(tmp_path)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_detect_languages_with_various_extensions(self, tmp_path):
        """Should detect languages by various file extensions."""
        # Python
        create_source_file(tmp_path / "script.py", "", lines=10)
        create_source_file(tmp_path / "module.pyi", "", lines=5)
        
        # TypeScript
        create_source_file(tmp_path / "app.ts", "", lines=8)
        create_source_file(tmp_path / "component.tsx", "", lines=7)
        
        # Go
        create_source_file(tmp_path / "main.go", "", lines=15)
        
        result = detect_languages(tmp_path)
        
        lang_names = {lang.name for lang in result}
        assert "Python" in lang_names
        assert "TypeScript" in lang_names
        assert "Go" in lang_names
    
    def test_detect_languages_ignores_unsupported_files(self, tmp_path):
        """Should ignore files with unsupported extensions."""
        # Supported
        create_source_file(tmp_path / "main.py", "", lines=10)
        
        # Unsupported
        (tmp_path / "data.json").write_text('{"key": "value"}')
        (tmp_path / "README.md").write_text('# Project')
        (tmp_path / "config.yaml").write_text('key: value')
        
        result = detect_languages(tmp_path)
        
        assert len(result) == 1
        assert result[0].name == "Python"
    
    def test_detect_languages_with_shebang(self, tmp_path):
        """Should detect language from shebang in extensionless files."""
        # Create file with Python shebang
        script = tmp_path / "script"
        script.write_text("#!/usr/bin/env python3\nprint('hello')\n")
        
        result = detect_languages(tmp_path)
        
        assert len(result) == 1
        assert result[0].name == "Python"
    
    def test_detect_languages_counts_non_empty_lines(self, tmp_path):
        """Should count only non-empty lines."""
        content = """
def hello():
    print('hello')

def world():
    print('world')

"""
        create_source_file(tmp_path / "main.py", content)
        
        result = detect_languages(tmp_path)
        
        # Should count 4 non-empty lines (2 def lines, 2 print lines)
        assert result[0].line_count == 4
    
    def test_detect_languages_handles_unicode(self, tmp_path):
        """Should handle files with unicode content."""
        content = """
# 中文注释
def hello():
    print('你好世界')
"""
        create_source_file(tmp_path / "main.py", content)
        
        result = detect_languages(tmp_path)
        
        assert len(result) == 1
        assert result[0].name == "Python"
    
    def test_detect_languages_handles_read_errors(self, tmp_path):
        """Should handle files that can't be read."""
        # Create a valid file
        create_source_file(tmp_path / "valid.py", "", lines=10)
        
        # Create a file with problematic encoding
        binary_file = tmp_path / "binary.py"
        binary_file.write_bytes(b'\x80\x81\x82\x83')
        
        result = detect_languages(tmp_path)
        
        # Should still detect Python from valid file
        assert len(result) == 1
        assert result[0].name == "Python"


class TestDetectLanguageVersions:
    """Tests for language version detection."""
    
    def test_detect_python_version_from_pyproject(self, tmp_path):
        """Should detect Python version from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
name = "myproject"
requires-python = ">=3.11"
""")
        create_source_file(tmp_path / "main.py", "", lines=10)
        
        result = detect_languages(tmp_path)
        
        assert result[0].name == "Python"
        assert result[0].version == ">=3.11"
    
    def test_detect_python_version_from_python_version_file(self, tmp_path):
        """Should detect Python version from .python-version file."""
        (tmp_path / ".python-version").write_text("python-3.11.5\n")
        create_source_file(tmp_path / "main.py", "", lines=10)
        
        result = detect_languages(tmp_path)
        
        assert result[0].name == "Python"
        assert result[0].version == "3.11.5"
    
    def test_detect_nodejs_version_from_package_json(self, tmp_path):
        """Should detect Node.js version from package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text("""
{
  "name": "myapp",
  "engines": {
    "node": ">=18.0.0"
  }
}
""")
        create_source_file(tmp_path / "app.js", "", lines=10)
        
        result = detect_languages(tmp_path)
        
        assert result[0].name == "JavaScript"
        assert result[0].version == ">=18.0.0"
    
    def test_detect_go_version_from_go_mod(self, tmp_path):
        """Should detect Go version from go.mod."""
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("""
module example.com/myapp

go 1.21

require (
    github.com/pkg/errors v0.9.1
)
""")
        create_source_file(tmp_path / "main.go", "", lines=10)
        
        result = detect_languages(tmp_path)
        
        assert result[0].name == "Go"
        assert result[0].version == "1.21"
    
    def test_no_version_detected(self, tmp_path):
        """Should handle case when no version file exists."""
        create_source_file(tmp_path / "main.py", "", lines=10)
        
        result = detect_languages(tmp_path)
        
        assert result[0].name == "Python"
        assert result[0].version is None


class TestGetLanguageConfidenceScore:
    """Tests for get_language_confidence_score function."""
    
    def test_confidence_score_high(self):
        """Should return 1.0 for >50% percentage."""
        lang_info = LanguageInfo(
            name="Python",
            file_count=100,
            line_count=5000,
            percentage=75.0
        )
        
        score = get_language_confidence_score(lang_info)
        
        assert score == 1.0
    
    def test_confidence_score_medium_high(self):
        """Should return 0.8 for 20-50% percentage."""
        lang_info = LanguageInfo(
            name="JavaScript",
            file_count=50,
            line_count=2000,
            percentage=35.0
        )
        
        score = get_language_confidence_score(lang_info)
        
        assert score == 0.8
    
    def test_confidence_score_medium(self):
        """Should return 0.5 for 10-20% percentage."""
        lang_info = LanguageInfo(
            name="TypeScript",
            file_count=20,
            line_count=800,
            percentage=15.0
        )
        
        score = get_language_confidence_score(lang_info)
        
        assert score == 0.5
    
    def test_confidence_score_low(self):
        """Should return 0.3 for <10% percentage."""
        lang_info = LanguageInfo(
            name="Go",
            file_count=5,
            line_count=200,
            percentage=5.0
        )
        
        score = get_language_confidence_score(lang_info)
        
        assert score == 0.3


class TestCheckLanguageMarkers:
    """Tests for check_language_markers function."""
    
    def test_detect_python_markers(self, tmp_path):
        """Should detect Python marker files."""
        (tmp_path / "requirements.txt").write_text("flask==2.0.0\n")
        (tmp_path / "setup.py").write_text("from setuptools import setup\n")
        
        markers = check_language_markers(tmp_path)
        
        assert "Python" in markers
    
    def test_detect_javascript_markers(self, tmp_path):
        """Should detect JavaScript marker files."""
        (tmp_path / "package.json").write_text('{"name": "myapp"}\n')
        
        markers = check_language_markers(tmp_path)
        
        assert "JavaScript" in markers
    
    def test_detect_typescript_markers(self, tmp_path):
        """Should detect TypeScript marker files."""
        (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}\n')
        
        markers = check_language_markers(tmp_path)
        
        assert "TypeScript" in markers
    
    def test_detect_go_markers(self, tmp_path):
        """Should detect Go marker files."""
        (tmp_path / "go.mod").write_text("module example.com/myapp\n")
        
        markers = check_language_markers(tmp_path)
        
        assert "Go" in markers
    
    def test_detect_rust_markers(self, tmp_path):
        """Should detect Rust marker files."""
        (tmp_path / "Cargo.toml").write_text('[package]\nname = "myapp"\n')
        
        markers = check_language_markers(tmp_path)
        
        assert "Rust" in markers
    
    def test_detect_multiple_markers(self, tmp_path):
        """Should detect multiple language markers."""
        (tmp_path / "package.json").write_text('{"name": "myapp"}\n')
        (tmp_path / "requirements.txt").write_text("flask==2.0.0\n")
        (tmp_path / "go.mod").write_text("module example.com/myapp\n")
        
        markers = check_language_markers(tmp_path)
        
        assert "JavaScript" in markers
        assert "Python" in markers
        assert "Go" in markers
    
    def test_no_markers_found(self, tmp_path):
        """Should return empty set when no markers found."""
        markers = check_language_markers(tmp_path)
        
        assert isinstance(markers, set)
        assert len(markers) == 0


class TestCountLinesInFile:
    """Tests for _count_lines_in_file function."""
    
    def test_count_lines_simple_file(self, tmp_path):
        """Should count non-empty lines."""
        file_path = tmp_path / "test.py"
        file_path.write_text("line1\nline2\nline3\n")
        
        count = _count_lines_in_file(file_path)
        
        assert count == 3
    
    def test_count_lines_with_empty_lines(self, tmp_path):
        """Should skip empty lines."""
        file_path = tmp_path / "test.py"
        file_path.write_text("line1\n\nline2\n\n\nline3\n")
        
        count = _count_lines_in_file(file_path)
        
        assert count == 3
    
    def test_count_lines_with_whitespace(self, tmp_path):
        """Should skip lines with only whitespace."""
        file_path = tmp_path / "test.py"
        file_path.write_text("line1\n   \nline2\n\t\nline3\n")
        
        count = _count_lines_in_file(file_path)
        
        assert count == 3
    
    def test_count_lines_empty_file(self, tmp_path):
        """Should return 0 for empty file."""
        file_path = tmp_path / "test.py"
        file_path.write_text("")
        
        count = _count_lines_in_file(file_path)
        
        assert count == 0


class TestDetectLanguageFromShebang:
    """Tests for _detect_language_from_shebang function."""
    
    def test_detect_python_shebang(self, tmp_path):
        """Should detect Python from shebang."""
        file_path = tmp_path / "script"
        file_path.write_text("#!/usr/bin/env python3\nprint('hello')\n")
        
        lang = _detect_language_from_shebang(file_path)
        
        assert lang == "Python"
    
    def test_detect_bash_shebang(self, tmp_path):
        """Should detect Shell from bash shebang."""
        file_path = tmp_path / "script"
        file_path.write_text("#!/bin/bash\necho 'hello'\n")
        
        lang = _detect_language_from_shebang(file_path)
        
        assert lang == "Shell"
    
    def test_detect_ruby_shebang(self, tmp_path):
        """Should detect Ruby from shebang."""
        file_path = tmp_path / "script"
        file_path.write_text("#!/usr/bin/env ruby\nputs 'hello'\n")
        
        lang = _detect_language_from_shebang(file_path)
        
        assert lang == "Ruby"
    
    def test_no_shebang(self, tmp_path):
        """Should return None when no shebang present."""
        file_path = tmp_path / "script"
        file_path.write_text("print('hello')\n")
        
        lang = _detect_language_from_shebang(file_path)
        
        assert lang is None


class TestLanguageDetectionIntegration:
    """Integration tests for language detection."""
    
    def test_realistic_python_project(self, tmp_path):
        """Should correctly analyze a realistic Python project."""
        # Create project structure
        create_source_file(tmp_path / "src" / "main.py", "", lines=50)
        create_source_file(tmp_path / "src" / "utils.py", "", lines=30)
        create_source_file(tmp_path / "tests" / "test_main.py", "", lines=40)
        (tmp_path / "requirements.txt").write_text("flask==2.0.0\n")
        (tmp_path / "pyproject.toml").write_text('requires-python = ">=3.11"\n')
        
        result = detect_languages(tmp_path)
        
        assert len(result) == 1
        assert result[0].name == "Python"
        assert result[0].file_count == 3
        assert result[0].line_count == 120
        assert result[0].version == ">=3.11"
        assert result[0].percentage == 100.0
    
    def test_realistic_fullstack_project(self, tmp_path):
        """Should correctly analyze a fullstack project."""
        # Backend (Python) - 60%
        create_source_file(tmp_path / "backend" / "api.py", "", lines=40)
        create_source_file(tmp_path / "backend" / "models.py", "", lines=20)
        
        # Frontend (TypeScript) - 40%
        create_source_file(tmp_path / "frontend" / "App.tsx", "", lines=25)
        create_source_file(tmp_path / "frontend" / "utils.ts", "", lines=15)
        
        # Config files
        (tmp_path / "requirements.txt").write_text("fastapi==0.100.0\n")
        (tmp_path / "package.json").write_text('{"name": "frontend"}\n')
        (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {}}\n')
        
        result = detect_languages(tmp_path)
        
        assert len(result) == 2
        assert result[0].name == "Python"
        assert result[0].percentage == 60.0
        assert result[1].name == "TypeScript"
        assert result[1].percentage == 40.0
        
        # Check markers
        markers = check_language_markers(tmp_path)
        assert "Python" in markers
        assert "JavaScript" in markers
        assert "TypeScript" in markers
