# Technical Debt Detection Implementation

**Version:** 3.0.0  
**Feature:** Code Review and Technical Debt Tracking  
**Status:** ✅ Complete  
**Last Updated:** February 2026

---

## Overview

HiveForge v3.0.0 introduces automatic technical debt detection and tracking through a 9th steering file (`technical-debt.md`). The system uses local static analysis to detect DRY violations, test gaps, architecture smells, and performance risks without requiring LLM calls.

---

## Architecture

### Components

```
DebtDetector (detectors/debt_detector.py)
    ├── _detect_dry_violations()      → AST-based function body hashing
    ├── _detect_test_gaps()            → File-to-test ratio analysis
    ├── _detect_architecture_smells()  → Circular imports, god classes
    └── _detect_performance_risks()    → Regex pattern matching

DebtReconciler (detectors/debt_reconciler.py)
    └── reconcile()                    → Merge existing + fresh analysis

SteeringFileGenerator
    └── generate_all_files()           → Now generates 9 files (added technical-debt.md)

AutonomousWorkflow
    └── _step_generate_files_autonomously()  → Wires DebtDetector into pipeline
```

### Data Flow

```
Init Workflow:
  Code Analysis
       ↓
  DebtDetector.detect()
       ↓
  Cache (.kiro/.cache/debt_analysis.json)
       ↓
  SteeringFileGenerator (debt_facts param)
       ↓
  technical-debt.md (9th file)

Update Workflow:
  Existing technical-debt.md
       ↓
  DebtDetector.detect()
       ↓
  DebtReconciler.reconcile()
       ↓
  Merged DebtAnalysisResult
       ↓
  SteeringFileGenerator
       ↓
  Updated technical-debt.md
```

---

## Features

### 1. Static Analysis Detectors

#### DRY Violations (Code Quality)
- **Method**: AST-based normalized function body hashing
- **Threshold**: ≥10 statements, Jaccard similarity ≥0.85
- **Fallback**: Line-hash comparison for non-Python files (≥15 consecutive non-blank lines)
- **Priority**: MEDIUM (escalates to HIGH if conventions.md mentions "DRY")

#### Test Gaps (Tests)
- **Method**: File-to-test ratio analysis + AST public function coverage
- **Detection**:
  - Missing test files (expected `test_{module}.py`)
  - Untested public functions (not called in test file)
- **Priority**: HIGH for missing files, MEDIUM for untested functions (escalates to HIGH if conventions.md mentions "tested > assumed")

