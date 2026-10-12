# Model Card: Linear regression (score to band) (`linreg`)

## 1. Model Details
- **Model Key**: `linreg`
- **Model Family**: Linear
- **Task Type**: score_to_band
- **Explainability Tier**: `native`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7032`
- **Accuracy**: `0.7014`
- **Quadratic Weighted Kappa (QWK)**: `0.6955`
- **Expected Calibration Error (ECE)**: `0.0213`
- **Brier Score**: `0.4126`
- **Single-Row Latency (p95)**: `13.23 ms`
- **5,000-Row Batch Latency**: `24.92 ms`
- **Serialized Size**: `0.01 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.7439 | 0.6378 | 0.6867 | 715 |
| **Medium** | 0.6458 | 0.7621 | 0.6992 | 1072 |
| **High** | 0.7893 | 0.6684 | 0.7238 | 594 |

## 4. Hyperparameters & Tuning
```json
{}
```

## 5. Limitations & Caveats
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The benchmark dataset is synthetic (12,000 rows). Relative model rankings reflect the non-linear data-generating process with saturation, interactions, and noise. Under a purely linear variant, simpler linear models perform near the top.

## 6. Intended Use & Ethics
- **Decision Support Only**: This model is built for human-in-the-loop decision support, not automated termination or promotion.
- **Zero Protected Inputs**: The model operates strictly on skills, output, and tenure metrics. Protected demographic attributes are excluded from all model training and inference pipelines.