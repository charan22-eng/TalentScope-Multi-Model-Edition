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

## 6. Fresh-Seed Confirmation Run (Seed = 2026, N = 2,381)
> [!NOTE]
> **Strictly Observational**: Per FF4 Item 3, this fresh-seed confirmation run evaluates all final models and calibrators on an independent, unseen synthetic draw (seed 2026, non-linear variant, 11,904 rows, test N = 2,381). **Zero retraining or hyperparameter tuning was performed.** Confirmation data was never used for model choice.

### Confirmation Holdout Metrics (N = 2,381, Seed = 2026)
| Rank | Model | Family | Macro-F1 (95% CI) | Accuracy (95% CI) | QWK (95% CI) | ECE | Conformal Cov. (α=0.10) |
|---|---|---|---|---|---|---|---|
| 1 | **Support vector machine (RBF)** (`svm`) | Kernel | `0.7997` [0.7831, 0.8157] | `0.7992` [0.7833, 0.8152] | `0.8037` [0.7853, 0.8209] | `0.0055` | `0.2831` |
| 2 | **Gradient boosting (histogram)** (`boost`) | Ensemble | `0.7937` [0.7772, 0.8100] | `0.7904` [0.7740, 0.8068] | `0.7943` [0.7757, 0.8121] | `0.0160` | `0.2801` |
| 3 | **Random forest** (`rf`) | Ensemble | `0.7638` [0.7466, 0.7806] | `0.7610` [0.7438, 0.7778] | `0.7645` [0.7447, 0.7832] | `0.0197` | `0.2394` |
| 4 | **Logistic regression (multinomial)** (`logreg`) | Linear | `0.7107` [0.6923, 0.7289] | `0.7098` [0.6917, 0.7283] | `0.7011` [0.6788, 0.7225] | `0.0270` | `0.0932` |
| 5 | **K-nearest neighbours** (`knn`) | Instance | `0.7058` [0.6872, 0.7243] | `0.7144` [0.6963, 0.7329] | `0.6865` [0.6635, 0.7088] | `0.0276` | `0.1243` |
| 6 | **Decision tree** (`dt`) | Tree | `0.6914` [0.6728, 0.7099] | `0.6926` [0.6737, 0.7106] | `0.6670` [0.6433, 0.6896] | `0.0268` | `0.0701` |
| 7 | **Linear regression (score to band)** (`linreg`) | Linear | `0.6873` [0.6684, 0.7058] | `0.6867` [0.6678, 0.7052] | `0.6756` [0.6521, 0.6978] | `0.0381` | `0.0811` |

### Confirmation MCDA Ranking (Seed = 2026)
- **Balanced**: Winner = `boost` (0.8114) vs Runner-up = `rf` (0.6637) | `svm` (0.6582, rank 3) | Rank-1 Prob = 99.9% | Decision Strength = `marginal`
- **Accuracy-first**: Winner = `boost` (0.9557) vs `svm` (0.8282) | Rank-1 Prob = 100.0% | Strength = `marginal`
- **Explainability-first**: Winner = `logreg` (0.7037) vs `boost` (0.6971) | Rank-1 Prob = 56.7% | Strength = `none`
- **Speed-first**: Winner = `boost` (0.4700) vs `svm` (0.3917) | Rank-1 Prob = 99.9% | Strength = `marginal`
- **Fairness-first**: Winner = `boost` (0.8686) vs `rf` (0.7529) | Rank-1 Prob = 100.0% | Strength = `marginal`
