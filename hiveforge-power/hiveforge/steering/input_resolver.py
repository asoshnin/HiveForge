"""
Input resolver for the LLM-Primary Steering Synthesis pipeline.

This module determines the applicable use case based on the presence of
source documents, codebase, and existing steering files.

Requirements: 3.3, 3.4, 3.5, 9.5
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from .models import UseCase

logger = logging.getLogger(__name__)


class InputResolver:
    """
    Determines the applicable use case and resolves source folder paths.
    
    The InputResolver analyzes the project state (source docs, codebase, steering files)
    to determine which generation workflow should be used.
    
    Requirements: 3.3, 3.4, 3.5, 9.5
    """
    
    # Intent document filename patterns
    INTENT_DOC_PATTERNS = [
        "intent.md",
        "INTENT.md",
        "user-intent.md",
        "USER-INTENT.md",
        "pivot.md",
        "PIVOT.md",
    ]
    
    def resolve(
        self,
        source_folder: Optional[Path],
        project_root: Path,
        steering_dir: Path,
    ) -> Tuple[UseCase, Optional[Path]]:
        """
        Determine the use case and resolve the source folder path.
        
        Args:
            source_folder: Optional path to source documents folder
            project_root: Root path of the project
            steering_dir: Path to the steering files directory (.kiro/steering)
        
        Returns:
            Tuple of (UseCase, resolved_source_folder_path)
            - UseCase: The determined workflow use case
            - resolved_source_folder_path: Absolute path to source folder, or None if not applicable
        
        Use case determination logic:
        | Source docs | Codebase | Existing steering | Use case           |
        |-------------|----------|-------------------|--------------------|
        | Yes         | No       | No                | new_from_docs      |
        | No          | Yes      | No                | reverse_engineer   |
        | Yes         | Yes      | Yes               | drift_correction   |
        | Any         | Any      | Broken/partial    | error_recovery     |
        | Yes (intent)| Any      | Any               | pivot              |
        | Yes         | Yes      | No                | update             |
        
        Requirements: 3.3, 3.4, 3.5, 9.5
        """
        # Resolve source folder path if provided
        resolved_source_folder = None
        if source_folder is not None:
            resolved_source_folder = Path(source_folder).resolve()
            if not resolved_source_folder.exists():
                logger.warning(f"Source folder does not exist: {source_folder}")
                resolved_source_folder = None
        
        # Check for source documents
        source_docs_present = self._has_source_docs(resolved_source_folder)
        
        # Check for intent document (pivot use case)
        has_intent_doc = self._has_intent_document(resolved_source_folder)
        
        # Check for codebase (any Python, JS, TS, etc. files in project root)
        codebase_present = self._has_codebase(project_root)
        
        # Check for existing steering files
        steering_state = self._check_steering_state(steering_dir)
        
        # Determine use case based on the decision table
        use_case = self._determine_use_case(
            source_docs_present=source_docs_present,
            has_intent_doc=has_intent_doc,
            codebase_present=codebase_present,
            steering_state=steering_state,
        )
        
        logger.info(
            f"Resolved use case: {use_case} "
            f"(source_docs={source_docs_present}, "
            f"intent_doc={has_intent_doc}, "
            f"codebase={codebase_present}, "
            f"steering={steering_state})"
        )
        
        return use_case, resolved_source_folder
    
    def _has_source_docs(self, source_folder: Optional[Path]) -> bool:
        """
        Check if source documents are present.
        
        Args:
            source_folder: Path to source folder (or None)
        
        Returns:
            True if source folder exists and contains at least one supported file
        """
        if source_folder is None or not source_folder.exists():
            return False
        
        # Check for any markdown, PDF, or image files
        supported_extensions = {".md", ".pdf", ".png", ".jpg", ".jpeg"}
        
        for file_path in source_folder.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                return True
        
        return False
    
    def _has_intent_document(self, source_folder: Optional[Path]) -> bool:
        """
        Check if an intent document is present in the source folder.
        
        Intent documents signal a "pivot" use case where the user wants to
        change direction based on explicit new requirements.
        
        Args:
            source_folder: Path to source folder (or None)
        
        Returns:
            True if an intent document is found
        """
        if source_folder is None or not source_folder.exists():
            return False
        
        for pattern in self.INTENT_DOC_PATTERNS:
            intent_path = source_folder / pattern
            if intent_path.exists() and intent_path.is_file():
                logger.info(f"Found intent document: {intent_path}")
                return True
        
        return False
    
    def _has_codebase(self, project_root: Path) -> bool:
        """
        Check if a codebase is present in the project root.
        
        A codebase is considered present if there are any source code files
        (Python, JavaScript, TypeScript, etc.) in the project.
        
        Args:
            project_root: Root path of the project
        
        Returns:
            True if codebase is present
        """
        if not project_root.exists():
            return False
        
        # Common source code extensions
        code_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx",
            ".java", ".go", ".rs", ".c", ".cpp", ".h",
            ".rb", ".php", ".swift", ".kt",
        }
        
        # Check for at least one source file (limit search depth to avoid deep traversal)
        max_depth = 5
        for file_path in project_root.rglob("*"):
            # Skip hidden directories and common non-code directories
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if any(part in {"node_modules", "venv", "__pycache__", "dist", "build"} for part in file_path.parts):
                continue
            
            # Check depth
            try:
                relative_depth = len(file_path.relative_to(project_root).parts)
                if relative_depth > max_depth:
                    continue
            except ValueError:
                continue
            
            if file_path.is_file() and file_path.suffix.lower() in code_extensions:
                return True
        
        return False
    
    def _check_steering_state(self, steering_dir: Path) -> str:
        """
        Check the state of existing steering files.
        
        Args:
            steering_dir: Path to steering directory
        
        Returns:
            One of: "absent", "complete", "partial", "broken"
        """
        if not steering_dir.exists():
            return "absent"
        
        # Expected steering files
        expected_files = [
            "project-vision.md",
            "tech-stack.md",
            "architecture.md",
            "conventions.md",
            "agents.md",
            "workflows.md",
            "security.md",
            "testing.md",
        ]
        
        existing_files = []
        broken_files = []
        
        for filename in expected_files:
            file_path = steering_dir / filename
            if file_path.exists():
                # Check if file is readable and non-empty
                try:
                    content = file_path.read_text(encoding="utf-8")
                    if len(content.strip()) > 0:
                        existing_files.append(filename)
                    else:
                        broken_files.append(filename)
                except Exception as e:
                    logger.warning(f"Failed to read {filename}: {e}")
                    broken_files.append(filename)
        
        # Determine state
        if len(broken_files) > 0:
            return "broken"
        elif len(existing_files) == len(expected_files):
            return "complete"
        elif len(existing_files) > 0:
            return "partial"
        else:
            return "absent"
    
    def _determine_use_case(
        self,
        source_docs_present: bool,
        has_intent_doc: bool,
        codebase_present: bool,
        steering_state: str,
    ) -> UseCase:
        """
        Determine the use case based on project state.
        
        Args:
            source_docs_present: Whether source documents are present
            has_intent_doc: Whether an intent document is present
            codebase_present: Whether a codebase is present
            steering_state: State of steering files ("absent", "complete", "partial", "broken")
        
        Returns:
            The determined UseCase
        
        Decision logic (priority order):
        1. If intent doc present → pivot
        2. If steering broken/partial → error_recovery
        3. If source docs + no codebase + no steering → new_from_docs
        4. If no source docs + codebase + no steering → reverse_engineer
        5. If source docs + codebase + complete steering → drift_correction
        6. If source docs + codebase + no steering → update
        7. Default → reverse_engineer (safest fallback)
        """
        # Priority 1: Intent document signals pivot
        if has_intent_doc:
            return "pivot"
        
        # Priority 2: Broken or partial steering needs recovery
        if steering_state in {"broken", "partial"}:
            return "error_recovery"
        
        # Priority 3: Source docs only (no codebase, no steering) → new project from docs
        if source_docs_present and not codebase_present and steering_state == "absent":
            return "new_from_docs"
        
        # Priority 4: Codebase only (no source docs, no steering) → reverse engineer
        if not source_docs_present and codebase_present and steering_state == "absent":
            return "reverse_engineer"
        
        # Priority 5: All three present → drift correction
        if source_docs_present and codebase_present and steering_state == "complete":
            return "drift_correction"
        
        # Priority 6: Source docs + codebase, no steering → update/initial generation
        if source_docs_present and codebase_present and steering_state == "absent":
            return "update"
        
        # Default fallback: reverse engineer from codebase
        # This is the safest option when the state doesn't match any clear pattern
        logger.warning(
            f"Ambiguous state: source_docs={source_docs_present}, "
            f"codebase={codebase_present}, steering={steering_state}. "
            f"Defaulting to reverse_engineer."
        )
        return "reverse_engineer"
