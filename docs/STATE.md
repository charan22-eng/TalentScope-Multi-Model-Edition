# STATE

## Done
- Monorepo layout initialized and Python/frontend tooling configured (Session 0).
- Multi-Model Dataset v2 implemented (`ml/src/epk/data.py`) with 3 variants: `linear`, `nonlinear`, `noisy_overlap` (Session MM-S1).
- Stage A completed: Codebase inventory (`docs/INVENTORY.md`), legacy auth security remediation, hygiene ratchet baseline (0 any, 0 console.log), invariant guard suite `make guard` (G1, G2, G13, G14), decisions log, and ADR-010.

## Decisions
- [ADR-001](../docs/adr/ADR-001.md): Stack decisions and versions.
- [ADR-002](../docs/adr/ADR-002.md): Package and dependency manager (uv).
- [ADR-006](../docs/adr/006-generator-freeze.md): Data Generator Freeze for Multi-Model Edition.
- [ADR-010](../docs/adr/010-legacy-reconciliation.md): Reconciling Legacy Code with Multi-Model Architecture.

## Metrics
- Dataset volume: 12,096 raw rows -> 11,820 cleaned rows (> 10,000 threshold).
- Default variant (`nonlinear`) spread: Best SVC F1=0.802, Worst DT F1=0.680, Spread=0.122 (>= 0.08).
- Hygiene: typescript_any=0, console_log=0, possible_secrets=0, bypass_flags=0.

## Known Issues
- `test_predict_equals_pipeline` explicitly skipped via `skipif` (Obligation O1) pending v2 golden tests in Stage H.

## Next Step
- Stage B: Model-Aware Preprocessing for Seven Models (MM-S2).
