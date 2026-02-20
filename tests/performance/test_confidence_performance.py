"""
Performance benchmarks for confidence calculation.

This module tests the performance of the ConfidenceCalculator to ensure
it meets the required performance targets:
- Per-file calculation: < 100ms
- Overall calculation: < 200ms

Note: ConfidenceCalculator is stateless and doesn't require a knowledge base.
It calculates confidence based on source tracking data.

Requirements: Phase 6.6.1 (Red Team Recommended)
"""

import pytest
import time

from hiveforge.steering.confidence import ConfidenceCalculator, ConfidenceScore


class TestPerFileConfidencePerformance:
    """Tests for per-file confidence calculation performance."""
    
    def test_per_file_calculation_under_100ms(self):
        """Test that per-file confidence calculation completes in < 100ms."""
        calculator = ConfidenceCalculator()
        
        # Sample sources with mixed types
        sources = {
            "documents": ["Section 1"],
            "code_analysis": ["Section 2"],
            "inferred": ["Section 3"],
        }
        content = "# Test File\n\n## Section 1\n\n## Section 2\n\n## Section 3"
        
        # Measure time for single file calculation
        start_time = time.perf_counter()
        score = calculator.calculate_file_confidence("test-file.md", sources, content)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify result is valid
        assert isinstance(score, ConfidenceScore)
        assert 0.0 <= score.overall <= 1.0
        
        # Performance assertion: < 100ms
        assert elapsed_ms < 100, f"Per-file calculation took {elapsed_ms:.2f}ms (target: < 100ms)"
    
    def test_per_file_calculation_average_performance(self):
        """Test average performance across multiple file calculations."""
        calculator = ConfidenceCalculator()
        
        # Create 10 different source configurations
        test_cases = []
        for i in range(10):
            sources = {
                "documents": [f"Doc Section {j}" for j in range(i % 3 + 1)],
                "code_analysis": [f"Code Section {j}" for j in range((i + 1) % 3 + 1)],
                "inferred": [f"Inferred Section {j}" for j in range((i + 2) % 3 + 1)],
            }
            content = f"# File {i}\n\nContent"
            test_cases.append((sources, content))
        
        # Measure average time
        times = []
        for i, (sources, content) in enumerate(test_cases):
            start_time = time.perf_counter()
            calculator.calculate_file_confidence(f"file_{i}.md", sources, content)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            times.append(elapsed_ms)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Average should be well under 100ms
        assert avg_time < 50, f"Average per-file calculation: {avg_time:.2f}ms (target: < 50ms avg)"
        assert max_time < 100, f"Max per-file calculation: {max_time:.2f}ms (target: < 100ms max)"


class TestOverallConfidencePerformance:
    """Tests for overall confidence calculation performance."""
    
    def test_overall_calculation_under_200ms(self):
        """Test that overall confidence calculation completes in < 200ms."""
        calculator = ConfidenceCalculator()
        
        # Create file scores for 8 steering files
        file_scores = {}
        for i in range(8):
            file_scores[f"file_{i}.md"] = ConfidenceScore(
                overall=0.7 + (i * 0.03),
                level="medium",
                sources={"documents": 0.5, "code_analysis": 0.3, "inferred": 0.2},
                inferred_sections=["Section 1"]
            )
        
        # Measure time for overall calculation
        start_time = time.perf_counter()
        overall_score = calculator.calculate_overall_confidence(file_scores)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify result is valid
        assert isinstance(overall_score, ConfidenceScore)
        assert 0.0 <= overall_score.overall <= 1.0
        
        # Performance assertion: < 200ms
        assert elapsed_ms < 200, f"Overall calculation took {elapsed_ms:.2f}ms (target: < 200ms)"
    
    def test_overall_calculation_with_large_dataset(self):
        """Test overall calculation performance with 100 files."""
        calculator = ConfidenceCalculator()
        
        # Create file scores for 100 files
        file_scores = {}
        for i in range(100):
            file_scores[f"file_{i}.md"] = ConfidenceScore(
                overall=0.5 + (i * 0.005),
                level="medium",
                sources={"documents": 0.4, "code_analysis": 0.3, "inferred": 0.3},
                inferred_sections=["Section 1", "Section 2", "Section 3"]
            )
        
        # Measure time for overall calculation
        start_time = time.perf_counter()
        overall_score = calculator.calculate_overall_confidence(file_scores)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify result is valid
        assert isinstance(overall_score, ConfidenceScore)
        
        # Performance should still be reasonable even with 100 files
        assert elapsed_ms < 500, f"Overall calculation with 100 files took {elapsed_ms:.2f}ms (target: < 500ms)"


