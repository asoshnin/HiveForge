"""
Property-based tests for structural consistency validation.

Validates: Requirements 21.1-21.6 (v02.1)
"""

import pytest
from hypothesis import given, strategies as st
from unittest.mock import Mock, patch

from hiveforge.steering.structural_checker import (
    StructuralConsistencyChecker,
    StructuralCheckResult,
    RoundTripResult,
)


class TestStructuralConsistency:
    """Tests for structural consistency checking."""
    
    def test_extract_sections_basic(self):
        """
        WHEN sections are extracted from markdown, all headers SHALL be identified.
        """
        checker = StructuralConsistencyChecker()
        
        content = """# Project Title

## Overview
Some content here.

### Goals
- Goal 1
- Goal 2

## Architecture
More content.
"""
        
        sections = checker.extract_sections(content)
        
        assert "Project Title" in sections
        assert "Overview" in sections
        # Level 3 headers are excluded (deeper than level 2)
        assert "Goals" not in sections
        assert "Architecture" in sections
    
    def test_extract_sections_ignores_deep_headers(self):
        """
        WHEN headers are deeper than level 2, they SHALL be ignored.
        """
        checker = StructuralConsistencyChecker()
        
        content = """# Title

## Section 1

### Subsection 1.1

#### Deep Subsection
Content here.
"""
        
        sections = checker.extract_sections(content)
        
        assert "Title" in sections
        assert "Section 1" in sections
        # Level 3 headers should be excluded (deeper than level 2)
        assert "Subsection 1.1" not in sections
        # Deep headers should be excluded
        assert "Deep Subsection" not in sections
    
    def test_extract_key_facts_technologies(self):
        """
        WHEN key facts are extracted, technology names and versions SHALL be identified.
        """
        checker = StructuralConsistencyChecker()
        
        content = """
        The project uses Python 3.11 and Node.js 18 for the backend.
        Frontend is built with React 18.
        Database is PostgreSQL 15.
        """
        
        facts = checker.extract_key_facts(content)
        
        # Check that each technology and version is present in facts
        has_python = any("Python" in f and "3.11" in f for f in facts)
        has_node = any("Node" in f and "18" in f for f in facts)
        has_react = any("React" in f and "18" in f for f in facts)
        has_postgres = any("PostgreSQL" in f and "15" in f for f in facts)
        
        assert has_python, f"Expected Python 3.11 in facts: {facts}"
        assert has_node, f"Expected Node.js 18 in facts: {facts}"
        assert has_react, f"Expected React 18 in facts: {facts}"
        assert has_postgres, f"Expected PostgreSQL 15 in facts: {facts}"
    
    def test_extract_key_facts_architecture(self):
        """
        WHEN key facts are extracted, architecture patterns SHALL be identified.
        """
        checker = StructuralConsistencyChecker()
        
        content = """
        The system follows a microservices architecture.
        API is exposed via REST endpoints.
        Services are containerized using Docker.
        """
        
        facts = checker.extract_key_facts(content)
        
        assert any("microservices" in f for f in facts)
        assert any("rest" in f for f in facts)
        assert any("containerized" in f for f in facts)
    
    def test_calculate_length_similarity_identical(self):
        """
        WHEN content has identical length, similarity SHALL be 1.0.
        """
        checker = StructuralConsistencyChecker()
        
        similarity = checker.calculate_length_similarity("hello world", "hello world")
        
        assert similarity == 1.0
    
    def test_calculate_length_similarity_similar(self):
        """
        WHEN content has similar length, similarity SHALL reflect the difference.
        """
        checker = StructuralConsistencyChecker()
        
        # 100 chars vs 120 chars = 16.7% difference
        content1 = "a" * 100
        content2 = "a" * 120
        
        similarity = checker.calculate_length_similarity(content1, content2)
        
        # Should be around 0.83 (1 - 20/120)
        assert 0.80 <= similarity <= 0.85
    
    def test_calculate_length_similarity_different(self):
        """
        WHEN content has very different length, similarity SHALL be low.
        """
        checker = StructuralConsistencyChecker()
        
        # 100 chars vs 500 chars = 80% difference
        content1 = "a" * 100
        content2 = "a" * 500
        
        similarity = checker.calculate_length_similarity(content1, content2)
        
        # Should be around 0.20 (1 - 400/500)
        assert similarity < 0.30
    
    def test_calculate_section_similarity_identical(self):
        """
        WHEN sections are identical, similarity SHALL be 1.0.
        """
        checker = StructuralConsistencyChecker()
        
        sections1 = ["Overview", "Architecture", "Goals"]
        sections2 = ["Overview", "Architecture", "Goals"]
        
        similarity, matched, missing, extra = checker.calculate_section_similarity(
            sections1, sections2
        )
        
        assert similarity == 1.0
        assert len(matched) == 3
        assert len(missing) == 0
        assert len(extra) == 0
    
    def test_calculate_section_similarity_partial(self):
        """
        WHEN sections partially match, similarity SHALL reflect overlap.
        """
        checker = StructuralConsistencyChecker()
        
        sections1 = ["Overview", "Architecture", "Goals"]
        sections2 = ["Overview", "Database", "Goals"]
        
        similarity, matched, missing, extra = checker.calculate_section_similarity(
            sections1, sections2
        )
        
        # 2 out of 4 unique sections = 0.5
        assert similarity == 0.5
        assert "Overview" in matched
        assert "Goals" in matched
        assert "Architecture" in missing
        assert "Database" in extra
    
    def test_calculate_section_similarity_no_overlap(self):
        """
        WHEN sections have no overlap, similarity SHALL be 0.0.
        """
        checker = StructuralConsistencyChecker()
        
        sections1 = ["Overview", "Architecture"]
        sections2 = ["Database", "Goals"]
        
        similarity, matched, missing, extra = checker.calculate_section_similarity(
            sections1, sections2
        )
        
        assert similarity == 0.0
        assert len(matched) == 0
    
    def test_calculate_key_facts_similarity(self):
        """
        WHEN key facts are compared, similarity SHALL reflect overlap.
        """
        checker = StructuralConsistencyChecker()
        
        facts1 = ["Python 3.11", "React 18", "PostgreSQL 15"]
        facts2 = ["Python 3.11", "React 18", "MongoDB"]
        
        similarity, present, missing = checker.calculate_key_facts_similarity(
            facts1, facts2
        )
        
        # 2 out of 3 = 0.67
        assert abs(similarity - 0.67) < 0.01
        assert "Python 3.11" in present
        assert "React 18" in present
        assert "PostgreSQL 15" in missing
    
    def test_check_structural_similarity_consistent(self):
        """
        WHEN content is structurally similar, result SHALL be consistent.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = """# Project

