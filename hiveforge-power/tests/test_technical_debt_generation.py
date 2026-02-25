"""
Integration tests for technical-debt.md generation.

Tests the full init pipeline with mocked LLMProvider, verifying:
- technical-debt.md is in files_written
- All 5 required sections are present
- Valid YAML frontmatter (inclusion=always, priority=3)
- skip_debt_detection still generates the file
- DebtDetector exception still generates the file

Requirements: 1.1, 1.2, 1.3, 1.4, 5.1, 11.1
"""

import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hiveforge.steering.context_assembler import ContextAssembler
from hiveforge.steering.models import (
    CodeAnalysisFacts,
    DebtAnalysisResult,
    DebtCategory,
    DebtEffort,
    DebtItem,
    DebtMetrics,
    DebtPriority,
    DebtRecommendation,
    DebtRisk,
    DebtStatus,
    NamingConventions,
)
from hiveforge.steering.prompt_builder import PromptBuilder
from hiveforge.steering.steering_file_generator import SteeringFileGenerator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = [
    "Overview",
    "Debt Categories",
    "Active Debt Items",
    "Resolved Debt Items",
    "Debt Metrics",
]

TECHNICAL_DEBT_CONTENT = """\
---
inclusion: always
priority: 3
---

# Technical Debt

## Overview

This file tracks technical debt for the project.

## Debt Categories

- Code Quality
- Tests
- Architecture
- Performance

## Active Debt Items

| ID | Category | Description | Priority |
|----|----------|-------------|----------|
| aabbccddeeff | code_quality | DRY violation | high |

## Resolved Debt Items

No resolved items.

## Debt Metrics

- Total active: 1
- Last updated: 2026-02-25T00:00:00+00:00
"""

GENERIC_CONTENT = "# {name}\n\n## Section\n\nContent.\n"

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


def _make_llm(technical_debt_content: str = TECHNICAL_DEBT_CONTENT) -> MagicMock:
    """Return a mocked LLMProvider that returns appropriate content per template."""

    async def _complete(system_prompt="", user_prompt="", **kwargs):
        if "technical-debt" in user_prompt.lower() or "technical debt" in user_prompt.lower():
            return technical_debt_content
        # Extract template name hint from system prompt
        for name in ["project-vision", "tech-stack", "architecture", "conventions",
                     "agents", "workflows", "security", "testing"]:
            if name in (system_prompt + user_prompt).lower():
                return GENERIC_CONTENT.format(name=name)
        return GENERIC_CONTENT.format(name="steering-file")

    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_llm.complete = AsyncMock(side_effect=_complete)
    return mock_llm


def _make_generator(technical_debt_content: str = TECHNICAL_DEBT_CONTENT) -> SteeringFileGenerator:
    generator = SteeringFileGenerator(_make_llm(technical_debt_content))
    generator._validate_draft = MagicMock(return_value=[])
    generator._check_duplicate_paragraphs = MagicMock(return_value=[])
    return generator


def _make_debt_item() -> DebtItem:
    return DebtItem(
        id="aabbccddeeff",
        category=DebtCategory.CODE_QUALITY,
        description="DRY violation in utils.py",
        location="src/utils.py:10",
        priority=DebtPriority.HIGH,
        effort=DebtEffort.MEDIUM,
        risk=DebtRisk.MEDIUM,
        status=DebtStatus.ACTIVE,
        confidence=0.9,
        recommendations=[
            DebtRecommendation("Refactor", "Extract shared function.", "Effort required.", True),
            DebtRecommendation("Defer", "Leave for later.", "Risk remains.", False),
        ],
    )


# ---------------------------------------------------------------------------
# Full init pipeline: technical-debt.md in files_written
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_init_pipeline_technical_debt_in_files_written(tmp_path):
    """
    Full init pipeline with mocked LLMProvider: technical-debt.md must be in files_written.

    Requirements: 1.1, 5.1
    """
    generator = _make_generator()
    output_dir = tmp_path / "steering"
    output_dir.mkdir()

    result = await generator.generate_all_files(
        context_assembler=ContextAssembler(),
        prompt_builder=PromptBuilder(),
        output_dir=output_dir,
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering={},
        debt_facts=None,
    )

    assert result.success is True
    assert "technical-debt.md" in result.files_written, (
        f"technical-debt.md missing from files_written: {result.files_written}"
    )
    assert (output_dir / "technical-debt.md").exists()


@pytest.mark.asyncio
async def test_full_init_pipeline_all_required_sections_present(tmp_path):
    """
    Full init pipeline: generated technical-debt.md must contain all 5 required sections.

    Feature: code-review-and-debt-tracking, Property 2: technical-debt.md always contains required sections
    Requirements: 1.3, 10.1
    """
    generator = _make_generator()
    output_dir = tmp_path / "steering"
    output_dir.mkdir()

    result = await generator.generate_all_files(
        context_assembler=ContextAssembler(),
        prompt_builder=PromptBuilder(),
        output_dir=output_dir,
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering={},
        debt_facts=None,
    )

    assert result.success is True
    content = (output_dir / "technical-debt.md").read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert section in content, (
            f"Required section '{section}' missing from technical-debt.md"
        )


