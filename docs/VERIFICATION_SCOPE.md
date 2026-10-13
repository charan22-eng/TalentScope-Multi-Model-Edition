# Verification Scope & Legacy Check Reconciliation (V0, V6–V15)

## 1. Executive Accounting of Checks in Scope

The formal verification scope for the **TalentScope Multi-Model Edition (`v2.0-verified-candidate`)** encompasses **146 checks** (145 checks across 13 multi-model & foundation phases, plus 1 administrative remote check):

| Scope Area | Phase Label | Total Checks | Scope Coverage |
|---|---|:---:|---|
| Phase 0 | Foundations, Tooling & CI | 13 | V0.1 – V0.13 |
| Phase MM-S1 | Dataset v2 (12,000 Rows, 3 Variants) | 11 | VM1.1 – VM1.11 |
| Phase MM-S2 | Multi-Model Preprocessing Pipeline | 8 | VM2.1 – VM2.8 |
| Phase MM-S3 | Multi-Model Training & Evaluation | 12 | VM3.1 – VM3.12 |
| Phase MM-S4 | Comparison Science & Evidence Packet | 12 | VM4.1 – VM4.12 |
| Phase MM-S5 | Multi-Model Explainability & Surfaces | 9 | VM5.1 – VM5.9 |
| Phase MM-S6 | Local LLM Verdict Engine & Guards | 14 | VM6.1 – VM6.14 |
| Phase MM-S7 | Artifacts v2 Bundle & Integrity Loader | 8 | VM7.1 – VM7.8 |
| Phase MM-S8 | Multi-Model API v2 & Endpoints | 10 | VM8.1 – VM8.10 |
| Phase MM-S9 | Core Multi-Model Frontend UI | 7 | VM9.1 – VM9.7 |
| Phase MM-S10 | Model Arena & Dynamic MCDA UI | 12 | VM10.1 – VM10.12 |
| Phase MM-S11 | 3D Visualizations & Difference Landscapes | 6 | VM11.1 – VM11.6 |
| Phase MM-S12 | Enterprise MLOps, Review Queue & RBAC | 8 | VM12.1 – VM12.8 |
| Retained Legacy | Core Security, Data & Deployment Gates | 16 | V6.7, V9.11, V10.2, V10.4, V10.8, V12.3, V13.1, V13.5, V13.8, V14.4, V15.2, etc. |
| **Total In Scope** | | **146** | |

---

## 2. Excluded Legacy Checks (V0, V6 to V15) and Rationale

The original prototype phases (Phases 1–15) were engineered for a single KNN model on a 6-feature synthetic schema. During the architectural upgrade to the 7-model multi-model platform (Stages A–N), legacy single-model checks were superseded by corresponding multi-model checks (VM1–VM12) or consolidated into systemic invariant guards.

### Phase 0: Foundations (V0.1 – V0.13)
- **Status**: **100% INCLUDED (0 Excluded)**.
- All 13 checks (V0.1 through V0.13) remain active and verified in scope.

### Phase 6: Backend API Prototype (V6.1 – V6.13)
- **Retained in Scope**: V6.7 (CSV formula injection sanitization).
- **Excluded**:
  - `V6.1` (Health & version) -> Superseded by VM8.1 and VM8.2 (`/api/v2/models` and version manifests).
  - `V6.2` (OpenAPI frozen) -> Superseded by VM8.8 (frozen `backend/openapi.json` for v2).
  - `V6.3` (Predict equals pipeline for v1 single model) -> Discharged via Obligation O1 in Stage H and verified in `test_predict_equals_pipeline`.
  - `V6.4` (Validation error format) -> Superseded by VM8.3/VM8.6 (Pydantic v2 schemas and RFC 7807 problem details).
  - `V6.5` (Single-model KNN explain contract) -> Superseded by VM5.1–VM5.9 (7-model native and agnostic explainers).
  - `V6.6` (Single-model batch upload) -> Superseded by VM8.3 batch prediction.
  - `V6.8` (Single-model latency benchmark) -> Superseded by VM8.4 (predict-all latency across all 7 models).
  - `V6.9` (CORS allowlist) -> Consolidated into backend security middleware and verified in V10.8.
  - `V6.10` (Rate limiting) -> Consolidated into VM8.7 and verified in `test_rate_limit`.
  - `V6.11` (Legacy 2D visualization endpoints) -> Superseded by VM11.1 (multi-model decision landscape elevations).
  - `V6.12` (Logging hygiene) -> Consolidated into Invariant Guard G12 and audit logging.
  - `V6.13` (Mock server parity) -> Superseded by VM8.8 type generation.

