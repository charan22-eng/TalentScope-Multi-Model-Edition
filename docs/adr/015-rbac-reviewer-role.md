# ADR-015: Formalization of the Reviewer Role in RBAC Matrix

## Status
Accepted

## Context
TalentScope implements human-in-the-loop oversight for automated algorithmic recommendations. In Stage L3 and Stage N, an uncertainty-first review queue was introduced (`/api/v2/review/queue` and `/api/v2/review/{review_id}/decision`) to allow compliance officers, ethics monitors, and HR specialists to review low-confidence, high-entropy, or split-decision model predictions before final adverse personnel actions are executed.

To support this operational function without granting full HR management or administrative privileges, a dedicated fifth role (`reviewer`) was introduced alongside `admin`, `hr_manager`, `analyst`, and `viewer`.

## Decision
1. **Formalize `reviewer` as a First-Class Role**:
   - `reviewer` is defined in the RBAC hierarchy: `admin > hr_manager > reviewer >= analyst > viewer`.
2. **Access Permissions**:
   - **Allowed**:
     - Read model cards and metadata (`GET /api/v2/models`, `/api/v2/models/versions`).
     - Access explainability tools (`POST /api/v2/explain`, `POST /explain`).
     - Access review queue (`GET /api/v2/review/queue`).
     - Submit review decisions with mandatory reason (`POST /api/v2/review/{review_id}/decision`).
     - View review analytics (`GET /api/v2/review/analytics`).
     - View drift status (`GET /api/v2/drift/status`).
     - View comparisons and visualizers (`GET /api/v2/compare/{topic}`, `GET /api/v2/viz/*`).
     - LLM verdict inspection (`GET /api/v2/llm/verdicts/{id}`).
     - Self logout (`POST /logout`, `POST /api/v2/auth/logout`).
   - **Forbidden (403 Forbidden)**:
     - Direct model predictions (`POST /api/v2/predict`, `/predict`, `/api/v2/predict/all`).
     - Batch upload predictions (`POST /batch`, `POST /api/v2/batch`).
     - Champion promotion / rollback (`POST /api/v2/models/approve-champion`, `rollback`).
     - Feature flag mutation (`POST /api/v2/admin/feature-flags`).
     - Retraining trigger (`POST /api/v2/retrain`).
     - Privacy data erasure (`POST /api/v2/privacy/delete-request`).
     - Employee transparency record inspection (`GET /api/v2/transparency/employee/{id}`).
3. **Database & Seed Alignment**:
   - Seeded default reviewer user: `reviewer@test.com` with role `reviewer`.

## Consequences
- Strict least-privilege boundary: reviewers cannot trigger mass batch inferences or modify platform configuration.
- Full auditability: every human override records `reviewer_email` in the immutable `ReviewDecision` and `AuditLog` tables.
