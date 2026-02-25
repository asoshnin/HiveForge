"""
Template population for steering files.

This module handles replacing placeholders in steering file templates with
gathered information from code analysis, document parsing, and user conversations.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict

from .templates import get_all_templates

logger = logging.getLogger(__name__)


class TemplatePopulator:
    """
    Populates steering file templates with gathered information.

    Accepts two knowledge dict shapes in populate() / populate_all():

    1. Nested (from SteeringAssistant.conduct_conversation + _combine_knowledge):
       {
           "project-vision": {"Elevator Pitch": "answer", "Target Users": "answer"},
           "tech-stack":     {"Rationale": "answer", "Backend": "Python 3.11+"},
       }

    2. Flat (legacy / direct callers):
       {"Elevator Pitch": "answer", "Rationale": "answer"}

    Both shapes are handled transparently via _flatten_knowledge().
    """

    def __init__(self):
        """Initialize the template populator with all template definitions."""
        self.templates = get_all_templates()
        self._template_dir = Path(__file__).parent.parent / "templates" / "steering"

    def populate(self, template_name: str, knowledge: Dict[str, Any]) -> str:
        """
        Populate a single template with gathered information.

        Args:
            template_name: Name of the template (e.g., "project-vision")
            knowledge: Flat or nested knowledge dict (see class docstring)

        Returns:
            Populated template content as a string

        Raises:
            ValueError: If template_name is not found
            FileNotFoundError: If the template file is missing
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template = self.templates[template_name]
        template_file = self._template_dir / template.file_name

        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")

        content = template_file.read_text(encoding="utf-8")
        frontmatter, body = self._extract_frontmatter(content)

        # Flatten nested knowledge so section names are top-level keys
        flat_knowledge = self._flatten_knowledge(template_name, knowledge)

        # Primary pass: use each section's placeholder_pattern regex
        populated_body = self._replace_by_section_patterns(body, template, flat_knowledge)

        # Secondary pass: catch any remaining simple {key} placeholders
        populated_body = self._replace_placeholders(populated_body, flat_knowledge)

        if frontmatter:
            return f"---\n{frontmatter}---\n\n{populated_body}"
        return populated_body

    def populate_all(self, knowledge: Dict[str, Any], show_progress: bool = True) -> Dict[str, str]:
        """
        Populate all templates with gathered information.

        Args:
            knowledge: Flat or nested knowledge dict (see class docstring)
            show_progress: Whether to display progress messages

        Returns:
            Dict mapping filename -> populated content

        Requirements: 4.6, 14.3
        """
        populated = {}
        total_templates = len(self.templates)

        for idx, (template_name, template) in enumerate(self.templates.items(), 1):
            if show_progress:
                print(f"   [{idx}/{total_templates}] Generating {template.file_name}...", end=" ")

            try:
                content = self.populate(template_name, knowledge)
                populated[template.file_name] = content
                if show_progress:
                    print("OK")
            except Exception as e:
                if show_progress:
                    print(f"ERROR: {str(e)[:50]}")
                logger.warning(f"Failed to populate {template_name}: {e}")
                continue

        return populated

    def preserve_frontmatter(self, original: str, populated: str) -> str:
        """
        Ensure frontmatter from original is preserved in populated content.

        Args:
            original: Original file content with frontmatter
            populated: Newly populated content

        Returns:
            Populated content with original frontmatter preserved
        """
        original_frontmatter, _ = self._extract_frontmatter(original)
        _, populated_body = self._extract_frontmatter(populated)

        if original_frontmatter:
            return f"---\n{original_frontmatter}---\n\n{populated_body}"
        return populated_body

    def _flatten_knowledge(self, template_name: str, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Produce a flat section_name->answer dict for a specific template.

        Handles two input shapes:
        - Nested: {"project-vision": {"Elevator Pitch": "x"}, "tech-stack": {...}}
          Merges top-level scalar values with the template-specific sub-dict.
        - Flat: {"Elevator Pitch": "x", "Rationale": "y"}
          Returned as-is (minus any nested sub-dicts).

        Args:
            template_name: The template being populated (e.g., "project-vision")
            knowledge: Raw knowledge dict

        Returns:
            Flat dict of {section_name_or_key: answer}
        """
        # Start with all top-level scalar values (skip nested dicts)
        flat: Dict[str, Any] = {k: v for k, v in knowledge.items() if not isinstance(v, dict)}

        # Merge in this template's section answers if they exist as a nested sub-dict
        if template_name in knowledge and isinstance(knowledge[template_name], dict):
            flat.update(knowledge[template_name])

        return flat

    def _replace_by_section_patterns(
        self, content: str, template: Any, knowledge: Dict[str, Any]
    ) -> str:
        """
        Replace template placeholders using each section's placeholder_pattern.

        This is the primary replacement pass. For each section defined in the
        template, if the knowledge dict has an answer keyed by that section name,
        the section's placeholder_pattern regex replaces ALL matching placeholders
        in the template body with the answer.

        Example:
            Section name:        "Elevator Pitch"
            placeholder_pattern: r"\{One sentence description.*?\}"
            knowledge key:       "Elevator Pitch" -> "HiveForge is the OS for agentic coding"
            Result:              "{One sentence description...}" replaced with the answer

        Args:
            content: Template body (frontmatter already stripped)
            template: Template definition object with .sections list
            knowledge: Flat dict of {section_name: answer}

        Returns:
            Content with matched section placeholders replaced
        """
        result = content

        for section in template.sections:
            answer = knowledge.get(section.name)
            if answer is None:
                continue

            value_str = str(answer) if not isinstance(answer, str) else answer

            try:
                result = re.sub(
                    section.placeholder_pattern,
                    lambda m, v=value_str: v,
                    result,
                    flags=re.DOTALL | re.IGNORECASE,
                )
            except re.error as e:
                logger.warning(
                    f"Invalid placeholder_pattern for section '{section.name}': {e}"
                )

        return result

    def _extract_frontmatter(self, content: str) -> tuple:
        """
        Extract YAML frontmatter from markdown content.

        Returns:
            Tuple of (frontmatter_content, body) - frontmatter excludes the --- delimiters
        """
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        return "", content

    def _replace_placeholders(self, content: str, knowledge: Dict[str, Any]) -> str:
        """
        Secondary replacement pass: replace simple {key} and {opt1|opt2|...} placeholders.

        Handles:
        1. Simple placeholders: {key} matched against knowledge keys
        2. Option placeholders: {opt1|opt2|key|...} where any option matches a key
        3. Special {PROJECT_NAME} placeholder

        Args:
            content: Template content (after section-pattern pass)
            knowledge: Flat dict with replacement values

        Returns:
            Content with remaining placeholders replaced
        """
        result = content

        for key, value in knowledge.items():
            if value is None:
                continue

            value_str = str(value) if not isinstance(value, str) else value

            # 1. Simple placeholder: {key}
            simple_pattern = re.escape(f"{{{key}}}")
            result = re.sub(simple_pattern, value_str, result, flags=re.IGNORECASE)

            # 2. Option placeholder: {option1|option2|key|...}
            option_pattern = r'\{([^}]*\|[^}]*)\}'

            def replace_option_placeholder(match, k=key, v=value_str):
                options = match.group(1)
                if k.lower() in [opt.strip().lower() for opt in options.split("|")]:
                    return v
                return match.group(0)

            result = re.sub(option_pattern, replace_option_placeholder, result)

        # 3. Special PROJECT_NAME placeholder
        if "project_name" in knowledge:
            result = result.replace("{PROJECT_NAME}", str(knowledge["project_name"]))

        return result
