# **Steering Files Generation: As-Is Analysis & To-Be Architecture**

**Date**: 2026-02-25 
**Role**: Product Owner / System Architect  
**Status**: Design Proposal

---

## **0\. Executive Summary**

The current steering file generation pipeline produces unusable output. The root cause is architectural: the system attempts to synthesize structured documentation using keyword matching, regex-based template population, and gap analysis heuristics — with LLM as an optional afterthought. The result is files where the same paragraph is copy-pasted into every section, placeholders remain unfilled, and content from one section bleeds into another (as seen in the generated `project-vision.md`).

The fix is a fundamental inversion: **LLM must be the primary synthesis engine**, not a fallback. All other components (code analysis, document parsing, codebase diff) become context providers that feed a well-structured LLM prompt.

# **1\. PROJECT OVERVIEW (WHAT WE ARE BUILDING)**

### **Summary of HiveForge Extension to KIRO**

**HiveForge** is a CLI scaffolding tool and an integrated Model Context Protocol (MCP) Power package designed to upgrade the KIRO IDE experience from unstructured "vibe coding" to "Systematic Agentic Engineering". It operates by instantiating a "Virtual Company" within a user's repository. Instead of relying on a single AI chat window that generates code rapidly but recklessly, HiveForge enforces the KIRO Methodology v05. It achieves this by supplying a shared backend architecture with specialized AI agents, immutable architectural rules (Steering Files), and a persistent state tracking system.

---

### **Potential Users (The Practitioners)**

HiveForge is built for developers who have moved past the "wow" phase of AI coding and have hit the "wall" of complexity. Specifically, the core users include:

* **Senior Software Engineers & Technical Leads:** Developers maintaining complex, long-term architectures or executing enterprise-scale legacy refactoring.  
* **Platform Engineers / DevOps:** Users who need to securely sandbox AI operations to infrastructure files without risking application logic.  
* **Agency Developers:** Engineers juggling multiple client codebases who cannot afford context loss when switching contexts between projects.  
* **Security & QA Engineers:** Practitioners operating in regulatory or compliance-heavy environments where audit trails and adversarial testing are mandatory.

---

### **User Pains & Problems**

These developers face a specific set of challenges when using generic AI coding assistants (like standard Cursor, Copilot, or Replit):

1. **Context Amnesia (The "Goldfish" Memory):** Even with large token windows, AI models forget architectural decisions made in previous sessions. They re-suggest dismissed approaches, ignore constraints, and lose track of the master plan after a few days of project downtime.  
2. **Spaghetti Code & Abstraction Leaks:** A single, unrestricted AI agent attempting to be "full-stack" creates boundary violations. It will lazily inject database query logic directly into UI components, creating circular dependencies and an unmaintainable mess.  
3. **The "Slop" Factor (AI-Generated Technical Debt):** Chat-based AI excels at rapid script generation but is systematically lacking in architectural judgment, leading to massive amounts of code cloning and long-term tech debt.  
4. **Legacy Codebase Disconnect:** AI tools excel at greenfield (new) projects but struggle with messy legacy systems where the original documentation completely contradicts the actual implemented code.

---

### **How HiveForge Fixes These Pains**

HiveForge acts as an operating system for AI agents, replacing chaotic chat interfaces with rigid engineering workflows:

**1\. Curing Amnesia with Persistent Project Memory** HiveForge introduces `swarm_state.md`, a Single Source of Truth that tracks the project's real-time operational reality. This file acts as the project's long-term memory. It logs decisions, technical debt, and active tasks. If a developer pauses a project for a month, the AI uses this file to know exactly where it left off, entirely eliminating cross-session amnesia.

**2\. Eliminating Spaghetti Code via Role-Based Sandboxing** Instead of one omnipotent AI, HiveForge scaffolds a specialized multi-agent roster (Orchestrator, Data Architect, Backend Engineer, Frontend Engineer, etc.). To prevent abstraction leaks, HiveForge utilizes strict `toolsSettings` that place physical limits on agent permissions. For example, the Backend agent is hard-blocked from editing UI or database migration files, and the Orchestrator can plan but is physically prevented from writing production code.

