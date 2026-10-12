# BUILD PROGRESS: TalentScope Multi-Model Edition

## Invariant Ratchet Baseline (G14)
Recorded at start of Stage A:
- `test_skips_or_xfail`: 1 (Obligation O1: `backend/tests/test_api.py:46` - pending Stage H)
- `lint_or_type_suppressions`: 0
- `bypass_flags`: 0
- `possible_secrets`: 0
- `typescript_any`: 10 (target: 0 in Stage A3)
- `console_log`: 3 (target: 0 in Stage A3)

## Obligations
- [x] **O1**: Re-enable skipped v1 golden tests (`test_predict_equals_pipeline` in `backend/tests/test_api.py`) in Stage H after v2 schema / pipeline reconciliation (Discharged: all 39 backend tests pass with 0 skips).

---

## Build Checklist

### Stage A: Audit, hygiene, guard suite (tag: `stage-a-built`)
- [x] **A1**: Inventory: write `docs/INVENTORY.md` classifying backend routes, frontend pages, models, scripts, tests, dependencies.
- [x] **A2**: Security review of legacy auth: environment JWT secret, remove default admin credentials, secure tokens.
- [x] **A3**: Hygiene: eliminate `any` (reduce baseline from 10 to 0), remove `console.log` in tests, record G14 baseline.
- [x] **A4**: Create `make guard` with G1, G2, G13, G14.
- [x] **A5**: Create `docs/BUILD_PROGRESS.md`, `docs/DECISIONS_LOG.md`, write `docs/adr/010-legacy-reconciliation.md`.

### Stage B: Preprocessing for seven models (tag: `stage-b-built`)
- [x] **B1**: EDA memo `docs/03-eda-findings.md` with evidence on nonlinearity, saturation, interaction, threshold.
- [x] **B2**: `ModelSpec` dataclass and 7 spec stubs (`linreg`, `logreg`, `knn`, `svm`, `dt`, `rf`, `boost`).
- [x] **B3**: `build_preprocessor(spec)` factory (model-aware scaling, imputation, ordinal, one-hot, train-only winsorizing).
- [x] **B4**: Ordered integer label encoding in one place (`classes_ == [0, 1, 2]`).
- [x] **B5**: Preprocessing unit tests & parametrized leakage test (G4) & mutation script.
- [x] **B6**: Ablation on representative scaled and tree models; log CV; author `docs/adr/007-preprocessing-policy.md`.

### Stage C: Registry, training, final evaluation (tag: `stage-c-built`)
- [x] **C1**: `ml/src/epk/models/registry.py` and `ScoreToBand` regressor wrapper; 7 full model specs under `ml/src/epk/models/specs/`.
- [x] **C2**: Frozen split 60/20/20 (seed 42) into `data/processed/split.json` (cal-A & cal-B disjoint, G5, G7).
- [x] **C3**: `train_all.py --profile {fast,standard,thorough}` with equal tuning budget and logging to `reports/experiments.csv`.
- [x] **C4**: Probability calibration on `cal-A` via `docs/adr/008-calibration-method.md` (Platt scaling / sigmoid).
- [x] **C5**: Repeated split seeds for stability std evaluation.
- [x] **C6**: `make final` with G6 lock for locked test evaluation, metric catalogue, `test_predictions.csv`, `reports/v2_final.md`.
- [x] **C7**: Activate guards G3, G4, G5, G6, G7 in `scripts/guard.py`.

### Stage D: Comparison science and evidence packet (tag: `stage-d-built`)
- [x] **D1**: Paired stratified bootstrap 95% CIs (2,000 resamples) for macro-F1, accuracy, QWK, and rank 1 vs 2 difference (`stats.py`).
- [x] **D2**: Pairwise McNemar tests across 21 pairs with Holm correction (`pairwise.json`).
- [x] **D3**: Calibration metrics (ECE, Brier) & conformal sets on `cal-B` (alpha 0.1) (`conformal.json`).
- [x] **D4**: Robustness stress-testing, demographic fairness disparity ratios, and stability metrics per model.
- [x] **D5**: MCDA module (`mcda.py`) with 5 profiles, Dirichlet rank probability, decision strength rule; author `docs/adr/009-champion-selection-rule.md`.
- [x] **D6**: Data sensitivity across `linear`, `nonlinear`, `noisy_overlap` via `make final-variants` and `artifacts/v2/comparison/sensitivity.json`.
- [x] **D7**: Machine-built evidence packet (`evidence.py`) with numbered facts, caveat `F90`, and G8 scanner.

### Stage E: Multi-model explainability and uncertainty (tag: `stage-e-built`)
- [x] **E1**: Model-agnostic explainers: permutation importance, local attribution, counterfactuals, stability, performance index.
- [x] **E2**: Native explainers: coefficients/odds ratios, tree rules, KNN neighbours (`explanation_type="native"`).
- [x] **E3**: Similar-cases view for non-KNN models labelled `"not how this model decided"`.
- [x] **E4**: Scaled space PCA 2D/3D background sample.
- [x] **E5**: 2D surface grids (40x40 default), Spearman importance agreement matrix, neutral summaries.

