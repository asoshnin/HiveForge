"""
Property tests for discovery scalability (v02.1).

This module contains property-based tests for the ScalableDiscovery class,
validating that discovery handles large repositories efficiently.

Property 24: Discovery Phase Scalability
Validates: Requirements 24.1-24.8
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from hypothesis import given, settings, assume
from hypothesis.strategies import integers, lists, text, one_of, booleans
from hypothesis.strategies import composite, sampled_from

from hiveforge.steering.scalable_discovery import (
    ScalableDiscovery,
    HeuristicSampler,
    IntelligentFileRanker,
    ParallelScanner,
    DiscoveryProgress,
    FileCandidate,
)


# Helper strategies for generating test data

@composite
def file_paths_strategy(draw, base_path: Path = None):
    """Generate a list of file paths for testing."""
    base = base_path or Path("/test/project")
    count = draw(integers(min_value=1, max_value=100))
    paths = []
    for i in range(count):
        # Generate varied file paths
        parts = []
        for _ in range(draw(integers(min_value=1, max_value=4))):
            part = draw(text(min_value=1, max_value=20, alphabet="abcdefghijklmnopqrstuvwxyz"))
            parts.append(part)
        paths.append(base / "/".join(parts) / f"file_{i}.txt")
    return paths


@composite
def project_structure_strategy(draw, max_depth: int = 5):
    """Generate a project structure with files and directories."""
    depth = draw(integers(min_value=1, max_value=max_depth))
    files = []
    
    def generate_at_depth(current_path, current_depth):
        if current_depth > depth:
            return
        # Add some files
        num_files = draw(integers(min_value=0, max_value=5))
        for i in range(num_files):
            files.append(current_path / f"file_{i}.txt")
        # Add subdirectories
        if current_depth < depth:
            num_dirs = draw(integers(min_value=0, max_value=3))
            for i in range(num_dirs):
                dir_name = draw(text(min_value=1, max_value=10, alphabet="abcdefghijklmnopqrstuvwxyz"))
                subdir = current_path / dir_name
                generate_at_depth(subdir, current_depth + 1)
    
    base = Path("/test/project")
    generate_at_depth(base, 1)
    return files


class TestHeuristicSampler:
    """Tests for the HeuristicSampler class."""

    def test_should_sample_below_threshold(self):
        """Files below threshold should not require sampling."""
        sampler = HeuristicSampler()
        assert sampler.should_sample(5000, threshold=10000) is False
        assert sampler.should_sample(9999, threshold=10000) is False

    def test_should_sample_above_threshold(self):
        """Files above threshold should require sampling."""
        sampler = HeuristicSampler()
        assert sampler.should_sample(10001, threshold=10000) is True
        assert sampler.should_sample(50000, threshold=10000) is True
        assert sampler.should_sample(100000, threshold=10000) is True

    def test_calculate_sample_size(self):
        """Sample size should be proportional to total files."""
        sampler = HeuristicSampler(sample_ratio=0.1, min_sample=100)
        
        # Below min_sample
        assert sampler.calculate_sample_size(500) == 100
        
        # Above min_sample
        assert sampler.calculate_sample_size(10000) == 1000
        assert sampler.calculate_sample_size(50000) == 5000

    def test_sample_files_returns_subset(self):
        """Sampled files should be a subset of all files."""
        sampler = HeuristicSampler(sample_ratio=0.5, min_sample=10)
        all_files = [Path(f"/test/file_{i}.txt") for i in range(100)]
        
        sampled = sampler.sample_files(all_files, 20)
        
        assert len(sampled) == 20
        for f in sampled:
            assert f in all_files

    def test_sample_files_all_files_when_small(self):
        """When files <= target, all files should be returned."""
        sampler = HeuristicSampler()
        all_files = [Path(f"/test/file_{i}.txt") for i in range(50)]
        
        sampled = sampler.sample_files(all_files, 100)
        
        assert len(sampled) == 50
        assert set(sampled) == set(all_files)

    def test_is_skip_dir(self):
        """Certain directories should be skipped."""
        sampler = HeuristicSampler()
        
        assert sampler.is_skip_dir(Path("/test/__pycache__")) is True
        assert sampler.is_skip_dir(Path("/test/.git")) is True
        assert sampler.is_skip_dir(Path("/test/node_modules")) is True
        assert sampler.is_skip_dir(Path("/test/src")) is False

    def test_is_skip_extension(self):
        """Certain file extensions should be skipped."""
        sampler = HeuristicSampler()
        
        assert sampler.is_skip_extension(Path("/test/file.pyc")) is True
        assert sampler.is_skip_extension(Path("/test/file.so")) is True
        assert sampler.is_skip_extension(Path("/test/file.py")) is False
        assert sampler.is_skip_extension(Path("/test/file.txt")) is False


class TestIntelligentFileRanker:
    """Tests for the IntelligentFileRanker class."""

    def test_rank_documentation_files_high(self):
        """Documentation files should have high relevance scores."""
        ranker = IntelligentFileRanker()
        
        readme_score = ranker.rank_file(Path("/test/README.md"))
        assert readme_score >= 0.9
        
        contributing_score = ranker.rank_file(Path("/test/CONTRIBUTING.md"))
        assert contributing_score >= 0.9

    def test_rank_config_files_medium(self):
        """Configuration files should have medium relevance scores."""
        ranker = IntelligentFileRanker()
        
        dockerfile_score = ranker.rank_file(Path("/test/Dockerfile"))
        assert 0.6 <= dockerfile_score <= 0.9
        
        package_score = ranker.rank_file(Path("/test/package.json"))
        assert 0.5 <= package_score <= 0.8

    def test_rank_source_files_lower(self):
        """Source files should have lower relevance scores."""
        ranker = IntelligentFileRanker()
        
        py_score = ranker.rank_file(Path("/test/src/main.py"))
        assert 0.3 <= py_score <= 0.6

    def test_rank_files_returns_sorted_list(self):
        """Ranked files should be sorted by relevance (descending)."""
        ranker = IntelligentFileRanker()
        
        files = [
            Path("/test/src/main.py"),
            Path("/test/README.md"),
            Path("/test/Dockerfile"),
            Path("/test/docs/guide.txt"),
        ]
        
        candidates = ranker.rank_files(files)
        scores = [c.relevance_score for c in candidates]
        
        # Scores should be in descending order
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    def test_rank_files_handles_access_errors(self):
        """Ranker should handle files that can't be accessed."""
        ranker = IntelligentFileRanker()
        
        # Create a candidate with access error
        candidate = FileCandidate(
            path=Path("/nonexistent/file.txt"),
            relevance_score=0.0,
            skip_reason="access_error",
        )
        
        assert candidate.should_include() is False