**3\. Preventing AI "Slop" with the Truth Hierarchy** To stop AI from hallucinating requirements, HiveForge enforces a "Cascade of Truth" using immutable Steering Files (e.g., `tech-stack.md`, `architecture.md`, `conventions.md`). The AI cannot generate code until these files are populated. If an AI generates a feature that contradicts the rules pinned in these documents, the output is rejected, ensuring the AI conforms to the project's architectural laws.

**4\. Bridging the Legacy Gap with Discrepancy Analysis** For messy, existing codebases, HiveForge provides a specific workflow to tame technical debt. The "Steering Assistant" parses ideal intent from old PDFs/specs into Steering Files. Then, the Orchestrator agent is unleashed to analyze the *actual* codebase against those files, automatically generating a `DISCREPANCY_REPORT.md`. This report highlights exactly where the code violates the architecture or where promised features are missing, giving developers a structured roadmap for refactoring.

**5\. Built-In Quality Gates via the Red Team** To prevent buggy or insecure code from shipping, HiveForge includes an adversarial "Red Team" agent. This agent has read-only access to the entire project and acts purely to hunt for security vulnerabilities, performance bottlenecks, and architectural drift before a developer signs off on a deployment.

---

## **2\. As-Is: Current Pipeline**

### **2.1 Architecture Overview**

```
flowchart TD
 A[User: hiveforge steering init] --> B[InitWorkflow / AutonomousWorkflow]
 B --> C[ScalableDiscovery\nScans ENTIRE project tree]
 C --> D[DocumentParser\nMarkdown / PDF / Image]
 B --> E[CodeAnalyzer\nAST + regex, local only]
 D --> F[KnowledgeBase\nIn-memory text index]
 E --> F
 F --> G[GapAnalysisEngine\nKeyword matching + regex]
 G --> H{LLM available?}
 H -- No --> I[TemplatePopulator\nRegex placeholder replacement]
 H -- Yes --> J[SteeringAssistant.generate_file\nLLM call per template]
 J -- LLM fails --> I
 I --> K[Write .kiro/steering/*.md]
 J --> K
 K --> L[SteeringValidator]
```

### **2.2 Component-by-Component Diagnosis**

#### ***Document Discovery (ScalableDiscovery)***

- **Problem**: Scans the entire project tree by default. No concept of a "trusted source folder". Picks up test fixtures, outdated docs, generated files, node\_modules leftovers — anything that survives the skip-list.  
- **Impact**: Knowledge base is polluted with irrelevant or contradictory content before synthesis even begins.

#### ***KnowledgeBase***

- **Problem**: A simple in-memory text concatenation. `get_relevant_content()` uses keyword matching (e.g., "backend", "framework") to extract snippets. There is no semantic understanding of what a document *means*.  
- **Impact**: The same paragraph that mentions multiple keywords gets injected into multiple template contexts, causing the copy-paste repetition seen in output.

#### ***GapAnalysisEngine***

- **Problem**: Classifies template sections as "complete / ambiguous / missing" using keyword presence in the knowledge base. A section is "complete" if keywords like "backend" appear near the section name. This is not gap analysis — it is keyword counting.  
- **Impact**: Sections are falsely marked "complete" when the knowledge base contains any text with matching words, so the LLM never gets called for those sections.

#### ***TemplatePopulator (primary path when LLM is absent or fails)***

- **Problem**: Uses `re.sub()` to replace `{placeholder}` patterns with whatever the knowledge base returned for that section. If the knowledge base returned a 500-character blob for "Elevator Pitch", that same blob gets substituted everywhere the pattern matches.  
- **Impact**: Produces the observed output: one paragraph repeated across Elevator Pitch, Problem Statement, Solution Overview, Target Users, Success Metrics, and Timeline.

