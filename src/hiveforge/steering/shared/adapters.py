"""
Workflow adapters for shared backend.

This module provides adapters that wrap existing v02 workflows,
allowing them to be used by both CLI and Power interfaces.
"""

import time
from pathlib import Path
from typing import Any, Optional

from .base import SharedWorkflowBase, WorkflowResult
from .telemetry import TelemetryCollector, InterfaceType, TelemetryLevel


class SharedInitWorkflow(SharedWorkflowBase):
    """Shared adapter for init workflow.
    
    This adapter wraps the existing InitWorkflow from v02,
    providing a consistent interface for both CLI and Power.
    """
    
    def __init__(
        self,
        project_root: str | Path = ".",
        auto_discover: bool = True,
        autonomous: bool = True,
        confidence_threshold: float = 0.7,
        config: Optional[dict[str, Any]] = None,
        telemetry_collector: Optional[TelemetryCollector] = None,
        interface_type: InterfaceType = InterfaceType.CLI
    ):
        """Initialize init workflow adapter.
        
        Args:
            project_root: Path to project root directory
            auto_discover: Enable automatic discovery of existing docs
            autonomous: Enable autonomous generation mode
            confidence_threshold: Minimum confidence for autonomous decisions
            config: Optional configuration dictionary
            telemetry_collector: Optional telemetry collector
            interface_type: Interface type (CLI or Power)
        """
        super().__init__(project_root, config)
        self.auto_discover = auto_discover
        self.autonomous = autonomous
        self.confidence_threshold = confidence_threshold
        self.telemetry_collector = telemetry_collector
        self.interface_type = interface_type
    
    def execute(self) -> WorkflowResult:
        """Execute init workflow.
        
        Returns:
            WorkflowResult with execution results
        """
        start_time = time.time()
        
        try:
            # Import v02 workflow components
            from ..models import SteeringConfig, FeatureFlagConfig
            from ..workflows.init_workflow import InitWorkflow
            
            # Create feature flags for autonomous mode
            feature_flags = None
            if self.autonomous:
                feature_flags = FeatureFlagConfig(
                    use_autonomous_generation=True,
                    confidence_threshold=self.confidence_threshold,
                    interactive=False
                )
            
            # Create v02 config
            v02_config = SteeringConfig(
                analyze_code=self.auto_discover,
                feature_flags=feature_flags,
                skip_validation=False,
                interactive=not self.autonomous
            )
            
            # Create and execute v02 workflow
            v02_workflow = InitWorkflow(
                config=v02_config,
                project_root=self.project_root
            )
            
            success = v02_workflow.execute()
            
            # Collect created files
            steering_dir = self._get_steering_dir()
            files_created = []
            if steering_dir.exists():
                files_created = [str(f.relative_to(self.project_root)) 
                                for f in steering_dir.glob("*.md")]
            
            # Build result message
            if success:
                message = f"Successfully initialized steering files ({len(files_created)} files created)"
            else:
                message = "Init workflow failed or was cancelled"
            
            # Collect warnings from validation report if available
            warnings = []
            if v02_workflow.state.validation_report:
                warnings = [issue.message for issue in v02_workflow.state.validation_report.warnings]
            
            result = WorkflowResult(
                success=success,
                message=message,
                files_created=files_created,
                warnings=warnings,
                metadata={
                    "autonomous": self.autonomous,
                    "auto_discover": self.auto_discover,
                    "confidence_threshold": self.confidence_threshold,
                    "files_count": len(files_created)
                }
            )
            
            # Collect telemetry
            if self.telemetry_collector:
                execution_time = time.time() - start_time
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="init",
                    interface_type=self.interface_type,
                    parameters={
                        "auto_discover": self.auto_discover,
                        "autonomous": self.autonomous,
                        "confidence_threshold": self.confidence_threshold
                    },
                    result_status="success" if success else "failed",
                    execution_time=execution_time,
                    files_created=files_created
                )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Collect telemetry for error
            if self.telemetry_collector:
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="init",
                    interface_type=self.interface_type,
                    parameters={
                        "auto_discover": self.auto_discover,
                        "autonomous": self.autonomous,
                        "confidence_threshold": self.confidence_threshold
                    },
                    result_status="failed",
                    execution_time=execution_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    error_recoverable=True
                )
            
            return self.handle_error(e)


