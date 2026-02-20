---
generated_by: hiveforge v2.2.0
generated_at: 2026-02-20T00:40:53.512741+00:00
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
patterns: ["src/ui/**", "src/components/**", "src/pages/**", "src/app/**", "**/*.tsx", "**/*.jsx"]
priority: 2
description: "UI component design rules. Only loaded when working on frontend code."---

# UI Standards & Conventions

## Component Structure
- One component per file
- Use functional components (not class components)
- Props first, hooks second, handlers third, render last

## Naming Conventions
- Components: PascalCase (`UserProfile.tsx`)
- Props interfaces: `{Component}Props` (`UserProfileProps`)
- Hooks: use prefix (`useAuth`, `useFetch`)
- Event handlers: `handle{Event}` (`handleClick`, `handleSubmit`)

## State Management
- Local state: `useState` for component-specific
- Global state: Context API or Redux/Zustand for app-wide
- Server state: React Query or SWR for API data

## Styling
- CSS Modules or Tailwind CSS (as defined in tech-stack.md)
- NO inline styles (except dynamic values)
- Use design tokens for colors, spacing, typography

## Accessibility
- All interactive elements must have `aria-label` or visible text
- Forms must have proper labels
- Color contrast ratio: minimum WCAG AA

## Performance
- Lazy load routes and heavy components
- Memoize expensive computations with `useMemo`
- Debounce search inputs

## Testing
- Every component needs tests (Jest + React Testing Library)
- Test user behavior, not implementation details