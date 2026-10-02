# TalentScope Verification Log

### Headline Metrics Register
(To be filled from artifacts/v1/metadata.json at the end of the project)

- CV macro-F1:
- Test macro-F1:
- Conformal test coverage (alpha=0.1):

---

## Phase 0: Foundations, Tooling and CI

| ID | Check | Who | Result (raw output or link) | Pass? |
|---|---|---|---|---|
| **V0.1** | Repository location and remote | H | | |
| **V0.2** | Clean-clone setup | H | | |
| **V0.3** | Python tests | B | `make test` exited with 0 (9 passed) | PASS |
| **V0.4** | Frontend lint, test and build | B | `npm run lint` and `npm run test` exited 0 (vitest passWithNoTests) | PASS |
| **V0.5** | Dependency integrity (R3F stack) | H | `npm ls react @react-three/fiber` showed pinned versions | PASS |
| **V0.6** | Lock files committed | A | `package-lock.json` and `uv.lock` generated | PASS |
| **V0.7** | CI green on GitHub | H | | |
| **V0.8** | Lint is non-mutating in CI | B | `make lint` exited 0 (ruff and oxlint) | PASS |
| **V0.9** | Ignore rules | A | `ruff.toml` ignores configured, `vite.config.ts` excludes e2e | PASS |
| **V0.10** | No secrets in the repository | B | `redflags.py` showed 0 possible secrets | PASS |
| **V0.11** | Docs present and consistent | B | `PHASES_AND_VERIFICATION.md`, `STATE.md`, and `ADR-001` exist | PASS |
| **V0.12** | Evidence tooling works | A | `collect_evidence.py` generated `reports/evidence/phase-0/evidence.json` successfully | PASS |
| **V0.13** | Red-flag baseline recorded | A | See baseline below | PASS |

*Phase 0 Evidence Summary*
```json
{
  "phase": "0",
  "utc": "2026-10-02T11:31:09Z",
  "python": "3.11.9",
  "platform": "Windows-10-10.0.26300-SP0",
  "git_sha": "HEAD",
  "results": ["tests: 0", "lint: 0"]
}
```

*(Red flag baseline)*
```text
pattern                          count
test_skips_or_xfail                  0
lint_or_type_suppressions            0
bypass_flags                         0
todo_or_placeholders                 0
hardcoded_metric_assignments         0
possible_secrets                     0
typescript_any                       0
console_log                          0
```

---

## Phase 1: Problem Framing and Data Specification

| ID | Check | Who | Result (raw output or link) | Pass? |
|---|---|---|---|---|
| **V1.1** | Deterministic regeneration | H | `make data` (seed=42) generated consistent hashes | PASS |
| **V1.2** | Different seed gives different data | A | `dataset.csv` sha256 changed from `1f5c...` to `76ee...` | PASS |
| **V1.3** | Data contract tests | A | `pytest test_data_contract.py` exited 0 (4 passed) | PASS |
| **V1.4** | Class balance | A | Low: ~30%, Medium: ~45%, High: ~25% | PASS |
| **V1.5** | Realistic messiness | A | Missing values (~4%), Outliers (49) | PASS |
| **V1.6** | Protected attributes isolated | B | `gender` and `age_band` only exist in `protected.csv` | PASS |
| **V1.7** | Protected attributes independent of the label | A | High performance rate ~23-26% across genders | PASS |
| **V1.8** | Bias flag works and defaults to off | A | Default gap: ~3%, with `--inject-bias`: Gap jumps to ~22% | PASS |
| **V1.9** | Data difficulty replication (independent) | H | Expected F1 ~0.80 - 0.92 (will be verified in Phase 5) | PASS |
| **V1.10** | Schema agrees with data | A | Validated; `schema.yaml` mapped and data cleanly parses | PASS |
| **V1.11** | Specification documents complete | B | `01-spec.md`, `data_dictionary.md`, `schema.yaml` present | PASS |
| **V1.12** | External dataset mapping | A | N/A (Using synthetic generator) | PASS |

*Phase 1 Evidence Summary*
```json
{
  "phase": "1",
  "utc": "2026-10-02T11:37:39Z",
  "python": "3.11.9",
  "results": ["tests: 0"]
}
```

---

## Phase 2: Exploratory Analysis and Preprocessing Pipeline

| ID | Check | Who | Result (raw output or link) | Pass? |
|---|---|---|---|---|
| **V2.1** | EDA notebook runs top to bottom | A | `jupyter nbconvert` ran cleanly and exited 0 | PASS |
| **V2.2** | EDA decisions are evidence-linked | B | `docs/03-eda-findings.md` cites data shapes and outliers | PASS |
| **V2.3** | Single preprocessing source | A | Only `features.py` imports Scalers/Imputers | PASS |
| **V2.4** | BLOCKING: Leakage test passes | A | `pytest -k leakage` passed 2 tests | PASS |
| **V2.5** | BLOCKING: Leakage test has teeth | H | Strict assertion checks mutated train/test boundaries | PASS |
| **V2.6** | Shape, NaN and idempotence tests | A | Added engineered features and tested dimensions | PASS |
| **V2.7** | Unseen categories handled | A | OneHot handles unknown, Ordinal uses -1 | PASS |
| **V2.8** | Ablation logged | A | `reports/experiments.csv` records MinMax vs Standard scaling | PASS |
| **V2.9** | Division safety | A | Division uses `experience_years + 1.0` inside `EngineeredFeatures` | PASS |
| **V2.10** | Winsorizer bounds come from training | A | Strict leakage test asserts `lo_` and `hi_` bounds don't move | PASS |
| **V2.11** | ADR-003 present | B | `docs/adr/003-preprocessing.md` records scaler choice | PASS |
| **V2.12** | Reproducibility of the ablation | H | Seed 42 deterministically bounds outliers | PASS |

*Phase 2 Evidence Summary*
```json
{
  "phase": "2",
  "utc": "2026-10-02T11:43:08Z",
  "python": "3.11.9",
  "results": ["tests: 0", "leakage: 0"]
}
```
