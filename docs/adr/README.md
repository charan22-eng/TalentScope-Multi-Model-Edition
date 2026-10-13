# Architecture Decision Records (ADRs) Index

This directory records all key architectural and governance decisions for **TalentScope Multi-Model Edition**.

| ADR | Title | Status | Date | Core Decision Summary |
|---|---|---|---|---|
| [ADR-001](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/ADR-001.md) | Single Source of Truth for Data Generation | Accepted | 2026-09-29 | Single generator seed and synthetic distribution logic. |
| [ADR-002](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/ADR-002.md) | Standardized Evaluation Pipeline | Accepted | 2026-09-29 | Standard metrics across all models. |
| [ADR-003](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/003-preprocessing.md) | Preprocessing and Pipeline Serialization | Accepted | 2026-10-01 | Encapsulate scikit-learn transformers inside serialized model pipelines. |
| [ADR-004](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/004-model-selection.md) | Model Evaluation & Selection Protocol | Accepted | 2026-10-01 | Baseline selection and evaluation metric protocol. |
| [ADR-005](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/005-low-f1.md) | Class Imbalance and Optimization | Accepted | 2026-10-01 | Addressing minority band performance and metric thresholds. |
| [ADR-006](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/006-conformal.md) | Split Conformal Prediction Strategy | Accepted | 2026-10-01 | Conformal calibration sets for coverage guarantees. |
| [ADR-006 (Freeze)](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/006-generator-freeze.md) | Synthetic Generator Freeze and Hash Lock | Accepted | 2026-10-12 | Freeze `ml/src/epk/data.py` at SHA-256 `72248D00...` with 0.8% realism layer noise. |
| [ADR-007](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/007-preprocessing-policy.md) | Preprocessing Policy for Seven Models | Accepted | 2026-10-12 | Model-aware scaling (StandardScaler for linreg/logreg/knn/svm; None for dt/rf/boost) with median imputation. |
| [ADR-008](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/008-calibration-method.md) | Calibration Method Selection | Accepted | 2026-10-12 | Platt scaling (sigmoid) on held-out Cal-A (1,190 samples) for calibrated probabilities. |
| [ADR-009](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/009-champion-selection-rule.md) | Champion Selection Rule & Multi-Criteria Decision Analysis | Accepted | 2026-10-12 | Deterministic 5-profile MCDA (Balanced default) with tie-breakers, 95% bootstrap CI, and McNemar significance testing. |
| [ADR-010](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/010-legacy-reconciliation.md) | Legacy v1 Reconciliation and Clean Coexistence | Accepted | 2026-10-12 | Coexistence of `/api/v1` and `/api/v2/*`, unskipping v1 test suites, unified schema definitions. |
| [ADR-011](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/011-artifact-storage-strategy.md) | Artifact Storage Strategy and Size Profile | Accepted | 2026-10-13 | Local Git storage under 50 MB budget, model size profiles, and cloud offload roadmap. |
| [ADR-012](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/012-dataset-checksum-strategy.md) | Dual-Layer Dataset Checksum Strategy | Accepted | 2026-10-13 | Dual primary LF-normalized byte SHA-256 and secondary row vector SHA-256 hashing. |
| [ADR-013](file:///c:/Users/resma/Documents/WORKSHOP/DM-CBP/docs/adr/013-coverage-exclusion-policy.md) | Coverage Omission Policy for Legacy CLI Wrappers | Accepted | 2026-10-13 | Exclude unreachable CLI scripts (audit, train, tune, validate) per VM13.1. |
