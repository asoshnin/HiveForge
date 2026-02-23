"""
Unit tests for P2-4: Template Synchronization and Resolution

Tests verify:
1. Template sync verification script works correctly
2. Templates resolve to canonical location (hiveforge-power/)
3. Base templates are identical between src/ and hiveforge-power/
4. Template variants exist only in canonical location
"""

import pytest
from pathlib import Path
import filecmp
import sys
import subprocess


class TestTemplateSyncScript:
    """Test the template sync verification script."""
    
    def test_sync_script_exists(self):
        """Test that sync script exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "check_template_sync.py"
        assert script_path.exists(), "Template sync script not found"
    
    def test_sync_script_executable(self):
        """Test that sync script can be executed."""
        script_path = Path(__file__).parent.parent / "scripts" / "check_template_sync.py"
        
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )
        
        # Should exit with 0 (success) or 1 (differences found)
        assert result.returncode in [0, 1], f"Script failed with unexpected exit code: {result.returncode}"
    
    def test_sync_script_detects_identical_templates(self):
        """Test that script correctly identifies identical templates."""
        script_path = Path(__file__).parent.parent / "scripts" / "check_template_sync.py"
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )
        
        # Check output contains success message if templates are in sync
        if result.returncode == 0:
            assert "SUCCESS" in result.stdout
            assert "in sync" in result.stdout.lower()


class TestCanonicalLocation:
    """Test that canonical location is correctly identified."""
    
    def test_canonical_location_is_hiveforge_power(self):
        """Test that hiveforge-power/ is the canonical location."""
        project_root = Path(__file__).parent.parent.parent
        canonical_dir = project_root / "hiveforge-power" / "hiveforge" / "templates" / "steering"
        
        assert canonical_dir.exists(), "Canonical template directory not found"
    
    def test_canonical_location_has_base_templates(self):
        """Test that canonical location has all base templates."""
        project_root = Path(__file__).parent.parent.parent
        canonical_dir = project_root / "hiveforge-power" / "hiveforge" / "templates" / "steering"
        
        base_templates = [
            "api-standards.md",
            "architecture.md",
            "conventions.md",
            "db-standards.md",
            "project-vision.md",
            "qa-standards.md",
            "tech-stack.md",
            "ui-standards.md",
        ]
        
        for template in base_templates:
            template_path = canonical_dir / template
            assert template_path.exists(), f"Base template {template} not found in canonical location"
    
    def test_canonical_location_has_variants(self):
        """Test that canonical location has template variants."""
        project_root = Path(__file__).parent.parent.parent
        canonical_dir = project_root / "hiveforge-power" / "hiveforge" / "templates" / "steering"
        
        # Template variants should exist only in canonical location
        variants = [
            "api-standards.mcp_server.md",
            "tech-stack.cli_tool.md",
            "tech-stack.web_app.md",
        ]
        
        for variant in variants:
            variant_path = canonical_dir / variant
            assert variant_path.exists(), f"Template variant {variant} not found in canonical location"


class TestTemplateSync:
    """Test that base templates are synchronized."""
    
    def test_base_templates_are_identical(self):
        """Test that base templates in src/ and hiveforge-power/ are byte-for-byte identical."""
        project_root = Path(__file__).parent.parent.parent
        src_dir = project_root / "src" / "hiveforge" / "templates" / "steering"
        hf_dir = project_root / "hiveforge-power" / "hiveforge" / "templates" / "steering"
        
        # Skip if src/ doesn't exist (may be removed in future)
        if not src_dir.exists():
            pytest.skip("src/ template directory not found (may have been removed)")
        
        base_templates = [
            "api-standards.md",
            "architecture.md",
            "conventions.md",
            "db-standards.md",
            "project-vision.md",
            "qa-standards.md",
            "tech-stack.md",
            "ui-standards.md",
        ]
        
        differences = []
        for template in base_templates:
            src_file = src_dir / template
            hf_file = hf_dir / template
            
            if not src_file.exists() or not hf_file.exists():
                continue
            
            # Compare byte-for-byte
            if not filecmp.cmp(src_file, hf_file, shallow=False):
                differences.append(template)
        
        assert len(differences) == 0, (
            f"Templates differ between src/ and hiveforge-power/: {', '.join(differences)}\n"
            f"Canonical location: hiveforge-power/hiveforge/templates/steering/\n"
            f"Please sync changes from canonical location to src/"
        )
    
    def test_variants_not_in_src(self):
        """Test that template variants do NOT exist in src/ (only in canonical location)."""
        project_root = Path(__file__).parent.parent.parent
        src_dir = project_root / "src" / "hiveforge" / "templates" / "steering"
        
        # Skip if src/ doesn't exist
        if not src_dir.exists():
            pytest.skip("src/ template directory not found")
        
        variants = [
            "api-standards.mcp_server.md",
            "tech-stack.cli_tool.md",
            "tech-stack.web_app.md",
        ]
        
        for variant in variants:
            variant_path = src_dir / variant
            assert not variant_path.exists(), (
                f"Template variant {variant} should NOT exist in src/\n"
                f"Variants should only exist in canonical location: hiveforge-power/"
            )


class TestTemplateResolution:
    """Test template resolution logic."""
    
    def test_resolve_base_template(self):
        """Test resolving base template path."""
        from hiveforge.steering.agents.steering_assistant import SteeringAssistant
        from unittest.mock import Mock
        
        project_root = Path(__file__).parent.parent.parent / "hiveforge-power"
        
        assistant = SteeringAssistant(
            knowledge_base=Mock(),
            gap_analysis=Mock(),
            project_root=project_root
        )
        
        # Resolve base template
        result = assistant._resolve_template_path('tech-stack.md')
        
        # Should resolve to canonical location
        expected = project_root / "hiveforge" / "templates" / "steering" / "tech-stack.md"
        assert result == expected
        assert result.exists()
    
    def test_resolve_variant_template(self):
        """Test resolving project-type-specific variant."""
        from hiveforge.steering.agents.steering_assistant import SteeringAssistant
        from unittest.mock import Mock
        
        project_root = Path(__file__).parent.parent.parent / "hiveforge-power"
        
        # Mock knowledge base with project type
        kb = Mock()
        kb.code_analysis = Mock()
        kb.code_analysis.project_type = 'cli_tool'
        
        assistant = SteeringAssistant(
            knowledge_base=kb,
            gap_analysis=Mock(),
            project_root=project_root
        )
        
        # Resolve template - should prefer variant
        result = assistant._resolve_template_path('tech-stack.md')
        
        # Should resolve to variant in canonical location
        expected = project_root / "hiveforge" / "templates" / "steering" / "tech-stack.cli_tool.md"
        assert result == expected
        assert result.exists()
    
    def test_resolve_fallback_to_base(self):
        """Test fallback to base template when variant doesn't exist."""
        from hiveforge.steering.agents.steering_assistant import SteeringAssistant
        from unittest.mock import Mock
        
        project_root = Path(__file__).parent.parent.parent / "hiveforge-power"
        
        # Mock knowledge base with project type that has no variant
        kb = Mock()
        kb.code_analysis = Mock()
        kb.code_analysis.project_type = 'library'  # No variant for library
        
        assistant = SteeringAssistant(
            knowledge_base=kb,
            gap_analysis=Mock(),
            project_root=project_root
        )
        
        # Resolve template - should fall back to base
        result = assistant._resolve_template_path('tech-stack.md')
        
        # Should resolve to base template in canonical location
        expected = project_root / "hiveforge" / "templates" / "steering" / "tech-stack.md"
        assert result == expected
        assert result.exists()


