"""
Tests for conventions extraction module.

This module tests the conventions extraction functionality to ensure it correctly
extracts coding conventions from codebases.
"""

import json
import pytest
from pathlib import Path

from src.hiveforge.steering.analyzers.conventions_extractor import (
    extract_conventions,
    summarize_conventions,
    _detect_naming_style,
    _detect_indent_style,
    _detect_indentation,
    _parse_editorconfig,
    _parse_json_config,
    _parse_pyproject_toml,
)


class TestExtractConventions:
    """Tests for extract_conventions function."""
    
    def test_extract_from_python_project(self, tmp_path):
        """Should extract conventions from Python project."""
        # Create Python files with conventions
        (tmp_path / 'module.py').write_text('''
def my_function():
    """This is a docstring."""
    my_variable = 42
    return my_variable

class MyClass:
    """Class docstring."""
    
    def my_method(self):
        """Method docstring."""
        pass

CONSTANT_VALUE = 100
''')
        
        result = extract_conventions(tmp_path)
        
        assert 'naming' in result
        assert 'formatting' in result
        assert 'documentation' in result
        assert len(result['naming']['functions']) > 0
        assert len(result['naming']['classes']) > 0
    
    def test_extract_from_javascript_project(self, tmp_path):
        """Should extract conventions from JavaScript project."""
        (tmp_path / 'app.js').write_text('''
function myFunction() {
    const myVariable = 42;
    return myVariable;
}

class MyClass {
    constructor() {
        this.value = 0;
    }
}

const CONSTANT_VALUE = 100;
''')
        
        result = extract_conventions(tmp_path)
        
        assert 'naming' in result
        assert len(result['naming']['functions']) > 0
        assert len(result['naming']['classes']) > 0
    
    def test_extract_with_config_files(self, tmp_path):
        """Should extract conventions from config files."""
        # Create .editorconfig
        (tmp_path / '.editorconfig').write_text('''
[*]
indent_style = space
indent_size = 4
''')
        
        result = extract_conventions(tmp_path)
        
        assert 'config_files' in result
        assert '.editorconfig' in result['config_files']
    
    def test_respects_sample_size(self, tmp_path):
        """Should respect sample size limit."""
        # Create file with many functions
        code = '\n'.join([f'def func_{i}(): pass' for i in range(200)])
        (tmp_path / 'module.py').write_text(code)
        
        result = extract_conventions(tmp_path, sample_size=50)
        
        # Should not exceed sample size
        assert len(result['naming']['functions']) <= 50
    
    def test_excludes_common_directories(self, tmp_path):
        """Should exclude node_modules, venv, etc."""
        # Create files in excluded directories
        (tmp_path / 'node_modules').mkdir()
        (tmp_path / 'node_modules' / 'lib.js').write_text('function test() {}')
        
        (tmp_path / 'venv').mkdir()
        (tmp_path / 'venv' / 'lib.py').write_text('def test(): pass')
        
        # Create file in included directory
        (tmp_path / 'src').mkdir()
        (tmp_path / 'src' / 'app.py').write_text('def my_func(): pass')
        
        result = extract_conventions(tmp_path)
        
        # Should only find functions from src/
        assert 'my_func' in result['naming']['functions']
        assert 'test' not in result['naming']['functions']
    
    def test_respects_excluded_paths(self, tmp_path):
        """Should respect excluded paths parameter."""
        (tmp_path / 'src').mkdir()
        (tmp_path / 'src' / 'app.py').write_text('def included(): pass')
        
        (tmp_path / 'build').mkdir()
        (tmp_path / 'build' / 'gen.py').write_text('def excluded(): pass')
        
        excluded = {Path('build')}
        result = extract_conventions(tmp_path, excluded_paths=excluded)
        
        assert 'included' in result['naming']['functions']
        assert 'excluded' not in result['naming']['functions']
    
    def test_empty_directory(self, tmp_path):
        """Should handle empty directory."""
        result = extract_conventions(tmp_path)
        
        assert 'naming' in result
        assert 'formatting' in result
        assert 'documentation' in result


class TestDetectNamingStyle:
    """Tests for _detect_naming_style function."""
    
    def test_detect_snake_case(self):
        """Should detect snake_case naming."""
        names = ['my_function', 'another_function', 'get_value']
        
        style = _detect_naming_style(names)
        
        assert style == 'snake_case'
    
    def test_detect_camel_case(self):
        """Should detect camelCase naming."""
        names = ['myFunction', 'anotherFunction', 'getValue']
        
        style = _detect_naming_style(names)
        
        assert style == 'camelCase'
    
    def test_detect_pascal_case(self):
        """Should detect PascalCase naming."""
        names = ['MyClass', 'AnotherClass', 'UserModel']
        
        style = _detect_naming_style(names)
        
        assert style == 'PascalCase'
    
    def test_detect_upper_snake_case(self):
        """Should detect UPPER_SNAKE_CASE naming."""
        names = ['MY_CONSTANT', 'ANOTHER_CONSTANT', 'MAX_VALUE']
        
        style = _detect_naming_style(names)
        
        assert style == 'UPPER_SNAKE_CASE'
    
    def test_empty_list(self):
        """Should handle empty list."""
        style = _detect_naming_style([])
        
        assert style == 'unknown'


