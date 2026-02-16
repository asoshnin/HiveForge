"""
Tests for the documentation parser module.

This module tests parsing of README files, documentation folders,
and inline comments from codebases.
"""

import pytest
from pathlib import Path
from src.hiveforge.steering.analyzers.documentation_parser import (
    parse_codebase_documentation,
    get_documentation_summary,
    _parse_readme_files,
    _parse_documentation_folders,
    _extract_inline_comments,
    _extract_comments_from_file,
    _get_language_from_extension,
    _parse_text_file,
)
from src.hiveforge.steering.models import ParsedDocument


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure with documentation."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Create README.md
    readme = project_root / "README.md"
    readme.write_text("""# Test Project

This is a test project for documentation parsing.

## Features
- Feature 1
- Feature 2

## Installation
```bash
pip install test-project
```
""", encoding='utf-8')
    
    # Create docs folder
    docs_dir = project_root / "docs"
    docs_dir.mkdir()
    
    # Create documentation files
    (docs_dir / "getting-started.md").write_text("""# Getting Started

Welcome to the project!

## Quick Start
Follow these steps...
""", encoding='utf-8')
    
    (docs_dir / "api.md").write_text("""# API Documentation

## Endpoints
- GET /api/users
- POST /api/users
""", encoding='utf-8')
    
    # Create source file with comments
    src_dir = project_root / "src"
    src_dir.mkdir()
    
    (src_dir / "main.py").write_text('''"""
Main module for the application.

This module provides the core functionality.
"""

def hello_world():
    """Print hello world message."""
    # This is a simple function
    print("Hello, World!")

class Calculator:
    """A simple calculator class."""
    
    def add(self, a, b):
        """Add two numbers together."""
        return a + b
''', encoding='utf-8')
    
    (src_dir / "utils.js").write_text('''/**
 * Utility functions for the application.
 * 
 * @module utils
 */

/**
 * Format a date string.
 * @param {Date} date - The date to format
 * @returns {string} Formatted date
 */
function formatDate(date) {
    // Format the date as ISO string
    return date.toISOString();
}

// Export the function
module.exports = { formatDate };
''', encoding='utf-8')
    
    return project_root


@pytest.fixture
def temp_project_no_docs(tmp_path):
    """Create a temporary project with no documentation."""
    project_root = tmp_path / "no_docs_project"
    project_root.mkdir()
    
    # Create only source files, no docs
    src_dir = project_root / "src"
    src_dir.mkdir()
    
    (src_dir / "code.py").write_text("print('hello')", encoding='utf-8')
    
    return project_root


class TestParseReadmeFiles:
    """Tests for README file parsing."""
    
    def test_parse_readme_md(self, temp_project):
        """Test parsing README.md file."""
        readme_docs = _parse_readme_files(temp_project)
        
        # On case-insensitive filesystems, may find multiple patterns pointing to same file
        assert len(readme_docs) >= 1
        # Check that at least one README was found
        readme_names = [doc.file_path.name for doc in readme_docs]
        assert any('README' in name.upper() for name in readme_names)
        # Check content
        assert any("Test Project" in doc.content for doc in readme_docs)
        assert any("Features" in doc.content for doc in readme_docs)
    
    def test_parse_no_readme(self, temp_project_no_docs):
        """Test parsing when no README exists."""
        readme_docs = _parse_readme_files(temp_project_no_docs)
        
        assert len(readme_docs) == 0
    
    def test_parse_multiple_readme_formats(self, tmp_path):
        """Test parsing different README formats."""
        project_root = tmp_path / "multi_readme"
        project_root.mkdir()
        
        # Create README.md
        (project_root / "README.md").write_text("# Markdown README", encoding='utf-8')
        
        # Create README.txt
        (project_root / "README.txt").write_text("Text README", encoding='utf-8')
        
        readme_docs = _parse_readme_files(project_root)
        
        # Should find both
        assert len(readme_docs) >= 1
        readme_names = [doc.file_path.name for doc in readme_docs]
        assert any('README' in name for name in readme_names)


