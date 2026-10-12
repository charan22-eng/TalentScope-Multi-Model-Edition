# Model Card: Gradient boosting (histogram) (`boost`)

## 1. Model Details
- **Model Key**: `boost`
- **Model Family**: Ensemble
- **Task Type**: classifier
- **Explainability Tier**: `partial`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.8038`
- **Accuracy**: `0.8013`
- **Quadratic Weighted Kappa (QWK)**: `0.8075`
- **Expected Calibration Error (ECE)**: `0.0904`
- **Brier Score**: `0.3068`
- **Single-Row Latency (p95)**: `105.77 ms`
- **5,000-Row Batch Latency**: `128.93 ms`
- **Serialized Size**: `1.03 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.8346 | 0.7972 | 0.8155 | 715 |
| **Medium** | 0.7573 | 0.8265 | 0.7904 | 1072 |
| **High** | 0.8561 | 0.7609 | 0.8057 | 594 |

## 4. Hyperparameters & Tuning
```json
{
  "l2_regularization": 0.1235748371091217,
  "learning_rate": 0.05634303024223015,
  "max_iter": 293,
  "max_leaf_nodes": 10
}
```

## 5. Limitations & Caveats
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The benchmark dataset is synthetic (12,000 rows). Relative model rankings reflect the non-linear data-generating process with saturation, interactions, and noise. Under a purely linear variant, simpler linear models perform near the top.

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.