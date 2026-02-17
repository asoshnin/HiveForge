"""
Test Fixtures for Architecture Validation

Provides fixtures for different project types and helper functions
for running CLI and Power tool tests.
"""

import pytest
import subprocess
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum


class ProjectType(Enum):
    """Types of test projects for architecture validation."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    MIXED = "mixed"


@pytest.fixture
def python_project(tmp_path):
    """Create a Python project for testing."""
    project_dir = tmp_path / "python_project"
    project_dir.mkdir()
    
    # Create Python project structure
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"

[tool.pytest.ini_options]
testpaths = ["tests"]
""")
    (project_dir / "src", "__init__.py").touch()
    (project_dir / "tests", "__init__.py").touch()
    (project_dir / "README.md").write_text("# Test Project\n\nA test Python project.")
    
    return project_dir


@pytest.fixture
def javascript_project(tmp_path):
    """Create a JavaScript project for testing."""
    project_dir = tmp_path / "javascript_project"
    project_dir.mkdir()
    
    # Create JS project structure
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "package.json").write_text("""
{
  "name": "test-project",
  "version": "0.1.0",
  "main": "src/index.js"
}
""")
    (project_dir / "src", "index.js").write_text("// Main entry point")
    (project_dir / "tests", "index.test.js").write_text("// Tests")
    (project_dir / "README.md").write_text("# Test Project\n\nA test JavaScript project.")
    
    return project_dir


@pytest.fixture
def typescript_project(tmp_path):
    """Create a TypeScript project for testing."""
    project_dir = tmp_path / "typescript_project"
    project_dir.mkdir()
    
    # Create TS project structure
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "package.json").write_text("""
{
  "name": "test-project",
  "version": "0.1.0",
  "main": "dist/index.js"
}
""")
    (project_dir / "tsconfig.json").write_text("""
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs"
  }
}
""")
    (project_dir / "src", "index.ts").write_text("// Main entry point")
    (project_dir / "tests", "index.test.ts").write_text("// Tests")
    (project_dir / "README.md").write_text("# Test Project\n\nA test TypeScript project.")
    
    return project_dir


@pytest.fixture
def go_project(tmp_path):
    """Create a Go project for testing."""
    project_dir = tmp_path / "go_project"
    project_dir.mkdir()
    
    # Create Go project structure
    (project_dir / "main.go").write_text("package main\n\nfunc main() {}")
    (project_dir / "go.mod").write_text("module test-project\n\ngo 1.21")
    (project_dir / "README.md").write_text("# Test Project\n\nA test Go project.")
    
    return project_dir


@pytest.fixture
def rust_project(tmp_path):
    """Create a Rust project for testing."""
    project_dir = tmp_path / "rust_project"
    project_dir.mkdir()
    
    # Create Rust project structure
    (project_dir / "src", "main.rs").write_text("fn main() {\n    println!(\"Hello\");\n}")
    (project_dir / "Cargo.toml").write_text("""
[package]
name = "test-project"
version = "0.1.0"
edition = "2021"
""")
    (project_dir / "README.md").write_text("# Test Project\n\nA test Rust project.")
    
    return project_dir


@pytest.fixture
def mixed_project(tmp_path):
    """Create a mixed language project for testing."""
    project_dir = tmp_path / "mixed_project"
    project_dir.mkdir()
    
    # Create mixed project structure
    (project_dir / "src").mkdir()
    (project_dir / "backend").mkdir()
    (project_dir / "frontend").mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'backend'")
    (project_dir / "frontend", "package.json").write_text('{"name": "frontend"}')
    (project_dir / "README.md").write_text("# Test Project\n\nA mixed language project.")
    
    return project_dir


@pytest.fixture
def project_type(request):
    """Parametrized fixture for different project types."""
    return request.param


def run_cli_command(args: list, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run a CLI command and return the result."""
    env = {
        **__import__("os").environ,
        "KIRO_STEERING_NO_INTERACTIVE": "1"
    }
    
    result = subprocess.run(
        ["hiveforge"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=120
    )
    
    return result


async def run_mcp_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """Run an MCP tool and return the result.
    
    This is a placeholder that simulates MCP tool invocation.
    In Phase 4.5, this will be replaced with actual MCP protocol calls.
    """
    # Placeholder implementation - will be replaced with actual MCP calls
    return {
        "status": "success",
        "tool": tool_name,
        "parameters": kwargs,
        "message": f"Tool {tool_name} executed successfully"
    }


@pytest.fixture
def cleanup_kiro_files(tmp_path):
    """Fixture to clean up .kiro files after test."""
    yield tmp_path
    # Cleanup after test
    kiro_dir = tmp_path / ".kiro"
    if kiro_dir.exists():
        shutil.rmtree(kiro_dir)


@pytest.fixture
def mock_llm_api():
    """Fixture to mock LLM API calls."""
    with patch("src.hiveforge.steering.workflows.InitWorkflow._call_llm") as mock:
        mock.return_value = {
            "content": "# Test Conventions\n\n## Naming\n- snake_case for functions",
            "confidence": 0.9
        }
        yield mock


@pytest.fixture
def performance_monitor():
    """Fixture to monitor performance metrics."""
    import time
    import psutil
    import os
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.process = psutil.Process(os.getpid())
        
        def start(self):
            self.start_time = time.perf_counter()
            self.start_memory = self.process.memory_info().rss
        
        def stop(self):
            end_time = time.perf_counter()
            end_memory = self.process.memory_info().rss
            
            return {
                "elapsed_seconds": end_time - self.start_time,
                "memory_bytes": end_memory - self.start_memory,
                "memory_mb": (end_memory - self.start_memory) / (1024 * 1024)
            }
    
    return PerformanceMonitor()