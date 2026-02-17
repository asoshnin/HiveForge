# Shared Backend Analysis: v02 Codebase

**Feature**: steering-power-conversion  
**Version**: 2.0.0  
**Status**: Complete  
**Phase**: 1.4 - Shared Backend Interface Design

---

## 1. Executive Summary

This document analyzes the existing v02 codebase to identify components that should be extracted into a shared backend for use by both CLI and Power interfaces. The analysis identifies:

- **3 core workflow classes** that need shared adapters
- **15+ utility modules** that can be used directly
- **5 new modules** that need to be created for the shared backend
- **95%+ code sharing potential** between CLI and Power interfaces

---

## 2. Existing Workflow Analysis

### 2.1 InitWorkflow (src/hiveforge/steering/workflows/init_workflow.py)

**Current State**: 
- Fully implemented with 10-step workflow
- Handles staging directory, code analysis, artifact parsing, gap analysis, conversation, template population, file writing, and validation
- Contains CLI-specific user interaction (print statements, input prompts)

**Shared Backend Extraction**:
```python
# What should be shared (business logic):
- _step_create_staging_directory() logic
- _step_analyze_code() logic  
- _step_parse_artifacts() logic
- _step_build_knowledge_base() logic
- _step_run_gap_analysis() logic
- _step_conduct_conversation() logic
- _step_populate_templates() logic
- _step_write_files() logic
- _step_run_validation() logic
- _combine_knowledge() logic
- _create_backup() logic

# What should be interface-specific (presentation):
- print() statements
- input() prompts
- Progress indicators
- Error message formatting
```

**Recommendation**: Create `SharedInitWorkflow` class that:
- Contains all business logic methods
- Returns structured results (dicts/objects) instead of printing
- Accepts callbacks for progress updates
- Raises exceptions for errors (no user-friendly formatting)

### 2.2 UpdateWorkflow (src/hiveforge/steering/workflows/update_workflow.py)

**Current State**:
- Fully implemented with 14-step workflow
- Handles existing file verification, customization detection, conflict resolution, diff generation, user approval, and change application
- Contains CLI-specific user interaction

**Shared Backend Extraction**:
```python
# What should be shared (business logic):
- _step_verify_existing_files() logic (file checking only)
- _step_parse_existing_files() logic
- _step_parse_new_artifacts() logic
- _step_detect_customizations() logic
- _step_build_knowledge_base() logic
- _step_run_gap_analysis() logic
- _step_conduct_conversation() logic
- _step_detect_conflicts() logic
- _step_generate_proposed_changes() logic
- _step_generate_diffs() logic
- _step_apply_changes() logic
- _step_run_validation() logic
- _parse_existing_content() logic
- _combine_knowledge() logic

# What should be interface-specific (presentation):
- User approval prompts
- Conflict resolution UI
- Diff display
- Progress indicators
```

**Recommendation**: Create `SharedUpdateWorkflow` class with same pattern as InitWorkflow.

### 2.3 ValidateWorkflow (src/hiveforge/steering/workflows/validate_workflow.py)

**Current State**:
- Fully implemented with 4-step workflow
- Handles file verification, validation execution, report generation, and exit code determination
- Contains CLI-specific report display

**Shared Backend Extraction**:
```python
# What should be shared (business logic):
- _step_verify_files_exist() logic (file checking only)
- _step_run_validator() logic
- _determine_exit_code() logic

# What should be interface-specific (presentation):
- Report display formatting
- Issue display formatting
- Color-coded output
```

**Recommendation**: Create `SharedValidateWorkflow` class with same pattern.

---

## 3. Directly Reusable Modules

These modules contain pure business logic with no CLI-specific code and can be used directly by both interfaces:

### 3.1 Core Analysis Modules
| Module | Path | Purpose | Reusable? |
|--------|------|---------|-----------|
| CodeAnalyzer | `analyzers/code_analyzer.py` | Analyze codebase | ✅ Yes |
| LanguageDetector | `analyzers/language_detector.py` | Detect languages | ✅ Yes |
| TechStackExtractor | `analyzers/tech_stack_extractor.py` | Extract tech stack | ✅ Yes |
| ArchitectureInferrer | `analyzers/architecture_inferrer.py` | Infer architecture | ✅ Yes |
| ConventionsExtractor | `analyzers/conventions_extractor.py` | Extract conventions | ✅ Yes |
| DocumentationParser | `analyzers/documentation_parser.py` | Parse docs | ✅ Yes |

