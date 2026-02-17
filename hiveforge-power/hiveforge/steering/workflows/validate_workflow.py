"""
Validate Workflow for Steering Assistant.

This module implements the ValidateWorkflow class that orchestrates the complete
workflow for validating existing steering files. It provides standalone validation
that can be run independently or as part of init/update workflows.

The workflow handles:
- Verifying steering files exist
- Running validator on all files
- Generating comprehensive validation report
- Displaying report to user
- Returning appropriate exit code based on findings

Requirements: 11.1-11.7
"""

import logging
from pathlib import Path
from typing import Optional

from ..models import SteeringConfig, WorkflowState, ValidationReport
from ..validators.steering_validator import SteeringValidator

logger = logging.getLogger(__name__)


class ValidateWorkflow:
    """
    Orchestrates the validate workflow for checking steering file quality.
    
    The ValidateWorkflow coordinates validation to:
    1. Verify steering files exist
    2. Run validator on all files
    3. Generate comprehensive validation report
    4. Display report to user with color-coded output
    5. Return appropriate exit code (0 for pass, non-zero for fail)
    
    Supports --strict flag to treat warnings as errors.
    
    Attributes:
        config: SteeringConfig with workflow settings
        state: WorkflowState tracking workflow progress
        project_root: Root directory of the project
        
    Requirements: 11.1-11.7
    """
    
    def __init__(
        self,
        config: SteeringConfig,
        project_root: Optional[Path] = None
    ):
        """
        Initialize the validate workflow.
        
        Args:
            config: SteeringConfig with workflow settings
            project_root: Root directory of the project (defaults to current directory)
        """
        self.config = config
        self.project_root = project_root or Path.cwd()
        
        # Initialize workflow state
        self.state = WorkflowState(
            workflow_type="validate",
            staging_dir=self.project_root / ".kiro" / "onboarding",
            steering_dir=self.project_root / ".kiro" / "steering",
        )
        
        logger.info(f"Initialized ValidateWorkflow for project: {self.project_root}")
    
    def execute(self) -> int:
        """
        Execute the complete validate workflow.
        
        Returns:
            Exit code: 0 if validation passes, non-zero if validation fails
            
        Requirements: 11.1-11.7
        """
        logger.info("="*70)
        logger.info("STARTING VALIDATE WORKFLOW")
        logger.info("="*70)
        
        try:
            # Step 1: Verify steering files exist (Req 11.1, 11.2)
            if not self._step_verify_files_exist():
                logger.info("Validate workflow aborted - no files to validate")
                return 1
            
            # Step 2: Run validator (Req 11.3)
            self._step_run_validator()
            
            # Step 3: Display report (Req 11.4)
            self._step_display_report()
            
            # Step 4: Determine exit code (Req 11.5, 11.6, 11.7)
            exit_code = self._determine_exit_code()
            
            logger.info("="*70)
            logger.info(f"VALIDATE WORKFLOW COMPLETED (exit code: {exit_code})")
            logger.info("="*70)
            
            return exit_code
        
        except Exception as e:
            logger.error(f"Validate workflow failed: {e}", exc_info=True)
            self._display_error_message(str(e))
            return 1
    
    def _step_verify_files_exist(self) -> bool:
        """
        Step 1: Verify that steering files exist.
        
        Returns:
            True if files exist, False otherwise
            
        Requirements: 11.1, 11.2
        """
        logger.info("Step 1: Verifying steering files exist")
        print("\n🔍 Checking for steering files...")
        
        # Check if steering directory exists
        if not self.state.steering_dir.exists():
            logger.warning("Steering directory does not exist")
            print("\n❌ ERROR: No steering directory found")
            print(f"   Expected location: {self.state.steering_dir}")
            print("\n💡 Suggestion: Use 'hiveforge steering init' to create steering files first")
            return False
        
        # Check for steering files
        existing_files = list(self.state.steering_dir.glob("*.md"))
        if not existing_files:
            logger.warning("Steering directory exists but is empty")
            print("\n❌ ERROR: No steering files found")
            print(f"   Directory: {self.state.steering_dir}")
            print("\n💡 Suggestion: Use 'hiveforge steering init' to create steering files first")
            return False
        
        logger.info(f"Found {len(existing_files)} steering file(s)")
        print(f"   ✓ Found {len(existing_files)} steering file(s) to validate")
        
        return True
    
    def _step_run_validator(self) -> None:
        """
        Step 2: Run validator on all steering files.
        
        Requirements: 11.3, 14.4
        """
        logger.info("Step 2: Running validator")
        print("\n🔍 Validating steering files...")
        
        try:
            # Create validator (use LLM only if explicitly enabled)
            validator = SteeringValidator(use_llm=False)
            
            # Run validation with progress indicators (Req 14.4)
            self.state.validation_report = validator.validate_all(
                self.state.steering_dir,
                use_llm=False,
                show_progress=True
            )
            
            logger.info(f"Validation complete: {self.state.validation_report.overall_status}")
        
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            raise RuntimeError(f"Could not validate steering files: {e}")
    
    def _step_display_report(self) -> None:
        """
        Step 3: Display validation report to user.
        
        Requirements: 11.4
        """
        logger.info("Step 3: Displaying validation report")
        
        report = self.state.validation_report
        
        # Display header
        print("\n" + "="*70)
        print("VALIDATION REPORT")
        print("="*70)
        
        # Display summary
        print(f"\n📊 Summary:")
        print(f"   • Files checked: {report.files_checked}")
        print(f"   • Critical issues: {len(report.critical_issues)}")
        print(f"   • Warnings: {len(report.warnings)}")
        print(f"   • Info messages: {len(report.info)}")
        print(f"   • Overall status: {report.overall_status.upper()}")
        
        # Display critical issues
        if report.critical_issues:
            print("\n❌ Critical Issues:")
            for issue in report.critical_issues:
                self._display_issue(issue)
        
        # Display warnings
        if report.warnings:
            print("\n⚠️  Warnings:")
            for issue in report.warnings:
                self._display_issue(issue)
        
        # Display info messages
        if report.info:
            print("\nℹ️  Info:")
            for issue in report.info:
                self._display_issue(issue)
        
        # Display footer
        print("\n" + "="*70)
        
        # Display final status message
        if report.overall_status == "pass":
            if report.warnings:
                print("✅ Validation passed with warnings")
            else:
                print("✅ All checks passed!")
        else:
            print("❌ Validation failed - fix critical issues and re-run")
        
        print("="*70)
    
    def _display_issue(self, issue) -> None:
        """
        Display a single validation issue with formatting.
        
        Args:
            issue: ValidationIssue to display
        """
        # Format file and line info
        location = f"{issue.file_name}"
        if issue.line_number is not None:
            location += f":{issue.line_number}"
        
        # Display issue
        print(f"\n   [{issue.issue_type}] {location}")
        print(f"   {issue.message}")
        
        # Display suggestion if available
        if issue.suggestion:
            print(f"   💡 Suggestion: {issue.suggestion}")
    
    def _determine_exit_code(self) -> int:
        """
        Step 4: Determine appropriate exit code based on validation results.
        
        Returns:
            0 if validation passes, non-zero if validation fails
            
        Requirements: 11.5, 11.6, 11.7
        """
        logger.info("Step 4: Determining exit code")
        
        report = self.state.validation_report
        
        # Critical issues always result in non-zero exit code (Req 11.5)
        if report.critical_issues:
            logger.info("Exit code: 1 (critical issues found)")
            return 1
        
        # In strict mode, warnings are treated as errors (Req 11.7)
        if self.config.strict_mode and report.warnings:
            logger.info("Exit code: 1 (warnings in strict mode)")
            print("\n⚠️  Note: Running in strict mode - warnings treated as errors")
            return 1
        
        # Only warnings or info messages - success (Req 11.6)
        logger.info("Exit code: 0 (validation passed)")
        return 0
    
    def _display_error_message(self, error: str) -> None:
        """
        Display error message with troubleshooting tips.
        
        Args:
            error: Error message to display
        """
        print("\n" + "="*70)
        print("❌ VALIDATION WORKFLOW FAILED")
        print("="*70)
        print(f"\nError: {error}")
        print("\n🔧 Troubleshooting:")
        print("   • Check the logs for detailed error information")
        print("   • Ensure steering files exist in .kiro/steering/")
        print("   • Verify file permissions allow reading")
        print("   • Check that files are valid markdown format")
        print("\n💬 Need help? Check the documentation or open an issue")
        print()
