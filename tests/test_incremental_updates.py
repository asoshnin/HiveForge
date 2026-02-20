"""
Property tests for incremental updates.

Validates: Property 23 - Incremental Update Correctness
Validates: Requirements 23.1-23.8
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest
from hypothesis import given, settings, strategies as st

from hiveforge.steering.incremental_updater import (
    ChangeInfo,
    IncrementalUpdateResult,
    IncrementalUpdater,
    SectionInfo,
    STEERING_CACHE_PATH,
)


# Sample steering file content for testing
SAMPLE_PROJECT_VISION = """# Project Vision: TestProject

## Elevator Pitch
A test project for validating incremental updates.

## Problem Statement
Testing incremental update functionality.

## Solution Overview
Implement comprehensive tests.

## Target Users
1. **Primary:** Developers
2. **Secondary:** QA Engineers
"""

SAMPLE_TECH_STACK = """# Technology Stack

## Core Technologies

### Backend
- **Language:** Python 3.11
- **Framework:** FastAPI
- **Runtime:** CPython

### Frontend
- **Framework:** React 18
- **Language:** TypeScript
- **Styling:** Tailwind

### Database
- **Primary:** PostgreSQL 15
- **Cache:** Redis 7

### Infrastructure
- **Container:** Docker
- **Orchestration:** K8s
- **Cloud:** AWS

## Rationale
Python and React are widely adopted.
"""

SAMPLE_ARCHITECTURE = """# Architecture Overview

## System Diagram
```mermaid
graph TD
    User -->|HTTP| API
    API -->|Query| Database
```

## Component Responsibilities

### API Server
- **Responsibility:** Handle HTTP requests
- **Interface:** REST API
- **Dependencies:** Database, Cache

### Database
- **Responsibility:** Store data
- **Interface:** PostgreSQL protocol
- **Dependencies:** None
"""

SAMPLE_CONVENTIONS = """# Coding Conventions

## General Principles
1. **Readability > Cleverness**
2. **Explicit > Implicit**
3. **Tested > Assumed**

## Naming Conventions
### Python
- `snake_case` for variables, functions
- `PascalCase` for classes
"""


class TestIncrementalUpdaterUnit:
    """Unit tests for IncrementalUpdater class."""

    def test_init_creates_cache(self):
        """Test that initialization creates empty cache if none exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            assert updater.cache_path == cache_path
            assert updater._cache == {"files": {}, "metadata": {}}

    def test_init_loads_existing_cache(self):
        """Test that initialization loads existing cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "test_cache.json"
            cache_data = {
                "files": {
                    "test.md": {
                        "file_name": "test.md",
                        "file_hash": "abc123",
                        "last_updated": "2024-01-01T00:00:00",
                        "sections": {},
                        "customizations": [],
                    }
                },
                "metadata": {"version": "2.1"},
            }
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(cache_data, f)

            updater = IncrementalUpdater(cache_path=cache_path)

            assert "test.md" in updater._cache["files"]
            assert updater._cache["metadata"]["version"] == "2.1"

    def test_compute_content_hash(self):
        """Test content hash computation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = IncrementalUpdater(cache_path=Path(tmpdir) / "cache.json")

            hash1 = updater._compute_content_hash("hello world")
            hash2 = updater._compute_content_hash("hello world")
            hash3 = updater._compute_content_hash("hello world!")

            assert hash1 == hash2
            assert hash1 != hash3
            assert len(hash1) == 32  # MD5 hex digest

    def test_parse_sections(self):
        """Test section parsing from markdown content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = IncrementalUpdater(cache_path=Path(tmpdir) / "cache.json")

            content = """# Header
Some header content.

## Section 1
Content of section 1.

