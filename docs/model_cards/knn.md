# Model Card: K-nearest neighbours (`knn`)

## 1. Model Details
- **Model Key**: `knn`
- **Model Family**: Instance
- **Task Type**: classifier
- **Explainability Tier**: `partial`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7543`
- **Accuracy**: `0.7518`
- **Quadratic Weighted Kappa (QWK)**: `0.7550`
- **Expected Calibration Error (ECE)**: `0.0246`
- **Brier Score**: `0.3443`
- **Single-Row Latency (p95)**: `16.94 ms`
- **5,000-Row Batch Latency**: `198.99 ms`
- **Serialized Size**: `1.01 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.8217 | 0.7091 | 0.7613 | 715 |
| **Medium** | 0.7031 | 0.7864 | 0.7424 | 1072 |
| **High** | 0.7788 | 0.7407 | 0.7593 | 594 |

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

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.