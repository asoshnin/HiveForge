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
- Props interfaces: `**В руководстве по UI-стандартам (`ui-standards.md`) закреплены следующие паттерны:** создание одного функционального компонента на файл со строгим порядком (пропсы, хуки, обработчики, рендер), использование PascalCase для компонентов и типов пропсов, префиксов `use` для хуков и `handle` для обработчиков событий, управление локальным состоянием через `useState`, глобальным через Redux/Zustand, а серверным через React Query/SWR, стилизация с помощью CSS Modules или Tailwind без использования инлайн-стилей, обязательное обеспечение доступности (наличие `aria-label` и минимальный контраст WCAG AA), оптимизация (ленивая загрузка, `useMemo`, debounce), а также обязательное тестирование поведения компонентов с помощью Jest и React Testing Library.Props` (`UserProfileProps`)
- Hooks: use prefix (`useAuth`, `useFetch`)
- Event handlers: `handle**В руководстве по UI-стандартам (`ui-standards.md`) закреплены следующие паттерны:** создание одного функционального компонента на файл со строгим порядком (пропсы, хуки, обработчики, рендер), использование PascalCase для компонентов и типов пропсов, префиксов `use` для хуков и `handle` для обработчиков событий, управление локальным состоянием через `useState`, глобальным через Redux/Zustand, а серверным через React Query/SWR, стилизация с помощью CSS Modules или Tailwind без использования инлайн-стилей, обязательное обеспечение доступности (наличие `aria-label` и минимальный контраст WCAG AA), оптимизация (ленивая загрузка, `useMemo`, debounce), а также обязательное тестирование поведения компонентов с помощью Jest и React Testing Library.` (`handleClick`, `handleSubmit`)

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