#### Architecture Smells (Architecture)
- **Method**: Import graph analysis + class size detection
- **Detection**:
  - Circular imports (Tarjan's SCC algorithm)
  - God classes (>500 lines)
- **Priority**: HIGH for cycles, MEDIUM for god classes

#### Performance Risks (Performance)
- **Method**: Regex pattern matching
- **Patterns**:
  - N+1 query in loop (HIGH)
  - Unbounded `while True` (HIGH)
  - String concatenation in loop (MEDIUM)
  - List allocation in loop (LOW)

### 2. Scalability Features

#### Large Codebase Handling
- **Threshold**: 10,000 files
- **Sampling**: Random sample of 2,000 files
- **Indicator**: `sampled=True` in result

#### Caching
- **Location**: `.kiro/.cache/debt_analysis.json`
- **Invalidation**: Automatic on codebase change
- **Corruption Handling**: Delete and re-run on parse error

#### .gitignore Respect
- **Library**: `pathspec` for pattern matching
- **Behavior**: Excludes all gitignore-matched paths from analysis

### 3. Reconciliation (Update Workflow)

#### Rules (Priority Order)
1. **User-edited items**: Preserve description/priority if manually changed
2. **Manually added items**: Preserve items with IDs absent from fresh analysis
3. **Auto-resolved items**: Move to RESOLVED if absent from fresh analysis
4. **New items**: Add with `status=ACTIVE` and `detected_at` timestamp
5. **Historical resolved items**: Preserve verbatim from Resolved section

#### Manual vs Auto-Detected Distinction
- **Manual items**: No `detected_at` timestamp in markdown table
- **Auto-detected items**: Have `detected_at` timestamp
- **Reconciler**: Uses presence/absence of `detected_at` to identify manual items

### 4. Priority Escalation

Based on `conventions.md` content:
- **DRY preference**: "dry", "don't repeat", "duplication" → CODE_QUALITY items escalated
- **Testing preference**: "tested > assumed", "minimum coverage" → TESTS items escalated to HIGH

### 5. CLI Integration

#### New Flag
```bash
hiveforge steering init --skip-debt-detection
```

- **Behavior**: Skips `DebtDetector.detect()` call
- **Result**: `technical-debt.md` still generated with placeholder content
- **Use case**: Fast init when debt analysis not needed

#### MCP Integration

**Metadata Enhancement**:
```json
{
  "status": "success",
  "files_written": [...],
  "debt_summary": {
    "total_active": 12,
    "by_category": {"code_quality": 3, "tests": 5, ...},
    "by_priority": {"high": 4, "medium": 6, "low": 2},
    "last_updated": "2026-02-25T00:00:00+00:00"
  }
}
```

---

## Data Models

### DebtItem
```python
@dataclass
class DebtItem:
    id: str                              # 12-char hex (stable across re-runs)
    category: DebtCategory               # CODE_QUALITY, TESTS, ARCHITECTURE, PERFORMANCE
    description: str
    location: str                        # file:line format
    priority: DebtPriority               # LOW, MEDIUM, HIGH, CRITICAL
    effort: DebtEffort                   # LOW, MEDIUM, HIGH
    risk: DebtRisk                       # LOW, MEDIUM, HIGH
    status: DebtStatus                   # ACTIVE, RESOLVED, ACCEPTED
    confidence: float                    # 0.0-1.0
    recommendations: List[DebtRecommendation]  # At least 2
    detected_at: Optional[str] = None    # ISO-8601 (None = manual item)
    resolved_at: Optional[str] = None    # ISO-8601
```

### DebtRecommendation
```python
@dataclass
class DebtRecommendation:
    title: str
    description: str
    trade_offs: str
    is_recommended: bool  # True for primary recommendation
```

### DebtAnalysisResult
```python
@dataclass
class DebtAnalysisResult:
    items: List[DebtItem]
    metrics: DebtMetrics
    sampled: bool
    analysis_time_s: float
    
    def to_json_dict(self) -> Dict[str, Any]: ...
    def active_items(self) -> List[DebtItem]: ...
    def resolved_items(self) -> List[DebtItem]: ...
```

---

## Testing

### Test Coverage

**Unit Tests** (15 tests):
- `test_debt_detector.py`: Sub-detector validation, ID stability, empty codebase, unparseable files
- `test_debt_reconciler.py`: Manual item preservation, auto-resolved handling, user edits, parse errors

**Property Tests** (22 tests):
- Property 1: `technical-debt.md` always generated (6 tests)
- Property 2: Required sections present (5 tests)
- Property 3: Valid YAML frontmatter (3 tests)
- Property 4: DebtItem field validity (1 test)
- Property 5: ID stability (1 test)
- Property 6: Gitignore exclusion (1 test)
- Property 7: Manual item preservation (1 test)
- Property 8: Auto-resolved items (1 test)
- Property 9: Atomic write with 9 files (12 tests)
- Property 10: Cache round-trip (1 test)
- Property 11: Cross-reference context assembly (4 tests)
- Property 12: DRY detection monotonicity (1 test)
- Property 13: Test gap detection monotonicity (1 test)

**Integration Tests** (13 tests):
- `test_technical_debt_generation.py`: Full pipeline, skip-detection, detector exception handling

**Total**: 68 tests, 100% pass rate

---

## Performance

### Benchmarks

| Codebase Size | Files Analyzed | Analysis Time | Sampled |
|---------------|----------------|---------------|---------|
| Small (<1k)   | All            | <1s           | No      |
| Medium (1k-10k) | All          | 1-5s          | No      |
| Large (>10k)  | 2,000 (sample) | 2-4s          | Yes     |

### Optimization Strategies

1. **Sampling**: Random 2k files for codebases >10k files
2. **Caching**: Skip analysis if codebase unchanged
3. **Early exit**: Skip unparseable files with WARNING log
4. **Parallel-safe**: No shared state between detectors

---

## File Format

### technical-debt.md Structure

```markdown
---
inclusion: always
priority: 3
---

# Technical Debt

## Overview
Brief description of technical debt tracking.

## Debt Categories
- Code Quality: DRY violations, duplication
- Tests: Missing tests, untested functions
- Architecture: Circular imports, god classes
- Performance: N+1 queries, inefficient patterns

## Active Debt Items

| ID | Category | Description | Location | Priority | Effort | Risk | Confidence | Detected At |
|----|----------|-------------|----------|----------|--------|------|------------|-------------|
| aabbccddeeff | code_quality | DRY violation | src/utils.py:10 | high | medium | medium | 0.85 | 2026-02-25T00:00:00+00:00 |

### Recommendations for aabbccddeeff
1. ✓ Extract shared helper (Recommended)
2. Accept duplication

## Resolved Debt Items

| ID | Category | Description | Resolved At |
|----|----------|-------------|-------------|
| 112233445566 | tests | Missing test file | 2026-02-24T00:00:00+00:00 |

## Debt Metrics

- Total active: 12
- By category: code_quality (3), tests (5), architecture (2), performance (2)
- By priority: high (4), medium (6), low (2)
- Last updated: 2026-02-25T00:00:00+00:00
```

---

## Migration Guide

### From v2.2.0 to v3.0.0

**No breaking changes**. The 9th file is added automatically.

**New CLI flag**:
```bash
# Skip debt detection (faster init)
hiveforge steering init --skip-debt-detection
```

**New MCP metadata**:
```python
result = await init_steering(ctx, project_root=".")
debt_summary = result.get("debt_summary")  # New in v3.0.0
```

**Existing workflows**: No changes required. The 9th file is generated automatically.

---

## Known Limitations

1. **Python-only DRY detection**: AST-based analysis only for Python; other languages use line-hash fallback
2. **First-segment import graph**: Circular import detection uses first segment of module names only
3. **Regex-based performance detection**: May have false positives/negatives
4. **No cross-file test coverage**: Only checks if test file exists and if function names appear in test
5. **Sampling randomness**: Large codebase sampling is non-deterministic (different files each run)

---

## Future Enhancements

### Planned for v3.1.0
- [ ] Multi-language DRY detection (JavaScript, TypeScript, Java)
- [ ] Coverage.py integration for precise test coverage
- [ ] Custom debt rules via `.kiro/debt-rules.yaml`
- [ ] Debt trend tracking over time
- [ ] IDE integration for inline debt annotations

### Under Consideration
- [ ] LLM-enhanced debt description generation
- [ ] Automatic refactoring suggestions
- [ ] Debt prioritization based on code churn
- [ ] Integration with issue trackers (GitHub Issues, Jira)

---

## References

- [Requirements](.kiro/specs/code-review-and-debt-tracking/requirements.md)
- [Design](.kiro/specs/code-review-and-debt-tracking/design.md)
- [Tasks](.kiro/specs/code-review-and-debt-tracking/tasks.md)
- [API Reference](API_REFERENCE.md#debt-detector-api)

---

**Last Updated:** February 2026  
**Maintainer:** HiveForge Team
