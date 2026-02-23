# RED TEAM QA Report: HiveForge Steering Quality Improvement Report
**Date:** 2026-02-24  
**Reviewer:** RED TEAM (Adversarial Auditor)  
**Subject:** `_DEVELOPMENT/2026-02-24_codeimprover_report.md`  
**Mandate:** Find flaws, false assumptions, and implementation risks before any code is written.  
**Framing:** Usefulness for the vibe coder — does this report actually help someone ship working code?

---

## Verdict

**CONDITIONAL SIGN-OFF.**

The P0 root cause analysis is accurate and the fixes are sound. Implement P0-1 through P0-4 immediately — they are correct, low-risk, and will produce a measurable improvement (files with `[INFERRED]` markers instead of raw `{placeholders}`).

The LLM integration design (Section 2) has **three blocking issues** that must be resolved before implementation. Do not write a line of LLM integration code until these are addressed. The drift detection design (Section 4) has one significant false-positive problem. Everything else is advisory.

---

## BLOCKING ISSUES (must fix before implementing Section 2)

### BLOCK-1: Wrong LLM Provider — OpenAI is not the right answer here

The report hardcodes `openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))` throughout Section 2 and the P0-1/P1-6 code sketches. This is the wrong design for a tool that runs inside KIRO IDE as an MCP Power.

**The actual situation:**

`init_steering.py` already receives a `ctx: Context` parameter from FastMCP (confirmed in the file). FastMCP's `Context` object provides `ctx.sample()` — a method that routes LLM calls through KIRO's own LLM infrastructure, using whatever model the user has selected (including "Auto" mode at 1 credit vs. Claude Opus at 2.2 credits).

The report never mentions `ctx.sample()`. It never mentions that `ctx` exists. It never mentions KIRO's credit system. For a tool whose primary users are vibe coders running inside KIRO, this is a critical omission.

**What `ctx.sample()` looks like (FastMCP standard):**

```python
# In init_steering.py (already has ctx: Context)
response = await ctx.sample(
    messages=[{"role": "user", "content": user_prompt}],
    system_prompt=SYSTEM_PROMPT_GENERATE_FILE,
    max_tokens=2000,
)
result = response.text
```

**The problem with the report's approach:**

- Requires the user to have an `OPENAI_API_KEY` environment variable set
- Adds a hard dependency on the `openai` package (which is NOT in `pyproject.toml` — see BLOCK-3)
- Bypasses KIRO's credit system entirely — the user pays OpenAI separately AND pays KIRO credits for the MCP tool invocation
- Ignores the user's model selection in KIRO settings
- Will not work at all for users who don't have an OpenAI account

**Required fix:** The LLM integration design must be rewritten to use `ctx.sample()` as the primary path. The `OPENAI_API_KEY` fallback can remain as a secondary option for CLI usage (where `ctx` is not available), but it must not be the primary design.

**Impact on code sketches:** Every code sketch in Section 2 that calls `openai.OpenAI(...)` needs to be replaced with `ctx.sample(...)`. This requires `ctx` to be threaded from `init_steering.py` → `SharedInitWorkflow` → `AutonomousWorkflow` → `SteeringAssistant.generate_file()`. The report does not address this threading at all.

---

### BLOCK-2: Async/Sync Mismatch — Will Block the Event Loop

The `@secure_execution` decorator (confirmed in `security.py`) is `async def wrapper(*args, **kwargs)`. All MCP tools run in an async context.

The report's `generate_file()` sketch calls `openai.OpenAI(...)` synchronously — the standard `openai` client is synchronous and will block the event loop when called from an async context. This will cause the entire MCP server to hang for the duration of every LLM call (typically 2–10 seconds per file × 8 files = up to 80 seconds of event loop blocking).

**The report does not mention this at all.**

**Required fix:** Either:
1. Use `ctx.sample()` which is already async (preferred — see BLOCK-1), or
2. Use `openai.AsyncOpenAI(...)` with `await client.chat.completions.create(...)`, or
3. Use `asyncio.to_thread(sync_openai_call)` to run the sync call in a thread pool