#### ***SteeringAssistant.generate\_file (LLM path)***

- **Problem**: The LLM path exists and is architecturally sound, but it is only reached when `llm_provider.is_available()` returns True. The `LLMProvider` defaults to `ProviderType.NONE` unless explicitly configured via env vars or `~/.hiveforge/llm_config.json`. In MCP mode, `ctx` is passed but the `ctx.sample()` call is the only path that works without external API keys. In practice, the LLM path is almost never reached.  
- **Impact**: The fallback (TemplatePopulator) is the de-facto primary path.

#### ***Source Document Scope (Critical Design Flaw)***

- **Problem**: The system has no enforced boundary between "user-provided design documents" and "everything else in the repo". The `source_docs_path` parameter exists but defaults to `.kiro/onboarding`, and the code analyzer scans the full project tree regardless.  
- **Impact**: The system cannot distinguish between a design spec the user wants to use as source-of-truth and a test fixture that happens to contain the word "architecture".

### **2.3 Observed Output Quality**

The generated `project-vision.md` demonstrates all failure modes simultaneously:

- The "Elevator Pitch" paragraph is copy-pasted verbatim into Problem Statement, Solution Overview, Target Users, Success Metrics, and Timeline  
- Russian-language content appears in English-language fields (content from one document bled into all sections)  
- Placeholders like `{Out of scope feature 1}` remain unfilled  
- The "Secondary" target user field contains `{Who else benefits}` — a raw template placeholder

---

## **3\. Use Cases That Must Be Supported**

```
mindmap
 root((Steering\nGeneration))
 New Project
 Design docs exist, no code yet
 Generate steering from docs only
 Existing Project
 Code exists, no design docs
 Reverse-engineer steering from codebase
 Drift Correction
 Both code and docs exist
 Reconcile divergence
 Error Recovery
 Broken/incomplete steering files
 Regenerate specific files
 Pivot / Scope Change
 User provides new intent document
 Update steering to reflect new direction
```

### **3.1 Use Case Matrix**

| Use Case | Primary Input | Secondary Input | LLM Task |
| :---- | :---- | :---- | :---- |
| New project from docs | Design docs in source folder | — | Synthesize steering from docs |
| Reverse engineering | Codebase analysis | — | Infer intent from code |
| Drift correction | Existing steering files | Codebase analysis | Identify delta, propose reconciliation |
| Error recovery | Existing (broken) steering | Codebase analysis | Regenerate specific files |
| Pivot / scope change | New intent doc | Existing steering \+ code | Merge new intent with existing context |

---

## **4\. To-Be: Proposed Architecture**

### **4.1 Core Design Principles**

1. **LLM is the synthesis engine, not a fallback.** Every steering file is generated by an LLM call. Python code only prepares context and writes output.  
2. **Source documents are a bounded, trusted input.** The user explicitly designates a folder. Nothing outside that folder (plus the codebase) is used as source material.  
3. **Codebase analysis is a context provider, not a content generator.** Code analysis produces structured facts (languages, dependencies, patterns) that enrich the LLM prompt — it does not produce prose.  
4. **Delta awareness.** The pipeline always computes three inputs: (a) what the design docs say, (b) what the code says, (c) what the existing steering files say. The LLM reconciles these.  
5. **Silence over hallucination.** If information is genuinely absent, the output section contains `N/A` or a clearly marked `[NOT FOUND]` — never fabricated content.  
6. **Zero mandatory user interaction.** The system generates a complete draft from available inputs. The user reviews and approves, but is never blocked waiting for answers.

### **4.2 To-Be Pipeline**

