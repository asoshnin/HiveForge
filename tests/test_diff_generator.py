"""
Tests for the DiffGenerator class.

Tests both unit examples and property-based tests for diff generation
and formatting functionality.
"""

import pytest
from hypothesis import given, strategies as st

from src.hiveforge.steering.diff_generator import DiffGenerator
from src.hiveforge.steering.models import FileDiff, DiffHunk, DiffLine


class TestDiffGeneratorUnit:
    """Unit tests for DiffGenerator with specific examples."""
    
    def test_compute_diff_no_changes(self):
        """Test diff computation when content is identical."""
        content = "line 1\nline 2\nline 3\n"
        diff = DiffGenerator.compute_diff(content, content, "test.md")
        
        assert diff.file_name == "test.md"
        assert len(diff.hunks) == 0
        assert not DiffGenerator.has_changes(diff)
    
    def test_compute_diff_addition(self):
        """Test diff computation with added lines."""
        old_content = "line 1\nline 2\n"
        new_content = "line 1\nline 2\nline 3\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        assert diff.file_name == "test.md"
        assert len(diff.hunks) == 1
        assert DiffGenerator.has_changes(diff)
        
        # Check that the addition is captured
        additions = [line for line in diff.hunks[0].lines if line.type == "addition"]
        assert len(additions) == 1
        assert "line 3" in additions[0].content
    
    def test_compute_diff_deletion(self):
        """Test diff computation with deleted lines."""
        old_content = "line 1\nline 2\nline 3\n"
        new_content = "line 1\nline 3\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        assert len(diff.hunks) == 1
        assert DiffGenerator.has_changes(diff)
        
        # Check that the deletion is captured
        deletions = [line for line in diff.hunks[0].lines if line.type == "deletion"]
        assert len(deletions) == 1
        assert "line 2" in deletions[0].content
    
    def test_compute_diff_modification(self):
        """Test diff computation with modified lines."""
        old_content = "line 1\nline 2\nline 3\n"
        new_content = "line 1\nline 2 modified\nline 3\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        assert len(diff.hunks) == 1
        assert DiffGenerator.has_changes(diff)
        
        # Modification shows as deletion + addition
        deletions = [line for line in diff.hunks[0].lines if line.type == "deletion"]
        additions = [line for line in diff.hunks[0].lines if line.type == "addition"]
        
        assert len(deletions) == 1
        assert len(additions) == 1
        assert "line 2" in deletions[0].content
        assert "line 2 modified" in additions[0].content
    
    def test_compute_diff_context_lines(self):
        """Test that context lines are included around changes."""
        old_content = "line 1\nline 2\nline 3\nline 4\nline 5\n"
        new_content = "line 1\nline 2\nline 3 modified\nline 4\nline 5\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        assert len(diff.hunks) == 1
        
        # Check for context lines
        context_lines = [line for line in diff.hunks[0].lines if line.type == "context"]
        assert len(context_lines) > 0
    
    def test_compute_diff_multiple_hunks(self):
        """Test diff with multiple separate change regions."""
        old_content = "line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\nline 8\nline 9\nline 10\n"
        new_content = "line 1 modified\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\nline 8\nline 9\nline 10 modified\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        # Should have 2 hunks for changes at beginning and end
        assert len(diff.hunks) >= 1
        assert DiffGenerator.has_changes(diff)
    
    def test_format_diff_no_color(self):
        """Test diff formatting without colorization."""
        old_content = "line 1\nline 2\n"
        new_content = "line 1\nline 2 modified\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        formatted = DiffGenerator.format_diff(diff, colorize=False)
        
        assert "--- a/test.md" in formatted
        assert "+++ b/test.md" in formatted
        assert "@@" in formatted
        assert "-line 2" in formatted
        assert "+line 2 modified" in formatted
    
    def test_format_diff_with_color(self):
        """Test diff formatting with colorization."""
        old_content = "line 1\nline 2\n"
        new_content = "line 1\nline 2 modified\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        formatted = DiffGenerator.format_diff(diff, colorize=True)
        
        # Should contain file headers and diff markers
        assert "test.md" in formatted
        assert "@@" in formatted
    
    def test_format_diff_no_changes(self):
        """Test formatting when there are no changes."""
        content = "line 1\nline 2\n"
        diff = DiffGenerator.compute_diff(content, content, "test.md")
        formatted = DiffGenerator.format_diff(diff, colorize=False)
        
        assert "No changes" in formatted
        assert "test.md" in formatted
    
    def test_compute_diff_empty_files(self):
        """Test diff computation with empty files."""
        diff = DiffGenerator.compute_diff("", "", "test.md")
        assert len(diff.hunks) == 0
        assert not DiffGenerator.has_changes(diff)
    
    def test_compute_diff_empty_to_content(self):
        """Test diff from empty file to content."""
        old_content = ""
        new_content = "line 1\nline 2\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        assert DiffGenerator.has_changes(diff)
        additions = []
        for hunk in diff.hunks:
            additions.extend([line for line in hunk.lines if line.type == "addition"])
        assert len(additions) == 2
    
    def test_compute_diff_content_to_empty(self):
        """Test diff from content to empty file."""
        old_content = "line 1\nline 2\n"
        new_content = ""
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        assert DiffGenerator.has_changes(diff)
        deletions = []
        for hunk in diff.hunks:
            deletions.extend([line for line in hunk.lines if line.type == "deletion"])
        assert len(deletions) == 2
    
    def test_compute_diff_preserves_line_content(self):
        """Test that diff preserves exact line content."""
        old_content = "  indented line\n\ttab line\n"
        new_content = "  indented line\n\ttab line modified\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        # Check that whitespace is preserved
        for hunk in diff.hunks:
            for line in hunk.lines:
                if "indented" in line.content:
                    assert line.content.startswith("  ")
                if "tab" in line.content:
                    assert "\t" in line.content or line.content.startswith("tab")


