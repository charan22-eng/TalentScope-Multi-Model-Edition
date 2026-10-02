# Data Dictionary

| Feature | Type | Valid Range | Missing Policy | Description |
|---|---|---|---|---|
| `attendance` | float | 0–100 (%) | median impute + missing flag | Percentage of days attended in the period. |
| `experience_years` | float | 0–50 | median | Years of professional experience. |
| `training_hours` | float | 0–300 | median | Hours spent in training programs. |
| `projects_completed` | int | 0–100 | median | Number of projects completed in the period. |
| `weekly_hours` | float | 0–100 | median | Average hours worked per week. |
| `prev_score` | float | 1–5 | median | Performance score from the *previous* review period. |
| `department` | categorical | fixed list | "Unknown" | Employee's department. |
| `job_level` | ordinal | fixed list | "Unknown" | Employee's seniority level. |

## Audit-Only Attributes
*These are never used as inputs to the model.*
| Feature | Type | Valid Range | Description |
|---|---|---|---|
| `gender` | categorical | fixed list | Used for fairness disparity checks. |
| `age_band` | categorical | fixed list | Used for fairness disparity checks. |
