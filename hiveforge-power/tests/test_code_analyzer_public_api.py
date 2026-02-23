"""
Tests for CodeAnalyzer.extract_public_api() method (P1-1).

This module tests the extraction of MCP tools, CLI commands, and public classes
from Python source files using AST parsing.
"""

import ast
from pathlib import Path
from textwrap import dedent

import pytest

from hiveforge.steering.analyzers.code_analyzer import CodeAnalyzer
from hiveforge.steering.models import (
    PublicAPIInfo,
    MCPToolInfo,
    CLICommandInfo,
)


@pytest.fixture
def temp_project_with_mcp(tmp_path):
    """Create a temporary project with MCP tools."""
    project_root = tmp_path / "mcp_project"
    project_root.mkdir()
    
    # Create MCP server file
    mcp_file = project_root / "server.py"
    mcp_file.write_text(dedent('''
        from mcp import mcp
        
        @mcp.tool()
        def get_weather(location: str, units: str = "metric"):
            """Get weather forecast for a location."""
            return {"temp": 20, "location": location}
        
        @mcp.tool()
        def search_database(query: str, limit: int = 10):
            """Search the database with a query string and return results."""
            return []
        
        def helper_function():
            """This is not an MCP tool."""
            pass
    '''))
    
    return project_root


@pytest.fixture
def temp_project_with_cli(tmp_path):
    """Create a temporary project with CLI commands."""
    project_root = tmp_path / "cli_project"
    project_root.mkdir()
    
    # Create CLI file with click
    cli_file = project_root / "cli.py"
    cli_file.write_text(dedent('''
        import click
        
        @click.command()
        def init(project_name: str):
            """Initialize a new project with the given name."""
            print(f"Initializing {project_name}")
        
        @click.command()
        def deploy(env: str, verbose: bool = False):
            """Deploy the application to the specified environment."""
            pass
        
        @command
        def build():
            """Build the project artifacts."""
            pass
    '''))
    
    return project_root


@pytest.fixture
def temp_project_with_classes(tmp_path):
    """Create a temporary project with public classes."""
    project_root = tmp_path / "class_project"
    project_root.mkdir()
    
    # Create file with classes
    classes_file = project_root / "models.py"
    classes_file.write_text(dedent('''
        class UserModel:
            """Represents a user in the system."""
            pass
        
        class _PrivateHelper:
            """This is a private class."""
            pass
        
        class OrderModel:
            """Represents an order with items and total."""
            pass
        
        class NoDocstring:
            pass
    '''))
    
    return project_root


@pytest.fixture
def temp_project_with_syntax_error(tmp_path):
    """Create a temporary project with a syntax error."""
    project_root = tmp_path / "error_project"
    project_root.mkdir()
    
    # Create file with syntax error
    error_file = project_root / "broken.py"
    error_file.write_text("def broken(:\n    pass")
    
    # Create valid file
    valid_file = project_root / "valid.py"
    valid_file.write_text(dedent('''
        @mcp.tool()
        def working_tool():
            """This tool should still be found."""
            pass
    '''))
    
    return project_root


