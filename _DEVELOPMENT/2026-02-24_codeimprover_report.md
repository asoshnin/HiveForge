# HiveForge Steering Quality Improvement Report
**Date:** 2026-02-24
**Analyst:** Senior Software Architect (AI)
**RED TEAM Review:** 2026-02-24 — Conditional sign-off. P0 fixes approved. Section 2 fully revised per BLOCK-1/2/3. LLM provider config added per user request.
**Scope:** `hiveforge-power/hiveforge/steering/` (active development path)
**Ground Truth:** `.kiro/steering/` files are 100% unreplaced templates — identical to source templates

---

## Section 1: Root Cause Analysis

### Verified Findings

The `.kiro/steering/` files (project-vision.md, tech-stack.md, architecture.md) are **byte-for-byte identical to the templates** in `hiveforge-power/hiveforge/templates/steering/`. Zero placeholders were replaced. This confirms a **total pipeline failure**, not a partial one.

### Root Cause Table

| # | Component | Function | Failure Mechanism | Severity |
|---|-----------|----------|-------------------|----------|
| 1 | `template_populator.py` | `_replace_placeholders()` | Regex replacement only works if `knowledge` dict keys exactly match placeholder names. `_combine_knowledge()` produces keys like `"Backend"`, `"Pattern"` — none match template placeholders like `{Python 3.11|Node.js 18|...}`. Result: 0% replacement rate. | P0 |
| 2 | `agents/steering_assistant.py` | `generate_file()` | **Method does not exist.** `AutonomousWorkflow._generate_single_file()` calls `assistant.generate_file(filename=..., context=...)`, but `SteeringAssistant` has no such method. `AttributeError` is silently caught, sets `self.generated_files[filename] = ""`. All files become empty strings. | P0 |
| 3 | `agents/steering_assistant.py` | `_gather_from_knowledge_base()` | In autonomous mode, returns dict with keys like `{"project-vision": {"Elevator Pitch": "<500 chars>"}}`. These keys do NOT match `TemplatePopulator._replace_placeholders()` expectations. No synthesis occurs. | P0 |
| 4 | `gap_analysis.py` | `_classify_section()` | Keyword matching only. With empty `.kiro/onboarding/`, every section classifies as `"missing"`. In autonomous mode (`interactive=False`) questions are never asked. | P1 |
| 5 | `analyzers/code_analyzer.py` | `analyze()` | `_load_cache()` always returns `None`. `to_summary()` produces a single-line string with no module structure, MCP tool names, or dependency versions. | P1 |
| 6 | `workflows/autonomous_workflow.py` | `_step_generate_files_autonomously()` | Calls `SteeringAssistant.generate_file()` which doesn't exist. Silent `except` sets all files to `""`. `_step_write_files()` skips empty files. **No files written.** Workflow reports "success". | P0 |

### Additional Root Causes Discovered

| # | Component | Function | Failure Mechanism | Severity |
|---|-----------|----------|-------------------|----------|
| 7 | `workflows/init_workflow.py` | `_step_check_existing_files()` | Calls `input()` in MCP async context — blocks indefinitely or raises `EOFError`. Also: `SteeringConfig.interactive` defaults to `True` and is never set to `False` by `SharedInitWorkflow`, so the guard added by P0-4 fix won't trigger without also fixing the caller. | P0 |
| 8 | `workflows/update_workflow.py` | `_step_build_knowledge_base()` | `code_analysis=None` hardcoded — update workflow never re-analyzes codebase. Drift detection impossible. | P1 |
| 9 | `knowledge_base.py` | `get_relevant_content()` | Keyword matching extracts line fragments. Empty onboarding folder → returns `""`. `[:500]` truncation further degrades quality. | P1 |
| 10 | `templates/steering/` | All 8 templates | Templates assume web app: `{React 18|Vue 3|...}`, `{PostgreSQL 15|...}`. HiveForge is a Python CLI/MCP tool. Nonsensical output even if placeholders were replaced. | P1 |
| 11 | `src/` vs `hiveforge-power/` | — | `src/` has `content_tagger.py`, `confidence.py`, `source_resolver.py` missing from `hiveforge-power/`. Both copies lack `generate_file()`. Both paths broken. | P1 |

---

## Section 2: LLM Integration Design

> **RED TEAM revision (BLOCK-1/2/3):** Original design hardcoded `openai.OpenAI()` as sole provider. This was wrong: (1) `openai` is not in `pyproject.toml`; (2) synchronous client blocks the async event loop; (3) ignores KIRO's native `ctx.sample()` which is the correct primary path for MCP Power users. This section has been fully rewritten.

### 2.0 LLM Provider Architecture

HiveForge runs in two contexts with different LLM access patterns:

| Context | LLM Access | Cost Model | Config |
|---------|-----------|------------|--------|
| MCP Power (inside KIRO IDE) | `ctx.sample()` via FastMCP | KIRO credits (Auto = 1 credit/call) | No extra config needed |
| CLI (`hiveforge steering init`) | External provider via credentials file | User's own API account | `~/.hiveforge/llm_config.json` |

**Default:** KIRO native (`ctx.sample()`) when `ctx` is available; external provider when running as CLI. No LLM → `[INFERRED]` markers.

### 2.1 LLM Provider Configuration

**New file:** `hiveforge-power/hiveforge/steering/llm_provider.py`

This module abstracts all LLM calls behind a single async interface. Callers never need to know which provider is active.

**Supported providers (priority order):**
1. KIRO native via `ctx.sample()` — used when `ctx` is available (MCP mode)
2. Google Vertex AI (Gemini 2.0 Flash / Pro) — via `~/.hiveforge/llm_config.json` or env vars
3. OpenAI — via `~/.hiveforge/llm_config.json` or `OPENAI_API_KEY` env var
4. No LLM — graceful fallback to `[INFERRED]` markers

**Configuration file** (`~/.hiveforge/llm_config.json`):

```json
{
    "provider": "vertex",
    "vertex": {
        "project_id": "YOUR_GCP_PROJECT_ID",
        "location": "us-central1",
        "model": "gemini-2.0-flash",
        "credentials_file": "/path/to/your/service-account.json"
    },
    "openai": {
        "api_key": "sk-YOUR_KEY_HERE",
        "model": "gpt-4o-mini"
    }
}
```

**Environment variable overrides** (take precedence over file):