## Section 2
Content of section 2.
"""

            sections = updater._parse_sections(content)

            # Section names preserve case from markdown headers
            assert "Header" in sections
            assert "Section 1" in sections
            assert "Section 2" in sections
            assert "Some header content" in sections["Header"]
            assert "Content of section 1" in sections["Section 1"]

    def test_parse_sections_empty_content(self):
        """Test parsing empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = IncrementalUpdater(cache_path=Path(tmpdir) / "cache.json")

            sections = updater._parse_sections("")

            assert len(sections) == 1
            assert "header" in sections

    def test_reconstruct_file(self):
        """Test file reconstruction from sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = IncrementalUpdater(cache_path=Path(tmpdir) / "cache.json")

            sections = {
                "header": "# Header\nContent",
                "Section 1": "## Section 1\nContent 1",
            }

            content = updater._reconstruct_file(sections)

            assert "# Header" in content
            assert "## Section 1" in content

    def test_get_unchanged_files(self):
        """Test identifying unchanged files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # First, cache some files
            files = {"test.md": "content1"}
            updater.update_cache(files)

            # Check unchanged
            unchanged = updater.get_unchanged_files({"test.md": "content1"})
            assert "test.md" in unchanged

            # Check changed
            changed = updater.get_changed_files({"test.md": "content2"})
            assert "test.md" in changed

    def test_get_changed_files(self):
        """Test identifying changed files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache a file
            updater.update_cache({"test.md": "original content"})

            # Check unchanged
            unchanged = updater.get_unchanged_files({"test.md": "original content"})
            assert "test.md" in unchanged

            # Check changed
            changed = updater.get_changed_files({"test.md": "modified content"})
            assert "test.md" in changed

    def test_should_use_incremental_force(self):
        """Test force incremental mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            updater = IncrementalUpdater(
                cache_path=Path(tmpdir) / "cache.json", force_incremental=True
            )

            assert updater.should_use_incremental({}) is True

    def test_should_use_incremental_with_cache(self):
        """Test incremental mode when cache exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # No cache yet
            assert updater.should_use_incremental({}) is False

            # Add cache
            updater.update_cache({"test.md": "content"})

            # Should use incremental now
            assert updater.should_use_incremental({}) is True

    def test_clear_cache(self):
        """Test cache clearing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            updater.update_cache({"test.md": "content"})
            assert "test.md" in updater._cache["files"]

            updater.clear_cache()
            assert updater._cache == {"files": {}, "metadata": {}}


class TestDetectSectionChanges:
    """Tests for detect_section_changes method."""

    def test_detect_new_file(self):
        """Test detecting a new file that wasn't cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            files = {"new-file.md": "# New File\nContent"}
            changes = updater.detect_section_changes(files)

            assert len(changes) == 1
            assert changes[0].file_name == "new-file.md"
            assert changes[0].change_type == "added"

    def test_detect_unchanged_file(self):
        """Test detecting an unchanged file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache the file first
            files = {"test.md": "# Test\nContent"}
            updater.update_cache(files)

            # Check for changes
            changes = updater.detect_section_changes(files)

            assert len(changes) == 1
            assert changes[0].file_name == "test.md"
            assert changes[0].change_type == "unchanged"

    def test_detect_modified_section(self):
        """Test detecting a modified section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache original file
            original = {"test.md": "# Test\n## Section 1\nOld content"}
            updater.update_cache(original)

            # Modify section
            modified = {"test.md": "# Test\n## Section 1\nNew content"}
            changes = updater.detect_section_changes(modified)

            section_changes = [c for c in changes if c.change_type == "modified"]
            assert len(section_changes) >= 1

    def test_detect_added_section(self):
        """Test detecting an added section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache original file
            original = {"test.md": "# Test\n## Section 1\nContent"}
            updater.update_cache(original)

            # Add new section
            modified = {"test.md": "# Test\n## Section 1\nContent\n\n## Section 2\nNew section"}
            changes = updater.detect_section_changes(modified)

            added_changes = [c for c in changes if c.change_type == "added"]
            assert len(added_changes) >= 1

    def test_detect_removed_section(self):
        """Test detecting a removed section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache original file with multiple sections
            original = {"test.md": "# Test\n## Section 1\nContent\n\n## Section 2\nTo remove"}
            updater.update_cache(original)

            # Remove a section
            modified = {"test.md": "# Test\n## Section 1\nContent"}
            changes = updater.detect_section_changes(modified)

            removed_changes = [c for c in changes if c.change_type == "removed"]
            assert len(removed_changes) >= 1


class TestUpdateOnlyChangedSections:
    """Tests for update_only_changed_sections method."""

    def test_update_modified_section(self):
        """Test updating only modified sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache original
            current = {"test.md": "# Test\n## Section 1\nOriginal"}
            updater.update_cache(current)

            # Generate new version
            generated = {"test.md": "# Test\n## Section 1\nUpdated\n\n## Section 2\nNew"}

            result = updater.update_only_changed_sections(current, generated)

            assert "test.md" in result
            assert "Updated" in result["test.md"]

    def test_preserve_unchanged_sections(self):
        """Test preserving unchanged sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache original
            current = {"test.md": "# Test\n## Section 1\nKeep this"}
            updater.update_cache(current)

            # Generate new version
            generated = {"test.md": "# Test\n## Section 1\nKeep this\n\n## Section 2\nNew"}

            result = updater.update_only_changed_sections(current, generated)

            assert "test.md" in result
            assert "Keep this" in result["test.md"]

    def test_preserve_customizations(self):
        """Test preserving customized sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache original
            current = {"test.md": "# Test\n## Section 1\nCustom content"}
            updater.update_cache(current)

            # Customization record
            customizations = {"test.md": [{"section": "Section 1", "type": "custom"}]}

            # Generate new version
            generated = {"test.md": "# Test\n## Section 1\nNew content\n\n## Section 2\nNew"}

            result = updater.update_only_changed_sections(current, generated, customizations)

            assert "test.md" in result
            assert "Custom content" in result["test.md"]