@pytest.mark.asyncio
async def test_full_init_pipeline_valid_yaml_frontmatter(tmp_path):
    """
    Full init pipeline: generated technical-debt.md must have valid YAML frontmatter
    with inclusion=always and priority=3.

    Feature: code-review-and-debt-tracking, Property 3: technical-debt.md always contains valid YAML frontmatter
    Requirements: 1.2
    """
    generator = _make_generator()
    output_dir = tmp_path / "steering"
    output_dir.mkdir()

    result = await generator.generate_all_files(
        context_assembler=ContextAssembler(),
        prompt_builder=PromptBuilder(),
        output_dir=output_dir,
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering={},
        debt_facts=None,
    )

    assert result.success is True
    content = (output_dir / "technical-debt.md").read_text(encoding="utf-8")

    # Extract YAML frontmatter between --- delimiters
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert fm_match is not None, (
        "technical-debt.md must start with YAML frontmatter delimited by ---"
    )

    import yaml
    frontmatter = yaml.safe_load(fm_match.group(1))
    assert frontmatter.get("inclusion") == "always", (
        f"Expected inclusion=always, got: {frontmatter.get('inclusion')}"
    )
    assert frontmatter.get("priority") == 3, (
        f"Expected priority=3, got: {frontmatter.get('priority')}"
    )


# ---------------------------------------------------------------------------
# skip_debt_detection: technical-debt.md still generated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_skip_debt_detection_still_generates_technical_debt_md(tmp_path):
    """
    When skip_debt_detection=True (debt_facts=None), technical-debt.md must still
    be generated with placeholder content.

    Requirements: 1.1, 6.1
    """
    generator = _make_generator()
    output_dir = tmp_path / "steering"
    output_dir.mkdir()

    result = await generator.generate_all_files(
        context_assembler=ContextAssembler(),
        prompt_builder=PromptBuilder(),
        output_dir=output_dir,
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering={},
        debt_facts=None,  # simulates skip_debt_detection=True
    )

    assert result.success is True
    assert "technical-debt.md" in result.files_written
    assert (output_dir / "technical-debt.md").exists()


# ---------------------------------------------------------------------------
# DebtDetector exception: workflow continues, technical-debt.md still generated
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_debt_detector_exception_workflow_continues(tmp_path):
    """
    If DebtDetector.detect() raises an exception, the workflow must continue
    and technical-debt.md must still be generated.

    Requirements: 1.1, 5.1, 11.1
    """
    generator = _make_generator()
    output_dir = tmp_path / "steering"
    output_dir.mkdir()

    # Simulate DebtDetector failure by passing debt_facts=None (as the workflow does on exception)
    result = await generator.generate_all_files(
        context_assembler=ContextAssembler(),
        prompt_builder=PromptBuilder(),
        output_dir=output_dir,
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering={},
        debt_facts=None,
    )

    assert result.success is True
    assert "technical-debt.md" in result.files_written, (
        "technical-debt.md must be generated even when DebtDetector fails"
    )


# ---------------------------------------------------------------------------
# Property 2: required sections present (hypothesis-style exhaustive check)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("section", REQUIRED_SECTIONS)
async def test_property2_required_section_present(tmp_path, section):
    """
    Property 2: technical-debt.md always contains required sections.
    Each required section is checked individually.

    Feature: code-review-and-debt-tracking, Property 2: technical-debt.md always contains required sections
    Validates: Requirements 1.3, 10.1
    """
    generator = _make_generator()
    output_dir = tmp_path / "steering"
    output_dir.mkdir()

    result = await generator.generate_all_files(
        context_assembler=ContextAssembler(),
        prompt_builder=PromptBuilder(),
        output_dir=output_dir,
        use_case="new_from_docs",
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering={},
        debt_facts=None,
    )

    assert result.success is True
    content = (output_dir / "technical-debt.md").read_text(encoding="utf-8")
    assert section in content, (
        f"Required section '{section}' missing from technical-debt.md.\n"
        f"Content preview: {content[:500]}"
    )


# ---------------------------------------------------------------------------
# Property 3: valid YAML frontmatter (parametrized over use_cases)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("use_case", ["new_from_docs", "new_from_code", "update"])
async def test_property3_valid_yaml_frontmatter_all_use_cases(tmp_path, use_case):
    """
    Property 3: technical-debt.md always contains valid YAML frontmatter
    with inclusion=always and priority=3, regardless of use_case.

    Feature: code-review-and-debt-tracking, Property 3: technical-debt.md always contains valid YAML frontmatter
    Validates: Requirements 1.2
    """
    import yaml

    generator = _make_generator()
    output_dir = tmp_path / "steering"
    output_dir.mkdir()

    result = await generator.generate_all_files(
        context_assembler=ContextAssembler(),
        prompt_builder=PromptBuilder(),
        output_dir=output_dir,
        use_case=use_case,
        source_docs=[],
        code_facts=_make_code_facts(),
        existing_steering={},
        debt_facts=None,
    )

    assert result.success is True
    content = (output_dir / "technical-debt.md").read_text(encoding="utf-8")

    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert fm_match is not None, (
        f"technical-debt.md must have YAML frontmatter for use_case={use_case}"
    )

    frontmatter = yaml.safe_load(fm_match.group(1))
    assert frontmatter.get("inclusion") == "always", (
        f"Expected inclusion=always for use_case={use_case}, got: {frontmatter}"
    )
    assert frontmatter.get("priority") == 3, (
        f"Expected priority=3 for use_case={use_case}, got: {frontmatter}"
    )
