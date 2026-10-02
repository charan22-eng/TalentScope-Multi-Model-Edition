# Exploratory Data Analysis & Audit Findings

## Structural Audit
- Shape: 5025 rows (includes 25 duplicates injected as part of realism).
- Missing values: ~4% missingness artificially injected into `attendance`, `experience_years`, `training_hours`, `projects_completed`, `weekly_hours`, and `prev_score`.
- Categoricals (`department`, `job_level`) have no missing values.
- **Decision:** Use Median imputation for numerics, Mode for categoricals (if they ever go missing in production).

## Univariate Analysis & Outliers
- `training_hours` and `weekly_hours` contain extreme outliers (e.g. 500 hours, 120 hours).
- `attendance` is bounded mostly 0-100 but can contain noise.
- **Decision:** Apply a custom `Winsorizer` (clipping at 1st and 99th percentiles learned on the training set) to robustly cap outliers before scaling.

## Class Balance
- Low: ~30%, Medium: ~45%, High: ~25%.
- **Decision:** Classes are reasonably balanced. We will use stratified k-fold, but heavy SMOTE oversampling is unnecessary.

## Correlation & Separability
- `projects_completed` and `prev_score` show the strongest correlation with the `High` performance class, validating Baseline Hypothesis 1.
- `experience_years` is correlated with `projects_completed`, which is expected.
- **Decision:** Features are sufficiently independent to not require PCA before classification. 
- **Decision:** Min-Max scaling will be used to normalize features into the [0, 1] range to ensure distance metrics (KNN) weight them fairly.
