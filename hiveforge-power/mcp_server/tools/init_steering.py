"""
MCP tool for initializing steering files.

This tool uses SharedInitWorkflow from the shared backend to ensure
identical behavior with the CLI.
"""

from pathlib import Path
from typing import Any

from fastmcp import Context

# Import security decorator
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from src.hiveforge.steering.shared.security import secure_execution


@secure_execution(
    max_memory_mb=512,
    max_cpu_time_sec=300,
    max_file_size_mb=10,
    enable_input_validation=True,
    enable_path_sanitization=True,
    enable_resource_limits=True,
    enable_error_obfuscation=True,
)
async def init_steering(
    ctx: Context,
    project_root: str = ".",
    auto_discover: bool = True,
    autonomous: bool = True,
    confidence_threshold: float = 0.7
) -> dict[str, Any]:
    """
    Initialize steering files for a project.
    
    This tool creates a complete set of steering files by analyzing the project
    structure, code, and existing documentation. It uses AI to generate contextually
    relevant content.
    
    Args:
        project_root: Path to project root directory (default: current directory)
        auto_discover: Enable automatic discovery of existing docs (default: True)
        autonomous: Enable autonomous generation mode (default: True)
        confidence_threshold: Minimum confidence for autonomous decisions (default: 0.7)
    
    Returns:
        Structured result with status, message, files created, and metadata
    
    Example:
        {
            "status": "success",
            "message": "Successfully initialized steering files (5 files created)",
            "files_created": [
                ".kiro/steering/tech-stack.md",
                ".kiro/steering/architecture.md",
                ".kiro/steering/conventions.md",
                ".kiro/steering/project-vision.md"
            ],
            "warnings": [],
            "errors": [],
            "autonomous": true,
            "auto_discover": true,
            "confidence_threshold": 0.7,
            "files_count": 5
        }
    """
    try:
        # Import shared workflow
        from hiveforge.steering.shared.adapters import SharedInitWorkflow
        
        # Create and execute workflow
        workflow = SharedInitWorkflow(
            project_root=project_root,
            auto_discover=auto_discover,
            autonomous=autonomous,
            confidence_threshold=confidence_threshold
        )
        
        result = workflow.execute()
        
        # Return structured JSON response
        return result.to_dict()
    
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Init workflow failed: {str(e)}",
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "errors": [str(e)],
            "warnings": []
        }
