"""
Tests for tech stack extraction module.

This module tests the tech stack extraction functionality to ensure it correctly
parses dependency files, identifies frameworks, databases, and ORMs.
"""

import json
import pytest
from pathlib import Path

from src.hiveforge.steering.analyzers.tech_stack_extractor import (
    extract_tech_stack,
    get_tech_stack_confidence_scores,
    _parse_package_json,
    _parse_requirements_txt,
    _parse_pyproject_toml,
    _parse_go_mod,
    _parse_cargo_toml,
)
from src.hiveforge.steering.models import TechStackInfo, Dependency


class TestExtractTechStack:
    """Tests for extract_tech_stack function."""
    
    def test_extract_from_package_json(self, tmp_path):
        """Should extract tech stack from package.json."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "myapp",
            "dependencies": {
                "react": "^18.2.0",
                "express": "^4.18.0"
            }
        }))
        
        result = extract_tech_stack(tmp_path)
        
        assert result.frontend_framework == "React"
        assert result.backend_framework == "Express"
        assert len(result.dependencies) == 2
    
    def test_extract_from_requirements_txt(self, tmp_path):
        """Should extract tech stack from requirements.txt."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("""
fastapi==0.100.0
sqlalchemy==2.0.0
redis==4.5.0
""")
        
        result = extract_tech_stack(tmp_path)
        
        assert result.backend_framework == "FastAPI"
        assert result.cache == "Redis"
        assert len(result.dependencies) == 3
    
    def test_extract_from_pyproject_toml(self, tmp_path):
        """Should extract tech stack from pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("""
[project]
dependencies = [
    "django>=4.2.0",
    "psycopg2>=2.9.0"
]
""")
        
        result = extract_tech_stack(tmp_path)
        
        assert result.backend_framework == "Django"
        assert result.database == "PostgreSQL"
    
    def test_extract_from_go_mod(self, tmp_path):
        """Should extract tech stack from go.mod."""
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("""
module example.com/myapp

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
    gorm.io/gorm v1.25.0
)
""")
        
        result = extract_tech_stack(tmp_path)
        
        assert result.backend_framework == "Gin"
        assert len(result.dependencies) == 2
    
    def test_extract_from_cargo_toml(self, tmp_path):
        """Should extract tech stack from Cargo.toml."""
        cargo_toml = tmp_path / "Cargo.toml"
        cargo_toml.write_text("""
[package]
name = "myapp"

[dependencies]
actix-web = "4.3.0"
diesel = "2.1.0"
""")
        
        result = extract_tech_stack(tmp_path)
        
        assert result.backend_framework == "Actix"
        assert len(result.dependencies) == 2
    
    def test_extract_empty_directory(self, tmp_path):
        """Should return empty tech stack for directory with no dependency files."""
        result = extract_tech_stack(tmp_path)
        
        assert isinstance(result, TechStackInfo)
        assert result.backend_framework is None
        assert result.frontend_framework is None
        assert len(result.dependencies) == 0
    
    def test_extract_fullstack_project(self, tmp_path):
        """Should extract both frontend and backend frameworks."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "dependencies": {
                "react": "^18.2.0",
                "next": "^13.0.0"
            }
        }))
        
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("fastapi==0.100.0\n")
        
        result = extract_tech_stack(tmp_path)
        
        assert result.frontend_framework in ["React", "Next.js"]
        assert result.backend_framework == "FastAPI"


class TestParsePackageJson:
    """Tests for _parse_package_json function."""
    
    def test_parse_dependencies(self, tmp_path):
        """Should parse dependencies from package.json."""
        file_path = tmp_path / "package.json"
        file_path.write_text(json.dumps({
            "dependencies": {
                "express": "^4.18.0",
                "react": "^18.2.0"
            }
        }))
        
        result = _parse_package_json(file_path)
        
        assert len(result) == 2
        assert any(dep.name == "express" for dep in result)
        assert any(dep.name == "react" for dep in result)
    
    def test_parse_dev_dependencies(self, tmp_path):
        """Should parse devDependencies separately."""
        file_path = tmp_path / "package.json"
        file_path.write_text(json.dumps({
            "dependencies": {
                "express": "^4.18.0"
            },
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }))
        
        result = _parse_package_json(file_path)
        
        assert len(result) == 2
        express_dep = next(dep for dep in result if dep.name == "express")
        jest_dep = next(dep for dep in result if dep.name == "jest")
        
        assert express_dep.dependency_type == "runtime"
        assert jest_dep.dependency_type == "dev"
    
    def test_parse_version_prefixes(self, tmp_path):
        """Should strip version prefixes like ^, ~, >=."""
        file_path = tmp_path / "package.json"
        file_path.write_text(json.dumps({
            "dependencies": {
                "pkg1": "^1.0.0",
                "pkg2": "~2.0.0",
                "pkg3": ">=3.0.0"
            }
        }))
        
        result = _parse_package_json(file_path)
        
        assert all(not dep.version.startswith(('^', '~', '>=', '<')) for dep in result if dep.version)


class TestParseRequirementsTxt:
    """Tests for _parse_requirements_txt function."""
    
    def test_parse_simple_requirements(self, tmp_path):
        """Should parse simple requirements."""
        file_path = tmp_path / "requirements.txt"
        file_path.write_text("""
flask==2.0.0
django>=4.2.0
requests~=2.28.0
""")
        
        result = _parse_requirements_txt(file_path)
        
        assert len(result) == 3
        assert any(dep.name == "flask" and dep.version == "2.0.0" for dep in result)
    
    def test_parse_with_comments(self, tmp_path):
        """Should skip comments."""
        file_path = tmp_path / "requirements.txt"
        file_path.write_text("""
