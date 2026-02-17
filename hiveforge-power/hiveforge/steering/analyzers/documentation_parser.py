"""
Documentation parser for code analysis.

This module parses README files, documentation folders, and inline comments
from codebases to extract project context for steering file generation.

All parsing is performed locally without LLM API calls.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional, Set

from ..models import ParsedDocument
from ..parsers.markdown import parse_markdown

logger = logging.getLogger(__name__)


# Common documentation directory names
DOC_DIRECTORIES = {'docs', 'documentation', 'doc', 'wiki'}

# Common README file patterns
README_PATTERNS = {
    'README.md', 'README.MD', 'readme.md', 'Readme.md',
    'README.rst', 'README.txt', 'README'
}

# File extensions to scan for inline comments
COMMENT_FILE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.go', '.rs',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
    '.kt', '.scala', '.r', '.sh', '.bash'
}

# Comment patterns by language
COMMENT_PATTERNS = {
    'python': [
        (r'"""(.*?)"""', re.DOTALL),  # Docstrings
        (r"'''(.*?)'''", re.DOTALL),  # Docstrings
        (r'#\s*(.+)$', re.MULTILINE),  # Single-line comments
    ],
    'javascript': [
        (r'/\*\*(.*?)\*/', re.DOTALL),  # JSDoc
        (r'/\*(.*?)\*/', re.DOTALL),  # Multi-line comments
        (r'//\s*(.+)$', re.MULTILINE),  # Single-line comments
    ],
    'java': [
        (r'/\*\*(.*?)\*/', re.DOTALL),  # Javadoc
        (r'/\*(.*?)\*/', re.DOTALL),  # Multi-line comments
        (r'//\s*(.+)$', re.MULTILINE),  # Single-line comments
    ],
    'c': [
        (r'/\*(.*?)\*/', re.DOTALL),  # Multi-line comments
        (r'//\s*(.+)$', re.MULTILINE),  # Single-line comments
    ],
    'shell': [
        (r'#\s*(.+)$', re.MULTILINE),  # Single-line comments
    ],
}


def parse_codebase_documentation(
    project_root: Path,
    excluded_paths: Optional[Set[Path]] = None,
    include_inline_comments: bool = False
) -> List[ParsedDocument]:
    """
    Parse documentation from a codebase.
    
    This function:
    - Finds and parses README files in the project root
    - Recursively parses documentation folders (docs/, documentation/)
    - Optionally extracts inline comments from source files
    - Returns ParsedDocument objects for each documentation source
    
    Args:
        project_root: Root directory of the project to analyze
        excluded_paths: Set of paths to exclude from analysis (e.g., from .gitignore)
        include_inline_comments: Whether to extract inline comments from code files
        
    Returns:
        List of ParsedDocument objects containing documentation content
        
    Requirements: 3A.8
    """
    logger.info(f"Parsing documentation in: {project_root}")
    
    if excluded_paths is None:
        excluded_paths = set()
    
    parsed_docs = []
    
    # 1. Parse README files in project root
    readme_docs = _parse_readme_files(project_root)
    parsed_docs.extend(readme_docs)
    logger.info(f"Found {len(readme_docs)} README file(s)")
    
    # 2. Parse documentation folders
    doc_folder_docs = _parse_documentation_folders(project_root, excluded_paths)
    parsed_docs.extend(doc_folder_docs)
    logger.info(f"Found {len(doc_folder_docs)} documentation file(s) in doc folders")
    
    # 3. Optionally extract inline comments
    if include_inline_comments:
        comment_docs = _extract_inline_comments(project_root, excluded_paths)
        parsed_docs.extend(comment_docs)
        logger.info(f"Extracted inline comments from {len(comment_docs)} file(s)")
    
    logger.info(f"Total documentation sources parsed: {len(parsed_docs)}")
    
    return parsed_docs


def _parse_readme_files(project_root: Path) -> List[ParsedDocument]:
    """
    Find and parse README files in the project root.
    
    Args:
        project_root: Root directory of project
        
    Returns:
        List of ParsedDocument objects for README files
    """
    parsed_docs = []
    
    for readme_name in README_PATTERNS:
        readme_path = project_root / readme_name
        
        if readme_path.exists() and readme_path.is_file():
            try:
                # Use existing markdown parser for .md files
                if readme_path.suffix.lower() in {'.md', '.markdown'}:
                    parsed_doc = parse_markdown(readme_path)
                else:
                    # Parse as plain text for other formats
                    parsed_doc = _parse_text_file(readme_path)
                
                parsed_docs.append(parsed_doc)
                logger.debug(f"Parsed README: {readme_path.name}")
                
            except Exception as e:
                logger.error(f"Error parsing README {readme_path}: {e}")
                # Create error document
                parsed_docs.append(ParsedDocument(
                    file_path=readme_path,
                    content="",
                    metadata={"file_type": "readme"},
                    parse_errors=[f"Failed to parse: {str(e)}"]
                ))
    
    return parsed_docs


def _parse_documentation_folders(
    project_root: Path,
    excluded_paths: Set[Path]
) -> List[ParsedDocument]:
    """
    Find and parse documentation folders (docs/, documentation/).
    
    Args:
        project_root: Root directory of project
        excluded_paths: Paths to exclude from analysis
        
    Returns:
        List of ParsedDocument objects for documentation files
    """
    parsed_docs = []
    
    # Find documentation directories
    doc_dirs = []
    for dir_name in DOC_DIRECTORIES:
        doc_dir = project_root / dir_name
        if doc_dir.exists() and doc_dir.is_dir():
            # Check if excluded
            if not _is_excluded(doc_dir, project_root, excluded_paths):
                doc_dirs.append(doc_dir)
    
    # Parse all markdown and text files in documentation directories
    for doc_dir in doc_dirs:
        try:
            for file_path in doc_dir.rglob('*'):
                # Skip if not a file
                if not file_path.is_file():
                    continue
                
                # Skip if excluded
                if _is_excluded(file_path, project_root, excluded_paths):
                    continue
                
                # Parse based on file extension
                suffix = file_path.suffix.lower()
                
                try:
                    if suffix in {'.md', '.markdown'}:
                        parsed_doc = parse_markdown(file_path)
                        parsed_docs.append(parsed_doc)
                        logger.debug(f"Parsed doc file: {file_path.relative_to(project_root)}")
                    
                    elif suffix in {'.txt', '.rst', ''}:
                        parsed_doc = _parse_text_file(file_path)
                        parsed_docs.append(parsed_doc)
                        logger.debug(f"Parsed text file: {file_path.relative_to(project_root)}")
                
                except Exception as e:
                    logger.debug(f"Error parsing {file_path}: {e}")
                    # Continue with other files
        
        except Exception as e:
            logger.error(f"Error scanning documentation directory {doc_dir}: {e}")
    
    return parsed_docs


def _extract_inline_comments(
    project_root: Path,
    excluded_paths: Set[Path],
    max_files: int = 100
) -> List[ParsedDocument]:
    """
    Extract inline comments from source code files.
    
    This function samples source files and extracts meaningful comments
    (docstrings, JSDoc, etc.) that provide project context.
    
    Args:
        project_root: Root directory of project
        excluded_paths: Paths to exclude from analysis
        max_files: Maximum number of files to process (for performance)
        
    Returns:
        List of ParsedDocument objects containing extracted comments
    """
    parsed_docs = []
    files_processed = 0
    
    try:
        for file_path in project_root.rglob('*'):
            # Stop if we've processed enough files
            if files_processed >= max_files:
                logger.debug(f"Reached max files limit ({max_files}) for comment extraction")
                break
            
            # Skip if not a file
            if not file_path.is_file():
                continue
            
            # Skip if excluded
            if _is_excluded(file_path, project_root, excluded_paths):
                continue
            
            # Check if file extension is relevant
            if file_path.suffix.lower() not in COMMENT_FILE_EXTENSIONS:
                continue
            
            try:
                # Extract comments from file
                comments = _extract_comments_from_file(file_path)
                
                if comments:
                    # Create ParsedDocument with extracted comments
                    parsed_doc = ParsedDocument(
                        file_path=file_path,
                        content=comments,
                        metadata={
                            "file_type": "inline_comments",
                            "source_file": str(file_path.relative_to(project_root))
                        },
                        parse_errors=[]
                    )
                    parsed_docs.append(parsed_doc)
                    files_processed += 1
                    logger.debug(f"Extracted comments from: {file_path.relative_to(project_root)}")
            
            except Exception as e:
                logger.debug(f"Error extracting comments from {file_path}: {e}")
                # Continue with other files
    
    except Exception as e:
        logger.error(f"Error during comment extraction: {e}")
    
    return parsed_docs


def _extract_comments_from_file(file_path: Path) -> str:
    """
    Extract comments from a source code file.
    
    Args:
        file_path: Path to source file
        
    Returns:
        Extracted comments as a single string
    """
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Determine language from extension
        ext = file_path.suffix.lower()
        language = _get_language_from_extension(ext)
        
        # Get comment patterns for this language
        patterns = COMMENT_PATTERNS.get(language, COMMENT_PATTERNS['c'])
        
        # Extract all comments
        comments = []
        for pattern, flags in patterns:
            matches = re.finditer(pattern, content, flags)
            for match in matches:
                comment_text = match.group(1).strip()
                # Filter out very short or empty comments
                if len(comment_text) > 10:
                    comments.append(comment_text)
        
        # Join comments with newlines
        return '\n\n'.join(comments)
    
    except Exception as e:
        logger.debug(f"Error reading file {file_path}: {e}")
        return ""


def _get_language_from_extension(ext: str) -> str:
    """
    Map file extension to language for comment extraction.
    
    Args:
        ext: File extension (e.g., '.py', '.js')
        
    Returns:
        Language identifier for comment pattern lookup
    """
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'javascript',
        '.tsx': 'javascript',
        '.jsx': 'javascript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'c',
        '.h': 'c',
        '.hpp': 'c',
        '.cs': 'c',
        '.go': 'c',
        '.rs': 'c',
        '.swift': 'c',
        '.kt': 'c',
        '.scala': 'c',
        '.sh': 'shell',
        '.bash': 'shell',
    }
    return ext_map.get(ext, 'c')


def _parse_text_file(file_path: Path) -> ParsedDocument:
    """
    Parse a plain text file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        ParsedDocument with file content
    """
    parse_errors = []
    content = ""
    metadata = {}
    
    try:
        # Try UTF-8 first
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata['file_size'] = file_path.stat().st_size
        metadata['file_name'] = file_path.name
        metadata['file_type'] = 'text'
    
    except UnicodeDecodeError:
        # Try with fallback encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            parse_errors.append("Used latin-1 encoding fallback")
        except Exception as e:
            parse_errors.append(f"Failed to read file: {str(e)}")
            content = ""
    
    except Exception as e:
        parse_errors.append(f"Error parsing text file: {str(e)}")
        content = ""
    
    return ParsedDocument(
        file_path=file_path,
        content=content,
        metadata=metadata,
        parse_errors=parse_errors
    )


def _is_excluded(file_path: Path, project_root: Path, excluded_paths: Set[Path]) -> bool:
    """
    Check if a file path should be excluded from analysis.
    
    Args:
        file_path: Path to check
        project_root: Root directory of project
        excluded_paths: Set of excluded paths
        
    Returns:
        True if path should be excluded, False otherwise
    """
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


def get_documentation_summary(parsed_docs: List[ParsedDocument]) -> dict:
    """
    Generate a summary of parsed documentation.
    
    Args:
        parsed_docs: List of parsed documentation
        
    Returns:
        Dictionary with summary statistics
    """
    total_docs = len(parsed_docs)
    total_content_length = sum(len(doc.content) for doc in parsed_docs)
    
    # Count by type
    readme_count = sum(1 for doc in parsed_docs 
                      if 'readme' in doc.file_path.name.lower())
    doc_folder_count = sum(1 for doc in parsed_docs 
                          if any(d in str(doc.file_path).lower() 
                                for d in DOC_DIRECTORIES))
    inline_comment_count = sum(1 for doc in parsed_docs 
                              if doc.metadata.get('file_type') == 'inline_comments')
    
    # Count errors
    with_errors = sum(1 for doc in parsed_docs if doc.parse_errors)
    
    return {
        "total_documents": total_docs,
        "readme_files": readme_count,
        "doc_folder_files": doc_folder_count,
        "inline_comment_files": inline_comment_count,
        "total_content_length": total_content_length,
        "documents_with_errors": with_errors
    }
