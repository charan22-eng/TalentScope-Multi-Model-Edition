# 09 ML Handoff (End of Model Build)

## Artifacts Generated
- `artifacts/v1/pipeline.joblib`: The primary tuned KNN pipeline.
- `artifacts/v1/projection.joblib`: PCA for 2D visualisations.
- `artifacts/v1/importance.json`: Global permutation importance.
- `artifacts/v1/personas.json`: K-Means personas.
- `docs/model_card.md`: Fairness, boundaries, and model details.
- `artifacts/v1/audit_report.json`: Metrics on robustness and demographic parity.

## Core Capabilities Provided
- **Explanation (`explain.py`):** `explain()`, `local_attribution()`, `counterfactual()`, `summarise()`.
- **Inference (`features.py`, `train.py`):** Full end-to-end processing with clipping (Winsorizer) and imputation.

## Readiness for Backend
The ML package (`epk`) is fully functional. It can be installed in the backend via `pip install -e ml/`. The backend must load the pipeline from `artifacts/v1/pipeline.joblib` and wrap the inference and explanation functions in FastAPI routes.

## Action Items for Phase 11 (Backend)
- Implement `/predict` (standard inference).
- Implement `/explain` (returns nearest neighbours).
- Implement `/simulate` (counterfactuals).
- Implement `/model/metadata` (feature importance, metrics).

**Definition of Done:**
- [x] Best model selected and justified (ADR-003).
- [x] Local and global explainability outputs produced.
- [x] Fairness parity tested.
- [x] Handoff document ready for API engineer.
