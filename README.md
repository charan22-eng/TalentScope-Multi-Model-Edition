# TalentScope: Multi-Model Edition

[![CI Status](https://github.com/talentscope/talentscope/actions/workflows/ci.yml/badge.svg)](https://github.com/talentscope/talentscope/actions)
[![Guard Suite](https://img.shields.io/badge/guards-14%2F14%20passing-success)](scripts/guard.py)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

TalentScope Multi-Model Edition is an enterprise-grade machine learning platform for governed employee performance evaluation and comparative ML analytics. It evaluates seven diverse model architectures simultaneously in a fair, frozen benchmark arena, supported by split-conformal prediction sets, paired bootstrap confidence intervals, native explainability, 3D decision landscapes, and local-LLM narrative synthesis.

---

## 🚀 Quick Start (10 Minutes, Works with LLM Offline)

TalentScope is designed to work completely out-of-the-box even without a GPU or local LLM server running. If Ollama is offline, the deterministic template fallback automatically synthesizes verified fact-grounded verdicts.

### Prerequisites
- Python 3.11+
- Node.js 20+
- Git

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/talentscope/talentscope.git
cd talentscope

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Initialize Database & Seed Users
```bash
python backend/db/migrate.py
```
This initializes all 17 governed database tables in SQLite (`hr_insights.db`) and seeds standard development role accounts.

### 3. Verify Guard Suite
```bash
python scripts/guard.py
# All 14 cryptographic invariants (G1-G14) must pass
```

### 4. Run Development Servers
In terminal 1 (Backend API):
```bash
uvicorn backend.app.main:app --reload --port 8000
```

In terminal 2 (Frontend SPA):
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 👥 Default Development Roles & Credentials

| Role | Email | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@test.com` | `AdminPassword123!` | Full system access, retrain pipeline, champion approval, audit logs, rollback |
| **HR Manager** | `hrmanager@test.com` | `HRManagerPassword123!` | Predictions, review queue, override decisions, transparency profiles, appeals |
| **Analyst** | `analyst@test.com` | `AnalystPassword123!` | Arena comparisons, MCDA sensitivity, drift monitoring, 3D landscapes |
| **Viewer** | `viewer@test.com` | `ViewerPassword123!` | Read-only Arena leaderboard, metric curves, model cards |

---

## 🧠 Seven Model Architectures

Every employee evaluation is scored simultaneously by 7 distinct model paradigms:

1. **`linreg` (Linear Regression via ScoreToBand)**: High interpretability; dominates linear data regimes.
2. **`logreg` (Multinomial Logistic Regression)**: Calibrated log-odds with Ridge regularization.
3. **`knn` (K-Nearest Neighbors)**: Non-parametric instance-based voting in scaled feature space.
4. **`svm` (Support Vector Classifier)**: High raw accuracy with RBF kernel and Platt probability scaling.
5. **`dt` (Decision Tree)**: Single-tree transparent rule path with depth pruning.
6. **`rf` (Random Forest - Governed Champion)**: 100-tree ensemble balancing high F1, low ECE, and stability.
7. **`boost` (Histogram Gradient Boosting)**: Fast iterative residual boosting; close runner-up.

---

## 🏟️ Architecture & Features

```
talentscope/
├── artifacts/v2/          # Cryptographically cataloged model joblibs, metrics, and manifest
├── backend/app/           # FastAPI application (v1 legacy & v2 unified multi-model API)
├── backend/db/            # SQLAlchemy unified models (17 tables) & SQLite/Postgres migration
├── frontend/src/pages/    # React 19 + TypeScript SPA
│   ├── arena/             # Multi-Model Arena (8 specialized analytical tabs)
│   ├── ThreePage.tsx      # 3D Decision Landscape, Difference Surface & PCA Galaxy
│   └── Predict.tsx        # Real-time 7-model consensus, agreement meter & explainability
├── ml/src/epk/            # Core ML: features, registry, stats, mcda, explain, llm
├── reports/               # Machine-generated benchmark evaluations & PDF report engines
└── scripts/guard.py       # Invariant Guard Suite (14 cryptographically verified gates)
```

- **Uncertainty-First Review Queue**: Automated predictions with low stability (<70) or split decisions are routed for mandatory human HR review with required override justifications.
- **Fairness & Drift Monitoring**: Real-time Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests tracking input distribution shift; demographic parity checks enforcing 4/5ths disparate impact rule.
- **3D Decision Surfaces**: Interactive Three.js/R3F visualizers displaying 2D/3D decision boundaries, KNN neighborhoods, and pairwise model difference surfaces ($P_A - P_B$).
- **PDF Report Generator**: ReportLab-powered automated generation of Employee Decision Transparency reports and Executive Multi-Model Arena summaries.

---

## 📜 Ethical Compliance & Governance Charter
TalentScope operates under strict automated decision-support constraints:
- **Decision Support Only**: No adverse employment action may be taken solely on model scores. Final decisions rest with human HR leadership.
- **Protected Attribute Isolation**: Demographics (gender, age, ethnicity) are strictly excluded from model inference features (cryptographically enforced by Guard G2).
- **Statutory Transparency**: Employees possess full access to their model scores, attribution factors, and the right to lodge human appeals.

---

## 🐳 Production Deployment (Docker Compose)
To launch the full production stack with PostgreSQL:
```bash
docker compose up -d --build
```
This starts:
- `talentscope-db`: PostgreSQL 16 on port 5432
- `talentscope-api`: FastAPI non-root container on port 8000
- `talentscope-web`: Nginx SPA container on port 80

---

## 🧪 Testing & Verification
```bash
# Run Invariant Guard Suite
python scripts/guard.py

# Run all backend & ML unit tests
python -m pytest backend/tests/ ml/tests/ -v

# Run frontend tests & build
cd frontend && npm test && npm run build
```
