# Repository Guidelines

## Project Structure & Module Organization
`backend/` contains the FastAPI service (entrypoint: `backend/main.py`) with layered modules:
- `api/v1/` for route handlers
- `application/services/` for business logic
- `infrastructure/` for DuckDB, ML registry, caching, and repositories
- `domain/` for schemas and domain errors

`frontend/` is a Next.js 16 app:
- `app/` for routes and layouts
- `components/` for UI and feature components
- `lib/` for API clients, types, and shared utilities
- `public/` for static assets

`docs/` holds product/architecture/testing notes. Use `docs/new-feature-ideas/` for new requirement drafts.

## Build, Test, and Development Commands
Backend (`cd backend`):
- `poetry install` installs Python dependencies.
- `poetry run uvicorn main:app --reload --port 8000` runs API locally.

Frontend (`cd frontend`):
- `npm install` installs JS dependencies.
- `npm run dev` starts local UI on `http://localhost:3000`.
- `npm run build` creates production build.
- `npm run start` serves production build.
- `npm run lint` runs ESLint.

## Coding Style & Naming Conventions
Python: 4-space indentation, `snake_case` for files/functions/variables, `PascalCase` for classes, and explicit typing for public interfaces.

TypeScript/React: strict TS is enabled (`frontend/tsconfig.json`), `PascalCase` components, `camelCase` variables/functions, and `kebab-case` filenames for component files (for example, `portfolio-search.tsx`).

Keep modules focused and place reusable UI primitives under `frontend/components/ui/`.

## Testing Guidelines
Current automated tests are limited; add tests with each non-trivial change.
- Backend: use `pytest` and `pytest-cov` (target from strategy doc: ~80% overall coverage).
- Frontend: add component/page tests when introducing complex UI logic.

Preferred naming:
- Backend: `backend/tests/test_<feature>.py`
- Frontend: `frontend/**/__tests__/*.test.ts(x)`

## Commit & Pull Request Guidelines
Follow Conventional Commits for release automation:
- `feat: ...`, `fix: ...`, `chore: ...`
- Use `feat!:` or `BREAKING CHANGE:` for major changes.

Branch flow is enforced by CI:
- PRs to `master` must come from `dev`
- PRs to `prod` must come from `master`

PRs should include: scope summary, linked issue (if available), validation steps, and screenshots for UI changes.

