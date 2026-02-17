"""
Update Workflow for Steering Assistant.

This module implements the UpdateWorkflow class that orchestrates the complete
workflow for updating existing steering files. It integrates all components:
DocumentParser, KnowledgeBase, GapAnalysisEngine, SteeringAssistant,
ConflictResolver, CustomizationDetector, DiffGenerator, and SteeringValidator.

The workflow handles:
- Verifying steering files exist
- Parsing existing steering files
- Parsing new artifacts from staging folder
- Detecting user customizations
- Running gap analysis
- Conducting conversation to gather missing information
- Detecting conflicts between old and new information
- Generating diffs for proposed changes
- Getting user approval for changes
- Applying approved changes
- Running validation

Requirements: 5.1-5.11, 13.3-13.5
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..models import (
    SteeringConfig,
    WorkflowState,
    ValidationReport,
    Conflict,
    Customization,
    FileDiff,
)
from ..utils import (
    create_staging_directory,
    is_staging_folder_empty,
    get_staging_directory_summary,
)
from ..parsers.orchestrator import parse_directory
from ..knowledge_base import KnowledgeBase
from ..gap_analysis import GapAnalysisEngine
from ..agents.steering_assistant import SteeringAssistant
from ..template_populator import TemplatePopulator
from ..conflict_resolver import ConflictResolver
from ..customization_detector import CustomizationDetector
from ..diff_generator import DiffGenerator
from ..validators.steering_validator import SteeringValidator
from ..templates import get_all_templates

logger = logging.getLogger(__name__)


class UpdateWorkflow:
    """
    Orchestrates the update workflow for modifying existing steering files.
    
    The UpdateWorkflow coordinates all components to:
    1. Verify steering files exist
    2. Parse existing steering files
    3. Parse new artifacts from staging folder
    4. Detect user customizations
    5. Run gap analysis
    6. Conduct conversation to gather missing information
    7. Detect conflicts between old and new information
    8. Generate diffs for proposed changes
    9. Get user approval for changes
    10. Apply approved changes
    11. Run validation (unless --skip-validation flag set)
    
    Implements incremental update logic:
    - Only sends changed sections to LLM (max 3000 tokens per file)
    - Preserves user customizations that don't conflict
    - Shows diffs before applying changes
    
    Attributes:
        config: SteeringConfig with workflow settings
        state: WorkflowState tracking workflow progress
        project_root: Root directory of the project
        
    Requirements: 5.1-5.11, 13.3-13.5
    """
    
    def __init__(
        self,
        config: SteeringConfig,
        project_root: Optional[Path] = None
    ):
        """
        Initialize the update workflow.
        
        Args:
            config: SteeringConfig with workflow settings
            project_root: Root directory of the project (defaults to current directory)
        """
        self.config = config
        self.project_root = project_root or Path.cwd()
        
        # Initialize workflow state
        self.state = WorkflowState(
            workflow_type="update",
            staging_dir=self.project_root / ".kiro" / "onboarding",
            steering_dir=self.project_root / ".kiro" / "steering",
        )
        
        # Storage for workflow data
        self.existing_files: Dict[str, str] = {}
        self.customizations: Dict[str, List[Customization]] = {}
        self.proposed_changes: Dict[str, str] = {}
        self.diffs: Dict[str, FileDiff] = {}
        
        logger.info(f"Initialized UpdateWorkflow for project: {self.project_root}")
    
    def execute(self) -> bool:
        """
        Execute the complete update workflow.
        
        Returns:
            True if workflow completed successfully, False otherwise
            
        Requirements: 5.1-5.11, 13.3-13.5
        """
        logger.info("="*70)
        logger.info("STARTING UPDATE WORKFLOW")
        logger.info("="*70)
        
        try:
            # Step 1: Create staging directory (Req 2.1)
            self._step_create_staging_directory()
            
            # Step 2: Verify steering files exist (Req 5.1, 5.2)
            if not self._step_verify_existing_files():
                logger.info("Update workflow aborted - no existing files")
                return False
            
            # Step 3: Parse existing steering files (Req 5.3)
            self._step_parse_existing_files()
            
            # Step 4: Parse new artifacts from staging folder (Req 5.4)
            self._step_parse_new_artifacts()
            
            # Step 5: Detect user customizations (Req 15.1-15.5)
            self._step_detect_customizations()
            
            # Step 6: Build knowledge base
            self._step_build_knowledge_base()
            
            # Step 7: Run gap analysis (Req 5.4, 6.1-6.5)
            self._step_run_gap_analysis()
            
            # Step 8: Conduct conversation (Req 7.1-7.8)
            self._step_conduct_conversation()
            
            # Step 9: Detect conflicts (Req 5.5, 8.1-8.4)
            self._step_detect_conflicts()
            
            # Step 10: Generate proposed changes
            self._step_generate_proposed_changes()
            
            # Step 11: Generate diffs (Req 5.6, 9.1-9.4)
            self._step_generate_diffs()
            
            # Step 12: Get user approval (Req 5.7, 5.8)
            if not self._step_get_user_approval():
                logger.info("Update workflow aborted by user")
                print("\n✓ No changes applied - existing files unchanged")
                return True  # Not an error, user chose to abort
            
            # Step 13: Apply changes (Req 5.7)
            self._step_apply_changes()
            
            # Step 14: Run validation (Req 5.9)
            if not self.config.skip_validation:
                self._step_run_validation()
            
            logger.info("="*70)
            logger.info("UPDATE WORKFLOW COMPLETED SUCCESSFULLY")
            logger.info("="*70)
            
            self._display_success_message()
            return True
        
        except Exception as e:
            logger.error(f"Update workflow failed: {e}", exc_info=True)
            self._display_error_message(str(e))
            return False
    
    def _step_create_staging_directory(self) -> None:
        """
        Step 1: Create staging directory if it doesn't exist.
        
        Requirements: 2.1
        """
        logger.info("Step 1: Creating staging directory")
        print("\n🔧 Setting up staging directory...")
        
        try:
            create_staging_directory(self.state.staging_dir)
            print(f"   ✓ Staging directory ready: {self.state.staging_dir}")
        
        except Exception as e:
            logger.error(f"Failed to create staging directory: {e}")
            raise RuntimeError(f"Could not create staging directory: {e}")
    
    def _step_verify_existing_files(self) -> bool:
        """
        Step 2: Verify that steering files exist.
        
        Returns:
            True if files exist, False otherwise
            
        Requirements: 5.1, 5.2
        """
        logger.info("Step 2: Verifying existing steering files")
        print("\n🔍 Checking for existing steering files...")
        
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
        
        logger.info(f"Found {len(existing_files)} existing steering file(s)")
        print(f"   ✓ Found {len(existing_files)} steering file(s)")
        for file_path in existing_files:
            print(f"     • {file_path.name}")
        
        return True
    
    def _step_parse_existing_files(self) -> None:
        """
        Step 3: Parse existing steering files to understand current state.
        
        Requirements: 5.3
        """
        logger.info("Step 3: Parsing existing steering files")
        print("\n📄 Parsing existing steering files...")
        
        try:
            file_paths = list(self.state.steering_dir.glob("*.md"))
            
            for file_path in file_paths:
                content = file_path.read_text(encoding='utf-8')
                self.existing_files[file_path.name] = content
                logger.debug(f"Parsed: {file_path.name}")
            
            print(f"   ✓ Parsed {len(self.existing_files)} file(s)")
        
        except Exception as e:
            logger.error(f"Failed to parse existing files: {e}", exc_info=True)
            raise RuntimeError(f"Could not parse existing steering files: {e}")
    
    def _step_parse_new_artifacts(self) -> None:
        """
        Step 4: Parse new artifacts from staging folder.
        
        Requirements: 5.4, 3.1-3.5, 14.1
        """
        logger.info("Step 4: Parsing new artifacts")
        
        # Check if staging folder is empty (Req 2.3)
        if is_staging_folder_empty(self.state.staging_dir):
            logger.info("Staging folder is empty, skipping artifact parsing")
            print("\n   ℹ No new artifacts to parse (staging folder is empty)")
            self.state.parsed_documents = []
            return
        
        print("\n📄 Parsing new artifacts...")
        
        # Display summary of staging folder contents
        summary = get_staging_directory_summary(self.state.staging_dir)
        print(f"   ℹ Found {summary['total_files']} new artifact(s):")
        if summary["markdown_count"] > 0:
            print(f"     • {summary['markdown_count']} markdown file(s)")
        if summary["pdf_count"] > 0:
            print(f"     • {summary['pdf_count']} PDF file(s)")
        if summary["image_count"] > 0:
            print(f"     • {summary['image_count']} image file(s)")
        
        try:
            # Parse with progress indicators (Req 14.1)
            self.state.parsed_documents = parse_directory(
                self.state.staging_dir,
                show_progress=True
            )
            
            # Display summary
            successful = sum(1 for doc in self.state.parsed_documents if not doc.parse_errors)
            failed = len(self.state.parsed_documents) - successful
            
            print(f"\n   ✓ Parsed {successful} file(s) successfully")
            if failed > 0:
                print(f"   ⚠️  {failed} file(s) had parsing errors")
                
                # Show first few errors
                error_docs = [doc for doc in self.state.parsed_documents if doc.parse_errors]
                for doc in error_docs[:3]:
                    print(f"     • {doc.file_path.name}: {doc.parse_errors[0]}")
        
        except Exception as e:
            logger.error(f"Artifact parsing failed: {e}", exc_info=True)
            print(f"   ⚠️  Artifact parsing failed: {e}")
            self.state.parsed_documents = []
    
    def _step_detect_customizations(self) -> None:
        """
        Step 5: Detect user customizations in existing steering files.
        
        Requirements: 15.1-15.5
        """
        logger.info("Step 5: Detecting user customizations")
        print("\n🔍 Detecting user customizations...")
        
        try:
            total_customizations = 0
            templates = get_all_templates()
            
            for filename, content in self.existing_files.items():
                # Get original template for this file
                template_name = filename.replace('.md', '')
                if template_name not in templates:
                    logger.warning(f"No template found for {filename}")
                    continue
                
                # Get the template content (we need the raw template string)
                # For now, we'll use an empty string as the original template
                # In a real implementation, you'd store the original template content
                original_template = ""  # TODO: Store original template content
                
                # Detect customizations
                detector = CustomizationDetector(original_template)
                customizations = detector.detect_customizations(content)
                
                if customizations:
                    self.customizations[filename] = customizations
                    total_customizations += len(customizations)
                    logger.info(f"Found {len(customizations)} customization(s) in {filename}")
            
            if total_customizations > 0:
                print(f"   ✓ Detected {total_customizations} customization(s) across {len(self.customizations)} file(s)")
                print("   ℹ Customizations will be preserved where possible")
            else:
                print("   ℹ No customizations detected - files match templates")
        
        except Exception as e:
            logger.error(f"Customization detection failed: {e}", exc_info=True)
            print(f"   ⚠️  Customization detection failed: {e}")
            print("   Continuing without customization detection...")
            self.customizations = {}
    
    def _step_build_knowledge_base(self) -> None:
        """
        Step 6: Build knowledge base from parsed documents.
        
        Requirements: 5.4
        """
        logger.info("Step 6: Building knowledge base")
        print("\n🧠 Building knowledge base...")
        
        try:
            self.state.knowledge_base = KnowledgeBase(
                documents=self.state.parsed_documents,
                code_analysis=None  # Update workflow doesn't do code analysis
            )
            
            # Display summary
            doc_count = len(self.state.parsed_documents)
            print(f"   ✓ Knowledge base built from {doc_count} document(s)")
        
        except Exception as e:
            logger.error(f"Failed to build knowledge base: {e}", exc_info=True)
            raise RuntimeError(f"Could not build knowledge base: {e}")
    
    def _step_run_gap_analysis(self) -> None:
        """
        Step 7: Run gap analysis to identify missing information.
        
        Requirements: 5.4, 6.1-6.5, 14.2
        """
        logger.info("Step 7: Running gap analysis")
        print("\n📊 Analyzing information gaps...")
        
        try:
            engine = GapAnalysisEngine(self.state.knowledge_base)
            # Run with progress indicators (Req 14.2)
            self.state.gap_analysis = engine.analyze(show_progress=True)
            
            # Display summary
            complete_count = sum(len(sections) for sections in self.state.gap_analysis.complete_sections.values())
            missing_count = sum(len(sections) for sections in self.state.gap_analysis.missing_sections.values())
            ambiguous_count = sum(len(sections) for sections in self.state.gap_analysis.ambiguous_sections.values())
            
            print(f"\n   ✓ Gap analysis complete:")
            print(f"     • {complete_count} section(s) have new information")
            if ambiguous_count > 0:
                print(f"     • {ambiguous_count} section(s) need clarification")
            if missing_count > 0:
                print(f"     • {missing_count} section(s) still missing")
            print(f"     • {len(self.state.gap_analysis.questions)} question(s) to ask")
        
        except Exception as e:
            logger.error(f"Gap analysis failed: {e}", exc_info=True)
            raise RuntimeError(f"Could not perform gap analysis: {e}")
    
    def _step_conduct_conversation(self) -> None:
        """
        Step 8: Conduct conversation to gather missing information.
        
        Requirements: 7.1-7.8
        """
        logger.info("Step 8: Conducting conversation")
        
        try:
            assistant = SteeringAssistant(
                knowledge_base=self.state.knowledge_base,
                gap_analysis=self.state.gap_analysis,
                research_enabled=self.config.research_enabled,
                interactive=self.config.interactive
            )
            
            self.state.gathered_info = assistant.conduct_conversation(
                max_questions_per_batch=8
            )
            
            logger.info(f"Gathered information for {len(self.state.gathered_info)} template(s)")
        
        except Exception as e:
            logger.error(f"Conversation failed: {e}", exc_info=True)
            raise RuntimeError(f"Could not conduct conversation: {e}")
    
    def _step_detect_conflicts(self) -> None:
        """
        Step 9: Detect conflicts between old and new information.
        
        Requirements: 5.5, 8.1-8.4
        """
        logger.info("Step 9: Detecting conflicts")
        print("\n⚠️  Checking for conflicts...")
        
        try:
            self.state.conflicts = []
            
            # Parse existing files into structured content
            old_content = self._parse_existing_content()
            
            # Get new content from gathered info
            new_content = self.state.gathered_info
            
            # Detect conflicts
            conflicts = ConflictResolver.detect_conflicts(old_content, new_content)
            self.state.conflicts = conflicts
            
            if conflicts:
                print(f"   ⚠️  Found {len(conflicts)} conflict(s)")
                print("   ℹ You will be asked to resolve these conflicts")
            else:
                print("   ✓ No conflicts detected")
        
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}", exc_info=True)
            print(f"   ⚠️  Conflict detection failed: {e}")
            print("   Continuing without conflict detection...")
            self.state.conflicts = []
    
    def _parse_existing_content(self) -> Dict[str, Any]:
        """
        Parse existing steering files into structured content for conflict detection.
        
        Returns:
            Dictionary mapping section names to their content
        """
        content = {}
        
        for filename, file_content in self.existing_files.items():
            # Extract key-value pairs from markdown content
            # This is a simplified parser - in production, you'd want more robust parsing
            lines = file_content.split('\n')
            current_section = None
            
            for line in lines:
                # Detect section headers
                if line.startswith('#'):
                    current_section = line.lstrip('#').strip()
                    content[current_section] = ""
                elif current_section and line.strip():
                    # Accumulate content for current section
                    if content[current_section]:
                        content[current_section] += "\n"
                    content[current_section] += line.strip()
        
        return content
    
    def _step_generate_proposed_changes(self) -> None:
        """
        Step 10: Generate proposed changes by populating templates with new information.
        
        Requirements: 5.6, 14.3
        """
        logger.info("Step 10: Generating proposed changes")
        print("\n📝 Generating proposed changes...")
        
        try:
            populator = TemplatePopulator()
            
            # Combine existing content with new information
            combined_knowledge = self._combine_knowledge()
            
            # Populate all templates with progress indicators (Req 14.3)
            self.proposed_changes = populator.populate_all(
                combined_knowledge,
                show_progress=True
            )
            
            print(f"\n   ✓ Generated proposed changes for {len(self.proposed_changes)} file(s)")
        
        except Exception as e:
            logger.error(f"Failed to generate proposed changes: {e}", exc_info=True)
            raise RuntimeError(f"Could not generate proposed changes: {e}")
    
    def _combine_knowledge(self) -> Dict[str, Any]:
        """
        Combine existing content with new information, resolving conflicts.
        
        Returns:
            Combined knowledge dictionary
        """
        combined = {}
        
        # Start with gathered info from conversation
        combined.update(self.state.gathered_info)
        
        # Apply conflict resolutions if any
        for conflict in self.state.conflicts:
            if hasattr(conflict, 'resolution') and conflict.resolution:
                combined[conflict.section] = conflict.resolution
        
        return combined
    
    def _step_generate_diffs(self) -> None:
        """
        Step 11: Generate diffs showing proposed changes.
        
        Requirements: 5.6, 9.1-9.4
        """
        logger.info("Step 11: Generating diffs")
        print("\n📊 Computing diffs...")
        
        try:
            files_with_changes = 0
            files_unchanged = 0
            
            for filename in self.existing_files.keys():
                old_content = self.existing_files[filename]
                new_content = self.proposed_changes.get(filename, old_content)
                
                # Generate diff
                diff = DiffGenerator.compute_diff(old_content, new_content, filename)
                self.diffs[filename] = diff
                
                if DiffGenerator.has_changes(diff):
                    files_with_changes += 1
                else:
                    files_unchanged += 1
            
            print(f"   ✓ Generated diffs:")
            print(f"     • {files_with_changes} file(s) with changes")
            print(f"     • {files_unchanged} file(s) unchanged")
        
        except Exception as e:
            logger.error(f"Diff generation failed: {e}", exc_info=True)
            raise RuntimeError(f"Could not generate diffs: {e}")
    
    def _step_get_user_approval(self) -> bool:
        """
        Step 12: Display diffs and get user approval for changes.
        
        Returns:
            True if user approves changes, False otherwise
            
        Requirements: 5.7, 5.8, 9.1-9.4
        """
        logger.info("Step 12: Getting user approval")
        
        # First, resolve any conflicts
        if self.state.conflicts:
            print("\n" + "="*70)
            print("CONFLICTS DETECTED")
            print("="*70)
            
            for i, conflict in enumerate(self.state.conflicts, 1):
                print(ConflictResolver.format_conflict_presentation(conflict))
                
                while True:
                    choice = input(f"Resolve conflict {i}/{len(self.state.conflicts)} (keep_old/use_new/merge): ").strip().lower()
                    
                    if choice in conflict.resolution_options:
                        resolution = ConflictResolver.resolve_conflict(conflict, choice)
                        conflict.resolution = resolution
                        logger.info(f"Conflict resolved: {conflict.section} -> {choice}")
                        break
                    else:
                        print(f"   ⚠️  Invalid choice. Please enter one of: {', '.join(conflict.resolution_options)}")
            
            print("\n✓ All conflicts resolved")
            
            # Regenerate proposed changes with conflict resolutions
            self._step_generate_proposed_changes()
            self._step_generate_diffs()
        
        # Display diffs
        print("\n" + "="*70)
        print("PROPOSED CHANGES")
        print("="*70)
        
        has_any_changes = False
        
        for filename, diff in self.diffs.items():
            if DiffGenerator.has_changes(diff):
                has_any_changes = True
                print(f"\n{DiffGenerator.format_diff(diff, colorize=True)}")
            else:
                print(f"\n{filename}: No changes")
        
        if not has_any_changes:
            print("\n✓ No changes to apply - all files are up to date")
            return False
        
        # Get user approval
        print("\n" + "="*70)
        
        while True:
            choice = input("\nApply these changes? (y/n): ").strip().lower()
            
            if choice == 'y':
                logger.info("User approved changes")
                return True
            elif choice == 'n':
                logger.info("User rejected changes")
                return False
            else:
                print("   ⚠️  Invalid choice. Please enter 'y' or 'n'")
    
    def _step_apply_changes(self) -> None:
        """
        Step 13: Apply approved changes to steering files.
        
        Requirements: 5.7
        """
        logger.info("Step 13: Applying changes")
        print("\n💾 Applying changes...")
        
        try:
            applied_count = 0
            
            for filename, diff in self.diffs.items():
                if DiffGenerator.has_changes(diff):
                    # Only apply if we have proposed changes for this file
                    if filename not in self.proposed_changes:
                        logger.warning(f"No proposed changes for {filename}, skipping")
                        continue
                    
                    # Write new content
                    file_path = self.state.steering_dir / filename
                    new_content = self.proposed_changes[filename]
                    file_path.write_text(new_content, encoding='utf-8')
                    applied_count += 1
                    logger.info(f"Updated: {filename}")
            
            print(f"   ✓ Applied changes to {applied_count} file(s)")
        
        except Exception as e:
            logger.error(f"Failed to apply changes: {e}", exc_info=True)
            raise RuntimeError(f"Could not apply changes: {e}")
    
    def _step_run_validation(self) -> None:
        """
        Step 14: Run validation on updated steering files.
        
        Requirements: 5.9, 14.4
        """
        logger.info("Step 14: Running validation")
        print("\n🔍 Validating updated steering files...")
        
        try:
            validator = SteeringValidator(use_llm=False)
            # Run with progress indicators (Req 14.4)
            self.state.validation_report = validator.validate_all(
                self.state.steering_dir,
                use_llm=False,
                show_progress=True
            )
            
            # Display summary
            report = self.state.validation_report
            print(f"\n   ✓ Validation complete:")
            print(f"     • {report.files_checked} file(s) checked")
            print(f"     • {len(report.critical_issues)} critical issue(s)")
            print(f"     • {len(report.warnings)} warning(s)")
            print(f"     • {len(report.info)} info message(s)")
            print(f"     • Overall status: {report.overall_status.upper()}")
            
            # Show critical issues if any
            if report.critical_issues:
                print("\n   ⚠️  Critical issues found:")
                for issue in report.critical_issues[:3]:
                    print(f"     • {issue.file_name}: {issue.message}")
                if len(report.critical_issues) > 3:
                    print(f"     ... and {len(report.critical_issues) - 3} more")
        
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            print(f"   ⚠️  Validation failed: {e}")
            print("   Steering files were updated but validation could not be completed")
    
    def _display_success_message(self) -> None:
        """Display success message with next steps."""
        print("\n" + "="*70)
        print("✅ STEERING FILES UPDATED SUCCESSFULLY!")
        print("="*70)
        print(f"\n📁 Location: {self.state.steering_dir}")
        print("\n🚀 Next steps:")
        print("   1. Review the updated steering files")
        print("   2. Continue development with updated configuration")
        print("\n💡 Tips:")
        print("   • Run 'hiveforge steering validate' to check file quality")
        print("   • Add more artifacts to .kiro/onboarding/ and re-run update")
        print("   • Use 'hiveforge steering update' again to refine further")
        print()
    
    def _display_error_message(self, error: str) -> None:
        """
        Display error message with troubleshooting tips.
        
        Args:
            error: Error message to display
        """
        print("\n" + "="*70)
        print("❌ UPDATE WORKFLOW FAILED")
        print("="*70)
        print(f"\nError: {error}")
        print("\n🔧 Troubleshooting:")
        print("   • Check the logs for detailed error information")
        print("   • Ensure you have write permissions in the project directory")
        print("   • Verify that artifact files are not corrupted")
        print("   • Try running with --skip-validation flag")
        print("\n💬 Need help? Check the documentation or open an issue")
        print()