### 3.2 Core Processing Modules
| Module | Path | Purpose | Reusable? |
|--------|------|---------|-----------|
| DocumentParser | `parsers/orchestrator.py` | Parse artifacts | ✅ Yes |
| KnowledgeBase | `knowledge_base.py` | Store knowledge | ✅ Yes |
| GapAnalysisEngine | `gap_analysis.py` | Analyze gaps | ✅ Yes |
| SteeringAssistant | `agents/steering_assistant.py` | Conduct conversation | ✅ Yes |
| TemplatePopulator | `template_populator.py` | Populate templates | ✅ Yes |
| SteeringValidator | `validators/steering_validator.py` | Validate files | ✅ Yes |

### 3.3 Utility Modules
| Module | Path | Purpose | Reusable? |
|--------|------|---------|-----------|
| ConflictResolver | `conflict_resolver.py` | Resolve conflicts | ✅ Yes |
| CustomizationDetector | `customization_detector.py` | Detect customizations | ✅ Yes |
| DiffGenerator | `diff_generator.py` | Generate diffs | ✅ Yes |
| BackupManager | `backup_manager.py` | Create backups | ✅ Yes |
| ErrorHandling | `error_handling.py` | Handle errors | ⚠️ Needs enhancement |
| Templates | `templates.py` | Template definitions | ✅ Yes |
| Models | `models.py` | Data models | ✅ Yes |
| Utils | `utils.py` | Utility functions | ✅ Yes |

---

## 4. Modules That Need Creation

These modules don't exist yet and need to be created for the shared backend:

### 4.1 Security Wrappers Module
**Path**: `src/hiveforge/steering/shared/security_wrappers.py`

**Purpose**: Provide security controls for MCP tool execution

**Components**:
```python
# Functions
- secure_tool_execution() decorator
- validate_parameters() function
- sanitize_path() function
- obfuscate_errors() function

# Classes
- SecurityError exception
- InputValidationError exception
- PathTraversalError exception
- ResourceLimitError exception
- ResourceLimiter context manager
- SecurityContext tracking class
```

**Status**: Design complete (SECURITY_WRAPPER_DESIGN.md), needs implementation

### 4.2 Telemetry Module
**Path**: `src/hiveforge/steering/shared/telemetry.py`

**Purpose**: Track usage metrics for both CLI and Power interfaces

**Components**:
```python
# Classes
- Telemetry class with methods:
  - record_cli_command(command, parameters)
  - record_power_invocation(tool, parameters)
  - get_last_entry()
  - query_entries(filters)
  
# Properties
- storage_dir: Path to .kiro/.telemetry/
- interface: "cli" or "power"
```

**Status**: Needs design and implementation

### 4.3 Shared Workflow Base Class
**Path**: `src/hiveforge/steering/shared/workflow_base.py`

**Purpose**: Base class for all shared workflows with common functionality

**Components**:
```python
class SharedWorkflowBase:
    """Base class for shared workflows."""
    
    def __init__(self, config, project_root, progress_callback=None):
        self.config = config
        self.project_root = project_root
        self.progress_callback = progress_callback or self._default_progress
        self.state = WorkflowState()
    
    def _default_progress(self, step, message, percentage):
        """Default progress callback (no-op)."""
        pass
    
    def _report_progress(self, step, message, percentage=None):
        """Report progress via callback."""
        self.progress_callback(step, message, percentage)
    
    def _handle_error(self, error, context):
        """Handle errors consistently."""
        # Log error
        # Raise structured exception
        pass
```

**Status**: Needs implementation

### 4.4 Shared Workflow Adapters
**Paths**: 
- `src/hiveforge/steering/shared/init_workflow.py`
- `src/hiveforge/steering/shared/update_workflow.py`
- `src/hiveforge/steering/shared/validate_workflow.py`

**Purpose**: Adapter classes that wrap existing workflows and provide interface-agnostic API

**Pattern**:
```python
class SharedInitWorkflow(SharedWorkflowBase):
    """Shared init workflow for both CLI and Power."""
    
    def execute(self) -> dict:
        """
        Execute init workflow.
        
        Returns:
            {
                "status": "success" | "failed",
                "files_created": int,
                "validation_report": dict,
                "errors": list,
                "warnings": list
            }
        """
        try:
            self._report_progress("init", "Starting init workflow", 0)
            
            # Step 1: Create staging directory
            self._create_staging_directory()
            self._report_progress("staging", "Staging directory ready", 10)
            
            # Step 2: Check existing files
            if not self._check_existing_files():
                return {"status": "aborted", "reason": "user_cancelled"}
            
            # ... continue with all steps
            
            return {
                "status": "success",
                "files_created": len(self.state.populated_files),
                "validation_report": self._format_validation_report(),
                "errors": [],
                "warnings": self.state.warnings
            }
        
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "partial_results": self._get_partial_results()
            }
```

**Status**: Needs implementation

