"""Advanced CLI tests - argument combinations and edge cases."""
import os
from pathlib import Path
import pytest
from typer.testing import CliRunner
from hiveforge.cli import app


runner = CliRunner()


class TestCLIArgumentCombinations:
    """Test suite for CLI argument combinations."""

    def test_both_short_flags_together(self, tmp_path):
        """CLI should accept both -n and -f flags together."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(app, ["-n", "test-project"])
            result = runner.invoke(app, ["-n", "test-project", "-f"])
            assert result.exit_code == 0
            assert "✅ KIRO v05 'test-project' initialized!" in result.stdout

    def test_long_and_short_flags_mixed(self, tmp_path):
        """CLI should accept mixed long and short flags."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(app, ["--project-name", "test-project"])
            result = runner.invoke(app, ["-n", "test-project", "--force"])
            assert result.exit_code == 0

    def test_flag_order_independence(self, tmp_path):
        """Flags should work in any order."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Force before project-name
            runner.invoke(app, ["-n", "test1"])
            result1 = runner.invoke(app, ["--force", "--project-name", "test1"])
            assert result1.exit_code == 0
            
            # Project-name before force
            runner.invoke(app, ["-n", "test2"])
            result2 = runner.invoke(app, ["--project-name", "test2", "--force"])
            assert result2.exit_code == 0

    def test_multiple_runs_same_session(self, tmp_path):
        """Multiple CLI runs in same session should work independently."""
        dir1 = tmp_path / "project1"
        dir2 = tmp_path / "project2"
        dir1.mkdir()
        dir2.mkdir()
        
        original_dir = os.getcwd()
        try:
            # First run
            os.chdir(dir1)
            result1 = runner.invoke(app, ["-n", "app-one"])
            assert result1.exit_code == 0
            
            # Second run in different directory
            os.chdir(dir2)
            result2 = runner.invoke(app, ["-n", "app-two"])
            assert result2.exit_code == 0
            
            # Verify both projects exist
            assert (dir1 / ".kiro").exists()
            assert (dir2 / ".kiro").exists()
        finally:
            os.chdir(original_dir)


class TestCLIEdgeCases:
    """Test suite for CLI edge cases."""

    def test_project_name_with_numbers(self, tmp_path):
        """CLI should accept project names with numbers."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", "project-123"])
            assert result.exit_code == 0
            assert "project-123" in result.stdout

    def test_very_long_project_name(self, tmp_path):
        """CLI should accept very long valid project names."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            long_name = "my-very-long-project-name-with-many-hyphens"
            result = runner.invoke(app, ["--project-name", long_name])
            assert result.exit_code == 0
            assert long_name in result.stdout

    def test_single_word_project_name(self, tmp_path):
        """CLI should accept single-word project names."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", "app"])
            assert result.exit_code == 0
            assert "app" in result.stdout

    def test_cli_output_includes_next_steps(self, tmp_path):
        """CLI output should include next steps guidance."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", "test-project"])
            assert result.exit_code == 0
            assert "Next:" in result.stdout or "Reload" in result.stdout

    def test_cli_shows_file_counts_in_output(self, tmp_path):
        """CLI should show file counts in success message."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", "test-project"])
            assert result.exit_code == 0
            # Should show counts for agents and steering
            assert "(7)" in result.stdout
            assert "(8)" in result.stdout


class TestCLIErrorMessages:
    """Test suite for CLI error message quality."""

    def test_error_message_suggests_kebab_case(self, tmp_path):
        """Error messages should suggest kebab-case format."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", "BadName"])
            assert result.exit_code == 1
            error_output = result.stdout + result.stderr
            assert "kebab-case" in error_output

    def test_error_message_shows_example(self, tmp_path):
        """Error messages should show example of valid format."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", "Bad Name"])
            assert result.exit_code == 1
            error_output = result.stdout + result.stderr
            assert "my-project" in error_output or "example" in error_output.lower()

    def test_duplicate_error_mentions_force_flag(self, tmp_path):
        """Duplicate error should mention --force flag."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(app, ["--project-name", "test-project"])
            result = runner.invoke(app, ["--project-name", "test-project"])
            assert result.exit_code == 1
            error_output = result.stdout + result.stderr
            assert "--force" in error_output or "force" in error_output.lower()

    def test_error_output_uses_emoji(self, tmp_path):
        """Error messages should use emoji for visual clarity."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["--project-name", "Bad Name"])
            assert result.exit_code == 1
            error_output = result.stdout + result.stderr
            # Should have error emoji or "Invalid" message
            assert "❌" in error_output or "Invalid" in error_output
