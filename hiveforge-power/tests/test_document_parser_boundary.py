"""
Property test for DocumentParser source folder boundary enforcement.

Tests that DocumentParser raises SourceFolderError for any path outside
the configured source_folder.

Requirements: 3.1, 3.2
"""

import tempfile
from pathlib import Path

import pytest

from hiveforge.steering.parsers import DocumentParser, SourceFolderError


class TestDocumentParserBoundaryEnforcement:
    """
    Property 9: Source folder boundary enforcement.
    
    For any path outside source_folder, DocumentParser must raise
    SourceFolderError.
    
    Requirements: 3.1, 3.2
    """
    
    def test_parse_file_inside_source_folder_succeeds(self, tmp_path):
        """
        Test that parsing a file inside source_folder succeeds.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder with a file
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        test_file = source_folder / "test.md"
        test_file.write_text("# Test Document\n\nContent here.")
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Should succeed
        doc = parser.parse_file(test_file)
        
        assert doc is not None
        assert doc.file_path == test_file
        assert "Test Document" in doc.content
    
    def test_parse_file_outside_source_folder_raises_error(self, tmp_path):
        """
        Test that parsing a file outside source_folder raises SourceFolderError.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        # Create file OUTSIDE source folder
        outside_file = tmp_path / "outside.md"
        outside_file.write_text("# Outside Document")
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Should raise SourceFolderError
        with pytest.raises(SourceFolderError) as exc_info:
            parser.parse_file(outside_file)
        
        assert "outside source folder" in str(exc_info.value).lower()
    
    def test_parse_file_with_parent_traversal_raises_error(self, tmp_path):
        """
        Test that path traversal attempts (../) are blocked.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        # Create file outside
        outside_file = tmp_path / "secret.md"
        outside_file.write_text("# Secret Document")
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Try to access file using ../
        traversal_path = source_folder / ".." / "secret.md"
        
        # Should raise SourceFolderError
        with pytest.raises(SourceFolderError) as exc_info:
            parser.parse_file(traversal_path)
        
        assert "outside source folder" in str(exc_info.value).lower()
    
    def test_parse_file_with_symlink_outside_raises_error(self, tmp_path):
        """
        Test that symlinks pointing outside source_folder are blocked.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        # Create file outside
        outside_file = tmp_path / "outside.md"
        outside_file.write_text("# Outside Document")
        
        # Create symlink inside source folder pointing outside
        symlink_path = source_folder / "link.md"
        try:
            symlink_path.symlink_to(outside_file)
        except OSError:
            # Symlinks may not be supported on Windows without admin rights
            pytest.skip("Symlinks not supported on this system")
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Should raise SourceFolderError when following symlink
        with pytest.raises(SourceFolderError) as exc_info:
            parser.parse_file(symlink_path)
        
        assert "outside source folder" in str(exc_info.value).lower()
    
    def test_parse_file_in_subdirectory_succeeds(self, tmp_path):
        """
        Test that parsing files in subdirectories of source_folder succeeds.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder with subdirectory
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        subdir = source_folder / "subdir"
        subdir.mkdir()
        
        test_file = subdir / "test.md"
        test_file.write_text("# Subdirectory Document")
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Should succeed
        doc = parser.parse_file(test_file)
        
        assert doc is not None
        assert doc.file_path == test_file
        assert "Subdirectory Document" in doc.content
    
    def test_parse_all_only_reads_from_source_folder(self, tmp_path):
        """
        Test that parse_all() only reads files from source_folder.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder with files
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        inside_file1 = source_folder / "inside1.md"
        inside_file1.write_text("# Inside 1")
        
        inside_file2 = source_folder / "inside2.md"
        inside_file2.write_text("# Inside 2")
        
        # Create files OUTSIDE source folder
        outside_file = tmp_path / "outside.md"
        outside_file.write_text("# Outside")
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Parse all
        docs = parser.parse_all()
        
        # Should only have files from inside source folder
        assert len(docs) == 2
        
        file_names = {doc.file_path.name for doc in docs}
        assert "inside1.md" in file_names
        assert "inside2.md" in file_names
        assert "outside.md" not in file_names
    
    def test_absolute_path_outside_source_folder_raises_error(self, tmp_path):
        """
        Test that absolute paths outside source_folder raise SourceFolderError.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        # Create file outside with absolute path
        outside_folder = tmp_path / "outside"
        outside_folder.mkdir()
        
        outside_file = outside_folder / "test.md"
        outside_file.write_text("# Outside Document")
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Should raise SourceFolderError
        with pytest.raises(SourceFolderError) as exc_info:
            parser.parse_file(outside_file.absolute())
        
        assert "outside source folder" in str(exc_info.value).lower()
    
    def test_relative_path_resolving_outside_raises_error(self, tmp_path):
        """
        Test that relative paths that resolve outside source_folder raise error.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        # Create file outside
        outside_file = tmp_path / "outside.md"
        outside_file.write_text("# Outside Document")
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Try various relative path tricks
        relative_paths = [
            "../outside.md",
            "./../outside.md",
            "subdir/../../outside.md",
        ]
        
        for rel_path in relative_paths:
            full_path = source_folder / rel_path
            
            with pytest.raises(SourceFolderError) as exc_info:
                parser.parse_file(full_path)
            
            assert "outside source folder" in str(exc_info.value).lower()
    
    def test_source_folder_itself_is_valid(self, tmp_path):
        """
        Test that the source_folder itself is considered valid.
        
        Requirements: 3.1, 3.2
        """
        # Create source folder
        source_folder = tmp_path / "source"
        source_folder.mkdir()
        
        # Create parser
        parser = DocumentParser(source_folder=source_folder)
        
        # Parsing the source folder itself should not raise error
        # (though it may return empty or handle gracefully)
        try:
            # This should not raise SourceFolderError
            # It may raise other errors (e.g., IsADirectoryError) which is fine
            parser.parse_file(source_folder)
        except SourceFolderError:
            pytest.fail("Source folder itself should not raise SourceFolderError")
        except Exception:
            # Other exceptions are acceptable
            pass
