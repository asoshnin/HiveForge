"""
Language detection module for code analysis.

This module detects programming languages used in a codebase by analyzing
file extensions, counting lines of code, and parsing version specifiers from
dependency files and runtime configuration files.

All analysis is performed locally without LLM API calls.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..models import LanguageInfo

logger = logging.getLogger(__name__)


# Language detection mappings
LANGUAGE_EXTENSIONS = {
    'Python': {'.py', '.pyw', '.pyx', '.pyi'},
    'JavaScript': {'.js', '.mjs', '.cjs'},
    'TypeScript': {'.ts', '.tsx'},
    'Java': {'.java'},
    'Go': {'.go'},
    'Rust': {'.rs'},
    'C': {'.c', '.h'},
    'C++': {'.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.h++'},
    'C#': {'.cs'},
    'Ruby': {'.rb'},
    'PHP': {'.php'},
    'Swift': {'.swift'},
    'Kotlin': {'.kt', '.kts'},
    'Scala': {'.scala'},
    'R': {'.r', '.R'},
    'Shell': {'.sh', '.bash', '.zsh'},
    'HTML': {'.html', '.htm'},
    'CSS': {'.css', '.scss', '.sass', '.less'},
    'SQL': {'.sql'},
    'Dart': {'.dart'},
    'Lua': {'.lua'},
    'Perl': {'.pl', '.pm'},
    'Haskell': {'.hs'},
    'Elixir': {'.ex', '.exs'},
    'Clojure': {'.clj', '.cljs', '.cljc'},
}

# Shebang patterns for language detection
SHEBANG_PATTERNS = {
    'Python': [r'#!/usr/bin/env python', r'#!/usr/bin/python'],
    'Ruby': [r'#!/usr/bin/env ruby', r'#!/usr/bin/ruby'],
    'Shell': [r'#!/bin/bash', r'#!/bin/sh', r'#!/usr/bin/env bash'],
    'Node.js': [r'#!/usr/bin/env node', r'#!/usr/bin/node'],
}

# Language-specific marker files
LANGUAGE_MARKERS = {
    'Python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
    'JavaScript': ['package.json', 'package-lock.json'],
    'TypeScript': ['tsconfig.json'],
    'Go': ['go.mod', 'go.sum'],
    'Rust': ['Cargo.toml', 'Cargo.lock'],
    'Java': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
    'Ruby': ['Gemfile', 'Gemfile.lock'],
    'PHP': ['composer.json', 'composer.lock'],
}

# Version detection patterns
VERSION_PATTERNS = {
    'Python': [
        (r'python_requires\s*=\s*["\']([^"\']+)["\']', 'setup.py'),
        (r'requires-python\s*=\s*["\']([^"\']+)["\']', 'pyproject.toml'),
        (r'python-(\d+\.\d+(?:\.\d+)?)', '.python-version'),
    ],
    'JavaScript': [  # Changed from 'Node.js' to match detected language name
        (r'"node"\s*:\s*"([^"]+)"', 'package.json'),
        (r'(\d+\.\d+\.\d+)', '.nvmrc'),
    ],
    'Go': [
        (r'^go\s+(\d+\.\d+(?:\.\d+)?)', 'go.mod'),
    ],
    'Rust': [
        (r'rust-version\s*=\s*"([^"]+)"', 'Cargo.toml'),
        (r'(\d+\.\d+\.\d+)', 'rust-toolchain'),
    ],
    'Java': [
        (r'<java\.version>([^<]+)</java\.version>', 'pom.xml'),
        (r'sourceCompatibility\s*=\s*["\']?([^"\'\s]+)["\']?', 'build.gradle'),
    ],
}


def detect_languages(
    project_root: Path,
    excluded_paths: Optional[Set[Path]] = None
) -> List[LanguageInfo]:
    """
    Detect programming languages used in the codebase.
    
    This function:
    - Counts files by extension
    - Counts lines of code per language
    - Calculates language percentages
    - Detects language versions from config files
    - Assigns confidence scores based on file count thresholds
    
    Args:
        project_root: Root directory of the project to analyze
        excluded_paths: Set of paths to exclude from analysis (e.g., from .gitignore)
        
    Returns:
        List of LanguageInfo objects sorted by percentage (descending)
        
    Requirements: 3A.3, 3A.4
    """
    logger.info(f"Detecting languages in: {project_root}")
    
    if excluded_paths is None:
        excluded_paths = set()
    
    # Count files and lines by language
    language_stats = _count_files_and_lines(project_root, excluded_paths)
    
    if not language_stats:
        logger.warning("No source files detected")
        return []
    
    # Calculate total lines for percentage calculation
    total_lines = sum(stats['lines'] for stats in language_stats.values())
    
    # Detect versions for each language
    language_versions = _detect_language_versions(project_root)
    
    # Build LanguageInfo objects
    language_infos = []
    for lang_name, stats in language_stats.items():
        percentage = (stats['lines'] / total_lines * 100) if total_lines > 0 else 0.0
        
        # Assign confidence score based on file count
        # 1.0 if >50% of files, 0.8 if 20-50%, 0.5 if 10-20%, 0.3 if <10%
        if percentage >= 50:
            confidence = 1.0
        elif percentage >= 20:
            confidence = 0.8
        elif percentage >= 10:
            confidence = 0.5
        else:
            confidence = 0.3
        
        language_info = LanguageInfo(
            name=lang_name,
            version=language_versions.get(lang_name),
            file_count=stats['files'],
            line_count=stats['lines'],
            percentage=round(percentage, 1)
        )
        
        language_infos.append(language_info)
        logger.info(
            f"Detected {lang_name}: {stats['files']} files, "
            f"{stats['lines']} lines ({percentage:.1f}%), "
            f"version: {language_versions.get(lang_name, 'unknown')}"
        )
    
    # Sort by percentage (descending)
    language_infos.sort(key=lambda x: x.percentage, reverse=True)
    
    return language_infos


def _count_files_and_lines(
    project_root: Path,
    excluded_paths: Set[Path]
) -> Dict[str, Dict[str, int]]:
    """
    Count files and lines of code by language.
    
    Args:
        project_root: Root directory to scan
        excluded_paths: Paths to exclude
        
    Returns:
        Dictionary mapping language name to {'files': int, 'lines': int}
    """
    language_stats: Dict[str, Dict[str, int]] = {}
    
    # Build reverse mapping: extension -> language
    ext_to_lang = {}
    for lang, extensions in LANGUAGE_EXTENSIONS.items():
        for ext in extensions:
            ext_to_lang[ext] = lang
    
    # Scan all files
    try:
        for file_path in project_root.rglob('*'):
            # Skip if not a file
            if not file_path.is_file():
                continue
            
            # Skip if in excluded paths
            if _is_excluded(file_path, project_root, excluded_paths):
                continue
            
            # Check extension
            ext = file_path.suffix.lower()
            if ext not in ext_to_lang:
                # Check shebang for extensionless files
                if not ext:
                    lang = _detect_language_from_shebang(file_path)
                    if not lang:
                        continue
                else:
                    continue
            else:
                lang = ext_to_lang[ext]
            
            # Initialize stats for this language if needed
            if lang not in language_stats:
                language_stats[lang] = {'files': 0, 'lines': 0}
            
            # Count file
            language_stats[lang]['files'] += 1
            
            # Count lines
            try:
                line_count = _count_lines_in_file(file_path)
                language_stats[lang]['lines'] += line_count
            except Exception as e:
                logger.debug(f"Error counting lines in {file_path}: {e}")
                # Still count the file even if we can't count lines
                language_stats[lang]['lines'] += 1
    
    except Exception as e:
        logger.error(f"Error scanning directory {project_root}: {e}")
    
    return language_stats


def _is_excluded(file_path: Path, project_root: Path, excluded_paths: Set[Path]) -> bool:
    """Check if a file path should be excluded from analysis."""
    try:
        relative_path = file_path.relative_to(project_root)
        
        # Check if any parent directory is in excluded paths
        for excluded in excluded_paths:
            try:
                relative_path.relative_to(excluded)
                return True
            except ValueError:
                continue
        
        return False
    except ValueError:
        return False


def _detect_language_from_shebang(file_path: Path) -> Optional[str]:
    """
    Detect language from shebang line in file.
    
    Args:
        file_path: Path to file to check
        
    Returns:
        Language name if detected, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline().strip()
            
            if first_line.startswith('#!'):
                for lang, patterns in SHEBANG_PATTERNS.items():
                    for pattern in patterns:
                        if re.search(pattern, first_line):
                            return lang
    except Exception:
        pass
    
    return None


