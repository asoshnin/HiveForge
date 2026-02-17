"""
Scalable discovery functionality for large repositories (v02.1).

This module provides the ScalableDiscovery class for handling discovery
in repositories with 100,000+ files efficiently using heuristic sampling,
intelligent file ranking, and parallel scanning.

Requirements: 24.1-24.8 (enhanced for v02.1)
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from threading import Event

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryProgress:
    """Tracks discovery progress for large repositories."""
    files_scanned: int = 0
    files_included: int = 0
    files_skipped: int = 0
    skipped_files: List[Dict] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    is_cancelled: bool = False
    estimated_total: Optional[int] = None
    
    def cancel(self) -> None:
        """Cancel the discovery operation."""
        self.is_cancelled = True
    
    def get_elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def get_files_per_second(self) -> float:
        """Calculate scanning speed."""
        elapsed = self.get_elapsed_seconds()
        if elapsed > 0:
            return self.files_scanned / elapsed
        return 0.0
    
    def get_estimated_remaining_seconds(self) -> Optional[float]:
        """Estimate remaining time based on current progress."""
        if self.estimated_total and self.files_scanned > 0:
            remaining = self.estimated_total - self.files_scanned
            speed = self.get_files_per_second()
            if speed > 0:
                return remaining / speed
        return None


@dataclass
class FileCandidate:
    """Represents a file candidate for discovery with ranking information."""
    path: Path
    relevance_score: float  # 0.0-1.0
    skip_reason: Optional[str] = None
    file_size_bytes: int = 0
    is_binary: bool = False
    
    def should_include(self) -> bool:
        """Check if this file should be included in discovery."""
        return self.skip_reason is None


class HeuristicSampler:
    """Implements heuristic sampling strategies for large repositories."""
    
    # High-priority patterns that indicate relevant documentation
    HIGH_PRIORITY_PATTERNS = [
        "readme", "contributing", "license", "changelog",
        "architecture", "design", "spec", "requirements",
    ]
    
    # Medium-priority patterns for configuration and metadata
    MEDIUM_PRIORITY_PATTERNS = [
        "package.json", "pyproject.toml", "cargo.toml", "pom.xml",
        "dockerfile", "docker-compose", "k8s", "helm",
        ".github/workflows", ".gitlab-ci", ".circleci",
    ]
    
    # Low-priority but still relevant patterns
    LOW_PRIORITY_PATTERNS = [
        "docs/", "documentation/", "api/", "guides/",
    ]
    
    # Directories to skip entirely
    SKIP_DIRS = {
        "__pycache__", ".git", "node_modules", "venv", ".venv",
        "build", "dist", ".tox", ".nox", "target", "out",
    }
    
    # File extensions to skip
    SKIP_EXTENSIONS = {
        ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".o", ".a",
        ".class", ".jar", ".war", ".ear", ".zip", ".tar", ".gz",
        ".min.js", ".min.css", ".map", ".lockb",
    }
    
    def __init__(self, sample_ratio: float = 0.1, min_sample: int = 100):
        """
        Initialize the heuristic sampler.
        
        Args:
            sample_ratio: Ratio of files to sample when repository is very large
            min_sample: Minimum number of files to sample
        """
        self.sample_ratio = sample_ratio
        self.min_sample = min_sample
    
    def should_sample(self, total_files: int, threshold: int = 10000) -> bool:
        """
        Determine if sampling should be used based on repository size.
        
        Args:
            total_files: Total number of files in repository
            threshold: Threshold for enabling sampling
            
        Returns:
            True if sampling should be used
        """
        return total_files > threshold
    
    def calculate_sample_size(self, total_files: int) -> int:
        """
        Calculate the number of files to sample.
        
        Args:
            total_files: Total number of files in repository
            
        Returns:
            Number of files to sample
        """
        sample_size = max(
            self.min_sample,
            int(total_files * self.sample_ratio)
        )
        return min(sample_size, total_files)
    
    def sample_files(
        self,
        all_files: List[Path],
        target_count: int,
    ) -> List[Path]:
        """
        Sample files using stratified sampling to ensure coverage.
        
        Args:
            all_files: All files in the repository
            target_count: Number of files to sample
            
        Returns:
            Sampled list of files
        """
        if len(all_files) <= target_count:
            return all_files
        
        # Stratify by priority
        high_priority: List[Path] = []
        medium_priority: List[Path] = []
        low_priority: List[Path] = []
        other: List[Path] = []
        
        for file_path in all_files:
            file_str = str(file_path).lower()
            priority = self._get_file_priority(file_str)
            if priority == "high":
                high_priority.append(file_path)
            elif priority == "medium":
                medium_priority.append(file_path)
            elif priority == "low":
                low_priority.append(file_path)
            else:
                other.append(file_path)
        
        # Calculate sample counts for each stratum
        total = len(all_files)
        high_ratio = len(high_priority) / total if total > 0 else 0
        medium_ratio = len(medium_priority) / total if total > 0 else 0
        low_ratio = len(low_priority) / total if total > 0 else 0
        
        high_sample = max(1, int(target_count * high_ratio))
        medium_sample = max(1, int(target_count * medium_ratio))
        low_sample = max(1, int(target_count * low_ratio))
        
        # Ensure we don't exceed available files
        high_sample = min(high_sample, len(high_priority))
        medium_sample = min(medium_sample, len(medium_priority))
        low_sample = min(low_sample, len(low_priority))
        
        remaining = target_count - high_sample - medium_sample - low_sample
        other_sample = max(0, remaining)
        
        # Sample from each stratum
        sampled = []
        sampled.extend(high_priority[:high_sample])
        sampled.extend(medium_priority[:medium_sample])
        sampled.extend(low_priority[:low_sample])
        
        if other_sample > 0 and other:
            # Sample from 'other' proportionally
            other_sample = min(other_sample, len(other))
            sampled.extend(other[:other_sample])
        
        return sampled
    
    def _get_file_priority(self, file_str: str) -> str:
        """Determine priority level for a file based on its path."""
        if any(pattern in file_str for pattern in self.HIGH_PRIORITY_PATTERNS):
            return "high"
        if any(pattern in file_str for pattern in self.MEDIUM_PRIORITY_PATTERNS):
            return "medium"
        if any(pattern in file_str for pattern in self.LOW_PRIORITY_PATTERNS):
            return "low"
        return "other"
    
    def is_skip_dir(self, path: Path) -> bool:
        """Check if a directory should be skipped entirely."""
        path_str = str(path).lower()
        return any(skip in path_str for skip in self.SKIP_DIRS)
    
    def is_skip_extension(self, file_path: Path) -> bool:
        """Check if a file extension should be skipped."""
        return file_path.suffix.lower() in self.SKIP_EXTENSIONS


class IntelligentFileRanker:
    """Ranks files by relevance for intelligent discovery."""
    
    # Relevance weights for different file types
    RELEVANCE_WEIGHTS = {
        "documentation": 1.0,
        "config": 0.8,
        "package": 0.7,
        "source": 0.5,
        "test": 0.3,
        "build": 0.2,
        "other": 0.1,
    }
    
    def __init__(self):
        """Initialize the file ranker."""
        self._file_type_cache: Dict[Path, str] = {}
    
    def rank_file(self, file_path: Path) -> float:
        """
        Calculate relevance score for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        file_str = str(file_path)
        file_type = self._get_file_type(file_str)
        base_weight = self.RELEVANCE_WEIGHTS.get(file_type, 0.1)
        
        # Adjust based on file name patterns
        name_bonus = self._get_name_bonus(file_str)
        
        # Adjust based on directory depth (shallower = more relevant)
        depth_bonus = self._get_depth_bonus(file_path)
        
        score = base_weight + name_bonus + depth_bonus
        return min(1.0, max(0.0, score))
    
    def rank_files(self, file_paths: List[Path]) -> List[FileCandidate]:
        """
        Rank multiple files and return candidates with scores.
        
        Args:
            file_paths: List of file paths to rank
            
        Returns:
            List of FileCandidate objects sorted by relevance
        """
        candidates = []
        for file_path in file_paths:
            try:
                stat = file_path.stat()
                is_binary = self._is_binary_file(file_path)
                score = self.rank_file(file_path)
                
                candidate = FileCandidate(
                    path=file_path,
                    relevance_score=score,
                    file_size_bytes=stat.st_size,
                    is_binary=is_binary,
                )
                candidates.append(candidate)
            except (OSError, IOError):
                # Skip files we can't access
                candidates.append(FileCandidate(
                    path=file_path,
                    relevance_score=0.0,
                    skip_reason="access_error",
                ))
        
        # Sort by relevance score (descending)
        candidates.sort(key=lambda c: c.relevance_score, reverse=True)
        return candidates
    
    def _get_file_type(self, file_str: str) -> str:
        """Determine the type category for a file."""
        file_str = file_str.lower()
        
        if any(doc in file_str for doc in ["readme", "contributing", "license", "changelog"]):
            return "documentation"
        if any(doc in file_str for doc in ["architecture", "design", "spec", "requirements"]):
            return "documentation"
        if any(doc in file_str for doc in ["docs/", "documentation/"]):
            return "documentation"
        
        if any(cfg in file_str for cfg in [".github/", ".gitlab-", ".circleci", "dockerfile", "docker-compose"]):
            return "config"
        if any(cfg in file_str for cfg in ["k8s/", "helm/", "jenkins"]):
            return "config"
        
        if any(pkg in file_str for pkg in ["package.json", "pyproject.toml", "cargo.toml", "pom.xml"]):
            return "package"
        
        if any(src in file_str for src in [".py", ".js", ".ts", ".java", ".go", ".rs"]):
            return "source"
        if "/src/" in file_str or "/lib/" in file_str:
            return "source"
        
        if "test" in file_str or "spec" in file_str or "/tests/" in file_str:
            return "test"
        
        if "build" in file_str or "dist" in file_str or "target" in file_str:
            return "build"
        
        return "other"
    
    def _get_name_bonus(self, file_str: str) -> float:
        """Calculate bonus score based on file name patterns."""
        bonus = 0.0
        file_str = file_str.lower()
        
        # Bonus for files in root directory
        if file_str.count("/") <= 1:
            bonus += 0.1
        
        # Bonus for files with specific names
        if file_str.endswith("readme.md") or file_str.endswith("readme.txt"):
            bonus += 0.15
        if "license" in file_str and file_str.endswith((".md", ".txt")):
            bonus += 0.1
        
        return bonus
    
    def _get_depth_bonus(self, file_path: Path) -> float:
        """Calculate bonus based on directory depth."""
        try:
            depth = len(file_path.relative_to(file_path.parent).parts) - 1
            # Shallower files get higher scores
            return max(0.0, 0.1 - (depth * 0.02))
        except ValueError:
            return 0.0
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is likely binary."""
        binary_extensions = {
            ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".o", ".a",
            ".class", ".jar", ".war", ".ear", ".zip", ".tar", ".gz",
            ".min.js", ".min.css", ".map", ".lockb", ".png", ".jpg",
            ".jpeg", ".gif", ".ico", ".pdf", ".woff", ".woff2",
        }
        return file_path.suffix.lower() in binary_extensions


class ParallelScanner:
    """Scans directories in parallel for faster discovery."""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize the parallel scanner.
        
        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
    
    def scan_directories(
        self,
        directories: List[Path],
        progress: Optional[DiscoveryProgress] = None,
    ) -> List[Path]:
        """
        Scan multiple directories in parallel.
        
        Args:
            directories: List of directories to scan
            progress: Optional progress tracker
            
        Returns:
            List of all files found
        """
        all_files: List[Path] = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._scan_directory, dir_path): dir_path
                for dir_path in directories
            }
            
            for future in as_completed(futures):
                if progress and progress.is_cancelled:
                    executor.shutdown(wait=False)
                    break
                
                try:
                    files = future.result()
                    all_files.extend(files)
                    if progress:
                        progress.files_scanned += len(files)
                except Exception as e:
                    logger.warning(f"Error scanning directory: {e}")
        
        return all_files
    
    def _scan_directory(self, directory: Path) -> List[Path]:
        """
        Scan a single directory recursively.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of files found in the directory
        """
        files: List[Path] = []
        
        try:
            for root, dirs, filenames in os.walk(directory):
                # Skip problematic directories
                dirs[:] = [d for d in dirs if not self._should_skip_dir(d)]
                
                for filename in filenames:
                    file_path = Path(root) / filename
                    try:
                        if file_path.is_file():
                            files.append(file_path)
                    except (OSError, IOError):
                        pass
        except (OSError, IOError) as e:
            logger.warning(f"Error scanning {directory}: {e}")
        
        return files
    
    def _should_skip_dir(self, dir_name: str) -> bool:
        """Check if a directory should be skipped."""
        skip_names = {
            "__pycache__", ".git", "node_modules", "venv", ".venv",
            "build", "dist", ".tox", ".nox", "target", "out",
            ".idea", ".vscode", ".vs",
        }
        return dir_name in skip_names


class ScalableDiscovery:
    """
    Scalable discovery for large repositories (100k+ files).
    
    This class provides efficient discovery for large repositories using:
    - Heuristic sampling for repositories with many files
    - Intelligent file ranking to prioritize relevant files
    - Parallel scanning for faster directory traversal
    - Progress tracking and cancellation support
    
    Requirements: 24.1-24.8 (enhanced for v02.1)
    """
    
    # Default configuration
    DEFAULT_MAX_DISCOVERY_FILES = 1000
    DEFAULT_MAX_FILE_SIZE_MB = 10
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_PARALLEL_WORKERS = 4
    DEFAULT_SAMPLE_THRESHOLD = 10000
    
    def __init__(
        self,
        max_discovery_files: int = None,
        max_file_size_mb: int = None,
        timeout_seconds: int = None,
        parallel_workers: int = None,
        sample_threshold: int = None,
        cache_dir: Path = None,
    ):
        """
        Initialize the ScalableDiscovery.
        
        Args:
            max_discovery_files: Maximum files to analyze (default: 1000)
            max_file_size_mb: Maximum file size in MB (default: 10)
            timeout_seconds: Timeout for discovery (default: 30)
            parallel_workers: Number of parallel workers (default: 4)
            sample_threshold: Threshold for enabling sampling (default: 10000)
            cache_dir: Directory for caching discovery results
        """
        self.max_discovery_files = max_discovery_files or self.DEFAULT_MAX_DISCOVERY_FILES
        self.max_file_size_mb = max_file_size_mb or self.DEFAULT_MAX_FILE_SIZE_MB
        self.timeout_seconds = timeout_seconds or self.DEFAULT_TIMEOUT_SECONDS
        self.parallel_workers = parallel_workers or self.DEFAULT_PARALLEL_WORKERS
        self.sample_threshold = sample_threshold or self.DEFAULT_SAMPLE_THRESHOLD
        self.cache_dir = cache_dir or Path(".kiro/.cache")
        
        self._sampler = HeuristicSampler()
        self._ranker = IntelligentFileRanker()
        self._scanner = ParallelScanner(max_workers=self.parallel_workers)
        self._progress: Optional[DiscoveryProgress] = None
    
    def heuristic_sampling(
        self,
        project_path: Path,
        target_count: Optional[int] = None,
    ) -> Tuple[List[Path], Dict[str, any]]:
        """
        Use heuristic sampling for large repositories.
        
        For repositories with more than 10,000 files, this method uses
        stratified sampling to identify relevant documentation while
        avoiding scanning every single file.
        
        Args:
            project_path: Root path of the project
            target_count: Target number of files to sample
            
        Returns:
            Tuple of (sampled files, sampling metadata)
        """
        target_count = target_count or self.max_discovery_files
        
        # First, get an estimate of total files
        total_files = self._estimate_file_count(project_path)
        
        if total_files <= self.sample_threshold:
            # No sampling needed for smaller repositories
            return [], {"sampled": False, "reason": "below_threshold", "total_files": total_files}
        
        # Collect all files using parallel scanning
        all_files = self._collect_all_files(project_path)
        
        if len(all_files) <= target_count:
            # No sampling needed
            return all_files, {"sampled": False, "reason": "within_limit", "total_files": len(all_files)}
        
        # Calculate sample size
        sample_size = self._sampler.calculate_sample_size(len(all_files))
        sample_size = min(sample_size, target_count)
        
        # Perform stratified sampling
        sampled = self._sampler.sample_files(all_files, sample_size)
        
        metadata = {
            "sampled": True,
            "total_files": total_files,
            "sampled_count": len(sampled),
            "sample_ratio": len(sampled) / len(all_files) if all_files else 0,
            "reason": "large_repository",
        }
        
        logger.info(
            f"Heuristic sampling: {len(sampled)} files sampled from {total_files} total "
            f"(ratio: {metadata['sample_ratio']:.2%})"
        )
        
        return sampled, metadata
    
    def intelligent_file_ranking(
        self,
        file_paths: List[Path],
        max_files: Optional[int] = None,
    ) -> Tuple[List[Path], Dict[str, any]]:
        """
        Rank and prioritize files by relevance.
        
        This method assigns relevance scores to files and returns them
        sorted by priority, ensuring the most relevant files are included
        when limits are applied.
        
        Args:
            file_paths: List of file paths to rank
            max_files: Maximum files to return (uses config default if None)
            
        Returns:
            Tuple of (ranked files, ranking metadata)
        """
        max_files = max_files or self.max_discovery_files
        
        # Rank all files
        candidates = self._ranker.rank_files(file_paths)
        
        # Filter and limit
        included: List[Path] = []
        skipped: List[Dict] = []
        
        for candidate in candidates:
            if len(included) >= max_files:
                # Add to skipped list
                skipped.append({
                    "path": str(candidate.path),
                    "reason": "limit_reached",
                    "relevance_score": candidate.relevance_score,
                })
                continue
            
            # Check file size limit
            file_size_mb = candidate.file_size_bytes / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                skipped.append({
                    "path": str(candidate.path),
                    "reason": "file_too_large",
                    "file_size_mb": file_size_mb,
                    "max_size_mb": self.max_file_size_mb,
                })
                candidate.skip_reason = "file_too_large"
                continue
            
            # Check if binary
            if candidate.is_binary:
                skipped.append({
                    "path": str(candidate.path),
                    "reason": "binary_file",
                })
                candidate.skip_reason = "binary_file"
                continue
            
            # Include the file
            included.append(candidate.path)
        
        metadata = {
            "total_input": len(file_paths),
            "total_included": len(included),
            "total_skipped": len(skipped),
            "skip_reasons": self._summarize_skip_reasons(skipped),
            "max_files": max_files,
            "max_file_size_mb": self.max_file_size_mb,
        }
        
        return included, metadata
    
    def parallel_scanning(
        self,
        project_path: Path,
        progress: Optional[DiscoveryProgress] = None,
    ) -> Tuple[List[Path], Dict[str, any]]:
        """
        Scan directories in parallel for faster discovery.
        
        This method uses multiple threads to scan directories concurrently,
        significantly reducing discovery time for large repositories.
        
        Args:
            project_path: Root path of the project
            progress: Optional progress tracker
            
        Returns:
            Tuple of (discovered files, scanning metadata)
        """
        self._progress = progress or DiscoveryProgress()
        
        # Identify directories to scan
        directories = self._get_scan_directories(project_path)
        
        if not directories:
            return [], {"error": "no_directories_to_scan"}
        
        # Set estimated total for progress tracking
        self._progress.estimated_total = self._estimate_file_count(project_path)
        
        # Scan in parallel
        start_time = time.time()
        all_files = self._scanner.scan_directories(directories, self._progress)
        elapsed = time.time() - start_time
        
        metadata = {
            "directories_scanned": len(directories),
            "files_found": len(all_files),
            "elapsed_seconds": elapsed,
            "files_per_second": len(all_files) / elapsed if elapsed > 0 else 0,
            "was_cancelled": self._progress.is_cancelled,
        }
        
        return all_files, metadata
    
    def discover_all(
        self,
        project_path: Path,
        show_progress: bool = True,
    ) -> Tuple[List[Path], Dict[str, any]]:
        """
        Run complete discovery with all scalability features.
        
        This method orchestrates all discovery methods:
        1. Check if sampling is needed for large repositories
        2. Scan directories in parallel
        3. Rank files by relevance
        4. Apply limits and filters
        5. Return results with metadata
        
        Args:
            project_path: Root path of the project
            show_progress: Whether to display progress
            
        Returns:
            Tuple of (discovered files, discovery metadata)
        """
        progress = DiscoveryProgress()
        
        # Estimate repository size
        total_files = self._estimate_file_count(project_path)
        
        if show_progress:
            print(f"Discovering project files (estimated {total_files} files)...")
        
        # Check if we need sampling
        use_sampling = self._sampler.should_sample(total_files, self.sample_threshold)
        
        if use_sampling:
            # Use heuristic sampling for large repositories
            if show_progress:
                print(f"Large repository detected ({total_files} files). Using heuristic sampling...")
            
            sampled_files, sampling_metadata = self.heuristic_sampling(
                project_path, self.max_discovery_files
            )
            
            # Rank and filter the sampled files
            ranked_files, ranking_metadata = self.intelligent_file_ranking(sampled_files)
            
            metadata = {
                "method": "sampling",
                "total_files_estimated": total_files,
                "sampling_metadata": sampling_metadata,
                "ranking_metadata": ranking_metadata,
                "max_files": self.max_discovery_files,
                "max_file_size_mb": self.max_file_size_mb,
            }
            
            if show_progress:
                print(f"Discovery complete: {len(ranked_files)} files selected from {total_files} estimated")
            
            return ranked_files, metadata
        
        # For smaller repositories, use parallel scanning
        if show_progress:
            print("Scanning directories...")
        
        all_files, scan_metadata = self.parallel_scanning(project_path, progress)
        
        # Rank and filter
        ranked_files, ranking_metadata = self.intelligent_file_ranking(all_files)
        
        metadata = {
            "method": "full_scan",
            "total_files_found": len(all_files),
            "scan_metadata": scan_metadata,
            "ranking_metadata": ranking_metadata,
            "max_files": self.max_discovery_files,
            "max_file_size_mb": self.max_file_size_mb,
        }
        
        if show_progress:
            print(f"Discovery complete: {len(ranked_files)} files found")
        
        return ranked_files, metadata
    
    def _estimate_file_count(self, project_path: Path) -> int:
        """
        Estimate the total number of files in a repository.
        
        This is a quick estimation to determine if sampling is needed.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            Estimated file count
        """
        try:
            # Count files in common source directories
            count = 0
            for root, dirs, filenames in os.walk(project_path):
                # Skip problematic directories
                dirs[:] = [d for d in dirs if not self._sampler.is_skip_dir(Path(d))]
                count += len(filenames)
                
                # Early exit if we've counted enough
                if count > self.sample_threshold * 2:
                    return count
            return count
        except (OSError, IOError):
            return 0
    
    def _collect_all_files(self, project_path: Path) -> List[Path]:
        """
        Collect all files in a repository.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            List of all file paths
        """
        files: List[Path] = []
        
        try:
            for root, dirs, filenames in os.walk(project_path):
                # Skip problematic directories
                dirs[:] = [d for d in dirs if not self._sampler.is_skip_dir(Path(d))]
                
                for filename in filenames:
                    file_path = Path(root) / filename
                    try:
                        if file_path.is_file():
                            files.append(file_path)
                    except (OSError, IOError):
                        pass
        except (OSError, IOError) as e:
            logger.warning(f"Error collecting files: {e}")
        
        return files
    
    def _get_scan_directories(self, project_path: Path) -> List[Path]:
        """
        Get directories to scan for discovery.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            List of directories to scan
        """
        directories = []
        
        # Add project root
        if project_path.exists() and project_path.is_dir():
            directories.append(project_path)
        
        # Add common documentation directories
        for doc_dir in ["docs", "documentation", "design", ".github"]:
            doc_path = project_path / doc_dir
            if doc_path.exists() and doc_path.is_dir():
                directories.append(doc_path)
        
        return directories
    
    def _summarize_skip_reasons(self, skipped: List[Dict]) -> Dict[str, int]:
        """Summarize skip reasons by count."""
        summary: Dict[str, int] = {}
        for item in skipped:
            reason = item.get("reason", "unknown")
            summary[reason] = summary.get(reason, 0) + 1
        return summary
    
    def get_cache_key(self, project_path: Path) -> str:
        """
        Generate a cache key for discovery results.
        
        Args:
            project_path: Root path of the project
            
        Returns:
            Cache key string
        """
        import hashlib
        path_str = str(project_path.resolve())
        config_str = f"{self.max_discovery_files}_{self.max_file_size_mb}"
        key = f"{path_str}_{config_str}"
        return hashlib.md5(key.encode()).hexdigest()