"""
Document parser orchestrator for the Steering Assistant.

This module provides the main orchestrator that coordinates parsing of all
supported file types in the staging directory, with error handling and
aggregation of results.
"""

import logging
from pathlib import Path
from typing import List

from ..models import ParsedDocument
from ..utils import list_supported_files, get_file_type
from .markdown import parse_markdown
from .pdf import parse_pdf
from .image import parse_image

logger = logging.getLogger(__name__)


def parse_directory(staging_dir: Path) -> List[ParsedDocument]:
    """
    Parse all supported files in the staging directory.
    
    This function:
    - Discovers all supported files (markdown, PDF, images) in the directory
    - Parses each file using the appropriate parser
    - Handles parsing failures gracefully (logs error and continues)
    - Aggregates all results into a list of ParsedDocument objects
    
    The function implements resilient parsing: if one file fails to parse,
    it logs the error and continues processing remaining files. This ensures
    that a single corrupted file doesn't block the entire workflow.
    
    Args:
        staging_dir: Path to the staging directory containing source artifacts
        
    Returns:
        List of ParsedDocument objects, one for each successfully discovered file.
        Files that fail to parse will still have a ParsedDocument entry with
        parse_errors populated.
        
    Requirements: 3.4, 3.5
    """
    logger.info(f"Starting directory parsing: {staging_dir}")
    
    # Discover all supported files
    try:
        file_paths = list_supported_files(staging_dir)
        logger.info(f"Found {len(file_paths)} supported files to parse")
    except Exception as e:
        logger.error(f"Failed to list files in staging directory: {e}")
        return []
    
    if not file_paths:
        logger.warning(f"No supported files found in {staging_dir}")
        return []
    
    # Parse each file with appropriate parser
    parsed_documents = []
    
    for file_path in file_paths:
        try:
            file_type = get_file_type(file_path)
            logger.debug(f"Parsing {file_type} file: {file_path}")
            
            # Route to appropriate parser based on file type
            if file_type == "markdown":
                parsed_doc = parse_markdown(file_path)
            elif file_type == "pdf":
                parsed_doc = parse_pdf(file_path)
            elif file_type == "image":
                parsed_doc = parse_image(file_path)
            else:
                # Unknown file type - create error document
                logger.warning(f"Unknown file type for: {file_path}")
                parsed_doc = ParsedDocument(
                    file_path=file_path,
                    content="",
                    metadata={"file_type": "unknown"},
                    parse_errors=[f"Unsupported file type: {file_path.suffix}"]
                )
            
            # Add to results
            parsed_documents.append(parsed_doc)
            
            # Log parsing result
            if parsed_doc.parse_errors:
                logger.warning(
                    f"Parsed {file_path.name} with {len(parsed_doc.parse_errors)} errors: "
                    f"{'; '.join(parsed_doc.parse_errors[:2])}"
                )
            else:
                logger.info(
                    f"Successfully parsed {file_path.name} "
                    f"({len(parsed_doc.content)} characters)"
                )
        
        except FileNotFoundError:
            # File was deleted between discovery and parsing
            logger.error(f"File not found during parsing: {file_path}")
            parsed_documents.append(ParsedDocument(
                file_path=file_path,
                content="",
                metadata={},
                parse_errors=[f"File not found: {file_path}"]
            ))
        
        except PermissionError:
            # Permission denied reading file
            logger.error(f"Permission denied reading file: {file_path}")
            parsed_documents.append(ParsedDocument(
                file_path=file_path,
                content="",
                metadata={},
                parse_errors=[f"Permission denied: {file_path}"]
            ))
        
        except Exception as e:
            # Unexpected error - log and continue with other files
            logger.error(f"Unexpected error parsing {file_path}: {e}", exc_info=True)
            parsed_documents.append(ParsedDocument(
                file_path=file_path,
                content="",
                metadata={},
                parse_errors=[f"Unexpected error: {str(e)}"]
            ))
    
    # Log summary
    successful_parses = sum(1 for doc in parsed_documents if not doc.parse_errors)
    failed_parses = len(parsed_documents) - successful_parses
    
    logger.info(
        f"Directory parsing complete: {successful_parses} successful, "
        f"{failed_parses} with errors"
    )
    
    return parsed_documents


def get_parsing_summary(parsed_documents: List[ParsedDocument]) -> dict:
    """
    Generate a summary of parsing results.
    
    Args:
        parsed_documents: List of parsed documents
        
    Returns:
        Dictionary with summary statistics:
        {
            "total_files": int,
            "successful": int,
            "with_errors": int,
            "total_content_length": int,
            "files_by_type": {"markdown": int, "pdf": int, "image": int},
            "error_summary": List[str]
        }
    """
    total_files = len(parsed_documents)
    successful = sum(1 for doc in parsed_documents if not doc.parse_errors)
    with_errors = total_files - successful
    total_content_length = sum(len(doc.content) for doc in parsed_documents)
    
    # Count by file type
    files_by_type = {"markdown": 0, "pdf": 0, "image": 0, "unknown": 0}
    for doc in parsed_documents:
        file_type = get_file_type(doc.file_path)
        files_by_type[file_type] += 1
    
    # Collect error summary (first error from each failed file)
    error_summary = []
    for doc in parsed_documents:
        if doc.parse_errors:
            error_summary.append(f"{doc.file_path.name}: {doc.parse_errors[0]}")
    
    return {
        "total_files": total_files,
        "successful": successful,
        "with_errors": with_errors,
        "total_content_length": total_content_length,
        "files_by_type": files_by_type,
        "error_summary": error_summary
    }
