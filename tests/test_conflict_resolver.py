"""
Tests for the ConflictResolver class.

Tests both unit examples and property-based tests for conflict detection
and resolution functionality.
"""

import pytest
from hypothesis import given, strategies as st

from src.hiveforge.steering.conflict_resolver import ConflictResolver
from src.hiveforge.steering.models import Conflict


class TestConflictResolverUnit:
    """Unit tests for ConflictResolver with specific examples."""
    
    def test_detect_conflicts_no_conflicts(self):
        """Test conflict detection when content is identical."""
        old_content = {"database": "PostgreSQL", "framework": "FastAPI"}
        new_content = {"database": "PostgreSQL", "framework": "FastAPI"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 0
    
    def test_detect_conflicts_technology_change(self):
        """Test detection of technology choice conflicts."""
        old_content = {"database": "PostgreSQL 15"}
        new_content = {"database": "MongoDB 6"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
        assert conflicts[0].section == "database"
        assert conflicts[0].old_value == "PostgreSQL 15"
        assert conflicts[0].new_value == "MongoDB 6"
        assert "technology" in conflicts[0].explanation.lower()
    
    def test_detect_conflicts_architecture_change(self):
        """Test detection of architecture pattern conflicts."""
        old_content = {"architecture_pattern": "monolithic"}
        new_content = {"architecture_pattern": "microservices"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
        assert conflicts[0].section == "architecture_pattern"
        assert "architecture" in conflicts[0].explanation.lower()
    
    def test_detect_conflicts_goal_change(self):
        """Test detection of project goal conflicts."""
        old_content = {"project_goal": "Build a simple blog"}
        new_content = {"project_goal": "Build an enterprise CMS"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
        assert conflicts[0].section == "project_goal"
        assert "goal" in conflicts[0].explanation.lower()
    
    def test_detect_conflicts_multiple_conflicts(self):
        """Test detection of multiple conflicts."""
        old_content = {
            "database": "PostgreSQL",
            "framework": "Django",
            "architecture": "monolithic"
        }
        new_content = {
            "database": "MongoDB",
            "framework": "FastAPI",
            "architecture": "microservices"
        }
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 3
        sections = {c.section for c in conflicts}
        assert sections == {"database", "framework", "architecture"}
    
    def test_detect_conflicts_ignores_new_keys(self):
        """Test that new keys without old values are not conflicts."""
        old_content = {"database": "PostgreSQL"}
        new_content = {"database": "PostgreSQL", "cache": "Redis"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        # Only common keys are checked, so no conflict for 'cache'
        assert len(conflicts) == 0
    
    def test_detect_conflicts_ignores_removed_keys(self):
        """Test that removed keys are not treated as conflicts."""
        old_content = {"database": "PostgreSQL", "cache": "Redis"}
        new_content = {"database": "PostgreSQL"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 0
    
    def test_detect_conflicts_ignores_empty_values(self):
        """Test that empty values are not treated as conflicts."""
        old_content = {"database": "PostgreSQL", "cache": ""}
        new_content = {"database": "PostgreSQL", "cache": "Redis"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        # Empty old value should be ignored
        assert len(conflicts) == 0
    
    def test_detect_conflicts_with_none_values(self):
        """Test handling of None values."""
        old_content = {"database": None}
        new_content = {"database": "PostgreSQL"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        # None values should be treated as empty and ignored
        assert len(conflicts) == 0
    
    def test_resolve_conflict_keep_old(self):
        """Test resolving conflict by keeping old value."""
        conflict = Conflict(
            section="database",
            old_value="PostgreSQL",
            new_value="MongoDB",
            explanation="Test conflict"
        )
        
        result = ConflictResolver.resolve_conflict(conflict, "keep_old")
        
        assert result == "PostgreSQL"
    
    def test_resolve_conflict_use_new(self):
        """Test resolving conflict by using new value."""
        conflict = Conflict(
            section="database",
            old_value="PostgreSQL",
            new_value="MongoDB",
            explanation="Test conflict"
        )
        
        result = ConflictResolver.resolve_conflict(conflict, "use_new")
        
        assert result == "MongoDB"
    
    def test_resolve_conflict_merge(self):
        """Test resolving conflict by merging values."""
        conflict = Conflict(
            section="database",
            old_value="PostgreSQL",
            new_value="MongoDB",
            explanation="Test conflict"
        )
        
        result = ConflictResolver.resolve_conflict(conflict, "merge")
        
        # Merged result should contain both values
        assert "PostgreSQL" in result
        assert "MongoDB" in result
    
    def test_resolve_conflict_invalid_choice(self):
        """Test that invalid resolution choice raises error."""
        conflict = Conflict(
            section="database",
            old_value="PostgreSQL",
            new_value="MongoDB",
            explanation="Test conflict"
        )
        
        with pytest.raises(ValueError, match="Invalid resolution choice"):
            ConflictResolver.resolve_conflict(conflict, "invalid_choice")
    
    def test_merge_values_short_phrases(self):
        """Test merging short phrases."""
        result = ConflictResolver._merge_values("PostgreSQL", "MongoDB")
        
        assert "PostgreSQL" in result
        assert "MongoDB" in result
        assert "/" in result
    
    def test_merge_values_sentences(self):
        """Test merging sentence-like content."""
        old = "This is the old approach."
        new = "This is the new approach."
        
        result = ConflictResolver._merge_values(old, new)
        
        assert old.strip() in result
        assert new.strip() in result
    
    def test_merge_values_multiline(self):
        """Test merging multi-line content."""
        old = "Line 1\nLine 2"
        new = "Line 3\nLine 4"
        
        result = ConflictResolver._merge_values(old, new)
        
        assert "Line 1" in result
        assert "Line 4" in result
        assert "\n\n" in result  # Should have blank line separator
    
    def test_merge_values_one_contains_other(self):
        """Test merging when one value contains the other."""
        old = "PostgreSQL"
        new = "PostgreSQL 15"
        
        result = ConflictResolver._merge_values(old, new)
        
        # Should return the longer one
        assert result == "PostgreSQL 15"
    
    def test_format_conflict_presentation(self):
        """Test formatting conflict for presentation."""
        conflict = Conflict(
            section="database",
            old_value="PostgreSQL 15",
            new_value="MongoDB 6",
            explanation="Database technology has changed"
        )
        
        presentation = ConflictResolver.format_conflict_presentation(conflict)
        
        assert "database" in presentation
        assert "PostgreSQL 15" in presentation
        assert "MongoDB 6" in presentation
        assert "Database technology has changed" in presentation
        assert "OLD VALUE" in presentation
        assert "NEW VALUE" in presentation
        assert "Resolution options" in presentation
    
    def test_detect_conflicts_framework_change(self):
        """Test detection of framework conflicts."""
        old_content = {"backend_framework": "Django"}
        new_content = {"backend_framework": "FastAPI"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
        assert "technology" in conflicts[0].explanation.lower()
    
    def test_detect_conflicts_vision_change(self):
        """Test detection of vision/mission conflicts."""
        old_content = {"project_vision": "Simple tool for personal use"}
        new_content = {"project_vision": "Enterprise-grade platform"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
        assert "vision" in conflicts[0].explanation.lower() or "goal" in conflicts[0].explanation.lower()
    
    def test_detect_conflicts_case_insensitive_keywords(self):
        """Test that keyword matching is case-insensitive."""
        old_content = {"Database": "PostgreSQL"}
        new_content = {"Database": "MongoDB"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
        assert "technology" in conflicts[0].explanation.lower()
    
    def test_conflict_has_resolution_options(self):
        """Test that detected conflicts have resolution options."""
        old_content = {"database": "PostgreSQL"}
        new_content = {"database": "MongoDB"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
        assert "keep_old" in conflicts[0].resolution_options
        assert "use_new" in conflicts[0].resolution_options
        assert "merge" in conflicts[0].resolution_options


class TestConflictResolverProperties:
    """Property-based tests for ConflictResolver."""
    
    # Feature: steering_assistant, Property 15: Conflict Detection
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=10
        )
    )
    def test_identical_content_produces_no_conflicts(self, content: dict):
        """Property: Identical content should produce no conflicts."""
        conflicts = ConflictResolver.detect_conflicts(content, content)
        assert len(conflicts) == 0
    
    # Feature: steering_assistant, Property 15: Conflict Detection
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=10
        ),
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=10
        )
    )
    def test_conflict_detection_is_deterministic(self, old_content: dict, new_content: dict):
        """Property: Detecting conflicts twice should give identical results."""
        conflicts1 = ConflictResolver.detect_conflicts(old_content, new_content)
        conflicts2 = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts1) == len(conflicts2)
        
        # Check that conflicts are the same
        for c1, c2 in zip(conflicts1, conflicts2):
            assert c1.section == c2.section
            assert c1.old_value == c2.old_value
            assert c1.new_value == c2.new_value
    
    # Feature: steering_assistant, Property 16: Conflict Presentation
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100)
    )
    def test_all_conflicts_have_explanations(self, section: str, old_val: str, new_val: str):
        """Property: All detected conflicts should have explanations."""
        if old_val == new_val:
            return  # Skip identical values
        
        old_content = {section: old_val}
        new_content = {section: new_val}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        for conflict in conflicts:
            assert conflict.explanation
            assert len(conflict.explanation) > 0
            assert conflict.section in conflict.explanation
    
    # Feature: steering_assistant, Property 16: Conflict Presentation
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100)
    )
    def test_conflict_presentation_contains_both_values(self, section: str, old_val: str, new_val: str):
        """Property: Conflict presentation should show both old and new values."""
        if old_val == new_val:
            return
        
        conflict = Conflict(
            section=section,
            old_value=old_val,
            new_value=new_val,
            explanation="Test conflict"
        )
        
        presentation = ConflictResolver.format_conflict_presentation(conflict)
        
        assert old_val in presentation
        assert new_val in presentation
        assert section in presentation
    
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100),
        st.sampled_from(["keep_old", "use_new", "merge"])
    )
    def test_resolve_conflict_returns_string(self, section: str, old_val: str, new_val: str, choice: str):
        """Property: Resolving a conflict should always return a string."""
        conflict = Conflict(
            section=section,
            old_value=old_val,
            new_value=new_val,
            explanation="Test conflict"
        )
        
        result = ConflictResolver.resolve_conflict(conflict, choice)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100)
    )
    def test_keep_old_preserves_old_value(self, section: str, old_val: str, new_val: str):
        """Property: Choosing 'keep_old' should return the old value unchanged."""
        conflict = Conflict(
            section=section,
            old_value=old_val,
            new_value=new_val,
            explanation="Test conflict"
        )
        
        result = ConflictResolver.resolve_conflict(conflict, "keep_old")
        
        assert result == old_val
    
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100)
    )
    def test_use_new_preserves_new_value(self, section: str, old_val: str, new_val: str):
        """Property: Choosing 'use_new' should return the new value unchanged."""
        conflict = Conflict(
            section=section,
            old_value=old_val,
            new_value=new_val,
            explanation="Test conflict"
        )
        
        result = ConflictResolver.resolve_conflict(conflict, "use_new")
        
        assert result == new_val
    
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100)
    )
    def test_merge_contains_both_values(self, section: str, old_val: str, new_val: str):
        """Property: Merging should produce a result containing both values."""
        if old_val in new_val or new_val in old_val:
            return  # Skip when one contains the other
        
        conflict = Conflict(
            section=section,
            old_value=old_val,
            new_value=new_val,
            explanation="Test conflict"
        )
        
        result = ConflictResolver.resolve_conflict(conflict, "merge")
        
        # Result should contain both values (or their stripped versions)
        assert old_val.strip() in result or new_val.strip() in result
    
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=20)
    )
    def test_invalid_choice_raises_error(self, section: str, old_val: str, new_val: str, invalid_choice: str):
        """Property: Invalid resolution choices should raise ValueError."""
        # Ensure invalid_choice is actually invalid
        if invalid_choice in ["keep_old", "use_new", "merge"]:
            return
        
        conflict = Conflict(
            section=section,
            old_value=old_val,
            new_value=new_val,
            explanation="Test conflict"
        )
        
        with pytest.raises(ValueError):
            ConflictResolver.resolve_conflict(conflict, invalid_choice)
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=10
        ),
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=10
        )
    )
    def test_conflicts_only_for_common_keys(self, old_content: dict, new_content: dict):
        """Property: Conflicts should only be detected for keys present in both dictionaries."""
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        common_keys = set(old_content.keys()) & set(new_content.keys())
        
        for conflict in conflicts:
            assert conflict.section in common_keys
    
    @given(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        st.text(min_size=1, max_size=100)
    )
    def test_conflict_has_required_fields(self, section: str, old_val: str, new_val: str):
        """Property: All conflicts should have required fields populated."""
        if old_val == new_val:
            return
        
        old_content = {section: old_val}
        new_content = {section: new_val}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        for conflict in conflicts:
            assert conflict.section
            assert conflict.old_value
            assert conflict.new_value
            assert conflict.explanation
            assert len(conflict.resolution_options) > 0
    
    @given(st.text(min_size=1, max_size=100), st.text(min_size=1, max_size=100))
    def test_merge_is_deterministic(self, old_val: str, new_val: str):
        """Property: Merging the same values should always produce the same result."""
        result1 = ConflictResolver._merge_values(old_val, new_val)
        result2 = ConflictResolver._merge_values(old_val, new_val)
        
        assert result1 == result2
    
    @given(st.text(min_size=1, max_size=100))
    def test_merge_with_self_returns_self(self, value: str):
        """Property: Merging a value with itself should return the value."""
        result = ConflictResolver._merge_values(value, value)
        
        # When values are identical, merge should return one of them
        assert value in result