class TestFullWorkflowPerformance:
    """Tests for full confidence calculation workflow performance."""
    
    def test_full_workflow_with_many_files(self):
        """Test full workflow performance with 100 files."""
        calculator = ConfidenceCalculator()
        
        # Simulate calculating confidence for 100 steering files
        file_sources = {}
        for i in range(100):
            file_sources[f"steering_{i}.md"] = {
                "documents": [f"Doc Section {j}" for j in range(i % 5)],
                "code_analysis": [f"Code Section {j}" for j in range((i + 1) % 5)],
                "inferred": [f"Inferred Section {j}" for j in range((i + 2) % 5)],
            }
        
        # Measure time for full workflow
        start_time = time.perf_counter()
        
        # Calculate per-file scores
        file_scores = {}
        for filename, sources in file_sources.items():
            content = f"# {filename}\n\nContent"
            file_scores[filename] = calculator.calculate_file_confidence(filename, sources, content)
        
        # Calculate overall score
        overall_score = calculator.calculate_overall_confidence(file_scores)
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Verify results
        assert len(file_scores) == 100
        assert isinstance(overall_score, ConfidenceScore)
        
        # Full workflow should complete in reasonable time
        # Target: 100 files * 1ms + 200ms overall = ~300ms
        assert elapsed_ms < 1000, f"Full workflow took {elapsed_ms:.2f}ms (target: < 1000ms)"
    
    def test_confidence_calculation_scales_linearly(self):
        """Test that confidence calculation scales linearly with number of files."""
        calculator = ConfidenceCalculator()
        
        times = []
        file_counts = [10, 50, 100]
        
        for count in file_counts:
            # Create source data for specified number of files
            file_sources = {}
            for i in range(count):
                file_sources[f"file_{i}.md"] = {
                    "documents": ["Section 1"],
                    "code_analysis": ["Section 2"],
                    "inferred": ["Section 3"],
                }
            
            # Measure time for full workflow
            start_time = time.perf_counter()
            
            file_scores = {}
            for filename, sources in file_sources.items():
                content = f"# {filename}\n\nContent"
                file_scores[filename] = calculator.calculate_file_confidence(filename, sources, content)
            
            calculator.calculate_overall_confidence(file_scores)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            times.append(elapsed_ms)
        
        # Verify all times are reasonable
        for i, (count, time_ms) in enumerate(zip(file_counts, times)):
            assert time_ms < count * 10, f"{count} files: {time_ms:.2f}ms (target: < {count * 10}ms)"
        
        # Check that scaling is reasonable (linear or better)
        # Time for 100 files should be < 20x time for 10 files
        if times[0] > 0:
            scaling_factor = times[2] / times[0]
            assert scaling_factor < 20, f"Scaling factor: {scaling_factor:.2f}x (should be < 20x)"


class TestEdgeCasePerformance:
    """Tests for performance with edge cases."""
    
    def test_empty_sources_performance(self):
        """Test performance with no source sections."""
        calculator = ConfidenceCalculator()
        
        sources = {
            "documents": [],
            "code_analysis": [],
            "inferred": []
        }
        content = "# Test File\n\nContent"
        
        start_time = time.perf_counter()
        score = calculator.calculate_file_confidence("test.md", sources, content)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Should be very fast with no sources
        assert elapsed_ms < 10, f"Empty sources calculation took {elapsed_ms:.2f}ms (target: < 10ms)"
        assert score.overall == 0.0  # No sources
    
    def test_all_document_sources_performance(self):
        """Test performance when all sections are from documents."""
        calculator = ConfidenceCalculator()
        
        sources = {
            "documents": [f"Section {i}" for i in range(20)],
            "code_analysis": [],
            "inferred": []
        }
        content = "# Test File\n\nContent"
        
        start_time = time.perf_counter()
        score = calculator.calculate_file_confidence("test.md", sources, content)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Should still be fast even with many sections
        assert elapsed_ms < 100, f"All-document calculation took {elapsed_ms:.2f}ms (target: < 100ms)"
        assert score.overall == 1.0  # All from documents
    
    def test_many_sections_performance(self):
        """Test performance with file containing many sections."""
        calculator = ConfidenceCalculator()
        
        # Create sources with 50 sections
        sources = {
            "documents": [f"Doc Section {i}" for i in range(17)],
            "code_analysis": [f"Code Section {i}" for i in range(17)],
            "inferred": [f"Inferred Section {i}" for i in range(16)],
        }
        content = "# Test File\n\nContent"
        
        start_time = time.perf_counter()
        score = calculator.calculate_file_confidence("test.md", sources, content)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Should handle many sections efficiently
        assert elapsed_ms < 150, f"50-section calculation took {elapsed_ms:.2f}ms (target: < 150ms)"
        assert isinstance(score, ConfidenceScore)
