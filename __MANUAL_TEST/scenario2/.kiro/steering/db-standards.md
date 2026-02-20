---
generated_by: hiveforge v2.2.0
generated_at: 2026-02-20T00:40:53.512552+00:00
source_documents: 0
code_analysis: true
confidence:
  overall: 0.00
  level: low
---

> ⚠️ **LOW CONFIDENCE**: This file was generated with limited source material.
> Most content is inferred from code analysis. Please review and update with actual project information.

---
inclusion: fileMatch
patterns: ["src/db/**", "migrations/**", "prisma/**", "src/api/**", "src/services/**"]
priority: 2
description: "Database design rules. Only loaded when working on data or API layer."---

# Database Standards & Conventions

## Schema Design
- **Primary Keys:** Use UUIDs (not auto-increment integers)
- **Timestamps:** Every table must have `created_at` and `updated_at`
- **Soft Deletes:** Use `deleted_at` timestamp (nullable)
- **Foreign Keys:** ALWAYS define foreign key constraints

## Naming Conventions
- Tables: plural, snake_case (`users`, `order_items`)
- Columns: snake_case (`first_name`, ` created_at`)
- Indexes: `idx_{table}_{columns}` (`idx_users_email`)
- Foreign Keys: `fk_{table}_{ref_table}` (`fk_orders_users`)

## Data Types
- **Text:** VARCHAR for bounded strings, TEXT for unbounded
- **Dates:** TIMESTAMP WITH TIME ZONE (always UTC)
- **Money:** DECIMAL(19, 4) (never FLOAT for money)
- **Booleans:** BOOLEAN (not TINYINT or CHAR)

## Migrations
- **Never edit existing migrations** - Always create new ones
- **Test migrations on staging** before production
- **Include rollback logic** in every migration

## ORM Best Practices
- Use query builders or ORM (Prisma, SQLAlchemy)
- **Avoid N+1 queries** - Use joins or `select_related`
- **Use transactions** for multi-step operations