The `generate_file()` method itself must be `async def` if it makes any awaitable calls. This cascades: `_generate_single_file()` in `autonomous_workflow.py` must also become `async def`, and `_step_generate_files_autonomously()` must `await` it.

---

### BLOCK-3: `openai` Package Not in `pyproject.toml`

Confirmed by reading `hiveforge-power/pyproject.toml`. The dependencies are:

```toml
dependencies = [
    "fastmcp>=0.1.0",
    "pydantic>=2.0.0",
    "typer>=0.9.0",
]
```

`openai` is not listed. The report's code sketches do `import openai` inside functions (which delays the `ImportError` until runtime), but the package will not be installed in any environment that installs HiveForge from `pyproject.toml`.

**The report does not mention this.**

**Required fix:** Either add `openai>=1.0.0` to `dependencies` (or `optional-dependencies`), or — better — use `ctx.sample()` and avoid the dependency entirely. If `openai` is kept as an optional fallback for CLI mode, add it to `[project.optional-dependencies]` under a new `[llm]` group:

```toml
[project.optional-dependencies]
llm = ["openai>=1.0.0"]
```

And document that CLI LLM features require `pip install hiveforge-steering-mcp[llm]`.

---

## SIGNIFICANT ISSUES (should fix before shipping)

### SIG-1: `DriftDetector._check_tech_stack()` — Hundreds of False Positives

The report's drift detection checks whether each dependency name appears anywhere in `tech-stack.md`. For a project with 50+ dependencies (HiveForge has `fastmcp`, `pydantic`, `typer`, plus all dev deps), this will flag every single dependency that isn't explicitly mentioned in the steering file as a "new_dependency" drift item.

The current `tech-stack.md` template has a `Key Dependencies` table with 2 placeholder rows. After init, it will have at most 5–10 entries. The drift detector will then flag 40+ "new dependencies" on the first update run, drowning the user in noise.

**Required fix:** Only flag dependencies that are architecturally significant (frameworks, ORMs, auth libraries) — not every transitive or dev dependency. A simple heuristic: only flag dependencies that appear in the `[project.dependencies]` section (not `dev`), and only if they match a curated list of "significant" package categories (web frameworks, databases, auth, testing frameworks). Or use the LLM classification to determine significance.

---

### SIG-2: `_detect_database()` False Positive on HiveForge Itself

The report's `_detect_database()` checks for `models.py` as a database indicator:

```python
db_indicators = ["migrations", "prisma", "alembic.ini", "models.py"]
for indicator in db_indicators:
    if (self.project_root / indicator).exists():
        return True
```

HiveForge has `hiveforge-power/hiveforge/steering/models.py`. This is a data models file for the steering system — it has nothing to do with a database. `_detect_database()` will return `True` for HiveForge itself, causing `db-standards.md` to be generated when it should be skipped.

The check `(self.project_root / "models.py").exists()` looks for `models.py` at the project root, not in subdirectories — so this specific case may not trigger. But `self.project_root.rglob("models.py")` would. The report doesn't specify which form is used, and the sketch uses `(self.project_root / indicator).exists()` which is root-only. This is fine for now but fragile — document the assumption explicitly.

---

### SIG-3: `_get_primary_language()` Infinite Recursion Risk

The report's `_get_primary_language()` sketch calls `self.analyze()`:

```python
def _get_primary_language(self) -> str:
    result = self.analyze()
    if result.languages:
        return max(result.languages, key=lambda l: l.percentage).name
    return "Python"
```

`_heuristic_classify()` calls `_get_primary_language()`. If `_heuristic_classify()` is called from within `analyze()` (which is plausible given the report recommends calling it after analysis), this creates a call chain: `analyze()` → `_heuristic_classify()` → `_get_primary_language()` → `analyze()` → infinite recursion.

**Required fix:** `_get_primary_language()` should not call `self.analyze()`. It should accept the analysis result as a parameter, or read from `self._cached_result` if the analyzer caches its output. The simplest fix: make it a static method that takes `languages: list[LanguageInfo]` as input.

---

