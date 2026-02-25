"""
Property 9: Atomic write guarantee holds for 9 files.

If any single file (including technical-debt.md) fails validation,
GenerationResult.files_written must be empty and no files written to disk.

Feature: code-review-and-debt-tracking
Property 9: Atomic write guarantee holds for 9 files
Validates: Requirements 5.4
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from hiveforge.steering.steering_file_generator import GENERATION_ORDER, SteeringFileGenerator
from hiveforge.steering.context_assembler import ContextAssembler
from hiveforge.steering.prompt_builder import PromptBuilder
from hiveforge.steering.models import CodeAnalysisFacts, NamingConventions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_generator(fail_on: str | None = None) -> SteeringFileGenerator:
    """Return a SteeringFileGenerator whose LLM always returns a valid draft.

    If *fail_on* is set, _validate_draft returns an error for that template.
    """
    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_llm.complete = AsyncMock(
        return_value="# Steering File\n\n## Section\n\nContent."
    )

    generator = SteeringFileGenerator(mock_llm)

    if fail_on:
        def _validate(template_name, draft, code_facts):
            if template_name == fail_on:
                return [f"Injected validation error for {template_name}"]
            return []
        generator._validate_draft = MagicMock(side_effect=_validate)
    else:
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
# Property 9: GENERATION_ORDER has exactly 9 entries
# ---------------------------------------------------------------------------

def test_property9_generation_order_has_9_files():
    """GENERATION_ORDER must contain exactly 9 entries including technical-debt.md."""
    # Feature: code-review-and-debt-tracking, Property 9: Atomic write guarantee holds for 9 files
    assert len(GENERATION_ORDER) == 9, (
        f"Expected 9 files in GENERATION_ORDER, got {len(GENERATION_ORDER)}: {GENERATION_ORDER}"
    )
    assert "technical-debt.md" in GENERATION_ORDER, (
        "technical-debt.md must be in GENERATION_ORDER"
    )
    assert GENERATION_ORDER[-1] == "technical-debt.md", (
        "technical-debt.md must be the last entry (position 9)"
    )


# ---------------------------------------------------------------------------
# Property 9: All 9 files written on success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_property9_all_9_files_written_on_success(tmp_path):
    """When all drafts pass validation, exactly 9 files are written to disk."""
    # Feature: code-review-and-debt-tracking, Property 9: Atomic write guarantee holds for 9 files
    generator = _make_generator(fail_on=None)
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
    )

    assert result.success is True
    assert len(result.files_written) == 9, (
        f"Expected 9 files written, got {len(result.files_written)}: {result.files_written}"
    )
    assert "technical-debt.md" in result.files_written

    for name in GENERATION_ORDER:
        assert (output_dir / name).exists(), f"{name} missing from disk"


# ---------------------------------------------------------------------------
# Property 9: Zero files written when technical-debt.md fails validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_property9_zero_files_when_technical_debt_fails(tmp_path):
    """If technical-debt.md fails validation, no files are written to disk."""
    # Feature: code-review-and-debt-tracking, Property 9: Atomic write guarantee holds for 9 files
    generator = _make_generator(fail_on="technical-debt.md")
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
    )

    assert result.success is False
    assert result.files_written == [], (
        f"Expected no files written, got: {result.files_written}"
    )
    # Verify nothing on disk
    written = list(output_dir.iterdir())
    assert written == [], f"Expected empty output dir, found: {written}"


# ---------------------------------------------------------------------------
# Property 9: Zero files written when any of the 9 files fails validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("fail_on", GENERATION_ORDER)
async def test_property9_zero_files_when_any_file_fails(tmp_path, fail_on):
    """For each of the 9 files, a validation failure must result in zero files written."""
    # Feature: code-review-and-debt-tracking, Property 9: Atomic write guarantee holds for 9 files
    generator = _make_generator(fail_on=fail_on)
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
    )

    assert result.success is False, f"Expected failure when {fail_on} fails validation"
    assert result.files_written == [], (
        f"Expected no files written when {fail_on} fails, got: {result.files_written}"
    )
    written = list(output_dir.iterdir())
    assert written == [], (
        f"Expected empty output dir when {fail_on} fails, found: {[f.name for f in written]}"
    )
