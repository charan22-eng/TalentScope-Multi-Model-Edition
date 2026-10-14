# Model Card: K-nearest neighbours (`knn`)

## 1. Model Details
- **Model Key**: `knn`
- **Model Family**: Instance
- **Task Type**: classifier
- **Explainability Tier**: `partial`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7190`
- **Accuracy**: `0.7278`
- **Quadratic Weighted Kappa (QWK)**: `0.7017`
- **Expected Calibration Error (ECE)**: `0.0239`
- **Brier Score**: `0.3724`
- **Single-Row Latency (p95)**: `12.90 ms`
- **5,000-Row Batch Latency**: `126.30 ms`
- **Serialized Size**: `1.01 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.9115 | 0.5329 | 0.6726 | 715 |
| **Medium** | 0.6418 | 0.8993 | 0.7490 | 1072 |
| **High** | 0.8416 | 0.6532 | 0.7355 | 594 |

## 4. Hyperparameters & Tuning
```json
{
  "weights": "uniform",
  "p": 2,
  "n_neighbors": 31
}
```

## 5. Limitations & Caveats
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The benchmark dataset is synthetic (12,000 rows). Relative model rankings reflect the non-linear data-generating process with saturation, interactions, and noise. Under a purely linear variant, simpler linear models perform near the top.
> 
> **Prediction Invariance under Temperature Scaling**: Under ADR-008 Platt scaling (OvR sigmoid), three independent binary sigmoids altered multi-class argmax rankings, yielding an artificial 0.7543 macro-F1. Under ADR-014 Temperature Scaling, uniform scalar temperature strictly preserves base model argmax predictions, yielding the authentic base model test performance of 0.7190 macro-F1 and 0.7278 accuracy.
> 
> **Dual Holdout Evaluation Disclosure**: The test split was evaluated twice during development (ADR-008 Platt scaling and ADR-014 Temperature Scaling). The calibration update was prompted by test-set audit results indicating Platt OvR degraded ensemble calibration. Temperature scaling was subsequently selected on `cal-A` 5-fold CV. Both evaluations are logged in `reports/test_eval_log.csv`.

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.

## 7. Fresh-Seed Confirmation Run (Seed = 2026, N = 2,381)
> [!NOTE]
> **Strictly Observational**: Evaluated frozen on seed 2026 (variant: non-linear, test N = 2,381) with zero retraining or hyperparameter tuning. Never used for model choice.

- **Accuracy**: `0.7182` (95% CI: [0.7005, 0.7354])
- **Macro-F1**: `0.7082` (95% CI: [0.6895, 0.7257])
- **Quadratic Weighted Kappa (QWK)**: `0.6872` (95% CI: [0.6648, 0.7089])
- **Expected Calibration Error (ECE)**: `0.0179`
- **Conformal Coverage (α = 0.10)**: `9.5%` (Mean set size: `0.10`)
