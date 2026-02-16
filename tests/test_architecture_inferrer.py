"""
Tests for architecture inference module.

This module tests the architecture inference functionality to ensure it correctly
detects architectural patterns from directory structure.
"""

import pytest
from pathlib import Path

from src.hiveforge.steering.analyzers.architecture_inferrer import (
    infer_architecture,
    get_architecture_confidence_score,
    detect_monorepo,
    _detect_architecture_pattern,
    _calculate_pattern_score,
)
from src.hiveforge.steering.models import ArchitectureInfo


def create_directory_structure(base_path: Path, structure: dict):
    """Helper to create a directory structure from a nested dict."""
    for name, content in structure.items():
        path = base_path / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            create_directory_structure(path, content)
        else:
            path.mkdir(parents=True, exist_ok=True)


class TestInferArchitecture:
    """Tests for infer_architecture function."""
    
    def test_detect_mvc_pattern(self, tmp_path):
        """Should detect MVC architecture pattern."""
        create_directory_structure(tmp_path, {
            'models': {},
            'views': {},
            'controllers': {},
            'routes': {}
        })
        
        result = infer_architecture(tmp_path)
        
        assert result.pattern == 'mvc'
        assert 'Models' in result.key_components
        assert 'Views' in result.key_components
        assert 'Controllers' in result.key_components
    
    def test_detect_layered_pattern(self, tmp_path):
        """Should detect layered architecture pattern."""
        create_directory_structure(tmp_path, {
            'controllers': {},
            'services': {},
            'models': {},
            'repositories': {}
        })
        
        result = infer_architecture(tmp_path)
        
        assert result.pattern == 'layered'
        assert len(result.key_components) > 0
    
    def test_detect_hexagonal_pattern(self, tmp_path):
        """Should detect hexagonal architecture pattern."""
        create_directory_structure(tmp_path, {
            'domain': {},
            'application': {},
            'infrastructure': {},
            'adapters': {}
        })
        
        result = infer_architecture(tmp_path)
        
        assert result.pattern == 'hexagonal'
        assert 'Domain' in result.key_components
    
    def test_detect_microservices_pattern(self, tmp_path):
        """Should detect microservices architecture pattern."""
        create_directory_structure(tmp_path, {
            'services': {
                'user-service': {},
                'order-service': {},
                'payment-service': {}
            }
        })
        # Create docker-compose file
        (tmp_path / 'docker-compose.yml').write_text('version: "3"\nservices:\n')
        
        result = infer_architecture(tmp_path)
        
        assert result.pattern == 'microservices'
    
    def test_detect_monolithic_pattern(self, tmp_path):
        """Should detect monolithic architecture as fallback."""
        create_directory_structure(tmp_path, {
            'src': {
                'utils': {},
                'helpers': {}
            }
        })
        
        result = infer_architecture(tmp_path)
        
        # Should detect monolithic or custom
        assert result.pattern in ['monolithic', 'custom']
    
    def test_detect_custom_pattern(self, tmp_path):
        """Should fall back to custom for unrecognized patterns."""
        create_directory_structure(tmp_path, {
            'random': {},
            'unusual': {},
            'structure': {}
        })
        
        result = infer_architecture(tmp_path)
        
        assert result.pattern == 'custom'
    
    def test_empty_directory(self, tmp_path):
        """Should handle empty directory."""
        result = infer_architecture(tmp_path)
        
        assert isinstance(result, ArchitectureInfo)
        assert result.pattern in ['custom', 'monolithic']
    
    def test_excludes_common_directories(self, tmp_path):
        """Should exclude node_modules, venv, etc."""
        create_directory_structure(tmp_path, {
            'src': {},
            'node_modules': {},
            'venv': {},
            '__pycache__': {}
        })
        
        result = infer_architecture(tmp_path)
        
        # Should not include excluded directories in components
        assert 'Node Modules' not in result.key_components
        assert 'Venv' not in result.key_components
    
    def test_respects_excluded_paths(self, tmp_path):
        """Should respect excluded paths parameter."""
        create_directory_structure(tmp_path, {
            'src': {},
            'build': {},
            'dist': {}
        })
        
        excluded = {Path('build'), Path('dist')}
        result = infer_architecture(tmp_path, excluded_paths=excluded)
        
        # Should not include excluded paths
        assert 'Build' not in result.key_components
        assert 'Dist' not in result.key_components


