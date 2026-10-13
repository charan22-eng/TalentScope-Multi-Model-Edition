# ADR 013: Test Coverage Omission Policy for Legacy CLI Wrappers

**Status:** Accepted  
**Date:** 2026-10-13  
**Deciders:** Core Engineering & Quality Assurance  

## Context
Standard quality verification (VM13.1) mandates that core production machine learning library code (`ml/src/epk`) maintain at least 80% line coverage with automated regression and smoke tests. 

However, during early development iterations (Stage 1 / v1 single-model baseline), several command-line entrypoint scripts were written as thin terminal wrappers. These scripts have been superseded by the unified multi-model pipelines (`train_all.py`, `final_eval.py`, `stats.py`, `evidence.py`).

## Decision
We omit only genuinely unreachable legacy CLI wrappers from coverage measurement. All active pipelines, data transformers, model specifications, evaluation routines, explainers, and evidence builders remain strictly measured under the $\ge 80\%$ coverage gate.

### Excluded Files
1. **`ml/src/epk/audit.py`**:
   - *Nature*: Standalone CLI diagnostic tool intended for terminal-based ad-hoc inspection (`python -m epk.audit`).
   - *Rationale*: All auditing logic is exercised natively by `scripts/guard.py` and the automated verification suite.
2. **`ml/src/epk/train.py`**:
   - *Nature*: Single-model CLI wrapper from v1.
   - *Rationale*: Superseded by `train_all.py` (which tunes and calibrates all seven models under consistent budgets).
3. **`ml/src/epk/tune.py`**:
   - *Nature*: Standalone hyperparameter search script from v1.
   - *Rationale*: Superseded by the integrated `RandomizedSearchCV` within `train_all.py`.
4. **`ml/src/epk/validate.py`**:
   - *Nature*: Deprecated terminal script for printing raw confusion matrices.
   - *Rationale*: Superseded by `final_eval.py` and comprehensive test suites in `ml/tests/`.
5. **`ml/src/epk/compare.py`**:
   - *Nature*: Legacy v1 CLI benchmarking script referencing obsolete `data/raw/dataset.csv`.
   - *Rationale*: Superseded by `evidence.py` and `mcda.py`.
6. **`ml/src/epk/train_extras.py`**:
   - *Nature*: Legacy v1 auxiliary asset script referencing obsolete `data/raw/dataset.csv`.
   - *Rationale*: Superseded by `explain.py` and `sensitivity.py`.

## Configuration
The exclusion is codified in `.coveragerc` and `pytest.ini`:
```ini
[run]
omit =
    */epk/audit.py
    */epk/train.py
    */epk/tune.py
    */epk/validate.py
    */epk/compare.py
    */epk/train_extras.py
```

## Consequences
- Prevents dead CLI wrappers from diluting coverage reporting.
- Production code coverage reflects the active Multi-Model Edition execution paths.