```
HIVEFORGE_LLM_PROVIDER=vertex|openai|kiro
HIVEFORGE_VERTEX_PROJECT=my-gcp-project
HIVEFORGE_VERTEX_LOCATION=us-central1
HIVEFORGE_VERTEX_MODEL=gemini-2.0-flash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

**`pyproject.toml` additions required:**

```toml
[project.optional-dependencies]
vertex = ["google-cloud-aiplatform>=1.38.0"]
openai = ["openai>=1.0.0"]
all-llm = ["google-cloud-aiplatform>=1.38.0", "openai>=1.0.0"]
```

**`llm_provider.py` implementation:**

```python
"""
LLM provider abstraction for HiveForge Steering.

Priority order:
  1. KIRO native (ctx.sample()) — MCP mode, billed as KIRO credits
  2. Google Vertex AI (Gemini) — via llm_config.json or env vars
  3. OpenAI — via llm_config.json or OPENAI_API_KEY
  4. None — caller uses [INFERRED] markers
"""
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)
DEFAULT_CONFIG_PATH = Path.home() / ".hiveforge" / "llm_config.json"


def load_llm_config(config_path: Optional[Path] = None) -> dict:
    """Load provider config from file, then apply env var overrides."""
    path = config_path or DEFAULT_CONFIG_PATH
    config: dict = {}
    if path.exists():
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not read LLM config from {path}: {e}")
    # Env overrides
    if os.environ.get("HIVEFORGE_LLM_PROVIDER"):
        config["provider"] = os.environ["HIVEFORGE_LLM_PROVIDER"]
    if os.environ.get("OPENAI_API_KEY"):
        config.setdefault("openai", {})["api_key"] = os.environ["OPENAI_API_KEY"]
    if os.environ.get("OPENAI_MODEL"):
        config.setdefault("openai", {})["model"] = os.environ["OPENAI_MODEL"]
    if os.environ.get("HIVEFORGE_VERTEX_PROJECT"):
        config.setdefault("vertex", {})["project_id"] = os.environ["HIVEFORGE_VERTEX_PROJECT"]
    if os.environ.get("HIVEFORGE_VERTEX_LOCATION"):
        config.setdefault("vertex", {})["location"] = os.environ["HIVEFORGE_VERTEX_LOCATION"]
    if os.environ.get("HIVEFORGE_VERTEX_MODEL"):
        config.setdefault("vertex", {})["model"] = os.environ["HIVEFORGE_VERTEX_MODEL"]
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        config.setdefault("vertex", {})["credentials_file"] = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    return config


