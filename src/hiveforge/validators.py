import re
from typing import Optional

def validate_project_name(name: Optional[str]) -> str:
    if not name:
        raise ValueError("Project name cannot be empty")
    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
        raise ValueError(f"Invalid: '{name}'. Use kebab-case (e.g., 'my-project')")
    return name
