"""
Document parser orchestrator for the Steering Assistant.

This module provides the main orchestrator that coordinates parsing of all
supported file types in the staging directory, with error handling and
aggregation of results.
"""

import logging
from pathlib import Path
from typing import List

from ..models import ParsedDocument
from ..utils import list_supported_files, get_file_type
from .markdown import parse_markdown
from .pdf import parse_pdf
from .image import parse_image

logger = logging.getLogger(__name__)


def parse_directory(staging_dir: Path, show_progress: bool = True) -> List[ParsedDocument]:
    """
    Parse all supported files in the staging directory.
    
    This function:
    - Discovers all supported files (markdown, PDF, images) in the directory
    - Parses each file using the appropriate parser
    - Handles parsing failures gracefully (logs error and continues)
    - Aggregates all results into a list of ParsedDocument objects
    - Displays progress for each file being processed (Req 14.1)
    
    The function implements resilient parsing: if one file fails to parse,
    it logs the error and continues processing remaining files. This ensures
    that a single corrupted file doesn't block the entire workflow.
    
    Args:
        staging_dir: Path to the staging directory containing source artifacts
        show_progress: Whether to display progress messages (default: True)
        
    Returns:
        List of ParsedDocument objects, one for each successfully discovered file.
        Files that fail to parse will still have a ParsedDocument entry with
        parse_errors populated.
        
    Requirements: 3.4, 3.5, 14.1
    """
    logger.info(f"Starting directory parsing: {staging_dir}")
    
    # Discover all supported files
    try:
        file_paths = list_supported_files(staging_dir)
        logger.info(f"Found {len(file_paths)} supported files to parse")
    except Exception as e:
        logger.error(f"Failed to list files in staging directory: {e}")
        return []
    
    if not file_paths:
        logger.warning(f"No supported files found in {staging_dir}")
        return []
    
    # Parse each file with appropriate parser
    parsed_documents = []
    total_files = len(file_paths)
    
    for idx, file_path in enumerate(file_paths, 1):
        # Display progress for current file (Req 14.1)
        if show_progress:
            print(f"   [{idx}/{total_files}] Parsing {file_path.name}...", end=" ")
        try:
            file_type = get_file_type(file_path)
            logger.debug(f"Parsing {file_type} file: {file_path}")
            
            # Route to appropriate parser based on file type
            if file_type == "markdown":
                parsed_doc = parse_markdown(file_path)
            elif file_type == "pdf":
                parsed_doc = parse_pdf(file_path)
            elif file_type == "image":
                parsed_doc = parse_image(file_path)
            else:
                # Unknown file type - create error document
                logger.warning(f"Unknown file type for: {file_path}")
                parsed_doc = ParsedDocument(
                    file_path=file_path,
                    content="",
                    metadata={"file_type": "unknown"},
                    parse_errors=[f"Unsupported file type: {file_path.suffix}"]
                )
            
            # Add to results
            parsed_documents.append(parsed_doc)
            
            # Display result for current file (Req 14.1)
            if show_progress:
                if parsed_doc.parse_errors:
                    print(f"⚠️  (with errors)")
                else:
                    print(f"✓")
            
            # Log parsing result
            if parsed_doc.parse_errors:
                logger.warning(
                    f"Parsed {file_path.name} with {len(parsed_doc.parse_errors)} errors: "
                    f"{'; '.join(parsed_doc.parse_errors[:2])}"
                )
            else:
                logger.info(
                    f"Successfully parsed {file_path.name} "
                    f"({len(parsed_doc.content)} characters)"
                )
        
        except FileNotFoundError:
            # File was deleted between discovery and parsing
            logger.error(f"File not found during parsing: {file_path}")
            if show_progress:
                print(f"✗ (file not found)")
            parsed_documents.append(ParsedDocument(
                file_path=file_path,
                content="",
                metadata={},
                parse_errors=[f"File not found: {file_path}"]
            ))
        
        except PermissionError:
            # Permission denied reading file
            logger.error(f"Permission denied reading file: {file_path}")
            if show_progress:
                print(f"✗ (permission denied)")
            parsed_documents.append(ParsedDocument(
                file_path=file_path,
                content="",
                metadata={},
                parse_errors=[f"Permission denied: {file_path}"]
            ))
        
        except Exception as e:
            # Unexpected error - log and continue with other files
            logger.error(f"Unexpected error parsing {file_path}: {e}", exc_info=True)
            if show_progress:
                print(f"✗ (error: {str(e)[:50]})")
            parsed_documents.append(ParsedDocument(
                file_path=file_path,
                content="",
                metadata={},
                parse_errors=[f"Unexpected error: {str(e)}"]
            ))
    
    # Log summary
    successful_parses = sum(1 for doc in parsed_documents if not doc.parse_errors)
    failed_parses = len(parsed_documents) - successful_parses
    
    logger.info(
        f"Directory parsing complete: {successful_parses} successful, "
        f"{failed_parses} with errors"
    )
    
    return parsed_documents


