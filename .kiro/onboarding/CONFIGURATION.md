# HiveForge LLM Configuration Guide

This guide explains how to configure LLM providers for HiveForge Steering System.

## Overview

HiveForge uses an LLM provider abstraction that supports multiple backends with automatic fallback:

1. **KIRO Native** (primary) - Uses KIRO IDE's built-in LLM via `ctx.sample()`
2. **Google Vertex AI** - Google Cloud's AI platform
3. **OpenAI** - OpenAI's GPT models
4. **None** - Falls back to `[INFERRED]` markers when no provider available

## Configuration Priority

The system loads configuration in this order (highest priority first):

1. **Environment Variables** - Override all other settings
2. **Configuration File** - `~/.hiveforge/llm_config.json`
3. **Defaults** - KIRO native if available, otherwise no external provider

## KIRO Native (Recommended for IDE Users)

When running inside KIRO IDE via MCP, no configuration is needed. HiveForge automatically detects the KIRO context and uses native LLM capabilities.

**Advantages:**
- Zero configuration required
- No API keys or credentials needed
- Fastest response times (no network overhead)
- Seamless integration with KIRO IDE

**Usage:**
Simply run HiveForge commands from within KIRO IDE. The system automatically uses KIRO native LLM.

## Google Vertex AI Configuration

### Prerequisites

1. Google Cloud project with Vertex AI API enabled
2. Service account with Vertex AI permissions
3. Service account credentials JSON file

### Environment Variables

```bash
export HIVEFORGE_LLM_PROVIDER=vertex
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### Configuration File

Create `~/.hiveforge/llm_config.json`:

```json
{
  "provider_type": "vertex_ai",
  "project_id": "your-gcp-project-id",
  "model": "gemini-pro",
  "temperature": 0.1,
  "max_tokens": 2000
}
```

**Note:** The credentials file path must still be set via `GOOGLE_APPLICATION_CREDENTIALS` environment variable.

### Installation

```bash
pip install hiveforge-steering-mcp[vertex]
```

### Configuration Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider_type` | string | - | Must be `"vertex_ai"` |
| `project_id` | string | - | Google Cloud project ID |
| `model` | string | `"gemini-pro"` | Vertex AI model name |
| `temperature` | float | `0.1` | Sampling temperature (0.0-1.0) |
| `max_tokens` | int | `2000` | Maximum response tokens |

## OpenAI Configuration

### Prerequisites

1. OpenAI account with API access
2. Valid API key with sufficient credits

### Environment Variables

```bash
export HIVEFORGE_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-api-key-here
```

### Configuration File

Create `~/.hiveforge/llm_config.json`:

```json
{
  "provider_type": "openai",
  "api_key": "sk-your-api-key-here",
  "model": "gpt-4",
  "temperature": 0.1,
  "max_tokens": 2000
}
```

### Installation

```bash
pip install hiveforge-steering-mcp[openai]
```

### Configuration Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider_type` | string | - | Must be `"openai"` |
| `api_key` | string | - | OpenAI API key |
| `model` | string | `"gpt-4"` | OpenAI model name |
| `temperature` | float | `0.1` | Sampling temperature (0.0-1.0) |
| `max_tokens` | int | `2000` | Maximum response tokens |

## Configuration File Format

### Location

- **Linux/Mac:** `~/.hiveforge/llm_config.json`
- **Windows:** `%USERPROFILE%\.hiveforge\llm_config.json`

### Schema

```json
{
  "provider_type": "vertex_ai" | "openai",
  "api_key": "string (optional, for OpenAI)",
  "project_id": "string (optional, for Vertex AI)",
  "model": "string (optional, default varies by provider)",
  "temperature": 0.1,
  "max_tokens": 2000
}
```

### Example Configurations

**Minimal Vertex AI:**
```json
{
  "provider_type": "vertex_ai",
  "project_id": "my-gcp-project"
}
```

**Minimal OpenAI:**
```json
{
  "provider_type": "openai",
  "api_key": "sk-..."
}
```

**Full Configuration:**
```json
{
  "provider_type": "openai",
  "api_key": "sk-...",
  "model": "gpt-4-turbo",
  "temperature": 0.2,
  "max_tokens": 3000
}
```

## Environment Variable Reference

### Provider Selection

| Variable | Values | Description |
|----------|--------|-------------|
| `HIVEFORGE_LLM_PROVIDER` | `vertex`, `openai` | Select LLM provider |

### Vertex AI

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account credentials JSON |

### OpenAI

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key (starts with `sk-`) |

## Fallback Behavior

When the primary provider fails, HiveForge automatically tries remaining providers:

1. **Primary fails** → Try Vertex AI
2. **Vertex AI fails** → Try OpenAI
3. **All fail** → Return `None`, caller uses `[INFERRED]` markers

**Example Fallback Chain:**
```
KIRO Native (unavailable in CLI mode)
  ↓ fallback
Vertex AI (configured but API error)
  ↓ fallback
OpenAI (configured and working)
  ↓ success
Returns LLM response
```

**No Provider Available:**
```
KIRO Native (unavailable in CLI mode)
  ↓ fallback
Vertex AI (not configured)
  ↓ fallback
OpenAI (not configured)
  ↓ fallback
Returns None → [INFERRED] markers applied
```

## Troubleshooting

### "No LLM provider available"

**Symptoms:**
- Warning: "No LLM provider available"
- Files generated with `[INFERRED]` markers

**Solutions:**
1. **In KIRO IDE:** Ensure running via MCP (not standalone CLI)
2. **In CLI:** Check environment variables or config file exists
3. **Install dependencies:** `pip install hiveforge-steering-mcp[vertex]` or `[openai]`
4. **Verify config:** Check `~/.hiveforge/llm_config.json` is valid JSON

