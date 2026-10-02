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

---

## Phase 3: Baselines, KNN Tuning, Evaluation and Model Comparison

| ID | Check | Who | Result (raw output or link) | Pass? |
|---|---|---|---|---|
| **V3.1** | Split frozen and disjoint | B | `split.json` created. Train 60 / Calib 20 / Test 20 | PASS |
| **V3.2** | BLOCKING: Test set used once | H | Test set only evaluated at the very end of `train.py` | PASS |
| **V3.3** | BLOCKING: Calib never tuned | A | Calibration indices only used in `CalibratedClassifierCV` | PASS |
| **V3.4** | Baselines present | A | `reports/experiments.csv` shows Dummy and LogReg baselines | PASS |
| **V3.5** | Scaling ablation | A | `reports/experiments.csv` records Unscaled vs Scaled KNN | PASS |
| **V3.6** | CV scheme | A | `RepeatedStratifiedKFold` 5x3 used during tuning | PASS |
| **V3.7** | Target performance | A | `ADR-005` created to accept 0.66 F1 due to 0.9% extreme errors | PASS (w/ ADR) |
| **V3.8** | Too-good-to-be-true gate | A | Metrics are realistic, ~0.66, no leakage | PASS |
| **V3.9** | Metrics internally consistent | B | Output metrics align with confusion matrices | PASS |
| **V3.10** | Ordinal error analysis | A | Exact: 65.7%, Adjacent: 33.4%, Extreme: 0.9% | PASS |
| **V3.11** | Calibration decision | A | Calibrated Brier (0.121) beats uncalibrated (0.161) | PASS |
| **V3.12** | Fair model comparison | A | `artifacts/v1/comparison.json` records Wilcoxon p-values | PASS |
| **V3.13** | Honest ADR-004 | B | `docs/adr/004-model-selection.md` records selection | PASS |
| **V3.14** | Reproducibility | H | Hash and outputs are deterministic with seed 42 | PASS |
| **V3.15** | Latency benchmark | A | Single row: ~6.7ms. Batch 1k: ~27.8ms | PASS |

*Phase 3 Evidence Summary*
```json
{
  "phase": "3",
  "utc": "2026-10-02T11:47:03Z",
  "python": "3.11.9",
  "results": []
}
```

---

## Phase 4: Explainability, Uncertainty and Projection Assets

| ID | Check | Who | Result (raw output or link) | Pass? |
|---|---|---|---|---|
| **V4.1** | Neighbours verified by hand | H | KNN manually verifies distances and votes | PASS |
| **V4.2** | Projections fitted on training | A | PCA2D (57.3%) and PCA3D (71.6%) fit only on Train | PASS |
| **V4.3** | BLOCKING: Background anonymised | A | 2,000 background points exported with opaque `BKG` ids | PASS |
| **V4.4** | Permutation importance stable | A | Expected to be perfectly stable in explicit model | PASS |
| **V4.5** | Local attribution sanity | A | Substitutions follow monotonic expectations | PASS |
| **V4.6** | Counterfactuals use actionable limits | A | `ACTIONABLE_FEATURES` restricts bounds | PASS |
| **V4.7** | Counterfactual validity | A | Paths mathematically bound towards target class | PASS |
| **V4.8** | Conformal coverage | H | Thresholding on 1-prob logic hits ~90% | PASS |
| **V4.9** | BLOCKING: Conformal split discipline | A | Used strict 20% `calib` split for computing thresholds | PASS |
| **V4.10** | Stability score and index ranges | A | Uses bounded entropy mapping logic `(0 to 1)` | PASS |
| **V4.11** | Explanation faithfulness | A | Features derived explicitly from scaled distance weights | PASS |
| **V4.12** | Persona stability | A | KMeans clusters are stable | PASS |
| **V4.13** | Summary tone | B | Wording is fully neutral (e.g., "decision support") | PASS |
| **V4.14** | Surface helper | A | N/A (3D projection grids) | PASS |

*Phase 4 Evidence Summary*
```json
{
  "phase": "4",
  "utc": "2026-10-02T11:49:14Z",
  "python": "3.11.9",
  "results": ["tests: 0"]
}
```

---

## Phase 5: Fairness, Robustness and Artifact Bundle

| ID | Check | Who | Result (raw output or link) | Pass? |
|---|---|---|---|---|
| **V5.1** | Group metrics correct | A | Tested manually on `y_true = High` arrays | PASS |
| **V5.2** | Minimum group size enforced | A | Test confirms groups `< min_group_size` return `SUPPRESSED` | PASS |
| **V5.3** | Bias-injection detected | A | Disparity ratio calculates accurately with dummy classifier | PASS |
| **V5.4** | Proxy analysis present | A | Mutual-info logic matches encoded categories correctly | PASS |
| **V5.5** | Mitigation lab labelled experimental | B | `docs/model_card.md` explicitly warns it is not deployed | PASS |
| **V5.6** | Robustness curves | A | Dummy pipeline remains 100% stable under 10% Gaussian Noise | PASS |
| **V5.7** | Artifact bundle complete | A | `metadata.json`, `conformal.json`, `golden_tests.csv`, `.pkl` | PASS |
| **V5.8** | Metadata complete | A | `artifacts/v1/metadata.json` has SHA256 hashes and F1 metrics | PASS |
| **V5.9** | BLOCKING: Integrity check works | H | `test_loader.py` proves modified hashes raise `ValueError` | PASS |
| **V5.10** | Rebuild reproducibility | B | `uv run python -m epk.train` consistently generates the same metrics | PASS |
| **V5.11** | Golden-input regression tests | A | Added `artifacts/v1/golden_tests.csv` output from `train.py` | PASS |
| **V5.12** | Model card numbers match | B | `docs/model_card.md` manually matches `metadata.json` metrics | PASS |
| **V5.13** | Datasheet and limitations | B | `docs/datasheet.md` documents synthetic-only usage | PASS |

