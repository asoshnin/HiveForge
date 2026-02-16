"""
Tests for markdown parser.

This module tests the markdown parsing functionality to ensure it correctly
extracts content, preserves code blocks and Mermaid diagrams, and handles
multi-language content.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.hiveforge.steering.parsers.markdown import (
    parse_markdown,
    extract_headers,
    extract_code_blocks,
)
from src.hiveforge.steering.models import ParsedDocument


class TestParseMarkdown:
    """Tests for parse_markdown function."""
    
    def test_parse_simple_markdown(self, tmp_path):
        """Should parse a simple markdown file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Hello World\n\nThis is a test.", encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert isinstance(result, ParsedDocument)
        assert result.file_path == md_file
        assert "# Hello World" in result.content
        assert "This is a test" in result.content
        assert len(result.parse_errors) == 0
    
    def test_parse_markdown_with_frontmatter(self, tmp_path):
        """Should extract frontmatter metadata."""
        md_file = tmp_path / "test.md"
        content = """---
title: Test Document
author: Test Author
version: 1.0
---

# Content

This is the main content.
"""
        md_file.write_text(content, encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert result.metadata.get('title') == 'Test Document'
        assert result.metadata.get('author') == 'Test Author'
        assert result.metadata.get('version') == '1.0'
        assert '---' not in result.content  # Frontmatter removed from content
        assert '# Content' in result.content
    
    def test_parse_markdown_with_code_blocks(self, tmp_path):
        """Should preserve code blocks with language tags."""
        md_file = tmp_path / "test.md"
        content = """# Code Example

Here's some Python code:

```python
def hello():
    print("Hello, World!")
```

And some JavaScript:

```javascript
function hello() {
    console.log("Hello, World!");
}
```
"""
        md_file.write_text(content, encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert '```python' in result.content
        assert 'def hello():' in result.content
        assert '```javascript' in result.content
        assert 'function hello()' in result.content
        assert len(result.parse_errors) == 0
    
    def test_parse_markdown_with_mermaid_diagram(self, tmp_path):
        """Should preserve Mermaid diagrams."""
        md_file = tmp_path / "test.md"
        content = """# Architecture

```mermaid
graph TD
    A[Client] --> B[Server]
    B --> C[Database]
```

This is the architecture diagram.
"""
        md_file.write_text(content, encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert '```mermaid' in result.content
        assert 'graph TD' in result.content
        assert 'A[Client] --> B[Server]' in result.content
        assert len(result.parse_errors) == 0
    
    def test_parse_markdown_utf8_content(self, tmp_path):
        """Should handle multi-language UTF-8 content."""
        md_file = tmp_path / "test.md"
        content = """# Multilingual Content

## English
Hello World

## Russian (Cyrillic)
Привет мир

## Chinese
你好世界

## Japanese
こんにちは世界

## Emoji
🚀 🎉 ✨
"""
        md_file.write_text(content, encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert 'Hello World' in result.content
        assert 'Привет мир' in result.content
        assert '你好世界' in result.content
        assert 'こんにちは世界' in result.content
        assert '🚀' in result.content
        assert len(result.parse_errors) == 0
    
    def test_parse_markdown_file_not_found(self, tmp_path):
        """Should raise FileNotFoundError for missing file."""
        md_file = tmp_path / "nonexistent.md"
        
        with pytest.raises(FileNotFoundError):
            parse_markdown(md_file)
    
    def test_parse_markdown_stores_file_metadata(self, tmp_path):
        """Should store file metadata."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test", encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert 'file_size' in result.metadata
        assert 'file_name' in result.metadata
        assert result.metadata['file_name'] == 'test.md'
        assert result.metadata['file_size'] > 0
    
    def test_parse_markdown_without_frontmatter(self, tmp_path):
        """Should handle markdown without frontmatter."""
        md_file = tmp_path / "test.md"
        content = "# No Frontmatter\n\nJust content."
        md_file.write_text(content, encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert result.content == content
        assert 'title' not in result.metadata
        assert 'file_name' in result.metadata  # File metadata still present
    
    def test_parse_markdown_empty_file(self, tmp_path):
        """Should handle empty markdown file."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("", encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert result.content == ""
        assert len(result.parse_errors) == 0
    
    def test_parse_markdown_with_tables(self, tmp_path):
        """Should preserve markdown tables."""
        md_file = tmp_path / "test.md"
        content = """# Table Example

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
"""
        md_file.write_text(content, encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert '| Column 1 | Column 2 | Column 3 |' in result.content
        assert '|----------|----------|----------|' in result.content
        assert 'Value 1' in result.content
    
    def test_parse_markdown_with_nested_code_blocks(self, tmp_path):
        """Should handle multiple code blocks in sequence."""
        md_file = tmp_path / "test.md"
        content = """# Multiple Code Blocks

First block:
```python
x = 1
```

Second block:
```javascript
let y = 2;
```

Third block:
```bash
echo "hello"
```
"""
        md_file.write_text(content, encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        assert '```python' in result.content
        assert '```javascript' in result.content
        assert '```bash' in result.content
        assert 'x = 1' in result.content
        assert 'let y = 2;' in result.content
        assert 'echo "hello"' in result.content


class TestExtractHeaders:
    """Tests for extract_headers function."""
    
    def test_extract_single_header(self):
        """Should extract a single header."""
        content = "# Main Title\n\nSome content."
        headers = extract_headers(content)
        
        assert len(headers) == 1
        assert headers[0]['level'] == 1
        assert headers[0]['text'] == 'Main Title'
    
    def test_extract_multiple_headers(self):
        """Should extract multiple headers at different levels."""
        content = """# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6
"""
        headers = extract_headers(content)
        
        assert len(headers) == 6
        assert headers[0]['level'] == 1
        assert headers[1]['level'] == 2
        assert headers[2]['level'] == 3
        assert headers[3]['level'] == 4
        assert headers[4]['level'] == 5
        assert headers[5]['level'] == 6
    
    def test_extract_headers_with_content(self):
        """Should extract headers from content with text."""
        content = """# Introduction

This is some text.

## Section 1

More text here.

### Subsection 1.1

Even more text.
"""
        headers = extract_headers(content)
        
        assert len(headers) == 3
        assert headers[0]['text'] == 'Introduction'
        assert headers[1]['text'] == 'Section 1'
        assert headers[2]['text'] == 'Subsection 1.1'
    
    def test_extract_headers_empty_content(self):
        """Should return empty list for content without headers."""
        content = "Just plain text without headers."
        headers = extract_headers(content)
        
        assert len(headers) == 0


class TestExtractCodeBlocks:
    """Tests for extract_code_blocks function."""
    
    def test_extract_single_code_block(self):
        """Should extract a single code block."""
        content = """# Example

```python
def hello():
    print("Hello")
```
"""
        blocks = extract_code_blocks(content)
        
        assert len(blocks) == 1
        assert blocks[0]['language'] == 'python'
        assert 'def hello():' in blocks[0]['code']
    
    def test_extract_multiple_code_blocks(self):
        """Should extract multiple code blocks."""
        content = """# Examples

```python
x = 1
```

```javascript
let y = 2;
```

```bash
echo "test"
```
"""
        blocks = extract_code_blocks(content)
        
        assert len(blocks) == 3
        assert blocks[0]['language'] == 'python'
        assert blocks[1]['language'] == 'javascript'
        assert blocks[2]['language'] == 'bash'
    
    def test_extract_code_block_without_language(self):
        """Should handle code blocks without language specification."""
        content = """# Example

```
plain code block
```
"""
        blocks = extract_code_blocks(content)
        
        assert len(blocks) == 1
        assert blocks[0]['language'] == 'text'
        assert 'plain code block' in blocks[0]['code']
    
    def test_extract_mermaid_diagram(self):
        """Should extract Mermaid diagrams as code blocks."""
        content = """# Diagram

```mermaid
graph TD
    A --> B
```
"""
        blocks = extract_code_blocks(content)
        
        assert len(blocks) == 1
        assert blocks[0]['language'] == 'mermaid'
        assert 'graph TD' in blocks[0]['code']
    
    def test_extract_code_blocks_empty_content(self):
        """Should return empty list for content without code blocks."""
        content = "Just plain text without code blocks."
        blocks = extract_code_blocks(content)
        
        assert len(blocks) == 0
    
    def test_extract_code_block_with_multiline_content(self):
        """Should preserve multiline code in code blocks."""
        content = """# Example

```python
def complex_function():
    x = 1
    y = 2
    z = x + y
    return z
```
"""
        blocks = extract_code_blocks(content)
        
        assert len(blocks) == 1
        code = blocks[0]['code']
        assert 'def complex_function():' in code
        assert '    x = 1' in code
        assert '    return z' in code


class TestMarkdownParserIntegration:
    """Integration tests for markdown parser."""
    
    def test_parse_real_world_document(self, tmp_path):
        """Should parse a realistic markdown document."""
        md_file = tmp_path / "architecture.md"
        content = """---
title: System Architecture
version: 1.0
---

# Architecture Overview

## System Diagram

```mermaid
graph TD
    User -->|HTTP| API_Gateway
    API_Gateway -->|RPC| App_Server
    App_Server -->|Query| Database
```

## Components

### API Gateway
- **Responsibility:** Route requests
- **Interface:** REST API
- **Dependencies:** None

### App Server
- **Responsibility:** Business logic
- **Interface:** RPC
- **Dependencies:** Database, Cache

## Code Example

```python
class APIGateway:
    def route_request(self, request):
        return self.app_server.handle(request)
```

## Data Flow

1. User sends HTTP request
2. API Gateway routes to App Server
3. App Server queries Database
4. Response flows back to User
"""
        md_file.write_text(content, encoding='utf-8')
        
        result = parse_markdown(md_file)
        
        # Check frontmatter extraction
        assert result.metadata['title'] == 'System Architecture'
        assert result.metadata['version'] == '1.0'
        
        # Check content preservation
        assert '# Architecture Overview' in result.content
        assert '## System Diagram' in result.content
        
        # Check Mermaid diagram preservation
        assert '```mermaid' in result.content
        assert 'graph TD' in result.content
        
        # Check code block preservation
        assert '```python' in result.content
        assert 'class APIGateway:' in result.content
        
        # Check no parse errors
        assert len(result.parse_errors) == 0
        
        # Extract and verify headers
        headers = extract_headers(result.content)
        assert len(headers) > 0
        assert any(h['text'] == 'Architecture Overview' for h in headers)
        
        # Extract and verify code blocks
        blocks = extract_code_blocks(result.content)
        assert len(blocks) == 2  # mermaid + python
        assert any(b['language'] == 'mermaid' for b in blocks)
        assert any(b['language'] == 'python' for b in blocks)
