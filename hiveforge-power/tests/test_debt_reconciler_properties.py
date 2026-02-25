"""
Property-based tests for DebtReconciler.

Feature: code-review-and-debt-tracking
Properties covered:
  Property 7: Manual debt items survive an update cycle
  Property 8: Auto-resolved items are moved, not deleted
"""

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st
from datetime import datetime, timezone

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

def _make_item(
    item_id: str,
    description: str = "Some debt",
    status: DebtStatus = DebtStatus.ACTIVE,
    priority: DebtPriority = DebtPriority.MEDIUM,
    detected_at: str | None = datetime.now(timezone.utc).isoformat(),
) -> DebtItem:
    return DebtItem(
        id=item_id,
        category=DebtCategory.CODE_QUALITY,
        description=description,
        location="src/module.py:10",
        priority=priority,
        effort=DebtEffort.LOW,
        risk=DebtRisk.LOW,
        status=status,
        confidence=0.8,
        recommendations=[
            DebtRecommendation("Fix it", "Do the fix.", "Some trade-off.", True),
            DebtRecommendation("Defer", "Leave for later.", "Risk remains.", False),
        ],
        detected_at=detected_at,
    )


def _make_manual_item(item_id: str, description: str = "Manual debt") -> DebtItem:
    """Create a manually-added item (no detected_at timestamp)."""
    return _make_item(item_id, description, detected_at=None)


def _make_technical_debt_md(active_items: list[DebtItem], resolved_items: list[DebtItem] = None) -> str:
    """Build a minimal technical-debt.md with the given items in table format."""
    resolved_items = resolved_items or []

    active_rows = "\n".join(
        f"| {i.id} | {i.description} | {i.priority.value} | {i.effort.value} | {i.risk.value} | {i.status.value} | {i.detected_at or ''} |"
        for i in active_items
    )
    resolved_rows = "\n".join(
        f"| {i.id} | {i.description} | {i.category.value} | {i.resolved_at or ''} |"
        for i in resolved_items
    )

    lines = [
        "---",
        "inclusion: always",
        "priority: 3",
        "---",
        "",
        "# Technical Debt",
        "",
        "## Overview",
        "",
        "Some overview text.",
        "",
        "## Debt Categories",
        "",
        "Four categories.",
        "",
        "## Active Debt Items",
        "",
        "| ID | Description | Priority | Effort | Risk | Status | Detected At |",
        "|----|-------------|----------|--------|------|--------|-------------|",
    ]
    if active_rows:
        lines.append(active_rows)
    lines += [
        "",
        "## Resolved Debt Items",
        "",
        "| ID | Description | Category | Resolved At |",
        "|----|-------------|----------|-------------|",
    ]
    if resolved_rows:
        lines.append(resolved_rows)
    lines += [
        "",
        "## Debt Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Active Items | {len(active_items)} |",
    ]
    return "\n".join(lines) + "\n"


def _make_result(items: list[DebtItem]) -> DebtAnalysisResult:
    active = [i for i in items if i.status != DebtStatus.RESOLVED]
    return DebtAnalysisResult(
        items=items,
        metrics=DebtMetrics(total_active=len(active)),
        sampled=False,
        analysis_time_s=0.1,
    )


# ---------------------------------------------------------------------------
# Property 7: Manual debt items survive an update cycle
# Feature: code-review-and-debt-tracking, Property 7: Manual debt items survive an update cycle
# ---------------------------------------------------------------------------

def test_property7_manual_items_preserved():
    """Manually added items (IDs absent from fresh analysis) must survive reconcile()."""
    # Auto-detected item (will be in fresh analysis)
    auto_item = _make_item("aabbccddeeff", "Auto-detected DRY violation")
    # Manually added item (will NOT be in fresh analysis, no detected_at)
    manual_item = _make_manual_item("112233445566", "Manual: tech debt from legacy migration")

    existing_content = _make_technical_debt_md([auto_item, manual_item])

    # Fresh analysis only contains the auto-detected item
    fresh_result = _make_result([auto_item])

    reconciler = DebtReconciler()
    merged = reconciler.reconcile(existing_content, fresh_result)

    merged_ids = {i.id for i in merged.items}
    assert manual_item.id in merged_ids, (
        f"Manual item {manual_item.id} was lost after reconcile. "
        f"Merged IDs: {merged_ids}"
    )


@given(
    n_manual=st.integers(min_value=1, max_value=5),
    n_auto=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property7_manual_items_preserved_parametric(n_manual, n_auto):
    """All manually added items survive reconcile() regardless of how many there are."""
    import hashlib

    def _id(prefix: str, i: int) -> str:
        return hashlib.sha256(f"{prefix}{i}".encode()).hexdigest()[:12]

    manual_items = [_make_manual_item(_id("manual", i), f"Manual item {i}") for i in range(n_manual)]
    auto_items = [_make_item(_id("auto", i), f"Auto item {i}") for i in range(n_auto)]

    existing_content = _make_technical_debt_md(manual_items + auto_items)

    # Fresh analysis only contains auto items
    fresh_result = _make_result(auto_items)

    reconciler = DebtReconciler()
    merged = reconciler.reconcile(existing_content, fresh_result)

    merged_ids = {i.id for i in merged.items}
    for manual_item in manual_items:
        assert manual_item.id in merged_ids, (
            f"Manual item {manual_item.id} was lost. Merged IDs: {merged_ids}"
        )


# ---------------------------------------------------------------------------
# Property 8: Auto-resolved items are moved, not deleted
# Feature: code-review-and-debt-tracking, Property 8: Auto-resolved items are moved, not deleted
# ---------------------------------------------------------------------------

def test_property8_auto_resolved_moved_not_deleted():
    """Previously detected item absent from new analysis must appear in resolved_items()."""
    previously_detected = _make_item("deadbeef1234", "DRY violation in utils.py")
    existing_content = _make_technical_debt_md([previously_detected])

    # Fresh analysis does NOT contain the previously detected item
    fresh_result = _make_result([])

    reconciler = DebtReconciler()
    merged = reconciler.reconcile(existing_content, fresh_result)

    resolved_ids = {i.id for i in merged.resolved_items()}
    assert previously_detected.id in resolved_ids, (
        f"Auto-resolved item {previously_detected.id} was deleted instead of moved to Resolved. "
        f"Resolved IDs: {resolved_ids}"
    )

    # Verify status is RESOLVED
    resolved_item = next(i for i in merged.items if i.id == previously_detected.id)
    assert resolved_item.status == DebtStatus.RESOLVED, (
        f"Expected RESOLVED status, got {resolved_item.status}"
    )
    assert resolved_item.resolved_at is not None, "resolved_at should be set"


@given(n_items=st.integers(min_value=1, max_value=10))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_property8_auto_resolved_parametric(n_items):
    """All previously detected items absent from new analysis appear in resolved_items()."""
    import hashlib

    def _id(i: int) -> str:
        return hashlib.sha256(f"prev{i}".encode()).hexdigest()[:12]

    prev_items = [_make_item(_id(i), f"Previously detected item {i}") for i in range(n_items)]
    existing_content = _make_technical_debt_md(prev_items)

    # Fresh analysis is empty
    fresh_result = _make_result([])

    reconciler = DebtReconciler()
    merged = reconciler.reconcile(existing_content, fresh_result)

    resolved_ids = {i.id for i in merged.resolved_items()}
    for item in prev_items:
        assert item.id in resolved_ids, (
            f"Item {item.id} was deleted instead of moved to Resolved"
        )
