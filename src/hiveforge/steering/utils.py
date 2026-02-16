"""
Utility functions for the Steering Assistant feature.

This module provides core utilities for staging folder management,
file type detection, and other common operations.
"""

import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)


# Supported file extensions for each category
SUPPORTED_MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}

# All supported extensions combined
ALL_SUPPORTED_EXTENSIONS = (
    SUPPORTED_MARKDOWN_EXTENSIONS | 
    SUPPORTED_PDF_EXTENSIONS | 
    SUPPORTED_IMAGE_EXTENSIONS
)


def create_staging_directory(staging_dir: Path) -> None:
    """
    Create the staging directory if it does not exist.
    
    This function ensures the .kiro/onboarding/ directory exists and is ready
    for users to place their source artifacts.
    
    Args:
        staging_dir: Path to the staging directory (typically .kiro/onboarding/)
        
    Raises:
        OSError: If directory creation fails due to permissions or other issues
        
    Requirements: 2.1
    """
    try:
        staging_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Staging directory ensured at: {staging_dir}")
    except OSError as e:
        logger.error(f"Failed to create staging directory {staging_dir}: {e}")
        raise


def is_supported_file_type(file_path: Path) -> bool:
    """
    Check if a file is a supported type for parsing.
    
    Supported types:
    - Markdown: .md, .markdown, .mdown, .mkd
    - PDF: .pdf
    - Images: .png, .jpg, .jpeg, .gif, .bmp, .tiff, .webp
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file extension is supported, False otherwise
        
    Requirements: 2.2
    """
    return file_path.suffix.lower() in ALL_SUPPORTED_EXTENSIONS


def get_file_type(file_path: Path) -> str:
    """
    Determine the type category of a supported file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        One of: "markdown", "pdf", "image", or "unknown"
        
    Requirements: 2.2
    """
    suffix = file_path.suffix.lower()
    
    if suffix in SUPPORTED_MARKDOWN_EXTENSIONS:
        return "markdown"
    elif suffix in SUPPORTED_PDF_EXTENSIONS:
        return "pdf"
    elif suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return "image"
    else:
        return "unknown"


def list_supported_files(staging_dir: Path) -> List[Path]:
    """
    List all supported files in the staging directory.
    
    This function recursively scans the staging directory and returns all files
    with supported extensions (markdown, PDF, images).
    
    Args:
        staging_dir: Path to the staging directory to scan
        
    Returns:
        List of Path objects for all supported files found, sorted by name
        
    Requirements: 2.2
    """
    if not staging_dir.exists():
        logger.warning(f"Staging directory does not exist: {staging_dir}")
        return []
    
    if not staging_dir.is_dir():
        logger.error(f"Staging path is not a directory: {staging_dir}")
        return []
    
    supported_files = []
    
    try:
        # Recursively find all files
        for file_path in staging_dir.rglob("*"):
            if file_path.is_file() and is_supported_file_type(file_path):
                supported_files.append(file_path)
                logger.debug(f"Found supported file: {file_path}")
    except OSError as e:
        logger.error(f"Error scanning staging directory {staging_dir}: {e}")
        raise
    
    # Sort by name for consistent ordering
    supported_files.sort(key=lambda p: str(p))
    
    logger.info(f"Found {len(supported_files)} supported files in {staging_dir}")
    return supported_files


def is_staging_folder_empty(staging_dir: Path) -> bool:
    """
    Check if the staging folder contains any supported files.
    
    Args:
        staging_dir: Path to the staging directory
        
    Returns:
        True if no supported files are found, False otherwise
        
    Requirements: 2.3
    """
    supported_files = list_supported_files(staging_dir)
    return len(supported_files) == 0


def categorize_files_by_type(file_paths: List[Path]) -> dict[str, List[Path]]:
    """
    Categorize a list of files by their type.
    
    Args:
        file_paths: List of file paths to categorize
        
    Returns:
        Dictionary mapping file types to lists of paths:
        {"markdown": [...], "pdf": [...], "image": [...]}
        
    Requirements: 2.2
    """
    categorized = {
        "markdown": [],
        "pdf": [],
        "image": [],
        "unknown": []
    }
    
    for file_path in file_paths:
        file_type = get_file_type(file_path)
        categorized[file_type].append(file_path)
    
    return categorized


def get_staging_directory_summary(staging_dir: Path) -> dict:
    """
    Get a summary of the staging directory contents.
    
    Args:
        staging_dir: Path to the staging directory
        
    Returns:
        Dictionary with summary information:
        {
            "exists": bool,
            "total_files": int,
            "markdown_count": int,
            "pdf_count": int,
            "image_count": int,
            "files_by_type": {"markdown": [...], "pdf": [...], "image": [...]},
            "is_empty": bool
        }
        
    Requirements: 2.2, 2.3
    """
    if not staging_dir.exists():
        return {
            "exists": False,
            "total_files": 0,
            "markdown_count": 0,
            "pdf_count": 0,
            "image_count": 0,
            "files_by_type": {"markdown": [], "pdf": [], "image": []},
            "is_empty": True
        }
    
    supported_files = list_supported_files(staging_dir)
    categorized = categorize_files_by_type(supported_files)
    
    return {
        "exists": True,
        "total_files": len(supported_files),
        "markdown_count": len(categorized["markdown"]),
        "pdf_count": len(categorized["pdf"]),
        "image_count": len(categorized["image"]),
        "files_by_type": {
            "markdown": categorized["markdown"],
            "pdf": categorized["pdf"],
            "image": categorized["image"]
        },
        "is_empty": len(supported_files) == 0
    }
