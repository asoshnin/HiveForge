"""
Tests for document parser orchestrator.

This module tests the orchestrator that coordinates parsing of all supported
file types, including error handling and result aggregation.
"""

import pytest
from pathlib import Path
from PIL import Image, ImageDraw

from src.hiveforge.steering.parsers.orchestrator import (
    parse_directory,
    get_parsing_summary
)
from src.hiveforge.steering.models import ParsedDocument


def create_test_markdown(file_path: Path, content: str):
    """Helper to create a test markdown file."""
    file_path.write_text(content, encoding='utf-8')


def create_test_pdf(file_path: Path, text: str):
    """Helper to create a simple test PDF."""
    # Note: This creates a minimal PDF-like structure for testing
    # In real tests, you might use reportlab or similar
    from pypdf import PdfWriter, PdfReader
    from io import BytesIO
    
    # Create a simple PDF with text
    # For now, we'll create a minimal valid PDF structure
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
({text}) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF"""
    file_path.write_text(pdf_content)


def create_test_image(file_path: Path, text: str):
    """Helper to create a test image with text."""
    image = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(image)
    draw.text((10, 40), text, fill='black')
    image.save(file_path)
    image.close()


class TestParseDirectory:
    """Tests for parse_directory function."""
    
    def test_parse_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        result = parse_directory(staging_dir)
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_parse_directory_with_markdown_files(self, tmp_path):
        """Should parse all markdown files in directory."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create test markdown files
        create_test_markdown(staging_dir / "file1.md", "# Content 1")
        create_test_markdown(staging_dir / "file2.md", "# Content 2")
        create_test_markdown(staging_dir / "file3.md", "# Content 3")
        
        result = parse_directory(staging_dir)
        
        assert len(result) == 3
        assert all(isinstance(doc, ParsedDocument) for doc in result)
        assert all("Content" in doc.content for doc in result)
    
    def test_parse_directory_with_mixed_file_types(self, tmp_path):
        """Should parse markdown, PDF, and image files."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create different file types
        create_test_markdown(staging_dir / "doc.md", "# Markdown")
        create_test_pdf(staging_dir / "doc.pdf", "PDF Content")
        create_test_image(staging_dir / "image.png", "Image Text")
        
        result = parse_directory(staging_dir)
        
        assert len(result) == 3
        
        # Check that all files were parsed
        file_names = {doc.file_path.name for doc in result}
        assert file_names == {"doc.md", "doc.pdf", "image.png"}
    
    def test_parse_directory_with_subdirectories(self, tmp_path):
        """Should recursively parse files in subdirectories."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create files in subdirectories
        subdir1 = staging_dir / "subdir1"
        subdir1.mkdir()
        create_test_markdown(subdir1 / "file1.md", "# Sub 1")
        
        subdir2 = staging_dir / "subdir2"
        subdir2.mkdir()
        create_test_markdown(subdir2 / "file2.md", "# Sub 2")
        
        # Create file in root
        create_test_markdown(staging_dir / "root.md", "# Root")
        
        result = parse_directory(staging_dir)
        
        assert len(result) == 3
        file_names = {doc.file_path.name for doc in result}
        assert file_names == {"file1.md", "file2.md", "root.md"}
    
    def test_parse_directory_handles_corrupted_files(self, tmp_path):
        """Should continue parsing when encountering corrupted files."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create valid file
        create_test_markdown(staging_dir / "valid.md", "# Valid")
        
        # Create corrupted PDF (invalid content)
        corrupted_pdf = staging_dir / "corrupted.pdf"
        corrupted_pdf.write_bytes(b"This is not a valid PDF")
        
        # Create another valid file
        create_test_markdown(staging_dir / "valid2.md", "# Valid 2")
        
        result = parse_directory(staging_dir)
        
        # Should have parsed all 3 files (corrupted one with errors)
        assert len(result) == 3
        
        # Check that valid files were parsed successfully
        valid_docs = [doc for doc in result if not doc.parse_errors]
        assert len(valid_docs) == 2
        
        # Check that corrupted file has errors
        corrupted_docs = [doc for doc in result if doc.parse_errors]
        assert len(corrupted_docs) == 1
        assert corrupted_docs[0].file_path.name == "corrupted.pdf"
    
    def test_parse_directory_handles_permission_errors(self, tmp_path):
        """Should handle permission errors gracefully."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create a file
        test_file = staging_dir / "test.md"
        create_test_markdown(test_file, "# Test")
        
        # Make file unreadable (Unix-like systems only)
        import os
        if os.name != 'nt':  # Skip on Windows
            test_file.chmod(0o000)
            
            result = parse_directory(staging_dir)
            
            # Should have one document with permission error
            assert len(result) == 1
            assert len(result[0].parse_errors) > 0
            assert any("Permission" in err or "permission" in err 
                      for err in result[0].parse_errors)
            
            # Restore permissions for cleanup
            test_file.chmod(0o644)
    
    def test_parse_directory_ignores_unsupported_files(self, tmp_path):
        """Should only parse supported file types."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create supported files
        create_test_markdown(staging_dir / "doc.md", "# Markdown")
        
        # Create unsupported files
        (staging_dir / "data.json").write_text('{"key": "value"}')
        (staging_dir / "script.py").write_text('print("hello")')
        (staging_dir / "data.csv").write_text('a,b,c\n1,2,3')
        
        result = parse_directory(staging_dir)
        
        # Should only parse the markdown file
        assert len(result) == 1
        assert result[0].file_path.name == "doc.md"
    
    def test_parse_directory_handles_nonexistent_directory(self, tmp_path):
        """Should handle nonexistent directory gracefully."""
        staging_dir = tmp_path / "nonexistent"
        
        result = parse_directory(staging_dir)
        
        # Should return empty list
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_parse_directory_preserves_file_order(self, tmp_path):
        """Should return files in consistent order."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create files with names that sort differently
        create_test_markdown(staging_dir / "z_last.md", "# Last")
        create_test_markdown(staging_dir / "a_first.md", "# First")
        create_test_markdown(staging_dir / "m_middle.md", "# Middle")
        
        result = parse_directory(staging_dir)
        
        # Files should be sorted by name
        file_names = [doc.file_path.name for doc in result]
        assert file_names == ["a_first.md", "m_middle.md", "z_last.md"]
    
    def test_parse_directory_with_large_files(self, tmp_path):
        """Should handle large files."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create a large markdown file (1MB of content)
        large_content = "# Large File\n" + ("Lorem ipsum " * 100000)
        create_test_markdown(staging_dir / "large.md", large_content)
        
        result = parse_directory(staging_dir)
        
        assert len(result) == 1
        assert len(result[0].content) > 1000000
        assert not result[0].parse_errors
    
    def test_parse_directory_with_unicode_content(self, tmp_path):
        """Should handle files with unicode content."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create files with various unicode content
        create_test_markdown(staging_dir / "chinese.md", "# 中文内容")
        create_test_markdown(staging_dir / "russian.md", "# Русский текст")
        create_test_markdown(staging_dir / "emoji.md", "# 🚀 Emoji 🎉")
        
        result = parse_directory(staging_dir)
        
        assert len(result) == 3
        assert all(not doc.parse_errors for doc in result)
        assert "中文" in result[0].content or "中文" in result[1].content or "中文" in result[2].content
    
    def test_parse_directory_with_special_characters_in_filenames(self, tmp_path):
        """Should handle files with special characters in names."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create files with special characters (that are valid on most systems)
        create_test_markdown(staging_dir / "file-with-dashes.md", "# Dashes")
        create_test_markdown(staging_dir / "file_with_underscores.md", "# Underscores")
        create_test_markdown(staging_dir / "file.with.dots.md", "# Dots")
        
        result = parse_directory(staging_dir)
        
        assert len(result) == 3
        assert all(not doc.parse_errors for doc in result)


class TestGetParsingSummary:
    """Tests for get_parsing_summary function."""
    
    def test_summary_for_empty_list(self):
        """Should handle empty document list."""
        summary = get_parsing_summary([])
        
        assert summary["total_files"] == 0
        assert summary["successful"] == 0
        assert summary["with_errors"] == 0
        assert summary["total_content_length"] == 0
    
    def test_summary_for_successful_parses(self, tmp_path):
        """Should summarize successful parses."""
        docs = [
            ParsedDocument(
                file_path=tmp_path / "file1.md",
                content="Content 1",
                metadata={},
                parse_errors=[]
            ),
            ParsedDocument(
                file_path=tmp_path / "file2.md",
                content="Content 2",
                metadata={},
                parse_errors=[]
            ),
        ]
        
        summary = get_parsing_summary(docs)
        
        assert summary["total_files"] == 2
        assert summary["successful"] == 2
        assert summary["with_errors"] == 0
        assert summary["total_content_length"] == len("Content 1") + len("Content 2")
    
    def test_summary_for_failed_parses(self, tmp_path):
        """Should summarize failed parses."""
        docs = [
            ParsedDocument(
                file_path=tmp_path / "file1.md",
                content="",
                metadata={},
                parse_errors=["Error 1"]
            ),
            ParsedDocument(
                file_path=tmp_path / "file2.md",
                content="",
                metadata={},
                parse_errors=["Error 2"]
            ),
        ]
        
        summary = get_parsing_summary(docs)
        
        assert summary["total_files"] == 2
        assert summary["successful"] == 0
        assert summary["with_errors"] == 2
        assert len(summary["error_summary"]) == 2
    
    def test_summary_for_mixed_results(self, tmp_path):
        """Should summarize mixed successful and failed parses."""
        docs = [
            ParsedDocument(
                file_path=tmp_path / "success.md",
                content="Success",
                metadata={},
                parse_errors=[]
            ),
            ParsedDocument(
                file_path=tmp_path / "failed.md",
                content="",
                metadata={},
                parse_errors=["Parse error"]
            ),
        ]
        
        summary = get_parsing_summary(docs)
        
        assert summary["total_files"] == 2
        assert summary["successful"] == 1
        assert summary["with_errors"] == 1
        assert len(summary["error_summary"]) == 1
        assert "failed.md" in summary["error_summary"][0]
    
    def test_summary_counts_by_file_type(self, tmp_path):
        """Should count files by type."""
        docs = [
            ParsedDocument(
                file_path=tmp_path / "file.md",
                content="Markdown",
                metadata={},
                parse_errors=[]
            ),
            ParsedDocument(
                file_path=tmp_path / "file.pdf",
                content="PDF",
                metadata={},
                parse_errors=[]
            ),
            ParsedDocument(
                file_path=tmp_path / "file.png",
                content="Image",
                metadata={},
                parse_errors=[]
            ),
        ]
        
        summary = get_parsing_summary(docs)
        
        assert summary["files_by_type"]["markdown"] == 1
        assert summary["files_by_type"]["pdf"] == 1
        assert summary["files_by_type"]["image"] == 1
    
    def test_summary_includes_first_error_only(self, tmp_path):
        """Should include only first error from each file."""
        docs = [
            ParsedDocument(
                file_path=tmp_path / "file.md",
                content="",
                metadata={},
                parse_errors=["Error 1", "Error 2", "Error 3"]
            ),
        ]
        
        summary = get_parsing_summary(docs)
        
        assert len(summary["error_summary"]) == 1
        assert "Error 1" in summary["error_summary"][0]
        assert "Error 2" not in summary["error_summary"][0]


class TestParseDirectoryIntegration:
    """Integration tests for parse_directory."""
    
    def test_realistic_staging_directory(self, tmp_path):
        """Should parse a realistic staging directory with mixed content."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create realistic project artifacts
        create_test_markdown(
            staging_dir / "project-spec.md",
            """# Project Specification
            
## Overview
This is a web application for task management.

## Features
- User authentication
- Task creation and editing
- Team collaboration
"""
        )
        
        create_test_markdown(
            staging_dir / "architecture.md",
            """# Architecture
            
## Components
- Frontend: React
- Backend: FastAPI
- Database: PostgreSQL
"""
        )
        
        # Create subdirectory with more docs
        docs_dir = staging_dir / "docs"
        docs_dir.mkdir()
        create_test_markdown(
            docs_dir / "api-design.md",
            "# API Design\n\n## Endpoints\n- GET /tasks\n- POST /tasks"
        )
        
        result = parse_directory(staging_dir)
        
        # Should parse all 3 markdown files
        assert len(result) == 3
        
        # All should be successful
        assert all(not doc.parse_errors for doc in result)
        
        # Check content was extracted
        all_content = " ".join(doc.content for doc in result)
        assert "Project Specification" in all_content
        assert "Architecture" in all_content
        assert "API Design" in all_content
        
        # Get summary
        summary = get_parsing_summary(result)
        assert summary["successful"] == 3
        assert summary["with_errors"] == 0
        assert summary["files_by_type"]["markdown"] == 3
    
    def test_handles_real_world_error_scenarios(self, tmp_path):
        """Should handle real-world error scenarios gracefully."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Valid file
        create_test_markdown(staging_dir / "valid.md", "# Valid Content")
        
        # Empty file
        (staging_dir / "empty.md").touch()
        
        # File with only whitespace
        create_test_markdown(staging_dir / "whitespace.md", "   \n\n   ")
        
        # Corrupted PDF
        (staging_dir / "corrupted.pdf").write_bytes(b"Not a PDF")
        
        result = parse_directory(staging_dir)
        
        # Should parse all 4 files
        assert len(result) == 4
        
        # At least the valid markdown should succeed
        successful = [doc for doc in result if not doc.parse_errors]
        assert len(successful) >= 1
        
        # Summary should reflect mixed results
        summary = get_parsing_summary(result)
        assert summary["total_files"] == 4
        assert summary["with_errors"] >= 1
