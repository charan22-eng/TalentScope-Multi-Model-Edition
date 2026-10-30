# RUN

## Prerequisites
- Python 3.11+
- Node.js 24+
- `uv` and `npm` installed
- PostgreSQL (or use SQLite/fallback)

## Installation
For a review demo, run the setup command from the repository root:
```bash
uv run python scripts/demo_setup.py
```

This creates a local `.env`, chooses an installed Ollama model when available,
checks the governed V2 artifacts, and seeds the SQLite database. It does not
download models.

## Running Locally
**Terminal 1 (Backend API)**
```bash
make api
```
API runs on `http://localhost:8000`

**Terminal 2 (Frontend Web App)**
```bash
cd frontend
npm run dev
```
Web app runs on `http://localhost:5173`

**Terminal 3 (review smoke test)**
```bash
uv run python scripts/demo_smoke.py
```

## Testing
```bash
make test
```
Runs backend unit tests and frontend tests.

## Linting
```bash
make lint
```

## Troubleshooting
- If `uv` fails to resolve, make sure it is updated.
- If Ollama is offline, the core prediction flow still works and LLM verdicts
  use the deterministic template fallback.
- Check `GET http://localhost:8000/ready` before opening the frontend.
- Check `project/qa-evidence/` for failed Playwright screenshots.
