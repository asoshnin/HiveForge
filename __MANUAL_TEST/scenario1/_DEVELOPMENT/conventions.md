# Coding Conventions

## Python (Backend)
- Use snake_case for variables and functions
- Use PascalCase for classes
- Type hints required for all function signatures
- Docstrings required for all public functions
- Line length: 100 characters
- Use Black for formatting
- Use Ruff for linting

## TypeScript (Frontend)
- Use camelCase for variables and functions
- Use PascalCase for components and types
- Prefer functional components with hooks
- Use ESLint with Airbnb config
- Use Prettier for formatting
- Line length: 100 characters

## Testing
- Minimum 80% code coverage
- Unit tests for all business logic
- Integration tests for API endpoints
- E2E tests for critical user flows
- Use pytest for Python
- Use Jest and React Testing Library for TypeScript

## Git Workflow
- Feature branches: feature/description
- Commit format: type(scope): description
- Types: feat, fix, docs, style, refactor, test, chore
- Squash commits before merging
- Require code review before merge
