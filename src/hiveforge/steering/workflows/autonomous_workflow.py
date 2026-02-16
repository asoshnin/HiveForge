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
        
        Returns:
            True if workflow completed successfully, False otherwise
            
        Requirements: 3.1-3.10, 16.8-16.11, 25.1-25.7
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
            
            # Step 8: Write files
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
    
    def _step_generate_files_autonomously(self) -> None:
        """
        Step 7: Generate steering files autonomously with confidence scoring.
        
        Generates files sequentially, passing previously generated files as
        context to maintain consistency across files.
        
        Requirements: 3.1-3.10, 16.8-16.11, 25.1-25.7
        """
        logger.info("Step 7: Generating files autonomously")
        print("\n📝 Generating steering files autonomously...")
        
        # Get gap analysis questions
        questions = self.state.gap_analysis.questions if self.state.gap_analysis else []
        
        # Generate each file in order
        for filename in self.GENERATION_ORDER:
            print(f"\n   Generating {filename}...", end=" ")
            
            try:
                # Get context from previously generated files
                previous_files = {
                    k: v for k, v in self.generated_files.items()
                    if k in self.GENERATION_ORDER[:self.GENERATION_ORDER.index(filename)]
                }
                
                # Generate file content
                content, confidence = self._generate_single_file(
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
                
                # Handle partial failure - continue with remaining files
                if self.feature_flag_config.interactive:
                    # In interactive mode, fallback to question workflow
                    self.fallback_triggered = True
                    self.fallback_reasons.append(f"{filename}: generation error")
                else:
                    # In autonomous mode, continue with remaining files
                    self.generated_files[filename] = ""
                    self.confidence_scores[filename] = ConfidenceScore(
                        value=0.0,
                        level=None,  # Will be set to LOW in __post_init__
                        evidence=[],
                    )
    
    def _generate_single_file(
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
        )
        
        # Generate content
        content = assistant.generate_file(
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
