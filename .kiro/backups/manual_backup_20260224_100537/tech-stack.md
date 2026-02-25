---
inclusion: always
priority: 1
description: "Approved technologies and dependencies. Changes require architecture review."
---

# Technology Stack

## Core Technologies

### Backend
- **Language:** Python 3.11+
- **Runtime:** CPython
- **Package Manager:** Poetry
- **CLI Framework:** Typer (built on Click) — type-safe CLI with automatic help generation
- **MCP Integration:** FastMCP — Model Context Protocol server for KIRO IDE integration

### Frontend
- N/A — HiveForge is a CLI tool and MCP server with no frontend UI

### Database
- **Primary:** None — filesystem-based operation only
- **Cache:** None — in-memory only during execution
- **ORM/ODM:** None required

### Infrastructure
- **Container:** Docker (optional, for development environments)
- **Orchestration:** None required for CLI tool
- **Cloud:** None required — runs fully local

## Key Dependencies
| Purpose | Library | Version | Notes |
|---------|---------|---------|-------|
| CLI framework | typer | >=0.9 | Type-safe CLI with auto help |
| MCP server | fastmcp | latest | KIRO IDE integration |
| Testing | pytest | >=7.0 | Primary test runner |
| Coverage | pytest-cov | >=4.0 | Minimum 80% coverage |
| AST parsing | ast (stdlib) | built-in | Python code analysis |
| Path matching | pathspec | >=0.11 | .gitignore-style patterns |
| LLM (primary) | KIRO Native | — | ctx.sample() in MCP mode |
| LLM (fallback 1) | google-cloud-aiplatform | >=1.38 | Vertex AI integration |
| LLM (fallback 2) | openai | >=1.0 | OpenAI API fallback |
| PDF parsing | pypdf / pdfplumber | >=3.0 | Document ingestion |
| OCR | pytesseract | >=0.3 | Image document parsing |
| Diff display | colorama | >=0.4 | Colored terminal output |

## Rationale

**Minimalist approach:** Python 3.11+ with Poetry provides a lightweight, maintainable foundation. Typer enables intuitive CLI development with minimal boilerplate. FastMCP enables seamless KIRO IDE integration without external dependencies.

**LLM flexibility:** Provider abstraction with automatic fallback (KIRO Native → Vertex AI → OpenAI → `[INFERRED]` markers) ensures the tool works in any environment without mandatory external API configuration.

**Local-first:** All code analysis runs locally without LLM calls, reducing API costs and privacy concerns. The tool is fully functional without any LLM configured.

**Testing first:** 80% coverage requirement ensures reliability for a developer tool that other developers depend on.

**No database:** Filesystem-based operation eliminates infrastructure complexity while maintaining full functionality.

**Trade-offs:**
- Simplicity over features: No ORM, no web framework, no real-time sync — keeps the tool focused and maintainable
- Python-only initially: Limits deep AST analysis to Python projects, but enables rich code understanding
- Optional LLM: Graceful degradation with `[INFERRED]` markers means the tool works without external APIs, but with reduced output quality
