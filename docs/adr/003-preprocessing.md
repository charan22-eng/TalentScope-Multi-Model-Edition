# ADR-003: Preprocessing and Scaler Choice

Status: Accepted

## Context
During EDA, we compared `MinMaxScaler` vs `StandardScaler` for KNN. We also explored engineered features like `projects_per_year` (`projects_completed / (experience_years + 1)`). 

## Decision
- We use **MinMaxScaler** because KNN is sensitive to distance, and min-max naturally bounds our primarily strictly-positive domain values (attendance, hours) between [0, 1].
- We added `projects_per_year` but implemented a safe division (`experience_years + 1`) to silently handle 0 experience.
- We use a custom `Winsorizer` to cap outliers strictly using training-data bounds, preventing data leakage.

## Consequences
- KNN distance calculations are stable.
- We avoid `np.inf` or `NaN` in production.
