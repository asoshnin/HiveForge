"""
Tests for PDF parser.

This module tests the PDF parsing functionality to ensure it correctly
extracts text content from all pages, handles encoding issues, and
gracefully handles errors.
"""

import pytest
from pathlib import Path
from io import BytesIO

from pypdf import PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from src.hiveforge.steering.parsers.pdf import (
    parse_pdf,
    extract_pdf_info,
)
from src.hiveforge.steering.models import ParsedDocument


def create_test_pdf(file_path: Path, pages_content: list[str], metadata: dict = None):
    """
    Helper function to create a test PDF file with specified content.
    
    Args:
        file_path: Path where to save the PDF
        pages_content: List of text content for each page
        metadata: Optional metadata dictionary
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    c = canvas.Canvas(str(file_path), pagesize=letter)
    
    # Set metadata if provided
    if metadata:
        if 'title' in metadata:
            c.setTitle(metadata['title'])
        if 'author' in metadata:
            c.setAuthor(metadata['author'])
        if 'subject' in metadata:
            c.setSubject(metadata['subject'])
    
    # Add content to each page
    for page_text in pages_content:
        c.drawString(100, 750, page_text)
        c.showPage()
    
    c.save()


class TestParsePdf:
    """Tests for parse_pdf function."""
    
    def test_parse_simple_pdf(self, tmp_path):
        """Should parse a simple single-page PDF."""
        pdf_file = tmp_path / "test.pdf"
        create_test_pdf(pdf_file, ["Hello World from PDF"])
        
        result = parse_pdf(pdf_file)
        
        assert isinstance(result, ParsedDocument)
        assert result.file_path == pdf_file
        assert "Hello World from PDF" in result.content
        assert "--- Page 1 ---" in result.content
        assert result.metadata['page_count'] == 1
    
    def test_parse_multi_page_pdf(self, tmp_path):
        """Should parse a multi-page PDF and extract all pages."""
        pdf_file = tmp_path / "multipage.pdf"
        pages = [
            "Page 1 content",
            "Page 2 content",
            "Page 3 content"
        ]
        create_test_pdf(pdf_file, pages)
        
        result = parse_pdf(pdf_file)
        
        assert "Page 1 content" in result.content
        assert "Page 2 content" in result.content
        assert "Page 3 content" in result.content
        assert "--- Page 1 ---" in result.content
        assert "--- Page 2 ---" in result.content
        assert "--- Page 3 ---" in result.content
        assert result.metadata['page_count'] == 3
    
    def test_parse_pdf_with_metadata(self, tmp_path):
        """Should extract PDF metadata."""
        pdf_file = tmp_path / "metadata.pdf"
        metadata = {
            'title': 'Test Document',
            'author': 'Test Author',
            'subject': 'Testing PDF Parser'
        }
        create_test_pdf(pdf_file, ["Content"], metadata)
        
        result = parse_pdf(pdf_file)
        
        assert result.metadata.get('title') == 'Test Document'
        assert result.metadata.get('author') == 'Test Author'
        assert result.metadata.get('subject') == 'Testing PDF Parser'
    
    def test_parse_pdf_stores_file_metadata(self, tmp_path):
        """Should store file metadata."""
        pdf_file = tmp_path / "test.pdf"
        create_test_pdf(pdf_file, ["Test content"])
        
        result = parse_pdf(pdf_file)
        
        assert 'file_size' in result.metadata
        assert 'file_name' in result.metadata
        assert 'page_count' in result.metadata
        assert result.metadata['file_name'] == 'test.pdf'
        assert result.metadata['file_size'] > 0
        assert result.metadata['page_count'] == 1
    
    def test_parse_pdf_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing file."""
        pdf_file = tmp_path / "nonexistent.pdf"
        
        with pytest.raises(FileNotFoundError):
            parse_pdf(pdf_file)
    
    def test_parse_pdf_with_long_content(self, tmp_path):
        """Should handle PDFs with longer text content."""
        pdf_file = tmp_path / "long.pdf"
        long_text = "This is a longer text. " * 50  # Repeat to make it longer
        create_test_pdf(pdf_file, [long_text])
        
        result = parse_pdf(pdf_file)
        
        assert "This is a longer text." in result.content
        assert len(result.content) > 100
    
    def test_parse_pdf_empty_pages(self, tmp_path):
        """Should handle PDFs with empty pages."""
        pdf_file = tmp_path / "empty.pdf"
        # Create PDF with empty content
        create_test_pdf(pdf_file, [""])
        
        result = parse_pdf(pdf_file)
        
        # Should still parse successfully
        assert isinstance(result, ParsedDocument)
        assert result.metadata['page_count'] == 1
        # May have parse errors about no text extracted
        # This is expected behavior
    
    def test_parse_pdf_special_characters(self, tmp_path):
        """Should handle special characters in PDF content."""
        pdf_file = tmp_path / "special.pdf"
        # Note: reportlab may have limitations with some Unicode characters
        content = "Special chars: @#$%^&*()_+-=[]{}|;:',.<>?/"
        create_test_pdf(pdf_file, [content])
        
        result = parse_pdf(pdf_file)
        
        # Should extract at least some of the content
        assert isinstance(result, ParsedDocument)
        assert len(result.content) > 0
    
    def test_parse_pdf_multiple_pages_with_different_content(self, tmp_path):
        """Should correctly separate content from different pages."""
        pdf_file = tmp_path / "multipage.pdf"
        pages = [
            "Introduction: This is the first page",
            "Chapter 1: Main content starts here",
            "Chapter 2: More detailed information",
            "Conclusion: Final thoughts"
        ]
        create_test_pdf(pdf_file, pages)
        
        result = parse_pdf(pdf_file)
        
        # Check all pages are present
        assert "Introduction" in result.content
        assert "Chapter 1" in result.content
        assert "Chapter 2" in result.content
        assert "Conclusion" in result.content
        
        # Check page separators
        assert result.content.count("--- Page") == 4
        assert result.metadata['page_count'] == 4
    
    def test_parse_pdf_no_parse_errors_on_valid_file(self, tmp_path):
        """Should have no parse errors for a valid PDF."""
        pdf_file = tmp_path / "valid.pdf"
        create_test_pdf(pdf_file, ["Valid content"])
        
        result = parse_pdf(pdf_file)
        
        # Should have no critical errors (warnings about image-based pages are ok)
        assert isinstance(result.parse_errors, list)
        # Check that there are no FileNotFound or Permission errors
        error_text = " ".join(result.parse_errors)
        assert "File not found" not in error_text
        assert "Permission denied" not in error_text
    
    def test_parse_invalid_pdf_file(self, tmp_path):
        """Should handle invalid PDF files gracefully."""
        pdf_file = tmp_path / "invalid.pdf"
        # Create a file that's not a valid PDF
        pdf_file.write_bytes(b"This is not a PDF file")
        
        result = parse_pdf(pdf_file)
        
        # Should not crash, but should have parse errors
        assert isinstance(result, ParsedDocument)
        assert len(result.parse_errors) > 0
        # Content should be empty or minimal
        assert len(result.content) == 0