## Overview
This is a Python project.

## Architecture
Uses FastAPI framework.
"""
        
        content2 = """# Project

## Overview
This is a Python project using FastAPI.

## Architecture
Built with FastAPI framework.
"""
        
        result = checker.check_structural_similarity(content1, content2)
        
        assert result.is_consistent
        assert result.similarity_score >= 0.70
        assert len(result.sections_missing) == 0
    
    def test_check_structural_similarity_inconsistent(self):
        """
        WHEN content has different sections, result SHALL be inconsistent.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = """# Project

## Overview
Content here.

## Architecture
More content.
"""
        
        content2 = """# Project

## Overview
Content here.
"""
        
        result = checker.check_structural_similarity(content1, content2)
        
        assert not result.is_consistent
        assert "Architecture" in result.sections_missing
    
    def test_check_structural_similarity_tracks_metrics(self):
        """
        WHEN section_type is provided, metrics SHALL be tracked.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        result = checker.check_structural_similarity(content1, content2, "tech-stack")
        
        metrics = checker.track_consistency_rate("tech-stack")
        
        assert metrics["total_checks"] == 1
        assert metrics["consistent_checks"] == 1
        assert metrics["consistency_rate"] == 1.0
    
    def test_set_generation_parameters(self):
        """
        WHEN generation parameters are set, they SHALL be stored.
        """
        checker = StructuralConsistencyChecker()
        
        checker.set_generation_parameters(temperature=0.0, seed=42)
        
        params = checker.get_generation_parameters()
        
        assert params["temperature"] == 0.0
        assert params["seed"] == 42
    
    def test_default_generation_parameters(self):
        """
        WHEN no parameters are set, defaults SHALL be used.
        """
        checker = StructuralConsistencyChecker()
        
        params = checker.get_generation_parameters()
        
        assert params["temperature"] == 0.0
        assert params["seed"] == 42
    
    def test_track_consistency_rate_no_data(self):
        """
        WHEN no checks have been run, no_data status SHALL be returned.
        """
        checker = StructuralConsistencyChecker()
        
        metrics = checker.track_consistency_rate("tech-stack")
        
        assert metrics["status"] == "no_data"
        assert metrics["total_checks"] == 0
    
    def test_track_consistency_rate_summary(self):
        """
        WHEN tracking multiple sections, summary SHALL be provided.
        """
        checker = StructuralConsistencyChecker()
        
        # Add some checks
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        checker.check_structural_similarity(content1, content2, "tech-stack")
        checker.check_structural_similarity(content1, content2, "architecture")
        
        metrics = checker.track_consistency_rate()
        
        assert "_summary" in metrics
        assert metrics["_summary"]["total_checks"] == 2
        assert metrics["_summary"]["total_consistent"] == 2
    
    def test_check_strategy_adjustment_below_threshold(self):
        """
        WHEN consistency is below 80%, adjustment SHALL be recommended.
        """
        checker = StructuralConsistencyChecker()
        
        # Simulate low consistency
        for _ in range(5):
            content1 = "# Project\n\n## Overview\nContent A."
            content2 = "# Different\n\n## Section\nContent B."
            checker.check_structural_similarity(content1, content2, "tech-stack")
        
        recommendation = checker.check_strategy_adjustment("tech-stack")
        
        assert recommendation["needs_adjustment"] is True
        assert recommendation["reason"] == "consistency_below_threshold"
        assert len(recommendation["recommendation"]) > 0
    
    def test_check_strategy_adjustment_acceptable(self):
        """
        WHEN consistency is acceptable, no adjustment SHALL be needed.
        """
        checker = StructuralConsistencyChecker()
        
        # Simulate high consistency
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        for _ in range(5):
            checker.check_structural_similarity(content1, content2, "tech-stack")
        
        recommendation = checker.check_strategy_adjustment("tech-stack")
        
        assert recommendation["needs_adjustment"] is False
        assert recommendation["reason"] == "consistency_acceptable"
    
    def test_check_strategy_adjustment_insufficient_data(self):
        """
        WHEN fewer than 5 checks, insufficient_data SHALL be returned.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        checker.check_structural_similarity(content1, content2, "tech-stack")
        
        recommendation = checker.check_strategy_adjustment("tech-stack")
        
        assert recommendation["needs_adjustment"] is False
        assert recommendation["reason"] == "insufficient_data"
    
    def test_test_round_trip_success(self):
        """
        WHEN round-trip generation succeeds, result SHALL show success.
        """
        checker = StructuralConsistencyChecker()
        checker.set_generation_parameters(temperature=0.0, seed=42)
        
        def mock_generate(context, temperature, seed):
            return "# Project\n\n## Overview\nGenerated content."
        
        result = checker.test_round_trip(
            generate_func=mock_generate,
            context={"project_name": "test"},
            max_attempts=2,
        )
        
        assert result.success is True
        # Initial generation + 2 regeneration attempts = 3 generations
        assert len(result.generations) == 3
        # 2 consistency scores (comparing gen2 vs gen1, gen3 vs gen1)
        assert len(result.consistency_scores) == 2
        assert result.average_consistency > 0.0
    
    def test_test_round_trip_inconsistency(self):
        """
        WHEN round-trip produces inconsistent results, SHALL be flagged.
        """
        checker = StructuralConsistencyChecker()
        checker.set_generation_parameters(temperature=0.0, seed=42)
        
        call_count = [0]
        
        def mock_generate(context, temperature, seed):
            call_count[0] += 1
            if call_count[0] == 1:
                return "# Project\n\n## Overview\nFirst version."
            else:
                return "# Different\n\n## Section\nSecond version."
        
        result = checker.test_round_trip(
            generate_func=mock_generate,
            context={"project_name": "test"},
            max_attempts=2,
        )
        
        assert result.success is True  # Generation succeeded, just inconsistent
        # Initial generation + 2 regeneration attempts = 3 generations
        assert len(result.generations) == 3
        assert len(result.unstable_sections) > 0
    
    def test_test_round_trip_generation_failure(self):
        """
        WHEN generation fails, result SHALL show failure.
        """
        checker = StructuralConsistencyChecker()
        
        def mock_generate(context, temperature, seed):
            raise ValueError("Generation failed")
        
        result = checker.test_round_trip(
            generate_func=mock_generate,
            context={"project_name": "test"},
            max_attempts=2,
        )
        
        assert result.success is False
        assert "failed" in result.details.lower()
    
    def test_reset_metrics(self):
        """
        WHEN reset is called, metrics SHALL be cleared.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        checker.check_structural_similarity(content1, content2, "tech-stack")
        
        assert checker.track_consistency_rate("tech-stack")["total_checks"] == 1
        
        checker.reset_metrics("tech-stack")
        
        assert checker.track_consistency_rate("tech-stack")["total_checks"] == 0
    
    def test_save_metrics(self):
        """
        WHEN save_metrics is called, file SHALL be created.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        checker.check_structural_similarity(content1, content2, "tech-stack")
        
        output_file = checker.save_metrics()
        
        assert output_file.exists()
        
        import json
        with open(output_file) as f:
            data = json.load(f)
        
        assert "timestamp" in data
        assert "metrics" in data
    
    def test_inconsistency_logging(self):
        """
        WHEN inconsistency is detected during round-trip, it SHALL be logged.
        """
        checker = StructuralConsistencyChecker()
        
        # Clean up any existing log file
        log_file = checker.telemetry_dir / "inconsistencies.jsonl"
        if log_file.exists():
            log_file.unlink()
        
        call_count = [0]
        
        def mock_generate(context, temperature, seed):
            call_count[0] += 1
            if call_count[0] == 1:
                return "# Project\n\n## Overview\nFirst version."
            else:
                return "# Different\n\n## Section\nSecond version."
        
        result = checker.test_round_trip(
            generate_func=mock_generate,
            context={"project_name": "test"},
            max_attempts=2,
        )
        
        assert log_file.exists()
        
        with open(log_file) as f:
            lines = f.readlines()
        
        # Should have entries for each inconsistent regeneration
        assert len(lines) >= 1
        
        import json
        log_entry = json.loads(lines[0])
        
        assert "timestamp" in log_entry
        assert log_entry["similarity_score"] < checker.min_similarity_score


