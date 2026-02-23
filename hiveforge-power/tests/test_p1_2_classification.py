"""Tests for CodeAnalyzer._heuristic_classify() (P1-2)."""
from pathlib import Path
import pytest
from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
from hiveforge.steering.models import PublicAPIInfo, LanguageInfo

@pytest.fixture
def lib_project(tmp_path):
    p = tmp_path / "lib"
    p.mkdir()
    (p / "utils.py").write_text("def f(): pass")
    return p

class TestHeuristicClassify:
    def test_returns_all_keys(self, lib_project):
        a = CodeAnalyzer(lib_project)
        r = a._heuristic_classify([LanguageInfo("Python", 100.0, 100)])
        assert all(k in r for k in ["project_type", "has_frontend", "has_database", "has_rest_api", "primary_language"])
    
    def test_defaults_to_library(self, lib_project):
        a = CodeAnalyzer(lib_project)
        r = a._heuristic_classify([LanguageInfo("Python", 100.0, 100)])
        assert r["project_type"] == "library"

class TestDetectDatabase:
    def test_detects_migrations(self, tmp_path):
        p = tmp_path / "p"
        p.mkdir()
        (p / "migrations").mkdir()
        assert CodeAnalyzer(p)._detect_database() is True
    
    def test_detects_models_at_root(self, tmp_path):
        p = tmp_path / "p"
        p.mkdir()
        (p / "models.py").write_text("class User: pass")
        assert CodeAnalyzer(p)._detect_database() is True
    
    def test_ignores_models_in_subdir(self, tmp_path):
        p = tmp_path / "p"
        p.mkdir()
        (p / "src").mkdir()
        (p / "src" / "models.py").write_text("class User: pass")
        assert CodeAnalyzer(p)._detect_database() is False

class TestDetectRestApi:
    def test_detects_src_api(self, tmp_path):
        p = tmp_path / "p"
        p.mkdir()
        (p / "src" / "api").mkdir(parents=True)
        assert CodeAnalyzer(p)._detect_rest_api() is True
    
    def test_detects_routes(self, tmp_path):
        p = tmp_path / "p"
        p.mkdir()
        (p / "routes").mkdir()
        assert CodeAnalyzer(p)._detect_rest_api() is True

class TestDetectFrontend:
    def test_detects_components(self, tmp_path):
        p = tmp_path / "p"
        p.mkdir()
        (p / "src" / "components").mkdir(parents=True)
        assert CodeAnalyzer(p)._detect_frontend() is True
