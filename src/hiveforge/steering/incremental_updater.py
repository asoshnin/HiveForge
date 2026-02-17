"""
Incremental update functionality for steering files.

This module provides per-section incremental updates to avoid regenerating
entire files when only specific information has changed. It uses section-level
caching to track changes and preserve customizations.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Set


# Cache file path for steering analysis
STEERING_CACHE_PATH = Path(".kiro/.cache/steering_cache.json")


@dataclass
class SectionInfo:
    """Information about a section in a steering file."""

    file_name: str
    section_name: str
    content_hash: str
    last_updated: datetime
    content: str
    is_customized: bool = False
    confidence: float = 1.0


@dataclass
class FileInfo:
    """Information about a steering file."""

    file_name: str
    file_hash: str
    last_updated: datetime
    sections: Dict[str, SectionInfo] = field(default_factory=dict)
    customizations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ChangeInfo:
    """Information about a detected change."""

    file_name: str
    section_name: Optional[str]
    change_type: str  # "added", "modified", "removed", "unchanged"
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    confidence: float = 1.0


@dataclass
class IncrementalUpdateResult:
    """Result of an incremental update operation."""

    files_to_update: List[str]
    files_unchanged: List[str]
    changes_detected: List[ChangeInfo]
    customizations_preserved: List[Dict[str, Any]]
    cache_updated: bool
    summary: str


class IncrementalUpdater:
    """
    Handles incremental updates for steering files.

    This class detects changes at the section level (not just file level),
    preserves customizations in unchanged sections, and uses caching to
    avoid unnecessary regeneration.

    Attributes:
        cache_path: Path to the steering cache file.
        force_incremental: Whether to force incremental mode even when not optimal.
    """

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        force_incremental: bool = False,
    ):
        """
        Initialize the IncrementalUpdater.

        Args:
            cache_path: Path to the steering cache file. Defaults to steering_cache.json.
            force_incremental: Whether to force incremental mode.
        """
        self.cache_path = cache_path or STEERING_CACHE_PATH
        self.force_incremental = force_incremental
        self._cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load the cache from disk if it exists."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache = {"files": {}, "metadata": {}}
        else:
            self._cache = {"files": {}, "metadata": {}}

    def _save_cache(self) -> None:
        """Save the cache to disk."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, indent=2, default=str)

    def _compute_content_hash(self, content: str) -> str:
        """
        Compute a hash of the content for change detection.

        Args:
            content: The content to hash.

        Returns:
            MD5 hash of the content.
        """
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """
        Parse a steering file into sections.

        Args:
            content: The file content to parse.

        Returns:
            Dictionary mapping section names to section content.
        """
        sections = {}
        lines = content.split("\n")
        current_section = "header"
        current_content = []

        for line in lines:
            if line.startswith("#"):
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line.lstrip("# ").strip()
                current_content = [line]
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def detect_section_changes(
        self,
        current_files: Dict[str, str],
        customizations: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> List[ChangeInfo]:
        """
        Identify changed sections by comparing current state with cached analysis.

        Args:
            current_files: Dictionary mapping file names to current content.
            customizations: Optional dictionary of customizations per file.

        Returns:
            List of ChangeInfo objects describing detected changes.
        """
        changes = []
        cached_files = self._cache.get("files", {})
        customizations = customizations or {}

        for file_name, current_content in current_files.items():
            current_hash = self._compute_content_hash(current_content)
            current_sections = self._parse_sections(current_content)

            if file_name in cached_files:
                cached_file = cached_files[file_name]
                cached_hash = cached_file.get("file_hash", "")
                cached_sections = cached_file.get("sections", {})

                if current_hash != cached_hash:
                    # File has changed, check which sections
                    for section_name, section_content in current_sections.items():
                        section_hash = self._compute_content_hash(section_content)

                        if section_name in cached_sections:
                            cached_section = cached_sections[section_name]
                            cached_section_hash = cached_section.get("content_hash", "")

                            if section_hash != cached_section_hash:
                                # Section modified
                                old_content = cached_section.get("content", "")
                                is_customized = any(
                                    c.get("section") == section_name
                                    for c in customizations.get(file_name, [])
                                )
                                changes.append(
                                    ChangeInfo(
                                        file_name=file_name,
                                        section_name=section_name,
                                        change_type="modified",
                                        old_content=old_content,
                                        new_content=section_content,
                                        confidence=0.9 if not is_customized else 0.7,
                                    )
                                )
                            else:
                                # Section unchanged
                                changes.append(
                                    ChangeInfo(
                                        file_name=file_name,
                                        section_name=section_name,
                                        change_type="unchanged",
                                        confidence=1.0,
                                    )
                                )
                        else:
                            # New section
                            changes.append(
                                ChangeInfo(
                                    file_name=file_name,
                                    section_name=section_name,
                                    change_type="added",
                                    new_content=section_content,
                                    confidence=0.8,
                                )
                            )

                    # Check for removed sections
                    for section_name in cached_sections:
                        if section_name not in current_sections:
                            cached_section = cached_sections[section_name]
                            changes.append(
                                ChangeInfo(
                                    file_name=file_name,
                                    section_name=section_name,
                                    change_type="removed",
                                    old_content=cached_section.get("content", ""),
                                    confidence=0.9,
                                )
                            )
                else:
                    # File unchanged
                    for section_name in current_sections:
                        changes.append(
                            ChangeInfo(
                                file_name=file_name,
                                section_name=section_name,
                                change_type="unchanged",
                                confidence=1.0,
                            )
                        )
            else:
                # New file - mark entire file as added
                changes.append(
                    ChangeInfo(
                        file_name=file_name,
                        section_name=None,
                        change_type="added",
                        new_content=current_content,
                        confidence=0.8,
                    )
                )

        return changes

    def update_only_changed_sections(
        self,
        current_files: Dict[str, str],
        generated_files: Dict[str, str],
        customizations: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Dict[str, str]:
        """
        Update only the sections that have changed.

        Args:
            current_files: Dictionary mapping file names to current content.
            generated_files: Dictionary mapping file names to newly generated content.
            customizations: Optional dictionary of customizations per file.

        Returns:
            Dictionary mapping file names to updated content.
        """
        customizations = customizations or {}
        updated_files = {}

        # Group changes by file - compare generated with cache to detect changes
        file_changes: Dict[str, List[ChangeInfo]] = {}
        for file_name, generated_content in generated_files.items():
            changes = self._detect_changes_for_file(file_name, generated_content, customizations)
            file_changes[file_name] = changes

        for file_name, generated_content in generated_files.items():
            changes = file_changes.get(file_name, [])
            has_changes = any(c.change_type != "unchanged" for c in changes)

            if not has_changes:
                # No changes, keep current content if exists
                if file_name in current_files:
                    updated_files[file_name] = current_files[file_name]
                else:
                    # New file, use generated content
                    updated_files[file_name] = generated_content
                continue

            if file_name in current_files:
                # Merge changes into current file
                current_content = current_files[file_name]
                current_sections = self._parse_sections(current_content)
                generated_sections = self._parse_sections(generated_content)

                for change in changes:
                    if change.section_name is None:
                        continue

                    # Check if section is customized
                    is_customized = any(
                        c.get("section") == change.section_name
                        for c in customizations.get(file_name, [])
                    )

                    if is_customized:
                        # Preserve customization, don't update
                        continue
                    elif change.new_content and change.change_type in ("added", "modified"):
                        # Update section with new content from generated
                        if change.section_name in generated_sections:
                            current_sections[change.section_name] = generated_sections[change.section_name]

                # Reconstruct file
                updated_content = self._reconstruct_file(current_sections)
                updated_files[file_name] = updated_content
            else:
                # New file, use generated content
                updated_files[file_name] = generated_content

        return updated_files

    def _detect_changes_for_file(
        self,
        file_name: str,
        generated_content: str,
        customizations: Dict[str, List[Dict[str, Any]]],
    ) -> List[ChangeInfo]:
        """
        Detect changes for a single file by comparing generated content with cache.

        Args:
            file_name: Name of the file.
            generated_content: The newly generated content.
            customizations: Dictionary of customizations per file.

        Returns:
            List of ChangeInfo objects for the file.
        """
        changes = []
        cached_files = self._cache.get("files", {})

        generated_hash = self._compute_content_hash(generated_content)
        generated_sections = self._parse_sections(generated_content)

        if file_name in cached_files:
            cached_file = cached_files[file_name]
            cached_hash = cached_file.get("file_hash", "")
            cached_sections = cached_file.get("sections", {})

            if generated_hash != cached_hash:
                # File has changed, check which sections
                for section_name, section_content in generated_sections.items():
                    section_hash = self._compute_content_hash(section_content)

                    if section_name in cached_sections:
                        cached_section = cached_sections[section_name]
                        cached_section_hash = cached_section.get("content_hash", "")

                        if section_hash != cached_section_hash:
                            # Section modified
                            old_content = cached_section.get("content", "")
                            is_customized = any(
                                c.get("section") == section_name
                                for c in customizations.get(file_name, [])
                            )
                            changes.append(
                                ChangeInfo(
                                    file_name=file_name,
                                    section_name=section_name,
                                    change_type="modified",
                                    old_content=old_content,
                                    new_content=section_content,
                                    confidence=0.9 if not is_customized else 0.7,
                                )
                            )
                        else:
                            # Section unchanged
                            changes.append(
                                ChangeInfo(
                                    file_name=file_name,
                                    section_name=section_name,
                                    change_type="unchanged",
                                    confidence=1.0,
                                )
                            )
                    else:
                        # New section
                        changes.append(
                            ChangeInfo(
                                file_name=file_name,
                                section_name=section_name,
                                change_type="added",
                                new_content=section_content,
                                confidence=0.8,
                            )
                        )

                # Check for removed sections
                for section_name in cached_sections:
                    if section_name not in generated_sections:
                        cached_section = cached_sections[section_name]
                        changes.append(
                            ChangeInfo(
                                file_name=file_name,
                                section_name=section_name,
                                change_type="removed",
                                old_content=cached_section.get("content", ""),
                                confidence=0.9,
                            )
                        )
            else:
                # File unchanged
                for section_name in generated_sections:
                    changes.append(
                        ChangeInfo(
                            file_name=file_name,
                            section_name=section_name,
                            change_type="unchanged",
                            confidence=1.0,
                        )
                    )
        else:
            # New file - mark entire file as added
            for section_name, section_content in generated_sections.items():
                changes.append(
                    ChangeInfo(
                        file_name=file_name,
                        section_name=section_name,
                        change_type="added",
                        new_content=section_content,
                        confidence=0.8,
                    )
                )

        return changes

    def _reconstruct_file(self, sections: Dict[str, str]) -> str:
        """
        Reconstruct a file from parsed sections.

        Args:
            sections: Dictionary mapping section names to section content.

        Returns:
            Reconstructed file content.
        """
        if not sections:
            return ""

        # Sort sections: header first, then others alphabetically
        sorted_sections = []
        header = sections.get("header") or sections.get("Header")
        if header:
            sorted_sections.append((None, header))  # None key sorts first

        for name, content in sorted(sections.items()):
            if name not in ("header", "Header"):
                sorted_sections.append((name, content))

        # Join sections with double newline
        return "\n\n".join(content for _, content in sorted_sections)

    def preserve_unchanged_sections(
        self,
        current_files: Dict[str, str],
        generated_files: Dict[str, str],
        customizations: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Dict[str, str]:
        """
        Preserve unchanged content and customizations.

        Args:
            current_files: Dictionary mapping file names to current content.
            generated_files: Dictionary mapping file names to newly generated content.
            customizations: Optional dictionary of customizations per file.

        Returns:
            Dictionary mapping file names to content with preserved sections.
        """
        customizations = customizations or {}
        preserved_files = {}

        for file_name, generated_content in generated_files.items():
            if file_name in current_files:
                current_content = current_files[file_name]
                current_sections = self._parse_sections(current_content)
                generated_sections = self._parse_sections(generated_content)

                preserved_sections = {}

                for section_name, generated_section in generated_sections.items():
                    if section_name in current_sections:
                        # Check if section is customized
                        is_customized = any(
                            c.get("section") == section_name
                            for c in customizations.get(file_name, [])
                        )

                        if is_customized:
                            # Preserve current content for customized sections
                            preserved_sections[section_name] = current_sections[
                                section_name
                            ]
                        else:
                            # Use generated content
                            preserved_sections[section_name] = generated_section
                    else:
                        # New section, use generated content
                        preserved_sections[section_name] = generated_section

                preserved_files[file_name] = self._reconstruct_file(preserved_sections)
            else:
                # New file, use generated content
                preserved_files[file_name] = generated_content

        return preserved_files

    def update_cache(
        self,
        files: Dict[str, str],
        customizations: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> None:
        """
        Update the cache with current file state.

        Args:
            files: Dictionary mapping file names to content.
            customizations: Optional dictionary of customizations per file.
        """
        customizations = customizations or {}
        cached_files = self._cache.get("files", {})

        for file_name, content in files.items():
            file_hash = self._compute_content_hash(content)
            sections = self._parse_sections(content)

            section_infos = {}
            for section_name, section_content in sections.items():
                section_hash = self._compute_content_hash(section_content)
                is_customized = any(
                    c.get("section") == section_name
                    for c in customizations.get(file_name, [])
                )

                section_infos[section_name] = {
                    "file_name": file_name,
                    "section_name": section_name,
                    "content_hash": section_hash,
                    "last_updated": datetime.now().isoformat(),
                    "content": section_content,
                    "is_customized": is_customized,
                    "confidence": 0.7 if is_customized else 1.0,
                }

            cached_files[file_name] = {
                "file_name": file_name,
                "file_hash": file_hash,
                "last_updated": datetime.now().isoformat(),
                "sections": section_infos,
                "customizations": customizations.get(file_name, []),
            }

        self._cache["files"] = cached_files
        self._cache["metadata"] = {
            "last_updated": datetime.now().isoformat(),
            "version": "2.1",
        }
        self._save_cache()

    def get_unchanged_files(self, files: Dict[str, str]) -> List[str]:
        """
        Get list of files that haven't changed since last cache.

        Args:
            files: Dictionary mapping file names to content.

        Returns:
            List of file names that are unchanged.
        """
        unchanged = []
        cached_files = self._cache.get("files", {})

        for file_name, content in files.items():
            if file_name in cached_files:
                cached_hash = cached_files[file_name].get("file_hash", "")
                current_hash = self._compute_content_hash(content)

                if current_hash == cached_hash:
                    unchanged.append(file_name)

        return unchanged

    def get_changed_files(self, files: Dict[str, str]) -> List[str]:
        """
        Get list of files that have changed since last cache.

        Args:
            files: Dictionary mapping file names to content.

        Returns:
            List of file names that have changed.
        """
        changed = []
        cached_files = self._cache.get("files", {})

        for file_name, content in files.items():
            if file_name not in cached_files:
                changed.append(file_name)
            else:
                cached_hash = cached_files[file_name].get("file_hash", "")
                current_hash = self._compute_content_hash(content)

                if current_hash != cached_hash:
                    changed.append(file_name)

        return changed

    def execute_incremental_update(
        self,
        current_files: Dict[str, str],
        generated_files: Dict[str, str],
        customizations: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> IncrementalUpdateResult:
        """
        Execute a complete incremental update operation.

        Args:
            current_files: Dictionary mapping file names to current content.
            generated_files: Dictionary mapping file names to newly generated content.
            customizations: Optional dictionary of customizations per file.

        Returns:
            IncrementalUpdateResult with details of the update.
        """
        customizations = customizations or {}

        # Detect changes by comparing generated files with cache
        all_changes: List[ChangeInfo] = []
        for file_name, generated_content in generated_files.items():
            changes = self._detect_changes_for_file(file_name, generated_content, customizations)
            all_changes.extend(changes)

        # Determine files to update vs unchanged
        # First, collect all files that have any non-unchanged changes
        files_with_changes: Set[str] = set()
        files_unchanged: Set[str] = set()

        for change in all_changes:
            if change.change_type == "unchanged":
                files_unchanged.add(change.file_name)
            else:
                files_with_changes.add(change.file_name)

        # Files with changes should NOT be in unchanged
        files_to_update = files_with_changes
        files_unchanged = files_unchanged - files_to_update

        # Update only changed sections
        updated_files = self.update_only_changed_sections(
            current_files, generated_files, customizations
        )

        # Preserve unchanged sections
        preserved_files = self.preserve_unchanged_sections(
            current_files, updated_files, customizations
        )

        # Update cache
        self.update_cache(preserved_files, customizations)

        # Build result
        files_to_update_list = list(files_to_update)
        files_unchanged_list = list(files_unchanged)

        summary = (
            f"Incremental update complete: {len(files_to_update_list)} files updated, "
            f"{len(files_unchanged_list)} files unchanged"
        )

        return IncrementalUpdateResult(
            files_to_update=files_to_update_list,
            files_unchanged=files_unchanged_list,
            changes_detected=all_changes,
            customizations_preserved=[
                c for c in customizations.values() for c in c  # type: ignore
            ],
            cache_updated=True,
            summary=summary,
        )

    def should_use_incremental(self, files: Dict[str, str]) -> bool:
        """
        Determine if incremental mode should be used.

        Args:
            files: Dictionary mapping file names to content.

        Returns:
            True if incremental mode should be used.
        """
        if self.force_incremental:
            return True

        # Use incremental if we have cached data
        cached_files = self._cache.get("files", {})
        return len(cached_files) > 0

    def clear_cache(self) -> None:
        """Clear the steering cache."""
        self._cache = {"files": {}, "metadata": {}}
        if self.cache_path.exists():
            self.cache_path.unlink()