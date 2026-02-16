# 🚀 Quick Start Guide

Get started with **hiveforge** in 5 minutes! This guide walks you through creating your first KIRO v05 project.

---

## Prerequisites

- Python 3.11 or higher
- Git (to clone the repository)
- pip package manager
- Basic familiarity with command line

---

## Step 1: Install hiveforge

### Clone the Repository

Since HiveForge is not yet published to PyPI, you'll need to install it from source:

```bash
# Clone the repository
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge
```

### Create a Virtual Environment (Recommended)

Using a virtual environment keeps your project dependencies isolated and prevents conflicts.

```bash
# macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt):
python -m venv venv
venv\Scripts\activate.bat

# Windows (PowerShell):
python -m venv venv
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### Install hiveforge

```bash
# Install in editable mode (recommended - changes reflect immediately)
pip install -e .

# OR use Poetry
poetry install
poetry shell
```

### Verify Installation

```bash
hiveforge --help
```

You should see:

```
Usage: hiveforge [OPTIONS]

Initialize KIRO v05 project (7 agents, 8 steering files, swarm_state.md)

Options:
  -n, --project-name TEXT  Project name (kebab-case)
  -f, --force              Overwrite .kiro/ if exists
  --help                   Show this message and exit.
```

**Note:** Remember to activate your virtual environment each time you open a new terminal session:

```bash
# macOS/Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

---

## Step 2: Create Your First Project

### Navigate to Your Workspace

Create a new folder for your project. This can be anywhere on your system (Desktop, Documents, ~/projects, etc.) - it does NOT need to be inside the HiveForge installation directory.

```bash
# Create project folder anywhere you like
cd ~/projects
mkdir my-awesome-app
cd my-awesome-app
```

**Important Notes:**
- The folder name (`my-awesome-app`) doesn't have to match the project name you pass to `-n`
- HiveForge creates files in the current directory where you run the command
- Each project is completely independent

### Initialize the Project

```bash
# The -n flag is just a label used in swarm_state.md
hiveforge --project-name my-awesome-app

# Or use a different name than the folder:
hiveforge -n awesome-task-manager
```

**Output:**

```
✅ KIRO v05 'my-awesome-app' initialized!
📁 .kiro/agents/ (7), .kiro/steering/ (8), swarm_state.md

🚀 Next: Reload Kiro IDE → Fill swarm_state.md → Act as Orchestrator
```

---

## Step 3: Open in Kiro IDE

Now open your project folder in Kiro IDE:

1. Open Kiro IDE
2. File → Open Folder
3. Select the `my-awesome-app` folder you just created
4. The `.kiro/` structure will be recognized automatically

---

## Step 4: Explore the Generated Structure

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

### Option A: Use Steering Assistant (Recommended)

The Steering Assistant can automatically analyze your project and generate comprehensive steering files.

#### For New Projects

```bash
# Generate steering files with interactive conversation
hiveforge steering init

# The assistant will ask questions about:
# - Project vision and goals
# - Target users
# - Technology choices
# - Development standards
```

#### For Existing Codebases

If you're adding KIRO to an existing project:

```bash
# Analyze existing code and generate steering files
hiveforge steering init --analyze-code

# The assistant will:
# 1. Detect languages, frameworks, and libraries
# 2. Infer architecture from directory structure
# 3. Extract coding conventions from actual code
# 4. Ask clarifying questions for missing info
# 5. Generate all 8 steering files
```

**Example interaction:**
```bash
$ hiveforge steering init --analyze-code

🔍 Analyzing codebase...
✓ Detected: Python 3.11, FastAPI, PostgreSQL
✓ Architecture: Monolithic web application

📋 I need some additional information:

1. What is the main problem this project solves?
   > Task management for remote teams

2. Who are the primary users?
   > Remote workers and small teams

✓ Generating steering files...
✅ Steering files created successfully!
```

### Option B: Manual Customization

If you prefer manual control, edit the steering files directly.

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

### 4.4 Validate Steering Files

After customizing, validate your steering files:

```bash
# Check for completeness and consistency
hiveforge steering validate

# Strict mode (treat warnings as errors)
hiveforge steering validate --strict
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

### Workflow 1: Starting a New Project

```bash
# 1. Initialize KIRO structure
hiveforge -n my-project