```
flowchart TD
 A[User: hiveforge steering init\nor update] --> B[InputResolver]
 B --> C{Source docs\npath provided?}
 C -- Yes --> D[Load docs from\nexplicit folder ONLY]
 C -- No --> E[Load docs from\n.kiro/onboarding ONLY]
 D --> F[DocumentParser\nMarkdown / PDF / Image → text]
 E --> F
 B --> G[CodeAnalyzer\nAST + regex → structured facts]
 B --> H[ExistingSteeringReader\nLoad current .kiro/steering/*.md]
 F --> I[ContextAssembler]
 G --> I
 H --> I
 I --> J[DeltaAnalyzer\nCompute doc↔code↔steering diffs]
 J --> K[PromptBuilder\nOne prompt per template]
 K --> L[LLMProvider\nctx.sample / OpenAI / Vertex]
 L --> M{Response\nvalid?}
 M -- Yes --> N[SteeringFileWriter]
 M -- No / empty --> O[RetryWithSimplifiedPrompt]
 O --> L
 N --> P[Write .kiro/steering/*.md]
 P --> Q[ConfidenceAnnotator\nMark N/A sections]
 Q --> R[User Review\nOptional approval step]
```

### **4.3 New Components**

#### ***InputResolver***

Determines what inputs are available and which use case applies. Produces a `GenerationContext` struct:

```py
@dataclass
class GenerationContext:
 use_case: Literal["new_from_docs", "reverse_engineer", "drift_correction", "update"]
 source_docs: list[ParsedDocument] # From bounded source folder only
 code_facts: CodeAnalysisFacts # Structured, not prose
 existing_steering: dict[str, str] # Current .kiro/steering/*.md content
 delta: DeltaReport # Computed differences
 user_intent: str | None # Optional free-text from user
```

#### ***DocumentParser (scoped)***

Unchanged in implementation, but **strictly scoped**: only reads files from the explicitly designated source folder. No project-wide scanning for source documents.

#### ***CodeAnalyzer (facts only)***

Produces structured facts, not prose summaries:

```py
@dataclass 
class CodeAnalysisFacts:
 primary_language: str
 frameworks: list[str]
 dependencies: list[Dependency]
 architecture_pattern: str # "layered", "microservices", "cli_tool", etc.
 has_tests: bool
 test_framework: str | None
 api_type: str | None # "REST", "GraphQL", "MCP", "CLI", None
 database: str | None
 entry_points: list[str] # main files, CLI commands, MCP tools
 naming_conventions: NamingConventions
 directory_structure: str # Compact tree representation
```

#### ***DeltaAnalyzer***

Computes three-way differences between design docs, codebase, and existing steering files. This is the key component for drift correction and update use cases:

```
flowchart LR
 A[Design Docs] --> D[DeltaAnalyzer]
 B[Codebase Facts] --> D
 C[Existing Steering] --> D
 D --> E[DeltaReport]
 E --> F[doc_vs_code: list of divergences]
 E --> G[steering_vs_code: list of drifts]
 E --> H[steering_vs_docs: list of conflicts]
 E --> I[missing_in_all: list of gaps]
```

#### ***PromptBuilder***

Builds one LLM prompt per steering template. The prompt includes:

* The template structure (section names and descriptions, not the raw template with placeholders).  
* **Template-relevant source document content** (extracted via semantic chunking to fit strictly within a 4,000 token budget per template).  
* Structured code facts (filtered to template-relevant fields, max 2,000 tokens).  
* Existing steering file content (max 1,000 tokens).  
* Delta report (for drift/update use cases).  
* Explicit instructions: fill every section, use `N/A` if information is absent, do not invent.

```py
def build_prompt(
 template_name: str,
 template_schema: TemplateSchema,
 context: GenerationContext, # Output of ContextAssembler
 previously_generated: dict[str, str] # Rolling summaries of prior files
) -> tuple[str, str]: # (system_prompt, user_prompt)
```

#### ***ContextAssembler (New)***

To prevent catastrophic context window bloat and "lost in the middle" LLM degradation, the `ContextAssembler` enforces strict token budgets per template. It implements template-specific context extraction.

