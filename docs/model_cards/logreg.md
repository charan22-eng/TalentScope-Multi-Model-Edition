# Model Card: Logistic regression (multinomial) (`logreg`)

## 1. Model Details
- **Model Key**: `logreg`
- **Model Family**: Linear
- **Task Type**: classifier
- **Explainability Tier**: `native`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7189`
- **Accuracy**: `0.7148`
- **Quadratic Weighted Kappa (QWK)**: `0.7173`
- **Expected Calibration Error (ECE)**: `0.1246`
- **Brier Score**: `0.4295`
- **Single-Row Latency (p95)**: `22.60 ms`
- **5,000-Row Batch Latency**: `11.97 ms`
- **Serialized Size**: `0.01 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.7568 | 0.6573 | 0.7036 | 715 |
| **Medium** | 0.6692 | 0.7416 | 0.7035 | 1072 |
| **High** | 0.7640 | 0.7357 | 0.7496 | 594 |

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

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.