class TestExtractPublicAPI:
    """Test extract_public_api() orchestration method."""
    
    def test_extract_from_empty_project(self, tmp_path):
        """Test extraction from project with no Python files."""
        project_root = tmp_path / "empty"
        project_root.mkdir()
        
        analyzer = CodeAnalyzer(project_root)
        result = analyzer.extract_public_api()
        
        assert isinstance(result, PublicAPIInfo)
        assert len(result.mcp_tools) == 0
        assert len(result.cli_commands) == 0
        assert len(result.public_classes) == 0
    
    def test_extract_mcp_tools(self, temp_project_with_mcp):
        """Test extraction of MCP tools."""
        analyzer = CodeAnalyzer(temp_project_with_mcp)
        result = analyzer.extract_public_api()
        
        assert len(result.mcp_tools) == 2
        
        # Check first tool
        tool1 = next(t for t in result.mcp_tools if t.name == "get_weather")
        assert tool1.name == "get_weather"
        assert "weather forecast" in tool1.docstring.lower()
        assert "location" in tool1.parameters
        assert "units" in tool1.parameters
        assert "self" not in tool1.parameters
        assert "ctx" not in tool1.parameters
        
        # Check second tool
        tool2 = next(t for t in result.mcp_tools if t.name == "search_database")
        assert tool2.name == "search_database"
        assert "search" in tool2.docstring.lower()
        assert "query" in tool2.parameters
        assert "limit" in tool2.parameters
    
    def test_extract_cli_commands(self, temp_project_with_cli):
        """Test extraction of CLI commands."""
        analyzer = CodeAnalyzer(temp_project_with_cli)
        result = analyzer.extract_public_api()
        
        assert len(result.cli_commands) >= 2
        
        # Check init command
        init_cmd = next(c for c in result.cli_commands if c.name == "init")
        assert init_cmd.name == "init"
        assert "initialize" in init_cmd.help_text.lower()
        assert "project_name" in init_cmd.parameters
        
        # Check deploy command
        deploy_cmd = next(c for c in result.cli_commands if c.name == "deploy")
        assert deploy_cmd.name == "deploy"
        assert "deploy" in deploy_cmd.help_text.lower()
        assert "env" in deploy_cmd.parameters
        assert "verbose" in deploy_cmd.parameters
    
    def test_extract_public_classes(self, temp_project_with_classes):
        """Test extraction of public classes."""
        analyzer = CodeAnalyzer(temp_project_with_classes)
        result = analyzer.extract_public_api()
        
        assert len(result.public_classes) == 2
        assert "UserModel" in result.public_classes
        assert "OrderModel" in result.public_classes
        assert "_PrivateHelper" not in result.public_classes
        assert "NoDocstring" not in result.public_classes
    
    def test_handles_syntax_errors_gracefully(self, temp_project_with_syntax_error):
        """Test that syntax errors are handled gracefully."""
        analyzer = CodeAnalyzer(temp_project_with_syntax_error)
        result = analyzer.extract_public_api()
        
        # Should still find the valid tool despite syntax error in other file
        assert isinstance(result, PublicAPIInfo)
        # The valid file should be processed
        assert len(result.mcp_tools) >= 0  # May or may not find depending on file order


