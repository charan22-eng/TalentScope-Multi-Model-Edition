# Frontend Kit

This document describes the foundation for the TalentScope UI.

## Tokens and Theming
- Uses standard CSS variables for the color palette (`Aurora Dark` defaults, with `Clean Light`).
- Theme persistence is managed via `localStorage` and a top-level `data-theme` attribute on the `<html>` element.

## Components
- `ClassChip`: A small status indicator avoiding color-only indicators (per WCAG specs), including standard `lucide-react` icons (CheckCircle, AlertCircle, HelpCircle).
- `SceneFrame`: A lazy-loaded safety boundary for React-Three-Fiber.
  - Contains memory disposal hooks to prevent WebGL context leaks during route changes.
  - Listens to `prefers-reduced-motion` and automatically hides the Canvas with a fallback UI.
  - Exposes quality tier selections (low/high/off).
  - Handles WebGL context loss dynamically.

## Networking
- Open API spec generated into typed client logic via `openapi-typescript`.

## Accessibility (A11y)
- The shell meets baseline Axe automated checks.
- Contrast ratios are handled by strictly separated background and text semantic variables (`--text-primary` on `--bg-primary`).