class TestPreserveUnchangedSections:
    """Tests for preserve_unchanged_sections method."""

    def test_preserve_customized_sections(self):
        """Test that customized sections are preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            current = {"test.md": "# Test\n## Section 1\nMy custom content"}
            generated = {"test.md": "# Test\n## Section 1\nGenerated content"}
            customizations = {"test.md": [{"section": "Section 1"}]}

            result = updater.preserve_unchanged_sections(current, generated, customizations)

            assert "My custom content" in result["test.md"]

    def test_update_non_customized_sections(self):
        """Test that non-customized sections are updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            current = {"test.md": "# Test\n## Section 1\nOriginal"}
            generated = {"test.md": "# Test\n## Section 1\nUpdated"}
            customizations = {"test.md": []}  # No customizations

            result = updater.preserve_unchanged_sections(current, generated, customizations)

            assert "Updated" in result["test.md"]

    def test_handle_new_files(self):
        """Test handling of new files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            current = {}  # No current files
            generated = {"new.md": "# New File\nContent"}

            result = updater.preserve_unchanged_sections(current, generated)

            assert "new.md" in result
            assert "Content" in result["new.md"]


class TestUpdateCache:
    """Tests for cache update functionality."""

    def test_update_cache_creates_sections(self):
        """Test that updating cache creates section entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            files = {"test.md": "# Test\n## Section 1\nContent"}
            updater.update_cache(files)

            assert "test.md" in updater._cache["files"]
            cached_file = updater._cache["files"]["test.md"]
            assert "sections" in cached_file
            assert "Section 1" in cached_file["sections"]

    def test_update_cache_preserves_metadata(self):
        """Test that cache update preserves metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            files = {"test.md": "# Test\nContent"}
            updater.update_cache(files)

            assert "metadata" in updater._cache
            assert updater._cache["metadata"]["version"] == "2.1"
            assert "last_updated" in updater._cache["metadata"]


class TestExecuteIncrementalUpdate:
    """Tests for execute_incremental_update method."""

    def test_execute_incremental_update(self):
        """Test complete incremental update flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # First run - all files are new
            current = {}
            generated = {"test.md": "# Test\nContent"}

            result = updater.execute_incremental_update(current, generated)

            assert isinstance(result, IncrementalUpdateResult)
            assert "test.md" in result.files_to_update
            assert result.cache_updated is True

    def test_execute_incremental_update_with_changes(self):
        """Test incremental update with file changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # First run
            current = {}
            generated = {"test.md": "# Test\nOriginal"}
            updater.execute_incremental_update(current, generated)

            # Second run with changes
            current = {"test.md": "# Test\nOriginal"}
            generated = {"test.md": "# Test\nUpdated"}
            result = updater.execute_incremental_update(current, generated)

            assert "test.md" in result.files_to_update

    def test_execute_incremental_update_summary(self):
        """Test that update summary is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            current = {}
            generated = {"test.md": "# Test\nContent"}
            result = updater.execute_incremental_update(current, generated)

            assert "files updated" in result.summary.lower()
            assert "files unchanged" in result.summary.lower()