class TestDetectArchitecturePattern:
    """Tests for _detect_architecture_pattern function."""
    
    def test_detect_mvc_with_high_confidence(self, tmp_path):
        """Should detect MVC with high confidence when all dirs present."""
        dir_structure = {
            'models': 'directory',
            'views': 'directory',
            'controllers': 'directory',
            'routes': 'directory'
        }
        
        pattern, confidence = _detect_architecture_pattern(tmp_path, dir_structure)
        
        assert pattern == 'mvc'
        assert confidence >= 0.8
    
    def test_detect_layered_with_partial_match(self, tmp_path):
        """Should detect layered even with partial match."""
        dir_structure = {
            'controllers': 'directory',
            'services': 'directory',
            'models': 'directory'
        }
        
        pattern, confidence = _detect_architecture_pattern(tmp_path, dir_structure)
        
        assert pattern == 'layered'
        assert confidence >= 0.7
    
    def test_confidence_below_threshold_returns_custom(self, tmp_path):
        """Should return custom when confidence is below threshold."""
        dir_structure = {
            'random': 'directory',
            'dirs': 'directory'
        }
        
        pattern, confidence = _detect_architecture_pattern(tmp_path, dir_structure)
        
        assert pattern == 'custom'


class TestCalculatePatternScore:
    """Tests for _calculate_pattern_score function."""
    
    def test_score_with_all_required_dirs(self):
        """Should give high score when all required dirs present."""
        pattern_def = {
            'required': [['models'], ['views'], ['controllers']],
            'optional': [],
            'confidence_threshold': 0.8
        }
        dir_names = {'models', 'views', 'controllers'}
        
        score = _calculate_pattern_score(
            'mvc', pattern_def, dir_names, {}, False
        )
        
        assert score == 1.0
    
    def test_score_with_partial_required_dirs(self):
        """Should give partial score when some required dirs missing."""
        pattern_def = {
            'required': [['models'], ['views'], ['controllers']],
            'optional': [],
            'confidence_threshold': 0.8
        }
        dir_names = {'models', 'views'}  # Missing controllers
        
        score = _calculate_pattern_score(
            'mvc', pattern_def, dir_names, {}, False
        )
        
        assert 0.6 < score < 0.7  # 2/3 of required
    
    def test_score_with_optional_dirs(self):
        """Should add bonus for optional dirs."""
        pattern_def = {
            'required': [['models']],
            'optional': [['helpers'], ['utils']],
            'confidence_threshold': 0.7
        }
        dir_names = {'models', 'helpers', 'utils'}
        
        score = _calculate_pattern_score(
            'test', pattern_def, dir_names, {}, False
        )
        
        assert score == 1.0  # All required + all optional
    
    def test_microservices_with_docker_compose(self):
        """Should boost score for microservices with docker-compose."""
        pattern_def = {
            'required': [['services']],
            'optional': [],
            'confidence_threshold': 0.6
        }
        dir_names = {'services', 'user-service', 'order-service'}
        
        score = _calculate_pattern_score(
            'microservices', pattern_def, dir_names, {}, has_docker_compose=True
        )
        
        # Should get bonus for multiple services and docker-compose
        assert score > 0.8


class TestGetArchitectureConfidenceScore:
    """Tests for get_architecture_confidence_score function."""
    
    def test_confidence_for_mvc(self):
        """Should return high confidence for MVC."""
        arch_info = ArchitectureInfo(pattern='mvc')
        
        score = get_architecture_confidence_score(arch_info)
        
        assert score == 0.8
    
    def test_confidence_for_hexagonal(self):
        """Should return high confidence for hexagonal."""
        arch_info = ArchitectureInfo(pattern='hexagonal')
        
        score = get_architecture_confidence_score(arch_info)
        
        assert score == 0.8
    
    def test_confidence_for_layered(self):
        """Should return medium-high confidence for layered."""
        arch_info = ArchitectureInfo(pattern='layered')
        
        score = get_architecture_confidence_score(arch_info)
        
        assert score == 0.7
    
    def test_confidence_for_custom(self):
        """Should return medium confidence for custom."""
        arch_info = ArchitectureInfo(pattern='custom')
        
        score = get_architecture_confidence_score(arch_info)
        
        assert score == 0.5