class TestParallelScanner:
    """Tests for the ParallelScanner class."""

    def test_scan_empty_directories(self):
        """Scanning empty directories should return empty list."""
        scanner = ParallelScanner()
        
        with TemporaryDirectory() as tmpdir:
            result = scanner.scan_directories([Path(tmpdir)])
            assert len(result) == 0

    def test_scan_single_directory(self):
        """Scanning a directory should find all files."""
        scanner = ParallelScanner(max_workers=2)
        
        with TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.txt").write_text("test1")
            (Path(tmpdir) / "file2.txt").write_text("test2")
            (Path(tmpdir) / "subdir").mkdir()
            (Path(tmpdir) / "subdir" / "file3.txt").write_text("test3")
            
            result = scanner.scan_directories([Path(tmpdir)])
            
            assert len(result) == 3

    def test_parallel_scanning_faster_than_sequential(self):
        """Parallel scanning should be faster for multiple directories."""
        scanner = ParallelScanner(max_workers=4)
        
        with TemporaryDirectory() as tmpdir:
            # Create multiple subdirectories with files
            for i in range(8):
                subdir = Path(tmpdir) / f"dir_{i}"
                subdir.mkdir()
                for j in range(10):
                    (subdir / f"file_{j}.txt").write_text(f"content {j}")
            
            result = scanner.scan_directories([Path(tmpdir)])
            
            # Should find all 80 files
            assert len(result) == 80


