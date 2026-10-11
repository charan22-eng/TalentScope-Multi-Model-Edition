# STATE

## Done
- Monorepo layout initialized and Python/frontend tooling configured (Session 0).
- Multi-Model Dataset v2 implemented (`ml/src/epk/data.py`) with 3 variants: `linear`, `nonlinear`, `noisy_overlap` (Session MM-S1).
- Realism layer calibrated (missing 4%, duplicates 0.8%, impossible values 0.8% <= 1%).
- Data directory layout established: `data/manifest.json` with variants under `data/<variant>/{dataset.csv, protected.csv}`.
- Data contract tests verified (`ml/tests/test_data_contract.py`).
- 7-model variant properties benchmarked (`ml/scripts/variant_check.py`).
- Generator frozen in ADR-006.

## Decisions
- [ADR-001](../docs/adr/ADR-001.md): Stack decisions and versions.
- [ADR-002](../docs/adr/ADR-002.md): Package and dependency manager (uv).
- [ADR-006](../docs/adr/006-generator-freeze.md): Data Generator Freeze for Multi-Model Edition.

## Metrics
- Dataset volume: 12,096 raw rows -> 11,820 cleaned rows (> 10,000 threshold).
- Default variant (`nonlinear`) spread: Best SVC F1=0.802, Worst DT F1=0.680, Spread=0.122 (>= 0.08).

## Known Issues
- `test_predict_equals_pipeline` explicitly skipped via `skipif` pending v2 golden tests in MM-S8 due to v1 schema type mismatch.

## Next Step
- Session MM-S2: Preprocessing pipeline, feature transformations, and VM2 verification.