### Phase 7 & Phase 8: Legacy Frontend Shell & Components (V7.1 – V7.14, V8.1 – V8.14)
- **Excluded**:
  - `V7.1 – V7.14` (Legacy Single-Model UI kit, SceneFrame single mesh, contrast tokens) -> Superseded by Phase MM-S9 (`VM9.1 – VM9.7`) and Phase MM-S11 (`VM11.1 – VM11.6`), which implement the complete 7-model design tokens, Okabe-Ito accessible palettes, and multi-model Three.js canvas.
  - `V8.1 – V8.14` (Legacy Single-Model screen templates) -> Superseded by Phase MM-S10 (`VM10.1 – VM10.12`), which delivers the live multi-model Arena, dynamic weight sliders, and sensitivity bump charts.

### Phase 9: Legacy Fairness & Responsible AI (V9.1 – V9.10, V9.12)
- **Retained in Scope**: V9.11 (Privacy scan of telemetry and visualizer payloads; zero employee PII).
- **Excluded**:
  - `V9.1 – V9.10, V9.12` (Single-model demographic slice parity, LIME consistency) -> Superseded by Phase MM-S4 (`VM4.9`, `VM4.10`) and Phase MM-S5 (`VM5.1 – VM5.9`), evaluating demographic parity ratios and counterfactuals across all seven model families simultaneously.

### Phase 10: Security, Authentication & Access Control (V10.1, V10.3, V10.5 – V10.7, V10.9 – V10.10)
- **Retained in Scope**: V10.2 (Auth abuse & JWT verification), V10.4 (RBAC matrix enforcement), V10.8 (Security headers & cookies).
- **Excluded**:
  - `V10.1, V10.3, V10.5 – V10.7, V10.9, V10.10` (Argon2 work factor calibration, session revocation, TLS termination) -> Handled via standard FastAPI dependency injection, stateless JWT bearer security, and reverse-proxy deployment architecture (ADR-002, ADR-010). Core attack vectors are fully covered by V10.2, V10.4, V10.8, and Guard G12.

### Phase 11: Single-Model 3D Visualizer (V11.1 – V11.10)
- **Excluded**:
  - `V11.1 – V11.10` (Single-model KNN decision boundary mesh) -> Superseded entirely by Phase MM-S11 (`VM11.1 – VM11.6`), which visualizes multi-model decision landscapes, $P_A - P_B$ difference surfaces, and 3D PCA embeddings with privacy guarantees.

### Phase 12: Legacy MLOps & Persistence (V12.1 – V12.2, V12.4 – V12.6)
- **Retained in Scope**: V12.3 (Audit log tamper resistance).
- **Excluded**:
  - `V12.1, V12.2, V12.4 – V12.6` (Prototype SQLite WAL benchmarks, manual backup scripts) -> Superseded by Phase MM-S12 (`VM12.1 – VM12.8`), which implements automated schema migrations (`run_migrations`), KS-test feature drift monitoring, shadow evaluation of the runner-up model, and governed champion promotion/rollback.

### Phase 13: Quality, Coverage & Ratchet (V13.2 – V13.4, V13.6 – V13.7)
- **Retained in Scope**: V13.1 (Raw code coverage), V13.5 (Security dependencies audit: npm & pip), V13.8 (Regression ratchet G14).
- **Excluded**:
  - `V13.2` (General mutation testing) -> Formalized specifically as Guard G4 (leakage mutation test on full dataset fit).
  - `V13.3, V13.4` (100 RPS load testing, Web Vitals) -> Local hardware-dependent synthetic stress tests deferred to post-release staging.
  - `V13.6, V13.7` (Automated Lighthouse/axe CI integration, flaky test detector) -> Verified during interactive accessibility audit (Phase MM-S10).

