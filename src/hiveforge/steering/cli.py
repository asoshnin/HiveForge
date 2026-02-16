"""
CLI command handler for Steering Assistant.

This module implements the CLI commands for the Steering Assistant feature:
- hiveforge steering init: Create steering files from scratch
- hiveforge steering update: Update existing steering files
- hiveforge steering validate: Validate steering file quality

Requirements: 1.1-1.8, 18.1-18.8, 24.2-24.4, 26.6
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

import typer

from .models import SteeringConfig, FeatureFlagConfig
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
    use_autonomous_generation: bool = typer.Option(
        False,
        "--use-autonomous-generation",
        help="Enable autonomous generation workflow (v02)"
    ),
    confidence_threshold: float = typer.Option(
        0.7,
        "--confidence-threshold",
        min=0.0,
        max=1.0,
        help="Confidence threshold for autonomous generation (0.0-1.0)"
    ),
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        help="Maximum tokens for LLM context"
    ),
    discovery_paths: List[str] = typer.Option(
        [],
        "--discovery-paths",
        help="Custom search locations for discovery"
    ),
    preserve_all: bool = typer.Option(
        False,
        "--preserve-all",
        help="Skip updates to customized sections"
    ),
    telemetry_off: bool = typer.Option(
        False,
        "--telemetry-off",
        help="Disable telemetry data collection"
    ),
    max_discovery_files: int = typer.Option(
        1000,
        "--max-discovery-files",
        help="Maximum files to discover"
    ),
    max_file_size: int = typer.Option(
        10,
        "--max-file-size",
        help="Maximum file size in MB for discovery"
    ),
    conservative_inference: bool = typer.Option(
        False,
        "--conservative-inference",
        help="Reduce inference aggressiveness"
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
        # Create feature flag configuration
        feature_flags = FeatureFlagConfig(
            use_autonomous_generation=use_autonomous_generation,
            confidence_threshold=confidence_threshold,
            max_tokens=max_tokens,
            discovery_paths=discovery_paths,
            preserve_all=preserve_all,
            telemetry_off=telemetry_off,
            max_discovery_files=max_discovery_files,
            max_file_size_mb=max_file_size,
            conservative_inference=conservative_inference,
            interactive=not interactive,  # --no-interactive sets interactive=True
        )
        
        # Validate feature flags
        errors = feature_flags.validate()
        if errors:
            for error in errors:
                typer.secho(f"Warning: {error}", fg=typer.colors.YELLOW)
        
        # Create configuration
        config = SteeringConfig(
            research_enabled=research,
            skip_validation=skip_validation,
            interactive=interactive,
            analyze_code=analyze_code,
            backup_enabled=True,
            backup_dir=Path.cwd() / ".kiro" / "backups",
            feature_flags=feature_flags,
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
    incremental: bool = typer.Option(
        False,
        "--incremental",
        help="Force incremental update mode (v02)"
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        help="Display changes without writing"
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
    
    Requirements: 1.2, 1.5, 1.6, 1.7, 20.1-20.7, 23.1-23.8
    """
    try:
        # Create configuration
        config = SteeringConfig(
            research_enabled=research,
            skip_validation=skip_validation,
            interactive=interactive,
            analyze_code=False,  # Update doesn't do code analysis
            backup_enabled=True,
            backup_dir=Path.cwd() / ".kiro" / "backups",
            incremental=incremental,
            preview=preview,
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

@app.command("rollback")
def steering_rollback(
    list_backups: bool = typer.Option(
        False,
        "--list",
        help="List available backups instead of restoring"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview changes without writing files"
    ),
    backup_name: Optional[str] = typer.Option(
        None,
        "--backup",
        help="Name of backup to restore (defaults to latest)"
    ),
) -> None:
    """
    Rollback steering files to a previous version.
    
    Restores steering files from a previous backup:
    1. Lists available backups (with --list)
    2. Selects backup to restore (or use latest)
    3. Shows preview of changes (with --dry-run)
    4. Restores files from backup
    
    Examples:
        # List available backups
        hiveforge steering rollback --list
        
        # Restore to latest backup
        hiveforge steering rollback
        
        # Preview changes before committing
        hiveforge steering rollback --dry-run
        
        # Restore to specific backup
        hiveforge steering rollback --backup backup_20260216_143045
    
    Requirements: 9.1-9.7, 20.1-20.7
    """
    try:
        from .backup_manager import BackupManager
        
        backup_dir = Path.cwd() / ".kiro" / "backups" / "steering"
        backup_manager = BackupManager(backup_dir=backup_dir)
        
        # List backups if requested
        if list_backups:
            backups = backup_manager.list_backups()
            
            if not backups:
                typer.secho("No backups found.", fg=typer.colors.YELLOW)
                sys.exit(0)
            
            typer.secho("\nAvailable backups:", fg=typer.colors.CYAN)
            for i, backup in enumerate(backups, 1):
                typer.echo(f"  {i}. {backup['name']}")
                typer.echo(f"     Timestamp: {backup['timestamp']}")
                typer.echo(f"     Files: {backup['file_count']}")
            
            sys.exit(0)
        
        # Get backup to restore
        if backup_name:
            backup_path = backup_dir / backup_name
            if not backup_path.exists():
                typer.secho(f"Backup not found: {backup_name}", fg=typer.colors.RED)
                sys.exit(1)
        else:
            backup_path = backup_manager.get_latest_backup()
            if backup_path is None:
                typer.secho("No backups found.", fg=typer.colors.YELLOW)
                sys.exit(1)
        
        # Get target directory
        target_dir = Path.cwd() / ".kiro" / "steering"
        
        # Show preview if dry-run
        if dry_run:
            typer.secho(f"\nPreview of rollback to {backup_path.name}:", fg=typer.colors.CYAN)
            typer.echo(f"Target directory: {target_dir}")
            
            # Show files that would be restored
            files_to_restore = list(backup_path.glob("*.md"))
            typer.echo(f"\nFiles to restore ({len(files_to_restore)}):")
            for file_path in files_to_restore:
                typer.echo(f"  - {file_path.name}")
            
            typer.echo("\n(No changes written - use without --dry-run to apply)")
            sys.exit(0)
        
        # Restore backup
        restored_files = backup_manager.restore_backup(backup_path, target_dir)
        
        typer.secho(f"\n✓ Restored {len(restored_files)} file(s) from {backup_path.name}", fg=typer.colors.GREEN)
        for file_path in restored_files:
            typer.echo(f"  - {file_path.name}")
        
        sys.exit(0)
    
    except KeyboardInterrupt:
        typer.secho("\n\n⚠️  Operation cancelled by user", fg=typer.colors.YELLOW)
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Rollback command failed: {e}", exc_info=True)
        typer.secho(f"\n❌ Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)


@app.command("calibrate")
def steering_calibrate(
    calibrate_confidence: bool = typer.Option(
        False,
        "--calibrate-confidence",
        help="Run confidence calibration analysis"
    ),
) -> None:
    """
    Run calibration analysis for confidence scores.
    
    Examples:
        # Run confidence calibration
        hiveforge steering calibrate --calibrate-confidence
    
    Requirements: 22.6
    """
    try:
        if calibrate_confidence:
            typer.secho("\nConfidence calibration analysis (stub for v02.1)", fg=typer.colors.YELLOW)
            typer.echo("This feature will be implemented in v02.1")
        else:
            typer.echo("Usage: hiveforge steering calibrate --calibrate-confidence")
        
        sys.exit(0)
    
    except KeyboardInterrupt:
        typer.secho("\n\n⚠️  Operation cancelled by user", fg=typer.colors.YELLOW)
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Calibrate command failed: {e}", exc_info=True)
        typer.secho(f"\n❌ Error: {e}", fg=typer.colors.RED, err=True)
        sys.exit(1)