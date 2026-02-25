"""
DeltaAnalyzer — computes three-way structural differences between design documents,
CodeAnalysisFacts, and existing steering files to produce a DeltaReport.

Detects structural drift only (Requirements 7.1, 7.4):
  - Technology mismatches (language, framework, database)
  - Dependency changes (added / removed packages)

Design documents are preferred over codebase when they diverge on a factual
field (Requirement 7.5).

Requirements: 7.1, 7.2, 7.4, 7.5
"""

import logging
import re
from typing import Dict, List, Optional

from .models import CodeAnalysisFacts, DeltaReport, ParsedDocument

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers for extracting technology mentions from free-form text
# ---------------------------------------------------------------------------

# Common technology tokens to look for in documents / steering files
_KNOWN_DATABASES = frozenset({
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis",
    "cassandra", "dynamodb", "mssql", "oracle", "mariadb", "cockroachdb",
})

_KNOWN_FRAMEWORKS = frozenset({
    "django", "flask", "fastapi", "express", "spring", "rails", "laravel",
    "nestjs", "gin", "fiber", "actix", "rocket", "typer", "click", "fastmcp",
})

_KNOWN_LANGUAGES = frozenset({
    "python", "javascript", "typescript", "java", "go", "rust", "ruby",
    "csharp", "c#", "cpp", "c++", "kotlin", "swift", "php",
})


def _extract_tech_tokens(text: str, token_set: frozenset) -> frozenset:
    """Return all tokens from *token_set* that appear in *text* (case-insensitive)."""
    lower = text.lower()
    return frozenset(t for t in token_set if t in lower)


def _extract_dependencies_from_text(text: str) -> frozenset:
    """
    Extract package names from free-form text.
    Looks for patterns like 'package==version', 'package>=version', or bare names
    in bullet lists.
    """
    # Match package names in requirements-style lines or markdown bullets
    pattern = re.compile(
        r"(?:^|\s|[-*•])\s*([a-zA-Z][a-zA-Z0-9_\-]{1,40})"
        r"(?:[>=<!~^]{1,2}[\d.]+)?",
        re.MULTILINE,
    )
    return frozenset(m.group(1).lower() for m in pattern.finditer(text))


