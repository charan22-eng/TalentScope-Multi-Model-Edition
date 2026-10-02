# Gap Analysis & Implementation Plan (Phases 14–18)

After auditing the current project against the master specification in `Employee_Performance_KNN_Build_Phases.md`, I have identified the functional gaps. 

Phases 0 through 13 have been executed successfully (Foundations, ML Data Engineering, Model Tuning, Explainability, FastAPI Backend, React Frontend). However, to reach the production-grade state outlined in the document, Phases 14 through 18 still need to be implemented.

## 1. Gap Analysis

| Phase | Expected (per Document) | Current State in Project | Gaps |
|---|---|---|---|
| **Phase 14: Persistence & Auth** | PostgreSQL/SQLite schemas via Alembic, JWT Auth, Role-Based Access Control (RBAC), Audit logs | Skipped for local demo. | No database integration. API is open. No users or login. |
| **Phase 15: Advanced Features** | Drift detection (PSI), batch background jobs, Persona clusters page, API keys | Skipped. | Missing background job processor (e.g., Celery/BackgroundTasks) and UI for drift/keys. |
| **Phase 16: Quality** | Unit coverage > 80%, Playwright E2E tests, k6 load testing, Accessibility audits (Lighthouse/Axe) | Partial. Backend has a basic `test_api.py`. | Missing frontend E2E tests, load testing scripts, security scan checks. |
| **Phase 17: DevOps** | Dockerfiles, `docker-compose.yml`, GitHub Actions for CI/CD, Nginx proxy setup | Skipped. | No containerization. Project runs bare-metal via `uvicorn` and `npm run dev`. |
| **Phase 18: Documentation** | Final polished user guide, video demo scripts, finalized `model_card.md` | Partial. | Need to create the final handover documentation suite. |

---

## 2. Implementation Plan

To close these gaps and bring the project to full compliance with the spec, we must execute the following sequential plan.

### Iteration 1: Persistence and Security (Phase 14)
- **Task 1.1:** Initialize SQLite (for local) and PostgreSQL (for prod) using `SQLAlchemy` and `Alembic` in `backend/db/`.
- **Task 1.2:** Create DB models for `User`, `PredictionHistory`, and `AuditLog`.
- **Task 1.3:** Implement JWT Authentication in FastAPI (`backend/core/security.py`).
- **Task 1.4:** Update frontend `App.tsx` to require login and add a Role-based guard (Admin vs Reviewer).

### Iteration 2: Quality and Testing (Phase 16)
- **Task 2.1:** Expand `backend/tests/` to cover all edge cases (bad payloads, unauthorized access).
- **Task 2.2:** Set up `Playwright` in `frontend/e2e/` and write 3 core tests (Login, Single Predict, Batch Upload).
- **Task 2.3:** Run a Lighthouse audit on the frontend and fix contrast/ARIA issues.

### Iteration 3: Containerization & DevOps (Phase 17)
- **Task 3.1:** Write `backend/Dockerfile` (slim Python image) and `frontend/Dockerfile` (Node builder to Nginx static).
- **Task 3.2:** Create a root `docker-compose.yml` to orchestrate Postgres, Backend API, and Frontend Proxy.
- **Task 3.3:** Scaffold `.github/workflows/ci.yml` for automated linting and testing on PRs.

### Iteration 4: Advanced Features & Handover (Phases 15 & 18)
- **Task 4.1:** Implement a simple Drift Detection route that compares live payloads to `train_stats.json`.
- **Task 4.2:** Finalize the `docs/user_guide.md` and complete the `docs/model_card.md`.
- **Task 4.3:** Freeze `v1.0` and prepare demo scripts.
