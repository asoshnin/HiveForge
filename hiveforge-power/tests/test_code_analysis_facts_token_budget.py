"""
Property test for CodeAnalysisFacts token budget.

Tests that CodeAnalysisFacts.to_json_dict() never exceeds 2,000 tokens
when serialized to JSON.

Requirements: 2.5
"""

import json
from pathlib import Path

from hiveforge.steering.models import CodeAnalysisFacts, NamingConventions, Dependency


class TestCodeAnalysisFactsTokenBudget:
    """
    Property 5 (partial): Token budget never exceeded.
    
    For any codebase, CodeAnalysisFacts.to_json_dict() serialized to JSON
    string must be ≤2,000 tokens.
    
    Requirements: 2.5
    """
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count using rough heuristic: 1 token ≈ 4 characters.
        
        This is a conservative estimate that matches the implementation
        in the codebase.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def test_minimal_facts_within_budget(self):
        """
        Test that minimal CodeAnalysisFacts is within token budget.
        
        Requirements: 2.5
        """
        facts = CodeAnalysisFacts(
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
        
        json_str = json.dumps(facts.to_json_dict())
        token_count = self._estimate_tokens(json_str)
        
        assert token_count <= 2000, (
            f"Minimal CodeAnalysisFacts exceeds token budget: "
            f"{token_count} tokens > 2000"
        )
    
    def test_typical_facts_within_budget(self):
        """
        Test that typical CodeAnalysisFacts is within token budget.
        
        Requirements: 2.5
        """
        facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI", "Typer"],
            dependencies=[
                Dependency(name="pytest", version="7.4.0", dependency_type="dev"),
                Dependency(name="openai", version="1.0.0", dependency_type="runtime"),
                Dependency(name="pathspec", version="0.11.0", dependency_type="runtime"),
            ],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=["main.py", "cli.py"],
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
                constants="UPPER_SNAKE_CASE",
                functions="snake_case",
            ),
            directory_structure="src, tests, docs, scripts",
        )
        
        json_str = json.dumps(facts.to_json_dict())
        token_count = self._estimate_tokens(json_str)
        
        assert token_count <= 2000, (
            f"Typical CodeAnalysisFacts exceeds token budget: "
            f"{token_count} tokens > 2000"
        )
    
    def test_large_facts_within_budget(self):
        """
        Test that large CodeAnalysisFacts is within token budget.
        
        This test creates a CodeAnalysisFacts with many dependencies
        and long strings to stress-test the token budget.
        
        Requirements: 2.5
        """
        # Create 50 dependencies (realistic for large projects)
        dependencies = [
            Dependency(
                name=f"dependency-{i}",
                version=f"1.{i}.0",
                dependency_type="runtime" if i % 2 == 0 else "dev"
            )
            for i in range(50)
        ]
        
        # Create 20 entry points
        entry_points = [f"module_{i}.py" for i in range(20)]
        
        # Long directory structure
        directory_structure = ", ".join([
            "src", "tests", "docs", "scripts", "config", "migrations",
            "templates", "static", "api", "models", "services", "utils",
            "controllers", "middleware", "validators", "schemas"
        ])
        
        facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI", "SQLAlchemy", "Pydantic", "Celery", "Redis"],
            dependencies=dependencies,
            architecture_pattern="microservices",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=entry_points,
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
                constants="UPPER_SNAKE_CASE",
                functions="snake_case",
            ),
            directory_structure=directory_structure,
        )
        
        json_str = json.dumps(facts.to_json_dict())
        token_count = self._estimate_tokens(json_str)
        
        assert token_count <= 2000, (
            f"Large CodeAnalysisFacts exceeds token budget: "
            f"{token_count} tokens > 2000"
        )
    
    def test_maximal_facts_within_budget(self):
        """
        Test that maximal CodeAnalysisFacts is within token budget.
        
        This test creates the largest possible CodeAnalysisFacts to ensure
        the token budget is never exceeded even in extreme cases.
        
        Requirements: 2.5
        """
        # Create 100 dependencies (extreme case)
        dependencies = [
            Dependency(
                name=f"very-long-dependency-name-{i}",
                version=f"10.{i}.{i % 10}",
                dependency_type="runtime" if i % 2 == 0 else "dev"
            )
            for i in range(100)
        ]
        
        # Create 50 entry points
        entry_points = [f"very_long_module_name_{i}.py" for i in range(50)]
        
        # Very long directory structure
        directory_structure = ", ".join([
            f"directory_{i}" for i in range(50)
        ])
        
        # Long framework names
        frameworks = [
            "FastAPI", "SQLAlchemy", "Pydantic", "Celery", "Redis",
            "Alembic", "Pytest", "Black", "Mypy", "Ruff"
        ]
        
        facts = CodeAnalysisFacts(
            primary_language="Python 3.11.5",
            frameworks=frameworks,
            dependencies=dependencies,
            architecture_pattern="microservices with event sourcing",
            has_tests=True,
            test_framework="pytest with coverage",
            api_type="REST",
            database="PostgreSQL 15.2",
            entry_points=entry_points,
            naming_conventions=NamingConventions(
                variables="snake_case with underscores",
                classes="PascalCase with prefixes",
                constants="UPPER_SNAKE_CASE with namespaces",
                functions="snake_case with verb prefixes",
            ),
            directory_structure=directory_structure,
        )
        
        json_str = json.dumps(facts.to_json_dict())
        token_count = self._estimate_tokens(json_str)
        
        # This is the critical test - even maximal facts must be within budget
        assert token_count <= 2000, (
            f"Maximal CodeAnalysisFacts exceeds token budget: "
            f"{token_count} tokens > 2000. "
            f"The implementation needs to truncate or limit data to stay within budget."
        )
    
    def test_json_serialization_succeeds(self):
        """
        Test that to_json_dict() always produces valid JSON.
        
        Requirements: 2.1, 2.2
        """
        facts = CodeAnalysisFacts(
            primary_language="Python 3.11",
            frameworks=["FastAPI"],
            dependencies=[
                Dependency(name="pytest", version="7.4.0", dependency_type="dev"),
            ],
            architecture_pattern="layered",
            has_tests=True,
            test_framework="pytest",
            api_type="REST",
            database="PostgreSQL",
            entry_points=["main.py"],
            naming_conventions=NamingConventions(
                variables="snake_case",
                classes="PascalCase",
            ),
            directory_structure="src, tests",
        )
        
        # Should not raise exception
        json_dict = facts.to_json_dict()
        json_str = json.dumps(json_dict)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        
        assert isinstance(parsed, dict)
        assert "primary_language" in parsed
        assert "frameworks" in parsed
        assert "dependencies" in parsed
    
    def test_empty_lists_within_budget(self):
        """
        Test that CodeAnalysisFacts with empty lists is within budget.
        
        Requirements: 2.5
        """
        facts = CodeAnalysisFacts(
            primary_language="Unknown",
            frameworks=[],
            dependencies=[],
            architecture_pattern="unknown",
            has_tests=False,
            test_framework=None,
            api_type=None,
            database=None,
            entry_points=[],
            naming_conventions=NamingConventions(),
            directory_structure="",
        )
        
        json_str = json.dumps(facts.to_json_dict())
        token_count = self._estimate_tokens(json_str)
        
        assert token_count <= 2000, (
            f"Empty CodeAnalysisFacts exceeds token budget: "
            f"{token_count} tokens > 2000"
        )
