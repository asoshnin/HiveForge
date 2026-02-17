# HiveForge Steering Power

KIRO Power for AI-powered steering file generation and maintenance.

## Overview

The HiveForge Steering Power provides intelligent steering file management through KIRO's Power framework. It automatically activates when you mention keywords like "steering", "documentation", or "onboarding" and provides tools for creating, updating, and validating project steering files.

## Features

- **Automatic Discovery**: Scans your project for existing documentation
- **AI-Powered Generation**: Creates comprehensive steering files using LLM
- **Smart Updates**: Preserves customizations while updating content
- **Validation**: Ensures steering files are complete and consistent
- **Reset Capability**: Restore files to default templates

## Installation

```bash
# Install via uvx (recommended)
uvx hiveforge-steering-mcp@latest

# Or install via pip
pip install hiveforge-steering-mcp
```

## Usage

The Power activates automatically in KIRO when you mention relevant keywords:

```
User: "I need to create steering files for my project"
→ Power activates automatically
→ Agent uses tools to help you
```

## Available Tools

1. **init_steering**: Initialize steering files from scratch
2. **update_steering**: Update existing steering files
3. **validate_steering**: Validate steering file quality
4. **reset_steering**: Reset files to default templates
5. **discover_docs**: Discover existing project documentation

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/yourusername/hiveforge-steering-mcp.git
cd hiveforge-steering-mcp

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Project Structure

```
hiveforge-power/
├── mcp-server/          # MCP server implementation
│   ├── server.py       # FastMCP server
│   └── tools/          # MCP tool implementations
├── tests/              # Test suite
├── pyproject.toml      # Package configuration
├── package.json        # Power metadata
└── README.md           # This file
```

## Architecture

This Power uses a shared backend architecture:

```
KIRO Orchestrator
    ↓
Power (MCP Tools)
    ↓
Shared Backend Adapters
    ↓
v02 Workflows
```

Both the CLI and Power use the same shared backend, ensuring identical behavior and output.

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## Support

- Documentation: https://docs.hiveforge.dev/steering
- Issues: https://github.com/yourusername/hiveforge-steering-mcp/issues
- Discussions: https://github.com/yourusername/hiveforge-steering-mcp/discussions
