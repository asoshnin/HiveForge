# **2026-02-13\_Methodology for Agentic Coding: The Virtual Company Framework's Universal Roles and Operational Loop**

# **Part 1: The Core Framework (Rules of Engagement)**

## **1.1 Universal Roles & Constraints**

The "Virtual Company" framework divides intelligence into three distinct roles. This separation prevents context pollution and hallucination. No single agent holds the entire project state in its working memory. Instead, agents operate within strict boundaries, handing off structured artifacts.

### **Role 1: The Orchestrator (Architect)**

The Orchestrator acts as the system's central nervous system. It possesses the sole authority to define *what* to build, but it lacks the permission to build it. Its primary function is state management and architectural integrity.

**Core Responsibilities:**

* **State Management:** Owns the `swarm_state.md` file. It updates the project status, current phase, and active tasks.  
* **Requirement Extraction:** Conducts "Socratic Lock-In" sessions to convert vague user intent into concrete specifications.  
* **Steering:** Creates and maintains global mandate files (Vision, Tech Stack, Conventions) in `.kiro/steering/`.  
* **Specification:** Translates requirements into technical specification documents (`docs/reference/`) for Builders.  
* **Gatekeeping:** interprets Red Team findings and decides when to trigger a "Human Gate" (stopping for manual approval).

**Input Dependencies:**

* Raw user input (Concepts, PRDs, or Codebases).  
* Red Team "Findings Logs."  
* Builder "Task Status" updates.

**Output Artifacts:**

* `swarm_state.md` (The Single Source of Truth).  
* Steering Files (`.kiro/steering/*.md`).  
* Feature Specifications (`docs/reference/*.md`).  
* Work Plans (`docs/reference/WORK_PLAN.md`).

**❌ Hard Constraints (The "NEVER" List):**

1. **NEVER write production code.** The Orchestrator must not write functions, classes, or business logic. It writes only Markdown specifications and plans.  
2. **NEVER modify Builder code.** If code requires changes, the Orchestrator must issue a new task or specification.  
3. **NEVER ignore Red Team findings.** It cannot dismiss critical or high-severity findings without documenting the accepted risk.  
4. **NEVER proceed while blocked.** If `swarm_state.md` indicates a "blocked" status, the Orchestrator must resolve the blocker before assigning new tasks.

---

### **Role 2: The Builder (Implementer)**

The Builder is the execution engine. It operates in short, focused bursts to convert specifications into functioning software. It does not question the architectural "why"; it solves the technical "how."

**Core Responsibilities:**

* **Implementation:** Writes production code in `src/` (or equivalent) based strictly on the active specification.  
* **Testing:** Adopts a "Test-First" approach, creating unit and integration tests in `tests/` before marking a task complete.  
* **Documentation:** Adds docstrings and comments explaining complex logic decisions.  
* **Self-Correction:** Runs local tests and linters. It must fix its own syntax errors and test failures before reporting success.

**Input Dependencies:**

* Active Task (assigned via `swarm_state.md`).  
* Active Specification (referenced in the task).  
* Technical Stack and Conventions (from Steering Files).

**Output Artifacts:**

* Production Source Code.  
* Test Suites (`tests/`).  
* API Documentation.  
* Task Status updates (Success/Failure flags only).

**❌ Hard Constraints (The "NEVER" List):**

1. **NEVER change Steering Files.** The Builder cannot alter architectural rules or conventions.  
2. **NEVER improvise logic.** It must strictly follow the specification. If the spec is ambiguous, the Builder must report a blocker, not guess.  
3. **NEVER skip tests.** Every feature implementation must include corresponding tests.  
4. **NEVER hide technical debt.** "Temporary" hacks must be explicitly documented with `TODO` comments and reported to the Orchestrator.  
5. **NEVER work without an active spec.** The Builder initiates action only when `swarm_state.md` assigns a specific, documented task.

---

### **Role 3: The Red Team (Auditor)**

The Red Team operates as an adversarial critic. It does not build or fix; it attempts to break the system. Its goal is to prove that the Orchestrator's plans are flawed or the Builder's code is insecure.

**Core Responsibilities:**

* **Requirements Validation:** challenges the Orchestrator’s specifications for completeness and clarity during the planning phase.  
* **Security Audit:** Scans code for vulnerabilities (e.g., injection, data leaks, broken auth).  
* **Architectural Audit:** Checks for "drift" where implementation deviates from the design in Steering Files.  
* **Performance Audit:** Identifies bottlenecks, inefficiencies, and resource leaks.  
* **Compliance Check:** Verifies that code matches the definition of done and coding conventions.

**Input Dependencies:**

* Current Lifecycle Stage (determines the audit focus).  
* Draft Specifications (for validation).  
* Implemented Code and Tests (for verification).

**Output Artifacts:**

* `red_team_findings` section in `swarm_state.md`.  
* Detailed vulnerability reports.  
* Remediation recommendations (text guidance, not code).

**❌ Hard Constraints (The "NEVER" List):**

1. **NEVER write code or fixes.** The Red Team identifies problems; it does not solve them.  
2. **NEVER approve quality.** Its role is negative validation (finding faults). It does not issue "certificates of quality."  
3. **NEVER ignore a finding.** Even minor issues must be logged.  
4. **NEVER work without context.** It must anchor every finding to specific violations of the Steering Files or Specifications.

### **🔴 Red Team Audit**

5. **Expansion Check:** Defined the four-tier "Cascade of Truth" using specific file paths and priority rules from Source. Included the exact "Context Injection Protocol" prompt template from Source. Detailed the "Change Management Protocol" steps from Source.  
6. **Jargon Scrubbed:** Removed "underscore," "pivotal," "leverage," "paradigm," and "delve." Replaced "ensure alignment" with "enforce consistency."  
7. **Continuity:** Connects the roles defined in 1.1 to the information structure they must obey.

## **1.2 The Truth Hierarchy**

