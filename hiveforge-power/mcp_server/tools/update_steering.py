"""
MCP tool for updating steering files.

This tool uses SharedUpdateWorkflow from the shared backend to ensure
identical behavior with the CLI.
"""

from pathlib import Path
from typing import Any, Optional

from fastmcp import Context


async def update_steering(
    ctx: Context,
    project_root: str = ".",
    files_to_update: Optional[list[str]] = None,
    preserve_customizations: bool = True,
    incremental: bool = True
) -> dict[str, Any]:
    """
    Update existing steering files with fresh project analysis.
    
    This tool re-analyzes the project and updates steering files while
    preserving user customizations. It can update all files or specific ones.
    
    Args:
        project_root: Path to project root directory (default: current directory)
        files_to_update: Specific files to update (default: None = all files)
        preserve_customizations: Preserve user customizations (default: True)
        incremental: Use incremental update mode (default: True)
    
    Returns:
        Structured result with status, message, files modified, and metadata
    
    Example:
        {
            "status": "success",
            "message": "Successfully updated steering files (3 files modified)",
            "files_created": [],
            "files_modified": [
                ".kiro/steering/tech-stack.md",
                ".kiro/steering/architecture.md"
            ],
            "files_deleted": [],
            "warnings": ["1 customization detected in tech-stack.md"],
            "errors": [],
            "incremental": true,
            "preserve_customizations": true,
            "files_count": 2,
            "customizations_detected": 1
        }
    """
    try:
        # Import shared workflow
        from hiveforge.steering.shared.adapters import SharedUpdateWorkflow
        
        # Create and execute workflow
        workflow = SharedUpdateWorkflow(
            project_root=project_root,
            files_to_update=files_to_update,
            preserve_customizations=preserve_customizations,
            incremental=incremental
        )
        
        result = workflow.execute()
        
        # Return structured JSON response
        return result.to_dict()
    
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Update workflow failed: {str(e)}",
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "errors": [str(e)],
            "warnings": []
        }
