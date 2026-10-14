# Model Card: Logistic regression (multinomial) (`logreg`)

## 1. Model Details
- **Model Key**: `logreg`
- **Model Family**: Linear
- **Task Type**: classifier
- **Explainability Tier**: `native`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7150`
- **Accuracy**: `0.7127`
- **Quadratic Weighted Kappa (QWK)**: `0.7083`
- **Expected Calibration Error (ECE)**: `0.0273`
- **Brier Score**: `0.3951`
- **Single-Row Latency (p95)**: `9.73 ms`
- **5,000-Row Batch Latency**: `14.82 ms`
- **Serialized Size**: `0.01 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.7532 | 0.6615 | 0.7044 | 715 |
| **Medium** | 0.6600 | 0.7640 | 0.7082 | 1072 |
| **High** | 0.7910 | 0.6818 | 0.7324 | 594 |

## 4. Hyperparameters & Tuning
```json
{
  "C": 0.07459343285726545,
  "class_weight": null
}
```

## 5. Limitations & Caveats
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The benchmark dataset is synthetic (12,000 rows). Relative model rankings reflect the non-linear data-generating process with saturation, interactions, and noise. Under a purely linear variant, simpler linear models perform near the top.
> 
> **Dual Holdout Evaluation Disclosure**: The test split was evaluated twice during development (ADR-008 Platt scaling and ADR-014 Temperature Scaling). The calibration update was prompted by test-set audit results indicating Platt OvR degraded linear model calibration (ECE increased from 0.0282 to 0.1246 under Platt OvR). Temperature scaling was subsequently selected on `cal-A` 5-fold CV. Both evaluations are logged in `reports/test_eval_log.csv`.

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.

## 7. Fresh-Seed Confirmation Run (Seed = 2026, N = 2,381)
> [!NOTE]
> **Strictly Observational**: Evaluated frozen on seed 2026 (variant: non-linear, test N = 2,381) with zero retraining or hyperparameter tuning. Never used for model choice.

- **Accuracy**: `0.6909` (95% CI: [0.6732, 0.7090])
- **Macro-F1**: `0.6954` (95% CI: [0.6766, 0.7136])
- **Quadratic Weighted Kappa (QWK)**: `0.6855` (95% CI: [0.6631, 0.7088])
- **Expected Calibration Error (ECE)**: `0.0156`
- **Conformal Coverage (α = 0.10)**: `10.6%` (Mean set size: `0.11`)