```py
class ContextAssembler:
 def assemble_context_for_template(
 self,
 template_name: str,
 source_docs: List[ParsedDocument],
 code_facts: CodeAnalysisFacts,
 existing_steering: Optional[str],
 ) -> GenerationContext:
 """
 Assemble ONLY the context relevant to this specific template.
 
 Token budget per template: 8000 tokens max 
- Source docs (relevant sections): 4000 tokens 
- Code facts: 2000 tokens 
- Existing steering: 1000 tokens 
- Previously generated files (rolling summaries or specific extracted fields, NOT raw text): 1000 tokens 

*Note: The ContextAssembler is strictly required because KIRO's internal #codebase index is closed and not exposed as a callable MCP tool for programmatic use.*
"""
 # Extracts sections using TEMPLATE_KEYWORDS mapping 
 relevant_sections = self._extract_relevant_sections(
 template_name, source_docs, max_tokens=4000
 ) 
 
 filtered_facts = self._filter_code_facts(template_name, code_facts) 
 # ... logic continues to build GenerationContext ... 
```

#### ***LLMProvider (enhanced)***

Priority chain remains the same (KIRO native → Vertex AI → OpenAI), but:

- Always enabled by default in MCP mode (uses `ctx.sample()`)  
- Explicit error if no provider is available (no silent fallback to TemplatePopulator)  
- Retry logic with simplified prompt on empty/invalid response

#### ***SteeringFileGenerator (Transactional Safety)***

To handle catastrophic hallucination or partial failures, file generation must be strictly transactional. Files are built in an in-memory buffer, validated deterministically against the `CodeAnalysisFacts`, and written atomically.

```py
class SteeringFileGenerator:
 def generate_all_files(self) -> GenerationResult:
 """
 Generate all 8 steering files with transactional semantics.
 Guarantees:
 1. All files succeed, or none are written (atomic).
 2. Hallucinated facts are detected and rejected.
 
 Hierarchy Rule: Retry loops (RetryWithSimplifiedPrompt) are strictly reserved for syntax errors or empty responses. Hallucinations detected during `_validate_against_facts` bypass the retry loop and immediately trigger a full transaction rollback to prevent compounding logical errors.
 """
 draft_files = {} 
 validation_errors = [] 

 for template_name in GENERATION_ORDER: 
 content = self._generate_single_file(template_name, draft_files) 
 errors = self._validate_against_facts(template_name, content) 
 
 if errors: validation_errors.append(errors) 
 draft_files[template_name] = content 

 if validation_errors:
 return GenerationResult(success=False, error="Hallucination detected", files_written=[]) 

 self._atomic_write_all(draft_files) # Atomic write (all or nothing) 
```

### **4.4 Prompt Design**

The quality of output is entirely determined by prompt quality. Each template gets a prompt structured as:

```
SYSTEM:
You are a technical documentation expert. Your task is to generate a 
{template_name} steering file for a software project.

Rules:
- Use ONLY the information provided. Do not invent facts.
- If a section cannot be filled from the provided context, write "N/A".
- Output ONLY the final Markdown. No explanations, no preamble.
- Each section must be filled independently. Do not repeat content across sections.
- Be specific and concise. Avoid generic statements.

USER:
## Template Structure
{section_name}: {section_description}
[... all sections ...]

## Source Documents
{full_text_of_source_docs}

## Codebase Facts
Language: {primary_language}
Frameworks: {frameworks}
Architecture: {architecture_pattern}
[... all facts ...]

## Existing Steering File (for reference / update)
{existing_content or "None"}

## Detected Divergences
{delta_report or "None"}

## User Intent (if provided)
{user_intent or "None"}

Generate the complete {template_name}.md file now.
```

### **4.5 Generation Order and Cross-File Consistency**

Files are generated sequentially. To respect the 1,000-token limit for cross-file context, each subsequent file receives a *rolling summary or explicitly extracted fields* from previously generated files (not the raw text). This ensures consistency (e.g., tech-stack.md references the same frameworks as architecture.md) without shattering the context window constraints:

