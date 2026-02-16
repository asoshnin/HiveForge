"""
Property-based tests for conflict detection.

Validates: Requirements 6.1-6.8, 19.1-19.7
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.conflict_resolver import ConflictResolver


class TestConflictDetection:
    """Tests for conflict detection behavior."""
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_detect_direct_conflicts(self):
        """
        WHEN analyzing drafts, direct contradictions SHALL be detected (Python vs JavaScript).
        """
        old_content = {"backend": "Python"}
        new_content = {"backend": "JavaScript"}
        
        conflicts = ConflictResolver.detect_direct_conflicts(old_content, new_content)
        
        assert len(conflicts) >= 1
        assert conflicts[0].section == "backend"
        assert conflicts[0].old_value == "Python"
        assert conflicts[0].new_value == "JavaScript"
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_detect_implicit_conflicts_microservices_monolithic(self):
        """
        WHEN analyzing drafts, implicit contradictions SHALL be detected (microservices vs monolithic).
        """
        old_content = {"architecture": "microservices"}
        new_content = {"architecture": "monolithic"}
        
        conflicts = ConflictResolver.detect_implicit_conflicts(old_content, new_content)
        
        assert len(conflicts) >= 1
        assert "microservices" in str(conflicts[0].old_value).lower() or \
               "monolithic" in str(conflicts[0].old_value).lower()
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_detect_version_conflicts(self):
        """
        WHEN analyzing drafts, version mismatches SHALL be detected.
        """
        old_content = {"framework": "React 17.0"}
        new_content = {"framework": "React 18.0"}
        
        conflicts = ConflictResolver.detect_version_conflicts(old_content, new_content)
        
        assert len(conflicts) >= 1
        assert "17.0" in str(conflicts[0].old_value)
        assert "18.0" in str(conflicts[0].new_value)
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_calculate_conflict_confidence(self):
        """
        WHEN conflicts are detected, high-confidence conflicts SHALL be presented to users.
        """
        conflict = ConflictResolver._analyze_conflict(
            "backend",
            "Python",
            "JavaScript",
        )
        
        confidence = ConflictResolver.calculate_conflict_confidence(conflict)
        
        assert 0.9 <= confidence <= 1.0
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_present_side_by_side(self):
        """
        WHEN conflicts are detected, side-by-side comparisons SHALL be shown with evidence.
        """
        conflict = ConflictResolver._analyze_conflict(
            "backend",
            "Python",
            "JavaScript",
        )
        
        presentation = ConflictResolver.format_conflict_presentation(conflict)
        
        assert "CONFLICT in section: backend" in presentation
        assert "Python" in presentation
        assert "JavaScript" in presentation
        assert "Resolution options" in presentation
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_batch_conflicts(self):
        """
        WHEN multiple conflicts are detected, they SHALL be grouped together.
        """
        conflicts = [
            ConflictResolver._analyze_conflict("backend", "Python", "JavaScript"),
            ConflictResolver._analyze_conflict("database", "PostgreSQL", "MongoDB"),
        ]
        
        batches = ConflictResolver.batch_conflicts(conflicts)
        
        assert "backend" in batches
        assert "database" in batches
        assert len(batches["backend"]) == 1
        assert len(batches["database"]) == 1
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_present_batch_view(self):
        """
        WHEN batch view is presented, multiple conflicts SHALL be shown together.
        """
        conflicts = [
            ConflictResolver._analyze_conflict("backend", "Python", "JavaScript"),
            ConflictResolver._analyze_conflict("database", "PostgreSQL", "MongoDB"),
        ]
        
        batches = ConflictResolver.batch_conflicts(conflicts)
        presentation = ConflictResolver.present_batch_view(batches)
        
        assert "BATCH CONFLICT RESOLUTION" in presentation
        assert "BACKEND" in presentation
        assert "DATABASE" in presentation
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_apply_batch_resolution(self):
        """
        WHEN batch resolution is enabled, same resolution strategy SHALL be applicable to similar conflicts.
        """
        conflicts = [
            ConflictResolver._analyze_conflict("backend", "Python", "JavaScript"),
            ConflictResolver._analyze_conflict("database", "PostgreSQL", "MongoDB"),
        ]
        
        # Apply "use_all_new" strategy
        resolved = ConflictResolver.apply_batch_resolution(conflicts, "use_all_new")
        
        assert len(resolved) == 2
        assert resolved[0] == "JavaScript"
        assert resolved[1] == "MongoDB"
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    def test_skip_conflicts(self):
        """
        WHEN conflicts are skipped, they SHALL be resolvable later.
        """
        conflicts = [
            ConflictResolver._analyze_conflict("backend", "Python", "JavaScript"),
        ]
        
        skipped = ConflictResolver.skip_conflicts(conflicts)
        
        assert len(skipped) == 1
        assert skipped[0].section == "backend"
    
    @pytest.mark.property("Property 6: Conflict Detection Precision")
    @pytest.mark.property("Property 19: Batch Conflict Resolution")
    @given(st.text(min_size=1, max_size=100))
    def test_conflict_detection_with_random_content(self, content: str):
        """
        Property: Conflict Detection Precision
        For any content, conflict detection should not crash.
        """
        old_content = {"section": content}
        new_content = {"section": "other content"}
        
        # Should not raise any exceptions
        conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
        
        # Result should be a list
        assert isinstance(conflicts, list)
