---
inclusion: always
priority: 1
description: "Core problem,users, success metrics. Never changes without scope adjustment."
---

# Project Vision: HiveForge

## Elevator Pitch
HiveForge is a CLI scaffolding tool and AI-powered Steering Assistant that generates KIRO Methodology v05 projects with multi-agent architecture and maintains comprehensive steering files throughout the project lifecycle.

## Problem Statement
Development teams struggle with:
- Manual creation of multi-agent project structures
- Inconsistent documentation across projects
- Documentation drift as projects evolve
- Time-consuming setup of agent definitions and steering files
- Knowledge loss when team members change

## Solution Overview
HiveForge provides:
1. **CLI Scaffolding Tool**: Generates complete KIRO v05 project structure (7 agents, 8 steering files, swarm state)
2. **Steering Assistant**: AI-powered tool that analyzes codebases, parses artifacts, and maintains steering files
3. **Shared Backend**: Unified implementation for both CLI and MCP Power interfaces
4. **Confidence Scoring**: Tracks which content is from source documents vs. inferred
5. **Automatic Updates**: Keeps steering files in sync with code changes while preserving customizations

## Target Users
1. **Primary:** Development teams using KIRO IDE for multi-agent development
2. **Secondary:** Solo developers wanting structured project documentation and AI-assisted maintenance

## Success Metrics
- **North Star Metric:** Number of active projects using HiveForge steering files
- **Target:** 100 active projects by Q3 2026

## Non-Goals (What We Explicitly Don't Do)
- IDE-specific features (remains IDE-agnostic)
- Code generation (focuses on structure and documentation)
- Project management (no task tracking or sprint planning)
- Real-time collaboration features

## Constraints & Assumptions
- **Business constraint:** Must remain free and open-source (MIT license)
- **Technical constraint:** Python 3.11+ required for modern type hints and performance
- **Key assumption:** Teams value comprehensive documentation and are willing to maintain steering files

## Timeline
- **MVP:** Completed (v1.0.0 - CLI scaffolding)
- **V2.0:** Completed (Steering Assistant with code analysis)
- **V2.2.0:** Completed (Custom source paths, confidence scoring, dry-run mode)
- **V3.0:** Planned Q2 2026 (Custom templates, plugin system)