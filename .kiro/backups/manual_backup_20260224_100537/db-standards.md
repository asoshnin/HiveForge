---
inclusion: fileMatch
patterns: ["hiveforge/**/models.py", "hiveforge/**/knowledge_base.py", "hiveforge/**/templates.py"]
priority: 2
description: "Data model and filesystem storage conventions. HiveForge has no database — this covers in-memory models and file storage patterns."
---

# Data & Storage Standards

## Overview
HiveForge is a filesystem-based CLI tool with no persistent database. All data storage uses:
- **In-memory dataclasses** during workflow execution
- **Markdown files** for steering file output (`.kiro/steering/*.md`)
- **JSON/YAML** for configuration and validation rules
- **Python `dataclasses`** for all domain models (no ORM)

## Data Model Conventions (`models.py`)

### Dataclass Design
- Use `@dataclass` for all domain models
- Use `@dataclass(frozen=True)` for value objects (e.g., `ConfidenceScore`)
- Always define `__post_init__` for derived fields and validation
- Use `field(default_factory=list)` for mutable defaults, never `field(default=[])`

### Naming
- Model classes: `PascalCase` with descriptive names (`WorkflowState`, `ValidationReport`, `DraftFile`)
- Fields: `snake_case` matching their semantic meaning
- Optional fields: `Optional[X] = None` with explicit `None` default

### Required Fields for State Models
Every workflow state model must include:
- `created_at: datetime` — when the state was created
- Status field indicating current lifecycle stage

### Example Pattern
```python
@dataclass
class WorkflowState:
    steering_dir: Path
    staging_dir: Path
    created_at: datetime = field(default_factory=datetime.now)
    gathered_info: Dict[str, Any] = field(default_factory=dict)
    populated_files: Dict[str, str] = field(default_factory=dict)
    validation_report: Optional[ValidationReport] = None
```

## Filesystem Storage Conventions

### Directory Structure
```
.kiro/
  steering/          # Generated steering files (output)
  onboarding/        # Source documents for analysis (input)
  backups/           # Timestamped backups before overwrite
    steering_backup_YYYYMMDD_HHMMSS/
```

### File Naming
- Steering files: `kebab-case.md` (e.g., `tech-stack.md`, `project-vision.md`)
- Backup directories: `steering_backup_{YYYYMMDD}_{HHMMSS}`
- Never use spaces or special characters in generated file names

### File Writing Rules
- Always create a timestamped backup before overwriting existing steering files
- Write atomically where possible (write to temp, then rename)
- Use `utf-8` encoding for all file reads and writes
- Never truncate existing files without explicit user confirmation

## Configuration Files

### `validation_rules.yaml`
- Defines structural and semantic validation rules for steering files
- Never edit at runtime — load once at startup
- Schema: `{rule_id, severity, check_type, pattern, message}`

### Template Files
- Located in `hiveforge/templates/steering/`
- One `.md` file per steering template
- Placeholders use `{placeholder_name}` or `{option1|option2|...}` format
- Frontmatter must be preserved exactly as-is during population

## Migration Strategy
Since there is no database, "migrations" apply to:
1. **Template format changes** — bump template version in `templates.py`; provide migration script if placeholder names change
2. **Model field additions** — always additive; use `Optional` with `None` default for new fields
3. **Steering file format changes** — document in `MIGRATION.md`; provide `hiveforge steering migrate` command for breaking changes
4. Never remove fields from public models without a deprecation cycle
