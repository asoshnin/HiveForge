"""
MCP tool for validating steering files.

This tool uses SharedValidateWorkflow from the shared backend to ensure
identical behavior with the CLI.
"""

from pathlib import Path
from typing import Any

from fastmcp import Context


async def validate_steering(
    ctx: Context,
    project_root: str = ".",
    strict: bool = False,
    use_llm: bool = True
) -> dict[str, Any]:
    """
    Validate steering files for completeness and quality.
    
    This tool checks steering files for missing sections, placeholder content,
    and semantic quality issues. It can use LLM for advanced validation.
    
    Args:
        project_root: Path to project root directory (default: current directory)
        strict: Treat warnings as errors (default: False)
        use_llm: Enable semantic validation with LLM (default: True)
    
    Returns:
        Structured result with status, message, validation issues, and metadata
    
    Example:
        {
            "status": "success",
            "message": "All validation checks passed",
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "warnings": [],
            "errors": [],
            "files_checked": 5,
            "critical_issues": 0,
            "warnings": 0,
            "info": 2,
            "overall_status": "valid",
            "strict_mode": false,
            "use_llm": true
        }
    """
    try:
        # Import shared workflow
        from hiveforge.steering.shared.adapters import SharedValidateWorkflow
        
        # Create and execute workflow
        workflow = SharedValidateWorkflow(
            project_root=project_root,
            strict=strict,
            use_llm=use_llm
        )
        
        result = workflow.execute()
        
        # Return structured JSON response
        return result.to_dict()
    
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Validation workflow failed: {str(e)}",
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "errors": [str(e)],
            "warnings": []
        }