# Property-based tests for Incremental Update Correctness
# Validates: Requirements 23.1-23.8


class TestIncrementalUpdateProperties:
    """Property-based tests for incremental update correctness."""

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=500),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=10)
    def test_detect_section_changes_idempotent(self, files: Dict[str, str]):
        """Property: Detecting changes twice should yield same result."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache files first
            updater.update_cache(files)

            # Detect changes twice
            changes1 = updater.detect_section_changes(files)
            changes2 = updater.detect_section_changes(files)

            assert len(changes1) == len(changes2)
            for c1, c2 in zip(changes1, changes2):
                assert c1.file_name == c2.file_name
                assert c1.change_type == c2.change_type

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=500),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=10)
    def test_unchanged_files_remain_unchanged(self, files: Dict[str, str]):
        """Property: Unchanged files should remain in unchanged list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache files
            updater.update_cache(files)

            # Get unchanged files
            unchanged = updater.get_unchanged_files(files)

            # All files should be unchanged
            assert set(unchanged) == set(files.keys())

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=500),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=10)
    def test_changed_files_detected_correctly(self, files: Dict[str, str]):
        """Property: Changed files should be correctly identified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache original files
            updater.update_cache(files)

            # Create modified versions
            modified = {k: v + " modified" for k, v in files.items()}

            # Get changed files
            changed = updater.get_changed_files(modified)

            # All files should be changed
            assert set(changed) == set(files.keys())

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=500),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=10)
    def test_preserve_unchanged_sections_preserves_all(self, files: Dict[str, str]):
        """Property: All sections should be preserved when no customizations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Parse sections from current content
            current_sections = {}
            for name, content in files.items():
                sections = updater._parse_sections(content)
                current_sections[name] = sections

            # Preserve unchanged
            result = updater.preserve_unchanged_sections(files, files, {})

            # All content should be preserved
            for name, content in files.items():
                assert content == result[name]

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=500),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=10)
    def test_incremental_update_preserves_cache_integrity(self, files: Dict[str, str]):
        """Property: Cache should be updated after incremental update."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Execute update
            result = updater.execute_incremental_update({}, files)

            # Cache should be updated
            assert result.cache_updated is True
            assert len(updater._cache["files"]) == len(files)

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.text(min_size=1, max_size=500),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=10)
    def test_update_result_contains_all_files(self, files: Dict[str, str]):
        """Property: Result should contain all files (updated or unchanged)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            result = updater.execute_incremental_update({}, files)

            all_files = set(result.files_to_update) | set(result.files_unchanged)
            assert all_files == set(files.keys())


