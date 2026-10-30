# TalentScope Multi-Model Edition: 5-Minute Demonstration Script

This script provides an exact, step-by-step 5-minute walkthrough of **TalentScope Multi-Model Edition** for executive demos, customer presentations, or viva examinations.

---

## Pre-Flight Check (30 seconds before demo)
1. Run `uv run python scripts/demo_setup.py` once from the repository root.
2. Backend running: `uv run uvicorn backend.app.main:app --reload --reload-dir backend --reload-dir ml/src --port 8000`
3. Frontend running: `cd frontend && npm run dev` (navigate to `http://localhost:5173`)
4. Log in as **HR Manager** (`hrmanager@test.com` / `HRManagerPassword123!`) or **Admin** (`admin@test.com` / `AdminPassword123!`).
5. Optional: run `uv run python scripts/demo_smoke.py` before the presentation.

---

## Scene 1: The Multi-Model Single Prediction & Agreement (1 Minute)
1. **Navigate to Single Prediction**: Click **Predict** in the navigation bar.
2. **Select an Employee**: Pick an existing employee or enter values (e.g., Senior Engineer with High Project Delivery, High Learning Rate, Moderate Overtime).
3. **Show the Champion Highlight**:
   - Point out that **Gradient Boosting (`boost`)** is flagged as the approved production Champion with a gold badge.
    - Show the predicted band: **Low**, **Medium**, or **High**, with calibrated probabilities and stability.
    - Note the **Split-Conformal Prediction Set** when it contains more than one band; this is an uncertainty signal for human review.
4. **Compare Across 7 Models**:
   - Scroll to the **All 7 Models Comparison Panel**.
   - Show the agreement meter: "5 of 7 models agree on Band 2 (71.4% consensus)".
   - Explain why this matters: If a single model gave Band 2 but others disagreed, it would be routed to human review. Here, high consensus provides operational confidence.
5. **Interactive What-If Advisor**:
    - Adjust attendance, training hours, projects completed, or certifications.
   - Watch the real-time slider re-evaluate without reloading, showing counterfactual sensitivity.

---

## Scene 2: The Model Arena & Head-to-Head Comparison (1.5 Minutes)
1. **Navigate to Arena**: Click **Model Arena** in the top navigation.
2. **Overview & Leaderboard**:
   - Show the 7 models ranked side-by-side with color-coded Okabe-Ito badges.
   - Point to the **Macro-F1**, calibration, fairness, latency, and MCDA columns. The governed champion is `boost` under the Balanced profile; `svm` is the runner-up.
3. **Head-to-Head**:
   - Select `boost` (Hist Gradient Boosting) vs `svm` (Support Vector Machine).
   - Point out that the comparison artifacts include paired uncertainty and significance information rather than relying on one raw metric.
4. **MCDA Priority Tuning**:
   - Switch from "Balanced" profile to "Accuracy-first" and then "Speed-first" or "Explainability-first".
   - Show how the deterministic MCDA rank updates: `boost` wins Balanced, `svm` wins Accuracy-first, while `dt`, `linreg`, or `logreg` surges when speed or explainability is prioritized.

---

## Scene 3: Explainability & 3D Decision Landscape (1 Minute)
1. **Navigate to 3D Decision Landscape**: Click **3D Experience** or the visual tab in Arena.
2. **Interactive Probability Surface**:
   - Rotate the 3D surface plot using the mouse.
   - Show the two-model overlay: `rf` surface vs `logreg` planar surface.
   - Switch to the **Difference Surface ($P_A - P_B$)**: Highlight the regions where non-linear trees capture interaction effects that the linear plane completely misses.
   - Show the 2D accessible heatmap fallback button for accessibility compliance.
3. **Feature Importance & Case Neighbors**:
    - Show the feature-attribution chart for the current employee feature contract.

---

## Scene 4: Governance, Review Queue, and MLOps (1.5 Minutes)
1. **Uncertainty-First Review Queue**:
   - Navigate to **Review Queue** (`/review`).
   - Show how cases where conformal set size $= 3$ or max calibrated probability $< 0.50$ are automatically flagged for senior HR review.
   - Open a pending item. Show that if an HR Manager attempts to overturn the recommendation, the system strictly enforces a mandatory written justification (`override_reason`), rejecting empty submissions.
2. **Audit Log & Reproducibility**:
   - Navigate to **Audit Explorer**.
   - Show immutable audit trails logging timestamp, user role, action (`PREDICTION_OVERTURN`, `CHAMPION_PROMOTED`), and cryptographic hash.
3. **Drift Monitoring & Shadow Mode**:
   - Navigate to **MLOps & Drift**.
   - Show Population Stability Index (PSI) and KS tests comparing inference batches against training baselines.
   - Highlight **Shadow Mode**: `boost` is quietly evaluated in parallel with `rf` on every live inference without impacting production decisions.
4. **Wrap-up**:
   - Generate an **Employee Transparency PDF** with one click.
   - Show the ethics charter notice: decision support only, zero protected attributes used, fully auditable.

---

## Key Talking Points Summary
- **7 models, 1 fair arena**: Not just one opaque black box, but seven competing architectures evaluated on identical frozen splits.
- **Rigor over guesswork**: 2,000-resample bootstrap, McNemar-Holm, conformal prediction, and 5-profile MCDA.
- **Complete safety**: On-premise local LLM, zero secrets, strict RBAC, human review queue, and one-click rollback.
