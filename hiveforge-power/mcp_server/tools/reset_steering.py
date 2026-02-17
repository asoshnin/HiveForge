"""
MCP tool for resetting steering files to templates.

This tool uses SharedResetWorkflow from the shared backend to ensure
identical behavior with the CLI.
"""

from pathlib import Path
from typing import Any, Optional

from fastmcp import Context


async def reset_steering(
    ctx: Context,
    project_root: str = ".",
    file: Optional[str] = None,
    confirm: bool = False
) -> dict[str, Any]:
    """
    Reset steering files to default templates.
    
    This tool resets steering files to their original template state,
    creating backups before making changes. Useful for starting fresh
    or fixing corrupted files.
    
    Args:
        project_root: Path to project root directory (default: current directory)
        file: Specific file to reset (default: None = all files)
        confirm: Skip confirmation prompt (default: False)
    
    Returns:
        Structured result with status, message, files reset, and backup location
    
    Example:
        {
            "status": "success",
            "message": "Successfully reset 5 file(s) to default templates",
            "files_created": [],
            "files_modified": [
                ".kiro/steering/tech-stack.md",
                ".kiro/steering/architecture.md",
                ".kiro/steering/conventions.md",
                ".kiro/steering/project-vision.md"
            ],
            "files_deleted": [],
            "warnings": [],
            "errors": [],
            "backup_location": ".kiro/backups/reset_20260217_143022",
            "files_count": 5
        }
    """
    try:
        # Import shared workflow
        from hiveforge.steering.shared.adapters import SharedResetWorkflow
        
        # Create and execute workflow
        workflow = SharedResetWorkflow(
            project_root=project_root,
            file=file,
            confirm=confirm
        )
        
        result = workflow.execute()
        
        # Return structured JSON response
        return result.to_dict()
    
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Reset workflow failed: {str(e)}",
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "errors": [str(e)],
            "warnings": []
        }
