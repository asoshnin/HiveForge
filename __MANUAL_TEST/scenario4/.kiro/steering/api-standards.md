---
generated_by: hiveforge v2.2.0
generated_at: 2026-02-20T00:40:53.769203+00:00
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
patterns: ["src/api/**", "tests/api/**", "src/**/api.py", "src/**/routes/**"]
priority: 2
description: "API naming, versioning, error handling. Only loaded when working on API code."---

# API Standards & Conventions

## Endpoint Naming
- Use plural nouns: `/users`, `/orders`
- Nested resources: `/users/{id}/orders`
- Actions as POST: `/users/{id}/reset-password`

## Versioning
- URL-based: `/api/v1/users`
- Never break existing versions

## Response Format
```json
{
  "data": {},
  "meta": {"page": 1, "total": 100},
  "errors": []
}
```

## HTTP Methods
- GET: Retrieve resource(s)
- POST: Create resource
- PUT: Replace resource (full update)
- PATCH: Partial update
- DELETE: Remove resource

## Status Codes
- 200: OK (GET, PATCH, PUT success)
- 201: Created (POST success)
- 204: No Content (DELETE success)
- 400: Bad Request (client error)
- 401: Unauthorized (not authenticated)
- 403: Forbidden (not authorized)
- 404: Not Found
- 422: Unprocessable Entity (validation error)
- 500: Internal Server Error

## Error Responses
```json
{
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "message": "Email is required",
      "field": "email"
    }
  ]
}
```

## Rate Limiting
- Header: `X-RateLimit-Remaining`
- Default: 100 req/min per user

## Authentication
- Use JWT tokens in `Authorization: Bearer {token}` header
- Refresh tokens: POST `/api/v1/auth/refresh`