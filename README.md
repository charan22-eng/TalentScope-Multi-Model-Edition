# TalentScope Multi-Model Edition

TalentScope is a machine-learning decision-support platform for **human-supervised employee performance review**.

This repository is the `DM-CBP` workspace. The application name shown to users is **TalentScope**.

> **If you remember only one sentence:** TalentScope compares seven machine-learning models, predicts an employee performance band, explains the result, identifies uncertain or conflicting cases for HR review, and records the governance trail around the decision.

---

## Quick Start: How to Run

To run the application, open two separate terminal windows from the repository root:

### 1. Backend API (Terminal 1)
```powershell
python -m uvicorn backend.app.main:app --port 8000 --reload
```
- API server URL: [http://localhost:8000](http://localhost:8000)
- Health check: [http://localhost:8000/ready](http://localhost:8000/ready)
- *(Alternative using `uv`)*: `uv run uvicorn backend.app.main:app --port 8000 --reload` (or `make api`)

### 2. Frontend Web App (Terminal 2)
```powershell
cd frontend
npm run dev
```
- Web application URL: [http://localhost:5173](http://localhost:5173)
- *(Alternative using make)*: `make web`

> **Note:** Direct access enabled — no login screen or credentials required. Opening [http://localhost:5173](http://localhost:5173) loads directly into the Model Arena with all views unlocked.

*(Optional — First-time database setup & seeding if needed)*:
```powershell
python scripts/demo_setup.py
```

---

## Contents

- [Quick Start: How to run](#quick-start-how-to-run)

- [Read this first](#read-this-first)
- [Real-world use cases](#real-world-use-cases)
- [The end-to-end workflow](#the-end-to-end-workflow)
- [Who uses it?](#who-uses-it)
- [What the user sees in the web app](#what-the-user-sees-in-the-web-app)
- [Architecture overview](#architecture-overview)
- [Repository structure](#repository-structure)
- [Technology stack](#technology-stack-and-why-each-part-is-used)
- [The data](#the-data)
- [The seven machine-learning models](#the-seven-machine-learning-models)
- [Training and evaluation](#how-training-and-evaluation-work)
- [Explanations and uncertainty](#explanations-and-uncertainty)
- [Model Arena](#model-arena-and-comparison-science)
- [Fairness, privacy, and ethics](#fairness-privacy-and-ethics)
- [Local LLM verdict engine](#local-llm-verdict-engine)
- [Backend API reference](#backend-api-reference)
- [Database and persistence](#database-and-persistence)
- [Model artifacts and integrity](#model-artifacts-and-integrity)
- [Security controls](#security-controls)
- [Invariant guard suite](#invariant-guard-suite)
- [Current project scope](#current-project-scope)
- [Quick start](#quick-start-for-a-new-developer)
- [CSV batch format](#csv-batch-format)
- [Environment configuration](#environment-configuration)
- [Docker Compose deployment](#docker-compose-deployment)
- [Training and evaluation commands](#training-and-evaluation-commands)
- [Verification and quality commands](#verification-and-quality-commands)
- [Troubleshooting](#troubleshooting)
- [Documentation map](#documentation-map)
- [Glossary](#glossary-for-a-complete-beginner)
- [Viva/presentation summary](#short-explanation-for-a-viva-or-presentation)

## Read this first

### What problem does it solve?

HR teams often review employee performance using spreadsheets, manager judgement, and inconsistent calculations. That creates several problems:

- Two managers may apply different standards to similar employees.
- A performance score may be produced without a clear explanation.
- A model may be confident even when it is wrong or when models disagree.
- Teams may select a machine-learning model using only accuracy and ignore fairness, calibration, speed, or explainability.
- After a decision, it may be difficult to prove what data, model, rule, and human override were used.

TalentScope fills the gap between a raw machine-learning prediction and a responsible HR workflow. It adds model comparison, uncertainty handling, explanations, fairness checks, human review, appeals, audit logs, model versioning, rollback, and privacy controls around the prediction.

### What does it actually do?

For an employee record, the platform can:

1. Accept job-related performance features such as attendance, experience, training, projects, weekly hours, previous score, peer feedback, on-time work, certifications, department, and job level.
2. Predict an ordered performance band: **Low**, **Medium**, or **High**.
3. Run one selected model or all seven models.
4. Return probabilities, confidence, stability, and a conformal prediction set.
5. Explain the prediction with feature attribution, model-native information, counterfactual suggestions, and similar historical cases.
6. Detect low stability, multi-band prediction sets, or disagreement between models.
7. Send uncertain cases to a human HR review queue.
8. Require a written reason when a reviewer overrides the model's band.
9. Compare the seven models using accuracy, ordinal quality, calibration, fairness, robustness, latency, training cost, and explainability.
10. Produce a deterministic model recommendation using MCDA, then optionally ask a local LLM to explain the evidence in plain language.
11. Monitor drift, fairness reports, consent, deletion requests, appeals, model versions, and audit activity.
12. Generate employee transparency and executive comparison PDF reports.

### What it is not

TalentScope is **not** an autonomous employment decision-maker. It must not be used by itself to:

- Hire or reject a person.
- Fire, demote, or discipline an employee.
- Deny a promotion or compensation change.
- Profile employees using protected attributes.
- Replace HR leadership, employee communication, or a right to appeal.

The intended policy is: **the model recommends, a human reviews, and the organization remains accountable**.

## Real-world use cases

### 1. Quarterly performance review support

An HR manager can enter or upload job-related performance information and receive a consistent second opinion. The result is not a final rating. It is a starting point for a documented conversation with the employee and manager.

### 2. Uncertainty-first HR review

The system does not treat every prediction as equally reliable. A case can be flagged when:

- Stability is below 70%.
- The conformal prediction set contains more than one band.
- The champion and shadow model disagree.

Those cases go to the review queue first, so human attention is spent where the model is least certain.

### 3. Model selection for a data-science team

A data-science team can compare seven model families on the same frozen data split and tuning protocol. The team can answer questions such as:

- Is the most accurate model also well calibrated?
- Does a faster model lose too much quality?
- Does the winner change when the organization values fairness or explainability more?
- Is the difference between two models larger than normal sampling noise?

### 4. Responsible AI and governance review

An organization can inspect:

- Which model version was active.
- Which model was selected and under which MCDA profile.
- Which evidence packet supported the recommendation.
- Whether a reviewer overrode the recommendation.
- Which reason was supplied for an override.
- Whether a data-deletion or employee appeal request was submitted.

### 5. Education, research, and demonstration

The repository is also a complete teaching and research example for:

- Comparing classification models fairly.
- Preventing data leakage.
- Calibrating probabilities.
- Using conformal prediction.
- Building explainable ML workflows.
- Adding RBAC and auditability to an ML API.
- Testing an LLM as a constrained narrator rather than as the decision-maker.

## The end-to-end workflow

```text
HR or analyst enters employee features
                |
                v
     FastAPI backend validates the request
                |
                v
   One model or all seven models run inference
                |
                v
 Prediction band + probabilities + stability
       + conformal set + explanations
                |
                v
  Uncertainty / disagreement checks are applied
                |
        +-------+--------+
        |                |
        v                v
  Clear case       Uncertain case
  HR continues     Review queue
                        |
                        v
              Human decision and reason
                        |
                        v
          Audit trail, report, or appeal
```

## The main concepts in plain English

| Term | Meaning in this project |
|---|---|
| **Feature** | An input used by a model, such as attendance or training hours. |
| **Performance band** | The ordered output `Low`, `Medium`, or `High`. Internally these are `0`, `1`, and `2`. |
| **Probability** | The model's estimated likelihood for each band. |
| **Confidence** | The largest probability for the predicted band. |
| **Stability score** | A score used to identify predictions that are too close or uncertain for unattended use. |
| **Conformal prediction set** | A set of plausible bands, such as `Medium` or `High`, instead of pretending only one answer is possible. |
| **Consensus** | The band selected by the majority of the seven model outputs. |
| **Split decision** | The seven models do not all agree on the same band. |
| **Shadow model** | A second model run in parallel for comparison while the active model remains the main result. |
| **Calibration** | Adjusting probabilities so that a probability such as 0.80 is more trustworthy as an approximate frequency. |
| **MCDA** | Multi-Criteria Decision Analysis: a weighted calculation that combines quality, calibration, speed, fairness, cost, and explainability. |
| **Drift** | A change in the distribution of incoming data compared with the reference data used during development. |
| **Artifact** | A saved model, metadata file, metric file, or evidence file used by the running system. |
| **RBAC** | Role-Based Access Control: different users can perform different actions. |
| **Audit log** | An append-oriented record of important operations such as login, review, model approval, and export. |

## Who uses it?

| User | Main purpose | Typical access |
|---|---|---|
| **Admin** | Operate and govern the platform | All features, user roles, audit logs, retraining, champion approval, rollback, deletion processing, feature flags |
| **HR manager** | Review employee cases | Predictions, batch work, review queue, overrides, transparency profiles, appeals, consent, employee reports |
| **Analyst** | Study model behavior | Model Arena, comparisons, MCDA, sensitivity, fairness, robustness, drift, 3D views, LLM model health |
| **Viewer** | Read model information | Read-only models, predictions, explanations, comparison data, visualizations |
| **Reviewer** | Resolve uncertain cases | Review queue, review decisions, review analytics, predictions, explanations, comparison views |

The backend enforces these roles. An invalid or forged token does not create a synthetic user. The user must exist in the database and must be active.

## What the user sees in the web app

The React application contains these main areas:

| Route | Purpose |
|---|---|
| `/login` | Authenticate with an email and password. |
| `/` and `/arena` | Open the Multi-Model Arena. |
| `/predict` | Run a single employee prediction and view explanations. |
| `/batch` | Upload a CSV and run batch inference. |
| `/dashboard` | View dashboard information and current model data. |
| `/model-lab` | Trigger or inspect model-lifecycle operations available to the current role. |
| `/data-explorer` | Explore available data and model-related views. |
| `/methodology` | Read the method and governance explanation inside the product. |
| `/3d` | View PCA and decision-surface visualizations. |
| `/components` | Internal UI component demonstration page. |

The Model Arena contains specialized views for overview, head-to-head comparison, metric deep dive, cost and speed, priorities/MCDA, sensitivity, fairness and robustness, explainability, and an LLM verdict.

## Architecture overview

```text
React 19 + TypeScript + Vite
              |
              | Axios JSON / multipart requests
              v
FastAPI application: backend/app/main.py
              |
              +--> backend/app/api_v2.py
              |       V2 prediction, comparison, review, privacy,
              |       LLM, governance, drift, and PDF endpoints
              |
              +--> backend/core/security.py
              |       JWT authentication, password verification,
              |       role checks, token revocation
              |
              +--> SQLAlchemy database layer
              |       SQLite for local development or PostgreSQL in Compose
              |
              +--> ml/src/epk
                      model registry, preprocessing, training,
                      calibration, uncertainty, explainability,
                      statistics, MCDA, fairness, LLM controls
                              |
                              v
                       artifacts/v2/
                       verified model and evidence files
```

## Repository structure

```text
.
├── README.md                         # This project guide
├── backend/
│   ├── app/main.py                   # FastAPI app and legacy routes
│   ├── app/api_v2.py                 # Main V2 API router
│   ├── app/schemas.py                # Pydantic request/response contracts
│   ├── app/config.py                 # Environment-backed settings
│   ├── core/security.py              # Authentication, JWT, RBAC, revocation
│   ├── db/models.py                  # SQLAlchemy tables
│   ├── db/database.py                # SQLite/PostgreSQL engine and sessions
│   ├── db/migrate.py                 # Tables, seeded development accounts, models
│   ├── services/                     # Drift and PDF services
│   ├── tests/                        # Backend API and governance tests
│   ├── Dockerfile                    # Python 3.11 non-root container
│   └── pyproject.toml                # Backend package and dependency contract
├── frontend/
│   ├── src/App.tsx                   # Routes, shell, protected-route guard
│   ├── src/pages/                    # Main product pages
│   ├── src/pages/arena/               # Model Arena pages
│   ├── src/lib/api-client-v2.ts      # Frontend V2 API client and normalizers
│   ├── package.json                  # React/Vite/Three.js tooling
│   └── Dockerfile                    # Vite build served by Nginx
├── ml/
│   ├── src/epk/data.py               # Synthetic dataset generator
│   ├── src/epk/features.py           # Feature preprocessing
│   ├── src/epk/models/               # Seven-model registry and specifications
│   ├── src/epk/train_all.py          # Multi-model training
│   ├── src/epk/final_eval.py         # Locked final evaluation
│   ├── src/epk/calibration.py        # Probability calibration
│   ├── src/epk/uncertainty.py        # Conformal and stability logic
│   ├── src/epk/explain.py            # Explanations and counterfactuals
│   ├── src/epk/fairness.py           # Fairness calculations
│   ├── src/epk/llm/                  # Local LLM client, validator, cache, fallback
│   └── tests/                        # ML and invariant tests
├── artifacts/v2/                    # Verified model and comparison artifacts
├── data/                            # Generated benchmark data and splits
├── reports/                         # Evaluation reports and evidence
├── docs/                            # Architecture, ethics, runbook, ADRs, model cards
├── scripts/                         # Guards, audits, backups, evidence tools
├── verification/                    # Independent and adversarial verification
├── project/                         # Project status, run guide, and risk log
├── docker-compose.yml                # PostgreSQL + API + Nginx stack
├── Makefile                          # Common setup, run, train, test, and guard commands
└── pytest.ini                        # Test paths and import configuration
```

## Technology stack and why each part is used

| Layer | Technology | Why it is used |
|---|---|---|
| Frontend language | TypeScript | Catches contract and UI mistakes before runtime. |
| Frontend framework | React 19 | Component-based product UI with protected routes. |
| Frontend build | Vite | Fast local development and production bundling. |
| Styling/UI | Tailwind CSS, custom CSS, Lucide icons | Consistent responsive interface and accessible controls. |
| Charts | Recharts | Metric, comparison, and monitoring charts. |
| 3D visualization | Three.js, React Three Fiber, Drei | Decision surfaces, PCA views, and model-difference visualizations. |
| Frontend state | Zustand and local storage | Small client state needs such as theme and token persistence. |
| Frontend HTTP | Axios | JSON, multipart upload, and bearer-token requests. |
| Backend language | Python 3.11 | Stable ML and API runtime used by the project lockfiles. |
| API framework | FastAPI | Typed HTTP APIs, OpenAPI generation, dependency injection, and async support. |
| Validation | Pydantic v2 | Request and response validation for employee features and governance payloads. |
| Authentication | JWT, OAuth2 bearer flow, bcrypt | Password-based login, stateless access tokens, and secure password hashes. |
| Database access | SQLAlchemy | One data model that can run with SQLite locally and PostgreSQL in Compose. |
| Database | SQLite or PostgreSQL 16 | SQLite keeps development simple; PostgreSQL is the Compose deployment target. |
| Machine learning | scikit-learn 1.2.2 | Seven comparable model families and common evaluation tools. |
| Data processing | pandas and NumPy | Tabular cleaning, feature preparation, metrics, and generated data. |
| Statistical analysis | SciPy and project statistical modules | Bootstrap intervals, McNemar tests, drift, and ranking analysis. |
| PDF reports | ReportLab | Employee transparency and executive comparison documents. |
| Local LLM | Ollama or local OpenAI-compatible server | Optional narrative explanation without sending employee-level data to a cloud API. |
| Containers | Docker Compose, Python slim, Nginx | Repeatable API/database/frontend deployment with non-root backend execution. |
| Package tooling | `uv`, npm | Fast Python dependency management and standard Node dependency management. |

## The data

### Is the data real?

No. The benchmark data in this repository is **synthetic**. It is generated by `ml/src/epk/data.py` with a fixed seed and three data-generating variants:

| Variant | What it represents | Why it exists |
|---|---|---|
| `linear` | Mostly additive relationships between features and performance. | Shows when simpler linear models are enough. |
| `nonlinear` | Saturating training effects, feature interactions, attendance effects, a weekly-hours curve, department offsets, and noise. | Default benchmark regime where flexible models can help. |
| `noisy_overlap` | Nonlinear data with more noise and adjacent-band label overlap. | Tests whether conclusions survive a harder, less separable problem. |

The generator creates about 12,000 raw rows, adds a realism layer, removes duplicates and impossible values, and requires at least 10,000 cleaned rows. The current cleaned benchmark contains **11,904 rows**.

Synthetic data makes the project reproducible and safe to share. It does **not** prove that the model is ready for a real employer's workforce. Real deployment would require consented, legally reviewed, anonymized data and an independent validation study.

### Model input features

The prediction contract uses job-related operational features. The API schema is defined in `backend/app/schemas.py`; the full data dictionary is in [`docs/data_dictionary.md`](docs/data_dictionary.md).

| Feature | Meaning |
|---|---|
| `attendance` | Attendance percentage for the evaluation period. |
| `experience_years` | Professional experience in years. |
| `training_hours` | Training hours completed. |
| `projects_completed` | Completed projects in the measured period. |
| `weekly_hours` | Average hours worked per week. |
| `prev_score` | Previous review score, on a 1–5 scale; nullable in the API. |
| `department` | Department category such as Engineering, Sales, HR, Finance, or Operations. |
| `job_level` | Seniority category such as Junior, Mid, Senior, or Lead. |
| `peer_feedback` | Peer feedback score; the API supplies a default when omitted. |
| `tasks_on_time_pct` | Percentage of tasks completed on time; the API supplies a default when omitted. |
| `certifications` | Number of relevant certifications; the API supplies a default when omitted. |

### What is never a model feature?

The following are targets, identifiers, or audit-only attributes and must not be used as model inputs:

- `employee_id`
- `performance_score`
- `performance`
- `gender`
- `age_band`
- Other protected attributes stored in the protected-attribute table

The performance target has two forms:

- `performance_score`: a continuous score used by the regression track.
- `performance`: an ordered class label, `Low`, `Medium`, or `High`.

Protected attributes are stored separately for fairness auditing. They are not sent into the prediction feature set.

## The seven machine-learning models

Every registered model uses the same basic task: predict the ordered band `Low`, `Medium`, or `High`. The registry is in `ml/src/epk/models/registry.py`. A new model is added by registering another model specification under `ml/src/epk/models/specs/`.

| Key | Model | What it is good for | Explanation level |
|---|---|---|---|
| `linreg` | Linear regression wrapped by `ScoreToBand` | Continuous score prediction and simple linear relationships. | Coefficients and regression metrics. |
| `logreg` | Multinomial logistic regression | Fast, regularized, relatively interpretable classification. | Coefficients and class probabilities. |
| `knn` | K-nearest neighbors | Similar-case reasoning and local neighborhoods. | Neighbor-based explanation. |
| `svm` | RBF support vector machine | Strong nonlinear classification accuracy. | Post-hoc explanation. |
| `dt` | Decision tree | Human-readable rule paths and simple branching logic. | Native tree rules. |
| `rf` | Random forest | Ensemble accuracy and stable nonlinear predictions. | Partial/native plus post-hoc explanation. |
| `boost` | Histogram gradient boosting | Flexible nonlinear prediction with a strong balanced trade-off. | Partial/native plus post-hoc explanation. |

The comparison is intentionally multi-model. The project does not assume that one algorithm is best for every data-generating process.

## How training and evaluation work

The machine-learning pipeline is designed to prevent optimistic or leaked results:

```text
Generate and clean data
        |
        v
Freeze the data generator and row split
        |
        v
Fit preprocessing only on training rows
        |
        v
Train all seven model families with comparable budgets
        |
        v
Calibrate probabilities on calibration data
        |
        v
Create conformal prediction sets on a separate calibration partition
        |
        v
Evaluate once on the locked test partition
        |
        v
Generate metrics, confidence intervals, evidence, model cards,
comparison artifacts, and the champion recommendation
```

The current frozen split is **60% train, 10% calibration A, 10% calibration B, and 20% test**. The split indices are disjoint and stored in `data/processed/split.json`.

### Metrics used

The project reports more than accuracy:

- Accuracy and balanced accuracy.
- Macro-F1, so minority bands are not hidden by the majority class.
- Quadratic weighted kappa, because the bands are ordered.
- MCC and ROC-AUC where applicable.
- Log-loss and Brier score.
- Expected Calibration Error (ECE).
- Extreme error rate, such as confusing Low with High.
- Single-row and batch latency.
- Training time and artifact size.
- Fairness, robustness, stability, and explainability dimensions for MCDA.

### Current benchmark snapshot

The following values come from the current `nonlinear` benchmark and the frozen holdout report in [`reports/v2_final.md`](reports/v2_final.md). They describe this synthetic benchmark, not guaranteed real-world performance.

| Rank by Macro-F1 | Model | Macro-F1 | Accuracy | QWK | ECE | Single-row p95 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | SVM (`svm`) | 0.8164 | 0.8148 | 0.8216 | 0.0025 | 11.31 ms |
| 2 | Gradient Boosting (`boost`) | 0.8056 | 0.8026 | 0.8107 | 0.0126 | 100.82 ms |
| 3 | Random Forest (`rf`) | 0.7787 | 0.7757 | 0.7819 | 0.0157 | 60.17 ms |
| 4 | KNN (`knn`) | 0.7190 | 0.7278 | 0.7017 | 0.0239 | 12.90 ms |
| 5 | Logistic Regression (`logreg`) | 0.7150 | 0.7127 | 0.7083 | 0.0273 | 9.73 ms |
| 6 | Decision Tree (`dt`) | 0.7111 | 0.7102 | 0.7015 | 0.0399 | 10.68 ms |
| 7 | Linear Regression (`linreg`) | 0.7011 | 0.6997 | 0.6920 | 0.0350 | 10.75 ms |

### Why is `boost` the champion when SVM has the highest Macro-F1?

This is one of the main lessons of the project.

The current Balanced MCDA profile selects `boost` with a composite score of **0.6665**. SVM is the runner-up at **0.6575**. The decision strength is **`none`**, meaning the difference is too close to describe as a strong or certain victory.

The Balanced profile combines several concerns instead of only raw accuracy:

- Predictive quality.
- Calibration quality.
- Robustness and fairness.
- Stability.
- Inference speed and training cost.
- Explainability.

Under an Accuracy-first profile, SVM can win. This is expected. The right model depends on the organization's priorities. The platform exposes that trade-off instead of hiding it behind one leaderboard number.

## Explanations and uncertainty

### Explainability

The `/api/v2/explain` endpoint can return:

- Model-native information where the model supports it.
- Local feature attribution.
- Actionable constrained counterfactuals, such as which measurable feature changes could move a result toward another band.
- Similar cases from the training context.
- Persona summaries for HR and data-science audiences.

Similar cases are not always the model's actual reasoning. For non-KNN models, the UI labels that distinction so a reviewer does not mistake a helpful comparison view for a causal explanation of a black-box model.

### Uncertainty

The system uses several signals:

- Maximum class probability.
- Stability score.
- Set-valued conformal prediction.
- Agreement across the seven models.
- Champion versus shadow-model disagreement.

An example of an honest output is:

```text
Top prediction: Medium
Possible prediction set: Medium, High
Stability: below the review threshold
Action: send to human HR review
```

This is better than presenting a borderline case as if the model were certain.

## Model Arena and comparison science

The Model Arena is the analytical part of the product. It is used by analysts, engineers, reviewers, and administrators to understand model trade-offs.

It includes:

- Overall leaderboard and champion information.
- Head-to-head pairwise comparisons.
- Confusion matrices and metric curves.
- Accuracy, calibration, cost, and latency views.
- MCDA priority tuning.
- Sensitivity across data-generating variants.
- Fairness and robustness reports.
- Explainability comparisons.
- Local LLM evidence-based verdicts.

The statistical comparison layer uses paired evaluation on the same test rows, bootstrap confidence intervals, and pairwise tests with multiple-comparison correction. The purpose is to avoid claiming a meaningful winner when two models are effectively tied.

## Fairness, privacy, and ethics

### Protected-attribute isolation

Protected fields are kept in a separate storage path and excluded from prediction features. This is an engineering control, not a guarantee that all proxy bias has disappeared.

The platform can still inspect fairness-related outcomes using audit-only attributes, including:

- Disparate-impact ratios.
- Demographic-parity differences.
- Four-fifths rule checks.
- Proxy-variable and robustness analysis.

### Human review and appeals

The system supports:

- A review queue for uncertain predictions.
- Mandatory override reasons when a reviewer changes the model band.
- Employee transparency profiles.
- Employee appeals with supporting information.
- Consent records.
- Administrative deletion requests.

### Data deletion

The privacy deletion flow retains the deletion and audit evidence while removing operational records such as predictions, review items, review decisions, consent records, appeals, protected attributes, and the employee record for the requested employee identifier.

### Important legal and operational boundary

This repository implements technical controls for responsible decision support. It is not legal advice and does not by itself make the system compliant with employment, privacy, or AI regulations in any country. A real organization still needs legal review, HR policy review, employee communication, access controls, retention rules, and an appeal process.

## Local LLM verdict engine

The optional LLM feature is deliberately constrained.

### The design rule: code decides, the LLM narrates

1. Python code computes the model comparison and deterministic winner.
2. The backend builds an evidence packet containing aggregate, precomputed facts.
3. The local LLM receives that packet and writes a human-readable explanation.
4. A validator checks the output structure, citations, numbers, recommendation, confidence, and caveats.
5. Invalid output is rejected, retried when configured, or replaced by a deterministic template fallback.

The LLM is not allowed to choose the champion by inventing a new calculation.

### Supported local runtimes

- Ollama at `http://localhost:11434`.
- Local OpenAI-compatible servers such as LM Studio, llama.cpp, vLLM, or LocalAI.
- The default SSRF guard accepts loopback names and `host.docker.internal` for the Docker host bridge. Public hosts are rejected unless a separate explicit remote policy is enabled in code.

### What happens when the LLM is offline?

The application still works. `/api/v2/llm/verdict` can return a verified deterministic template fallback when `allow_fallback` is enabled. This keeps local development, CI, and CPU-only machines usable without a GPU or LLM server.

See [`docs/LLM_SETUP.md`](docs/LLM_SETUP.md) for runtime configuration and troubleshooting.

## Backend API reference

The generated OpenAPI schema is available in [`openapi.json`](openapi.json). When the API is running, open:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Public lifecycle endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Lightweight liveness response. |
| `GET` | `/ready` | Database, artifact, and model readiness status. |
| `GET` | `/version` | API and active model version information. |
| `POST` | `/login` | Obtain a bearer token using an OAuth2 password form. |

### Authentication endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/refresh` | Revoke the current token and issue a new token. |
| `POST` | `/logout` | Revoke the current token. |
| `POST` | `/api/v2/auth/refresh` | V2 token rotation. |
| `POST` | `/api/v2/auth/logout` | V2 token revocation. |

### V2 prediction and explanation endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v2/models` | List registered models, metadata, metrics, and artifact hashes. |
| `POST` | `/api/v2/predict` | Run one selected model, persist the result, and create review flags when needed. |
| `POST` | `/api/v2/predict/all` | Run all seven models and return consensus, agreement, and split-decision information. |
| `POST` | `/api/v2/explain` | Return model-specific explanation, attribution, counterfactuals, and similar cases. |
| `POST` | `/api/v2/batch` | Run CSV batch prediction using one model, the champion, or all models. |

The V2 batch endpoint limits uploads to CSV, rejects formula-like cells, limits the request to 5,000 data rows, and rejects files larger than 10 MB. The legacy `/batch` route also has request-size and row protections.

### V2 comparison and visualization endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v2/compare/{topic}` | Read verified comparison artifacts such as leaderboard, curves, confusion, pairwise, fairness, robustness, sensitivity, MCDA, evidence, and conformal data. |
| `POST` | `/api/v2/compare/mcda` | Recalculate MCDA using validated non-negative custom weights. |
| `GET` / `POST` | `/api/v2/viz/surface` | Read a precomputed model decision surface; grid size is capped at 80×80. |
| `GET` | `/api/v2/viz/pca` | Read PCA 2D/3D projection data and the background sample. |

### V2 LLM endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v2/llm/health` | Check whether the local runtime is reachable. |
| `GET` | `/api/v2/llm/models` | List models reported by the local runtime. |
| `PUT` | `/api/v2/llm/config` | Change provider, model, or local base URL as an admin. |
| `POST` | `/api/v2/llm/verdict` | Generate, validate, cache, or template-fallback an evidence-based verdict. |
| `GET` | `/api/v2/llm/verdicts/{verdict_id}` | Retrieve a stored verdict for its owner or an admin. |

### V2 review, privacy, and employee transparency endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v2/review/queue` | List pending or filtered uncertainty-first review items. |
| `POST` | `/api/v2/review/{review_id}/decision` | Submit a human decision; an override reason is required when changing the band. |
| `GET` | `/api/v2/review/analytics` | Show pending, reviewed, override, and agreement counts. |
| `GET` | `/api/v2/transparency/employee/{employee_id}` | Read an employee transparency profile. |
| `POST` | `/api/v2/transparency/appeal` | Register an employee decision appeal. |
| `POST` | `/api/v2/privacy/consent` | Record or withdraw consent. |
| `POST` | `/api/v2/privacy/delete-request` | Process an admin deletion request. |

### V2 governance, operations, and reports

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v2/audit/logs` | Admin-only append-oriented audit log query. |
| `PUT` | `/api/v2/users/{user_id}/role` | Admin-only role change with an audit record. |
| `POST` | `/api/v2/retrain` | Prepare a governed candidate retrain result. |
| `POST` | `/api/v2/models/approve-champion` | Approve a candidate model version. |
| `POST` | `/api/v2/models/rollback` | Roll back the active champion to the governed baseline. |
| `GET` | `/api/v2/models/versions` | List model versions and approval state. |
| `GET` | `/api/v2/drift/status` | Assess feature drift using PSI and KS-related reporting. |
| `GET` / `POST` | `/api/v2/admin/feature-flags` | Read or update feature flags; updates require admin access. |
| `GET` | `/api/v2/reports/employee/{employee_id}/pdf` | Download an employee transparency PDF. |
| `GET` | `/api/v2/reports/comparison/pdf` | Download the executive multi-model comparison PDF. |

### Legacy compatibility endpoints

The original API remains in `backend/app/main.py` for compatibility with older clients and tests. It includes `/predict`, `/explain`, `/batch`, `/analytics/drift`, `/batch/report/pdf`, and visualization stubs. New development should use the `/api/v2/*` endpoints because V2 contains the multi-model and governance contracts.

## Database and persistence

The data layer supports SQLite for local work and PostgreSQL for the Docker Compose stack.

The governed database model contains these main entities:

1. `users`
2. `employees`
3. `protected_attributes`
4. `snapshots`
5. `predictions`
6. `prediction_history` for legacy compatibility
7. `review_items`
8. `review_decisions`
9. `batch_jobs`
10. `model_versions`
11. `comparison_runs`
12. `llm_verdicts`
13. `drift_reports`
14. `fairness_reports`
15. `api_keys`
16. `audit_logs`
17. `consent_records`
18. `deletion_requests`
19. `appeals`

SQLite foreign-key enforcement is enabled. PostgreSQL is the intended Compose database for a multi-container deployment.

## Model artifacts and integrity

The V2 artifact bundle is under `artifacts/v2/`:

```text
artifacts/v2/
├── MANIFEST.json                         # SHA-256 and size metadata
├── champion.json                         # Active governed champion metadata
├── dataset_meta.json                     # Dataset contract metadata
├── models/<model_key>/model.joblib       # Saved model for each of 7 keys
├── models/<model_key>/metadata.json      # Per-model metrics and library data
├── comparison/leaderboard.json           # Model metrics and latency
├── comparison/mcda.json                  # Profiles and rankings
├── comparison/pairwise.json              # Pairwise model results
├── comparison/confusion.json             # Confusion data
├── comparison/fairness.json              # Fairness artifacts
├── comparison/robustness.json            # Robustness artifacts
├── comparison/importance.json            # Importance data
├── comparison/curves.json                # Metric curves
├── comparison/sensitivity.json           # Variant sensitivity
├── comparison/conformal.json             # Conformal results
├── comparison/evidence_packet.json       # Aggregate evidence for the LLM
└── explainability/                       # Surfaces and PCA data
```

`ml/src/epk/artifacts.py` provides the `ArtifactLoader`. It:

- Whitelists model keys.
- Refuses path traversal strings.
- Verifies the SHA-256 manifest before loading registered files.
- Lazily loads models and JSON files.
- Refuses tampered model artifacts.

When a champion file is updated by the governed API, its manifest hash is updated at the same time and the in-memory loader cache is invalidated.

## Security controls

The project includes multiple layers of security rather than relying on one login screen:

- Bcrypt password hashes, not plaintext passwords.
- JWT bearer tokens with expiration.
- Token refresh rotation and in-memory revocation.
- Database-backed active-user lookup for every authenticated request.
- Role-based endpoint authorization.
- Default-deny OpenAPI route checks, with only health, readiness, version, and login public.
- Request-size limits and CSV row limits.
- CSV formula-injection rejection while allowing legitimate negative numbers.
- Security headers including `X-Content-Type-Options`, `X-Frame-Options`, HSTS, and `Referrer-Policy`.
- Model key whitelist and path traversal refusal.
- SHA-256 artifact integrity verification.
- Local-host restriction for LLM requests.
- Prompt scanning for employee-level identifiers.
- LLM fact, number, citation, and confidence validation.
- Audit records for important governance actions.
- Non-root backend container user.

## Invariant guard suite

Run `python scripts/guard.py` or `make guard` to check the project's G1–G14 invariants:

| Guard | What it protects |
|---|---|
| G1 | Frozen generator hash. |
| G2 | Target and protected-attribute isolation. |
| G3 | Ordered class labels `[0, 1, 2]` across all models. |
| G4 | Leakage-safe preprocessing across model specifications. |
| G5 | Frozen, disjoint train/calibration/test split. |
| G6 | Test-set lock and one-time evaluation rule. |
| G7 | Calibration-set isolation from tuning. |
| G8 | Evidence packet safety and absence of employee data. |
| G9 | LLM validator and prompt hygiene. |
| G10 | Local-only LLM SSRF protection. |
| G11 | Model whitelist and traversal refusal. |
| G12 | RBAC matrix and default-deny route enforcement. |
| G13 | No detected secrets or bypass flags. |
| G14 | Ratchet against new skips, suppressions, `any`, and console logging. |

## Current project scope

### In scope

- Employee performance classification as decision support.
- Seven-model comparison under a common evaluation protocol.
- Model explanations and uncertainty indicators.
- Batch prediction for up to 5,000 CSV data rows on the V2 route.
- HR review queue and documented human overrides.
- Model Arena analytics and visualizations.
- Fairness, robustness, and drift monitoring artifacts.
- Local, validated LLM narrative synthesis.
- Model version governance, champion approval, and rollback.
- Consent, appeals, deletion, audit logs, and PDF reports.

### Out of scope

- Fully automatic employment decisions.
- Real payroll, HRIS, recruiting, or identity-provider integration.
- Legal certification for a particular country.
- A guarantee that synthetic-data fairness results transfer to a real workforce.
- Cloud-hosted LLM calls by default.
- Replacing HR policy or professional judgement.

### Future production work

Before using the system with real employees, an organization would still need to:

1. Obtain and document lawful, consented, minimal data.
2. Validate labels and features with HR domain experts.
3. Run an independent external validation set.
4. Perform legal, privacy, security, and labor-policy review.
5. Add enterprise identity integration and secret management.
6. Run remote Linux CI and production container verification.
7. Define retention, deletion, appeal, and incident-response procedures.
8. Pilot the tool with human supervision and measure real-world outcomes.

## Quick start for a new developer

This section is for someone who knows nothing about the repository.

### Prerequisites

Minimum practical setup:

- Git.
- Python 3.11.
- Node.js 20 or newer. Node 24 is the project guide recommendation.
- npm.
- `uv` for Python environments and lockfiles.
- Docker Desktop only if you want the PostgreSQL + API + Nginx stack.
- Ollama is optional. The application has a deterministic LLM fallback.

### Option A: local development with SQLite (recommended for review)

From the repository root:

```bash
# Create the local .env, select an installed Ollama model, verify V2 artifacts,
# and seed the SQLite development database.
uv run python scripts/demo_setup.py
```

The setup script keeps `DATABASE_URL` on SQLite and creates a local-only JWT
secret. It does not download models. If Ollama is running, it selects the best
installed text model for this project; if Ollama is offline, the deterministic
template fallback remains available.

If you prefer manual configuration, keep `DATABASE_URL` as SQLite:

```env
DATABASE_URL=sqlite:///./hr_insights.db
ENVIRONMENT=development
JWT_SECRET_KEY=replace-with-a-unique-local-32-character-secret
```

Start the backend in one terminal:

```bash
make api
```

The API should be available at `http://localhost:8000`.

Start the frontend in a second terminal:

```bash
make web
```

The web app should be available at `http://localhost:5173`.

After both processes are running, verify the review flow from a third terminal:

```bash
uv run python scripts/demo_smoke.py
```

Open `http://localhost:5173/login`.

### Option B: run without `make`

If `make` is not installed on Windows, run the underlying commands directly:

```bash
# Backend
uv run uvicorn backend.app.main:app --reload --reload-dir backend --reload-dir ml/src --port 8000

# Frontend, in another terminal
cd frontend
npm install
npm run dev
```

### Development accounts

`backend/db/migrate.py` seeds these accounts when they do not already exist:

| Role | Email | Development password | Use it to learn |
|---|---|---|---|
| Admin | `admin@test.com` | `AdminPassword123!` | All screens, governance, audit, rollback, and privacy administration. |
| HR manager | `hrmanager@test.com` | `HRManagerPassword123!` | Prediction, review, transparency, appeal, and employee-report flows. |
| Analyst | `analyst@test.com` | `AnalystPassword123!` | Model Arena, metrics, fairness, robustness, drift, and LLM health. |
| Viewer | `viewer@test.com` | `ViewerPassword123!` | Read-only prediction, explanation, comparison, and visualization flows. |
| Reviewer | `reviewer@test.com` | `ReviewerPassword123!` | Uncertainty queue, review decisions, and review analytics. |

These passwords are for local development only. Change or remove seeded accounts before any shared or production deployment.

### First product walkthrough

1. Sign in as `admin@test.com`.
2. Open **Model Arena** to see the seven registered models and the current champion.
3. Open **Predict** and enter the employee feature values.
4. Run a prediction and inspect the predicted band, probabilities, stability, and review flag.
5. Open the explanation panel to see attribution, counterfactuals, and similar cases.
6. Open **Batch** and upload a CSV with the columns shown below.
7. Open **Fairness**, **Robustness**, **Sensitivity**, and **Cost/Speed** inside the Arena to understand the model trade-offs.
8. Sign in as a reviewer to inspect the uncertainty queue and submit a review decision.
9. Sign in as an admin to inspect audit logs, model versions, champion lifecycle, and PDF reports.

## CSV batch format

The V2 batch endpoint expects a CSV containing the model feature columns. A minimal valid example is:

```csv
attendance,experience_years,training_hours,projects_completed,weekly_hours,prev_score,department,job_level,peer_feedback,tasks_on_time_pct,certifications
90,5,100,5,40,3.0,Sales,Junior,3.8,85,2
78,2,35,2,42,2.5,Support,Mid,3.1,68,1
```

Use the complete feature set when possible. The API validates ranges and rejects extra fields in individual prediction requests. Negative numeric values are allowed where the feature contract allows them; formula-like cells beginning with `=`, `+`, or `@` are rejected.

## Environment configuration

Copy `.env.example` to `.env` and never commit real secrets.

| Variable | Purpose | Local example |
|---|---|---|
| `ENVIRONMENT` | Runtime mode. Production and staging require a real 32+ character JWT secret. | `development` |
| `DATABASE_URL` | SQLAlchemy database URL. | `sqlite:///./hr_insights.db` |
| `POSTGRES_USER` | Compose PostgreSQL username. | `talentscope` |
| `POSTGRES_PASSWORD` | Required Compose PostgreSQL password. | Set privately; do not commit. |
| `POSTGRES_DB` | Compose database name. | `talentscope` |
| `JWT_SECRET_KEY` | Signs access tokens. Must be unique and at least 32 characters in production/staging. | Set privately. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime. | `60` |
| `CORS_ORIGINS` | Comma-separated allowed browser origins. | `http://localhost:5173,http://localhost:3000` |
| `LLM_ENABLED` | Enables live local LLM calls; fallback remains available when disabled. | `true` |
| `LLM_PROVIDER` | `ollama` or local OpenAI-compatible provider. | `ollama` |
| `LLM_BASE_URL` | Local LLM base URL. Do not include a trailing `/v1` for the client. | `http://localhost:11434` |
| `OLLAMA_BASE_URL` | Compose/local Ollama address used by the runtime. | `http://localhost:11434` |
| `DOCKER_OLLAMA_BASE_URL` | Ollama address from inside the Docker backend container. | `http://host.docker.internal:11434` |
| `LLM_MODEL` | Local model name. | `llama3.1:latest` |
| `LLM_TEMPERATURE` | Deterministic generation temperature. | `0.0` |
| `LLM_SEED` | Reproducibility seed. | `42` |
| `LLM_NUM_CTX` | Ollama context window. | `8192` |
| `LLM_TIMEOUT_S` | Local LLM request timeout. | `120.0` |
| `LLM_MAX_RETRIES` | Validator retry count before fallback. | `2` |
| `LLM_ALLOW_REMOTE` | Must remain `false` for local-only demos. | `false` |

Production and staging fail fast when `JWT_SECRET_KEY` is missing, too short, or one of the known insecure development placeholders.

## Optional Ollama setup

If you want live local LLM verdicts instead of deterministic fallback text:

```bash
ollama serve
ollama list
```

For the current review machine, `llama3.1:latest` produced the best structured-
evidence result in the six-packet benchmark: 83.3% first-attempt validity,
83.3% post-retry validity, 16.7% template fallback, and 30.4 seconds mean
latency. `qwen2.5:3b` is the faster low-memory alternative; `qwen2.5:7b`
was slower and had a higher fallback rate in the same run. The benchmark is
local and hardware-dependent, so the setup script selects from installed
models rather than downloading one.

Then set the local model in `.env`, for example:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=llama3.1:latest
```

The core prediction and comparison flows do not require Ollama. If the local runtime is offline or returns invalid evidence, the backend can use the template fallback.

## Docker Compose deployment

The Compose stack contains:

- `talentscope-db`: PostgreSQL 16.
- `talentscope-api`: FastAPI backend on port `8000`.
- `talentscope-web`: Nginx-served frontend on port `80`.

Before starting it, set the required secrets in the shell or in a private `.env` file:

```env
POSTGRES_USER=talentscope
POSTGRES_PASSWORD=use-a-private-database-password
POSTGRES_DB=talentscope
JWT_SECRET_KEY=use-a-unique-production-secret-at-least-32-characters
```

Then run:

```bash
docker compose up -d --build
```

Verify the API:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Open the web application at `http://localhost`.

The Compose file deliberately refuses to start when `POSTGRES_PASSWORD` or `JWT_SECRET_KEY` is missing. This is safer than silently using a shared default secret.

## Training and evaluation commands

The repository includes commands for the complete ML workflow:

```bash
# Generate linear, nonlinear, and noisy-overlap data variants
make data

# Train the registered models using the selected profile
make train PROFILE=fast

# Run the locked final evaluation on the default nonlinear variant
make final VARIANT=nonlinear

# Run sensitivity across data-generating variants
make final-variants

# Rebuild the evidence and comparison artifacts when the pipeline requires it
make evidence PHASE=final
```

The exact training outputs depend on the checked-in data, artifacts, Python version, and configuration. Do not compare a model number from a different generator variant as if it came from the same experiment.

## Verification and quality commands

### Main checks

```bash
# Invariant guards G1-G14
make guard

# Backend and ML tests
python -m pytest -q ml/tests backend/tests

# Frontend tests
cd frontend
npm run test -- --run

# TypeScript build
npm run build

# Frontend lint
npm run lint
```

### Direct checks used during development

```bash
uv run ruff check .
uv run black --check .
uv run python -m compileall -q backend ml/src scripts verification
uv pip check
python verification/run_adversarial_tests.py
docker compose config
```

### Current verification snapshot

The current workspace has an explicit ML/backend test run of **176 passing tests** using:

```bash
python -m pytest -q ml/tests backend/tests
```

The frontend test suite currently reports **25 passing tests**. The build passes. The frontend lint command passes with React effect warnings that are reported by the linter but do not fail the command. A root-level pytest invocation can be sensitive to the one-minute rate-limit window because one legacy explanation test sends 21 deliberately expensive requests; use the explicit test paths above for the normal project check.

## Troubleshooting

### The frontend shows “Sign in required”

The browser has no token in local storage. Open `/login`, sign in with a seeded development account, and reload the page.

### Login returns an authentication error

Run the migration/seed command again:

```bash
uv run python backend/db/migrate.py
```

Confirm that the account exists and is active in the configured database.

### The API says the model is unavailable

Check:

```bash
curl http://localhost:8000/ready
```

The readiness response reports database, artifact, model, and model-source status. The default startup path disables legacy V1 artifact loading and uses the governed V2 model artifacts.

### The LLM endpoint says the runtime is offline

That is allowed. Either start Ollama/local runtime or keep `allow_fallback=true` so the deterministic template path can respond. Check `/api/v2/llm/health` as an admin or analyst.

### Docker Compose refuses to interpolate variables

Set both required values before running Compose:

```bash
export POSTGRES_PASSWORD='private-password'
export JWT_SECRET_KEY='private-32-character-or-longer-secret'
docker compose config
```

On Windows PowerShell:

```powershell
$env:POSTGRES_PASSWORD = "private-password"
$env:JWT_SECRET_KEY = "private-32-character-or-longer-secret"
docker compose config
```

### `uv` cannot install a package

Use Python 3.11 and the project lockfiles. A clean project environment is preferred over the host Python installation:

```bash
uv venv .venv --python 3.11
uv pip install -r backend/requirements.txt -e ml
```

The project has previously observed unrelated host-global dependency conflicts. Those do not represent the isolated project environment.

### The batch upload is rejected

Check that:

- The filename ends in `.csv`.
- The CSV is UTF-8.
- The file is no larger than 10 MB for `/api/v2/batch`.
- There are no more than 5,000 data rows.
- No cell begins with `=`, `+`, or `@`.
- The feature names and value ranges match the schema.

## Documentation map

Start with this README, then use the specialist documents below:

| Document | What it explains |
|---|---|
| [`docs/user_guide.md`](docs/user_guide.md) | Product usage flow for HR users. |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | Feature meanings, targets, and audit-only attributes. |
| [`docs/01-ethics.md`](docs/01-ethics.md) | Intended use, prohibited use, and human-review policy. |
| [`docs/MULTIMODEL_PACK.md`](docs/MULTIMODEL_PACK.md) | Detailed multi-model design decisions and statistical protocol. |
| [`docs/model_card.md`](docs/model_card.md) | Model-card summary and limitations. |
| [`docs/model_cards/`](docs/model_cards/) | Per-model cards for all seven models. |
| [`docs/LLM_SETUP.md`](docs/LLM_SETUP.md) | Local LLM runtimes, sizing, security, and fallback behavior. |
| [`docs/runbook.md`](docs/runbook.md) | Operational and deployment runbook. |
| [`docs/viva_qa.md`](docs/viva_qa.md) | Technical viva questions and explanations. |
| [`docs/STATE.md`](docs/STATE.md) | Project phase history and current engineering state. |
| [`docs/FINAL_READINESS.md`](docs/FINAL_READINESS.md) | Release-readiness evidence and human sign-off items. |
| [`project/RUN.md`](project/RUN.md) | Short project run instructions. |
| [`project/RISKS.md`](project/RISKS.md) | Known project risks and mitigations. |
| [`verification/README.md`](verification/README.md) | Independent verification script index. |
| [`docs/adr/`](docs/adr/) | Architecture and governance decisions. |

## Glossary for a complete beginner

### Machine learning model

A mathematical program that learns patterns from example data and then estimates an output for new data.

### Classification

Predicting a category. Here the categories are `Low`, `Medium`, and `High`.

### Regression

Predicting a continuous number. Here `linreg` predicts a continuous performance score and then converts it into an ordered band.

### Training data

Examples used to fit model parameters.

### Calibration data

Separate examples used to adjust probabilities and create uncertainty thresholds without touching the final test result.

### Test data

Held-out examples used for the final benchmark. TalentScope locks this partition to reduce accidental re-evaluation or tuning against the test set.

### Data leakage

When information from the target or evaluation data accidentally enters training. Leakage makes a model look better in testing than it will be in reality.

### Fairness

Checking whether results differ in concerning ways across groups. Removing protected columns helps, but it does not automatically remove proxy bias.

### Drift

When new production-like data no longer looks like the reference data. Drift can mean the organization changed, the process changed, or the data pipeline broke.

### Model governance

The controls around a model's lifecycle: versioning, metrics, approval, promotion, monitoring, rollback, and audit records.

### Evidence packet

A machine-generated set of aggregate facts used to support an LLM narrative. It is designed to contain no employee-level records.

## Short explanation for a viva or presentation

> TalentScope is a human-supervised employee performance decision-support platform. It addresses the gap between a raw ML prediction and a responsible HR workflow by comparing seven models under a fair evaluation protocol, calibrating and explaining predictions, surfacing uncertainty and disagreement, routing risky cases to human review, isolating protected attributes, and recording model governance, appeals, deletion, and audit evidence. The current benchmark uses reproducible synthetic data, so the system is a research and production-shaped prototype rather than proof that an employer can deploy it without further legal, privacy, and real-world validation.

## License and project status

The current workspace does not contain a checked-in `LICENSE` file, so do not assume the MIT badge from earlier project materials is a legal license grant. Add and review an explicit license before redistributing the software.

The codebase is a **release-candidate research prototype** with a substantial API, UI, ML, governance, and verification surface. The final readiness documents still call for human sign-off, remote CI verification, and real-world validation before production use.