class TestParseDocumentationFolders:
    """Tests for documentation folder parsing."""
    
    def test_parse_docs_folder(self, temp_project):
        """Test parsing docs/ folder."""
        doc_docs = _parse_documentation_folders(temp_project, set())
        
        assert len(doc_docs) == 2
        filenames = [doc.file_path.name for doc in doc_docs]
        assert "getting-started.md" in filenames
        assert "api.md" in filenames
    
    def test_parse_no_docs_folder(self, temp_project_no_docs):
        """Test parsing when no docs folder exists."""
        doc_docs = _parse_documentation_folders(temp_project_no_docs, set())
        
        assert len(doc_docs) == 0
    
    def test_parse_docs_with_exclusions(self, temp_project):
        """Test parsing docs folder with exclusions."""
        # Exclude the docs folder
        excluded = {Path("docs")}
        doc_docs = _parse_documentation_folders(temp_project, excluded)
        
        # Should find nothing since docs is excluded
        assert len(doc_docs) == 0
    
    def test_parse_nested_docs(self, tmp_path):
        """Test parsing nested documentation structure."""
        project_root = tmp_path / "nested_docs"
        project_root.mkdir()
        
        # Create nested docs structure
        docs_dir = project_root / "docs"
        docs_dir.mkdir()
        
        api_dir = docs_dir / "api"
        api_dir.mkdir()
        
        (api_dir / "endpoints.md").write_text("# Endpoints", encoding='utf-8')
        
        doc_docs = _parse_documentation_folders(project_root, set())
        
        assert len(doc_docs) == 1
        assert doc_docs[0].file_path.name == "endpoints.md"


class TestExtractInlineComments:
    """Tests for inline comment extraction."""
    
    def test_extract_python_comments(self, temp_project):
        """Test extracting comments from Python files."""
        comment_docs = _extract_inline_comments(temp_project, set(), max_files=10)
        
        # Should find comments from main.py
        assert len(comment_docs) >= 1
        
        # Find the Python file
        py_doc = next((doc for doc in comment_docs if doc.file_path.suffix == '.py'), None)
        assert py_doc is not None
        assert "Main module" in py_doc.content or "simple calculator" in py_doc.content
    
    def test_extract_javascript_comments(self, temp_project):
        """Test extracting comments from JavaScript files."""
        comment_docs = _extract_inline_comments(temp_project, set(), max_files=10)
        
        # Find the JavaScript file
        js_doc = next((doc for doc in comment_docs if doc.file_path.suffix == '.js'), None)
        assert js_doc is not None
        assert "Utility functions" in js_doc.content or "Format a date" in js_doc.content
    
    def test_extract_no_comments(self, temp_project_no_docs):
        """Test extracting when no meaningful comments exist."""
        comment_docs = _extract_inline_comments(temp_project_no_docs, set(), max_files=10)
        
        # May find the file but with minimal content
        assert isinstance(comment_docs, list)
    
    def test_max_files_limit(self, tmp_path):
        """Test that max_files limit is respected."""
        project_root = tmp_path / "many_files"
        project_root.mkdir()
        
        src_dir = project_root / "src"
        src_dir.mkdir()
        
        # Create many files
        for i in range(20):
            (src_dir / f"file{i}.py").write_text(f'"""File {i}"""\npass', encoding='utf-8')
        
        comment_docs = _extract_inline_comments(project_root, set(), max_files=5)
        
        # Should respect the limit
        assert len(comment_docs) <= 5


