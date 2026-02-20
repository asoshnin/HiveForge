"""
Tests for the CustomizationDetector class.

Tests both unit examples and property-based tests for customization detection
functionality.
"""

import pytest
from hypothesis import given, strategies as st

from hiveforge.steering.customization_detector import CustomizationDetector
from hiveforge.steering.models import Customization


class TestCustomizationDetectorUnit:
    """Unit tests for CustomizationDetector with specific examples."""
    
    def test_no_customizations_identical_content(self):
        """Test that identical content produces no customizations."""
        template = "# Section 1\n{placeholder}\n\n# Section 2\n{another placeholder}\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(template)
        
        assert len(customizations) == 0
    
    def test_detect_placeholder_replacement(self):
        """Test detection of replaced placeholders."""
        template = "# Tech Stack\n\nBackend: {Python|Node.js|Go}\n"
        current = "# Tech Stack\n\nBackend: Python 3.11 with FastAPI\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        # Should have high confidence for placeholder replacement
        assert any(c.confidence >= 0.7 for c in customizations)
        assert any("Python 3.11" in c.customized for c in customizations)
    
    def test_detect_custom_section_addition(self):
        """Test detection of new custom sections."""
        template = "# Section 1\nContent 1\n\n# Section 2\nContent 2\n"
        current = "# Section 1\nContent 1\n\n# Custom Section\nMy custom content\n\n# Section 2\nContent 2\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        # Custom section should have high confidence
        assert any(c.confidence >= 0.7 for c in customizations)
        assert any("Custom Section" in c.customized for c in customizations)
    
    def test_detect_content_addition(self):
        """Test detection of substantial content additions."""
        template = "# Overview\n\n{Project description}\n"
        current = "# Overview\n\nThis is a comprehensive project that does many things. " \
                 "It includes multiple features and serves various use cases. " \
                 "The architecture is designed for scalability and maintainability.\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        # Substantial content should have high confidence
        assert any(c.confidence >= 0.6 for c in customizations)
    
    def test_detect_code_block_addition(self):
        """Test detection of code blocks as customizations."""
        template = "# Example\n\n{code example}\n"
        current = "# Example\n\n```python\ndef hello():\n    print('world')\n```\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        # Code blocks should have high confidence
        assert any(c.confidence >= 0.6 for c in customizations)
        assert any("```" in c.customized for c in customizations)
    
    def test_detect_table_addition(self):
        """Test detection of tables as customizations."""
        template = "# Dependencies\n\n{list dependencies}\n"
        current = "# Dependencies\n\n| Name | Version | Purpose |\n|------|---------|----------|\n| FastAPI | 0.100.0 | Web framework |\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        # Tables should have high confidence
        assert any(c.confidence >= 0.6 for c in customizations)
        assert any("|" in c.customized for c in customizations)
    
    def test_detect_list_addition(self):
        """Test detection of lists as customizations."""
        template = "# Features\n\n{feature list}\n"
        current = "# Features\n\n- Authentication\n- Authorization\n- Data validation\n- API documentation\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        assert any(c.confidence >= 0.5 for c in customizations)
    
    def test_whitespace_only_changes_low_confidence(self):
        """Test that whitespace-only changes have low confidence."""
        template = "# Section\nContent here\n"
        current = "# Section\n  Content here  \n"  # Added spaces
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should either have no customizations or very low confidence
        if customizations:
            assert all(c.confidence < 0.5 for c in customizations)
    
    def test_minor_edit_low_confidence(self):
        """Test that minor edits have lower confidence."""
        template = "# Section\nThis is content.\n"
        current = "# Section\nThis is content!\n"  # Just added punctuation
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Minor changes should have lower confidence
        if customizations:
            assert all(c.confidence < 0.7 for c in customizations)
    
    def test_section_tracking(self):
        """Test that customizations are tracked by section."""
        template = "# Section 1\n{content}\n\n# Section 2\n{content}\n"
        current = "# Section 1\nCustom content 1\n\n# Section 2\nCustom content 2\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should have customizations for both sections
        sections = [c.section for c in customizations]
        assert "Section 1" in sections or "Section 2" in sections
    
    def test_confidence_score_range(self):
        """Test that confidence scores are in valid range [0.0, 1.0]."""
        template = "# Section\n{placeholder}\n"
        current = "# Section\nSome custom content here\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        for customization in customizations:
            assert 0.0 <= customization.confidence <= 1.0
    
    def test_empty_template(self):
        """Test with empty template."""
        template = ""
        current = "# New Section\nContent\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # All content is customization
        assert len(customizations) >= 1
    
    def test_empty_current_content(self):
        """Test with empty current content."""
        template = "# Section\nContent\n"
        current = ""
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Deletion detected
        assert len(customizations) >= 1
    
    def test_multiple_placeholder_replacements(self):
        """Test detection of multiple placeholder replacements."""
        template = "# Config\n\nLanguage: {language}\nFramework: {framework}\nDatabase: {database}\n"
        current = "# Config\n\nLanguage: Python 3.11\nFramework: FastAPI\nDatabase: PostgreSQL 15\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should detect the replacements
        assert len(customizations) >= 1
        # Should have reasonable confidence
        assert any(c.confidence >= 0.5 for c in customizations)
    
    def test_partial_placeholder_replacement(self):
        """Test when only some placeholders are replaced."""
        template = "# Config\n\nLanguage: {language}\nFramework: {framework}\n"
        current = "# Config\n\nLanguage: Python 3.11\nFramework: {framework}\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should detect the partial replacement
        assert len(customizations) >= 1
    
    def test_todo_marker_replacement(self):
        """Test detection of TODO marker replacements."""
        template = "# Section\n\nTODO: Add content here\n"
        current = "# Section\n\nThis is the actual content that was added.\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        # Replacing TODO should have high confidence
        assert any(c.confidence >= 0.6 for c in customizations)
    
    def test_ellipsis_replacement(self):
        """Test detection of ellipsis (...) replacements."""
        template = "# Features\n\n...\n"
        current = "# Features\n\n- Feature 1\n- Feature 2\n- Feature 3\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        assert any(c.confidence >= 0.6 for c in customizations)
    
    def test_preserve_original_and_customized_content(self):
        """Test that original and customized content are preserved."""
        template = "# Section\n{placeholder}\n"
        current = "# Section\nCustom content\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        customization = customizations[0]
        assert "{placeholder}" in customization.original or customization.original == "{placeholder}"
        assert "Custom content" in customization.customized
    
    def test_very_similar_content_low_confidence(self):
        """Test that very similar content has lower confidence."""
        template = "# Section\nThis is some content.\n"
        current = "# Section\nThis is some content here.\n"  # Just added "here"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Very similar changes should have lower confidence
        if customizations:
            assert all(c.confidence < 0.8 for c in customizations)
    
    def test_very_different_content_high_confidence(self):
        """Test that very different content has higher confidence."""
        template = "# Section\n{placeholder}\n"
        current = "# Section\nCompletely different content with many details and explanations.\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        assert any(c.confidence >= 0.6 for c in customizations)