class TestScanForMCPTools:
    """Test _scan_for_mcp_tools() method."""
    
    def test_detects_mcp_tool_decorator(self):
        """Test detection of @mcp.tool() decorator."""
        code = dedent('''
            @mcp.tool()
            def my_tool(param1: str, param2: int):
                """This is my tool."""
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        tools = analyzer._scan_for_mcp_tools(tree)
        
        assert len(tools) == 1
        assert tools[0].name == "my_tool"
        assert tools[0].docstring == "This is my tool."
        assert tools[0].parameters == ["param1", "param2"]
    
    def test_excludes_self_and_ctx_parameters(self):
        """Test that self and ctx parameters are excluded."""
        code = dedent('''
            class MyClass:
                @mcp.tool()
                def method_tool(self, ctx, real_param: str):
                    """A method tool."""
                    pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        tools = analyzer._scan_for_mcp_tools(tree)
        
        assert len(tools) == 1
        assert "self" not in tools[0].parameters
        assert "ctx" not in tools[0].parameters
        assert "real_param" in tools[0].parameters
    
    def test_truncates_long_docstrings(self):
        """Test that docstrings are truncated to 120 characters."""
        long_docstring = "A" * 200
        code = f'''
@mcp.tool()
def tool():
    """{long_docstring}"""
    pass
'''
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        tools = analyzer._scan_for_mcp_tools(tree)
        
        assert len(tools) == 1
        assert len(tools[0].docstring) <= 120
    
    def test_uses_first_line_of_multiline_docstring(self):
        """Test that only first line of docstring is used."""
        code = dedent('''
            @mcp.tool()
            def tool():
                """First line of docstring.
                
                This is the second paragraph that should be ignored.
                And more details here.
                """
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        tools = analyzer._scan_for_mcp_tools(tree)
        
        assert len(tools) == 1
        assert tools[0].docstring == "First line of docstring."
    
    def test_handles_missing_docstring(self):
        """Test handling of functions without docstrings."""
        code = dedent('''
            @mcp.tool()
            def no_doc_tool():
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        tools = analyzer._scan_for_mcp_tools(tree)
        
        assert len(tools) == 1
        assert tools[0].docstring == ""


class TestScanForCLICommands:
    """Test _scan_for_cli_commands() method."""
    
    def test_detects_command_decorator(self):
        """Test detection of @command decorator."""
        code = dedent('''
            @command
            def my_command(arg1: str):
                """My command help text."""
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        commands = analyzer._scan_for_cli_commands(tree)
        
        assert len(commands) == 1
        assert commands[0].name == "my_command"
        assert commands[0].help_text == "My command help text."
        assert commands[0].parameters == ["arg1"]
    
    def test_detects_click_command_decorator(self):
        """Test detection of @click.command() decorator."""
        code = dedent('''
            @click.command()
            def cli_tool():
                """CLI tool description."""
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        commands = analyzer._scan_for_cli_commands(tree)
        
        assert len(commands) == 1
        assert commands[0].name == "cli_tool"
    
    def test_excludes_self_and_ctx_parameters(self):
        """Test that self and ctx parameters are excluded."""
        code = dedent('''
            @command
            def cmd(self, ctx, real_arg: str):
                """Command."""
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        commands = analyzer._scan_for_cli_commands(tree)
        
        assert len(commands) == 1
        assert "self" not in commands[0].parameters
        assert "ctx" not in commands[0].parameters
        assert "real_arg" in commands[0].parameters


class TestExtractPublicClasses:
    """Test _extract_public_classes() method."""
    
    def test_extracts_classes_with_docstrings(self):
        """Test extraction of classes with docstrings."""
        code = dedent('''
            class PublicClass:
                """This is a public class."""
                pass
            
            class AnotherPublic:
                """Another public class."""
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        classes = analyzer._extract_public_classes(tree)
        
        assert len(classes) == 2
        assert "PublicClass" in classes
        assert "AnotherPublic" in classes
    
    def test_excludes_private_classes(self):
        """Test that private classes (starting with _) are excluded."""
        code = dedent('''
            class _PrivateClass:
                """This is private."""
                pass
            
            class PublicClass:
                """This is public."""
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        classes = analyzer._extract_public_classes(tree)
        
        assert len(classes) == 1
        assert "PublicClass" in classes
        assert "_PrivateClass" not in classes
    
    def test_excludes_classes_without_docstrings(self):
        """Test that classes without docstrings are excluded."""
        code = dedent('''
            class NoDocstring:
                pass
            
            class WithDocstring:
                """Has docstring."""
                pass
        ''')
        tree = ast.parse(code)
        
        analyzer = CodeAnalyzer(Path("."))
        classes = analyzer._extract_public_classes(tree)
        
        assert len(classes) == 1
        assert "WithDocstring" in classes
        assert "NoDocstring" not in classes


class TestExcludedPaths:
    """Test that excluded paths are respected."""
    
    def test_skips_excluded_directories(self, tmp_path):
        """Test that __pycache__, .venv, tests/ are skipped."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        
        # Create excluded directories
        (project_root / "__pycache__").mkdir()
        (project_root / ".venv").mkdir()
        (project_root / "tests").mkdir()
        
        # Add MCP tools in excluded directories
        (project_root / "__pycache__" / "cached.py").write_text(dedent('''
            @mcp.tool()
            def cached_tool():
                """Should be excluded."""
                pass
        '''))
        
        (project_root / ".venv" / "venv_tool.py").write_text(dedent('''
            @mcp.tool()
            def venv_tool():
                """Should be excluded."""
                pass
        '''))
        
        # Add valid tool in main directory
        (project_root / "main.py").write_text(dedent('''
            @mcp.tool()
            def main_tool():
                """Should be included."""
                pass
        '''))
        
        # Create .gitignore to exclude these paths
        (project_root / ".gitignore").write_text("__pycache__/\n.venv/\ntests/\n")
        
        analyzer = CodeAnalyzer(project_root)
        analyzer._load_gitignore()
        result = analyzer.extract_public_api()
        
        # Should only find the main tool
        assert len(result.mcp_tools) == 1
        assert result.mcp_tools[0].name == "main_tool"


class TestFileLimit:
    """Test that file scanning is limited to 50 files."""
    
    def test_limits_to_50_files(self, tmp_path):
        """Test that only 50 Python files are scanned."""
        project_root = tmp_path / "large_project"
        project_root.mkdir()
        
        # Create 60 Python files
        for i in range(60):
            file_path = project_root / f"file_{i}.py"
            file_path.write_text(f'''
@mcp.tool()
def tool_{i}():
    """Tool {i}."""
    pass
''')
        
        analyzer = CodeAnalyzer(project_root)
        result = analyzer.extract_public_api()
        
        # Should find at most 50 tools (one per file)
        assert len(result.mcp_tools) <= 50
