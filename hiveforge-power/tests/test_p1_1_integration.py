"""
Integration test for P1-1: CodeAnalyzer.extract_public_api()

This test verifies the complete workflow of extracting MCP tools, CLI commands,
and public classes from a realistic project structure.
"""

from pathlib import Path
from textwrap import dedent

import pytest

from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer


@pytest.fixture
def realistic_project(tmp_path):
    """Create a realistic project structure with MCP server and CLI."""
    project_root = tmp_path / "hiveforge_project"
    project_root.mkdir()
    
    # Create MCP server directory
    mcp_dir = project_root / "mcp_server"
    mcp_dir.mkdir()
    
    # Create MCP tools file
    (mcp_dir / "tools.py").write_text(dedent('''
        """MCP tools for the HiveForge project."""
        from mcp import mcp
        
        @mcp.tool()
        def init_steering(project_root: str, source_docs_path: str = None):
            """Initialize steering files for a project."""
            return {"status": "success"}
        
        @mcp.tool()
        def update_steering(project_root: str, files_to_update: list = None):
            """Update existing steering files with fresh project analysis."""
            return {"status": "success"}
        
        @mcp.tool()
        def validate_steering(project_root: str, strict: bool = False):
            """Validate steering files for completeness and quality."""
            return {"status": "valid"}
    '''))
    
    # Create CLI directory
    cli_dir = project_root / "cli"
    cli_dir.mkdir()
    
    # Create CLI commands file
    (cli_dir / "commands.py").write_text(dedent('''
        """CLI commands for HiveForge."""
        import click
        
        @click.command()
        def init(project_path: str):
            """Initialize a new HiveForge project."""
            print(f"Initializing {project_path}")
        
        @click.command()
        def analyze(project_path: str, verbose: bool = False):
            """Analyze project structure and generate reports."""
            pass
    '''))
    
    # Create models directory
    models_dir = project_root / "models"
    models_dir.mkdir()
    
    # Create models file
    (models_dir / "data_models.py").write_text(dedent('''
        """Data models for HiveForge."""
        
        class CodeAnalysisResult:
            """Complete result of code analysis for a project."""
            pass
        
        class SteeringConfig:
            """Configuration for steering workflow."""
            pass
        
        class _InternalHelper:
            """Internal helper class."""
            pass
        
        class NoDocClass:
            pass
    '''))
    
    # Create .gitignore
    (project_root / ".gitignore").write_text("__pycache__/\n*.pyc\n.venv/\n")
    
    return project_root


def test_extract_public_api_integration(realistic_project):
    """Test complete extraction workflow on realistic project."""
    analyzer = CodeAnalyzer(realistic_project)
    result = analyzer.extract_public_api()
    
    # Verify MCP tools were found
    assert len(result.mcp_tools) == 3
    tool_names = {tool.name for tool in result.mcp_tools}
    assert "init_steering" in tool_names
    assert "update_steering" in tool_names
    assert "validate_steering" in tool_names
    
    # Verify tool details
    init_tool = next(t for t in result.mcp_tools if t.name == "init_steering")
    assert "initialize steering files" in init_tool.docstring.lower()
    assert "project_root" in init_tool.parameters
    assert "source_docs_path" in init_tool.parameters
    
    # Verify CLI commands were found
    assert len(result.cli_commands) == 2
    cmd_names = {cmd.name for cmd in result.cli_commands}
    assert "init" in cmd_names
    assert "analyze" in cmd_names
    
    # Verify command details
    init_cmd = next(c for c in result.cli_commands if c.name == "init")
    assert "initialize" in init_cmd.help_text.lower()
    assert "project_path" in init_cmd.parameters
    
    # Verify public classes were found
    assert len(result.public_classes) == 2
    assert "CodeAnalysisResult" in result.public_classes
    assert "SteeringConfig" in result.public_classes
    assert "_InternalHelper" not in result.public_classes
    assert "NoDocClass" not in result.public_classes


def test_extract_public_api_respects_gitignore(tmp_path):
    """Test that .gitignore patterns are respected during extraction."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    # Create .gitignore
    (project_root / ".gitignore").write_text("excluded/\n")
    
    # Create excluded directory with MCP tool
    excluded_dir = project_root / "excluded"
    excluded_dir.mkdir()
    (excluded_dir / "tool.py").write_text(dedent('''
        @mcp.tool()
        def excluded_tool():
            """This should be excluded."""
            pass
    '''))
    
    # Create included file with MCP tool
    (project_root / "included.py").write_text(dedent('''
        @mcp.tool()
        def included_tool():
            """This should be included."""
            pass
    '''))
    
    analyzer = CodeAnalyzer(project_root)
    analyzer._load_gitignore()
    result = analyzer.extract_public_api()
    
    # Should only find the included tool
    assert len(result.mcp_tools) == 1
    assert result.mcp_tools[0].name == "included_tool"


def test_extract_public_api_performance(tmp_path):
    """Test that extraction completes quickly even with many files."""
    project_root = tmp_path / "large_project"
    project_root.mkdir()
    
    # Create 60 Python files (should only scan 50)
    for i in range(60):
        file_path = project_root / f"module_{i}.py"
        file_path.write_text(f'''
@mcp.tool()
def tool_{i}():
    """Tool number {i}."""
    pass
''')
    
    import time
    start = time.time()
    
    analyzer = CodeAnalyzer(project_root)
    result = analyzer.extract_public_api()
    
    elapsed = time.time() - start
    
    # Should complete in under 5 seconds
    assert elapsed < 5.0
    
    # Should find at most 50 tools (file limit)
    assert len(result.mcp_tools) <= 50
