# LLM Provider Configuration

The HiveForge Steering system uses an LLM provider abstraction that supports multiple backends with automatic fallback.

## Provider Priority

The system tries providers in this order:

1. **KIRO Native** (primary in MCP mode) - Uses `ctx.sample()` from KIRO IDE
2. **Google Vertex AI** - Google Cloud's AI platform
3. **OpenAI** - OpenAI's GPT models
4. **None** - Falls back to `[INFERRED]` markers

## Configuration Methods

### 1. Environment Variables (Highest Priority)

#### For Vertex AI:
```bash
export HIVEFORGE_LLM_PROVIDER=vertex
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

#### For OpenAI:
```bash
export HIVEFORGE_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-api-key
```

### 2. Configuration File

Create `~/.hiveforge/llm_config.json`:

#### For Vertex AI:
```json
{
  "provider_type": "vertex_ai",
  "project_id": "your-gcp-project",
  "model": "gemini-pro",
  "temperature": 0.1,
  "max_tokens": 2000
}
```

#### For OpenAI:
```json
{
  "provider_type": "openai",
  "api_key": "sk-your-api-key",
  "model": "gpt-4",
  "temperature": 0.1,
  "max_tokens": 2000
}
```

### 3. KIRO Native (MCP Mode)

When running inside KIRO IDE via MCP, no configuration is needed. The system automatically uses KIRO's native LLM capabilities through the `ctx` parameter.

## Installation

### Base Installation
```bash
pip install hiveforge-steering-mcp
```

### With Vertex AI Support
```bash
pip install hiveforge-steering-mcp[vertex]
```

### With OpenAI Support
```bash
pip install hiveforge-steering-mcp[openai]
```

### With All LLM Providers
```bash
pip install hiveforge-steering-mcp[all-llm]
```

## Usage in Code

```python
from hiveforge.steering.llm import LLMProvider

# In MCP mode (with KIRO context)
provider = LLMProvider(ctx=ctx)

# In CLI mode (uses config file or env vars)
provider = LLMProvider(ctx=None)

# Check if any provider is available
if provider.is_available():
    response = await provider.complete(
        system_prompt="You are a technical documentation expert.",
        user_prompt="Generate a tech stack description for a Python FastAPI project.",
        max_tokens=2000,
        temperature=0.3
    )
    print(response)
else:
    print("No LLM provider available, using fallback markers")
```

## Fallback Behavior

When no LLM provider is available or all providers fail:

1. The system logs warnings about the failure
2. Returns `None` from `complete()` calls
3. Callers apply `[INFERRED: placeholder]` markers to templates
4. Files are still generated with placeholder content for manual review

This ensures the system never crashes due to LLM unavailability.

## Error Handling

The LLMProvider handles errors gracefully:

- **KIRO native fails**: Falls back to Vertex AI → OpenAI → None
- **Vertex AI fails**: Falls back to OpenAI → None
- **OpenAI fails**: Returns None
- **All fail**: Returns None, caller uses `[INFERRED]` markers

All failures are logged at WARNING level with details about the error.

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure config files
- For Vertex AI, use service account credentials with minimal permissions
- For OpenAI, use API keys with usage limits

## Troubleshooting

### "No LLM provider available"
- Check that environment variables are set correctly
- Verify `~/.hiveforge/llm_config.json` exists and is valid JSON
- Ensure optional dependencies are installed (`pip install hiveforge-steering-mcp[vertex]` or `[openai]`)

### "Vertex AI call failed"
- Verify `GOOGLE_CLOUD_PROJECT` is set
- Check that credentials file exists and is valid
- Ensure the service account has Vertex AI permissions

### "OpenAI call failed"
- Verify `OPENAI_API_KEY` is set and valid
- Check API key has sufficient credits
- Ensure you're not hitting rate limits

### "KIRO native call failed"
- Verify you're running inside KIRO IDE (MCP mode)
- Check that `ctx` parameter is being passed correctly
- Ensure KIRO IDE has LLM access enabled
