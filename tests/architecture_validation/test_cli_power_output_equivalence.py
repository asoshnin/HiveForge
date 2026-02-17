
"""
Test CLI/Power Output Equivalence

**Validates: Requirements 1.1, 1.2, 1.3**

This test module validates that CLI and Power tools produce identical file outputs
given the same inputs. This is the core architectural claim that both interfaces
use the same shared backend.

Architecture Validation Criteria:
- CLI/Power Output Equivalence: 100% identical file outputs for same inputs
- Shared Backend Utilization: > 95% code shared between CLI and Power
- Error Handling Parity: Identical error handling for both interfaces

Test Cases Reference:
- EQ-01: init_steering equivalence
- EQ-02: update_steering equivalence
- EQ-03: validate_steering equivalence
- EQ-04: reset_steering equivalence
- EQ-05: discover_docs equivalence

Phase: 1.2 Integration Test Suite for Architecture Validation
Implementation: Phase 4.5 (when both interfaces are available)
"""

import pytest
import asyncio
import json
import shutil
import subprocess
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from unittest.mock import Mock, patch, AsyncMock
# =============================================================================
# Test Fixtures
# =============================================================================
# Fixtures provide consistent test data and environments for all validation tests.
# See design.md Section 8 for fixture specifications.

@pytest.fixture
def python_flask_project(tmp_path: Path) -> Path:
    """Create a Python Flask project fixture for equivalence testing.
    
    Use Cases: EQ-01, SB-01, PF-01
    Success Criteria: Project has app.py, requirements.txt, README.md
    """
    project = tmp_path / "python_flask"
    project.mkdir()
    
    (project / "app.py").write_text(
        '# Flask Application\n'
        'from flask import Flask\n'
        'app = Flask(__name__)\n'
        '\n'
        '@app.route("/")\n'
        'def index():\n'
        '    return "Hello, World!"\n'
    )
    
    (project / "requirements.txt").write_text(
        'flask>=2.0.0\n'
        'pytest>=7.0.0\n'
        'gunicorn>=20.0.0\n'
    )
    
    (project / "README.md").write_text(
        '# Flask App\n'
        '\n'
        'A simple Flask application for testing.\n'
        '\n'
        '## Features\n'
        '- Web endpoint\n'
        '- Test coverage\n'
    )
    
    return project


@pytest.fixture
def node_express_project(tmp_path: Path) -> Path:
    """Create a Node.js Express project fixture for equivalence testing.
    
    Use Cases: EQ-01, SB-01, PF-01
    Success Criteria: Project has index.js, package.json, README.md
    """
    project = tmp_path / "node_express"
    project.mkdir()
    
    (project / "index.js").write_text(
        'const express = require("express");\n'
        'const app = express();\n'
        '\n'
        'app.get("/", (req, res) => {\n'
        '    res.send("Hello, World!");\n'
        '});\n'
        '\n'
        'module.exports = app;\n'
    )
    
    (project / "package.json").write_text(
        '{\n'
        '  "name": "express-app",\n'
        '  "version": "1.0.0",\n'
        '  "main": "index.js",\n'
        '  "dependencies": {\n'
        '    "express": "^4.18.0"\n'
        '  }\n'
        '}\n'
    )
    
    (project / "README.md").write_text(
        '# Express App\n'
        '\n'
        'A simple Express application for testing.\n'
    )
    
    return project


@pytest.fixture
def django_project(tmp_path: Path) -> Path:
    """Create a Django project fixture for equivalence testing.
    
    Use Cases: EQ-01, SB-01, PF-01
    Success Criteria: Project has settings.py, urls.py, manage.py
    """
    project = tmp_path / "django_project"
    project.mkdir()
    
    (project / "settings.py").write_text(
        '# Django Settings\n'
        'SECRET_KEY = "test-secret-key"\n'
        'DEBUG = True\n'
        'INSTALLED_APPS = ["django.contrib.contenttypes"]\n'
        'DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}\n'
    )
    
    (project / "urls.py").write_text(
        'from django.urls import path\n'
        'from . import views\n'
        '\n'
        'urlpatterns = [\n'
        '    path("", views.index),\n'
        ']\n'
    )
    
    (project / "manage.py").write_text(
        '#!/usr/bin/env python\n'
        'import os\n'
        'import sys\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")\n'
        '    from django.core.management import execute_from_command_line\n'
        '    execute_from_command_line(sys.argv)\n'
    )
    
    (project / "README.md").write_text(
        '# Django Project\n'
        '\n'
        'A simple Django project for testing.\n'
    )
    
    return project


@pytest.fixture
def go_microservice(tmp_path: Path) -> Path:
    """Create a Go microservice project fixture for equivalence testing.
    
    Use Cases: EQ-01, SB-01, PF-01
    Success Criteria: Project has go.mod, main.go, README.md
    """
    project = tmp_path / "go_microservice"
    project.mkdir()
    
    (project / "main.go").write_text(
        'package main\n'
        '\n'
        'import (\n'
        '    "fmt"\n'
        '    "net/http"\n'
        ')\n'
        '\n'
        'func main() {\n'
        '    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {\n'
        '        fmt.Fprintf(w, "Hello, World!")\n'
        '    })\n'
        '    http.ListenAndServe(":8080", nil)\n'
        '}\n'
    )
    
    (project / "go.mod").write_text(
        'module github.com/example/microservice\n'
        '\n'
        'go 1.21\n'
        '\n'
        'require (\n'
        '    github.com/gorilla/mux v1.8.0\n'
        ')\n'
    )
    
    (project / "README.md").write_text(
        '# Go Microservice\n'
        '\n'
        'A simple Go microservice for testing.\n'
    )
    
    return project


@pytest.fixture
def empty_project(tmp_path: Path) -> Path:
    """Create an empty project fixture for baseline testing.
    
    Use Cases: EQ-01, PF-01
    Success Criteria: Project has only a README.md
    """
    project = tmp_path / "empty_project"
    project.mkdir()
    
    (project / "README.md").write_text(
        '# Empty Project\n'
        '\n'
        'A project with no existing documentation.\n'
    )
    
    return project


@pytest.fixture
def existing_steering_project(tmp_path: Path) -> Path:
    """Create a project with existing steering files for update/reset testing.
    
    Use Cases: EQ-02, EQ-03, EQ-04
    Success Criteria: Project has .kiro/steering/ with existing files
    """
    project = tmp_path / "existing_steering"
    project.mkdir()
    
    steering_dir = project / ".kiro" / "steering"
    steering_dir.mkdir(parents=True)
    
    (steering_dir / "tech-stack.md").write_text(
        '# Technology Stack\n'
        '\n'
        '## Core Technologies\n'
        '\n'
        '### Backend\n'
        '- **Language:** Python 3.11\n'
        '- **Framework:** FastAPI\n'
        '\n'
        '## Key Dependencies\n'
        '| Purpose | Library | Version |\n'
        '|---------|---------|--------|\n'
        '| Web | FastAPI | 0.100.0 |\n'
    )
    
    (steering_dir / "conventions.md").write_text(
        '# Coding Conventions\n'
        '\n'
        '## General Principles\n'
        '1. Readability over cleverness\n'
        '2. Explicit over implicit\n'
        '\n'
        '## Naming Conventions\n'
        '- snake_case for variables and functions\n'
        '- PascalCase for classes\n'
    )
    
    (steering_dir / "architecture.md").write_text(
        '# Architecture Overview\n'
        '\n'
        '## System Diagram\n'
        '```mermaid\n'
        'graph TD\n'
        '    User --> API\n'
        '    API --> Service\n'
        '```\n'
    )
    
    return project


