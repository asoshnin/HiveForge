# 🚀 hiveforge

> **Scaffold KIRO Methodology v05 projects in seconds**

[![PyPI version](https://badge.fury.io/py/hiveforge.svg)](https://badge.fury.io/py/hiveforge)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-189%2B%20passed-brightgreen)](https://github.com/asoshnin/HiveForge)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/asoshnin/HiveForge)

**hiveforge** is a CLI tool that scaffolds [KIRO Methodology v05](https://kiro.ai) projects with a complete multi-agent architecture, steering files, and swarm state management—ready for use with Kiro IDE.

---

## ✨ Features

- 🤖 **7 Specialized Agent Definitions** - Orchestrator, Data Architect, Backend Engineer, Frontend Engineer, QA Engineer, DevOps Engineer, Red Team
- 📋 **8 Steering Files** - Project vision, tech stack, conventions, architecture, and standards
- 🧭 **Steering Assistant** - AI-powered tool to create and maintain steering files throughout your project lifecycle
- 🤖 **LLM-Primary Synthesis** - Direct LLM generation of steering files with hallucination detection (v3.0.0)
- 📂 **Custom Source Document Paths** - Specify where your design documents are located (v2.2.0)
- 🎯 **Confidence Scoring** - Know which content is from documents vs. inferred (v2.2.0)
- ⚠️ **Hallucination Guardrails** - Duplicate paragraph detection prevents LLM hallucinations (v3.0.0)
- 👁️ **Dry-Run Mode** - Preview what will be generated before committing (v2.2.0)
- 🔄 **Draft Review Workflow** - Review generated files before writing to disk (v3.0.0)
- 📊 **Swarm State Management** - Pre-configured `swarm_state.md` with dynamic placeholders
- 🔒 **Permission-Based Security** - `toolsSettings` enforce role boundaries (Orchestrator can't write to `src/`)
- ⚡ **Zero Configuration** - Works out of the box, no setup required
- 🎯 **Kebab-Case Validation** - Enforces clean, consistent project naming
- 🔄 **Force Overwrite** - Regenerate projects with `--force` flag

---

## 📦 Installation

### From Source (Current Method)

Since HiveForge is not yet published to PyPI, install it directly from source:

```bash
# Clone repository
git clone https://github.com/asoshnin/HiveForge.git
cd HiveForge

# Create and activate virtual environment
# macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Windows (Command Prompt):
python -m venv venv
venv\Scripts\activate.bat

# Windows (PowerShell):
python -m venv venv
venv\Scripts\Activate.ps1

# Install in editable mode (recommended for development)
pip install -e .

# OR install with Poetry
poetry install
poetry shell

# Verify installation
hiveforge --help
```

### From PyPI (Coming Soon)

Once published to PyPI, you'll be able to install with:

```bash
pip install hiveforge
```

### For Contributors

```bash
# Clone repository
git clone https://github.com/yourusername/hiveforge.git
cd hiveforge

# Install with Poetry (creates virtual environment automatically)
poetry install

# Activate Poetry's virtual environment
poetry shell

# Verify installation
hiveforge --help
```

---

## 🚀 Quick Start

### 1. Initialize a New Project

```bash
# Using explicit project name
hiveforge --project-name my-awesome-app

# Using current directory name
cd my-awesome-app
hiveforge
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
hiveforge --project-name my-project

# Use short flags
hiveforge -n my-project

# Overwrite existing project
hiveforge -n my-project --force
hiveforge -n my-project -f

# Use current directory name
cd my-existing-project
hiveforge
```

### Steering Assistant Commands

The Steering Assistant helps you create and maintain steering files throughout your project lifecycle:

```bash
# Create steering files from scratch
hiveforge steering init

# Create with code analysis (auto-extract project info)
hiveforge steering init --analyze-code

# Non-interactive mode (use only artifacts)
hiveforge steering init --no-interactive

# Enable web research for missing information
hiveforge steering init --research

# Update existing steering files
hiveforge steering update

# Validate steering files
hiveforge steering validate

# Strict validation (warnings as errors)
hiveforge steering validate --strict
```

#### Steering Workflow

1. **Place artifacts** in `.kiro/onboarding/` (optional):
   - Project specs, architecture diagrams, requirements docs
   - Supports markdown, PDF, and images

2. **Run init** to create steering files:
   ```bash
   hiveforge steering init --analyze-code
   ```

3. **Answer questions** during interactive conversation (if needed)

4. **Review generated files** in `.kiro/steering/`

5. **Update later** when project evolves:
   ```bash
   hiveforge steering update
   ```

See the [Steering Assistant Guide](#-steering-assistant) for detailed usage.

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
hiveforge -n my-app
# ... edit .kiro/steering/tech-stack.md ...
hiveforge -n my-app --force  # Preserves your steering edits
```

### Integration with CI/CD

```yaml
# .github/workflows/init.yml
- name: Initialize KIRO project
  run: |
    pip install hiveforge
    hiveforge -n ${{ github.event.repository.name }}
```

---

## 🔧 LLM Configuration

HiveForge uses an LLM provider abstraction that supports multiple backends with automatic fallback. When running inside KIRO IDE, no configuration is needed—it uses KIRO's native LLM capabilities automatically.

### Provider Priority

The system tries providers in this order:

1. **KIRO Native** (primary in MCP mode) - Uses KIRO IDE's built-in LLM
2. **Google Vertex AI** - Google Cloud's AI platform
3. **OpenAI** - OpenAI's GPT models
4. **None** - Falls back to `[INFERRED]` markers

### Quick Setup

#### For KIRO IDE Users (Recommended)
No configuration needed! HiveForge automatically uses KIRO's native LLM when running inside the IDE.

#### For CLI Users with Vertex AI
```bash
export HIVEFORGE_LLM_PROVIDER=vertex
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Install with Vertex AI support
pip install hiveforge-steering-mcp[vertex]
```

#### For CLI Users with OpenAI
```bash
export HIVEFORGE_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-api-key

# Install with OpenAI support
pip install hiveforge-steering-mcp[openai]
```

### Configuration File (Optional)

Create `~/.hiveforge/llm_config.json` for persistent configuration:

**Vertex AI:**
```json
{
  "provider_type": "vertex_ai",
  "project_id": "your-gcp-project",
  "model": "gemini-pro",
  "temperature": 0.1,
  "max_tokens": 2000
}
```

**OpenAI:**
```json
{
  "provider_type": "openai",
  "api_key": "sk-your-api-key",
  "model": "gpt-4",
  "temperature": 0.1,
  "max_tokens": 2000
}
```

### Troubleshooting

**"No LLM provider available"**
- In KIRO IDE: Ensure you're running via MCP (not standalone CLI)
- In CLI: Check environment variables or config file
- Install optional dependencies: `pip install hiveforge-steering-mcp[vertex]` or `[openai]`

**"Vertex AI call failed"**
- Verify `GOOGLE_CLOUD_PROJECT` is set
- Check credentials file exists and is valid
- Ensure service account has Vertex AI permissions

**"OpenAI call failed"**
- Verify `OPENAI_API_KEY` is set and valid
- Check API key has sufficient credits
- Ensure you're not hitting rate limits

For detailed configuration options, see [docs/CONFIGURATION.md](hiveforge-power/docs/CONFIGURATION.md).

---

## 🧭 Steering Assistant

The Steering Assistant is an AI-powered tool that helps you create and maintain steering files throughout your project lifecycle.

### What It Does

- **Analyzes Your Codebase**: Automatically extracts tech stack, architecture, and conventions
- **Parses Artifacts**: Reads project specs, diagrams, and documentation
- **Fills Knowledge Gaps**: Asks targeted questions to gather missing information
- **Generates Steering Files**: Creates comprehensive, consistent documentation
- **Maintains Over Time**: Updates steering files as your project evolves
- **Preserves Customizations**: Keeps your manual edits during updates

### Commands

#### `hiveforge steering init`

Create steering files from scratch.

**Flags:**
- `--analyze-code`: Analyze existing codebase to extract project information
- `--research`: Enable web research to find missing information
- `--skip-validation`: Skip automatic validation after generation
- `--interactive` / `--no-interactive`: Enable/disable conversation mode (default: interactive)

**Examples:**
```bash
# Basic init with conversation
hiveforge steering init

# Import existing codebase
hiveforge steering init --analyze-code

# Non-interactive (use only artifacts)
hiveforge steering init --no-interactive

# With web research
hiveforge steering init --research
```

#### `hiveforge steering update`

Update existing steering files with new information.

**Flags:**
- `--research`: Enable web research
- `--skip-validation`: Skip validation after update
- `--interactive` / `--no-interactive`: Enable/disable conversation mode

**Examples:**
```bash
# Update with new artifacts
hiveforge steering update

# Non-interactive update
hiveforge steering update --no-interactive
```

#### `hiveforge steering validate`

Validate steering files for completeness and consistency.

**Flags:**
- `--strict`: Treat warnings as errors

**Examples:**
```bash
# Basic validation
hiveforge steering validate

# Strict mode (for CI/CD)
hiveforge steering validate --strict
```

### Workflow Example

```bash
# 1. Create new project
hiveforge -n my-app

# 2. Add project artifacts (optional)
mkdir -p .kiro/onboarding
cp project-spec.md .kiro/onboarding/
cp architecture.pdf .kiro/onboarding/

# 3. Generate steering files
hiveforge steering init --analyze-code

# 4. Answer questions during conversation
# The assistant will ask about missing information

# 5. Review generated files
ls .kiro/steering/

# 6. Later, when project evolves...
cp updated-requirements.md .kiro/onboarding/
hiveforge steering update

# 7. Validate before committing
hiveforge steering validate --strict
```

### What Gets Analyzed

When you use `--analyze-code`, the Steering Assistant automatically extracts:

- **Languages & Versions**: Detected from file extensions and dependency files
- **Tech Stack**: Frameworks, libraries, databases from package.json, requirements.txt, etc.
- **Architecture**: Inferred from directory structure (monolithic, microservices, layered, etc.)
- **Conventions**: Naming patterns, indentation, docstring styles from actual code
- **Documentation**: Existing README files, docs folders, inline comments

### Token Efficiency

The Steering Assistant is designed to minimize LLM API costs:

- **Question Batching**: Max 8 questions per batch
- **Response Caching**: Avoids re-asking answered questions
- **Token Limiting**: Max 4000 tokens of context per prompt
- **Incremental Updates**: Only sends changed sections (max 3000 tokens per file)
- **Local Analysis**: All code analysis runs locally without LLM calls

### Error Handling

The Steering Assistant handles errors gracefully:

- **Corrupted Files**: Skips and continues with other files
- **Missing Dependencies**: Infers from import statements
- **LLM Rate Limiting**: Automatic retry with exponential backoff
- **Network Issues**: Retries with backoff, falls back to cached responses

---

## 📚 Documentation

- **[Workflow Guide](./WORKFLOW.md)** - End-to-end workflows with diagrams
- **[Quick Start Guide](./QUICKSTART.md)** - 5-minute walkthrough
- **[Architecture](./docs/architecture.md)** - How hiveforge works
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
git clone https://github.com/yourusername/hiveforge.git
cd hiveforge

# Install with Poetry (automatically creates and manages virtual environment)
poetry install

# Activate Poetry's virtual environment
poetry shell

# Run tests
pytest tests/ -v --cov=src/hiveforge

# Make changes and test
# ... edit code ...
pytest tests/ -v

# Deactivate virtual environment when done
exit
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
