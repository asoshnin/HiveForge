"""Integration tests for CLI module."""
from pathlib import Path
import pytest
from typer.testing import CliRunner
from kiro_init.cli import app


runner = CliRunner()


class TestCLI:
    """Test suite for CLI interface."""

    def test_help_command(self):
        """CLI should display help message."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Initialize KIRO v05 project" in result.stdout
        assert "--project-name" in result.stdout
        assert "--force" in result.stdout

    def test_generate_project_with_name_flag(self, tmp_path):
        """CLI should generate project with --project-name flag."""
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(app, ["--project-name", "test-project"])
            assert result.exit_code == 0
            assert "✅ KIRO v05 'test-project' initialized!" in result.stdout
            
            # Verify files were created
            project_path = Path(td)
            assert (project_path / ".kiro" / "agents").exists()
            assert (project_path / ".kiro" / "steering").exists()
            assert (project_path / "swarm_state.md").exists()

    def test_generate_project_with_short_flag(self, tmp_path):
        """CLI should accept -n short flag for project name."""
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(app, ["-n", "my-project"])
            assert result.exit_code == 0
            assert "✅ KIRO v05 'my-project' initialized!" in result.stdout

    def test_generate_project_uses_current_dir_name(self, tmp_path):
        """CLI without --project-name should use current directory name if valid."""
        # Create a directory with a valid kebab-case name
        test_dir = tmp_path / "my-test-app"
        test_dir.mkdir()
        
        # Change to that directory and run CLI
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(test_dir)
            result = runner.invoke(app, [])
            # Should succeed because directory name is valid kebab-case
            assert result.exit_code == 0
            assert "Using: my-test-app" in result.stdout
            assert "✅ KIRO v05 'my-test-app' initialized!" in result.stdout
        finally:
            os.chdir(original_dir)
    
    def test_generate_project_invalid_current_dir_name(self, tmp_path):
        """CLI without --project-name should fail if current directory name is invalid."""
        # Create a directory with an invalid name (underscores)
        test_dir = tmp_path / "invalid_dir_name"
        test_dir.mkdir()
        
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(test_dir)
            result = runner.invoke(app, [])
            # Should fail because directory name has underscores
            assert result.exit_code == 1
            error_output = result.stdout + result.stderr
            assert "Using: invalid_dir_name" in result.stdout
            assert "Invalid" in error_output or "kebab-case" in error_output
        finally:
            os.chdir(original_dir)

    def test_invalid_project_name_shows_error(self, tmp_path):
        """CLI should show error for invalid project names."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", "Bad Name"])
            assert result.exit_code == 1
            # Typer outputs errors to stderr
            error_output = result.stdout + result.stderr
            assert "❌" in error_output or "Invalid: 'Bad Name'" in error_output
            assert "kebab-case" in error_output

    def test_duplicate_project_shows_error(self, tmp_path):
        """Running CLI twice should show duplicate error."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First run
            runner.invoke(app, ["--project-name", "test-project"])
            
            # Second run without force
            result = runner.invoke(app, ["--project-name", "test-project"])
            assert result.exit_code == 1
            error_output = result.stdout + result.stderr
            assert ".kiro/ exists" in error_output
            assert "--force" in error_output

    def test_force_flag_overwrites_existing_project(self, tmp_path):
        """Force flag should overwrite existing project."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # First run
            runner.invoke(app, ["--project-name", "test-project"])
            
            # Second run with force
            result = runner.invoke(app, ["--project-name", "test-project", "--force"])
            assert result.exit_code == 0
            assert "✅ KIRO v05 'test-project' initialized!" in result.stdout

    def test_force_short_flag(self, tmp_path):
        """CLI should accept -f short flag for force."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(app, ["-n", "test-project"])
            result = runner.invoke(app, ["-n", "test-project", "-f"])
            assert result.exit_code == 0
            assert "✅ KIRO v05 'test-project' initialized!" in result.stdout

    @pytest.mark.parametrize("invalid_name", [
        "Bad Name",
        "test_project",
        "TestProject",
        "test.project",
    ])
    def test_multiple_invalid_names_via_cli(self, tmp_path, invalid_name):
        """Parametrized test for multiple invalid names via CLI."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", invalid_name])
            assert result.exit_code == 1
            error_output = result.stdout + result.stderr
            assert "❌" in error_output or "Invalid" in error_output

    def test_generated_files_count(self, tmp_path):
        """CLI should generate correct number of files."""
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(app, ["--project-name", "test-project"])
            assert result.exit_code == 0
            
            project_path = Path(td)
            agents = list((project_path / ".kiro" / "agents").glob("*.md"))
            steering = list((project_path / ".kiro" / "steering").glob("*.md"))
            
            assert len(agents) == 7
            assert len(steering) == 8
            assert "(7)" in result.stdout
            assert "(8)" in result.stdout
