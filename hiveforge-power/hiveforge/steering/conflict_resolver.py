"""
Conflict resolution for steering file updates.

This module provides functionality to detect and resolve conflicts between
old and new information when updating steering files.
"""

from typing import Dict, Any, List
import re

from .models import Conflict


class ConflictResolver:
    """
    Detects and resolves conflicts between old and new steering file content.
    
    Conflicts occur when new information contradicts existing content in areas like:
    - Technology choices (e.g., database, framework changes)
    - Architecture decisions (e.g., pattern changes)
    - Project goals and vision
    """
    
    # Keywords that indicate technology-related sections
    TECH_KEYWORDS = {
        'language', 'framework', 'database', 'cache', 'library', 'dependency',
        'backend', 'frontend', 'runtime', 'version', 'tech', 'stack'
    }
    
    # Keywords that indicate architecture-related sections
    ARCH_KEYWORDS = {
        'architecture', 'pattern', 'monolithic', 'microservices', 'layered',
        'mvc', 'hexagonal', 'component', 'structure', 'design'
    }
    
    # Keywords that indicate goal/vision-related sections
    GOAL_KEYWORDS = {
        'goal', 'vision', 'objective', 'mission', 'purpose', 'problem',
        'solution', 'target', 'metric', 'success'
    }
    
    @staticmethod
    def detect_conflicts(
        old_content: Dict[str, Any],
        new_content: Dict[str, Any]
    ) -> List[Conflict]:
        """
        Identify contradictions between old and new information.
        
        Compares old and new content dictionaries to find conflicts in:
        - Technology choices (databases, frameworks, languages)
        - Architecture decisions (patterns, structures)
        - Project goals and vision
        
        Args:
            old_content: Dictionary of existing steering file content
            new_content: Dictionary of new/updated content
            
        Returns:
            List of Conflict objects representing detected contradictions
        """
        conflicts = []
        
        # Get all keys that exist in both old and new content
        common_keys = set(old_content.keys()) & set(new_content.keys())
        
        for key in common_keys:
            old_value = old_content[key]
            new_value = new_content[key]
            
            # Skip if values are identical
            if old_value == new_value:
                continue
            
            # Convert to strings for comparison
            old_str = str(old_value) if old_value is not None else ""
            new_str = str(new_value) if new_value is not None else ""
            
            # Skip empty values
            if not old_str.strip() or not new_str.strip():
                continue
            
            # Detect conflict type and create appropriate conflict object
            conflict = ConflictResolver._analyze_conflict(key, old_str, new_str)
            if conflict:
                conflicts.append(conflict)
        
        return conflicts
    
    @staticmethod
    def _analyze_conflict(section: str, old_value: str, new_value: str) -> Conflict:
        """
        Analyze a potential conflict and create a Conflict object with explanation.
        
        Args:
            section: The section name where the conflict occurs
            old_value: The existing value
            new_value: The new value
            
        Returns:
            Conflict object with appropriate explanation, or None if not a real conflict
        """
        section_lower = section.lower()
        
        # Determine conflict category
        is_tech = any(keyword in section_lower for keyword in ConflictResolver.TECH_KEYWORDS)
        is_arch = any(keyword in section_lower for keyword in ConflictResolver.ARCH_KEYWORDS)
        is_goal = any(keyword in section_lower for keyword in ConflictResolver.GOAL_KEYWORDS)
        
        # Generate explanation based on conflict type
        if is_tech:
            explanation = (
                f"Technology choice conflict detected in '{section}'. "
                f"The existing configuration specifies '{old_value}' but new information "
                f"indicates '{new_value}'. This may affect dependencies, tooling, and "
                f"development workflows."
            )
        elif is_arch:
            explanation = (
                f"Architecture decision conflict detected in '{section}'. "
                f"The current architecture uses '{old_value}' but new information "
                f"suggests '{new_value}'. This may require significant refactoring "
                f"and impact system design."
            )
        elif is_goal:
            explanation = (
                f"Project goal/vision conflict detected in '{section}'. "
                f"The existing goal is '{old_value}' but new information "
                f"indicates '{new_value}'. This may affect project direction "
                f"and priorities."
            )
        else:
            # Generic conflict
            explanation = (
                f"Content conflict detected in '{section}'. "
                f"The existing value '{old_value}' differs from new value '{new_value}'."
            )
        
        return Conflict(
            section=section,
            old_value=old_value,
            new_value=new_value,
            explanation=explanation,
            resolution_options=["keep_old", "use_new", "merge"]
        )
    
    @staticmethod
    def resolve_conflict(conflict: Conflict, user_choice: str) -> str:
        """
        Apply user's resolution choice to a conflict.
        
        Args:
            conflict: The Conflict object to resolve
            user_choice: User's choice - one of "keep_old", "use_new", or "merge"
            
        Returns:
            The resolved value as a string
            
        Raises:
            ValueError: If user_choice is not a valid option
        """
        if user_choice not in conflict.resolution_options:
            raise ValueError(
                f"Invalid resolution choice '{user_choice}'. "
                f"Must be one of: {', '.join(conflict.resolution_options)}"
            )
        
        if user_choice == "keep_old":
            return conflict.old_value
        elif user_choice == "use_new":
            return conflict.new_value
        elif user_choice == "merge":
            # Simple merge strategy: combine both values with a separator
            return ConflictResolver._merge_values(conflict.old_value, conflict.new_value)
        
        # Should never reach here due to validation above
        raise ValueError(f"Unexpected resolution choice: {user_choice}")
    
    @staticmethod
    def _merge_values(old_value: str, new_value: str) -> str:
        """
        Merge two conflicting values intelligently.
        
        Strategy:
        - If values are single words/phrases, combine with " / "
        - If values are sentences, combine with newline
        - If one contains the other, use the longer one
        - Otherwise, combine with appropriate separator
        
        Args:
            old_value: The existing value
            new_value: The new value
            
        Returns:
            Merged value string
        """
        # If one value contains the other, use the longer one
        if old_value in new_value:
            return new_value
        if new_value in old_value:
            return old_value
        
        # Check if values are multi-line
        old_lines = old_value.count('\n')
        new_lines = new_value.count('\n')
        
        if old_lines > 0 or new_lines > 0:
            # Multi-line content: separate with blank line
            return f"{old_value.strip()}\n\n{new_value.strip()}"
        
        # Check if values are sentences (contain periods)
        if '.' in old_value or '.' in new_value:
            # Sentence-like content: separate with space
            return f"{old_value.strip()} {new_value.strip()}"
        
        # Short phrases: separate with slash
        return f"{old_value.strip()} / {new_value.strip()}"
    
    @staticmethod
    def format_conflict_presentation(conflict: Conflict) -> str:
        """
        Format a conflict for side-by-side presentation to the user.
        
        Args:
            conflict: The Conflict object to format
            
        Returns:
            Formatted string showing the conflict details
        """
        separator = "=" * 70
        
        presentation = f"\n{separator}\n"
        presentation += f"CONFLICT in section: {conflict.section}\n"
        presentation += f"{separator}\n\n"
        
        presentation += f"Explanation:\n{conflict.explanation}\n\n"
        
        presentation += f"OLD VALUE:\n"
        presentation += f"{'-' * 70}\n"
        presentation += f"{conflict.old_value}\n"
        presentation += f"{'-' * 70}\n\n"
        
        presentation += f"NEW VALUE:\n"
        presentation += f"{'-' * 70}\n"
        presentation += f"{conflict.new_value}\n"
        presentation += f"{'-' * 70}\n\n"
        
        presentation += f"Resolution options: {', '.join(conflict.resolution_options)}\n"
        presentation += f"{separator}\n"
        
        return presentation

    @staticmethod
    def format_conflict_presentation(conflict: Conflict) -> str:
        """
        Format a conflict for side-by-side presentation to the user.

        Args:
            conflict: The Conflict object to format

        Returns:
            Formatted string showing the conflict details
        """
        separator = "=" * 70

        presentation = f"\n{separator}\n"
        presentation += f"CONFLICT in section: {conflict.section}\n"
        presentation += f"{separator}\n\n"

        presentation += f"Explanation:\n{conflict.explanation}\n\n"

        presentation += f"OLD VALUE:\n"
        presentation += f"{'-' * 70}\n"
        presentation += f"{conflict.old_value}\n"
        presentation += f"{'-' * 70}\n\n"

        presentation += f"NEW VALUE:\n"
        presentation += f"{'-' * 70}\n"
        presentation += f"{conflict.new_value}\n"
        presentation += f"{'-' * 70}\n\n"

        presentation += f"Resolution options: {', '.join(conflict.resolution_options)}\n"
        presentation += f"{separator}\n"

        return presentation

    @staticmethod
    def detect_direct_conflicts(
        old_content: Dict[str, Any],
        new_content: Dict[str, Any]
    ) -> List[Conflict]:
        """
        Detect direct contradictions between old and new content.

        Args:
            old_content: Dictionary of existing steering file content
            new_content: Dictionary of new/updated content

        Returns:
            List of Conflict objects for direct contradictions
        """
        return ConflictResolver.detect_conflicts(old_content, new_content)

    @staticmethod
    def detect_implicit_conflicts(
        old_content: Dict[str, Any],
        new_content: Dict[str, Any]
    ) -> List[Conflict]:
        """
        Detect implicit contradictions between old and new content.

        Args:
            old_content: Dictionary of existing steering file content
            new_content: Dictionary of new/updated content

        Returns:
            List of Conflict objects for implicit contradictions
        """
        conflicts = []

        # Check for implicit contradictions
        old_str = str(old_content).lower()
        new_str = str(new_content).lower()

        # Check for microservices vs monolithic
        if ("microservices" in old_str and "monolithic" in new_str) or \
           ("monolithic" in old_str and "microservices" in new_str):
            conflicts.append(Conflict(
                section="architecture",
                old_value="microservices" if "microservices" in old_str else "monolithic",
                new_value="monolithic" if "monolithic" in new_str else "microservices",
                explanation="Architecture pattern conflict: microservices vs monolithic",
                resolution_options=["keep_old", "use_new", "merge"]
            ))

        # Check for REST vs GraphQL
        if ("rest" in old_str and "graphql" in new_str) or \
           ("graphql" in old_str and "rest" in new_str):
            conflicts.append(Conflict(
                section="api",
                old_value="REST" if "rest" in old_str else "GraphQL",
                new_value="GraphQL" if "graphql" in new_str else "REST",
                explanation="API pattern conflict: REST vs GraphQL",
                resolution_options=["keep_old", "use_new", "merge"]
            ))

        return conflicts

    @staticmethod
    def detect_version_conflicts(
        old_content: Dict[str, Any],
        new_content: Dict[str, Any]
    ) -> List[Conflict]:
        """
        Detect version mismatches between old and new content.

        Args:
            old_content: Dictionary of existing steering file content
            new_content: Dictionary of new/updated content

        Returns:
            List of Conflict objects for version mismatches
        """
        conflicts = []

        # Extract version information
        import re

        version_pattern = r"(\d+\.\d+)"

        old_versions = re.findall(version_pattern, str(old_content))
        new_versions = re.findall(version_pattern, str(new_content))

        # Check for version mismatches
        for old_v in old_versions:
            for new_v in new_versions:
                if old_v != new_v:
                    conflicts.append(Conflict(
                        section="version",
                        old_value=old_v,
                        new_value=new_v,
                        explanation=f"Version mismatch: {old_v} vs {new_v}",
                        resolution_options=["keep_old", "use_new", "merge"]
                    ))

        return conflicts

    @staticmethod
    def calculate_conflict_confidence(
        conflict: Conflict,
    ) -> float:
        """
        Calculate confidence score for a detected conflict.

        Args:
            conflict: The Conflict object

        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence for direct conflicts
        base_confidence = 0.95

        # Reduce confidence for implicit conflicts
        if "implicit" in conflict.explanation.lower():
            base_confidence = 0.85

        # Ensure confidence is in valid range
        return max(0.0, min(1.0, base_confidence))

    @staticmethod
    def batch_conflicts(
        conflicts: List[Conflict],
    ) -> Dict[str, List[Conflict]]:
        """
        Group similar conflicts together.

        Args:
            conflicts: List of Conflict objects

        Returns:
            Dictionary mapping conflict type to list of conflicts
        """
        batches = {}

        for conflict in conflicts:
            conflict_type = conflict.section.lower()

            if conflict_type not in batches:
                batches[conflict_type] = []

            batches[conflict_type].append(conflict)

        return batches

    @staticmethod
    def present_batch_view(
        batches: Dict[str, List[Conflict]],
    ) -> str:
        """
        Present multiple conflicts together.

        Args:
            batches: Dictionary of conflict batches

        Returns:
            Formatted string showing all conflicts
        """
        output = []
        output.append("=" * 70)
        output.append("BATCH CONFLICT RESOLUTION")
        output.append("=" * 70)

        for conflict_type, conflicts in batches.items():
            output.append(f"\n{conflict_type.upper()} ({len(conflicts)} conflicts):")
            output.append("-" * 70)

            for i, conflict in enumerate(conflicts, 1):
                output.append(f"\n  Conflict {i}:")
                output.append(f"    Section: {conflict.section}")
                output.append(f"    Old: {conflict.old_value}")
                output.append(f"    New: {conflict.new_value}")

        output.append("\n" + "=" * 70)
        output.append("Resolution options: keep_all_old, use_all_new, review_individual")
        output.append("=" * 70)

        return "\n".join(output)

    @staticmethod
    def apply_batch_resolution(
        conflicts: List[Conflict],
        resolution: str,
    ) -> List[str]:
        """
        Apply same resolution strategy to all conflicts in batch.

        Args:
            conflicts: List of Conflict objects
            resolution: Resolution strategy ("keep_all_old", "use_all_new", "review_individual")

        Returns:
            List of resolved values
        """
        resolved = []

        for conflict in conflicts:
            if resolution == "keep_all_old":
                resolved.append(conflict.old_value)
            elif resolution == "use_all_new":
                resolved.append(conflict.new_value)
            elif resolution == "review_individual":
                # Keep conflict for individual review
                resolved.append(None)
            else:
                resolved.append(None)

        return resolved

    @staticmethod
    def skip_conflicts(
        conflicts: List[Conflict],
    ) -> List[Conflict]:
        """
        Mark conflicts to be resolved later.

        Args:
            conflicts: List of Conflict objects

        Returns:
            List of conflicts to be resolved later
        """
        return conflicts