class SharedUpdateWorkflow(SharedWorkflowBase):
    """Shared adapter for update workflow.
    
    This adapter wraps the existing UpdateWorkflow from v02,
    providing a consistent interface for both CLI and Power.
    """
    
    def __init__(
        self,
        project_root: str | Path = ".",
        files_to_update: Optional[list[str]] = None,
        preserve_customizations: bool = True,
        incremental: bool = True,
        config: Optional[dict[str, Any]] = None,
        telemetry_collector: Optional[TelemetryCollector] = None,
        interface_type: InterfaceType = InterfaceType.CLI
    ):
        """Initialize update workflow adapter.
        
        Args:
            project_root: Path to project root directory
            files_to_update: Specific files to update (None = all)
            preserve_customizations: Preserve user customizations
            incremental: Use incremental update mode
            config: Optional configuration dictionary
            telemetry_collector: Optional telemetry collector
            interface_type: Interface type (CLI or Power)
        """
        super().__init__(project_root, config)
        self.files_to_update = files_to_update
        self.preserve_customizations = preserve_customizations
        self.incremental = incremental
        self.telemetry_collector = telemetry_collector
        self.interface_type = interface_type
    
    def execute(self) -> WorkflowResult:
        """Execute update workflow.
        
        Returns:
            WorkflowResult with execution results
        """
        start_time = time.time()
        
        try:
            # Import v02 workflow components
            from ..models import SteeringConfig
            from ..workflows.update_workflow import UpdateWorkflow
            
            # Create v02 config
            v02_config = SteeringConfig(
                incremental=self.incremental,
                skip_validation=False,
                interactive=True
            )
            
            # Create and execute v02 workflow
            v02_workflow = UpdateWorkflow(
                config=v02_config,
                project_root=self.project_root
            )
            
            success = v02_workflow.execute()
            
            # Collect modified files
            steering_dir = self._get_steering_dir()
            files_modified = []
            if steering_dir.exists():
                # Get all steering files (they may have been modified)
                all_files = [str(f.relative_to(self.project_root)) 
                            for f in steering_dir.glob("*.md")]
                
                # If specific files were requested, filter to those
                if self.files_to_update:
                    files_modified = [f for f in all_files 
                                     if any(req in f for req in self.files_to_update)]
                else:
                    files_modified = all_files
            
            # Build result message
            if success:
                if files_modified:
                    message = f"Successfully updated steering files ({len(files_modified)} files modified)"
                else:
                    message = "Update completed - no changes applied"
            else:
                message = "Update workflow failed or was cancelled"
            
            # Collect warnings from validation report if available
            warnings = []
            if v02_workflow.state.validation_report:
                warnings = [issue.message for issue in v02_workflow.state.validation_report.warnings]
            
            # Collect customizations detected
            customizations_count = sum(len(customs) for customs in v02_workflow.customizations.values())
            
            result = WorkflowResult(
                success=success,
                message=message,
                files_modified=files_modified,
                warnings=warnings,
                metadata={
                    "incremental": self.incremental,
                    "preserve_customizations": self.preserve_customizations,
                    "files_count": len(files_modified),
                    "customizations_detected": customizations_count
                }
            )
            
            # Collect telemetry
            if self.telemetry_collector:
                execution_time = time.time() - start_time
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="update",
                    interface_type=self.interface_type,
                    parameters={
                        "files_to_update": self.files_to_update,
                        "preserve_customizations": self.preserve_customizations,
                        "incremental": self.incremental
                    },
                    result_status="success" if success else "failed",
                    execution_time=execution_time,
                    files_modified=files_modified
                )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Collect telemetry for error
            if self.telemetry_collector:
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="update",
                    interface_type=self.interface_type,
                    parameters={
                        "files_to_update": self.files_to_update,
                        "preserve_customizations": self.preserve_customizations,
                        "incremental": self.incremental
                    },
                    result_status="failed",
                    execution_time=execution_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    error_recoverable=True
                )
            
            return self.handle_error(e)


