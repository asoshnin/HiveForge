---
inclusion: always
priority: 1
description: "Core problem, users, success metrics. Never changes without scope adjustment."
---

# Project Vision: HiveForge

## Elevator Pitch
HiveForge is the operating system for agentic coding — a CLI tool and KIRO IDE Power that replaces chaotic "vibe coding" with systematic, structured engineering by scaffolding a "Virtual Company" directly inside your repository.

## Problem Statement
AI coding tools excel at rapid prototyping but fundamentally fail at scale due to "context amnesia" and a lack of strict architectural boundaries. Agents forget past decisions across sessions, hallucinate requirements, and generate unmaintainable spaghetti code full of abstraction leaks and circular dependencies — saddling human developers with compounding technical debt.

## Solution Overview
HiveForge solves this through three core pillars:

1. **Truth Hierarchy** — Locks project vision, architecture, and coding conventions into immutable Steering Files. AI agents cannot write code until they validate against these rules, physically preventing hallucinations and architectural drift.
2. **Persistent Memory** — A living `swarm_state.md` file tracks every decision, task, and technical debt item across any duration of development, eliminating cross-session context amnesia.
3. **Role-Based Agent Sandboxing** — Deploys specialized agents (Orchestrator, Builders, Red Team) with hard-coded read/write permissions that prevent cross-domain abstraction leaks.

Additionally, the **Steering Assistant** automatically analyzes existing codebases or parses artifacts to generate and maintain documentation, with a **Discrepancy Analysis** workflow to resolve gaps between intended architecture and actual implementation.

## Target Users
1. **Primary:** Developers using KIRO Methodology v05 who need to scaffold new projects or generate steering files for existing projects.
2. **Secondary:** Development teams adopting KIRO methodology, technical leads setting up project documentation standards, and open-source contributors to HiveForge itself.

## Success Metrics
- **North Star Metric:** Number of projects successfully using HiveForge steering files in active development
- **Target:** 80% of generated steering files pass validation without manual edits by Q3 2026

## Non-Goals (What We Explicitly Don't Do)
- Not a general-purpose AI coding assistant or chat interface
- Not a replacement for version control (Git) or project management tools
- Does not execute code or deploy applications
- Does not manage secrets or credentials

## Constraints & Assumptions
- Requires Python 3.11+ runtime environment
- LLM integration is optional — tool must work fully without external API keys using local analysis
- Assumes projects follow a standard directory structure with source code and documentation
- Steering files are project-specific and not shared across repositories

## Timeline
- **MVP:** Released (CLI tool with steering init/update/validate)
- **V1.0:** Q2 2026 (full autonomous generation with confidence scoring)
- **Scale:** Q4 2026 (multi-project support, team collaboration features)
