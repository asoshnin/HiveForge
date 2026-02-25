"""
Property-based tests for DebtDetector.

Feature: code-review-and-debt-tracking
Properties covered:
  Property 4:  DebtItem fields are always valid
  Property 5:  DebtItem IDs are stable across re-runs
  Property 6:  DebtDetector produces no items from gitignore-excluded paths
  Property 10: Debt analysis cache round-trip
  Property 12: DRY violation detection is monotone
  Property 13: Test gap detection is monotone
"""

import json
import textwrap
from pathlib import Path

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from hiveforge.steering.detectors.debt_detector import (
    DebtDetector,
    _deserialize_result,
    _serialize_result,
)
from hiveforge.steering.models import (
    DebtCategory,
    DebtEffort,
    DebtPriority,
    DebtRisk,
    DebtStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_py(tmp_path: Path, name: str, source: str) -> Path:
    """Write a Python source file and return its path."""
    p = tmp_path / name
    p.write_text(textwrap.dedent(source), encoding="utf-8")
    return p


def _make_detector(tmp_path: Path, conventions: str = "") -> DebtDetector:
    return DebtDetector(project_root=tmp_path, conventions_content=conventions)


# ---------------------------------------------------------------------------
# Property 5: DebtItem IDs are stable across re-runs
# Feature: code-review-and-debt-tracking, Property 5: DebtItem IDs are stable across re-runs
# ---------------------------------------------------------------------------

def test_property5_id_stability(tmp_path):
    """Two successive detect() calls on unchanged code produce identical IDs."""
    _write_py(tmp_path, "module_a.py", """\
        def foo():
            x = 1
            y = 2
            return x + y
    """)

    det = _make_detector(tmp_path)
    result1 = det.detect()

    # Delete cache so second call re-runs analysis
    cache = tmp_path / ".kiro" / ".cache" / "debt_analysis.json"
    if cache.exists():
        cache.unlink()

    det2 = _make_detector(tmp_path)
    result2 = det2.detect()

    ids1 = {item.id for item in result1.items}
    ids2 = {item.id for item in result2.items}
    assert ids1 == ids2, f"IDs changed between runs: {ids1 ^ ids2}"


@given(
    category=st.sampled_from(list(DebtCategory)),
    location=st.text(min_size=1, max_size=80, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc"))),
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
def test_property5_make_item_id_deterministic(tmp_path, category, location):
    """_make_item_id returns the same value for the same inputs."""
    det = _make_detector(tmp_path)
    id1 = det._make_item_id(category, location)
    id2 = det._make_item_id(category, location)
    assert id1 == id2
    assert len(id1) == 12


# ---------------------------------------------------------------------------
# Property 6: DebtDetector produces no items from gitignore-excluded paths
# Feature: code-review-and-debt-tracking, Property 6: DebtDetector produces no items from gitignore-excluded paths
# ---------------------------------------------------------------------------

def test_property6_gitignore_exclusion(tmp_path):
    """Items from gitignore-excluded paths must not appear in results."""
    # Create a file that would normally trigger a test-gap item
    excluded_dir = tmp_path / "vendor"
    excluded_dir.mkdir()
    _write_py(excluded_dir, "third_party.py", """\
        def helper():
            pass
    """)

    # Write .gitignore that excludes vendor/
    (tmp_path / ".gitignore").write_text("vendor/\n", encoding="utf-8")

    det = _make_detector(tmp_path)
    result = det.detect()

    for item in result.items:
        assert not item.location.startswith("vendor"), (
            f"Item from gitignore-excluded path found: {item.location}"
        )


@given(
    excluded_dir_name=st.sampled_from(["build", "dist", "node_modules", "vendor", ".venv"]),
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
def test_property6_gitignore_exclusion_parametric(tmp_path, excluded_dir_name):
    """No items reference paths matching .gitignore patterns."""
    excl = tmp_path / excluded_dir_name
    excl.mkdir()
    _write_py(excl, "generated.py", "def gen(): pass\n")
    (tmp_path / ".gitignore").write_text(f"{excluded_dir_name}/\n", encoding="utf-8")

    det = _make_detector(tmp_path)
    result = det.detect()

    for item in result.items:
        assert not item.location.startswith(excluded_dir_name + "/") and \
               not item.location.startswith(excluded_dir_name + "\\"), (
            f"Item from excluded path '{excluded_dir_name}': {item.location}"
        )


# ---------------------------------------------------------------------------
# Property 12: DRY violation detection is monotone
# Feature: code-review-and-debt-tracking, Property 12: DRY violation detection is monotone
# ---------------------------------------------------------------------------

def test_property12_dry_monotone(tmp_path):
    """Adding a verbatim copy of a function produces at least one extra CODE_QUALITY item."""
    original = textwrap.dedent("""\
        def compute(a, b, c, d, e, f, g, h, i, j):
            r1 = a + b
            r2 = c + d
            r3 = e + f
            r4 = g + h
            r5 = i + j
            r6 = r1 * r2
            r7 = r3 * r4
            r8 = r5 * r6
            r9 = r7 + r8
            return r9
    """)

    _write_py(tmp_path, "module_a.py", original)

    det_baseline = _make_detector(tmp_path)
    baseline = det_baseline.detect()
    baseline_cq = sum(1 for i in baseline.items if i.category == DebtCategory.CODE_QUALITY)

    # Add a verbatim copy in a new file
    _write_py(tmp_path, "module_b.py", original)

    # Clear cache so detector re-runs
    cache = tmp_path / ".kiro" / ".cache" / "debt_analysis.json"
    if cache.exists():
        cache.unlink()

    det_after = _make_detector(tmp_path)
    after = det_after.detect()
    after_cq = sum(1 for i in after.items if i.category == DebtCategory.CODE_QUALITY)

    assert after_cq > baseline_cq, (
        f"Expected more CODE_QUALITY items after adding duplicate function "
        f"(baseline={baseline_cq}, after={after_cq})"
    )


# ---------------------------------------------------------------------------
# Property 13: Test gap detection is monotone
# Feature: code-review-and-debt-tracking, Property 13: Test gap detection is monotone
# ---------------------------------------------------------------------------

def test_property13_test_gap_monotone(tmp_path):
    """Removing a test file produces at least one extra TESTS item."""
    _write_py(tmp_path, "calculator.py", """\
        def add(a, b):
            return a + b

        def subtract(a, b):
            return a - b
    """)
    test_file = _write_py(tmp_path, "test_calculator.py", """\
        from calculator import add, subtract

        def test_add():
            assert add(1, 2) == 3

        def test_subtract():
            assert subtract(3, 1) == 2
    """)

    det_baseline = _make_detector(tmp_path)
    baseline = det_baseline.detect()
    baseline_tests = sum(1 for i in baseline.items if i.category == DebtCategory.TESTS)

    # Remove the test file
    test_file.unlink()

    cache = tmp_path / ".kiro" / ".cache" / "debt_analysis.json"
    if cache.exists():
        cache.unlink()

    det_after = _make_detector(tmp_path)
    after = det_after.detect()
    after_tests = sum(1 for i in after.items if i.category == DebtCategory.TESTS)

    assert after_tests > baseline_tests, (
        f"Expected more TESTS items after removing test file "
        f"(baseline={baseline_tests}, after={after_tests})"
    )


# ---------------------------------------------------------------------------
# Property 4: DebtItem fields are always valid
# Feature: code-review-and-debt-tracking, Property 4: DebtItem fields are always valid
# ---------------------------------------------------------------------------

def test_property4_debt_item_fields_valid(tmp_path):
    """All DebtItems produced by detect() have valid enum fields, confidence in [0,1], >=2 recs."""
    _write_py(tmp_path, "service.py", """\
        def process(items):
            result = ""
            for item in items:
                result += str(item)
            return result

        def validate(x):
            pass
    """)

    det = _make_detector(tmp_path)
    result = det.detect()

    valid_categories = set(DebtCategory)
    valid_priorities = set(DebtPriority)
    valid_efforts = set(DebtEffort)
    valid_risks = set(DebtRisk)
    valid_statuses = set(DebtStatus)

    for item in result.items:
        assert item.category in valid_categories, f"Invalid category: {item.category}"
        assert item.priority in valid_priorities, f"Invalid priority: {item.priority}"
        assert item.effort in valid_efforts, f"Invalid effort: {item.effort}"
        assert item.risk in valid_risks, f"Invalid risk: {item.risk}"
        assert item.status in valid_statuses, f"Invalid status: {item.status}"
        assert 0.0 <= item.confidence <= 1.0, f"Confidence out of range: {item.confidence}"
        assert len(item.recommendations) >= 2, (
            f"Item {item.id} has fewer than 2 recommendations: {len(item.recommendations)}"
        )


# ---------------------------------------------------------------------------
# Property 10: Debt analysis cache round-trip
# Feature: code-review-and-debt-tracking, Property 10: Debt analysis cache round-trip
# ---------------------------------------------------------------------------

def test_property10_cache_roundtrip(tmp_path):
    """Serializing and deserializing DebtAnalysisResult preserves item IDs, categories, priorities."""
    _write_py(tmp_path, "app.py", """\
        def run():
            result = ""
            for i in range(100):
                result += str(i)
            return result
    """)

    det = _make_detector(tmp_path)
    original = det.detect()

    # Force cache write
    det._save_cache(original)

    # Load from cache
    loaded = det._load_cache()
    assert loaded is not None, "Cache should be loadable after save"

    orig_ids = {i.id for i in original.items}
    loaded_ids = {i.id for i in loaded.items}
    assert orig_ids == loaded_ids, f"IDs differ after round-trip: {orig_ids ^ loaded_ids}"

    for orig_item in original.items:
        loaded_item = next((i for i in loaded.items if i.id == orig_item.id), None)
        assert loaded_item is not None
        assert loaded_item.category == orig_item.category
        assert loaded_item.priority == orig_item.priority


@given(st.integers(min_value=0, max_value=50))
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
def test_property10_serialize_deserialize_roundtrip(tmp_path, n_items):
    """Serialization round-trip preserves all item IDs for arbitrary item counts."""
    from hiveforge.steering.models import (
        DebtAnalysisResult, DebtItem, DebtMetrics, DebtRecommendation,
    )
    import hashlib

    items = []
    for i in range(n_items):
        loc = f"file_{i}.py:{i + 1}"
        item_id = hashlib.sha256(f"CODE_QUALITY{loc}".encode()).hexdigest()[:12]
        items.append(DebtItem(
            id=item_id,
            category=DebtCategory.CODE_QUALITY,
            description=f"Item {i}",
            location=loc,
            priority=DebtPriority.MEDIUM,
            effort=DebtEffort.LOW,
            risk=DebtRisk.LOW,
            status=DebtStatus.ACTIVE,
            confidence=0.8,
            recommendations=[
                DebtRecommendation("Fix it", "Do the fix", "Some trade-off", True),
                DebtRecommendation("Ignore it", "Leave as-is", "Risk remains", False),
            ],
        ))

    result = DebtAnalysisResult(items=items, sampled=False, analysis_time_s=0.1)
    serialized = _serialize_result(result)
    deserialized = _deserialize_result(serialized)

    assert {i.id for i in result.items} == {i.id for i in deserialized.items}