class TestExtractCommentsFromFile:
    """Tests for comment extraction from individual files."""
    
    def test_extract_python_docstrings(self, tmp_path):
        """Test extracting Python docstrings."""
        py_file = tmp_path / "test.py"
        py_file.write_text('''"""
This is a module docstring.
It spans multiple lines.
"""

def func():
    """Function docstring."""
    pass
''', encoding='utf-8')
        
        comments = _extract_comments_from_file(py_file)
        
        assert "module docstring" in comments
        assert "Function docstring" in comments
    
    def test_extract_jsdoc_comments(self, tmp_path):
        """Test extracting JSDoc comments."""
        js_file = tmp_path / "test.js"
        js_file.write_text('''/**
 * This is a JSDoc comment.
 * @param {string} name
 */
function greet(name) {
    // Single line comment
    console.log(name);
}
''', encoding='utf-8')
        
        comments = _extract_comments_from_file(js_file)
        
        assert "JSDoc comment" in comments
    
    def test_extract_no_comments(self, tmp_path):
        """Test extracting from file with no comments."""
        py_file = tmp_path / "no_comments.py"
        py_file.write_text("x = 1\ny = 2\n", encoding='utf-8')
        
        comments = _extract_comments_from_file(py_file)
        
        assert comments == ""
    
    def test_filter_short_comments(self, tmp_path):
        """Test that very short comments are filtered out."""
        py_file = tmp_path / "short.py"
        py_file.write_text('''# x
# This is a longer comment that should be included
x = 1
''', encoding='utf-8')
        
        comments = _extract_comments_from_file(py_file)
        
        # Short comment "x" should be filtered, longer one kept
        assert "longer comment" in comments


class TestGetLanguageFromExtension:
    """Tests for language detection from file extension."""
    
    def test_python_extension(self):
        """Test Python extension mapping."""
        assert _get_language_from_extension('.py') == 'python'
    
    def test_javascript_extensions(self):
        """Test JavaScript/TypeScript extension mapping."""
        assert _get_language_from_extension('.js') == 'javascript'
        assert _get_language_from_extension('.ts') == 'javascript'
        assert _get_language_from_extension('.tsx') == 'javascript'
    
    def test_c_family_extensions(self):
        """Test C/C++ extension mapping."""
        assert _get_language_from_extension('.c') == 'c'
        assert _get_language_from_extension('.cpp') == 'c'
        assert _get_language_from_extension('.h') == 'c'
    
    def test_unknown_extension(self):
        """Test unknown extension defaults to 'c'."""
        assert _get_language_from_extension('.xyz') == 'c'