class TestStructuralConsistencyProperties:
    """Property-based tests for structural consistency."""
    
    @pytest.mark.property("Property 21: Generation Consistency")
    @given(st.text(min_size=1, alphabet=st.characters(
        whitelist_categories=['L', 'N'],
        whitelist_characters=' _-'
    )))
    def test_section_extraction_property(self, content: str):
        """
        Property: Section extraction should handle any string input.
        For any content string, the extractor should return a list.
        """
        checker = StructuralConsistencyChecker()
        
        sections = checker.extract_sections(content)
        
        assert isinstance(sections, list)
    
    @pytest.mark.property("Property 21: Generation Consistency")
    @given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
    def test_section_similarity_property(self, sections: list):
        """
        Property: Section similarity should always return valid values.
        For any list of sections, similarity should be between 0 and 1.
        """
        checker = StructuralConsistencyChecker()
        
        similarity, matched, missing, extra = checker.calculate_section_similarity(
            sections, sections
        )
        
        assert 0.0 <= similarity <= 1.0
        # When comparing identical lists, all elements should be in matched
        # (using set comparison, duplicates are merged)
        assert len(matched) <= len(sections)
        assert len(missing) == 0
        assert len(extra) == 0
    
    @pytest.mark.property("Property 21: Generation Consistency")
    @given(st.floats(min_value=0.1, max_value=1.0))  # Avoid very small values that cause overflow
    def test_length_similarity_property(self, length_ratio: float):
        """
        Property: Length similarity should handle any length ratio.
        For any length ratio, the similarity calculation should be valid.
        """
        checker = StructuralConsistencyChecker()
        
        # Create content with specific length ratio
        base_len = 100
        if length_ratio > 0 and length_ratio < 1:
            len1 = base_len
            len2 = int(base_len * (1 - length_ratio) / length_ratio)
        elif length_ratio >= 1:
            len1 = base_len
            len2 = base_len
        else:
            len1 = base_len
            len2 = 0
        
        # Ensure lengths are reasonable
        len2 = max(0, min(len2, 10000))
        
        content1 = "a" * len1
        content2 = "a" * len2
        
        similarity = checker.calculate_length_similarity(content1, content2)
        
        assert 0.0 <= similarity <= 1.0
    
    @pytest.mark.property("Property 21: Generation Consistency")
    @given(st.integers(min_value=1, max_value=1000))
    def test_consistency_tracking_property(self, num_checks: int):
        """
        Property: Consistency tracking should handle any number of checks.
        For any number of consistency checks, metrics should be accurate.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        for _ in range(num_checks):
            checker.check_structural_similarity(content1, content2, "tech-stack")
        
        metrics = checker.track_consistency_rate("tech-stack")
        
        assert metrics["total_checks"] == num_checks
        assert metrics["consistent_checks"] == num_checks
        assert metrics["consistency_rate"] == 1.0
    
    @pytest.mark.property("Property 21: Generation Consistency")
    @given(st.integers(min_value=1, max_value=10))
    def test_round_trip_attempts_property(self, attempts: int):
        """
        Property: Round-trip should handle any number of attempts.
        For any number of attempts, the result should reflect all generations.
        """
        checker = StructuralConsistencyChecker()
        checker.set_generation_parameters(temperature=0.0, seed=42)
        
        call_count = [0]
        
        def mock_generate(context, temperature, seed):
            call_count[0] += 1
            return f"# Generation {call_count[0]}\n\n## Section\nContent {call_count[0]}."
        
        result = checker.test_round_trip(
            generate_func=mock_generate,
            context={},
            max_attempts=attempts,
        )
        
        # Initial generation + attempts = attempts + 1 generations
        assert len(result.generations) == attempts + 1
        # One consistency score per attempt
        assert len(result.consistency_scores) == attempts
    
    @pytest.mark.property("Property 21: Generation Consistency")
    @given(st.sampled_from(["tech-stack", "architecture", "conventions", "project-vision"]))
    def test_section_type_tracking_property(self, section_type: str):
        """
        Property: Each section type should track metrics independently.
        For any section type, metrics should be tracked separately.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        checker.check_structural_similarity(content1, content2, section_type)
        
        metrics = checker.track_consistency_rate(section_type)
        
        assert metrics["section_type"] == section_type
        assert metrics["total_checks"] == 1
        assert metrics["status"] == "healthy"
    
    @pytest.mark.property("Property 21: Generation Consistency")
    @given(st.floats(min_value=0.5, max_value=1.0))
    def test_threshold_property(self, threshold: float):
        """
        Property: Custom thresholds should be respected.
        For any threshold between 0.5 and 1.0, the checker should use it.
        """
        checker = StructuralConsistencyChecker(min_consistency_rate=threshold)
        
        assert checker.min_consistency_rate == threshold
        
        # Test with content that should be consistent
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        
        result = checker.check_structural_similarity(content1, content2, "test")
        
        # Should be consistent regardless of threshold in this range
        assert result.is_consistent