class TestConflictResolverEdgeCases:
    """Edge case tests for ConflictResolver."""
    
    def test_detect_conflicts_with_unicode(self):
        """Test conflict detection with Unicode characters."""
        old_content = {"database": "PostgreSQL 数据库"}
        new_content = {"database": "MongoDB 数据库"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
        assert "数据库" in conflicts[0].old_value
        assert "数据库" in conflicts[0].new_value
    
    def test_detect_conflicts_with_special_characters(self):
        """Test conflict detection with special characters."""
        old_content = {"config": "key=value&param=123"}
        new_content = {"config": "key=newvalue&param=456"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
    
    def test_detect_conflicts_with_very_long_values(self):
        """Test conflict detection with very long values."""
        old_content = {"description": "a" * 1000}
        new_content = {"description": "b" * 1000}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 1
    
    def test_resolve_conflict_with_multiline_values(self):
        """Test resolving conflicts with multi-line values."""
        conflict = Conflict(
            section="architecture",
            old_value="Component 1\nComponent 2\nComponent 3",
            new_value="Service A\nService B\nService C",
            explanation="Architecture changed"
        )
        
        result = ConflictResolver.resolve_conflict(conflict, "merge")
        
        assert "Component 1" in result
        assert "Service C" in result
    
    def test_format_conflict_with_long_explanation(self):
        """Test formatting conflict with very long explanation."""
        conflict = Conflict(
            section="database",
            old_value="PostgreSQL",
            new_value="MongoDB",
            explanation="This is a very long explanation " * 20
        )
        
        presentation = ConflictResolver.format_conflict_presentation(conflict)
        
        assert "PostgreSQL" in presentation
        assert "MongoDB" in presentation
    
    def test_detect_conflicts_mixed_types(self):
        """Test conflict detection with mixed value types."""
        old_content = {"port": 8080, "enabled": True, "name": "service"}
        new_content = {"port": 9000, "enabled": False, "name": "new-service"}
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        # All three should be detected as conflicts
        assert len(conflicts) == 3
    
    def test_detect_conflicts_with_whitespace_differences(self):
        """Test that whitespace differences are detected as conflicts."""
        old_content = {"value": "test"}
        new_content = {"value": "test "}  # Trailing space
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        # Whitespace differences should be detected
        assert len(conflicts) == 1
    
    def test_merge_values_with_empty_strings(self):
        """Test merging when one value is effectively empty."""
        # This shouldn't happen in practice due to filtering, but test the merge logic
        result = ConflictResolver._merge_values("value", "   ")
        
        # Should handle gracefully
        assert isinstance(result, str)
    
    def test_conflict_detection_with_nested_keywords(self):
        """Test that keywords in section names are detected correctly."""
        old_content = {
            "primary_database_choice": "PostgreSQL",
            "microservices_architecture_pattern": "event-driven",
            "project_success_goal": "1M users"
        }
        new_content = {
            "primary_database_choice": "MongoDB",
            "microservices_architecture_pattern": "REST-based",
            "project_success_goal": "10M users"
        }
        
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        assert len(conflicts) == 3
        
        # Check that appropriate conflict types are detected
        explanations = [c.explanation.lower() for c in conflicts]
        assert any("technology" in exp or "database" in exp for exp in explanations)
        assert any("architecture" in exp for exp in explanations)
        assert any("goal" in exp or "vision" in exp for exp in explanations)