### 4.5 Enhanced Error Handling Module
**Path**: `src/hiveforge/steering/shared/error_handling.py`

**Purpose**: Enhanced error handling with automatic rollback

**Components**:
```python
# Classes
- ToolExecutor: Execute operations with automatic rollback
- ErrorContext: Track error context
- ErrorSeverity: Enum for error severity levels

# Functions
- create_backup(directory) -> backup_path
- restore_backup(backup_path, target_directory)
- rollback_on_error() decorator
```

**Status**: Existing module needs enhancement for rollback support

---

## 5. Shared Backend Module Structure

Proposed directory structure:

```
src/hiveforge/steering/
├── shared/                          # NEW: Shared backend modules
│   ├── __init__.py
│   ├── workflow_base.py            # NEW: Base class for workflows
│   ├── init_workflow.py            # NEW: Shared init workflow
│   ├── update_workflow.py          # NEW: Shared update workflow
│   ├── validate_workflow.py        # NEW: Shared validate workflow
│   ├── security_wrappers.py        # NEW: Security controls
│   ├── telemetry.py                # NEW: Usage tracking
│   └── error_handling.py           # ENHANCED: Add rollback support
│
├── workflows/                       # EXISTING: CLI-specific workflows
│   ├── init_workflow.py            # REFACTOR: Use SharedInitWorkflow
│   ├── update_workflow.py          # REFACTOR: Use SharedUpdateWorkflow
│   └── validate_workflow.py        # REFACTOR: Use SharedValidateWorkflow
│
├── analyzers/                       # EXISTING: Reusable as-is
├── parsers/                         # EXISTING: Reusable as-is
├── validators/                      # EXISTING: Reusable as-is
├── agents/                          # EXISTING: Reusable as-is
├── models.py                        # EXISTING: Reusable as-is
├── templates.py                     # EXISTING: Reusable as-is
├── utils.py                         # EXISTING: Reusable as-is
└── cli.py                           # REFACTOR: Use shared workflows
```

---

## 6. Interface Adapter Pattern

### 6.1 CLI Adapter Pattern

```python
# src/hiveforge/steering/cli.py

from .shared.init_workflow import SharedInitWorkflow
from .shared.security_wrappers import secure_tool_execution

@app.command("init")
def steering_init(
    analyze_code: bool = True,
    autonomous: bool = True,
    # ... other CLI flags
):
    """Initialize steering files (CLI interface)."""
    
    # 1. Parse CLI arguments into config
    config = SteeringConfig(
        analyze_code=analyze_code,
        interactive=not autonomous,
        # ... map CLI flags to config
    )
    
    # 2. Create progress callback for CLI
    def cli_progress(step, message, percentage):
        if percentage is not None:
            print(f"   [{percentage:3d}%] {message}")
        else:
            print(f"   {message}")
    
    # 3. Execute shared workflow
    workflow = SharedInitWorkflow(
        config=config,
        project_root=Path.cwd(),
        progress_callback=cli_progress
    )
    
    result = workflow.execute()
    
    # 4. Format result for CLI display
    if result["status"] == "success":
        print(f"\n✅ Created {result['files_created']} steering files")
        _display_validation_report(result["validation_report"])
        sys.exit(0)
    else:
        print(f"\n❌ Init failed: {result['error']}")
        sys.exit(1)
```

### 6.2 Power Tool Adapter Pattern

```python
# mcp-server/tools/init_steering.py

from fastmcp import FastMCP
from src.hiveforge.steering.shared.init_workflow import SharedInitWorkflow
from src.hiveforge.steering.shared.security_wrappers import secure_tool_execution

mcp = FastMCP("hiveforge-steering")

@mcp.tool()
@secure_tool_execution(
    max_memory_mb=512,
    max_cpu_time_sec=300,
    allowed_directories=["."]
)
async def init_steering(
    auto_discover: bool = True,
    autonomous: bool = True,
    project_root: str = ".",
    confidence_threshold: float = 0.7
) -> dict:
    """Initialize steering files with autonomous generation."""
    
    # 1. Create config from MCP parameters
    config = SteeringConfig(
        analyze_code=auto_discover,
        interactive=not autonomous,
        feature_flags=FeatureFlagConfig(
            use_autonomous_generation=autonomous,
            confidence_threshold=confidence_threshold
        )
    )
    
    # 2. Create progress callback for MCP (optional)
    progress_updates = []
    def mcp_progress(step, message, percentage):
        progress_updates.append({
            "step": step,
            "message": message,
            "percentage": percentage
        })
    
    # 3. Execute shared workflow
    workflow = SharedInitWorkflow(
        config=config,
        project_root=Path(project_root),
        progress_callback=mcp_progress
    )
    
    result = workflow.execute()
    
    # 4. Format result for MCP JSON response
    return {
        "status": result["status"],
        "files_created": result.get("files_created", 0),
        "validation": result.get("validation_report", {}),
        "progress": progress_updates,
        "message": _format_message(result)
    }
```

