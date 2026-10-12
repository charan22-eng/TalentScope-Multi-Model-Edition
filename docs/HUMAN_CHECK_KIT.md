# TALENTSCOPE HUMAN CHECK KIT

This kit contains all checks marked **H (Human-only)** and the human half of checks marked **B (Both Agent & Human)** as defined in `docs/MULTIMODEL_PACK.md` Part 8 and `docs/PHASES_AND_VERIFICATION.md`.

These checks require interactive browser evaluation, visual inspection, live local LLM runtime execution, external network/CI access, or subjective user experience testing that an automated verification script cannot execute without human oversight.

---

## 1. Quick 20-Minute Smoke Path

Follow this path to verify end-to-end functionality across all layers in under 20 minutes:

### Step 1: Start Backend and Frontend
- **Terminal 1 (Backend)**:
  - PowerShell:
    ```powershell
    python -m uvicorn backend.app.main:app --port 8000 --reload
    ```
  - Bash:
    ```bash
    python -m uvicorn backend.app.main:app --port 8000 --reload
    ```
- **Terminal 2 (Frontend)**:
  - Both:
    ```bash
    cd frontend && npm run dev
    ```
- Open browser at `http://localhost:5173`.

### Step 2: Role-Based Access Control Smoke Test
Log in with each seeded user and verify access permissions:
1. `viewer@test.com` / `viewer123`:
   - Can view Dashboard and Leaderboard.
   - **Verify**: Cannot access Model Lab settings or execute Champion Promotion.
2. `analyst@test.com` / `analyst123`:
   - Can run Single Predict and Batch Predict.
   - Can run MCDA sensitivity simulations.
3. `hrmanager@test.com` / `hr123`:
   - Can run batch predictions and export CSV/PDF reports.
4. `admin@test.com` / `admin123`:
   - Full access, can promote champion model in Model Lab.

### Step 3: Multi-Model Single Predict
- Navigate to `/predict`.
- Click "Fill Sample" (e.g., Attendance=92, Experience=6.0, PrevScore=3.0).
- Click "Predict with All Models".
- **Verify**: Results table displays predictions from all 7 models (`rf`, `boost`, `svm`, `logreg`, `knn`, `linreg`, `dt`).
- **Verify**: Conformal prediction set and stability index are displayed.

### Step 4: Model Arena Exploration
- Navigate to `/arena`.
- **Leaderboard**: Verify Random Forest is displayed as Champion and rank order matches Balanced profile (`rf`, `boost`, `svm`, `logreg`, `knn`, `linreg`, `dt`).
- **Head-to-Head**: Select `rf` vs `boost`. Verify McNemar p-value and win-rate matrix display.
- **Dynamic MCDA**: Adjust weight sliders (e.g. increase Fairness). Verify model ranking updates in real-time.
- **3D Decision Surface**: Inspect 3D Canvas. Rotate camera, toggle between 2D heatmap and 3D surface. Verify no frame rate stutter.

### Step 5: Batch Prediction with Messy CSV
- Navigate to `/batch`.
- Upload a CSV containing missing values or formula cells (e.g., `=SUM(...)`).
- Verify formula characters are safely stripped and predictions return for valid rows without server 500 error.

### Step 6: Local LLM Verdict Panel
- With local Ollama offline:
  - Request LLM second opinion in Arena.
  - Verify UI displays fallback template explanation stating local LLM is unreachable (HTTP 503 Problem Details), without crashing.
- With local Ollama running (`ollama run llama3.1` or `qwen2.5:7b`):
  - Request verdict.
  - Verify JSON verdict renders with grounded facts and winner alignment.

---

## 2. Top 15 Priority Checks (Blocking & Core Science Replications)

### [1] VM3.2 (BLOCKING) — Test Set Used Once & Lock Integrity
- **What to check**: Verify that `reports/test_eval.lock` contains configuration hash and cannot be re-executed without `--new-config`. Verify no leakage of test indices in training code.
- **PowerShell**:
  ```powershell
  python ml/src/epk/final_eval.py --check-lock
  Get-Content reports/test_eval.lock
  ```
- **Bash**:
  ```bash
  python ml/src/epk/final_eval.py --check-lock
  cat reports/test_eval.lock
  ```
