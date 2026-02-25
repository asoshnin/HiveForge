"""
Unit tests for DebtReconciler.

Requirements: 4.2, 4.3, 4.4, 4.5, 11.5
"""

from datetime import datetime, timezone

import pytest

from hiveforge.steering.detectors.debt_reconciler import DebtReconciler
from hiveforge.steering.models import (
    DebtAnalysisResult,
    DebtCategory,
    DebtEffort,
    DebtItem,
    DebtMetrics,
    DebtPriority,
    DebtRecommendation,
    DebtRisk,
    DebtStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS = datetime.now(timezone.utc).isoformat()


def _item(
    item_id: str,
    description: str = "Some debt",
    priority: DebtPriority = DebtPriority.MEDIUM,
    detected_at: str | None = _TS,
) -> DebtItem:
    return DebtItem(
        id=item_id,
        category=DebtCategory.CODE_QUALITY,
        description=description,
        location="src/module.py:10",
        priority=priority,
        effort=DebtEffort.LOW,
        risk=DebtRisk.LOW,
        status=DebtStatus.ACTIVE,
        confidence=0.8,
        recommendations=[
            DebtRecommendation("Fix it", "Do the fix.", "Some trade-off.", True),
            DebtRecommendation("Defer", "Leave for later.", "Risk remains.", False),
        ],
        detected_at=detected_at,
    )


def _manual(item_id: str, description: str = "Manual debt") -> DebtItem:
    """Manually added item — no detected_at."""
    return _item(item_id, description, detected_at=None)


def _make_md(active: list[DebtItem], resolved: list[DebtItem] | None = None) -> str:
    resolved = resolved or []
    active_rows = "\n".join(
        f"| {i.id} | {i.description} | {i.priority.value} | {i.effort.value} | "
        f"{i.risk.value} | {i.status.value} | {i.detected_at or ''} |"
        for i in active
    )
    resolved_rows = "\n".join(
        f"| {i.id} | {i.description} | {i.category.value} | {i.resolved_at or ''} |"
        for i in resolved
    )
    lines = [
        "---", "inclusion: always", "priority: 3", "---", "",
        "# Technical Debt", "",
        "## Active Debt Items", "",
        "| ID | Description | Priority | Effort | Risk | Status | Detected At |",
        "|----|-------------|----------|--------|------|--------|-------------|",
    ]
    if active_rows:
        lines.append(active_rows)
    lines += [
        "", "## Resolved Debt Items", "",
        "| ID | Description | Category | Resolved At |",
        "|----|-------------|----------|-------------|",
    ]
    if resolved_rows:
        lines.append(resolved_rows)
    lines += ["", "## Debt Metrics", ""]
    return "\n".join(lines) + "\n"


def _result(items: list[DebtItem]) -> DebtAnalysisResult:
    active = [i for i in items if i.status != DebtStatus.RESOLVED]
    return DebtAnalysisResult(
        items=items,
        metrics=DebtMetrics(total_active=len(active)),
        sampled=False,
        analysis_time_s=0.1,
    )


# ---------------------------------------------------------------------------
# Manual items are preserved after reconcile
# ---------------------------------------------------------------------------

def test_manual_items_preserved():
    """Hand-crafted technical-debt.md with manual items: all preserved after reconcile."""
    auto = _item("aabbccddeeff", "Auto-detected issue")
    manual = _manual("112233445566", "Manual: legacy migration debt")

    content = _make_md([auto, manual])
    fresh = _result([auto])  # fresh analysis only has auto item

    merged = DebtReconciler().reconcile(content, fresh)
    merged_ids = {i.id for i in merged.items}

    assert manual.id in merged_ids, (
        f"Manual item {manual.id} was lost. Merged: {merged_ids}"
    )
    assert auto.id in merged_ids


# ---------------------------------------------------------------------------
# Previously auto-detected item absent from new result: moved to Resolved
# ---------------------------------------------------------------------------

def test_auto_resolved_item_moved_to_resolved():
    """Previously auto-detected item absent from new result is moved to Resolved."""
    prev = _item("deadbeef1234", "DRY violation in utils.py")
    content = _make_md([prev])
    fresh = _result([])  # item no longer detected

    merged = DebtReconciler().reconcile(content, fresh)

    resolved_ids = {i.id for i in merged.resolved_items()}
    assert prev.id in resolved_ids, (
        f"Item {prev.id} should be in resolved_items(), got: {resolved_ids}"
    )

    resolved_item = next(i for i in merged.items if i.id == prev.id)
    assert resolved_item.status == DebtStatus.RESOLVED
    assert resolved_item.resolved_at is not None


# ---------------------------------------------------------------------------
# User-edited description kept over freshly detected value
# ---------------------------------------------------------------------------

def test_user_edited_description_preserved():
    """User-edited description in existing file is kept over freshly detected value."""
    original = _item("aabbccddeeff", "Original description")
    # User edited the description in the file
    edited = _item("aabbccddeeff", "User-edited description")

    content = _make_md([edited])  # file has user-edited version

    # Fresh analysis has the original (auto-detected) description
    fresh_item = _item("aabbccddeeff", "Original description")
    fresh = _result([fresh_item])

    merged = DebtReconciler().reconcile(content, fresh)

    merged_item = next(i for i in merged.items if i.id == "aabbccddeeff")
    assert merged_item.description == "User-edited description", (
        f"Expected user-edited description, got: {merged_item.description!r}"
    )


# ---------------------------------------------------------------------------
# Parse error on existing file: treated as empty, fresh analysis used
# ---------------------------------------------------------------------------

def test_parse_error_treated_as_empty():
    """Parse error on existing file: treated as empty, fresh analysis used."""
    fresh_item = _item("aabbccddeeff", "Fresh item")
    fresh = _result([fresh_item])

    # Completely invalid content
    bad_content = "NOT A VALID MARKDOWN TABLE AT ALL\n\x00\x01\x02"

    merged = DebtReconciler().reconcile(bad_content, fresh)

    # Fresh item should be present
    merged_ids = {i.id for i in merged.items}
    assert fresh_item.id in merged_ids, (
        f"Fresh item should be present after parse error, got: {merged_ids}"
    )


# ---------------------------------------------------------------------------
# Historical resolved items preserved verbatim
# ---------------------------------------------------------------------------

def test_historical_resolved_items_preserved():
    """Historical resolved items from the Resolved section are preserved."""
    resolved_item = DebtItem(
        id="cafebabe1234",
        category=DebtCategory.CODE_QUALITY,
        description="Old resolved issue",
        location="",
        priority=DebtPriority.LOW,
        effort=DebtEffort.LOW,
        risk=DebtRisk.LOW,
        status=DebtStatus.RESOLVED,
        confidence=0.8,
        recommendations=[
            DebtRecommendation("N/A", "Already resolved.", "N/A", True),
            DebtRecommendation("Re-open", "Re-open if regression.", "N/A", False),
        ],
        resolved_at="2026-01-01T00:00:00+00:00",
    )

    content = _make_md(active=[], resolved=[resolved_item])
    fresh = _result([])

    merged = DebtReconciler().reconcile(content, fresh)

    resolved_ids = {i.id for i in merged.resolved_items()}
    assert resolved_item.id in resolved_ids, (
        f"Historical resolved item {resolved_item.id} was lost. Resolved: {resolved_ids}"
    )