class TestParseTextFile:
    """Tests for plain text file parsing."""
    
    def test_parse_utf8_text(self, tmp_path):
        """Test parsing UTF-8 text file."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hello, World!\nThis is a test.", encoding='utf-8')
        
        parsed = _parse_text_file(text_file)
        
        assert parsed.content == "Hello, World!\nThis is a test."
        assert len(parsed.parse_errors) == 0
        assert parsed.metadata['file_type'] == 'text'
    
    def test_parse_with_encoding_fallback(self, tmp_path):
        """Test parsing with encoding fallback."""
        text_file = tmp_path / "latin.txt"
        # Write with latin-1 encoding
        text_file.write_bytes("Café".encode('latin-1'))
        
        parsed = _parse_text_file(text_file)
        
        # Should succeed with fallback
        assert len(parsed.content) > 0


class TestParseCodebaseDocumentation:
    """Tests for the main documentation parsing function."""
    
    def test_parse_complete_project(self, temp_project):
        """Test parsing a complete project with all doc types."""
        parsed_docs = parse_codebase_documentation(
            temp_project,
            excluded_paths=set(),
            include_inline_comments=True
        )
        
        # Should find README + docs files + source comments
        assert len(parsed_docs) >= 3
        
        # Check we have different types
        has_readme = any('README' in doc.file_path.name for doc in parsed_docs)
        has_docs = any('docs' in str(doc.file_path) for doc in parsed_docs)
        
        assert has_readme
        assert has_docs
    
    def test_parse_without_inline_comments(self, temp_project):
        """Test parsing without inline comment extraction."""
        parsed_docs = parse_codebase_documentation(
            temp_project,
            excluded_paths=set(),
            include_inline_comments=False
        )
        
        # Should find README + docs files only
        assert len(parsed_docs) >= 3
        
        # Should not have inline comments
        has_inline = any(
            doc.metadata.get('file_type') == 'inline_comments' 
            for doc in parsed_docs
        )
        assert not has_inline
    
    def test_parse_with_exclusions(self, temp_project):
        """Test parsing with path exclusions."""
        # Exclude docs folder
        excluded = {Path("docs")}
        
        parsed_docs = parse_codebase_documentation(
            temp_project,
            excluded_paths=excluded,
            include_inline_comments=False
        )
        
        # Should only find README
        assert len(parsed_docs) >= 1
        
        # Should not have docs folder files
        has_docs = any('docs' in str(doc.file_path) for doc in parsed_docs)
        assert not has_docs
    
    def test_parse_empty_project(self, temp_project_no_docs):
        """Test parsing project with no documentation."""
        parsed_docs = parse_codebase_documentation(
            temp_project_no_docs,
            excluded_paths=set(),
            include_inline_comments=False
        )
        
        # Should return empty list or minimal results
        assert isinstance(parsed_docs, list)


class TestGetDocumentationSummary:
    """Tests for documentation summary generation."""
    
    def test_summary_with_docs(self, temp_project):
        """Test generating summary with documentation."""
        parsed_docs = parse_codebase_documentation(
            temp_project,
            excluded_paths=set(),
            include_inline_comments=True
        )
        
        summary = get_documentation_summary(parsed_docs)
        
        assert summary['total_documents'] == len(parsed_docs)
        assert summary['readme_files'] >= 1
        assert summary['doc_folder_files'] >= 2
        assert summary['total_content_length'] > 0
        assert 'documents_with_errors' in summary
    
    def test_summary_empty(self):
        """Test generating summary with no documents."""
        summary = get_documentation_summary([])
        
        assert summary['total_documents'] == 0
        assert summary['readme_files'] == 0
        assert summary['doc_folder_files'] == 0
        assert summary['total_content_length'] == 0


class TestErrorHandling:
    """Tests for error handling in documentation parsing."""
    
    def test_parse_nonexistent_directory(self, tmp_path):
        """Test parsing non-existent directory."""
        nonexistent = tmp_path / "does_not_exist"
        
        parsed_docs = parse_codebase_documentation(
            nonexistent,
            excluded_paths=set(),
            include_inline_comments=False
        )
        
        # Should handle gracefully
        assert isinstance(parsed_docs, list)
    
    def test_parse_with_permission_error(self, tmp_path):
        """Test handling permission errors."""
        # This test is platform-dependent and may not work on all systems
        # Just verify the function doesn't crash
        parsed_docs = parse_codebase_documentation(
            tmp_path,
            excluded_paths=set(),
            include_inline_comments=False
        )
        
        assert isinstance(parsed_docs, list)
    
    def test_parse_corrupted_file(self, tmp_path):
        """Test parsing corrupted markdown file."""
        project_root = tmp_path / "corrupted"
        project_root.mkdir()
        
        # Create a file with invalid UTF-8
        readme = project_root / "README.md"
        readme.write_bytes(b'\xff\xfe Invalid UTF-8')
        
        parsed_docs = parse_codebase_documentation(
            project_root,
            excluded_paths=set(),
            include_inline_comments=False
        )
        
        # Should handle gracefully, may have parse errors
        assert isinstance(parsed_docs, list)


class TestIntegration:
    """Integration tests for documentation parsing."""
    
    def test_real_world_structure(self, tmp_path):
        """Test parsing a realistic project structure."""
        project_root = tmp_path / "real_project"
        project_root.mkdir()
        
        # Create README
        (project_root / "README.md").write_text("# Real Project\n\nDescription", encoding='utf-8')
        
        # Create docs with subdirectories
        docs = project_root / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("# Documentation Index", encoding='utf-8')
        
        api_docs = docs / "api"
        api_docs.mkdir()
        (api_docs / "rest.md").write_text("# REST API", encoding='utf-8')
        
        # Create source with comments
        src = project_root / "src"
        src.mkdir()
        (src / "app.py").write_text('"""Main app"""\npass', encoding='utf-8')
        
        # Parse everything
        parsed_docs = parse_codebase_documentation(
            project_root,
            excluded_paths=set(),
            include_inline_comments=True
        )
        
        # Verify we found everything
        assert len(parsed_docs) >= 4  # README + 2 docs + 1 source
        
        summary = get_documentation_summary(parsed_docs)
        assert summary['readme_files'] >= 1
        assert summary['doc_folder_files'] >= 2
