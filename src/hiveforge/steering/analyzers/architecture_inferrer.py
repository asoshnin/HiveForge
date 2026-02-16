"""
Architecture inference module for code analysis.

This module infers architectural patterns from directory structure and code
organization. All analysis is performed locally using pattern matching against
directory structures.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..models import ArchitectureInfo

logger = logging.getLogger(__name__)


# Architecture pattern definitions with directory indicators
ARCHITECTURE_PATTERNS = {
    'microservices': {
        'required': [['services', 'microservices']],
        'optional': [['api-gateway', 'gateway'], ['service-mesh']],
        'indicators': ['multiple service directories', 'docker-compose with multiple services'],
        'confidence_threshold': 0.6,
    },
    'layered': {
        'required': [['controllers', 'handlers'], ['services', 'business'], ['models', 'entities']],
        'optional': [['repositories', 'data'], ['views', 'presentation']],
        'indicators': ['clear separation of concerns', 'horizontal layers'],
        'confidence_threshold': 0.7,
    },
    'mvc': {
        'required': [['models'], ['views'], ['controllers']],
        'optional': [['routes', 'routing']],
        'indicators': ['model-view-controller pattern'],
        'confidence_threshold': 0.8,
    },
    'hexagonal': {
        'required': [['domain'], ['application'], ['infrastructure']],
        'optional': [['adapters', 'ports']],
        'indicators': ['ports and adapters', 'domain-driven design'],
        'confidence_threshold': 0.7,
    },
    'clean': {
        'required': [['domain', 'entities'], ['use-cases', 'usecases', 'application']],
        'optional': [['interfaces', 'adapters'], ['frameworks']],
        'indicators': ['clean architecture', 'dependency rule'],
        'confidence_threshold': 0.7,
    },
    'monolithic': {
        'required': [['src', 'app', 'lib']],
        'optional': [],
        'indicators': ['single application', 'unified codebase'],
        'confidence_threshold': 0.3,
    },
}


def infer_architecture(
    project_root: Path,
    excluded_paths: Optional[Set[Path]] = None
) -> ArchitectureInfo:
    """
    Infer architectural pattern from directory structure.
    
    This function:
    - Analyzes directory structure patterns
    - Detects patterns: monolithic, microservices, layered, MVC, hexagonal, clean
    - Assigns confidence scores based on pattern match strength
    - Falls back to "custom" for unrecognized patterns
    - Extracts key components and directory structure
    
    Args:
        project_root: Root directory of the project
        excluded_paths: Set of paths to exclude from analysis
        
    Returns:
        ArchitectureInfo object with inferred pattern and details
        
    Requirements: 3A.6
    """
    logger.info(f"Inferring architecture from: {project_root}")
    
    if excluded_paths is None:
        excluded_paths = set()
    
    # Get directory structure
    dir_structure = _get_directory_structure(project_root, excluded_paths)
    
    # Detect architectural pattern
    pattern, confidence = _detect_architecture_pattern(project_root, dir_structure)
    
    # Extract key components
    key_components = _extract_key_components(dir_structure, pattern)
    
    # Build architecture info
    architecture_info = ArchitectureInfo(
        pattern=pattern,
        directory_structure=dir_structure,
        key_components=key_components
    )
    
    logger.info(
        f"Inferred architecture: {pattern} (confidence: {confidence:.2f}), "
        f"components: {len(key_components)}"
    )
    
    return architecture_info


def _get_directory_structure(
    project_root: Path,
    excluded_paths: Set[Path],
    max_depth: int = 3
) -> Dict[str, str]:
    """
    Get directory structure up to max_depth.
    
    Args:
        project_root: Root directory
        excluded_paths: Paths to exclude
        max_depth: Maximum depth to traverse
        
    Returns:
        Dictionary mapping relative paths to descriptions
    """
    structure = {}
    
    def traverse(path: Path, current_depth: int, relative_base: Path):
        if current_depth > max_depth:
            return
        
        try:
            for item in path.iterdir():
                # Skip excluded paths
                if _is_excluded(item, project_root, excluded_paths):
                    continue
                
                if item.is_dir():
                    relative_path = item.relative_to(relative_base)
                    
                    # Count files in directory
                    try:
                        file_count = sum(1 for _ in item.rglob('*') if _.is_file())
                        structure[str(relative_path)] = f"directory ({file_count} files)"
                    except Exception:
                        structure[str(relative_path)] = "directory"
                    
                    # Recurse into subdirectory
                    traverse(item, current_depth + 1, relative_base)
        except PermissionError:
            logger.debug(f"Permission denied accessing {path}")
        except Exception as e:
            logger.debug(f"Error traversing {path}: {e}")
    
    traverse(project_root, 0, project_root)
    return structure


def _is_excluded(path: Path, project_root: Path, excluded_paths: Set[Path]) -> bool:
    """Check if a path should be excluded from analysis."""
    try:
        relative_path = path.relative_to(project_root)
        
        # Check if any parent directory is in excluded paths
        for excluded in excluded_paths:
            try:
                relative_path.relative_to(excluded)
                return True
            except ValueError:
                continue
        
        # Also exclude common non-source directories
        excluded_names = {
            'node_modules', 'venv', 'env', '.venv', '__pycache__',
            '.git', '.svn', '.hg', 'dist', 'build', 'target',
            '.pytest_cache', '.mypy_cache', 'coverage'
        }
        
        if path.name in excluded_names:
            return True
        
        return False
    except ValueError:
        return False


def _detect_architecture_pattern(
    project_root: Path,
    dir_structure: Dict[str, str]
) -> Tuple[str, float]:
    """
    Detect architectural pattern from directory structure.
    
    Args:
        project_root: Root directory
        dir_structure: Directory structure mapping
        
    Returns:
        Tuple of (pattern_name, confidence_score)
    """
    # Get all directory names (case-insensitive) - both leaf names and full paths
    dir_names = {Path(d).name.lower() for d in dir_structure.keys()}
    
    # Also include all path components for nested directory detection
    # e.g., "src/controllers" contributes both "src", "controllers", and "src/controllers"
    all_path_components = set()
    for dir_path in dir_structure.keys():
        path = Path(dir_path)
        # Add each component
        for part in path.parts:
            all_path_components.add(part.lower())
        # Add the full path for nested matching
        all_path_components.add(str(path).lower())
    
    # Combine both sets for comprehensive matching
    dir_names = dir_names.union(all_path_components)
    
    # Check for docker-compose files (for microservices detection)
    has_docker_compose = (
        (project_root / 'docker-compose.yml').exists() or
        (project_root / 'docker-compose.yaml').exists()
    )
    
    # Score each pattern
    pattern_scores = {}
    
    for pattern_name, pattern_def in ARCHITECTURE_PATTERNS.items():
        score = _calculate_pattern_score(
            pattern_name,
            pattern_def,
            dir_names,
            dir_structure,
            has_docker_compose
        )
        pattern_scores[pattern_name] = score
    
    # Find best match - exclude monolithic from initial consideration
    # to prioritize more specific patterns
    non_monolithic_scores = {
        k: v for k, v in pattern_scores.items() if k != 'monolithic'
    }
    
    if non_monolithic_scores:
        best_pattern = max(non_monolithic_scores.items(), key=lambda x: x[1])
        pattern_name, confidence = best_pattern
        
        # Check if confidence meets threshold
        threshold = ARCHITECTURE_PATTERNS[pattern_name]['confidence_threshold']
        if confidence >= threshold:
            return pattern_name, confidence
    
    # If no specific pattern matched, check monolithic
    if 'monolithic' in pattern_scores:
        confidence = pattern_scores['monolithic']
        threshold = ARCHITECTURE_PATTERNS['monolithic']['confidence_threshold']
        if confidence >= threshold:
            return 'monolithic', confidence
    
    # Fall back to custom
    return 'custom', 0.5


def _calculate_pattern_score(
    pattern_name: str,
    pattern_def: Dict,
    dir_names: Set[str],
    dir_structure: Dict[str, str],
    has_docker_compose: bool
) -> float:
    """
    Calculate confidence score for a pattern match.
    
    Args:
        pattern_name: Name of the pattern
        pattern_def: Pattern definition
        dir_names: Set of directory names
        dir_structure: Full directory structure
        has_docker_compose: Whether docker-compose file exists
        
    Returns:
        Confidence score (0.0-1.0)
    """
    score = 0.0
    total_weight = 0.0
    
    # Check required directories (weight: 1.0 each)
    for required_group in pattern_def['required']:
        total_weight += 1.0
        if any(req.lower() in dir_names for req in required_group):
            score += 1.0
    
    # Check optional directories (weight: 0.5 each)
    for optional_group in pattern_def['optional']:
        total_weight += 0.5
        if any(opt.lower() in dir_names for opt in optional_group):
            score += 0.5
    
    # Special handling for microservices
    if pattern_name == 'microservices':
        # Check for multiple service directories
        service_dirs = [d for d in dir_names if 'service' in d or d.endswith('-api')]
        if len(service_dirs) >= 2:
            score += 1.0
            total_weight += 1.0
        
        # Check for docker-compose
        if has_docker_compose:
            score += 0.5
            total_weight += 0.5
    
    # Calculate final score
    if total_weight > 0:
        return score / total_weight
    else:
        return 0.0


def _extract_key_components(
    dir_structure: Dict[str, str],
    pattern: str
) -> List[str]:
    """
    Extract key components from directory structure.
    
    Args:
        dir_structure: Directory structure mapping
        pattern: Detected architecture pattern
        
    Returns:
        List of key component names
    """
    components = []
    
    # Extract top-level directories as components
    for dir_path in dir_structure.keys():
        path_parts = Path(dir_path).parts
        
        # Only consider top-level or second-level directories
        if len(path_parts) <= 2:
            # Clean up component name
            component_name = path_parts[0]
            
            # Skip common non-component directories
            skip_dirs = {
                'tests', 'test', '__pycache__', 'node_modules',
                'venv', 'env', '.git', 'dist', 'build'
            }
            
            if component_name.lower() not in skip_dirs:
                # Capitalize for display
                display_name = component_name.replace('_', ' ').replace('-', ' ').title()
                if display_name not in components:
                    components.append(display_name)
    
    # Limit to top 10 components
    return sorted(components)[:10]


def get_architecture_confidence_score(architecture_info: ArchitectureInfo) -> float:
    """
    Calculate confidence score for detected architecture.
    
    Confidence scoring:
    - 1.0: Perfect pattern match
    - 0.8: Partial match with most indicators
    - 0.5: Weak match or custom
    - 0.3: Guessed
    
    Args:
        architecture_info: ArchitectureInfo object
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    pattern = architecture_info.pattern
    
    if pattern == 'custom':
        return 0.5
    
    # For recognized patterns, confidence depends on how well it matched
    # This is a simplified version - in practice, we'd store the actual
    # confidence from the detection process
    if pattern in ['mvc', 'hexagonal', 'clean']:
        return 0.8  # These require specific structure
    elif pattern in ['layered', 'microservices']:
        return 0.7  # These have more variation
    elif pattern == 'monolithic':
        return 0.6  # This is often a fallback
    else:
        return 0.5


def detect_monorepo(project_root: Path) -> bool:
    """
    Detect if the project is a monorepo.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        True if monorepo detected, False otherwise
    """
    # Check for common monorepo indicators
    monorepo_indicators = [
        'lerna.json',
        'nx.json',
        'pnpm-workspace.yaml',
        'workspaces',  # in package.json
    ]
    
    for indicator in monorepo_indicators:
        if (project_root / indicator).exists():
            return True
    
    # Check for multiple package.json files in subdirectories
    package_jsons = list(project_root.glob('*/package.json'))
    if len(package_jsons) >= 2:
        return True
    
    return False


def analyze_component_relationships(
    project_root: Path,
    key_components: List[str]
) -> Dict[str, List[str]]:
    """
    Analyze relationships between components (simplified version).
    
    This is a placeholder for more sophisticated analysis that could
    examine imports/dependencies between components.
    
    Args:
        project_root: Root directory
        key_components: List of key component names
        
    Returns:
        Dictionary mapping components to their dependencies
    """
    # Placeholder implementation
    # In a full implementation, this would analyze import statements
    # to determine which components depend on which others
    relationships = {}
    
    for component in key_components:
        relationships[component] = []
    
    return relationships