class TestDetectMonorepo:
    """Tests for detect_monorepo function."""
    
    def test_detect_lerna_monorepo(self, tmp_path):
        """Should detect Lerna monorepo."""
        (tmp_path / 'lerna.json').write_text('{}')
        
        result = detect_monorepo(tmp_path)
        
        assert result is True
    
    def test_detect_nx_monorepo(self, tmp_path):
        """Should detect Nx monorepo."""
        (tmp_path / 'nx.json').write_text('{}')
        
        result = detect_monorepo(tmp_path)
        
        assert result is True
    
    def test_detect_pnpm_workspace(self, tmp_path):
        """Should detect pnpm workspace."""
        (tmp_path / 'pnpm-workspace.yaml').write_text('packages:\n  - packages/*')
        
        result = detect_monorepo(tmp_path)
        
        assert result is True
    
    def test_detect_multiple_package_jsons(self, tmp_path):
        """Should detect monorepo from multiple package.json files."""
        (tmp_path / 'package1').mkdir()
        (tmp_path / 'package1' / 'package.json').write_text('{}')
        (tmp_path / 'package2').mkdir()
        (tmp_path / 'package2' / 'package.json').write_text('{}')
        
        result = detect_monorepo(tmp_path)
        
        assert result is True
    
    def test_not_monorepo(self, tmp_path):
        """Should return False for non-monorepo."""
        (tmp_path / 'package.json').write_text('{}')
        
        result = detect_monorepo(tmp_path)
        
        assert result is False


class TestArchitectureInferenceIntegration:
    """Integration tests for architecture inference."""
    
    def test_realistic_django_project(self, tmp_path):
        """Should correctly analyze a Django project structure."""
        create_directory_structure(tmp_path, {
            'myapp': {
                'models': {},
                'views': {},
                'urls': {},
                'templates': {}
            },
            'static': {},
            'manage.py': {}
        })
        
        result = infer_architecture(tmp_path)
        
        # Django typically uses MVC (or MVT)
        assert result.pattern in ['mvc', 'custom']
        assert len(result.key_components) > 0
    
    def test_realistic_express_api(self, tmp_path):
        """Should correctly analyze an Express.js API structure."""
        create_directory_structure(tmp_path, {
            'src': {
                'controllers': {},
                'services': {},
                'models': {},
                'routes': {},
                'middleware': {}
            }
        })
        
        result = infer_architecture(tmp_path)
        
        assert result.pattern == 'layered'
        assert 'Src' in result.key_components
    
    def test_realistic_microservices_project(self, tmp_path):
        """Should correctly analyze a microservices project."""
        create_directory_structure(tmp_path, {
            'services': {
                'auth-service': {
                    'src': {}
                },
                'user-service': {
                    'src': {}
                },
                'api-gateway': {
                    'src': {}
                }
            },
            'shared': {}
        })
        (tmp_path / 'docker-compose.yml').write_text("""
version: '3'
services:
  auth:
    build: ./services/auth-service
  user:
    build: ./services/user-service
""")
        
        result = infer_architecture(tmp_path)
        
        assert result.pattern == 'microservices'
        assert 'Services' in result.key_components
    
    def test_realistic_clean_architecture(self, tmp_path):
        """Should correctly analyze a clean architecture project."""
        create_directory_structure(tmp_path, {
            'domain': {
                'entities': {},
                'value-objects': {}
            },
            'use-cases': {},
            'interfaces': {
                'controllers': {},
                'presenters': {}
            },
            'infrastructure': {
                'database': {},
                'external-services': {}
            }
        })
        
        result = infer_architecture(tmp_path)
        
        assert result.pattern in ['clean', 'hexagonal']
        assert 'Domain' in result.key_components
    
    def test_complex_nested_structure(self, tmp_path):
        """Should handle complex nested structures."""
        create_directory_structure(tmp_path, {
            'src': {
                'api': {
                    'v1': {
                        'controllers': {},
                        'services': {}
                    },
                    'v2': {
                        'controllers': {},
                        'services': {}
                    }
                },
                'models': {},
                'utils': {}
            },
            'tests': {},
            'docs': {}
        })
        
        result = infer_architecture(tmp_path)
        
        assert isinstance(result, ArchitectureInfo)
        assert result.pattern in ['layered', 'custom']
        # Should extract meaningful components
        assert len(result.key_components) > 0
        assert 'Tests' not in result.key_components  # Should exclude test dirs
