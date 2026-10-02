# Employee Performance Classification (KNN): Phased Iteration Build Plan

**From an empty repository to an advanced, production-grade full website**

*Authored from the perspective of a senior data mining researcher, senior data mining engineer and senior AI engineer. This document is the execution companion to the project report: the report says **what and why**; this plan says **how, in what order, and how we know each step is done**.*

---

## Table of Contents

- [Part A: How to Use This Plan](#part-a-how-to-use-this-plan)
- [Part B: Master Roadmap](#part-b-master-roadmap)
- [Part C: Target End-State Architecture](#part-c-target-end-state-architecture)
- [Part D: Phase-by-Phase Iterations](#part-d-phase-by-phase-iterations)
  - Track 1: Research and Data Mining (Phases 0–10)
  - Track 2: Backend and Platform (Phases 11, 14)
  - Track 3: Frontend and UX (Phases 12–13)
  - Track 4: Advanced, Quality and Delivery (Phases 15–18)
- [Part E: Cross-Cutting Standards](#part-e-cross-cutting-standards)
- [Appendices](#appendices)

---

# Part A: How to Use This Plan

## A.1 Conventions

| Term | Meaning |
|---|---|
| **Phase** | A major stage with a single goal and an exit gate (Phase 0 to Phase 18) |
| **Iteration** | A small, shippable unit inside a phase, ID format `P.I` (for example `6.3` = Phase 6, Iteration 3). Each takes 0.5 to 3 days |
| **DoD** | Definition of Done: measurable acceptance criteria for an iteration |
| **Exit gate** | Checklist that must pass before the next phase starts (or before the dependent track starts) |
| **Release tag** | Git tag created at the end of a phase (`v0.1` … `v1.0`) |
| **Owner roles** | **DMR** Data Mining Researcher, **DME** Data Mining Engineer, **AIE** AI Engineer, **BE** Backend Engineer, **FE** Frontend Engineer, **UX** UX Designer, **QA** Quality/DevOps |

A small team can wear several hats (for example, one person can be DME + AIE). Roles exist so responsibilities are explicit, not to force a team of seven.

## A.2 Working principles

1. **Thin vertical slices first.** Get a crude end-to-end path (data → model → prediction on screen) early (Phase 5), then deepen each layer. This prevents a "beautiful model, no product" failure.
2. **Reproducibility is non-negotiable.** Fixed seeds, pinned dependencies, data checksums, artifacts carry metadata.
3. **Test set is sacred.** Split once in Phase 5, freeze it, and touch it only for final reporting in Phases 6 and 7.
4. **No leakage.** Every transformation that learns from data lives inside a scikit-learn `Pipeline` and is fit on training folds only.
5. **Explain everything.** Every prediction ships with its neighbours, confidence and a review flag.
6. **Contract-first integration.** The API contract (OpenAPI) is agreed before frontend and backend diverge; the frontend uses a mock server until the real API is ready.
7. **Decisions are written down.** Any non-trivial choice gets a short ADR (template in Appendix D).
8. **Definition of Done includes tests and docs**, not just "it runs on my machine".

## A.3 Team cadence

- **Sprint length:** 2 weeks (six sprints for the full 12-week plan).
- **Ceremonies:** 15-minute daily stand-up, sprint planning, sprint demo (live), retrospective.
- **Branching:** `main` (always releasable) ← `develop` ← `feature/<phase>-<short-name>`. Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`). Pull request required, at least one reviewer, CI green.
- **Board columns:** Backlog → Ready → In Progress → Review → Done, with labels per phase and per role.

## A.4 Global quality targets (tune to your context)

| Area | Target |
|---|---|
| Model quality | Cross-validated macro-F1 ≥ 0.80 on the primary dataset; extreme errors (Low ↔ High) ≤ 3% |
| Baselines | Tuned KNN must beat majority-class and unscaled KNN clearly |
| API latency | Single prediction p95 < 300 ms; 5,000-row batch < 10 s |
| Test coverage | ≥ 80% on `ml/` and `backend/` core logic |
| Accessibility | Lighthouse accessibility ≥ 90; no critical axe violations |
| Usability | SUS score ≥ 75 with at least 5 test users |
| Reproducibility | Fresh clone → `make setup && make test` passes |

---

# Part B: Master Roadmap

## B.1 Phase overview

| # | Phase | Main owner | Release | Indicative duration | Depends on |
|---|---|---|---|---|---|
| 0 | Foundations and governance | QA / all | (none) | 2 days | none |
| 1 | Problem framing and data specification | DMR | (spec v1) | 2–3 days | 0 |
| 2 | Data acquisition and synthetic generation | DME | **v0.1** | 3 days | 1 |
| 3 | Exploratory data analysis and audit | DMR | (memo) | 3 days | 2 |
| 4 | Preprocessing and feature pipeline | DME | (lib) | 4 days | 3 |
| 5 | Baselines and first KNN (vertical slice) | DMR + AIE | **v0.2** | 3 days | 4 |
| 6 | KNN optimisation and rigorous evaluation | DMR | **v0.3** | 5 days | 5 |
| 7 | Model comparison and selection | DMR | **v0.4** | 3 days | 6 |
| 8 | Explainability and advanced analytics | AIE | **v0.5** | 5 days | 6 |
| 9 | Fairness, robustness and responsible AI | DMR + AIE | (report) | 4 days | 7, 8 |
| 10 | Model packaging and registry | AIE | (artifact v1) | 2 days | 8, 9 |
| 11 | Backend API | BE | **v0.6** | 6 days | 10 (mock earlier) |
| 12 | Frontend foundation and design system | FE + UX | (kit) | 5 days | 0 (parallel) |
| 13 | Frontend feature pages | FE + UX | **v0.7** | 8 days | 11/12 |
| 14 | Persistence, authentication, RBAC, audit | BE | **v0.8** | 5 days | 11 |
| 15 | Advanced features | AIE + BE + FE | **v0.9-adv** | 8 days | 13, 14 |
| 16 | Quality: testing, performance, security, accessibility | QA | **v0.9** | 5 days | 13, 14 |
| 17 | DevOps, deployment and observability | QA | **v1.0-rc** | 4 days | 16 |
| 18 | Documentation, demo and handover | All | **v1.0** | 4 days | 17 |

## B.2 Parallel tracks (12-week view)

```
Week      1    2    3    4    5    6    7    8    9    10   11   12
Track 1   [P0-P3][P4-P5 ][P6    ][P7-P8       ][P9  ][P10]
Track 2                       [P11 (mock→real)   ][P14      ]
Track 3        [P12 design kit  ][P13 pages (mock API)     ]
Track 4                                   [P15 advanced          ]
                                                   [P16 QA ][P17][P18]
```

**Critical path:** P0 → P1 → P2 → P4 → P5 → P6 → P8 → P10 → P11 → P13 → P16 → P17 → P18. Everything else can overlap.

## B.3 Release map

| Tag | Meaning | Demo-able outcome |
|---|---|---|
| v0.1 | Data ready | Reproducible dataset and data dictionary |
| v0.2 | First vertical slice | Notebook + Streamlit safety-net demo predicts a class |
| v0.3 | Tuned KNN | Validated model with full metric report |
| v0.4 | Model comparison | Evidence-based model choice |
| v0.5 | Explainable model | Neighbours, importance and what-if in notebooks |
| v0.6 | API alpha | Swagger UI serving predictions and explanations |
| v0.7 | Web MVP | Predict, Neighbour Explorer, Batch, Dashboard in React |
| v0.8 | Secure web app | Login, roles, persisted history, audit log |
| v0.9 | Hardened | Tests, performance, security and accessibility passes |
| v1.0 | Release | Deployed, documented, demo-ready |

---

# Part C: Target End-State Architecture

```
                         ┌───────────────────────────────┐
                         │   Browser: React + TS SPA     │
                         │  Tailwind · shadcn/ui · Charts│
                         └───────────────┬───────────────┘
                                         │ HTTPS (JSON, multipart)
                              ┌──────────▼──────────┐
                              │   Reverse proxy     │  TLS, gzip, static assets
                              │   (Nginx / Caddy)   │
                              └──────────┬──────────┘
                                         │
        ┌────────────────────────────────▼───────────────────────────────┐
        │                     FastAPI application                       │
        │  Routers: auth · predict · explain · batch · analytics ·      │
        │           models · fairness · reports · admin                 │
        │  Services: InferenceService · ExplainService · DriftService   │
        │  Cross-cutting: JWT/RBAC · validation · rate-limit · audit    │
        └───────┬──────────────────────┬─────────────────────┬──────────┘
                │                      │                     │
        ┌───────▼───────┐     ┌────────▼────────┐    ┌───────▼────────┐
        │ ML artifacts  │     │   PostgreSQL    │    │  Job worker    │
        │ pipeline.joblib│    │ users, history, │    │ (batch,        │
        │ projection,    │    │ audit, models,  │    │  retrain,      │
        │ metadata.json  │    │ reports         │    │  drift jobs)   │
        └───────────────┘     └─────────────────┘    └────────────────┘
```

**Repository layout (monorepo):**

```
employee-performance-knn/
├── ml/                     # research + training code (importable package)
│   ├── src/epk/            #   data.py features.py train.py evaluate.py explain.py fairness.py drift.py
│   ├── notebooks/          #   01_eda … 09_fairness
│   ├── configs/            #   train.yaml (seeds, grids, paths)
│   └── tests/
├── backend/                # FastAPI service
│   ├── app/                #   main.py api/ core/ db/ schemas/ services/
│   ├── alembic/            #   migrations
│   └── tests/
├── frontend/               # React + Vite + TypeScript
│   ├── src/                #   pages/ components/ hooks/ api/ lib/ styles/
│   └── e2e/                #   Playwright specs
├── artifacts/              # versioned model bundles (git-ignored, or DVC/LFS)
├── data/                   # raw/ processed/ external/ (git-ignored, checksummed)
├── docs/                   # specs, ADRs, model card, user guide
├── deploy/                 # Dockerfiles, compose, nginx, CI templates
├── Makefile  .env.example  README.md  docker-compose.yml
```

---

# Part D: Phase-by-Phase Iterations

> Each phase lists **Goal → Iterations (task, deliverable, DoD) → Key technical notes → Exit gate**.

---

## Phase 0: Foundations and Governance

**Goal:** Anyone can clone the repo, install, lint, test and run a "hello world" in one command.
**Owner:** QA with all. **Duration:** ~2 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 0.1 | Create monorepo, licence, `.gitignore`, README skeleton | Repo on GitHub | Layout in Part C exists |
| 0.2 | Python tooling: Python 3.11+, virtualenv, dependency pinning (`pip-tools`, `uv` or `poetry`), `ruff`, `black`, `pytest`, `pre-commit` | `ml/pyproject.toml`, `backend/requirements.txt`, `.pre-commit-config.yaml` | `pre-commit run --all-files` passes |
| 0.3 | JS tooling: current Node LTS, `pnpm`, ESLint, Prettier, TypeScript strict mode | `frontend/` scaffolded with Vite | `pnpm lint && pnpm build` pass |
| 0.4 | Git workflow, PR template, CODEOWNERS, issue labels | `.github/` folder | First PR merged through the template |
| 0.5 | CI v0: lint + unit tests on every PR (GitHub Actions) | `.github/workflows/ci.yml` | Green check on PR |
| 0.6 | `Makefile` with standard targets | `make setup / lint / test / data / train / api / web` | Works on a fresh clone |
| 0.7 | ADR-001: technology stack decision | `docs/adr/001-stack.md` | Reviewed by all |

**Makefile sketch**

```makefile
setup:   ; python -m venv .venv && .venv/bin/pip install -r backend/requirements.txt -e ml && cd frontend && pnpm install
lint:    ; ruff check . && black --check . && cd frontend && pnpm lint
test:    ; pytest -q && cd frontend && pnpm test --run
data:    ; python -m epk.data --out data/raw --seed 42
train:   ; python -m epk.train --config ml/configs/train.yaml
api:     ; uvicorn app.main:app --reload --app-dir backend
web:     ; cd frontend && pnpm dev
```

**Exit gate:** `make setup && make lint && make test` succeeds on a clean machine; CI is green; ADR-001 signed off.

---

## Phase 1: Problem Framing and Data Specification

**Goal:** Turn the idea into an unambiguous, testable specification (the "contract" the data and model must satisfy).
**Owner:** DMR. **Duration:** 2–3 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 1.1 | Personas and use cases (HR Manager, HR Analyst, Team Lead, Reviewer) | `docs/01-personas.md` | Each persona has 3 jobs-to-be-done |
| 1.2 | Formal problem statement: inputs, output classes (ordered Low < Medium < High), success metrics, non-goals | `docs/01-spec.md` | Metrics and targets from A.4 included |
| 1.3 | Data dictionary: name, type, unit, valid range, missing-value policy, sensitivity | `docs/data_dictionary.md` and `ml/configs/schema.yaml` | Machine-readable schema exists |
| 1.4 | Label definition and leakage review (label derived from a *current-period* appraisal composite; "previous performance score" is *prior-period*) | Section in spec | Reviewer confirms no feature encodes the label |
| 1.5 | Ethics and scope charter: decision support only, no protected attributes as inputs, human review | `docs/01-ethics.md` | Included in model card outline |
| 1.6 | Baseline hypotheses list (for example "higher project count and prior score increase P(High)") | Hypothesis table | Each hypothesis is testable in EDA |

**Core feature schema (source of truth):**

| Feature | Type | Valid range | Missing policy |
|---|---|---|---|
| attendance | float | 0–100 (%) | median impute + missing flag |
| experience_years | float | 0–50 | median |
| training_hours | float | 0–300 | median |
| projects_completed | int | 0–100 | median |
| weekly_hours | float | 0–100 | median |
| prev_score | float | 1–5 | median |
| department, job_level | categorical/ordinal | fixed lists | "Unknown" |
| gender, age_band | **audit-only**, never model inputs | n/a | stored separately |

**Exit gate:** Spec and schema approved; every later phase can be checked against them.

---

## Phase 2: Data Acquisition and Synthetic Generation → **v0.1**

**Goal:** A reproducible, realistic, versioned dataset (plus an external validation set).
**Owner:** DME. **Duration:** ~3 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 2.1 | Generator v1 for the six core features with realistic correlations (experience ↔ training/prev score) and a latent performance score (see project report §5.4) | `ml/src/epk/data.py` | Same seed → identical file |
| 2.2 | Label creation by quantiles of latent score plus noise (30% Low / 45% Medium / 25% High) | `performance` column | Class ratios within ±2% of target |
| 2.3 | Realism layer: 3–5% missing values, small share of outliers, a few duplicate rows, a few impossible values | Dirty dataset | Preprocessing has real work to do |
| 2.4 | Audit-only attributes (`gender`, `age_band`) and optional `department`, `job_level`, generated *independent* of the label by default | Separate `protected.csv` keyed by `employee_id` | Not present in the training table |
| 2.5 | Optional bias-injection switch for Phase 9 demos (label mildly depends on a protected attribute) | `--inject-bias` flag | Default off |
| 2.6 | External validation set: map a public HR dataset's columns to the schema (document every assumption and re-derive the three classes explicitly) | `data/external/` + mapping doc | Licence noted; mapping reviewed |
| 2.7 | Dataset versioning: SHA-256 checksum, `data/README.md`, optional DVC | `data/manifest.json` | Checksum verified by a test |
| 2.8 | Data contract tests | `ml/tests/test_data_contract.py` | Schema, ranges, class balance, no duplicate IDs |

**Realism guidance:** if a first model gets ~100% accuracy, the generator is too deterministic. Increase noise until the achievable CV macro-F1 is roughly 0.80–0.92, with visible overlap between adjacent classes.

**Exit gate (v0.1):** `make data` regenerates the exact dataset; contract tests pass; manifest committed.

---

## Phase 3: Exploratory Data Analysis and Audit

**Goal:** Understand the data well enough to justify every preprocessing and modelling decision.
**Owner:** DMR. **Duration:** ~3 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 3.1 | Structural audit: shape, dtypes, missingness matrix, duplicates | `01_eda.ipynb` §1 | Issues catalogued with counts |
| 3.2 | Univariate analysis: histograms/KDE, skewness, outlier fences (IQR, z-score) | §2 | Outlier policy proposed per feature |
| 3.3 | Class balance and per-class distributions (box/violin) | §3 | Separation strength ranked per feature |
| 3.4 | Correlation (Pearson/Spearman), VIF for multicollinearity | §4 | Redundant features flagged |
| 3.5 | Separability check: 2-D PCA/UMAP projection, per-class silhouette, quick k-NN score as a "ceiling" hint | §5 | Expected performance range stated |
| 3.6 | Hypothesis testing: Kruskal-Wallis across classes per feature, effect sizes | §6 | Each Phase 1 hypothesis marked supported or not |
| 3.7 | EDA decision memo | `docs/03-eda-findings.md` | Lists decisions (impute, cap, drop, engineer) with evidence |

**Exit gate:** Memo reviewed; preprocessing plan for Phase 4 is fully specified and evidence-based.

---

## Phase 4: Preprocessing and Feature Pipeline

**Goal:** One reusable, leakage-safe, tested transformation pipeline used identically in training and serving.
**Owner:** DME. **Duration:** ~4 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 4.1 | Validation layer (schema + range checks) with clear error messages | `epk/validate.py` | Rejects bad rows with row-level reasons |
| 4.2 | Imputation (median numeric, mode categorical) with optional missing-indicator flags | in `features.py` | Fit on train only |
| 4.3 | Outlier handling: winsorisation with learned bounds (custom transformer) | `Winsorizer` | Bounds learned from train only |
| 4.4 | Encoding: ordinal for `job_level`, one-hot (or Gower option) for `department` | `ColumnTransformer` | Unknown categories handled safely |
| 4.5 | Scaling experiments: Min-Max vs Standard vs Robust | Ablation table | Choice justified by CV, recorded in ADR |
| 4.6 | Feature engineering candidates: `projects_per_year = projects / (experience + 1)`, `training_per_project = training / (projects + 1)`, attendance bands | Feature config flags | Each has an on/off ablation |
| 4.7 | Package as one `build_preprocessor(config)` function | `features.py` | Imported by training and backend |
| 4.8 | Unit tests: shapes, no NaN out, idempotence, **leakage test** (fit on train, verify test stats are never used) | `ml/tests/test_features.py` | All pass in CI |

**Reference: winsorising transformer**

```python
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class Winsorizer(BaseEstimator, TransformerMixin):
    """Clip each column to quantile bounds learned on the training data only."""
    def __init__(self, lower=0.01, upper=0.99):
        self.lower, self.upper = lower, upper

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=float)
        self.lo_ = np.nanquantile(X, self.lower, axis=0)
        self.hi_ = np.nanquantile(X, self.upper, axis=0)
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, dtype=float), self.lo_, self.hi_)
```

**Reference: preprocessor factory**

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler

NUM = ["attendance", "experience_years", "training_hours",
       "projects_completed", "weekly_hours", "prev_score"]

def build_preprocessor(scaler=None):
    scaler = scaler or MinMaxScaler()
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")),
                        ("winsor", Winsorizer(0.01, 0.99)),
                        ("scale", scaler)])
    return ColumnTransformer([("num", numeric, NUM)], remainder="drop")
```

**Exit gate:** `build_preprocessor()` is tested, documented and frozen as the single source of truth.

---

## Phase 5: Baselines and First KNN (Vertical Slice) → **v0.2**

**Goal:** A working end-to-end path that predicts a class, plus baselines that give every later number meaning.
**Owner:** DMR + AIE. **Duration:** ~3 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 5.1 | **Freeze the split:** stratified 80/20, seed 42; save index files and hash | `data/processed/split.json` | Test-set hash checked in CI |
| 5.2 | Baselines: majority class, stratified random, logistic regression | Baseline table | Recorded in experiment log |
| 5.3 | Vanilla KNN (k = 5) **unscaled vs scaled** | Ablation figure | Scaled beats unscaled (evidence for the viva) |
| 5.4 | First metrics: accuracy, per-class precision/recall/F1, confusion matrix | `reports/v0.2_metrics.md` | Matches spec metric definitions |
| 5.5 | **Safety-net demo:** minimal Streamlit app (sliders → class + probabilities) | `ml/demo_app.py` | Runs locally; kept as fallback for presentations |
| 5.6 | Experiment log started (Appendix D template) | `reports/experiments.csv` | Every run appends a row |

**Exit gate (v0.2):** Someone unfamiliar with the project can move sliders and see a prediction; baseline numbers are recorded.

---

## Phase 6: KNN Optimisation and Rigorous Evaluation → **v0.3**

**Goal:** The best defensible KNN configuration, evaluated honestly.
**Owner:** DMR. **Duration:** ~5 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 6.1 | CV design: repeated stratified K-fold (for example 5×3) on the training set | `train.yaml` | Fold scores stored |
| 6.2 | Grid/random search over `n_neighbors` (1–31 odd), `weights` (uniform/distance), `p` (1/2), scaler choice, `algorithm` (auto/kd_tree/ball_tree) | `search_results.csv` | Scoring is macro-F1 |
| 6.3 | Feature subset and **feature-weighting** experiment (weights from permutation importance applied after scaling) | Ablation table | Keep only if CV improvement is meaningful |
| 6.4 | Imbalance handling if needed: SMOTE/resampling **inside an `imblearn` Pipeline** (KNN has no `class_weight`) | Comparison | Resampling never touches validation folds |
| 6.5 | Probability calibration: KNN probabilities are coarse vote fractions, so test sigmoid/isotonic calibration | Reliability diagram | Brier score reported before/after |
| 6.6 | Diagnostic curves: k-vs-score (validation curve), learning curve, train/validation gap | Figures | Bias–variance story written |
| 6.7 | **Single final test evaluation** with the chosen config | `reports/v0.3_final.md` | Test set used exactly once |
| 6.8 | Ordinal error analysis: exact / adjacent / extreme error rates; top-10 confident mistakes | Table + notes | Extreme error target from A.4 checked |
| 6.9 | Latency benchmark for single and batch prediction | Benchmark table | Meets API budgets in A.4 |

**Reference: tuning skeleton**

```python
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

pipe = Pipeline([("prep", build_preprocessor()), ("knn", KNeighborsClassifier())])
grid = {"knn__n_neighbors": list(range(1, 32, 2)),
        "knn__weights": ["uniform", "distance"],
        "knn__p": [1, 2]}
cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
search = GridSearchCV(pipe, grid, cv=cv, scoring="f1_macro", n_jobs=-1, refit=True)
search.fit(X_train, y_train)
```

**Exit gate (v0.3):** Final model config recorded in ADR-002 with CV mean ± std, test metrics, calibration decision and error analysis.

---

## Phase 7: Model Comparison and Selection → **v0.4**

**Goal:** Prove, with evidence, that the chosen model (and KNN's role) is justified.
**Owner:** DMR. **Duration:** ~3 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 7.1 | Candidate set: Logistic Regression, Decision Tree, Random Forest, Naive Bayes, SVM, Gradient Boosting (plus KNN) | `compare.py` | All use the same `build_preprocessor()` and splits |
| 7.2 | Fair tuning: each candidate gets an equal tuning budget; **nested CV** for unbiased estimates | Results table | Inner/outer folds documented |
| 7.3 | Significance testing: paired comparison over fold scores (Wilcoxon or Friedman + post-hoc) and McNemar on test predictions | Stats table | p-values and effect sizes reported |
| 7.4 | Multi-criteria selection matrix: macro-F1, extreme-error rate, latency, explainability, calibration | Weighted scorecard | Weights justified in ADR |
| 7.5 | Decision: KNN remains the **primary, explainable** model; the strongest challenger is kept as a **benchmark** shown on the Model Lab page | ADR-003 | Honest write-up even if another model scores higher |
| 7.6 | Export comparison results as JSON for the UI | `artifacts/v1/comparison.json` | Schema matches API contract |

**Exit gate (v0.4):** Comparison table, significance results and ADR-003 finalised.

---

## Phase 8: Explainability and Advanced Analytics → **v0.5**

**Goal:** Make every prediction transparent and actionable. This is the project's signature differentiator.
**Owner:** AIE. **Duration:** ~5 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 8.1 | Neighbour retrieval: k nearest training employees with distances, classes and feature values, plus vote fractions | `explain.py::explain()` | Verified against brute-force distances in a test |
| 8.2 | 2-D projection: PCA fitted on the *scaled training data*, saved as an artifact; project the query and neighbours; keep a 500-point background sample for the scatter plot | `projection.joblib` | Explained variance recorded; UI note that 2-D distance is only an approximation |
| 8.3 | Global importance: permutation importance on validation data (macro-F1 drop) | `importance.json` | Stable across repeats |
| 8.4 | Local attribution: replace one feature at a time with the training median, record the shift in predicted-class probability | `local_attribution()` | Sums and signs sanity-checked |
| 8.5 | Counterfactual advisor over **actionable** features only (training hours, projects), never attendance history or experience | `counterfactual()` | Returns path and effort; always framed as a suggestion |
| 8.6 | Deterministic plain-language summary generator (template-based, no free-text model) | `summarise()` | Reviewed for neutral, non-punitive tone |
| 8.7 | Clustering personas: K-Means on scaled features, k chosen by silhouette, personas named from centroids; cross-tab with classes | `personas.json` | Personas are stable across seeds |
| 8.8 | Faithfulness checks: removing the top-attributed feature changes the probability more than removing a random feature (averaged over many rows) | Test + figure | Passes on ≥ 80% of sampled rows |

**Reference: neighbour explanation**

```python
import pandas as pd

def explain(pipe, X_train: pd.DataFrame, y_train: pd.Series, x_new: pd.DataFrame):
    prep, knn = pipe.named_steps["prep"], pipe.named_steps["knn"]
    dist, idx = knn.kneighbors(prep.transform(x_new))
    nb = X_train.iloc[idx[0]].copy()
    nb["class"] = y_train.iloc[idx[0]].values
    nb["distance"] = dist[0].round(4)
    votes = nb["class"].value_counts(normalize=True).to_dict()
    return nb.reset_index(drop=True), votes
```

**Reference: local attribution by feature ablation**

```python
def local_attribution(pipe, x_row: pd.DataFrame, train_medians: pd.Series):
    classes = list(pipe.classes_)
    base = pipe.predict_proba(x_row)[0]
    pred = classes[int(base.argmax())]
    out = {}
    for f in x_row.columns:
        trial = x_row.copy()
        trial[f] = train_medians[f]
        out[f] = float(base[classes.index(pred)]
                       - pipe.predict_proba(trial)[0][classes.index(pred)])
    return pred, dict(sorted(out.items(), key=lambda kv: -abs(kv[1])))
```
A positive value means the feature pushed the prediction toward the predicted class relative to a "typical" employee.

**Reference: greedy counterfactual**

```python
ACTIONABLE = {"training_hours": (5, 120), "projects_completed": (1, 20)}  # (step, cap)

def counterfactual(pipe, x_row, target="High", max_iter=40):
    x, path = x_row.copy(), []
    ti = list(pipe.classes_).index(target)
    for _ in range(max_iter):
        if pipe.predict(x)[0] == target:
            return x, path
        best = None
        for f, (step, cap) in ACTIONABLE.items():
            if x[f].iloc[0] + step > cap:
                continue
            trial = x.copy()
            trial[f] = trial[f] + step
            p = pipe.predict_proba(trial)[0][ti]
            if best is None or p > best[0]:
                best = (p, f, trial)
        if best is None:
            return None, path
        _, f, x = best
        path.append(f)
    return None, path
```

**Exit gate (v0.5):** Each explanation function has tests; a notebook demo shows one employee end-to-end: prediction → neighbours → attribution → counterfactual.

---

## Phase 9: Fairness, Robustness and Responsible AI

**Goal:** Demonstrate that the system was audited, not just built.
**Owner:** DMR + AIE. **Duration:** ~4 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 9.1 | Group metrics on audit-only attributes: selection rate for High, accuracy, true-positive rate, disparity ratios | `fairness.py` + notebook | Report per attribute |
| 9.2 | Proxy analysis: correlation and mutual information between model features and protected attributes | Table | Suspicious proxies flagged |
| 9.3 | **Bias-injection experiment** on synthetic data: inject bias in labels, show the audit detects it and how metrics move | Figure | Demonstrates the audit tool actually works |
| 9.4 | Robustness: Gaussian noise on inputs, random missing features, boundary stability (do tiny perturbations flip the class?) | Stress-test report | Degradation curves included |
| 9.5 | Uncertainty policy: pick the "needs human review" threshold from a coverage-versus-accuracy curve (for example flag when top-class vote share < 0.6) | ADR-004 | Threshold justified with data |
| 9.6 | Model card and datasheet: intended use, out-of-scope use, data provenance, metrics, fairness results, limitations, contact | `docs/model_card.md`, `docs/datasheet.md` | Reviewed |

**Reference: group fairness table (loop form)**

```python
import pandas as pd

def fairness_table(df: pd.DataFrame, group: str, pos: str = "High"):
    """df needs columns: y_true, y_pred, and the group column."""
    rows = []
    for g, part in df.groupby(group):
        actual_pos = (part.y_true == pos).sum()
        rows.append({
            group: g, "n": len(part),
            "selection_rate": (part.y_pred == pos).mean(),
            "accuracy": (part.y_pred == part.y_true).mean(),
            "tpr": ((part.y_pred == pos) & (part.y_true == pos)).sum() / max(actual_pos, 1),
        })
    out = pd.DataFrame(rows).set_index(group)
    out["disparity_ratio"] = out["selection_rate"] / out["selection_rate"].max()
    return out
```
Treat a disparity ratio well below 1 (for example under 0.8, the common "four-fifths" heuristic) as a **signal to investigate**, not a legal verdict.

**Exit gate:** Fairness and robustness report complete; model card drafted; review flag threshold decided.

---

## Phase 10: Model Packaging and Registry

**Goal:** A single, versioned, verifiable artifact bundle that the backend loads, with no notebook code in production.
**Owner:** AIE. **Duration:** ~2 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 10.1 | Bundle contents: `pipeline.joblib`, `projection.joblib`, `background_sample.parquet`, `train_stats.json` (per-feature quantiles for drift), `importance.json`, `comparison.json`, `personas.json`, `metadata.json` | `artifacts/v1/` | All files generated by one `make train` |
| 10.2 | `metadata.json`: model version (semver), git SHA, data checksum, split hash, library versions, hyperparameters, metrics, review threshold, created timestamp | Schema-validated file | Loader refuses mismatched schema |
| 10.3 | Integrity check: SHA-256 of every artifact verified on load. **Only load artifacts you produced**: `joblib`/pickle files can execute code when loaded | `loader.py` | Tamper test fails as expected |
| 10.4 | Inference contract tests: golden inputs → expected outputs (regression test on the artifact) | `test_artifact.py` | Runs in CI |
| 10.5 | Optional experiment tracking with MLflow (or the CSV log) and a `candidate → champion → archived` lifecycle | Registry notes | Promotion rule documented |

**Exit gate:** `artifacts/v1/` is reproducible from a clean checkout and passes contract tests.

---

## Phase 11: Backend API → **v0.6**

**Goal:** A clean, documented, validated REST API around the artifact.
**Owner:** BE. **Duration:** ~6 days (mock server available from day 1 for the frontend).

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 11.1 | Project skeleton: FastAPI app factory, settings via environment (`pydantic-settings`), structured logging, `/health` and `/version` | `backend/app/` | `GET /health` returns model version |
| 11.2 | Request/response schemas (Pydantic v2) with strict ranges and examples | `schemas/` | Bad input returns HTTP 422 with field-level messages |
| 11.3 | `POST /api/v1/predict` | Router + service | Returns label, probabilities, confidence, `needs_review`, model version |
| 11.4 | `POST /api/v1/explain` | Router + service | Returns neighbours, votes, 2-D projection, attribution, counterfactual |
| 11.5 | `POST /api/v1/batch` (CSV upload): validate, report row errors, predict; synchronous up to a size limit, background job above it | Router + job model | 5,000 rows < 10 s; error report downloadable |
| 11.6 | Analytics endpoints: dataset summary, class distribution, correlations, model metrics, comparison, importance, personas | Routers | Match `comparison.json` etc. |
| 11.7 | Consistent error format (problem-details style: `type`, `title`, `status`, `detail`, `errors[]`) and global exception handlers | `core/errors.py` | Every error path tested |
| 11.8 | Security basics: CORS allow-list, request size limits, file-type sniffing for uploads, basic rate limiting | Middleware | Tests for oversized/invalid uploads |
| 11.9 | OpenAPI export and generated TypeScript types for the frontend | `openapi.json`, `frontend/src/api/types.ts` | Frontend compiles against it |
| 11.10 | Mock server (for example MSW or Prism) from the OpenAPI file | `frontend/mocks/` | Frontend can run without the backend |

**Reference: schemas and prediction endpoint**

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
import pandas as pd

class EmployeeIn(BaseModel):
    attendance: float = Field(ge=0, le=100, examples=[92])
    experience_years: float = Field(ge=0, le=50, examples=[6])
    training_hours: float = Field(ge=0, le=300, examples=[55])
    projects_completed: int = Field(ge=0, le=100, examples=[9])
    weekly_hours: float = Field(ge=0, le=100, examples=[44])
    prev_score: float = Field(ge=1, le=5, examples=[4.1])

class PredictOut(BaseModel):
    label: str
    probabilities: dict[str, float]
    confidence: float
    needs_review: bool
    model_version: str

app = FastAPI(title="Employee Performance API", version="1.0.0")

@app.post("/api/v1/predict", response_model=PredictOut)
def predict(emp: EmployeeIn):
    x = pd.DataFrame([emp.model_dump()])
    proba = bundle.pipeline.predict_proba(x)[0]
    classes = list(bundle.pipeline.classes_)
    top = float(proba.max())
    return PredictOut(
        label=classes[int(proba.argmax())],
        probabilities={c: float(p) for c, p in zip(classes, proba)},
        confidence=top,
        needs_review=top < bundle.meta["review_threshold"],
        model_version=bundle.meta["version"],
    )
```

**Exit gate (v0.6):** Swagger UI works; contract tests, validation tests and batch tests pass; OpenAPI file frozen for the frontend.

---

## Phase 12: Frontend Foundation and Design System

**Goal:** A polished, accessible UI kit and application shell before any feature page is built. Runs **in parallel** with Phases 4–11 using the mock API.
**Owner:** FE + UX. **Duration:** ~5 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 12.1 | Design tokens: colours, spacing (8-pt), radii, shadows, typography scale; light and dark themes | `tailwind.config`, `tokens.css` | Contrast checked ≥ 4.5:1 |
| 12.2 | Class semantics: High (teal-green `#1B9E77` with ▲), Medium (amber `#E0A100` with ●), Low (coral `#D95F02` with ▼); always icon + text + colour | `<ClassChip/>` | Works in grayscale |
| 12.3 | Component kit (shadcn/ui + Radix): Button, Card, KPI card, Slider+NumberInput pair, Tabs, Table (sort/filter), Dialog, Toast, Tooltip, Skeleton, EmptyState, ErrorState, FileDropzone | `components/ui/` | Each has keyboard and screen-reader behaviour |
| 12.4 | App shell: collapsible sidebar, top bar, theme toggle (remembers choice), breadcrumbs, responsive breakpoints | `AppLayout` | Works at 360 px, 768 px, 1280 px+ |
| 12.5 | Routing (React Router), server-state layer (TanStack Query), light client state (Zustand), API client from the OpenAPI types | `api/`, `hooks/` | Loading, error and empty states standardised |
| 12.6 | Chart wrappers with accessible text alternatives: bar, donut, line, heatmap (confusion matrix), scatter | `components/charts/` | Every chart has a "view as table" toggle |
| 12.7 | Optional: Storybook for the kit; visual regression on key components | Storybook | Reviewed by UX |
| 12.8 | UX writing guide: neutral, respectful, plain-language; standard disclaimers | `docs/ux-writing.md` | Applied in all copy |

**Reference: typed data hook (TanStack Query)**

```tsx
import { useMutation } from "@tanstack/react-query";
import { api } from "../api/client";
import type { EmployeeIn, PredictOut } from "../api/types";

export function usePredict() {
  return useMutation<PredictOut, Error, EmployeeIn>({
    mutationFn: (emp) => api.post("/api/v1/predict", emp).then((r) => r.data),
  });
}
```

**Exit gate:** Kit + shell deployed to a preview URL against the mock API; UX signs off on visual language.

---

## Phase 13: Frontend Feature Pages → **v0.7**

**Goal:** Every screen from the UI/UX blueprint, functional and polished.
**Owner:** FE + UX. **Duration:** ~8 days. Build in this order (each page is one or more iterations).

| ID | Page | Key behaviour | DoD |
|---|---|---|---|
| 13.1 | **Predict** (hero screen) | Sliders + number inputs, example loaders (High/Medium/Low), live **k** control (Model Lab mode), probability bars, confidence, review flag, "Why?" summary | Result within 300 ms of a change; keyboard-only usable |
| 13.2 | **Neighbour Explorer** (signature) | PCA scatter with query star and highlighted neighbours, neighbour table with distances, radar chart vs class averages, k slider updating votes | Tooltip on every element; note explaining 2-D approximation |
| 13.3 | **What-if / Advisor** | Adjust one lever, watch class/probabilities change; counterfactual suggestions with clear "suggestion, not guarantee" wording | Only actionable features editable in advisor mode |
| 13.4 | **Batch Prediction** | Template download, drag-and-drop, pre-run validation report, results table (sort/filter/chips), low-confidence filter, CSV export | Handles 5,000 rows smoothly (virtualised table) |
| 13.5 | **Overview Dashboard** | KPI cards, class donut, class-by-department bars, confusion-matrix heatmap, accuracy-vs-k line, filters | Every chart has a text/table alternative |
| 13.6 | **Model Lab** | Tune KNN parameters, compare algorithms, learning curves, feature importance; deployed configuration clearly marked | Metrics update from server responses, not hard-coded |
| 13.7 | **Data Explorer** | Distributions, correlations, missingness, class balance per feature | Filter by department/job level |
| 13.8 | **Fairness & Bias** | Group tables with traffic-light indicators, plain-language explanations, link to model card | Restricted to authorised roles (Phase 14) |
| 13.9 | **Reports** | Generate/download summaries (PDF added in Phase 15) | Print stylesheet works |
| 13.10 | **Methodology & About** | Pipeline diagram, model card summary, limitations, ethics | Content mirrors `docs/model_card.md` |
| 13.11 | Onboarding tour (3–4 steps), empty states, help tooltips explaining every metric in plain words | Tour component | Skippable, remembers dismissal |
| 13.12 | Frontend tests: component tests (Vitest + Testing Library) and 3 e2e flows (predict, batch, explain) with Playwright | `frontend/e2e/` | Green in CI |

**Reference wireframe (Predict):**

```
┌────────────────────────────┬──────────────────────────────────────┐
│ Employee details           │ RESULT                               │
│ Attendance       [92] ━●━  │ ▲ HIGH PERFORMANCE                   │
│ Experience (yrs) [ 6] ━●━  │ Confidence 80% (4 of 5 neighbours)   │
│ Training hrs     [55] ━●━  │ High   ████████░░ 80%                │
│ Projects         [ 9] ━●━  │ Medium ██░░░░░░░░ 20%                │
│ Weekly hours     [44] ━●━  │ Low    ░░░░░░░░░░  0%                 │
│ Prev. score      [4.1]━●━  │ Why? projects ↑ · prev. score ↑      │
│ [Load example ▾] [Classify]│ [See nearest employees →] [What-if]  │
└────────────────────────────┴──────────────────────────────────────┘
```

**Exit gate (v0.7):** Full click-through demo against the real API; no console errors; responsive; keyboard navigation works on all pages.

---

## Phase 14: Persistence, Authentication, RBAC and Audit → **v0.8**

**Goal:** Turn the demo into a secure multi-user application with traceable actions.
**Owner:** BE (with FE for guards). **Duration:** ~5 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 14.1 | PostgreSQL schema + Alembic migrations (Appendix C); SQLite for local dev | `db/models.py`, `alembic/` | `alembic upgrade head` works on empty DB |
| 14.2 | Authentication: email + password with a modern password hash (Argon2 or bcrypt), short-lived JWT access token + refresh token (httpOnly cookie), logout/rotation | `auth` router | Brute-force attempts rate-limited |
| 14.3 | RBAC (matrix below) enforced by dependency injection on every route | `core/security.py` | Negative tests for each role |
| 14.4 | Persist predictions (input, output, model version, user) and batch jobs | Tables + repositories | History page can query them |
| 14.5 | Audit log for sensitive actions (login, export, retrain, role change, fairness view) | `audit_logs` | Immutable append-only writes |
| 14.6 | Privacy controls: pseudonymous employee references, protected attributes in a separate restricted table, retention policy and delete endpoint | Docs + code | Verified by tests |
| 14.7 | Frontend: login page, route guards, role-aware navigation, session-expiry handling | FE changes | Unauthorised pages are not reachable or rendered |
| 14.8 | Seed script: demo users per role and demo data | `make seed` | One command prepares a demo environment |

**RBAC matrix**

| Action | Admin | HR Manager | Analyst | Viewer |
|---|:-:|:-:|:-:|:-:|
| Single predict + explain | ✓ | ✓ | ✓ | ✓ |
| Batch upload | ✓ | ✓ | ✓ |  |
| View dashboard / data explorer | ✓ | ✓ | ✓ | ✓ |
| Model Lab (tune/compare) | ✓ |  | ✓ |  |
| Fairness page | ✓ | ✓ | ✓ |  |
| Export reports | ✓ | ✓ | ✓ |  |
| Retrain / promote model | ✓ |  |  |  |
| Manage users / view audit log | ✓ |  |  |  |

**Exit gate (v0.8):** Role-based access verified by automated tests; audit log populated; no plaintext secrets anywhere.

---

## Phase 15: Advanced Features → **v0.9-adv**

**Goal:** The differentiators that lift the project above a standard submission. Implement in priority order; each is independently shippable behind a **feature flag**.
**Owner:** AIE + BE + FE. **Duration:** ~8 days.

| ID | Feature | Design notes | DoD |
|---|---|---|---|
| 15.1 | **PDF reports** (employee report, batch summary, model card) | Server-side HTML → PDF (for example WeasyPrint or ReportLab); includes disclaimer and model version | Renders identically on two machines |
| 15.2 | **Drift monitoring** | Compare live input distributions with `train_stats.json` using PSI and KS test; scheduled job; page with per-feature status (green/amber/red) | Injected shift is detected in a test |
| 15.3 | **Governed retraining** | Admin uploads new labelled data → job trains a *candidate* → auto-compares to champion on a frozen holdout → admin approves promotion → hot reload | Rollback works in one click |
| 15.4 | **Team / department analytics** | Aggregations and drill-down (minimum group size enforced to avoid identifying individuals) | Groups smaller than a threshold are suppressed |
| 15.5 | **Time-trend view** | Quarterly snapshots per employee; trend chart of predicted class and probability | Data model supports periods (`employee_snapshots`) |
| 15.6 | **Persona clusters page** | K-Means personas, cross-tab with classes, plain-language persona descriptions | Personas stable across reruns |
| 15.7 | **Second-opinion benchmark** | Show the strongest challenger model's prediction next to KNN and flag disagreements for review | Disagreement rate reported on dashboard |
| 15.8 | **API keys / integration access** for external tools | Scoped, revocable keys, usage logs | Keys hashed at rest |
| 15.9 | **Internationalisation** (English + one more language) and locale-aware numbers/dates | i18n library, string catalogue | Language switch without reload |
| 15.10 | **Notifications** (optional): weekly digest of drift, review-queue size | Email/queue | Opt-in only |
| 15.11 | **Review queue** for low-confidence or disagreeing predictions with reviewer notes | Table + page | Every decision recorded with reviewer and timestamp |

**Reference: Population Stability Index for drift**

```python
import numpy as np

def psi(expected, actual, bins=10):
    cuts = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    cuts[0], cuts[-1] = -np.inf, np.inf
    e = np.histogram(expected, cuts)[0] / len(expected)
    a = np.histogram(actual, cuts)[0] / len(actual)
    e, a = np.clip(e, 1e-6, None), np.clip(a, 1e-6, None)
    return float(np.sum((a - e) * np.log(a / e)))
```
Common rule of thumb: PSI < 0.1 stable, 0.1–0.25 moderate shift, > 0.25 significant shift. Treat these as guidance and calibrate alerts to your data.

**Exit gate:** Each shipped feature has tests, a feature flag, and a short user-guide entry.

---

## Phase 16: Quality: Testing, Performance, Security and Accessibility → **v0.9**

**Goal:** Evidence that the system is correct, fast, safe and usable.
**Owner:** QA. **Duration:** ~5 days (testing also happens continuously in earlier phases).

| ID | Area | Activities | DoD |
|---|---|---|---|
| 16.1 | Test pyramid | Unit (ml, backend), integration (API + DB with a test container), contract (OpenAPI schema), e2e (Playwright) | Coverage target in A.4 met |
| 16.2 | Model regression | Golden-input tests, metric thresholds on the frozen test set, calibration and fairness thresholds | CI fails if a retrained model regresses |
| 16.3 | Performance | Load test the API (for example k6 or Locust): single-predict p95, batch throughput, concurrent users; profile hot paths | Budgets in A.4 met; results documented |
| 16.4 | Security | Checklist review against common web risks (injection, broken auth/access control, sensitive data exposure, upload abuse, SSRF, insecure deserialisation), dependency vulnerability scan, secret scanning, security headers | No high-severity findings open |
| 16.5 | Accessibility | Automated (axe, Lighthouse) plus manual keyboard and screen-reader pass | Score target in A.4; issues fixed |
| 16.6 | Usability | 5-user task test (predict, upload, explain, what-if) with SUS questionnaire; fix the top 3 issues | SUS ≥ 75 or a documented action plan |
| 16.7 | Cross-browser and device | Latest Chrome, Firefox, Safari, Edge; one small phone and one tablet | Layout and functionality verified |
| 16.8 | Data and model edge cases | Missing columns, wrong types, extreme values, tie votes, single-row CSV, very large files, duplicated IDs, unicode headers | Each has an automated test |

**Exit gate (v0.9):** Quality dashboard green; all critical/high defects closed; release-candidate checklist ready.

---

## Phase 17: DevOps, Deployment and Observability → **v1.0-rc**

**Goal:** One-command, repeatable deployment with visibility into the running system.
**Owner:** QA/DevOps. **Duration:** ~4 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 17.1 | Dockerfiles: backend (slim Python image), frontend (multi-stage build → static files served by Nginx/Caddy), non-root users, health checks | `deploy/` | Images build reproducibly |
| 17.2 | `docker-compose.yml`: `db`, `api`, `web`, optional `worker` and `proxy` | Compose file | `docker compose up` gives a working system |
| 17.3 | CI/CD (GitHub Actions): lint → test → build images → scan → push → deploy to staging on `main`, production on tag | Workflows | A tag produces a deployed release |
| 17.4 | Environments and configuration: dev / staging / prod, secrets through the platform's secret store, `.env.example` only for non-secrets | Docs | No secrets in the repo history |
| 17.5 | Hosting: pick a target (cloud VM or container platform; static frontend host plus API host is a common low-cost split). Verify current pricing and free-tier limits before committing | ADR-005 | Public HTTPS URL with a custom domain (optional) |
| 17.6 | Observability: structured JSON logs with request IDs, health/readiness endpoints, basic metrics (latency, errors, prediction counts), error tracking (optional) | Dashboards | Alert for elevated error rate and drift status |
| 17.7 | Backups and recovery: automated DB backups, tested restore, artifact retention | Runbook | Restore drill completed once |
| 17.8 | Release process: semantic versioning, changelog, rollback procedure | `CHANGELOG.md`, runbook | Rollback rehearsed |

**Reference: compose sketch**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: epk
      POSTGRES_USER: epk
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: [dbdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U epk"]
      interval: 5s
      retries: 10
  api:
    build: { context: ., dockerfile: deploy/backend.Dockerfile }
    environment:
      DATABASE_URL: postgresql+psycopg://epk:${DB_PASSWORD}@db:5432/epk
      JWT_SECRET: ${JWT_SECRET}
      ARTIFACT_DIR: /artifacts/v1
    volumes: [./artifacts:/artifacts:ro]
    depends_on: { db: { condition: service_healthy } }
  web:
    build: { context: ., dockerfile: deploy/frontend.Dockerfile }
    ports: ["80:80"]
    depends_on: [api]
volumes: { dbdata: {} }
```

**Reference: backend Dockerfile**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ml/ /ml
RUN pip install --no-cache-dir /ml
COPY backend/ .
RUN useradd -m appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Exit gate (v1.0-rc):** A fresh environment can be built and deployed from scratch using only the README and CI.

---

## Phase 18: Documentation, Demo and Handover → **v1.0**

**Goal:** The project can be understood, demonstrated, defended and maintained by someone who was not on the team.
**Owner:** All. **Duration:** ~4 days.

| ID | Task | Deliverable | DoD |
|---|---|---|---|
| 18.1 | README with screenshots/GIFs, quick start, architecture diagram, live link | `README.md` | New user runs it in under 10 minutes |
| 18.2 | Documentation set: architecture, API reference (from OpenAPI), data dictionary, model card, datasheet, user guide per role, runbook, ADR index | `docs/` | Linked from README |
| 18.3 | Final project report update (methods, results tables, figures, ethics, limitations, future work) | Report | Numbers match the released artifact |
| 18.4 | Presentation deck (10–12 slides) and 3-minute demo video; pre-recorded fallback | Assets | Rehearsed twice |
| 18.5 | Viva preparation: each member explains the full pipeline; question bank from the project report §15.3 | Q&A sheet | Mock viva completed |
| 18.6 | Retrospective and lessons learned; backlog for v1.1+ | `docs/retro.md` | Prioritised backlog created |
| 18.7 | Tag `v1.0`, publish release notes | GitHub release | Artifacts attached |

**Demo script (5 minutes)**
1. Problem in one sentence (20 s).
2. Predict a High-looking employee → probabilities and confidence (40 s).
3. Open **Neighbour Explorer**, change k, watch the vote change (60 s).
4. **What-if advisor**: what moves a Medium to High (40 s).
5. **Batch upload** with a deliberately messy CSV → validation report → export (60 s).
6. **Model Lab**: comparison table, honest note on trade-offs (30 s).
7. **Fairness page** and **model card**, then limitations (30 s).
8. Close with architecture and roadmap (20 s).

**Exit gate (v1.0):** All Part E checklists complete; release published.

---

# Part E: Cross-Cutting Standards

## E.1 Master Definition of Done (applies to every iteration)

- [ ] Code reviewed and merged via PR; CI green
- [ ] Unit/integration tests added or updated
- [ ] No new lint or type errors; no secrets committed
- [ ] Docs updated (docstrings, README section, ADR if a decision was made)
- [ ] Experiment logged (for modelling work) with seed, data hash, config and metrics
- [ ] Accessibility and error states handled (for UI work)
- [ ] Demo-able in the next sprint review

## E.2 Coding standards

| Area | Standard |
|---|---|
| Python | Type hints on public functions, docstrings, `ruff` + `black`, small pure functions, no notebooks imported into production |
| Notebooks | Numbered, cleaned outputs before commit, all reusable logic moved into `epk/` |
| API | Versioned paths (`/api/v1`), pagination on lists, idempotent uploads where possible, consistent error format |
| Frontend | TypeScript strict, no `any` in new code, components small and tested, accessibility lint rules on |
| Git | Small PRs (< 400 changed lines where possible), conventional commits, squash-merge |

## E.3 Risk register

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Synthetic data too easy (near-perfect scores) | Medium | High | Noise/overlap tuning in 2.3; external validation set (2.6) | DME |
| Data leakage inflates metrics | Medium | High | Pipelines only, leakage tests (4.8), frozen test set (5.1) | DMR |
| Scope creep in Phase 15 | High | Medium | Feature flags, priority order, freeze at week 10 | PM/all |
| Frontend blocked by backend delay | Medium | Medium | OpenAPI-first, mock server (11.10) | BE/FE |
| Demo-day failure | Low | High | Pre-recorded video, Streamlit fallback (5.5), staging URL | QA |
| Insecure model loading | Low | High | Load only self-produced artifacts; hash verification (10.3) | AIE |
| Fairness or ethics criticism | Medium | Medium | Phase 9 audit, model card, human-review policy | DMR |
| Key member unavailable | Medium | Medium | Pairing, code review, cross-training, docs | All |
| Deployment cost or limit surprises | Low | Medium | Verify current pricing/limits early (17.5) | QA |

## E.4 Progress tracking (KPIs per sprint)

| Metric | Why it matters |
|---|---|
| Phases exited / planned | Schedule health |
| CV macro-F1 (mean ± std) trend | Model progress without test-set peeking |
| Open critical/high defects | Quality gate |
| Test coverage % | Regression safety |
| API p95 latency | Performance budget |
| Lighthouse accessibility score | UX quality |
| Review-queue size / disagreement rate (post-Phase 15) | Model trust in operation |

## E.5 Compressed 6-week path (if time is short)

| Week | Do | Skip or defer |
|---|---|---|
| 1 | Phases 0–2 (light), 3 | Public-dataset mapping (2.6), VIF/UMAP details |
| 2 | Phases 4–5 (including the Streamlit safety net) | Winsor/feature-engineering ablations beyond one or two |
| 3 | Phase 6 (grid search, curves, final test), Phase 7 (comparison without nested CV) | Calibration, feature weighting |
| 4 | Phase 8 (neighbours, PCA, importance, counterfactual), Phase 10 | Personas, faithfulness checks |
| 5 | Phases 11 and 12–13 (Predict, Neighbour Explorer, Batch, Dashboard) | Data Explorer, Reports polish |
| 6 | Phase 9 (essential fairness table), 14 (basic login), 16–18 (smoke tests, Docker, docs, demo) | Phase 15 except review flag and PDF, full RBAC matrix |

---

# Appendices

## Appendix A: Folder-Level Ownership

| Path | Primary owner | Reviewers |
|---|---|---|
| `ml/src/epk/` | DME / AIE | DMR |
| `ml/notebooks/` | DMR | DME |
| `backend/app/` | BE | AIE |
| `frontend/src/` | FE | UX |
| `deploy/`, `.github/` | QA | BE |
| `docs/` | Everyone | Reviewer of the phase |

## Appendix B: API Contract (v1)

| Method | Path | Purpose | Roles |
|---|---|---|---|
| GET | `/health`, `/version` | Liveness, model version | public |
| POST | `/api/v1/auth/login`, `/refresh`, `/logout` | Session handling | public/auth |
| POST | `/api/v1/predict` | Single prediction | all |
| POST | `/api/v1/explain` | Neighbours, projection, attribution, counterfactual | all |
| POST | `/api/v1/batch` | CSV upload → validation + predictions | Admin, HR, Analyst |
| GET | `/api/v1/batch/{id}` | Job status and results | owner/Admin |
| GET | `/api/v1/analytics/summary` | Dataset and class summary | all |
| GET | `/api/v1/analytics/correlations`, `/distributions` | EDA data | all |
| GET | `/api/v1/models/current`, `/comparison`, `/importance` | Model metadata and evidence | all |
| POST | `/api/v1/models/tune` | Live k/metric evaluation on validation data | Admin, Analyst |
| GET | `/api/v1/fairness` | Group fairness report | Admin, HR, Analyst |
| GET | `/api/v1/drift` | Drift status | Admin, Analyst |
| POST | `/api/v1/models/retrain`, `/promote`, `/rollback` | Governed lifecycle | Admin |
| GET | `/api/v1/reports/{type}` | PDF/CSV reports | Admin, HR, Analyst |
| GET | `/api/v1/audit` | Audit log | Admin |

**Example: `POST /api/v1/explain` response**

```json
{
  "prediction": {"label": "High", "probabilities": {"High": 0.8, "Medium": 0.2, "Low": 0.0},
                 "confidence": 0.8, "needs_review": false, "model_version": "1.0.0"},
  "neighbours": [
    {"rank": 1, "class": "High", "distance": 0.112,
     "features": {"attendance": 93, "experience_years": 6.5, "training_hours": 58,
                  "projects_completed": 9, "weekly_hours": 43, "prev_score": 4.0},
     "xy": [0.41, -0.22]}
  ],
  "votes": {"High": 0.8, "Medium": 0.2},
  "query_xy": [0.39, -0.20],
  "projection": {"explained_variance": [0.46, 0.21]},
  "attribution": {"projects_completed": 0.21, "prev_score": 0.17, "attendance": 0.06},
  "counterfactual": null,
  "summary": "Predicted High: 4 of the 5 most similar employees were High. Project output and prior score were the strongest contributors. This is decision support and should be reviewed by a person."
}
```

## Appendix C: Database Schema (PostgreSQL)

| Table | Key columns | Notes |
|---|---|---|
| `users` | id, email (unique), password_hash, role, is_active, created_at | Roles: admin, hr_manager, analyst, viewer |
| `employees` | id, external_ref (pseudonymous), department, job_level, created_at | No names required |
| `employee_protected_attrs` | employee_id (FK), gender, age_band | **Restricted table**; audit use only |
| `employee_snapshots` | id, employee_id (FK), period, attendance, experience_years, training_hours, projects_completed, weekly_hours, prev_score | Supports time trends |
| `predictions` | id, snapshot_id (nullable), input_json, label, proba_json, confidence, needs_review, model_version, user_id, created_at | History and audit |
| `review_items` | id, prediction_id (FK), status, reviewer_id, note, decided_at | Human-in-the-loop queue |
| `batch_jobs` | id, user_id, filename, status, row_count, error_count, result_path, created_at, finished_at | Async batches |
| `model_versions` | id, version, artifact_path, sha256, metrics_json, params_json, status (candidate/champion/archived), created_at, promoted_by | Registry |
| `drift_reports` | id, model_version, created_at, psi_json, ks_json, status | Monitoring |
| `fairness_reports` | id, model_version, created_at, report_json | Stored audits |
| `api_keys` | id, name, key_hash, scopes, created_by, revoked_at, last_used_at | Hashed at rest |
| `audit_logs` | id, user_id, action, entity, entity_id, ip, meta_json, created_at | Append-only |

## Appendix D: Templates

**Experiment log row (`reports/experiments.csv`)**

| Column | Example |
|---|---|
| run_id | 2026-10-04_knn_017 |
| phase / iteration | 6.2 |
| git_sha | a1b2c3d |
| data_checksum | 9f3e… |
| model / params | KNN k=15, weights=distance, p=2, MinMax |
| cv_macro_f1 (mean ± std) | 0.861 ± 0.012 |
| test_macro_f1 | (blank until final) |
| notes | Winsorisation on; SMOTE off |

**ADR template (`docs/adr/NNN-title.md`)**

```
# ADR-NNN: Title
Status: Proposed | Accepted | Superseded by ADR-XXX
Date: YYYY-MM-DD
## Context      (the problem and constraints)
## Options      (2–3 alternatives with pros/cons)
## Decision     (what we chose and why; evidence links)
## Consequences (trade-offs, follow-ups)
```

**Pull request checklist**

```
- [ ] Linked iteration ID (for example 6.2) and issue
- [ ] Tests added/updated and passing
- [ ] Docs/ADR updated
- [ ] No secrets, no large data files
- [ ] Screenshots or GIFs for UI changes
- [ ] Accessibility considered (labels, focus, contrast)
- [ ] Rollback plan noted if it touches data or models
```

**Sprint review checklist**

```
- [ ] Demo of every completed iteration on the shared environment
- [ ] Metrics dashboard reviewed (Part E.4)
- [ ] Risks and blockers reviewed
- [ ] Next sprint scope agreed against the critical path
```

## Appendix E: Recommended Sprint Plan (12 weeks, 6 sprints)

| Sprint | Weeks | Sprint goal | Phases | Release |
|---|---|---|---|---|
| 1 | 1–2 | "Data you can trust" | 0, 1, 2, 3, start 12 (design tokens) | v0.1 |
| 2 | 3–4 | "First end-to-end slice, honest baselines" | 4, 5, 12 (kit), start 6 | v0.2 |
| 3 | 5–6 | "Best defensible model, evidence-based choice" | 6, 7, start 8, 11 (mock + skeleton) | v0.3, v0.4 |
| 4 | 7–8 | "Explainable model behind an API" | 8, 9, 10, 11 | v0.5, v0.6 |
| 5 | 9–10 | "A real web product" | 13, 14, start 15 | v0.7, v0.8 |
| 6 | 11–12 | "Harden, ship, present" | 15 (finish), 16, 17, 18 | v0.9, v1.0 |

## Appendix F: Final Release Checklist (v1.0)

**Data and model**
- [ ] Dataset reproducible; checksum matches manifest
- [ ] Test set used once; final metrics recorded
- [ ] Comparison, significance results and ADRs complete
- [ ] Calibration and review threshold decided and documented
- [ ] Fairness, robustness and drift baselines recorded; model card and datasheet published

**Product**
- [ ] All Phase 13 pages complete and responsive; dark and light themes verified
- [ ] Auth, RBAC and audit log working; negative access tests pass
- [ ] Batch upload handles messy files and large files gracefully
- [ ] Every chart has a text/table alternative; keyboard-only run-through done

**Engineering**
- [ ] CI/CD green; images scanned; no secrets in history
- [ ] Load and security checks documented; backups and rollback rehearsed
- [ ] Observability in place with at least an error-rate alert

**Communication**
- [ ] README, user guide, API reference, runbook complete
- [ ] Demo video recorded; presentation rehearsed; viva Q&A prepared
- [ ] Limitations and ethics stated plainly in the report, the model card and the UI

---

### Closing Guidance

Follow the order deliberately: **trust the data (P1–P4) → prove the model (P5–P7) → make it explainable and fair (P8–P9) → productise it (P10–P14) → differentiate (P15) → harden and ship (P16–P18).** Build the thin vertical slice in Phase 5 so there is always something demonstrable, keep the test set untouched until Phase 6, and treat explainability, fairness and human review as first-class features rather than afterthoughts. If time runs short, use the compressed path in E.5 and protect these non-negotiables: leakage-free evaluation, the Neighbour Explorer, batch prediction with validation, and an honest limitations section.