def get_parsing_summary(parsed_documents: List[ParsedDocument]) -> dict:
    """
    Generate a summary of parsing results.
    
    Args:
        parsed_documents: List of parsed documents
        
    Returns:
        Dictionary with summary statistics:
        {
            "total_files": int,
            "successful": int,
            "with_errors": int,
            "total_content_length": int,
            "files_by_type": {"markdown": int, "pdf": int, "image": int},
            "error_summary": List[str]
        }
    """
    total_files = len(parsed_documents)
    successful = sum(1 for doc in parsed_documents if not doc.parse_errors)
    with_errors = total_files - successful
    total_content_length = sum(len(doc.content) for doc in parsed_documents)
    
    # Count by file type
    files_by_type = {"markdown": 0, "pdf": 0, "image": 0, "unknown": 0}
    for doc in parsed_documents:
        file_type = get_file_type(doc.file_path)
        files_by_type[file_type] += 1
    
    # Collect error summary (first error from each failed file)
    error_summary = []
    for doc in parsed_documents:
        if doc.parse_errors:
            error_summary.append(f"{doc.file_path.name}: {doc.parse_errors[0]}")
    
    return {
        "total_files": total_files,
        "successful": successful,
        "with_errors": with_errors,
        "total_content_length": total_content_length,
        "files_by_type": files_by_type,
        "error_summary": error_summary
    }

