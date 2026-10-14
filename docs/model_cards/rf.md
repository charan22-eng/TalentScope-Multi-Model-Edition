# Model Card: Random forest (`rf`)

## 1. Model Details
- **Model Key**: `rf`
- **Model Family**: Ensemble
- **Task Type**: classifier
- **Explainability Tier**: `partial`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7787`
- **Accuracy**: `0.7757`
- **Quadratic Weighted Kappa (QWK)**: `0.7819`
- **Expected Calibration Error (ECE)**: `0.0157`
- **Brier Score**: `0.3163`
- **Single-Row Latency (p95)**: `60.17 ms`
- **5,000-Row Batch Latency**: `92.15 ms`
- **Serialized Size**: `26.09 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.8058 | 0.7720 | 0.7886 | 715 |
| **Medium** | 0.7316 | 0.7985 | 0.7636 | 1072 |
| **High** | 0.8346 | 0.7391 | 0.7839 | 594 |

## 4. Hyperparameters & Tuning
```json
{
  "max_depth": 20,
  "max_features": null,
  "min_samples_leaf": 3,
  "n_estimators": 264
}
```

## 5. Limitations & Caveats
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The benchmark dataset is synthetic (12,000 rows). Relative model rankings reflect the non-linear data-generating process with saturation, interactions, and noise. Under a purely linear variant, simpler linear models perform near the top.
> 
> **Dual Holdout Evaluation Disclosure**: The test split was evaluated twice during development (ADR-008 Platt scaling and ADR-014 Temperature Scaling). The calibration update was prompted by test-set audit results indicating Platt OvR degraded ensemble calibration. Temperature scaling was subsequently selected on `cal-A` 5-fold CV. Both evaluations are logged in `reports/test_eval_log.csv`.

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.

## 7. Fresh-Seed Confirmation Run (Seed = 2026, N = 2,381)
> [!NOTE]
> **Strictly Observational**: Evaluated frozen on seed 2026 (variant: non-linear, test N = 2,381) with zero retraining or hyperparameter tuning. Never used for model choice.

- **Accuracy**: `0.7665` (95% CI: [0.7488, 0.7833])
- **Macro-F1**: `0.7676` (95% CI: [0.7500, 0.7838])
- **Quadratic Weighted Kappa (QWK)**: `0.7628` (95% CI: [0.7411, 0.7811])
- **Expected Calibration Error (ECE)**: `0.0247`
- **Conformal Coverage (α = 0.10)**: `21.8%` (Mean set size: `0.24`)