class TestCustomizationDetectorProperties:
    """Property-based tests for CustomizationDetector."""
    
    @given(st.text(min_size=0, max_size=1000))
    def test_identical_content_no_customizations(self, content: str):
        """Property: Identical content should produce no customizations."""
        detector = CustomizationDetector(content)
        customizations = detector.detect_customizations(content)
        
        assert len(customizations) == 0
    
    @given(st.text(min_size=1, max_size=500))
    def test_confidence_scores_in_range(self, template: str):
        """Property: All confidence scores should be in [0.0, 1.0]."""
        current = template + "\nAdditional content"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        for customization in customizations:
            assert 0.0 <= customization.confidence <= 1.0
    
    @given(
        st.text(min_size=1, max_size=500),
        st.text(min_size=1, max_size=500)
    )
    def test_detection_is_deterministic(self, template: str, current: str):
        """Property: Running detection twice should give identical results."""
        detector = CustomizationDetector(template)
        
        customizations1 = detector.detect_customizations(current)
        customizations2 = detector.detect_customizations(current)
        
        assert len(customizations1) == len(customizations2)
        
        for c1, c2 in zip(customizations1, customizations2):
            assert c1.section == c2.section
            assert c1.original == c2.original
            assert c1.customized == c2.customized
            assert c1.confidence == c2.confidence
    
    @given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=20))
    def test_adding_content_creates_customization(self, lines: list):
        """Property: Adding content should create at least one customization."""
        template = "\n".join(lines)
        current = template + "\n\nNew custom section with content"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should detect the addition
        assert len(customizations) >= 1
    
    @given(st.lists(st.text(min_size=1, max_size=100), min_size=2, max_size=20))
    def test_removing_content_creates_customization(self, lines: list):
        """Property: Removing content should create at least one customization."""
        template = "\n".join(lines)
        current = "\n".join(lines[:-1])  # Remove last line
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should detect the removal
        if len(lines) > 1:
            assert len(customizations) >= 1
    
    @given(st.text(min_size=10, max_size=500))
    def test_placeholder_replacement_high_confidence(self, content: str):
        """Property: Replacing placeholders should have higher confidence."""
        template = "# Section\n\n{placeholder}\n"
        current = f"# Section\n\n{content}\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # If customizations detected, at least one should have decent confidence
        if customizations and len(content.strip()) > 20:
            assert any(c.confidence >= 0.5 for c in customizations)
    
    @given(
        st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=20),
        st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=20)
    )
    def test_customization_objects_have_required_fields(
        self, template_lines: list, current_lines: list
    ):
        """Property: All customization objects should have required fields."""
        template = "\n".join(template_lines)
        current = "\n".join(current_lines)
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        for customization in customizations:
            assert isinstance(customization.section, str)
            assert isinstance(customization.original, str)
            assert isinstance(customization.customized, str)
            assert isinstance(customization.confidence, float)
    
    @given(st.text(min_size=0, max_size=500))
    def test_empty_current_content_handling(self, template: str):
        """Property: Empty current content should be handled gracefully."""
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations("")
        
        # Should not crash, may or may not have customizations
        assert isinstance(customizations, list)
        for c in customizations:
            assert 0.0 <= c.confidence <= 1.0
    
    @given(st.text(min_size=1, max_size=500))
    def test_empty_template_handling(self, current: str):
        """Property: Empty template should be handled gracefully."""
        detector = CustomizationDetector("")
        customizations = detector.detect_customizations(current)
        
        # Should not crash
        assert isinstance(customizations, list)
        for c in customizations:
            assert 0.0 <= c.confidence <= 1.0
    
    @given(
        st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=15),
        st.integers(min_value=0, max_value=10)
    )
    def test_adding_lines_increases_customizations(self, lines: list, num_additions: int):
        """Property: Adding more lines should not decrease customization count."""
        template = "\n".join(lines)
        current = template + "\n" + "\n".join([f"Added line {i}" for i in range(num_additions)])
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        if num_additions > 0:
            # Should have at least one customization
            assert len(customizations) >= 1
    
    @given(st.text(min_size=10, max_size=500))
    def test_substantial_content_high_confidence(self, content: str):
        """Property: Substantial content additions should have higher confidence."""
        # Only test with substantial content
        if len(content.strip()) < 200:
            return
        
        template = "# Section\n\n{placeholder}\n"
        current = f"# Section\n\n{content}\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Substantial content should have decent confidence
        if customizations:
            assert any(c.confidence >= 0.5 for c in customizations)


