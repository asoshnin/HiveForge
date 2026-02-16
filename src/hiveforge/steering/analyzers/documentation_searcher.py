"""
Documentation search functionality for the Steering Assistant v02.

This module provides the DocumentationSearcher class for intelligently locating
and importing project documentation, metadata, and existing steering files.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple


class DocumentationSearcher:
    """Searches for documentation files and directories in a project."""
    
    # Documentation file patterns to search for
    DOC_FILE_PATTERNS = [
        "README*",
        "CONTRIBUTING*",
        "ARCHITECTURE*",
        "DESIGN*",
        "SPEC*",
        "REQUIREMENTS*",
    ]
    
    # Documentation directories to search
    DOC_DIRS = ["docs/", "documentation/", "design/", ".github/"]
    
    # Package metadata files to search for
    PACKAGE_FILES = [
        "package.json",
        "pyproject.toml",
        "Cargo.toml",
        "pom.xml",
    ]
    
    # CI/CD configuration files to search for
    CI_CD_FILES = [
        ".github/workflows/",
        ".gitlab-ci.yml",
        ".circleci/",
        "Jenkinsfile",
    ]
    
    # Deployment manifests to search for
    DEPLOYMENT_FILES = [
        "Dockerfile",
        "docker-compose.yml",
        "k8s/",
        "helm/",
    ]
    
    def __init__(
        self,
        max_file_size_mb: int = 10,
        max_files: int = 1000,
        custom_paths: Optional[List[str]] = None,
    ):
        """
        Initialize the DocumentationSearcher.
        
        Args:
            max_file_size_mb: Maximum file size in MB to analyze
            max_files: Maximum number of files to analyze
            custom_paths: Custom paths to search in addition to defaults
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_files = max_files
        self.custom_paths = custom_paths or []
        self._files_found = 0
    
    def search_docs_files(self, project_path: Path) -> List[Path]:
        """
        Search for documentation files matching patterns.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            List of paths to documentation files found
        """
        docs_files = []
        
        for pattern in self.DOC_FILE_PATTERNS:
            # Search in project root
            for match in project_path.glob(pattern):
                if match.is_file() and self._should_include_file(match):
                    docs_files.append(match)
                    self._files_found += 1
                    if self._files_found >= self.max_files:
                        return docs_files
            
            # Search in docs directories
            for docs_dir in self.DOC_DIRS:
                docs_path = project_path / docs_dir
                if docs_path.exists():
                    for match in docs_path.glob(pattern):
                        if match.is_file() and self._should_include_file(match):
                            docs_files.append(match)
                            self._files_found += 1
                            if self._files_found >= self.max_files:
                                return docs_files
        
        return docs_files
    
    def search_docs_dirs(self, project_path: Path) -> List[Path]:
        """
        Search for documentation directories.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            List of paths to documentation directories found
        """
        docs_dirs = []
        
        for dir_name in self.DOC_DIRS:
            dir_path = project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                docs_dirs.append(dir_path)
        
        return docs_dirs
    
    def search_package_files(self, project_path: Path) -> List[Path]:
        """
        Search for package metadata files.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            List of paths to package metadata files found
        """
        package_files = []
        
        for package_file in self.PACKAGE_FILES:
            file_path = project_path / package_file
            if file_path.exists() and file_path.is_file():
                package_files.append(file_path)
        
        return package_files
    
    def search_config_files(self, project_path: Path) -> List[Path]:
        """
        Search for CI/CD and deployment configuration files.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            List of paths to configuration files found
        """
        config_files = []
        
        # Search CI/CD files
        for ci_cd_file in self.CI_CD_FILES:
            file_path = project_path / ci_cd_file
            if file_path.exists():
                if file_path.is_file():
                    config_files.append(file_path)
                elif file_path.is_dir():
                    # Add all files in the directory
                    for f in file_path.rglob("*"):
                        if f.is_file() and self._should_include_file(f):
                            config_files.append(f)
                            self._files_found += 1
                            if self._files_found >= self.max_files:
                                return config_files
        
        # Search deployment files
        for deploy_file in self.DEPLOYMENT_FILES:
            file_path = project_path / deploy_file
            if file_path.exists():
                if file_path.is_file():
                    config_files.append(file_path)
                elif file_path.is_dir():
                    # Add all files in the directory
                    for f in file_path.rglob("*"):
                        if f.is_file() and self._should_include_file(f):
                            config_files.append(f)
                            self._files_found += 1
                            if self._files_found >= self.max_files:
                                return config_files
        
        return config_files
    
    def discover_all(self, project_path: Path) -> Tuple[List[Path], int]:
        """
        Run all discovery methods and return combined results.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            Tuple of (list of all discovered files, total count)
        """
        self._files_found = 0
        
        all_files = []
        
        # Search documentation files
        all_files.extend(self.search_docs_files(project_path))
        
        # Search package files
        all_files.extend(self.search_package_files(project_path))
        
        # Search config files
        all_files.extend(self.search_config_files(project_path))
        
        # Search docs directories
        all_files.extend(self.search_docs_dirs(project_path))
        
        # Add custom paths if specified
        for custom_path in self.custom_paths:
            path = Path(custom_path)
            if path.exists():
                if path.is_file():
                    all_files.append(path)
                elif path.is_dir():
                    for f in path.rglob("*"):
                        if f.is_file() and self._should_include_file(f):
                            all_files.append(f)
                            self._files_found += 1
                            if self._files_found >= self.max_files:
                                return all_files, min(len(all_files), self.max_files)
        
        return all_files, min(len(all_files), self.max_files)
    
    def _should_include_file(self, file_path: Path) -> bool:
        """
        Check if a file should be included based on size and type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be included
        """
        try:
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                return False
            
            # Skip binary files
            binary_extensions = {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin"}
            if file_path.suffix.lower() in binary_extensions:
                return False
            
            return True
        except (OSError, IOError):
            return False
