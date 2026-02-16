"""
Conflict resolution for steering file updates.

This module provides functionality to detect and resolve conflicts between
old and new information when updating steering files.
"""

from typing import Dict, Any, List
import re

from src.hiveforge.steering.models import Conflict


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
