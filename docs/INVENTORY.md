# Codebase Inventory and Classification

Classification taxonomy:
- **KEEP**: Compliant with architecture, preserved as-is or with minor standard updates.
- **REFACTOR**: Active component requiring modification to support the 7-model arena, API v2, or updated contracts.
- **REMOVE**: Obsolete, duplicate, dead code, or superseded implementation.
- **SECURITY-REVIEW**: Contains authentication, authorization, or sensitive logic requiring audit and remediation.

---

## 1. Backend Routes

| Route | File | Method | Classification | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `/health` | `backend/app/main.py` | GET | **KEEP** | Standard health check. |
| `/version` | `backend/app/main.py` | GET | **REFACTOR** | Update to report v2 model bundle status. |
| `/login` | `backend/app/main.py` | POST | **SECURITY-REVIEW** | Uses OAuth2 password flow; audit password verify & JWT. |
| `/predict` | `backend/app/main.py` | POST | **KEEP** | Serves v1 backward-compatible predictions (default KNN). |
| `/analytics/drift` | `backend/app/main.py` | GET | **REFACTOR** | Currently simple summary; upgrade to multi-model PSI/KS in Stage L. |
| `/explain` | `backend/app/main.py` | POST | **KEEP** | Serves v1 backward-compatible KNN explanations. |
| `/batch` | `backend/app/main.py` | POST | **REFACTOR** | Add multi-model support (5000x7 rows, disagreement filter). |
| `/batch/report/pdf` | `backend/app/main.py` | GET | **REFACTOR** | PDF export using ReportLab; update to include model version disclaimers. |
| `/viz/galaxy` | `backend/app/main.py` | GET | **REFACTOR** | Serves 2D/3D background projection. |
| `/viz/surface` | `backend/app/main.py` | GET | **REFACTOR** | Currently stubbed; implement full decision surface grid for v2. |
| `/analytics` | `backend/app/main.py` | GET | **REFACTOR** | Stubbed; integrate Arena comparison metrics. |
| `/analytics/constellation` | `backend/app/main.py` | GET | **REMOVE** | Stubbed legacy route not in v2 specification. |
| `/drift/projection` | `backend/app/main.py` | GET | **REMOVE** | Stubbed legacy route; replaced by `/analytics/drift`. |
| Legacy root routes | `backend/main.py` | ALL | **REMOVE** | Obsolete root file containing hardcoded admin credentials. `backend/app/main.py` is authoritative. |

---

## 2. Database Models

| Model | File | Classification | Notes |
| :--- | :--- | :--- | :--- |
| `User` | `backend/db/models.py` | **SECURITY-REVIEW** | Basic email, hashed_password, role. Needs extension for RBAC roles (Admin, HR Manager, Analyst, Viewer) in Stage L. |
| `PredictionHistory` | `backend/db/models.py` | **REFACTOR** | Needs `model_key` field to distinguish 7 models and consensus flags. |

---

## 3. Core Security & Auth

| Component | File | Classification | Notes |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | `backend/core/security.py` | **SECURITY-REVIEW** | Currently defaults to hardcoded dummy secret. Must read from `JWT_SECRET_KEY` env var with refusal if unset in production. |
| `create_access_token` | `backend/core/security.py` | **SECURITY-REVIEW** | Expiry default set to 15 min; reconcile with `ACCESS_TOKEN_EXPIRE_MINUTES` (30 min). |
| `authenticate_user` | `backend/core/security.py` | **SECURITY-REVIEW** | Bcrypt verify logic is sound; ensure constant-time comparison. |
| `get_current_user_email` | `backend/core/security.py` | **SECURITY-REVIEW** | Token verification dependency; extend to return full user claims for RBAC. |

---

## 4. Frontend Pages & Navigation

| Page | File | Classification | Notes |
| :--- | :--- | :--- | :--- |
| `Predict` | `frontend/src/pages/Predict.tsx` | **REFACTOR** | Add model selector, 7-model consensus panel, agreement meter, champion badge. |
| `Batch` | `frontend/src/pages/Batch.tsx` | **REFACTOR** | Add multi-model columns, disagreement filter, 5000-row batching. |
| `ModelLab` | `frontend/src/pages/ModelLab.tsx` | **REFACTOR** | Add server-side tuning with "experimental, not deployed" banner. |
| `Dashboard` | `frontend/src/pages/Dashboard.tsx` | **REFACTOR** | Add champion KPI, agreement rate, Arena link. |
| `Login` | `frontend/src/pages/Login.tsx` | **KEEP** | Clean auth form; integrate with token storage. |
| `Methodology` | `frontend/src/pages/Methodology.tsx` | **REFACTOR** | Render 7 model cards and datasheet v2. |
| `DataExplorer` | `frontend/src/pages/DataExplorer.tsx` | **REFACTOR** | Integrate 12,000-row dataset v2 exploration. |
| *Arena Pages* | `frontend/src/pages/arena/*` | **[NEW]** | Overview, Priorities, Head-to-head, Deep Dive, Cost/Speed, Sensitivity, Explain, Fairness, LLM Verdict. |

---

## 5. Frontend Components & 3D

| Component | File | Classification | Notes |
| :--- | :--- | :--- | :--- |
| `Button`, `Card` | `frontend/src/components/*` | **KEEP** | Shared UI primitives. |
| `SceneFrame` | `frontend/src/components/three/SceneFrame.tsx` | **REFACTOR** | Replace `any` types with Three.js types; add 2-surface overlay support and difference surface. |
| `ModelChip` | `frontend/src/components/ModelChip.tsx` | **[NEW]** | Okabe-Ito color + distinct shape glyph + model label. |

---

## 6. Scripts & Tooling

| Script | File | Classification | Notes |
| :--- | :--- | :--- | :--- |
| `redflags.py` | `scripts/redflags.py` | **KEEP** | Core security and hygiene audit. |
| `collect_evidence.py` | `scripts/collect_evidence.py` | **KEEP** | Evidence collector for verification. |
| `build_review_bundle.py` | `scripts/build_review_bundle.py` | **KEEP** | Monorepo review bundler. |
| `generate_phase4_assets.py` | `scripts/generate_phase4_assets.py` | **REFACTOR** | Legacy asset generator; replace with v2 pipeline generators. |
| `guard.py` | `scripts/guard.py` | **[NEW]** | Invariant guard suite runner for `make guard`. |

---

## 7. Automated Tests

| Test Suite | Path | Classification | Notes |
| :--- | :--- | :--- | :--- |
| `test_data_contract.py` | `ml/tests/test_data_contract.py` | **KEEP** | Contract tests on frozen dataset v2 (12,000 rows). |
| `test_features.py` | `ml/tests/test_features.py` | **REFACTOR** | Upgrade for `build_preprocessor(spec)` and leakage tests. |
| `test_train.py` | `ml/tests/test_train.py` | **REFACTOR** | Upgrade to test 7 models and `ScoreToBand`. |
| `test_api.py` | `backend/tests/test_api.py` | **REFACTOR** | Obligation O1: resolve skipif and add v2 API test suite. |
| `components.test.tsx` | `frontend/src/components.test.tsx` | **KEEP** | Vitest component unit test. |
| `predict.spec.ts` | `frontend/tests/predict.spec.ts` | **REFACTOR** | Remove `console.log` debugging lines; update for v2 UI. |
| `e2e.spec.ts`, `screenshots.spec.ts` | `frontend/tests/*` | **REFACTOR** | Expand to cover Model Arena navigation. |