### SIG-4: `ConfidenceScore` Constructor in P0-3 Fix Sketch — Inconsistency

The P0-3 fix sketch passes `level=ConfidenceLevel.LOW` explicitly:

```python
self.confidence_scores[filename] = ConfidenceScore(
    value=0.1,
    level=ConfidenceLevel.LOW,
    evidence=[],
)
```

But `ConfidenceScore.__post_init__()` (confirmed in `models.py`) **overwrites `level` based on `value`**:

```python
def __post_init__(self):
    if self.value >= 0.9:
        self.level = ConfidenceLevel.HIGH
    elif self.value >= 0.7:
        self.level = ConfidenceLevel.MEDIUM
    else:
        self.level = ConfidenceLevel.LOW
```

With `value=0.1`, `__post_init__` will set `level=ConfidenceLevel.LOW` anyway — so passing `level=ConfidenceLevel.LOW` explicitly is redundant but not wrong. However, the original `_step_generate_files_autonomously()` code passes `level=None`, which also works because `__post_init__` overwrites it. The report's own Section 1 root cause table says `level=None` is "actually correct" — then the P0-3 fix sketch passes `level=ConfidenceLevel.LOW`. This is inconsistent and will confuse the developer implementing it.

**Required fix:** Standardize on `level=None` everywhere (since `__post_init__` always overwrites it), or remove `level` from the constructor signature entirely and let `__post_init__` be the sole setter. Document this behavior clearly.

---

## ADVISORY ISSUES (worth noting, low urgency)

### ADV-1: Token Cost Estimates Are Optimistic

Section 2 estimates "~1500–2500 tokens per file." This does not account for:

- Template frontmatter (~100 tokens of YAML noise per file, sent to LLM unnecessarily)
- The `context` parameter containing all previously generated files — by file 8 (`ui-standards.md`), `context` contains 7 previously generated files × ~500 tokens each = ~3500 tokens of context alone, exceeding the 1500-token estimate for the context parameter

**Actual estimate for file 8:** ~500 (system) + ~3500 (previous files) + ~800 (KB content) + ~600 (template) + ~2000 (response) = ~7400 tokens. At `gpt-4o-mini` pricing this is still cheap (~$0.002), but the estimate in the report is off by 3–5×.

**Recommendation:** Strip frontmatter from templates before sending to LLM. Cap `context` (previous files) to the 3 most recently generated files, not all previous files.

---

### ADV-2: Section 3 Draft Review — "Mark All Approved in MCP Mode" Defeats the Purpose

Section 3's `_step_review_draft()` sketch includes:

```python
# MCP mode: non-interactive, return draft via state
if not self.config.interactive:
    for df in draft.files.values():
        df.is_approved = True
    return True
```

This auto-approves everything in MCP mode, which means the draft review step adds zero value for MCP users — files are written immediately just as before. The stated purpose of the draft step is to let users see what will be written before it's written.

The correct MCP behavior is: return the draft summary in the MCP response, do NOT write files yet, and require a second MCP call (e.g., `approve_draft` or `update_steering` with `apply_draft=True`) to actually write. This is a more significant design change than the report acknowledges.

For the vibe coder: the current "auto-approve in MCP mode" design means they still get surprised by what gets written. The whole point of the draft step is to prevent that surprise.

---

### ADV-3: Section 7 Roadmap — P0-1 and P1-6 Are the Same Thing

The roadmap lists:

- **P0-1:** "Add `generate_file()` to `SteeringAssistant`" — 2h
- **P1-6:** "Add LLM injection to `generate_file()`" — 2h

These are the same function. The P0-1 code sketch already includes the full LLM call with `openai`. There is no version of `generate_file()` that is "P0 complete" without LLM and then "P1-6 complete" with LLM — the sketch in Section 7 already has both.

This creates confusion: a developer reading the roadmap might implement P0-1 as "just the fallback path" and then implement P1-6 as "add the LLM call" — but the P0-1 sketch already has the LLM call. The roadmap should either merge these into one item or clearly describe what P0-1 delivers vs. what P1-6 adds.

