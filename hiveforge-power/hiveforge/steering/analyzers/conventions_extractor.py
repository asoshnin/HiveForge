"""
Conventions extraction module for code analysis.

This module extracts coding conventions from existing codebases by analyzing:
- Naming patterns (functions, variables, classes)
- Indentation style (spaces vs tabs, indent size)
- Docstring and comment patterns
- Configuration files (.editorconfig, .prettierrc, etc.)

All analysis is performed locally without LLM calls.
"""

import ast
import json
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import tomli
except ImportError:
    tomli = None

logger = logging.getLogger(__name__)


# Config file parsers priority order
CONFIG_FILES = [
    '.editorconfig',
    '.prettierrc',
    '.prettierrc.json',
    '.prettierrc.js',
    '.eslintrc',
    '.eslintrc.json',
    '.eslintrc.js',
    'pyproject.toml',
    '.pylintrc',
    'setup.cfg',
]


def extract_conventions(
    project_root: Path,
    excluded_paths: Optional[Set[Path]] = None,
    sample_size: int = 100
) -> Dict[str, any]:
    """
    Extract coding conventions from a codebase.
    
    This function:
    - Analyzes naming patterns from AST (samples up to sample_size items)
    - Detects indentation style from code blocks
    - Identifies docstring/comment patterns
    - Parses config files with priority order
    
    Args:
        project_root: Root directory of the project
        excluded_paths: Set of paths to exclude from analysis
        sample_size: Maximum number of items to sample for analysis
        
    Returns:
        Dictionary containing extracted conventions
        
    Requirements: 3A.7, 3A.11
    """
    logger.info(f"Extracting conventions from: {project_root}")
    
    if excluded_paths is None:
        excluded_paths = set()
    
    conventions = {
        'naming': {},
        'formatting': {},
        'documentation': {},
        'config_files': {},
    }
    
    # Parse config files first (highest priority)
    config_conventions = _parse_config_files(project_root)
    conventions['config_files'] = config_conventions
    
    # Analyze Python files
    python_files = _find_code_files(project_root, ['.py'], excluded_paths)
    if python_files:
        python_conventions = _analyze_python_conventions(
            python_files, sample_size
        )
        _merge_conventions(conventions, python_conventions)
    
    # Analyze JavaScript/TypeScript files
    js_files = _find_code_files(
        project_root, ['.js', '.jsx', '.ts', '.tsx'], excluded_paths
    )
    if js_files:
        js_conventions = _analyze_js_conventions(js_files, sample_size)
        _merge_conventions(conventions, js_conventions)
    
    logger.info(
        f"Extracted conventions: {len(conventions['naming'])} naming patterns, "
        f"{len(conventions['formatting'])} formatting rules"
    )
    
    return conventions


def _find_code_files(
    project_root: Path,
    extensions: List[str],
    excluded_paths: Set[Path],
    max_files: int = 1000
) -> List[Path]:
    """Find code files with given extensions."""
    files = []
    
    # Common directories to exclude
    excluded_names = {
        'node_modules', 'venv', 'env', '.venv', '__pycache__',
        '.git', '.svn', '.hg', 'dist', 'build', 'target',
        '.pytest_cache', '.mypy_cache', 'coverage', 'htmlcov'
    }
    
    for ext in extensions:
        for file_path in project_root.rglob(f'*{ext}'):
            # Check if file should be excluded
            try:
                relative_path = file_path.relative_to(project_root)
                
                # Skip if in excluded paths
                skip = False
                for excluded in excluded_paths:
                    try:
                        relative_path.relative_to(excluded)
                        skip = True
                        break
                    except ValueError:
                        continue
                
                if skip:
                    continue
                
                # Skip if in excluded directory
                if any(part in excluded_names for part in relative_path.parts):
                    continue
                
                files.append(file_path)
                
                if len(files) >= max_files:
                    break
            except (ValueError, OSError):
                continue
        
        if len(files) >= max_files:
            break
    
    return files[:max_files]


def _parse_config_files(project_root: Path) -> Dict[str, Dict]:
    """Parse configuration files for coding conventions."""
    config_data = {}
    
    for config_file in CONFIG_FILES:
        config_path = project_root / config_file
        
        if not config_path.exists():
            continue
        
        try:
            if config_file == '.editorconfig':
                config_data[config_file] = _parse_editorconfig(config_path)
            elif config_file.endswith('.json') or config_file in ['.prettierrc', '.eslintrc']:
                config_data[config_file] = _parse_json_config(config_path)
            elif config_file == 'pyproject.toml':
                config_data[config_file] = _parse_pyproject_toml(config_path)
            elif config_file == '.pylintrc':
                config_data[config_file] = _parse_pylintrc(config_path)
            elif config_file == 'setup.cfg':
                config_data[config_file] = _parse_setup_cfg(config_path)
        except Exception as e:
            logger.debug(f"Error parsing {config_file}: {e}")
            continue
    
    return config_data


