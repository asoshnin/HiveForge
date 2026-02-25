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
    copy_files: bool = False,
    skip_debt_detection: bool = False,
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
                         Examples:
                           - "_DEVELOPMENT" - Use docs from _DEVELOPMENT folder
                           - "docs/design" - Use docs from docs/design folder
                           - "my-docs" - Use docs from my-docs folder
                         Note: Only one path is used (no merging of multiple locations)
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
        Structured result with status, message, files created, and metadata.
        
        Confidence Metadata:
          - confidence_level: "high" (0.7-1.0), "medium" (0.4-0.7), or "low" (0.0-0.4)
          - confidence_score: Overall confidence score (0.0-1.0)
          - source_documents_found: Number of source documents discovered
          - Files with low confidence include [INFERRED] tags on inferred sections
        
        Warnings:
          - "No source documents found" - Empty source folder, all content inferred
          - "Low confidence" - Few source documents, mostly inferred content
          - Path validation errors - Invalid or inaccessible source_docs_path
    
    Example Response:
        {
            "status": "success",
            "message": "Successfully initialized steering files (5 files created)",
            "files_created": [
                ".kiro/steering/tech-stack.md",
                ".kiro/steering/architecture.md",
                ".kiro/steering/conventions.md",
                ".kiro/steering/project-vision.md"
            ],
            "warnings": ["No source documents found in .kiro/onboarding/"],
            "errors": [],
            "autonomous": true,
            "auto_discover": true,
            "confidence_threshold": 0.7,
            "files_count": 5,
            "source_documents_found": 0,
            "confidence_level": "low",
            "confidence_score": 0.35,
            "metadata": {
                "source_docs_path": null,
                "discovery_stats": {
                    "files_discovered": 0,
                    "files_included": 0
                }
            }
        }
    
    Example Usage from KIRO Chat:
        "Initialize steering files for my project"
        "Initialize steering files using documents from __DEVELOPMENT"
        "Initialize steering with source_docs_path='docs/specs'"
        "Show me what steering files would be generated (dry-run mode)"
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
            copy_files=copy_files,
            config={"skip_debt_detection": skip_debt_detection},
        )
        
        result = workflow.execute()
        response = result.to_dict()

        # Append debt_summary to metadata when debt analysis was performed
        # (Requirements 6.2, 6.3)
        debt_analysis = getattr(getattr(workflow, "_v02_workflow", None), "state", None)
        if debt_analysis is None:
            # Try inner workflow stored on adapter
            inner = getattr(workflow, "_inner_workflow", None)
            debt_analysis = getattr(getattr(inner, "state", None), "debt_analysis", None)
        else:
            debt_analysis = getattr(debt_analysis, "debt_analysis", None)

        if debt_analysis is not None:
            response.setdefault("metadata", {})["debt_summary"] = debt_analysis.metrics.__dict__

        # Return structured JSON response
        return response
    
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