**Recommendation:** Merge into one item: "Add `generate_file()` with `ctx.sample()` LLM call and `[INFERRED]` fallback — 3h."

---

### ADV-4: `_step_check_existing_files()` Fix Is Incomplete

The P0-4 fix sketch adds a guard for `if not self.config.interactive:` before the `input()` call. This is correct. However, the report does not verify whether `self.config.interactive` is actually set to `False` when called from MCP mode.

In `init_steering.py`, `SharedInitWorkflow` is constructed with no `interactive` parameter — the `SteeringConfig` default is `interactive: bool = True` (confirmed in `models.py`). So even after the P0-4 fix, `self.config.interactive` will be `True` in MCP mode, and the `input()` call will still execute.

**Required fix:** `SharedInitWorkflow` (or `init_steering.py`) must explicitly set `interactive=False` when constructing `SteeringConfig` for MCP invocations. This is a one-line fix but the report misses it.

---

### ADV-5: `ctx` Threading Is a Non-Trivial Refactor

BLOCK-1 requires threading `ctx` from `init_steering.py` through `SharedInitWorkflow` → `AutonomousWorkflow` → `SteeringAssistant.generate_file()`. The report estimates P0-1 at 2 hours. With the `ctx` threading requirement, the actual effort is closer to 4–6 hours, because:

- `SharedInitWorkflow.__init__()` needs a `ctx` parameter
- `AutonomousWorkflow.__init__()` needs a `ctx` parameter  
- `SteeringAssistant.__init__()` needs a `ctx` parameter
- All intermediate `execute()` and `_generate_single_file()` calls need to pass `ctx` through
- `generate_file()` must become `async def`
- `_generate_single_file()` must become `async def`
- `_step_generate_files_autonomously()` must become `async def` and use `asyncio.gather()` or sequential `await`

This is a meaningful refactor, not a 2-hour patch. The roadmap effort estimates should be revised upward.

---

## What the Report Gets Right

- Root cause identification is accurate. The `AttributeError` on `generate_file()`, the key mismatch in `_replace_placeholders()`, and the `input()` block in MCP mode are all real bugs, correctly diagnosed.
- The `[INFERRED]` marker fallback is the right UX for the no-LLM case. Vibe coders get something useful immediately.
- The `DraftState` concept is sound — the implementation detail (auto-approve in MCP mode) needs fixing, but the data structure is right.
- The `DriftDetector` architecture is correct. The false-positive problem (SIG-1) is a tuning issue, not a design flaw.
- The template variant table (Section 6.2) is exactly right. Generating `ui-standards.md` for a CLI tool is actively harmful.
- The code analyzer improvements (Section 5) are well-scoped and the AST-based extraction approach is correct.

---

## Summary for the Vibe Coder

**Do this now (P0, today):**
- P0-2: `_get_raw_template()` — 30 minutes, zero risk
- P0-3: Fix silent failure in `_step_generate_files_autonomously()` — 1 hour, zero risk
- P0-4: Fix `input()` in MCP mode — but also fix `interactive=False` not being set (ADV-4) — 1 hour total

**Do this before touching LLM code:**
- Resolve BLOCK-1: Rewrite LLM integration to use `ctx.sample()` instead of `openai.OpenAI()`
- Resolve BLOCK-2: Make `generate_file()` async
- Resolve BLOCK-3: Either add `openai` to `pyproject.toml` optional deps or drop it entirely in favor of `ctx.sample()`

**Then implement P0-1 (now renamed):** `generate_file()` with `ctx.sample()` as primary, `OPENAI_API_KEY` as CLI fallback — estimate 4–6 hours including `ctx` threading.

**The payoff for the vibe coder:** After P0 fixes, `hiveforge steering init` produces 8 files with `[INFERRED: ...]` markers instead of raw `{placeholders}`. That's already useful — the user can see the structure and fill in the gaps. After LLM integration with `ctx.sample()`, the files are populated automatically using KIRO's own LLM at Auto-mode cost (1 credit per init run, not per file). No OpenAI account required.

---

*RED TEAM review complete. All findings based on direct file inspection. No assumptions made about unread code.*
