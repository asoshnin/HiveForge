"""
Autonomous Workflow for Steering Assistant v02.

This module implements the AutonomousWorkflow class that extends InitWorkflow
to provide autonomous generation with confidence scoring, semantic validation,
and fallback to question-asking workflow when needed.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..models import (
    SteeringConfig,
    WorkflowState,
    CodeAnalysisResult,
    ValidationReport,
    FeatureFlagConfig,
    ConfidenceScore,
)
from ..feature_flags import FeatureFlagManager
from ..confidence_scorer import ConfidenceScorer
from ..validators.steering_validator import SteeringValidator
from ..validators.validation_rules_loader import ValidationRulesLoader
from ..validators.tech_stack_validator import TechStackValidator
from ..validators.contradiction_detector import ContradictionDetector
from .init_workflow import InitWorkflow

logger = logging.getLogger(__name__)


class AutonomousWorkflow(InitWorkflow):
    """
    Orchestrates autonomous generation of steering files.
    
    Extends InitWorkflow to provide:
    - Sequential file generation (one at a time with shared context)
    - Confidence scoring for generated content
    - Rule-based semantic validation
    - Fallback to question-asking workflow when confidence is low
    - Token budget management
    
    Attributes:
        config: SteeringConfig with workflow settings
        feature_flag_config: FeatureFlagConfig for autonomous generation settings
        feature_flag_manager: FeatureFlagManager for flag handling
        confidence_scorer: ConfidenceScorer for scoring generated content
        validator: SteeringValidator for semantic validation
        validation_rules_loader: ValidationRulesLoader for loading rules
        framework_classifications: Framework classification database
        rules: List of validation rules
        generated_files: Dictionary of generated file contents
        confidence_scores: Dictionary of confidence scores per file
        fallback_triggered: Whether fallback was triggered for any file
        
    Requirements: 3.1-3.10, 16.8-16.11, 25.1-25.7
    """
    
    # Order for generating steering files
    GENERATION_ORDER = [
        "project-vision.md",
        "tech-stack.md",
        "architecture.md",
        "conventions.md",
        "api-standards.md",
        "db-standards.md",
        "qa-standards.md",
        "ui-standards.md",
    ]
    
    def __init__(
        self,
        config: SteeringConfig,
        feature_flag_config: FeatureFlagConfig,
        project_root: Optional[Path] = None,
    ):
        """
        Initialize the autonomous workflow.
        
        Args:
            config: SteeringConfig with workflow settings
            feature_flag_config: FeatureFlagConfig for autonomous generation
            project_root: Root directory of the project (defaults to current directory)
        """
        super().__init__(config, project_root)
        
        self.feature_flag_config = feature_flag_config
        self.feature_flag_manager = FeatureFlagManager(feature_flag_config)
        self.confidence_scorer = ConfidenceScorer()
        
        # Initialize validators
        self.validator = SteeringValidator(use_llm=False)
        self.validation_rules_loader = ValidationRulesLoader()
        
        # Load validation rules
        try:
            self.framework_classifications = self.validation_rules_loader.get_framework_classifications()
            self.rules = self.validation_rules_loader.get_rules()
        except Exception as e:
            logger.warning(f"Failed to load validation rules: {e}")
            self.framework_classifications = {}
            self.rules = []
        
        # Track generated files and confidence
        self.generated_files: Dict[str, str] = {}
        self.confidence_scores: Dict[str, ConfidenceScore] = {}
        self.fallback_triggered: bool = False
        self.fallback_reasons: List[str] = []
        
        logger.info(f"Initialized AutonomousWorkflow for project: {self.project_root}")
    
    def execute(self) -> bool:
        """
        Execute the autonomous generation workflow.
        
        Workflow Steps:
        1. Create staging directory
        2. Check for existing steering files
        3. Analyze codebase (if enabled)
        4. Parse artifacts from staging folder
        5. Build knowledge base
        6. Run gap analysis
        7. Generate files autonomously
        7.5. Review draft (P1-3):
             - CLI mode: Prompt user for approval
             - MCP mode: Store draft in self.state.draft for IDE review
        8. Write files (only if approved in CLI or after MCP approval)
        9. Run validation (if not skipped)
        
        Draft Review Integration (P1-3):
        - _step_review_draft() is called after file generation (step 7)
        - In CLI mode (interactive=True):
          * Prints draft summary with confidence scores
          * Prompts user to approve/reject
          * Returns True if approved (proceed to write files)
          * Returns False if rejected (abort workflow)
        - In MCP mode (interactive=False):
          * Stores draft in self.state.draft
          * Returns False (don't write files yet)
          * Caller must include draft in WorkflowResult.metadata
          * User calls update_steering(apply_draft=True) to write files
        
        Returns:
            True if workflow completed successfully, False otherwise
            
        Requirements: 3.1-3.10, 16.8-16.11, 25.1-25.7, P1-3
        """
        logger.info("="*70)
        logger.info("STARTING AUTONOMOUS GENERATION WORKFLOW")
        logger.info("="*70)
        
        try:
            # Step 1: Create staging directory
            self._step_create_staging_directory()
            
            # Step 2: Check for existing steering files
            if not self._step_check_existing_files():
                logger.info("Autonomous workflow aborted by user")
                return False
            
            # Step 3: Analyze codebase
            if self.config.analyze_code:
                self._step_analyze_code()
            
            # Step 4: Parse artifacts from staging folder
            self._step_parse_artifacts()
            
            # Step 5: Build knowledge base
            self._step_build_knowledge_base()
            
            # Step 6: Run gap analysis
            self._step_run_gap_analysis()
            
            # Step 7: Generate files autonomously
            self._step_generate_files_autonomously()
            
            # Step 7.5: Review draft (NEW - P1-3)
            if not self._step_review_draft():
                # Draft not approved or in MCP mode - don't write files
                logger.info("Draft review: files not written")
                if not self.config.interactive:
                    # MCP mode: return success with draft stored
                    logger.info("MCP mode: draft stored for later review")
                    self._display_draft_stored_message()
                    return True
                else:
                    # CLI mode: user rejected
                    logger.info("CLI mode: user rejected draft")
                    return False
            
            # Step 8: Write files (only if approved in CLI or skipped review)
            self._step_write_files()
            
            # Step 9: Run validation
            if not self.config.skip_validation:
                self._step_run_validation()
            
            logger.info("="*70)
            logger.info("AUTONOMOUS GENERATION WORKFLOW COMPLETED")
            logger.info("="*70)
            
            self._display_success_message()
            return True
        
        except Exception as e:
            logger.error(f"Autonomous workflow failed: {e}", exc_info=True)
            self._display_error_message(str(e))
            return False
    
    async def _step_generate_files_autonomously(self) -> None:
        """
        Step 7: Generate steering files autonomously with confidence scoring.
        
        Generates files sequentially, passing previously generated files as
        context to maintain consistency across files.
        
        Requirements: 3.1-3.10, 16.8-16.11, 25.1-25.7, P0-3, P2-1
        """
        logger.info("Step 7: Generating files autonomously")
        print("\n📝 Generating steering files autonomously...")
        
        # Get gap analysis questions
        questions = self.state.gap_analysis.questions if self.state.gap_analysis else []
        
        # Filter templates based on project type (P2-1)
        files_to_generate = self._filter_files_for_project_type(self.GENERATION_ORDER)
        
        # Generate each file in order
        for filename in files_to_generate:
            print(f"\n   Generating {filename}...", end=" ")
            
            try:
                # Get context from previously generated files
                previous_files = {
                    k: v for k, v in self.generated_files.items()
                    if k in files_to_generate[:files_to_generate.index(filename)]
                }
                
                # Generate file content with fallback handling (P0-3)
                content, confidence = await self._generate_file_with_fallback(
                    filename=filename,
                    previous_files=previous_files,
                    questions=questions,
                )
                
                # Store generated file
                self.generated_files[filename] = content
                self.confidence_scores[filename] = confidence
                
                # Check if fallback should be triggered
                if self.feature_flag_manager.should_fallback(confidence.value):
                    self.fallback_triggered = True
                    self.fallback_reasons.append(
                        f"{filename}: confidence {confidence.value:.2f} < threshold {self.feature_flag_config.confidence_threshold}"
                    )
                    print(f"⚠️  Low confidence ({confidence.value:.2f}), will fallback")
                else:
                    print(f"✓ (confidence: {confidence.value:.2f})")
            
            except Exception as e:
                logger.error(f"Failed to generate {filename}: {e}", exc_info=True)
                print(f"✗ Error: {e}")
                
                # Apply fallback with [INFERRED] markers (P0-3)
                content, confidence = self._apply_fallback(filename, str(e))
                self.generated_files[filename] = content
                self.confidence_scores[filename] = confidence
        
        # Verify no empty files (P0-3)
        for filename, content in self.generated_files.items():
            if not content or not content.strip():
                logger.error(f"Generated empty file: {filename}")
                self.generated_files[filename] = (
                    f"[GENERATION FAILED — please fill manually]\n\n"
                    f"File: {filename}"
                )
                self.confidence_scores[filename] = ConfidenceScore(
                    value=0.0,
                    level=None,  # Will be set to LOW in __post_init__
                    evidence=[],
                )
    
    async def _generate_file_with_fallback(
        self,
        filename: str,
        previous_files: Dict[str, str],
        questions: List[dict],
    ) -> tuple[str, ConfidenceScore]:
        """
        Generate file with automatic fallback on failure.
        
        Args:
            filename: Name of the file to generate
            previous_files: Previously generated files for context
            questions: Gap analysis questions
            
        Returns:
            Tuple of (content, confidence score)
            
        Requirements: P0-3
        """
        try:
            content, confidence = await self._generate_single_file(
                filename=filename,
                previous_files=previous_files,
                questions=questions,
            )
            
            # Verify content is not empty
            if not content or not content.strip():
                raise ValueError("LLM returned empty content")
            
            return (content, confidence)
        
        except Exception as e:
            logger.warning(
                f"Generation failed for {filename}: {type(e).__name__}: {e}"
            )
            return self._apply_fallback(filename, str(e))
    
    async def _generate_single_file(
        self,
        filename: str,
        previous_files: Dict[str, str],
        questions: List[dict],
    ) -> tuple[str, ConfidenceScore]:
        """
        Generate a single steering file with confidence scoring.
        
        Args:
            filename: Name of the file to generate
            previous_files: Previously generated files for context
            questions: Gap analysis questions
            
        Returns:
            Tuple of (content, confidence score)
        """
        from ..agents.steering_assistant import SteeringAssistant
        
        # Build context with previous files
        context = self._build_generation_context(previous_files, questions)
        
        # Create assistant for generation
        assistant = SteeringAssistant(
            knowledge_base=self.state.knowledge_base,
            gap_analysis=self.state.gap_analysis,
            research_enabled=self.config.research_enabled,
            interactive=False,  # Autonomous mode
            project_root=self.project_root,
            llm_provider=None,  # Will be set when LLMProvider is implemented
        )
        
        # Generate content (async call)
        content = await assistant.generate_file(
            filename=filename,
            context=context,
        )
        
        # Calculate confidence score
        confidence = self._calculate_file_confidence(
            filename=filename,
            content=content,
            context=context,
        )
        
        return content, confidence
    
    def _apply_fallback(
        self,
        filename: str,
        error_reason: str
    ) -> tuple[str, ConfidenceScore]:
        """
        Apply [INFERRED] marker fallback when generation fails.
        
        Args:
            filename: Name of the file that failed to generate
            error_reason: Reason for the failure
            
        Returns:
            Tuple of (fallback_content, confidence_score)
            
        Requirements: P0-3
        """
        try:
            # Import SteeringAssistant to access template methods
            from ..agents.steering_assistant import SteeringAssistant
            
            # Create temporary assistant to access template methods
            assistant = SteeringAssistant(
                knowledge_base=self.state.knowledge_base,
                gap_analysis=self.state.gap_analysis,
                research_enabled=False,
                interactive=False,
                project_root=self.project_root,
            )
            
            # Get raw template
            raw_template = assistant._get_raw_template(filename)
            
            # Strip frontmatter
            template_content = assistant._strip_frontmatter(raw_template)
            
            # Apply [INFERRED] markers
            fallback_content = assistant._apply_inferred_markers(template_content)
            
            # Track fallback reason
            reason = f"{filename}: {error_reason}"
            self.fallback_reasons.append(reason)
            
            logger.info(
                f"Applied [INFERRED] fallback for {filename}"
            )
            
            # Return with very low confidence (0.1)
            return (fallback_content, ConfidenceScore(
                value=0.1,
                level=None,  # Will be set to LOW in __post_init__
                evidence=[],
            ))
        
        except Exception as e:
            # Last resort: return error message
            logger.error(
                f"Fallback failed for {filename}: {type(e).__name__}: {e}"
            )
            
            error_content = (
                f"[GENERATION FAILED — please fill manually]\n\n"
                f"File: {filename}\n"
                f"Error: {error_reason}\n"
                f"Fallback Error: {str(e)}"
            )
            
            self.fallback_reasons.append(
                f"{filename}: {error_reason} (fallback also failed)"
            )
            
            return (error_content, ConfidenceScore(
                value=0.0,
                level=None,  # Will be set to LOW in __post_init__
                evidence=[],
            ))
    
    def _build_generation_context(
        self,
        previous_files: Dict[str, str],
        questions: List[dict],
    ) -> str:
        """
        Build context string for file generation.
        
        Args:
            previous_files: Previously generated files
            questions: Gap analysis questions
            
        Returns:
            Context string for LLM
        """
        context_parts = []
        
        # Add previous files as context
        if previous_files:
            context_parts.append("PREVIOUSLY GENERATED FILES:")
            for filename, content in previous_files.items():
                context_parts.append(f"\n--- {filename} ---")
                context_parts.append(content)
        
        # Add gap analysis questions
        if questions:
            context_parts.append("\nGAP ANALYSIS QUESTIONS:")
            for question in questions[:5]:  # Limit to 5 questions
                context_parts.append(f"- {question.get('question_text', 'Unknown')}")
        
        return "\n\n".join(context_parts)
    
    def _calculate_file_confidence(
        self,
        filename: str,
        content: str,
        context: str,
    ) -> ConfidenceScore:
        """
        Calculate confidence score for generated file.
        
        Args:
            filename: Name of the generated file
            content: Generated content
            context: Generation context
            
        Returns:
            ConfidenceScore object
        """
        evidence = []
        
        # Evidence from code analysis
        if self.state.code_analysis:
            evidence.append(self.confidence_scorer.create_evidence(
                source="CODE_ANALYSIS",
                description=f"Code analysis provided context for {filename}",
                strength=0.85,
            ))
        
        # Evidence from artifacts
        if self.state.parsed_documents:
            evidence.append(self.confidence_scorer.create_evidence(
                source="ARTIFACT",
                description=f"Artifacts provided context for {filename}",
                strength=0.80,
            ))
        
        # Evidence from context
        if context:
            evidence.append(self.confidence_scorer.create_evidence(
                source="INFERENCE",
                description=f"Context from previous files used for {filename}",
                strength=0.75,
            ))
        
        # Calculate confidence
        confidence_value = self.confidence_scorer.calculate_confidence(
            content=content,
            evidence=evidence,
        )
        
        return ConfidenceScore(
            value=confidence_value,
            level=None,  # Will be set in __post_init__
            evidence=evidence,
        )
    
    def _step_review_draft(self) -> bool:
        """
        Review generated files before writing to disk.
        
        In CLI mode (interactive=True): Prints draft summary and prompts user for approval.
        In MCP mode (interactive=False): Stores draft in self.state.draft for IDE review.
        
        MCP Mode Metadata Population (P1-3):
        The draft is stored in self.state.draft, which should be accessed by the
        MCP tool wrapper (e.g., init_steering.py) to populate WorkflowResult.metadata:
        
        Example MCP tool wrapper code:
        ```python
        @mcp.tool()
        async def init_steering(ctx: Context, ...) -> dict:
            workflow = AutonomousWorkflow(...)
            success = workflow.execute()
            
            # Populate metadata with draft summary for IDE display
            metadata = {}
            if workflow.state.draft:
                metadata['draft_summary'] = workflow.state.draft.summary()
                metadata['draft_files'] = [f.to_dict() for f in workflow.state.draft.files]
            
            return {
                'status': 'draft_ready' if workflow.state.draft else 'success',
                'metadata': metadata
            }
        ```
        
        Returns:
            True if files should be written (CLI mode approved), False otherwise
            
        Requirements: P1-3
        """
        import re
        from datetime import datetime
        from ..models import DraftState, DraftFile
        
        logger.info("Reviewing draft files")
        
        # Create draft files with metadata
        draft_files = []
        for filename, content in self.generated_files.items():
            # Calculate placeholder count using regex {[^}]+}
            placeholder_count = len(re.findall(r'\{[^}]+\}', content))
            
            # Calculate confidence: 1.0 - (placeholder_count * 0.1), capped at 0.0
            confidence = max(0.0, 1.0 - (placeholder_count * 0.1))
            
            # Get preview (first 300 chars, replace newlines with spaces)
            preview = content[:300].replace('\n', ' ')
            
            draft_files.append(DraftFile(
                filename=filename,
                content=content,
                confidence=confidence,
                placeholder_count=placeholder_count,
                preview=preview
            ))
        
        # Create draft state
        draft = DraftState(
            files=draft_files,
            created_at=datetime.now(),
            is_approved=False
        )
        
        if self.config.interactive:
            # CLI mode: print summary and prompt user
            print("\n" + "="*70)
            print("📋 DRAFT REVIEW")
            print("="*70)
            print(draft.summary())
            print("="*70)
            
            response = input("\nApprove and write files? (y/n): ").strip().lower()
            
            if response == 'y':
                draft.is_approved = True
                logger.info("User approved draft")
                return True
            else:
                logger.info("User rejected draft")
                print("\n   ℹ Draft rejected. Files not written.")
                return False
        else:
            # MCP mode: store draft for IDE review
            self.state.draft = draft
            logger.info("Draft stored for IDE review (non-interactive mode)")
            
            # Note: In MCP mode, the caller should include draft summary in
            # WorkflowResult.metadata["draft_summary"] for IDE display
            # This will be handled by the MCP tool wrapper
            
            return False  # Don't write files in MCP mode
    
    def _step_write_files(self) -> None:
        """
        Step 8: Write generated steering files to .kiro/steering/.
        
        Overrides parent method to include confidence scores in output.
        
        Requirements: 4.7
        """
        logger.info("Step 8: Writing steering files")
        print("\n💾 Writing steering files...")
        
        try:
            # Ensure steering directory exists
            self.state.steering_dir.mkdir(parents=True, exist_ok=True)
            
            # Write each file
            written_files = []
            for filename, content in self.generated_files.items():
                if content:  # Only write non-empty files
                    file_path = self.state.steering_dir / filename
                    file_path.write_text(content, encoding='utf-8')
                    written_files.append(filename)
                    logger.info(f"Wrote: {filename}")
            
            print(f"   ✓ Wrote {len(written_files)} file(s) to {self.state.steering_dir}")
            for filename in written_files:
                confidence = self.confidence_scores.get(filename)
                confidence_str = f" ({confidence.value:.2f})" if confidence else ""
                print(f"     • {filename}{confidence_str}")
            
            # Display fallback information if triggered
            if self.fallback_triggered:
                print("\n   ⚠️  Fallback triggered for the following files:")
                for reason in self.fallback_reasons:
                    print(f"     • {reason}")
        
        except Exception as e:
            logger.error(f"Failed to write files: {e}", exc_info=True)
            raise RuntimeError(f"Could not write steering files: {e}")
    
    def _step_run_validation(self) -> None:
        """
        Step 9: Run semantic validation on generated steering files.
        
        Overrides parent method to include semantic validation with rules.
        
        Requirements: 4.8, 14.4
        """
        logger.info("Step 9: Running semantic validation")
        print("\n🔍 Validating steering files...")
        
        try:
            # Run standard validation
            validator = SteeringValidator(use_llm=False)
            self.state.validation_report = validator.validate_all(
                self.state.steering_dir,
                use_llm=False,
                show_progress=True
            )
            
            # Run semantic validation with rules
            if self.generated_files:
                semantic_issues = validator.validate_with_rules(
                    files=self.generated_files,
                    framework_classifications=self.framework_classifications,
                    rules=self.rules,
                )
                
                # Add semantic issues to report
                for issue in semantic_issues:
                    severity = issue.get("severity", "warning")
                    self.state.validation_report.warnings.append(
                        type(self.state.validation_report.warnings[0])(
                            severity=severity,
                            file_name=issue.get("file", "unknown"),
                            issue_type=issue.get("type", "semantic"),
                            message=issue.get("message", ""),
                            suggestion=issue.get("suggestion"),
                        )
                    )
            
            # Display summary
            report = self.state.validation_report
            print(f"\n   ✓ Validation complete:")
            print(f"     • {report.files_checked} file(s) checked")
            print(f"     • {len(report.critical_issues)} critical issue(s)")
            print(f"     • {len(report.warnings)} warning(s)")
            print(f"     • {len(report.info)} info message(s)")
            print(f"     • Overall status: {report.overall_status.upper()}")
            
            # Show confidence summary
            if self.confidence_scores:
                avg_confidence = sum(
                    c.value for c in self.confidence_scores.values()
                ) / len(self.confidence_scores)
                print(f"\n   📊 Confidence Summary:")
                print(f"     • Average confidence: {avg_confidence:.2f}")
                
                high_count = sum(
                    1 for c in self.confidence_scores.values()
                    if c.level.value == "HIGH"
                )
                medium_count = sum(
                    1 for c in self.confidence_scores.values()
                    if c.level.value == "MEDIUM"
                )
                low_count = sum(
                    1 for c in self.confidence_scores.values()
                    if c.level.value == "LOW"
                )
                print(f"     • HIGH: {high_count}, MEDIUM: {medium_count}, LOW: {low_count}")
            
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
            print("   Steering files were created but validation could not be completed")

    def _display_draft_stored_message(self) -> None:
        """Display message when draft is stored in MCP mode."""
        print("\n" + "="*70)
        print("📋 DRAFT READY FOR REVIEW")
        print("="*70)
        print(f"\n✓ Generated {len(self.generated_files)} steering file(s)")
        print("\n📝 Draft stored for IDE review")
        print("   Files have NOT been written to disk yet.")
        print("   Review the draft in your IDE and approve to write files.")
        print("\n💡 Next steps:")
        print("   1. Review the draft summary in your IDE")
        print("   2. Call update_steering(apply_draft=True) to write files")
        print("   3. Or regenerate with different settings")
        print()

    def write_draft_to_disk(self) -> bool:
        """
        Write draft files to disk (called when user approves draft in MCP mode).
        
        This method is called by update_steering(apply_draft=True) in MCP mode:
        
        MCP Tool Flow (P1-3):
        1. User calls init_steering() in KIRO IDE
        2. Workflow generates files and stores draft in self.state.draft
        3. IDE displays draft summary from WorkflowResult.metadata
        4. User reviews draft in IDE
        5. User calls update_steering(apply_draft=True) to approve
        6. update_steering() retrieves stored workflow instance
        7. update_steering() calls workflow.write_draft_to_disk()
        8. Files are written to .kiro/steering/
        
        Example update_steering implementation:
        ```python
        @mcp.tool()
        async def update_steering(
            ctx: Context,
            apply_draft: bool = False
        ) -> dict:
            if apply_draft:
                # Retrieve stored workflow instance
                workflow = get_stored_workflow()  # Implementation-specific
                
                if not workflow or not workflow.state.draft:
                    return {'status': 'error', 'message': 'No draft available'}
                
                # Write draft files to disk
                success = workflow.write_draft_to_disk()
                
                if success:
                    return {
                        'status': 'success',
                        'message': f'Applied draft: {len(workflow.state.draft.files)} files written'
                    }
                else:
                    return {'status': 'error', 'message': 'Failed to write draft files'}
            
            # Otherwise run normal update workflow
            # ...
        ```
        
        Returns:
            True if files written successfully, False otherwise
            
        Requirements: P1-3
        """
        if not self.state.draft:
            logger.error("No draft available to write")
            return False
        
        try:
            # Ensure steering directory exists
            self.state.steering_dir.mkdir(parents=True, exist_ok=True)
            
            # Write each file from draft
            written_files = []
            for draft_file in self.state.draft.files:
                file_path = self.state.steering_dir / draft_file.filename
                file_path.write_text(draft_file.content, encoding='utf-8')
                written_files.append(draft_file.filename)
                logger.info(f"Wrote: {draft_file.filename}")
            
            # Mark draft as approved
            self.state.draft.is_approved = True
            
            logger.info(f"Successfully wrote {len(written_files)} files from draft")
            return True
        
        except Exception as e:
            logger.error(f"Failed to write draft files: {e}", exc_info=True)
            return False

    def _filter_files_for_project_type(self, template_files: List[str]) -> List[str]:
        """
        Filter template files based on project type.

        Skips templates that are not applicable to the detected project type:
        - Skips ui-standards.md for CLI tools and MCP servers (no frontend)
        - Skips db-standards.md for projects without database
        - Selects project-type-specific template variants when available

        Args:
            template_files: List of template filenames to filter

        Returns:
            Filtered list of template filenames applicable to project type

        Requirements: P2-1
        """
        if not self.state.code_analysis:
            logger.warning("No code analysis available, using all templates")
            return template_files

        # Get project classification
        try:
            classification = self.state.code_analysis.classification
            if not classification:
                logger.warning("No project classification available, using all templates")
                return template_files

            project_type = classification.get('project_type', 'library')
            has_frontend = classification.get('has_frontend', False)
            has_database = classification.get('has_database', False)

            logger.info(
                f"Filtering templates for project_type={project_type}, "
                f"has_frontend={has_frontend}, has_database={has_database}"
            )
        except Exception as e:
            logger.warning(f"Error accessing classification: {e}, using all templates")
            return template_files

        filtered_files = []

        for filename in template_files:
            # Skip ui-standards.md for CLI tools and MCP servers (no frontend)
            if filename == "ui-standards.md":
                if project_type in ("cli_tool", "mcp_server", "cli_and_mcp") or not has_frontend:
                    logger.info(f"Skipping {filename} for {project_type} (no frontend)")
                    continue

            # Skip db-standards.md for projects without database
            if filename == "db-standards.md":
                if not has_database:
                    logger.info(f"Skipping {filename} for {project_type} (no database)")
                    continue

            # Add file to filtered list
            filtered_files.append(filename)

        logger.info(
            f"Filtered {len(template_files)} templates to {len(filtered_files)} "
            f"for project type {project_type}"
        )

        return filtered_files