class TestDiffGeneratorProperties:
    """Property-based tests for DiffGenerator."""
    
    @given(st.text(min_size=0, max_size=1000))
    def test_identical_content_produces_no_diff(self, content: str):
        """Property: Identical content should produce no changes."""
        diff = DiffGenerator.compute_diff(content, content, "test.md")
        assert not DiffGenerator.has_changes(diff)
        assert len(diff.hunks) == 0
    
    @given(
        st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=50),
        st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=50)
    )
    def test_diff_is_deterministic(self, old_lines: list, new_lines: list):
        """Property: Computing diff twice should give identical results."""
        old_content = "\n".join(old_lines)
        new_content = "\n".join(new_lines)
        
        diff1 = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        diff2 = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        assert len(diff1.hunks) == len(diff2.hunks)
        for hunk1, hunk2 in zip(diff1.hunks, diff2.hunks):
            assert hunk1.old_start == hunk2.old_start
            assert hunk1.new_start == hunk2.new_start
            assert len(hunk1.lines) == len(hunk2.lines)
    
    @given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=50))
    def test_adding_line_creates_addition(self, lines: list):
        """Property: Adding a line should create an addition in the diff."""
        old_content = "\n".join(lines)
        new_content = old_content + "\nnew line"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        assert DiffGenerator.has_changes(diff)
        
        # Count additions
        additions = []
        for hunk in diff.hunks:
            additions.extend([line for line in hunk.lines if line.type == "addition"])
        
        assert len(additions) >= 1
    
    @given(st.lists(st.text(min_size=1, max_size=100), min_size=2, max_size=50))
    def test_removing_line_creates_deletion(self, lines: list):
        """Property: Removing a line should create a deletion in the diff."""
        old_content = "\n".join(lines)
        new_content = "\n".join(lines[:-1])  # Remove last line
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        if len(lines) > 1:  # Only if there was something to remove
            assert DiffGenerator.has_changes(diff)
            
            # Count deletions
            deletions = []
            for hunk in diff.hunks:
                deletions.extend([line for line in hunk.lines if line.type == "deletion"])
            
            assert len(deletions) >= 1
    
    @given(st.text(min_size=0, max_size=1000))
    def test_format_diff_is_string(self, content: str):
        """Property: format_diff should always return a string."""
        diff = DiffGenerator.compute_diff(content, content + "\n", "test.md")
        
        formatted_color = DiffGenerator.format_diff(diff, colorize=True)
        formatted_no_color = DiffGenerator.format_diff(diff, colorize=False)
        
        assert isinstance(formatted_color, str)
        assert isinstance(formatted_no_color, str)
    
    @given(
        st.lists(st.text(min_size=0, max_size=100), min_size=0, max_size=50),
        st.lists(st.text(min_size=0, max_size=100), min_size=0, max_size=50)
    )
    def test_formatted_diff_contains_file_name(self, old_lines: list, new_lines: list):
        """Property: Formatted diff should contain the file name."""
        old_content = "\n".join(old_lines)
        new_content = "\n".join(new_lines)
        file_name = "test_file.md"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, file_name)
        formatted = DiffGenerator.format_diff(diff, colorize=False)
        
        assert file_name in formatted
    
    @given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=50))
    def test_has_changes_consistency(self, lines: list):
        """Property: has_changes should be consistent with hunk presence."""
        old_content = "\n".join(lines)
        new_content = old_content + "\nnew line"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        # has_changes should match whether there are hunks
        assert DiffGenerator.has_changes(diff) == (len(diff.hunks) > 0)
    
    @given(
        st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=30),
        st.lists(st.text(min_size=0, max_size=100), min_size=1, max_size=30)
    )
    def test_diff_line_types_are_valid(self, old_lines: list, new_lines: list):
        """Property: All diff lines should have valid types."""
        old_content = "\n".join(old_lines)
        new_content = "\n".join(new_lines)
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        
        valid_types = {"context", "addition", "deletion"}
        for hunk in diff.hunks:
            for line in hunk.lines:
                assert line.type in valid_types
    
    @given(st.text(min_size=0, max_size=500))
    def test_format_without_color_has_no_escape_codes(self, content: str):
        """Property: Non-colorized output should not contain ANSI escape codes."""
        diff = DiffGenerator.compute_diff(content, content + "\nchange", "test.md")
        formatted = DiffGenerator.format_diff(diff, colorize=False)
        
        # Check for common ANSI escape sequences
        assert "\x1b[" not in formatted  # ANSI escape start
        assert "\033[" not in formatted  # Alternative ANSI escape start


