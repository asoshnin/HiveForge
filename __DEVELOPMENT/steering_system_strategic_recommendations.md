# Steering System: Strategic Recommendations

**Date**: 2026-02-17  
**Author**: Product Owner / System Architect  
**Based on**: Diagnostic Report 20260217_150519

---

## EXECUTIVE DECISION: Convert to KIRO Power

**Recommendation**: Transform Steering Assistant into a KIRO Power, not just a KIRO agent.

**Rationale**:
- Powers already solve the exact problems identified (dynamic activation, zero baseline cost, focused behavior)
- Steering Assistant fits Power model perfectly (documentation-focused, keyword-activated, tool-based)
- Avoids creating yet another integration pattern - use the one that works
- Future-proof: Powers is KIRO's strategic direction

**Why not just "make it an agent"?**
- Agent = still requires Orchestrator integration, manual invocation
- Power = automatic activation on keywords like "steering", "documentation", "onboarding"
- Power = can be installed/uninstalled independently
- Power = follows proven pattern that already works

---

## STRATEGIC ROADMAP

### Phase 1: Quick Wins (1-2 weeks)
**Goal**: Fix broken workflow immediately

1. **Update WORKFLOW_refactoring_01.md**
   - Remove Step 2.2 entirely
   - Make Step 2.3 (CLI) the primary approach
   - Remove "NOT RECOMMENDED" label
   - Add clear CLI examples with expected output

2. **Fix Documentation**
   - Add template location to README.md
   - Document `.kiro/onboarding/` folder purpose upfront
   - Create single "Getting Started" path
   - Consolidate WORKFLOW.md and WORKFLOW_refactoring_01.md

3. **Add Template Restoration**
   ```bash
   hiveforge steering reset <file>  # Reset single file
   hiveforge steering reset --all   # Reset all files
   ```

**Impact**: Users can successfully complete workflows today

---

### Phase 2: Autonomous Generation (2-4 weeks)
**Goal**: Invert the automation pyramid

1. **Implement Proactive Discovery**
   ```python
   # Auto-discover existing docs
   discovered = discover_project_docs()
   # README.md, CONTRIBUTING.md, docs/, package.json, etc.
   
   if discovered:
       print(f"Found {len(discovered)} documents. Import? [Y/n]")
   ```

2. **Enable Autonomous Mode**
   - Make `--use-autonomous-generation` actually work
   - Generate complete drafts from code analysis + discovered docs
   - Use confidence scores to identify gaps
   - Only ask questions for low-confidence sections

3. **Generation-Time Validation**
   - Validate during generation, not after
   - Auto-regenerate if validation fails
   - Present only validated output to users

**Target UX**:
```bash
$ hiveforge steering init --auto

Discovering project context...
✓ Found README.md, package.json, 3 docs
✓ Analyzed codebase (Python 3.11, FastAPI, PostgreSQL)
✓ Generated 8 steering files (2 min)
✓ All files validated

Review generated files in .kiro/steering/
```

**Impact**: 10-minute workflow → 2-minute workflow, 14 questions → 0-2 questions

---

### Phase 3: Convert to KIRO Power (3-4 weeks)
**Goal**: Full KIRO IDE integration


#### 3.1 Power Architecture

**Structure**:
```
hiveforge-power/
├── POWER.md                    # Power documentation
├── mcp-server/                 # MCP server implementation
│   ├── server.py              # FastMCP server
│   └── tools/
│       ├── init_steering.py   # hiveforge steering init
│       ├── update_steering.py # hiveforge steering update
│       ├── validate_steering.py
│       ├── reset_steering.py
│       └── discover_docs.py
├── steering/                   # Existing steering code
│   └── [current implementation]
└── package.json               # Power metadata
```

**Power Metadata**:
```json
{
  "name": "hiveforge-steering",
  "displayName": "HiveForge Steering Assistant",
  "version": "2.0.0",
  "keywords": ["steering", "documentation", "onboarding", "project-setup"],
  "description": "AI-powered steering file generation and maintenance",
  "mcpServers": {
    "hiveforge-steering": {
      "command": "uvx",
      "args": ["hiveforge-steering-mcp@latest"]
    }
  }
}
```

#### 3.2 MCP Tools

**Tool 1: init_steering**
```python
@mcp.tool()
async def init_steering(
    auto_discover: bool = True,
    autonomous: bool = True,
    project_root: str = "."
) -> dict:
    """Initialize steering files with autonomous generation."""
    # Discover docs, analyze code, generate files
    return {"files_created": 8, "validation": "passed"}
```

