# Model Card: Random forest (`rf`)

## 1. Model Details
- **Model Key**: `rf`
- **Model Family**: Ensemble
- **Task Type**: classifier
- **Explainability Tier**: `partial`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7804`
- **Accuracy**: `0.7770`
- **Quadratic Weighted Kappa (QWK)**: `0.7841`
- **Expected Calibration Error (ECE)**: `0.0133`
- **Brier Score**: `0.3179`
- **Single-Row Latency (p95)**: `99.38 ms`
- **5,000-Row Batch Latency**: `131.41 ms`
- **Serialized Size**: `26.09 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.8085 | 0.7678 | 0.7877 | 715 |
| **Medium** | 0.7347 | 0.7957 | 0.7640 | 1072 |
| **High** | 0.8281 | 0.7542 | 0.7894 | 594 |

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

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.