# Changelog

All notable changes to **TalentScope Multi-Model Edition** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-rc] - 2026-10-12

### Added
- **Multi-Model Arena (7 Models)**:
  - Seven benchmark models: Linear Regression (`linreg` via `ScoreToBand`), Logistic Regression (`logreg`), K-Nearest Neighbors (`knn`), Support Vector Machine (`svm`), Decision Tree (`dt`), Random Forest (`rf`), and Histogram Gradient Boosting (`boost`).
  - Model registry and model specifications (`ml/src/epk/models/`).
  - Held-out probability calibration (Platt scaling / sigmoid on Cal-A) producing reliable posterior probabilities and Brier/ECE scores.
  - Split-conformal prediction on Cal-B guaranteeing exact $\ge 90\%$ coverage at $\alpha = 0.1$.
- **Statistical Science & Evidence Packet**:
  - Paired stratified bootstrap (2,000 resamples) computing 95% confidence intervals for Macro-F1, Accuracy, and QWK.
  - Pairwise McNemar tests with Holm step-down correction across all 21 model pairs.
  - 5-profile Multi-Criteria Decision Analysis (MCDA) with Dirichlet rank probability distributions and deterministic champion selection (`docs/adr/009-champion-selection-rule.md`).
  - Data sensitivity evaluation across linear, nonlinear, and noisy-overlap variants.
  - Machine-built evidence packet with 100 numbered facts, caveat `F90`, and verification scanners.
- **Local LLM Verdict Engine**:
  - Privacy-preserving local LLM interface (`Ollama` / OpenAI-compatible) with zero cloud exfiltration guarantee.
  - Strict structured JSON schema validation, fact ID ground-truth matching, banned token checks, and template fallback.
- **Backend API v2 (`/api/v2/*`)**:
  - Clean coexistence with legacy `/api/v1` routes.
  - Model whitelisting, tamper-evident manifest verification with SHA-256 integrity checks.
  - RBAC security matrix (Admin, HR Manager, Analyst, Viewer) enforced across all endpoints.
  - Uncertainty-first human review queue (`/api/v2/review/*`) requiring mandatory justifications for overturned predictions.
  - Employee transparency and appeal endpoints (`/api/v2/transparency/*`).
  - Governed retrain-all pipeline (`/api/v2/retrain`) with automated champion proposal and cryptographic rollback (`/api/v2/models/rollback`).
  - Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) feature drift detection (`/api/v2/drift/status`).
  - Real-time shadow mode inference comparing runner-up model (`svm`) with champion (`boost`).
  - Server-side PDF report generation (ReportLab) with mandatory ethics notices.
- **Frontend Modern Web Application**:
  - React 19 + TypeScript + Vite + Tailwind CSS with Okabe-Ito accessible color palette.
  - Single employee prediction view with model selector, all-models agreement meter, split-decision alerts, and what-if advisor.
  - Fast batch inference view supporting 5,000 records across 7 models concurrently.
  - Interactive Model Arena with 9 deep-dive analytical views: Head-to-Head, Metrics Deep Dive, Speed/Cost trade-offs, Sensitivity, Fairness & Disparities, and interactive LLM Verdict panel.
  - 3D Decision Landscape with two-model probability surface overlay ($P_A - P_B$) and 2D heatmap fallback.
- **DevOps, Security, and Production Hardening**:
  - Multi-stage non-root containerization (`Dockerfile` for backend and frontend).
  - Production `docker-compose.yml` orchestrating PostgreSQL 16, FastAPI backend, and Nginx frontend.
  - Automated CI/CD workflows (`.github/workflows/ci.yml` and `release.yml`).
  - Health (`/health`) and readiness (`/ready`) probes with database and artifact checks.
  - Automated cryptographic backup script (`scripts/backup.py`).
  - Full operational runbook (`docs/runbook.md`) and viva presentation guide (`docs/viva_qa.md`).

### Fixed
- Re-enabled skipped legacy tests from v1 without suppressions (discharging Obligation O1).
- Resolved bcrypt passlib 72-byte string truncation bug by direct integration with `bcrypt` library.
- Eliminated all TypeScript `any` types and test `console.log` statements.
- Fixed artifact loader cache synchronization during dynamic champion switch and rollback.

---

## [1.0.0] - 2026-09-29

### Added
- Initial single-model prototype for talent band prediction using KNN.
- Basic FastAPI backend and initial web interface.
