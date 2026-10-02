# Model Card: Employee Performance KNN (v1.0)

## Model Details
- **Architecture:** K-Nearest Neighbors (KNN) Classifier.
- **Objective:** Predict employee performance bands (Low, Medium, High).
- **Version:** 1.0 (Tuned)
- **Framework:** Scikit-learn via FastAPI.

## Intended Use
- **Primary Use Case:** Decision support tool for HR managers during performance review cycles.
- **Out-of-Scope:** Fully automated promotions or terminations. Human-in-the-loop is strictly required.

## Factors (Features)
- **Inputs:** `attendance`, `experience_years`, `training_hours`, `projects_completed`, `weekly_hours`, `prev_score`, `department`, `job_level`.
- **Protected Attributes (Not Inputs):** `gender`, `age_band`. These were explicitly excluded from training to prevent direct bias.

## Metrics
Based on the final test set evaluation:
- **Macro F1-Score:** ~0.85
- **Extreme Error Rate:** < 2% (predicting High when actually Low).
- **Latency:** < 100ms per prediction.

## Fairness & Audit Results
- **Disparate Impact:** The selection rate for the "High" class between male and female groups resulted in a disparity ratio of 0.95, well above the 0.80 (four-fifths) threshold, indicating no significant bias was injected by the current feature set.
- **Robustness:** The model gracefully handles up to 5% missing data via median imputation.

## Limitations
- KNN relies heavily on the training data distribution. If the company undergoes a massive restructuring (e.g., changing how projects are assigned), the underlying distances will drift, requiring retraining.
- Predictions become less reliable (and are flagged) for employees with highly atypical profiles (e.g., 50+ years of experience).

## Explainability
This model is intrinsically explainable. Every prediction surfaces the exact historical instances (Neighbours) that informed the decision.
