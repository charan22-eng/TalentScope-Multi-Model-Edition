# Exploratory Data Analysis & Nonlinearity Findings (Dataset v2)

## 1. Dataset Dimensions and Class Balance
- **Raw Volume**: 12,000 generated rows; **Cleaned Volume**: 11,904 rows (after deduplication and removing impossible values).
- **Target Distribution**:
  - `Low`: 30.01% (3,572 rows)
  - `Medium`: 45.04% (5,362 rows)
  - `High`: 24.95% (2,970 rows)
- **Decision**: Target distribution adheres to the contract quantiles (30th and 75th percentiles). Stratified splitting (60% Train, 20% Calibration, 20% Test) is mandated across all models to preserve class proportions.

## 2. Missingness and Realism Audit
- **Feature Missingness**:
  - `attendance`: 3.91%
  - `experience_years`: 3.88%
  - `training_hours`: 3.77%
  - `projects_completed`: 3.81%
  - `weekly_hours`: 3.99%
  - `prev_score`: 3.98%
  - Extended features (`peer_feedback`, `tasks_on_time_pct`, `certifications`) and categoricals (`department`, `job_level`): 0.00% missing.
- **Decision**: Missingness is within the strict 3% to 5% realism boundary. Use median imputation learned exclusively on training folds. Trees (e.g. histogram boosting) can handle native missingness if configured.

## 3. Kruskal-Wallis Feature Discrimination Tests
Non-parametric rank sum tests across the three performance bands ($k=3$):

| Feature | Kruskal-Wallis $H$ | $p$-value | Effect Rank |
| :--- | :--- | :--- | :--- |
| `projects_completed` | 2272.58 | $< 10^{-300}$ | 1 (Dominant) |
| `prev_score` | 2237.62 | $< 10^{-300}$ | 2 (Dominant) |
| `training_hours` | 1380.13 | $2.04 \times 10^{-300}$ | 3 (Strong) |
| `experience_years` | 974.91 | $2.00 \times 10^{-212}$ | 4 (Strong) |
| `attendance` | 654.99 | $5.89 \times 10^{-143}$ | 5 (Significant) |
| `tasks_on_time_pct` | 540.26 | $4.83 \times 10^{-118}$ | 6 (Moderate) |
| `peer_feedback` | 520.76 | $8.27 \times 10^{-114}$ | 7 (Moderate) |
| `weekly_hours` | 355.81 | $5.45 \times 10^{-78}$ | 8 (Nonlinear) |
| `certifications` | 282.90 | $3.71 \times 10^{-62}$ | 9 (Moderate) |

All 9 continuous/ordinal features exhibit statistically significant differences across performance tiers ($p < 10^{-60}$).

## 4. Empirical Evidence for Non-Linear Data Structure

### 4.1 Saturating Effect of Training Hours
- Quantile binning shows diminishing marginal returns of training:
  - Bin 1 [0 to 31 hrs]: Mean score = **34.67**
  - Bin 2 (31 to 39 hrs]: Mean score = **42.83** (+8.16 pts)
  - Bin 3 (39 to 46 hrs]: Mean score = **46.07** (+3.24 pts)
  - Bin 4 (46 to 53 hrs]: Mean score = **49.01** (+2.94 pts)
  - Bin 5 (53 to 61 hrs]: Mean score = **50.79** (+1.78 pts)
  - Bin 6 (61 to 108 hrs]: Mean score = **54.64** (+3.85 pts across 47 hours)
- **Insight**: Linear models fail to capture this saturation without non-linear feature engineering or kernel functions (SVM/RBF, Gradient Boosting).

### 4.2 Inverted U-Shape for Weekly Working Hours
- Optimal performance centers around 41–44 hours/week; overwork and underwork heavily penalize performance:
  - $\le 38$ hrs: Mean score = **43.64**
  - 38 to 41 hrs: Mean score = **49.89**
  - **41 to 44 hrs (Optimum)**: Mean score = **51.75**
  - 44 to 47 hrs: Mean score = **47.66**
  - 47 to 52 hrs: Mean score = **41.45**
  - $> 52$ hrs (Burnout): Mean score = **30.40**
- **Insight**: Monotonic linear models cannot resolve this parabolic relationship without polynomial expansion.

### 4.3 Attendance Threshold Discontinuity
- Performance exhibits a non-linear cliff around 86% attendance:
  - $\text{Attendance} < 86\%$: Mean score = **39.04**
  - $\text{Attendance} \ge 86\%$: Mean score = **48.64** (+9.60 point drop below threshold)
- **Insight**: Tree-based splitters easily locate this cut-point; linear regressors struggle without step functions.

### 4.4 Synergistic Interaction: Projects $\times$ Previous Score
- Partitioning employees by median `projects_completed` (5) and `prev_score` (3.2):
  - Low Projects, Low Prev Score: **37.99**
  - Low Projects, High Prev Score: **45.00** (+7.01)
  - High Projects, Low Prev Score: **43.95** (+5.96)
  - **High Projects, High Prev Score**: **66.16** (+21.16 over baseline!)
- **Insight**: The compound return ($+28.17$) significantly exceeds the sum of independent marginals ($+7.01 + 5.96 = +12.97$). Tree ensembles and boosting natively capture this feature interaction.

## 5. Architectural Preprocessing Decisions
1. **Model-Aware Scaling**: Tree models (`dt`, `rf`, `boost`) receive unscaled features to preserve natural feature thresholds and avoid unnecessary computation. Distance and margin models (`linreg`, `logreg`, `knn`, `svm`) receive `StandardScaler`.
2. **Train-Only Winsorizing**: Outliers clipped at 1st and 99th percentiles fitted exclusively on training folds to prevent leakage.
3. **Encoding Discipline**: Ordinal encoding on `job_level` (`Junior`=0, `Mid`=1, `Senior`=2, `Lead`=3); one-hot encoding on `department` (8 categories, `handle_unknown="ignore"`).
4. **Label Ordering**: Bands encoded strictly as ordered integers: `Low`=0, `Medium`=1, `High`=2.
