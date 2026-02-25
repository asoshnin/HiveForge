"""
SteeringFileGenerator — transactional orchestration of all 8 steering files.

All 8 files are generated in memory first; if every draft passes validation
they are written atomically to disk. Any failure discards all drafts and
returns GenerationResult(success=False).

Generation order (fixed, so each file can receive rolling summaries):
  1. project-vision.md
  2. tech-stack.md
  3. architecture.md
  4. conventions.md
  5. agents.md
  6. workflows.md
  7. security.md
  8. testing.md

Requirements: 1.1, 1.2, 1.3, 5.1, 5.2, 5.3, 5.4, 5.5,
              6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.3, 8.4, 10.5
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .context_assembler import ContextAssembler, _rolling_summary
from .models import (
    CodeAnalysisFacts,
    DebtAnalysisResult,
    DeltaReport,
    GenerationContext,
    GenerationResult,
    LLMUnavailableError,
    ParsedDocument,
    UseCase,
)
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

# Fixed generation order (Requirement 5.4)
GENERATION_ORDER: List[str] = [
    "project-vision.md",
    "tech-stack.md",
    "architecture.md",
    "conventions.md",
    "agents.md",
    "workflows.md",
    "security.md",
    "testing.md",
    "technical-debt.md",
]


class SteeringFileGenerator:
    """
    Orchestrates transactional generation of all 8 steering files.

    Requirements: 1.1, 1.2, 1.3, 5.1-5.5, 6.1-6.6, 8.3, 8.4, 10.5
    """

    def __init__(self, llm_provider) -> None:
        """
        Args:
            llm_provider: LLMProvider instance.

        Raises:
            LLMUnavailableError: If llm_provider.is_available() returns False.

        Requirements: 1.2, 8.2, 8.4
        """
        if not llm_provider.is_available():
            raise LLMUnavailableError(
                "No LLM provider is configured. "
                "Run `hiveforge config llm` to set one up, or use KIRO MCP mode."
            )
        self._llm = llm_provider

    async def generate_all_files(
        self,
        context_assembler: ContextAssembler,
        prompt_builder: PromptBuilder,
        output_dir: Path,
        *,
        use_case: UseCase,
        source_docs: List[ParsedDocument],
        code_facts: CodeAnalysisFacts,
        existing_steering: Dict[str, str],
        delta: Optional[DeltaReport] = None,
        user_intent: Optional[str] = None,
        template_contents: Optional[Dict[str, str]] = None,
        debt_facts: Optional[DebtAnalysisResult] = None,
    ) -> GenerationResult:
        """
        Generate all 8 steering files in memory, validate, then write atomically.

        Steps:
        1. Generate all 8 files in memory in fixed sequential order.
        2. Validate each draft (hallucination detection + duplicate paragraphs).
        3. If all pass: write all files to output_dir atomically.
        4. If any fail: discard all drafts, return GenerationResult(success=False).

        Args:
            context_assembler: ContextAssembler instance.
            prompt_builder:    PromptBuilder instance.
            output_dir:        Directory to write steering files into.
            use_case:          Determined use case from InputResolver.
            source_docs:       Parsed source documents.
            code_facts:        Structured code analysis facts.
            existing_steering: Existing steering file contents keyed by filename.
            delta:             DeltaReport (required for drift_correction / update).
            user_intent:       Optional user intent string.
            template_contents: Optional dict of template_name → template Markdown.
                               When None, empty templates are used.
            debt_facts:        Optional DebtAnalysisResult from DebtDetector.
                               Passed to ContextAssembler when generating technical-debt.md.

        Returns:
            GenerationResult with success flag, files_written, validation_errors.

        Requirements: 1.1, 5.1, 5.2, 5.3, 5.4, 5.5
        """
        if template_contents is None:
            template_contents = {}

        drafts: Dict[str, str] = {}
        previously_generated: Dict[str, str] = {}
        all_validation_errors: List[str] = []

        for template_name in GENERATION_ORDER:
            template_content = template_contents.get(template_name, f"# {template_name}\n")

            # Assemble context (includes rolling summaries of already-generated files)
            context = context_assembler.assemble(
                template_name=template_name,
                template_schema=self._schema_sections(template_name),
                use_case=use_case,
                source_docs=source_docs,
                code_facts=code_facts,
                existing_steering=existing_steering,
                previously_generated=previously_generated,
                delta=delta,
                user_intent=user_intent,
                debt_facts=debt_facts if template_name == "technical-debt.md" else None,
            )

            # Generate draft via LLM (with one simplified retry on empty/malformed)
            draft, gen_errors = await self._generate_draft(
                template_name, template_content, context, prompt_builder
            )

            if gen_errors:
                all_validation_errors.extend(gen_errors)
                logger.error("Generation failed for %s: %s", template_name, gen_errors)
                return GenerationResult(
                    success=False,
                    files_written=[],
                    validation_errors=all_validation_errors,
                )

            # Validate draft
            val_errors = self._validate_draft(template_name, draft, code_facts)
            val_errors += self._check_duplicate_paragraphs(draft)

            if val_errors:
                all_validation_errors.extend(
                    [f"{template_name}: {e}" for e in val_errors]
                )
                logger.error("Validation failed for %s: %s", template_name, val_errors)
                return GenerationResult(
                    success=False,
                    files_written=[],
                    validation_errors=all_validation_errors,
                )

            drafts[template_name] = draft
            # Store rolling summary for subsequent templates (Requirement 5.4)
            previously_generated[template_name] = _rolling_summary(draft)
            logger.info("Generated and validated: %s", template_name)

        # All 8 drafts passed — atomic write (Requirements 5.1, 5.2)
        output_dir.mkdir(parents=True, exist_ok=True)
        files_written: List[str] = []
        for name, content in drafts.items():
            dest = output_dir / name
            dest.write_text(content, encoding="utf-8")
            files_written.append(name)
            logger.info("Written: %s", dest)

        return GenerationResult(
            success=True,
            files_written=files_written,
            validation_errors=[],
        )

    # ------------------------------------------------------------------
    # Draft generation
    # ------------------------------------------------------------------

    async def _generate_draft(
        self,
        template_name: str,
        template_content: str,
        context: GenerationContext,
        prompt_builder: PromptBuilder,
    ) -> Tuple[str, List[str]]:
        """
        Call LLM to generate a draft. Retry once with simplified prompt on
        empty or malformed response. Never retry on hallucination errors.

        Returns:
            (draft_text, error_list)  — error_list is empty on success.

        Requirements: 1.1, 1.3, 6.5
        """
        system_prompt, user_prompt = prompt_builder.build(
            template_name, template_content, context
        )

        response = await self._llm.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000,
            temperature=0.2,
        )

        if self._is_empty_or_malformed(response):
            logger.warning(
                "%s: empty/malformed response — retrying with simplified prompt",
                template_name,
            )
            system_prompt, user_prompt = prompt_builder.build_simplified(
                template_name, template_content, context
            )
            response = await self._llm.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=3000,
                temperature=0.2,
            )

            if self._is_empty_or_malformed(response):
                return "", [
                    f"LLM returned empty/malformed response after simplified retry "
                    f"for {template_name}"
                ]

        return response, []

    def _is_empty_or_malformed(self, response: Optional[str]) -> bool:
        """Return True if response is None, empty, or lacks any Markdown heading."""
        if not response or not response.strip():
            return True
        # A valid steering file must have at least one Markdown heading
        return not re.search(r"^#{1,6}\s+\S", response, re.MULTILINE)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_draft(
        self,
        template_name: str,
        draft: str,
        code_facts: CodeAnalysisFacts,
    ) -> List[str]:
        """
        Deterministic string-matching hallucination detection.

        Checks database name and backend framework against CodeAnalysisFacts.
        Returns a list of validation errors (empty = pass).

        Requirements: 6.1, 6.2, 6.3
        """
        errors: List[str] = []
        draft_lower = draft.lower()

        # Only validate tech-stack.md for factual contradictions (most likely file)
        if template_name not in ("tech-stack.md", "architecture.md"):
            return errors

        # Database contradiction check (Requirement 6.2)
        if code_facts.database:
            expected_db = code_facts.database.lower()
            # Common database names to check for contradictions
            known_databases = {
                "postgresql", "postgres", "mysql", "sqlite", "mongodb",
                "redis", "cassandra", "dynamodb", "mssql", "oracle",
            }
            for db in known_databases:
                if db == expected_db:
                    continue
                if db in draft_lower and expected_db not in draft_lower:
                    errors.append(
                        f"Hallucination detected: draft mentions '{db}' but "
                        f"CodeAnalysisFacts specifies database='{code_facts.database}'"
                    )

        # Backend framework contradiction check (Requirement 6.3)
        if code_facts.frameworks:
            expected_frameworks = {f.lower() for f in code_facts.frameworks}
            known_frameworks = {
                "django", "flask", "fastapi", "express", "spring", "rails",
                "laravel", "nestjs", "gin", "fiber", "actix", "rocket",
            }
            for fw in known_frameworks:
                if fw in expected_frameworks:
                    continue
                if fw in draft_lower:
                    # Only flag if none of the expected frameworks appear
                    if not any(ef in draft_lower for ef in expected_frameworks):
                        errors.append(
                            f"Hallucination detected: draft mentions '{fw}' but "
                            f"CodeAnalysisFacts specifies frameworks={code_facts.frameworks}"
                        )

        return errors

    def _check_duplicate_paragraphs(self, draft: str) -> List[str]:
        """
        Detect verbatim paragraph duplication across sections.

        Returns a list of validation errors (empty = pass).

        Requirements: 10.5
        """
        errors: List[str] = []
        # Split on double newlines to get paragraphs; ignore very short ones
        paragraphs = [
            p.strip() for p in draft.split("\n\n")
            if len(p.strip()) > 80  # ignore headings and short lines
        ]

        seen: Dict[str, int] = {}
        for idx, para in enumerate(paragraphs):
            if para in seen:
                errors.append(
                    f"Duplicate paragraph detected (first at paragraph {seen[para]}, "
                    f"repeated at paragraph {idx}): "
                    f'"{para[:60]}..."'
                )
            else:
                seen[para] = idx

        return errors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _schema_sections(self, template_name: str) -> List[str]:
        """Return a minimal list of expected section names for a template."""
        _schemas: Dict[str, List[str]] = {
            "project-vision.md": [
                "Elevator Pitch", "Problem Statement", "Solution Overview",
                "Target Users", "Success Metrics", "Non-Goals", "Constraints",
            ],
            "tech-stack.md": [
                "Backend", "Frontend", "Database", "Infrastructure",
                "Key Dependencies", "Rationale",
            ],
            "architecture.md": [
                "System Diagram", "Component Responsibilities", "Data Flow",
                "Key Decisions", "Scalability",
            ],
            "conventions.md": [
                "General Principles", "Naming Conventions", "Code Style",
                "Testing", "Git Conventions",
            ],
            "agents.md": [
                "Agent Roster", "Roles and Responsibilities", "Capabilities",
            ],
            "workflows.md": [
                "Core Workflows", "Trigger Events", "Automation",
            ],
            "security.md": [
                "Authentication", "Authorization", "Secrets Management",
                "Threat Model",
            ],
            "testing.md": [
                "Testing Strategy", "Unit Tests", "Integration Tests",
                "Coverage Requirements",
            ],
            "technical-debt.md": [
                "Overview", "Debt Categories", "Active Debt Items",
                "Resolved Debt Items", "Debt Metrics",
            ],
        }
        return _schemas.get(template_name, [])
