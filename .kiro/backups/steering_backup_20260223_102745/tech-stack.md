---
inclusion: always
priority: 1
description: "Approved technologies and dependencies. Changes require architecture review."
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** Python 3.11+
- **Framework:** Typer (CLI), FastMCP (MCP server)
- **Runtime:** CPython

### Frontend
- **Framework:** N/A (CLI tool, no frontend)
- **Language:** N/A
- **Styling:** N/A

### Database
- **Primary:** N/A (file-based storage)
- **Cache:** JSON files (.kiro/.cache/)
- **ORM/ODM:** N/A

### Infrastructure
- **Container:** Docker (planned for v3.0)
- **Orchestration:** N/A
- **Cloud:** N/A (local execution)

## Key Dependencies
| Purpose | Library | Version | Notes |
|---------|---------|---------|-------|
| CLI Framework | typer | 0.9+ | Type-safe CLI with auto-help generation |
| Testing | pytest | 7.4+ | 863 tests, 97% pass rate |
| Code Analysis | pathspec | 0.11+ | .gitignore pattern matching |
| PDF Parsing | PyPDF2 | 3.0+ | Extract text from PDF artifacts |
| Image OCR | pytesseract | 0.3+ | Extract text from images |
| LLM Integration | openai | 1.0+ | GPT-4 for steering assistant |
| MCP Server | fastmcp | 0.1+ | Model Context Protocol implementation |
| Dependency Management | poetry | 1.7+ | Deterministic builds |

## Rationale

**Why Python?**
- Excellent ecosystem for CLI tools (typer, click)
- Strong LLM integration libraries (openai, anthropic)
- Rich file parsing libraries (PyPDF2, pytesseract, markdown)
- Type hints for maintainability (Python 3.11+)

**Why Typer over Click/argparse?**
- Modern, type-safe API
- Automatic help generation from docstrings
- Built on Click (battle-tested)
- Excellent error messages

**Why Poetry over pip?**
- Deterministic builds (poetry.lock)
- Better dependency resolution
- Built-in virtual environment management
- Easy PyPI publishing

**Why FastMCP?**
- Lightweight MCP server implementation
- Easy integration with KIRO IDE
- Supports both CLI and Power interfaces

**Trade-offs:**
- Python 3.11+ requirement limits compatibility with older systems
- No frontend means no visual configuration UI
- File-based caching is simple but not suitable for concurrent access
- Local execution only (no cloud/distributed processing)