class TestDetectIndentStyle:
    """Tests for _detect_indent_style function."""
    
    def test_detect_4_spaces(self):
        """Should detect 4-space indentation."""
        indents = ['4spaces'] * 10 + ['2spaces'] * 2
        
        style = _detect_indent_style(indents)
        
        assert style == '4spaces'
    
    def test_detect_2_spaces(self):
        """Should detect 2-space indentation."""
        indents = ['2spaces'] * 10 + ['4spaces'] * 2
        
        style = _detect_indent_style(indents)
        
        assert style == '2spaces'
    
    def test_detect_tabs(self):
        """Should detect tab indentation."""
        indents = ['tabs'] * 10 + ['4spaces'] * 2
        
        style = _detect_indent_style(indents)
        
        assert style == 'tabs'
    
    def test_empty_list(self):
        """Should handle empty list."""
        style = _detect_indent_style([])
        
        assert style == 'unknown'


class TestDetectIndentation:
    """Tests for _detect_indentation function."""
    
    def test_detect_spaces(self):
        """Should detect space indentation."""
        content = '''
def func():
    x = 1
    y = 2
'''
        
        indents = _detect_indentation(content)
        
        assert '4spaces' in indents
    
    def test_detect_tabs(self):
        """Should detect tab indentation."""
        content = 'def func():\n\tx = 1\n\ty = 2'
        
        indents = _detect_indentation(content)
        
        assert 'tabs' in indents
    
    def test_mixed_indentation(self):
        """Should detect mixed indentation."""
        content = '''
def func():
    x = 1
  y = 2
'''
        
        indents = _detect_indentation(content)
        
        assert '4spaces' in indents
        assert '2spaces' in indents


class TestParseConfigFiles:
    """Tests for config file parsing functions."""
    
    def test_parse_editorconfig(self, tmp_path):
        """Should parse .editorconfig file."""
        config_path = tmp_path / '.editorconfig'
        config_path.write_text('''
[*]
indent_style = space
indent_size = 4

[*.py]
max_line_length = 100
''')
        
        result = _parse_editorconfig(config_path)
        
        assert '*' in result
        assert result['*']['indent_style'] == 'space'
        assert result['*']['indent_size'] == '4'
        assert '*.py' in result
    
    def test_parse_json_config(self, tmp_path):
        """Should parse JSON config file."""
        config_path = tmp_path / '.prettierrc'
        config_path.write_text(json.dumps({
            'semi': True,
            'singleQuote': True,
            'tabWidth': 2
        }))
        
        result = _parse_json_config(config_path)
        
        assert result['semi'] is True
        assert result['singleQuote'] is True
        assert result['tabWidth'] == 2
    
    def test_parse_pyproject_toml(self, tmp_path):
        """Should parse pyproject.toml file."""
        config_path = tmp_path / 'pyproject.toml'
        config_path.write_text('''
[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
''')
        
        result = _parse_pyproject_toml(config_path)
        
        if result:  # Only if tomli is available
            assert 'tool' in result
            assert 'black' in result['tool']


class TestSummarizeConventions:
    """Tests for summarize_conventions function."""
    
    def test_summarize_naming_conventions(self):
        """Should summarize naming conventions."""
        conventions = {
            'naming': {
                'functions': ['my_func', 'another_func', 'get_value'],
                'classes': ['MyClass', 'AnotherClass'],
                'constants': ['MY_CONST', 'ANOTHER_CONST'],
            },
            'formatting': {},
            'documentation': {},
            'config_files': {},
        }
        
        summary = summarize_conventions(conventions)
        
        assert 'function_naming' in summary
        assert summary['function_naming'] == 'snake_case'
        assert 'class_naming' in summary
        assert summary['class_naming'] == 'PascalCase'
    
    def test_summarize_formatting(self):
        """Should summarize formatting conventions."""
        conventions = {
            'naming': {},
            'formatting': {
                'indentation': ['4spaces'] * 10 + ['2spaces'] * 2,
            },
            'documentation': {},
            'config_files': {},
        }
        
        summary = summarize_conventions(conventions)
        
        assert 'indentation' in summary
        assert summary['indentation'] == '4spaces'
    
    def test_summarize_documentation(self):
        """Should summarize documentation conventions."""
        conventions = {
            'naming': {},
            'formatting': {},
            'documentation': {
                'has_docstrings': 8,
                'total_functions': 10,
            },
            'config_files': {},
        }
        
        summary = summarize_conventions(conventions)
        
        assert 'documentation' in summary
        assert 'Most functions have docstrings' in summary['documentation']
    
    def test_summarize_config_files(self):
        """Should summarize config files."""
        conventions = {
            'naming': {},
            'formatting': {},
            'documentation': {},
            'config_files': {
                '.editorconfig': {},
                '.prettierrc': {},
            },
        }
        
        summary = summarize_conventions(conventions)
        
        assert 'config_files' in summary
        assert '.editorconfig' in summary['config_files']
        assert '.prettierrc' in summary['config_files']


