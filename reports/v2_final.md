# TalentScope Multi-Model Final Evaluation Report (v2)

**Variant Evaluated**: `nonlinear` | **Holdout Test Set Size**: 2,381 rows
**Generated**: 2026-10-12 13:41:28 UTC

## 1. Classification Leaderboard (Sorted by Primary Metric: Macro-F1)

| Rank | Model Key | Label | Family | Macro-F1 | Accuracy | QWK | MCC | ROC-AUC | Log-Loss | ECE |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `svm` | Support vector machine (RBF) | Kernel | **0.8164** | 0.8148 | 0.8216 | 0.7110 | 0.9266 | 0.4977 | 0.0270 |
| 2 | `boost` | Gradient boosting (histogram) | Ensemble | **0.8038** | 0.8013 | 0.8075 | 0.6898 | 0.9282 | 0.5067 | 0.0904 |
| 3 | `rf` | Random forest | Ensemble | **0.7804** | 0.7770 | 0.7841 | 0.6517 | 0.9139 | 0.5368 | 0.0133 |
| 4 | `knn` | K-nearest neighbours | Instance | **0.7543** | 0.7518 | 0.7550 | 0.6122 | 0.9006 | 0.5698 | 0.0246 |
| 5 | `logreg` | Logistic regression (multinomial) | Linear | **0.7189** | 0.7148 | 0.7173 | 0.5542 | 0.8678 | 0.6943 | 0.1246 |
| 6 | `dt` | Decision tree | Tree | **0.7094** | 0.7085 | 0.6993 | 0.5431 | 0.8549 | 0.7071 | 0.0342 |
| 7 | `linreg` | Linear regression (score to band) | Linear | **0.7032** | 0.7014 | 0.6955 | 0.5310 | 0.8585 | 0.6791 | 0.0213 |

## 2. Efficiency and Latency Benchmarks

| Model Key | Single-Row p50 (ms) | Single-Row p95 (ms) | Batch 5,000 (ms) | Model Size (KB) | Tuning Time (s) |
|---|---|---|---|---|---|
| `svm` | 11.85 | 23.47 | 2013.6 | 765.6 | 20.8 |
| `boost` | 45.19 | 105.77 | 128.9 | 1051.0 | 31.9 |
| `rf` | 59.35 | 99.38 | 131.4 | 26715.6 | 30.2 |
| `knn` | 10.33 | 16.94 | 199.0 | 1039.0 | 1.6 |
| `logreg` | 14.08 | 22.60 | 12.0 | 7.2 | 0.8 |
| `dt` | 8.24 | 16.27 | 8.9 | 19.7 | 0.5 |
| `linreg` | 7.07 | 13.23 | 24.9 | 7.1 | 0.4 |

## 3. Error Breakdown (Exact vs Adjacent vs Extreme)

| Model Key | Exact Agreement (%) | Adjacent Error (+-1 Band) (%) | Extreme Error (Low <-> High) (%) |
|---|---|---|---|
| `svm` | 81.5% | 18.5% | 0.04% |
| `boost` | 80.1% | 19.7% | 0.13% |
| `rf` | 77.7% | 22.1% | 0.17% |
| `knn` | 75.2% | 24.6% | 0.25% |
| `logreg` | 71.5% | 28.1% | 0.38% |
| `dt` | 70.9% | 28.4% | 0.71% |
| `linreg` | 70.1% | 29.5% | 0.34% |

## 4. Regression Track (Continuous Performance Score)

| Model | MAE | RMSE | R2 | Spearman rho |
|---|---|---|---|---|
| `linreg` (ScoreToBand) | 7.94 | 10.07 | 0.6669 | 0.8032 |

## 5. Decision Support & Ethics Disclaimer

> **Notice**: Model rankings depend on the synthetic data-generating process and variant parameters.
> Protected attributes (gender, age_band) are strictly excluded from all training and inference feature sets.
> Output bands and probabilities are designed strictly for decision support and human review.