@pytest.fixture
def large_project(tmp_path: Path) -> Path:
    """Create a large project fixture for performance testing.
    
    Use Cases: PF-04, PF-05
    Success Criteria: Project has 100+ files across multiple directories
    """
    project = tmp_path / "large_project"
    project.mkdir()
    
    # Create multiple subdirectories with files
    for i in range(10):
        subdir = project / f"src" / f"module_{i}"
        subdir.mkdir(parents=True)
        
        for j in range(10):
            (subdir / f"file_{j}.py").write_text(
                f'# Module {i}, File {j}\n'
                f'def function_{i}_{j}():\n'
                f'    """Function {i}_{j} implementation."""\n'
                f'    return {i} + {j}\n'
            )
    
    (project / "requirements.txt").write_text(
        '\n'.join([f'package{i}>=1.0.0' for i in range(20)])
    )
    
    (project / "README.md").write_text(
        '# Large Project\n'
        '\n'
        'A project with many files for performance testing.\n'
    )
    
    return project


@pytest.fixture
def python_project(tmp_path: Path) -> Path:
    """Alias for python_flask_project for backward compatibility."""
    return python_flask_project(tmp_path)
# =============================================================================
# Helper Functions
# =============================================================================
# Helper functions for running CLI commands and MCP tools, and comparing outputs.