class TestConventionsExtractionIntegration:
    """Integration tests for conventions extraction."""
    
    def test_realistic_python_project(self, tmp_path):
        """Should correctly analyze a realistic Python project."""
        # Create project structure
        (tmp_path / 'src').mkdir()
        (tmp_path / 'src' / 'models.py').write_text('''
"""Models module."""

class UserModel:
    """User model class."""
    
    def __init__(self, name: str):
        """Initialize user."""
        self.name = name
    
    def get_name(self) -> str:
        """Get user name."""
        return self.name

MAX_USERS = 100
''')
        
        (tmp_path / 'src' / 'utils.py').write_text('''
"""Utility functions."""

def format_name(name: str) -> str:
    """Format a name."""
    return name.title()

def validate_email(email: str) -> bool:
    """Validate email address."""
    return '@' in email
''')
        
        # Create config file
        (tmp_path / '.editorconfig').write_text('''
[*.py]
indent_style = space
indent_size = 4
''')
        
        result = extract_conventions(tmp_path)
        summary = summarize_conventions(result)
        
        assert summary['function_naming'] == 'snake_case'
        assert summary['class_naming'] == 'PascalCase'
        assert summary['indentation'] == '4spaces'
        assert 'Most functions have docstrings' in summary['documentation']
    
    def test_realistic_javascript_project(self, tmp_path):
        """Should correctly analyze a realistic JavaScript project."""
        (tmp_path / 'src').mkdir()
        (tmp_path / 'src' / 'app.js').write_text('''
class UserService {
  constructor() {
    this.users = [];
  }
  
  addUser(user) {
    this.users.push(user);
  }
  
  getUser(id) {
    return this.users.find(u => u.id === id);
  }
}

const MAX_USERS = 100;

function formatName(name) {
  return name.trim();
}
''')
        
        (tmp_path / '.prettierrc').write_text(json.dumps({
            'semi': True,
            'singleQuote': False,
            'tabWidth': 2
        }))
        
        result = extract_conventions(tmp_path)
        summary = summarize_conventions(result)
        
        assert summary['function_naming'] == 'camelCase'
        assert summary['class_naming'] == 'PascalCase'
        assert summary['indentation'] == '2spaces'
    
    def test_mixed_language_project(self, tmp_path):
        """Should handle projects with multiple languages."""
        # Python file
        (tmp_path / 'backend.py').write_text('''
def process_data(data):
    """Process data."""
    return data.strip()
''')
        
        # JavaScript file
        (tmp_path / 'frontend.js').write_text('''
function processData(data) {
  return data.trim();
}
''')
        
        result = extract_conventions(tmp_path)
        
        # Should extract conventions from both languages
        assert len(result['naming']['functions']) >= 2
    
    def test_large_codebase_sampling(self, tmp_path):
        """Should sample large codebases efficiently."""
        # Create many files
        (tmp_path / 'src').mkdir()
        for i in range(20):
            code = '\n'.join([f'def func_{i}_{j}(): pass' for j in range(20)])
            (tmp_path / 'src' / f'module_{i}.py').write_text(code)
        
        result = extract_conventions(tmp_path, sample_size=100)
        
        # Should respect sample size
        assert len(result['naming']['functions']) <= 100
    
    def test_handles_syntax_errors(self, tmp_path):
        """Should handle files with syntax errors gracefully."""
        # Create file with syntax error
        (tmp_path / 'broken.py').write_text('''
def broken_func(
    # Missing closing parenthesis
    pass
''')
        
        # Create valid file
        (tmp_path / 'valid.py').write_text('''
def valid_func():
    pass
''')
        
        result = extract_conventions(tmp_path)
        
        # Should still extract from valid file
        assert 'valid_func' in result['naming']['functions']
