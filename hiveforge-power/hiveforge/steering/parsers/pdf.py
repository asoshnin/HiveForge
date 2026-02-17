"""
PDF parser for the Steering Assistant.

This module provides functionality to parse PDF files and extract
text content from all pages with fallback strategies for encoding issues.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ..models import ParsedDocument
from ..error_handling import ErrorRecovery, safe_file_operation

logger = logging.getLogger(__name__)


def parse_pdf(file_path: Path) -> ParsedDocument:
    """
    Parse a PDF file and extract text content from all pages.
    
    This function:
    - Extracts text from all pages in the PDF
    - Handles encoding issues with fallback strategies
    - Collects metadata from PDF properties
    - Gracefully handles corrupted or encrypted PDFs
    
    Args:
        file_path: Path to the PDF file to parse
        
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
        # Open and read the PDF file
        reader = PdfReader(str(file_path))
        
        # Extract PDF metadata
        if reader.metadata:
            try:
                # Common PDF metadata fields
                if reader.metadata.title:
                    metadata['title'] = reader.metadata.title
                if reader.metadata.author:
                    metadata['author'] = reader.metadata.author
                if reader.metadata.subject:
                    metadata['subject'] = reader.metadata.subject
                if reader.metadata.creator:
                    metadata['creator'] = reader.metadata.creator
                if reader.metadata.producer:
                    metadata['producer'] = reader.metadata.producer
            except Exception as e:
                parse_errors.append(f"Error extracting PDF metadata: {e}")
        
        # Store page count
        num_pages = len(reader.pages)
        metadata['page_count'] = num_pages
        metadata['file_name'] = file_path.name
        metadata['file_size'] = file_path.stat().st_size
        
        # Extract text from all pages
        page_texts = []
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    # Add page separator for clarity
                    page_texts.append(f"--- Page {page_num} ---\n{page_text}")
                else:
                    parse_errors.append(f"Page {page_num}: No text extracted (may be image-based)")
            except Exception as e:
                parse_errors.append(f"Page {page_num}: Error extracting text - {e}")
        
        # Combine all page texts
        content = "\n\n".join(page_texts)
        
        # If no content was extracted, add a warning
        if not content.strip():
            parse_errors.append("No text content extracted from PDF (may be image-based or encrypted)")
        
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
    except PdfReadError as e:
        error_context = ErrorRecovery.handle_parsing_error(e, file_path, "pdf")
        logger.warning(str(error_context))
        parse_errors.append(f"PDF read error: {e}")
        
        # Try fallback strategy: attempt to read with strict=False
        logger.info("Attempting fallback parsing with strict=False")
        try:
            reader = PdfReader(str(file_path), strict=False)
            num_pages = len(reader.pages)
            metadata['page_count'] = num_pages
            metadata['file_name'] = file_path.name
            metadata['file_size'] = file_path.stat().st_size
            
            page_texts = []
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        page_texts.append(f"--- Page {page_num} ---\n{page_text}")
                except Exception as page_error:
                    parse_errors.append(f"Page {page_num}: {page_error}")
            
            content = "\n\n".join(page_texts)
            parse_errors.append("Fallback parsing with strict=False succeeded")
            logger.info("Fallback parsing succeeded")
        except Exception as fallback_error:
            logger.error(f"Fallback parsing failed: {fallback_error}")
            parse_errors.append(f"Fallback parsing also failed: {fallback_error}")
            content = ""
    except Exception as e:
        error_context = ErrorRecovery.handle_parsing_error(e, file_path, "pdf")
        logger.error(str(error_context))
        parse_errors.append(f"Unexpected error parsing PDF: {e}")
        content = ""
    
    return ParsedDocument(
        file_path=file_path,
        content=content,
        metadata=metadata,
        parse_errors=parse_errors
    )


def extract_pdf_info(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata information from a PDF file without parsing content.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dictionary containing PDF metadata
    """
    info = {}
    
    try:
        reader = PdfReader(str(file_path))
        
        # Basic info
        info['page_count'] = len(reader.pages)
        info['file_name'] = file_path.name
        info['file_size'] = file_path.stat().st_size
        
        # Metadata
        if reader.metadata:
            if reader.metadata.title:
                info['title'] = reader.metadata.title
            if reader.metadata.author:
                info['author'] = reader.metadata.author
            if reader.metadata.subject:
                info['subject'] = reader.metadata.subject
        
        # Check if encrypted
        info['is_encrypted'] = reader.is_encrypted
        
    except Exception as e:
        info['error'] = str(e)
    
    return info
