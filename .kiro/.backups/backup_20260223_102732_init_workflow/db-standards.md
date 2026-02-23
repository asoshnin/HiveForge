---
inclusion: fileMatch
patterns: ["src/**/storage/**", "src/**/cache/**", "src/**/models.py", ".kiro/.cache/**"]
priority: 2
description: "File-based storage patterns, caching strategies, data models. Loaded when working on storage/cache code."
---

# Storage & Caching Standards

## File-Based Storage Design

### Storage Locations
- **Steering Files:** `.kiro/steering/` - User-facing documentation
- **Cache Files:** `.kiro/.cache/` - Performance optimization
- **Telemetry:** `.kiro/.telemetry/` - Monitoring data
- **Backups:** `.kiro/backups/` - Automatic rollback support
- **Staging:** `.kiro/onboarding/` - Source documents for analysis

### File Naming Conventions
- Use kebab-case for directories: `.kiro/steering/`
- Use snake_case for Python modules: `code_analyzer.py`
- Use descriptive names: `response_cache.json`, `code_analysis.json`
- Include timestamps for backups: `backup_20260217_103000/`
- Include event type for telemetry: `workflow_start_2026-02-17T10-30-00.json`

### File Formats
- **Configuration:** JSON (`.json`) - Structured data, easy parsing
- **Documentation:** Markdown (`.md`) - Human-readable, version control friendly
- **Cache:** JSON (`.json`) - Fast serialization/deserialization
- **Logs:** JSON Lines (`.jsonl`) - Append-only, streaming-friendly

## Data Models (Pydantic)

### Model Design Principles
- Use Pydantic for validation and serialization
- Provide sensible defaults
- Make fields optional when appropriate
- Use type hints for all fields

### Core Models
```python
class SteeringConfig(BaseModel):
    research_enabled: bool = False
    skip_validation: bool = False
    interactive: bool = True
    analyze_code: bool = False
    backup_enabled: bool = True
    backup_dir: Path = Path(".kiro/backups")
    strict_mode: bool = False
    rollback_enabled: bool = True
    max_backups: int = 10
    telemetry_enabled: bool = True
```

### Validation Rules
- Validate paths exist before reading
- Validate paths are writable before writing
- Validate file types against whitelist
- Validate JSON schema on deserialization

## Caching Strategy

### Response Cache
- **Location:** `.kiro/.cache/response_cache.json`
- **Purpose:** Cache LLM responses to avoid redundant API calls
- **Key:** Hash of question + context
- **Invalidation:** Manual or on knowledge base changes
- **Max Size:** 10 MB (automatic cleanup of oldest entries)

### Code Analysis Cache
- **Location:** `.kiro/.cache/code_analysis.json`
- **Purpose:** Cache code analysis results for performance
- **Key:** Project root path + file modification times
- **Invalidation:** On file changes (mtime comparison)
- **Max Age:** 24 hours

### Validation Cache
- **Location:** `.kiro/.cache/validation_cache.json`
- **Purpose:** Cache validation results for performance
- **Key:** File path + content hash
- **Invalidation:** On file changes
- **Max Age:** 1 hour

## Backup & Rollback

### Backup Strategy
- **Automatic Backups:** Created before destructive operations (init with --force, update, reset)
- **Backup Location:** `.kiro/backups/backup_YYYYMMDD_HHMMSS/`
- **Backup Contents:** All steering files from `.kiro/steering/`
- **Max Backups:** 10 (configurable, oldest deleted first)

### Rollback Process
1. List available backups: `ls .kiro/backups/`
2. Verify backup contents: `ls .kiro/backups/backup_20260217_103000/steering/`
3. Restore: `cp -r .kiro/backups/backup_20260217_103000/steering .kiro/`
4. Validate: `hiveforge steering validate`

## Telemetry Storage

### Event Types
- `workflow_start`: Workflow initiated
- `workflow_complete`: Workflow succeeded
- `workflow_error`: Workflow failed
- `tool_invocation`: MCP tool called
- `llm_api_call`: LLM API request made

### Event Schema
```json
{
  "event_type": "workflow_complete",
  "timestamp": "2026-02-17T10:30:05Z",
  "workflow_name": "init",
  "interface_type": "CLI",
  "success": true,
  "duration_ms": 15234,
  "files_created": 8,
  "parameters": {}
}
```

### Retention Policy
- Keep telemetry for 30 days
- Automatic cleanup of old events
- No PII collected
- Local storage only (never transmitted)

## File System Operations

### Read Operations
- Always use UTF-8 encoding with fallbacks (latin-1, cp1252, iso-8859-1)
- Handle missing files gracefully (log warning, continue)
- Respect .gitignore patterns using pathspec library
- Use Path objects from pathlib (not string concatenation)

### Write Operations
- Create parent directories automatically: `path.parent.mkdir(parents=True, exist_ok=True)`
- Use atomic writes (write to temp file, then rename)
- Always use UTF-8 encoding
- Normalize paths before writing: `path.resolve()`

### Security
- Validate paths to prevent directory traversal: `path.resolve().is_relative_to(project_root)`
- Never execute user-provided paths
- Sanitize file names: Remove special characters, limit length
- Check write permissions before attempting write

## Performance Optimization

### File I/O
- Use buffered I/O for large files
- Stream large files instead of loading into memory
- Use `mmap` for very large files (>100 MB)
- Batch file operations when possible

### Caching
- Cache frequently accessed data (templates, validation rules)
- Use LRU cache for in-memory caching: `@lru_cache(maxsize=128)`
- Invalidate cache on file changes
- Monitor cache hit rate in telemetry

### Sampling Strategy
- For codebases >10k files, sample 1000 files
- Prioritize recently modified files
- Include all dependency files (package.json, requirements.txt, etc.)
- Log sampling statistics to telemetry

## Error Handling

### File Not Found
- Log warning with file path
- Continue with remaining files
- Include in validation report

### Permission Denied
- Log error with file path
- Suggest checking file permissions
- Fail gracefully (don't crash)

### Disk Full
- Detect before writing (check available space)
- Clean up partial writes
- Suggest freeing disk space

### Corrupted Files
- Detect using JSON schema validation
- Log error with file path
- Attempt recovery from backup
- Suggest manual inspection
