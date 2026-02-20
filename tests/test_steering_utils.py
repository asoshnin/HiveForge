"""
Unit tests for steering utilities.

Tests the staging folder management functions including directory creation,
file type detection, and file listing.
"""

import pytest
from pathlib import Path
from hiveforge.steering.utils import (
    create_staging_directory,
    is_supported_file_type,
    get_file_type,
    list_supported_files,
    is_staging_folder_empty,
    categorize_files_by_type,
    get_staging_directory_summary,
    SUPPORTED_MARKDOWN_EXTENSIONS,
    SUPPORTED_PDF_EXTENSIONS,
    SUPPORTED_IMAGE_EXTENSIONS,
)


class TestCreateStagingDirectory:
    """Tests for create_staging_directory function."""
    
    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that directory is created when it doesn't exist."""
        staging_dir = tmp_path / ".kiro" / "onboarding"
        assert not staging_dir.exists()
        
        create_staging_directory(staging_dir)
        
        assert staging_dir.exists()
        assert staging_dir.is_dir()
    
    def test_succeeds_if_directory_already_exists(self, tmp_path):
        """Test that function succeeds when directory already exists."""
        staging_dir = tmp_path / ".kiro" / "onboarding"
        staging_dir.mkdir(parents=True)
        assert staging_dir.exists()
        
        # Should not raise an error
        create_staging_directory(staging_dir)
        
        assert staging_dir.exists()
        assert staging_dir.is_dir()
    
    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if needed."""
        staging_dir = tmp_path / "a" / "b" / "c" / "staging"
        assert not staging_dir.parent.exists()
        
        create_staging_directory(staging_dir)
        
        assert staging_dir.exists()
        assert staging_dir.parent.exists()


class TestIsSupportedFileType:
    """Tests for is_supported_file_type function."""
    
    @pytest.mark.parametrize("extension", [".md", ".markdown", ".mdown", ".mkd"])
    def test_recognizes_markdown_files(self, extension):
        """Test that markdown extensions are recognized."""
        file_path = Path(f"test{extension}")
        assert is_supported_file_type(file_path) is True
    
    def test_recognizes_pdf_files(self):
        """Test that PDF files are recognized."""
        file_path = Path("test.pdf")
        assert is_supported_file_type(file_path) is True
    
    @pytest.mark.parametrize("extension", [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"])
    def test_recognizes_image_files(self, extension):
        """Test that image extensions are recognized."""
        file_path = Path(f"test{extension}")
        assert is_supported_file_type(file_path) is True
    
    @pytest.mark.parametrize("extension", [".txt", ".doc", ".docx", ".py", ".js", ".html"])
    def test_rejects_unsupported_files(self, extension):
        """Test that unsupported extensions are rejected."""
        file_path = Path(f"test{extension}")
        assert is_supported_file_type(file_path) is False
    
    def test_case_insensitive(self):
        """Test that extension matching is case-insensitive."""
        assert is_supported_file_type(Path("test.MD")) is True
        assert is_supported_file_type(Path("test.PDF")) is True
        assert is_supported_file_type(Path("test.PNG")) is True


class TestGetFileType:
    """Tests for get_file_type function."""
    
    def test_identifies_markdown(self):
        """Test markdown file identification."""
        assert get_file_type(Path("test.md")) == "markdown"
        assert get_file_type(Path("test.markdown")) == "markdown"
    
    def test_identifies_pdf(self):
        """Test PDF file identification."""
        assert get_file_type(Path("test.pdf")) == "pdf"
    
    def test_identifies_image(self):
        """Test image file identification."""
        assert get_file_type(Path("test.png")) == "image"
        assert get_file_type(Path("test.jpg")) == "image"
    
    def test_returns_unknown_for_unsupported(self):
        """Test that unsupported files return 'unknown'."""
        assert get_file_type(Path("test.txt")) == "unknown"
        assert get_file_type(Path("test.py")) == "unknown"


class TestListSupportedFiles:
    """Tests for list_supported_files function."""
    
    def test_returns_empty_list_for_nonexistent_directory(self, tmp_path):
        """Test that non-existent directory returns empty list."""
        staging_dir = tmp_path / "nonexistent"
        result = list_supported_files(staging_dir)
        assert result == []
    
    def test_returns_empty_list_for_empty_directory(self, tmp_path):
        """Test that empty directory returns empty list."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        result = list_supported_files(staging_dir)
        assert result == []
    
    def test_finds_supported_files(self, tmp_path):
        """Test that supported files are found."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create test files
        (staging_dir / "test.md").touch()
        (staging_dir / "test.pdf").touch()
        (staging_dir / "test.png").touch()
        (staging_dir / "test.txt").touch()  # Unsupported
        
        result = list_supported_files(staging_dir)
        
        assert len(result) == 3
        assert staging_dir / "test.md" in result
        assert staging_dir / "test.pdf" in result
        assert staging_dir / "test.png" in result
        assert staging_dir / "test.txt" not in result
    
    def test_finds_files_recursively(self, tmp_path):
        """Test that files in subdirectories are found."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        subdir = staging_dir / "subdir"
        subdir.mkdir()
        
        (staging_dir / "root.md").touch()
        (subdir / "nested.pdf").touch()
        
        result = list_supported_files(staging_dir)
        
        assert len(result) == 2
        assert staging_dir / "root.md" in result
        assert subdir / "nested.pdf" in result
    
    def test_returns_sorted_list(self, tmp_path):
        """Test that results are sorted by name."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        (staging_dir / "c.md").touch()
        (staging_dir / "a.pdf").touch()
        (staging_dir / "b.png").touch()
        
        result = list_supported_files(staging_dir)
        
        # Check that files are sorted
        file_names = [f.name for f in result]
        assert file_names == sorted(file_names)


class TestIsStagingFolderEmpty:
    """Tests for is_staging_folder_empty function."""
    
    def test_returns_true_for_nonexistent_directory(self, tmp_path):
        """Test that non-existent directory is considered empty."""
        staging_dir = tmp_path / "nonexistent"
        assert is_staging_folder_empty(staging_dir) is True
    
    def test_returns_true_for_empty_directory(self, tmp_path):
        """Test that empty directory is considered empty."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        assert is_staging_folder_empty(staging_dir) is True
    
    def test_returns_true_when_only_unsupported_files(self, tmp_path):
        """Test that directory with only unsupported files is considered empty."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        (staging_dir / "test.txt").touch()
        (staging_dir / "test.py").touch()
        
        assert is_staging_folder_empty(staging_dir) is True
    
    def test_returns_false_when_supported_files_exist(self, tmp_path):
        """Test that directory with supported files is not empty."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        (staging_dir / "test.md").touch()
        
        assert is_staging_folder_empty(staging_dir) is False