- **Expected Result**: Exit code 0; `status: LOCKED`, `config_sha: 01ba89823e26...`.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [2] VM7.2 (BLOCKING) — Artifact Tamper Detection
- **What to check**: Loader refuses any modified joblib or MANIFEST.json file.
- **Command**:
  ```bash
  python verification/run_adversarial_tests.py
  ```
- **Expected Result**: Section `X4 Artifact Tamper Detection` passes with `ArtifactIntegrityError`.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [3] VM6.2 (BLOCKING) — Local LLM SSRF Guard
- **What to check**: Base URLs pointing to cloud metadata (`169.254.169.254`) or public internet are strictly rejected.
- **Command**:
  ```bash
  python -c "from epk.llm_engine import validate_llm_url; print('Loopback:', validate_llm_url('http://127.0.0.1:11434')); print('Metadata:', validate_llm_url('http://169.254.169.254/latest'))"
  ```
- **Expected Result**: Loopback returns `True`; Metadata returns `False` (SSRF violation raised).
- **Paste Raw Output Here**:
  ```text

  ```

---

### [4] VM6.3 (BLOCKING) & VM4.11 (BLOCKING) — Zero Employee-Level Data in Prompts & Evidence Packet
- **What to check**: Capture generated prompt and `evidence_packet.json`; assert 0 occurrences of employee IDs, names, or raw rows.
- **Command**:
  ```bash
  python -c "import json; p = json.load(open('artifacts/v2/comparison/evidence_packet.json')); assert 'employee_id' not in str(p); assert 'gender' not in str(p); print('Evidence Packet Safe:', len(p['facts']), 'facts')"
  ```
- **Expected Result**: `Evidence Packet Safe: 31 facts`.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [5] VM8.9 (BLOCKING) — Model Whitelist and Traversal Refusal
- **What to check**: Model loading rejects path traversal (`../`, absolute paths) and unregistered model keys.
- **Command**:
  ```bash
  python -c "from epk.artifacts import default_loader; [default_loader.load_model(k) for k in ['../secret', 'unknown', '/etc/passwd']]"
  ```
- **Expected Result**: `KeyError` or `ValueError: Unknown model key`.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [6] V10.2 (BLOCKING) & V10.4 (BLOCKING) — RBAC Matrix & Token Validation
- **What to check**: Anonymous requests to `/api/v2/models` and `/api/v2/verdicts` are rejected (401/403). Expired tokens return 401.
- **Command**:
  ```bash
  python verification/x08_rbac_auth.py
  ```
- **Expected Result**: Anonymous denied, expired token denied (401), valid user allowed.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [7] V6.7 (BLOCKING) — Upload and CSV Sanitization
- **What to check**: CSV upload containing formula injection `=cmd|' /C calc'!A0` or `@SUM(...)` strips dangerous leading characters.
- **Command**:
  ```bash
  python -c "from backend.services.csv_cleaner import sanitize_cell; print(sanitize_cell('=1+1'), sanitize_cell('@SUM(A1)'))"
  ```
- **Expected Result**: Formula symbols stripped or escaped with leading single quote.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [8] V10.8 (BLOCKING) — Security Headers & Cookie Flags
- **What to check**: Verify backend response headers include HSTS, X-Content-Type-Options, X-Frame-Options, and CSP.
- **PowerShell**:
  ```powershell
  curl -I http://localhost:8000/health
  ```
- **Bash**:
  ```bash
  curl -s -I http://localhost:8000/health | grep -iE "(x-frame|x-content|strict-transport|content-security)"
  ```
