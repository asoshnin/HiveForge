# Swarm State: {PROJECT_NAME}

> State Version: 0.1.0 | Topology: v5.0 (Level 5 Hive) | Last Updated: {ISO_TIMESTAMP}

---

## 1. Project Identity & Context

- **Project Name:** {PROJECT_NAME}
- **Created At:** {ISO_TIMESTAMP}
- **Last Updated:** {ISO_TIMESTAMP}
- **Input Type:** {concept|spec|code|hybrid}
- **Lifecycle Stage:** {greenfield|build_extend|mature_audit|mixed}
- **Current Phase:** {input_analysis|socratic_lockin|architecture_design|delegated_execution|qa_verification|red_team_audit|refinement|ready_for_deploy}
- **Phase Status:** {pending|in_progress|blocked|complete}
- **Definition of Done:**
  - [ ] All P0 requirements implemented
  - [ ] All Critical/High Red Team findings resolved
  - [ ] QA tests passing >90% coverage  
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
├── .kiro/
│   ├── steering/          # Global Rules (Tier 1)
│   ├── agents/            # 7 Role Definitions with v05 toolsSettings
│   └── hooks/             # Autonomic Reflexes (Enclave-specific)
├── .swarm/
│   ├── plan/
│   └── audit_logs/
├── src/
│   ├── db/                # Data Architect Domain
│   ├── api/               # Backend Engineer Domain
│   ├── services/          # Backend Engineer Domain
│   ├── ui/                # Frontend Engineer Domain
│   ├── components/        # Frontend Engineer Domain
│   └── utils/             # Shared utilities
├── tests/                 # QA Engineer Domain
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── infra/                 # DevOps Engineer Domain
├── .github/workflows/     # DevOps Engineer Domain
├── docs/                  # Orchestrator Domain
│   ├── reference/         # Specifications (Tier 2)
│   └── api/
├── swarm_state.md         # THIS FILE
└── swarm_runner.py        # Meta-Orchestrator
```

### 3.3 Coding Conventions

**Style Guide:** {PEP8|StandardJS|Airbnb|Custom}

**Naming Conventions:**
- Variables: {snake_case|camelCase}
- Classes: {PascalCase}
- Constants: {UPPER_SNAKE_CASE}

**Commit Format:** {Conventional Commits|Custom}
Example: `feat(auth): add JWT token refresh`

### 3.4 Architecture Decisions

| Decision | Rationale | Alternatives Considered | Date |
|----------|-----------|------------------------|------|
| {DECISION_1} | {WHY} | {ALT_1}, {ALT_2} | {DATE} |
| {DECISION_2} | {WHY} | {ALT_1}, {ALT_2} | {DATE} |

---

## 4. Delegation Tree & Task Management (v04)

### 4.1 Active Subagent Tasks

#### Data Layer (Data Architect)
- **Task ID:** {TASK_ID}
- **Description:** {e.g., "Design and implement 'users' and 'tasks' tables"}
- **Status:** {pending|in_progress|complete|blocked|failed}
- **Assigned Agent:** `data_architect`
- **Started At:** {ISO_TIMESTAMP}
- **Completed At:** {ISO_TIMESTAMP or N/A}
- **Output Artifacts:** {List of files created}
- **Blockers:** {Spec ambiguity, dependency on external decision, etc.}

#### API Layer (Backend Engineer)
- **Task ID:** {TASK_ID}
- **Description:** {e.g., "Implement /api/auth/login and /api/auth/register endpoints"}
- **Status:** {pending|in_progress|complete|blocked|failed}
- **Assigned Agent:** `backend_engineer`
- **Dependencies:** {e.g., "Blocked until Data Architect completes DB schema"}
- **Started At:** {ISO_TIMESTAMP}
- **Completed At:** {ISO_TIMESTAMP or N/A}
- **Output Artifacts:** {List of files created}
- **Blockers:** {List or None}

#### UI Layer (Frontend Engineer)
- **Task ID:** {TASK_ID}
- **Description:** {e.g., "Build Login and Registration UI components"}
- **Status:** {pending|in_progress|complete|blocked|failed}
- **Assigned Agent:** `frontend_engineer`
- **Dependencies:** {e.g., "Blocked until Backend Engineer completes API"}
- **Started At:** {ISO_TIMESTAMP}
- **Completed At:** {ISO_TIMESTAMP or N/A}
- **Output Artifacts:** {List of files created}
- **Blockers:** {List or None}

####  Infrastructure (DevOps Engineer)
- **Task ID:** {TASK_ID}
- **Description:** {e.g., "Containerize app and set up CI/CD pipeline"}
- **Status:** {pending|in_progress|complete|blocked|failed}
- **Assigned Agent:** `devops_engineer`
- **Started At:** {ISO_TIMESTAMP}
- **Completed At:** {ISO_TIMESTAMP or N/A}
- **Output Artifacts:** {Dockerfile, docker-compose.yml, .github/workflows/deploy.yml}
- **Blockers:** {List or None}

### 4.2 QA Verification Status

- **Task ID:** {TASK_ID}
- **Description:** {e.g., "Write and run E2E tests for authentication flow"}
- **Status:** {pending|in_progress|pass|fail}
- **Assigned Agent:** `qa_engineer`
- **Test Results:**
  - **Passed:** {COUNT}
  - **Failed:** {COUNT}
  - **Coverage:** {PERCENTAGE}%
- **Failures (if any):**
  | Test | Expected | Actual | Likely Enclave | File |
  |------|----------|--------|----------------|------|
  | {TEST_NAME} | {EXPECTED} | {ACTUAL} | {backend_engineer|frontend_engineer|data_architect} | {FILE_PATH} |

### 4.3 Delegation Queue (Backlog)

| Priority | Enclave | Task ID | Description | Dependencies | Status |
|----------|---------|---------|-------------|--------------|--------|
| P0 | data_architect | {ID} | {DESC} | None | pending |
| P0 | backend_engineer | {ID} | {DESC} | data_architect:{ID} | pending |
| P1 | frontend_engineer | {ID} | {DESC} | backend_engineer:{ID} | pending |

### 4.4 Completed Subagent Tasks

- [x] {TASK_ID} | {ENCLAVE} | {DESCRIPTION} | Completed: {DATE}

---

## 5. Red Team Audit Status

### 5.1 Current Focus Areas

{requirements_clarity|architectural_feasibility|security|performance|edge_cases|enclave_drift|integration}

### 5.2 Findings Log

#### **Finding #RT-001**

- **Severity:** {Critical|High|Medium|Low}
- **Category:** {security|performance|logic|compliance|architecture|enclave_drift|integration}
- **Enclave:** {orchestrator|data_architect|backend_engineer|frontend_engineer|qa_engineer|devops_engineer}
- **Description:** {DETAILED_DESCRIPTION}
- **Affected Area:** {FILE_PATH_OR_COMPONENT}
- **Evidence:** {CODE_SNIPPET_OR_LOG}
- **Impact:** {WHAT_COULD_GO_WRONG}
- **Recommended Fix:** {SPECIFIC_GUIDANCE}
- **Status:** {Open|Fixed|Re-Validating|Closed}
- **Discovered By:** `red_team`
- **Discovered At:** {ISO_TIMESTAMP}

### 5.3 Audit Status

- **Overall Status:** {pending|in_progress|findings_reported|awaiting_fixes|re_validating|cleared}
- **Last Audit:** {ISO_TIMESTAMP}
- **Critical Findings:** {COUNT}
- **High Findings:** {COUNT}
- **Medium Findings:** {COUNT}
- **Low Findings:** {COUNT}
- **Open Findings:** {COUNT}

---

## 6. Error Handling & Recovery

### 6.1 Error Log

| Timestamp | Enclave | Error Type | Description | Recovery Action | Status |
|-----------|---------|------------|-------------|-----------------|--------|
| {TS} | {ENCLAVE} | {transient|logic|context|system|delegation} | {DESC} | {ACTION} | {resolved|pending} |

### 6.2 Checkpoint History

- **Last Successful Checkpoint:** {ISO_TIMESTAMP} - {DESCRIPTION}
- **Recovery Point:** {PHASE_OR_TASK_TO_RESUME}

### 6.3 Human Gates Pending

- [ ] {GATE_DESCRIPTION} | Required By: {PHASE} | Blocking: {yes|no} | Requested At: {TS}

---

## 7. File References

### 7.1 Steering Files (Truth Hierarchy: 1 - Highest)

**Path:** `.kiro/steering/`

| File | Applicable Enclaves | Status | Last Updated |
|------|---------------------|--------|--------------| 
| project-vision.md | All | {current|stale} | {TS} |
| tech-stack.md | All | {current|stale} | {TS} |
| conventions.md | All | {current|stale} | {TS} |
| architecture.md | All | {current|stale} | {TS} |
| db-standards.md | data_architect, backend_engineer | {current|stale} | {TS} |
| api-standards.md | backend_engineer | {current|stale} | {TS} |
| ui-standards.md | frontend_engineer | {current|stale} | {TS} |
| qa-standards.md | qa_engineer | {current|stale} | {TS} |

### 7.2 Specifications (Truth Hierarchy: 2)

**Path:** `docs/reference/`

| Spec | Applicable Enclaves | Status | Version |
|------|---------------------|--------|---------|
| {SPEC_NAME}.md | {LIST_ENCLAVES} | {draft|approved|stale} | {VERSION} |

### 7.3 Code & Tests (Truth Hierarchy: 3)

- **Data Layer:** `src/db/`, `migrations/`
- **API Layer:** `src/api/`, `src/services/`
- **UI Layer:** `src/ui/`, `src/components/`
- **Infrastructure:** `infra/`, `.github/`
- **Tests:** `tests/`
- **Overall Coverage:** {PERCENTAGE}%

### 7.4 Documentation

- **Path:** `docs/`
- **Generated:** {yes|no}

---

## 8. Metadata

- **State Version:** {SEMANTIC_VERSION}
- **Orchestrator Version:** v5.0
- **Topology:** Level 5 (Delegation Tree)
- **Active Enclaves:** {COUNT}
- **Next Scheduled Action:** {WHAT_HAPPENS_NEXT}
- **Blockers:** {LIST_OR_NONE}
- **Notes:** {ANY_ADDITIONAL_CONTEXT}