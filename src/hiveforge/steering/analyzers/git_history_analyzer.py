"""
Git history analysis functionality for the Steering Assistant v02.

This module provides the GitHistoryAnalyzer class for extracting commit messages
and PR descriptions from git history.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


class GitHistoryAnalyzer:
    """Analyzes git history for project context."""
    
    def __init__(self, max_commits: int = 100, max_tokens: int = 2000):
        """
        Initialize the GitHistoryAnalyzer.
        
        Args:
            max_commits: Maximum number of commits to analyze
            max_tokens: Maximum tokens for summary
        """
        self.max_commits = max_commits
        self.max_tokens = max_tokens
    
    def analyze_commits(self, project_path: Path) -> List[dict]:
        """
        Extract commit messages from git history.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            List of commit information dictionaries
        """
        commits = []
        
        try:
            # Check if git repository exists
            if not (project_path / ".git").exists():
                return commits
            
            # Get commit log
            result = subprocess.run(
                [
                    "git",
                    "-C",
                    str(project_path),
                    "log",
                    f"-n{self.max_commits}",
                    "--pretty=format:%H|%an|%ae|%ad|%s",
                    "--date=iso-strict",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                return commits
            
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|", 4)
                    if len(parts) >= 5:
                        commits.append({
                            "hash": parts[0],
                            "author": parts[1],
                            "email": parts[2],
                            "date": parts[3],
                            "message": parts[4],
                        })
        
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            # Git not available or command failed
            pass
        
        return commits
    
    def analyze_prs(self, project_path: Path) -> List[dict]:
        """
        Extract PR descriptions from git history (if available).
        
        Args:
            project_path: Root path of the project
            
        Returns:
            List of PR information dictionaries
        """
        prs = []
        
        try:
            # Check if PR refs exist (GitHub-style)
            refs_path = project_path / ".git" / "refs" / "pull"
            if not refs_path.exists():
                return prs
            
            # Get PR numbers
            for pr_dir in refs_path.iterdir():
                if pr_dir.is_dir():
                    pr_number = pr_dir.name
                    head_file = pr_dir / "head"
                    merge_file = pr_dir / "merge-commit"
                    
                    pr_info = {"number": pr_number}
                    
                    if head_file.exists():
                        pr_info["head"] = head_file.read_text().strip()
                    
                    if merge_file.exists():
                        pr_info["merge_commit"] = merge_file.read_text().strip()
                    
                    prs.append(pr_info)
        
        except (OSError, IOError):
            pass
        
        return prs
    
    def get_summary(self, project_path: Path) -> str:
        """
        Create a token-limited summary of git history.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            Summarized string of git history
        """
        commits = self.analyze_commits(project_path)
        prs = self.analyze_prs(project_path)
        
        summary_parts = []
        
        # Add commit summary
        if commits:
            summary_parts.append(f"Recent commits ({len(commits)}):")
            for commit in commits[:10]:  # Show last 10 commits
                summary_parts.append(
                    f"- {commit['message']} ({commit['author']}, {commit['date'][:10]})"
                )
        
        # Add PR summary
        if prs:
            summary_parts.append(f"\nPull requests ({len(prs)}):")
            for pr in prs[:5]:  # Show first 5 PRs
                summary_parts.append(f"- PR #{pr['number']}")
        
        # Join and truncate if needed
        full_summary = "\n".join(summary_parts)
        
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = self.max_tokens * 4
        if len(full_summary) > max_chars:
            full_summary = full_summary[:max_chars] + "..."
        
        return full_summary
    
    def get_commit_count(self, project_path: Path) -> int:
        """
        Get the total number of commits in the repository.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            Number of commits
        """
        try:
            result = subprocess.run(
                ["git", "-C", str(project_path), "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode == 0:
                return int(result.stdout.strip())
        
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
            pass
        
        return 0
