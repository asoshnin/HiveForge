"""
Markdown parser for the Steering Assistant.

This module provides functionality to parse markdown files and extract
text content while preserving structure, code blocks, and Mermaid diagrams.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List

from ..models import ParsedDocument
from ..error_handling import ErrorRecovery

logger = logging.getLogger(__name__)


def parse_markdown(file_path: Path) -> ParsedDocument:
    """
    Parse a markdown file and extract text content and structure.
    
    This function:
    - Handles multi-language content (UTF-8 encoding)
    - Preserves code blocks with language tags
    - Preserves Mermaid diagrams
    - Extracts metadata from frontmatter if present
    
    Args:
        file_path: Path to the markdown file to parse
        
    Returns:
        ParsedDocument containing the extracted content and metadata
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    parse_errors: List[str] = []
    metadata: Dict[str, Any] = {}
    content = ""
    
    try:
        # Read file with UTF-8 encoding to handle multi-language content
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Extract frontmatter if present (YAML between --- markers)
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', raw_content, re.DOTALL)
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            # Simple YAML parsing for common key: value pairs
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            # Remove frontmatter from content
            content = raw_content[frontmatter_match.end():]
        else:
            content = raw_content
        
        # Preserve code blocks and Mermaid diagrams by marking them
        # This ensures they're kept intact in the extracted content
        content = _preserve_code_blocks(content)
        
        # Store file metadata
        metadata['file_size'] = file_path.stat().st_size
        metadata['file_name'] = file_path.name
        
    except FileNotFoundError as e:
        error_context = ErrorRecovery.handle_file_system_error(e, file_path, "read")
        logger.error(str(error_context))
        parse_errors.append(f"File not found: {file_path}")
        raise
    except PermissionError as e:
        error_context = ErrorRecovery.handle_file_system_error(e, file_path, "read")
        logger.error(str(error_context))
        parse_errors.append(f"Permission denied reading file: {file_path}")
        raise
    except UnicodeDecodeError as e:
        error_context = ErrorRecovery.handle_parsing_error(e, file_path, "markdown")
        logger.warning(str(error_context))
        parse_errors.append(f"Encoding error: {e}")
        
        # Try with fallback encodings
        logger.info("Attempting fallback encodings")
        for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                logger.debug(f"Trying encoding: {encoding}")
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                parse_errors.append(f"Fallback to {encoding} encoding succeeded")
                logger.info(f"Successfully parsed with {encoding} encoding")
                break
            except Exception as fallback_error:
                logger.debug(f"Encoding {encoding} failed: {fallback_error}")
                continue
        else:
            # All encodings failed
            logger.error("All fallback encodings failed")
            parse_errors.append("All fallback encodings failed")
            content = ""
    except Exception as e:
        error_context = ErrorRecovery.handle_parsing_error(e, file_path, "markdown")
        logger.error(str(error_context))
        parse_errors.append(f"Unexpected error parsing markdown: {e}")
        content = ""
    
    return ParsedDocument(
        file_path=file_path,
        content=content,
        metadata=metadata,
        parse_errors=parse_errors
    )


def _preserve_code_blocks(content: str) -> str:
    """
    Preserve code blocks and Mermaid diagrams in markdown content.
    
    This function identifies code blocks (```language ... ```) and ensures
    they are kept intact with their language tags. Special handling for
    Mermaid diagrams.
    
    Args:
        content: Raw markdown content
        
    Returns:
        Content with code blocks preserved
    """
    # Pattern to match code blocks: ```language\n...code...\n```
    # This preserves the language tag and the code content
    code_block_pattern = re.compile(
        r'```(\w*)\n(.*?)```',
        re.DOTALL
    )
    
    # The content is already in the correct format, we just need to ensure
    # it's not modified. The regex pattern above will match and preserve:
    # - Language identifier (e.g., python, javascript, mermaid)
    # - Code content between the backticks
    # - The structure of the code block
    
    # We don't need to transform the content, just validate it's preserved
    # The content will be returned as-is, which maintains code blocks
    return content


def extract_headers(content: str) -> List[Dict[str, Any]]:
    """
    Extract markdown headers from content.
    
    Args:
        content: Markdown content
        
    Returns:
        List of dictionaries with header level and text
    """
    headers = []
    header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    for match in header_pattern.finditer(content):
        level = len(match.group(1))
        text = match.group(2).strip()
        headers.append({
            'level': level,
            'text': text
        })
    
    return headers


def extract_code_blocks(content: str) -> List[Dict[str, str]]:
    """
    Extract all code blocks from markdown content.
    
    Args:
        content: Markdown content
        
    Returns:
        List of dictionaries with language and code content
    """
    code_blocks = []
    code_block_pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    
    for match in code_block_pattern.finditer(content):
        language = match.group(1) or 'text'
        code = match.group(2)
        code_blocks.append({
            'language': language,
            'code': code
        })
    
    return code_blocks