def _parse_editorconfig(config_path: Path) -> Dict:
    """Parse .editorconfig file."""
    config = {}
    
    try:
        content = config_path.read_text(encoding='utf-8')
        
        # Simple parser for editorconfig
        current_section = 'root'
        config[current_section] = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                config[current_section] = {}
            elif '=' in line:
                key, value = line.split('=', 1)
                config[current_section][key.strip()] = value.strip()
    except Exception as e:
        logger.debug(f"Error parsing .editorconfig: {e}")
    
    return config


def _parse_json_config(config_path: Path) -> Dict:
    """Parse JSON config file."""
    try:
        content = config_path.read_text(encoding='utf-8')
        return json.loads(content)
    except Exception as e:
        logger.debug(f"Error parsing JSON config: {e}")
        return {}


def _parse_pyproject_toml(config_path: Path) -> Dict:
    """Parse pyproject.toml file."""
    if tomli is None:
        logger.debug("tomli not available, skipping pyproject.toml")
        return {}
    
    try:
        content = config_path.read_text(encoding='utf-8')
        return tomli.loads(content)
    except Exception as e:
        logger.debug(f"Error parsing pyproject.toml: {e}")
        return {}


def _parse_pylintrc(config_path: Path) -> Dict:
    """Parse .pylintrc file."""
    config = {}
    
    try:
        content = config_path.read_text(encoding='utf-8')
        
        current_section = None
        for line in content.split('\n'):
            line = line.strip()
            
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                config[current_section] = {}
            elif '=' in line and current_section:
                key, value = line.split('=', 1)
                config[current_section][key.strip()] = value.strip()
    except Exception as e:
        logger.debug(f"Error parsing .pylintrc: {e}")
    
    return config


def _parse_setup_cfg(config_path: Path) -> Dict:
    """Parse setup.cfg file."""
    # Similar to pylintrc
    return _parse_pylintrc(config_path)


def _analyze_python_conventions(
    files: List[Path],
    sample_size: int
) -> Dict:
    """Analyze Python code conventions."""
    conventions = {
        'naming': {
            'functions': [],
            'variables': [],
            'classes': [],
            'constants': [],
        },
        'formatting': {
            'indentation': [],
            'line_length': [],
        },
        'documentation': {
            'has_docstrings': 0,
            'total_functions': 0,
            'comment_style': [],
        }
    }
    
    samples_collected = 0
    
    for file_path in files:
        if samples_collected >= sample_size:
            break
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Analyze indentation
            indents = _detect_indentation(content)
            conventions['formatting']['indentation'].extend(indents)
            
            # Parse AST for naming patterns
            try:
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if samples_collected >= sample_size:
                        break
                    
                    if isinstance(node, ast.FunctionDef):
                        conventions['naming']['functions'].append(node.name)
                        conventions['documentation']['total_functions'] += 1
                        
                        if ast.get_docstring(node):
                            conventions['documentation']['has_docstrings'] += 1
                        
                        samples_collected += 1
                    
                    elif isinstance(node, ast.ClassDef):
                        conventions['naming']['classes'].append(node.name)
                        samples_collected += 1
                    
                    elif isinstance(node, ast.Name):
                        name = node.id
                        if name.isupper() and len(name) > 1:
                            conventions['naming']['constants'].append(name)
                        else:
                            conventions['naming']['variables'].append(name)
                        samples_collected += 1
            
            except SyntaxError:
                logger.debug(f"Syntax error in {file_path}")
                continue
        
        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")
            continue
    
    return conventions


