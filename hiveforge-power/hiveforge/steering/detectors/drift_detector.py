"""Drift detection for steering files."""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

from ..models import (
    CodeAnalysisResult,
    DriftCategory,
    DriftItem,
    DriftReport,
)

logger = logging.getLogger(__name__)


class DriftDetector:
    """Detects drift between steering files and codebase."""
    
    SIGNIFICANT_DEPS = {
        'fastapi', 'flask', 'django', 'sqlalchemy', 'prisma',
        'redis', 'celery', 'pydantic', 'typer', 'click',
        'pytest', 'asyncio', 'aiohttp', 'requests', 'numpy',
        'pandas', 'torch', 'tensorflow', 'scikit-learn',
        'plotly', 'streamlit'
    }
    
    def __init__(self, project_root: Path, logger_instance: Optional[logging.Logger] = None):
        self.project_root = project_root
        self.logger = logger_instance or logger
    
    def detect(self, existing_files: Dict[str, str], code_analysis: CodeAnalysisResult) -> DriftReport:
        items = []
        lang_drift = self._detect_language_version_drift(existing_files, code_analysis)
        if lang_drift:
            items.append(lang_drift)
        dep_drifts = self._detect_dependency_drift(existing_files, code_analysis)
        items.extend(dep_drifts)
        arch_drift = self._detect_architecture_drift(existing_files, code_analysis)
        if arch_drift:
            items.append(arch_drift)
        conv_drift = self._detect_convention_drift(existing_files, code_analysis)
        if conv_drift:
            items.append(conv_drift)
        items.sort(key=lambda x: x.confidence, reverse=True)
        return DriftReport(items=items)
    
    def _detect_language_version_drift(self, existing_files: Dict[str, str], code_analysis: CodeAnalysisResult) -> Optional[DriftItem]:
        tech_stack_content = existing_files.get('tech-stack.md', '')
        if not tech_stack_content:
            return None
        pyproject_path = self.project_root / 'pyproject.toml'
        if not pyproject_path.exists():
            return None
        try:
            with open(pyproject_path, 'rb') as f:
                pyproject_data = tomllib.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to parse pyproject.toml: {e}")
            return None
        python_requires = pyproject_data.get('project', {}).get('requires-python', '')
        if not python_requires:
            return None
        version_match = re.search(r'(\d+\.\d+)', python_requires)
        if not version_match:
            return None
        pyproject_version = version_match.group(1)
        if pyproject_version not in tech_stack_content:
            return DriftItem(
                category=DriftCategory.LANGUAGE_VERSION,
                description=f"Python version in tech-stack.md differs from pyproject.toml (requires {python_requires})",
                confidence=0.95,
                suggested_action=f"Update tech-stack.md to reflect Python {pyproject_version} requirement"
            )
        return None
    
    def _detect_dependency_drift(self, existing_files: Dict[str, str], code_analysis: CodeAnalysisResult) -> List[DriftItem]:
        tech_stack_content = existing_files.get('tech-stack.md', '')
        if not tech_stack_content:
            return []
        current_deps = self._extract_current_dependencies()
        significant_current = self._filter_significant_dependencies(current_deps)
        new_deps = []
        for dep in significant_current:
            if dep.lower() not in tech_stack_content.lower():
                new_deps.append(dep)
        items = []
        for dep in new_deps:
            items.append(DriftItem(
                category=DriftCategory.NEW_DEPENDENCY,
                description=f"New significant dependency detected: {dep}",
                confidence=0.85,
                suggested_action=f"Add {dep} to tech-stack.md Key Dependencies section"
            ))
        return items
    
    def _extract_current_dependencies(self) -> List[str]:
        pyproject_path = self.project_root / 'pyproject.toml'
        if not pyproject_path.exists():
            return []
        try:
            with open(pyproject_path, 'rb') as f:
                pyproject_data = tomllib.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to parse pyproject.toml: {e}")
            return []
        dependencies = pyproject_data.get('project', {}).get('dependencies', [])
        dep_names = []
        for dep in dependencies:
            name = re.split(r'[<>=\[\]!]', dep)[0].strip()
            if name:
                dep_names.append(name)
        return dep_names
    
    def _filter_significant_dependencies(self, dependencies: List[str]) -> List[str]:
        significant = []
        for dep in dependencies:
            dep_lower = dep.lower()
            if dep_lower in self.SIGNIFICANT_DEPS:
                significant.append(dep)
            else:
                for keyword in self.SIGNIFICANT_DEPS:
                    if keyword in dep_lower:
                        significant.append(dep)
                        break
        return significant
    
    def _detect_architecture_drift(self, existing_files: Dict[str, str], code_analysis: CodeAnalysisResult) -> Optional[DriftItem]:
        architecture_content = existing_files.get('architecture.md', '')
        if not architecture_content:
            return None
        current_pattern = code_analysis.architecture.pattern if code_analysis.architecture else None
        if not current_pattern:
            return None
        if current_pattern.lower() not in architecture_content.lower():
            return DriftItem(
                category=DriftCategory.ARCHITECTURE_PATTERN,
                description=f"Architecture pattern in architecture.md differs from codebase ({current_pattern})",
                confidence=0.75,
                suggested_action=f"Update architecture.md to reflect {current_pattern} pattern"
            )
        return None
    
    def _detect_convention_drift(self, existing_files: Dict[str, str], code_analysis: CodeAnalysisResult) -> Optional[DriftItem]:
        conventions_content = existing_files.get('conventions.md', '')
        if not conventions_content:
            return None
        current_conventions = code_analysis.conventions.naming_style if code_analysis.conventions else {}
        if not current_conventions:
            return None
        convention_keywords = ['snake_case', 'camelCase', 'PascalCase', 'UPPER_SNAKE_CASE']
        documented_conventions = sum(1 for kw in convention_keywords if kw in conventions_content)
        if documented_conventions < 2:
            return DriftItem(
                category=DriftCategory.CONVENTION_MISMATCH,
                description="Naming conventions in conventions.md are incomplete or outdated",
                confidence=0.70,
                suggested_action="Review and update conventions.md with current naming conventions"
            )
        return None
