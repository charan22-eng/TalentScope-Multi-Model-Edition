# ADR-008: Probability Calibration Protocol and Method Selection

## Status
Accepted

## Context
TalentScope compares seven models in a fair arena. Downstream components (log-loss, Brier score, ECE, conformal prediction sets, and LLM uncertainty narration) depend on well-calibrated class probability estimates:
1. Some models (like uncalibrated SVM with RBF kernel) do not natively produce calibrated probabilities without expensive internal multi-fold CV.
2. Even models with probabilistic outputs (logistic regression, trees, gradient boosting) can suffer from overconfidence or miscalibration under class imbalance or nonlinear interactions.
3. To maintain strict fairness across all algorithms, the protocol mandates one common probability calibration method evaluated on `cal-A` (10% of the dataset, 1,190 rows), ensuring the held-out test split is never touched.

## Evaluation on Cal-A Cross-Validation
We performed a 5-fold cross-validation calibration ablation strictly within `cal-A` comparing Platt scaling (`sigmoid`) versus Non-parametric Isotonic Regression (`isotonic`) via `CalibratedClassifierCV(method=..., cv="prefit")` on the models trained on the training partition:

| Model | Method | Brier Score (Mean ± Std) | Log-Loss (Mean ± Std) | Observation |
|---|---|---|---|---|
| `logreg` | Sigmoid | 0.4335 ± 0.0164 | **0.7065 ± 0.0272** | Stable likelihood, well-behaved tails |
| `logreg` | Isotonic | 0.4279 ± 0.0218 | 0.7775 ± 0.1405 | High variance, overfitted step boundaries |
| `svm` | Sigmoid | 0.3029 ± 0.0252 | **0.5172 ± 0.0247** | Smooth Platt transformation of decision function |
| `svm` | Isotonic | 0.2890 ± 0.0225 | 0.5533 ± 0.1314 | Tail degradation |
| `rf` | Sigmoid | 0.3322 ± 0.0226 | **0.5512 ± 0.0354** | Avoids extreme 0/1 voting probabilities |
| `rf` | Isotonic | 0.3304 ± 0.0236 | 0.6439 ± 0.1910 | High log-loss penalty on edge cases |
| `boost` | Sigmoid | 0.3213 ± 0.0194 | **0.5206 ± 0.0297** | Retains smooth ranking |
| `boost` | Isotonic | 0.3238 ± 0.0186 | 0.6241 ± 0.1515 | Severe penalties on misranked probabilities |

## Decision
1. **Calibration Method**: We select **Platt scaling (`method="sigmoid"`)** as the universal post-hoc calibration method across the comparison platform.
2. **Implementation**:
   - Models are fitted on `train` (7,142 rows).
   - Post-hoc calibration is fitted on `cal-A` (1,190 rows) using `CalibratedClassifierCV(estimator=model, method="sigmoid", cv="prefit")`.
   - Linear Regression (`linreg` via `ScoreToBand`) derives Gaussian residual probabilities directly from its out-of-fold residuals, but can also be wrapped or evaluated consistently.
   - `cal-B` is reserved exclusively for conformal prediction thresholds (guaranteeing independence between probability calibration and conformal coverage guarantees).
3. **Invariants Enforced**:
   - `cal-A` and `cal-B` are strictly forbidden from model tuning search loops (enforced by guard G7).
   - The test set is evaluated exactly once in `make final` (guard G6).

## Consequences
- Guaranteed smooth, strictly non-zero probabilities avoiding infinite log-loss penalties.
- High stability across cross-validation splits without the step-function artifacts inherent to isotonic regression on medium sample sizes (N ≈ 1,200).