class SharedValidateWorkflow(SharedWorkflowBase):
    """Shared adapter for validate workflow.
    
    This adapter wraps the existing ValidateWorkflow from v02,
    providing a consistent interface for both CLI and Power.
    """
    
    def __init__(
        self,
        project_root: str | Path = ".",
        strict: bool = False,
        use_llm: bool = True,
        config: Optional[dict[str, Any]] = None,
        telemetry_collector: Optional[TelemetryCollector] = None,
        interface_type: InterfaceType = InterfaceType.CLI
    ):
        """Initialize validate workflow adapter.
        
        Args:
            project_root: Path to project root directory
            strict: Treat warnings as errors
            use_llm: Enable semantic validation with LLM
            config: Optional configuration dictionary
            telemetry_collector: Optional telemetry collector
            interface_type: Interface type (CLI or Power)
        """
        super().__init__(project_root, config)
        self.strict = strict
        self.use_llm = use_llm
        self.telemetry_collector = telemetry_collector
        self.interface_type = interface_type
    
    def execute(self) -> WorkflowResult:
        """Execute validate workflow.
        
        Returns:
            WorkflowResult with execution results
        """
        start_time = time.time()
        
        try:
            # Import v02 workflow components
            from ..models import SteeringConfig
            from ..workflows.validate_workflow import ValidateWorkflow
            
            # Create v02 config (note: use_llm is not a SteeringConfig parameter)
            v02_config = SteeringConfig(
                strict_mode=self.strict
            )
            
            # Create and execute v02 workflow
            v02_workflow = ValidateWorkflow(
                config=v02_config,
                project_root=self.project_root
            )
            
            exit_code = v02_workflow.execute()
            
            # Convert v02 results to shared format
            report = v02_workflow.state.validation_report
            
            # Determine success based on exit code
            success = (exit_code == 0)
            
            # Build message
            if success:
                if report.warnings:
                    message = f"Validation passed with {len(report.warnings)} warning(s)"
                else:
                    message = "All validation checks passed"
            else:
                message = f"Validation failed with {len(report.critical_issues)} critical issue(s)"
            
            # Collect warnings and errors
            warnings = [issue.message for issue in report.warnings]
            errors = [issue.message for issue in report.critical_issues]
            
            result = WorkflowResult(
                success=success,
                message=message,
                warnings=warnings,
                errors=errors,
                metadata={
                    "files_checked": report.files_checked,
                    "critical_issues": len(report.critical_issues),
                    "warnings": len(report.warnings),
                    "info": len(report.info),
                    "overall_status": report.overall_status,
                    "strict_mode": self.strict,
                    "use_llm": self.use_llm
                }
            )
            
            # Collect telemetry
            if self.telemetry_collector:
                execution_time = time.time() - start_time
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="validate",
                    interface_type=self.interface_type,
                    parameters={
                        "strict": self.strict,
                        "use_llm": self.use_llm
                    },
                    result_status="success" if success else "failed",
                    execution_time=execution_time,
                    files_validated=[str(f) for f in report.files_checked] if hasattr(report, 'files_checked') else []
                )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Collect telemetry for error
            if self.telemetry_collector:
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="validate",
                    interface_type=self.interface_type,
                    parameters={
                        "strict": self.strict,
                        "use_llm": self.use_llm
                    },
                    result_status="failed",
                    execution_time=execution_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    error_recoverable=True
                )
            
            return self.handle_error(e)


