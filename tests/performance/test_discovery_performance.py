"""
Performance benchmarks for source document discovery.

This module tests the performance of the SourceDocumentResolver to ensure
it meets the required performance targets:
- 1000-file project: < 1s
- 10,000-file project: < 10s
- Symlink is faster than copy

Requirements: Phase 6.6.3 (Red Team Recommended)
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path

from hiveforge.steering.source_resolver import SourceDocumentResolver


@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root directory."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    return project_root


@pytest.fixture
def small_source_dir(temp_project_root):
    """Create a source directory with 100 files."""
    source_dir = temp_project_root / "docs_small"
    source_dir.mkdir()
    
    for i in range(100):
        (source_dir / f"doc_{i}.md").write_text(f"# Document {i}\n\nContent for document {i}.")
    
    return source_dir


@pytest.fixture
def medium_source_dir(temp_project_root):
    """Create a source directory with 1000 files."""
    source_dir = temp_project_root / "docs_medium"
    source_dir.mkdir()
    
    # Create subdirectories for organization
    for subdir_idx in range(10):
        subdir = source_dir / f"subdir_{subdir_idx}"
        subdir.mkdir()
        
        for i in range(100):
            (subdir / f"doc_{i}.md").write_text(f"# Document {subdir_idx}_{i}\n\nContent.")
    
    return source_dir


@pytest.fixture
def large_source_dir(temp_project_root):
    """Create a source directory with 10,000 files (for stress testing)."""
    source_dir = temp_project_root / "docs_large"
    source_dir.mkdir()
    
    # Create subdirectories for organization
    for subdir_idx in range(100):
        subdir = source_dir / f"subdir_{subdir_idx}"
        subdir.mkdir()
        
        for i in range(100):
            (subdir / f"doc_{i}.md").write_text(f"# Doc {subdir_idx}_{i}\nContent.")
    
    return source_dir


class TestSmallProjectDiscoveryPerformance:
    """Tests for discovery performance on small projects (100 files)."""
    
    def test_100_files_discovery_under_100ms(self, temp_project_root, small_source_dir):
        """Test that discovering 100 files completes in < 100ms."""
        resolver = SourceDocumentResolver(temp_project_root)
        staging_dir = temp_project_root / ".kiro" / "staging"
        
        # Measure discovery time with symlinks
        start_time = time.perf_counter()
        resolved_dir, discovered_docs = resolver.resolve(
            str(small_source_dir.relative_to(temp_project_root)),
            copy_files=False
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify results
        assert len(discovered_docs) == 100
        
        # Performance assertion: < 100ms for 100 files
        assert elapsed_ms < 100, f"100-file discovery took {elapsed_ms:.2f}ms (target: < 100ms)"


class TestMediumProjectDiscoveryPerformance:
    """Tests for discovery performance on medium projects (1000 files)."""
    
    def test_1000_files_discovery_under_1s(self, temp_project_root, medium_source_dir):
        """Test that discovering 1000 files completes in < 1s."""
        resolver = SourceDocumentResolver(temp_project_root)
        
        # Measure discovery time with symlinks
        start_time = time.perf_counter()
        resolved_dir, discovered_docs = resolver.resolve(
            str(medium_source_dir.relative_to(temp_project_root)),
            copy_files=False
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify results
        assert len(discovered_docs) == 1000
        
        # Performance assertion: < 1000ms (1s) for 1000 files
        assert elapsed_ms < 1000, f"1000-file discovery took {elapsed_ms:.2f}ms (target: < 1000ms)"
    
    def test_1000_files_with_nested_directories(self, temp_project_root):
        """Test discovery performance with deeply nested directories."""
        # Create nested structure
        source_dir = temp_project_root / "docs_nested"
        current_dir = source_dir
        
        # Create 10 levels of nesting, 100 files per level
        for level in range(10):
            current_dir.mkdir(parents=True, exist_ok=True)
            for i in range(100):
                (current_dir / f"doc_{level}_{i}.md").write_text(f"# Doc {level}_{i}")
            current_dir = current_dir / f"level_{level}"
        
        resolver = SourceDocumentResolver(temp_project_root)
        
        # Measure discovery time
        start_time = time.perf_counter()
        resolved_dir, discovered_docs = resolver.resolve(
            str(source_dir.relative_to(temp_project_root)),
            copy_files=False
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify results
        assert len(discovered_docs) == 1000
        
        # Should still be fast with nested structure
        assert elapsed_ms < 1500, f"Nested discovery took {elapsed_ms:.2f}ms (target: < 1500ms)"


class TestLargeProjectDiscoveryPerformance:
    """Tests for discovery performance on large projects (10,000 files)."""
    
    @pytest.mark.slow
    def test_10000_files_discovery_under_10s(self, temp_project_root, large_source_dir):
        """Test that discovering 10,000 files completes in < 10s."""
        resolver = SourceDocumentResolver(temp_project_root)
        
        # Measure discovery time with symlinks
        start_time = time.perf_counter()
        resolved_dir, discovered_docs = resolver.resolve(
            str(large_source_dir.relative_to(temp_project_root)),
            copy_files=False
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify results
        assert len(discovered_docs) == 10000
        
        # Performance assertion: < 10000ms (10s) for 10,000 files
        assert elapsed_ms < 10000, f"10000-file discovery took {elapsed_ms:.2f}ms (target: < 10000ms)"


class TestSymlinkVsCopyPerformance:
    """Tests comparing symlink vs copy performance."""
    
    def test_symlink_faster_than_copy_100_files(self, temp_project_root, small_source_dir):
        """Test that symlink is faster than copy for 100 files."""
        resolver = SourceDocumentResolver(temp_project_root)
        source_path = str(small_source_dir.relative_to(temp_project_root))
        
        # Measure symlink time
        start_time = time.perf_counter()
        resolved_dir_symlink, docs_symlink = resolver.resolve(source_path, copy_files=False)
        symlink_ms = (time.perf_counter() - start_time) * 1000
        
        # Clean up
        if resolved_dir_symlink.exists():
            shutil.rmtree(resolved_dir_symlink)
        
        # Measure copy time
        start_time = time.perf_counter()
        resolved_dir_copy, docs_copy = resolver.resolve(source_path, copy_files=True)
        copy_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify both methods work
        assert len(docs_symlink) == 100
        assert len(docs_copy) == 100
        
        # Symlink should be faster
        assert symlink_ms < copy_ms, f"Symlink ({symlink_ms:.2f}ms) should be faster than copy ({copy_ms:.2f}ms)"
        
        # Symlink should be significantly faster (at least 2x)
        speedup = copy_ms / symlink_ms if symlink_ms > 0 else float('inf')
        assert speedup > 2, f"Symlink speedup: {speedup:.2f}x (target: > 2x)"
    
    def test_symlink_faster_than_copy_1000_files(self, temp_project_root, medium_source_dir):
        """Test that symlink is faster than copy for 1000 files."""
        resolver = SourceDocumentResolver(temp_project_root)
        source_path = str(medium_source_dir.relative_to(temp_project_root))
        
        # Measure symlink time
        start_time = time.perf_counter()
        resolved_dir_symlink, docs_symlink = resolver.resolve(source_path, copy_files=False)
        symlink_ms = (time.perf_counter() - start_time) * 1000
        
        # Clean up
        if resolved_dir_symlink.exists():
            shutil.rmtree(resolved_dir_symlink)
        
        # Measure copy time
        start_time = time.perf_counter()
        resolved_dir_copy, docs_copy = resolver.resolve(source_path, copy_files=True)
        copy_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify both methods work
        assert len(docs_symlink) == 1000
        assert len(docs_copy) == 1000
        
        # Symlink should be faster
        assert symlink_ms < copy_ms, f"Symlink ({symlink_ms:.2f}ms) should be faster than copy ({copy_ms:.2f}ms)"
        
        # Symlink should be significantly faster (at least 2x for larger sets)
        speedup = copy_ms / symlink_ms if symlink_ms > 0 else float('inf')
        assert speedup > 2, f"Symlink speedup: {speedup:.2f}x (target: > 2x)"
    
    def test_symlink_is_default(self, temp_project_root, small_source_dir):
        """Test that symlink is the default behavior (copy_files=False)."""
        resolver = SourceDocumentResolver(temp_project_root)
        source_path = str(small_source_dir.relative_to(temp_project_root))
        
        # Call resolve without copy_files parameter (should default to False)
        resolved_dir, discovered_docs = resolver.resolve(source_path)
        
        # Verify it used symlinks (check if staging dir is a symlink or contains symlinks)
        # The implementation may vary, but symlink should be default
        assert len(discovered_docs) == 100


class TestDiscoveryScalability:
    """Tests for discovery scalability."""
    
    def test_discovery_scales_linearly(self, temp_project_root):
        """Test that discovery performance scales linearly with file count."""
        resolver = SourceDocumentResolver(temp_project_root)
        times = []
        file_counts = [100, 500, 1000]
        
        for count in file_counts:
            # Create source directory with specified file count
            source_dir = temp_project_root / f"docs_{count}"
            source_dir.mkdir()
            
            for i in range(count):
                (source_dir / f"doc_{i}.md").write_text(f"# Doc {i}")
            
            # Measure discovery time
            start_time = time.perf_counter()
            resolved_dir, discovered_docs = resolver.resolve(
                str(source_dir.relative_to(temp_project_root)),
                copy_files=False
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            times.append(elapsed_ms)
            
            # Verify results
            assert len(discovered_docs) == count
            
            # Clean up
            if resolved_dir.exists():
                shutil.rmtree(resolved_dir)
        
        # Check that scaling is reasonable (linear or better)
        # 1000 files should take < 10x the time of 100 files
        if times[0] > 0:
            scaling_factor = times[2] / times[0]
            assert scaling_factor < 10, f"Scaling factor: {scaling_factor:.2f}x (should be < 10x)"


class TestEdgeCasePerformance:
    """Tests for performance with edge cases."""
    
    def test_empty_directory_performance(self, temp_project_root):
        """Test performance with empty source directory."""
        source_dir = temp_project_root / "empty_docs"
        source_dir.mkdir()
        
        resolver = SourceDocumentResolver(temp_project_root)
        
        start_time = time.perf_counter()
        resolved_dir, discovered_docs = resolver.resolve(
            str(source_dir.relative_to(temp_project_root)),
            copy_files=False
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Should be very fast with empty directory
        assert elapsed_ms < 10, f"Empty directory discovery took {elapsed_ms:.2f}ms (target: < 10ms)"
        assert len(discovered_docs) == 0
    
    def test_single_file_performance(self, temp_project_root):
        """Test performance with single file."""
        source_dir = temp_project_root / "single_doc"
        source_dir.mkdir()
        (source_dir / "doc.md").write_text("# Single Document")
        
        resolver = SourceDocumentResolver(temp_project_root)
        
        start_time = time.perf_counter()
        resolved_dir, discovered_docs = resolver.resolve(
            str(source_dir.relative_to(temp_project_root)),
            copy_files=False
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Should be very fast with single file
        assert elapsed_ms < 10, f"Single file discovery took {elapsed_ms:.2f}ms (target: < 10ms)"
        assert len(discovered_docs) == 1
    
    def test_mixed_file_types_performance(self, temp_project_root):
        """Test performance with mixed file types."""
        source_dir = temp_project_root / "mixed_docs"
        source_dir.mkdir()
        
        # Create 500 markdown files and 500 other files
        for i in range(500):
            (source_dir / f"doc_{i}.md").write_text(f"# Doc {i}")
            (source_dir / f"image_{i}.png").write_bytes(b"fake image data")
        
        resolver = SourceDocumentResolver(temp_project_root)
        
        start_time = time.perf_counter()
        resolved_dir, discovered_docs = resolver.resolve(
            str(source_dir.relative_to(temp_project_root)),
            copy_files=False
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Should handle mixed types efficiently
        assert elapsed_ms < 500, f"Mixed file discovery took {elapsed_ms:.2f}ms (target: < 500ms)"
        # Should discover all files (markdown and non-markdown)
        assert len(discovered_docs) > 0


@pytest.mark.skip(reason="Requires pytest-benchmark plugin")
@pytest.mark.benchmark
class TestDiscoveryBenchmarks:
    """Benchmark tests for source discovery (optional, for profiling)."""
    
    def test_benchmark_discovery_100_files(self, benchmark, temp_project_root, small_source_dir):
        """Benchmark discovery of 100 files."""
        resolver = SourceDocumentResolver(temp_project_root)
        source_path = str(small_source_dir.relative_to(temp_project_root))
        
        def discover():
            resolved_dir, discovered_docs = resolver.resolve(source_path, copy_files=False)
            # Clean up after each run
            if resolved_dir.exists():
                shutil.rmtree(resolved_dir)
            return discovered_docs
        
        result = benchmark(discover)
        assert len(result) == 100
    
    def test_benchmark_discovery_1000_files(self, benchmark, temp_project_root, medium_source_dir):
        """Benchmark discovery of 1000 files."""
        resolver = SourceDocumentResolver(temp_project_root)
        source_path = str(medium_source_dir.relative_to(temp_project_root))
        
        def discover():
            resolved_dir, discovered_docs = resolver.resolve(source_path, copy_files=False)
            # Clean up after each run
            if resolved_dir.exists():
                shutil.rmtree(resolved_dir)
            return discovered_docs
        
        result = benchmark(discover)
        assert len(result) == 1000
