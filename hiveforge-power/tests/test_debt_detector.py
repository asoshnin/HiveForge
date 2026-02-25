"""
Unit tests for DebtDetector.

Requirements: 2.1, 2.2, 2.3, 2.4, 11.2, 11.4
"""

import json
import textwrap
from pathlib import Path

import pytest

from hiveforge.steering.detectors.debt_detector import DebtDetector
from hiveforge.steering.models import DebtAnalysisResult, DebtCategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_detector(tmp_path: Path, conventions: str = "") -> DebtDetector:
    return DebtDetector(project_root=tmp_path, conventions_content=conventions)


def _write(tmp_path: Path, rel: str, content: str) -> Path:
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _make_item_id: stable for identical inputs
# ---------------------------------------------------------------------------

def test_make_item_id_stable():
    """_make_item_id produces identical output for identical inputs."""
    d = DebtDetector.__new__(DebtDetector)
    id1 = d._make_item_id(DebtCategory.CODE_QUALITY, "src/utils.py:10")
    id2 = d._make_item_id(DebtCategory.CODE_QUALITY, "src/utils.py:10")
    assert id1 == id2
    assert len(id1) == 12
    assert all(c in "0123456789abcdef" for c in id1)


def test_make_item_id_differs_for_different_inputs():
    """_make_item_id produces different IDs for different inputs."""
    d = DebtDetector.__new__(DebtDetector)
    id1 = d._make_item_id(DebtCategory.CODE_QUALITY, "src/a.py:1")
    id2 = d._make_item_id(DebtCategory.TESTS, "src/a.py:1")
    id3 = d._make_item_id(DebtCategory.CODE_QUALITY, "src/b.py:1")
    assert id1 != id2
    assert id1 != id3
    assert id2 != id3


# ---------------------------------------------------------------------------
# Empty codebase: zero items, no exceptions
# ---------------------------------------------------------------------------

def test_empty_codebase_produces_zero_items(tmp_path):
    """Empty codebase produces DebtAnalysisResult with zero items and no exceptions."""
    detector = _make_detector(tmp_path)
    result = detector.detect()
    assert isinstance(result, DebtAnalysisResult)
    assert result.items == []
    assert result.metrics.total_active == 0


# ---------------------------------------------------------------------------
# Unparseable .py file: skipped without raising
# ---------------------------------------------------------------------------

def test_unparseable_py_file_skipped(tmp_path):
    """Unparseable .py file is skipped without raising an exception."""
    _write(tmp_path, "src/broken.py", "def foo(\n  # unclosed paren\n")
    detector = _make_detector(tmp_path)
    # Should not raise
    result = detector.detect()
    assert isinstance(result, DebtAnalysisResult)


# ---------------------------------------------------------------------------
# DRY violation detection
# ---------------------------------------------------------------------------

def test_dry_violation_detected(tmp_path):
    """Two files with identical function bodies produce a CODE_QUALITY DebtItem."""
    body = "\n".join(f"    x_{i} = {i}" for i in range(15))
    func = f"def compute():\n{body}\n    return x_0\n"

    _write(tmp_path, "src/module_a.py", func)
    _write(tmp_path, "src/module_b.py", func)

    detector = _make_detector(tmp_path)
    result = detector.detect()

    dry_items = [i for i in result.items if i.category == DebtCategory.CODE_QUALITY]
    assert len(dry_items) >= 1, (
        f"Expected at least one CODE_QUALITY item for DRY violation, got: {result.items}"
    )


# ---------------------------------------------------------------------------
# Test gap detection
# ---------------------------------------------------------------------------

def test_test_gap_detected_for_missing_test_file(tmp_path):
    """Missing test file for a module with public functions produces a TESTS DebtItem."""
    _write(tmp_path, "src/calculator.py", textwrap.dedent("""\
        def add(a, b):
            return a + b

        def subtract(a, b):
            return a - b
    """))
    # No test_calculator.py

    detector = _make_detector(tmp_path)
    result = detector.detect()

    test_items = [i for i in result.items if i.category == DebtCategory.TESTS]
    assert len(test_items) >= 1, (
        f"Expected at least one TESTS item for missing test file, got: {result.items}"
    )


# ---------------------------------------------------------------------------
# Architecture smell: circular import detection
# ---------------------------------------------------------------------------

def test_architecture_smell_detected_for_cycle(tmp_path):
    """Circular imports between two modules produce an ARCHITECTURE DebtItem."""
    # Place modules at top level so their module names are "alpha" and "beta".
    # The import graph uses the first segment of each imported module name, so
    # "import beta" from alpha.py creates edge alpha -> beta, and vice versa.
    _write(tmp_path, "alpha.py", "import beta\n")
    _write(tmp_path, "beta.py", "import alpha\n")

    detector = _make_detector(tmp_path)
    result = detector.detect()

    arch_items = [i for i in result.items if i.category == DebtCategory.ARCHITECTURE]
    assert len(arch_items) >= 1, (
        f"Expected at least one ARCHITECTURE item for circular import, got: {result.items}"
    )


# ---------------------------------------------------------------------------
# Performance risk detection
# ---------------------------------------------------------------------------

def test_performance_risk_detected_for_n_plus_one(tmp_path):
    """N+1 query pattern in a loop produces a PERFORMANCE DebtItem."""
    _write(tmp_path, "src/views.py", textwrap.dedent("""\
        def get_users(db):
            users = db.query('SELECT * FROM users')
            for user in users:
                orders = db.query('SELECT * FROM orders WHERE user_id = ' + str(user.id))
            return users
    """))

    detector = _make_detector(tmp_path)
    result = detector.detect()

    perf_items = [i for i in result.items if i.category == DebtCategory.PERFORMANCE]
    assert len(perf_items) >= 1, (
        f"Expected at least one PERFORMANCE item for N+1 pattern, got: {result.items}"
    )


# ---------------------------------------------------------------------------
# Each DebtItem has >= 2 recommendations
# ---------------------------------------------------------------------------

def test_each_item_has_two_recommendations(tmp_path):
    """Every DebtItem produced by detect() has at least 2 recommendations."""
    body = "\n".join(f"    x_{i} = {i}" for i in range(15))
    func = f"def compute():\n{body}\n    return x_0\n"
    _write(tmp_path, "src/a.py", func)
    _write(tmp_path, "src/b.py", func)

    detector = _make_detector(tmp_path)
    result = detector.detect()

    for item in result.items:
        assert len(item.recommendations) >= 2, (
            f"Item {item.id} has only {len(item.recommendations)} recommendations"
        )


# ---------------------------------------------------------------------------
# to_json_dict fits within 1000 tokens (≈4000 chars)
# ---------------------------------------------------------------------------

def test_to_json_dict_fits_within_token_budget(tmp_path):
    """to_json_dict() output fits within 1000 tokens (≈4000 characters)."""
    body = "\n".join(f"    x_{i} = {i}" for i in range(15))
    func = f"def compute():\n{body}\n    return x_0\n"
    _write(tmp_path, "src/a.py", func)
    _write(tmp_path, "src/b.py", func)

    detector = _make_detector(tmp_path)
    result = detector.detect()

    json_str = json.dumps(result.to_json_dict())
    # 1 token ≈ 4 chars; 1000 tokens ≈ 4000 chars
    assert len(json_str) <= 4000, (
        f"to_json_dict() output is {len(json_str)} chars, exceeds 4000-char budget"
    )
