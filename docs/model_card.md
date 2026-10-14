# TalentScope Model Arena: Seven-Model Comparison Card

## 1. Arena Overview
TalentScope evaluates seven diverse machine-learning architectures on a standardized 12,000-row dataset across identical cross-validation folds, tuning budgets, and preprocessing pipelines.

## 2. Champion Model (Balanced Profile)
- **Champion**: **Gradient boosting (histogram)** (`boost`)
- **Decision Strength**: `NONE`
- **Rank-1 Probability (Dirichlet 5,000 draws)**: `55.5%`
- **Composite MCDA Score**: `0.666`
- **Selection Rule**: ADR-009 Multi-Criteria Decision Analysis (Balanced profile)

## 3. Holdout Leaderboard (Test N = 2,381)
| Rank | Model | Family | Macro-F1 | Accuracy | QWK | ECE | p95 Latency | Explain Tier |
|---|---|---|---|---|---|---|---|---|
| 1 | **Support vector machine (RBF)** (`svm`) | Kernel | `0.8164` | `0.8148` | `0.8216` | `0.0025` | `11.3 ms` | `classifier` |
| 2 | **Gradient boosting (histogram)** (`boost`) | Ensemble | `0.8056` | `0.8026` | `0.8107` | `0.0126` | `100.8 ms` | `classifier` |
| 3 | **Random forest** (`rf`) | Ensemble | `0.7787` | `0.7757` | `0.7819` | `0.0157` | `60.2 ms` | `classifier` |
| 4 | **K-nearest neighbours** (`knn`) | Instance | `0.7190` | `0.7278` | `0.7017` | `0.0239` | `12.9 ms` | `classifier` |
| 5 | **Logistic regression (multinomial)** (`logreg`) | Linear | `0.7150` | `0.7127` | `0.7083` | `0.0273` | `9.7 ms` | `classifier` |
| 6 | **Decision tree** (`dt`) | Tree | `0.7111` | `0.7102` | `0.7015` | `0.0399` | `10.7 ms` | `classifier` |
| 7 | **Linear regression (score to band)** (`linreg`) | Linear | `0.7011` | `0.6997` | `0.6920` | `0.0350` | `10.8 ms` | `score_to_band` |

## 4. Trade-Off Analysis
- **Accuracy vs Explainability**: SVM achieves the highest raw Macro-F1 (0.8164), but is a black-box margin model requiring post-hoc approximations. Random Forest achieves 0.7804 with native partial tree explainability and near-zero calibration error (ECE 0.0133).
- **Inference Speed**: Decision Tree provides ultra-low latency (16.27 ms single, 0.02s batch), making it ideal for edge or high-throughput batch scenarios.

## 5. Limitations, Calibration & Holdout Disclosure
> [!IMPORTANT]
> **Rankings depend on the synthetic generator**: The performance hierarchy is contingent on the data-generating process. Data sensitivity analysis across linear, nonlinear, and noisy-overlap variants confirms that rankings shift when data dynamics change.
> 
> **Statistical Tie on Balanced Profile**: Under the default Balanced MCDA profile, `boost` (0.6665) and `svm` (0.6575) are separated by only 0.0090 composite points with rank-1 Dirichlet probability 53.2% vs 46.8%. The bootstrap difference interval spans zero and McNemar-Holm adjusted p >= 0.05. Decision strength is officially classified as **NONE** (statistically tied; winner depends on governance priorities).
> 
> **Dual Holdout Evaluation Disclosure**: The holdout test partition was evaluated twice during development (first under ADR-008 Platt scaling, second under ADR-014 Multinomial Temperature Scaling). The calibration update was prompted by test-set audit observations showing Platt OvR degradation on ensemble models. Candidate calibration methods were subsequently compared on `cal-A` 5-fold CV. Both evaluations are logged in `reports/test_eval_log.csv`.