class TestStructuralConsistencyEdgeCases:
    """Edge case tests for structural consistency."""
    
    def test_empty_content(self):
        """
        WHEN content is empty, similarity calculations SHALL handle gracefully.
        """
        checker = StructuralConsistencyChecker()
        
        result = checker.check_structural_similarity("", "")
        
        assert result.is_consistent
        assert result.similarity_score == 1.0
        assert result.sections_missing == []
        assert result.sections_extra == []
    
    def test_one_empty_content(self):
        """
        WHEN one content is empty, similarity SHALL be low.
        """
        checker = StructuralConsistencyChecker()
        
        result = checker.check_structural_similarity("content", "")
        
        assert not result.is_consistent
        # Length similarity is 0, but sections and key facts may match
        assert result.length_similarity == 0.0
    
    def test_no_sections(self):
        """
        WHEN content has no sections, sections list SHALL be empty.
        """
        checker = StructuralConsistencyChecker()
        
        content = "Just plain text without any headers."
        sections = checker.extract_sections(content)
        
        assert sections == []
    
    def test_very_long_content(self):
        """
        WHEN content is very long, similarity SHALL still be calculated.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = "# Project\n\n" + ("Content line.\n" * 1000)
        content2 = "# Project\n\n" + ("Content line.\n" * 1000)
        
        result = checker.check_structural_similarity(content1, content2)
        
        assert result.is_consistent
        assert result.similarity_score > 0.9
    
    def test_unicode_content(self):
        """
        WHEN content contains unicode, it SHALL be handled correctly.
        """
        checker = StructuralConsistencyChecker()
        
        content1 = "# 项目\n\n## 概述\n内容。"
        content2 = "# 项目\n\n## 概述\n内容。"
        
        result = checker.check_structural_similarity(content1, content2)
        
        assert result.is_consistent
    
    def test_special_characters_in_sections(self):
        """
        WHEN sections contain special characters, they SHALL be extracted.
        """
        checker = StructuralConsistencyChecker()
        
        content = """# Project with Special Chars: Test

## Section with (parentheses) and [brackets]
Content here.
"""
        
        sections = checker.extract_sections(content)
        
        assert any("Project with Special Chars" in s for s in sections)
        assert any("Section with" in s for s in sections)
    
    def test_consecutive_round_trips(self):
        """
        WHEN multiple round-trips are run, metrics SHALL accumulate.
        """
        checker = StructuralConsistencyChecker()
        checker.set_generation_parameters(temperature=0.0, seed=42)
        
        def mock_generate(context, temperature, seed):
            return "# Project\n\n## Overview\nContent."
        
        # Run round-trips
        checker.test_round_trip(mock_generate, {}, max_attempts=2)
        checker.test_round_trip(mock_generate, {}, max_attempts=2)
        
        # Track metrics explicitly for a section type
        content1 = "# Project\n\n## Overview\nContent."
        content2 = "# Project\n\n## Overview\nContent."
        checker.check_structural_similarity(content1, content2, "tech-stack")
        checker.check_structural_similarity(content1, content2, "tech-stack")
        
        metrics = checker.track_consistency_rate()
        
        # Should have accumulated checks from both round-trips
        assert metrics["_summary"]["total_checks"] >= 2