```
## 1.2 The Truth Hierarchy

Agents hallucinate when context is ambiguous. To prevent this, the Virtual Company framework enforces a strict "Cascade of Truth." This hierarchy dictates which information takes precedence when contradictions arise. It resolves conflicts between long-term rules (Steering) and short-term instructions (Chat).

### The Cascade of Truth

Data flows down. Constraints flow up. An agent must always defer to the higher tier.

**Tier 1: Steering Files (Global Mandates)**
*   **Priority:** Absolute.
*   **Location:** `.kiro/steering/*.md`
*   **Function:** These files define the immutable laws of the project. They persist across all tasks and phases.
*   **Components:**
    *   `project-vision.md`: The core problem and success metrics.
    *   `tech-stack.md`: Approved languages, frameworks, and libraries.
    *   `conventions.md`: Coding styles, naming rules, and patterns.
    *   `architecture.md`: System design and component boundaries.
    *   `definitions.md`: Domain terminology.
*   **Rule:** If a Specification (Tier 2) contradicts a Steering File, the Steering File wins. The Specification is wrong.

**Tier 2: Specifications (Feature Specs)**
*   **Priority:** High.
*   **Location:** `docs/reference/*.md`
*   **Function:** These files define *what* to build. They are static documents created by the Orchestrator.
*   **Components:**
    *   `feature-*.md`: Detailed requirements for specific modules.
    *   `WORK_PLAN.md`: Sequence of execution.
    *   `api-*.md`: Interface contracts.
*   **Rule:** If the Chat Context (Tier 4) contradicts a Specification, the Specification wins. The agent must ignore the chat instruction.

**Tier 3: Swarm State (Operational Reality)**
*   **Priority:** Operational.
*   **Location:** `swarm_state.md`
*   **Function:** This file tracks the dynamic "now." It records the current phase, active task, and recent Red Team findings.
*   **Rule:** This file reflects reality but does not set architectural rules. It is the sync point between agents.

**Tier 4: Chat Context (Ephemeral)**
*   **Priority:** Lowest.
*   **Location:** The active chat session / working memory.
*   **Function:** Temporary storage for the current turn of conversation.
*   **Rule:** Information here is volatile. If it is not saved to Tier 1, 2, or 3, it does not exist. Agents must treat chat instructions as suggestions until verified against higher tiers.

---

### Native Steering Configuration

Instead of manually injecting context into every prompt, we utilize Kiro's native **Steering Engine**. This ensures the Truth Hierarchy is enforced at the system level, reducing token costs and latency.

**Configuration Strategy:**
Every file in `.kiro/steering/` must contain YAML front matter defining its inclusion rule.

**1. Global Mandates (Tier 1):**
Files like `project-vision.md` and `tech-stack.md` are set to `inclusion: always`. They are invisible to the agent but present in the context window 100% of the time.

**2. Dynamic Specifications (Tier 2):**
Feature specifications use `inclusion: auto` or `inclusion: manual`. The Orchestrator references them by name (e.g., `#auth-spec`), and Kiro loads them instantly.

**Conflict Resolution:**
Kiro's internal logic prioritizes `.kiro/steering/*` (System Context) over user chat messages, automatically enforcing the hierarchy without script intervention.
```

---

### **Change Management Protocol**

When a higher tier changes (e.g., the Vision changes), lower tiers become "stale." Agents operating on stale context generate waste.

**The Invalidation Loop:**

1. **Detection:** An agent or human identifies that a Steering File or Specification is outdated.  
2. **Signal:** The agent updates `swarm_state.md` → `error_log` with the tag `[CONTEXT_STALE]`.  
3. **Stop:** The Orchestrator pauses all active Builders.  
4. **Update:** The Orchestrator updates the Tier 1 or Tier 2 file. It increments the file version.  
5. **Invalidate:** The Orchestrator issues a `RELOAD_CONTEXT` command. This forces all agents to discard their current chat session and reload the Truth Hierarchy.  
6. **Verify:** The Red Team checks that the new code aligns with the updated rules.

## **1.3 The Universal State Schema**

Agents have short memories. To maintain continuity over days or weeks, the Virtual Company relies on a persistent state file: `swarm_state.md`. This file acts as the project's memory bank. It is the Single Source of Truth (SSoT) for the current operational reality.

Every agent must read this file before acting and update it after finishing a task.

### **The Structure of `swarm_state.md`**

The file follows a strict Markdown schema to ensure both human readability and machine parsing. It contains eight mandatory sections.

**1\. Project Identity & Context**

7. **Function:** Defines the project's DNA and adaptive parameters.  
8. **Critical Fields:**  
   * `Input Type`: Categorizes the starting point (Concept, Spec, Code, or Hybrid). This triggers the specific workflow strategy.  
   * `Lifecycle Stage`: Defines the project maturity (Greenfield, Build/Extend, Mature/Audit). This dictates the Red Team's focus.  
   * `Current Phase`: Tracks the macro-step in the operational loop (e.g., "Socratic Lock-In" or "Implementation").  
   * `Definition of Done`: The explicit criteria required to close the phase.

**2\. Clarified Vision (Lock-In Output)**

9. **Function:** Anchors the project to the user's original intent. It prevents scope creep.  
10. **Critical Fields:**  
    * `Core Problem Statement`: The specific user pain point being solved.  
    * `Success Metrics`: Quantifiable targets (e.g., "Response time \< 200ms").  
    * `Prioritized Requirements`: A ranked list of Must-Have (P0) vs. Nice-to-Have (P2) features.  
    * `Constraints`: Hard limits on budget, time, or technology.

**3\. Architecture & Technical Context**

11. **Function:** Establishes the technical boundaries.  
12. **Critical Fields:**  
    * `Tech Stack`: Approved languages, frameworks, and libraries.  
    * `Folder Structure`: The expected file layout.  
    * `Coding Conventions`: Style guides and naming rules.  
    * `Architecture Decisions`: A log of major technical choices and their rationale.

**4\. Team & Task Management**

13. **Function:** Manages the "Check-out/Check-in" process for agents.  
14. **Critical Fields:**  
    * `Active Task`: The single unit of work currently in progress, assigned to specific agents.  
    * `Task Queue`: The backlog of pending work.  
    * `Completed Tasks`: A history log of finished items.

**5\. Red Team Audit Status**

15. **Function:** Visualizes technical debt and risk.  
16. **Critical Fields:**  
    * `Current Focus`: The specific attack vector active for the current phase (e.g., "Security" or "Requirements").  
    * `Findings Log`: A structured list of defects. Each finding includes Severity (Critical/High), Description, and Status.  
    * `Audit Status`: The overall health signal (e.g., "Blocked by Critical Finding").

**6\. Error Handling & Recovery**

17. **Function:** Provides resilience against crashes or logic loops.  
18. **Critical Fields:**  
    * `Error Log`: A record of recent failures and their types.  
    * `Checkpoint History`: Pointers to the last known good state (git tags).  
    * `Human Gates Pending`: A list of decisions requiring manual user approval.

**7\. File References**

19. **Function:** Acts as an index for the Truth Hierarchy.  
20. **Critical Fields:**  
    * Links to Tier 1 Steering Files (`.kiro/steering/`).  
    * Links to Tier 2 Specifications (`docs/reference/`).  
    * Links to Tier 3 Code and Test outputs.

**8\. Metadata**

21. **Function:** System-level tracking.  
22. **Critical Fields:**  
    * `State Version`: Semantic versioning of the state file itself.  
    * `Blockers`: A high-level flag for stopping work.

**Note:** For the exact Markdown syntax and field definitions, refer to the **Universal State Template** in **Section 5.2**.

# **Part 2: Adaptive Logic (The Brain)**

## **2.1 Input Classification**

The Orchestrator must classify every project before assigning tasks. This classification determines the intensity of the "Socratic Lock-In," the focus of the Red Team, and the sequence of the workflow.

There are two dimensions to this classification: **Input Type** (What do we have?) and **Lifecycle Stage** (Where are we?).

### **The 4 Input Types (Source Logic)**

The Input Type defines the starting material. It dictates the "Socratic Strategy."

**Type A: Concept / Idea**

* **Definition:** Raw user intent. The user has a problem or a vision but lacks formal requirements, technical specs, or code.  
* **Indicators:** "I have an idea for...", "Napkin sketch", "What if we built...".  
* **Missing:** Formal requirements, architecture, acceptance criteria.

**Type B: Specification / PRD**

* **Definition:** Structured requirements exist. The user provides a Product Requirements Document (PRD), wireframes, or detailed user stories.  
* **Indicators:** "Here is the spec", "Follow this document", "Implement this RFC".  
* **Missing:** Implementation code, test suites.

**Type C: Codebase**

* **Definition:** Source code exists. The user provides a repository for refactoring, auditing, or extension.  
* **Indicators:** "Refactor this legacy app", "Audit this repo", "Fix this bug".  
* **Missing:** Often lacks current documentation, tests, or clear intent for the original logic.

**Type D: Hybrid**

* **Definition:** A mix of legacy code and new requirements. The most common enterprise scenario (e.g., "Add a subscription module to this existing monolith").  
* **Indicators:** "Integrate X into Y", "Migrate this service to Go".  
* **Missing:** Clear boundaries between old and new systems.

---

### **The 4 Lifecycle Stages (Maturity Logic)**

The Lifecycle Stage defines the project's maturity. It dictates the "Red Team Focus."

**Stage 1: Green-Field**

* **Definition:** Zero production code exists. The project is in the design or prototyping phase.  
* **Focus:** Getting the foundation right (Architecture & Vision).

**Stage 2: Build / Extend**

* **Definition:** Fundamental code exists and is stable. The team is actively building features or expanding capabilities.  
* **Focus:** Velocity and integration (preventing regressions).

**Stage 3: Mature / Audit**

* **Definition:** The codebase is feature-complete or in production. The goal is optimization, security, or stability.  
* **Focus:** Hardening and protection (Security & Performance).

**Stage 4: Mixed**

* **Definition:** The project operates in multiple stages simultaneously (e.g., maintaining a legacy backend while building a greenfield frontend).  
* **Focus:** Coordination and consistency.

---

### **Adaptation Lookup Matrix**

The Orchestrator uses these tables to configure the workflow.

#### ***Table 2.1.A: Input Type Adaptation***

| Input Type | Risk Profile | Workflow Adaptation |
| :---- | :---- | :---- |
| **Concept** | **High Ambiguity.** Risk of solving the wrong problem or scope creep. | **Intensive Lock-In.** Spend \~40-50% of time on Socratic questions. Focus on problem validation and defining "Success Metrics." |
| **Spec** | **Gap Risk.** Risk of conflicting requirements or ignored edge cases. | **Gap Analysis.** Focused Lock-In (\~20% time). Red Team validates the Spec *before* code generation starts. |
| **Codebase** | **Legacy Risk.** Risk of breaking changes or misunderstanding "Chesterton's Fence" (intent). | **Archaeology First.** Skip standard Lock-In. Run "Code Analysis" phase to reverse-engineer intent and document current behavior. |
| **Hybrid** | **Integration Risk.** Risk of interface mismatch between old and new systems. | **Reconciliation.** "Interface-First" strategy. Define contracts between old and new components before implementation. |

#### ***Table 2.1.B: Lifecycle Stage Adaptation***

| Lifecycle Stage | Risk Profile | Red Team Primary Focus |
| :---- | :---- | :---- |
| **Green-Field** | **Feasibility Risk.** Selecting the wrong stack or over-engineering the solution. | **Requirements Clarity.** Attack the assumptions. "Is this problem real? Will this stack scale?" |
| **Build/Extend** | **Drift Risk.** New features slowly breaking the original architectural constraints. | **Architectural Impact.** "Does this new feature violate the rules in `architecture.md`?" |
| **Mature/Audit** | **Vulnerability Risk.** Hidden security holes or performance bottlenecks in production. | **Security & Performance.** OWASP Top 10 scans, load testing, and edge-case fuzzing. |
| **Mixed** | **Coordination Risk.** Changes in one stream breaking a parallel stream. | **Cross-Stream Impact.** "Did the backend change break the frontend build?" |

## **2.2 Decision Protocols**

The Orchestrator does not guess; it follows a deterministic logic tree. This section defines the exact algorithm used to configure the project workflow based on the `Input Type` and `Lifecycle Stage` defined in Section 2.1. This logic ensures that a "Concept" project gets more planning time, while a "Code Audit" project focuses immediately on security scanning.

### **The Orchestrator Decision Engine**

The following Python pseudocode represents the core logic for the `swarm_runner.py` script. It automates five critical project decisions:

1. **Socratic Intensity:** How many questions to ask before building.  
2. **Phase Sequence:** The order of operations (e.g., skip design for audits).  
3. **Red Team Configuration:** What the auditors should attack.  
4. **Human Gates:** Where to stop for mandatory approval.  
5. **Builder Composition:** Which specialist agents to spawn.

```py
def determine_workflow_strategy(input_type, lifecycle_stage, current_context):
    """
    Returns: WorkflowConfiguration object based on project parameters.
    """

    # === DECISION 1: Socratic Lock-In Intensity ===
    # Determines how much time to spend clarifying requirements
    if input_type == "concept":
        socratic_config = {
            "duration_estimate": "40-50% of total project time",
            "focus_areas": ["problem_validation", "user_personas", "success_metrics", 
                            "constraints_extraction", "scope_boundaries"],
            "exit_criteria": "Clear vision document with acceptance criteria",
            "red_team_focus": ["assumption_validation", "feasibility_challenges", 
                               "missing_constraints"]
        }
    elif input_type == "spec":
        socratic_config = {
            "duration_estimate": "15-20% of total project time",
            "focus_areas": ["gap_analysis", "ambiguity_resolution", "edge_case_identification"],
            "exit_criteria": "Validated spec with no critical ambiguities",
            "red_team_focus": ["spec_completeness", "contradiction_detection"]
        }
    elif input_type == "code":
        socratic_config = {
            "duration_estimate": "5-10% of total project time (or skip)",
            "focus_areas": ["intent_extraction", "reverse_engineering_goals"],
            "exit_criteria": "Understood current state and user intent for changes",
            "red_team_focus": ["code_archaeology_accuracy", "hidden_dependencies"]
        }
    else:  # hybrid
        socratic_config = {
            "duration_estimate": "20-30% of total project time",
            "focus_areas": ["reconciliation", "scope_definition", "integration_boundaries"],
            "exit_criteria": "Unified plan resolving spec-code discrepancies",
            "red_team_focus": ["integration_risks", "consistency_gaps"]
        }

    # === DECISION 2: Phase Sequence ===
    # Determines the order of operations
    if lifecycle_stage == "greenfield":
        phase_sequence = [
            "input_analysis",
            "socratic_lockin",
            "architecture_design",
            "implementation",
            "red_team_audit",
            "refinement",
            "ready_for_deploy"
        ]
        parallel_workstreams = 1
    elif lifecycle_stage == "build_extend":
        phase_sequence = [
            "current_state_analysis",
            "architecture_impact_assessment",
            "implementation",  # Can have multiple parallel features
            "integration_testing",
            "red_team_audit",
            "regression_testing",
            "ready_for_deploy"
        ]
        parallel_workstreams = "multiple_features"
    elif lifecycle_stage == "mature_audit":
        phase_sequence = [
            "code_analysis",
            "security_audit",
            "performance_audit",
            "fix_implementation",
            "re_validation",
            "ready_for_deploy"
        ]
        parallel_workstreams = 1  # Sequential for thoroughness
    else:  # mixed
        phase_sequence = [
            "stream_identification",
            "parallel_execution",  # Multiple streams with different phases
            "integration_testing",
            "system_wide_audit",
            "ready_for_deploy"
        ]
        parallel_workstreams = "mixed_phases"

    # === DECISION 3: Red Team Configuration ===
    # Configures the auditor's primary attack vectors
    red_team_config = get_red_team_config(lifecycle_stage)

    # === DECISION 4: Human Gates Placement ===
    # Defines where execution MUST pause for human approval
    human_gates = []
    if lifecycle_stage in ["greenfield", "build_extend"]:
        human_gates.extend([
            "post_architecture_design",
            "pre_production_deploy"
        ])
    
    if input_type in ["code", "hybrid"]:
        human_gates.append("before_breaking_changes")
        
    if lifecycle_stage == "mature_audit":
        human_gates.extend([
            "post_security_audit",
            "if_critical_findings"
        ])

    # === DECISION 5: Builder Swarm Composition ===
    # Defines the necessary agent skills
    if lifecycle_stage == "greenfield":
        builders = ["full_stack_generalist"]
    elif lifecycle_stage == "build_extend":
        builders = ["specialist_per_feature"]
    elif lifecycle_stage == "mature_audit":
        builders = ["security_specialist", "performance_specialist"]
    else:  # mixed
        builders = ["coordinator", "specialist_stream_1", "specialist_stream_2"]

    return WorkflowConfiguration(
        socratic=socratic_config,
        phases=phase_sequence,
        red_team=red_team_config,
        human_gates=human_gates,
        builders=builders,
        parallel_workstreams=parallel_workstreams
    )

def get_red_team_config(lifecycle_stage):
    """
    Maps lifecycle stage to audit priorities.
    """
    configs = {
        "greenfield": {
            "primary_focus": "requirements_clarity",
            "secondary_focus": "architectural_feasibility",
            "tertiary_focus": "assumption_validation",
            "audit_points": ["post_socratic", "post_architecture", "per_feature"]
        },
        "build_extend": {
            "primary_focus": "architectural_impact",
            "secondary_focus": "technical_debt",
            "tertiary_focus": "integration_points",
            "audit_points": ["per_feature", "pre_integration", "final"]
        },
        "mature_audit": {
            "primary_focus": "security_vulnerabilities",
            "secondary_focus": "performance_bottlenecks",
            "tertiary_focus": "edge_cases",
            "audit_points": ["security", "performance", "comprehensive"]
        },
        "mixed": {
            "primary_focus": "cross_stream_impact",
            "secondary_focus": "coordination_risk",
            "tertiary_focus": "consistency",
            "audit_points": ["per_stream", "integration", "final"]
        }
    }
    return configs[lifecycle_stage]
```

## **2.3 Socratic Lock-In Protocols**

The Orchestrator never builds on assumptions. Before generating a single line of code or specification, it must "lock in" the requirements using a Socratic interview. The nature of this interview changes based on the **Input Type** defined in Section 2.1.

There are four distinct protocols. The Orchestrator selects one and executes it sequentially.

### **Variant A: The Concept Protocol (for Green-Field/Ideas)**

**Trigger:** Input is a raw idea, napkin sketch, or high-level wish. **Goal:** Convert vague intent into a clear Problem Statement and set of Constraints. **Duration:** High Intensity (40-50% of planning time).

* **Round 1: Problem & User Identification**  
    
  1. "What specific problem does this solve? Describe it to someone unfamiliar with the domain."  
  2. "Who experiences this problem most acutely? What do they do right now to cope?"  
  3. "How do you know this is a real problem? Do you have data, observations, or specific user stories?"


* **Round 2: Solution & Value**  
    
  1. "If this solution works perfectly, how does the user's life change in 30 days?"  
  2. "What is the user willing to give up (time, money, data) to solve this?"  
  3. "What existing solutions (even manual workarounds) do people use now? Why are they insufficient?"


* **Round 3: Boundaries & Constraints**  
    
  1. "What is explicitly **OUT** of scope? What features are we intentionally excluding?"  
  2. "What hard constraints exist? (Budget, strict deadlines, specific technologies, compliance rules?)"  
  3. "What part of the user's current process must remain unchanged?"


* **Round 4: Success & Failure Metrics**  
    
  1. "How will we objectively measure success? What specific number must change?"  
  2. "Under what conditions would this project be considered a failure, even if the code works?"  
  3. "What risks could kill this project in the first 3 months? How do we spot them early?"

---

### **Variant B: The Spec Protocol (for PRDs/Requirements)**

**Trigger:** Input is a structured document (PRD, RFC, or list of requirements). **Goal:** Find gaps, ambiguities, and edge cases in the text. **Duration:** Medium Intensity (15-20% of planning time).

* **Round 1: Completeness & Clarity**  
    
  1. "For requirement X, what happens if the prerequisite condition Y is *not* met?"  
  2. "The term 'Z' is used in multiple places. Does it mean exactly the same thing everywhere? Please define it."  
  3. "Which requirement is the hardest to test? How exactly will we verify it?"


* **Round 2: Edge Cases & Stress**  
    
  1. "What happens when Action A and Action B occur simultaneously (concurrency)?"  
  2. "How does the system behave if the external service takes 30 seconds to respond? 5 minutes?"  
  3. "What data is considered 'invalid,' and how often does it occur in reality?"


* **Round 3: Dependencies & Integrations**  
    
  1. "This spec assumes System Y exists. What if System Y changes its API or goes down?"  
  2. "What changes in this document would require rewriting parts we have already built?"  
  3. "Are there implicit business process dependencies not written here?"


* **Round 4: Priorities & Trade-offs**  
    
  1. "If we must choose between Security and Speed for this feature, which wins?"  
  2. "Which requirement could be cut without losing the core value of the product?"  
  3. "What is the impact if we launch without Feature X?"

---

### **Variant C: The Code Protocol (for Audits/Refactoring)**

**Trigger:** Input is an existing codebase. **Goal:** Reverse-engineer the original intent and identify "Chesterton's Fence" (why things are the way they are). **Duration:** Low Intensity (5-10% of planning time) or skipped in favor of automated analysis.

* **Round 1: Code Archaeology**  
    
  1. "Looking at the folder structure, what architecture were the original authors trying to implement?"  
  2. "What `TODO` comments or disabled tests indicate unfinished work?"  
  3. "Which files have changed most frequently in the git history? Why are they unstable?"


* **Round 2: Functionality & Intent**  
    
  1. "What business problem does this specific module solve? Explain it without using technical terms."  
  2. "What do the 'magic numbers' or hardcoded strings represent? Why were these values chosen?"  
  3. "What invariants does the code maintain? (What must always be true?)"


* **Round 3: Quality & Risk**  
    
  1. "Which parts of the system have zero test coverage? What are we running on faith?"  
  2. "Are there cyclic dependencies between modules?"  
  3. "Which external dependencies are outdated or have known vulnerabilities?"


* **Round 4: Change Intent**  
    
  1. "What exactly needs to change and why? What problem does the change solve?"  
  2. "What must absolutely **NOT** be changed (Critical Paths)?"  
  3. "How will we prove that our changes didn't break existing functionality?"

---

### **Variant D: The Hybrid Protocol (for Integration/Modernization)**

**Trigger:** Input is a mix of old code and new requirements (e.g., "Add feature X to Legacy App Y"). **Goal:** Reconcile the conflict between the ideal spec and the messy reality of the code. **Duration:** Medium-High Intensity (20-30% of planning time).

* **Round 1: Mapping & Conflict**  
    
  1. "Where does the existing code already implement parts of the new requirements?"  
  2. "Where does the current code directly contradict the new requirements?"  
  3. "Which new requirements will force a breaking change to the existing API?"


* **Round 2: Boundaries & Interfaces**  
    
  1. "Where exactly do we draw the line between 'keep old' and 'build new'?"  
  2. "What data must flow from the old system to the new one? In what format?"  
  3. "How do we prevent data conflicts between the old and new sources of truth?"


* **Round 3: Migration Strategy**  
    
  1. "How do we transition from the current state to the target state without downtime?"  
  2. "If the new implementation performs worse than the old one, what is the rollback plan?"  
  3. "What tests must pass on *both* systems to ensure compatibility?"


* **Round 4: Priorities & Sequence**  
    
  1. "Do we refactor the old code first, or build the new feature first? Why?"  
  2. "If resources run out, do we prefer a full rewrite of Module X or a patch on Module Y?"  
  3. "What is the smallest step that delivers value (MVP within the hybrid project)?"

## **2.4 Red Team Focus Matrix**

The Red Team does not audit randomly. Its behavior is strictly governed by the project's **Lifecycle Stage** (defined in Section 2.1). The Orchestrator sets the stage in `swarm_state.md`, and the Red Team applies the corresponding audit profile.

This matrix dictates exactly what the Red Team looks for and when it must stop the line.

| Lifecycle Stage | Primary Focus (The "Must Haves") | Secondary Focus (The "Should Haves") | Tertiary Focus (The "Nice to Haves") | Triggers for Escalation (Stop Work) |
| :---- | :---- | :---- | :---- | :---- |
| **Green-Field** \*(New Project)\* | **Requirements Clarity** Attacks assumptions: "Is the problem real? Is the solution defined?" | **Architectural Feasibility** Checks limits: "Will this stack handle the projected load?" | **Assumption Validation** Stress tests logic: "What if the market or tech changes?" | • Unclear success criteria • Contradictory constraints • Unrealistic deadlines • Missing "Definition of Done" |
| **Build/Extend** \*(Active Dev)\* | **Architectural Impact** Checks consistency: "Does this new feature break the existing design rules?" | **Technical Debt** Checks quality: "Are we taking shortcuts that will hurt us later?" | **Integration Points** Checks boundaries: "How does the new code talk to the old code?" | • **Architectural Drift** (violating `architecture.md`) • Missing tests for new code • Cyclic dependencies • API contract violations |
| **Mature/Audit** \*(Production)\* | **Security Vulnerabilities** Attacks vectors: Injection, XSS, Broken Auth, Data Leaks. | **Performance** Checks resources: Bottlenecks, N+1 queries, memory leaks. | **Edge Cases** Checks resilience: "What happens on null input, timeouts, or disconnects?" | • **Critical/High Severity Findings** • Missing input validation • Hardcoded secrets • PII/Data exposure |
| **Mixed** \*(Hybrid)\* | **Cross-Stream Impact** Checks collision: "Did changes in Stream A break Stream B?" | **Coordination Risk** Checks conflict: "Are parallel tasks modifying the same file?" | **Consistency** Checks style: "Are both streams using the same patterns?" | • Merge conflicts in architecture files • Incompatible interface changes • Loss of context between streams |

### **Dynamic Focusing Rule**

The Red Team agent reads `swarm_state.md` before every task.

1. It identifies the `lifecycle_stage`.  
2. It selects the corresponding row from the matrix above.  
3. It generates its audit checklist based **only** on that row's priorities.  
4. If a **Trigger for Escalation** is found, the Red Team immediately flags the task as `BLOCKED` and requests a Human Gate.

# **Part 3: Operational Workflow (The Loop)**

## **3.1 The Universal Operational Loop**

The Virtual Company does not work in a chaotic stream of chat messages. It follows a strict, linear operational loop. This loop forces every project—whether a one-hour script or a three-month platform—through seven distinct gates.

The Orchestrator drives this loop. It moves the project from one phase to the next only when the `swarm_state.md` criteria are met.

### **The 7 Linear Phases**

**1\. Input Detection & Classification**

* **Action:** The Orchestrator receives the raw user prompt.  
* **Output:** It updates `swarm_state.md` with the `Input Type` (Concept, Spec, Code, Hybrid) and `Lifecycle Stage`. This configuration determines the intensity of the next steps.

**2\. Socratic Lock-In**

* **Action:** The Orchestrator interviews the user to clarify intent. It uses the specific "Protocol Variant" (A, B, C, or D) assigned in Phase 1\.  
* **Output:** A "Clarified Vision" document and a prioritized list of requirements in `swarm_state.md`.  
* **Stop Condition:** The user confirms, "Yes, that is exactly what I want."

**3\. Architecture Design (or Analysis)**

* **Action:**  
  * *Green-Field:* The Orchestrator creates the Tier 1 Steering Files (`tech-stack.md`, `architecture.md`).  
  * *Legacy:* The Orchestrator maps the existing system constraints.  
* **Output:** The technical blueprint. No code is written yet.

**4\. Implementation (The Builder Loop)**

* **Action:** The Orchestrator breaks the plan into atomic tasks. Builders execute them one by one.  
* **Output:** Production source code and passing tests.  
* **Constraint:** Builders work in isolation on specific features; they do not see the whole picture.

**5\. Red Team Audit (System Level)**

* **Action:** The Red Team performs a comprehensive scan of the completed work against the `Red Team Focus Matrix` (Section 2.4).  
* **Output:** A list of findings categorized by severity (Critical, High, Medium, Low).

**6\. Refinement**

* **Action:** The Orchestrator pauses new feature work. Builders switch to "Fix Mode" to resolve Critical and High findings.  
* **Output:** A clean codebase with no blocking issues.

**7\. Deployment & Hand-off**

* **Action:** The system hits a "Human Gate." The user approves the final result.  
* **Output:** Deployment to production and update of `docs/`.

---

### **The "Recursive Red Team" Principle**

In traditional workflows, audits happen at the end (Phase 5). In the Virtual Company, this is too late. The Red Team operates recursively. It attacks the project at *every* stage of the loop to prevent "compounding errors."

**The 3 Audit Injection Points:**

1. **Check \#1: Requirements Validation (Post-Phase 2\)**  
     
   * *Timing:* Immediately after Socratic Lock-In.  
   * *Target:* The "Clarified Vision" text.  
   * *Question:* "Are these requirements contradictory? Is this success metric measurable?"  
   * *Result:* If the plan is flawed, the loop returns to Phase 2\. No architecture is designed until the requirements are solid.

   

2. **Check \#2: Architecture Audit (Post-Phase 3\)**  
     
   * *Timing:* Before the first line of code is written.  
   * *Target:* The Steering Files.  
   * *Question:* "Will this tech stack handle the projected load? Does this design violate security best practices?"  
   * *Result:* If the design is weak, the loop returns to Phase 3\. No builders are summoned.

   

3. **Check \#3: Code Audit (During Phase 4\)**  
     
   * *Timing:* After every single task or feature completion.  
   * *Target:* The specific PR or commit.  
   * *Question:* "Does this code match the spec? Did the Builder skip tests?"  
   * *Result:* If the code is bad, the task is marked `FAILED` and returned to the Builder immediately.

**Rule:** The Red Team detects defects when they are cheap (in text), not when they are expensive (in production code).

## **3.2 Error Handling & Safety**

AI agents can loop indefinitely, hallucinate, or crash. To prevent data loss and runaway costs, the Virtual Company operates with a "Crash-Only" architecture. The system assumes failure is inevitable and relies on frequent state saving to recover.

### **The Checkpoint Protocol**

The Orchestrator must freeze the project state at specific intervals. This creates a "Save Game" point.

**Trigger Conditions:**

1. **Phase Completion:** Immediately after a phase moves to `complete` (e.g., Socratic Lock-In finished).  
2. **Time Elapsed:** Every 30 minutes of active execution.  
3. **Manual:** Before any high-risk operation (e.g., large refactoring).

**Execution Steps:**

1. **Snapshot:** Copy `swarm_state.md` to `.checkpoints/swarm_state_{timestamp}.md`.  
2. **Version Control:** Create a git commit with the tag `checkpoint-{phase}-{timestamp}`.  
3. **Archive:** Save current agent logs to the checkpoint folder.  
4. **Validate:** The Red Team verifies that the checkpoint file is valid JSON/Markdown and references existing files.  
5. **Pointer Update:** Update the `last_successful_checkpoint` field in the active `swarm_state.md`.

---

### **The Recovery Procedure**

When an agent crashes, gets stuck in a logic loop, or corrupts the state file, the Orchestrator initiates recovery.

**Trigger:** System timeout, unparseable `swarm_state.md`, or manual "Emergency Stop."

**Execution Steps:**

1. **Identify:** Read the `last_successful_checkpoint` timestamp from the corrupted state file (or the latest file in `.checkpoints/` if unreadable).  
2. **Restore:** Overwrite the active `swarm_state.md` with the checkpoint version.  
3. **Reset Code:** Execute `git checkout checkpoint-{phase}-{timestamp}` to revert the codebase to match the state file.  
4. **Resume:** Set the `recovery_point` field to the interrupted task and change `task_status` from `in_progress` to `pending`.  
5. **Re-Plan:** The Orchestrator re-reads the state and assigns the task to a different agent (to avoid repeating the same error).

---

### **Human Gate Triggers (Mandatory Pauses)**

The system is not fully autonomous. It **MUST** pause execution and wait for explicit human approval in `swarm_state.md` when these triggers occur.

1. **Deployment Approval:** Any attempt to push code to a production or staging environment.  
2. **Architecture Change:** Any proposed modification to Tier 1 Steering Files (`tech-stack.md`, `architecture.md`).  
3. **Security Finding:** The Red Team reports a **Critical** or **High** severity vulnerability.  
4. **Scope Change:** Any modification to the "Definition of Done" or "Clarified Vision" after Phase 1\.  
5. **Resource Overrun:** The project exceeds estimated time or budget by \>20%.  
6. **Ambiguity:** The Orchestrator cannot resolve a conflict between the Spec and the Steering Files.

## **3.3 Workflow Reference Scenarios**

### **Scenario 1: Concept → Code (Green-Field)**

| Phase | Action | Owner |
| :---- | :---- | :---- |
| **0\. Input** | Classify as **Type A (Concept)** \+ **Stage 1 (Greenfield)**. | Orchestrator |
| **1\. Lock-In** | **Intensive Socratic Protocol (4 Rounds).** Define User, Problem, Vision. | Orchestrator |
| **2\. Design** | Create Steering Files. **Human Gate:** Approve Architecture. | Orchestrator |
| **3\. Build** | Sprint 1: Core MVP. Sprint 2: Features. **Red Team:** Audit per feature. | Builder |
| **4\. Audit** | **Pre-Launch Audit.** Security & Performance check. | Red Team |
| **5\. Deploy** | **Human Gate:** Go/No-Go. Deploy to Prod. | Human |

### **Scenario 2: Spec → Code (Feature Add)**

| Phase | Action | Owner |
| :---- | :---- | :---- |
| **0\. Input** | Classify as **Type B (Spec)** \+ **Stage 2 (Build/Extend)**. | Orchestrator |
| **1\. Lock-In** | **Focused Protocol.** Gap analysis of the provided PRD. | Orchestrator |
| **2\. Design** | Impact Assessment. How does new spec fit old arch? | Orchestrator |
| **3\. Build** | Parallel Streams (Backend/Frontend). **Red Team:** Integration check. | Builder |
| **4\. Audit** | **Regression Testing.** Ensure no breakages. | Red Team |
| **5\. Deploy** | **Human Gate:** Deploy to Staging/Prod. | Human |

### **Scenario 3: Code Audit (Security/Refactor)**

| Phase | Action | Owner |
| :---- | :---- | :---- |
| **0\. Input** | Classify as **Type C (Code)** \+ **Stage 3 (Mature)**. | Orchestrator |
| **1\. Analysis** | **Code Archaeology.** Map existing flows and dependencies. | Orchestrator |
| **2\. Audit** | **Automated Scan \+ Manual Pen-Test.** Document findings. | Red Team |
| **3\. Fix** | Prioritize Critical/High. Fix implementation. | Builder |
| **4\. Verify** | Re-validate fixes. **Human Gate:** Sign-off. | Red Team |

### **Scenario 4: Hybrid Refactoring (Legacy \+ New)**

| Phase | Action | Owner |
| :---- | :---- | :---- |
| **0\. Input** | Classify as **Type D (Hybrid)** \+ **Stage 4 (Mixed)**. | Orchestrator |
| **1\. Reconcile** | **Hybrid Protocol.** Map old code to new requirements. | Orchestrator |
| **2\. Interface** | Define "Strangler Fig" boundaries and API contracts. | Orchestrator |
| **3\. Build** | Stream A: Refactor Legacy. Stream B: Build New. | Builders |
| **4\. Integ** | **Cross-Stream Audit.** Check data consistency. | Red Team |
| **5\. Switch** | Gradual traffic migration. **Human Gate:** Final switchover. | Human |

# **Part 4: Technical Implementation (The Setup)**

## **4.1 Hybrid Architecture Setup**

Native AI coding assistants act as plugins. They require a human to click "Send" for every action. To create a functioning Virtual Company that operates autonomously, we must wrap these assistants in a control layer.

This manual mandates **Scenario B: Hybrid Architecture**.

This approach splits the system into two distinct layers: a persistent "Manager" (Python) and ephemeral "Workers" (KIRO Agents).

### **Component 1: The Python Meta-Orchestrator (`swarm_runner.py`)**

This script acts as the operating system for the project. It runs continuously in the background, maintaining the project's memory and heartbeat. It does not generate code; it manages the process.

**Core Functions:**

* **State Persistence:** It reads and writes to `swarm_state.md`. It ensures that the project status survives even if an individual agent crashes.  
* **Task Scheduling:** It parses the `task_queue`, identifies the next priority item, and selects the correct agent from the manifest.  
* **Context Injection:** It assembles the specific prompt for each task. It concatenates the relevant Steering Files (Tier 1\) and Specifications (Tier 2\) before invoking an agent.  
* **Human Gate Control:** It pauses execution when it detects a "Gate Trigger" (e.g., deployment or architecture change) and waits for user input.

### **Component 2: KIRO Agent Instances**

KIRO agents are the execution engine. They are stateless and ephemeral. They wake up, perform a single task, and shut down.

**Operational Logic:**

* **Activation:** Agents do not decide when to work. They are triggered by the Meta-Orchestrator via a CLI command or a file-based signal.  
* **Execution:** The agent receives a specific "Task Prompt" containing its role, constraints, and necessary context. It performs the work (coding, auditing, or planning).  
* **Output:** The agent writes its results to specific locations:  
  * Source code to `src/`  
  * Tests to `tests/`  
  * Findings to `swarm_state.md`  
* **Termination:** Once the artifacts are written, the agent process terminates. It retains no memory of the session.

### **Component 3: Native Agent Definitions (.kiro/agents/)**

We replace the passive JSON manifest with active **Native Agent Definitions**. These are Markdown files located in `.kiro/agents/` that define the agent's personality *and* its physical permissions.

**The Security Upgrade:** We use `toolsSettings` to enforce roles programmatically.

**1\. The Orchestrator (`orchestrator.md`):**

* **Write Access:** `allowedPaths: ["./docs/**", "./swarm_state.md"]`  
* **Blocked Access:** `deniedPaths: ["./src/**", "./tests/**"]`  
* *Result:* It is physically impossible for the Orchestrator to write production code, even if it tries.

**2\. The Builder (`builder.md`):**

* **Write Access:** `allowedPaths: ["./src/**", "./tests/**"]`  
* **Blocked Access:** `deniedPaths: [".kiro/steering/**"]`  
* *Result:* The Builder cannot change the architecture or rules.

## **4.2 Integration Protocols**

The Python Meta-Orchestrator and the KIRO Agents communicate through three strict interfaces. These protocols define how work begins (Activation), what information is provided (Context Injection), and how results are returned (Output Capture).

### **Interface A: Activation (Orchestrator → Agent)**

The Orchestrator triggers an agent using one of two methods, depending on the available runtime environment.  
**Method 1: CLI Execution (Verified)** The Orchestrator invokes the specific agent profile. Kiro handles the context loading based on the agent's definition file.

```shell
kiro-cli chat \
  --agent orchestrator \
  --no-interactive \
  --message "{prompt_content}"
```

**Method 2: File-Based Trigger (Fallback)** If CLI access is restricted, the Orchestrator writes a "Job File" to a watched directory.

1. **Write:** Orchestrator saves `task_{id}.md` to `.kiro_tasks/`.  
2. **Detect:** The KIRO runtime (or human operator) sees the new file.  
3. **Execute:** The agent loads the file as its primary instruction.

---

### **Interface B: Context Injection (The Prompt Block)**

Agents have no long-term memory. The Orchestrator must construct a "Just-In-Time" memory block for every task. This prompt concatenates the Truth Hierarchy into a single instruction set.

**The Injection Template:**

```
# AGENT TASK PROMPT

## Your Role
You are: {builder|red_team|orchestrator}
Your constraints: {role_specific_constraints_from_manifest}

## Context (Truth Hierarchy)
### 1. Steering Mandates (Highest Priority)
{content from .kiro/steering/*.md}

### 2. Active Specification
{content from docs/reference/{active_spec}.md}

### 3. Current State
{relevant excerpt from swarm_state.md}

## Your Task
{specific_task_description}

## Output Requirements
- Code location: {path}
- Test location: {path}
- Update swarm_state.md section: {section}
```

**Conflict Resolution Rule:** The prompt explicitly states: "If Steering contradicts Spec → Follow Steering. If Spec contradicts Chat → Follow Spec."  
---

### **Interface C: Output Capture (Agent → Orchestrator)**

Agents must return structured data, not just chat text. The Orchestrator parses this JSON output to update the `swarm_state.md`.

**The Result Schema (`result.json`):**

```json
{
  "task_id": "auth-implementation-001",
  "agent_id": "builder_backend",
  "status": "complete", 
  "summary": "Implemented JWT logic and added unit tests.",
  "artifacts": {
    "code": ["src/auth/login.py", "src/auth/jwt_handler.py"],
    "tests": ["tests/test_auth.py"],
    "docs": ["docs/auth_api.md"]
  },
  "findings": [
    {
      "severity": "High",
      "category": "Security",
      "description": "Hardcoded secret in test file",
      "file": "tests/test_auth.py"
    }
  ],
  "blockers": []
}
```

**Status Codes:**

* `complete`: Work finished, tests passed.  
* `failed`: Work attempted but tests failed or code crashed.  
* `blocked`: Work stopped due to ambiguity or missing dependency.

# **Part 5: The Asset Pack (Templates & Scripts)**

## **5.1 System Prompts**

These prompts are the "operating system" for the agents. They must be pasted into the agent's context or passed via the API for every session.

### **A. The Orchestrator Agent Definition**

**File:** `.kiro/agents/orchestrator.md`

````
---
name: orchestrator
description: "Architect and Project Manager. Manages state, plans work, but CANNOT write code."
model: "claude-sonnet-4"
toolsSettings:
  write:
    allowedPaths: ["./docs/**", "./swarm_state.md", "./.kiro/steering/**"]
    deniedPaths: ["./src/**", "./tests/**"]
---

# SYSTEM PROMPT
```
# SYSTEM PROMPT: Universal Orchestrator Agent

## Your Identity
You are the **Orchestrator** — the central planning and coordination intelligence of the Virtual Company. You are the only agent authorized to make architectural decisions, manage global state, and coordinate other agents.

## Your Core Responsibilities
1. **State Management:** Own and maintain `swarm_state.md` as the single source of truth.
2. **Workflow Coordination:** Determine current phase, assign tasks, manage transitions.
3. **Context Curation:** Create and maintain Steering Files and Specifications.
4. **Quality Gatekeeping:** Interpret Red Team findings, enforce quality standards.
5. **Human Interface:** Identify when human approval is required, formulate clear questions.

## Hard Constraints (NEVER Violate)
- ❌ **NEVER write production code** (functions, classes, business logic). Only specs, plans, and documentation.
- ❌ **NEVER modify code written by Builders**. If code needs changes, create a spec for Builder to implement.
- ❌ **NEVER ignore Critical or High severity findings** from Red Team without explicit human approval documented in `swarm_state.md`.
- ❌ **NEVER proceed when `swarm_state.md` shows `phase_status: blocked`** without resolving the blocker.
- ❌ **NEVER invent requirements** not derived from user input or clarified through Socratic Lock-In.

## Input Type Detection Logic
When you receive input, classify it:

### IF input matches these patterns:
- "I have an idea...", "What if we...", "Startup concept...", "Napkin sketch"
- No formal requirements document
- High ambiguity, many open questions
**THEN:** `input_type = concept`
**Action:** Initiate Intensive Socratic Lock-In (40-50% project time)

### IF input matches these patterns:
- "Here is the PRD...", "Specification attached...", "Requirements document..."
- Formal or semi-formal structure
- Defined features, but may have gaps
**THEN:** `input_type = spec`
**Action:** Initiate Focused Socratic Lock-In (15-20% project time) for gap analysis

### IF input matches these patterns:
- "Here is the codebase...", "We need to refactor...", "Audit this code..."
- Existing source code provided
- Intent to modify, extend, or audit
**THEN:** `input_type = code`
**Action:** Skip/Minimize Socratic Lock-In, begin Code Analysis Phase

### IF input matches multiple patterns:
**THEN:** `input_type = hybrid`
**Action:** Initiate Reconciliation Socratic Lock-In (20-30% project time)

## Lifecycle Stage Detection Logic
Analyze `swarm_state.md` and codebase (if provided):

- **IF no code exists AND project is conceptual:** `lifecycle_stage = greenfield`
- **IF foundation code exists AND adding features/refactoring:** `lifecycle_stage = build_extend`
- **IF code is feature-complete AND focus is audit/optimization:** `lifecycle_stage = mature_audit`
- **IF multiple stages simultaneously active:** `lifecycle_stage = mixed`

## Adaptive Socratic Lock-In Protocol
Based on `input_type`, execute corresponding variant:

### For `concept` (Intensive - 4 rounds):
*   **Round 1:** "What specific problem does this solve? Describe it to someone unfamiliar with the domain."
*   **Round 2:** "If this works perfectly, how does the user's life change in 30 days?"
*   **Round 3:** "What is explicitly OUT of scope? What hard constraints exist?"
*   **Round 4:** "How will we objectively know this is successful? (North Star Metric)"

### For `spec` (Focused - 4 rounds):
*   **Round 1:** "For requirement X, what happens if condition Y is not met?"
*   **Round 2:** "What happens when action A and B occur simultaneously?"
*   **Round 3:** "What does this spec assume about external dependencies?"
*   **Round 4:** "If forced to choose: security vs speed, which matters more?"

### For `code` (Reverse Engineering - 4 rounds):
*   **Round 1:** "What architecture were the authors trying to implement?"
*   **Round 2:** "What business problem does this module solve?"
*   **Round 3:** "Where are there no tests? What works 'on faith'?"
*   **Round 4:** "What exactly needs to change and why?"

### For `hybrid` (Reconciliation - 4 rounds):
*   **Round 1:** "Where does existing code implement new requirements? Where does it contradict?"
*   **Round 2:** "Where do we draw the line between 'keep old' and 'build new'?"
*   **Round 3:** "How do we transition from current to target without downtime?"
*   **Round 4:** "Refactor old first or build new first? Why?"

## Workflow Coordination Logic

### Phase Sequence by Lifecycle:
*   **Green-Field:** Input Analysis → Socratic Lock-In → Architecture Design → Implementation → Red Team Audit → Refinement → Ready for Deploy
*   **Build/Extend:** Current State Analysis → Architecture Impact → Implementation (parallel) → Integration Testing → Red Team Audit → Ready for Deploy
*   **Mature/Audit:** Code Analysis → Security Audit → Performance Audit → Fix Implementation → Re-validation → Ready for Deploy

### State Management Protocol
*   **Reading:** Always read `swarm_state.md` at start. Check `current_phase`, `active_task`, and `error_log`.
*   **Updating:** After every action, update `swarm_state.md`. Increment `state_version`.

### Error Handling & Escalation
*   **Retry:** If Builder fails, retry 1x with clarification. Then escalate.
*   **Human Gate:** Trigger (pause execution) when:
    *   Deployment to production required.
    *   Steering Files need modification.
    *   Critical security finding discovered.
    *   Architectural change proposed.

## Output Format: XML Tags

You must output your decision using strict XML tags. Do not use Markdown code blocks for the tags.

**Schema:**
```xml
<summary>Brief explanation of your decision.</summary>
<next_action>PLAN | BUILD | AUDIT | DONE | ERROR</next_action>
<plan>
  <item>1. Task description...</item>
  <item>2. Task description...</item>
</plan>
<steering_update file="tech.md">New content...</steering_update>
```
````

---

### **B. The Red Team Auditor Prompt**

**File:** `Red_Team_Auditor_MetaPrompt.md`

````
# SYSTEM PROMPT: Red Team / Auditor Agent

## Your Identity
You are the **Red Team** — the adversarial auditor and quality gatekeeper. Your mission is to find flaws, challenge assumptions, and ensure nothing substandard passes. You are hostile to bugs, security holes, and logical inconsistencies. You are the guardian of quality.

## Your Core Responsibilities
1. **Requirements Validation:** Ensure requirements are complete, consistent, and testable.
2. **Architecture Audit:** Verify architectural decisions are sound and scalable.
3. **Security Audit:** Find vulnerabilities, injection points, data leaks.
4. **Performance Audit:** Identify bottlenecks, inefficiencies, resource leaks.
5. **Code Review:** Verify code matches specifications, find logic errors.
6. **Edge Case Discovery:** Find scenarios not covered by happy-path thinking.

## Hard Constraints (NEVER Violate)
- ❌ **NEVER write code or fixes yourself**. Only identify and document problems.
- ❌ **NEVER approve quality** — your job is to find problems, not certify goodness.
- ❌ **NEVER ignore a finding**, no matter how small it seems.
- ❌ **NEVER work without context** from `swarm_state.md` and Steering Files.
- ❌ **NEVER attack the person** — attack the code, architecture, or requirements.

## Adaptive Attack Vector Selection
Read `swarm_state.md` → `lifecycle_stage` to determine your focus:

### IF `lifecycle_stage = greenfield`:
*   **Primary Focus:** Requirements Clarity ("Is the problem real?").
*   **Secondary Focus:** Architectural Feasibility ("Will the stack hold?").
*   **Attack:** Challenge assumptions, find missing constraints, stress-test the vision.

### IF `lifecycle_stage = build_extend`:
*   **Primary Focus:** Architectural Impact ("Does this break the design?").
*   **Secondary Focus:** Technical Debt ("Are we cutting corners?").
*   **Attack:** Check for architectural drift, cyclic dependencies, missing tests.

### IF `lifecycle_stage = mature_audit`:

*   **Primary Focus: Security Vulnerabilities**
    *   **Injection:** SQL, NoSQL, Command, LDAP injection points.
    *   **Broken Auth:** Session management, password handling, JWT flaws.
    *   **Sensitive Data Exposure:** Logs, errors, API responses leaking PII.
    *   **Broken Access Control:** IDOR, privilege escalation.
    *   **XSS:** Stored, reflected, DOM-based XSS.
    *   **Dependencies:** Outdated libraries with known CVEs.

*   **Secondary Focus: Performance Bottlenecks**
    *   **Database:** N+1 queries, missing indexes, unbounded queries.
    *   **Memory:** Leaks, unbounded caches, large object retention.
    *   **Concurrency:** Race conditions, deadlocks, thread-safety issues.

*   **Tertiary Focus: Edge Cases & Error Handling**
    *   **Resilience:** Null/undefined inputs, empty collections, network timeouts.
    *   **Resources:** Disk full, memory low, API rate limits.

### IF `lifecycle_stage = mixed`:
*   **Primary Focus:** Cross-Stream Impact ("Does Stream A break Stream B?").
*   **Secondary Focus:** Coordination Risk.

## Output Format: XML Tags

You must output your findings using strict XML tags.

**Schema:**
```xml
<summary>Brief analysis of the codebase status.</summary>
<status>FIX | DONE | ERROR</status>
<findings>
  <finding>
    <severity>High</severity>
    <description>SQL Injection in login.py</description>
    <file>src/login.py</file>
  </finding>
</findings>
````

---

### **C. The Builder Agent Prompt**

**File:** `Builder_Agent_MetaPrompt.md`

````
# SYSTEM PROMPT: Builder Agent Template

## Your Identity
You are a **Builder** — an implementation specialist. Your job is to turn specifications into working, tested, documented code. You are a craftsman who takes pride in clean, correct, well-tested implementations.

## Your Core Responsibilities
1. **Code Implementation:** Write production code according to specifications.
2. **Test Creation:** Write unit and integration tests (test-first when possible).
3. **Documentation:** Document APIs, complex logic, and usage patterns.
4. **Self-Validation:** Run tests and verify your work before marking complete.
5. **Blocker Reporting:** Immediately report ambiguities or blockers in specs.

## Hard Constraints (NEVER Violate)
- ❌ **NEVER change Steering Files or Architecture**. If you see a problem, report to Orchestrator.
- ❌ **NEVER invent logic not in the specification**. If spec is unclear, ask for clarification.
- ❌ **NEVER skip tests**. Every feature must have tests. No exceptions.
- ❌ **NEVER hide technical debt**. Document shortcuts with TODOs and explanations.
- ❌ **NEVER commit secrets** (passwords, keys, tokens) to code.

## Your Workflow

### Step 1: Understand
1. Read the specification completely.
2. Identify acceptance criteria.
3. Check `.kiro/steering/conventions.md` for coding standards.

### Step 2: Test-First
1. Write test cases covering happy path, edge cases, and error cases.
2. Run tests — they should fail.

### Step 3: Implement
1. Write clean, readable code following conventions.
2. Add docstrings and comments.
3. Handle errors gracefully.

### Step 4: Validate
1. Run all tests — they must pass.
2. Run linting/type checking.
3. Check for security issues (input validation).

### Step 5: Report Completion
Update `swarm_state.md`:
- Set `task_status: complete`.
- List created artifacts (files, tests, docs).
- Note any technical debt or spec ambiguities.

## Output Format: XML Tags

You must output your status using strict XML tags.

**Schema:**
```xml
<summary>Brief description of changes applied.</summary>
<status>BUILD | AUDIT | ERROR</status>
<completed_task_id>task-01</completed_task_id>
<test_results>
  <cmd>pytest tests/test_login.py</cmd>
  <outcome>PASS</outcome>
</test_results>
````

## **5.2 File Templates**

These templates form the structural backbone of the project. They must be copied into the project root and `.kiro/steering/` directory at initialization.

### **A. The Universal State File**

**File:** `swarm_state_TEMPLATE.md`

````
# Swarm State: {PROJECT_NAME}

> State Version: 0.1.0 | Last Updated: {ISO_TIMESTAMP} | Orchestrator: v1.0

---

## 1. Project Identity & Context

- **Project Name:** {PROJECT_NAME}
- **Created At:** {ISO_TIMESTAMP}
- **Last Updated:** {ISO_TIMESTAMP}
- **Input Type:** {concept|spec|code|hybrid}
- **Lifecycle Stage:** {greenfield|build_extend|mature_audit|mixed}
- **Current Phase:** {input_analysis|socratic_lockin|architecture_design|implementation|red_team_audit|refinement|ready_for_deploy}
- **Phase Status:** {pending|in_progress|blocked|complete}
- **Definition of Done:**
  - [ ] All P0 requirements implemented
  - [ ] All Critical/High Red Team findings resolved
  - [ ] Tests passing >90% coverage
  - [ ] Documentation complete
  - [ ] Human approval for deployment

---

## 2. Clarified Vision & Requirements (Socratic Lock-In Output)

### 2.1 Core Problem Statement
{WHAT_PROBLEM_DOES_THIS_SOLVE}

### 2.2 Target Users
- **Primary:** {USER_PERSONA_1}
- **Secondary:** {USER_PERSONA_2}

### 2.3 Success Metrics
- **Primary Metric:** {MEASURABLE_OUTCOME}
- **Target:** {NUMBER} by {TIMEFRAME}

### 2.4 Key Requirements (Prioritized)

#### P0 (Critical - Must Have)
1. {REQUIREMENT_1}
2. {REQUIREMENT_2}

#### P1 (Important - Should Have)
1. {REQUIREMENT_3}

#### P2 (Nice to Have - Could Have)
1. {REQUIREMENT_4}

### 2.5 Constraints & Assumptions
**Hard Constraints:**
- {CONSTRAINT_1}
- {CONSTRAINT_2}

**Technical Constraints:**
- {TECH_CONSTRAINT_1}

**Business Assumptions:**
- {ASSUMPTION_1}

**Edge Cases to Handle:**
- {EDGE_CASE_1}
- {EDGE_CASE_2}

### 2.6 Acceptance Criteria
- [ ] {CRITERION_1}
- [ ] {CRITERION_2}
- [ ] {CRITERION_3}

---

## 3. Architecture & Technical Context

### 3.1 Technology Stack
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Language | {Python|JavaScript|Go|...} | {version} | {notes} |
| Framework | {FastAPI|React|Django|...} | {version} | {notes} |
| Database | {PostgreSQL|MongoDB|...} | {version} | {notes} |
| Cache | {Redis|...} | {version} | {notes} |
| Testing | {pytest|jest|...} | {version} | {notes} |
| Deployment | {Docker|K8s|...} | {version} | {notes} |

### 3.2 Folder Structure
```text
{PROJECT_ROOT}/
├── src/                    # Source code
│   ├── {module1}/
│   ├── {module2}/
│   └── utils/
├── tests/                  # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                   # Documentation
│   ├── reference/          # Specifications
│   └── api/               # API docs
├── .kiro/                  # KIRO configuration
│   └── steering/          # Global rules
├── scripts/               # Automation scripts
└── config/               # Configuration files
### **3.3 Coding Conventions**

**Style Guide:** {PEP8|StandardJS|Airbnb|Custom}

**Naming Conventions:**

- Variables: {snake\_case|camelCase}  
- Classes: {PascalCase}  
- Constants: {UPPER\_SNAKE\_CASE}

**Commit Format:** {Conventional Commits|Custom} Example: `feat(auth): add JWT token refresh`

### **3.4 Architecture Decisions**

| Decision | Rationale | Alternatives Considered | Date |
| :---- | :---- | :---- | :---- |
| {DECISION\_1} | {WHY} | {ALT\_1}, {ALT\_2} | {DATE} |
| {DECISION\_2} | {WHY} | {ALT\_1}, {ALT\_2} | {DATE} |

---

## **4\. Team & Task Management**

### **4.1 Active Task**

- **Task ID:** {TASK\_ID}  
- **Description:** {WHAT\_NEEDS\_TO\_BE\_DONE}  
- **Assigned Agents:** \[{AGENT\_ID\_1}, {AGENT\_ID\_2}\]  
- **Task Status:** {pending|in\_progress|blocked|complete|failed}  
- **Started At:** {ISO\_TIMESTAMP}  
- **Estimated Completion:** {ISO\_TIMESTAMP}  
- **Output Location:** {PATH}

### **4.2 Task Queue (Backlog)**

| Priority | Task ID | Description | Assigned To | Est. Effort |
| :---- | :---- | :---- | :---- | :---- |
| P0 | {ID} | {DESC} | {AGENT} | {TIME} |
| P1 | {ID} | {DESC} | {AGENT} | {TIME} |

### **4.3 Completed Tasks**

- [x] {TASK\_ID} | {DESCRIPTION} | Completed: {DATE} | By: {AGENT}

---

## **5\. Red Team Audit Status**

### **5.1 Current Focus Areas**

{requirements\_clarity|architectural\_feasibility|security|performance|edge\_cases|cross\_stream\_impact}

### **5.2 Findings Log**

#### ***Finding \#RT-001***

- **Severity:** {Critical|High|Medium|Low}  
- **Category:** {security|performance|logic|compliance|architecture}  
- **Description:** {DETAILED\_DESCRIPTION}  
- **Affected Area:** {FILE\_PATH\_OR\_COMPONENT}  
- **Evidence:** {CODE\_SNIPPET\_OR\_LOG}  
- **Impact:** {WHAT\_COULD\_GO\_WRONG}  
- **Recommended Fix:** {SPECIFIC\_GUIDANCE}  
- **Status:** {Open|Fixed|Re-Validating|Closed}  
- **Discovered By:** {AGENT\_ID}  
- **Discovered At:** {ISO\_TIMESTAMP}

### **5.3 Audit Status**

- **Overall Status:** {pending|in\_progress|findings\_reported|awaiting\_fixes|re\_validating|cleared}  
- **Last Audit:** {ISO\_TIMESTAMP}  
- **Critical Findings:** {COUNT}  
- **High Findings:** {COUNT}  
- **Medium Findings:** {COUNT}  
- **Low Findings:** {COUNT}  
- **Open Findings:** {COUNT}

---

## **6\. Error Handling & Recovery**

### **6.1 Error Log**

| Timestamp | Agent | Error Type | Description | Recovery Action | Status |
| :---- | :---- | :---- | :---- | :---- | :---- |
| {TS} | {AGENT} | {transient | logic | context | system |

### **6.2 Checkpoint History**

- **Last Successful Checkpoint:** {ISO\_TIMESTAMP} \- {DESCRIPTION}  
- **Recovery Point:** {PHASE\_OR\_TASK\_TO\_RESUME}

### **6.3 Human Gates Pending**

- [ ] {GATE\_DESCRIPTION} | Required By: {PHASE} | Blocking: {yes|no} | Requested At: {TS}

---

## **7\. File References**

### **7.1 Steering Files (Truth Hierarchy: 1 \- Highest)**

**Path:** `.kiro/steering/`

| File | Status | Last Updated |
| :---- | :---- | :---- |
| project-vision.md | {current | stale} |
| tech-stack.md | {current | stale} |
| conventions.md | {current | stale} |
| architecture.md | {current | stale} |
| definitions.md | {current | stale} |

### **7.2 Specifications (Truth Hierarchy: 2\)**

**Path:** `docs/reference/`

| Spec | Status | Version |
| :---- | :---- | :---- |
| {SPEC\_NAME}.md | {draft | approved |

### **7.3 Code & Tests (Truth Hierarchy: 3\)**

- **Source:** `{CODE_PATH}/`  
- **Tests:** `{TEST_PATH}/`  
- **Coverage:** {PERCENTAGE}%

### **7.4 Documentation**

- **Path:** `{DOCS_PATH}/`  
- **Generated:** {yes|no}

---

## **8\. Metadata**

- **State Version:** {SEMANTIC\_VERSION}  
- **Orchestrator Version:** {VERSION}  
- **Next Scheduled Action:** {WHAT\_HAPPENS\_NEXT}  
- **Blockers:** {LIST\_OR\_NONE}  
- **Notes:** {ANY\_ADDITIONAL\_CONTEXT}
````

---

### **B. Native Agent Templates**

**Location:** `.kiro/agents/`

*Note: See Section 5.1 for the full content of `orchestrator.md`. Create similar files for `builder.md` and `red_team.md` using the Standard Agent Schema.*  
---

### **C. Core Steering Files**

**Location:** `.kiro/steering/`

#### ***1\. Project Vision Template***

**File:** `.kiro/steering/project-vision.md`

```
# Project Vision: {PROJECT_NAME}

## Elevator Pitch
{One sentence description of what this does and for whom}

## Problem Statement
{What pain does this solve? Be specific.}

## Solution Overview
{How do we solve it? High-level approach.}

## Target Users
1. **Primary:** {Who benefits most}
2. **Secondary:** {Who else benefits}

## Success Metrics
- **North Star Metric:** {The one number that matters}
- **Target:** {Value} by {Date}

## Non-Goals (What We Explicitly Don't Do)
- {Out of scope feature 1}
- {Out of scope feature 2}

## Constraints & Assumptions
- {Business constraint}
- {Technical constraint}
- {Key assumption that if wrong, invalidates project}

## Timeline
- **MVP:** {Date}
- **V1.0:** {Date}
- **Scale:** {Date}
```

#### ***2\. Tech Stack Template***

**File:** `.kiro/steering/tech-stack.md`

```
# Technology Stack

## Core Technologies

### Backend
- **Language:** {Python 3.11|Node.js 18|Go 1.21|...}
- **Framework:** {FastAPI|Express|Gin|...}
- **Runtime:** {CPython|Node|...}

### Frontend
- **Framework:** {React 18|Vue 3|Svelte|...}
- **Language:** {TypeScript|JavaScript|...}
- **Styling:** {Tailwind|Styled Components|...}

### Database
- **Primary:** {PostgreSQL 15|MongoDB 6|...}
- **Cache:** {Redis 7|...}
- **ORM/ODM:** {SQLAlchemy|Prisma|Mongoose|...}

### Infrastructure
- **Container:** {Docker|...}
- **Orchestration:** {K8s|Docker Compose|...}
- **Cloud:** {AWS|GCP|Azure|...}

## Key Dependencies
| Purpose | Library | Version | Notes |
|---------|---------|---------|-------|
| Auth | {library} | {version} | {why} |
| Testing | {library} | {version} | {why} |

## Rationale
{Why this stack? Trade-offs considered?}
```

#### ***3\. Conventions Template***

**File:** `.kiro/steering/conventions.md`

```
# Coding Conventions

## General Principles
1. **Readability > Cleverness**
2. **Explicit > Implicit**
3. **Tested > Assumed**

## Naming Conventions
### Python
- `snake_case` for variables, functions
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- `_prefix` for private

### JavaScript/TypeScript
- `camelCase` for variables, functions
- `PascalCase` for classes, components, types
- `UPPER_SNAKE_CASE` for constants

## Code Style
### Formatting
- Line length: 100 characters
- Indent: 4 spaces (Python), 2 spaces (JS)
- Trailing commas: required

### Imports
- Group: stdlib, third-party, local
- Sort: alphabetical within groups
- No wildcard imports

### Documentation
- All public functions must have docstrings
- Complex logic needs inline comments (why, not what)
- README for every module

## Testing
- Minimum coverage: 80%
- All new code needs tests
- Test file naming: `test_{module}.py` or `{module}.test.js`

## Git Conventions
- Format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Example: `feat(auth): add password reset endpoint`
```

#### ***4\. Architecture Template***

**File:** `.kiro/steering/architecture.md`

````
# Architecture Overview

## System Diagram
```mermaid
graph TD
    User -->|HTTP| API_Gateway
    API_Gateway -->|RPC| App_Server
    App_Server -->|Query| Database
    App_Server -->|Cache| Redis

## **Component Responsibilities**

### **{Component 1}**

- **Responsibility:** {What it does}  
- **Interface:** {How others talk to it}  
- **Dependencies:** {What it needs}

### **{Component 2}**

- **Responsibility:** {What it does}  
- **Interface:** {How others talk to it}  
- **Dependencies:** {What it needs}

## **Data Flow**

1. {Step 1}  
2. {Step 2}  
3. {Step 3}

## **Key Decisions**

| Decision | Rationale | Trade-offs |
| :---- | :---- | :---- |
| {Decision} | {Why} | {What we gave up} |

## **Scalability Considerations**

- {How we handle growth}  
- {Bottlenecks to watch}
````

#### ***D. Specification Templates***

These templates provide the structure for the "Tier 2" documents defined in the Truth Hierarchy.

###### *docs/reference/refactoring-plan-TEMPLATE.md*

```
# Refactoring Plan: {COMPONENT_NAME}

## 1. Current State

### 1.1 Problem
{What's wrong with current implementation}

### 1.2 Impact
{How it affects system: performance, maintainability, stability}

### 1.3 Code Smells
- {Smell 1}
- {Smell 2}

## 2. Target State

### 2.1 Goal
{What good looks like}

### 2.2 Benefits
- {Benefit 1}
- {Benefit 2}

## 3. Strategy

### 3.1 Approach
- [ ] Strangler Fig (gradual replacement)
- [ ] Big Bang (complete rewrite - justify why)
- [ ] Branch by Abstraction

### 3.2 Execution Steps
1. {Step 1}
2. {Step 2}

## 4. Rollback Plan
If refactoring fails or causes regression:
1. {Step 1}
2. {Step 2}

## 5. Testing Strategy
- {How to ensure parity between old and new logic}
```

###### *docs/reference/audit-checklist-TEMPLATE.md*

```
# Audit Checklist: {SCOPE}

## Scope
{What is being audited: e.g., "Auth Module" or "Full System"}

## Criteria

### Security
- [ ] Input validation (All user inputs sanitized?)
- [ ] Authentication (No broken auth flows?)
- [ ] Authorization (IDOR checks passed?)
- [ ] Data protection (No cleartext secrets?)
- [ ] Dependency vulnerabilities (Checked against CVEs?)

### Performance
- [ ] Response times (Within NFR limits?)
- [ ] Database queries (No N+1 detected?)
- [ ] Memory usage (Stable under load?)
- [ ] Concurrency handling (Thread safe?)

### Code Quality
- [ ] Test coverage (>80%?)
- [ ] Code duplication (DRY principles?)
- [ ] Complexity (Cyclomatic complexity acceptable?)
- [ ] Documentation (Docstrings present?)

## Sign-off
- [ ] All Critical/High findings resolved
- [ ] Medium findings scheduled
- [ ] Audit Report reviewed by Orchestrator
```

## **5.3 Automation Scripts**

The Virtual Company cannot run on chat alone. It requires a persistent "Meta-Orchestrator" to manage state, enforce the Truth Hierarchy, and coordinate the agent swarm.

### **The Swarm Runner**

**File:** `swarm_runner.py`  
This script is the heartbeat of the system. It runs locally, monitoring `swarm_state.md`. It determines the next action based on the logic defined in Section 2.2 and triggers the appropriate KIRO agent.

```py
#!/usr/bin/env python3
"""
KIRO Golden Copy Orchestrator (v3.0)
------------------------------------
Chassis: Opus 4.6 (DAG + Worktrees + Verification)
Brain:   KIMI (Truth Hierarchy + Socratic Logic)
Parser:  GPT-5.2 (XML/Regex)
Safety:  FileLock Mutex

Usage:
    python swarm_runner.py --input "Build a Snake Game"
    python swarm_runner.py --input ./docs/specs/v1.md
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# ─── CRITICAL DEPENDENCY CHECK ─────────────────────
try:
    from filelock import FileLock
except ImportError:
    print("❌ CRITICAL ERROR: 'filelock' is missing.")
    print("   Run: pip install filelock")
    sys.exit(1)

try:
    import structlog
except ImportError:
    # Fallback if structlog is missing, though Opus 4.6 spec requires it.
    print("⚠️ WARNING: 'structlog' missing. Install for better logs: pip install structlog")
    class MockLogger:
        def info(self, *args, **kwargs): print(f"[INFO] {kwargs}")
        def error(self, *args, **kwargs): print(f"[ERROR] {kwargs}")
    structlog = None

# ─── CONFIGURATION ─────────────────────────────────
BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / ".swarm_state.json"  # JSON for machine persistence
SESSIONS_DIR = BASE_DIR / ".sessions"
STEERING_DIR = BASE_DIR / ".kiro" / "steering"
LOG_DIR = BASE_DIR / ".swarm_logs"
REPO_LOCK_PATH = BASE_DIR / "git_ops.lock"

MAX_BUDGET_PER_AGENT = 10.00
CLI_TIMEOUT_SECONDS = 300

# ─── 1. OBSERVABILITY ──────────────────────────────
class SwarmLogger:
    """Structured JSON logging with trace IDs."""
    def __init__(self, execution_id: str):
        LOG_DIR.mkdir(exist_ok=True)
        if structlog:
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.JSONRenderer()
                ],
                logger_factory=structlog.WriteLoggerFactory(
                    file=open(LOG_DIR / f"execution_{execution_id}.jsonl", "a")
                )
            )
            self.log = structlog.get_logger()
        else:
            self.log = MockLogger()

# ─── 2. STATE MANAGEMENT ───────────────────────────
class PersistentStateManager:
    """
    Manages .swarm_state.json.
    Enables crash recovery and idempotency.
    """
    def __init__(self):
        self.state = self._load_or_init()

    def _load_or_init(self) -> dict:
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ State file corrupted. Backing up and resetting.")
                STATE_FILE.rename(STATE_FILE.with_suffix(".bak"))
        
        return {
            "version": "3.0",
            "execution_id": str(uuid.uuid4()),
            "mode": "",
            "phase": "init",
            "completed_tasks": [],
            "failed_tasks": [],
            "plan": [],
            "total_cost_usd": 0.0
        }

    def save(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

# ─── 3. CONCURRENCY SAFETY (MUTEX) ─────────────────
class GitMutex:
    """
    GOLDEN COPY FIX: Prevents index corruption in Worktrees.
    Wraps all git operations in a file lock.
    """
    def __init__(self):
        self.lock = FileLock(REPO_LOCK_PATH)

    def run_git(self, args: List[str], check=True) -> subprocess.CompletedProcess:
        with self.lock:
            return subprocess.run(["git"] + args, capture_output=True, text=True, check=check)

# ─── 4. TRUTH INJECTION (NATIVE) ───────────────────

class PromptPipeline:
    """
    Native Steering Wrapper.
    Context is now handled by Kiro's internal engine via .kiro/steering/.
    This class constructs the minimal task wrapper.
    """
    @staticmethod
    def build_task(task_desc: str) -> str:
        return f"""
# TASK
{task_desc}

# OUTPUT INSTRUCTION
You must output your decision using strict XML tags.
<summary>Brief explanation</summary>
<next_action>PLAN | BUILD | AUDIT | DONE</next_action>
<status>SUCCESS | FAILED</status>
<plan> (If planning) ... </plan>
"""

# ─── 5. XML OUTPUT PARSER ──────────────────────────
class OutputParser:
    """
    GPT-5.2 FIX: Extracts XML tags from CLI stdout.
    Replaces the unstable '--output-format json'.
    """
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        results = {}
        # Extract basic tags
        patterns = {
            "next_action": r"<next_action>(.*?)</next_action>",
            "status": r"<status>(.*?)</status>",
            "summary": r"<summary>(.*?)</summary>",
        }
        for key, pat in patterns.items():
            m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
            if m:
                results[key] = m.group(1).strip()
            else:
                results[key] = "UNKNOWN"

        # Extract Plan (JSON list inside XML)
        # Attempt to parse <plan>...</plan> as structure if possible, otherwise raw text
        plan_m = re.search(r"<plan>(.*?)</plan>", text, re.DOTALL | re.IGNORECASE)
        if plan_m:
            # Simple heuristic: try to find list items
            items = re.findall(r"<item>(.*?)</item>", plan_m.group(1))
            if items:
                results["plan"] = [{"id": f"task-{i}", "description": item} for i, item in enumerate(items)]
            else:
                # Fallback: Treat as raw text or try simple parsing
                results["plan_raw"] = plan_m.group(1).strip()
        
        return results

# ─── 6. SECURE CLI EXECUTOR ────────────────────────
class CLIExecutor:
    """
    Wraps kiro-cli. Removes '--output-format json'.
    """
    def __init__(self):
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    def execute(self, role: str, message: str) -> tuple[int, str, str]:
        session_path = SESSIONS_DIR / f"{role}.session"
        
        cmd = [
            "kiro-cli", "chat",
            "--no-interactive",
            "--max-budget-usd", str(MAX_BUDGET_PER_AGENT),
            "--message", message
        ]
        
        if session_path.exists():
            cmd.extend(["--resume", str(session_path)])
        else:
            cmd.extend(["--save", str(session_path)])

        try:
            # Capture stdout directly (No JSON formatting flag)
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT_SECONDS
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "TIMEOUT"

# ─── 7. LOGIC ENGINES (OPUS 4.6) ───────────────────
class DAGOrchestrator:
    """Dependency Analysis."""
    def compute_next_batch(self, plan: List[dict], completed_ids: List[str]) -> List[dict]:
        available = []
        for task in plan:
            if task['id'] in completed_ids:
                continue
            # Simple logic: if no dependencies, or all deps met
            deps = task.get('dependencies', [])
            if not deps or all(d in completed_ids for d in deps):
                available.append(task)
        return available

class VerificationPipeline:
    """The Firewall: Code must pass tests."""
    def verify(self) -> bool:
        checks = [
            ("Lint", ["ruff", "check", "."]),  # Assuming python
            ("Test", ["pytest", "-q"])
        ]
        for name, cmd in checks:
            print(f"    🔍 Running {name} check...")
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"    ❌ Verification Failed: {name}")
                return False
        return True

class MergeConflictResolver:
    """Uses Mutex to safely merge."""
    def __init__(self):
        self.mutex = GitMutex()

    def merge(self, branch: str) -> bool:
        try:
            self.mutex.run_git(["merge", "--no-commit", branch])
            return True
        except subprocess.CalledProcessError:
            print(f"    ⚠️ Merge Conflict in {branch}. Aborting.")
            self.mutex.run_git(["merge", "--abort"], check=False)
            return False

# ─── 8. MAIN LOOP ──────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    # Init Components
    mgr = PersistentStateManager()
    state = mgr.state
    logger = SwarmLogger(state["execution_id"])
    cli = CLIExecutor()
    verifier = VerificationPipeline()
    dag = DAGOrchestrator()
    git_mutex = GitMutex() # Ensure git ops are safe

    print(f"🚀 Swarm Runner v3.0 Started. ID: {state['execution_id']}")
    print(f"📂 Project Root: {BASE_DIR}")

    # Initial Phase Detection
    if state["phase"] == "init":
        print("🤖 [Orchestrator] Analyzing Input...")
        # Inject Truth + Input
        prompt = PromptPipeline.build_task(
    f"Input: {args.input}. Analyze requirements. If greenfield, generate steering files and a plan. Output <next_action>PLAN</next_action>."
)
        
        _, stdout, _ = cli.execute("orchestrator", prompt)
        parsed = OutputParser.parse(stdout)
        
        if parsed["next_action"] == "PLAN":
            state["phase"] = "planning"
            print(f"    📋 Orchestrator Summary: {parsed['summary']}")
            if "plan" in parsed:
                state["plan"] = parsed["plan"]
            elif "plan_raw" in parsed:
                # Basic handling if XML list parsing failed
                print("    ⚠️ Plan parsed as raw text. Manual intervention might be needed for DAG.")
                state["plan"] = [{"id": "task-01", "description": parsed["plan_raw"]}] 
            
            mgr.save()
        else:
            print(f"    ⚠️ Orchestrator did not proceed. Action: {parsed['next_action']}")

    # Main GRLS Loop
    while len(state["completed_tasks"]) < len(state.get("plan", [])) or state["phase"] == "planning":
        
        # 1. READ STATE
        current_phase = state["phase"]
        
        # 2. PLANNING PHASE HANDLING
        if current_phase == "planning":
             # In a real run, we might loop here to refine specs. 
             # For now, transition to build if we have a plan.
             if state["plan"]:
                 state["phase"] = "building"
                 mgr.save()
                 continue
             else:
                 print("❌ Stuck in planning with no plan.")
                 break

        # 3. BUILD PHASE HANDLING
        if current_phase == "building":
            # Compute DAG
            batch = dag.compute_next_batch(state.get("plan", []), state["completed_tasks"])
            
            if not batch:
                if len(state["completed_tasks"]) == len(state.get("plan", [])):
                    state["phase"] = "auditing"
                    continue
                else:
                    print("❌ Deadlock: Tasks remain but dependencies not met.")
                    break                        
            # Select Task (Opus 4.6 Logic - Serialized)
            active_task = batch [0]
            print(f"🏗️  [Builder] Starting Task: {active_task['id']}")

            
            # Build Prompt
            prompt = PromptPipeline.build_task(
    f"Implement Task {active_task['id']}: {active_task['description']}. \n"
    f"Verify your code with tests. Output <status>SUCCESS</status> if verified."
)
            
            # Execute
            ret, stdout, stderr = cli.execute("builder", prompt)
            
            # Parse
            parsed = OutputParser.parse(stdout)
            
            # 4. VERIFY & UPDATE
            if parsed["status"] == "SUCCESS":
                # Double check with internal verifier (Firewall)
                if verifier.verify():
                    print(f"    ✅ Task {active_task['id']} Verified & Merged.")
                    state["completed_tasks"].append(active_task["id"])
                    mgr.save()
                else:
                    print(f"    ⛔ Task {active_task['id']} Failed Verification Pipeline.")
            else:
                print(f"    ⚠️ Builder reported failure: {parsed['summary']}")
                # Retry logic would go here
                break

        # 5. AUDIT PHASE HANDLING
        if current_phase == "auditing":
            print("🛡️  [Red Team] Starting Audit...")
            prompt = PromptPipeline.build_task(
    "Audit the codebase against the now-native Steering Files. "
    "Check for security, architecture, and code quality issues. "
    "Output <status>SUCCESS</status> if clean."
)
            ret, stdout, stderr = cli.execute("auditor", prompt)
            parsed = OutputParser.parse(stdout)
            
            if parsed["status"] == "SUCCESS":
                print("    ✅ Audit Passed. Project Complete.")
                state["phase"] = "complete"
                mgr.save()
                break
            else:
                print("    🚨 Audit Findings. Transitioning to Fixing.")
                state["phase"] = "fixing"
                mgr.save()
                # Fix loop logic would follow here

    if state["phase"] == "complete":
        print("🏆 SUCCESS: Golden Copy Execution Finished.")

if __name__ == "__main__":
    main()
```

## **Part 6: User Manual**

This manual describes how to operate the Virtual Company. It assumes you are acting as the "Human in the Loop," responding to requests from the Python Meta-Orchestrator.

### **6.1 Setup & Initialization**

Before running the agent swarm, you must prepare the physical environment.

**Prerequisites:**

* Python 3.9+  
* Git initialized repository  
* KIRO IDE (or access to KIRO agents via CLI)  
* **filelock**: Required for concurrency safety. Run `pip install filelock`.  
* *Note: The `swarm_runner.py` provided in Part 5 is a reference implementation. You may need to adjust the regex parsing logic if you modify the markdown templates.*

**Step 1: Create Folder Structure** Run the following commands in your project root to establish the standard directory layout:

```shell
mkdir -p src tests docs/reference .kiro/steering .checkpoints
```

**Step 1.5: Configure Lifecycle Hooks** To prevent environment errors, create `.kiro/hooks/python-env.json`. This forces Kiro to activate your virtual environment every time an agent spawns.

```json
{
  "hooks": {
    "agentSpawn": [
      {
        "command": "bash",
        "args": ["-c", "if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi"]
      }
    ]
  }
}
```

**Step 2: Install the Asset Pack** Copy the templates defined in **Part 5** to their respective locations:

1. `swarm_state_TEMPLATE.md` → Rename to `swarm_state.md` in the root.  
2. `Native Agents → Ensure .kiro/agents/ contains orchestrator.md, builder.md, etc.`  
3. `swarm_runner.py` → Place in the root.  
4. Steering Files (`project-vision.md`, `tech-stack.md`, etc.) → Place in `.kiro/steering/`.  
5. Specification Templates (`refactoring-plan-TEMPLATE.md`, `audit-checklist-TEMPLATE.md`) → Place in `docs/reference/`.

**Step 3: Initial Configuration** Open `swarm_state.md` and edit **Section 1: Project Identity**:

6. Set `Input Type` (e.g., `concept`, `spec`, or `code`).  
7. Set `Lifecycle Stage` (e.g., `greenfield` or `build_extend`).  
8. *Note:* These settings tell the Orchestrator which logic strategy to load.

**Step 4: Ignite the Swarm** Run the orchestrator script to start the first cycle:

```shell
python swarm_runner.py --input "My new project idea"
```

### **6.2 Input Submission**

The Orchestrator reads your intent from `swarm_state.md`. You do not chat with it directly; you write to the file.

**How to Submit a Concept:**

1. Open `swarm_state.md`.  
2. Navigate to **Section 2: Clarified Vision**.  
3. Fill in `2.1 Core Problem Statement` and `2.2 Target Users`.  
   * *Example:* "Problem: People struggle to find reliable dog walkers. Users: Busy professionals in cities."  
4. Save the file.  
5. Run `python swarm_runner.py`. The Orchestrator will detect the input and trigger "Socratic Lock-In."

**How to Submit a Specification:**

1. Place your full PRD/Spec file in `docs/reference/FULL_SPEC.md`.  
2. Open `swarm_state.md`.  
3. In Section 2, add a reference: "See `#file docs/reference/FULL_SPEC.md` for requirements."  
4. Set `Input Type: spec`.  
5. Run the orchestrator.

**How to Submit a Refactoring Plan (for Legacy Code):**

6. Copy `docs/reference/refactoring-plan-TEMPLATE.md` to `docs/reference/refactor-{component}.md`.  
     
7. Fill in **Section 1: Current State** (Code Smells) and **Section 2: Target State**.  
     
8. Open `swarm_state.md`.  
     
9. In Section 2, add: "See \#file docs/reference/refactor-{component}.md for refactoring strategy."  
     
10. Set Input Type: `code` (for pure cleanup) or `hybrid` (if adding features).  
      
11. Run the orchestrator.

---

### **6.3 Socratic Lock-In Protocols**

Once initialized, the Orchestrator will pause and ask questions to clarify your intent.

**Where to see questions:** Check the output log of `swarm_runner.py` or the `active_task` field in `swarm_state.md`.

**How to answer:**

1. Write your answers directly into `swarm_state.md` under the relevant section (usually adding details to Section 2).  
2. *Rule:* Be specific. If the Orchestrator asks "Who is the user?", do not say "Everyone." Say "Junior developers using VS Code."  
3. *Rule:* Challenge assumptions. If the Orchestrator suggests a feature you don't want, explicitly list it under "Non-Goals" in `.kiro/steering/project-vision.md`.

**Completion:** The phase ends only when the Orchestrator marks `swarm_state.md` → `Phase Status: complete`.

---

### **6.4 Human Gates**

The system cannot deploy code or change architecture without your permission. When a critical decision is needed, the Orchestrator pauses.

**The Trigger:** The runner output will display:

```
============================================================
HUMAN GATE REQUIRED
Gate: Approve deployment to production?
Blocking: yes
Please resolve and update swarm_state.md
============================================================
```

**How to Approve:**

1. Open `swarm_state.md`.  
2. Navigate to **Section 6.3: Human Gates Pending**.  
3. Find the pending gate item.  
4. Mark the checkbox `[x]` and add your approval note.  
   * *From:* `[ ] Approve deployment | Required By: Phase 7`  
   * *To:* `[x] Approve deployment | Approved: 2024-10-12 | Notes: "Go ahead"`  
5. Save the file.  
6. Restart `swarm_runner.py`. The Orchestrator will see the checkmark and resume execution.

**How to Reject:** Do not check the box. Instead, update the `active_task` or `red_team_findings` to reflect why you are rejecting (e.g., "Fix critical bug X first").

---

### **6.5 Troubleshooting**

**Scenario A: System Status is "Blocked"**

* **Symptom:** The runner loops but does nothing. `swarm_state.md` says `Phase Status: blocked`.  
* **Fix:**  
  1. Read `swarm_state.md` → **Section 6.1 Error Log**.  
  2. Identify the blocker (e.g., "Ambiguous requirement in spec").  
  3. Fix the issue (e.g., update the spec file).  
  4. Manually change `Phase Status` from `blocked` to `in_progress`.  
  5. Restart the runner.

**Scenario B: Red Team finds too many issues**

* **Symptom:** `swarm_state.md` lists 20+ findings.  
* **Analysis:** This is normal functionality, not a bug. The Red Team is designed to be pedantic.  
* **Fix:** Do not delete findings. Ask the Orchestrator (via `active_task`) to "Prioritize fixing Critical/High findings only."

**Scenario C: Orchestrator Hallucination / Confusion**

* **Symptom:** The agent is editing the wrong files or ignoring instructions.  
* **Fix (The "Hard Reset"):**  
  1. Stop the runner (`Ctrl+C`).  
  2. Check `.checkpoints/` for the last known good state.  
  3. Copy the checkpoint content into `swarm_state.md`.  
  4. Run `git checkout` to match the code to that checkpoint timestamp.  
  5. Restart the runner.

**Scenario D: KIRO CLI Not Responding**

* **Symptom:** Logs show "KIRO agent timeout."  
* **Fix:**  
  1. Check if a task file exists in `.kiro_tasks/`.  
  2. If yes, the system fell back to "File-Based Trigger."  
  3. You must manually open the KIRO IDE, paste the prompt from that file, run it, and save the result to `.kiro_output/`.

## **Appendix A: Interaction Examples (Transcripts)**

These examples illustrate exactly how a human operator interacts with the Orchestrator via `swarm_state.md`.

### **Example 1: Concept Input (Green-Field)**

**Scenario:** You have a vague startup idea.

**User Input (in `swarm_state.md`):**

```
## 2. Clarified Vision
"I want to build an Uber for dog walking. The main problem is reliability."
```

**Orchestrator Response (via Task Log):**

"Initiating Socratic Lock-In (Variant A). Please answer the following in Section 2:"

1. "Who is the specific user? (e.g., 'Busy professionals' vs 'Elderly owners')"  
2. "How do you verify trust? (Background checks? Social proof?)"

**User Response (Edit to `swarm_state.md`):**

```
### 2.2 Target Users
- Primary: Busy urban professionals (25-40) who travel for work.
- Trust Mechanism: We need an API integration with a background check service (Checkr).
```

---

### **Example 2: Handling a Security Finding**

**Scenario:** The Red Team blocks deployment due to a vulnerability.

**Red Team Finding (in `swarm_state.md`):**

```
#### Finding #RT-042
- **Severity:** Critical
- **Description:** SQL Injection vulnerability in search endpoint.
- **Status:** Open
```

**Orchestrator Action:**

Sets `Phase Status: blocked`. Triggers Human Gate: "Critical Security Finding \#RT-042 must be resolved."

**User Action:**

1. Do **NOT** ignore.  
2. Verify the Builder has been assigned a fix task.  
3. Once the Builder reports "Complete," trigger the Red Team to re-validate.  
4. Only when Red Team updates status to `Closed` do you unblock the phase.

---

### **Example 3: Scope Change Mid-Project**

**Scenario:** You realize you need a mobile app halfway through building the web API.

**User Input (in `swarm_state.md`):**

```
## 2. Clarified Vision
[ADDED] We also need a React Native mobile app for walkers.
```

**Orchestrator Response:**

"Global Scope Shift detected."

1. Pausing all active tasks.  
2. Invalidating `architecture.md` (Context Stale).  
3. Generating new Work Plan: "Mobile App Architecture Design".  
4. Requesting Human Approval for new timeline estimates.

---

## **Appendix B: Architecture Decision Record (ADR)**

**Title:** Adoption of Hybrid Architecture (Python Meta-Orchestrator \+ KIRO) **Status:** Approved **Date:** 2024-01-15

### **Context**

We require an AI coding system that is **autonomous** (can run loops without clicking "Send"), **stateful** (remembers context over weeks), and **safe** (prevents hallucinations).

### **Decision**

We have selected **Scenario B: Hybrid Architecture**. This consists of a local Python script (`swarm_runner.py`) managing state and logic, while using KIRO agents strictly as ephemeral execution engines triggered via CLI/Files.

### **Rationale**

| Capability | Native KIRO (IDE Only) | Hybrid (Python \+ KIRO) |
| :---- | :---- | :---- |
| **Persistence** | ❌ Session-based (Lost on restart) | ✅ File-based (Git \+ Markdown) |
| **Autonomy** | ❌ Human must click for every step | ✅ Loops until blocked |
| **State** | ⚠️ Implicit (Chat context) | ✅ Explicit (`swarm_state.md`) |
| **Role Limits** | ❌ Liquid (Agent forgets constraints) | ✅ Hard (Enforced by Prompt Injection) |

### **Consequences**

1. **Complexity:** Requires Python runtime and local file management.  
2. **Latency:** Slower than a direct chat due to context loading per task.  
3. **Resilience:** High. If the AI crashes, the state file remains.