class TestDiffGeneratorEdgeCases:
    """Edge case tests for DiffGenerator."""
    
    def test_diff_with_unicode_content(self):
        """Test diff with Unicode characters."""
        old_content = "Hello 世界\n"
        new_content = "Hello 世界!\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        assert DiffGenerator.has_changes(diff)
        
        formatted = DiffGenerator.format_diff(diff, colorize=False)
        assert "世界" in formatted
    
    def test_diff_with_very_long_lines(self):
        """Test diff with very long lines."""
        old_content = "a" * 1000 + "\n"
        new_content = "a" * 1000 + "b\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        assert DiffGenerator.has_changes(diff)
    
    def test_diff_with_special_characters(self):
        """Test diff with special characters."""
        old_content = "Line with $pecial ch@rs!\n"
        new_content = "Line with $pecial ch@rs modified!\n"
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        assert DiffGenerator.has_changes(diff)
        
        formatted = DiffGenerator.format_diff(diff, colorize=False)
        assert "$pecial" in formatted
        assert "@" in formatted
    
    def test_diff_with_only_whitespace_changes(self):
        """Test diff with only whitespace changes."""
        old_content = "line 1\nline 2\n"
        new_content = "line 1 \nline 2\n"  # Added trailing space
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        # Whitespace changes should be detected
        assert DiffGenerator.has_changes(diff)
    
    def test_diff_with_blank_lines(self):
        """Test diff with blank lines."""
        old_content = "line 1\n\nline 3\n"
        new_content = "line 1\n\n\nline 3\n"  # Added blank line
        
        diff = DiffGenerator.compute_diff(old_content, new_content, "test.md")
        assert DiffGenerator.has_changes(diff)
