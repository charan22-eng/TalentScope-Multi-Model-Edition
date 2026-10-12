# Dataset Datasheet: TalentScope Employee Performance v2

## 1. Motivation
- **Purpose**: Created to evaluate seven distinct machine learning models under fair, identical conditions for multi-class employee performance assessment.
- **Dataset Version**: `2.0.0`
- **Clean SHA-256**: ``

## 2. Composition
- **Total Rows**: `11904` (after automated data cleaning)
- **Variants Built**: `linear`, `nonlinear` (default), `noisy_overlap`
- **Features (11)**: `attendance, experience_years, training_hours, projects_completed, weekly_hours, prev_score, peer_feedback, tasks_on_time_pct, certifications, department, job_level`
- **Targets (2)**: `performance, performance_score`

## 3. Split Strategy
- **Train (60%)**: 7,142 rows (model fitting and inner 5-fold CV tuning)
- **Calibration A (10%)**: 1,190 rows (probability calibration via Platt scaling)
- **Calibration B (10%)**: 1,191 rows (conformal prediction nonconformity scores)
- **Holdout Test (20%)**: 2,381 rows (locked single evaluation under Guard G6)

## 4. Protected Attributes & Ethical Boundary
- Protected demographic attributes (`gender`, `age_band`) are stored in an isolated file (`protected.csv`) and strictly excluded from all training features.
- Minimum group representation is enforced for all demographic fairness disparity ratio audits.

## 5. Limitations
> [!IMPORTANT]
> **Synthetic Benchmark**: All employee records are synthetically generated. Model performance and comparative rankings reflect the mathematical relationships embedded in the generator.