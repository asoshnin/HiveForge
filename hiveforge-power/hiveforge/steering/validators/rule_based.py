"""
Rule-based validation functions for steering files.

This module provides validation functions that use regex, structure checks,
and keyword matching to validate steering files without requiring LLM calls.
These functions are designed to be fast, deterministic, and token-efficient.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..models import Template, ValidationIssue


def check_completeness(
    content: str,
    template: Template,
    file_name: str
) -> List[ValidationIssue]:
    """
    Check if all required template sections are populated using regex.
    
    Detects unreplaced placeholders like {placeholder}, {value}, etc.
    
    Args:
        content: The steering file content to validate
        template: The template definition for this file
        file_name: Name of the file being validated
        
    Returns:
        List of validation issues found (empty if complete)
    """
    issues: List[ValidationIssue] = []
    
    # Check each section for unreplaced placeholders
    for section in template.sections:
        if not section.placeholder_pattern:
            continue
            
        # Find all matches of the placeholder pattern
        matches = re.finditer(section.placeholder_pattern, content, re.IGNORECASE)
        
        for match in matches:
            # Get line number for the match
            line_number = content[:match.start()].count('\n') + 1
            
            # Create issue for unreplaced placeholder
            severity = "critical" if section.required else "warning"
            issues.append(ValidationIssue(
                severity=severity,
                file_name=file_name,
                line_number=line_number,
                issue_type="incomplete_section",
                message=f"Section '{section.name}' contains unreplaced placeholder: {match.group()}",
                suggestion=f"Replace the placeholder with actual content for {section.name}"
            ))
    
    # Also check for generic placeholder patterns that might not be in template
    generic_patterns = [
        r'\{[A-Z_]+\}',  # {PLACEHOLDER}
        r'\{\.\.\.+\}',  # {...}
        r'\{TODO[:\s].*?\}',  # {TODO: something} or {TODO something}
        r'\{FILL.*?\}',  # {FILL IN}
    ]
    
    for pattern in generic_patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            # Skip if already reported by section-specific check
            if any(issue.line_number == content[:match.start()].count('\n') + 1 
                   for issue in issues):
                continue
                
            line_number = content[:match.start()].count('\n') + 1
            issues.append(ValidationIssue(
                severity="warning",
                file_name=file_name,
                line_number=line_number,
                issue_type="unreplaced_placeholder",
                message=f"Unreplaced placeholder found: {match.group()}",
                suggestion="Replace this placeholder with actual content"
            ))
    
    return issues


def check_structure(
    content: str,
    template: Template,
    file_name: str
) -> List[ValidationIssue]:
    """
    Verify frontmatter and template structure are preserved.
    
    Checks for:
    - Presence of required frontmatter fields
    - Correct frontmatter format (YAML between --- markers)
    - Presence of required sections
    
    Args:
        content: The steering file content to validate
        template: The template definition for this file
        file_name: Name of the file being validated
        
    Returns:
        List of validation issues found (empty if structure is valid)
    """
    issues: List[ValidationIssue] = []
    
    # Check for frontmatter presence
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    frontmatter_match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not frontmatter_match:
        issues.append(ValidationIssue(
            severity="critical",
            file_name=file_name,
            line_number=1,
            issue_type="missing_frontmatter",
            message="File is missing frontmatter (YAML between --- markers)",
            suggestion="Add frontmatter at the beginning of the file with 'inclusion' and 'priority' fields"
        ))
        return issues  # Can't check further without frontmatter
    
    frontmatter_content = frontmatter_match.group(1)
    
    # Check for required frontmatter fields
    required_fields = template.frontmatter.keys()
    for field in required_fields:
        field_pattern = rf'^{field}:\s*.+$'
        if not re.search(field_pattern, frontmatter_content, re.MULTILINE):
            issues.append(ValidationIssue(
                severity="critical",
                file_name=file_name,
                line_number=2,  # Approximate line in frontmatter
                issue_type="missing_frontmatter_field",
                message=f"Frontmatter is missing required field: {field}",
                suggestion=f"Add '{field}: {template.frontmatter[field]}' to frontmatter"
            ))
    
    # Check for presence of required sections (by heading)
    for section in template.sections:
        if not section.required:
            continue
            
        # Look for section heading (markdown header)
        # Try different header levels (##, ###, ####)
        section_patterns = [
            rf'^##\s+{re.escape(section.name)}\s*$',
            rf'^###\s+{re.escape(section.name)}\s*$',
            rf'^####\s+{re.escape(section.name)}\s*$',
        ]
        
        found = False
        for pattern in section_patterns:
            if re.search(pattern, content, re.MULTILINE):
                found = True
                break
        
        if not found:
            issues.append(ValidationIssue(
                severity="critical",
                file_name=file_name,
                line_number=None,
                issue_type="missing_required_section",
                message=f"Required section '{section.name}' is missing",
                suggestion=f"Add a section with heading '## {section.name}'"
            ))
    
    return issues


def check_consistency(
    files: Dict[str, str],
    file_names: Optional[List[str]] = None
) -> List[ValidationIssue]:
    """
    Check for contradictions across steering files using keyword matching.
    
    Performs rule-based consistency checks:
    - Technology choices mentioned in tech-stack should align with conventions
    - Database type should be consistent across tech-stack and db-standards
    - Language mentioned in tech-stack should match conventions
    
    Args:
        files: Dictionary mapping file names to their content
        file_names: Optional list of file names to check (defaults to all)
        
    Returns:
        List of validation issues found (empty if consistent)
    """
    issues: List[ValidationIssue] = []
    
    if file_names is None:
        file_names = list(files.keys())
    
    # Extract tech-stack content if available
    tech_stack_content = files.get("tech-stack.md", "")
    conventions_content = files.get("conventions.md", "")
    db_standards_content = files.get("db-standards.md", "")
    
    # Check 1: Database consistency between tech-stack and db-standards
    if tech_stack_content and db_standards_content:
        db_issues = _check_database_consistency(
            tech_stack_content,
            db_standards_content
        )
        issues.extend(db_issues)
    
    # Check 2: Language consistency between tech-stack and conventions
    if tech_stack_content and conventions_content:
        lang_issues = _check_language_consistency(
            tech_stack_content,
            conventions_content
        )
        issues.extend(lang_issues)
    
    # Check 3: Framework consistency
    if tech_stack_content and conventions_content:
        framework_issues = _check_framework_consistency(
            tech_stack_content,
            conventions_content
        )
        issues.extend(framework_issues)
    
    return issues


def _check_database_consistency(
    tech_stack_content: str,
    db_standards_content: str
) -> List[ValidationIssue]:
    """Check consistency between database choices in tech-stack and db-standards."""
    issues: List[ValidationIssue] = []
    
    # Define database types and their keywords
    sql_databases = {"postgresql", "postgres", "mysql", "mariadb", "sqlite", "sql server"}
    nosql_databases = {"mongodb", "mongo", "couchdb", "cassandra", "dynamodb"}
    
    # Extract database mentions from tech-stack
    tech_stack_lower = tech_stack_content.lower()
    mentioned_sql = any(db in tech_stack_lower for db in sql_databases)
    mentioned_nosql = any(db in tech_stack_lower for db in nosql_databases)
    
    # Check db-standards for SQL vs NoSQL patterns
    db_standards_lower = db_standards_content.lower()
    # Use word boundaries for SQL to avoid matching "nosql"
    has_sql_patterns = any(keyword in db_standards_lower 
                          for keyword in ["table", "join", "foreign key"]) or \
                      bool(re.search(r'\bsql\b', db_standards_lower))
    has_nosql_patterns = any(keyword in db_standards_lower 
                            for keyword in ["document", "collection", "key-value", "mongodb"])
    
    # Detect contradictions
    if mentioned_sql and has_nosql_patterns and not has_sql_patterns:
        issues.append(ValidationIssue(
            severity="warning",
            file_name="db-standards.md",
            line_number=None,
            issue_type="database_type_mismatch",
            message="tech-stack.md mentions SQL database but db-standards.md contains NoSQL patterns",
            suggestion="Ensure db-standards.md includes SQL-specific guidelines (tables, schemas, joins)"
        ))
    
    if mentioned_nosql and has_sql_patterns and not has_nosql_patterns:
        issues.append(ValidationIssue(
            severity="warning",
            file_name="db-standards.md",
            line_number=None,
            issue_type="database_type_mismatch",
            message="tech-stack.md mentions NoSQL database but db-standards.md contains SQL patterns",
            suggestion="Ensure db-standards.md includes NoSQL-specific guidelines (documents, collections)"
        ))
    
    return issues


def _check_language_consistency(
    tech_stack_content: str,
    conventions_content: str
) -> List[ValidationIssue]:
    """Check consistency between languages in tech-stack and conventions."""
    issues: List[ValidationIssue] = []
    
    # Define language keywords and their naming conventions
    language_conventions = {
        "python": {"snake_case", "pascalcase", "upper_snake_case"},
        "javascript": {"camelcase", "pascalcase", "upper_snake_case"},
        "typescript": {"camelcase", "pascalcase", "upper_snake_case"},
        "go": {"camelcase", "pascalcase", "mixedcaps"},
        "rust": {"snake_case", "pascalcase", "upper_snake_case"},
        "java": {"camelcase", "pascalcase", "upper_snake_case"},
        "ruby": {"snake_case", "pascalcase", "upper_snake_case"},
    }
    
    tech_stack_lower = tech_stack_content.lower()
    conventions_lower = conventions_content.lower()
    
    # Find mentioned languages
    mentioned_languages = [lang for lang in language_conventions.keys() 
                          if lang in tech_stack_lower]
    
    if not mentioned_languages:
        return issues
    
    # Check if conventions mention appropriate naming styles
    for lang in mentioned_languages:
        expected_conventions = language_conventions[lang]
        has_expected = any(conv in conventions_lower for conv in expected_conventions)
        
        if not has_expected:
            issues.append(ValidationIssue(
                severity="info",
                file_name="conventions.md",
                line_number=None,
                issue_type="missing_language_conventions",
                message=f"tech-stack.md mentions {lang.title()} but conventions.md doesn't include typical {lang.title()} naming conventions",
                suggestion=f"Consider adding {lang.title()}-specific naming conventions (e.g., {', '.join(list(expected_conventions)[:2])})"
            ))
    
    return issues


def _check_framework_consistency(
    tech_stack_content: str,
    conventions_content: str
) -> List[ValidationIssue]:
    """Check consistency between frameworks in tech-stack and conventions."""
    issues: List[ValidationIssue] = []
    
    # Define framework-specific patterns
    framework_patterns = {
        "react": ["jsx", "component", "hook", "props"],
        "vue": ["component", "template", "composition"],
        "angular": ["component", "directive", "service"],
        "express": ["middleware", "route", "controller"],
        "fastapi": ["endpoint", "route", "dependency"],
        "django": ["view", "model", "template"],
    }
    
    tech_stack_lower = tech_stack_content.lower()
    conventions_lower = conventions_content.lower()
    
    # Find mentioned frameworks
    for framework, patterns in framework_patterns.items():
        if framework in tech_stack_lower:
            # Check if conventions mention framework-specific patterns
            has_patterns = any(pattern in conventions_lower for pattern in patterns)
            
            if not has_patterns:
                issues.append(ValidationIssue(
                    severity="info",
                    file_name="conventions.md",
                    line_number=None,
                    issue_type="missing_framework_conventions",
                    message=f"tech-stack.md mentions {framework.title()} but conventions.md doesn't include {framework.title()}-specific patterns",
                    suggestion=f"Consider adding {framework.title()}-specific conventions (e.g., {', '.join(patterns[:2])})"
                ))
    
    return issues