def run_cli_command(
    args: List[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 300
) -> subprocess.CompletedProcess:
    """Run a CLI command and return the result.
    
    Args:
        args: Command arguments (e.g., ["steering", "init", "--autonomous"])
        cwd: Working directory (defaults to current directory)
        env: Environment variables
        timeout: Command timeout in seconds
    
    Returns:
        CompletedProcess with returncode, stdout, and stderr
    
    Success Criteria:
        - Command executes without exception
        - Return code reflects success/failure
        - Output is captured correctly
    """
    import subprocess
    
    default_env = {"PYTHONPATH": str(Path(__file__).parent.parent.parent)}
    if env:
        default_env.update(env)
    
    try:
        result = subprocess.run(
            ["hiveforge"] + args,
            cwd=cwd,
            env=default_env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=["hiveforge"] + args,
            returncode=-1,
            stdout="",
            stderr="Command timed out"
        )
    except Exception as e:
        return subprocess.CompletedProcess(
            args=["hiveforge"] + args,
            returncode=-1,
            stdout="",
            stderr=str(e)
        )


async def run_mcp_tool(
    tool_name: str,
    **kwargs: Any
) -> Dict[str, Any]:
    """Run an MCP tool and return the result.
    
    Args:
        tool_name: Name of the MCP tool (e.g., "init_steering")
        **kwargs: Tool parameters
    
    Returns:
        Dictionary with tool response
    
    Success Criteria:
        - Tool executes without exception
        - Response has required fields (status, message)
        - Error responses are properly formatted
    """
    # Simulated MCP tool call for Phase 1.2 specifications
    # Actual implementation in Phase 4.5 when MCP server is available
    
    # This is a placeholder that will be replaced with actual MCP client
    mock_responses = {
        "init_steering": {
            "status": "success",
            "files_created": ["CONVENTIONS.md", "ARCHITECTURE.md", "TECH-STACK.md"],
            "message": "Generated 3 steering files"
        },
        "update_steering": {
            "status": "success",
            "files_updated": 2,
            "message": "Updated 2 steering files"
        },
        "validate_steering": {
            "status": "success",
            "validation_results": {"passed": True, "issues": []},
            "message": "Validation passed"
        },
        "reset_steering": {
            "status": "success",
            "files_reset": 1,
            "backup_created": True,
            "message": "Reset 1 file to default template"
        },
        "discover_project_docs": {
            "status": "success",
            "found": [{"path": "README.md", "type": "readme", "relevance": 0.95}],
            "message": "Found 1 document"
        }
    }
    
    # Return mock response for specification purposes
    # In Phase 4.5, this will be replaced with actual MCP client call
    return mock_responses.get(tool_name, {"status": "failed", "message": "Unknown tool"})


def compare_file_outputs(
    cli_dir: Path,
    power_dir: Path
) -> Dict[str, Any]:
    """Compare file outputs between CLI and Power runs.
    
    Args:
        cli_dir: Directory containing CLI-generated files
        power_dir: Directory containing Power-generated files
    
    Returns:
        Dictionary with comparison results:
        - identical: bool
        - matching_files: List[str]
        - differing_files: List[str]
        - missing_in_cli: List[str]
        - missing_in_power: List[str]
    
    Success Criteria:
        - All files are byte-for-byte identical
        - No extra or missing files
        - File metadata may differ but content must match
    """
    if not cli_dir.exists():
        return {
            "identical": False,
            "error": "CLI directory does not exist"
        }
    
    if not power_dir.exists():
        return {
            "identical": False,
            "error": "Power directory does not exist"
        }
    
    cli_files = set(f.name for f in cli_dir.iterdir() if f.is_file())
    power_files = set(f.name for f in power_dir.iterdir() if f.is_file())
    
    matching_files = []
    differing_files = []
    missing_in_cli = power_files - cli_files
    missing_in_power = cli_files - power_files
    
    for filename in cli_files & power_files:
        cli_content = (cli_dir / filename).read_text()
        power_content = (power_dir / filename).read_text()
        
        if cli_content == power_content:
            matching_files.append(filename)
        else:
            differing_files.append(filename)
    
    return {
        "identical": len(differing_files) == 0 and len(missing_in_cli) == 0 and len(missing_in_power) == 0,
        "matching_files": matching_files,
        "differing_files": differing_files,
        "missing_in_cli": list(missing_in_cli),
        "missing_in_power": list(missing_in_power),
        "cli_file_count": len(cli_files),
        "power_file_count": len(power_files)
    }


def get_steering_files(project_dir: Path) -> Dict[str, str]:
    """Get all steering files and their contents from a project.
    
    Args:
        project_dir: Path to project root
    
    Returns:
        Dictionary mapping filename to content
    
    Success Criteria:
        - All .kiro/steering/*.md files are captured
        - Content is read correctly
    """
    steering_dir = project_dir / ".kiro" / "steering"
    
    if not steering_dir.exists():
        return {}
    
    files = {}
    for filepath in steering_dir.glob("*.md"):
        files[filepath.name] = filepath.read_text()
    
    return files


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single run."""
    elapsed_time: float
    peak_memory_mb: float
    cpu_time: float
    files_created: int
    files_modified: int


def measure_performance(
    func,
    *args,
    **kwargs
) -> PerformanceMetrics:
    """Measure the performance of a function call.
    
    Args:
        func: Function to measure
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function
    
    Returns:
        PerformanceMetrics with timing and resource usage
    
    Success Criteria:
        - Elapsed time is measured accurately
        - Peak memory is captured
        - CPU time is tracked
    """
    import time
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    start_time = time.time()
    start_memory = process.memory_info().rss / (1024 * 1024)
    start_cpu = process.cpu_times()
    
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        result = None
    
    end_time = time.time()
    end_memory = process.memory_info().rss / (1024 * 1024)
    end_cpu = process.cpu_times()
    
    return PerformanceMetrics(
        elapsed_time=end_time - start_time,
        peak_memory_mb=max(start_memory, end_memory),
        cpu_time=end_cpu.user - start_cpu.user + end_cpu.system - start_cpu.system,
        files_created=0,
        files_modified=0
    )
# =============================================================================
# Test Classes
# =============================================================================
# Test classes organized by tool and test category.


class TestCLIOutputEquivalence:
    """Test that CLI commands produce expected outputs.
    
    **Validates: Requirements FR-5 (CLI Backward Compatibility)**
    
    Success Criteria:
        - All CLI commands execute successfully
        - Expected files are created
        - Output format is correct
    """
    
    def test_init_command_produces_expected_files(
        self,
        python_project: Path
    ):
        """Test that 'steering init' creates expected files.
        
        Test ID: CLI-EQ-01
        Input: python_project with app.py, requirements.txt
        Expected: CONVENTIONS.md, ARCHITECTURE.md, TECH-STACK.md created
        """
        result = run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        steering_dir = python_project / ".kiro" / "steering"
        assert steering_dir.exists(), "Steering directory was not created"
        
        expected_files = ["CONVENTIONS.md", "ARCHITECTURE.md", "TECH-STACK.md"]
        for filename in expected_files:
            assert (steering_dir / filename).exists(), \
                f"Expected file {filename} was not created"
    
    def test_init_command_with_custom_options(
        self,
        python_project: Path
    ):
        """Test init with custom options (no auto-discover, no autonomous).
        
        Test ID: CLI-EQ-02
        Input: python_project with --no-auto-discover --no-autonomous
        Expected: Files created with default content
        """
        result = run_cli_command(
            ["steering", "init", "--no-auto-discover", "--no-autonomous"],
            cwd=python_project
        )
        
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        
        steering_dir = python_project / ".kiro" / "steering"
        assert steering_dir.exists()
        assert (steering_dir / "CONVENTIONS.md").exists()
    
    def test_update_command_produces_expected_diff(
        self,
        existing_steering_project: Path
    ):
        """Test that 'steering update' produces expected changes.
        
        Test ID: CLI-EQ-03
        Input: existing_steering_project with steering files
        Expected: Files updated, customizations preserved
        """
        # First, initialize to ensure we have a baseline
        result = run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=existing_steering_project
        )
        assert result.returncode == 0
        
        # Then update
        result = run_cli_command(
            ["steering", "update", "--incremental", "--no-interactive"],
            cwd=existing_steering_project
        )
        
        assert result.returncode == 0, f"Update failed: {result.stderr}"
        
        steering_dir = existing_steering_project / ".kiro" / "steering"
        # Update should modify files, not create unexpected new ones
        assert (steering_dir / "CONVENTIONS.md").exists()
    
    def test_update_command_preserves_customizations(
        self,
        existing_steering_project: Path
    ):
        """Test that update preserves user customizations.
        
        Test ID: CLI-EQ-04
        Input: existing_steering_project with custom content
        Expected: Custom content is preserved after update
        """
        # Add custom content to a file
        conventions_file = (
            existing_steering_project / ".kiro" / "steering" / "conventions.md"
        )
        custom_section = "\n\n## Custom Section\nThis is custom content.\n"
        original_content = conventions_file.read_text()
        conventions_file.write_text(original_content + custom_section)
        
        # Run update
        result = run_cli_command(
            ["steering", "update", "--incremental", "--no-interactive"],
            cwd=existing_steering_project
        )
        
        assert result.returncode == 0
        
        # Verify custom content is preserved
        updated_content = conventions_file.read_text()
        assert "## Custom Section" in updated_content, \
            "Custom content was not preserved during update"
    
    def test_validate_command_returns_expected_status(
        self,
        python_project: Path
    ):
        """Test that 'steering validate' returns expected validation status.
        
        Test ID: CLI-EQ-05
        Input: python_project with initialized steering files
        Expected: JSON output with status and validation_results
        """
        # First initialize
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        # Then validate
        result = run_cli_command(
            ["steering", "validate", "--json"],
            cwd=python_project
        )
        
        assert result.returncode == 0, f"Validate failed: {result.stderr}"
        
        output = json.loads(result.stdout)
        assert "status" in output, "Missing 'status' in output"
        assert "validation_results" in output, "Missing 'validation_results' in output"
        assert output["status"] in ["passed", "failed", "warning"]
    
    def test_validate_command_strict_mode(
        self,
        python_project: Path
    ):
        """Test validate with strict mode (warnings as errors).
        
        Test ID: CLI-EQ-06
        Input: python_project with --strict flag
        Expected: Strict validation results
        """
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        result = run_cli_command(
            ["steering", "validate", "--json", "--strict"],
            cwd=python_project
        )
        
        assert result.returncode == 0 or result.returncode == 1
        output = json.loads(result.stdout)
        assert "strict" in output or "issues" in output
    
    def test_reset_command_creates_backup(
        self,
        existing_steering_project: Path
    ):
        """Test that 'steering reset' creates a backup before resetting.
        
        Test ID: CLI-EQ-07
        Input: existing_steering_project with --confirm flag
        Expected: Backup created, file reset to template
        """
        result = run_cli_command(
            ["steering", "reset", "--file", "conventions.md", "--confirm"],
            cwd=existing_steering_project
        )
        
        assert result.returncode == 0, f"Reset failed: {result.stderr}"
        
        # Verify backup was created
        backups_dir = existing_steering_project / ".kiro" / "backups"
        assert backups_dir.exists(), "Backup directory was not created"
        
        # Verify file was reset (should have template content)
        conventions_file = (
            existing_steering_project / ".kiro" / "steering" / "conventions.md"
        )
        content = conventions_file.read_text()
        assert "## Coding Conventions" in content, \
            "File was not properly reset to template"
    
    def test_discover_command_finds_docs(
        self,
        python_project: Path
    ):
        """Test that 'steering discover' finds existing documentation.
        
        Test ID: CLI-EQ-08
        Input: python_project with README.md, requirements.txt
        Expected: Discovery results with found documents
        """
        result = run_cli_command(
            ["steering", "discover", "--json"],
            cwd=python_project
        )
        
        assert result.returncode == 0, f"Discover failed: {result.stderr}"
        
        output = json.loads(result.stdout)
        assert "found" in output, "Missing 'found' in output"
        assert isinstance(output["found"], list), "'found' should be a list"
        
        # Should find README.md
        found_paths = [doc.get("path", "") for doc in output["found"]]
        assert any("README" in path for path in found_paths), \
            "README.md was not discovered"
class TestPowerOutputEquivalence:
    """Test that Power tools produce expected outputs.
    
    **Validates: Requirements FR-3 (MCP Tools Implementation)**
    
    Success Criteria:
        - All MCP tools execute successfully
        - Expected files are created
        - Response format is correct for MCP protocol
    """
    
    @pytest.mark.asyncio
    async def test_init_tool_produces_expected_files(
        self,
        python_project: Path
    ):
        """Test that init_steering tool creates expected files.
        
        Test ID: PWR-EQ-01
        Input: python_project, auto_discover=True, autonomous=True
        Expected: CONVENTIONS.md, ARCHITECTURE.md, TECH-STACK.md created
        """
        result = await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(python_project)
        )
        
        assert result["status"] == "success", \
            f"Tool failed: {result.get('message', 'Unknown error')}"
        
        steering_dir = python_project / ".kiro" / "steering"
        assert steering_dir.exists(), "Steering directory was not created"
        
        expected_files = ["CONVENTIONS.md", "ARCHITECTURE.md", "TECH-STACK.md"]
        for filename in expected_files:
            assert (steering_dir / filename).exists(), \
                f"Expected file {filename} was not created"
    
    @pytest.mark.asyncio
    async def test_init_tool_with_custom_options(
        self,
        python_project: Path
    ):
        """Test init_steering with custom options.
        
        Test ID: PWR-EQ-02
        Input: python_project, confidence_threshold=0.9
        Expected: Files created with high confidence threshold
        """
        result = await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            confidence_threshold=0.9,
            project_root=str(python_project)
        )
        
        assert result["status"] == "success"
        assert "files_created" in result
        assert isinstance(result["files_created"], list)
    
    @pytest.mark.asyncio
    async def test_update_tool_produces_expected_changes(
        self,
        existing_steering_project: Path
    ):
        """Test that update_steering tool produces expected changes.
        
        Test ID: PWR-EQ-03
        Input: existing_steering_project, incremental=True
        Expected: Files updated, response indicates success
        """
        # First initialize
        await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(existing_steering_project)
        )
        
        # Then update
        result = await run_mcp_tool(
            "update_steering",
            incremental=True,
            project_root=str(existing_steering_project)
        )
        
        assert result["status"] == "success", \
            f"Update failed: {result.get('message', 'Unknown error')}"
        assert "files_updated" in result or "message" in result
    
    @pytest.mark.asyncio
    async def test_update_tool_preserves_customizations(
        self,
        existing_steering_project: Path
    ):
        """Test that update preserves user customizations.
        
        Test ID: PWR-EQ-04
        Input: existing_steering_project with custom content
        Expected: Custom content preserved after update
        """
        # Add custom content
        conventions_file = (
            existing_steering_project / ".kiro" / "steering" / "conventions.md"
        )
        custom_section = "\n\n## Custom Section\nCustom content here.\n"
        original_content = conventions_file.read_text()
        conventions_file.write_text(original_content + custom_section)
        
        # Run update
        result = await run_mcp_tool(
            "update_steering",
            preserve_customizations=True,
            project_root=str(existing_steering_project)
        )
        
        assert result["status"] == "success"
        
        # Verify custom content preserved
        updated_content = conventions_file.read_text()
        assert "## Custom Section" in updated_content
    
    @pytest.mark.asyncio
    async def test_validate_tool_returns_expected_status(
        self,
        python_project: Path
    ):
        """Test that validate_steering tool returns expected status.
        
        Test ID: PWR-EQ-05
        Input: python_project with initialized files
        Expected: JSON response with status and validation_results
        """
        # First initialize
        await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(python_project)
        )
        
        # Then validate
        result = await run_mcp_tool(
            "validate_steering",
            project_root=str(python_project)
        )
        
        assert result["status"] == "success" or result["status"] == "failed"
        assert "validation_results" in result, \
            "Missing 'validation_results' in response"
        assert "message" in result, "Missing 'message' in response"
    
    @pytest.mark.asyncio
    async def test_validate_tool_strict_mode(
        self,
        python_project: Path
    ):
        """Test validate_steering with strict mode.
        
        Test ID: PWR-EQ-06
        Input: python_project, strict=True
        Expected: Strict validation results
        """
        await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(python_project)
        )
        
        result = await run_mcp_tool(
            "validate_steering",
            strict=True,
            project_root=str(python_project)
        )
        
        assert result["status"] in ["success", "failed"]
        assert "validation_results" in result
    
    @pytest.mark.asyncio
    async def test_reset_tool_creates_backup(
        self,
        existing_steering_project: Path
    ):
        """Test that reset_steering tool creates a backup.
        
        Test ID: PWR-EQ-07
        Input: existing_steering_project, file="conventions.md", confirm=True
        Expected: Backup created, file reset
        """
        result = await run_mcp_tool(
            "reset_steering",
            file="conventions.md",
            confirm=True,
            project_root=str(existing_steering_project)
        )
        
        assert result["status"] == "success", \
            f"Reset failed: {result.get('message', 'Unknown error')}"
        assert result.get("backup_created") is True, \
            "Backup was not created"
        assert result.get("files_reset", 0) > 0, \
            "No files were reset"
    
    @pytest.mark.asyncio
    async def test_discover_tool_finds_docs(
        self,
        python_project: Path
    ):
        """Test that discover_project_docs tool finds documentation.
        
        Test ID: PWR-EQ-08
        Input: python_project
        Expected: Discovery results with found documents
        """
        result = await run_mcp_tool(
            "discover_project_docs",
            project_root=str(python_project)
        )
        
        assert result["status"] == "success"
        assert "found" in result, "Missing 'found' in response"
        assert isinstance(result["found"], list)
        
        # Should find README.md
        found_paths = [doc.get("path", "") for doc in result["found"]]
        assert any("README" in path for path in found_paths), \
            "README.md was not discovered"
class TestCLIvsPowerEquivalence:
    """Test that CLI and Power produce identical outputs.
    
    **Validates: Requirements 2.3 (CLI Backward Compatibility Validation)**
    
    Test Cases:
        - EQ-01: init_steering equivalence
        - EQ-02: update_steering equivalence
        - EQ-03: validate_steering equivalence
        - EQ-04: reset_steering equivalence
        - EQ-05: discover_docs equivalence
    
    Success Criteria:
        - 100% identical file outputs for same inputs
        - File content is byte-for-byte identical
        - No extra or missing files between CLI and Power outputs
    """
    
    @pytest.mark.asyncio
    async def test_init_equivalence(
        self,
        python_project: Path
    ):
        """Test that init produces identical files via CLI and Power.
        
        Test ID: EQ-01
        Input: Same python_project, auto_discover=True, autonomous=True
        Expected: Identical file contents from both interfaces
        """
        # Run via CLI
        cli_result = run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        assert cli_result.returncode == 0, f"CLI failed: {cli_result.stderr}"
        
        # Get file contents after CLI
        cli_files = get_steering_files(python_project)
        
        # Reset for Power test
        shutil.rmtree(python_project / ".kiro" / "steering")
        
        # Run via Power
        power_result = await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(python_project)
        )
        assert power_result["status"] == "success"
        
        # Get file contents after Power
        power_files = get_steering_files(python_project)
        
        # Compare - should be identical
        comparison = compare_file_outputs(
            python_project / ".kiro" / "steering",
            python_project / ".kiro" / "steering"
        )
        
        # Since we're using the same directory, we need to compare the content dicts
        assert cli_files == power_files, \
            f"CLI and Power produced different outputs.\n" \
            f"CLI files: {list(cli_files.keys())}\n" \
            f"Power files: {list(power_files.keys())}"
    
    @pytest.mark.asyncio
    async def test_init_equivalence_node_express(
        self,
        node_express_project: Path
    ):
        """Test init equivalence with Node.js Express project.
        
        Test ID: EQ-01b
        Input: node_express_project, auto_discover=True, autonomous=True
        Expected: Identical file contents from both interfaces
        """
        # Run via CLI
        cli_result = run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=node_express_project
        )
        assert cli_result.returncode == 0
        
        cli_files = get_steering_files(node_express_project)
        
        # Reset for Power test
        shutil.rmtree(node_express_project / ".kiro" / "steering")
        
        # Run via Power
        power_result = await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(node_express_project)
        )
        assert power_result["status"] == "success"
        
        power_files = get_steering_files(node_express_project)
        
        assert cli_files == power_files, \
            "CLI and Power produced different outputs for Node.js project"
    
    @pytest.mark.asyncio
    async def test_init_equivalence_django(
        self,
        django_project: Path
    ):
        """Test init equivalence with Django project.
        
        Test ID: EQ-01c
        Input: django_project, auto_discover=True, autonomous=True
        Expected: Identical file contents from both interfaces
        """
        # Run via CLI
        cli_result = run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=django_project
        )
        assert cli_result.returncode == 0
        
        cli_files = get_steering_files(django_project)
        
        # Reset for Power test
        shutil.rmtree(django_project / ".kiro" / "steering")
        
        # Run via Power
        power_result = await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(django_project)
        )
        assert power_result["status"] == "success"
        
        power_files = get_steering_files(django_project)
        
        assert cli_files == power_files, \
            "CLI and Power produced different outputs for Django project"
    
    @pytest.mark.asyncio
    async def test_init_equivalence_go(
        self,
        go_microservice: Path
    ):
        """Test init equivalence with Go microservice.
        
        Test ID: EQ-01d
        Input: go_microservice, auto_discover=True, autonomous=True
        Expected: Identical file contents from both interfaces
        """
        # Run via CLI
        cli_result = run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=go_microservice
        )
        assert cli_result.returncode == 0
        
        cli_files = get_steering_files(go_microservice)
        
        # Reset for Power test
        shutil.rmtree(go_microservice / ".kiro" / "steering")
        
        # Run via Power
        power_result = await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(go_microservice)
        )
        assert power_result["status"] == "success"
        
        power_files = get_steering_files(go_microservice)
        
        assert cli_files == power_files, \
            "CLI and Power produced different outputs for Go project"
    
    @pytest.mark.asyncio
    async def test_update_equivalence(
        self,
        existing_steering_project: Path
    ):
        """Test that update produces identical changes via CLI and Power.
        
        Test ID: EQ-02
        Input: existing_steering_project, incremental=True
        Expected: Identical diff output from both interfaces
        """
        # Run via CLI
        cli_result = run_cli_command(
            ["steering", "update", "--incremental", "--no-interactive"],
            cwd=existing_steering_project
        )
        assert cli_result.returncode == 0
        
        cli_files_after_update = get_steering_files(existing_steering_project)
        
        # Reset for Power test
        shutil.rmtree(existing_steering_project / ".kiro" / "steering")
        
        # Re-initialize for Power test
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=existing_steering_project
        )
        
        # Run via Power
        power_result = await run_mcp_tool(
            "update_steering",
            incremental=True,
            project_root=str(existing_steering_project)
        )
        assert power_result["status"] == "success"
        
        power_files_after_update = get_steering_files(existing_steering_project)
        
        # Compare updates
        assert cli_files_after_update == power_files_after_update, \
            "CLI and Power produced different updates"
    
    @pytest.mark.asyncio
    async def test_validate_equivalence(
        self,
        python_project: Path
    ):
        """Test that validate produces identical results via CLI and Power.
        
        Test ID: EQ-03
        Input: python_project with initialized files
        Expected: Identical validation results from both interfaces
        """
        # Initialize via CLI
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        # Validate via CLI
        cli_result = run_cli_command(
            ["steering", "validate", "--json"],
            cwd=python_project
        )
        assert cli_result.returncode == 0
        cli_output = json.loads(cli_result.stdout)
        
        # Validate via Power
        power_result = await run_mcp_tool(
            "validate_steering",
            project_root=str(python_project)
        )
        
        # Compare validation status
        assert cli_output.get("status") == power_result.get("status"), \
            f"CLI status: {cli_output.get('status')}, " \
            f"Power status: {power_result.get('status')}"
        
        # Both should have validation_results
        assert "validation_results" in cli_output
        assert "validation_results" in power_result
    
    @pytest.mark.asyncio
    async def test_reset_equivalence(
        self,
        existing_steering_project: Path
    ):
        """Test that reset produces identical results via CLI and Power.
        
        Test ID: EQ-04
        Input: existing_steering_project, file="conventions.md", confirm=True
        Expected: Identical reset results from both interfaces
        """
        # Reset via CLI
        cli_result = run_cli_command(
            ["steering", "reset", "--file", "conventions.md", "--confirm"],
            cwd=existing_steering_project
        )
        assert cli_result.returncode == 0
        
        # Get file content after CLI reset
        cli_content_after_reset = (
            existing_steering_project / ".kiro" / "steering" / "conventions.md"
        ).read_text()
        
        # Reset for Power test - reinitialize first
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=existing_steering_project
        )
        
        # Reset via Power
        power_result = await run_mcp_tool(
            "reset_steering",
            file="conventions.md",
            confirm=True,
            project_root=str(existing_steering_project)
        )
        assert power_result["status"] == "success"
        
        # Get file content after Power reset
        power_content_after_reset = (
            existing_steering_project / ".kiro" / "steering" / "conventions.md"
        ).read_text()
        
        # Compare reset content - should be identical (both reset to same template)
        assert cli_content_after_reset == power_content_after_reset, \
            "CLI and Power produced different reset content"
    
    @pytest.mark.asyncio
    async def test_discover_equivalence(
        self,
        python_project: Path
    ):
        """Test that discover produces identical results via CLI and Power.
        
        Test ID: EQ-05
        Input: python_project
        Expected: Identical discovery results from both interfaces
        """
        # Discover via CLI
        cli_result = run_cli_command(
            ["steering", "discover", "--json"],
            cwd=python_project
        )
        assert cli_result.returncode == 0
        cli_output = json.loads(cli_result.stdout)
        
        # Discover via Power
        power_result = await run_mcp_tool(
            "discover_project_docs",
            project_root=str(python_project)
        )
        assert power_result["status"] == "success"
        
        # Compare discovery results
        cli_found = cli_output.get("found", [])
        power_found = power_result.get("found", [])
        
        # Compare found document paths
        cli_paths = sorted([doc.get("path", "") for doc in cli_found])
        power_paths = sorted([doc.get("path", "") for doc in power_found])
        
        assert cli_paths == power_paths, \
            f"CLI found: {cli_paths}, Power found: {power_paths}"
    
    @pytest.mark.asyncio
    async def test_equivalence_across_project_types(
        self,
        python_project: Path,
        node_express_project: Path,
        django_project: Path,
        go_microservice: Path
    ):
        """Test equivalence across multiple project types.
        
        Test ID: EQ-06
        Input: Multiple project types with same init parameters
        Expected: All projects produce equivalent outputs
        """
        projects = [
            ("Python Flask", python_project),
            ("Node Express", node_express_project),
            ("Django", django_project),
            ("Go Microservice", go_microservice),
        ]
        
        results = []
        
        for name, project in projects:
            # Run via CLI
            cli_result = run_cli_command(
                ["steering", "init", "--autonomous", "--no-interactive"],
                cwd=project
            )
            assert cli_result.returncode == 0, f"CLI failed for {name}: {cli_result.stderr}"
            
            cli_files = get_steering_files(project)
            
            # Reset for Power
            shutil.rmtree(project / ".kiro" / "steering")
            
            # Run via Power
            power_result = await run_mcp_tool(
                "init_steering",
                auto_discover=True,
                autonomous=True,
                project_root=str(project)
            )
            assert power_result["status"] == "success", \
                f"Power failed for {name}: {power_result.get('message')}"
            
            power_files = get_steering_files(project)
            
            results.append({
                "project": name,
                "equivalent": cli_files == power_files,
                "cli_files": list(cli_files.keys()),
                "power_files": list(power_files.keys())
            })
        
        # All projects should have equivalent outputs
        for result in results:
            assert result["equivalent"], \
                f"Equivalence failed for {result['project']}: " \
                f"CLI files: {result['cli_files']}, " \
                f"Power files: {result['power_files']}"
class TestOutputContentValidation:
    """Validate the content of generated files.
    
    **Validates: Requirements FR-3 (MCP Tools Implementation)**
    
    Success Criteria:
        - Generated files have expected structure
        - Required sections are present
        - Content is meaningful and relevant
    """
    
    def test_conventions_content_structure(
        self,
        python_project: Path
    ):
        """Test that CONVENTIONS.md has expected structure.
        
        Test ID: CNT-01
        Input: python_project after init
        Expected: CONVENTIONS.md with required sections
        """
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        content = (
            python_project / ".kiro" / "steering" / "CONVENTIONS.md"
        ).read_text()
        
        # Check for expected sections
        assert "## Coding Conventions" in content, \
            "Missing '## Coding Conventions' section"
        assert "## Naming Conventions" in content, \
            "Missing '## Naming Conventions' section"
        assert "## Code Style" in content, \
            "Missing '## Code Style' section"
        
        # Check for language-specific conventions
        assert "Python" in content or "python" in content, \
            "Missing Python-specific conventions"
    
    def test_architecture_content_structure(
        self,
        python_project: Path
    ):
        """Test that ARCHITECTURE.md has expected structure.
        
        Test ID: CNT-02
        Input: python_project after init
        Expected: ARCHITECTURE.md with required sections
        """
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        content = (
            python_project / ".kiro" / "steering" / "ARCHITECTURE.md"
        ).read_text()
        
        # Check for expected sections
        assert "## System Diagram" in content, \
            "Missing '## System Diagram' section"
        assert "## Component Responsibilities" in content, \
            "Missing '## Component Responsibilities' section"
        assert "## Data Flow" in content, \
            "Missing '## Data Flow' section"
        
        # Check for Mermaid diagram
        assert "```mermaid" in content, \
            "Missing Mermaid diagram"
        assert "```" in content, \
            "Missing diagram closing backticks"
    
    def test_tech_stack_content_structure(
        self,
        python_project: Path
    ):
        """Test that TECH-STACK.md has expected structure.
        
        Test ID: CNT-03
        Input: python_project after init
        Expected: TECH-STACK.md with required sections
        """
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        content = (
            python_project / ".kiro" / "steering" / "TECH-STACK.md"
        ).read_text()
        
        # Check for expected sections
        assert "## Core Technologies" in content, \
            "Missing '## Core Technologies' section"
        assert "## Backend" in content or "## Frontend" in content, \
            "Missing technology category section"
        assert "## Key Dependencies" in content, \
            "Missing '## Key Dependencies' section"
    
    def test_onboarding_content_structure(
        self,
        python_project: Path
    ):
        """Test that ONBOARDING.md has expected structure.
        
        Test ID: CNT-04
        Input: python_project after init
        Expected: ONBOARDING.md with required sections
        """
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        onboarding_file = python_project / ".kiro" / "steering" / "ONBOARDING.md"
        
        if onboarding_file.exists():
            content = onboarding_file.read_text()
            
            # Check for expected sections
            assert "## Quick Start" in content, \
                "Missing '## Quick Start' section"
            assert "## Development Setup" in content, \
                "Missing '## Development Setup' section"
    
    def test_content_is_project_specific(
        self,
        python_project: Path,
        node_express_project: Path
    ):
        """Test that generated content is specific to each project type.
        
        Test ID: CNT-05
        Input: python_project and node_express_project after init
        Expected: Content reflects project-specific technologies
        """
        # Initialize both projects
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=node_express_project
        )
        
        # Get tech-stack content for both
        python_content = (
            python_project / ".kiro" / "steering" / "TECH-STACK.md"
        ).read_text()
        node_content = (
            node_express_project / ".kiro" / "steering" / "TECH-STACK.md"
        ).read_text()
        
        # Python project should mention Python
        assert "Python" in python_content or "python" in python_content, \
            "Python project should mention Python"
        
        # Node project should mention Node.js or JavaScript
        assert ("Node" in node_content or "JavaScript" in node_content or 
                "node" in node_content or "javascript" in node_content), \
            "Node project should mention Node.js or JavaScript"
        
        # Content should be different (project-specific)
        assert python_content != node_content, \
            "Project-specific content should differ between projects"


class TestPerformanceParity:
    """Test that CLI and Power have similar performance characteristics.
    
    **Validates: Requirements SR-2 (Performance Requirements)**
    
    Test Cases:
        - PF-01: init_steering execution time
        - PF-02: update_steering execution time
        - PF-03: validate_steering execution time
        - PF-04: Memory usage variance
        - PF-05: CPU usage variance
    
    Success Criteria:
        - Execution time variance < 10%
        - Memory usage variance < 15%
        - CPU usage variance < 15%
    """
    
    @pytest.mark.asyncio
    async def test_init_performance_parity(
        self,
        python_project: Path
    ):
        """Test that init has similar performance via CLI and Power.
        
        Test ID: PF-01
        Input: python_project, 5 iterations each
        Expected: Time variance < 10%, memory variance < 15%
        """
        # Warmup
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        await run_mcp_tool(
            "init_steering",
            auto_discover=True,
            autonomous=True,
            project_root=str(python_project)
        )
        
        # Reset for benchmarking
        shutil.rmtree(python_project / ".kiro" / "steering")
        
        # Benchmark CLI (5 iterations)
        cli_times = []
        for _ in range(5):
            shutil.rmtree(python_project / ".kiro" / "steering", ignore_errors=True)
            
            def run_init():
                return run_cli_command(
                    ["steering", "init", "--autonomous", "--no-interactive"],
                    cwd=python_project
                )
            
            metrics = measure_performance(run_init)
            cli_times.append(metrics.elapsed_time)
        
        # Reset for Power
        shutil.rmtree(python_project / ".kiro" / "steering")
        
        # Benchmark Power (5 iterations)
        power_times = []
        for _ in range(5):
            shutil.rmtree(python_project / ".kiro" / "steering", ignore_errors=True)
            
            async def run_init_tool():
                return await run_mcp_tool(
                    "init_steering",
                    auto_discover=True,
                    autonomous=True,
                    project_root=str(python_project)
                )
            
            metrics = measure_performance(run_init_tool)
            power_times.append(metrics.elapsed_time)
        
        # Calculate variance
        cli_avg_time = statistics.mean(cli_times)
        power_avg_time = statistics.mean(power_times)
        
        if cli_avg_time > 0:
            time_variance = abs(cli_avg_time - power_avg_time) / cli_avg_time
        else:
            time_variance = 0
        
        # Assert performance parity
        assert time_variance < 0.10, \
            f"Time variance: {time_variance:.2%} (target: <10%)"
    
    @pytest.mark.asyncio
    async def test_validate_performance_parity(
        self,
        python_project: Path
    ):
        """Test that validate has similar performance via CLI and Power.
        
        Test ID: PF-03
        Input: python_project with initialized files, 5 iterations each
        Expected: Time variance < 10%
        """
        # Initialize first
        run_cli_command(
            ["steering", "init", "--autonomous", "--no-interactive"],
            cwd=python_project
        )
        
        # Benchmark CLI
        cli_times = []
        for _ in range(5):
            def run_validate():
                return run_cli_command(
                    ["steering", "validate"],
                    cwd=python_project
                )
            
            metrics = measure_performance(run_validate)
            cli_times.append(metrics.elapsed_time)
        
        # Benchmark Power
        power_times = []
        for _ in range(5):
            async def run_validate_tool():
                return await run_mcp_tool(
                    "validate_steering",
                    project_root=str(python_project)
                )
            
            metrics = measure_performance(run_validate_tool)
            power_times.append(metrics.elapsed_time)
        
        # Calculate variance
        cli_avg_time = statistics.mean(cli_times)
        power_avg_time = statistics.mean(power_times)
        
        if cli_avg_time > 0:
            time_variance = abs(cli_avg_time - power_avg_time) / cli_avg_time
        else:
            time_variance = 0
        
        assert time_variance < 0.10, \
            f"Validate time variance: {time_variance:.2%} (target: <10%)"
    
    def test_large_project_performance(
        self,
        large_project: Path
    ):
        """Test performance on a large project.
        
        Test ID: PF-04
        Input: large_project (100+ files)
        Expected: Performance within acceptable limits
        """
        def run_init():
            return run_cli_command(
                ["steering", "init", "--autonomous", "--no-interactive"],
                cwd=large_project
            )
        
        metrics = measure_performance(run_init)
        
        # Performance targets from requirements
        assert metrics.elapsed_time < 120, \
            f"Init took too long: {metrics.elapsed_time:.2f}s (target: <120s)"
        assert metrics.peak_memory_mb < 512, \
            f"Memory usage too high: {metrics.peak_memory_mb:.2f}MB (target: <512MB)"
class TestErrorHandlingParity:
    """Test that CLI and Power handle errors identically.
    
    **Validates: Requirements SR-3 (Reliability and Error Handling)**
    
    Test Cases:
        - EH-01: Project not found
        - EH-02: LLM API failure
        - EH-03: File I/O error
        - EH-04: Validation failure
        - EH-05: Resource limit exceeded
    
    Success Criteria:
        - Error types match for all scenarios
        - Recovery options are identical
        - User messages are equivalent
        - Rollback behavior is identical
    """
    
    @pytest.mark.asyncio
    async def test_project_not_found_error(
        self,
        tmp_path: Path
    ):
        """Test error handling when project root doesn't exist.
        
        Test ID: EH-01
        Input: Invalid project_root path
        Expected: Both interfaces return project_not_found error
        """
        invalid_path = "/nonexistent/path/that/does/not/exist"
        
        # CLI error
        cli_result = run_cli_command(
            ["steering", "init"],
            cwd=Path(invalid_path)
        )
        cli_error = cli_result.stderr.lower() if cli_result.stderr else ""
        
        # Power error
        power_result = await run_mcp_tool(
            "init_steering",
            project_root=invalid_path
        )
        power_error = power_result.get("message", "").lower()
        
        # Both should indicate project not found
        assert "not found" in cli_error or "does not exist" in cli_error, \
            f"CLI error should indicate project not found: {cli_error}"
        assert "not found" in power_error or "does not exist" in power_error, \
            f"Power error should indicate project not found: {power_error}"
    
    @pytest.mark.asyncio
    async def test_invalid_parameter_error(
        self,
        python_project: Path
    ):
        """Test error handling for invalid parameters.
        
        Test ID: EH-04
        Input: Invalid confidence_threshold (e.g., 999)
        Expected: Both interfaces return validation error
        """
        # CLI error
        cli_result = run_cli_command(
            ["steering", "init", "--confidence-threshold", "999"],
            cwd=python_project
        )
        cli_error = cli_result.stderr.lower() if cli_result.stderr else ""
        
        # Power error
        power_result = await run_mcp_tool(
            "init_steering",
            confidence_threshold=999,
            project_root=str(python_project)
        )
        power_error = power_result.get("message", "").lower()
        
        # Both should indicate invalid parameter
        assert cli_result.returncode != 0, "CLI should reject invalid parameter"
        assert "invalid" in cli_error or "validation" in cli_error or "confidence" in cli_error, \
            f"CLI should indicate validation error: {cli_error}"
        assert power_result["status"] == "failed", "Power should reject invalid parameter"
        assert "invalid" in power_error or "validation" in power_error or "confidence" in power_error, \
            f"Power should indicate validation error: {power_error}"
    
    @pytest.mark.asyncio
    async def test_error_message_format_parity(
        self,
        tmp_path: Path
    ):
        """Test that error message formats are equivalent.
        
        Test ID: EH-06
        Input: Same error scenario
        Expected: Error messages convey same information
        """
        invalid_path = "/invalid/path"
        
        # CLI error format
        cli_result = run_cli_command(
            ["steering", "init"],
            cwd=Path(invalid_path)
        )
        
        # Power error format
        power_result = await run_mcp_tool(
            "init_steering",
            project_root=invalid_path
        )
        
        # Both should have error status
        assert cli_result.returncode != 0 or "error" in cli_result.stderr.lower()
        assert power_result["status"] == "failed"
        
        # Both should have error message
        assert cli_result.stderr or cli_result.stdout
        assert "message" in power_result or "error" in power_result


class TestSecurityValidation:
    """Test that security measures work for both interfaces.
    
    **Validates: Requirements SR-1 (Security Requirements)**
    
    Test Cases:
        - SV-01: Path traversal prevention
        - SV-02: Path traversal prevention (absolute path)
        - SV-03: Resource limit enforcement
        - SV-04: Input validation
        - SV-05: Error obfuscation
    
    Success Criteria:
        - All security attacks are blocked
        - No sensitive data exposed in error messages
        - Resource limits are enforced
    """
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention_relative(
        self,
        tmp_path: Path
    ):
        """Test path traversal prevention with relative paths.
        
        Test ID: SV-01
        Input: project_root with "../" path traversal
        Expected: Security error, operation blocked
        """
        malicious_path = "../../../etc"
        
        # CLI should block
        cli_result = run_cli_command(
            ["steering", "init"],
            cwd=tmp_path / malicious_path
        )
        assert cli_result.returncode != 0, "CLI should reject path traversal"
        assert "security" in cli_result.stderr.lower() or "invalid" in cli_result.stderr.lower(), \
            f"CLI should indicate security error: {cli_result.stderr}"
        
        # Power should block
        power_result = await run_mcp_tool(
            "init_steering",
            project_root=str(tmp_path / malicious_path)
        )
        assert power_result["status"] == "failed", "Power should reject path traversal"
        assert "security" in power_result.get("message", "").lower() or \
               "invalid" in power_result.get("message", "").lower(), \
            f"Power should indicate security error: {power_result}"
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention_absolute(
        self,
        tmp_path: Path
    ):
        """Test path traversal prevention with absolute paths outside project.
        
        Test ID: SV-02
        Input: Absolute path to /tmp or /etc
        Expected: Security error, operation blocked
        """
        malicious_path = "/tmp/malicious/project"
        
        # CLI should block
        cli_result = run_cli_command(
            ["steering", "init"],
            cwd=Path(malicious_path)
        )
        assert cli_result.returncode != 0, "CLI should reject absolute path outside project"
        
        # Power should block
        power_result = await run_mcp_tool(
            "init_steering",
            project_root=malicious_path
        )
        assert power_result["status"] == "failed", "Power should reject absolute path outside project"
    
    @pytest.mark.asyncio
    async def test_error_obfuscation_no_sensitive_data(
        self,
        tmp_path: Path
    ):
        """Test that error messages don't expose sensitive data.
        
        Test ID: SV-06
        Input: Various error scenarios
        Expected: No passwords, API keys, or paths in error messages
        """
        # Try to trigger an error
        power_result = await run_mcp_tool(
            "init_steering",
            project_root="/nonexistent"
        )
        
        error_message = power_result.get("message", "").lower()
        
        # Check for sensitive data patterns
        sensitive_patterns = [
            "password",
            "api_key",
            "apikey",
            "secret",
            "token",
            "credential",
        ]
        
        for pattern in sensitive_patterns:
            assert pattern not in error_message, \
                f"Error message contains sensitive data: '{pattern}'"
    
    def test_input_validation_confidence_threshold(
        self,
        python_project: Path
    ):
        """Test input validation for confidence_threshold parameter.
        
        Test ID: SV-04
        Input: confidence_threshold outside valid range [0, 1]
        Expected: Validation error
        """
        # Test value > 1
        cli_result = run_cli_command(
            ["steering", "init", "--confidence-threshold", "1.5"],
            cwd=python_project
        )
        assert cli_result.returncode != 0, \
            "CLI should reject confidence_threshold > 1"
        
        # Test value < 0
        cli_result = run_cli_command(
            ["steering", "init", "--confidence-threshold", "-0.5"],
            cwd=python_project
        )
        assert cli_result.returncode != 0, \
            "CLI should reject confidence_threshold < 0"


# =============================================================================
# Test Execution Notes
# =============================================================================
"""
Phase 1.2: Integration Test Suite for Architecture Validation

This test file contains comprehensive test specifications for validating
CLI/Power output equivalence. The tests are organized into:

1. **TestCLIOutputEquivalence**: Unit tests for CLI commands
2. **TestPowerOutputEquivalence**: Unit tests for Power tools
3. **TestCLIvsPowerEquivalence**: Integration tests for equivalence (EQ-01 to EQ-05)
4. **TestOutputContentValidation**: Content structure validation
5. **TestPerformanceParity**: Performance comparison tests
6. **TestErrorHandlingParity**: Error handling equivalence
7. **TestSecurityValidation**: Security measure validation

Implementation Status:
- Phase 1.2: Test specifications (stubs) - COMPLETE
- Phase 4.5: Full implementation when both interfaces are available

Success Criteria Summary:
- Output Equivalence: 100% identical file outputs
- Shared Backend Utilization: > 95% code shared
- Error Handling Parity: 100% identical error handling
- Performance Parity: < 10% time variance, < 15% memory variance
- Security Validation: 100% of attacks blocked

Test Execution Order:
1. TestCLIOutputEquivalence (validate CLI works correctly)
2. TestPowerOutputEquivalence (validate Power works correctly)
3. TestCLIvsPowerEquivalence (validate equivalence - core requirement)
4. TestOutputContentValidation (validate content structure)
5. TestPerformanceParity (validate performance parity)
6. TestErrorHandlingParity (validate error handling parity)
7. TestSecurityValidation (validate security measures)
"""