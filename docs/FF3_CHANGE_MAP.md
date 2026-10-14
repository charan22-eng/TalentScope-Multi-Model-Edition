# FF3 Change Map: Commit ff46989 Functional Grouping

**Commit Reference:** `ff46989`  
**Commit Message:** `feat(ff3): complete final follow-up across sections A through G with real legacy checks, ADR-014 calibration, truth table alignment, and final readiness docs`  
**Total Files Changed:** 103 files  
**Total Lines Changed:** +24,017 insertions, -18,593 deletions  

---

## 1. Executive Summary

Commit `ff46989` consolidated the comprehensive transition from FF2 to FF3. It resolved foundational calibration discrepancies, retired Platt scaling OvR in favor of multinomial temperature scaling (ADR-014), enforced the real 23 legacy verification gate definitions, eliminated unmaintained/dead ML code, aligned API access-control policies with RBAC reviewer documentation, and established strict numbers consistency across all artifacts.

To facilitate rigorous auditability, all 103 files modified in `ff46989` are categorized below into 8 distinct functional groups.

---

## 2. Functional Grouping of Modified Files

### Group 1: Calibration & Uncertainty Methodology (ADR-014)
*Addresses Finding A/B: Replaced OvR Platt sigmoid with multinomial temperature scaling cross-validated on cal-A, eliminated deprecated scikit-learn usage, and resolved conformal parameter naming.*

| File Path | Functional Purpose |
| :--- | :--- |
| `docs/adr/014-temperature-scaling-calibration.md` | Architectural Decision Record selecting Multinomial Temperature Scaling over Platt/Isotonic based on cal-A mean Brier CV. |
| `ml/src/epk/calibration.py` | Implementation of `MultinomialTemperatureCalibrator` with L-BFGS optimization on calibrated logits. |
| `ml/src/epk/uncertainty.py` | Renamed `min_prob_threshold` to `threshold`, documented non-empty set fallback rule, added tie-handling logic. |
| `ml/tests/test_calibration.py` | Unit tests for temperature scaling calibration, probability simplex preservation, and monotonic confidence behavior. |
| `ml/tests/test_conformal.py` | Conformal tests verifying quantile thresholding, coverage with and without fallback, and tie-breaking. |
| `scripts/adr014_calibration_cv.py` | Cross-validation script evaluating sigmoid OvR, isotonic OvR, and temperature scaling across 5 folds of cal-A. |
| `reports/calibration_cv_cal_a.json` | Machine-readable results of cal-A 5-fold cross-validation showing temperature scaling achieved superior mean Brier (0.3341). |

---

### Group 2: Model Predictions & Metrics Artifacts
*Machine-generated artifact files for all 7 candidate models following the frozen-estimator evaluation.*

| File Path | Functional Purpose |
| :--- | :--- |
| `artifacts/v2/models/boost/*` (metadata, metrics, model, predictions, tuning) | Boost model evaluation: metrics, raw/calibrated ECE, test predictions, and frozen pipeline joblib. |
| `artifacts/v2/models/dt/*` (metadata, metrics, model, predictions, tuning) | Decision Tree evaluation: metrics, test predictions, and model artifact. |
| `artifacts/v2/models/knn/*` (metadata, metrics, model, predictions, tuning) | KNN model evaluation: metrics, test predictions, and model artifact. |
| `artifacts/v2/models/linreg/*` (metadata, metrics, model, predictions, tuning) | Linear Regression evaluation: metrics, test predictions, and model artifact. |
| `artifacts/v2/models/logreg/*` (metadata, metrics, model, predictions, tuning) | Logistic Regression evaluation: metrics, test predictions, and model artifact. |
| `artifacts/v2/models/rf/*` (metadata, metrics, model, predictions, tuning) | Random Forest evaluation: metrics, test predictions, and model artifact. |
| `artifacts/v2/models/svm/*` (metadata, metrics, model, predictions, tuning) | Support Vector Machine evaluation: metrics, test predictions, and model artifact. |
| `artifacts/v2/MANIFEST.json` | Cryptographic SHA-256 manifest of all bundle files. |
| `artifacts/v2/champion.json` | Champion selection metadata recording balanced score and tie narrative. |

---

### Group 3: Comparison Suite & Multi-Criteria Decision Analysis
*Artifacts synthesizing comparative evaluation across all 7 models across 5 profiles.*

| File Path | Functional Purpose |
| :--- | :--- |
| `artifacts/v2/comparison/leaderboard.json` | Full comparison leaderboard displaying raw and calibrated ECE, Brier, accuracy, macro-F1, QWK, and conformal coverage. |
| `artifacts/v2/comparison/mcda.json` | Multi-Criteria Decision Analysis rankings, criteria weights, and rank-1 probability distributions across 5 profiles. |
| `artifacts/v2/comparison/pairwise.json` | Pairwise McNemar test p-values and bootstrap difference confidence intervals. |
| `artifacts/v2/comparison/sensitivity.json` | Sensitivity analyses across variant datasets and profile criteria variations. |
| `artifacts/v2/comparison/conformal.json` | Conformal prediction efficiency and empirical coverage across models. |
| `artifacts/v2/comparison/confusion.json` | Multiclass confusion matrices. |
| `artifacts/v2/comparison/curves.json` | Calibration reliability curves and ROC/PR data points. |
| `artifacts/v2/comparison/evidence_packet.json` | Structured evidence packet for LLM verdict engine, including synthesized facts and deterministic rankings. |

---

