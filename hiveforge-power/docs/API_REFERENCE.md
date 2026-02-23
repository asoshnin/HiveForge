# HiveForge Steering API Reference

**Version:** 2.2.0  
**Last Updated:** February 2026

This document provides comprehensive API documentation for all public methods introduced in the HiveForge Steering system improvements (v2.2.0).

---

## Table of Contents

1. [LLM Provider API](#llm-provider-api)
2. [Steering Assistant API](#steering-assistant-api)
3. [Code Analyzer API](#code-analyzer-api)
4. [Drift Detector API](#drift-detector-api)
5. [Workflow APIs](#workflow-apis)
6. [Data Models](#data-models)

---

## LLM Provider API

### `LLMProvider`

**Module:** `hiveforge.steering.llm.provider`

Main provider abstraction for routing LLM calls with automatic fallback.

#### Constructor

```python
def __init__(self, ctx: Optional[Any] = None)
```

**Parameters:**
- `ctx` (Optional[Any]): KIRO context object (available in MCP mode). If provided, KIRO native LLM becomes the primary provider.

**Example:**
```python
from hiveforge.steering.llm.provider import LLMProvider

# MCP mode (with KIRO context)
provider = LLMProvider(ctx=ctx)

# CLI mode (without context)
provider = LLMProvider()
```

#### Methods

##### `is_available()`

Check if any LLM provider is available and accessible.

```python
def is_available(self) -> bool
```

**Returns:**
- `bool`: True if any provider is configured and accessible, False otherwise.

**Example:**
```python
if provider.is_available():
    response = await provider.complete(system_prompt, user_prompt)
else:
    # Use fallback logic
    content = apply_inferred_markers(template)
```

##### `complete()`

Call LLM with automatic fallback chain.

```python
async def complete(
    self,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.3,
    json_mode: bool = False,
) -> Optional[str]
```

**Parameters:**
- `system_prompt` (str): System instruction for the LLM
- `user_prompt` (str): User message/prompt
- `max_tokens` (int): Maximum tokens in response (default: 2000)
- `temperature` (float): Sampling temperature 0.0-1.0 (default: 0.3)
- `json_mode` (bool): Whether to request JSON response format (default: False)

**Returns:**
- `Optional[str]`: LLM response string, or None if all providers fail

**Raises:**
- No exceptions raised; failures are logged and None is returned

**Example:**
```python
response = await provider.complete(
    system_prompt="You are a technical documentation expert.",
    user_prompt="Generate a tech stack description for a FastAPI project.",
    max_tokens=1000,
    temperature=0.1
)

if response:
    print(f"Generated: {response}")
else:
    print("LLM unavailable, using fallback")
```

---

## Steering Assistant API

### `SteeringAssistant`

**Module:** `hiveforge.steering.agents.steering_assistant`

Generates steering file content using LLM synthesis with fallback to [INFERRED] markers.

#### Constructor

```python
def __init__(
    self,
    project_root: Path,
    llm_provider: LLMProvider,
    code_analysis: CodeAnalysisResult,
    ctx: Optional[Any] = None
)
```

**Parameters:**
- `project_root` (Path): Root directory of the project
- `llm_provider` (LLMProvider): LLM provider instance
- `code_analysis` (CodeAnalysisResult): Code analysis results
- `ctx` (Optional[Any]): KIRO context (for MCP mode)

#### Methods

##### `generate_file()`

Generate steering file content using LLM synthesis.

```python
async def generate_file(
    self,
    filename: str,
    context: Dict[str, Any]
) -> str
```

**Parameters:**
- `filename` (str): Name of steering file (e.g., 'tech-stack.md')
- `context` (Dict[str, Any]): Knowledge base context including code analysis

**Returns:**
- `str`: Populated markdown string (never empty)

**Raises:**
- `FileNotFoundError`: If template not found

**Behavior:**
1. Loads raw template with frontmatter
2. Strips YAML frontmatter before sending to LLM
3. Calls LLM if available with template + context
4. Returns populated content if LLM succeeds
5. Falls back to [INFERRED] markers if LLM fails or unavailable

**Example:**
```python
assistant = SteeringAssistant(
    project_root=Path("."),
    llm_provider=provider,
    code_analysis=analysis_result
)

context = {
    'languages': ['Python'],
    'dependencies': ['fastapi', 'sqlalchemy'],
    'architecture': 'monolithic'
}

content = await assistant.generate_file('tech-stack.md', context)
print(content)
```

**Output Example (LLM available):**
```markdown
# Technology Stack

## Core Technologies

### Backend
- **Language:** Python 3.11
- **Framework:** FastAPI 0.104
- **Runtime:** CPython

### Database
- **Primary:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
```

**Output Example (LLM unavailable):**
```markdown
# Technology Stack

## Core Technologies

### Backend
- **Language:** [INFERRED: Python version]
- **Framework:** [INFERRED: Backend framework]
- **Runtime:** [INFERRED: Runtime environment]
```

---

## Code Analyzer API

### `CodeAnalyzer`

**Module:** `hiveforge.steering.analyzers.code_analyzer`

Analyzes codebase to extract project information for steering file generation.

#### Methods

##### `extract_public_api()`

Extract MCP tools, CLI commands, and public classes from codebase.

```python
def extract_public_api(self) -> PublicAPIInfo
```

**Returns:**
- `PublicAPIInfo`: Dataclass containing:
  - `mcp_tools` (List[MCPToolInfo]): MCP tools with names, docstrings, parameters
  - `cli_commands` (List[CLICommandInfo]): CLI commands with names, help text
  - `public_classes` (List[str]): Public class names

**Behavior:**
- Scans Python files for `@mcp.tool()` decorated functions
- Detects `@command()` or similar CLI decorators
- Finds non-private classes with docstrings
- Excludes `self` and `ctx` parameters
- Handles syntax errors gracefully (skips malformed files)
- Limits scan to 50 files to avoid timeout

**Example:**
```python
analyzer = CodeAnalyzer(project_root=Path("."))
api_info = analyzer.extract_public_api()

print(f"MCP Tools: {len(api_info.mcp_tools)}")
for tool in api_info.mcp_tools:
    print(f"  - {tool.name}: {tool.docstring}")
    print(f"    Parameters: {', '.join(tool.parameters)}")

print(f"\nCLI Commands: {len(api_info.cli_commands)}")
for cmd in api_info.cli_commands:
    print(f"  - {cmd.name}: {cmd.help_text}")

print(f"\nPublic Classes: {', '.join(api_info.public_classes)}")
```

**Output Example:**
```
MCP Tools: 5
  - init_steering: Initialize steering files for a project
    Parameters: project_root, source_docs_path, dry_run
  - update_steering: Update existing steering files
    Parameters: project_root, apply_draft
  - validate_steering: Validate steering files for completeness
    Parameters: project_root, strict

CLI Commands: 3
  - init: Create steering files from scratch
  - update: Update existing steering files
  - validate: Validate steering files

Public Classes: CodeAnalyzer, SteeringAssistant, LLMProvider, DriftDetector
```

##### `classify_project_with_llm()`

Classify project type using LLM enrichment (optional enhancement over heuristic classification).

```python
async def classify_project_with_llm(
    self,
    llm_provider: LLMProvider
) -> Dict[str, Any]
```

**Parameters:**
- `llm_provider` (LLMProvider): LLM provider for enrichment

**Returns:**
- `Dict[str, Any]`: Classification dict with keys:
  - `project_type` (str): "cli_tool", "mcp_server", "cli_and_mcp", "web_app", or "library"
  - `has_frontend` (bool): Whether project has frontend
  - `has_database` (bool): Whether project has database
  - `has_rest_api` (bool): Whether project has REST API
  - `primary_language` (str): Primary programming language
  - `one_line_description` (str): LLM-generated project description
  - `key_capabilities` (List[str]): LLM-generated list of 3 key capabilities

**Behavior:**
1. Runs heuristic classification first
2. If LLM available, sends code analysis summary for enrichment
3. LLM adds `one_line_description` and `key_capabilities`
4. Falls back to heuristic-only if LLM unavailable

**Example:**
```python
analyzer = CodeAnalyzer(project_root=Path("."))
classification = await analyzer.classify_project_with_llm(llm_provider)

print(f"Project Type: {classification['project_type']}")
print(f"Description: {classification['one_line_description']}")
print(f"Capabilities:")
for cap in classification['key_capabilities']:
    print(f"  - {cap}")
```

**Output Example:**
```
Project Type: cli_and_mcp
Description: AI-powered steering file generator for KIRO methodology projects
Capabilities:
  - Automatic code analysis and documentation extraction
  - LLM-powered steering file generation with confidence scoring
  - Drift detection between documentation and codebase
```

---

## Drift Detector API

### `DriftDetector`

**Module:** `hiveforge.steering.detectors.drift_detector`

Detects drift between steering files and current codebase state.

#### Constructor

```python
def __init__(self, logger=None)
```

**Parameters:**
- `logger` (Optional[logging.Logger]): Logger instance (defaults to module logger)

#### Methods

##### `detect()`

Detect drift between steering files and codebase.

```python
def detect(
    self,
    existing_files: Dict[str, str],
    code_analysis: CodeAnalysisResult
) -> DriftReport
```

**Parameters:**
- `existing_files` (Dict[str, str]): Dict of filename → content from steering files
- `code_analysis` (CodeAnalysisResult): Fresh code analysis result

**Returns:**
- `DriftReport`: Report containing:
  - `items` (List[DriftItem]): List of detected drift items
  - `detected_at` (datetime): Timestamp of detection
  - `has_drift()` method: Returns True if any drift detected
  - `by_severity()` method: Returns items sorted by confidence (highest first)

**Drift Categories:**
- `LANGUAGE_VERSION`: Python version mismatch (confidence: 0.95)
- `NEW_DEPENDENCY`: New significant dependency detected (confidence: 0.85)
- `ARCHITECTURE_PATTERN`: Architecture pattern mismatch (confidence: 0.75)
- `CONVENTION_MISMATCH`: Naming convention mismatch (confidence: 0.70)

**Example:**
```python
detector = DriftDetector()

# Load existing steering files
existing_files = {
    'tech-stack.md': Path('.kiro/steering/tech-stack.md').read_text(),
    'architecture.md': Path('.kiro/steering/architecture.md').read_text(),
    'conventions.md': Path('.kiro/steering/conventions.md').read_text(),
}

# Get fresh code analysis
analyzer = CodeAnalyzer(project_root=Path("."))
code_analysis = analyzer.analyze()

# Detect drift
report = detector.detect(existing_files, code_analysis)

if report.has_drift():
    print(f"Detected {len(report.items)} drift items:")
    for item in report.by_severity():
        print(f"\n[{item.category.value}] Confidence: {item.confidence:.0%}")
        print(f"  {item.description}")
        print(f"  → {item.suggested_action}")
else:
    print("No drift detected - steering files are up to date!")
```

**Output Example:**
```
Detected 3 drift items:

[language_version] Confidence: 95%
  Python version mismatch: tech-stack.md says 3.10, pyproject.toml has 3.11
  → Update tech-stack.md to Python 3.11

[new_dependency] Confidence: 85%
  New significant dependency detected: redis
  → Add redis to tech-stack.md dependencies table

[architecture_pattern] Confidence: 75%
  Architecture pattern mismatch: docs say monolith, code shows microservices
  → Review and update architecture.md to reflect microservices pattern
```

---

## Workflow APIs

### `AutonomousWorkflow`

**Module:** `hiveforge.steering.workflows.autonomous_workflow`

Autonomous steering file generation workflow with LLM synthesis and draft review.

#### Key Methods

##### `execute()`

Execute the autonomous workflow.

```python
async def execute(self) -> WorkflowResult
```

**Returns:**
- `WorkflowResult`: Result containing:
  - `status` (str): "success", "draft_ready", or "failed"
  - `files_created` (List[Path]): Files that were created
  - `files_modified` (List[Path]): Files that were modified
  - `errors` (List[str]): Error messages
  - `warnings` (List[str]): Warning messages
  - `metadata` (Dict[str, Any]): Additional metadata including:
    - `draft_summary` (str): Draft summary for IDE display (MCP mode)
    - `draft_files` (List[Dict]): Draft file metadata (MCP mode)
    - `confidence_scores` (Dict[str, float]): Confidence scores per file
    - `fallback_reasons` (List[str]): Reasons for fallback usage

**Workflow Steps:**
1. Analyze code (if enabled)
2. Generate all files with LLM synthesis
3. Create draft state with confidence scores
4. Review draft (interactive in CLI, stored in MCP)
5. Write files (if approved in CLI, deferred in MCP)
6. Validate files

**Example (CLI mode):**
```python
workflow = AutonomousWorkflow(
    config=SteeringConfig(
        project_root=Path("."),
        interactive=True,
        analyze_code=True
    ),
    ctx=None
)

result = await workflow.execute()

if result.status == "success":
    print(f"Created {len(result.files_created)} steering files")
else:
    print(f"Errors: {', '.join(result.errors)}")
```

**Example (MCP mode):**
```python
workflow = AutonomousWorkflow(
    config=SteeringConfig(
        project_root=Path("."),
        interactive=False,
        analyze_code=True
    ),
    ctx=ctx
)

result = await workflow.execute()

if result.status == "draft_ready":
    # Draft stored for IDE review
    print(result.metadata['draft_summary'])
    
    # User reviews in IDE, then calls:
    # await update_steering(ctx, apply_draft=True)
```

---

## Data Models

### `PublicAPIInfo`

**Module:** `hiveforge.steering.models`

Container for extracted public API information.

```python
@dataclass
class PublicAPIInfo:
    mcp_tools: List[MCPToolInfo]
    cli_commands: List[CLICommandInfo]
    public_classes: List[str]
```

### `MCPToolInfo`

Information about an MCP tool.

```python
@dataclass
class MCPToolInfo:
    name: str
    docstring: str
    parameters: List[str]
```

### `CLICommandInfo`

Information about a CLI command.

```python
@dataclass
class CLICommandInfo:
    name: str
    help_text: str
    parameters: List[str]
```

### `DraftFile`

Single file in draft state.

```python
@dataclass
class DraftFile:
    filename: str
    content: str
    confidence: float
    placeholder_count: int
    preview: str  # First 300 chars
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
```

### `DraftState`

State of generated files awaiting review.

```python
@dataclass
class DraftState:
    files: List[DraftFile]
    created_at: datetime
    is_approved: bool = False
    
    def summary(self) -> str:
        """Generate summary for display"""
```

### `DriftItem`

Single drift detection result.

```python
@dataclass
class DriftItem:
    category: DriftCategory
    description: str
    confidence: float  # 0.0-1.0
    suggested_action: str
```

### `DriftReport`

Report of all detected drift.

```python
@dataclass
class DriftReport:
    items: List[DriftItem]
    detected_at: datetime
    
    def has_drift(self) -> bool:
        """Check if any drift detected"""
    
    def by_severity(self) -> List[DriftItem]:
        """Return items sorted by confidence (highest first)"""
```

### `LLMConfig`

Configuration for LLM provider.

```python
@dataclass
class LLMConfig:
    provider_type: ProviderType
    api_key: Optional[str] = None
    project_id: Optional[str] = None  # For Vertex AI
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000
```

---

## Usage Examples

### Complete Workflow Example

```python
from pathlib import Path
from hiveforge.steering.llm.provider import LLMProvider
from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
from hiveforge.steering.agents.steering_assistant import SteeringAssistant
from hiveforge.steering.detectors.drift_detector import DriftDetector
from hiveforge.steering.workflows.autonomous_workflow import AutonomousWorkflow
from hiveforge.steering.models import SteeringConfig

async def generate_steering_files(project_root: Path, ctx=None):
    """Complete example of generating steering files"""
    
    # 1. Initialize LLM provider
    llm_provider = LLMProvider(ctx=ctx)
    
    if not llm_provider.is_available():
        print("Warning: No LLM provider available, will use [INFERRED] markers")
    
    # 2. Analyze codebase
    analyzer = CodeAnalyzer(project_root=project_root)
    code_analysis = analyzer.analyze()
    
    # Extract public API
    api_info = analyzer.extract_public_api()
    print(f"Found {len(api_info.mcp_tools)} MCP tools")
    print(f"Found {len(api_info.cli_commands)} CLI commands")
    
    # Classify project
    classification = await analyzer.classify_project_with_llm(llm_provider)
    print(f"Project type: {classification['project_type']}")
    
    # 3. Generate steering files
    config = SteeringConfig(
        project_root=project_root,
        interactive=False,  # MCP mode
        analyze_code=True
    )
    
    workflow = AutonomousWorkflow(config=config, ctx=ctx)
    result = await workflow.execute()
    
    if result.status == "draft_ready":
        print("\nDraft Summary:")
        print(result.metadata['draft_summary'])
        
        # In MCP mode, user reviews and approves in IDE
        # Then calls: await update_steering(ctx, apply_draft=True)
    
    elif result.status == "success":
        print(f"\nSuccess! Created {len(result.files_created)} files")
        
        # 4. Check for drift (optional)
        existing_files = {
            f.name: f.read_text()
            for f in (project_root / '.kiro' / 'steering').glob('*.md')
        }
        
        detector = DriftDetector()
        drift_report = detector.detect(existing_files, code_analysis)
        
        if drift_report.has_drift():
            print(f"\nWarning: Detected {len(drift_report.items)} drift items")
            for item in drift_report.by_severity()[:3]:  # Top 3
                print(f"  - {item.description}")
    
    else:
        print(f"\nFailed: {', '.join(result.errors)}")

# Run the workflow
import asyncio
asyncio.run(generate_steering_files(Path(".")))
```

---

## Error Handling

All public methods follow these error handling principles:

1. **LLM Provider**: Never raises exceptions; returns `None` on failure
2. **Steering Assistant**: Raises `FileNotFoundError` for missing templates; never returns empty content
3. **Code Analyzer**: Handles syntax errors gracefully; skips malformed files
4. **Drift Detector**: Never raises exceptions; returns empty report on failure
5. **Workflows**: Return `WorkflowResult` with errors list; never crash

**Example Error Handling:**

```python
# LLM Provider
response = await provider.complete(system_prompt, user_prompt)
if response is None:
    # Handle fallback
    content = apply_inferred_markers(template)

# Steering Assistant
try:
    content = await assistant.generate_file('tech-stack.md', context)
except FileNotFoundError as e:
    print(f"Template not found: {e}")

# Code Analyzer
api_info = analyzer.extract_public_api()
# Always returns PublicAPIInfo, even if empty

# Drift Detector
report = detector.detect(existing_files, code_analysis)
if not report.has_drift():
    print("No drift detected")
```

---

## Version History

### v2.2.0 (February 2026)

**New APIs:**
- `LLMProvider.complete()` - LLM abstraction with fallback
- `SteeringAssistant.generate_file()` - LLM-powered file generation
- `CodeAnalyzer.extract_public_api()` - MCP/CLI detection
- `CodeAnalyzer.classify_project_with_llm()` - LLM-enriched classification
- `DriftDetector.detect()` - Drift detection between docs and code

**New Data Models:**
- `PublicAPIInfo`, `MCPToolInfo`, `CLICommandInfo`
- `DraftFile`, `DraftState`
- `DriftItem`, `DriftReport`
- `LLMConfig`

---

## See Also

- [Configuration Guide](CONFIGURATION.md) - LLM provider configuration
- [Steering Assistant Guide](../docs/steering-assistant-guide.md) - User guide
- [Architecture Documentation](../docs/architecture.md) - System architecture
- [Migration Guide](MIGRATION.md) - Upgrading from v2.1.x

---

**Last Updated:** February 2026  
**Maintainer:** HiveForge Team
