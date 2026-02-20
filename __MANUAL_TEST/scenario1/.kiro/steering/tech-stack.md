---
generated_by: hiveforge v2.2.0
generated_at: 2026-02-20T00:40:53.029938+00:00
source_documents: 3
source_docs_path: _DEVELOPMENT
code_analysis: true
confidence:
  overall: 1.00
  level: high
  sources:
    documents: 1.00
    code_analysis: 0.00
    inferred: 0.00
---
---
inclusion: always
priority: 1
description: "Approved technologies and dependencies. Changes require architecture review."---

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