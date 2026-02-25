---
inclusion: fileMatch
patterns: ["src/api/**", "tests/api/**", "src/**/api.py", "src/**/routes/**"]
priority: 2
description: "API naming, versioning, error handling. Only loaded when working on API code."---

# API Standards & Conventions

## Endpoint Naming
- Use plural nouns: `/users`, `/orders`
- Nested resources: `/users/## Error Handling

The LLMProvider handles errors gracefully:

- **KIRO native fails**: Falls back to Vertex AI → OpenAI → None
- **Vertex AI fails**: Falls back to OpenAI → None
- **OpenAI fails**: Returns None
- **All fail**: Returns None, caller uses `[INFERRED]` markers

All failures are logged at WARNING level with details about the error.
/orders`
- Actions as POST: `/users/## Error Handling

The LLMProvider handles errors gracefully:

- **KIRO native fails**: Falls back to Vertex AI → OpenAI → None
- **Vertex AI fails**: Falls back to OpenAI → None
- **OpenAI fails**: Returns None
- **All fail**: Returns None, caller uses `[INFERRED]` markers

All failures are logged at WARNING level with details about the error.
/reset-password`

## Versioning
- URL-based: `/api/v1/users`
- Never break existing versions

## Response Format
```json
## Error Handling

The LLMProvider handles errors gracefully:

- **KIRO native fails**: Falls back to Vertex AI → OpenAI → None
- **Vertex AI fails**: Falls back to OpenAI → None
- **OpenAI fails**: Returns None
- **All fail**: Returns None, caller uses `[INFERRED]` markers

All failures are logged at WARNING level with details about the error.
,
  "meta": ## Error Handling

The LLMProvider handles errors gracefully:

- **KIRO native fails**: Falls back to Vertex AI → OpenAI → None
- **Vertex AI fails**: Falls back to OpenAI → None
- **OpenAI fails**: Returns None
- **All fail**: Returns None, caller uses `[INFERRED]` markers

All failures are logged at WARNING level with details about the error.
,
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
## Error Handling

The LLMProvider handles errors gracefully:

- **KIRO native fails**: Falls back to Vertex AI → OpenAI → None
- **Vertex AI fails**: Falls back to OpenAI → None
- **OpenAI fails**: Returns None
- **All fail**: Returns None, caller uses `[INFERRED]` markers

All failures are logged at WARNING level with details about the error.

  ]
}
```

## Rate Limiting
- Header: `X-RateLimit-Remaining`
- Default: 100 req/min per user

## Authentication
- Use JWT tokens in `Authorization: Bearer ## Error Handling

The LLMProvider handles errors gracefully:

- **KIRO native fails**: Falls back to Vertex AI → OpenAI → None
- **Vertex AI fails**: Falls back to OpenAI → None
- **OpenAI fails**: Returns None
- **All fail**: Returns None, caller uses `[INFERRED]` markers

All failures are logged at WARNING level with details about the error.
` header
- Refresh tokens: POST `/api/v1/auth/refresh`