class SharedResetWorkflow(SharedWorkflowBase):
    """Shared adapter for reset workflow.
    
    This is a new workflow that resets steering files to default templates.
    """
    
    def __init__(
        self,
        project_root: str | Path = ".",
        file: Optional[str] = None,
        confirm: bool = False,
        config: Optional[dict[str, Any]] = None,
        telemetry_collector: Optional[TelemetryCollector] = None,
        interface_type: InterfaceType = InterfaceType.CLI
    ):
        """Initialize reset workflow adapter.
        
        Args:
            project_root: Path to project root directory
            file: Specific file to reset (None = all files)
            confirm: Skip confirmation prompt
            config: Optional configuration dictionary
            telemetry_collector: Optional telemetry collector
            interface_type: Interface type (CLI or Power)
        """
        super().__init__(project_root, config)
        self.file = file
        self.confirm = confirm
        self.telemetry_collector = telemetry_collector
        self.interface_type = interface_type
    
    def execute(self) -> WorkflowResult:
        """Execute reset workflow.
        
        Returns:
            WorkflowResult with execution results
        """
        start_time = time.time()
        
        try:
            from ..templates import get_all_templates
            import shutil
            from datetime import datetime
            
            steering_dir = self._get_steering_dir()
            
            # Check if steering directory exists
            if not steering_dir.exists():
                return self._create_failure_result(
                    "No steering directory found",
                    errors=["Steering directory does not exist. Run 'init' first."]
                )
            
            # Determine which files to reset
            if self.file:
                # Reset specific file
                files_to_reset = [steering_dir / self.file]
                if not files_to_reset[0].exists():
                    return self._create_failure_result(
                        f"File not found: {self.file}",
                        errors=[f"File {self.file} does not exist in steering directory"]
                    )
            else:
                # Reset all files
                files_to_reset = list(steering_dir.glob("*.md"))
                if not files_to_reset:
                    return self._create_failure_result(
                        "No steering files found to reset",
                        errors=["Steering directory is empty"]
                    )
            
            # Create backup directory
            backup_dir = self.project_root / ".kiro" / "backups" / f"reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Get all templates
            templates_dict = get_all_templates()
            
            # Backup and reset files
            files_reset = []
            for file_path in files_to_reset:
                # Create backup
                backup_path = backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                
                # Find matching template
                template_name = file_path.stem  # e.g., "tech-stack" from "tech-stack.md"
                template = templates_dict.get(template_name)
                
                if template:
                    # Reset to template
                    template_content = self._generate_template_content(template)
                    file_path.write_text(template_content)
                    files_reset.append(str(file_path.relative_to(self.project_root)))
            
            if files_reset:
                message = f"Successfully reset {len(files_reset)} file(s) to default templates"
            else:
                message = "No files were reset"
            
            result = WorkflowResult(
                success=True,
                message=message,
                files_modified=files_reset,
                metadata={
                    "backup_location": str(backup_dir.relative_to(self.project_root)),
                    "files_count": len(files_reset)
                }
            )
            
            # Collect telemetry
            if self.telemetry_collector:
                execution_time = time.time() - start_time
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="reset",
                    interface_type=self.interface_type,
                    parameters={
                        "file": self.file,
                        "confirm": self.confirm
                    },
                    result_status="success",
                    execution_time=execution_time,
                    files_modified=files_reset
                )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Collect telemetry for error
            if self.telemetry_collector:
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="reset",
                    interface_type=self.interface_type,
                    parameters={
                        "file": self.file,
                        "confirm": self.confirm
                    },
                    result_status="failed",
                    execution_time=execution_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    error_recoverable=True
                )
            
            return self.handle_error(e)
    
    def _generate_template_content(self, template) -> str:
        """Generate template content with placeholders.
        
        Args:
            template: Template object
        
        Returns:
            Template content as string
        """
        lines = []
        
        # Add frontmatter if present
        if template.frontmatter:
            lines.append("---")
            for key, value in template.frontmatter.items():
                lines.append(f"{key}: {value}")
            lines.append("---")
            lines.append("")
        
        # Add sections
        for section in template.sections:
            lines.append(f"# {section.name}")
            lines.append("")
            lines.append(section.placeholder_pattern)
            lines.append("")
        
        return "\n".join(lines)


