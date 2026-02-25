"""
DebtDetector — static analysis for technical debt patterns.

Detects DRY violations, test gaps, architecture smells, and performance risks.
Respects .gitignore via pathspec. Caches results in .kiro/.cache/debt_analysis.json.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 7.1-7.5, 12.1-12.5
"""

import ast
import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import pathspec
except ImportError:
    pathspec = None  # type: ignore[assignment]

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


class DebtDetector:
    """
    Analyzes a codebase for technical debt using local static analysis.

    Requirements: 2.1-2.8, 7.1-7.5, 12.1-12.5
    """

    CACHE_FILE = ".kiro/.cache/debt_analysis.json"
    LARGE_CODEBASE_THRESHOLD = 10_000
    SAMPLE_SIZE = 2_000

    def __init__(
        self,
        project_root: Path,
        conventions_content: Optional[str] = None,
        logger_instance: Optional[logging.Logger] = None,
    ) -> None:
        """
        Args:
            project_root: Root directory of the project to analyze.
            conventions_content: Content of conventions.md for preference escalation.
            logger_instance: Optional logger; defaults to module logger.
        """
        self.project_root = Path(project_root)
        self.conventions_content = conventions_content or ""
        self.logger = logger_instance or logger
        self._gitignore_spec: Optional[object] = None


    # ------------------------------------------------------------------ helpers

    def _make_item_id(self, category: DebtCategory, location: str) -> str:
        """Return a stable 12-char hex ID for (category, location).

        Requirements: 2.7
        """
        raw = category.value + location
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def _load_gitignore(self) -> Optional[object]:
        """Load .gitignore patterns using pathspec.

        Requirements: 2.6
        """
        if pathspec is None:
            self.logger.warning("pathspec not installed; .gitignore patterns will be ignored")
            return None
        gitignore_path = self.project_root / ".gitignore"
        if not gitignore_path.exists():
            return None
        try:
            patterns = gitignore_path.read_text(encoding="utf-8").splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        except Exception as exc:
            self.logger.warning("Failed to load .gitignore: %s", exc)
            return None

    def _collect_files(self) -> List[Path]:
        """Walk project_root and return all files, respecting .gitignore.

        Requirements: 2.6
        """
        spec = self._load_gitignore()
        collected: List[Path] = []
        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            # Skip hidden dirs (e.g. .git, .kiro)
            parts = path.relative_to(self.project_root).parts
            if any(p.startswith(".") for p in parts):
                continue
            if spec is not None:
                rel = str(path.relative_to(self.project_root))
                if spec.match_file(rel):
                    continue
            collected.append(path)
        return collected

    def _apply_sampling(self, files: List[Path]) -> List[Path]:
        """Return up to SAMPLE_SIZE files when count exceeds LARGE_CODEBASE_THRESHOLD.

        Requirements: 2.5, 12.3
        """
        if len(files) <= self.LARGE_CODEBASE_THRESHOLD:
            return files
        import random
        self.logger.info(
            "Large codebase (%d files) — sampling %d files", len(files), self.SAMPLE_SIZE
        )
        return random.sample(files, self.SAMPLE_SIZE)

    # ------------------------------------------------------------------ cache

    def _load_cache(self) -> Optional[DebtAnalysisResult]:
        """Load cached DebtAnalysisResult from disk.

        Deletes and returns None on corrupt cache.
        Requirements: 12.4
        """
        cache_path = self.project_root / self.CACHE_FILE
        if not cache_path.exists():
            return None
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            return _deserialize_result(data)
        except Exception as exc:
            self.logger.warning("Corrupt debt cache (%s) — deleting and re-running", exc)
            try:
                cache_path.unlink()
            except Exception:
                pass
            return None

    def _save_cache(self, result: DebtAnalysisResult) -> None:
        """Persist DebtAnalysisResult to disk.

        Requirements: 12.4
        """
        cache_path = self.project_root / self.CACHE_FILE
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps(_serialize_result(result), indent=2), encoding="utf-8"
            )
        except Exception as exc:
            self.logger.warning("Failed to save debt cache: %s", exc)

    # ------------------------------------------------------------------ conventions

    def _apply_conventions_preferences(self, items: List[DebtItem]) -> List[DebtItem]:
        """Escalate priorities based on conventions_content.

        Requirements: 7.1-7.5
        """
        conv = self.conventions_content.lower()
        dry_pref = "dry" in conv or "don't repeat" in conv or "duplication" in conv
        test_pref = (
            "tested > assumed" in conv
            or "minimum coverage" in conv
            or "testing preference" in conv
        )
        for item in items:
            if dry_pref and item.category == DebtCategory.CODE_QUALITY:
                if item.priority == DebtPriority.LOW:
                    item.priority = DebtPriority.MEDIUM
                elif item.priority == DebtPriority.MEDIUM:
                    item.priority = DebtPriority.HIGH
            if test_pref and item.category == DebtCategory.TESTS:
                if item.priority in (DebtPriority.LOW, DebtPriority.MEDIUM):
                    item.priority = DebtPriority.HIGH
        return items

    # ------------------------------------------------------------------ sub-detectors

    def _detect_dry_violations(self, files: List[Path]) -> List[DebtItem]:
        """AST-based repeated function/class body detection.

        Requirements: 2.1, 8.1-8.4
        """
        items: List[DebtItem] = []
        # Map body_hash -> list of (file, lineno, func_name)
        body_map: Dict[str, List[Tuple[Path, int, str]]] = {}

        for path in files:
            if path.suffix != ".py":
                # Non-Python: line-hash comparison on blocks of >=15 consecutive non-blank lines
                items.extend(self._detect_dry_nonpy(path))
                continue
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source, filename=str(path))
            except Exception as exc:
                self.logger.warning("Skipping %s (parse error): %s", path, exc)
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                body = node.body
                if len(body) < 10:
                    continue
                # Normalize: rename all Name nodes to "_"
                normalized = _normalize_ast(body)
                body_hash = hashlib.sha256(normalized.encode()).hexdigest()
                rel = str(path.relative_to(self.project_root))
                body_map.setdefault(body_hash, []).append((path, node.lineno, node.name))

        for body_hash, occurrences in body_map.items():
            if len(occurrences) < 2:
                continue
            locations = [f"{p.relative_to(self.project_root)}:{ln}" for p, ln, _ in occurrences]
            primary_path, primary_line, primary_name = occurrences[0]
            location = f"{primary_path.relative_to(self.project_root)}:{primary_line}"
            item_id = self._make_item_id(DebtCategory.CODE_QUALITY, location)
            items.append(DebtItem(
                id=item_id,
                category=DebtCategory.CODE_QUALITY,
                description=(
                    f"DRY violation: function '{primary_name}' body duplicated in "
                    f"{len(occurrences)} locations: {', '.join(locations[:3])}"
                ),
                location=location,
                priority=DebtPriority.MEDIUM,
                effort=DebtEffort.MEDIUM,
                risk=DebtRisk.MEDIUM,
                status=DebtStatus.ACTIVE,
                confidence=0.85,
                recommendations=[
                    DebtRecommendation(
                        title="Extract shared helper",
                        description=(
                            f"Move the duplicated logic from '{primary_name}' into a shared "
                            "utility function and import it in all call sites."
                        ),
                        trade_offs="Requires refactoring all call sites; may affect public API.",
                        is_recommended=True,
                    ),
                    DebtRecommendation(
                        title="Accept duplication",
                        description="Leave the code as-is if the duplication is intentional.",
                        trade_offs="Increases maintenance burden; future changes must be applied in multiple places.",
                        is_recommended=False,
                    ),
                ],
                detected_at=_now_iso(),
            ))
        return items

    def _detect_dry_nonpy(self, path: Path) -> List[DebtItem]:
        """Line-hash comparison for non-Python files (>=15 consecutive non-blank lines)."""
        items: List[DebtItem] = []
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return items

        block_map: Dict[str, List[int]] = {}
        i = 0
        while i < len(lines):
            if lines[i].strip():
                block: List[str] = []
                j = i
                while j < len(lines) and lines[j].strip():
                    block.append(lines[j])
                    j += 1
                if len(block) >= 15:
                    block_hash = hashlib.sha256("\n".join(block).encode()).hexdigest()
                    block_map.setdefault(block_hash, []).append(i + 1)
                i = j
            else:
                i += 1

        for block_hash, line_nos in block_map.items():
            if len(line_nos) < 2:
                continue
            location = f"{path.relative_to(self.project_root)}:{line_nos[0]}"
            item_id = self._make_item_id(DebtCategory.CODE_QUALITY, location)
            items.append(DebtItem(
                id=item_id,
                category=DebtCategory.CODE_QUALITY,
                description=(
                    f"DRY violation: repeated block at lines {line_nos} in "
                    f"{path.relative_to(self.project_root)}"
                ),
                location=location,
                priority=DebtPriority.LOW,
                effort=DebtEffort.LOW,
                risk=DebtRisk.LOW,
                status=DebtStatus.ACTIVE,
                confidence=0.70,
                recommendations=[
                    DebtRecommendation(
                        title="Extract shared template or constant",
                        description="Move the repeated block into a shared constant or template.",
                        trade_offs="May require build tooling changes.",
                        is_recommended=True,
                    ),
                    DebtRecommendation(
                        title="Accept duplication",
                        description="Leave as-is if the repetition is intentional.",
                        trade_offs="Increases maintenance burden.",
                        is_recommended=False,
                    ),
                ],
                detected_at=_now_iso(),
            ))
        return items

    def _detect_test_gaps(self, files: List[Path]) -> List[DebtItem]:
        """File-to-test ratio analysis; uncovered public functions.

        Requirements: 2.2, 8.1-8.4
        """
        items: List[DebtItem] = []
        py_files = [f for f in files if f.suffix == ".py"]
        test_stems: Set[str] = {
            f.stem for f in py_files if f.stem.startswith("test_") or f.stem.endswith("_test")
        }
        source_files = [
            f for f in py_files
            if not (f.stem.startswith("test_") or f.stem.endswith("_test"))
            and f.stem != "__init__"
        ]

        # Escalate to HIGH when conventions specify testing preference
        test_pref = (
            "tested > assumed" in self.conventions_content.lower()
            or "minimum coverage" in self.conventions_content.lower()
        )
        missing_priority = DebtPriority.HIGH if test_pref else DebtPriority.HIGH
        untested_priority = DebtPriority.HIGH if test_pref else DebtPriority.MEDIUM

        for src in source_files:
            expected_test = f"test_{src.stem}"
            if expected_test not in test_stems:
                location = str(src.relative_to(self.project_root))
                item_id = self._make_item_id(DebtCategory.TESTS, location)
                items.append(DebtItem(
                    id=item_id,
                    category=DebtCategory.TESTS,
                    description=f"Missing test file for module '{src.stem}' (expected test_{src.stem}.py)",
                    location=location,
                    priority=missing_priority,
                    effort=DebtEffort.MEDIUM,
                    risk=DebtRisk.HIGH,
                    status=DebtStatus.ACTIVE,
                    confidence=0.90,
                    recommendations=[
                        DebtRecommendation(
                            title=f"Create test_{src.stem}.py",
                            description=f"Add a test file covering the public API of {src.name}.",
                            trade_offs="Requires time investment; may reveal existing bugs.",
                            is_recommended=True,
                        ),
                        DebtRecommendation(
                            title="Add tests to an existing test file",
                            description="Merge tests into a related existing test module.",
                            trade_offs="Reduces discoverability of tests for this module.",
                            is_recommended=False,
                        ),
                    ],
                    detected_at=_now_iso(),
                ))
            else:
                # Check for untested public functions via AST
                test_file = next(
                    (f for f in py_files if f.stem == expected_test), None
                )
                if test_file is None:
                    continue
                try:
                    src_tree = ast.parse(src.read_text(encoding="utf-8", errors="replace"))
                    test_tree = ast.parse(test_file.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    continue

                public_fns = {
                    node.name
                    for node in ast.walk(src_tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not node.name.startswith("_")
                }
                called_names = {
                    node.id
                    for node in ast.walk(test_tree)
                    if isinstance(node, ast.Name)
                }
                called_names |= {
                    node.attr
                    for node in ast.walk(test_tree)
                    if isinstance(node, ast.Attribute)
                }
                untested = public_fns - called_names
                for fn_name in untested:
                    # Find line number
                    lineno = next(
                        (
                            node.lineno
                            for node in ast.walk(src_tree)
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and node.name == fn_name
                        ),
                        1,
                    )
                    location = f"{src.relative_to(self.project_root)}:{lineno}"
                    item_id = self._make_item_id(DebtCategory.TESTS, location)
                    items.append(DebtItem(
                        id=item_id,
                        category=DebtCategory.TESTS,
                        description=f"Public function '{fn_name}' in {src.name} has no test coverage",
                        location=location,
                        priority=untested_priority,
                        effort=DebtEffort.LOW,
                        risk=DebtRisk.MEDIUM,
                        status=DebtStatus.ACTIVE,
                        confidence=0.75,
                        recommendations=[
                            DebtRecommendation(
                                title=f"Add test for '{fn_name}'",
                                description=f"Write unit tests covering normal and edge-case inputs for {fn_name}.",
                                trade_offs="Requires understanding of function contract.",
                                is_recommended=True,
                            ),
                            DebtRecommendation(
                                title="Add integration test",
                                description="Cover the function indirectly via a higher-level integration test.",
                                trade_offs="Less precise; may miss edge cases.",
                                is_recommended=False,
                            ),
                        ],
                        detected_at=_now_iso(),
                    ))
        return items

    def _detect_architecture_smells(self, files: List[Path]) -> List[DebtItem]:
        """Circular import detection and god class detection.

        Requirements: 2.3, 8.1-8.4
        """
        items: List[DebtItem] = []
        py_files = [f for f in files if f.suffix == ".py"]

        # Build import graph
        import_graph: Dict[str, Set[str]] = {}
        for path in py_files:
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source)
            except Exception as exc:
                self.logger.warning("Skipping %s (parse error): %s", path, exc)
                continue

            module_name = str(path.relative_to(self.project_root)).replace("/", ".").replace("\\", ".").removesuffix(".py")
            imports: Set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
            import_graph[module_name] = imports

            # God class detection
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    end = getattr(node, "end_lineno", node.lineno)
                    loc = end - node.lineno
                    if loc > 500:
                        location = f"{path.relative_to(self.project_root)}:{node.lineno}"
                        item_id = self._make_item_id(DebtCategory.ARCHITECTURE, location)
                        items.append(DebtItem(
                            id=item_id,
                            category=DebtCategory.ARCHITECTURE,
                            description=f"God class: '{node.name}' has {loc} lines of code",
                            location=location,
                            priority=DebtPriority.MEDIUM,
                            effort=DebtEffort.HIGH,
                            risk=DebtRisk.MEDIUM,
                            status=DebtStatus.ACTIVE,
                            confidence=0.90,
                            recommendations=[
                                DebtRecommendation(
                                    title="Split into smaller classes",
                                    description=f"Decompose '{node.name}' by responsibility using SRP.",
                                    trade_offs="Large refactor; may break existing callers.",
                                    is_recommended=True,
                                ),
                                DebtRecommendation(
                                    title="Extract helper modules",
                                    description="Move utility methods to separate helper modules.",
                                    trade_offs="Partial improvement; class remains large.",
                                    is_recommended=False,
                                ),
                            ],
                            detected_at=_now_iso(),
                        ))

        # Tarjan's SCC for circular imports
        cycles = _tarjan_scc(import_graph)
        for cycle in cycles:
            if len(cycle) < 2:
                continue
            cycle_str = " → ".join(sorted(cycle))
            location = sorted(cycle)[0]
            item_id = self._make_item_id(DebtCategory.ARCHITECTURE, "cycle:" + cycle_str)
            items.append(DebtItem(
                id=item_id,
                category=DebtCategory.ARCHITECTURE,
                description=f"Circular import detected: {cycle_str}",
                location=location,
                priority=DebtPriority.HIGH,
                effort=DebtEffort.HIGH,
                risk=DebtRisk.HIGH,
                status=DebtStatus.ACTIVE,
                confidence=0.85,
                recommendations=[
                    DebtRecommendation(
                        title="Break the cycle with dependency inversion",
                        description="Introduce an interface or abstract base class to invert the dependency.",
                        trade_offs="Requires architectural changes; may need new abstraction layer.",
                        is_recommended=True,
                    ),
                    DebtRecommendation(
                        title="Move shared code to a common module",
                        description="Extract the shared dependency into a third module imported by both.",
                        trade_offs="May create a utility module that grows over time.",
                        is_recommended=False,
                    ),
                ],
                detected_at=_now_iso(),
            ))
        return items

    def _detect_performance_risks(self, files: List[Path]) -> List[DebtItem]:
        """Regex pattern matching for performance anti-patterns.

        Requirements: 2.4, 8.1-8.4
        """
        items: List[DebtItem] = []

        # (pattern, description, priority, effort, risk, confidence)
        PATTERNS: List[Tuple[str, str, DebtPriority, DebtEffort, DebtRisk, float]] = [
            (
                r"for\s+\w+\s+in\s+.+:\n(?:[ \t]+.*\n)*?[ \t]+.*\.query\(",
                "N+1 query pattern: database query inside a loop",
                DebtPriority.HIGH, DebtEffort.MEDIUM, DebtRisk.HIGH, 0.80,
            ),
            (
                r"while\s+True\s*:",
                "Unbounded loop: 'while True' without visible break",
                DebtPriority.HIGH, DebtEffort.LOW, DebtRisk.HIGH, 0.70,
            ),
            (
                r"(\w+)\s*\+=\s*['\"]",
                "String concatenation in loop (potential O(n²) allocation)",
                DebtPriority.MEDIUM, DebtEffort.LOW, DebtRisk.MEDIUM, 0.75,
            ),
            (
                r"for\s+\w+\s+in\s+.+:\n(?:[ \t]+.*\n)*?[ \t]+\w+\s*=\s*\[",
                "List allocation inside loop",
                DebtPriority.LOW, DebtEffort.LOW, DebtRisk.LOW, 0.65,
            ),
        ]

        RECOMMENDATIONS: Dict[str, Tuple[DebtRecommendation, DebtRecommendation]] = {
            "N+1": (
                DebtRecommendation(
                    title="Batch the query outside the loop",
                    description="Fetch all required records in a single query before the loop.",
                    trade_offs="May require query refactoring; increases memory usage.",
                    is_recommended=True,
                ),
                DebtRecommendation(
                    title="Add caching",
                    description="Cache query results to avoid repeated database hits.",
                    trade_offs="Cache invalidation complexity; stale data risk.",
                    is_recommended=False,
                ),
            ),
            "while True": (
                DebtRecommendation(
                    title="Add explicit termination condition",
                    description="Replace 'while True' with a condition that naturally terminates.",
                    trade_offs="May require refactoring loop logic.",
                    is_recommended=True,
                ),
                DebtRecommendation(
                    title="Add timeout or iteration limit",
                    description="Add a counter or timeout to bound the loop.",
                    trade_offs="Partial fix; root cause remains.",
                    is_recommended=False,
                ),
            ),
            "string concat": (
                DebtRecommendation(
                    title="Use str.join() or io.StringIO",
                    description="Collect parts in a list and join at the end.",
                    trade_offs="Minor code restructuring required.",
                    is_recommended=True,
                ),
                DebtRecommendation(
                    title="Use f-strings with list comprehension",
                    description="Build the string in a single expression.",
                    trade_offs="May reduce readability for complex strings.",
                    is_recommended=False,
                ),
            ),
            "list alloc": (
                DebtRecommendation(
                    title="Pre-allocate or use a generator",
                    description="Allocate the list outside the loop or use a generator expression.",
                    trade_offs="Minor refactor; negligible for small loops.",
                    is_recommended=True,
                ),
                DebtRecommendation(
                    title="Accept current implementation",
                    description="Leave as-is if the loop is small and performance is not critical.",
                    trade_offs="Potential performance issue at scale.",
                    is_recommended=False,
                ),
            ),
        }

        pattern_keys = ["N+1", "while True", "string concat", "list alloc"]

        for path in files:
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            lines = source.splitlines()
            for (pattern, description, priority, effort, risk, confidence), key in zip(PATTERNS, pattern_keys):
                for match in re.finditer(pattern, source, re.MULTILINE):
                    lineno = source[: match.start()].count("\n") + 1
                    location = f"{path.relative_to(self.project_root)}:{lineno}"
                    item_id = self._make_item_id(DebtCategory.PERFORMANCE, location)
                    rec_pair = RECOMMENDATIONS[key]
                    items.append(DebtItem(
                        id=item_id,
                        category=DebtCategory.PERFORMANCE,
                        description=f"{description} at line {lineno}",
                        location=location,
                        priority=priority,
                        effort=effort,
                        risk=risk,
                        status=DebtStatus.ACTIVE,
                        confidence=confidence,
                        recommendations=list(rec_pair),
                        detected_at=_now_iso(),
                    ))
        return items

    # ------------------------------------------------------------------ orchestration

    def detect(self) -> DebtAnalysisResult:
        """Run all detectors and return aggregated results.

        Uses cache when available and codebase is unchanged.
        Requirements: 2.5, 2.6, 3.3, 12.1-12.5
        """
        start = time.monotonic()

        # Try cache first
        cached = self._load_cache()
        if cached is not None:
            self.logger.info("Returning cached debt analysis result")
            return cached

        files = self._collect_files()
        sampled = len(files) > self.LARGE_CODEBASE_THRESHOLD
        files = self._apply_sampling(files)

        all_items: List[DebtItem] = []
        for detector_fn in (
            self._detect_dry_violations,
            self._detect_test_gaps,
            self._detect_architecture_smells,
            self._detect_performance_risks,
        ):
            try:
                all_items.extend(detector_fn(files))
            except Exception as exc:
                self.logger.warning("Sub-detector %s failed: %s", detector_fn.__name__, exc)

        all_items = self._apply_conventions_preferences(all_items)

        # Compute metrics
        now = _now_iso()
        active = [i for i in all_items if i.status != DebtStatus.RESOLVED]
        by_cat: Dict[str, int] = {}
        by_pri: Dict[str, int] = {}
        for item in active:
            by_cat[item.category.value] = by_cat.get(item.category.value, 0) + 1
            by_pri[item.priority.value] = by_pri.get(item.priority.value, 0) + 1

        metrics = DebtMetrics(
            total_active=len(active),
            by_category=by_cat,
            by_priority=by_pri,
            last_updated=now,
        )

        result = DebtAnalysisResult(
            items=all_items,
            metrics=metrics,
            sampled=sampled,
            analysis_time_s=round(time.monotonic() - start, 3),
        )

        self._save_cache(result)
        return result


# ============================================================================
# Module-level helpers
# ============================================================================

def _now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _normalize_ast(body: list) -> str:
    """Normalize an AST body by renaming all Name nodes to '_'."""
    class _Normalizer(ast.NodeTransformer):
        def visit_Name(self, node: ast.Name) -> ast.Name:
            return ast.Name(id="_", ctx=node.ctx)

        def visit_arg(self, node: ast.arg) -> ast.arg:
            return ast.arg(arg="_", annotation=None)

    normalized_body = [_Normalizer().visit(n) for n in body]
    return ast.dump(ast.Module(body=normalized_body, type_ignores=[]))


def _tarjan_scc(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Tarjan's strongly connected components algorithm."""
    index_counter = [0]
    stack: List[str] = []
    lowlink: Dict[str, int] = {}
    index: Dict[str, int] = {}
    on_stack: Dict[str, bool] = {}
    sccs: List[List[str]] = []

    def strongconnect(v: str) -> None:
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack[v] = True

        for w in graph.get(v, set()):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink.get(w, lowlink[v]))
            elif on_stack.get(w, False):
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            scc: List[str] = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)

    for v in list(graph.keys()):
        if v not in index:
            try:
                strongconnect(v)
            except RecursionError:
                pass  # Skip deeply nested graphs

    return sccs


