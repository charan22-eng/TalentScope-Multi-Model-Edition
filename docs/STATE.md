# STATE

## Done
- Monorepo layout initialized and Python/frontend tooling configured (Session 0).
- Multi-Model Dataset v2 implemented (`ml/src/epk/data.py`) with 3 variants: `linear`, `nonlinear`, `noisy_overlap` (Session MM-S1).
- Stage A completed: Codebase inventory (`docs/INVENTORY.md`), legacy auth security remediation, hygiene ratchet baseline (0 any, 0 console.log), invariant guard suite `make guard` (G1, G2, G13, G14), decisions log, and ADR-010.
- Stage B completed: Preprocessing for 7 models (`ml/src/epk/features.py`), EDA memo (`docs/03-eda-findings.md`), `ModelSpec` registry stubs, ordered labels (`epk.labels`), leakage tests (G4 passing), mutation script, ablation CV experiments in `reports/experiments.csv`, and ADR-007.
- Stage C completed: Model registry and modular specs (`ml/src/epk/models/specs/`), frozen 60/10/10/20 split (`data/processed/split.json`), fair training harness `train_all.py`, probability calibration on `cal-A` (Platt scaling / sigmoid per ADR-008), single locked test-set evaluation `final_eval.py` (make final) with G6 lock, and active guards G1, G2, G3, G4, G5, G6, G7, G13, G14.

## Decisions
- [ADR-001](../docs/adr/ADR-001.md): Stack decisions and versions.
- [ADR-002](../docs/adr/ADR-002.md): Package and dependency manager (uv).
- [ADR-006](../docs/adr/006-generator-freeze.md): Data Generator Freeze for Multi-Model Edition.
- [ADR-007](../docs/adr/007-preprocessing-policy.md): Preprocessing Policy for Seven-Model Arena.
- [ADR-008](../docs/adr/008-calibration-method.md): Probability Calibration Protocol and Method Selection.
- [ADR-010](../docs/adr/010-legacy-reconciliation.md): Reconciling Legacy Code with Multi-Model Architecture.

## Metrics
- Dataset volume: 11,904 cleaned rows (> 10,000 threshold).
- Final Holdout Test Metrics (Holdout N = 2,381 rows, single evaluation under G6 lock):
  - `svm`: Macro-F1 = 0.8164, Accuracy = 0.8148, QWK = 0.8216, ECE = 0.0270, p95 Latency = 23.47ms
  - `boost`: Macro-F1 = 0.8038, Accuracy = 0.8013, QWK = 0.8075, ECE = 0.0904, p95 Latency = 105.77ms
  - `rf`: Macro-F1 = 0.7804, Accuracy = 0.7770, QWK = 0.7841, ECE = 0.0133, p95 Latency = 99.38ms
  - `knn`: Macro-F1 = 0.7543, Accuracy = 0.7518, QWK = 0.7550, ECE = 0.0246, p95 Latency = 16.94ms
  - `logreg`: Macro-F1 = 0.7189, Accuracy = 0.7148, QWK = 0.7173, ECE = 0.1246, p95 Latency = 22.60ms
  - `dt`: Macro-F1 = 0.7094, Accuracy = 0.7085, QWK = 0.6993, ECE = 0.0342, p95 Latency = 16.27ms
  - `linreg`: Macro-F1 = 0.7032, Accuracy = 0.7014, QWK = 0.6955, ECE = 0.0213, p95 Latency = 13.23ms (R² = 0.6669)
- Invariant Guards: G1, G2, G3, G4, G5, G6, G7, G13, G14 all GREEN.
- Hygiene: typescript_any=0, console_log=0, possible_secrets=0, bypass_flags=0.

## Known Issues
- `test_predict_equals_pipeline` explicitly skipped via `skipif` (Obligation O1) pending v2 golden tests in Stage H.

## Next Step
- Stage D: Comparison Science, MCDA, and Evidence Packet (MM-S4).