class TestDocumentation:
    """Test that documentation exists for template management."""
    
    def test_templates_documentation_exists(self):
        """Test that TEMPLATES.md documentation exists."""
        doc_path = Path(__file__).parent.parent / "docs" / "TEMPLATES.md"
        assert doc_path.exists(), "TEMPLATES.md documentation not found"
    
    def test_documentation_mentions_canonical_location(self):
        """Test that documentation specifies canonical location."""
        doc_path = Path(__file__).parent.parent / "docs" / "TEMPLATES.md"
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should mention canonical location
        assert "canonical" in content.lower()
        assert "hiveforge-power" in content.lower()
    
    def test_documentation_has_sync_instructions(self):
        """Test that documentation includes sync instructions."""
        doc_path = Path(__file__).parent.parent / "docs" / "TEMPLATES.md"
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have sync instructions
        assert "sync" in content.lower()
        assert "check_template_sync.py" in content


class TestCIIntegration:
    """Test CI workflow integration."""
    
    def test_ci_workflow_exists(self):
        """Test that CI workflow file exists."""
        project_root = Path(__file__).parent.parent.parent
        ci_path = project_root / ".github" / "workflows" / "ci.yml"
        assert ci_path.exists(), "CI workflow file not found"
    
    def test_ci_workflow_has_template_check(self):
        """Test that CI workflow includes template sync check."""
        project_root = Path(__file__).parent.parent.parent
        ci_path = project_root / ".github" / "workflows" / "ci.yml"
        
        with open(ci_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should include template sync check
        assert "template" in content.lower()
        assert "check_template_sync.py" in content
    
    def test_ci_workflow_has_template_sync_job(self):
        """Test that CI workflow has dedicated template-sync-check job."""
        project_root = Path(__file__).parent.parent.parent
        ci_path = project_root / ".github" / "workflows" / "ci.yml"
        
        with open(ci_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have template-sync-check job
        assert "template-sync-check" in content.lower()
