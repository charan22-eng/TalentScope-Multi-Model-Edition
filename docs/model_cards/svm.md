# Model Card: Support vector machine (RBF) (`svm`)

## 1. Model Details
- **Model Key**: `svm`
- **Model Family**: Kernel
- **Task Type**: classifier
- **Explainability Tier**: `post_hoc`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.8164`
- **Accuracy**: `0.8148`
- **Quadratic Weighted Kappa (QWK)**: `0.8216`
- **Expected Calibration Error (ECE)**: `0.0025`
- **Brier Score**: `0.3030`
- **Single-Row Latency (p95)**: `11.31 ms`
- **5,000-Row Batch Latency**: `1761.20 ms`
- **Serialized Size**: `0.75 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.8746 | 0.8000 | 0.8356 | 715 |
| **Medium** | 0.7655 | 0.8498 | 0.8055 | 1072 |
| **High** | 0.8510 | 0.7694 | 0.8081 | 594 |

## 4. Hyperparameters & Tuning
```json
{
  "C": 0.8179499475211671,
  "gamma": 0.037520558551242804
}
```

## 5. Limitations & Caveats
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The benchmark dataset is synthetic (12,000 rows). Relative model rankings reflect the non-linear data-generating process with saturation, interactions, and noise. Under a purely linear variant, simpler linear models perform near the top.

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.