"""
Discovery orchestrator for the Steering Assistant v02.

This module extends the DocumentParserOrchestrator with discovery capabilities
for finding documentation, analyzing git history, and managing user selections.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models import ParsedDocument
from ..analyzers.documentation_searcher import DocumentationSearcher
from ..analyzers.git_history_analyzer import GitHistoryAnalyzer


class DiscoveryOrchestrator:
    """Orchestrates the discovery phase for the Steering Assistant v02."""
    
    def __init__(
            self,
            max_discovery_files: int = 1000,
            max_file_size_mb: int = 10,
            discovery_paths: Optional[List[str]] = None,
            timeout_seconds: int = 30,
            source_docs_path: Optional[str] = None,
            file_types: Optional[List[str]] = None,
        ):
            """
            Initialize the DiscoveryOrchestrator.

            Args:
                max_discovery_files: Maximum files to analyze during discovery
                max_file_size_mb: Maximum file size in MB to analyze
                discovery_paths: Custom paths to search in addition to defaults
                timeout_seconds: Timeout for discovery operations
                source_docs_path: Optional path to prioritize for discovery (relative to project root)
                file_types: Optional list of file extensions to include (e.g., [".md", ".pdf"])
            """
            self.max_discovery_files = max_discovery_files
            self.max_file_size_mb = max_file_size_mb
            self.discovery_paths = discovery_paths or []
            self.timeout_seconds = timeout_seconds
            self.source_docs_path = source_docs_path
            self.file_types = file_types
            self._searcher: Optional[DocumentationSearcher] = None
            self._git_analyzer: Optional[GitHistoryAnalyzer] = None
            self._discovery_cache: Dict = {}
            self._discovery_stats: Dict[str, any] = {
                "files_by_type": {},
                "files_by_path": {},
                "files_included": 0,
                "files_excluded": 0
            }
    
    def _get_searcher(self) -> DocumentationSearcher:
        """Get or create the DocumentationSearcher instance."""
        if self._searcher is None:
            self._searcher = DocumentationSearcher(
                max_file_size_mb=self.max_file_size_mb,
                max_files=self.max_discovery_files,
                custom_paths=self.discovery_paths,
            )
        return self._searcher
    
    def _get_git_analyzer(self) -> GitHistoryAnalyzer:
        """Get or create the GitHistoryAnalyzer instance."""
        if self._git_analyzer is None:
            self._git_analyzer = GitHistoryAnalyzer()
        return self._git_analyzer
    
    def _discover_with_priority(
        self, project_path: Path, priority_path: Path
    ) -> Tuple[List[Path], int]:
        """
        Discover files with priority given to source_docs_path.
        
        Args:
            project_path: Root path of the project
            priority_path: Priority path to search first
            
        Returns:
            Tuple of (discovered files, file count)
        """
        searcher = self._get_searcher()
        
        # First, discover files in priority path
        priority_files, priority_count = searcher.discover_all(priority_path)
        
        # If we haven't reached the max files limit, discover from project root
        remaining_budget = self.max_discovery_files - len(priority_files)
        
        if remaining_budget > 0:
            # Temporarily adjust max files for remaining discovery
            original_max = searcher.max_files
            searcher.max_files = remaining_budget
            
            # Discover from project root, excluding priority path
            other_files, other_count = searcher.discover_all(project_path)
            
            # Filter out files already in priority_files
            priority_file_set = set(priority_files)
            other_files = [f for f in other_files if f not in priority_file_set]
            
            # Restore original max
            searcher.max_files = original_max
            
            # Combine results
            all_files = priority_files + other_files
            total_count = priority_count + other_count
        else:
            all_files = priority_files
            total_count = priority_count
        
        return all_files, total_count
    
    def _filter_by_file_types(self, files: List[Path]) -> List[Path]:
        """
        Filter files by specified file types.
        
        Args:
            files: List of file paths to filter
            
        Returns:
            Filtered list of files
        """
        if not self.file_types:
            return files
        
        filtered = []
        for file_path in files:
            if any(str(file_path).endswith(ext) for ext in self.file_types):
                filtered.append(file_path)
                self._discovery_stats["files_included"] += 1
            else:
                self._discovery_stats["files_excluded"] += 1
        
        return filtered
    
    def _update_discovery_stats(self, files: List[Path], project_path: Path) -> None:
        """
        Update discovery statistics for discovered files.
        
        Args:
            files: List of discovered files
            project_path: Root path of the project
        """
        for file_path in files:
            # Count by file type
            suffix = file_path.suffix.lower()
            if suffix:
                self._discovery_stats["files_by_type"][suffix] = \
                    self._discovery_stats["files_by_type"].get(suffix, 0) + 1
            else:
                self._discovery_stats["files_by_type"]["no_extension"] = \
                    self._discovery_stats["files_by_type"].get("no_extension", 0) + 1
            
            # Count by path (relative to project root)
            try:
                relative_path = file_path.relative_to(project_path)
                # Get the top-level directory
                if len(relative_path.parts) > 1:
                    top_dir = relative_path.parts[0]
                else:
                    top_dir = "root"
                
                self._discovery_stats["files_by_path"][top_dir] = \
                    self._discovery_stats["files_by_path"].get(top_dir, 0) + 1
            except ValueError:
                # File is outside project root
                self._discovery_stats["files_by_path"]["external"] = \
                    self._discovery_stats["files_by_path"].get("external", 0) + 1
    
    def discover_all(self, project_path: Path) -> Tuple[List[Path], Dict[str, any]]:
        """
        Run all discovery methods and return combined results.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            Tuple of (list of discovered files, discovery metadata)
        """
        searcher = self._get_searcher()
        
        # Reset statistics
        self._discovery_stats = {
            "files_by_type": {},
            "files_by_path": {},
            "files_included": 0,
            "files_excluded": 0
        }
        
        # Prioritize source_docs_path if provided
        if self.source_docs_path:
            source_path = project_path / self.source_docs_path
            if source_path.exists() and source_path.is_dir():
                # Discover files in priority path first
                discovered_files, file_count = self._discover_with_priority(
                    project_path, source_path
                )
            else:
                logger.warning(f"Source docs path does not exist: {source_path}")
                # Fall back to default discovery
                discovered_files, file_count = searcher.discover_all(project_path)
        else:
            # Default discovery
            discovered_files, file_count = searcher.discover_all(project_path)
        
        # Apply file type filtering if specified
        if self.file_types:
            discovered_files = self._filter_by_file_types(discovered_files)
        
        # Update statistics
        self._update_discovery_stats(discovered_files, project_path)
        
        # Get git history summary
        git_analyzer = self._get_git_analyzer()
        git_summary = git_analyzer.get_summary(project_path)
        commit_count = git_analyzer.get_commit_count(project_path)
        
        # Build enhanced metadata
        metadata = {
            "file_count": len(discovered_files),
            "commit_count": commit_count,
            "git_summary_available": len(git_summary) > 0,
            "custom_paths": self.discovery_paths,
            "max_files": self.max_discovery_files,
            "max_file_size_mb": self.max_file_size_mb,
            "source_docs_path": self.source_docs_path,
            "file_types": self.file_types,
            "files_by_type": self._discovery_stats["files_by_type"],
            "files_by_path": self._discovery_stats["files_by_path"],
            "files_included": self._discovery_stats["files_included"],
            "files_excluded": self._discovery_stats["files_excluded"],
        }
        
        return discovered_files, metadata
    
    def present_to_user(
        self,
        discovered_files: List[Path],
        metadata: Dict[str, any],
        show_relevance: bool = True,
    ) -> List[Path]:
        """
        Present discovered files to the user with relevance indicators.
        
        Args:
            discovered_files: List of discovered file paths
            metadata: Discovery metadata
            show_relevance: Whether to show relevance indicators
            
        Returns:
            List of files selected by the user (all by default)
        """
        print("\n=== Discovery Results ===")
        print(f"Files found: {metadata['file_count']}")
        print(f"Commits analyzed: {metadata['commit_count']}")
        
        if metadata['custom_paths']:
            print(f"Custom paths: {', '.join(metadata['custom_paths'])}")
        
        print("\nDiscovered files:")
        
        # Group files by type
        docs_files = []
        config_files = []
        package_files = []
        other_files = []
        
        for file_path in discovered_files:
            file_str = str(file_path)
            if any(doc in file_str for doc in ["README", "CONTRIBUTING", "ARCHITECTURE", "DESIGN", "SPEC", "REQUIREMENTS"]):
                docs_files.append(file_path)
            elif any(cfg in file_str for cfg in [".github", ".gitlab", ".circleci", "Jenkinsfile", "docker", "k8s", "helm"]):
                config_files.append(file_path)
            elif any(pkg in file_str for pkg in ["package.json", "pyproject.toml", "Cargo.toml", "pom.xml"]):
                package_files.append(file_path)
            else:
                other_files.append(file_path)
        
        # Display grouped
        if docs_files:
            print("\nDocumentation files:")
            for f in docs_files[:20]:  # Show first 20
                relevance = self._calculate_relevance(f)
                if show_relevance:
                    print(f"  {f} (relevance: {relevance:.1%})")
                else:
                    print(f"  {f}")
        
        if config_files:
            print("\nConfiguration files:")
            for f in config_files[:20]:
                relevance = self._calculate_relevance(f)
                if show_relevance:
                    print(f"  {f} (relevance: {relevance:.1%})")
                else:
                    print(f"  {f}")
        
        if package_files:
            print("\nPackage metadata files:")
            for f in package_files:
                relevance = self._calculate_relevance(f)
                if show_relevance:
                    print(f"  {f} (relevance: {relevance:.1%})")
                else:
                    print(f"  {f}")
        
        if other_files:
            print("\nOther files:")
            for f in other_files[:10]:
                relevance = self._calculate_relevance(f)
                if show_relevance:
                    print(f"  {f} (relevance: {relevance:.1%})")
                else:
                    print(f"  {f}")
        
        # If more than 50 files, indicate truncation
        total_shown = len(docs_files) + len(config_files) + len(package_files) + len(other_files)
        if total_shown < metadata['file_count']:
            print(f"\n... and {metadata['file_count'] - total_shown} more files")
        
        # For now, return all files (user selection can be added later)
        return discovered_files
    
    def _calculate_relevance(self, file_path: Path) -> float:
        """
        Calculate relevance score for a discovered file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        file_str = str(file_path).lower()
        
        # High relevance for standard documentation
        if any(doc in file_str for doc in ["readme", "contributing"]):
            return 0.95
        if any(doc in file_str for doc in ["architecture", "design"]):
            return 0.90
        if any(doc in file_str for doc in ["spec", "requirements"]):
            return 0.85
        
        # Medium relevance for configuration
        if any(cfg in file_str for cfg in ["docker", "k8s", "helm"]):
            return 0.70
        if any(cfg in file_str for cfg in [".github", ".gitlab", ".circleci"]):
            return 0.65
        
        # Lower relevance for package files
        if any(pkg in file_str for pkg in ["package.json", "pyproject.toml"]):
            return 0.60
        
        return 0.50
    
    def filter_by_user_selection(
        self,
        discovered_files: List[Path],
        user_selection: Optional[List[Path]] = None,
    ) -> List[Path]:
        """
        Filter discovered files based on user selection.
        
        Args:
            discovered_files: All discovered files
            user_selection: User-selected files (None = select all)
            
        Returns:
            Filtered list of files
        """
        if user_selection is None or len(user_selection) == 0:
            return discovered_files
        
        # Return only selected files that were discovered
        return [f for f in user_selection if f in discovered_files]
    
    def cache_results(
        self,
        discovered_files: List[Path],
        metadata: Dict[str, any],
        cache_dir: Path = Path(".kiro/.cache"),
    ) -> None:
        """
        Save discovery results to cache.
        
        Args:
            discovered_files: List of discovered file paths
            metadata: Discovery metadata
            cache_dir: Directory to save cache to
        """
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "discovery_cache.json"
        
        self._discovery_cache = {
            "files": [str(f) for f in discovered_files],
            "metadata": metadata,
            "timestamp": metadata.get("timestamp", ""),
        }
        
        with open(cache_file, "w") as f:
            json.dump(self._discovery_cache, f, indent=2)
    
    def load_cached_results(
        self,
        cache_dir: Path = Path(".kiro/.cache"),
    ) -> Optional[Dict]:
        """
        Load discovery results from cache.
        
        Args:
            cache_dir: Directory containing cache
            
        Returns:
            Cached results or None if not found
        """
        cache_file = cache_dir / "discovery_cache.json"
        
        if cache_file.exists():
            with open(cache_file, "r") as f:
                return json.load(f)
        
        return None
    
    def clear_cache(
        self,
        cache_dir: Path = Path(".kiro/.cache"),
    ) -> None:
        """
        Clear discovery cache.
        
        Args:
            cache_dir: Directory containing cache
        """
        cache_file = cache_dir / "discovery_cache.json"
        
        if cache_file.exists():
            cache_file.unlink()
