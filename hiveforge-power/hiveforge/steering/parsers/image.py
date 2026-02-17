"""
Image parser for the Steering Assistant.

This module provides functionality to parse image files and extract
text content using OCR (Optical Character Recognition) via pytesseract.
"""

from pathlib import Path
from typing import Dict, Any, List

try:
    from PIL import Image
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from ..models import ParsedDocument


def parse_image(file_path: Path) -> ParsedDocument:
    """
    Parse an image file and extract text using OCR.
    
    This function:
    - Handles various image formats (PNG, JPG, JPEG, BMP, GIF, TIFF)
    - Extracts text using pytesseract OCR
    - Handles encoding and OCR errors gracefully
    - Provides detailed error messages when OCR fails
    
    Args:
        file_path: Path to the image file to parse
        
    Returns:
        ParsedDocument containing the extracted text and metadata
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    parse_errors: List[str] = []
    metadata: Dict[str, Any] = {}
    content = ""
    
    # Check if pytesseract is available
    if not TESSERACT_AVAILABLE:
        parse_errors.append(
            "pytesseract or Pillow not available. "
            "Install with: pip install pytesseract Pillow"
        )
        return ParsedDocument(
            file_path=file_path,
            content="",
            metadata=metadata,
            parse_errors=parse_errors
        )
    
    try:
        # Verify file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Store file metadata
        metadata['file_name'] = file_path.name
        metadata['file_size'] = file_path.stat().st_size
        metadata['file_extension'] = file_path.suffix.lower()
        
        # Open the image
        try:
            image = Image.open(file_path)
        except Exception as e:
            parse_errors.append(f"Failed to open image: {e}")
            raise
        
        # Store image metadata
        metadata['image_format'] = image.format
        metadata['image_mode'] = image.mode
        metadata['image_size'] = image.size  # (width, height)
        
        # Perform OCR
        try:
            # Extract text using pytesseract
            # Use default configuration for best results
            extracted_text = pytesseract.image_to_string(image)
            
            # Clean up the extracted text
            content = extracted_text.strip()
            
            # Store OCR metadata
            metadata['ocr_performed'] = True
            metadata['text_length'] = len(content)
            
            if not content:
                parse_errors.append(
                    "OCR completed but no text was extracted. "
                    "Image may not contain readable text."
                )
        
        except pytesseract.TesseractNotFoundError:
            parse_errors.append(
                "Tesseract OCR engine not found. "
                "Please install tesseract-ocr: "
                "apt-get install tesseract-ocr (Linux) or "
                "brew install tesseract (macOS)"
            )
            metadata['ocr_performed'] = False
        
        except Exception as e:
            parse_errors.append(f"OCR extraction failed: {e}")
            metadata['ocr_performed'] = False
        
        finally:
            # Close the image to free resources
            image.close()
    
    except FileNotFoundError:
        parse_errors.append(f"File not found: {file_path}")
        raise
    
    except PermissionError:
        parse_errors.append(f"Permission denied reading file: {file_path}")
        raise
    
    except Exception as e:
        parse_errors.append(f"Unexpected error parsing image: {e}")
        content = ""
    
    return ParsedDocument(
        file_path=file_path,
        content=content,
        metadata=metadata,
        parse_errors=parse_errors
    )


def is_supported_image_format(file_path: Path) -> bool:
    """
    Check if the file format is supported for OCR.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        True if the format is supported, False otherwise
    """
    supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.tif'}
    return file_path.suffix.lower() in supported_extensions


def get_image_info(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata information from an image file without performing OCR.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Dictionary containing image metadata
    """
    info = {}
    
    if not TESSERACT_AVAILABLE:
        info['error'] = "Pillow not available"
        return info
    
    try:
        # Basic file info
        info['file_name'] = file_path.name
        info['file_size'] = file_path.stat().st_size
        info['file_extension'] = file_path.suffix.lower()
        
        # Open image to get format info
        with Image.open(file_path) as image:
            info['image_format'] = image.format
            info['image_mode'] = image.mode
            info['image_size'] = image.size  # (width, height)
            info['width'] = image.size[0]
            info['height'] = image.size[1]
    
    except Exception as e:
        info['error'] = str(e)
    
    return info
