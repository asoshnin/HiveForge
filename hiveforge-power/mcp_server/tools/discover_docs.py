"""
MCP tool for discovering existing documentation.

This tool uses SharedDiscoveryWorkflow from the shared backend to ensure
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
async def discover_docs(
    ctx: Context,
    project_root: str = ".",
    include_git_history: bool = False,
    max_discovery_files: int = 1000,
    max_file_size_mb: int = 10
) -> dict[str, Any]:
    """
    Discover existing documentation and project files.
    
    This tool analyzes the project to find existing documentation, README files,
    configuration files, and other relevant content. It can optionally analyze
    git history for additional context.
    
    Args:
        project_root: Path to project root directory (default: current directory)
        include_git_history: Analyze git commits and PRs (default: False)
        max_discovery_files: Maximum files to analyze (default: 1000)
        max_file_size_mb: Maximum file size in MB (default: 10)
    
    Returns:
        Structured result with status, message, discovered files, and metadata
    
    Example:
        {
            "status": "success",
            "message": "Discovery complete: 42 files found",
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "warnings": ["5 files skipped: too large"],
            "errors": [],
            "files_discovered": 42,
            "files_included": 37,
            "commit_count": 0,
            "include_git_history": false,
            "max_discovery_files": 1000,
            "max_file_size_mb": 10,
            "discovery_method": "scalable",
            "discovery_metadata": {...}
        }
    """
    try:
        # Import shared workflow
        from hiveforge.steering.shared.adapters import SharedDiscoveryWorkflow
        
        # Create and execute workflow
        workflow = SharedDiscoveryWorkflow(
            project_root=project_root,
            include_git_history=include_git_history,
            max_discovery_files=max_discovery_files,
            max_file_size_mb=max_file_size_mb
        )
        
        result = workflow.execute()
        
        # Return structured JSON response
        return result.to_dict()
    
    except Exception as e:
        return {
            "status": "failed",
            "message": f"Discovery workflow failed: {str(e)}",
            "files_created": [],
            "files_modified": [],
            "files_deleted": [],
            "errors": [str(e)],
            "warnings": []
        }