**Tool 2: update_steering**
```python
@mcp.tool()
async def update_steering(
    files: list[str] = None,  # None = all files
    preserve_customizations: bool = True
) -> dict:
    """Update steering files with new information."""
    return {"files_updated": 3, "conflicts": 0}
```

**Tool 3: validate_steering**
```python
@mcp.tool()
async def validate_steering(
    strict: bool = False,
    use_llm: bool = True
) -> dict:
    """Validate steering files for completeness."""
    return {"status": "passed", "issues": []}
```

**Tool 4: reset_steering**
```python
@mcp.tool()
async def reset_steering(
    file: str = None,  # None = all files
    confirm: bool = False
) -> dict:
    """Reset steering files to default templates."""
    return {"files_reset": 1}
```

**Tool 5: discover_project_docs**
```python
@mcp.tool()
async def discover_project_docs(
    project_root: str = "."
) -> dict:
    """Discover existing project documentation."""
    return {
        "found": ["README.md", "docs/api.md"],
        "suggested_import": True
    }
```

#### 3.3 Keyword Activation

Power activates when user mentions:
- "steering files"
- "project documentation"
- "onboarding"
- "setup documentation"
- "generate docs"

**Example**:
```
User: "I need to create steering files for my project"
→ Power activates
→ Tools available to agent
→ Agent: "I'll help you generate steering files. Let me discover your project..."
→ Calls init_steering(auto_discover=True, autonomous=True)
```

#### 3.4 Integration with Orchestrator

**No special integration needed** - Powers work automatically:
1. User mentions "steering" keyword
2. KIRO activates hiveforge-steering Power
3. Tools become available to current agent
4. Agent uses tools to complete task
5. Power deactivates when task complete

---

### Phase 4: Dynamic Templates (4-6 weeks)
**Goal**: Flexible, project-aware templates

#### 4.1 Template Sets

**Minimal** (3 files):
- project-vision.md
- tech-stack.md
- conventions.md

**Standard** (8 files):
- Current 8-file structure

**Enterprise** (12 files):
- Standard + security-standards.md, deployment-guide.md, monitoring.md, compliance.md

**Custom**:
- User-defined template sets

#### 4.2 Auto-Detection

```python
def detect_template_set(project_analysis):
    if project_analysis.is_library:
        return "minimal"
    elif project_analysis.team_size > 10:
        return "enterprise"
    elif project_analysis.has_frontend and project_analysis.has_backend:
        return "standard"
    else:
        return "minimal"
```

#### 4.3 CLI Enhancement

```bash
# Auto-detect appropriate template set
hiveforge steering init --auto

# Specify template set
hiveforge steering init --template-set=minimal

# List available template sets
hiveforge steering templates list

# Create custom template set
hiveforge steering templates create my-custom-set
```

---

## CRITICAL DECISIONS

### Decision 1: Power vs. Agent vs. CLI-Only

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Power** | ✅ Proven pattern<br>✅ Auto-activation<br>✅ Zero baseline cost<br>✅ Future-proof | ⚠️ Requires MCP server<br>⚠️ 3-4 weeks effort | ✅ **RECOMMENDED** |
| Agent | ✅ Direct integration<br>✅ Orchestrator aware | ❌ Manual invocation<br>❌ Another pattern<br>❌ Not strategic direction | ❌ Not recommended |
| CLI-Only | ✅ Works today<br>✅ No changes needed | ❌ No IDE integration<br>❌ Manual workflow<br>❌ Inconsistent UX | ❌ Not recommended |

**Decision**: Convert to Power (Phase 3)

### Decision 2: Autonomous vs. Q&A

| Approach | User Effort | Quality | Token Cost | Recommendation |
|----------|-------------|---------|------------|----------------|
| **Autonomous** | 2 min | High (with validation) | 11K tokens | ✅ **RECOMMENDED** |
| Q&A (current) | 10 min | Low (83 errors) | 16K tokens | ❌ Not recommended |
| Hybrid | 5 min | Medium | 13K tokens | ⚠️ Fallback only |

**Decision**: Autonomous with confidence-based questions (Phase 2)

### Decision 3: Template Flexibility

| Approach | Flexibility | Complexity | Recommendation |
|----------|-------------|------------|----------------|
| **Dynamic Sets** | High | Medium | ✅ **RECOMMENDED** |
| Fixed 8 files | Low | Low | ❌ Current problem |
| Fully custom | Very high | High | ⚠️ Future enhancement |

