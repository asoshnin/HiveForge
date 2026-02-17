"""
Template definitions for steering files.

This module defines the structure and requirements for all eight steering file
templates used in HiveForge projects.
"""

from typing import Dict, List
from .models import Template, TemplateSection, ValidationRule


def get_all_templates() -> Dict[str, Template]:
    """
    Get all steering file template definitions.
    
    Returns:
        Dictionary mapping template names to Template objects
    """
    return {
        "project-vision": _create_project_vision_template(),
        "tech-stack": _create_tech_stack_template(),
        "architecture": _create_architecture_template(),
        "conventions": _create_conventions_template(),
        "api-standards": _create_api_standards_template(),
        "db-standards": _create_db_standards_template(),
        "qa-standards": _create_qa_standards_template(),
        "ui-standards": _create_ui_standards_template(),
    }


def _create_project_vision_template() -> Template:
    """Create the project-vision template definition."""
    return Template(
        name="project-vision",
        file_name="project-vision.md",
        priority=1,  # Highest priority
        sections=[
            TemplateSection(
                name="Elevator Pitch",
                required=True,
                placeholder_pattern=r"\{One sentence description.*?\}",
            ),
            TemplateSection(
                name="Problem Statement",
                required=True,
                placeholder_pattern=r"\{What pain does this solve.*?\}",
            ),
            TemplateSection(
                name="Solution Overview",
                required=True,
                placeholder_pattern=r"\{How do we solve it.*?\}",
            ),
            TemplateSection(
                name="Target Users",
                required=True,
                placeholder_pattern=r"\{Who benefits.*?\}",
            ),
            TemplateSection(
                name="Success Metrics",
                required=True,
                placeholder_pattern=r"\{The one number that matters\}|\{Value\}|\{Date\}",
            ),
            TemplateSection(
                name="Non-Goals",
                required=False,
                placeholder_pattern=r"\{Out of scope feature.*?\}",
            ),
            TemplateSection(
                name="Constraints & Assumptions",
                required=False,
                placeholder_pattern=r"\{.*?constraint\}|\{Key assumption.*?\}",
            ),
            TemplateSection(
                name="Timeline",
                required=False,
                placeholder_pattern=r"\{Date\}",
            ),
        ],
        frontmatter={"inclusion": "auto", "priority": 1},
    )


def _create_tech_stack_template() -> Template:
    """Create the tech-stack template definition."""
    return Template(
        name="tech-stack",
        file_name="tech-stack.md",
        priority=1,  # Highest priority (same as project-vision)
        sections=[
            TemplateSection(
                name="Backend",
                required=True,
                placeholder_pattern=r"\{Python.*?|Node\.js.*?|Go.*?|\.\.\.?\}",
            ),
            TemplateSection(
                name="Frontend",
                required=False,
                placeholder_pattern=r"\{React.*?|Vue.*?|Svelte.*?|\.\.\.?\}",
            ),
            TemplateSection(
                name="Database",
                required=True,
                placeholder_pattern=r"\{PostgreSQL.*?|MongoDB.*?|\.\.\.?\}",
            ),
            TemplateSection(
                name="Cache",
                required=False,
                placeholder_pattern=r"\{Redis.*?|\.\.\.?\}",
            ),
            TemplateSection(
                name="Infrastructure",
                required=False,
                placeholder_pattern=r"\{Docker|K8s|AWS|GCP|Azure|\.\.\.?\}",
            ),
            TemplateSection(
                name="Key Dependencies",
                required=False,
                placeholder_pattern=r"\{library\}|\{version\}|\{why\}",
            ),
            TemplateSection(
                name="Rationale",
                required=False,
                placeholder_pattern=r"\{Why this stack.*?\}",
            ),
        ],
        frontmatter={"inclusion": "auto", "priority": 1},
    )


def _create_architecture_template() -> Template:
    """Create the architecture template definition."""
    return Template(
        name="architecture",
        file_name="architecture.md",
        priority=2,
        sections=[
            TemplateSection(
                name="System Diagram",
                required=False,
                placeholder_pattern=r"",  # Mermaid diagrams are optional
            ),
            TemplateSection(
                name="Component Responsibilities",
                required=True,
                placeholder_pattern=r"\{Component.*?\}|\{What it does\}|\{How others talk to it\}|\{What it needs\}",
            ),
            TemplateSection(
                name="Data Flow",
                required=False,
                placeholder_pattern=r"\{Step.*?\}",
            ),
            TemplateSection(
                name="Key Decisions",
                required=False,
                placeholder_pattern=r"\{Decision\}|\{Why\}|\{What we gave up\}",
            ),
            TemplateSection(
                name="Scalability Considerations",
                required=False,
                placeholder_pattern=r"\{How we handle growth\}|\{Bottlenecks to watch\}",
            ),
        ],
        frontmatter={"inclusion": "auto", "priority": 2},
    )


def _create_conventions_template() -> Template:
    """Create the conventions template definition."""
    return Template(
        name="conventions",
        file_name="conventions.md",
        priority=2,
        sections=[
            TemplateSection(
                name="General Principles",
                required=False,
                placeholder_pattern=r"",
            ),
            TemplateSection(
                name="Naming Conventions",
                required=True,
                placeholder_pattern=r"",  # Usually filled from code analysis
            ),
            TemplateSection(
                name="Code Style",
                required=True,
                placeholder_pattern=r"",  # Usually filled from code analysis
            ),
            TemplateSection(
                name="Testing",
                required=False,
                placeholder_pattern=r"",
            ),
            TemplateSection(
                name="Git Conventions",
                required=False,
                placeholder_pattern=r"",
            ),
        ],
        frontmatter={"inclusion": "auto", "priority": 2},
    )


def _create_api_standards_template() -> Template:
    """Create the api-standards template definition."""
    return Template(
        name="api-standards",
        file_name="api-standards.md",
        priority=3,
        sections=[
            TemplateSection(
                name="API Design Principles",
                required=True,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Error Handling",
                required=True,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Authentication",
                required=False,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Versioning",
                required=False,
                placeholder_pattern=r"\{.*?\}",
            ),
        ],
        frontmatter={"inclusion": "auto", "priority": 3},
    )


def _create_db_standards_template() -> Template:
    """Create the db-standards template definition."""
    return Template(
        name="db-standards",
        file_name="db-standards.md",
        priority=3,
        sections=[
            TemplateSection(
                name="Schema Design",
                required=True,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Migration Strategy",
                required=True,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Query Patterns",
                required=False,
                placeholder_pattern=r"\{.*?\}",
            ),
        ],
        frontmatter={"inclusion": "auto", "priority": 3},
    )


def _create_qa_standards_template() -> Template:
    """Create the qa-standards template definition."""
    return Template(
        name="qa-standards",
        file_name="qa-standards.md",
        priority=3,
        sections=[
            TemplateSection(
                name="Testing Strategy",
                required=True,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Coverage Requirements",
                required=True,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Test Types",
                required=False,
                placeholder_pattern=r"\{.*?\}",
            ),
        ],
        frontmatter={"inclusion": "auto", "priority": 3},
    )


def _create_ui_standards_template() -> Template:
    """Create the ui-standards template definition."""
    return Template(
        name="ui-standards",
        file_name="ui-standards.md",
        priority=3,
        sections=[
            TemplateSection(
                name="Component Patterns",
                required=True,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Styling Guidelines",
                required=False,
                placeholder_pattern=r"\{.*?\}",
            ),
            TemplateSection(
                name="Accessibility",
                required=False,
                placeholder_pattern=r"\{.*?\}",
            ),
        ],
        frontmatter={"inclusion": "auto", "priority": 3},
    )
