# ADR-010: Reconciling Legacy Code with Multi-Model Architecture

## Status
Accepted

## Date
2026-10-12

## Context
During earlier prototype development phases (Phases 7 and 8), substantial frontend and backend code was integrated in bulk without full architectural audit. This legacy code included:
1. Root application stub (`backend/main.py`) containing hardcoded default admin credentials (`admin@hr.local` / `admin123`) and placeholder classification logic.
2. Hardcoded fallback secrets in `backend/core/security.py`.
3. Incomplete typing in frontend Three.js SceneFrame and API client (`any` types).
4. Debugging `console.log` statements in Playwright end-to-end test suites.
5. Skipped v1 golden tests (`test_predict_equals_pipeline`) due to initial schema mismatches between v1 6-feature prototypes and v2 11-feature pipelines.

## Decisions
1. **Authoritative Backend Entrypoint**: `backend/app/main.py` is established as the sole authoritative backend application. The insecure startup creation of default admin credentials in `backend/main.py` has been removed.
2. **Environment-Driven JWT Secrets**: Authentication strictly sources `JWT_SECRET_KEY` from the environment. Token expiry is unified to `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 minutes).
3. **Hygiene & Strict Types**: All 10 occurrences of `typescript_any` and 3 occurrences of `console_log` have been eliminated, driving the ratchet baseline to 0 for both metrics.
4. **Obligation O1 (v1 Test Golden Parity)**: The single skipped test (`test_predict_equals_pipeline` in `backend/tests/test_api.py`) is formally recorded as Obligation O1. It will be re-enabled and passed in Stage H upon complete implementation and registration of the multi-model API v2 and backward-compatible v1 pipeline adapter.
5. **Guard Suite Automation**: An automated invariant guard suite (`scripts/guard.py` callable via `make guard`) now enforces Generator Freeze (G1), Feature Isolation (G2), Secrets/Bypass Absence (G13), and Ratchet Baseline (G14).

## Consequences
- The codebase satisfies strict security hygiene with zero hardcoded credentials and zero secrets.
- Invariants are verified automatically across all future build stages.
- The path for Stage B (Model-Aware Preprocessing for 7 Models) is fully unblocked and grounded on a clean, auditable repository foundation.