**Decision**: Dynamic template sets with auto-detection (Phase 4)

---

## IMPLEMENTATION PRIORITIES

### Must Have (Phase 1-2)
1. ✅ Fix broken workflow documentation
2. ✅ Add template restoration command
3. ✅ Implement proactive discovery
4. ✅ Enable autonomous generation
5. ✅ Generation-time validation

### Should Have (Phase 3)
6. ✅ Convert to KIRO Power
7. ✅ MCP server implementation
8. ✅ Keyword-based activation
9. ✅ Full IDE integration

### Nice to Have (Phase 4)
10. ⚠️ Dynamic template sets
11. ⚠️ Auto-detection logic
12. ⚠️ Custom template creation

---

## MIGRATION STRATEGY

### For Existing Users

**Backward Compatibility**:
```bash
# Old CLI still works
hiveforge steering init

# New Power works automatically in KIRO IDE
# User: "create steering files"
# → Power activates, uses same backend
```

**Migration Path**:
1. Phase 1-2: CLI improvements (no breaking changes)
2. Phase 3: Power available, CLI still works
3. Phase 4+: Recommend Power, maintain CLI for CI/CD

### For New Users

**Recommended Flow**:
1. Install HiveForge Power in KIRO IDE
2. Open project in KIRO
3. Say: "Generate steering files"
4. Power auto-discovers, generates, validates
5. Review and customize as needed

---

## SUCCESS METRICS

### Phase 1 (Quick Wins)
- ✅ Workflow completion rate: 0% → 100%
- ✅ User confusion reports: High → Low
- ✅ Documentation clarity score: 3/10 → 8/10

### Phase 2 (Autonomous)
- ✅ Time to generate: 10 min → 2 min
- ✅ Questions asked: 14 → 0-2
- ✅ Validation errors: 83 → 0
- ✅ Token efficiency: 16K → 11K

### Phase 3 (Power)
- ✅ IDE integration: 0% → 100%
- ✅ Keyword activation success: N/A → 95%
- ✅ User satisfaction: 5/10 → 9/10

### Phase 4 (Dynamic)
- ✅ Template relevance: 60% → 95%
- ✅ Irrelevant questions: 30% → 5%
- ✅ Customization adoption: 10% → 40%

---

## RISKS & MITIGATION

### Risk 1: MCP Server Complexity
**Impact**: High  
**Probability**: Medium  
**Mitigation**: 
- Use FastMCP (proven, simple)
- Wrap existing Python code (minimal rewrite)
- Extensive testing before release

### Risk 2: Breaking Changes
**Impact**: High  
**Probability**: Low  
**Mitigation**:
- Maintain CLI backward compatibility
- Gradual rollout (CLI → Power)
- Clear migration documentation

### Risk 3: Autonomous Generation Quality
**Impact**: Medium  
**Probability**: Medium  
**Mitigation**:
- Confidence thresholds (ask if < 0.7)
- Generation-time validation
- Easy reset/regeneration

### Risk 4: Template Set Complexity
**Impact**: Low  
**Probability**: Medium  
**Mitigation**:
- Start with 3 sets (minimal, standard, enterprise)
- Auto-detection with manual override
- Phase 4 (not critical path)

---

## RESOURCE REQUIREMENTS

### Phase 1 (1-2 weeks)
- 1 developer (documentation, CLI enhancements)
- 0.5 QA (testing)

### Phase 2 (2-4 weeks)
- 1 senior developer (autonomous generation)
- 0.5 QA (testing)

### Phase 3 (3-4 weeks)
- 1 senior developer (MCP server, Power conversion)
- 0.5 DevOps (packaging, deployment)
- 0.5 QA (integration testing)

### Phase 4 (4-6 weeks)
- 1 developer (template system)
- 0.5 QA (testing)

**Total**: ~12-16 weeks, 1.5-2 FTE

---

## FINAL RECOMMENDATION

**Convert Steering Assistant to KIRO Power** following this sequence:

1. **Week 1-2**: Fix immediate issues (Phase 1)
2. **Week 3-6**: Implement autonomous generation (Phase 2)
3. **Week 7-10**: Convert to Power (Phase 3)
4. **Week 11-16**: Dynamic templates (Phase 4)

**Why this approach?**
- Fixes broken workflow immediately
- Delivers value incrementally
- Aligns with KIRO's strategic direction (Powers)
- Maintains backward compatibility
- Positions for future innovation

**Your instinct to make it a KIRO agent is correct** - but go one step further and make it a Power. Powers are the future, and Steering Assistant is a perfect fit.
