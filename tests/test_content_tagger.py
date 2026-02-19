"""
Tests for Content Tagger.

This module tests the content tagging system for steering file generation,
including inferred section tagging, metadata headers, and low confidence warnings.
"""

import pytest
from datetime import datetime
from src.hiveforge.steering.content_tagger import ContentTagger
from src.hiveforge.steering.confidence import ConfidenceScore


class TestContentTagger:
    """Tests for ContentTagger class."""
    
    def test_tag_inferred_sections_single_section(self):
        """Test tagging a single inferred section."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with managing documentation.

## Solution
We provide automated tools.
"""
        
        tagged = tagger.tag_inferred_sections(content, ["Problem Statement"])
        
        assert "<!-- INFERRED: Please verify this section -->" in tagged
        assert "<!-- END INFERRED -->" in tagged
        
        # Verify the tag is placed correctly after the header
        lines = tagged.split('\n')
        problem_idx = next(i for i, line in enumerate(lines) if "## Problem Statement" in line)
        assert "<!-- INFERRED" in lines[problem_idx + 1]
    
    def test_tag_inferred_sections_multiple_sections(self):
        """Test tagging multiple inferred sections."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with managing documentation.

## Solution
We provide automated tools.

## Target Users
Developers and teams.
"""
        
        tagged = tagger.tag_inferred_sections(
            content,
            ["Problem Statement", "Target Users"]
        )
        
        # Should have two pairs of tags
        assert tagged.count("<!-- INFERRED: Please verify this section -->") == 2
        assert tagged.count("<!-- END INFERRED -->") == 2
    
    def test_tag_inferred_sections_no_sections(self):
        """Test tagging with empty inferred sections list."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with managing documentation.
"""
        
        tagged = tagger.tag_inferred_sections(content, [])
        
        # Content should be unchanged
        assert tagged == content
        assert "<!-- INFERRED" not in tagged
    
    def test_tag_inferred_sections_nested_headers(self):
        """Test tagging with nested header levels."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with managing documentation.

### Specific Pain Points
- Point 1
- Point 2

## Solution
We provide automated tools.
"""
        
        tagged = tagger.tag_inferred_sections(content, ["Problem Statement"])
        
        # Should close the inferred section before the Solution header
        lines = tagged.split('\n')
        solution_idx = next(i for i, line in enumerate(lines) if "## Solution" in line)
        
        # Find the END INFERRED tag before Solution
        end_tag_found = False
        for i in range(solution_idx):
            if "<!-- END INFERRED -->" in lines[i]:
                end_tag_found = True
                break
        
        assert end_tag_found
    
    def test_tag_inferred_sections_preserves_formatting(self):
        """Test that tagging preserves markdown formatting."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with **bold text** and *italic text*.

- List item 1
- List item 2

```python
code_block()
```

## Solution
We provide automated tools.
"""
        
        tagged = tagger.tag_inferred_sections(content, ["Problem Statement"])
        
        # Verify formatting is preserved
        assert "**bold text**" in tagged
        assert "*italic text*" in tagged
        assert "- List item 1" in tagged
        assert "```python" in tagged
        assert "code_block()" in tagged
    
    def test_tag_inferred_sections_special_characters(self):
        """Test tagging sections with special markdown characters (RED TEAM EDGE CASE)."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement (Critical)
Users struggle with managing documentation.

## Solution & Approach
We provide automated tools.
"""
        
        # Section names with special characters
        tagged = tagger.tag_inferred_sections(
            content,
            ["Problem Statement (Critical)", "Solution & Approach"]
        )
        
        # Should handle special characters correctly
        assert tagged.count("<!-- INFERRED: Please verify this section -->") == 2
        assert tagged.count("<!-- END INFERRED -->") == 2
    
    def test_tag_inferred_sections_empty_content(self):
        """Test tagging empty content (edge case)."""
        tagger = ContentTagger()
        
        content = ""
        
        tagged = tagger.tag_inferred_sections(content, ["Problem Statement"])
        
        # Should handle empty content gracefully
        assert tagged == ""
    
    def test_tag_inferred_sections_very_long_section_name(self):
        """Test tagging with very long section names (RED TEAM EDGE CASE)."""
        tagger = ContentTagger()
        
        long_section = "This is a Very Long Section Name That Might Cause Issues With Processing"
        content = f"""# Project Vision

## {long_section}
Content here.

## Solution
More content.
"""
        
        tagged = tagger.tag_inferred_sections(content, [long_section])
        
        assert "<!-- INFERRED: Please verify this section -->" in tagged
        assert "<!-- END INFERRED -->" in tagged
    
    def test_add_metadata_header_basic(self):
        """Test adding basic metadata header."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Content here.
"""
        
        confidence = ConfidenceScore(
            overall=0.65,
            level="medium",
            sources={"documents": 0.5, "code_analysis": 0.1, "inferred": 0.05},
            inferred_sections=["Problem Statement"]
        )
        
        metadata = {
            "source_documents": 3,
            "code_analysis": True
        }
        
        tagged = tagger.add_metadata_header(content, confidence, metadata)
        
        # Verify frontmatter is present
        assert tagged.startswith("---\n")
        assert "generated_by: hiveforge v2.2.0" in tagged
        assert "source_documents: 3" in tagged
        assert "code_analysis: true" in tagged
        assert "confidence:" in tagged
        assert "overall: 0.65" in tagged
        assert "level: medium" in tagged
        assert "inferred_sections:" in tagged
        assert '"Problem Statement"' in tagged
    
    def test_add_metadata_header_with_source_path(self):
        """Test adding metadata header with source_docs_path."""
        tagger = ContentTagger()
        
        content = "# Content"
        
        confidence = ConfidenceScore(0.8, "high", {}, [])
        
        metadata = {
            "source_documents": 5,
            "source_docs_path": "_DEVELOPMENT",
            "code_analysis": True
        }
        
        tagged = tagger.add_metadata_header(content, confidence, metadata)
        
        assert "source_docs_path: _DEVELOPMENT" in tagged
    
    def test_add_metadata_header_no_inferred_sections(self):
        """Test metadata header when no sections are inferred."""
        tagger = ContentTagger()
        
        content = "# Content"
        
        confidence = ConfidenceScore(
            overall=1.0,
            level="high",
            sources={"documents": 1.0},
            inferred_sections=[]
        )
        
        metadata = {"source_documents": 5, "code_analysis": False}
        
        tagged = tagger.add_metadata_header(content, confidence, metadata)
        
        # Should not have inferred_sections field if empty
        assert "inferred_sections:" not in tagged or "inferred_sections:\n---" in tagged
    
    def test_add_metadata_header_removes_existing_frontmatter(self):
        """Test that existing frontmatter is replaced."""
        tagger = ContentTagger()
        
        content = """---
old_metadata: value
---

# Content
"""
        
        confidence = ConfidenceScore(0.7, "medium", {}, [])
        metadata = {"source_documents": 2, "code_analysis": True}
        
        tagged = tagger.add_metadata_header(content, confidence, metadata)
        
        # Should not contain old metadata
        assert "old_metadata: value" not in tagged
        # Should contain new metadata
        assert "generated_by: hiveforge v2.2.0" in tagged
    
    def test_add_metadata_header_escapes_special_characters(self):
        """Test that section names with special characters are escaped (RED TEAM EDGE CASE)."""
        tagger = ContentTagger()
        
        content = "# Content"
        
        confidence = ConfidenceScore(
            overall=0.5,
            level="medium",
            sources={},
            inferred_sections=['Section with "quotes"', "Section with 'apostrophe'"]
        )
        
        metadata = {"source_documents": 1, "code_analysis": True}
        
        tagged = tagger.add_metadata_header(content, confidence, metadata)
        
        # Should escape quotes in section names
        assert 'Section with \\"quotes\\"' in tagged or '"Section with \\"quotes\\""' in tagged
    
    def test_add_low_confidence_warning(self):
        """Test adding low confidence warning."""
        tagger = ContentTagger()
        
        content = """---
generated_by: hiveforge v2.2.0
---

# Project Vision
"""
        
        warned = tagger.add_low_confidence_warning(content)
        
        assert "⚠️ **LOW CONFIDENCE**" in warned
        assert "limited source material" in warned
        assert "Please review and update" in warned
        
        # Warning should be after frontmatter
        lines = warned.split('\n')
        warning_idx = next(i for i, line in enumerate(lines) if "⚠️" in line)
        frontmatter_end_idx = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
        
        assert warning_idx > frontmatter_end_idx
    
    def test_add_low_confidence_warning_no_frontmatter(self):
        """Test adding warning when no frontmatter exists."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Content here.
"""
        
        warned = tagger.add_low_confidence_warning(content)
        
        assert "⚠️ **LOW CONFIDENCE**" in warned
        # Warning should be at the beginning
        assert warned.startswith("\n> ⚠️")
    
    def test_tag_content_high_confidence(self):
        """Test full tagging workflow with high confidence."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with managing documentation.

## Solution
We provide automated tools.
"""
        
        confidence = ConfidenceScore(
            overall=0.85,
            level="high",
            sources={"documents": 0.8, "code_analysis": 0.05},
            inferred_sections=[]
        )
        
        metadata = {"source_documents": 5, "code_analysis": True}
        
        tagged = tagger.tag_content(content, confidence, metadata)
        
        # Should have frontmatter
        assert tagged.startswith("---\n")
        assert "confidence:" in tagged
        assert "level: high" in tagged
        
        # Should NOT have low confidence warning
        assert "⚠️ **LOW CONFIDENCE**" not in tagged
        
        # Should NOT have inferred tags (no inferred sections)
        assert "<!-- INFERRED" not in tagged
    
    def test_tag_content_low_confidence(self):
        """Test full tagging workflow with low confidence."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with managing documentation.

## Solution
We provide automated tools.
"""
        
        confidence = ConfidenceScore(
            overall=0.3,
            level="low",
            sources={"inferred": 0.3},
            inferred_sections=["Problem Statement", "Solution"]
        )
        
        metadata = {"source_documents": 0, "code_analysis": True}
        
        tagged = tagger.tag_content(content, confidence, metadata)
        
        # Should have frontmatter
        assert tagged.startswith("---\n")
        assert "level: low" in tagged
        
        # Should have low confidence warning
        assert "⚠️ **LOW CONFIDENCE**" in tagged
        
        # Should have inferred tags
        assert "<!-- INFERRED: Please verify this section -->" in tagged
        assert "<!-- END INFERRED -->" in tagged
        assert tagged.count("<!-- INFERRED") == 2
    
    def test_tag_content_medium_confidence(self):
        """Test full tagging workflow with medium confidence."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with managing documentation.
"""
        
        confidence = ConfidenceScore(
            overall=0.6,
            level="medium",
            sources={"documents": 0.4, "code_analysis": 0.15, "inferred": 0.05},
            inferred_sections=["Problem Statement"]
        )
        
        metadata = {"source_documents": 2, "code_analysis": True}
        
        tagged = tagger.tag_content(content, confidence, metadata)
        
        # Should have frontmatter
        assert "level: medium" in tagged
        
        # Should NOT have low confidence warning (only for "low" level)
        assert "⚠️ **LOW CONFIDENCE**" not in tagged
        
        # Should have inferred tags for Problem Statement
        assert "<!-- INFERRED: Please verify this section -->" in tagged
    
    def test_tag_content_preserves_structure(self):
        """Test that full tagging preserves markdown structure."""
        tagger = ContentTagger()
        
        content = """# Project Vision

## Problem Statement
Users struggle with **bold** and *italic*.

- List item 1
- List item 2

## Solution
We provide tools.
"""
        
        confidence = ConfidenceScore(
            overall=0.5,
            level="medium",
            sources={},
            inferred_sections=["Problem Statement"]
        )
        
        metadata = {"source_documents": 1, "code_analysis": True}
        
        tagged = tagger.tag_content(content, confidence, metadata)
        
        # Verify structure is preserved
        assert "**bold**" in tagged
        assert "*italic*" in tagged
        assert "- List item 1" in tagged
        assert "- List item 2" in tagged
        assert "## Problem Statement" in tagged
        assert "## Solution" in tagged
    
    def test_remove_existing_frontmatter(self):
        """Test internal method for removing frontmatter."""
        tagger = ContentTagger()
        
        content = """---
old: metadata
---

# Content
"""
        
        result = tagger._remove_existing_frontmatter(content)
        
        assert "---" not in result
        assert "old: metadata" not in result
        assert "# Content" in result
    
    def test_remove_existing_frontmatter_no_frontmatter(self):
        """Test removing frontmatter when none exists."""
        tagger = ContentTagger()
        
        content = """# Content

No frontmatter here.
"""
        
        result = tagger._remove_existing_frontmatter(content)
        
        # Should return unchanged
        assert result == content
    
    def test_remove_existing_frontmatter_incomplete(self):
        """Test removing incomplete frontmatter (no closing ---)."""
        tagger = ContentTagger()
        
        content = """---
incomplete: frontmatter

# Content
"""
        
        result = tagger._remove_existing_frontmatter(content)
        
        # Should return original if frontmatter is incomplete
        assert result == content
    
    def test_tag_content_empty_content(self):
        """Test tagging empty content (edge case)."""
        tagger = ContentTagger()
        
        content = ""
        
        confidence = ConfidenceScore(0.5, "medium", {}, [])
        metadata = {"source_documents": 0, "code_analysis": False}
        
        tagged = tagger.tag_content(content, confidence, metadata)
        
        # Should still add frontmatter
        assert tagged.startswith("---\n")
        assert "generated_by: hiveforge v2.2.0" in tagged
    
    def test_metadata_header_timestamp_format(self):
        """Test that timestamp is in correct ISO format."""
        tagger = ContentTagger()
        
        content = "# Content"
        confidence = ConfidenceScore(0.7, "medium", {}, [])
        metadata = {"source_documents": 1, "code_analysis": True}
        
        tagged = tagger.add_metadata_header(content, confidence, metadata)
        
        # Should have ISO format timestamp
        assert "generated_at:" in tagged
        lines = tagged.split('\n')
        timestamp_line = next(line for line in lines if "generated_at:" in line)
        
        # Extract timestamp
        timestamp_str = timestamp_line.split("generated_at:")[1].strip()
        
        # Verify it can be parsed as ISO format (with or without Z suffix)
        try:
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp '{timestamp_str}' is not in valid ISO format")