class LLMProvider:
    """
    Unified async LLM interface for HiveForge.

    MCP mode:   LLMProvider(ctx=ctx)   → routes through ctx.sample()
    CLI mode:   LLMProvider()          → routes through configured external provider
    No config:  returns None           → caller uses [INFERRED] fallback
    """

    def __init__(self, ctx=None, config_path: Optional[Path] = None):
        self.ctx = ctx
        self.config = load_llm_config(config_path)

    def is_available(self) -> bool:
        if self.ctx is not None:
            return True
        p = self._resolve_provider()
        if p == "vertex":
            return bool(self.config.get("vertex", {}).get("project_id"))
        if p == "openai":
            return bool(self.config.get("openai", {}).get("api_key"))
        return False

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> Optional[str]:
        """
        Send a completion request. Returns response text or None.
        Priority: ctx.sample() > vertex > openai > None.
        """
        if self.ctx is not None:
            return await self._complete_kiro(system_prompt, user_prompt, max_tokens)
        provider = self._resolve_provider()
        if provider == "vertex":
            return await self._complete_vertex(system_prompt, user_prompt, max_tokens, temperature, json_mode)
        if provider == "openai":
            return await self._complete_openai(system_prompt, user_prompt, max_tokens, temperature, json_mode)
        return None

    def _resolve_provider(self) -> Optional[str]:
        explicit = self.config.get("provider")
        if explicit in ("vertex", "openai"):
            return explicit
        if self.config.get("vertex", {}).get("project_id"):
            return "vertex"
        if self.config.get("openai", {}).get("api_key"):
            return "openai"
        return None

    async def _complete_kiro(self, system_prompt: str, user_prompt: str, max_tokens: int) -> Optional[str]:
        try:
            response = await self.ctx.sample(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                max_tokens=max_tokens,
            )
            return response.text
        except Exception as e:
            logger.warning(f"ctx.sample() failed: {e}")
            return None

    async def _complete_vertex(
        self, system_prompt: str, user_prompt: str,
        max_tokens: int, temperature: float, json_mode: bool
    ) -> Optional[str]:
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel, GenerationConfig
            vcfg = self.config.get("vertex", {})
            if vcfg.get("credentials_file"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = vcfg["credentials_file"]
            vertexai.init(project=vcfg.get("project_id"), location=vcfg.get("location", "us-central1"))
            model = GenerativeModel(
                vcfg.get("model", "gemini-2.0-flash"),
                system_instruction=system_prompt,
            )
            gen_config = GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                response_mime_type="application/json" if json_mode else "text/plain",
            )
            # Vertex SDK is sync — run in thread to avoid blocking event loop
            response = await asyncio.to_thread(model.generate_content, user_prompt, generation_config=gen_config)
            return response.text
        except ImportError:
            logger.warning("google-cloud-aiplatform not installed. pip install hiveforge-steering-mcp[vertex]")
            return None
        except Exception as e:
            logger.warning(f"Vertex AI call failed: {e}")
            return None

    async def _complete_openai(
        self, system_prompt: str, user_prompt: str,
        max_tokens: int, temperature: float, json_mode: bool
    ) -> Optional[str]:
        try:
            from openai import AsyncOpenAI
            ocfg = self.config.get("openai", {})
            client = AsyncOpenAI(api_key=ocfg.get("api_key"))
            kwargs: dict[str, Any] = {
                "model": ocfg.get("model", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except ImportError:
            logger.warning("openai not installed. pip install hiveforge-steering-mcp[openai]")
            return None
        except Exception as e:
            logger.warning(f"OpenAI call failed: {e}")
            return None
```

**`ctx` threading requirement:** `ctx` must be passed from `init_steering.py` → `SharedInitWorkflow.__init__` → `AutonomousWorkflow.__init__` → `SteeringAssistant.__init__`. Each gains `ctx=None`. `generate_file()`, `_generate_single_file()`, and `_step_generate_files_autonomously()` all become `async def`. Estimated effort: 2–3 hours on top of `generate_file()` implementation.

---

### Design Principles (revised)
- Python handles structured extraction (fast, free, deterministic)
- LLM handles synthesis and content generation (where quality matters)
- **Primary LLM path (MCP mode):** `ctx.sample()` — KIRO native, billed as KIRO credits, no extra config
- **Secondary LLM path (CLI or user preference):** External provider via `~/.hiveforge/llm_config.json` — supports Google Vertex AI (Gemini 2.0 Flash/Pro) and OpenAI
- No LLM configured → graceful degradation to `[INFERRED]` markers (always useful, never crashes)
- All LLM calls are `async`, wrapped in `try/except`, with fallback
- `openai` and `google-cloud-aiplatform` are **optional dependencies** — not installed by default

---

### Injection Point 1: `SteeringAssistant.generate_file()` — THE MISSING METHOD (P0)

**File:** `hiveforge-power/hiveforge/steering/agents/steering_assistant.py`
**Trigger:** Called from `AutonomousWorkflow._generate_single_file()` when `interactive=False`
**Token estimate:** ~2500–7400 tokens per file (grows with context accumulation — strip frontmatter, cap context to last 3 files)
**Model:** Determined by `LLMProvider` — KIRO Auto by default; Gemini 2.0 Flash or gpt-4o-mini for external

```python
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_GENERATE_FILE = (
    "You are a technical documentation expert generating a KIRO steering file.\n"
    "Steering files are Markdown documents used by AI agents to understand a project.\n"
    "Replace ALL {placeholder} text with real, specific content based on the project context.\n"
    "Output ONLY the final Markdown. No explanations, no preamble.\n"
    "If a section is not applicable (e.g., Frontend for a CLI tool), write a brief N/A note.\n"
    "Never leave {placeholder} text in your output."
)

async def generate_file(self, filename: str, context: str) -> str:
    """
    Generate a single steering file using LLM synthesis.

    Uses LLMProvider which routes to ctx.sample() (KIRO native) or
    an external provider (Vertex/OpenAI) based on configuration.
    Falls back to [INFERRED] markers if no LLM is available.

    Args:
        filename: e.g. "tech-stack.md"
        context: previously generated files (capped to last 3) + gap analysis questions

    Returns:
        Populated markdown string (never empty)
    """
    template_name = filename.replace(".md", "")

    # Load raw template, strip frontmatter before sending to LLM
    try:
        from ..template_populator import TemplatePopulator
        populator = TemplatePopulator()
        raw_template = populator._get_raw_template(template_name)
        template_content = _strip_frontmatter(raw_template)
    except Exception as e:
        logger.error(f"Cannot load template for {filename}: {e}")
        return f"# {template_name}\n\n[ERROR: Template not found]\n"

    if not self.llm_provider.is_available():
        logger.info(f"No LLM provider — using [INFERRED] markers for {filename}")
        return self._apply_inferred_markers(template_content)

    kb_content = self.knowledge_base.get_relevant_content(template_name, max_tokens=3000)
    context_capped = _cap_context(context, max_files=3)

    user_prompt = (
        f"PROJECT CONTEXT (code analysis + documents):\n{kb_content}\n\n"
        f"PREVIOUSLY GENERATED FILES (for consistency):\n"
        f"{context_capped if context_capped else 'None yet.'}\n\n"
        f"TEMPLATE TO FILL (replace ALL placeholders):\n{template_content}\n\n"
        f"Generate the completed steering file for: {filename}"
    )

    result = await self.llm_provider.complete(
        system_prompt=SYSTEM_PROMPT_GENERATE_FILE,
        user_prompt=user_prompt,
        max_tokens=2000,
        temperature=0.3,
    )

    if result:
        logger.info(f"LLM generated {filename} ({len(result)} chars)")
        return result

    logger.warning(f"LLM returned None for {filename}. Using [INFERRED] fallback.")
    return self._apply_inferred_markers(template_content)

def _apply_inferred_markers(self, template_content: str) -> str:
    """Replace {placeholder} patterns with [INFERRED: placeholder] markers."""
    return re.sub(r'\{([^}]+)\}', r'[INFERRED: \1]', template_content)


def _strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter (--- ... ---) before sending template to LLM."""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].lstrip("\n")
    return content


def _cap_context(context: str, max_files: int = 3) -> str:
    """Cap context to last N generated files to prevent token blowup on later files."""
    if not context:
        return ""
    parts = context.split("\n--- ")
    if len(parts) <= max_files + 1:
        return context
    return parts[0] + "\n--- " + "\n--- ".join(parts[-max_files:])
```

**`SteeringAssistant.__init__` change:**
```python
def __init__(self, ..., ctx=None):
    ...
    from ..llm_provider import LLMProvider
    self.llm_provider = LLMProvider(ctx=ctx)
```

**Also add to `TemplatePopulator`:**
```python
def _get_raw_template(self, template_name: str) -> str:
    """Return raw template content (including frontmatter — caller strips if needed)."""
    if template_name not in self.templates:
        raise ValueError(f"Template '{template_name}' not found. "
                         f"Available: {list(self.templates.keys())}")
    template = self.templates[template_name]
    template_file = self._template_dir / template.file_name
    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_file}")
    return template_file.read_text(encoding="utf-8")
```

---

### Injection Point 2: `CodeAnalyzer` — Project Type + Public API Extraction (P1)

**File:** `hiveforge-power/hiveforge/steering/analyzers/code_analyzer.py`
**Trigger:** After local analysis completes, if LLM provider is available
**Note:** `_heuristic_classify()` (Section 6.1) always runs first. LLM enrichment only adds `one_line_description` and `key_capabilities` that heuristics cannot produce.

```python
SYSTEM_PROMPT_CLASSIFY_PROJECT = """You are a software architect. Given a code analysis summary,
output a JSON object with these exact keys:
{
  "project_type": "cli_tool" | "web_app" | "library" | "mcp_server" | "cli_and_mcp",
  "has_frontend": boolean,
  "has_database": boolean,
  "has_rest_api": boolean,
  "primary_language": string,
  "one_line_description": string,
  "key_capabilities": [string, string, string]
}
Base your answer only on the provided analysis. No explanations."""

async def classify_project_with_llm(
    self, analysis_summary: str, llm_provider: "LLMProvider"
) -> dict:
    """Enrich heuristic classification with LLM-generated description and capabilities."""
    base = self._heuristic_classify()  # always run heuristics first
    if not llm_provider.is_available():
        return base
    try:
        import json as _json
        result_text = await llm_provider.complete(
            system_prompt=SYSTEM_PROMPT_CLASSIFY_PROJECT,
            user_prompt=analysis_summary,
            max_tokens=300,
            temperature=0.1,
            json_mode=True,
        )
        if result_text:
            llm_result = _json.loads(result_text)
            base["one_line_description"] = llm_result.get("one_line_description", "")
            base["key_capabilities"] = llm_result.get("key_capabilities", [])
    except Exception as e:
        logger.warning(f"Project classification LLM enrichment failed: {e}")
    return base
```

---

### Injection Point 3: `GapAnalysisEngine` — Semantic Section Classification (P2)

**File:** `hiveforge-power/hiveforge/steering/gap_analysis.py`
**Trigger:** When `_classify_section()` returns `"missing"` AND LLM provider is available
**Fallback:** Current keyword-matching behavior

```python
SYSTEM_PROMPT_CLASSIFY_SECTION = """Given project context and a steering file section name,
determine if the context contains enough information to fill that section.
Reply with JSON: {"classification": "complete"|"partial"|"missing", "reason": "one sentence"}"""

async def _classify_section_with_llm(
    self,
    template_name: str,
    section_name: str,
    context: str,
    llm_provider: "LLMProvider",
) -> str:
    """LLM-assisted section classification. Returns 'complete', 'ambiguous', or 'missing'."""
    if not llm_provider.is_available() or len(context) < 50:
        return "missing"
    try:
        import json as _json
        result_text = await llm_provider.complete(
            system_prompt=SYSTEM_PROMPT_CLASSIFY_SECTION,
            user_prompt=f"Section: {template_name}/{section_name}\nContext:\n{context[:800]}",
            max_tokens=100,
            temperature=0.1,
            json_mode=True,
        )
        if result_text:
            result = _json.loads(result_text)
            mapping = {"complete": "complete", "partial": "ambiguous", "missing": "missing"}
            return mapping.get(result.get("classification", "missing"), "missing")
    except Exception:
        pass
    return "missing"
```

---

## Section 3: User Review Step Design

### Problem
Both `init_workflow.py` and `autonomous_workflow.py` write files directly to `.kiro/steering/` with no preview. In MCP mode, the user sees nothing until files are already written.

> **RED TEAM note (ADV-2):** The original design auto-approved all files in MCP mode, defeating the purpose. The correct MCP behavior is: return the draft summary in the MCP response, do NOT write files yet, require a second call to apply. This design implements that correctly.

### Data Structure: `DraftState`

```python
# Add to models.py
@dataclass
class DraftFile:
    """A single steering file in draft state."""
    filename: str
    content: str
    confidence: float
    placeholder_count: int
    is_approved: bool = False
    user_edits: Optional[str] = None

@dataclass
class DraftState:
    """Complete draft state for user review before writing to disk."""
    files: Dict[str, DraftFile] = field(default_factory=dict)
    overall_confidence: float = 0.0
    warnings: list = field(default_factory=list)

    def all_approved(self) -> bool:
        return all(f.is_approved for f in self.files.values())

    def get_summary(self) -> str:
        lines = [f"Draft ready: {len(self.files)} files"]
        for fname, df in self.files.items():
            status = "✓" if df.placeholder_count == 0 else f"⚠ {df.placeholder_count} placeholders"
            lines.append(f"  {fname}: confidence={df.confidence:.2f} {status}")
        return "\n".join(lines)
```

### Where to Insert in `init_workflow.py`

Insert between Step 8 (`_step_populate_templates`) and Step 9 (`_step_write_files`):

```python
# Step 8.5: User review (new)
if not self._step_review_draft():
    logger.info("User rejected draft — no files written")
    return False
# Step 9: Write files (existing)
self._step_write_files()
```

```python
def _step_review_draft(self) -> bool:
    """
    Step 8.5: Present draft to user for review before writing.

    In CLI mode: prints content, prompts for approval.
    In MCP mode: stores draft in WorkflowResult.metadata["draft_summary"],
                 returns False (does NOT write files). User must call
                 update_steering(apply_draft=True) to apply.
    """
    import re
    draft = DraftState()
    for filename, content in getattr(self.state, 'populated_files', {}).items():
        placeholder_count = len(re.findall(r'\{[^}]+\}', content))
        confidence = max(0.0, 1.0 - (placeholder_count * 0.1))
        draft.files[filename] = DraftFile(
            filename=filename,
            content=content,
            confidence=confidence,
            placeholder_count=placeholder_count,
        )
    self.state.draft = draft  # always store for MCP access

    # MCP mode: return draft via WorkflowResult, do NOT write files
    if not self.config.interactive:
        logger.info(f"MCP mode: draft stored ({len(draft.files)} files), awaiting approval")
        return False  # caller reads state.draft and returns it in metadata

    # CLI mode: show and prompt
    print("\n" + "="*70)
    print("DRAFT REVIEW — Files to be written:")
    print("="*70)
    for filename, df in draft.files.items():
        print(f"\n{'─'*50}")
        print(f"FILE: {filename}  (confidence: {df.confidence:.2f}, placeholders: {df.placeholder_count})")
        print('─'*50)
        print(df.content[:800] + ("..." if len(df.content) > 800 else ""))
    print("\n" + "="*70)
    choice = input("Approve all and write? (y/n): ").strip().lower()
    if choice == 'y':
        for df in draft.files.values():
            df.is_approved = True
        return True
    return False
```

### MCP Mode: How Draft is Returned to KIRO IDE

In `SharedInitWorkflow.execute()`, after `v02_workflow.execute()` completes (whether True or False), read `v02_workflow.state.draft` and include it in `WorkflowResult.metadata`:

```python
draft_summary = None
if hasattr(v02_workflow.state, 'draft') and v02_workflow.state.draft:
    draft_summary = {
        fname: {
            "confidence": df.confidence,
            "placeholder_count": df.placeholder_count,
            "preview": df.content[:300],
        }
        for fname, df in v02_workflow.state.draft.files.items()
    }
result = WorkflowResult(
    status="draft_ready" if draft_summary else "success",
    metadata={"draft_summary": draft_summary, ...}
)
```

The KIRO IDE user sees the draft summary and calls `update_steering(apply_draft=True)` to write files.

---

## Section 4: Update Workflow — Drift Detection

### Current State
`UpdateWorkflow._step_build_knowledge_base()` hardcodes `code_analysis=None`. No drift detection possible.

### `DriftItem` Data Structure

```python
# Add to models.py
@dataclass
class DriftItem:
    category: Literal[
        "dependency_version", "architecture_pattern", "language_version",
        "missing_component", "convention_mismatch", "test_coverage", "new_dependency",
    ]
    steering_file: str
    section: str
    current_steering_content: str
    detected_code_reality: str
    confidence: float
    suggested_update: str

@dataclass
class DriftReport:
    items: list[DriftItem] = field(default_factory=list)
    project_root: str = ""
    analyzed_at: str = ""

    def has_drift(self) -> bool:
        return len(self.items) > 0

    def by_severity(self) -> list[DriftItem]:
        return sorted(self.items, key=lambda x: x.confidence, reverse=True)
```

### Comparisons to Make

| Comparison | Source of Truth | Steering File | Section |
|------------|----------------|---------------|---------|
| Python version | `pyproject.toml` `requires-python` | `tech-stack.md` | Backend |
| Runtime deps only (not dev) | `pyproject.toml` `[dependencies]` | `tech-stack.md` | Key Dependencies |
| Architecture pattern | `ArchitectureInfo.pattern` | `architecture.md` | System Diagram |
| Top-level packages | `src/*/` directory names | `architecture.md` | Component Responsibilities |
| Naming convention | `ConventionsInfo.naming_style` | `conventions.md` | Naming Conventions |
| Test framework | `pyproject.toml` dev deps | `qa-standards.md` | Test Types |
| New MCP tools | `@mcp.tool()` decorated functions | `tech-stack.md` | Key Dependencies |

### `DriftDetector` — New Class

> **RED TEAM note (SIG-1):** Only flag runtime dependencies that are architecturally significant — not every dep. The `_check_tech_stack` method below filters to runtime deps only and skips dev deps entirely. Further filtering by significance category is recommended for projects with 20+ deps.

**File:** `hiveforge-power/hiveforge/steering/drift_detector.py` (new file)

```python
"""
Drift detector for the update workflow.
Compares existing steering files against fresh code analysis.
"""
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from .models import DriftItem, DriftReport, CodeAnalysisResult

logger = logging.getLogger(__name__)

# Only flag these runtime dep categories as architecturally significant
SIGNIFICANT_DEP_KEYWORDS = {
    "fastmcp", "fastapi", "flask", "django", "express", "gin",
    "sqlalchemy", "prisma", "alembic", "mongoose",
    "redis", "celery", "kafka",
    "pydantic", "typer", "click",
    "pytest", "jest", "cypress", "playwright",
}


class DriftDetector:
    """Detects drift between steering files and current codebase state."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def detect(self, existing_files: Dict[str, str], code_analysis: CodeAnalysisResult) -> DriftReport:
        report = DriftReport(
            project_root=str(self.project_root),
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )
        if "tech-stack.md" in existing_files:
            report.items.extend(self._check_tech_stack(existing_files["tech-stack.md"], code_analysis))
        if "architecture.md" in existing_files:
            report.items.extend(self._check_architecture(existing_files["architecture.md"], code_analysis))
        if "conventions.md" in existing_files:
            report.items.extend(self._check_conventions(existing_files["conventions.md"], code_analysis))
        return report

    def _check_tech_stack(self, content: str, analysis: CodeAnalysisResult) -> list[DriftItem]:
        items = []
        # Python version check
        for lang in (analysis.languages or []):
            if lang.name.lower() == "python" and lang.version:
                match = re.search(r'Python\s+([\d.]+)', content)
                if match and match.group(1) != lang.version:
                    items.append(DriftItem(
                        category="language_version",
                        steering_file="tech-stack.md",
                        section="Backend",
                        current_steering_content=f"Python {match.group(1)}",
                        detected_code_reality=f"Python {lang.version}",
                        confidence=0.95,
                        suggested_update=f"- **Language:** Python {lang.version}",
                    ))
        # Significant runtime deps only (not dev, not every dep)
        if (self.project_root / "pyproject.toml").exists() and analysis.tech_stack.dependencies:
            for dep in analysis.tech_stack.dependencies:
                if dep.dependency_type != "runtime":
                    continue
                if dep.name.lower() not in SIGNIFICANT_DEP_KEYWORDS:
                    continue
                if dep.name not in content:
                    items.append(DriftItem(
                        category="new_dependency",
                        steering_file="tech-stack.md",
                        section="Key Dependencies",
                        current_steering_content="(not listed)",
                        detected_code_reality=f"{dep.name} {dep.version or ''}",
                        confidence=0.85,
                        suggested_update=f"| {dep.name} | {dep.version or 'latest'} | runtime | |",
                    ))
        return items

    def _check_architecture(self, content: str, analysis: CodeAnalysisResult) -> list[DriftItem]:
        items = []
        if analysis.architecture.pattern and analysis.architecture.pattern != "custom":
            if analysis.architecture.pattern.lower() not in content.lower():
                items.append(DriftItem(
                    category="architecture_pattern",
                    steering_file="architecture.md",
                    section="System Diagram",
                    current_steering_content="(pattern not mentioned)",
                    detected_code_reality=f"Detected pattern: {analysis.architecture.pattern}",
                    confidence=0.75,
                    suggested_update=f"Architecture follows {analysis.architecture.pattern} pattern.",
                ))
        return items

    def _check_conventions(self, content: str, analysis: CodeAnalysisResult) -> list[DriftItem]:
        items = []
        for style_key, style_val in (analysis.conventions.naming_style or {}).items():
            if style_val and style_val not in content:
                items.append(DriftItem(
                    category="convention_mismatch",
                    steering_file="conventions.md",
                    section="Naming Conventions",
                    current_steering_content="(not specified)",
                    detected_code_reality=f"{style_key}: {style_val}",
                    confidence=0.70,
                    suggested_update=f"- `{style_val}` for {style_key}",
                ))
        return items
```

### Relationship to KIRO Orchestrator's `DISCREPANCY_REPORT.md`

| | `DRIFT_REPORT.md` (HiveForge) | `DISCREPANCY_REPORT.md` (KIRO Orchestrator) |
|---|---|---|
| **Who generates** | HiveForge `update` workflow | KIRO Orchestrator + specialized agents |
| **What it compares** | Steering files vs. code analysis (structural) | Steering files vs. actual code behavior (semantic) |
| **Speed** | Seconds (local analysis) | Minutes (LLM agents) |
| **When to use** | Before running Orchestrator, to update stale steering files | After steering files are current, to find code-doc gaps |

**Recommended workflow:** `hiveforge steering update` → review `DRIFT_REPORT.md` → apply → run KIRO Orchestrator.

---

## Section 5: Code Analyzer Improvements

### Current Output (Verified)
`CodeAnalysisResult.to_summary()` produces at most:
```
Languages: Python 3.11 (95.0%), Markdown (3.0%)
Tech Stack: (empty if no framework detected)
Architecture: custom
Conventions: functions=snake_case, classes=PascalCase
```

This is insufficient for LLM-based content generation.

### 5.1 Public API Surface — MCP Tool Names + CLI Commands

**New method:** `CodeAnalyzer.extract_public_api()`

```python
# Add to models.py
@dataclass
class MCPToolInfo:
    name: str
    docstring: str  # first line only
    parameters: list[str]

@dataclass
class CLICommandInfo:
    name: str
    help_text: str

@dataclass
class PublicAPIInfo:
    mcp_tools: list[MCPToolInfo] = field(default_factory=list)
    cli_commands: list[CLICommandInfo] = field(default_factory=list)
    public_classes: list[str] = field(default_factory=list)
```

```python
def extract_public_api(self) -> "PublicAPIInfo":
    """Extract MCP tool names, CLI commands, and public classes via AST."""
    import ast
    from ..models import PublicAPIInfo, MCPToolInfo, CLICommandInfo
    api = PublicAPIInfo()
    for py_file in self.project_root.rglob("*.py"):
        if self._should_exclude_path(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec) if hasattr(ast, 'unparse') else ""
                    if "tool" in dec_str.lower():
                        docstring = ast.get_docstring(node) or ""
                        api.mcp_tools.append(MCPToolInfo(
                            name=node.name,
                            docstring=docstring.split("\n")[0][:120],
                            parameters=[a.arg for a in node.args.args if a.arg not in ("self", "ctx")],
                        ))
                    elif "command" in dec_str.lower():
                        docstring = ast.get_docstring(node) or ""
                        api.cli_commands.append(CLICommandInfo(
                            name=node.name,
                            help_text=docstring.split("\n")[0][:120],
                        ))
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                docstring = ast.get_docstring(node) or ""
                if docstring:
                    api.public_classes.append(f"{node.name}: {docstring.split(chr(10))[0][:100]}")
    return api
```

### 5.2 Dependency Inventory with Versions

```python
# In tech_stack_extractor.py
def _parse_pyproject_toml_dependencies(project_root: Path) -> list[Dependency]:
    """Parse pyproject.toml for runtime dependencies with versions."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return []
    try:
        import tomllib
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
    except ImportError:
        return []
    deps = []
    for dep_str in data.get("project", {}).get("dependencies", []):
        name, version = _parse_dep_string(dep_str)
        deps.append(Dependency(name=name, version=version, dependency_type="runtime"))
    return deps

def _parse_dep_string(dep: str) -> tuple[str, str]:
    import re
    match = re.match(r'^([A-Za-z0-9_\-\.]+)(.*)', dep.strip())
    if match:
        return match.group(1), match.group(2).strip() or "latest"
    return dep, "latest"
```

### 5.3 Module Structure

```python
def extract_module_structure(self) -> dict[str, str]:
    """Extract top-level package names and purpose from __init__.py docstrings."""
    import ast
    modules = {}
    for init_file in self.project_root.rglob("__init__.py"):
        if self._should_exclude_path(init_file):
            continue
        rel = init_file.relative_to(self.project_root)
        if len(rel.parts) > 4:
            continue
        try:
            source = init_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
            docstring = ast.get_docstring(tree) or ""
            package_name = str(rel.parent).replace("\\", "/")
            if docstring:
                modules[package_name] = docstring.split("\n")[0][:120]
        except (SyntaxError, OSError):
            continue
    return modules
```

### 5.4 Test Inventory

```python
def extract_test_inventory(self) -> dict:
    """Count test files, test functions, and detect test framework."""
    import ast
    test_files = [
        f for f in list(self.project_root.rglob("test_*.py")) + list(self.project_root.rglob("*_test.py"))
        if not self._should_exclude_path(f)
    ]
    function_count = 0
    for tf in test_files:
        try:
            tree = ast.parse(tf.read_text(encoding="utf-8", errors="ignore"))
            function_count += sum(
                1 for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test_")
            )
        except (SyntaxError, OSError):
            continue
    framework = "pytest"
    pyproject = self.project_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        if "pytest" in content:
            framework = "pytest"
        elif "unittest" in content:
            framework = "unittest"
    return {"test_file_count": len(test_files), "test_function_count": function_count, "framework": framework}
```

### 5.5 Mapping to Steering File Sections

| Extracted Data | Steering File | Section |
|----------------|---------------|---------|
| `mcp_tools` names + docstrings | `tech-stack.md` | Key Dependencies; `architecture.md` Component Responsibilities |
| `cli_commands` names + help | `tech-stack.md` | Key Dependencies; `project-vision.md` Solution Overview |
| `dependencies` with versions | `tech-stack.md` | Key Dependencies |
| `module_structure` | `architecture.md` | Component Responsibilities |
| `test_inventory` | `qa-standards.md` | Coverage Requirements, Test Types |
| `public_classes` | `architecture.md` | Component Responsibilities |

---

## Section 6: Template System Improvements

### 6.1 Project Type Detection (Rule-Based)

> **RED TEAM note (SIG-2):** `_detect_database()` checks for `models.py` at project root only — not subdirectories. This is intentional and must be documented. `_get_primary_language()` must NOT call `self.analyze()` (infinite recursion risk). It takes `languages` as a parameter instead.

> **RED TEAM note (SIG-3):** `_get_primary_language()` has been fixed below to accept `languages` as a parameter rather than calling `self.analyze()`.

```python
def _heuristic_classify(self) -> dict:
    """
    Rule-based project type detection. No LLM required.
    Rules (first match wins):
    1. Has mcp_server/ OR @mcp.tool() decorators → "mcp_server"
    2. Has both CLI + MCP → "cli_and_mcp"
    3. Has CLI commands → "cli_tool"
    4. Has src/components/ OR *.tsx → "web_app"
    5. Default → "library"
    """
    has_mcp = self._detect_mcp()
    has_cli = self._detect_cli()
    has_frontend = self._detect_frontend()
    has_db = self._detect_database()

    if has_mcp and has_cli:
        project_type = "cli_and_mcp"
    elif has_mcp:
        project_type = "mcp_server"
    elif has_cli:
        project_type = "cli_tool"
    elif has_frontend:
        project_type = "web_app"
    else:
        project_type = "library"

    return {
        "project_type": project_type,
        "has_frontend": has_frontend,
        "has_database": has_db,
        "has_rest_api": self._detect_rest_api(),
        "primary_language": self._get_primary_language(self._cached_languages),
        "one_line_description": "",  # requires LLM or README parsing
        "key_capabilities": [],
    }

def _detect_mcp(self) -> bool:
    if any(p.exists() for p in [self.project_root / "mcp_server"]):
        return True
    for py_file in list(self.project_root.rglob("*.py"))[:50]:
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if "@mcp.tool" in content or "FastMCP" in content:
                return True
        except OSError:
            continue
    return False

def _detect_cli(self) -> bool:
    pyproject = self.project_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        if "[project.scripts]" in content or "console_scripts" in content:
            return True
    for py_file in list(self.project_root.rglob("cli.py"))[:10]:
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if "typer" in content or "click" in content or "argparse" in content:
                return True
        except OSError:
            continue
    return False

def _detect_frontend(self) -> bool:
    for indicator in ["src/components", "src/pages", "src/app", "package.json"]:
        if (self.project_root / indicator).exists():
            return True
    return bool(list(self.project_root.rglob("*.tsx"))[:1] or list(self.project_root.rglob("*.jsx"))[:1])

def _detect_database(self) -> bool:
    """
    Checks for database indicators at project root only (not subdirectories).
    models.py in subdirectories (e.g. steering/models.py) does NOT trigger this.
    """
    for indicator in ["migrations", "prisma", "alembic.ini", "models.py"]:
        if (self.project_root / indicator).exists():
            return True
    return False

def _detect_rest_api(self) -> bool:
    for indicator in ["src/api", "routes", "endpoints"]:
        if (self.project_root / indicator).exists():
            return True
    return False

@staticmethod
def _get_primary_language(languages: list) -> str:
    """Return dominant language name. Takes languages list to avoid calling analyze() recursively."""
    if languages:
        return max(languages, key=lambda l: l.percentage).name
    return "Python"
```

### 6.2 Template Variants by Project Type

| File | Web App | CLI/MCP Tool | Change Type |
|------|---------|-------------|-------------|
| `project-vision.md` | Generic placeholders | Same structure | adapt |
| `tech-stack.md` | Frontend/Backend/DB/Cache | Remove Frontend; add MCP Interface + CLI Interface | replace |
| `architecture.md` | HTTP/Gateway/DB/Redis diagram | CLI→Workflow→FileSystem; no HTTP gateway | replace |
| `conventions.md` | Python + JS/TS | Python only | adapt |
| `api-standards.md` | REST API standards | Replace with MCP Tool Standards | replace |
| `db-standards.md` | SQL schema, migrations | Replace with File System Standards OR skip | replace/skip |
| `ui-standards.md` | React/Tailwind/TSX | Skip entirely | skip |
| `qa-standards.md` | Cypress/Playwright E2E | Remove E2E; add MCP tool testing section | adapt |

### 6.3 Graceful N/A Handling

| Scenario | Action |
|----------|--------|
| `ui-standards.md` for CLI tool | Skip — do not write to `.kiro/steering/` |
| `db-standards.md` for tool with no database | Write: `# Database Standards\n\nN/A — This project does not use a relational database.` |
| `api-standards.md` for MCP-only tool | Replace with MCP Tool Standards template |

```python
def _filter_files_for_project_type(self, all_files: list[str], classification: dict) -> list[str]:
    skip_rules = {
        "ui-standards.md": not classification.get("has_frontend", True),
        "db-standards.md": not classification.get("has_database", True),
    }
    return [f for f in all_files if not skip_rules.get(f, False)]
```

### 6.4 Template Duplication: `src/` vs `hiveforge-power/`

Both template directories are currently identical. Recommendations:
1. Create canonical `templates/steering/` at repo root; both packages resolve to it
2. Short-term: CI check using `filecmp.dircmp` to assert parity
3. Port `content_tagger.py`, `confidence.py`, `source_resolver.py` from `src/` to `hiveforge-power/`

---

## Section 7: Implementation Roadmap

### Priority Table

> **RED TEAM note (ADV-3):** P0-1 and P1-6 were the same item in the original report. Merged below. P0-4 effort updated to include the `interactive=False` fix in `SharedInitWorkflow` (ADV-4). P0-1 effort updated to include `ctx` threading (ADV-5).

| Priority | What | File(s) to Change | Effort |
|----------|------|-------------------|--------|
| P0-1 | Add `LLMProvider` + `generate_file()` with `ctx.sample()` primary path + `[INFERRED]` fallback; thread `ctx` through `SharedInitWorkflow` → `AutonomousWorkflow` → `SteeringAssistant` | `llm_provider.py` (new), `steering_assistant.py`, `autonomous_workflow.py`, `shared/adapters.py` | 5h |
| P0-2 | Add `_get_raw_template()` to `TemplatePopulator` | `template_populator.py` | 30m |
| P0-3 | Fix `AutonomousWorkflow` silent failure — use `[INFERRED]` fallback instead of empty string | `autonomous_workflow.py` | 1h |
| P0-4 | Fix `input()` in MCP mode: guard with `if not self.config.interactive` AND set `interactive=False` in `SharedInitWorkflow` | `init_workflow.py`, `shared/adapters.py` | 1h |
| P1-1 | Add `CodeAnalyzer.extract_public_api()` + `PublicAPIInfo` model | `code_analyzer.py`, `models.py` | 3h |
| P1-2 | Add `CodeAnalyzer._heuristic_classify()` + detection methods (with SIG-2/SIG-3 fixes) | `code_analyzer.py` | 2h |
| P1-3 | Add `DraftState` + `_step_review_draft()` with correct MCP behavior (no auto-approve) | `models.py`, `init_workflow.py`, `shared/adapters.py` | 3h |
| P1-4 | Add `DriftDetector` with significant-deps-only filter (SIG-1 fix) + `_step_detect_drift()` in update workflow | `drift_detector.py` (new), `update_workflow.py` | 4h |
| P1-5 | Port `content_tagger.py`, `confidence.py`, `source_resolver.py` from `src/` to `hiveforge-power/` | 3 new files | 30m |
| P2-1 | Template variants by project type + `_filter_files_for_project_type()` | `templates.py`, `autonomous_workflow.py` | 4h |
| P2-2 | LLM project classification enrichment (one_line_description, key_capabilities) | `code_analyzer.py` | 1h |
| P2-3 | LLM gap analysis section classification | `gap_analysis.py` | 1h |
| P2-4 | Unify template directories + CI parity check | `src/hiveforge/templates/`, `hiveforge-power/hiveforge/templates/` | 2h |

---

### P0 Code Sketches

#### P0-2: `TemplatePopulator._get_raw_template()`

```python
def _get_raw_template(self, template_name: str) -> str:
    """Return raw template content. Caller strips frontmatter if needed."""
    if template_name not in self.templates:
        raise ValueError(f"Template '{template_name}' not found. "
                         f"Available: {list(self.templates.keys())}")
    template = self.templates[template_name]
    template_file = self._template_dir / template.file_name
    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_file}")
    return template_file.read_text(encoding="utf-8")
```

#### P0-3: Fix `AutonomousWorkflow` Silent Failure

> **RED TEAM note (SIG-4):** Use `level=None` consistently — `ConfidenceScore.__post_init__` always overwrites `level` based on `value`. Passing `level=ConfidenceLevel.LOW` explicitly is redundant and inconsistent.

```python
# BEFORE (broken — silently swallows AttributeError, writes empty string):
except Exception as e:
    ...
    self.generated_files[filename] = ""
    self.confidence_scores[filename] = ConfidenceScore(value=0.0, level=None, evidence=[])

# AFTER (correct — uses [INFERRED] fallback, never empty):
except Exception as e:
    logger.error(f"Failed to generate {filename}: {e}", exc_info=True)
    print(f"✗ Error: {e} (using [INFERRED] fallback)")
    self.fallback_triggered = True
    self.fallback_reasons.append(f"{filename}: {type(e).__name__}: {e}")
    try:
        from ..template_populator import TemplatePopulator
        populator = TemplatePopulator()
        raw = populator._get_raw_template(filename.replace(".md", ""))
        import re
        fallback_content = re.sub(r'\{([^}]+)\}', r'[INFERRED: \1]', raw)
    except Exception:
        fallback_content = f"# {filename}\n\n[GENERATION FAILED — please fill manually]\n"
    self.generated_files[filename] = fallback_content
    self.confidence_scores[filename] = ConfidenceScore(value=0.1, level=None, evidence=[])
```

#### P0-4: Fix `input()` in MCP Mode

> **RED TEAM note (ADV-4):** The guard alone is insufficient. `SteeringConfig.interactive` defaults to `True`. `SharedInitWorkflow` must explicitly pass `interactive=False` when constructing config for MCP invocations.

```python
# Fix 1: In init_workflow.py _step_check_existing_files():
if not self.config.interactive:
    logger.info("Non-interactive mode: auto-backing up existing files and proceeding")
    return self._create_backup(existing_files)

while True:
    choice = input("   Choose option (1 or 2): ").strip()
    ...

# Fix 2: In shared/adapters.py SharedInitWorkflow (or init_steering.py):
config = SteeringConfig(
    interactive=False,  # MCP mode — never prompt
    ...
)
```

---

### Execution Order for Developer

1. **Day 1 (P0 fixes — 5 hours):** P0-2, P0-3, P0-4. After these, `hiveforge steering init` produces files with `[INFERRED: ...]` markers instead of raw `{placeholders}`. Already useful without any LLM.

2. **Day 2 (LLM provider + generate_file — 5 hours):** P0-1. Implement `llm_provider.py`, thread `ctx`, make `generate_file()` async. Test with KIRO Auto mode (no extra config), then test with Vertex AI credentials file, then test with no LLM (verify `[INFERRED]` fallback).

3. **Day 3 (Code analyzer + drift — 6 hours):** P1-1, P1-2, P1-4. Better context for LLM calls. Drift detection for update workflow.

4. **Day 4 (Draft review + template variants — 6 hours):** P1-3, P2-1. Correct MCP draft behavior. Eliminate inapplicable sections for CLI/MCP projects.

5. **Day 5 (Cleanup — 3 hours):** P1-5, P2-4. Port missing files, unify templates, add CI check.

---

## Appendix: Verified File Inventory

| File | Exists in `hiveforge-power/` | Exists in `src/` | Notes |
|------|------------------------------|-----------------|-------|
| `steering_assistant.py` | ✓ | ✓ | Both missing `generate_file()` |
| `template_populator.py` | ✓ | ✓ | Both missing `_get_raw_template()` |
| `gap_analysis.py` | ✓ | ✓ | Keyword-only classification |
| `code_analyzer.py` | ✓ | ✓ | No public API extraction |
| `knowledge_base.py` | ✓ | ✓ | 500-char truncation bug |
| `init_workflow.py` | ✓ | ✓ | `input()` blocks MCP mode; `interactive` never set to False |
| `autonomous_workflow.py` | ✓ | ✓ | Silent failure on `generate_file()` |
| `update_workflow.py` | ✓ | ✓ | No code re-analysis, no drift detection |
| `llm_provider.py` | ✗ | ✗ | New file — does not exist yet |
| `content_tagger.py` | ✗ | ✓ | Missing from `hiveforge-power/` |
| `confidence.py` | ✗ | ✓ | Missing from `hiveforge-power/` |
| `source_resolver.py` | ✗ | ✓ | Missing from `hiveforge-power/` |
| `drift_detector.py` | ✗ | ✗ | New file — does not exist yet |
| `models.py` (`DraftState`) | ✗ | ✗ | New dataclasses needed |
| `models.py` (`DriftItem`) | ✗ | ✗ | New dataclasses needed |
| `models.py` (`PublicAPIInfo`) | ✗ | ✗ | New dataclasses needed |

---
*Report updated 2026-02-24 to incorporate RED TEAM findings (BLOCK-1/2/3, SIG-1/2/3/4, ADV-2/3/4/5) and user-requested LLM provider configuration design (KIRO native + Google Vertex AI + OpenAI).*
