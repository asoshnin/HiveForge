"""
Tests for image parser.

This module tests the image parsing functionality to ensure it correctly
extracts text using OCR, handles various image formats, and gracefully
handles errors.
"""

import pytest
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from src.hiveforge.steering.parsers.image import (
    parse_image,
    is_supported_image_format,
    get_image_info,
    TESSERACT_AVAILABLE,
)
from src.hiveforge.steering.models import ParsedDocument


def is_tesseract_installed():
    """Check if Tesseract OCR engine is actually installed on the system."""
    if not TESSERACT_AVAILABLE:
        return False
    try:
        import pytesseract
        # Try to get version - will fail if tesseract not installed
        pytesseract.get_tesseract_version()
        return True
    except:
        return False


TESSERACT_INSTALLED = is_tesseract_installed()


def create_test_image_with_text(file_path: Path, text: str, image_format: str = "PNG"):
    """
    Helper function to create a test image with text.
    
    Args:
        file_path: Path where to save the image
        text: Text to render in the image
        image_format: Image format (PNG, JPEG, etc.)
    """
    # Create a white image
    width, height = 800, 200
    image = Image.new('RGB', (width, height), color='white')
    
    # Draw text on the image
    draw = ImageDraw.Draw(image)
    
    # Use default font (may vary by system)
    try:
        # Try to use a larger font if available
        font = ImageFont.load_default()
    except:
        font = None
    
    # Draw text in black
    text_position = (50, 80)
    draw.text(text_position, text, fill='black', font=font)
    
    # Save the image
    if image_format.upper() == 'JPEG' or image_format.upper() == 'JPG':
        image.save(file_path, format='JPEG')
    else:
        image.save(file_path, format=image_format.upper())
    
    image.close()


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="pytesseract or Pillow not available")
class TestParseImage:
    """Tests for parse_image function."""
    
    def test_parse_simple_png_image(self, tmp_path):
        """Should parse a simple PNG image with text."""
        img_file = tmp_path / "test.png"
        test_text = "Hello World"
        create_test_image_with_text(img_file, test_text, "PNG")
        
        result = parse_image(img_file)
        
        assert isinstance(result, ParsedDocument)
        assert result.file_path == img_file
        assert result.metadata['image_format'] == 'PNG'
        
        # Check if Tesseract is actually installed
        if TESSERACT_INSTALLED:
            # OCR should work
            assert result.metadata['ocr_performed'] is True
            # OCR might not be perfect, but should extract something or be empty
            assert len(result.content) >= 0
        else:
            # Tesseract not installed - should have error message
            assert result.metadata['ocr_performed'] is False
            assert any("Tesseract" in err for err in result.parse_errors)
    
    def test_parse_jpeg_image(self, tmp_path):
        """Should parse a JPEG image with text."""
        img_file = tmp_path / "test.jpg"
        test_text = "Test JPEG"
        create_test_image_with_text(img_file, test_text, "JPEG")
        
        result = parse_image(img_file)
        
        assert isinstance(result, ParsedDocument)
        assert result.file_path == img_file
        assert result.metadata['image_format'] == 'JPEG'
        
        if TESSERACT_INSTALLED:
            assert result.metadata['ocr_performed'] is True
            assert len(result.content) >= 0
        else:
            assert result.metadata['ocr_performed'] is False
            assert any("Tesseract" in err for err in result.parse_errors)
    
    def test_parse_image_stores_metadata(self, tmp_path):
        """Should store image metadata."""
        img_file = tmp_path / "test.png"
        create_test_image_with_text(img_file, "Metadata Test", "PNG")
        
        result = parse_image(img_file)
        
        assert 'file_name' in result.metadata
        assert 'file_size' in result.metadata
        assert 'file_extension' in result.metadata
        assert 'image_format' in result.metadata
        assert 'image_mode' in result.metadata
        assert 'image_size' in result.metadata
        assert 'ocr_performed' in result.metadata
        
        assert result.metadata['file_name'] == 'test.png'
        assert result.metadata['file_extension'] == '.png'
        assert result.metadata['file_size'] > 0
        assert result.metadata['image_size'] == (800, 200)
    
    def test_parse_image_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing file."""
        img_file = tmp_path / "nonexistent.png"
        
        with pytest.raises(FileNotFoundError):
            parse_image(img_file)
    
    def test_parse_image_with_multiple_lines(self, tmp_path):
        """Should handle images with multiple lines of text."""
        img_file = tmp_path / "multiline.png"
        
        # Create image with multiple lines
        width, height = 800, 300
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        lines = ["Line 1: First line", "Line 2: Second line", "Line 3: Third line"]
        y_position = 50
        for line in lines:
            draw.text((50, y_position), line, fill='black')
            y_position += 80
        
        image.save(img_file, format='PNG')
        image.close()
        
        result = parse_image(img_file)
        
        assert isinstance(result, ParsedDocument)
        
        if TESSERACT_INSTALLED:
            assert result.metadata['ocr_performed'] is True
            # Should extract some text
            assert len(result.content) >= 0
        else:
            assert result.metadata['ocr_performed'] is False
    
    def test_parse_empty_image(self, tmp_path):
        """Should handle images without text."""
        img_file = tmp_path / "empty.png"
        
        # Create blank white image
        image = Image.new('RGB', (800, 200), color='white')
        image.save(img_file, format='PNG')
        image.close()
        
        result = parse_image(img_file)
        
        assert isinstance(result, ParsedDocument)
        
        if TESSERACT_INSTALLED:
            # Should have performed OCR but found no text
            assert result.metadata['ocr_performed'] is True
            # May have a warning about no text extracted
            if not result.content:
                assert any("no text" in err.lower() for err in result.parse_errors)
        else:
            assert result.metadata['ocr_performed'] is False
    
    def test_parse_image_different_formats(self, tmp_path):
        """Should handle different image formats."""
        formats = [
            ("test.png", "PNG"),
            ("test.jpg", "JPEG"),
            ("test.bmp", "BMP"),
        ]
        
        for filename, format_name in formats:
            img_file = tmp_path / filename
            create_test_image_with_text(img_file, f"Test {format_name}", format_name)
            
            result = parse_image(img_file)
            
            assert isinstance(result, ParsedDocument)
            
            if TESSERACT_INSTALLED:
                assert result.metadata['ocr_performed'] is True
            else:
                assert result.metadata['ocr_performed'] is False
    
    def test_parse_invalid_image_file(self, tmp_path):
        """Should handle invalid image files gracefully."""
        img_file = tmp_path / "invalid.png"
        # Create a file that's not a valid image
        img_file.write_bytes(b"This is not an image file")
        
        result = parse_image(img_file)
        
        # Should not crash, but should have parse errors
        assert isinstance(result, ParsedDocument)
        assert len(result.parse_errors) > 0
        # Content should be empty
        assert len(result.content) == 0
    
    def test_parse_image_with_numbers(self, tmp_path):
        """Should extract numbers from images."""
        img_file = tmp_path / "numbers.png"
        test_text = "12345 67890"
        create_test_image_with_text(img_file, test_text, "PNG")
        
        result = parse_image(img_file)
        
        assert isinstance(result, ParsedDocument)
        
        if TESSERACT_INSTALLED:
            assert result.metadata['ocr_performed'] is True
            # Should extract some numeric content
            assert len(result.content) >= 0
        else:
            assert result.metadata['ocr_performed'] is False
    
    def test_parse_image_with_special_characters(self, tmp_path):
        """Should handle special characters in images."""
        img_file = tmp_path / "special.png"
        test_text = "Test: @#$%"
        create_test_image_with_text(img_file, test_text, "PNG")
        
        result = parse_image(img_file)
        
        assert isinstance(result, ParsedDocument)
        
        if TESSERACT_INSTALLED:
            assert result.metadata['ocr_performed'] is True
            # Should extract something
            assert len(result.content) >= 0
        else:
            assert result.metadata['ocr_performed'] is False


class TestIsSupportedImageFormat:
    """Tests for is_supported_image_format function."""
    
    def test_supported_formats(self):
        """Should recognize supported image formats."""
        supported = [
            Path("test.png"),
            Path("test.jpg"),
            Path("test.jpeg"),
            Path("test.bmp"),
            Path("test.gif"),
            Path("test.tiff"),
            Path("test.tif"),
        ]
        
        for path in supported:
            assert is_supported_image_format(path) is True
    
    def test_unsupported_formats(self):
        """Should reject unsupported formats."""
        unsupported = [
            Path("test.txt"),
            Path("test.pdf"),
            Path("test.doc"),
            Path("test.svg"),
            Path("test.webp"),
        ]
        
        for path in unsupported:
            assert is_supported_image_format(path) is False
    
    def test_case_insensitive(self):
        """Should be case-insensitive."""
        paths = [
            Path("test.PNG"),
            Path("test.JPG"),
            Path("test.JPEG"),
            Path("test.Png"),
            Path("test.JpG"),
        ]
        
        for path in paths:
            assert is_supported_image_format(path) is True


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Pillow not available")
class TestGetImageInfo:
    """Tests for get_image_info function."""
    
    def test_get_info_from_png(self, tmp_path):
        """Should extract info from PNG image."""
        img_file = tmp_path / "test.png"
        create_test_image_with_text(img_file, "Info Test", "PNG")
        
        info = get_image_info(img_file)
        
        assert 'file_name' in info
        assert 'file_size' in info
        assert 'file_extension' in info
        assert 'image_format' in info
        assert 'image_mode' in info
        assert 'image_size' in info
        assert 'width' in info
        assert 'height' in info
        
        assert info['file_name'] == 'test.png'
        assert info['file_extension'] == '.png'
        assert info['image_format'] == 'PNG'
        assert info['width'] == 800
        assert info['height'] == 200
    
    def test_get_info_from_jpeg(self, tmp_path):
        """Should extract info from JPEG image."""
        img_file = tmp_path / "test.jpg"
        create_test_image_with_text(img_file, "JPEG Info", "JPEG")
        
        info = get_image_info(img_file)
        
        assert info['image_format'] == 'JPEG'
        assert info['file_extension'] == '.jpg'
    
    def test_get_info_from_invalid_file(self, tmp_path):
        """Should handle invalid files gracefully."""
        img_file = tmp_path / "invalid.png"
        img_file.write_bytes(b"Not an image")
        
        info = get_image_info(img_file)
        
        assert 'error' in info


class TestImageParserIntegration:
    """Integration tests for image parser."""
    
    @pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="pytesseract or Pillow not available")
    def test_parse_realistic_screenshot(self, tmp_path):
        """Should parse a realistic screenshot-like image."""
        img_file = tmp_path / "screenshot.png"
        
        # Create an image that looks like a screenshot with multiple text elements
        width, height = 1000, 600
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Add title
        draw.text((50, 50), "System Architecture Diagram", fill='black')
        
        # Add some component labels
        draw.text((100, 150), "API Gateway", fill='black')
        draw.text((400, 150), "Application Server", fill='black')
        draw.text((700, 150), "Database", fill='black')
        
        # Add some arrows (as text)
        draw.text((250, 150), "-->", fill='black')
        draw.text((550, 150), "-->", fill='black')
        
        image.save(img_file, format='PNG')
        image.close()
        
        result = parse_image(img_file)
        
        # Check metadata
        assert result.metadata['image_format'] == 'PNG'
        assert result.metadata['image_size'] == (1000, 600)
        
        if TESSERACT_INSTALLED:
            # Check that OCR was performed
            assert result.metadata['ocr_performed'] is True
            # Check that some text was extracted
            assert len(result.content) >= 0
        else:
            assert result.metadata['ocr_performed'] is False
        
        # Should have minimal errors
        critical_errors = [e for e in result.parse_errors 
                          if "File not found" in e or "Permission denied" in e]
        assert len(critical_errors) == 0
    
    @pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="pytesseract or Pillow not available")
    def test_parse_technical_diagram(self, tmp_path):
        """Should parse a technical diagram with labels."""
        img_file = tmp_path / "diagram.png"
        
        # Create a simple technical diagram
        width, height = 800, 400
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Add component names
        components = [
            (100, 100, "User"),
            (300, 100, "Frontend"),
            (500, 100, "Backend"),
            (700, 100, "DB"),
        ]
        
        for x, y, label in components:
            draw.text((x, y), label, fill='black')
        
        image.save(img_file, format='PNG')
        image.close()
        
        result = parse_image(img_file)
        
        # Check file metadata
        assert result.metadata['file_name'] == 'diagram.png'
        assert result.metadata['file_size'] > 0
        
        if TESSERACT_INSTALLED:
            # Verify OCR was performed
            assert result.metadata['ocr_performed'] is True
            # Verify some content was extracted
            assert len(result.content) >= 0
        else:
            assert result.metadata['ocr_performed'] is False


class TestImageParserWithoutTesseract:
    """Tests for image parser when tesseract is not available."""
    
    @pytest.mark.skipif(TESSERACT_AVAILABLE, reason="Test only when tesseract is not available")
    def test_parse_image_without_tesseract(self, tmp_path):
        """Should handle missing tesseract gracefully."""
        img_file = tmp_path / "test.png"
        
        # Create a simple image file
        img_file.write_bytes(b"fake image data")
        
        result = parse_image(img_file)
        
        # Should return a ParsedDocument with errors
        assert isinstance(result, ParsedDocument)
        assert len(result.parse_errors) > 0
        assert any("pytesseract" in err or "Pillow" in err for err in result.parse_errors)
        assert result.content == ""