### "Vertex AI call failed"

**Symptoms:**
- Error: "Vertex AI call failed: ..."
- Fallback to OpenAI or `[INFERRED]` markers

**Solutions:**
1. **Check project ID:** `echo $GOOGLE_CLOUD_PROJECT`
2. **Verify credentials:** `echo $GOOGLE_APPLICATION_CREDENTIALS`
3. **Test credentials:** `gcloud auth application-default print-access-token`
4. **Check permissions:** Ensure service account has `Vertex AI User` role
5. **Enable API:** Ensure Vertex AI API is enabled in GCP project

### "OpenAI call failed"

**Symptoms:**
- Error: "OpenAI call failed: ..."
- Fallback to `[INFERRED]` markers

**Solutions:**
1. **Check API key:** `echo $OPENAI_API_KEY` (should start with `sk-`)
2. **Verify credits:** Check OpenAI dashboard for remaining credits
3. **Test API key:** `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`
4. **Check rate limits:** Wait a few minutes if hitting rate limits
5. **Update key:** Generate new API key if expired

### "KIRO native call failed"

**Symptoms:**
- Error: "KIRO native call failed: ..."
- Fallback to Vertex AI or OpenAI

**Solutions:**
1. **Verify MCP mode:** Ensure running inside KIRO IDE (not standalone)
2. **Check ctx parameter:** Verify `ctx` is being passed correctly
3. **Update KIRO IDE:** Ensure using latest version with LLM support
4. **Check IDE settings:** Verify LLM access is enabled in KIRO IDE

### Configuration File Not Loading

**Symptoms:**
- Config file exists but not being used
- Environment variables override config file

**Solutions:**
1. **Check location:** Verify file is at `~/.hiveforge/llm_config.json`
2. **Validate JSON:** Use `python -m json.tool ~/.hiveforge/llm_config.json`
3. **Check permissions:** Ensure file is readable (`chmod 600 ~/.hiveforge/llm_config.json`)
4. **Clear env vars:** Unset environment variables to test config file

## Security Best Practices

### API Keys

- **Never commit** API keys to version control
- **Use environment variables** for CI/CD pipelines
- **Rotate keys regularly** (every 90 days recommended)
- **Set usage limits** in provider dashboards
- **Use separate keys** for development and production

### Configuration File

- **Restrict permissions:** `chmod 600 ~/.hiveforge/llm_config.json`
- **Exclude from backups** if contains sensitive data
- **Use environment variables** for shared/CI environments
- **Document key rotation** procedures for your team

### Vertex AI

- **Use service accounts** with minimal permissions
- **Enable audit logging** for API calls
- **Set project quotas** to prevent unexpected costs
- **Use workload identity** in Kubernetes environments
- **Rotate credentials** every 90 days

### OpenAI

- **Set spending limits** in OpenAI dashboard
- **Monitor usage** regularly for anomalies
- **Use organization keys** for team projects
- **Enable rate limiting** to prevent abuse
- **Review API logs** for suspicious activity

## Performance Considerations

### Response Times

| Provider | Typical Latency | Notes |
|----------|----------------|-------|
| KIRO Native | < 1 second | No network overhead |
| Vertex AI | 1-5 seconds | Depends on region and model |
| OpenAI | 2-8 seconds | Depends on model and load |

### Cost Optimization

**Vertex AI:**
- Use `gemini-pro` for cost-effective generation
- Set `max_tokens` to minimum needed (default: 2000)
- Use lower `temperature` for consistent results (default: 0.1)

**OpenAI:**
- Use `gpt-3.5-turbo` for lower costs (vs `gpt-4`)
- Set `max_tokens` to minimum needed (default: 2000)
- Cache responses when possible (not implemented yet)

### Token Usage

**Typical steering file generation:**
- Input: 1000-2000 tokens (template + context)
- Output: 500-1500 tokens (populated content)
- Total: ~1500-3500 tokens per file

**Full project initialization (8 files):**
- Total tokens: ~12,000-28,000
- Vertex AI cost: ~$0.01-0.03
- OpenAI (GPT-4) cost: ~$0.36-0.84
- OpenAI (GPT-3.5) cost: ~$0.02-0.04

## Advanced Configuration

### Custom Models

**Vertex AI:**
```json
{
  "provider_type": "vertex_ai",
  "project_id": "my-project",
  "model": "gemini-1.5-pro"
}
```

**OpenAI:**
```json
{
  "provider_type": "openai",
  "api_key": "sk-...",
  "model": "gpt-4-turbo-preview"
}
```

### Temperature Tuning

Lower temperature (0.0-0.3) for consistent, deterministic output:
```json
{
  "temperature": 0.1
}
```

Higher temperature (0.7-1.0) for creative, varied output:
```json
{
  "temperature": 0.8
}
```

### Token Limits

Increase for longer files:
```json
{
  "max_tokens": 4000
}
```

Decrease for cost savings:
```json
{
  "max_tokens": 1000
}
```

## Related Documentation

- [README.md](../../README.md) - Quick start guide
- [LLM_CONFIGURATION.md](./LLM_CONFIGURATION.md) - Technical implementation details
- [P0-1_IMPLEMENTATION_SUMMARY.md](./P0-1_IMPLEMENTATION_SUMMARY.md) - LLMProvider implementation

## Support

For issues or questions:
- GitHub Issues: https://github.com/asoshnin/HiveForge/issues
- Email: 89580632+asoshnin@users.noreply.github.com