```
sequenceDiagram
 participant PB as PromptBuilder
 participant LLM as LLMProvider
 participant CTX as Context Accumulator

 PB->>LLM: Generate project-vision.md (no prior context)
 LLM-->>CTX: project-vision.md content
 PB->>LLM: Generate tech-stack.md + project-vision.md as context
 LLM-->>CTX: tech-stack.md content
 PB->>LLM: Generate architecture.md + prior 2 files as context
 LLM-->>CTX: architecture.md content
 Note over PB,CTX: Continue for all 8 templates
```

---

## **5\. Use Case Implementations**

### **5.1 New Project from Design Documents**

```
flowchart LR
 A[Design docs in\nsource folder] --> B[DocumentParser]
 B --> C[ContextAssembler\nno code facts, no existing steering]
 C --> D[PromptBuilder\nuse_case=new_from_docs]
 D --> E[LLM generates\n8 steering files]
```

- Code analysis is skipped (no code exists)  
- Delta analysis is skipped (no existing steering)  
- LLM fills sections from docs; writes `N/A` for anything not found in docs

### **5.2 Reverse Engineering from Codebase**

```
flowchart LR
 A[Codebase] --> B[CodeAnalyzer]
 B --> C[ContextAssembler\nno source docs, no existing steering]
 C --> D[PromptBuilder\nuse_case=reverse_engineer]
 D --> E[LLM infers intent\nfrom code facts]
```

- Source docs folder is empty or absent  
- LLM infers project vision, architecture, conventions from code facts  
- Sections that cannot be inferred (e.g., business goals, success metrics) get `N/A`

### **5.3 Drift Correction**

```
flowchart LR
 A[Source docs] --> C[ContextAssembler]
 B[Codebase] --> C
 D[Existing steering] --> C
 C --> E[DeltaAnalyzer]
 E --> F[PromptBuilder\nuse_case=drift_correction\ndelta included in prompt]
 F --> G[LLM reconciles\ndocs vs code vs steering]
```

- DeltaAnalyzer identifies: what docs say vs what code does vs what steering claims  
- LLM prompt explicitly includes the delta report  
- LLM is instructed to resolve conflicts, preferring design docs over code when they diverge (unless user\_intent says otherwise)

### **5.4 Pivot / Scope Change**

- User provides a new intent document (e.g., "we are pivoting from B2C to B2B")  
- This document is placed in the source folder alongside existing docs  
- `user_intent` field in the prompt explicitly flags the pivot  
- LLM updates steering files to reflect the new direction while preserving unchanged sections

---

## **6\. Delta Analysis Detail**

The DeltaAnalyzer is an LLM-based text comparison tool. It is strictly scoped to detect **structural drift** (e.g., "Design doc says PostgreSQL, code uses MongoDB") and dependency drift. It **cannot** detect behavioral drift or architectural boundary violations (e.g., UI importing database code), as the `CodeAnalyzer` outputs structural facts, not behavioral execution graphs.

```py
def analyze_delta(
 doc_corpus: str, # Full text of design docs 
 code_facts: CodeAnalysisFacts, # Structured facts only 
 steering_corpus: str, # Full text of existing steering 
) -> DeltaReport:
 """Use LLM to compare three text corpora and identify discrepancies."""
 prompt = f"""
 Compare these three sources and identify discrepancies:
 DESIGN DOCS: {doc_corpus} 
 CODE FACTS: {code_facts.to_json()} 
 EXISTING STEERING: {steering_corpus} 
 """ 
 response = llm.complete(prompt) 
 return parse_delta_report(response) 
```

---

## **7\. Implementation Roadmap**

### **Phase 1: Core Synthesis & Transactional Safety (Weeks 1-2)**

The following table: Task,Description Enforce boundaries & facts ,"Remove project-wide scanning. Implement `CodeAnalysisFacts` to replace prose summaries and **add real-time CLI progress indicators for deep directory traversals**."