def _analyze_js_conventions(
    files: List[Path],
    sample_size: int
) -> Dict:
    """Analyze JavaScript/TypeScript code conventions."""
    conventions = {
        'naming': {
            'functions': [],
            'variables': [],
            'classes': [],
            'constants': [],
        },
        'formatting': {
            'indentation': [],
            'line_length': [],
        },
        'documentation': {
            'has_jsdoc': 0,
            'total_functions': 0,
            'comment_style': [],
        }
    }
    
    samples_collected = 0
    
    # Regex patterns for JS/TS
    function_pattern = re.compile(r'function\s+(\w+)\s*\(')
    const_function_pattern = re.compile(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(')
    class_pattern = re.compile(r'class\s+(\w+)')
    const_pattern = re.compile(r'const\s+([A-Z_][A-Z0-9_]*)\s*=')
    var_pattern = re.compile(r'(?:const|let|var)\s+(\w+)\s*=')
    
    for file_path in files:
        if samples_collected >= sample_size:
            break
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Analyze indentation
            indents = _detect_indentation(content)
            conventions['formatting']['indentation'].extend(indents)
            
            # Extract naming patterns using regex
            for match in function_pattern.finditer(content):
                if samples_collected >= sample_size:
                    break
                conventions['naming']['functions'].append(match.group(1))
                conventions['documentation']['total_functions'] += 1
                samples_collected += 1
            
            for match in const_function_pattern.finditer(content):
                if samples_collected >= sample_size:
                    break
                conventions['naming']['functions'].append(match.group(1))
                conventions['documentation']['total_functions'] += 1
                samples_collected += 1
            
            for match in class_pattern.finditer(content):
                if samples_collected >= sample_size:
                    break
                conventions['naming']['classes'].append(match.group(1))
                samples_collected += 1
            
            for match in const_pattern.finditer(content):
                if samples_collected >= sample_size:
                    break
                conventions['naming']['constants'].append(match.group(1))
                samples_collected += 1
            
            for match in var_pattern.finditer(content):
                if samples_collected >= sample_size:
                    break
                name = match.group(1)
                if not name.isupper():
                    conventions['naming']['variables'].append(name)
                samples_collected += 1
        
        except Exception as e:
            logger.debug(f"Error analyzing {file_path}: {e}")
            continue
    
    return conventions


def _detect_indentation(content: str) -> List[str]:
    """Detect indentation style from code content."""
    indents = []
    
    for line in content.split('\n'):
        if not line or not line[0].isspace():
            continue
        
        # Count leading whitespace
        indent = len(line) - len(line.lstrip())
        
        if indent > 0:
            # Determine if spaces or tabs
            if line[0] == '\t':
                indents.append('tabs')
            else:
                indents.append(f'{indent}spaces')
    
    return indents


def _merge_conventions(target: Dict, source: Dict):
    """Merge source conventions into target."""
    for category in ['naming', 'formatting', 'documentation']:
        if category in source:
            for key, value in source[category].items():
                if key not in target[category]:
                    target[category][key] = value
                elif isinstance(value, list):
                    target[category][key].extend(value)
                elif isinstance(value, (int, float)):
                    target[category][key] += value


def summarize_conventions(conventions: Dict) -> Dict[str, str]:
    """
    Summarize extracted conventions into human-readable format.
    
    Args:
        conventions: Raw conventions data
        
    Returns:
        Dictionary with summarized conventions
    """
    summary = {}
    
    # Summarize naming conventions
    naming = conventions.get('naming', {})
    
    if naming.get('functions'):
        func_style = _detect_naming_style(naming['functions'])
        summary['function_naming'] = func_style
    
    if naming.get('variables'):
        var_style = _detect_naming_style(naming['variables'])
        summary['variable_naming'] = var_style
    
    if naming.get('classes'):
        class_style = _detect_naming_style(naming['classes'])
        summary['class_naming'] = class_style
    
    if naming.get('constants'):
        const_style = _detect_naming_style(naming['constants'])
        summary['constant_naming'] = const_style
    
    # Summarize formatting
    formatting = conventions.get('formatting', {})
    
    if formatting.get('indentation'):
        indent_style = _detect_indent_style(formatting['indentation'])
        summary['indentation'] = indent_style
    
    # Summarize documentation
    documentation = conventions.get('documentation', {})
    
    if documentation.get('total_functions', 0) > 0:
        docstring_rate = (
            documentation.get('has_docstrings', 0) /
            documentation['total_functions']
        )
        if docstring_rate > 0.7:
            summary['documentation'] = 'Most functions have docstrings'
        elif docstring_rate > 0.3:
            summary['documentation'] = 'Some functions have docstrings'
        else:
            summary['documentation'] = 'Few functions have docstrings'
    
    # Add config file info
    config_files = conventions.get('config_files', {})
    if config_files:
        summary['config_files'] = ', '.join(config_files.keys())
    
    return summary


def _detect_naming_style(names: List[str]) -> str:
    """Detect naming style from list of names."""
    if not names:
        return 'unknown'
    
    # Sample up to 50 names
    sample = names[:50]
    
    styles = {
        'snake_case': 0,
        'camelCase': 0,
        'PascalCase': 0,
        'UPPER_SNAKE_CASE': 0,
    }
    
    for name in sample:
        if '_' in name:
            if name.isupper():
                styles['UPPER_SNAKE_CASE'] += 1
            else:
                styles['snake_case'] += 1
        elif name[0].isupper():
            styles['PascalCase'] += 1
        elif any(c.isupper() for c in name[1:]):
            styles['camelCase'] += 1
        else:
            styles['snake_case'] += 1
    
    # Return most common style
    return max(styles.items(), key=lambda x: x[1])[0]


def _detect_indent_style(indents: List[str]) -> str:
    """Detect indentation style from list of indents."""
    if not indents:
        return 'unknown'
    
    # Count occurrences
    counter = Counter(indents)
    most_common = counter.most_common(1)[0][0]
    
    if most_common == 'tabs':
        return 'tabs'
    else:
        # Extract number from '4spaces', '2spaces', etc.
        return most_common
