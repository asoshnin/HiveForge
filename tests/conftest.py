"""Shared pytest fixtures for hiveforge tests."""
import pytest
from pathlib import Path


@pytest.fixture
def sample_project_name():
    """Sample valid project name."""
    return "test-project"


@pytest.fixture
def invalid_project_names():
    """List of invalid project names for testing."""
    return [
        "Bad Name",        # spaces
        "test_project",    # underscores
        "TestProject",     # PascalCase
        "test.project",    # dots
        "123-start",       # starts with number
        "",                # empty
    ]


@pytest.fixture
def template_dir():
    """Path to templates directory."""
    return Path(__file__).parent.parent / "src" / "hiveforge" / "templates"


@pytest.fixture
def expected_agent_files():
    """List of expected agent filenames."""
    return [
        "orchestrator.md",
        "data_architect.md",
        "backend_engineer.md",
        "frontend_engineer.md",
        "qa_engineer.md",
        "devops_engineer.md",
        "red_team.md",
    ]


@pytest.fixture
def expected_steering_files():
    """List of expected steering filenames."""
    return [
        "project-vision.md",
        "tech-stack.md",
        "conventions.md",
        "architecture.md",
        "db-standards.md",
        "api-standards.md",
        "ui-standards.md",
        "qa-standards.md",
    ]
