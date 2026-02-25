---
inclusion: always
priority: 1
description: "System design, component responsibilities, data flow."
---

# Architecture Overview

## System Diagram
```mermaid
graph TD
    User -->|HTTP| API_Gateway
    API_Gateway -->|RPC| App_Server
    App_Server -->|Query| Database
    App_Server -->|Cache| Redis
```

## Component Responsibilities

### {Component 1}
- **Responsibility:** {What it does}
- **Interface:** {How others talk to it}
- **Dependencies:** {What it needs}

### {Component 2}
- **Responsibility:** {What it does}
- **Interface:** {How others talk to it}
- **Dependencies:** {What it needs}

## Data Flow
1. {Step 1}
2. {Step 2}
3. {Step 3}

## Key Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| {Decision} | {Why} | {What we gave up} |

## Scalability Considerations
- {How we handle growth}
- {Bottlenecks to watch}