# This is a comment
flask==2.0.0
# Another comment
django>=4.2.0
""")
        
        result = _parse_requirements_txt(file_path)
        
        assert len(result) == 2
    
    def test_parse_with_empty_lines(self, tmp_path):
        """Should skip empty lines."""
        file_path = tmp_path / "requirements.txt"
        file_path.write_text("""
flask==2.0.0

django>=4.2.0

""")
        
        result = _parse_requirements_txt(file_path)
        
        assert len(result) == 2


class TestParsePyprojectToml:
    """Tests for _parse_pyproject_toml function."""
    
    def test_parse_project_dependencies(self, tmp_path):
        """Should parse project dependencies."""
        file_path = tmp_path / "pyproject.toml"
        file_path.write_text("""
[project]
dependencies = [
    "fastapi>=0.100.0",
    "sqlalchemy>=2.0.0"
]
""")
        
        result = _parse_pyproject_toml(file_path)
        
        assert len(result) == 2
        assert any(dep.name == "fastapi" for dep in result)
    
    def test_parse_optional_dependencies(self, tmp_path):
        """Should parse optional dependencies."""
        file_path = tmp_path / "pyproject.toml"
        file_path.write_text("""
[project]
dependencies = ["fastapi>=0.100.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
""")
        
        result = _parse_pyproject_toml(file_path)
        
        assert len(result) == 2
        pytest_dep = next(dep for dep in result if dep.name == "pytest")
        assert pytest_dep.dependency_type == "optional"


class TestParseGoMod:
    """Tests for _parse_go_mod function."""
    
    def test_parse_go_dependencies(self, tmp_path):
        """Should parse Go dependencies."""
        file_path = tmp_path / "go.mod"
        file_path.write_text("""
module example.com/myapp

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/pkg/errors v0.9.1
)
""")
        
        result = _parse_go_mod(file_path)
        
        assert len(result) == 2
        assert any("gin-gonic/gin" in dep.name for dep in result)
        assert any(dep.version == "1.9.0" for dep in result)


class TestParseCargoToml:
    """Tests for _parse_cargo_toml function."""
    
    def test_parse_rust_dependencies(self, tmp_path):
        """Should parse Rust dependencies."""
        file_path = tmp_path / "Cargo.toml"
        file_path.write_text("""
[package]
name = "myapp"

[dependencies]
actix-web = "4.3.0"
serde = "1.0"
""")
        
        result = _parse_cargo_toml(file_path)
        
        assert len(result) == 2
        assert any(dep.name == "actix-web" and dep.version == "4.3.0" for dep in result)
    
    def test_parse_dev_dependencies(self, tmp_path):
        """Should parse dev-dependencies."""
        file_path = tmp_path / "Cargo.toml"
        file_path.write_text("""
[dependencies]
actix-web = "4.3.0"

[dev-dependencies]
tokio-test = "0.4"
""")
        
        result = _parse_cargo_toml(file_path)
        
        assert len(result) == 2
        test_dep = next(dep for dep in result if dep.name == "tokio-test")
        assert test_dep.dependency_type == "dev"


class TestGetTechStackConfidenceScores:
    """Tests for get_tech_stack_confidence_scores function."""
    
    def test_confidence_scores_for_found_components(self):
        """Should return 1.0 confidence for components found in dependencies."""
        tech_stack = TechStackInfo(
            backend_framework="FastAPI",
            frontend_framework="React",
            database="PostgreSQL",
            cache="Redis"
        )
        
        scores = get_tech_stack_confidence_scores(tech_stack)
        
        assert scores['backend_framework'] == 1.0
        assert scores['frontend_framework'] == 1.0
        assert scores['database'] == 1.0
        assert scores['cache'] == 1.0
    
    def test_confidence_scores_for_partial_stack(self):
        """Should only include scores for found components."""
        tech_stack = TechStackInfo(
            backend_framework="FastAPI"
        )
        
        scores = get_tech_stack_confidence_scores(tech_stack)
        
        assert 'backend_framework' in scores
        assert 'frontend_framework' not in scores
        assert 'database' not in scores


class TestTechStackIntegration:
    """Integration tests for tech stack extraction."""
    
    def test_realistic_python_fastapi_project(self, tmp_path):
        """Should correctly analyze a FastAPI project."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("""
fastapi==0.100.0
uvicorn==0.23.0
sqlalchemy==2.0.0
psycopg2-binary==2.9.0
redis==4.5.0
""")
        
        result = extract_tech_stack(tmp_path)
        
        assert result.backend_framework == "FastAPI"
        assert result.database == "PostgreSQL"
        assert result.cache == "Redis"
        assert len(result.dependencies) == 5
        
        scores = get_tech_stack_confidence_scores(result)
        assert all(score == 1.0 for score in scores.values())
    
    def test_realistic_nodejs_express_project(self, tmp_path):
        """Should correctly analyze an Express.js project."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "name": "myapp",
            "dependencies": {
                "express": "^4.18.0",
                "pg": "^8.11.0",
                "ioredis": "^5.3.0"
            },
            "devDependencies": {
                "jest": "^29.0.0"
            }
        }))
        
        result = extract_tech_stack(tmp_path)
        
        assert result.backend_framework == "Express"
        assert result.database == "PostgreSQL"
        assert result.cache == "Redis"
        assert len(result.dependencies) == 4
    
    def test_realistic_fullstack_nextjs_project(self, tmp_path):
        """Should correctly analyze a Next.js fullstack project."""
        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({
            "dependencies": {
                "next": "^13.0.0",
                "react": "^18.2.0",
                "prisma": "^5.0.0"
            }
        }))
        
        result = extract_tech_stack(tmp_path)
        
        # Should detect Next.js (which includes React)
        assert result.frontend_framework in ["Next.js", "React"]
        assert len(result.dependencies) == 3