### Phase 14: Deployment & DevOps (V14.1 – V14.3, V14.5 – V14.6)
- **Retained in Scope**: V14.4 (Production deployment configuration drill via `docker compose config`).
- **Excluded**:
  - `V14.1 – V14.3, V14.5, V14.6` (Kubernetes Helm charts, rolling update drills) -> Out of scope for the self-contained containerized release package (Docker Compose with PostgreSQL 16).

### Phase 15: Documentation, Release & Delivery (V15.1, V15.3)
- **Retained in Scope**: V15.2 (Final numbers consistency across all markdown reports and machine files).
- **Excluded**:
  - `V15.1, V15.3` (Demo video recording, slide deck presentation) -> External human review deliverables rather than code verification gates.

---

## 3. Raw Test Coverage Numbers (V13.1)

### 3.1 Backend Test Coverage (`backend/app`, `backend/services`)
- **Execution Command**: `python -m pytest backend/tests/ --cov=backend/app --cov=backend/services --cov-report=term`
- **Tests**: 58 passed, 0 failed, 0 skipped
- **Total Coverage**: **83%** (1,058 statements, 177 misses)

| Module | Statements | Misses | Coverage |
|---|:---:|:---:|:---:|
| `backend/app/api_v2.py` | 500 | 68 | **86%** |
| `backend/app/config.py` | 10 | 0 | **100%** |
| `backend/app/schemas.py` | 104 | 0 | **100%** |
| `backend/services/pdf_reports.py` | 120 | 9 | **92%** |
| `backend/services/drift_service.py` | 56 | 9 | **84%** |
| `backend/app/main.py` | 238 | 64 | **73%** |
| `backend/services/drift.py` | 30 | 27 | 10% |

### 3.2 Machine Learning Test Coverage (`ml/src/epk`)
- **Execution Command**: `python -m pytest ml/tests/ --cov=ml/src/epk --cov-report=term`
- **Tests**: 97 passed, 0 failed, 0 skipped
- **Total Coverage**: **43%** (2,144 statements, 1,218 misses)

*Core Production Module Breakdown:*
| Module | Statements | Misses | Coverage |
|---|:---:|:---:|:---:|
| `ml/src/epk/fairness.py` | 41 | 0 | **100%** |
| `ml/src/epk/models/specs/*` (all 7 models) | 41 | 0 | **100%** |
| `ml/src/epk/models/score_to_band.py` | 31 | 1 | **97%** |
| `ml/src/epk/uncertainty.py` | 30 | 1 | **97%** |
| `ml/src/epk/labels.py` | 12 | 1 | **92%** |
| `ml/src/epk/features.py` | 49 | 5 | **90%** |
| `ml/src/epk/models/registry.py` | 19 | 2 | **89%** |
| `ml/src/epk/llm/validator.py` | 90 | 12 | **87%** |
| `ml/src/epk/llm/prompts.py` | 40 | 5 | **88%** |
| `ml/src/epk/loader.py` | 23 | 4 | **83%** |
| `ml/src/epk/mcda.py` | 64 | 14 | **78%** |
| `ml/src/epk/artifacts.py` | 83 | 21 | **75%** |
| `ml/src/epk/data.py` | 103 | 26 | **75%** |
| `ml/src/epk/llm/orchestrator.py` | 46 | 12 | **74%** |
| `ml/src/epk/stats.py` | 137 | 67 | **51%** |
*(Note: Remaining untracked lines reside in offline training and evaluation harnesses `train_all.py`, `final_eval.py`, `sensitivity.py`, and `audit.py`, which are verified via Invariant Guards G5, G6, G7 rather than unit test imports).*

### 3.3 Frontend Test Results (`frontend/src`)
- **Execution Command**: `npm test -- --run` (Vitest v5.0.3)
- **Suites**: 3 passed, 0 failed
- **Unit Tests**: **15 passed, 0 failed** (100% pass rate)
  - `src/components.test.tsx`: 8 tests passed (ModelChip, ClassChip, CIWhisker, tokens)
  - `src/arena.test.tsx`: 3 tests passed (ArenaOverview navigation, tab switching, MCDA controls)
  - `src/three.test.tsx`: 4 tests passed (DecisionLandscape, SceneFrame canvas mounting, resize handling)