# 2. Generate steering files with Steering Assistant
hiveforge steering init --analyze-code

# 3. Act as Orchestrator in Kiro IDE
"I want to build [feature]. Please plan the implementation."

# 4. Orchestrator delegates to specialized agents
# 5. Switch agents and implement
# 6. Red Team reviews the implementation
```

### Workflow 2: Adding KIRO to Existing Project

```bash
# 1. Clone your existing repository
git clone https://github.com/youruser/existing-project.git
cd existing-project

# 2. Initialize KIRO structure
hiveforge -n existing-project

# 3. Generate steering files from existing code
hiveforge steering init --analyze-code

# 4. Review generated steering files
cat .kiro/steering/tech-stack.md
cat .kiro/steering/architecture.md

# 5. Start using KIRO methodology
# Act as Orchestrator to plan improvements
```

### Workflow 3: Continuing Work on Existing KIRO Project

```bash
# 1. Install HiveForge (see INSTALLATION_GUIDE.md)
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge
pip install -e .

# 2. Clone your project
cd ~/projects
git clone https://github.com/youruser/your-project.git
cd your-project

# 3. Verify KIRO structure exists
ls -la .kiro/

# 4. Review project context
cat swarm_state.md
cat .kiro/steering/project-vision.md

# 5. Continue development in Kiro IDE
# Act as Orchestrator to check status and continue work
```

### Workflow 4: Adding a New Feature

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

### Workflow 5: Fixing a Bug

```bash
# 1. Act as QA Engineer
"I found a bug: users can't reset passwords. Investigate and fix."

# 2. QA Engineer analyzes and delegates to Backend Engineer
# 3. Backend Engineer fixes the issue
# 4. QA Engineer writes regression test
```

### Workflow 6: Updating Steering Files

```bash
# When your project evolves, update steering files

# 1. Add new documentation to onboarding folder
cp updated-architecture.md .kiro/onboarding/

# 2. Update steering files
hiveforge steering update

# 3. Review proposed changes
# The assistant will show diffs and ask for approval

# 4. Validate updated files
hiveforge steering validate --strict
```

### Workflow 7: Regenerating Project

```bash
# If you need to reset agent definitions
hiveforge -n my-awesome-app --force

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
- 🛠️ **[Development Guide](./docs/development.md)** - Contribute to hiveforge
- 🔍 **[Troubleshooting](./docs/troubleshooting.md)** - Common issues

### Join the Community

- 💬 **[Discord](https://discord.gg/your-invite)** - Chat with other users
- 🐛 **[GitHub Issues](https://github.com/asoshnin/HiveForge/issues)** - Report bugs
- 💡 **[Discussions](https://github.com/asoshnin/HiveForge/discussions)** - Share ideas

---

## Troubleshooting

### "Could not find a version that satisfies the requirement hiveforge"

**Problem:**
```bash
ERROR: Could not find a version that satisfies the requirement hiveforge (from versions: none)
```

**Cause:** HiveForge is not yet published to PyPI.

**Solution:** Install from source instead:
```bash
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge
pip install -e .
```

### "Invalid project name" Error

**Problem:**
```bash
❌ Invalid: 'My Project'. Use kebab-case (e.g., 'my-project')
```

**Solution:**
Use lowercase letters, numbers, and hyphens only:
```bash
hiveforge -n my-project  # ✅ Correct
```

### ".kiro/ exists" Error

**Problem:**
```bash
❌ .kiro/ exists. Use --force to overwrite.
```

**Solution:**
Add the `--force` flag:
```bash
hiveforge -n my-project --force
```

### Command Not Found

**Problem:**
```bash
hiveforge: command not found
```

**Solution:**

1. Ensure hiveforge is installed:
```bash
pip install hiveforge
```

2. If using a virtual environment, make sure it's activated:
```bash
# macOS/Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

3. If installed with `--user` flag, ensure your PATH includes the user bin directory:
```bash
# macOS/Linux: Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# Windows: Add %APPDATA%\Python\Scripts to your PATH environment variable
```

4. Try reinstalling:
```bash
pip uninstall hiveforge
pip install hiveforge
```

---

<div align="center">

**🎉 Congratulations! You've created your first KIRO v05 project!**

Need help? Check the [full documentation](./README.md) or [open an issue](https://github.com/asoshnin/HiveForge/issues).

</div>
