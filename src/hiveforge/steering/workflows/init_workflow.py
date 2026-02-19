"""
Init Workflow for Steering Assistant.

This module implements the InitWorkflow class that orchestrates the complete
workflow for creating steering files from scratch. It integrates all components:
DocumentParser, CodeAnalyzer, KnowledgeBase, GapAnalysisEngine, SteeringAssistant,
TemplatePopulator, and SteeringValidator.

The workflow handles:
- Creating staging directory
- Optionally analyzing existing codebase
- Parsing artifacts from staging folder
- Building knowledge base
- Running gap analysis
- Conducting conversation to gather missing information
- Populating templates
- Writing files to .kiro/steering/
- Running validation

Requirements: 4.1-4.8, 13.1-13.2
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import (
    SteeringConfig,
    WorkflowState,
    CodeAnalysisResult,
    ValidationReport,
)
from ..utils import (
    create_staging_directory,
    is_staging_folder_empty,
    get_staging_directory_summary,
)
from ..parsers.orchestrator import parse_directory
from ..analyzers.code_analyzer import CodeAnalyzer
from ..knowledge_base import KnowledgeBase
from ..gap_analysis import GapAnalysisEngine
from ..agents.steering_assistant import SteeringAssistant
from ..template_populator import TemplatePopulator
from ..validators.steering_validator import SteeringValidator
from ..source_resolver import SourceDocumentResolver
from ..confidence import ConfidenceCalculator
from ..content_tagger import ContentTagger

logger = logging.getLogger(__name__)


class InitWorkflow:
    """
    Orchestrates the init workflow for creating steering files from scratch.
    
    The InitWorkflow coordinates all components to:
    1. Create staging directory
    2. Optionally analyze existing codebase (if --analyze-code flag set)
    3. Parse artifacts from staging folder
    4. Build knowledge base (combining code analysis + artifacts)
    5. Run gap analysis
    6. Conduct conversation to gather missing information
    7. Populate templates
    8. Write files to .kiro/steering/
    9. Run validation (unless --skip-validation flag set)
    
    Attributes:
        config: SteeringConfig with workflow settings
        state: WorkflowState tracking workflow progress
        project_root: Root directory of the project
        
    Requirements: 4.1-4.8, 13.1-13.2
    """
    
    def __init__(
        self,
        config: SteeringConfig,
        project_root: Optional[Path] = None,
        source_docs_path: Optional[str] = None
    ):
        """
        Initialize the init workflow.
        
        Args:
            config: SteeringConfig with workflow settings
            project_root: Root directory of the project (defaults to current directory)
            source_docs_path: Optional path to source documents folder (relative to project_root)
        """
        self.config = config
        self.project_root = project_root or Path.cwd()
        self.source_docs_path = source_docs_path
        
        # Initialize workflow state
        self.state = WorkflowState(
            workflow_type="init",
            staging_dir=self.project_root / ".kiro" / "onboarding",
            steering_dir=self.project_root / ".kiro" / "steering",
        )
        
        # Initialize source document resolver
        self.source_resolver = SourceDocumentResolver(self.project_root)
        
        # Track discovered documents for statistics
        self.discovered_documents = []
        
        logger.info(f"Initialized InitWorkflow for project: {self.project_root}")
        if source_docs_path:
            logger.info(f"Custom source documents path: {source_docs_path}")
    
    def execute(self) -> bool:
        """
        Execute the complete init workflow.
        
        Returns:
            True if workflow completed successfully, False otherwise
            
        Requirements: 4.1-4.8, 13.1-13.2
        """
        logger.info("="*70)
        logger.info("STARTING INIT WORKFLOW")
        logger.info("="*70)
        
        try:
            # Step 1: Create staging directory (Req 2.1, 4.1)
            self._step_create_staging_directory()
            
            # Step 2: Check for existing steering files (Req 4.1, 4.2, 13.1)
            if not self._step_check_existing_files():
                logger.info("Init workflow aborted by user")
                return False
            
            # Step 3: Optionally analyze code (Req 3A.1-3A.15)
            if self.config.analyze_code:
                self._step_analyze_code()
            
            # Step 4: Parse artifacts from staging folder (Req 4.3)
            self._step_parse_artifacts()
            
            # Step 5: Build knowledge base (Req 3A.9)
            self._step_build_knowledge_base()
            
            # Step 6: Run gap analysis (Req 4.4, 6.1-6.5)
            self._step_run_gap_analysis()
            
            # Step 7: Conduct conversation (Req 4.5, 7.1-7.8)
            self._step_conduct_conversation()
            
            # Step 8: Populate templates (Req 4.6)
            self._step_populate_templates()
            
            # Step 9: Write files (Req 4.7)
            self._step_write_files()
            
            # Step 10: Run validation (Req 4.8)
            if not self.config.skip_validation:
                self._step_run_validation()
            
            logger.info("="*70)
            logger.info("INIT WORKFLOW COMPLETED SUCCESSFULLY")
            logger.info("="*70)
            
            self._display_success_message()
            return True
        
        except Exception as e:
            logger.error(f"Init workflow failed: {e}", exc_info=True)
            self._display_error_message(str(e))
            return False
    
    def _step_create_staging_directory(self) -> None:
        """
        Step 1: Create staging directory and resolve source documents.
        
        If source_docs_path is provided, discovers documents from that path
        and links/copies them to the staging directory. Otherwise, uses the
        default .kiro/onboarding/ directory.
        
        Requirements: 2.1, 4.1, R1.3, R1.4
        """
        logger.info("Step 1: Creating staging directory and resolving source documents")
        print("\n🔧 Setting up staging directory...")
        
        try:
            # Use SourceDocumentResolver to resolve path and discover documents
            resolved_staging_dir, discovered_docs = self.source_resolver.resolve(
                source_docs_path=self.source_docs_path,
                copy_files=False  # Use symlinks by default for performance
            )
            
            # Update state with resolved staging directory
            self.state.staging_dir = resolved_staging_dir
            self.discovered_documents = discovered_docs
            
            print(f"   ✓ Staging directory ready: {self.state.staging_dir}")
            
            # Display source path if custom path was used
            if self.source_docs_path:
                print(f"   ℹ Using custom source path: {self.source_docs_path}")
                print(f"   ℹ Discovered {len(discovered_docs)} document(s)")
            
            # Display summary of staging folder contents
            summary = get_staging_directory_summary(self.state.staging_dir)
            if summary["is_empty"]:
                print("   ℹ Staging folder is empty - will proceed with conversation-only mode")
            else:
                print(f"   ℹ Found {summary['total_files']} artifact(s):")
                if summary["markdown_count"] > 0:
                    print(f"     • {summary['markdown_count']} markdown file(s)")
                if summary["pdf_count"] > 0:
                    print(f"     • {summary['pdf_count']} PDF file(s)")
                if summary["image_count"] > 0:
                    print(f"     • {summary['image_count']} image file(s)")
            
            # Add document discovery statistics to state
            self._add_discovery_statistics()
        
        except Exception as e:
            logger.error(f"Failed to create staging directory: {e}")
            raise RuntimeError(f"Could not create staging directory: {e}")
    
    def _step_check_existing_files(self) -> bool:
        """
        Step 2: Check if steering files already exist and handle accordingly.
        
        Returns:
            True to proceed, False to abort
            
        Requirements: 4.1, 4.2, 13.1, 13.2
        """
        logger.info("Step 2: Checking for existing steering files")
        
        # Check if steering directory exists and has files
        if not self.state.steering_dir.exists():
            logger.info("No existing steering directory found")
            return True
        
        existing_files = list(self.state.steering_dir.glob("*.md"))
        if not existing_files:
            logger.info("Steering directory exists but is empty")
            return True
        
        # Existing files found - warn user (Req 4.1, 13.1)
        logger.warning(f"Found {len(existing_files)} existing steering file(s)")
        print("\n⚠️  WARNING: Existing steering files detected!")
        print(f"   Found {len(existing_files)} file(s) in {self.state.steering_dir}")
        print("   Files:")
        for file_path in existing_files[:5]:  # Show first 5
            print(f"     • {file_path.name}")
        if len(existing_files) > 5:
            print(f"     ... and {len(existing_files) - 5} more")
        print()
        
        # Offer options (Req 4.2, 13.2)
        print("   Options:")
        print("     1. Backup existing files and proceed")
        print("     2. Abort (use 'steering update' instead)")
        print()
        
        while True:
            choice = input("   Choose option (1 or 2): ").strip()
            
            if choice == "1":
                # Create backup (Req 13.2)
                if self._create_backup(existing_files):
                    logger.info("User chose to backup and proceed")
                    return True
                else:
                    logger.error("Backup failed")
                    return False
            
            elif choice == "2":
                logger.info("User chose to abort")
                print("\n   ℹ Use 'hiveforge steering update' to modify existing files")
                return False
            
            else:
                print("   ⚠️  Invalid choice. Please enter 1 or 2.")
    
    def _create_backup(self, files: list[Path]) -> bool:
        """
        Create timestamped backup of existing steering files.
        
        Args:
            files: List of file paths to backup
            
        Returns:
            True if backup successful, False otherwise
            
        Requirements: 13.2
        """
        if not self.config.backup_enabled:
            logger.info("Backups disabled in config")
            return True
        
        try:
            # Create backup directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.config.backup_dir / f"steering_backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Creating backup in: {backup_dir}")
            print(f"\n   📦 Creating backup: {backup_dir}")
            
            # Copy each file
            for file_path in files:
                dest_path = backup_dir / file_path.name
                shutil.copy2(file_path, dest_path)
                logger.debug(f"Backed up: {file_path.name}")
            
            print(f"   ✓ Backed up {len(files)} file(s)")
            return True
        
        except Exception as e:
            logger.error(f"Backup failed: {e}", exc_info=True)
            print(f"   ✗ Backup failed: {e}")
            return False
    
    def _step_analyze_code(self) -> None:
        """
        Step 3: Analyze existing codebase to extract project information.
        
        Requirements: 3A.1-3A.15, 3B.1-3B.7, 3C.1-3C.5
        """
        logger.info("Step 3: Analyzing codebase")
        print("\n🔍 Analyzing codebase...")
        
        try:
            analyzer = CodeAnalyzer(self.project_root)
            self.state.code_analysis = analyzer.analyze()
            
            # Display summary
            print("\n   Analysis complete:")
            
            # Languages
            if self.state.code_analysis.languages:
                print("   📊 Languages:")
                for lang in self.state.code_analysis.languages[:5]:
                    version_str = f" {lang.version}" if lang.version else ""
                    print(f"     • {lang.name}{version_str}: {lang.percentage:.1f}%")
            
            # Tech stack
            tech = self.state.code_analysis.tech_stack
            if tech.backend_framework or tech.frontend_framework or tech.database:
                print("   📦 Tech Stack:")
                if tech.backend_framework:
                    print(f"     • Backend: {tech.backend_framework}")
                if tech.frontend_framework:
                    print(f"     • Frontend: {tech.frontend_framework}")
                if tech.database:
                    print(f"     • Database: {tech.database}")
                if tech.cache:
                    print(f"     • Cache: {tech.cache}")
            
            # Architecture
            arch = self.state.code_analysis.architecture
            if arch.pattern:
                print(f"   🏗️  Architecture: {arch.pattern}")
            
            # Conventions
            conv = self.state.code_analysis.conventions
            if conv.naming_style:
                print("   📝 Conventions detected")
            
            # Documentation
            if self.state.code_analysis.documentation:
                print(f"   📄 Documentation: {len(self.state.code_analysis.documentation)} source(s)")
        
        except Exception as e:
            logger.error(f"Code analysis failed: {e}", exc_info=True)
            print(f"   ⚠️  Code analysis failed: {e}")
            print("   Continuing with artifact parsing only...")
            self.state.code_analysis = None
    
    def _step_parse_artifacts(self) -> None:
        """
        Step 4: Parse all artifacts from staging folder.
        
        Requirements: 4.3, 3.1-3.5, 14.1, R2.1, R2.2
        """
        logger.info("Step 4: Parsing artifacts")
        
        # Check if staging folder is empty (Req 2.3, R2.1)
        if is_staging_folder_empty(self.state.staging_dir):
            logger.info("Staging folder is empty, skipping artifact parsing")
            print("\n   ℹ No artifacts to parse (staging folder is empty)")
            self.state.parsed_documents = []
            
            # Add empty source folder warnings (R2.1, R2.2)
            self._add_empty_source_folder_warnings()
            return
        
        print("\n📄 Parsing artifacts...")
        
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
            print(f"   ✗ Artifact parsing failed: {e}")
            self.state.parsed_documents = []
    
    def _add_empty_source_folder_warnings(self) -> None:
        """
        Add warnings when staging folder is empty.
        
        Requirements: R2.1, R2.2
        """
        # Add primary warning (R2.1)
        warning = (
            "No source documents found. Steering files will be generated from "
            "code analysis only. Consider adding design documents to improve accuracy."
        )
        self.state.warnings.append(warning)
        logger.warning(warning)
        
        # Set metadata (R2.1)
        self.state.metadata["source_documents_found"] = 0
        self.state.metadata["confidence_level"] = "low"
        
        # Add autonomous mode warning (R2.2)
        if self.config.feature_flags and self.config.feature_flags.use_autonomous_generation:
            autonomous_warning = (
                "Autonomous mode with no source documents may produce inferred content. "
                "Review generated files carefully."
            )
            self.state.warnings.append(autonomous_warning)
            logger.warning(autonomous_warning)
    
    def _step_build_knowledge_base(self) -> None:
        """
        Step 5: Build knowledge base from parsed documents and code analysis.
        
        Requirements: 3A.9
        """
        logger.info("Step 5: Building knowledge base")
        print("\n🧠 Building knowledge base...")
        
        try:
            self.state.knowledge_base = KnowledgeBase(
                documents=self.state.parsed_documents,
                code_analysis=self.state.code_analysis
            )
            
            # Display summary
            doc_count = len(self.state.parsed_documents)
            has_code_analysis = self.state.code_analysis is not None
            
            print(f"   ✓ Knowledge base built:")
            print(f"     • {doc_count} document(s)")
            if has_code_analysis:
                print("     • Code analysis results")
        
        except Exception as e:
            logger.error(f"Failed to build knowledge base: {e}", exc_info=True)
            raise RuntimeError(f"Could not build knowledge base: {e}")
    
    def _step_run_gap_analysis(self) -> None:
        """
        Step 6: Run gap analysis to identify missing information.
        
        Requirements: 4.4, 6.1-6.5, 3A.10, 14.2
        """
        logger.info("Step 6: Running gap analysis")
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
            print(f"     • {complete_count} section(s) complete")
            if ambiguous_count > 0:
                print(f"     • {ambiguous_count} section(s) need clarification")
            if missing_count > 0:
                print(f"     • {missing_count} section(s) missing")
            print(f"     • {len(self.state.gap_analysis.questions)} question(s) to ask")
        
        except Exception as e:
            logger.error(f"Gap analysis failed: {e}", exc_info=True)
            raise RuntimeError(f"Could not perform gap analysis: {e}")
    
    def _step_conduct_conversation(self) -> None:
        """
        Step 7: Conduct conversation to gather missing information.
        
        Requirements: 4.5, 7.1-7.8
        """
        logger.info("Step 7: Conducting conversation")
        
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
    
    def _step_populate_templates(self) -> None:
        """
        Step 8: Populate all steering file templates with gathered information.
        
        This step now includes:
        1. Template population with gathered information
        2. Confidence calculation for each file
        3. Content tagging with [INFERRED] markers and metadata
        
        Requirements: 4.6, 14.3, R3.1, R3.2, R3.3, R3.4
        """
        logger.info("Step 8: Populating templates")
        print("\n📝 Generating steering files...")
        
        try:
            populator = TemplatePopulator()
            
            # Combine knowledge base info with gathered info
            combined_knowledge = self._combine_knowledge()
            
            # Populate all templates with progress indicators (Req 14.3)
            populated_files = populator.populate_all(
                combined_knowledge,
                show_progress=True
            )
            
            print(f"\n   ✓ Generated {len(populated_files)} steering file(s)")
            
            # Step 8a: Calculate confidence and tag content (R3.1-R3.4)
            print("\n🏷️  Tagging content with confidence metadata...")
            tagged_files = self._calculate_confidence_and_tag_content(
                populated_files,
                combined_knowledge
            )
            
            # Store tagged files in state for writing
            self.state.populated_files = tagged_files
            
            print(f"   ✓ Tagged {len(tagged_files)} file(s) with confidence metadata")
        
        except Exception as e:
            logger.error(f"Template population failed: {e}", exc_info=True)
            raise RuntimeError(f"Could not populate templates: {e}")
    
    def _combine_knowledge(self) -> dict:
        """
        Combine knowledge base information with gathered information.
        
        Prioritizes code analysis for technical details and artifacts for
        business context, as specified in Req 3A.9.
        
        Returns:
            Combined knowledge dictionary
        """
        combined = {}
        
        # Start with gathered info from conversation
        combined.update(self.state.gathered_info)
        
        # Add code analysis results if available
        if self.state.code_analysis:
            # Tech stack
            tech = self.state.code_analysis.tech_stack
            if "tech-stack" not in combined:
                combined["tech-stack"] = {}
            
            if tech.backend_framework:
                combined["tech-stack"]["Backend"] = tech.backend_framework
            if tech.frontend_framework:
                combined["tech-stack"]["Frontend"] = tech.frontend_framework
            if tech.database:
                combined["tech-stack"]["Database"] = tech.database
            if tech.cache:
                combined["tech-stack"]["Cache"] = tech.cache
            
            # Architecture
            arch = self.state.code_analysis.architecture
            if "architecture" not in combined:
                combined["architecture"] = {}
            
            if arch.pattern:
                combined["architecture"]["Pattern"] = arch.pattern
            if arch.key_components:
                combined["architecture"]["Components"] = ", ".join(arch.key_components)
            
            # Conventions
            conv = self.state.code_analysis.conventions
            if "conventions" not in combined:
                combined["conventions"] = {}
            
            if conv.naming_style:
                combined["conventions"]["Naming"] = str(conv.naming_style)
            if conv.formatting:
                combined["conventions"]["Formatting"] = str(conv.formatting)
        
        return combined
    
    def _calculate_confidence_and_tag_content(
        self,
        populated_files: dict,
        combined_knowledge: dict
    ) -> dict:
        """
        Calculate confidence scores and tag content with metadata.
        
        This method:
        1. Extracts source tracking from gathered_info
        2. Calculates confidence for each file
        3. Tags inferred sections with [INFERRED] markers
        4. Adds metadata headers with confidence info
        5. Adds low confidence warnings where needed
        
        Args:
            populated_files: Dictionary of filename -> content
            combined_knowledge: Combined knowledge used for population
        
        Returns:
            Dictionary of filename -> tagged content
            
        Requirements: R3.1, R3.2, R3.3, R3.4
        """
        calculator = ConfidenceCalculator()
        tagger = ContentTagger()
        tagged_files = {}
        file_scores = {}
        
        # Extract source tracking from gathered_info
        sources_by_file = self._extract_source_tracking()
        
        # Calculate metadata for tagging
        metadata = {
            "source_documents": len(self.state.parsed_documents),
            "code_analysis": self.state.code_analysis is not None,
        }
        
        if self.source_docs_path:
            metadata["source_docs_path"] = self.source_docs_path
        
        # Process each file
        for filename, content in populated_files.items():
            # Get source tracking for this file
            file_sources = sources_by_file.get(filename, {
                "documents": [],
                "code_analysis": [],
                "inferred": []
            })
            
            # Calculate confidence for this file
            confidence = calculator.calculate_file_confidence(
                filename,
                file_sources,
                content
            )
            
            # Store for overall calculation
            file_scores[filename] = confidence
            
            # Tag the content
            tagged_content = tagger.tag_content(
                content,
                confidence,
                metadata
            )
            
            tagged_files[filename] = tagged_content
            
            logger.info(
                f"Tagged {filename}: confidence={confidence.level} "
                f"({confidence.overall:.2f}), "
                f"inferred_sections={len(confidence.inferred_sections)}"
            )
        
        # Calculate and store overall confidence
        overall_confidence = calculator.calculate_overall_confidence(file_scores)
        self.state.metadata["overall_confidence"] = overall_confidence.level
        self.state.metadata["overall_confidence_score"] = overall_confidence.overall
        
        logger.info(
            f"Overall workflow confidence: {overall_confidence.level} "
            f"({overall_confidence.overall:.2f})"
        )
        
        return tagged_files
    
    def _extract_source_tracking(self) -> dict:
        """
        Extract source tracking information from gathered_info.
        
        The gathered_info from SteeringAssistant includes a "_sources" key
        for each template that tracks which sections came from which sources.
        
        Returns:
            Dictionary mapping filename to source tracking:
            {
                "tech-stack.md": {
                    "documents": ["Backend", "Frontend"],
                    "code_analysis": ["Database"],
                    "inferred": ["Cache"]
                }
            }
            
        Requirements: R3.2
        """
        sources_by_file = {}
        
        # gathered_info has structure:
        # {
        #     "tech-stack": {
        #         "Backend": "FastAPI",
        #         "_sources": {
        #             "documents": ["Backend"],
        #             "code_analysis": ["Database"],
        #             "inferred": ["Cache"]
        #         }
        #     }
        # }
        
        for template_name, template_data in self.state.gathered_info.items():
            # Convert template name to filename
            filename = f"{template_name}.md"
            
            # Extract _sources if present
            if isinstance(template_data, dict) and "_sources" in template_data:
                sources_by_file[filename] = template_data["_sources"]
            else:
                # No source tracking available, assume all inferred
                # This happens when using non-interactive mode or old code
                sources_by_file[filename] = {
                    "documents": [],
                    "code_analysis": [],
                    "inferred": []
                }
        
        # Handle case where we have code analysis but no gathered info
        # (e.g., all info came from code analysis)
        if self.state.code_analysis and not sources_by_file:
            # Mark tech-stack, architecture, conventions as from code analysis
            for filename in ["tech-stack.md", "architecture.md", "conventions.md"]:
                sources_by_file[filename] = {
                    "documents": [],
                    "code_analysis": ["all"],  # Simplified tracking
                    "inferred": []
                }
        
        return sources_by_file
    
    def _step_write_files(self) -> None:
        """
        Step 9: Write populated steering files to .kiro/steering/.
        
        Files are already tagged with confidence metadata and [INFERRED] markers
        from the previous step.
        
        Requirements: 4.7, R3.3, R3.4
        """
        logger.info("Step 9: Writing steering files")
        print("\n💾 Writing steering files...")
        
        try:
            # Ensure steering directory exists
            self.state.steering_dir.mkdir(parents=True, exist_ok=True)
            
            # Write each file (content is already tagged)
            written_files = []
            for filename, content in getattr(self.state, 'populated_files', {}).items():
                file_path = self.state.steering_dir / filename
                file_path.write_text(content, encoding='utf-8')
                written_files.append(filename)
                logger.info(f"Wrote: {filename}")
            
            print(f"   ✓ Wrote {len(written_files)} file(s) to {self.state.steering_dir}")
            for filename in written_files:
                print(f"     • {filename}")
        
        except Exception as e:
            logger.error(f"Failed to write files: {e}", exc_info=True)
            raise RuntimeError(f"Could not write steering files: {e}")
    
    def _step_run_validation(self) -> None:
        """
        Step 10: Run validation on generated steering files.
        
        Requirements: 4.8, 14.4
        """
        logger.info("Step 10: Running validation")
        print("\n🔍 Validating steering files...")
        
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
            print("   Steering files were created but validation could not be completed")
    
    def _display_success_message(self) -> None:
        """Display success message with next steps."""
        print("\n" + "="*70)
        print("✅ STEERING FILES CREATED SUCCESSFULLY!")
        print("="*70)
        print(f"\n📁 Location: {self.state.steering_dir}")
        print("\n🚀 Next steps:")
        print("   1. Review the generated steering files")
        print("   2. Customize as needed for your project")
        print("   3. Start using HiveForge agents for development")
        print("\n💡 Tips:")
        print("   • Run 'hiveforge steering validate' to check file quality")
        print("   • Run 'hiveforge steering update' to refine files later")
        print("   • Add more artifacts to .kiro/onboarding/ and re-run update")
        print()
    
    def _display_error_message(self, error: str) -> None:
        """
        Display error message with troubleshooting tips.
        
        Args:
            error: Error message to display
        """
        print("\n" + "="*70)
        print("❌ INIT WORKFLOW FAILED")
        print("="*70)
        print(f"\nError: {error}")
        print("\n🔧 Troubleshooting:")
        print("   • Check the logs for detailed error information")
        print("   • Ensure you have write permissions in the project directory")
        print("   • Verify that artifact files are not corrupted")
        print("   • Try running with --skip-validation flag")
        print("\n💬 Need help? Check the documentation or open an issue")
        print()
    
    def _add_discovery_statistics(self) -> None:
        """
        Add document discovery statistics to workflow state.
        
        This method tracks statistics about discovered documents including:
        - Total document count
        - Documents by type (markdown, pdf, image)
        - Documents by source (custom_path, staging, project_root)
        - Symlink vs. copied files
        
        Requirements: R1.3 (Add document discovery statistics to state)
        """
        if not hasattr(self.state, 'discovery_statistics'):
            self.state.discovery_statistics = {}
        
        # Count documents by type
        by_type = {}
        by_source = {}
        symlink_count = 0
        
        for doc in self.discovered_documents:
            # Count by type
            by_type[doc.file_type] = by_type.get(doc.file_type, 0) + 1
            
            # Count by source
            by_source[doc.discovered_from] = by_source.get(doc.discovered_from, 0) + 1
            
            # Count symlinks
            if doc.is_symlink:
                symlink_count += 1
        
        self.state.discovery_statistics = {
            "total_documents": len(self.discovered_documents),
            "by_type": by_type,
            "by_source": by_source,
            "symlink_count": symlink_count,
            "copied_count": len(self.discovered_documents) - symlink_count,
            "source_docs_path": self.source_docs_path
        }
        
        logger.info(f"Discovery statistics: {self.state.discovery_statistics}")
