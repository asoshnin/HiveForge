# Phase 6.6 Performance Testing Status

**Date:** 2026-02-19  
**Spec:** source-docs-and-guardrails  
**Phase:** 6.6 (Performance Testing - Red Team Recommended)

## Summary

Performance testing was partially completed. Discovery performance tests are working well, but confidence and tagging performance tests have API mismatches that need to be addressed.

## Test Results

### 6.6.3 Source Discovery Performance ✅ MOSTLY PASSING

**Status:** 10/12 tests passing (83% pass rate)

**Passing Tests:**
- ✅ 100 files discovery under 100ms
- ✅ 1000 files discovery under 1s
- ✅ 1000 files with nested directories
- ✅ 10,000 files discovery under 10s
- ✅ Symlink faster than copy (100 files)
- ✅ Symlink is default
- ✅ Discovery scales linearly
- ✅ Empty directory performance
- ✅ Single file performance
- ✅ Mixed file types performance

**Failing Tests:**
- ❌ Symlink faster than copy (1000 files) - Speedup 2.42x vs target 3x
  - This is a minor performance issue, not a critical failure
  - Symlink is still faster, just not by the target margin

**Benchmark Tests:**
- ⚠️ 2 benchmark tests require `pytest-benchmark` plugin (not installed)

**Verdict:** Discovery performance is good. The symlink speedup for 1000 files is slightly below target but still demonstrates performance benefit.

### 6.6.1 Confidence Calculation Performance ❌ API MISMATCH

**Status:** 0/9 tests passing (0% pass rate)

**Issue:** Tests were written with incorrect API assumptions:
- `ConfidenceCalculator()` doesn't take a `knowledge_base` argument
- `ConfidenceCalculator` is stateless - it doesn't need initialization with a KB
- `ConfidenceScore` has different field names:
  - `overall` not `overall_score`
  - `sources` not `source_breakdown`
  - No `section_count` or `inferred_count` fields

**Root Cause:** Tests were written based on design document assumptions rather than actual implementation.

**Required Fix:** Complete rewrite of all confidence performance tests to match actual API:
```python
# Correct API usage:
calculator = ConfidenceCalculator()
sources = {
    "documents": ["Section 1", "Section 2"],
    "code_analysis": ["Section 3"],
    "inferred": ["Section 4"]
}
score = calculator.calculate_file_confidence("file.md", sources, content)
```

### 6.6.2 Content Tagging Performance ❌ API MISMATCH

**Status:** 0/15 tests passing (0% pass rate)

**Issues:**
1. `ConfidenceScore` fixture uses wrong field names (same as above)
2. Content size assertions are too strict (151KB vs 100KB target, 1520KB vs 1MB target)
3. Tag format mismatch: Tests expect `[INFERRED]` but implementation uses HTML comments
4. Benchmark tests require `pytest-benchmark` plugin

**Required Fix:** 
- Update `ConfidenceScore` fixture to use correct API
- Relax content size assertions (allow ±50% variance)
- Update tag format expectations to match implementation
- Install `pytest-benchmark` or skip benchmark tests

## Performance Targets vs Actual

### Discovery Performance (MEASURED)
| Target | Actual | Status |
|--------|--------|--------|
| 100 files < 100ms | ✅ Passing | ✅ |
| 1000 files < 1s | ✅ Passing | ✅ |
| 10,000 files < 10s | ✅ Passing | ✅ |
| Symlink faster than copy | ✅ 2.42x speedup | ⚠️ Below 3x target |

### Confidence Calculation Performance (NOT MEASURED)
| Target | Actual | Status |
|--------|--------|--------|
| Per-file < 100ms | ❌ Not measured | ❌ |
| Overall < 200ms | ❌ Not measured | ❌ |
| 100-file KB reasonable | ❌ Not measured | ❌ |

### Content Tagging Performance (NOT MEASURED)
| Target | Actual | Status |
|--------|--------|--------|
| 10KB < 1ms | ❌ Not measured | ❌ |
| 100KB < 10ms | ❌ Not measured | ❌ |
| 1MB < 100ms | ❌ Not measured | ❌ |

## Recommendations

### Option 1: Fix Performance Tests (Recommended for v2.2.1)
**Effort:** 2-3 hours
**Approach:**
1. Rewrite confidence performance tests to use correct API
2. Fix tagging performance tests (ConfidenceScore fixture, content sizes, tag format)
3. Install `pytest-benchmark` or skip benchmark tests
4. Re-run all performance tests
5. Mark Phase 6.6 as complete

**Pros:**
- Complete performance validation
- Meets Red Team recommendation
- Provides baseline for future optimization

**Cons:**
- Delays v2.2.1 release by a few hours
- Tests may reveal performance issues requiring fixes

### Option 2: Skip Performance Tests for v2.2.1 (Defer to v2.2.2)
**Effort:** 0 hours
**Approach:**
1. Mark Phase 6.6 as "Deferred to v2.2.2"
2. Document known issues in release notes
3. Proceed to Phase 7 (Release Preparation)
4. Address performance testing in v2.2.2 patch release

**Pros:**
- Faster release of v2.2.1
- Discovery performance is validated (most critical)
- Can address performance issues in patch release

**Cons:**
- Doesn't fully meet Red Team recommendation
- No baseline for confidence/tagging performance
- May miss performance regressions

### Option 3: Minimal Performance Validation (Quick Win)
**Effort:** 30 minutes
**Approach:**
1. Write 2-3 simple performance tests for confidence calculation
2. Write 2-3 simple performance tests for content tagging
3. Use actual API (no fixtures, minimal setup)
4. Set generous performance targets (2x current targets)
5. Mark Phase 6.6 as "Partially Complete"

**Pros:**
- Quick validation of basic performance
- Meets spirit of Red Team recommendation
- Provides some baseline data

**Cons:**
- Not comprehensive
- May not catch edge case performance issues

## Decision Required

**Question:** Which option should we pursue for Phase 6.6?

**My Recommendation:** Option 3 (Minimal Performance Validation)
- Provides quick validation without delaying release
- Meets Red Team recommendation in spirit
- Can be expanded in v2.2.2 if needed
- Discovery performance (most critical) is already validated

## Files Created

- `tests/performance/__init__.py` ✅
- `tests/performance/test_confidence_performance.py` ⚠️ (needs rewrite)
- `tests/performance/test_tagging_performance.py` ⚠️ (needs rewrite)
- `tests/performance/test_discovery_performance.py` ✅ (mostly working)

## Next Steps

Based on decision:
1. **If Option 1:** Fix all performance tests, re-run, mark complete
2. **If Option 2:** Document deferral, proceed to Phase 7
3. **If Option 3:** Write minimal tests, mark partially complete, proceed to Phase 7
