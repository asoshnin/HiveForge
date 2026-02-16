"""
CLI command handler for Steering Assistant.

This module implements the CLI commands for the Steering Assistant feature:
- hiveforge steering init: Create steering files from scratch
- hiveforge steering update: Update existing steering files
- hiveforge steering validate: Validate steering file quality

Requirements: 1.1-1.8
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer

from .models import SteeringConfig
from .workflows.init_workflow import InitWorkflow
from .workflows.update_workflow import UpdateWorkflow
from .workflows.validate_workflow import ValidateWorkflow

# Create steering subcommand app
app = typer.Typer(
    name="steering",
    help="Manage steering files for HiveForge projects",
    add_completion=False
)

# Configure logging
logger = logging.getLogger(__name__)


@app.command("init")
def steering_init(
    research: bool = typer.Option(
        False,
        "--research",
        help="Enable web research to find missing information"
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip automatic validation after generation"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Enable or disable interactive conversation mode"
    ),
    analyze_code: bool = typer.Option(
        False,
        "--analyze-code",
        help="Analyze existing codebase to extract project information"
    ),
) -> None:
    """
    Initialize steering files from scratch.
    
    Creates all 8 steering files by:
    1. Optionally analyzing existing codebase (with --analyze-code)
    2. Parsing artifacts from .kiro/onboarding/
    3. Conducting conversation to gather missing information
    4. Generating steering files in .kiro/steering/
    5. Validating generated files (unless --skip-validation)
    
    Examples:
        # Create steering files with conversation
        hiveforge steering init
        
        # Import existing codebase
        hiveforge steering init --analyze-code
        
        # Non-interactive mode (use only artifacts)
        hiveforge steering init --no-interactive
        
        # Enable web research for missing info
        hiveforge steering init --research
    
    Requirements: 1.1, 1.4, 1.5, 1.6, 1.7
    """
    try:
        # Create configuration
        config = SteeringConfig(
            research_enabled=research,
            skip_validation=skip_validation,
            interactive=interactive,
            analyze_code=analyze_code,
            backup_enabled=True,
            backup_dir=Path.cwd() / ".kiro" / "backups"
        )
        
        # Create and execute workflow
        workflow = InitWorkflow(config=config, project_root=Path.cwd())
        success = workflow.execute()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        typer.secho("\n\n⚠️  Operation cancelled by user", fg=typer.colors.YELLOW)
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Init command failed: {e}", exc_info=True)
        typer.secho(f"\n❌ Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


@app.command("update")
def steering_update(
    research: bool = typer.Option(
        False,
        "--research",
        help="Enable web research to find missing information"
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip automatic validation after update"
    ),
    interactive: bool = typer.Option(
        True,
        "--interactive/--no-interactive",
        help="Enable or disable interactive conversation mode"
    ),
) -> None:
    """
    Update existing steering files with new information.
    
    Updates steering files by:
    1. Parsing existing steering files
    2. Parsing new artifacts from .kiro/onboarding/
    3. Detecting user customizations
    4. Conducting conversation to gather missing information
    5. Detecting conflicts between old and new information
    6. Showing diffs and getting user approval
    7. Applying approved changes
    8. Validating updated files (unless --skip-validation)
    
    Examples:
        # Update with new artifacts
        hiveforge steering update
        
        # Non-interactive mode
        hiveforge steering update --no-interactive
        
        # Enable web research
        hiveforge steering update --research
        
        # Skip validation
        hiveforge steering update --skip-validation
    
    Requirements: 1.2, 1.5, 1.6, 1.7
    """
    try:
        # Create configuration
        config = SteeringConfig(
            research_enabled=research,
            skip_validation=skip_validation,
            interactive=interactive,
            analyze_code=False,  # Update doesn't do code analysis
            backup_enabled=True,
            backup_dir=Path.cwd() / ".kiro" / "backups"
        )
        
        # Create and execute workflow
        workflow = UpdateWorkflow(config=config, project_root=Path.cwd())
        success = workflow.execute()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        typer.secho("\n\n⚠️  Operation cancelled by user", fg=typer.colors.YELLOW)
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Update command failed: {e}", exc_info=True)
        typer.secho(f"\n❌ Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


@app.command("validate")
def steering_validate(
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Treat warnings as errors (exit with non-zero code)"
    ),
) -> None:
    """
    Validate steering files for completeness and consistency.
    
    Validates steering files by:
    1. Checking all required sections are populated
    2. Verifying template structure and frontmatter
    3. Detecting contradictions across files
    4. Generating comprehensive validation report
    
    Exit codes:
        0: Validation passed (or only warnings in non-strict mode)
        1: Validation failed (critical issues or warnings in strict mode)
    
    Examples:
        # Validate steering files
        hiveforge steering validate
        
        # Strict mode (warnings as errors)
        hiveforge steering validate --strict
    
    Requirements: 1.3, 1.7
    """
    try:
        # Create configuration
        config = SteeringConfig(
            strict_mode=strict,
            research_enabled=False,
            skip_validation=False,
            interactive=False,
            analyze_code=False,
            backup_enabled=False
        )
        
        # Create and execute workflow
        workflow = ValidateWorkflow(config=config, project_root=Path.cwd())
        exit_code = workflow.execute()
        
        # Exit with workflow's exit code
        sys.exit(exit_code)
    
    except KeyboardInterrupt:
        typer.secho("\n\n⚠️  Operation cancelled by user", fg=typer.colors.YELLOW)
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Validate command failed: {e}", exc_info=True)
        typer.secho(f"\n❌ Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


@app.callback(invoke_without_command=True)
def steering_callback(ctx: typer.Context) -> None:
    """
    Steering file management commands.
    
    The steering assistant helps you create and maintain steering files
    throughout your project's lifecycle.
    
    Requirements: 1.8
    """
    # If no subcommand provided, show help
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        sys.exit(0)


if __name__ == "__main__":
    app()