### Stage F: Local LLM verdict engine (tag: `stage-f-built`)
- [x] **F1**: LLM client (`ml/src/epk/llm/`) with `assert_local` guard (G10) for Ollama and OpenAI-compat.
- [x] **F2**: SYSTEM_PROMPT, user template, inline VERDICT_SCHEMA, prompt versioning.
- [x] **F3**: Verdict validator (schema, fact IDs, numbers, rules, banned words, G9) & retry/template fallback orchestrator.
- [x] **F4**: Cache and verdict persistence.
- [x] **F5**: Golden evaluation harness (`ml/scripts/llm_eval.py`) with 6 golden packets.
- [x] **F6**: Documentation `docs/LLM_SETUP.md`.
- [x] **F7**: Forbidden employee-level key prompt scanner.

### Stage G: Artifacts v2 and model cards (tag: `stage-g-built`)
- [x] **G1**: `artifacts/v2` layout with `MANIFEST.json` SHA-256 hashes and `champion.json`.
- [x] **G2**: Lazy loader with model key whitelist and checksum validation.
- [x] **G3**: Golden-input regression tests across 7 models.
- [x] **G4**: Machine-generated model cards, comparison card `docs/model_card.md`, and `docs/datasheet.md`.

### Stage H: Backend API v2 (tag: `stage-h-built`)
- [x] **H1**: Preserve `/api/v1` (default KNN); implement `/api/v2/*` endpoints.
- [x] **H2**: Integrated RBAC on v2 routes, stricter LLM rate limits, problem-details errors.
- [x] **H3**: Resolve Obligation O1: fix v1 test schema mismatch, remove skipif.
- [x] **H4**: OpenAPI v2 export, generated TypeScript types, mock verdicts.
- [x] **H5**: Guards G11 (whitelist/path traversal) and G12 (RBAC matrix) active; predict/all p95 < 800ms.

### Stage I: Frontend core pages (tag: `stage-i-built`)
- [x] **I1**: Okabe-Ito color palette, marker shapes, `ModelChip`, small multiples chart kit.
- [x] **I2**: Predict page: model selector, all-models panel, agreement meter, split-decision alert, champion highlight.
- [x] **I3**: What-if advisor, Batch (5000x7 smooth), Model Lab, Dashboard.
- [x] **I4**: Component & Playwright tests; strict TypeScript.

### Stage J: Model Arena (tag: `stage-j-built`)
- [x] **J1**: Arena pages: Overview, Priorities (live server MCDA), Head-to-Head, Metrics Deep Dive, Cost/Speed, Sensitivity, Explainability, Fairness/Robustness, LLM Verdict.
- [x] **J2**: LLM Verdict interactive panel (fact chips highlighting charts, why-not accordion, template fallback state).
- [x] **J3**: Table views for every chart, monochrome distinguishable markers, CI whiskers.
- [x] **J4**: Component and Playwright tests.

### Stage K: 3D Multi-Model Experiences (tag: `stage-k-built`)
- [x] **K1**: Decision Landscape with 2-model overlay & difference surface ($P_A - P_B$), 2D heatmap fallback, similar-cases 3D view.
- [x] **K2**: Talent Galaxy hero scene with pause control.
- [x] **K3**: Disposal/leak tests, performance budgets recorded in `docs/performance.md`.

### Stage L: Secure app and MLOps (tag: `stage-l-built`)
- [x] **L1**: SQLite & PostgreSQL database migrations for all tables.
- [x] **L2**: RBAC enforcement across all routes with negative tests, append-only audit log.
- [x] **L3**: Review workflow & employee transparency page.
- [x] **L4**: Governed retrain-all pipeline with Admin approval and rollback.
- [x] **L5**: Per-model drift monitoring (PSI/KS), shadow inference mode.
- [x] **L6**: PDF reports with ReportLab.

### Stage M: Optional Wave 2 (tag: `stage-m-built` or SKIPPED)
- [ ] **M1**: Scoped API keys, saved views, webhooks (or documented as SKIPPED).

### Stage N: Hardening and delivery (tag: `stage-n-built`, release: `v2.0-rc`)
- [ ] **N1**: Test coverage >= 80% on core backend and ML code.
- [ ] **N2**: Dockerfiles, docker-compose, CI workflows.
- [ ] **N3**: Quickstart README (works with LLM offline), runbooks, viva Q&A sheet.
- [ ] **N4**: Final guard suite check, double reproducibility check of `make train PROFILE=fast`.
- [ ] **N5**: Author `docs/BUILD_REPORT.md` and print final summary.
