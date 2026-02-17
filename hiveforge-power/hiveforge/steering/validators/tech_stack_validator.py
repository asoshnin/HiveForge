"""
Tech stack validation for the Steering Assistant v02.

This module provides the TechStackValidator class for validating technology
stack claims against code analysis and framework classifications.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TechStackValidator:
    """Validates technology stack information for consistency."""
    
    def __init__(self, framework_classifications: Dict[str, List[str]]):
        """
        Initialize the TechStackValidator.
        
        Args:
            framework_classifications: Framework classification database
        """
        self.framework_classifications = framework_classifications
    
    def validate_tech_stack(
        self,
        files: Dict[str, str],
        code_analysis: Optional[Dict[str, any]] = None
    ) -> List[Dict[str, any]]:
        """
        Validate tech stack against code analysis results.
        
        Args:
            files: Dictionary mapping file names to their content
            code_analysis: Optional code analysis results
            
        Returns:
            List of validation issues
        """
        issues = []
        
        tech_stack_content = files.get("tech-stack.md", "")
        
        if not tech_stack_content:
            return issues
        
        # Extract tech stack information
        tech_info = self._extract_tech_stack(tech_stack_content)
        
        # Validate against code analysis if available
        if code_analysis:
            analysis_issues = self._validate_against_analysis(tech_info, code_analysis)
            issues.extend(analysis_issues)
        
        return issues
    
    def validate_framework_pairings(
        self,
        files: Dict[str, str],
        framework_type: str,
        forbidden_type: str
    ) -> List[Dict[str, any]]:
        """
        Validate that frameworks are correctly classified.
        
        Args:
            files: Dictionary mapping file names to their content
            framework_type: Type of framework to check (e.g., "backend")
            forbidden_type: Type that should not be used (e.g., "frontend")
            
        Returns:
            List of validation issues
        """
        issues = []
        
        tech_stack_content = files.get("tech-stack.md", "")
        if not tech_stack_content:
            return issues
        
        # Get forbidden frameworks
        forbidden_frameworks = self.framework_classifications.get(forbidden_type, [])
        
        # Extract framework from tech stack
        framework = self._extract_framework(tech_stack_content, framework_type)
        
        if framework and framework in forbidden_frameworks:
            issues.append({
                "file": "tech-stack.md",
                "type": "framework_misclassification",
                "message": f"{framework_type.capitalize()} framework '{framework}' is classified as a {forbidden_type} framework",
                "suggestion": f"Use a {framework_type} framework instead"
            })
        
        return issues
    
    def validate_version_consistency(
        self,
        files: Dict[str, str]
    ) -> List[Dict[str, any]]:
        """
        Validate version consistency across files.
        
        Args:
            files: Dictionary mapping file names to their content
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Extract versions from each file
        versions = {}
        for file_name, content in files.items():
            file_versions = self._extract_versions(content)
            if file_versions:
                versions[file_name] = file_versions
        
        # Check for version mismatches
        for file1, versions1 in versions.items():
            for file2, versions2 in versions.items():
                if file1 >= file2:  # Avoid duplicate checks
                    continue
                
                for tech, version1 in versions1.items():
                    if tech in versions2:
                        version2 = versions2[tech]
                        if version1 != version2:
                            issues.append({
                                "file": file1,
                                "type": "version_mismatch",
                                "message": f"Version mismatch for '{tech}': {file1} says '{version1}', {file2} says '{version2}'",
                                "suggestion": "Use consistent versions across files"
                            })
        
        return issues
    
    def validate_database_consistency(
        self,
        files: Dict[str, str]
    ) -> List[Dict[str, any]]:
        """
        Validate that database in db-standards.md is in tech-stack.md.
        
        Args:
            files: Dictionary mapping file names to their content
            
        Returns:
            List of validation issues
        """
        issues = []
        
        tech_stack_content = files.get("tech-stack.md", "")
        db_standards_content = files.get("db-standards.md", "")
        
        if not tech_stack_content or not db_standards_content:
            return issues
        
        # Extract databases
        tech_db = self._extract_database(tech_stack_content)
        db_standards_db = self._extract_database(db_standards_content)
        
        # Check if db-standards databases are in tech-stack
        for db in db_standards_db:
            if db not in tech_db:
                issues.append({
                    "file": "db-standards.md",
                    "type": "database_not_in_tech_stack",
                    "message": f"Database '{db}' in db-standards.md is not mentioned in tech-stack.md",
                    "suggestion": "Add database reference to tech-stack.md"
                })
        
        return issues
    
    def validate_api_consistency(
        self,
        files: Dict[str, str]
    ) -> List[Dict[str, any]]:
        """
        Validate that API framework matches backend framework.
        
        Args:
            files: Dictionary mapping file names to their content
            
        Returns:
            List of validation issues
        """
        issues = []
        
        tech_stack_content = files.get("tech-stack.md", "")
        api_standards_content = files.get("api-standards.md", "")
        
        if not tech_stack_content or not api_standards_content:
            return issues
        
        # Extract frameworks
        backend_framework = self._extract_backend_framework(tech_stack_content)
        api_framework = self._extract_api_framework(api_standards_content)
        
        # Check consistency
        if backend_framework and api_framework:
            if backend_framework != api_framework:
                issues.append({
                    "file": "api-standards.md",
                    "type": "api_framework_mismatch",
                    "message": f"API framework '{api_framework}' does not match backend framework '{backend_framework}'",
                    "suggestion": "Update API framework to match backend"
                })
        
        return issues
    
    def _extract_tech_stack(self, content: str) -> Dict[str, str]:
        """Extract tech stack information from content."""
        tech_info = {}
        
        # Extract backend framework
        backend_match = re.search(r"Backend.*?Framework:\s*(.+)", content, re.IGNORECASE | re.DOTALL)
        if backend_match:
            tech_info["backend_framework"] = backend_match.group(1).strip()
        
        # Extract frontend framework
        frontend_match = re.search(r"Frontend.*?Framework:\s*(.+)", content, re.IGNORECASE | re.DOTALL)
        if frontend_match:
            tech_info["frontend_framework"] = frontend_match.group(1).strip()
        
        # Extract database
        db_match = re.search(r"Primary:\s*(.+)", content, re.IGNORECASE)
        if db_match:
            tech_info["database"] = db_match.group(1).strip()
        
        return tech_info
    
    def _extract_framework(self, content: str, framework_type: str) -> Optional[str]:
        """Extract framework of specified type from content."""
        pattern = rf"{framework_type.capitalize()}\s*Framework:\s*(.+)"
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    def _extract_versions(self, content: str) -> Dict[str, str]:
        """Extract version information from content."""
        versions = {}
        
        # Match patterns like "Python 3.11", "React 18", "PostgreSQL 15"
        version_pattern = r"(\w+)\s*(\d+\.\d+)"
        
        for match in re.finditer(version_pattern, content):
            tech = match.group(1)
            version = match.group(2)
            
            # Skip common false positives
            if tech.lower() in ["the", "this", "that", "with", "using"]:
                continue
            
            versions[tech] = version
        
        return versions
    
    def _extract_database(self, content: str) -> List[str]:
        """Extract database mentions from content."""
        databases = ["PostgreSQL", "MongoDB", "MySQL", "Redis", "Cassandra"]
        found = []
        
        for db in databases:
            if db.lower() in content.lower():
                found.append(db)
        
        return found
    
    def _extract_backend_framework(self, content: str) -> Optional[str]:
        """Extract backend framework from content."""
        frameworks = ["FastAPI", "Express", "Django", "Flask", "Gin", "Spring Boot"]
        
        for framework in frameworks:
            if framework.lower() in content.lower():
                return framework
        
        return None
    
    def _extract_api_framework(self, content: str) -> Optional[str]:
        """Extract API framework from content."""
        return self._extract_backend_framework(content)
    
    def _validate_against_analysis(
        self,
        tech_info: Dict[str, str],
        code_analysis: Dict[str, any]
    ) -> List[Dict[str, any]]:
        """Validate tech stack against code analysis results."""
        issues = []
        
        # Compare detected languages with declared tech stack
        detected_languages = code_analysis.get("languages", [])
        detected_frameworks = code_analysis.get("frameworks", [])
        
        # Check for mismatches
        for lang in detected_languages:
            lang_name = lang.get("name", "")
            if lang_name.lower() == "javascript" and "python" in tech_info.get("backend_framework", "").lower():
                issues.append({
                    "file": "tech-stack.md",
                    "type": "language_mismatch",
                    "message": f"Detected JavaScript but backend framework is {tech_info.get('backend_framework')}",
                    "suggestion": "Review tech stack declaration"
                })
        
        return issues
