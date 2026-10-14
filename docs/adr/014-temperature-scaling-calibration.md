# ADR-014: Multinomial Temperature Scaling as Unified Calibration Method

## Status
Accepted (Supersedes ADR-008)

## Context
TalentScope compares seven diverse model families in a unified comparison arena. In ADR-008, Platt scaling (`CalibratedClassifierCV(method="sigmoid", cv="prefit")`) was initially selected. However, independent audits and follow-up evaluations demonstrated that independent One-vs-Rest (OvR) sigmoid calibration degrades calibration performance on several models:
- On `boost` (HistGradientBoosting), Platt OvR increased test ECE from 0.0198 to 0.0904, and Brier from 0.2794 to 0.3068.
- On `logreg` (Multinomial Logistic Regression), Platt OvR increased test ECE from 0.0282 to 0.1246, and Brier from 0.3954 to 0.4295.
- On `knn` (K-Nearest Neighbors), test probabilities were distorted by independent binary sigmoids destroying the softmax coupling condition ($\sum_c p_c = 1$).

To establish an empirically grounded calibration standard, we performed a 5-fold cross-validation experiment strictly within the held-out `cal-A` calibration split ($N = 1,190$, exactly 10% of the dataset). The test set was NOT evaluated during method selection.

## Empirical Comparison on Cal-A (5-Fold Stratified CV)
Candidate methods evaluated across all seven models:
1. **Raw (Baseline)**: Uncalibrated probabilities directly from the trained pipelines.
2. **Sigmoid OvR (Platt Scaling)**: Binary Platt scaling fitted independently per class via `CalibratedClassifierCV`.
3. **Isotonic OvR**: Non-parametric isotonic regression fitted per class.
4. **Multinomial Temperature Scaling**: Single scalar temperature $T > 0$ optimizing Negative Log-Likelihood (NLL) via `scipy.optimize.minimize_scalar`, preserving rank order and softmax coupling.

### Results Across All Seven Models (Mean over Models, 5-Fold CV on Cal-A)
| Method | Mean Brier Score | Mean ECE (10-bin top label) | Mean Log Loss |
|---|:---:|:---:|:---:|
| Raw (Uncalibrated Baseline) | 0.3677 | 0.0639 | 0.6200 |
| Sigmoid OvR (Platt Scaling) | 0.3688 | 0.0683 | 0.6135 |
| Isotonic OvR | 0.3675 | 0.0600 | 0.6775 |
| **Multinomial Temperature Scaling** | **0.3640** | **0.0472** | **0.6051** |

### Per-Model Brier Score Breakdown on Cal-A
| Model | Raw | Sigmoid OvR | Isotonic OvR | Temperature Scaling |
|---|:---:|:---:|:---:|:---:|
| `boost` | 0.2906 | 0.3167 | 0.3189 | **0.2911** |
| `dt` | 0.4175 | 0.4195 | 0.4159 | **0.4158** |
| `knn` | 0.3964 | **0.3588** | 0.3643 | 0.3864 |
| `linreg` | **0.4171** | 0.4196 | 0.4226 | 0.4179 |
| `logreg` | 0.3967 | 0.4333 | 0.4279 | **0.3966** |
| `rf` | 0.3281 | 0.3293 | 0.3266 | **0.3252** |
| `svm` | 0.3271 | **0.3042** | 0.2959 | 0.3147 |

## Decision
1. **Universal Calibration Method**: Select **Multinomial Temperature Scaling** (`TemperatureScalingCalibrator`) as the unified calibration method across the TalentScope platform.
2. **Implementation Protocol**:
   - The base model is trained strictly on `train` (7,142 rows).
   - Temperature parameter $T > 0$ is fitted on `cal-A` (1,190 rows) by minimizing cross-entropy.
   - For SVM, $T$ operates directly on decision function logits $z$.
   - For probabilistic classifiers, $T$ operates on centered log-probabilities $\log p_c - \frac{1}{K}\sum_j \log p_j$.
3. **Dual Metric Reporting**:
   - Both raw (uncalibrated) and calibrated metrics (ECE, Brier, Log Loss) are recorded side-by-side in `leaderboard.json` and model cards.
4. **Clean Scikit-Learn Wrapper**:
   - The custom estimator implements `BaseEstimator` and `ClassifierMixin`, providing `predict`, `predict_proba`, and `classes_ = [0, 1, 2]`, eliminating any `cv="prefit"` deprecation warnings.

## Consequences
- Mean Brier across models improves to 0.3640 (lowest among all candidates).
- Mean ECE across models drops from 0.0683 (sigmoid) to 0.0472 (temperature scaling), a 31% reduction in calibration error.
- Multiclass probabilities naturally sum to 1.0 without heuristic re-normalization.
- Preserves multiclass rank order: $\text{argmax}_c P_T(y=c|x) = \text{argmax}_c P(y=c|x)$.

## Holdout Integrity & Dual Evaluation Disclosure
1. **Dual Test Set Evaluation**: The holdout test split ($N = 2,381$) was evaluated twice during project development:
   - First evaluation under ADR-008 (One-vs-Rest Platt scaling via `CalibratedClassifierCV(method="sigmoid", cv="prefit")`), logged in `reports/test_eval_log.csv` at `2026-10-12T13:41:03Z`.
   - Second evaluation under ADR-014 (Multinomial Temperature Scaling fitted on `cal-A`), logged in `reports/test_eval_log.csv` at `2026-10-13T19:37:16Z`.
2. **Audit Prompt & Holdout Non-Pristineness**: The decision to revisit calibration was prompted by test-set audit findings in earlier review rounds indicating that Platt OvR degraded ensemble and linear model calibration (e.g. `boost` ECE increased from 0.0198 to 0.0904, `logreg` from 0.0282 to 0.1246).
3. **Partition Isolation**: Although candidate calibration methods were compared strictly via 5-fold cross-validation on `cal-A` ($N = 1,190$) without test peeking, the test partition cannot be claimed as an untouched single-look holdout. Both test evaluations, the full log trail in `reports/test_eval_log.csv`, and all raw vs calibrated metrics are permanently disclosed.

