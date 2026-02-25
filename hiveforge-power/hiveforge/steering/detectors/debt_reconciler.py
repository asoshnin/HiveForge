"""
DebtReconciler — merges fresh DebtAnalysisResult with existing technical-debt.md.

Preserves manually added items and user edits while auto-resolving items
that are no longer detected.

Requirements: 4.2, 4.3, 4.4, 4.5, 10.2, 10.3, 11.5
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from ..models import (
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

logger = logging.getLogger(__name__)

# Regex to extract table rows from the Active Debt Items section.
# Matches: | id | description | priority | effort | risk | status | detected_at |
# detected_at column is optional (may be empty or absent in older files).
_TABLE_ROW_RE = re.compile(
    r"^\|\s*([a-f0-9]{12})\s*\|"   # id (12-char hex)
    r"\s*([^|]+?)\s*\|"             # description
    r"\s*([^|]+?)\s*\|"             # priority
    r"\s*([^|]+?)\s*\|"             # effort
    r"\s*([^|]+?)\s*\|"             # risk
    r"\s*([^|]+?)\s*\|"             # status
    r"(?:\s*([^|]*?)\s*\|)?",       # detected_at (optional column)
    re.MULTILINE,
)

# Regex for resolved table rows: | id | description | category | resolved_at |
_RESOLVED_ROW_RE = re.compile(
    r"^\|\s*([a-f0-9]{12})\s*\|"
    r"\s*([^|]+?)\s*\|"
    r"\s*([^|]+?)\s*\|"
    r"\s*([^|]+?)\s*\|",
    re.MULTILINE,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DebtReconciler:
    """
    Merges a fresh DebtAnalysisResult with the existing technical-debt.md,
    preserving manually added items and user edits.

    Requirements: 4.2, 4.3, 4.4, 4.5, 10.2, 10.3, 11.5
    """

    def reconcile(
        self,
        existing_content: str,
        new_result: DebtAnalysisResult,
    ) -> DebtAnalysisResult:
        """
        Return a merged DebtAnalysisResult applying all five reconciliation rules.

        Rules (in priority order):
        1. User-edited items: keep existing description/priority when they differ.
        2. Manually added items: preserve with current status unchanged.
        3. Auto-resolved items: move to Resolved with resolved_at timestamp.
        4. New items: add with status=Active and detected_at timestamp.
        5. Historical resolved items: preserve verbatim from Resolved section.

        Requirements: 4.2, 4.3, 4.4, 4.5, 10.2, 10.3, 11.5
        """
        try:
            existing_active, existing_resolved = self._parse_existing_items(existing_content)
        except Exception as exc:
            logger.warning(
                "DebtReconciler: failed to parse existing technical-debt.md (%s) — "
                "treating as empty and using fresh analysis",
                exc,
            )
            existing_active = []
            existing_resolved = []

        new_items_by_id: Dict[str, DebtItem] = {i.id: i for i in new_result.items}
        existing_active_by_id: Dict[str, DebtItem] = {i.id: i for i in existing_active}
        existing_resolved_by_id: Dict[str, DebtItem] = {i.id: i for i in existing_resolved}

        # IDs that appear in the new analysis (auto-detected this run)
        detected_ids: Set[str] = set(new_items_by_id.keys())

        merged: List[DebtItem] = []

        # --- Rules 1 & 2: process items present in existing active section ---
        for item_id, existing_item in existing_active_by_id.items():
            if item_id in new_items_by_id:
                # Rule 1: user-edited — keep existing description/priority if different
                new_item = new_items_by_id[item_id]
                if (
                    existing_item.description != new_item.description
                    or existing_item.priority != new_item.priority
                ):
                    # Human override wins
                    merged.append(existing_item)
                else:
                    merged.append(new_item)
            else:
                if self._is_manually_added(existing_item, detected_ids):
                    # Rule 2: manually added — preserve as-is
                    merged.append(existing_item)
                else:
                    # Rule 3: auto-resolved — move to Resolved
                    resolved_item = DebtItem(
                        id=existing_item.id,
                        category=existing_item.category,
                        description=existing_item.description,
                        location=existing_item.location,
                        priority=existing_item.priority,
                        effort=existing_item.effort,
                        risk=existing_item.risk,
                        status=DebtStatus.RESOLVED,
                        confidence=existing_item.confidence,
                        recommendations=existing_item.recommendations,
                        detected_at=existing_item.detected_at,
                        resolved_at=_now_iso(),
                    )
                    merged.append(resolved_item)

        # --- Rule 4: new items not in existing active section ---
        for item_id, new_item in new_items_by_id.items():
            if item_id not in existing_active_by_id:
                # Brand-new detection
                new_item.detected_at = new_item.detected_at or _now_iso()
                merged.append(new_item)

        # --- Rule 5: historical resolved items — preserve verbatim ---
        for item_id, resolved_item in existing_resolved_by_id.items():
            # Only add if not already in merged (avoid duplicates)
            if not any(i.id == item_id for i in merged):
                merged.append(resolved_item)

        # Recompute metrics
        active = [i for i in merged if i.status != DebtStatus.RESOLVED]
        by_cat: Dict[str, int] = {}
        by_pri: Dict[str, int] = {}
        for item in active:
            by_cat[item.category.value] = by_cat.get(item.category.value, 0) + 1
            by_pri[item.priority.value] = by_pri.get(item.priority.value, 0) + 1

        metrics = DebtMetrics(
            total_active=len(active),
            by_category=by_cat,
            by_priority=by_pri,
            last_updated=_now_iso(),
        )

        return DebtAnalysisResult(
            items=merged,
            metrics=metrics,
            sampled=new_result.sampled,
            analysis_time_s=new_result.analysis_time_s,
        )

    def _parse_existing_items(
        self, content: str
    ) -> tuple[List[DebtItem], List[DebtItem]]:
        """Extract DebtItem objects from markdown table rows in technical-debt.md.

        Returns (active_items, resolved_items).
        Raises on unrecoverable parse errors.
        """
        active: List[DebtItem] = []
        resolved: List[DebtItem] = []

        # Split into Active and Resolved sections
        resolved_section_match = re.search(
            r"##\s+Resolved Debt Items(.*?)(?=^##|\Z)", content, re.DOTALL | re.MULTILINE
        )
        active_section_match = re.search(
            r"##\s+Active Debt Items(.*?)(?=^##|\Z)", content, re.DOTALL | re.MULTILINE
        )

        if active_section_match:
            active_text = active_section_match.group(1)
            for m in _TABLE_ROW_RE.finditer(active_text):
                item_id = m.group(1)
                description = m.group(2)
                priority_str = m.group(3)
                effort_str = m.group(4)
                risk_str = m.group(5)
                status_str = m.group(6)
                # group(7) is the optional detected_at column; None means column absent
                detected_at_raw = m.group(7)
                detected_at: Optional[str] = None
                if detected_at_raw is not None:
                    val = detected_at_raw.strip()
                    detected_at = val if val else None
                try:
                    item = DebtItem(
                        id=item_id.strip(),
                        category=DebtCategory.CODE_QUALITY,  # category not in active table; default
                        description=description.strip(),
                        location="",
                        priority=_parse_priority(priority_str.strip()),
                        effort=_parse_effort(effort_str.strip()),
                        risk=_parse_risk(risk_str.strip()),
                        status=_parse_status(status_str.strip()),
                        confidence=0.8,
                        recommendations=[
                            DebtRecommendation("Resolve", "Address this item.", "N/A", True),
                            DebtRecommendation("Defer", "Defer to later.", "Risk remains.", False),
                        ],
                        detected_at=detected_at,
                    )
                    active.append(item)
                except (ValueError, KeyError) as exc:
                    logger.warning("Skipping unparseable active row id=%s: %s", item_id, exc)

        if resolved_section_match:
            resolved_text = resolved_section_match.group(1)
            for m in _RESOLVED_ROW_RE.finditer(resolved_text):
                item_id, description, category_str, resolved_at = (
                    m.group(1), m.group(2), m.group(3), m.group(4)
                )
                # Skip header rows
                if item_id.strip().lower() in ("id", "---"):
                    continue
                try:
                    item = DebtItem(
                        id=item_id.strip(),
                        category=_parse_category(category_str.strip()),
                        description=description.strip(),
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
                        resolved_at=resolved_at.strip() or None,
                    )
                    resolved.append(item)
                except (ValueError, KeyError) as exc:
                    logger.warning("Skipping unparseable resolved row id=%s: %s", item_id, exc)

        return active, resolved

    def _is_manually_added(self, item: DebtItem, detected_ids: Set[str]) -> bool:
        """Return True when item was manually added (not auto-detected).

        Heuristic: an item is considered manually added when its ID has never
        appeared in any auto-detection run. We detect this by checking whether
        the item's detected_at field is absent — manually added items typically
        lack a detected_at timestamp since they were not produced by DebtDetector.

        Requirements: 4.4
        """
        # Items without a detected_at were added by hand, not by the detector
        return item.detected_at is None


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_priority(s: str) -> DebtPriority:
    mapping = {v.value.lower(): v for v in DebtPriority}
    return mapping.get(s.lower(), DebtPriority.MEDIUM)


def _parse_effort(s: str) -> DebtEffort:
    mapping = {v.value.lower(): v for v in DebtEffort}
    return mapping.get(s.lower(), DebtEffort.MEDIUM)


def _parse_risk(s: str) -> DebtRisk:
    mapping = {v.value.lower(): v for v in DebtRisk}
    return mapping.get(s.lower(), DebtRisk.MEDIUM)


def _parse_status(s: str) -> DebtStatus:
    mapping = {v.value.lower(): v for v in DebtStatus}
    return mapping.get(s.lower(), DebtStatus.ACTIVE)


def _parse_category(s: str) -> DebtCategory:
    mapping = {v.value.lower(): v for v in DebtCategory}
    return mapping.get(s.lower(), DebtCategory.CODE_QUALITY)
