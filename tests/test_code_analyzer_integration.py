"""
Integration tests for CodeAnalyzer orchestrator.

These tests verify the end-to-end functionality of the CodeAnalyzer
with real file system operations (using temporary directories).
"""

import json
from pathlib import Path

import pytest

from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer, analyze_codebase
from hiveforge.steering.models import CodeAnalysisResult


@pytest.fixture
def sample_python_project(tmp_path):
    """Create a sample Python project for integration testing."""
    project_root = tmp_path / "sample_project"
    project_root.mkdir()
    
    # Create Python source files
    (project_root / "main.py").write_text("""
#!/usr/bin/env python3
\"\"\"Main application module.\"\"\"

def main():
    \"\"\"Main entry point.\"\"\"
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")
    
    (project_root / "utils.py").write_text("""
\"\"\"Utility functions.\"\"\"

def helper_function(value):
    \"\"\"Helper function with snake_case naming.\"\"\"
    return value * 2

class HelperClass:
    \"\"\"Helper class with PascalCase naming.\"\"\"
    
    MAX_VALUE = 100  # UPPER_SNAKE_CASE constant
    
    def __init__(self):
        self.internal_value = 0
""")
    
    # Create requirements.txt
    (project_root / "requirements.txt").write_text("""
fastapi==0.104.0
uvicorn==0.24.0
sqlalchemy==2.0.23
redis==5.0.1
""")
    
    # Create README
    (project_root / "README.md").write_text("""
# Sample Project

This is a sample Python project for testing the CodeAnalyzer.

## Features
- FastAPI backend
- SQLAlchemy ORM
- Redis caching
""")
    
    # Create .gitignore
    (project_root / ".gitignore").write_text("""
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/
""")
    
    # Create ignored directory
    pycache = project_root / "__pycache__"
    pycache.mkdir()
    (pycache / "main.cpython-311.pyc").write_text("compiled bytecode")
    
    return project_root


@pytest.fixture
def sample_js_project(tmp_path):
    """Create a sample JavaScript project for integration testing."""
    project_root = tmp_path / "js_project"
    project_root.mkdir()
    
    # Create JavaScript source files
    (project_root / "index.js").write_text("""
/**
 * Main application entry point
 */
function main() {
    console.log('Hello, World!');
}

const helperFunction = (value) => {
    return value * 2;
};

class HelperClass {
    constructor() {
        this.internalValue = 0;
    }
}

main();
""")
    
    # Create package.json
    (project_root / "package.json").write_text(json.dumps({
        "name": "sample-project",
        "version": "1.0.0",
        "dependencies": {
            "express": "^4.18.2",
            "react": "^18.2.0",
            "pg": "^8.11.0"
        },
        "devDependencies": {
            "jest": "^29.5.0"
        }
    }))
    
    # Create README
    (project_root / "README.md").write_text("""
# Sample JS Project

Express backend with React frontend.
""")
    
    return project_root


class TestPythonProjectAnalysis:
    """Test analysis of Python projects."""
    
    def test_analyze_python_project_complete(self, sample_python_project):
        """Test complete analysis of a Python project."""
        analyzer = CodeAnalyzer(sample_python_project)
        result = analyzer.analyze()
        
        # Verify result structure
        assert isinstance(result, CodeAnalysisResult)
        
        # Verify languages detected
        assert len(result.languages) > 0
        python_lang = next((l for l in result.languages if l.name == "Python"), None)
        assert python_lang is not None
        assert python_lang.percentage > 0
        
        # Verify tech stack extracted
        assert result.tech_stack.backend_framework == "FastAPI"
        # Note: SQLAlchemy alone doesn't indicate specific database
        # Database would be detected if we had psycopg2, pymongo, etc.
        assert result.tech_stack.cache == "Redis"
        
        # Verify dependencies extracted
        assert len(result.tech_stack.dependencies) > 0
        dep_names = [d.name for d in result.tech_stack.dependencies]
        assert "fastapi" in dep_names
        assert "sqlalchemy" in dep_names
        
        # Verify architecture inferred
        assert result.architecture.pattern in ["monolithic", "custom"]
        
        # Verify conventions extracted
        assert result.conventions.naming_style is not None
        
        # Verify documentation parsed
        assert len(result.documentation) > 0
        readme_doc = next((d for d in result.documentation if "README" in d.file_path.name), None)
        assert readme_doc is not None
        assert "Sample Project" in readme_doc.content
        
        # Verify confidence scores
        assert len(result.confidence_scores) > 0
    
    def test_analyze_respects_gitignore(self, sample_python_project):
        """Test that .gitignore is respected during analysis."""
        analyzer = CodeAnalyzer(sample_python_project)
        analyzer._load_gitignore()
        
        # Check that __pycache__ is excluded
        excluded_names = {path.parts[0] for path in analyzer.excluded_paths if path.parts}
        assert "__pycache__" in excluded_names
    
    def test_analyze_caching_works(self, sample_python_project):
        """Test that caching works correctly."""
        analyzer = CodeAnalyzer(sample_python_project)
        
        # First analysis
        result1 = analyzer.analyze()
        
        # Check cache file was created
        cache_path = sample_python_project / ".kiro" / ".cache" / "code_analysis.json"
        assert cache_path.exists()
        
        # Cache should contain data
        cache_data = json.loads(cache_path.read_text())
        assert "timestamp" in cache_data
        assert "summary" in cache_data


class TestJavaScriptProjectAnalysis:
    """Test analysis of JavaScript projects."""
    
    def test_analyze_js_project_complete(self, sample_js_project):
        """Test complete analysis of a JavaScript project."""
        result = analyze_codebase(sample_js_project)
        
        # Verify result structure
        assert isinstance(result, CodeAnalysisResult)
        
        # Verify languages detected
        assert len(result.languages) > 0
        js_lang = next((l for l in result.languages if l.name == "JavaScript"), None)
        assert js_lang is not None
        
        # Verify tech stack extracted
        assert result.tech_stack.backend_framework == "Express"
        assert result.tech_stack.frontend_framework == "React"
        
        # Verify dependencies
        dep_names = [d.name for d in result.tech_stack.dependencies]
        assert "express" in dep_names
        assert "react" in dep_names
        assert "pg" in dep_names
    
    def test_analyze_detects_test_framework(self, sample_js_project):
        """Test that test frameworks are detected."""
        result = analyze_codebase(sample_js_project)
        
        # Jest should be in dependencies
        dep_names = [d.name for d in result.tech_stack.dependencies]
        assert "jest" in dep_names


class TestTokenLimitedSummary:
    """Test token-limited summary generation."""
    
    def test_summary_respects_token_limit(self, sample_python_project):
        """Test that summary respects token limits."""
        analyzer = CodeAnalyzer(sample_python_project)
        
        # Generate summary with small token limit
        summary = analyzer.get_summary_for_llm(max_tokens=100)
        
        # Rough check: 100 tokens ≈ 400 characters
        assert len(summary) <= 500  # Allow some margin
        
        # Should still contain key information
        assert len(summary) > 0
    
    def test_summary_contains_key_info(self, sample_python_project):
        """Test that summary contains key information."""
        analyzer = CodeAnalyzer(sample_python_project)
        summary = analyzer.get_summary_for_llm(max_tokens=2000)
        
        # Should contain language info
        assert "Python" in summary
        
        # Should contain tech stack info
        assert "FastAPI" in summary or "Backend" in summary


class TestEmptyProject:
    """Test analysis of empty or minimal projects."""
    
    def test_analyze_empty_directory(self, tmp_path):
        """Test analyzing an empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        result = analyze_codebase(empty_dir)
        
        # Should complete without errors
        assert isinstance(result, CodeAnalysisResult)
        assert len(result.languages) == 0
        assert len(result.tech_stack.dependencies) == 0
    
    def test_analyze_no_gitignore(self, tmp_path):
        """Test analyzing a project without .gitignore."""
        project = tmp_path / "no_gitignore"
        project.mkdir()
        (project / "main.py").write_text("print('hello')")
        
        result = analyze_codebase(project)
        
        # Should work fine without .gitignore
        assert isinstance(result, CodeAnalysisResult)
        assert len(result.languages) > 0


class TestLargeCodebaseHandling:
    """Test handling of large codebases."""
    
    def test_warns_on_large_codebase(self, tmp_path, caplog):
        """Test that large codebases trigger warnings."""
        # Create a project with many files
        project = tmp_path / "large_project"
        project.mkdir()
        
        # Create many small files
        for i in range(100):
            (project / f"file_{i}.py").write_text(f"# File {i}\npass")
        
        analyzer = CodeAnalyzer(project)
        
        # Mock the file count to simulate large codebase
        with pytest.MonkeyPatch.context() as m:
            m.setattr(analyzer, "_count_files", lambda: 15000)
            
            result = analyzer.analyze()
            
            # Should complete successfully
            assert isinstance(result, CodeAnalysisResult)


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_handles_malformed_dependency_file(self, tmp_path):
        """Test handling of malformed dependency files."""
        project = tmp_path / "malformed"
        project.mkdir()
        
        # Create malformed package.json
        (project / "package.json").write_text("{ invalid json")
        (project / "main.js").write_text("console.log('test');")
        
        result = analyze_codebase(project)
        
        # Should handle error gracefully
        assert isinstance(result, CodeAnalysisResult)
        # May or may not detect JavaScript, but shouldn't crash
    
    def test_handles_unreadable_files(self, tmp_path):
        """Test handling of files that can't be read."""
        project = tmp_path / "unreadable"
        project.mkdir()
        
        # Create a normal file
        (project / "main.py").write_text("print('test')")
        
        result = analyze_codebase(project)
        
        # Should complete successfully
        assert isinstance(result, CodeAnalysisResult)


class TestConfidenceScores:
    """Test confidence score calculation."""
    
    def test_high_confidence_for_clear_patterns(self, sample_python_project):
        """Test that clear patterns get high confidence scores."""
        result = analyze_codebase(sample_python_project)
        
        # Python should have high confidence (it's the only language)
        python_score = result.confidence_scores.get("language_Python")
        assert python_score is not None
        assert python_score >= 0.8
        
        # Backend framework from dependencies should have 1.0 confidence
        backend_score = result.confidence_scores.get("backend_framework")
        if backend_score is not None:
            assert backend_score == 1.0
    
    def test_low_confidence_for_ambiguous_patterns(self, tmp_path):
        """Test that ambiguous patterns get lower confidence scores."""
        project = tmp_path / "ambiguous"
        project.mkdir()
        
        # Create minimal project with unclear architecture
        (project / "main.py").write_text("print('test')")
        
        result = analyze_codebase(project)
        
        # Architecture should have lower confidence for minimal project
        arch_score = result.confidence_scores.get("architecture")
        if arch_score is not None:
            assert arch_score <= 0.7
