# TalentScope Multi-Model Final Evaluation Report (v2)

**Variant Evaluated**: `nonlinear` | **Holdout Test Set Size**: 2,381 rows
**Generated**: 2026-10-30 05:57:21 UTC

## 1. Classification Leaderboard (Sorted by Primary Metric: Macro-F1)

| Rank | Model Key | Label | Family | Macro-F1 | Accuracy | QWK | MCC | ROC-AUC | Log-Loss | ECE |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `svm` | Support vector machine (RBF) | Kernel | **0.8164** | 0.8148 | 0.8216 | 0.7110 | 0.9324 | 0.5180 | 0.0025 |
| 2 | `boost` | Gradient boosting (histogram) | Ensemble | **0.8056** | 0.8026 | 0.8107 | 0.6919 | 0.9310 | 0.4608 | 0.0126 |
| 3 | `rf` | Random forest | Ensemble | **0.7787** | 0.7757 | 0.7819 | 0.6495 | 0.9133 | 0.5350 | 0.0157 |
| 4 | `knn` | K-nearest neighbours | Instance | **0.7190** | 0.7278 | 0.7017 | 0.5843 | 0.8970 | 0.6639 | 0.0239 |
| 5 | `logreg` | Logistic regression (multinomial) | Linear | **0.7150** | 0.7127 | 0.7083 | 0.5493 | 0.8678 | 0.6452 | 0.0273 |
| 6 | `dt` | Decision tree | Tree | **0.7111** | 0.7102 | 0.7015 | 0.5459 | 0.8546 | 0.7524 | 0.0399 |
| 7 | `linreg` | Linear regression (score to band) | Linear | **0.7011** | 0.6997 | 0.6920 | 0.5284 | 0.8585 | 0.6732 | 0.0350 |

## 2. Efficiency and Latency Benchmarks

| Model Key | Single-Row p50 (ms) | Single-Row p95 (ms) | Batch 5,000 (ms) | Model Size (KB) | Tuning Time (s) |
|---|---|---|---|---|---|
| `svm` | 8.91 | 11.31 | 1761.2 | 765.1 | 11.1 |
| `boost` | 46.78 | 100.82 | 122.4 | 1050.5 | 23.5 |
| `rf` | 48.93 | 60.17 | 92.2 | 26719.5 | 21.1 |
| `knn` | 9.02 | 12.90 | 126.3 | 1038.5 | 1.3 |
| `logreg` | 6.81 | 9.73 | 14.8 | 6.8 | 0.6 |
| `dt` | 8.43 | 10.68 | 16.5 | 19.2 | 0.5 |
| `linreg` | 8.30 | 10.75 | 10.3 | 6.7 | 0.3 |

## 3. Error Breakdown (Exact vs Adjacent vs Extreme)

| Model Key | Exact Agreement (%) | Adjacent Error (+-1 Band) (%) | Extreme Error (Low <-> High) (%) |
|---|---|---|---|
| `svm` | 81.5% | 18.5% | 0.04% |
| `boost` | 80.3% | 19.7% | 0.08% |
| `rf` | 77.6% | 22.3% | 0.17% |
| `knn` | 72.8% | 27.1% | 0.08% |
| `logreg` | 71.3% | 28.3% | 0.38% |
| `dt` | 71.0% | 28.3% | 0.71% |
| `linreg` | 70.0% | 29.7% | 0.34% |

## 4. Calibration Analysis (ADR-014 Multinomial Temperature Scaling vs Raw)

| Model Key | Temperature (T) | Calibrated ECE | Raw ECE | Calibrated Brier | Raw Brier | Calibrated Log-Loss | Raw Log-Loss |
|---|---|---|---|---|---|---|---|
| `svm` | 0.6961 | **0.0025** | 0.1014 | **0.3030** | 0.3181 | **0.5180** | 0.5581 |
| `boost` | 0.9623 | **0.0126** | 0.0198 | **0.2790** | 0.2794 | **0.4608** | 0.4617 |
| `rf` | 0.8079 | **0.0157** | 0.0514 | **0.3163** | 0.3212 | **0.5350** | 0.5470 |
| `knn` | 0.6648 | **0.0239** | 0.0890 | **0.3724** | 0.3875 | **0.6639** | 0.6994 |
| `logreg` | 0.9731 | **0.0273** | 0.0282 | **0.3951** | 0.3954 | **0.6452** | 0.6457 |
| `dt` | 1.4026 | **0.0399** | 0.0492 | **0.4154** | 0.4171 | **0.7524** | 0.7550 |
| `linreg` | 1.0152 | **0.0350** | 0.0321 | **0.4127** | 0.4125 | **0.6732** | 0.6730 |

## 5. Regression Track (Continuous Performance Score)

| Model | MAE | RMSE | R2 | Spearman rho |
|---|---|---|---|---|
| `linreg` (ScoreToBand) | 7.94 | 10.07 | 0.6669 | 0.8032 |

## 6. Decision Support & Ethics Disclaimer

> **Notice**: Model rankings depend on the synthetic data-generating process and variant parameters.
> Protected attributes (gender, age_band) are strictly excluded from all training and inference feature sets.
> Output bands and probabilities are designed strictly for decision support and human review.