| Task | Description |
| :---- | :---- |
| **Enforce boundaries & facts** | Remove project-wide scanning. Implement `CodeAnalysisFacts` to replace prose summaries. |
| **Token Budgeting** | Implement `ContextAssembler` with keyword-based relevance filtering to enforce the 8,000 token limit per template. |
| **Transactional Generation** | Implement `SteeringFileGenerator` with in-memory drafting. Ensure atomic writes (all 8 files succeed, or 0 are written). |
| **Hallucination Detection** | Implement deterministic `_validate_against_facts` rules for critical infrastructure fields (database, backend framework, etc.) before writing to disk. |

### **Phase 2: Delta Awareness & Relevance (Weeks 3-4)**

| Task | Description |
| :---- | :---- |
| **Implement Scoped DeltaAnalyzer** | Build the LLM-based text comparison tool for detecting structural drift. |
| **Update Prompts** | Include the `DeltaReport` in prompts for drift correction workflows. |
| **Advanced Relevance Ranking** | Add LLM-based relevance ranking to the `ContextAssembler` for edge cases where keyword matching fails on massive source documents. |

### **Phase 3: Advanced Robustness (Weeks 5+)**

| Task | Description |
| :---- | :---- |
| **Comprehensive Validation** | Expand deterministic validation rules to cover all 8 templates completely. |
| **Self-Consistency Checks** | Add LLM-based self-consistency checks (e.g., generate twice, compare results, flag discrepancies). |

---

## **8\. What Does NOT Change**

- The `LLMProvider` priority chain (KIRO native → Vertex AI → OpenAI) is correct and stays.  
- The `CodeAnalyzer` local analysis (AST, regex, language detection) is valuable and stays — it just feeds structured facts instead of prose.  
- The template structure (8 files, section names) stays.  
- The `SteeringValidator` post-generation validation stays.  
- The `BackupManager` and rollback capability stays.  
- The MCP tool interface (`init_steering`, `update_steering`, etc.) stays.

---

## **9\. Key Risk: LLM Dependency**

The proposed architecture requires a working LLM. This is a deliberate trade-off:

|  | Current (Python synthesis) | Proposed (LLM synthesis) |
| :---- | :---- | :---- |
| Output quality | Garbage (copy-paste, unfilled placeholders) | High (coherent, section-specific) |
| Works without LLM | Yes (produces garbage) | No (fails with clear error) |
| Cost | Zero | Per-call LLM cost |
| Speed | Fast | 30-90 seconds for 8 files |
| Maintainability | Complex regex/heuristic code | Simple prompt engineering |

The current "works without LLM" property is not a feature — it is a false promise. Producing garbage output silently is worse than failing loudly. The proposed system fails loudly when LLM is unavailable, which is the correct behavior.

In MCP mode (the primary deployment target), `ctx.sample()` is always available at zero additional cost to the user. The LLM dependency is therefore not a practical barrier.

# **APPENDIX: Implementation Backlog: Phase 1 (Core Synthesis & Transactional Safety)**

Excellent. Breaking this down into structured Jira tickets will ensure the engineering team executes the Red Team constraints exactly as designed, without losing the critical architectural nuances.

Here is the complete backlog for **Phase 1: Core Synthesis & Transactional Safety (Weeks 1-2)**. You can copy and paste these directly into your issue tracker.

---

### **🟦 EPIC: HiveForge Steering File Generation (Core LLM Synthesis)**

**Description:** Refactor the HiveForge steering file generation from a regex-based `TemplatePopulator` fallback system to a strict LLM-primary synthesis engine. This epic focuses on creating a safe, transactional generation pipeline that avoids context window bloat and explicitly prevents hallucinated files from being written to the workspace.

---

### **🟩 STORY 1.1: Upgrade CodeAnalyzer to output structured facts & real-time CLI progress**

