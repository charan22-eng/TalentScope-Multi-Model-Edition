# Model Card: Decision tree (`dt`)

## 1. Model Details
- **Model Key**: `dt`
- **Model Family**: Tree
- **Task Type**: classifier
- **Explainability Tier**: `native`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7111`
- **Accuracy**: `0.7102`
- **Quadratic Weighted Kappa (QWK)**: `0.7015`
- **Expected Calibration Error (ECE)**: `0.0399`
- **Brier Score**: `0.4154`
- **Single-Row Latency (p95)**: `10.68 ms`
- **5,000-Row Batch Latency**: `16.51 ms`
- **Serialized Size**: `0.02 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.7403 | 0.7217 | 0.7309 | 715 |
| **Medium** | 0.6681 | 0.7397 | 0.7021 | 1072 |
| **High** | 0.7686 | 0.6431 | 0.7003 | 594 |

## 4. Hyperparameters & Tuning
```json
{
  "ccp_alpha": 0.0006838478430964043,
  "criterion": "gini",
  "max_depth": 13,
  "min_samples_leaf": 25
}
```

## 5. Limitations & Caveats
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The benchmark dataset is synthetic (12,000 rows). Relative model rankings reflect the non-linear data-generating process with saturation, interactions, and noise. Under a purely linear variant, simpler linear models perform near the top.

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.