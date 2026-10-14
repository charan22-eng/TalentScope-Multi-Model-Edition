# Model Card: Linear regression (score to band) (`linreg`)

## 1. Model Details
- **Model Key**: `linreg`
- **Model Family**: Linear
- **Task Type**: score_to_band
- **Explainability Tier**: `native`
- **Artifact SemVer**: `2.0.0`
- **Dataset Split Hash**: `45a90aaf72c97cca...`

## 2. Test Performance Metrics (Holdout N = 2,381)
- **Macro-F1**: `0.7011`
- **Accuracy**: `0.6997`
- **Quadratic Weighted Kappa (QWK)**: `0.6920`
- **Expected Calibration Error (ECE)**: `0.0350`
- **Brier Score**: `0.4127`
- **Single-Row Latency (p95)**: `10.75 ms`
- **5,000-Row Batch Latency**: `10.27 ms`
- **Serialized Size**: `0.01 MB`

## 3. Class-Level Performance
| Band | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Low** | 0.7466 | 0.6224 | 0.6789 | 715 |
| **Medium** | 0.6425 | 0.7677 | 0.6995 | 1072 |
| **High** | 0.7897 | 0.6700 | 0.7250 | 594 |

## 4. Hyperparameters & Tuning
```json
{}
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

- **Accuracy**: `0.6665` (95% CI: [0.6476, 0.6838])
- **Macro-F1**: `0.6692` (95% CI: [0.6502, 0.6871])
- **Quadratic Weighted Kappa (QWK)**: `0.6525` (95% CI: [0.6291, 0.6763])
- **Expected Calibration Error (ECE)**: `0.0287`
- **Conformal Coverage (α = 0.10)**: `9.5%` (Mean set size: `0.10`)