def _count_lines_in_file(file_path: Path) -> int:
    """
    Count non-empty lines in a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Number of non-empty lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def _detect_language_versions(project_root: Path) -> Dict[str, str]:
    """
    Detect language versions from configuration files.
    
    Args:
        project_root: Root directory of project
        
    Returns:
        Dictionary mapping language name to version string
    """
    versions = {}
    
    for lang, patterns in VERSION_PATTERNS.items():
        for pattern, filename in patterns:
            file_path = project_root / filename
            
            if not file_path.exists():
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                match = re.search(pattern, content, re.MULTILINE)
                
                if match:
                    version = match.group(1)
                    # Clean up version string
                    version = version.strip().strip('"\'')
                    versions[lang] = version
                    logger.debug(f"Detected {lang} version {version} from {filename}")
                    break  # Use first match
            except Exception as e:
                logger.debug(f"Error reading {file_path}: {e}")
    
    return versions


def get_language_confidence_score(language_info: LanguageInfo) -> float:
    """
    Calculate confidence score for a detected language.
    
    Confidence scoring:
    - 1.0 if >50% of codebase
    - 0.8 if 20-50%
    - 0.5 if 10-20%
    - 0.3 if <10%
    
    Args:
        language_info: LanguageInfo object
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    percentage = language_info.percentage
    
    if percentage >= 50:
        return 1.0
    elif percentage >= 20:
        return 0.8
    elif percentage >= 10:
        return 0.5
    else:
        return 0.3


def check_language_markers(project_root: Path) -> Set[str]:
    """
    Check for language-specific marker files in the project.
    
    This provides additional confidence for language detection by looking
    for files like package.json, go.mod, Cargo.toml, etc.
    
    Args:
        project_root: Root directory of project
        
    Returns:
        Set of language names that have marker files present
    """
    detected_languages = set()
    
    for lang, markers in LANGUAGE_MARKERS.items():
        for marker in markers:
            if (project_root / marker).exists():
                detected_languages.add(lang)
                logger.debug(f"Found {lang} marker file: {marker}")
                break
    
    return detected_languages