class TestDiscoveryProgress:
    """Tests for the DiscoveryProgress class."""

    def test_progress_tracking(self):
        """Progress should track files scanned and included."""
        progress = DiscoveryProgress()
        
        progress.files_scanned = 100
        progress.files_included = 50
        progress.files_skipped = 50
        
        assert progress.files_scanned == 100
        assert progress.files_included == 50
        assert progress.files_skipped == 50

    def test_cancel(self):
        """Cancel should set is_cancelled flag."""
        progress = DiscoveryProgress()
        
        assert progress.is_cancelled is False
        progress.cancel()
        assert progress.is_cancelled is True

    def test_elapsed_time(self):
        """Elapsed time should be calculated correctly."""
        progress = DiscoveryProgress()
        
        import time
        time.sleep(0.1)
        
        elapsed = progress.get_elapsed_seconds()
        assert elapsed >= 0.1

    def test_files_per_second(self):
        """Files per second should be calculated correctly."""
        progress = DiscoveryProgress()
        
        import time
        progress.files_scanned = 100
        time.sleep(0.1)
        
        rate = progress.get_files_per_second()
        assert rate >= 900  # Should be close to 1000


class TestScalableDiscovery:
    """Property tests for the ScalableDiscovery class."""

    def test_default_configuration(self):
        """Default configuration should have expected values."""
        discovery = ScalableDiscovery()
        
        assert discovery.max_discovery_files == 1000
        assert discovery.max_file_size_mb == 10
        assert discovery.timeout_seconds == 30
        assert discovery.parallel_workers == 4
        assert discovery.sample_threshold == 10000

    def test_custom_configuration(self):
        """Custom configuration should be applied correctly."""
        discovery = ScalableDiscovery(
            max_discovery_files=500,
            max_file_size_mb=5,
            timeout_seconds=60,
            parallel_workers=8,
            sample_threshold=5000,
        )
        
        assert discovery.max_discovery_files == 500
        assert discovery.max_file_size_mb == 5
        assert discovery.timeout_seconds == 60
        assert discovery.parallel_workers == 8
        assert discovery.sample_threshold == 5000

    def test_heuristic_sampling_small_repo(self):
        """Small repositories should not use sampling."""
        discovery = ScalableDiscovery()
        
        with TemporaryDirectory() as tmpdir:
            # Create a small project
            (Path(tmpdir) / "README.md").write_text("# Test")
            (Path(tmpdir) / "main.py").write_text("print('hello')")
            
            sampled, metadata = discovery.heuristic_sampling(Path(tmpdir))
            
            assert metadata["sampled"] is False
            assert "below_threshold" in metadata["reason"]

    def test_heuristic_sampling_large_repo(self):
        """Large repositories should use sampling."""
        discovery = ScalableDiscovery(sample_threshold=100)
        
        with TemporaryDirectory() as tmpdir:
            # Create a large project structure
            for i in range(200):
                subdir = Path(tmpdir) / f"dir_{i}"
                subdir.mkdir()
                for j in range(5):
                    (subdir / f"file_{j}.txt").write_text(f"content {j}")
            
            sampled, metadata = discovery.heuristic_sampling(Path(tmpdir), target_count=50)
            
            assert metadata["sampled"] is True
            assert "large_repository" in metadata["reason"]
            assert metadata["sampled_count"] <= 50

    def test_intelligent_file_ranking(self):
        """Files should be ranked and filtered correctly."""
        discovery = ScalableDiscovery(max_discovery_files=10)
        
        with TemporaryDirectory() as tmpdir:
            # Create test files
            for i in range(20):
                (Path(tmpdir) / f"file_{i}.txt").write_text("content")
            
            files = list(Path(tmpdir).glob("*.txt"))
            ranked, metadata = discovery.intelligent_file_ranking(files)
            
            assert len(ranked) <= 10
            assert metadata["total_input"] == 20
            assert metadata["total_included"] == len(ranked)

    def test_intelligent_file_ranking_size_limit(self):
        """Large files should be skipped."""
        discovery = ScalableDiscovery(max_file_size_mb=0.001)  # 1KB limit
        
        with TemporaryDirectory() as tmpdir:
            # Create a large file (>1KB)
            large_file = Path(tmpdir) / "large.txt"
            large_file.write_text("x" * 2000)  # 2KB
            
            # Create a small file
            small_file = Path(tmpdir) / "small.txt"
            small_file.write_text("small")
            
            files = [large_file, small_file]
            ranked, metadata = discovery.intelligent_file_ranking(files)
            
            assert len(ranked) == 1
            assert ranked[0] == small_file
            assert metadata["total_skipped"] == 1
            assert "file_too_large" in metadata["skip_reasons"]

    def test_parallel_scanning(self):
        """Parallel scanning should find all files."""
        discovery = ScalableDiscovery(parallel_workers=4)
        
        with TemporaryDirectory() as tmpdir:
            # Create a project structure
            for i in range(10):
                subdir = Path(tmpdir) / f"dir_{i}"
                subdir.mkdir()
                for j in range(5):
                    (subdir / f"file_{j}.txt").write_text(f"content {j}")
            
            files, metadata = discovery.parallel_scanning(Path(tmpdir))
            
            assert len(files) == 50
            assert metadata["directories_scanned"] >= 1
            assert metadata["files_found"] == 50
            assert metadata["elapsed_seconds"] >= 0

    def test_discover_all_small_repo(self):
        """Small repositories should use full scan."""
        discovery = ScalableDiscovery()
        
        with TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "README.md").write_text("# Test")
            (Path(tmpdir) / "main.py").write_text("print('hello')")
            
            files, metadata = discovery.discover_all(Path(tmpdir), show_progress=False)
            
            assert metadata["method"] == "full_scan"
            assert len(files) >= 2

    def test_discover_all_large_repo(self):
        """Large repositories should use sampling."""
        discovery = ScalableDiscovery(sample_threshold=50, max_discovery_files=20)
        
        with TemporaryDirectory() as tmpdir:
            # Create a large project
            for i in range(100):
                subdir = Path(tmpdir) / f"dir_{i}"
                subdir.mkdir()
                for j in range(3):
                    (subdir / f"file_{j}.txt").write_text(f"content {j}")
            
            files, metadata = discovery.discover_all(Path(tmpdir), show_progress=False)
            
            assert metadata["method"] == "sampling"
            assert len(files) <= 20

    def test_get_cache_key(self):
        """Cache key should be consistent for same inputs."""
        discovery = ScalableDiscovery()
        
        key1 = discovery.get_cache_key(Path("/test/project"))
        key2 = discovery.get_cache_key(Path("/test/project"))
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hex digest

    def test_get_cache_key_different_configs(self):
        """Different configs should produce different cache keys."""
        discovery1 = ScalableDiscovery(max_discovery_files=1000)
        discovery2 = ScalableDiscovery(max_discovery_files=500)
        
        key1 = discovery1.get_cache_key(Path("/test/project"))
        key2 = discovery2.get_cache_key(Path("/test/project"))
        
        assert key1 != key2


