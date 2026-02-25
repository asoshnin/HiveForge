"""
Property 11: Context assembly includes cross-reference steering files.

For any call to ContextAssembler.assemble() with template_name="technical-debt.md"
and existing_steering containing conventions.md, qa-standards.md, architecture.md,
the returned context must include all three.

Feature: code-review-and-debt-tracking
Property 11: Context assembly includes cross-reference steering files
Validates: Requirements 9.1
"""

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from hiveforge.steering.context_assembler import ContextAssembler
from hiveforge.steering.models import CodeAnalysisFacts, NamingConventions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_code_facts() -> CodeAnalysisFacts:
    return CodeAnalysisFacts(
        primary_language="Python 3.11",
        frameworks=[],
        dependencies=[],
        architecture_pattern="custom",
        has_tests=False,
        test_framework=None,
        api_type=None,
        database=None,
        entry_points=[],
        naming_conventions=NamingConventions(),
        directory_structure="",
    )


CROSS_REF_FILES = {"conventions.md", "qa-standards.md", "architecture.md"}


# ---------------------------------------------------------------------------
# Property 11: deterministic test
# ---------------------------------------------------------------------------

def test_property11_cross_ref_files_included_in_context():
    """
    ContextAssembler.assemble() for technical-debt.md must include
    conventions.md, qa-standards.md, and architecture.md in the returned context.

    Feature: code-review-and-debt-tracking, Property 11: Context assembly includes cross-reference steering files
    """
    assembler = ContextAssembler()

    existing_steering = {
        "conventions.md": "# Conventions\n\nSome conventions.",
        "qa-standards.md": "# QA Standards\n\nSome QA standards.",
        "architecture.md": "# Architecture\n\nSome architecture.",
        "project-vision.md": "# Vision\n\nSome vision.",
    }

    ctx = assembler.assemble(
        template_name="technical-debt.md",
        template_schema=["Overview", "Debt Categories", "Active Debt Items",
                         "Resolved Debt Items", "Debt Metrics"],
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering=existing_steering,
        previously_generated={},
        delta=None,
        user_intent=None,
    )

    for key in CROSS_REF_FILES:
        assert key in ctx.existing_steering, (
            f"Expected '{key}' in context.existing_steering for technical-debt.md, "
            f"got keys: {list(ctx.existing_steering.keys())}"
        )


def test_property11_cross_ref_files_not_injected_for_other_templates():
    """
    Cross-reference injection must NOT alter context for non-technical-debt templates.
    Only the files present in existing_steering should appear.
    """
    assembler = ContextAssembler()

    existing_steering = {
        "conventions.md": "# Conventions\n\nSome conventions.",
    }

    ctx = assembler.assemble(
        template_name="testing.md",
        template_schema=["Testing Strategy"],
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering=existing_steering,
        previously_generated={},
        delta=None,
        user_intent=None,
    )

    # qa-standards.md and architecture.md were not in existing_steering
    assert "qa-standards.md" not in ctx.existing_steering
    assert "architecture.md" not in ctx.existing_steering


def test_property11_cross_ref_from_previously_generated():
    """
    Cross-reference files available in previously_generated (not existing_steering)
    must also be included in context for technical-debt.md.
    """
    assembler = ContextAssembler()

    # conventions.md only in previously_generated, not existing_steering
    ctx = assembler.assemble(
        template_name="technical-debt.md",
        template_schema=["Overview"],
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering={
            "qa-standards.md": "# QA\n\nStandards.",
            "architecture.md": "# Arch\n\nDiagram.",
        },
        previously_generated={
            "conventions.md": "# Conventions\n\nGenerated conventions.",
        },
        delta=None,
        user_intent=None,
    )

    assert "conventions.md" in ctx.existing_steering, (
        "conventions.md from previously_generated must appear in context for technical-debt.md"
    )


# ---------------------------------------------------------------------------
# Property 11: parametric — any subset of cross-ref files present must be included
# ---------------------------------------------------------------------------

@given(
    present=st.frozensets(
        st.sampled_from(sorted(CROSS_REF_FILES)),
        min_size=1,
        max_size=3,
    )
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
def test_property11_parametric_cross_ref_subset(present):
    """
    Whatever subset of cross-ref files is in existing_steering,
    all of them must appear in the assembled context for technical-debt.md.
    """
    assembler = ContextAssembler()

    existing_steering = {key: f"# {key}\n\nContent." for key in present}

    ctx = assembler.assemble(
        template_name="technical-debt.md",
        template_schema=["Overview"],
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering=existing_steering,
        previously_generated={},
        delta=None,
        user_intent=None,
    )

    for key in present:
        assert key in ctx.existing_steering, (
            f"'{key}' was in existing_steering but missing from assembled context. "
            f"Context keys: {list(ctx.existing_steering.keys())}"
        )
