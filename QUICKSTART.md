# 🚀 Quick Start Guide

Get started with **kiro-init** in 5 minutes! This guide walks you through creating your first KIRO v05 project.

---

## Prerequisites

- Python 3.11 or higher
- pip or poetry package manager
- Basic familiarity with command line

---

## Step 1: Install kiro-init

### Option A: Using pip (Recommended)

```bash
pip install kiro-init
```

### Option B: Using poetry

```bash
poetry add kiro-init
```

### Verify Installation

```bash
kiro-init --help
```

You should see:

```
Usage: kiro-init [OPTIONS]

Initialize KIRO v05 project (7 agents, 8 steering files, swarm_state.md)

Options:
  -n, --project-name TEXT  Project name (kebab-case)
  -f, --force              Overwrite .kiro/ if exists
  --help                   Show this message and exit.
```

---

## Step 2: Create Your First Project

### Navigate to Your Workspace

```bash
cd ~/projects
mkdir my-awesome-app
cd my-awesome-app
```

### Initialize the Project

```bash
kiro-init --project-name my-awesome-app
```

**Output:**

```
✅ KIRO v05 'my-awesome-app' initialized!
📁 .kiro/agents/ (7), .kiro/steering/ (8), swarm_state.md

🚀 Next: Reload Kiro IDE → Fill swarm_state.md → Act as Orchestrator
```

---

## Step 3: Explore the Generated Structure

```bash
tree -L 3
```

**You'll see:**

```
my-awesome-app/
├── .kiro/
│   ├── agents/
│   │   ├── orchestrator.md
│   │   ├── data_architect.md
│   │   ├── backend_engineer.md
│   │   ├── frontend_engineer.md
│   │   ├── qa_engineer.md
│   │   ├── devops_engineer.md
│   │   └── red_team.md
│   └── steering/
│       ├── project-vision.md
│       ├── tech-stack.md
│       ├── conventions.md
│       ├── architecture.md
│       ├── db-standards.md
│       ├── api-standards.md
│       ├── ui-standards.md
│       └── qa-standards.md
├── .swarm/
│   ├── plan/
│   └── audit_logs/
└── swarm_state.md
```

---

## Step 4: Customize Your Project

### 4.1 Fill in Swarm State

Open `swarm_state.md` and fill in the project details:

```markdown
## 1. Project Identity & Context

**Project Name:** my-awesome-app
**Created:** 2026-02-14T14:25:13.123456Z
**Last Updated:** 2026-02-14T14:25:13.123456Z

**Brief Description:**
A web application for managing tasks with AI-powered suggestions.

**Target Users:**
- Busy professionals
- Small teams (5-20 people)
- Remote workers

**Core Value Proposition:**
AI-assisted task management that learns from your workflow patterns.
```

### 4.2 Define Your Tech Stack

Edit `.kiro/steering/tech-stack.md`:

```markdown
# Tech Stack

## Backend
- **Framework:** FastAPI
- **Database:** PostgreSQL 15
- **ORM:** SQLAlchemy 2.0
- **Authentication:** JWT

## Frontend
- **Framework:** React 18 + TypeScript
- **Styling:** TailwindCSS
- **State Management:** Zustand

## DevOps
- **Hosting:** AWS (ECS + RDS)
- **CI/CD:** GitHub Actions
- **Monitoring:** Datadog
```

### 4.3 Set Conventions

Edit `.kiro/steering/conventions.md`:

```markdown
# Coding Conventions

## Naming
- **Files:** kebab-case (`user-service.ts`)
- **Classes:** PascalCase (`UserService`)
- **Functions:** camelCase (`getUserById`)
- **Constants:** SCREAMING_SNAKE_CASE (`MAX_RETRIES`)

## Git Commits
- Use conventional commits: `feat:`, `fix:`, `docs:`, etc.
- Keep commits atomic and focused
```

---

## Step 5: Start Working with Agents

### 5.1 Act as the Orchestrator

