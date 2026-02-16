"""
Diff generation for steering file updates.

This module provides functionality to compute and display differences between
old and new steering file content using unified diff format with colored output.
"""

import difflib
from typing import List

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

from .models import DiffHunk, DiffLine, FileDiff


class DiffGenerator:
    """
    Generates and formats diffs for steering file updates.
    
    Uses Python's difflib to compute unified diffs and colorama for
    terminal output with colored additions (green) and deletions (red).
    """
    
    @staticmethod
    def compute_diff(old_content: str, new_content: str, file_name: str = "") -> FileDiff:
        """
        Compute a unified diff between old and new content.
        
        Args:
            old_content: Original file content
            new_content: Updated file content
            file_name: Name of the file being diffed
            
        Returns:
            FileDiff object containing structured diff information
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_name}",
            tofile=f"b/{file_name}",
            lineterm=""
        ))
        
        # Parse diff into hunks
        hunks = DiffGenerator._parse_hunks(diff_lines)
        
        return FileDiff(
            file_name=file_name,
            old_lines=[line.rstrip('\n\r') for line in old_lines],
            new_lines=[line.rstrip('\n\r') for line in new_lines],
            hunks=hunks
        )
    
    @staticmethod
    def _parse_hunks(diff_lines: List[str]) -> List[DiffHunk]:
        """
        Parse unified diff output into structured hunks.
        
        Args:
            diff_lines: Lines from unified_diff output
            
        Returns:
            List of DiffHunk objects
        """
        hunks = []
        current_hunk = None
        
        for line in diff_lines:
            # Skip file headers
            if line.startswith('---') or line.startswith('+++'):
                continue
            
            # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
            if line.startswith('@@'):
                if current_hunk:
                    hunks.append(current_hunk)
                
                # Extract hunk range information
                parts = line.split('@@')[1].strip().split()
                old_range = parts[0][1:]  # Remove '-' prefix
                new_range = parts[1][1:]  # Remove '+' prefix
                
                old_start, old_count = DiffGenerator._parse_range(old_range)
                new_start, new_count = DiffGenerator._parse_range(new_range)
                
                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    lines=[]
                )
            elif current_hunk is not None:
                # Parse diff line
                if line.startswith('+'):
                    current_hunk.lines.append(DiffLine(
                        type="addition",
                        content=line[1:]  # Remove '+' prefix
                    ))
                elif line.startswith('-'):
                    current_hunk.lines.append(DiffLine(
                        type="deletion",
                        content=line[1:]  # Remove '-' prefix
                    ))
                elif line.startswith(' '):
                    current_hunk.lines.append(DiffLine(
                        type="context",
                        content=line[1:]  # Remove ' ' prefix
                    ))
        
        # Add the last hunk
        if current_hunk:
            hunks.append(current_hunk)
        
        return hunks
    
    @staticmethod
    def _parse_range(range_str: str) -> tuple[int, int]:
        """
        Parse a range string like '10,5' or '10' into (start, count).
        
        Args:
            range_str: Range string from hunk header
            
        Returns:
            Tuple of (start_line, line_count)
        """
        if ',' in range_str:
            start, count = range_str.split(',')
            return int(start), int(count)
        else:
            return int(range_str), 1
    
    @staticmethod
    def format_diff(diff: FileDiff, colorize: bool = True) -> str:
        """
        Format a FileDiff for display with optional colorization.
        
        Args:
            diff: FileDiff object to format
            colorize: Whether to add terminal color codes (default: True)
            
        Returns:
            Formatted diff string ready for display
        """
        if not diff.hunks:
            return f"No changes in {diff.file_name}"
        
        lines = []
        
        # File header
        if colorize and COLORAMA_AVAILABLE:
            lines.append(f"{Style.BRIGHT}--- a/{diff.file_name}{Style.RESET_ALL}")
            lines.append(f"{Style.BRIGHT}+++ b/{diff.file_name}{Style.RESET_ALL}")
        else:
            lines.append(f"--- a/{diff.file_name}")
            lines.append(f"+++ b/{diff.file_name}")
        
        # Format each hunk
        for hunk in diff.hunks:
            # Hunk header
            header = f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@"
            if colorize and COLORAMA_AVAILABLE:
                lines.append(f"{Fore.CYAN}{header}{Style.RESET_ALL}")
            else:
                lines.append(header)
            
            # Format each line in the hunk
            for diff_line in hunk.lines:
                formatted_line = DiffGenerator._format_line(diff_line, colorize)
                lines.append(formatted_line)
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_line(diff_line: DiffLine, colorize: bool) -> str:
        """
        Format a single diff line with appropriate prefix and color.
        
        Args:
            diff_line: DiffLine to format
            colorize: Whether to add color codes
            
        Returns:
            Formatted line string
        """
        if diff_line.type == "addition":
            prefix = "+"
            if colorize and COLORAMA_AVAILABLE:
                return f"{Fore.GREEN}{prefix}{diff_line.content}{Style.RESET_ALL}"
            else:
                return f"{prefix}{diff_line.content}"
        elif diff_line.type == "deletion":
            prefix = "-"
            if colorize and COLORAMA_AVAILABLE:
                return f"{Fore.RED}{prefix}{diff_line.content}{Style.RESET_ALL}"
            else:
                return f"{prefix}{diff_line.content}"
        else:  # context
            prefix = " "
            return f"{prefix}{diff_line.content}"
    
    @staticmethod
    def has_changes(diff: FileDiff) -> bool:
        """
        Check if a diff contains any actual changes.
        
        Args:
            diff: FileDiff to check
            
        Returns:
            True if there are additions or deletions, False otherwise
        """
        return len(diff.hunks) > 0