### Group 4: Dead Code Elimination & Test Suite Expansion
*Addresses Finding F: Deleted unused legacy modules, restored active testing for operational utilities, and reported coverage without artificial exclusions.*

| File Path | Functional Purpose |
| :--- | :--- |
| `ml/src/epk/audit.py` (DELETED) | Removed unused legacy audit script. |
| `ml/src/epk/compare.py` (DELETED) | Removed redundant model comparison prototype. |
| `ml/src/epk/train.py` (DELETED) | Removed legacy single-model training script. |
| `ml/src/epk/tune.py` (DELETED) | Removed obsolete tuning loop superseded by `train_all.py`. |
| `.coveragerc` | Removed exclusions for active scripts; restored unpadded coverage measurement. |
| `ml/src/epk/train_extras.py` | Retained and maintained for CSV line-ending validation and export sanitation. |
| `ml/tests/test_legacy_used.py` | Added test coverage for `train_extras.py` and operational validation logic. |
| `ml/tests/test_pipeline_smoke.py` | Smoke tests asserting lock semantics, artifact loaders, and pipeline execution. |

---

### Group 5: API Security, RBAC & Legacy Route Hardening
*Addresses Finding D/E: Enforced access-control matrix, introduced reviewer role documentation, implemented token revocation/logout, and aligned route permissions.*

| File Path | Functional Purpose |
| :--- | :--- |
| `backend/app/api_v2.py` | Added v2 batch prediction endpoint, authenticated review endpoints, and strict role enforcement (`admin`, `hr_manager`, `analyst`). |
| `backend/app/main.py` | Enforced role checks across legacy routes, registered token revocation and logout endpoints, added cookie security headers. |
| `backend/core/security.py` | Added token revocation blacklist and verification helpers. |
| `docs/adr/015-rbac-reviewer-role.md` | ADR defining the `reviewer` role, its permissions (read-only audit, review triage), and integration into JWT claims. |
| `backend/openapi.json` | Synchronized OpenAPI schema with security definitions and route matrix. |
| `openapi.json` | Root OpenAPI specification export. |
| `backend/tests/test_api.py` | Integration tests verifying authentication and legacy route protections. |
| `backend/tests/test_api_v2.py` | Integration tests for v2 prediction, appeal, and batch authorization. |
| `backend/tests/test_stage_l.py` | Tests verifying security headers, rate limiting, and 401 unauthenticated handling. |

---

### Group 6: Legacy Verification Gates (Real Definitions)
*Addresses Finding C/D: Implemented automated test harnesses executing all 23 legacy checks using their authentic titles and criteria.*

| File Path | Functional Purpose |
| :--- | :--- |
| `scripts/verify_legacy_gates.py` | Comprehensive test harness executing all 23 legacy gates (V6.8, V6.11, V6.12, V10.2-V10.14, V13.2-V13.8, V14.4). |
| `reports/legacy_gates_verification.json` | JSON output capturing status, raw stdout, latency, and assertions for each legacy check. |

---

### Group 7: Numbers Truth & Consistency Auditing
*Addresses Finding A/B: Replaced hand-typed values with single-source-of-truth script calculations and verified zero discrepancy.*

| File Path | Functional Purpose |
| :--- | :--- |
| `scripts/numbers_truth.py` | Single-source-of-truth audit script recalculating all test metrics directly from prediction CSVs. |
| `verification/x26_numbers_consistency.py` | Consistency check asserting zero divergence between raw test outputs and documentation tables. |
| `reports/numbers_truth.json` | Export of exact calculated values across all 7 models. |
| `reports/test_eval_log.csv` | Immutable append-only log of test evaluation acquisitions under G6 lock. |
| `reports/test_eval.lock` | G6 evaluation lock hash. |
| `reports/experiments.csv` | Training experiment tracking log. |
| `reports/v2_final.md` | Final evaluation report summarizing performance, fairness, and uncertainty metrics. |

---

### Group 8: Documentation, Model Cards & UI Configurations
*Transparency updates reflecting temperature scaling, champion tie narrative, and human verification kits.*

| File Path | Functional Purpose |
| :--- | :--- |
| `docs/BUILD_REPORT.md` | Consolidated build report updated with verified machine numbers and zero hand-typed edits. |
| `docs/FINAL_READINESS.md` | Readiness matrix documenting all 25 blocking checks, raw evidence paths, and proposed waivers. |
| `docs/HUMAN_CHECK_KIT.md` | Explicit manual verification instructions for human auditor (V0.1, VM1.2, VM1.3, etc.). |
| `docs/VERIFICATION_LOG.md` | Audit log with check-by-check evidence paths and results. |
| `docs/VERIFICATION_SCOPE.md` | Scope declaration classifying automated vs. human-gated verification criteria. |
| `docs/model_card.md` | Primary model card documenting dataset, variants, calibration method, and champion narrative. |
| `docs/model_cards/*.md` (7 files) | Per-model cards (`boost.md`, `dt.md`, `knn.md`, `linreg.md`, `logreg.md`, `rf.md`, `svm.md`). |
| `artifacts/v2/verdicts/eval_report.json` | Verdict engine evaluation report. |
| `reports/llm_eval.json` | LLM evaluation benchmarks on golden packets. |
| `frontend/package.json` | Frontend dependency updates including vitest coverage tool. |
| `frontend/package-lock.json` | Lockfile synchronization for frontend testing tools. |
| `.gitignore` | Maintained artifact tracking rules. |

---

## 3. Verification & Traceability

Every file modified in commit `ff46989` maps directly to an explicit requirement in the project charter and review prompt. No untracked or orphan changes were introduced.