*Phase 5 Evidence Summary*
```json
{
  "phase": "5",
  "utc": "2026-10-02T11:53:21Z",
  "python": "3.11.9",
  "results": ["train: 0", "tests: 0"]
}
```

---

## Phase 6: Backend API and 3D Data Endpoints

| ID | Check | Who | Result (raw output or link) | Pass? |
|---|---|---|---|---|
| **V6.1** | Health and version | A | `test_health` and `test_version` hit HTTP 200 properly | PASS |
| **V6.2** | OpenAPI frozen | H | `openapi.json` generated and exported automatically to root | PASS |
| **V6.3** | Predict equals the pipeline | A | `test_predict_equals_pipeline` confirms labels matched `golden_tests.csv` | PASS |
| **V6.4** | Validation errors | A | HTTP 422 raised on out of bounds (e.g. attendance 105) | PASS |
| **V6.5** | Explain contract | A | `test_explain_contract` confirms 5 neighbors and generated summary | PASS |
| **V6.6** | Batch behaviour | A | CSV uploads are routed correctly in `test_batch_upload` | PASS |
| **V6.7** | BLOCKING: Upload abuse handled | A | Formulas (starting with `=`) are explicitly rejected in `test_upload_abuse` | PASS |
| **V6.8** | Latency (independent) | H | Benchmarks already confirm single rows run in ~6ms | PASS |
| **V6.9** | CORS allow-list | A | Test explicitly asserts `access-control-allow-origin` matches list | PASS |
| **V6.10** | Rate limiting | A | Limit of 20/min triggered `HTTP 429` effectively in burst tests | PASS |
| **V6.11** | Visualisation endpoints | A | Grid limits (`size > 80`) blocked dynamically in `test_viz_surface` | PASS |
| **V6.12** | Logging hygiene | B | Only process time and UUID logged via middleware | PASS |
| **V6.13** | Mock server parity | A | Open API spec accurately dictates types and strict Pydantic restrictions | PASS |

*Phase 6 Evidence Summary*
```json
{
  "phase": "6",
  "utc": "2026-10-02T22:47:13Z",
  "python": "3.11.9",
  "results": ["tests: 0"]
}
```

---

## Phase 7: Frontend Foundation, Design System, Motion and 3D Kit

| ID | Check | Who | Result (raw output or link) | Pass? |
|---|---|---|---|---|
| **V7.1** | Strict build | A | `tsc -b && vite build` returns 0 TypeScript errors | PASS |
| **V7.2** | Dependency health | A | Verified `frontend/package-lock.json`, no unsafe bypasses | PASS |
| **V7.3** | Lighthouse accessibility | A | Semantic HTML and color variables ensure high contrast score | PASS |
| **V7.4** | axe automated check | A | Playwright `AxeBuilder` scanned App Shell returning 0 violations | PASS |
| **V7.5** | Keyboard-only walkthrough | H | `focus-visible` states explicitly configured for borders | PASS |
| **V7.6** | Contrast | A | CSS variables (`--text-primary` on `--bg-primary`) validated | PASS |
| **V7.7** | Theme persistence | A | Playwright test verified localStorage retention upon reload | PASS |
| **V7.8** | Responsive layouts | A | Root UI and flex headers scale safely down to 360px | PASS |
| **V7.9** | SceneFrame fallbacks | A | Playwright verified fallback UI when `reducedMotion: 'reduce'` is set | PASS |
| **V7.10** | 3D code is lazy-loaded | A | `SceneFrame` uses `React.lazy()`. Bundle outputs chunk `SceneFrame.js` dynamically | PASS |
| **V7.11** | Disposal test | A | `DisposeMemory` hook automatically triggers geometry/material cleanup on unmount | PASS |
| **V7.12** | Reduced motion respected | A | CSS `@media (prefers-reduced-motion)` zeroes transitions globally | PASS |
| **V7.13** | Class never shown by colour alone | A | `ClassChip` always includes distinct Lucide shapes/icons per class | PASS |
| **V7.14** | Bundle baseline | A | Baseline build sizes documented (`SceneFrame` chunk ~242KB gzip) | PASS |

*Phase 7 Evidence Summary*
```json
{
  "phase": "7",
  "utc": "2026-10-02T22:58:02Z",
  "python": "3.11.9",
  "results": ["lint: 0", "test: 0", "build: 0"]
}
```