Open Kiro IDE and load the Orchestrator agent (`.kiro/agents/orchestrator.md`).

**Example Prompt:**

```
I need to build the user authentication system. Please delegate this task to the appropriate agents.
```

**Orchestrator Response:**

```
I'll delegate this to:
1. Data Architect - Design user/session tables
2. Backend Engineer - Implement JWT auth endpoints
3. QA Engineer - Write integration tests
4. Red Team - Review security implications

Creating delegation tree in swarm_state.md...
```

### 5.2 Switch to Specialized Agents

When the Orchestrator delegates, switch to the appropriate agent:

**Data Architect:**
```
Design the user authentication schema with password hashing and session management.
```

**Backend Engineer:**
```
Implement POST /auth/login and POST /auth/register endpoints using the schema from Data Architect.
```

---

## Step 6: Common Workflows

### Workflow 1: Adding a New Feature

```bash
# 1. Act as Orchestrator
"I want to add email notifications. Please plan the implementation."

# 2. Orchestrator delegates to:
#    - Data Architect (notification_queue table)
#    - Backend Engineer (email service)
#    - DevOps Engineer (SMTP configuration)

# 3. Switch agents and implement
# 4. Red Team reviews the implementation
```

### Workflow 2: Fixing a Bug

```bash
# 1. Act as QA Engineer
"I found a bug: users can't reset passwords. Investigate and fix."

# 2. QA Engineer analyzes and delegates to Backend Engineer
# 3. Backend Engineer fixes the issue
# 4. QA Engineer writes regression test
```

### Workflow 3: Regenerating Project

```bash
# If you need to reset agent definitions
kiro-init -n my-awesome-app --force

# This preserves swarm_state.md but resets agent templates
```

---

## Step 7: Best Practices

### ✅ Do's

- **Always start with Orchestrator** - Let it plan and delegate
- **Update swarm_state.md** - Keep it as the single source of truth
- **Use steering files** - Reference them for consistency
- **Let Red Team audit** - Catch issues early
- **Follow role boundaries** - Orchestrator plans, Engineers implement

### ❌ Don'ts

- **Don't skip Orchestrator** - Jumping straight to implementation causes chaos
- **Don't ignore toolsSettings** - They enforce important boundaries
- **Don't modify agent definitions** - Use `--force` to regenerate if needed
- **Don't forget to commit** - Version control your `.kiro/` and `swarm_state.md`

---

## Next Steps

### Learn More

- 📖 **[Architecture Guide](./docs/architecture.md)** - Understand how it works
- 🛠️ **[Development Guide](./docs/development.md)** - Contribute to kiro-init
- 🔍 **[Troubleshooting](./docs/troubleshooting.md)** - Common issues

### Join the Community

- 💬 **[Discord](https://discord.gg/your-invite)** - Chat with other users
- 🐛 **[GitHub Issues](https://github.com/asoshnin/HiveForge/issues)** - Report bugs
- 💡 **[Discussions](https://github.com/asoshnin/HiveForge/discussions)** - Share ideas

---

## Troubleshooting

### "Invalid project name" Error

**Problem:**
```bash
❌ Invalid: 'My Project'. Use kebab-case (e.g., 'my-project')
```

**Solution:**
Use lowercase letters, numbers, and hyphens only:
```bash
kiro-init -n my-project  # ✅ Correct
```

### ".kiro/ exists" Error

**Problem:**
```bash
❌ .kiro/ exists. Use --force to overwrite.
```

**Solution:**
Add the `--force` flag:
```bash
kiro-init -n my-project --force
```

### Command Not Found

**Problem:**
```bash
kiro-init: command not found
```

**Solution:**
Ensure kiro-init is installed and in your PATH:
```bash
pip install --user kiro-init
# or
poetry install
poetry shell
```

---

<div align="center">

**🎉 Congratulations! You've created your first KIRO v05 project!**

Need help? Check the [full documentation](./README.md) or [open an issue](https://github.com/asoshnin/HiveForge/issues).

</div>
