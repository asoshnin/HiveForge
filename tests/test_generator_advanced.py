"""Advanced tests for generator module - content validation and edge cases."""
import os
from pathlib import Path
import pytest
from kiro_init.generator import generate_project


class TestGeneratorContentValidation:
    """Test suite for validating generated file content."""

    def test_orchestrator_has_toolsettings(self, tmp_path, sample_project_name):
        """Orchestrator.md should have toolsSettings configuration."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)
        
        orchestrator = (tmp_path / ".kiro" / "agents" / "orchestrator.md").read_text(encoding="utf-8")
        assert "toolsSettings:" in orchestrator
        assert "allowedPaths:" in orchestrator
        assert "deniedPaths:" in orchestrator

    def test_orchestrator_has_use_subagent_config(self, tmp_path, sample_project_name):
        """Orchestrator.md should have use_subagent configuration."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)
        
        orchestrator = (tmp_path / ".kiro" / "agents" / "orchestrator.md").read_text(encoding="utf-8")
        assert "use_subagent:" in orchestrator
        assert "availableAgents:" in orchestrator
        assert "data_architect" in orchestrator
        assert "backend_engineer" in orchestrator

    def test_swarm_state_has_valid_iso_timestamp(self, tmp_path, sample_project_name):
        """swarm_state.md timestamp should be valid ISO 8601 format."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)
        
        swarm = (tmp_path / "swarm_state.md").read_text(encoding="utf-8")
        
        # Extract timestamps and validate format
        import re
        from datetime import datetime
        timestamps = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z', swarm)
        assert len(timestamps) > 0, "No ISO timestamps found in swarm_state.md"
        
        # Verify first timestamp is parseable
        timestamp_str = timestamps[0].replace('Z', '+00:00')
        parsed = datetime.fromisoformat(timestamp_str)
        assert parsed is not None

    def test_swarm_state_has_required_sections(self, tmp_path, sample_project_name):
        """swarm_state.md should have all required sections."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)
        
        swarm = (tmp_path / "swarm_state.md").read_text(encoding="utf-8")
        required_sections = [
            "## 1. Project Identity & Context",
            "## 2. Clarified Vision & Requirements",
            "## 3. Architecture & Technical Context",
            "## 4. Delegation Tree & Task Management",
            "## 5. Red Team Audit Status",
        ]
        for section in required_sections:
            assert section in swarm, f"Missing section: {section}"

    def test_agent_files_have_substantial_content(self, tmp_path, sample_project_name):
        """All agent files should have substantial content (>1KB)."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)
        
        for agent_file in (tmp_path / ".kiro" / "agents").glob("*.md"):
            content = agent_file.read_text(encoding="utf-8")
            assert len(content) > 1000, f"{agent_file.name} is too small ({len(content)} bytes)"

    def test_steering_files_have_content(self, tmp_path, sample_project_name):
        """All steering files should have meaningful content."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)
        
        for steering_file in (tmp_path / ".kiro" / "steering").glob("*.md"):
            content = steering_file.read_text(encoding="utf-8")
            # Steering files are shorter but should still have content
            assert len(content) > 100, f"{steering_file.name} is too small ({len(content)} bytes)"


class TestGeneratorEdgeCases:
    """Test suite for edge cases."""

    def test_project_name_with_numbers(self, tmp_path):
        """Project names with numbers should work correctly."""
        os.chdir(tmp_path)
        generate_project("project-123", force=False)
        
        swarm = (tmp_path / "swarm_state.md").read_text(encoding="utf-8")
        assert "project-123" in swarm

    def test_very_long_project_name(self, tmp_path):
        """Very long project names should work if valid."""
        os.chdir(tmp_path)
        long_name = "my-very-long-project-name-with-many-words-separated-by-hyphens"
        generate_project(long_name, force=False)
        
        swarm = (tmp_path / "swarm_state.md").read_text(encoding="utf-8")
        assert long_name in swarm

    def test_generated_files_use_utf8_encoding(self, tmp_path, sample_project_name):
        """All generated files should use UTF-8 encoding."""
        os.chdir(tmp_path)
        generate_project(sample_project_name, force=False)
        
        # Try to read all files with UTF-8 (should not raise UnicodeDecodeError)
        for md_file in (tmp_path / ".kiro").rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            assert len(content) > 0

    def test_full_workflow_generate_modify_regenerate(self, tmp_path):
        """Test complete workflow: generate, modify, regenerate with force."""
        os.chdir(tmp_path)
        
        # Generate
        generate_project("my-app", force=False)
        
        # Modify a file
        orchestrator = tmp_path / ".kiro" / "agents" / "orchestrator.md"
        original_content = orchestrator.read_text(encoding="utf-8")
        orchestrator.write_text("MODIFIED_CONTENT", encoding="utf-8")
        
        # Regenerate with force
        generate_project("my-app", force=True)
        
        # Verify original content restored
        new_content = orchestrator.read_text(encoding="utf-8")
        assert new_content == original_content
        assert "MODIFIED_CONTENT" not in new_content

    def test_multiple_projects_in_different_directories(self, tmp_path):
        """Should be able to generate multiple projects in different directories."""
        project1_dir = tmp_path / "project1"
        project2_dir = tmp_path / "project2"
        project1_dir.mkdir()
        project2_dir.mkdir()
        
        # Generate first project
        os.chdir(project1_dir)
        generate_project("app-one", force=False)
        
        # Generate second project
        os.chdir(project2_dir)
        generate_project("app-two", force=False)
        
        # Verify both exist independently
        swarm1 = (project1_dir / "swarm_state.md").read_text(encoding="utf-8")
        swarm2 = (project2_dir / "swarm_state.md").read_text(encoding="utf-8")
        
        assert "app-one" in swarm1
        assert "app-two" in swarm2
        assert "app-two" not in swarm1
        assert "app-one" not in swarm2

    def test_generation_completes_quickly(self, tmp_path, sample_project_name):
        """Project generation should complete in reasonable time (<5 seconds)."""
        import time
        os.chdir(tmp_path)
        
        start = time.time()
        generate_project(sample_project_name, force=False)
        duration = time.time() - start
        
        assert duration < 5.0, f"Generation took {duration:.2f}s, should be <5s"
