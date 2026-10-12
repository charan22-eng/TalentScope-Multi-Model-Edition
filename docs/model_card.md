# TalentScope Model Arena: Seven-Model Comparison Card

## 1. Arena Overview
TalentScope evaluates seven diverse machine-learning architectures on a standardized 12,000-row dataset across identical cross-validation folds, tuning budgets, and preprocessing pipelines.

## 2. Champion Model (Balanced Profile)
- **Champion**: **Random Forest** (`rf`)
- **Decision Strength**: `MARGINAL`
- **Rank-1 Probability (Dirichlet 5,000 draws)**: `64.2%`
- **Composite MCDA Score**: `0.573`
- **Selection Rule**: ADR-009 Multi-Criteria Decision Analysis (Balanced profile)

## 3. Holdout Leaderboard (Test N = 2,381)
| Rank | Model | Family | Macro-F1 | Accuracy | QWK | ECE | p95 Latency | Explain Tier |
|---|---|---|---|---|---|---|---|---|
| 1 | **Support vector machine (RBF)** (`svm`) | Kernel | `0.8164` | `0.8148` | `0.8216` | `0.0270` | `23.5 ms` | `classifier` |
| 2 | **Gradient boosting (histogram)** (`boost`) | Ensemble | `0.8038` | `0.8013` | `0.8075` | `0.0904` | `105.8 ms` | `classifier` |
| 3 | **Random forest** (`rf`) | Ensemble | `0.7804` | `0.7770` | `0.7841` | `0.0133` | `99.4 ms` | `classifier` |
| 4 | **K-nearest neighbours** (`knn`) | Instance | `0.7543` | `0.7518` | `0.7550` | `0.0246` | `16.9 ms` | `classifier` |
| 5 | **Logistic regression (multinomial)** (`logreg`) | Linear | `0.7189` | `0.7148` | `0.7173` | `0.1246` | `22.6 ms` | `classifier` |
| 6 | **Decision tree** (`dt`) | Tree | `0.7094` | `0.7085` | `0.6993` | `0.0342` | `16.3 ms` | `classifier` |
| 7 | **Linear regression (score to band)** (`linreg`) | Linear | `0.7032` | `0.7014` | `0.6955` | `0.0213` | `13.2 ms` | `score_to_band` |

## 4. Trade-Off Analysis
- **Accuracy vs Explainability**: SVM achieves the highest raw Macro-F1 (0.8164), but is a black-box margin model requiring post-hoc approximations. Random Forest achieves 0.7804 with native partial tree explainability and near-zero calibration error (ECE 0.0133).
- **Inference Speed**: Decision Tree provides ultra-low latency (16.27 ms single, 0.02s batch), making it ideal for edge or high-throughput batch scenarios.

## 5. Limitations & Caveat
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The performance hierarchy is contingent on the data-generating process. Data sensitivity analysis across linear, nonlinear, and noisy-overlap variants confirms that rankings shift when data dynamics change.