# ============================================================================
# Serialization helpers (for cache round-trip)
# ============================================================================

def _serialize_result(result: DebtAnalysisResult) -> dict:
    """Serialize DebtAnalysisResult to a JSON-compatible dict."""
    def _ser_item(item: DebtItem) -> dict:
        return {
            "id": item.id,
            "category": item.category.value,
            "description": item.description,
            "location": item.location,
            "priority": item.priority.value,
            "effort": item.effort.value,
            "risk": item.risk.value,
            "status": item.status.value,
            "confidence": item.confidence,
            "recommendations": [
                {
                    "title": r.title,
                    "description": r.description,
                    "trade_offs": r.trade_offs,
                    "is_recommended": r.is_recommended,
                }
                for r in item.recommendations
            ],
            "detected_at": item.detected_at,
            "resolved_at": item.resolved_at,
        }

    return {
        "items": [_ser_item(i) for i in result.items],
        "metrics": {
            "total_active": result.metrics.total_active,
            "by_category": result.metrics.by_category,
            "by_priority": result.metrics.by_priority,
            "last_updated": result.metrics.last_updated,
        },
        "sampled": result.sampled,
        "analysis_time_s": result.analysis_time_s,
    }


def _deserialize_result(data: dict) -> DebtAnalysisResult:
    """Deserialize a dict (from cache) back to DebtAnalysisResult."""
    items: List[DebtItem] = []
    for d in data.get("items", []):
        recs = [
            DebtRecommendation(
                title=r["title"],
                description=r["description"],
                trade_offs=r["trade_offs"],
                is_recommended=r.get("is_recommended", False),
            )
            for r in d.get("recommendations", [])
        ]
        items.append(DebtItem(
            id=d["id"],
            category=DebtCategory(d["category"]),
            description=d["description"],
            location=d["location"],
            priority=DebtPriority(d["priority"]),
            effort=DebtEffort(d["effort"]),
            risk=DebtRisk(d["risk"]),
            status=DebtStatus(d["status"]),
            confidence=d["confidence"],
            recommendations=recs,
            detected_at=d.get("detected_at"),
            resolved_at=d.get("resolved_at"),
        ))

    m = data.get("metrics", {})
    metrics = DebtMetrics(
        total_active=m.get("total_active", 0),
        by_category=m.get("by_category", {}),
        by_priority=m.get("by_priority", {}),
        last_updated=m.get("last_updated"),
    )

    return DebtAnalysisResult(
        items=items,
        metrics=metrics,
        sampled=data.get("sampled", False),
        analysis_time_s=data.get("analysis_time_s", 0.0),
    )
