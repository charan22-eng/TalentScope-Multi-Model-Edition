# RUN

## Prerequisites
- Python 3.11+
- Node.js 24+
- `uv` and `npm` installed
- PostgreSQL (or use SQLite/fallback)

## Installation
Run a single setup command:
```bash
make setup
```

## Running Locally
**Terminal 1 (Backend API)**
```bash
make api
```
API runs on `http://localhost:8000`

**Terminal 2 (Frontend Web App)**
```bash
make web
```
Web app runs on `http://localhost:5173`

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
- Verify environment variables using `verify-env` (to be added).
- Check `project/qa-evidence/` for failed playwright screenshots.