class SharedDiscoveryWorkflow(SharedWorkflowBase):
    """Shared adapter for discovery workflow.
    
    This adapter wraps the existing discovery logic from v02,
    providing a consistent interface for both CLI and Power.
    """
    
    def __init__(
        self,
        project_root: str | Path = ".",
        include_git_history: bool = False,
        max_discovery_files: int = 1000,
        max_file_size_mb: int = 10,
        config: Optional[dict[str, Any]] = None,
        telemetry_collector: Optional[TelemetryCollector] = None,
        interface_type: InterfaceType = InterfaceType.CLI
    ):
        """Initialize discovery workflow adapter.
        
        Args:
            project_root: Path to project root directory
            include_git_history: Analyze git commits and PRs
            max_discovery_files: Maximum files to analyze during discovery
            max_file_size_mb: Maximum file size in MB to analyze
            config: Optional configuration dictionary
            telemetry_collector: Optional telemetry collector
            interface_type: Interface type (CLI or Power)
        """
        super().__init__(project_root, config)
        self.include_git_history = include_git_history
        self.max_discovery_files = max_discovery_files
        self.max_file_size_mb = max_file_size_mb
        self.telemetry_collector = telemetry_collector
        self.interface_type = interface_type
    
    def execute(self) -> WorkflowResult:
        """Execute discovery workflow.
        
        Returns:
            WorkflowResult with execution results
        """
        start_time = time.time()
        
        try:
            # Import discovery components
            from ..scalable_discovery import ScalableDiscovery
            from ..parsers.orchestrator import DiscoveryOrchestrator
            
            # Create discovery orchestrator
            orchestrator = DiscoveryOrchestrator(
                max_discovery_files=self.max_discovery_files,
                max_file_size_mb=self.max_file_size_mb
            )
            
            # Run discovery
            discovered_files, metadata = orchestrator.discover_all(self.project_root)
            
            # Build result message
            file_count = metadata.get("file_count", len(discovered_files))
            commit_count = metadata.get("commit_count", 0)
            
            if discovered_files:
                message = f"Discovery complete: {file_count} files found"
                if self.include_git_history and commit_count > 0:
                    message += f", {commit_count} commits analyzed"
            else:
                message = "Discovery complete: no relevant files found"
            
            # Collect warnings if any files were skipped
            warnings = []
            if "ranking_metadata" in metadata:
                ranking_meta = metadata["ranking_metadata"]
                skipped_count = ranking_meta.get("total_skipped", 0)
                if skipped_count > 0:
                    skip_reasons = ranking_meta.get("skip_reasons", {})
                    for reason, count in skip_reasons.items():
                        warnings.append(f"{count} files skipped: {reason}")
            
            result = WorkflowResult(
                success=True,
                message=message,
                warnings=warnings,
                metadata={
                    "files_discovered": file_count,
                    "files_included": len(discovered_files),
                    "commit_count": commit_count,
                    "include_git_history": self.include_git_history,
                    "max_discovery_files": self.max_discovery_files,
                    "max_file_size_mb": self.max_file_size_mb,
                    "discovery_method": metadata.get("method", "unknown"),
                    "discovery_metadata": metadata
                }
            )
            
            # Collect telemetry
            if self.telemetry_collector:
                execution_time = time.time() - start_time
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="discovery",
                    interface_type=self.interface_type,
                    parameters={
                        "include_git_history": self.include_git_history,
                        "max_discovery_files": self.max_discovery_files,
                        "max_file_size_mb": self.max_file_size_mb
                    },
                    result_status="success",
                    execution_time=execution_time
                )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Collect telemetry for error
            if self.telemetry_collector:
                self.telemetry_collector.collect_workflow_execution(
                    workflow_type="discovery",
                    interface_type=self.interface_type,
                    parameters={
                        "include_git_history": self.include_git_history,
                        "max_discovery_files": self.max_discovery_files,
                        "max_file_size_mb": self.max_file_size_mb
                    },
                    result_status="failed",
                    execution_time=execution_time,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    error_recoverable=True
                )
            
            return self.handle_error(e)