class DeltaAnalyzer:
    """
    Computes three-way structural differences between design documents,
    CodeAnalysisFacts, and existing steering files.

    Requirements: 7.1, 7.2, 7.4, 7.5
    """

    def analyze(
        self,
        source_docs: List[ParsedDocument],
        code_facts: CodeAnalysisFacts,
        existing_steering: Dict[str, str],
    ) -> DeltaReport:
        """
        Produce a DeltaReport by comparing all three sources.

        Detects structural drift only: technology mismatches and dependency
        changes. Does NOT detect behavioral or architectural boundary violations.

        When design documents and codebase diverge on a factual field, design
        documents are treated as the source of truth (Requirement 7.5).

        Args:
            source_docs:      Parsed design / source documents.
            code_facts:       Structured facts from CodeAnalyzer.to_facts().
            existing_steering: Existing steering file contents keyed by filename.

        Returns:
            DeltaReport with all four divergence lists populated.

        Requirements: 7.1, 7.2, 7.4, 7.5
        """
        combined_doc_text = "\n\n".join(d.content for d in source_docs)
        combined_steering_text = "\n\n".join(existing_steering.values())

        doc_vs_code = self._compare_docs_vs_code(combined_doc_text, code_facts)
        steering_vs_code = self._compare_steering_vs_code(combined_steering_text, code_facts)
        steering_vs_docs = self._compare_steering_vs_docs(
            combined_steering_text, combined_doc_text
        )
        missing_in_all = self._find_missing_in_all(
            combined_doc_text, code_facts, combined_steering_text
        )

        report = DeltaReport(
            doc_vs_code=doc_vs_code,
            steering_vs_code=steering_vs_code,
            steering_vs_docs=steering_vs_docs,
            missing_in_all=missing_in_all,
        )

        logger.info(
            "DeltaAnalyzer: doc_vs_code=%d steering_vs_code=%d "
            "steering_vs_docs=%d missing_in_all=%d",
            len(doc_vs_code),
            len(steering_vs_code),
            len(steering_vs_docs),
            len(missing_in_all),
        )
        return report

    # ------------------------------------------------------------------
    # Private comparison methods
    # ------------------------------------------------------------------

    def _compare_docs_vs_code(
        self, doc_text: str, code_facts: CodeAnalysisFacts
    ) -> List[str]:
        """
        Detect divergences between design documents and codebase facts.

        Design docs are preferred — divergences are reported as
        "docs say X but code shows Y" (Requirement 7.5).
        """
        divergences: List[str] = []

        if not doc_text.strip():
            return divergences

        # Language check
        doc_languages = _extract_tech_tokens(doc_text, _KNOWN_LANGUAGES)
        code_lang = code_facts.primary_language.lower()
        if doc_languages and code_lang not in doc_languages:
            divergences.append(
                f"Primary language mismatch: design docs mention {sorted(doc_languages)} "
                f"but codebase primary language is '{code_facts.primary_language}'"
            )

        # Database check
        doc_databases = _extract_tech_tokens(doc_text, _KNOWN_DATABASES)
        if code_facts.database:
            code_db = code_facts.database.lower()
            if doc_databases and code_db not in doc_databases:
                divergences.append(
                    f"Database mismatch: design docs mention {sorted(doc_databases)} "
                    f"but codebase shows '{code_facts.database}' "
                    "(design docs take precedence)"
                )

        # Framework check
        doc_frameworks = _extract_tech_tokens(doc_text, _KNOWN_FRAMEWORKS)
        code_frameworks = {f.lower() for f in code_facts.frameworks}
        unexpected_in_docs = doc_frameworks - code_frameworks
        missing_from_docs = code_frameworks - doc_frameworks
        if unexpected_in_docs:
            divergences.append(
                f"Frameworks in design docs not found in codebase: "
                f"{sorted(unexpected_in_docs)} (design docs take precedence)"
            )
        if missing_from_docs:
            divergences.append(
                f"Frameworks in codebase not mentioned in design docs: "
                f"{sorted(missing_from_docs)}"
            )

        # Dependency drift
        doc_deps = _extract_dependencies_from_text(doc_text)
        code_dep_names = {d.name.lower() for d in code_facts.dependencies}
        in_docs_not_code = doc_deps & _KNOWN_FRAMEWORKS - code_dep_names
        if in_docs_not_code:
            divergences.append(
                f"Dependencies mentioned in design docs but absent from codebase: "
                f"{sorted(in_docs_not_code)}"
            )

        return divergences

    def _compare_steering_vs_code(
        self, steering_text: str, code_facts: CodeAnalysisFacts
    ) -> List[str]:
        """Detect drifts between existing steering files and current codebase facts."""
        drifts: List[str] = []

        if not steering_text.strip():
            return drifts

        # Database drift
        steering_databases = _extract_tech_tokens(steering_text, _KNOWN_DATABASES)
        if code_facts.database:
            code_db = code_facts.database.lower()
            if steering_databases and code_db not in steering_databases:
                drifts.append(
                    f"Steering files mention database(s) {sorted(steering_databases)} "
                    f"but codebase now shows '{code_facts.database}'"
                )
        elif steering_databases:
            drifts.append(
                f"Steering files mention database(s) {sorted(steering_databases)} "
                "but no database detected in codebase"
            )

        # Framework drift
        steering_frameworks = _extract_tech_tokens(steering_text, _KNOWN_FRAMEWORKS)
        code_frameworks = {f.lower() for f in code_facts.frameworks}
        stale_frameworks = steering_frameworks - code_frameworks
        new_frameworks = code_frameworks - steering_frameworks
        if stale_frameworks:
            drifts.append(
                f"Steering files reference frameworks no longer in codebase: "
                f"{sorted(stale_frameworks)}"
            )
        if new_frameworks:
            drifts.append(
                f"New frameworks in codebase not yet in steering files: "
                f"{sorted(new_frameworks)}"
            )

        # Language drift
        steering_languages = _extract_tech_tokens(steering_text, _KNOWN_LANGUAGES)
        code_lang = code_facts.primary_language.lower()
        if steering_languages and code_lang not in steering_languages:
            drifts.append(
                f"Steering files mention language(s) {sorted(steering_languages)} "
                f"but primary language is now '{code_facts.primary_language}'"
            )

        return drifts

    def _compare_steering_vs_docs(
        self, steering_text: str, doc_text: str
    ) -> List[str]:
        """Detect conflicts between existing steering files and design documents."""
        conflicts: List[str] = []

        if not steering_text.strip() or not doc_text.strip():
            return conflicts

        # Database conflicts
        steering_dbs = _extract_tech_tokens(steering_text, _KNOWN_DATABASES)
        doc_dbs = _extract_tech_tokens(doc_text, _KNOWN_DATABASES)
        if steering_dbs and doc_dbs and steering_dbs != doc_dbs:
            conflicts.append(
                f"Database conflict: steering files mention {sorted(steering_dbs)} "
                f"but design docs mention {sorted(doc_dbs)} "
                "(design docs take precedence)"
            )

        # Framework conflicts
        steering_fws = _extract_tech_tokens(steering_text, _KNOWN_FRAMEWORKS)
        doc_fws = _extract_tech_tokens(doc_text, _KNOWN_FRAMEWORKS)
        stale = steering_fws - doc_fws
        if stale:
            conflicts.append(
                f"Steering files reference frameworks not in design docs: "
                f"{sorted(stale)}"
            )

        return conflicts

    def _find_missing_in_all(
        self,
        doc_text: str,
        code_facts: CodeAnalysisFacts,
        steering_text: str,
    ) -> List[str]:
        """Identify gaps absent from all three sources."""
        missing: List[str] = []

        # If no database anywhere
        has_db_in_docs = bool(_extract_tech_tokens(doc_text, _KNOWN_DATABASES))
        has_db_in_code = code_facts.database is not None
        has_db_in_steering = bool(_extract_tech_tokens(steering_text, _KNOWN_DATABASES))
        if not has_db_in_docs and not has_db_in_code and not has_db_in_steering:
            missing.append("Database/storage strategy not defined in any source")

        # If no test framework anywhere
        has_test_in_docs = any(
            kw in doc_text.lower()
            for kw in ("pytest", "unittest", "jest", "test", "testing")
        )
        has_test_in_code = code_facts.has_tests or code_facts.test_framework is not None
        has_test_in_steering = "test" in steering_text.lower()
        if not has_test_in_docs and not has_test_in_code and not has_test_in_steering:
            missing.append("Testing strategy not defined in any source")

        # If no architecture pattern anywhere
        arch_keywords = ("monolith", "microservice", "layered", "hexagonal", "event")
        has_arch_in_docs = any(kw in doc_text.lower() for kw in arch_keywords)
        has_arch_in_code = code_facts.architecture_pattern not in ("custom", "unknown", "")
        has_arch_in_steering = any(kw in steering_text.lower() for kw in arch_keywords)
        if not has_arch_in_docs and not has_arch_in_code and not has_arch_in_steering:
            missing.append("Architecture pattern not defined in any source")

        return missing
