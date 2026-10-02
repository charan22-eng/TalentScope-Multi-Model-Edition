# 04 Bootstrap Summary (Phase 0)

## Repository
- Git initialized.
- `.gitignore` added for Python, Node, OS, and project-specific artifacts.

## Toolchain
- **Python Backend & ML**: Python 3.11+, `uv` for dependency management. `backend/requirements.txt` and `ml/pyproject.toml` created.
- **Frontend**: Scaffolding with `npm create vite@latest frontend --template react-ts`.

## Quality Tooling
- `ruff` and `black` for Python linting and formatting.
- `eslint` (via oxlint/vite) for TypeScript.

## Test Harnesses
- `pytest` for Python backend and ML.
- Dummy tests created and passing.

## Configuration
- `.env.example` created.
- `Makefile` created with standard targets (`setup`, `lint`, `test`, `data`, `train`, `api`, `web`).
- `RUN.md` added.

**Definition of Done:** 
- [x] Clean install, one-command start and health check (skeleton) verified.
- [x] Lint, unit harnesses run end to end.
- [x] `.env.example` and `RUN.md` complete and accurate.
- [x] Git initialised with a committed baseline.
