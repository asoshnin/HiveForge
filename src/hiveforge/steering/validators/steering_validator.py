"""
Steering Validator Agent for validating steering files.

This module provides the SteeringValidator class that validates steering files
for completeness, consistency, and structural correctness. It uses primarily
rule-based validation with optional LLM-based semantic checks for ambiguous cases.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from ..models import ValidationIssue, ValidationReport, Template
from ..templates import get_all_templates
from .rule_based import check_completeness, check_structure, check_consistency


class SteeringValidator:
    """
    Validates steering files for completeness, consistency, and correctness.
    
    Uses primarily rule-based checks (regex, structure validation, keyword matching)
    with optional LLM-based semantic checks for ambiguous cases. Implements caching
    to avoid re-validating unchanged files.
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        use_llm: bool = False
    ):
        """
        Initialize the SteeringValidator.
        
        Args:
            cache_dir: Directory for caching validation results (defaults to .kiro/.cache)
            use_llm: Whether to use LLM for semantic consistency checks
        """
        self.templates = get_all_templates()
        self.use_llm = use_llm
        self.cache_dir = cache_dir or Path(".kiro/.cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "validation_cache.json"
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load validation cache from disk."""
        self._cache: Dict[str, Dict] = {}
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                # If cache is corrupted, start fresh
                self._cache = {}
    
    def _save_cache(self) -> None:
        """Save validation cache to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except IOError:
            # If we can't save cache, just continue without it
            pass
    
    def _compute_file_hash(self, content: str) -> str:
        """Compute hash of file content for caching."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _get_cached_result(
        self,
        file_name: str,
        content_hash: str
    ) -> Optional[List[ValidationIssue]]:
        """
        Get cached validation result if available and unchanged.
        
        Args:
            file_name: Name of the file
            content_hash: Hash of the file content
            
        Returns:
            Cached validation issues if available, None otherwise
        """
        if file_name not in self._cache:
            return None
        
        cached_entry = self._cache[file_name]
        if cached_entry.get('hash') != content_hash:
            return None
        
        # Reconstruct ValidationIssue objects from cached data
        issues = []
        for issue_data in cached_entry.get('issues', []):
            issues.append(ValidationIssue(
                severity=issue_data['severity'],
                file_name=issue_data['file_name'],
                line_number=issue_data.get('line_number'),
                issue_type=issue_data['issue_type'],
                message=issue_data['message'],
                suggestion=issue_data.get('suggestion')
            ))
        
        return issues
    
    def _cache_result(
        self,
        file_name: str,
        content_hash: str,
        issues: List[ValidationIssue]
    ) -> None:
        """
        Cache validation result for future use.
        
        Args:
            file_name: Name of the file
            content_hash: Hash of the file content
            issues: List of validation issues found
        """
        # Convert ValidationIssue objects to serializable dicts
        issues_data = []
        for issue in issues:
            issues_data.append({
                'severity': issue.severity,
                'file_name': issue.file_name,
                'line_number': issue.line_number,
                'issue_type': issue.issue_type,
                'message': issue.message,
                'suggestion': issue.suggestion
            })
        
        self._cache[file_name] = {
            'hash': content_hash,
            'issues': issues_data
        }
        
        self._save_cache()
    
    def validate_file(
        self,
        file_path: Path
    ) -> List[ValidationIssue]:
        """
        Validate a single steering file using rule-based checks.
        
        Performs:
        - Completeness check (unreplaced placeholders)
        - Structure check (frontmatter, required sections)
        
        Args:
            file_path: Path to the steering file to validate
            
        Returns:
            List of validation issues found (empty if valid)
        """
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            return [ValidationIssue(
                severity="critical",
                file_name=file_path.name,
                line_number=None,
                issue_type="file_read_error",
                message=f"Failed to read file: {e}",
                suggestion="Check file permissions and path"
            )]
        
        # Check cache
        content_hash = self._compute_file_hash(content)
        cached_issues = self._get_cached_result(file_path.name, content_hash)
        if cached_issues is not None:
            return cached_issues
        
        # Get template for this file
        template_name = file_path.stem  # e.g., "tech-stack" from "tech-stack.md"
        template = self.templates.get(template_name)
        
        if not template:
            issue = ValidationIssue(
                severity="warning",
                file_name=file_path.name,
                line_number=None,
                issue_type="unknown_template",
                message=f"No template found for {file_path.name}",
                suggestion="This file may be a custom steering file"
            )
            return [issue]
        
        # Run rule-based validations
        issues: List[ValidationIssue] = []
        
        # Check completeness
        completeness_issues = check_completeness(content, template, file_path.name)
        issues.extend(completeness_issues)
        
        # Check structure
        structure_issues = check_structure(content, template, file_path.name)
        issues.extend(structure_issues)
        
        # Cache result
        self._cache_result(file_path.name, content_hash, issues)
        
        return issues
    
    def validate_all(
        self,
        steering_dir: Path,
        use_llm: Optional[bool] = None,
        show_progress: bool = True
    ) -> ValidationReport:
        """
        Validate all steering files in a directory.
        
        Performs:
        - Individual file validation (completeness, structure)
        - Cross-file consistency checks
        - Optional semantic consistency checks using LLM
        
        Args:
            steering_dir: Directory containing steering files
            use_llm: Override instance setting for LLM usage
            show_progress: Whether to display progress messages (default: True)
            
        Returns:
            ValidationReport with all findings categorized by severity
            
        Requirements: 10.1-10.10, 14.4
        """
        if use_llm is None:
            use_llm = self.use_llm
        
        # Initialize report
        report = ValidationReport(
            files_checked=0,
            overall_status="pass",
            llm_calls_made=0,
            tokens_used=0
        )
        
        # Find all steering files
        steering_files = list(steering_dir.glob("*.md"))
        
        if not steering_files:
            report.critical_issues.append(ValidationIssue(
                severity="critical",
                file_name="",
                line_number=None,
                issue_type="no_files_found",
                message=f"No steering files found in {steering_dir}",
                suggestion="Run 'hiveforge steering init' to create steering files"
            ))
            report.overall_status = "fail"
            return report
        
        # Validate each file individually
        all_issues: List[ValidationIssue] = []
        file_contents: Dict[str, str] = {}
        total_files = len(steering_files)
        
        for idx, file_path in enumerate(steering_files, 1):
            report.files_checked += 1
            
            # Display progress for current file (Req 14.4)
            if show_progress:
                print(f"   [{idx}/{total_files}] Checking {file_path.name}...", end=" ")
            
            # Validate file
            file_issues = self.validate_file(file_path)
            all_issues.extend(file_issues)
            
            # Display result (Req 14.4)
            if show_progress:
                if file_issues:
                    critical_count = sum(1 for i in file_issues if i.severity == "critical")
                    warning_count = sum(1 for i in file_issues if i.severity == "warning")
                    if critical_count > 0:
                        print(f"✗ ({critical_count} critical, {warning_count} warnings)")
                    elif warning_count > 0:
                        print(f"⚠️  ({warning_count} warnings)")
                    else:
                        print(f"ℹ️  (info only)")
                else:
                    print(f"✓")
            
            # Store content for cross-file checks
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_contents[file_path.name] = f.read()
            except IOError:
                pass  # Already reported in validate_file
        
        # Run cross-file consistency checks
        if len(file_contents) > 1:
            if show_progress:
                print(f"   Checking cross-file consistency...", end=" ")
            
            consistency_issues = check_consistency(file_contents)
            all_issues.extend(consistency_issues)
            
            if show_progress:
                if consistency_issues:
                    print(f"⚠️  ({len(consistency_issues)} issues)")
                else:
                    print(f"✓")
        
        # Optional: Run semantic consistency checks with LLM
        if use_llm and len(file_contents) > 1:
            if show_progress:
                print(f"   Running semantic consistency checks (LLM)...", end=" ")
            
            semantic_issues = self.check_consistency_semantic(file_contents)
            all_issues.extend(semantic_issues)
            
            if show_progress:
                if semantic_issues:
                    print(f"⚠️  ({len(semantic_issues)} issues)")
                else:
                    print(f"✓")
            # Note: LLM usage tracking would be updated in check_consistency_semantic
        
        # Categorize issues by severity
        for issue in all_issues:
            if issue.severity == "critical":
                report.critical_issues.append(issue)
            elif issue.severity == "warning":
                report.warnings.append(issue)
            else:  # "info"
                report.info.append(issue)
        
        # Determine overall status
        if report.critical_issues:
            report.overall_status = "fail"
        else:
            report.overall_status = "pass"
        
        return report
    
    def check_consistency_semantic(
        self,
        files: Dict[str, str],
        max_tokens: int = 1000
    ) -> List[ValidationIssue]:
        """
        Check semantic consistency using LLM for ambiguous cases.
        
        This method is optional and only used when rule-based checks cannot
        determine consistency. It sends a token-limited summary to the LLM
        to check for semantic contradictions.
        
        Args:
            files: Dictionary mapping file names to their content
            max_tokens: Maximum tokens to use per check
            
        Returns:
            List of validation issues found through semantic analysis
        """
        # TODO: Implement LLM-based semantic consistency checking
        # This would:
        # 1. Extract key information from each file (token-limited)
        # 2. Send to LLM with prompt asking for contradictions
        # 3. Parse LLM response for issues
        # 4. Track LLM calls and tokens used
        # 5. Return ValidationIssue objects
        
        # For now, return empty list (rule-based checks are primary)
        return []