class TestCategorizeFilesByType:
    """Tests for categorize_files_by_type function."""
    
    def test_categorizes_empty_list(self):
        """Test categorization of empty list."""
        result = categorize_files_by_type([])
        assert result == {
            "markdown": [],
            "pdf": [],
            "image": [],
            "unknown": []
        }
    
    def test_categorizes_mixed_files(self, tmp_path):
        """Test categorization of mixed file types."""
        files = [
            tmp_path / "test1.md",
            tmp_path / "test2.pdf",
            tmp_path / "test3.png",
            tmp_path / "test4.md",
            tmp_path / "test5.jpg",
        ]
        
        result = categorize_files_by_type(files)
        
        assert len(result["markdown"]) == 2
        assert len(result["pdf"]) == 1
        assert len(result["image"]) == 2
        assert len(result["unknown"]) == 0
    
    def test_categorizes_unsupported_files(self, tmp_path):
        """Test that unsupported files go to 'unknown' category."""
        files = [
            tmp_path / "test.txt",
            tmp_path / "test.py",
        ]
        
        result = categorize_files_by_type(files)
        
        assert len(result["unknown"]) == 2
        assert len(result["markdown"]) == 0
        assert len(result["pdf"]) == 0
        assert len(result["image"]) == 0


class TestGetStagingDirectorySummary:
    """Tests for get_staging_directory_summary function."""
    
    def test_summary_for_nonexistent_directory(self, tmp_path):
        """Test summary for non-existent directory."""
        staging_dir = tmp_path / "nonexistent"
        result = get_staging_directory_summary(staging_dir)
        
        assert result["exists"] is False
        assert result["total_files"] == 0
        assert result["is_empty"] is True
    
    def test_summary_for_empty_directory(self, tmp_path):
        """Test summary for empty directory."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        result = get_staging_directory_summary(staging_dir)
        
        assert result["exists"] is True
        assert result["total_files"] == 0
        assert result["is_empty"] is True
        assert result["markdown_count"] == 0
        assert result["pdf_count"] == 0
        assert result["image_count"] == 0
    
    def test_summary_with_files(self, tmp_path):
        """Test summary with various file types."""
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        
        # Create test files
        (staging_dir / "test1.md").touch()
        (staging_dir / "test2.md").touch()
        (staging_dir / "test3.pdf").touch()
        (staging_dir / "test4.png").touch()
        (staging_dir / "test5.jpg").touch()
        (staging_dir / "test6.txt").touch()  # Unsupported
        
        result = get_staging_directory_summary(staging_dir)
        
        assert result["exists"] is True
        assert result["total_files"] == 5  # Excludes unsupported
        assert result["markdown_count"] == 2
        assert result["pdf_count"] == 1
        assert result["image_count"] == 2
        assert result["is_empty"] is False
        
        # Check files_by_type structure
        assert len(result["files_by_type"]["markdown"]) == 2
        assert len(result["files_by_type"]["pdf"]) == 1
        assert len(result["files_by_type"]["image"]) == 2
