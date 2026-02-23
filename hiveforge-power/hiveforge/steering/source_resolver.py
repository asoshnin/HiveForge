"""
Source Document Resolver for HiveForge Steering.

This module provides secure path resolution and document discovery for custom
source document locations. It includes comprehensive security checks to prevent
path traversal attacks and respects .gitignore patterns.

**Validates: Requirements R1.3, R1.4, R1.5, R1.6**
"""

import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import pathspec
except ImportError:
    pathspec = None

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SourceDocumentInfo:
    """Information about a discovered source document."""
    
    path: Path
    file_type: str
    size_bytes: int
    discovered_from: str  # "staging", "custom_path", "project_root"
    is_symlink: bool = False
    original_path: Optional[Path] = None


# ============================================================================
# Exceptions
# ============================================================================

class SourceResolverError(Exception):
    """Base exception for source resolver errors."""
    pass


class PathValidationError(SourceResolverError):
    """Raised when path validation fails."""
    pass


class PathTraversalError(PathValidationError):
    """Raised when path traversal is detected."""
    pass


# ============================================================================
# Source Document Resolver
# ============================================================================

class SourceDocumentResolver:
    """
    Resolves and validates custom source document paths.
    
    This class provides secure path resolution with comprehensive security checks:
    - Path sanitization (whitespace, separators, null bytes)
    - Path validation (within project root, no traversal)
    - Symlink resolution and boundary checking
    - .gitignore pattern respect
    - Document discovery with symlink/copy options
    
    **Validates: Requirements R1.3, R1.4**
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the source document resolver.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root.resolve()
        self.excluded_paths: set = set()
        self._load_gitignore()
    
    def sanitize_path(self, path_str: str) -> str:
        """
        Sanitize user-provided path string.
        
        Sanitization rules:
        1. Strip leading/trailing whitespace
        2. Normalize path separators (convert to OS-specific)
        3. Remove redundant separators (// → /)
        4. Reject paths with null bytes
        5. Reject paths with control characters
        
        Args:
            path_str: Path string to sanitize
            
        Returns:
            Sanitized path string
            
        Raises:
            PathValidationError: If path contains invalid characters
            
        **Validates: Design - Input Sanitization**
        """
        if not path_str:
            raise PathValidationError("Path string is empty")
        
        # Strip whitespace
        path_str = path_str.strip()
        
        if not path_str:
            raise PathValidationError("Path string is empty after stripping whitespace")
        
        # Check for null bytes
        if '\0' in path_str:
            raise PathValidationError("Path contains null bytes")
        
        # Check for control characters (ASCII 0-31 except tab, newline, carriage return)
        for char in path_str:
            if ord(char) < 32 and char not in ('\t', '\n', '\r'):
                raise PathValidationError(
                    f"Path contains control character: {repr(char)}"
                )
        
        # Normalize separators to forward slashes first
        path_str = path_str.replace('\\', '/')
        
        # Remove redundant separators
        while '//' in path_str:
            path_str = path_str.replace('//', '/')
        
        # Remove trailing slash (except for root)
        if path_str != '/' and path_str.endswith('/'):
            path_str = path_str.rstrip('/')
        
        return path_str
    
    def validate_path(self, path: Path) -> bool:
        """
        Validate that path exists and is within project root.
        
        Security checks:
        1. Resolve symlinks to real paths
        2. Ensure resolved path is within project root
        3. Reject paths with null bytes
        4. Reject absolute paths outside project
        5. Reject parent directory traversal attempts
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid
            
        Raises:
            PathValidationError: If path is invalid
            PathTraversalError: If path attempts to escape project root
            
        **Validates: Design - Path Validation, Security Considerations**
        """
        try:
            # Check for null bytes in string representation
            path_str = str(path)
            if '\0' in path_str:
                raise PathValidationError("Path contains null bytes")
            
            # Resolve symlinks and relative paths to absolute path
            try:
                resolved = path.resolve(strict=False)
            except (OSError, ValueError) as e:
                raise PathValidationError(f"Cannot resolve path: {e}")
            
            # Ensure resolved path is within project root
            try:
                resolved.relative_to(self.project_root)
            except ValueError:
                raise PathTraversalError(
                    f"Path {path} resolves to {resolved} which is outside "
                    f"project root {self.project_root}"
                )
            
            # Additional check: ensure resolved path starts with project root
            # This catches symlink attacks where relative_to might pass but
            # the actual path escapes via symlink
            if not str(resolved).startswith(str(self.project_root)):
                raise PathTraversalError(
                    f"Path {path} escapes project root via symlink: "
                    f"{resolved} is not under {self.project_root}"
                )
            
            return True
            
        except PathValidationError:
            raise
        except PathTraversalError:
            raise
        except Exception as e:
            raise PathValidationError(f"Path validation failed: {e}")
    
    def resolve(
        self,
        source_docs_path: Optional[str],
        copy_files: bool = False
    ) -> Tuple[Path, List[SourceDocumentInfo]]:
        """
        Resolve source document path and discover documents.
        
        Args:
            source_docs_path: Relative path to source documents (None for default)
            copy_files: If True, copy files to staging. If False, use symlinks (default)
            
        Returns:
            Tuple of (resolved_path, discovered_documents)
            
        Raises:
            PathValidationError: If path is invalid or doesn't exist
            
        **Validates: Requirements R1.3, R1.4**
        """
        if source_docs_path is None:
            # Use default staging directory
            staging_dir = self.project_root / ".kiro" / "onboarding"
            staging_dir.mkdir(parents=True, exist_ok=True)
            
            # Discover documents in staging directory
            documents = self._discover_in_directory(
                staging_dir,
                discovered_from="staging"
            )
            
            return staging_dir, documents
        
        # Sanitize the provided path
        sanitized = self.sanitize_path(source_docs_path)
        
        # Create Path object (relative to project root)
        source_path = self.project_root / sanitized
        
        # Validate the path
        self.validate_path(source_path)
        
        # Check if path exists
        if not source_path.exists():
            raise PathValidationError(
                f"Source document path does not exist: {source_path}"
            )
        
        if not source_path.is_dir():
            raise PathValidationError(
                f"Source document path is not a directory: {source_path}"
            )
        
        # Create staging directory
        staging_dir = self.project_root / ".kiro" / "onboarding"
        staging_dir.mkdir(parents=True, exist_ok=True)
        
        # Discover and link/copy documents to staging
        documents = self.discover_documents(
            source_path,
            staging_dir,
            copy_files=copy_files
        )
        
        return staging_dir, documents
    
    def discover_documents(
        self,
        path: Path,
        staging_dir: Path,
        copy_files: bool = False
    ) -> List[SourceDocumentInfo]:
        """
        Discover documents in path and link/copy to staging.
        
        Args:
            path: Path to discover documents from
            staging_dir: Staging directory to link/copy to
            copy_files: If True, copy files. If False, create symlinks (default)
            
        Returns:
            List of discovered document info
            
        **Validates: Requirements R1.3, Design - Performance Considerations**
        """
        documents = []
        
        # Discover documents in the source path
        for file_path in self._iter_supported_files(path):
            # Skip if excluded by .gitignore
            if self._is_excluded(file_path):
                logger.debug(f"Skipping excluded file: {file_path}")
                continue
            
            # Get file info
            try:
                size_bytes = file_path.stat().st_size
            except OSError as e:
                logger.warning(f"Cannot stat file {file_path}: {e}")
                continue
            
            file_type = self._get_file_type(file_path)
            
            # Create destination path in staging
            # Use relative path from source to maintain structure
            try:
                rel_path = file_path.relative_to(path)
            except ValueError:
                # File is not under source path, skip
                logger.warning(f"File {file_path} is not under {path}, skipping")
                continue
            
            dest_path = staging_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Link or copy file to staging
            is_symlink = False
            if copy_files:
                # Copy file
                try:
                    shutil.copy2(file_path, dest_path)
                    logger.debug(f"Copied {file_path} to {dest_path}")
                except (OSError, shutil.Error) as e:
                    logger.warning(f"Cannot copy {file_path} to {dest_path}: {e}")
                    continue
            else:
                # Create symlink (default for performance)
                try:
                    # Remove existing file/symlink if present
                    if dest_path.exists() or dest_path.is_symlink():
                        dest_path.unlink()
                    
                    # Create symlink
                    dest_path.symlink_to(file_path)
                    is_symlink = True
                    logger.debug(f"Symlinked {file_path} to {dest_path}")
                except (OSError, NotImplementedError) as e:
                    # Symlinks might not be supported on some systems
                    # Fall back to copying
                    logger.warning(
                        f"Cannot create symlink from {dest_path} to {file_path}: {e}. "
                        f"Falling back to copy."
                    )
                    try:
                        shutil.copy2(file_path, dest_path)
                        logger.debug(f"Copied {file_path} to {dest_path} (fallback)")
                    except (OSError, shutil.Error) as e2:
                        logger.warning(f"Cannot copy {file_path} to {dest_path}: {e2}")
                        continue
            
            # Create document info
            doc_info = SourceDocumentInfo(
                path=dest_path,
                file_type=file_type,
                size_bytes=size_bytes,
                discovered_from="custom_path",
                is_symlink=is_symlink,
                original_path=file_path if is_symlink else None
            )
            documents.append(doc_info)
        
        logger.info(
            f"Discovered {len(documents)} documents from {path} "
            f"({'symlinked' if not copy_files else 'copied'} to {staging_dir})"
        )
        
        return documents
    
    def _discover_in_directory(
        self,
        directory: Path,
        discovered_from: str = "staging"
    ) -> List[SourceDocumentInfo]:
        """
        Discover documents in a directory without linking/copying.
        
        Args:
            directory: Directory to discover documents in
            discovered_from: Source label for discovered documents
            
        Returns:
            List of discovered document info
        """
        documents = []
        
        if not directory.exists():
            return documents
        
        for file_path in self._iter_supported_files(directory):
            # Skip if excluded by .gitignore
            if self._is_excluded(file_path):
                logger.debug(f"Skipping excluded file: {file_path}")
                continue
            
            # Get file info
            try:
                size_bytes = file_path.stat().st_size
                is_symlink = file_path.is_symlink()
            except OSError as e:
                logger.warning(f"Cannot stat file {file_path}: {e}")
                continue
            
            file_type = self._get_file_type(file_path)
            
            # Create document info
            doc_info = SourceDocumentInfo(
                path=file_path,
                file_type=file_type,
                size_bytes=size_bytes,
                discovered_from=discovered_from,
                is_symlink=is_symlink,
                original_path=file_path.resolve() if is_symlink else None
            )
            documents.append(doc_info)
        
        logger.info(f"Discovered {len(documents)} documents in {directory}")
        
        return documents
    
    def _iter_supported_files(self, directory: Path):
        """
        Iterate over supported files in directory.
        
        Supported types:
        - Markdown: .md, .markdown, .mdown, .mkd
        - PDF: .pdf
        - Images: .png, .jpg, .jpeg, .gif, .bmp, .tiff, .webp
        
        Args:
            directory: Directory to scan
            
        Yields:
            Path objects for supported files
        """
        supported_extensions = {
            # Markdown
            ".md", ".markdown", ".mdown", ".mkd",
            # PDF
            ".pdf",
            # Images
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"
        }
        
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    yield file_path
        except OSError as e:
            logger.error(f"Error scanning directory {directory}: {e}")
    
    def _get_file_type(self, file_path: Path) -> str:
        """
        Determine the type category of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            One of: "markdown", "pdf", "image"
        """
        suffix = file_path.suffix.lower()
        
        if suffix in {".md", ".markdown", ".mdown", ".mkd"}:
            return "markdown"
        elif suffix == ".pdf":
            return "pdf"
        elif suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}:
            return "image"
        else:
            return "unknown"
    
    def _load_gitignore(self) -> None:
        """
        Load .gitignore file and build exclusion list.
        
        Uses pathspec library to parse .gitignore patterns and build
        a set of paths to exclude from discovery.
        
        **Validates: Design - .gitignore respect**
        """
        gitignore_path = self.project_root / ".gitignore"
        
        if not gitignore_path.exists():
            logger.debug("No .gitignore file found")
            return
        
        if pathspec is None:
            logger.warning(
                "pathspec library not available, .gitignore will not be respected. "
                "Install with: pip install pathspec"
            )
            return
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
            
            # Build set of excluded paths
            for file_path in self.project_root.rglob("*"):
                try:
                    rel_path = file_path.relative_to(self.project_root)
                    if spec.match_file(str(rel_path)):
                        self.excluded_paths.add(file_path)
                except (ValueError, OSError):
                    continue
            
            logger.info(f"Loaded .gitignore: {len(self.excluded_paths)} paths excluded")
        
        except Exception as e:
            logger.warning(f"Error parsing .gitignore: {e}")
            # Continue without exclusions rather than failing
    
    def _is_excluded(self, file_path: Path) -> bool:
        """
        Check if a file path is excluded by .gitignore.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if path should be excluded
        """
        return file_path in self.excluded_paths
