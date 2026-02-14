# 🚀 kiro-init

> **Scaffold KIRO Methodology v05 projects in seconds**

[![PyPI version](https://badge.fury.io/py/kiro-init.svg)](https://badge.fury.io/py/kiro-init)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-66%20passed-brightgreen)](https://github.com/asoshnin/HiveForge)
[![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)](https://github.com/asoshnin/HiveForge)

**kiro-init** is a CLI tool that scaffolds [KIRO Methodology v05](https://kiro.ai) projects with a complete multi-agent architecture, steering files, and swarm state management—ready for use with Kiro IDE.

---

## ✨ Features

- 🤖 **7 Specialized Agent Definitions** - Orchestrator, Data Architect, Backend Engineer, Frontend Engineer, QA Engineer, DevOps Engineer, Red Team
- 📋 **8 Steering Files** - Project vision, tech stack, conventions, architecture, and standards
- 📊 **Swarm State Management** - Pre-configured `swarm_state.md` with dynamic placeholders
- 🔒 **Permission-Based Security** - `toolsSettings` enforce role boundaries (Orchestrator can't write to `src/`)
- ⚡ **Zero Configuration** - Works out of the box, no setup required
- 🎯 **Kebab-Case Validation** - Enforces clean, consistent project naming
- 🔄 **Force Overwrite** - Regenerate projects with `--force` flag

---

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install kiro-init
```

### From Source

```bash
git clone https://github.com/yourusername/kiro-init.git
cd kiro-init
poetry install
```

---

## 🚀 Quick Start

### 1. Initialize a New Project

```bash
# Using explicit project name
kiro-init --project-name my-awesome-app

# Using current directory name
cd my-awesome-app
kiro-init
```

### 2. What Gets Created

```
my-awesome-app/
├── .kiro/
│   ├── agents/
│   │   ├── orchestrator.md          # 🎯 Delegation & planning
│   │   ├── data_architect.md        # 🗄️ Database design
│   │   ├── backend_engineer.md      # ⚙️ API & business logic
│   │   ├── frontend_engineer.md     # 🎨 UI/UX implementation
│   │   ├── qa_engineer.md           # ✅ Testing & quality
│   │   ├── devops_engineer.md       # 🚢 Deployment & infra
│   │   └── red_team.md              # 🔍 Security & audits
│   └── steering/
│       ├── project-vision.md        # 📝 Goals & objectives
│       ├── tech-stack.md            # 🛠️ Technology choices
│       ├── conventions.md           # 📏 Code style & naming
│       ├── architecture.md          # 🏗️ System design
│       ├── db-standards.md          # 🗃️ Database patterns
│       ├── api-standards.md         # 🔌 API design rules
│       ├── ui-standards.md          # 🎨 UI/UX guidelines
│       └── qa-standards.md          # ✅ Testing strategy
├── .swarm/
│   ├── plan/                        # 📋 Task planning
│   └── audit_logs/                  # 📊 Agent activity logs
└── swarm_state.md                   # 🧠 Central state document
```

### 3. Open in Kiro IDE

```bash
# Reload Kiro IDE to recognize the new project structure
# Fill in swarm_state.md with your project details
# Start acting as the Orchestrator agent
```

---

## 📖 Usage

### Basic Commands

```bash
# Initialize with project name
kiro-init --project-name my-project

# Use short flags
kiro-init -n my-project

# Overwrite existing project
kiro-init -n my-project --force
kiro-init -n my-project -f

# Use current directory name
cd my-existing-project
kiro-init
```

### Project Name Rules

✅ **Valid Names:**
- `my-project`
- `awesome-app`
- `project-123`
- `app`

❌ **Invalid Names:**
- `My Project` (spaces)
- `my_project` (underscores)
- `MyProject` (PascalCase)
- `my.project` (dots)

---

## 🎯 What is KIRO Methodology v05?

KIRO v05 is a **multi-agent development methodology** that uses:

1. **Role-Based Agents** - Each agent has specific responsibilities (Orchestrator delegates, Backend Engineer writes APIs, etc.)
2. **Permission-Based Security** - Agents can only modify files within their domain (enforced via `toolsSettings`)
3. **Steering Files** - Shared knowledge base that all agents reference for consistency
4. **Swarm State** - Central document tracking project status, decisions, and delegation tree
5. **Red Team Audits** - Continuous quality checks and security reviews

### Key Benefits

- 🎯 **Clear Separation of Concerns** - Each agent focuses on their expertise
- 🔒 **Built-in Safety** - Orchestrator can't accidentally modify source code
- 📚 **Knowledge Continuity** - Steering files prevent context loss
- 🔄 **Iterative Refinement** - Red Team provides continuous feedback
- 🤝 **Collaborative AI** - Multiple agents work together on complex projects

---

## 🛠️ Advanced Usage

### Custom Workflows

```bash
# Generate project, modify steering files, regenerate
kiro-init -n my-app
# ... edit .kiro/steering/tech-stack.md ...
kiro-init -n my-app --force  # Preserves your steering edits
```

### Integration with CI/CD

```yaml
# .github/workflows/init.yml
- name: Initialize KIRO project
  run: |
    pip install kiro-init
    kiro-init -n ${{ github.event.repository.name }}
```

---

## 📚 Documentation

- **[Workflow Guide](./WORKFLOW.md)** - End-to-end workflows with diagrams
- **[Quick Start Guide](./QUICKSTART.md)** - 5-minute walkthrough
- **[Architecture](./docs/architecture.md)** - How kiro-init works
- **[Development Guide](./docs/development.md)** - Contributing & testing
- **[Troubleshooting](./docs/troubleshooting.md)** - Common issues & FAQ
- **[Changelog](./CHANGELOG.md)** - Version history

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for:

- Code of Conduct
- Development setup
- Pull request process
- Coding standards

### Quick Start for Contributors

```bash
# Clone and setup
git clone https://github.com/yourusername/kiro-init.git
cd kiro-init
poetry install

# Run tests
pytest tests/ -v --cov=src/kiro_init

# Make changes and test
# ... edit code ...
pytest tests/ -v
```

---

## 📊 Project Status

- ✅ **Phase 1 MVP** - Complete (CLI scaffolding tool)
- 🚧 **Phase 2** - In Progress (CI/CD, PyPI publishing, beta testing)
- 📅 **Phase 3** - Planned (IDE-agnostic mode, tech-stack templates)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built for the [Kiro IDE](https://kiro.ai) ecosystem
- Inspired by multi-agent development best practices
- Thanks to all [contributors](https://github.com/asoshnin/HiveForge/graphs/contributors)

---

## 📞 Support

- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/asoshnin/HiveForge/issues)
- 💡 **Feature Requests:** [GitHub Discussions](https://github.com/asoshnin/HiveForge/discussions)
- 📧 **Email:** 89580632+asoshnin@users.noreply.github.com

---

<div align="center">

**Made with ❤️ by [Alex Soshnin](https://github.com/asoshnin)**

⭐ **Star this repo if you find it useful!** ⭐

</div>
