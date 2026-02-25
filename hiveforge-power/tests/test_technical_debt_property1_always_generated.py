"""
Property 1: technical-debt.md is always generated during init.

For any valid project root and SteeringConfig (with or without skip_debt_detection),
the init workflow must produce a files_written list that includes technical-debt.md.

Feature: code-review-and-debt-tracking
Property 1: technical-debt.md is always generated during init
Validates: Requirements 1.1, 5.1
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from hiveforge.steering.steering_file_generator import SteeringFileGenerator
from hiveforge.steering.context_assembler import ContextAssembler
from hiveforge.steering.prompt_builder import PromptBuilder
from hiveforge.steering.models import CodeAnalysisFacts, NamingConventions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_generator() -> SteeringFileGenerator:
    """Return a SteeringFileGenerator with a mocked LLM that always succeeds."""
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_llm.complete = AsyncMock(
        return_value="# Steering File\n\n## Section\n\nContent."
    )
    generator = SteeringFileGenerator(mock_llm)
    generator._validate_draft = MagicMock(return_value=[])
    generator._check_duplicate_paragraphs = MagicMock(return_value=[])
    return generator


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


# ---------------------------------------------------------------------------
# Property 1: technical-debt.md always in files_written
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_property1_technical_debt_in_files_written_no_debt_facts(tmp_path):
    """
    technical-debt.md must appear in files_written even when debt_facts=None
    (e.g. skip_debt_detection=True or DebtDetector failed).

    Feature: code-review-and-debt-tracking, Property 1: technical-debt.md is always generated during init
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
async def test_property1_technical_debt_in_files_written_with_debt_facts(tmp_path):
    """
    technical-debt.md must appear in files_written when debt_facts is provided.

    Feature: code-review-and-debt-tracking, Property 1: technical-debt.md is always generated during init
    """
    from hiveforge.steering.models import (
        DebtAnalysisResult, DebtCategory, DebtEffort, DebtItem,
        DebtMetrics, DebtPriority, DebtRecommendation, DebtRisk, DebtStatus,
    )

    debt_item = DebtItem(
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
    debt_facts = DebtAnalysisResult(
        items=[debt_item],
        metrics=DebtMetrics(total_active=1),
        sampled=False,
        analysis_time_s=0.5,
    )

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
        debt_facts=debt_facts,
    )

    assert result.success is True
    assert "technical-debt.md" in result.files_written, (
        f"technical-debt.md missing from files_written: {result.files_written}"
    )
    assert (output_dir / "technical-debt.md").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("use_case", [
    "new_from_docs",
    "new_from_code",
    "drift_correction",
    "update",
])
async def test_property1_technical_debt_generated_for_all_use_cases(tmp_path, use_case):
    """
    technical-debt.md must be generated regardless of the use_case.

    Feature: code-review-and-debt-tracking, Property 1: technical-debt.md is always generated during init
    """
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
    )

    assert result.success is True
    assert "technical-debt.md" in result.files_written, (
        f"technical-debt.md missing for use_case={use_case}: {result.files_written}"
    )
