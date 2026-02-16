"""
Template population for steering files.

This module handles replacing placeholders in steering file templates with
gathered information from code analysis, document parsing, and user conversations.
"""

import re
from pathlib import Path
from typing import Any, Dict

from .templates import get_all_templates


class TemplatePopulator:
    """
    Populates steering file templates with gathered information.
    
    This class loads template definitions and replaces placeholders with
    actual project information while preserving frontmatter and structure.
    """
    
    def __init__(self):
        """Initialize the template populator with all template definitions."""
        self.templates = get_all_templates()
        self._template_dir = Path(__file__).parent.parent / "templates" / "steering"
    
    def populate(self, template_name: str, knowledge: Dict[str, Any]) -> str:
        """
        Populate a single template with gathered information.
        
        Args:
            template_name: Name of the template to populate (e.g., "project-vision")
            knowledge: Dictionary containing information to populate the template
                      Keys should match template placeholder names
        
        Returns:
            Populated template content as a string
            
        Raises:
            ValueError: If template_name is not found
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        template_file = self._template_dir / template.file_name
        
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        # Read the template content
        content = template_file.read_text(encoding="utf-8")
        
        # Extract and preserve frontmatter
        frontmatter, body = self._extract_frontmatter(content)
        
        # Populate the body with knowledge
        populated_body = self._replace_placeholders(body, knowledge)
        
        # Reconstruct with frontmatter
        if frontmatter:
            return f"---\n{frontmatter}---\n\n{populated_body}"
        else:
            return populated_body
    
    def populate_all(self, knowledge: Dict[str, Any], show_progress: bool = True) -> Dict[str, str]:
        """
        Populate all templates with gathered information.
        
        Args:
            knowledge: Dictionary containing information for all templates
                      Can be nested by template name or flat with all keys
            show_progress: Whether to display progress messages (default: True)
        
        Returns:
            Dictionary mapping filename to populated content
            Example: {"project-vision.md": "...", "tech-stack.md": "..."}
            
        Requirements: 4.6, 14.3
        """
        populated = {}
        total_templates = len(self.templates)
        
        for idx, (template_name, template) in enumerate(self.templates.items(), 1):
            # Display progress for current template (Req 14.3)
            if show_progress:
                print(f"   [{idx}/{total_templates}] Generating {template.file_name}...", end=" ")
            
            # Get knowledge specific to this template if nested, otherwise use all
            template_knowledge = knowledge.get(template_name, knowledge)
            
            try:
                content = self.populate(template_name, template_knowledge)
                populated[template.file_name] = content
                
                # Display result (Req 14.3)
                if show_progress:
                    print(f"✓")
            except Exception as e:
                # Log error but continue with other templates
                if show_progress:
                    print(f"✗ (error: {str(e)[:50]})")
                print(f"Warning: Failed to populate {template_name}: {e}")
                continue
        
        return populated
    
    def preserve_frontmatter(self, original: str, populated: str) -> str:
        """
        Ensure frontmatter from original is preserved in populated content.
        
        This is useful when updating existing files to maintain their frontmatter.
        
        Args:
            original: Original file content with frontmatter
            populated: Newly populated content (may have different frontmatter)
        
        Returns:
            Populated content with original frontmatter preserved
        """
        original_frontmatter, _ = self._extract_frontmatter(original)
        _, populated_body = self._extract_frontmatter(populated)
        
        if original_frontmatter:
            return f"---\n{original_frontmatter}---\n\n{populated_body}"
        else:
            return populated_body
    
    def _extract_frontmatter(self, content: str) -> tuple[str, str]:
        """
        Extract YAML frontmatter from markdown content.
        
        Args:
            content: Markdown content that may contain frontmatter
        
        Returns:
            Tuple of (frontmatter, body) where frontmatter is the YAML content
            between --- delimiters (without the delimiters), and body is the rest
        """
        # Match frontmatter pattern: starts with ---, ends with ---
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            return match.group(1), match.group(2)
        else:
            return "", content
    
    def _replace_placeholders(self, content: str, knowledge: Dict[str, Any]) -> str:
        """
        Replace placeholders in content with values from knowledge dictionary.
        
        Placeholders are in the format {placeholder_name} or {option1|option2|...}
        
        Args:
            content: Template content with placeholders
            knowledge: Dictionary with replacement values
        
        Returns:
            Content with placeholders replaced
        """
        result = content
        
        # Replace each key-value pair from knowledge
        for key, value in knowledge.items():
            if value is None:
                continue
            
            # Convert value to string if it's not already
            value_str = str(value) if not isinstance(value, str) else value
            
            # Handle different placeholder formats
            # 1. Simple placeholder: {key}
            simple_pattern = re.escape(f"{{{key}}}")
            result = re.sub(simple_pattern, value_str, result, flags=re.IGNORECASE)
            
            # 2. Placeholder with options: {option1|option2|key|...}
            # Find all placeholders with pipes and check if key matches any option
            option_pattern = r'\{([^}]*\|[^}]*)\}'
            
            def replace_option_placeholder(match):
                options = match.group(1)
                # Check if our key is one of the options
                if key.lower() in [opt.strip().lower() for opt in options.split('|')]:
                    return value_str
                return match.group(0)  # Keep original if no match
            
            result = re.sub(option_pattern, replace_option_placeholder, result)
        
        # Handle special common placeholders
        if "project_name" in knowledge:
            result = result.replace("{PROJECT_NAME}", str(knowledge["project_name"]))
        
        return result