**Type:** Feature / Enhancement **Description:** The `CodeAnalyzer` currently outputs prose summaries, which are poorly suited for strict LLM prompt injection. We need to refactor it to output a rigid `CodeAnalysisFacts` dataclass. Additionally, because deep directory traversals can take 2-5 minutes, we must add real-time CLI feedback to prevent users from thinking the tool has frozen.

**Acceptance Criteria:**

- [ ] `CodeAnalyzer.to_summary()` is removed and replaced with a `CodeAnalysisFacts` dataclass (JSON-serializable).  
- [ ] The returned facts strictly contain keys for: dependencies, architecture\_pattern, backend\_framework, database, and conventions.  
- [ ] A real-time console progress indicator (e.g., `Scanning directory X of Y...` or a progress bar) is implemented and displays during the `hiveforge steering init` command.

**Technical Notes:**

* Do not change the underlying AST or regex parsing logic; only change the output format and the CLI wrapper.

---

### **🟩 STORY 1.2: Implement ContextAssembler with strict Token Budgeting**

**Type:** Backend Task **Description:** KIRO's internal `#codebase` index is closed and not accessible via MCP. Therefore, we must build our own `ContextAssembler` to prevent LLM context window bloat. The assembler must enforce a strict 8,000 token limit per template by filtering input documents and passing cross-file context safely.

**Acceptance Criteria:**

- [ ] Create `ContextAssembler` class that accepts parsed source docs, `CodeAnalysisFacts`, and previously generated templates.  
        
- [ ] Implement keyword-based relevance filtering to extract only template-relevant paragraphs from source PDFs/Markdown.  
        
- [ ] Enforce the following hard token limits per generation:  
        
* Source docs: Max 4,000 tokens  
    
* Code facts: Max 2,000 tokens  
    
* Previously generated files / Cross-file context: Max 1,000 tokens  
    
- [ ] Cross-file context must be implemented as *rolling summaries* or extracted fields, NOT raw file text appends.

---

### **🟩 STORY 1.3: Implement SteeringFileGenerator with In-Memory Transactional Drafting**

**Type:** Core Feature **Description:** To prevent the LLM from leaving partially generated or corrupted steering files in the user's workspace upon failure, the generation pipeline must be completely atomic (all 8 files succeed, or 0 files are written).

**Acceptance Criteria:**

- [ ] Create `SteeringFileGenerator` class.  
- [ ] Update the `PromptBuilder` signature to accept the `GenerationContext` from the `ContextAssembler`.  
- [ ] Generator must loop through the 8 templates sequentially, holding the generated markdown in an in-memory dictionary (`draft_files`).  
- [ ] Implement `_atomic_write_all(draft_files)`. Disk writes *only* occur after all 8 files are successfully generated and validated.  
- [ ] If the pipeline is aborted at file \#5, the system exits cleanly without modifying the user's file system.

---

### **🟩 STORY 1.4: Implement Deterministic Hallucination Detection & Fallback Integrity**

**Type:** Security / Validation **Description:** Probabilistic LLM outputs must be gated by deterministic code. We must validate the LLM's generated markdown against the ground-truth `CodeAnalysisFacts` before allowing the transaction to commit.

**Acceptance Criteria:**

- [ ] Implement `_validate_against_facts(template_name, content)` inside the `SteeringFileGenerator`.  
- [ ] Add regex/string-matching rules for critical infrastructure fields (e.g., if `CodeAnalysisFacts` says "PostgreSQL", but the LLM output for `tech-stack.md` says "MySQL", throw a validation error).  
- [ ] **Enforce Retry vs. Rollback Hierarchy:**  
* If the LLM returns an empty response or malformed Markdown \-\> Trigger `RetryWithSimplifiedPrompt`.  
* If the LLM triggers a validation error from `_validate_against_facts` \-\> Bypass retries and immediately abort the entire transaction.

**Technical Notes:**

* The system must explicitly fail loudly. Do not attempt to auto-correct the LLM's hallucination. Silence over hallucination.