- **Expected Result**: `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [9] V13.5 (BLOCKING) — Dependency Audit
- **What to check**: `npm audit --omit=dev` and `pip-audit` report 0 high/critical vulnerabilities.
- **Command**:
  ```bash
  cd frontend && npm audit --omit=dev
  ```
- **Expected Result**: `found 0 vulnerabilities`.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [10] V14.4 (BLOCKING) — Production Deployment & Health Drill
- **What to check**: Docker compose config validates cleanly and service healthchecks succeed.
- **Command**:
  ```bash
  docker compose config
  ```
- **Expected Result**: Valid configuration with 0 syntax errors.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [11] V15.2 (BLOCKING) — Cross-Document Numbers Consistency
- **What to check**: Automated audit comparing README, model cards, datasheets, and machine leaderboard files.
- **Command**:
  ```bash
  python verification/x26_numbers_consistency.py
  ```
- **Expected Result**: All reported metrics match machine files within stated tolerances.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [12] VM1.2 & VM1.3 — Dataset Determinism and Variant Properties
- **What to check**: Confirm dataset generation produces identical hash across independent runs with seed 42.
- **Command**:
  ```bash
  python ml/src/epk/data.py --variant default --output test_gen.csv
  ```
- **Expected Result**: Generates 12,096 raw rows.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [13] VM3.9 — Independent Replication of Logistic Regression and Random Forest
- **What to check**: Train LogReg and RF using independent script on frozen train split and evaluate on frozen test split.
- **Command**:
  ```bash
  python verification/x16_independent_metrics.py
  ```
- **Expected Result**: Macro-F1 matches within 0.02 of reported leaderboard values (RF: 0.8124, LogReg: 0.7712).
- **Paste Raw Output Here**:
  ```text

  ```

---

### [14] VM4.4 — Independent MCDA 5-Profile Recomputation
- **What to check**: Recompute TOPSIS/PROMETHEE scores and ranks across all 5 profiles using pure NumPy/SciPy.
- **Command**:
  ```bash
  python verification/x17_independent_mcda.py
  ```
- **Expected Result**: Balanced Profile: Winner `rf` (0.6387), Runner-up `boost` (0.6247). Rank match: PASS.
- **Paste Raw Output Here**:
  ```text

  ```

---

### [15] VM5.3 — KNN Neighbours By Hand & Counterfactual Validity
- **What to check**: Sample 50 queries; calculate Euclidean distance to nearest neighbours by hand and verify against `calibrated_knn`.
- **Command**:
  ```bash
  python verification/x20_knn_surface.py
  ```
- **Expected Result**: Distance difference < 1e-6; Counterfactual validity 100%.
- **Paste Raw Output Here**:
  ```text

  ```

---

## 3. Real-Model LLM Golden Evaluation (`ml/scripts/llm_eval.py`)

If a local LLM runtime (e.g. Ollama with `llama3.1:8b` or `qwen2.5:7b`) is installed and running on `http://127.0.0.1:11434`:

1. Start Ollama:
   ```bash
   ollama serve
   ollama pull qwen2.5:7b
   ```
2. Run Golden Evaluation:
   ```bash
   python ml/scripts/llm_eval.py --model qwen2.5:7b --url http://127.0.0.1:11434
   ```
3. Evaluation Criteria:
   - Schema adherence: 100% valid JSON conforming to `verdict_schema.json`.
   - Winner consistency: Verdict names `rf` (Random Forest) as Champion matching evidence packet.
   - Grounded facts: Citations refer only to facts 1-31 from `evidence_packet.json`.
   - Prompt hygiene: No employee PII echoed.
4. Record Result in `docs/VERIFICATION_LOG.md` under `VM6.6`.

---

## 4. Usability Test Script (5 Users, System Usability Scale - SUS)

### Participants
- 5 representative users: 2 HR Managers, 2 Business Analysts, 1 Department Lead.

### Task Protocol (15 minutes per user)
1. **Task A (Single Predict)**: Enter features for an employee with attendance 88% and prev_score 3. Identify the predicted performance band and confidence set.
2. **Task B (What-If Advisor)**: Explore counterfactual options to move prediction from "Medium" to "High". Note if immutable attributes (experience years) are correctly protected.
3. **Task C (Arena Inspection)**: Inspect Model Arena. Identify which model is Champion and why it was selected over Gradient Boosting.
4. **Task D (Batch Upload)**: Upload a 20-row sample CSV. Review batch summary and download PDF report.

### SUS Questionnaire (Score 1-5: Strongly Disagree to Strongly Agree)
1. I think that I would like to use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think that I would need the support of a technical person to be able to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

### Scoring
- Calculate SUS Score: $((\sum \text{odd} - 5) + (25 - \sum \text{even})) \times 2.5$.
- Target Threshold: SUS $\ge 75$ (Good/Excellent usability).
- Record score in `docs/VERIFICATION_LOG.md` under `V15.1`.
