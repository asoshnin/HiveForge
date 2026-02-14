"""Unit tests for generator module."""
import os
import re
from pathlib import Path
import pytest
from kiro_init.generator import generate_project


class TestGenerateProject:
    """Test suite for generate_project function."""

    def test_creates_all_directories(self, tmp_path, sample_project_name):
        """Generator should create all required directories."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        assert (tmp_path / ".kiro" / "agents").exists()
        assert (tmp_path / ".kiro" / "steering").exists()
        assert (tmp_path / ".swarm" / "plan").exists()
        assert (tmp_path / ".swarm" / "audit_logs").exists()

    def test_creates_correct_number_of_agent_files(self, tmp_path, sample_project_name):
        """Generator should create exactly 7 agent files."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        agents = list((tmp_path / ".kiro" / "agents").glob("*.md"))
        assert len(agents) == 7

    def test_creates_correct_number_of_steering_files(self, tmp_path, sample_project_name):
        """Generator should create exactly 8 steering files."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        steering = list((tmp_path / ".kiro" / "steering").glob("*.md"))
        assert len(steering) == 8

    def test_creates_swarm_state_file(self, tmp_path, sample_project_name):
        """Generator should create swarm_state.md in project root."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        assert (tmp_path / "swarm_state.md").exists()

    def test_creates_expected_agent_files(self, tmp_path, sample_project_name, expected_agent_files):
        """Generator should create all expected agent files."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        for filename in expected_agent_files:
            assert (tmp_path / ".kiro" / "agents" / filename).exists()

    def test_creates_expected_steering_files(self, tmp_path, sample_project_name, expected_steering_files):
        """Generator should create all expected steering files."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        for filename in expected_steering_files:
            assert (tmp_path / ".kiro" / "steering" / filename).exists()

    def test_replaces_project_name_placeholder(self, tmp_path):
        """swarm_state.md should have {PROJECT_NAME} replaced."""
        os.chdir(tmp_path)
        project_name = "my-test-project"
        generate_project(project_name, force=False)

        swarm_content = (tmp_path / "swarm_state.md").read_text(encoding="utf-8")
        assert project_name in swarm_content
        assert "{PROJECT_NAME}" not in swarm_content

    def test_replaces_timestamp_placeholder(self, tmp_path, sample_project_name):
        """swarm_state.md should have {ISO_TIMESTAMP} replaced with valid ISO timestamp."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        swarm_content = (tmp_path / "swarm_state.md").read_text(encoding="utf-8")
        assert "{ISO_TIMESTAMP}" not in swarm_content
        # Verify ISO 8601 format (basic check)
        assert re.search(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', swarm_content)

    def test_duplicate_project_raises_error(self, tmp_path, sample_project_name):
        """Generating twice without --force should raise FileExistsError."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        with pytest.raises(FileExistsError, match=".kiro/ exists"):
            generate_project(sample_project_name, force=False)

    def test_force_flag_overwrites_existing_project(self, tmp_path, sample_project_name):
        """Force flag should overwrite existing project."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        # Modify a file to verify overwrite
        orchestrator_path = tmp_path / ".kiro" / "agents" / "orchestrator.md"
        orchestrator_path.write_text("MODIFIED_CONTENT", encoding="utf-8")

        # Generate again with force
        generate_project(sample_project_name, force=True)

        # Verify file was overwritten (no longer contains "MODIFIED_CONTENT")
        content = orchestrator_path.read_text(encoding="utf-8")
        assert "MODIFIED_CONTENT" not in content

    def test_agent_files_have_content(self, tmp_path, sample_project_name):
        """Generated agent files should not be empty."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        for agent_file in (tmp_path / ".kiro" / "agents").glob("*.md"):
            content = agent_file.read_text(encoding="utf-8")
            assert len(content) > 100  # Reasonable minimum content length

    def test_steering_files_have_content(self, tmp_path, sample_project_name):
        """Generated steering files should not be empty."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        for steering_file in (tmp_path / ".kiro" / "steering").glob("*.md"):
            content = steering_file.read_text(encoding="utf-8")
            assert len(content) > 50  # Reasonable minimum content length

    def test_prints_success_message(self, tmp_path, sample_project_name, capsys):
        """Generator should print success message with file counts."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)

        captured = capsys.readouterr()
        assert "✅ KIRO v05" in captured.out
        assert sample_project_name in captured.out
        assert "(7)" in captured.out  # 7 agents
        assert "(8)" in captured.out  # 8 steering files