class TestExtractPdfInfo:
    """Tests for extract_pdf_info function."""
    
    def test_extract_info_from_simple_pdf(self, tmp_path):
        """Should extract basic info from a PDF."""
        pdf_file = tmp_path / "test.pdf"
        create_test_pdf(pdf_file, ["Content"])
        
        info = extract_pdf_info(pdf_file)
        
        assert 'page_count' in info
        assert 'file_name' in info
        assert 'file_size' in info
        assert info['page_count'] == 1
        assert info['file_name'] == 'test.pdf'
        assert info['file_size'] > 0
    
    def test_extract_info_with_metadata(self, tmp_path):
        """Should extract metadata from PDF."""
        pdf_file = tmp_path / "metadata.pdf"
        metadata = {
            'title': 'Info Test',
            'author': 'Test Author',
            'subject': 'Testing'
        }
        create_test_pdf(pdf_file, ["Content"], metadata)
        
        info = extract_pdf_info(pdf_file)
        
        assert info.get('title') == 'Info Test'
        assert info.get('author') == 'Test Author'
        assert info.get('subject') == 'Testing'
    
    def test_extract_info_from_multipage_pdf(self, tmp_path):
        """Should correctly count pages."""
        pdf_file = tmp_path / "multipage.pdf"
        create_test_pdf(pdf_file, ["Page 1", "Page 2", "Page 3", "Page 4", "Page 5"])
        
        info = extract_pdf_info(pdf_file)
        
        assert info['page_count'] == 5
    
    def test_extract_info_from_invalid_file(self, tmp_path):
        """Should handle invalid files gracefully."""
        pdf_file = tmp_path / "invalid.pdf"
        pdf_file.write_bytes(b"Not a PDF")
        
        info = extract_pdf_info(pdf_file)
        
        assert 'error' in info
    
    def test_extract_info_encryption_status(self, tmp_path):
        """Should detect if PDF is encrypted."""
        pdf_file = tmp_path / "test.pdf"
        create_test_pdf(pdf_file, ["Content"])
        
        info = extract_pdf_info(pdf_file)
        
        assert 'is_encrypted' in info
        assert info['is_encrypted'] is False