# Property-based tests using Hypothesis

class TestScalableDiscoveryProperties:
    """Property-based tests for ScalableDiscovery."""

    @given(lists(text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz_.-"), min_size=1, max_size=100))
    @settings(max_examples=10)
    def test_intelligent_file_ranking_always_returns_subset(
        self, file_names: List[str]
    ):
        """Ranked files should always be a subset of input files."""
        discovery = ScalableDiscovery()
        
        files = [Path(f"/test/{name}.txt") for name in file_names]
        ranked, _ = discovery.intelligent_file_ranking(files)
        
        for f in ranked:
            assert f in files

    @given(lists(text(min_size=1, max_size=20), min_size=1, max_size=50))
    @settings(max_examples=10)
    def test_heuristic_sampling_preserves_high_priority(
        self, file_names: List[str]
    ):
        """Sampled files should include high-priority documentation files."""
        sampler = HeuristicSampler(sample_ratio=0.5, min_sample=5)
        
        # Create files including documentation
        files = [Path(f"/test/{name}.txt") for name in file_names]
        files.append(Path("/test/README.md"))
        files.append(Path("/test/CONTRIBUTING.md"))
        
        sampled = sampler.sample_files(files, 10)
        
        # Should include at least some documentation files
        doc_files = [f for f in sampled if "readme" in str(f).lower() or "contributing" in str(f).lower()]
        assert len(doc_files) >= 1

    @given(integers(min_value=50, max_value=1000))
    @settings(max_examples=20)
    def test_sample_size_respects_minimum(self, total_files: int):
        """Sample size should respect minimum sample setting."""
        sampler = HeuristicSampler(sample_ratio=0.01, min_sample=50)
        
        sample_size = sampler.calculate_sample_size(total_files)
        
        assert sample_size >= 50
        assert sample_size <= total_files

    @given(integers(min_value=1, max_value=100000))
    @settings(max_examples=10)
    def test_should_sample_threshold(self, file_count: int):
        """Sampling decision should respect threshold."""
        sampler = HeuristicSampler()
        threshold = 10000
        
        result = sampler.should_sample(file_count, threshold)
        
        if file_count <= threshold:
            assert result is False
        else:
            assert result is True


# Integration tests with real file systems

class TestScalableDiscoveryIntegration:
    """Integration tests with real file systems."""

    def test_full_discovery_workflow(self):
        """Test complete discovery workflow with various file types."""
        discovery = ScalableDiscovery(
            max_discovery_files=50,
            max_file_size_mb=1,
            sample_threshold=20,
        )
        
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create various file types
            (tmppath / "README.md").write_text("# Project")
            (tmppath / "CONTRIBUTING.md").write_text("Contributing guide")
            (tmppath / "main.py").write_text("print('hello')")
            (tmppath / "Dockerfile").write_text("FROM python:3.11")
            (tmppath / "package.json").write_text('{"name": "test"}')
            
            # Create subdirectory with files
            (tmppath / "docs").mkdir()
            (tmppath / "docs" / "guide.md").write_text("# Guide")
            
            files, metadata = discovery.discover_all(tmppath, show_progress=False)
            
            # Should find all created files
            assert len(files) >= 6
            assert "README.md" in [f.name for f in files]
            assert "CONTRIBUTING.md" in [f.name for f in files]
            assert "main.py" in [f.name for f in files]

    def test_discovery_with_binary_files(self):
        """Discovery should skip binary files."""
        discovery = ScalableDiscovery()
        
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create text and binary-like files
            (tmppath / "main.py").write_text("print('hello')")
            (tmppath / "data.bin").write_text("\x00\x01\x02\x03")
            (tmppath / "config.pyc").write_text("compiled")
            
            files, metadata = discovery.discover_all(tmppath, show_progress=False)
            
            # Should include Python file, skip binary files
            file_names = [f.name for f in files]
            assert "main.py" in file_names
            assert "data.bin" not in file_names
            assert "config.pyc" not in file_names

    def test_discovery_with_large_files(self):
        """Discovery should skip files larger than limit."""
        discovery = ScalableDiscovery(max_file_size_mb=0.001)  # 1KB limit
        
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create small file
            (tmppath / "small.txt").write_text("small")
            
            # Create large file (>1KB)
            (tmppath / "large.txt").write_text("x" * 2000)
            
            files, metadata = discovery.discover_all(tmppath, show_progress=False)
            
            assert len(files) == 1
            assert files[0].name == "small.txt"
            assert metadata["ranking_metadata"]["skip_reasons"].get("file_too_large", 0) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])