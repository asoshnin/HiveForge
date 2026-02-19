"""
MCP tool for initializing steering files.

This tool uses SharedInitWorkflow from the shared backend to ensure
identical behavior with the CLI.
"""

from typing import Any

from fastmcp import Context

# Import security decorator from packaged version
from hiveforge.steering.shared.security import secure_execution


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
    source_docs_path: str | None = None,
    auto_discover: bool = True,
    autonomous: bool = True,
    confidence_threshold: float = 0.7,
    dry_run: bool = False,
    copy_files: bool = False
) -> dict[str, Any]:
    """
    Initialize steering files for a project.
    
    This tool creates a complete set of steering files by analyzing the project
    structure, code, and existing documentation. It uses AI to generate contextually
    relevant content.
    
    Args:
        project_root: Path to project root directory (default: current directory)
        source_docs_path: Optional path to source documents folder (relative to project_root).
                         When provided, restricts document discovery to that path.
                         When NOT provided, uses default behavior (scan .kiro/onboarding/ first).
                         Example: "_DEVELOPMENT" or "docs/design"
        auto_discover: Enable automatic discovery of existing docs (default: True)
        autonomous: Enable autonomous generation mode (LLM fills gaps without asking) (default: True)
        confidence_threshold: Minimum confidence for autonomous decisions (0.0-1.0, default: 0.7).
                             Controls when to ask vs. infer in autonomous mode.
                             Higher values = more questions, less inference.
                             Lower values = fewer questions, more inference.
                             Note: This parameter only affects autonomous mode decisions,
                             not warning generation (warnings trigger at < 0.5 overall confidence).
        dry_run: Preview what would be created without writing files (default: False)
        copy_files: If True, copy source files to staging. If False, use symlinks for performance (default: False)
    
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
            "files_count": 5,
            "source_documents_found": 3,
            "confidence_level": "medium",
            "metadata": {
                "source_docs_path": "_DEVELOPMENT",
                "discovery_stats": {...}
            }
        }
    """
    try:
        # Import shared workflow
        from hiveforge.steering.shared.adapters import SharedInitWorkflow
        
        # Create and execute workflow
        workflow = SharedInitWorkflow(
            project_root=project_root,
            source_docs_path=source_docs_path,
            auto_discover=auto_discover,
            autonomous=autonomous,
            confidence_threshold=confidence_threshold,
            dry_run=dry_run,
            copy_files=copy_files
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
