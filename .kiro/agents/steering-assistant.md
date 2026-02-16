# Steering Assistant Agent

## Overview

The Steering Assistant is an AI agent that helps create and maintain steering files for HiveForge projects. It conducts interactive conversations to gather project information, fills knowledge gaps, and generates comprehensive steering documentation.

## Capabilities

### Information Gathering
- Conducts structured conversations to gather missing project information
- Asks targeted questions based on gap analysis of existing knowledge
- Batches questions efficiently (max 8 per batch) to minimize back-and-forth
- Supports both interactive and non-interactive modes

### Knowledge Integration
- Integrates information from multiple sources:
  - Parsed artifacts (markdown, PDF, images)
  - Code analysis results (tech stack, architecture, conventions)
  - User responses during conversation
  - Optional web research (when --research flag enabled)

### Template Population
- Populates 8 steering file templates with gathered information
- Preserves frontmatter and template structure
- Replaces placeholders with contextually appropriate content
- Generates token-efficient summaries (max 4000 tokens per template)

### Intelligent Question Generation
- Prioritizes questions by importance and template requirements
- Groups questions by steering file for logical flow
- Provides context for each question to help users respond accurately
- Avoids redundant questions through response caching

## Usage

### Init Workflow

The Steering Assistant is invoked during `hiveforge steering init`:

```bash
# Interactive mode (default)
hiveforge steering init

# With code analysis
hiveforge steering init --analyze-code

# Non-interactive mode (use only artifacts)
hiveforge steering init --no-interactive

# With web research
hiveforge steering init --research
```

### Update Workflow

The Steering Assistant is invoked during `hiveforge steering update`:

```bash
# Interactive mode (default)
hiveforge steering update

# Non-interactive mode
hiveforge steering update --no-interactive

# With web research
hiveforge steering update --research
```

## Workflow Integration

### Init Workflow Steps
1. Parse artifacts from `.kiro/onboarding/`
2. Optionally analyze existing codebase (with --analyze-code)
3. Build knowledge base from parsed content
4. Run gap analysis to identify missing information
5. **Conduct conversation** to fill knowledge gaps
6. Populate steering file templates
7. Write files to `.kiro/steering/`
8. Validate generated files

### Update Workflow Steps
1. Parse existing steering files
2. Parse new artifacts from `.kiro/onboarding/`
3. Detect user customizations
4. Run gap analysis on new information
5. **Conduct conversation** to fill knowledge gaps
6. Detect conflicts between old and new information
7. Generate diffs and get user approval
8. Apply approved changes
9. Validate updated files

## Configuration

The Steering Assistant behavior is controlled by `SteeringConfig`:

```python
config = SteeringConfig(
    research_enabled=False,      # Enable web research
    interactive=True,            # Enable conversation mode
    skip_validation=False,       # Skip post-generation validation
    analyze_code=False,          # Analyze existing codebase
    backup_enabled=True,         # Create backups before changes
    backup_dir=Path(".kiro/backups")
)
```

## Response Caching

The Steering Assistant uses response caching to avoid redundant API calls:

- Cache key: Hash of question text
- Cache location: `.kiro/.cache/response_cache.json`
- Cache invalidation: Manual (delete cache file)
- Benefits: Faster responses, reduced API costs, consistent answers

## Token Efficiency

The Steering Assistant implements several strategies to minimize token usage:

1. **Question Batching**: Max 8 questions per batch
2. **Knowledge Base Limiting**: Max 4000 tokens of context per prompt
3. **Template Summaries**: Max 2000 tokens per steering file
4. **Response Caching**: Avoid re-asking answered questions
5. **Incremental Updates**: Only send changed sections (max 3000 tokens per file)

## Error Handling

The Steering Assistant handles various error conditions gracefully:

- **LLM API Errors**: Exponential backoff with max 3 retries
- **Rate Limiting**: Automatic retry with backoff (2^retry_count seconds)
- **Timeouts**: Retry with increased timeout
- **Invalid Responses**: Request regeneration
- **Network Errors**: Retry with backoff

## Best Practices

### For Users

1. **Prepare Artifacts**: Place relevant documents in `.kiro/onboarding/` before running init
2. **Use Code Analysis**: Enable --analyze-code for existing projects to auto-extract information
3. **Be Specific**: Provide detailed answers during conversation for better results
4. **Review Output**: Always review generated steering files before committing
5. **Customize**: Feel free to customize generated files - the assistant preserves customizations during updates

### For Developers

1. **Gap Analysis First**: Always run gap analysis before starting conversation
2. **Batch Questions**: Group related questions together for better context
3. **Provide Context**: Include relevant context with each question
4. **Cache Responses**: Use response cache to avoid redundant API calls
5. **Token Limiting**: Respect token limits for knowledge base and templates

## Examples

### Example 1: Init with Artifacts

```bash
# 1. Place artifacts in staging folder
mkdir -p .kiro/onboarding
cp project-spec.md .kiro/onboarding/
cp architecture-diagram.pdf .kiro/onboarding/

# 2. Run init
hiveforge steering init

# 3. Answer questions during conversation
# The assistant will ask about missing information

# 4. Review generated files
ls .kiro/steering/
```

### Example 2: Init with Code Analysis

```bash
# Analyze existing codebase and generate steering files
hiveforge steering init --analyze-code

# The assistant will:
# - Detect languages and versions
# - Extract tech stack from dependencies
# - Infer architecture from directory structure
# - Extract coding conventions from code
# - Parse existing documentation
# - Ask only about information it couldn't extract
```

### Example 3: Update with New Information

```bash
# 1. Add new artifacts
cp updated-requirements.md .kiro/onboarding/

# 2. Run update
hiveforge steering update

# 3. Review conflicts and diffs
# The assistant will show what changed and ask for approval

# 4. Approve changes
# Your customizations will be preserved
```

## Troubleshooting

### Issue: Assistant asks too many questions

**Solution**: Use --analyze-code to auto-extract information, or place more artifacts in `.kiro/onboarding/`

### Issue: Generated content is too generic

**Solution**: Provide more detailed answers during conversation, or add more specific artifacts

### Issue: Assistant doesn't preserve my customizations

**Solution**: The assistant should preserve customizations automatically. If not, check that your changes are substantial (not just placeholder replacements)

### Issue: LLM API rate limiting

**Solution**: The assistant automatically retries with exponential backoff. Wait a few minutes if you hit rate limits repeatedly.

### Issue: Conversation takes too long

**Solution**: Use --no-interactive mode to skip conversation and use only artifacts and code analysis

## Related Components

- **GapAnalysisEngine**: Identifies missing information before conversation
- **KnowledgeBase**: Stores and retrieves gathered information
- **TemplatePopulator**: Populates steering file templates
- **ResponseCache**: Caches LLM responses to avoid redundant calls
- **SteeringValidator**: Validates generated steering files

## Requirements

Implements requirements:
- 4.1-4.8: Init workflow conversation and template generation
- 5.1-5.11: Update workflow conversation and conflict resolution
- 7.1-7.8: Conversation orchestration and token efficiency
- 12.1-12.5: Interactive vs non-interactive modes

## See Also

- [Steering Validator Agent](./steering-validator.md)
- [Init Workflow Documentation](../docs/init-workflow.md)
- [Update Workflow Documentation](../docs/update-workflow.md)