---

## 7. Code Sharing Metrics

### 7.1 Estimated Code Distribution

| Component | Lines of Code | Shared? | Percentage |
|-----------|---------------|---------|------------|
| Business Logic (workflows) | ~2000 | ✅ Yes | 95% |
| Analysis modules | ~1500 | ✅ Yes | 100% |
| Utility modules | ~800 | ✅ Yes | 100% |
| Security wrappers | ~500 | ✅ Yes | 100% |
| Telemetry | ~200 | ✅ Yes | 100% |
| CLI interface | ~300 | ❌ No | 0% |
| Power interface | ~300 | ❌ No | 0% |
| **Total** | **~5600** | **~5000** | **~89%** |

### 7.2 Achieving >95% Code Sharing

To achieve the >95% target:

1. **Extract all business logic** from workflows into shared backend
2. **Minimize interface-specific code** to only:
   - Argument parsing (CLI flags vs MCP parameters)
   - Progress display (terminal vs JSON)
   - Result formatting (text vs JSON)
3. **Use callbacks** for all user interaction points
4. **Return structured data** instead of formatted strings

**Projected sharing after refactoring**: 96-98%

---

## 8. Migration Strategy

### Phase 2.1: Create Shared Backend Foundation
1. Create `src/hiveforge/steering/shared/` directory
2. Implement `SharedWorkflowBase` class
3. Implement security wrappers module
4. Implement telemetry module
5. Enhance error handling module

### Phase 2.2: Extract Init Workflow
1. Create `SharedInitWorkflow` class
2. Extract business logic from `InitWorkflow`
3. Add progress callbacks
4. Add structured result returns
5. Write unit tests

### Phase 2.3: Extract Update Workflow
1. Create `SharedUpdateWorkflow` class
2. Extract business logic from `UpdateWorkflow`
3. Add progress callbacks
4. Add structured result returns
5. Write unit tests

### Phase 2.4: Extract Validate Workflow
1. Create `SharedValidateWorkflow` class
2. Extract business logic from `ValidateWorkflow`
3. Add progress callbacks
4. Add structured result returns
5. Write unit tests

### Phase 3: Refactor CLI
1. Update `cli.py` to use shared workflows
2. Implement CLI-specific progress callbacks
3. Implement CLI-specific result formatting
4. Test backward compatibility
5. Verify all CLI commands work

### Phase 4: Implement Power Tools
1. Create MCP server structure
2. Implement Power tools using shared workflows
3. Implement MCP-specific progress callbacks
4. Implement JSON result formatting
5. Test with KIRO orchestrator

---

## 9. Success Criteria

### 9.1 Code Sharing Metrics
- [ ] >95% of business logic code is shared
- [ ] <5% of code is interface-specific
- [ ] Zero duplicate business logic between CLI and Power

### 9.2 Functional Equivalence
- [ ] CLI and Power produce identical file outputs for same inputs
- [ ] Both interfaces use same validation logic
- [ ] Both interfaces use same error handling
- [ ] Both interfaces use same security controls

### 9.3 Maintainability
- [ ] Single source of truth for business logic
- [ ] Bug fixes apply to both interfaces automatically
- [ ] New features can be added to shared backend once
- [ ] Clear separation between business logic and presentation

---

## 10. Risks and Mitigation

### Risk 1: Breaking CLI Backward Compatibility
**Mitigation**: 
- Comprehensive integration tests before refactoring
- Test all CLI commands with various flag combinations
- Keep old CLI implementation until new one is validated

### Risk 2: Shared Backend Too Complex
**Mitigation**:
- Start with simple adapter pattern
- Iterate based on actual needs
- Keep interfaces thin (just parsing and formatting)

### Risk 3: Performance Overhead from Abstraction
**Mitigation**:
- Benchmark before and after refactoring
- Optimize hot paths if needed
- Use profiling to identify bottlenecks

---

## 11. Next Steps

1. ✅ Complete this analysis document
2. ⏭️ Design shared backend Python module structure (Task 1.4.2)
3. ⏭️ Define adapter interfaces for CLI and Power (Task 1.4.3)
4. ⏭️ Design error handling with automatic rollback (Task 1.4.4)
5. ⏭️ Design shared telemetry system (Task 1.4.5)
6. ⏭️ Create interface specification document (Task 1.4.6)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-17  
**Next Review**: Before Phase 2 implementation