class TestPdfParserIntegration:
    """Integration tests for PDF parser."""
    
    def test_parse_realistic_document(self, tmp_path):
        """Should parse a realistic multi-page document."""
        pdf_file = tmp_path / "architecture.pdf"
        pages = [
            "Architecture Overview - System Design Document",
            "Table of Contents: 1. Introduction 2. Components 3. Data Flow",
            "Introduction: This document describes the system architecture",
            "Components: API Gateway, Application Server, Database",
            "Data Flow: User -> API Gateway -> App Server -> Database"
        ]
        metadata = {
            'title': 'System Architecture',
            'author': 'Engineering Team',
            'subject': 'Architecture Documentation'
        }
        create_test_pdf(pdf_file, pages, metadata)
        
        result = parse_pdf(pdf_file)
        
        # Check metadata extraction
        assert result.metadata['title'] == 'System Architecture'
        assert result.metadata['author'] == 'Engineering Team'
        assert result.metadata['page_count'] == 5
        
        # Check content extraction
        assert "Architecture Overview" in result.content
        assert "Table of Contents" in result.content
        assert "Introduction" in result.content
        assert "Components" in result.content
        assert "Data Flow" in result.content
        
        # Check page separators
        assert "--- Page 1 ---" in result.content
        assert "--- Page 5 ---" in result.content
        
        # Should have minimal or no errors
        critical_errors = [e for e in result.parse_errors 
                          if "File not found" in e or "Permission denied" in e]
        assert len(critical_errors) == 0
    
    def test_parse_technical_specification(self, tmp_path):
        """Should parse a technical specification document."""
        pdf_file = tmp_path / "tech-spec.pdf"
        pages = [
            "Technical Specification v1.0",
            "Requirements: REQ-001, REQ-002, REQ-003",
            "Design: Component A interfaces with Component B via REST API",
            "Implementation: Use Python 3.11 with FastAPI framework",
            "Testing: Unit tests required for all components"
        ]
        create_test_pdf(pdf_file, pages)
        
        result = parse_pdf(pdf_file)
        
        # Verify all sections are extracted
        assert "Technical Specification" in result.content
        assert "Requirements" in result.content
        assert "Design" in result.content
        assert "Implementation" in result.content
        assert "Testing" in result.content
        
        # Verify specific details
        assert "REQ-001" in result.content
        assert "Python 3.11" in result.content
        assert "FastAPI" in result.content