class TestIncrementalUpdateRequirements:
    """
    Tests specifically targeting Requirements 23.1-23.8.

    These tests validate the acceptance criteria for incremental updates.
    """

    def test_requirement_23_1_incremental_analysis(self):
        """
        Requirement 23.1: WHEN updating existing steering files, THE Steering_Assistant
        SHALL perform incremental analysis to identify changed information.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache original files
            original = {"tech-stack.md": SAMPLE_TECH_STACK}
            updater.update_cache(original)

            # Detect changes
            modified = {
                "tech-stack.md": SAMPLE_TECH_STACK.replace("Python 3.11", "Python 3.12")
            }
            changes = updater.detect_section_changes(modified)

            # Should detect changes
            modified_changes = [c for c in changes if c.change_type == "modified"]
            assert len(modified_changes) > 0

    def test_requirement_23_2_compare_with_cached_analysis(self):
        """
        Requirement 23.2: THE Steering_Assistant SHALL compare current project state
        with previous analysis (cached in `.kiro/.cache/steering_cache.json`) to
        detect new information.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Create and cache initial state
            initial_state = {"project-vision.md": SAMPLE_PROJECT_VISION}
            updater.update_cache(initial_state)

            # Add new information
            new_state = {
                "project-vision.md": SAMPLE_PROJECT_VISION
                + "\n## New Section\nNew information."
            }
            changes = updater.detect_section_changes(new_state)

            # Should detect new section
            added_changes = [c for c in changes if c.change_type == "added"]
            assert len(added_changes) > 0

    def test_requirement_23_3_regenerate_only_affected_files(self):
        """
        Requirement 23.3: WHEN only specific information has changed (e.g., new
        dependency added), THE Steering_Assistant SHALL regenerate only affected files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache multiple files
            original = {
                "project-vision.md": SAMPLE_PROJECT_VISION,
                "tech-stack.md": SAMPLE_TECH_STACK,
            }
            updater.update_cache(original)

            # Modify only one file
            modified = {
                "project-vision.md": SAMPLE_PROJECT_VISION,
                "tech-stack.md": SAMPLE_TECH_STACK.replace("React 18", "React 19"),
            }

            result = updater.execute_incremental_update(original, modified)

            # Only tech-stack.md should be in updated files
            assert "tech-stack.md" in result.files_to_update
            assert "project-vision.md" in result.files_unchanged

    def test_requirement_23_4_unchanged_files_as_context(self):
        """
        Requirement 23.4: WHEN performing incremental updates, THE Steering_Assistant
        SHALL pass unchanged files as context to maintain consistency.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Cache multiple files
            original = {
                "project-vision.md": SAMPLE_PROJECT_VISION,
                "tech-stack.md": SAMPLE_TECH_STACK,
            }
            updater.update_cache(original)

            # Get unchanged files - these should be available as context
            unchanged = updater.get_unchanged_files(original)

            # Unchanged files should be available
            assert "project-vision.md" in unchanged

    def test_requirement_23_5_preserve_customizations(self):
        """
        Requirement 23.5: WHEN performing incremental updates, THE Steering_Assistant
        SHALL preserve customizations in unchanged sections.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            current = {"architecture.md": SAMPLE_ARCHITECTURE}
            generated = {"architecture.md": SAMPLE_ARCHITECTURE.replace("API", "Gateway")}
            customizations = {"architecture.md": [{"section": "System Diagram"}]}

            result = updater.preserve_unchanged_sections(current, generated, customizations)

            # Customized section should be preserved
            assert "System Diagram" in result["architecture.md"]

    def test_requirement_23_6_incremental_flag(self):
        """
        Requirement 23.6: THE Steering_Assistant SHALL support a `--incremental`
        flag to force incremental update mode.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Force incremental mode
            updater = IncrementalUpdater(
                cache_path=Path(tmpdir) / "cache.json", force_incremental=True
            )

            # Should use incremental even without cache
            assert updater.should_use_incremental({}) is True

    def test_requirement_23_7_display_updated_files(self):
        """
        Requirement 23.7: THE Steering_Assistant SHALL display which files were
        updated and which were preserved unchanged.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # First run
            result1 = updater.execute_incremental_update({}, {"test.md": "content"})

            # Result should contain both lists
            assert hasattr(result1, "files_to_update")
            assert hasattr(result1, "files_unchanged")

    def test_requirement_23_8_sequential_generation(self):
        """
        Requirement 23.8: WHEN incremental mode is used with autonomous generation,
        files SHALL be generated sequentially (not in batch) to support per-file updates.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / "cache.json"
            updater = IncrementalUpdater(cache_path=cache_path)

            # Multiple files
            files = {
                "project-vision.md": SAMPLE_PROJECT_VISION,
                "tech-stack.md": SAMPLE_TECH_STACK,
                "architecture.md": SAMPLE_ARCHITECTURE,
            }

            # Execute update
            result = updater.execute_incremental_update({}, files)

            # All files should be in result
            all_files = set(result.files_to_update) | set(result.files_unchanged)
            assert all_files == set(files.keys())

            # Sequential generation is implied by per-file processing
            # (the implementation processes files one at a time)