class TestCustomizationDetectorEdgeCases:
    """Edge case tests for CustomizationDetector."""
    
    def test_unicode_content(self):
        """Test with Unicode characters."""
        template = "# Section\n\n{content}\n"
        current = "# Section\n\n世界你好 Hello World Привет мир\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        assert any("世界" in c.customized for c in customizations)
    
    def test_special_regex_characters(self):
        """Test with special regex characters."""
        template = "# Section\n\n{content}\n"
        current = "# Section\n\n$pecial ch@rs: .*+?[]{}()|^\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should not crash with regex special chars
        assert isinstance(customizations, list)
    
    def test_very_long_content(self):
        """Test with very long content."""
        template = "# Section\n\n{content}\n"
        current = "# Section\n\n" + "a" * 5000 + "\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        # Long content should have high confidence
        assert any(c.confidence >= 0.6 for c in customizations)
    
    def test_multiple_consecutive_placeholders(self):
        """Test with multiple consecutive placeholders."""
        template = "# Section\n\n{placeholder1}\n{placeholder2}\n{placeholder3}\n"
        current = "# Section\n\nContent 1\nContent 2\nContent 3\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
    
    def test_nested_markdown_structures(self):
        """Test with nested markdown structures."""
        template = "# Section\n\n{content}\n"
        current = """# Section

## Subsection 1

Content here

### Sub-subsection

More content

## Subsection 2

Final content
"""
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        assert any(c.confidence >= 0.6 for c in customizations)
    
    def test_mixed_line_endings(self):
        """Test with mixed line endings."""
        template = "# Section\r\n{content}\r\n"
        current = "# Section\nCustom content\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should handle mixed line endings
        assert isinstance(customizations, list)
    
    def test_only_whitespace_content(self):
        """Test with only whitespace content."""
        template = "# Section\n\n{content}\n"
        current = "# Section\n\n   \n\t\n  \n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Whitespace-only should have low confidence or no detection
        if customizations:
            assert all(c.confidence < 0.6 for c in customizations)
    
    def test_mermaid_diagram_addition(self):
        """Test detection of Mermaid diagrams."""
        template = "# Architecture\n\n{diagram}\n"
        current = """# Architecture

```mermaid
graph TD
    A[Client] --> B[Server]
    B --> C[Database]
```
"""
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        assert len(customizations) >= 1
        # Mermaid diagrams should have high confidence
        assert any(c.confidence >= 0.6 for c in customizations)
        assert any("mermaid" in c.customized for c in customizations)
    
    def test_frontmatter_preservation(self):
        """Test that frontmatter changes are detected."""
        template = "---\ntitle: Template\n---\n\n# Content\n"
        current = "---\ntitle: My Custom Title\nauthor: John Doe\n---\n\n# Content\n"
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Frontmatter changes should be detected
        assert len(customizations) >= 1
    
    def test_multiple_sections_with_different_confidence(self):
        """Test multiple sections with varying confidence levels."""
        template = """# Section 1
{placeholder}

# Section 2
Some existing content

# Section 3
{another placeholder}
"""
        current = """# Section 1
Substantial custom content with many details and explanations

# Section 2
Some existing content with minor edit

# Section 3
Short
"""
        
        detector = CustomizationDetector(template)
        customizations = detector.detect_customizations(current)
        
        # Should have multiple customizations with different confidence levels
        assert len(customizations) >= 2
        confidences = [c.confidence for c in customizations]
        # Should have variation in confidence scores
        assert max(confidences) - min(confidences) > 0.1
